from typing import List, Dict, AsyncGenerator, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId
import uuid
from app.models.chatbot import CHATBOTS_COLLECTION
from app.models.conversation import CONVERSATIONS_COLLECTION
from app.models.message import MessageRole, MESSAGES_COLLECTION
from app.models.api_key import API_KEYS_COLLECTION
from app.models.usage_log import USAGE_LOGS_COLLECTION
from app.services.llm.factory import LLMProviderFactory
from app.services.rag_service import RAGService
from app.core.security import decrypt_api_key
from app.core.database import serialize_doc


class ChatService:
    """Service for handling chat operations"""

    def __init__(self):
        self.rag_service = RAGService()

    async def create_conversation(
        self,
        chatbot_id: str,
        user_identifier: Optional[str],
        db: AsyncIOMotorDatabase
    ) -> dict:
        """Create a new conversation"""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        conv_doc = {
            "chatbot_id": chatbot_id,
            "session_id": session_id,
            "user_identifier": user_identifier,
            "started_at": now,
            "last_message_at": now
        }
        result = await db[CONVERSATIONS_COLLECTION].insert_one(conv_doc)
        return {**conv_doc, "id": str(result.inserted_id)}

    async def get_or_create_conversation(
        self,
        chatbot_id: str,
        session_id: Optional[str],
        user_identifier: Optional[str],
        db: AsyncIOMotorDatabase
    ) -> dict:
        """Get existing conversation or create new one"""
        if session_id:
            conv = await db[CONVERSATIONS_COLLECTION].find_one({"session_id": session_id})
            if conv:
                return serialize_doc(conv)
        return await self.create_conversation(chatbot_id, user_identifier, db)

    async def send_message(
        self,
        chatbot_id: str,
        user_message: str,
        session_id: Optional[str],
        user_identifier: Optional[str],
        db: AsyncIOMotorDatabase,
        streaming: bool = True
    ) -> AsyncGenerator[Dict, None]:
        """Send a message and get AI response"""
        start_time = datetime.utcnow()

        try:
            chatbot = await db[CHATBOTS_COLLECTION].find_one({"_id": ObjectId(chatbot_id)})
            if not chatbot:
                yield {
                    "type": "error",
                    "content": "Chatbot not found",
                    "error_code": "CHATBOT_NOT_FOUND"
                }
                return
            chatbot = serialize_doc(chatbot)
        except Exception as e:
            yield {
                "type": "error",
                "content": f"Failed to load chatbot: {str(e)}",
                "error_code": "CHATBOT_LOAD_ERROR"
            }
            return

        conversation = await self.get_or_create_conversation(
            chatbot_id, session_id, user_identifier, db
        )

        now = datetime.utcnow()
        await db[MESSAGES_COLLECTION].insert_one({
            "conversation_id": conversation["id"],
            "role": MessageRole.USER.value,
            "content": user_message,
            "tokens_used": 0,
            "created_at": now
        })

        await db[CONVERSATIONS_COLLECTION].update_one(
            {"session_id": conversation["session_id"]},
            {"$set": {"last_message_at": now}}
        )

        try:
            messages = await self._build_message_history(conversation, chatbot, user_message, db)
        except Exception as e:
            # Log error but continue without RAG context
            messages = [
                {"role": "system", "content": chatbot.get("system_prompt") or "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ]

        # Validate API key exists
        api_key_doc = await db[API_KEYS_COLLECTION].find_one({
            "organization_id": chatbot["organization_id"],
            "provider": chatbot["provider"],
            "is_active": True
        })

        if not api_key_doc:
            yield {
                "type": "error",
                "content": f"No active API key configured for {chatbot['provider']}. Please add an API key in settings.",
                "error_code": "API_KEY_NOT_FOUND"
            }
            return

        try:
            api_key = decrypt_api_key(api_key_doc["encrypted_key"])
            provider = LLMProviderFactory.get_provider(chatbot["provider"], api_key)
        except Exception as e:
            yield {
                "type": "error",
                "content": f"Failed to initialize AI provider: {str(e)}",
                "error_code": "PROVIDER_INIT_ERROR"
            }
            return

        config = {
            "model": chatbot["model_name"],
            "temperature": chatbot["temperature"],
            "max_tokens": chatbot["max_tokens"]
        }

        full_response = ""

        try:
            if streaming and chatbot.get("streaming_enabled", True):
                async for chunk in provider.generate_response(messages, config):
                    full_response += chunk
                    yield {
                        "type": "chunk",
                        "content": chunk,
                        "session_id": conversation["session_id"]
                    }
            else:
                response_data = await provider.generate_response_non_streaming(messages, config)
                full_response = response_data["content"]
                yield {
                    "type": "complete",
                    "content": full_response,
                    "session_id": conversation["session_id"],
                    "tokens_used": response_data["tokens_used"]
                }
        except Exception as e:
            yield {
                "type": "error",
                "content": f"AI provider error: {str(e)}",
                "error_code": "LLM_GENERATION_ERROR"
            }
            return

        # Save response and usage logs
        try:
            end_time = datetime.utcnow()
            response_time_ms = int((end_time - start_time).total_seconds() * 1000)
            tokens_used = provider.count_tokens(user_message + full_response)

            await db[MESSAGES_COLLECTION].insert_one({
                "conversation_id": conversation["id"],
                "role": MessageRole.ASSISTANT.value,
                "content": full_response,
                "tokens_used": tokens_used,
                "provider_used": chatbot["provider"],
                "model_used": chatbot["model_name"],
                "response_time_ms": response_time_ms,
                "created_at": datetime.utcnow()
            })

            await db[USAGE_LOGS_COLLECTION].insert_one({
                "organization_id": chatbot["organization_id"],
                "chatbot_id": chatbot["id"],
                "provider": chatbot["provider"],
                "model": chatbot["model_name"],
                "tokens_used": tokens_used,
                "estimated_cost": provider.estimate_cost(tokens_used, chatbot["model_name"]),
                "date": datetime.utcnow().date().isoformat(),
                "created_at": datetime.utcnow()
            })

            await db[API_KEYS_COLLECTION].update_one(
                {"_id": api_key_doc["_id"]},
                {"$set": {"last_used_at": datetime.utcnow()}}
            )

            yield {
                "type": "done",
                "session_id": conversation["session_id"],
                "tokens_used": tokens_used,
                "response_time_ms": response_time_ms
            }
        except Exception as e:
            # Log error but don't fail the response
            yield {
                "type": "warning",
                "content": "Response generated but logging failed",
                "session_id": conversation["session_id"]
            }

    async def _build_message_history(
        self,
        conversation: dict,
        chatbot: dict,
        current_message: str,
        db: AsyncIOMotorDatabase
    ) -> List[Dict[str, str]]:
        """Build message history for LLM"""
        messages = []
        system_prompt = chatbot.get("system_prompt") or "You are a helpful assistant."

        # Try to get RAG context, but don't fail if it doesn't work
        try:
            rag_context = await self.rag_service.search_similar_chunks(
                current_message, chatbot["id"], db, top_k=3
            )

            if rag_context:
                context_text = self.rag_service.format_context(rag_context)
                system_prompt += f"\n\n{context_text}\n\nUse the above information to answer questions when relevant."
        except Exception:
            # Continue without RAG context if it fails
            pass

        messages.append({"role": "system", "content": system_prompt})

        try:
            cursor = db[MESSAGES_COLLECTION].find(
                {"conversation_id": conversation["id"]}
            ).sort("created_at", -1).limit(10)
            history = await cursor.to_list(length=10)
            history.reverse()

            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        except Exception:
            # Continue with just system prompt and current message if history fetch fails
            pass

        return messages

    async def get_conversation_history(
        self,
        conversation_id: str,
        db: AsyncIOMotorDatabase
    ) -> List[dict]:
        """Get conversation message history"""
        cursor = db[MESSAGES_COLLECTION].find(
            {"conversation_id": conversation_id}
        ).sort("created_at", 1)
        messages = await cursor.to_list(length=None)
        return [serialize_doc(m) for m in messages]
