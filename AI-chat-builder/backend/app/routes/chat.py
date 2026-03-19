from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Optional
import json
from app.core.database import get_db, to_object_id, serialize_doc
from app.core.dependencies import get_current_active_user
from app.schemas.chat import ChatMessageRequest, ConversationResponse, MessageResponse
from app.models.chatbot import CHATBOTS_COLLECTION
from app.models.conversation import CONVERSATIONS_COLLECTION
from app.models.message import MESSAGES_COLLECTION
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["Chat"])
chat_service = ChatService()


@router.post("/{chatbot_id}/message")
async def send_message(
    chatbot_id: str,
    request: ChatMessageRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Send a message to a chatbot"""
    oid = to_object_id(chatbot_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")

    chatbot = await db[CHATBOTS_COLLECTION].find_one({
        "_id": oid,
        "organization_id": current_user["organization_id"]
    })
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")

    async def generate():
        async for chunk in chat_service.send_message(
            chatbot_id=chatbot_id,
            user_message=request.message,
            session_id=request.session_id,
            user_identifier=request.user_identifier,
            db=db
        ):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    chatbot_id: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List conversations"""
    chatbot_ids_cursor = db[CHATBOTS_COLLECTION].find(
        {"organization_id": current_user["organization_id"]},
        {"_id": 1}
    )
    chatbot_docs = await chatbot_ids_cursor.to_list(length=None)
    org_chatbot_ids = [str(c["_id"]) for c in chatbot_docs]

    query: dict = {"chatbot_id": {"$in": org_chatbot_ids}}
    if chatbot_id:
        query = {"chatbot_id": chatbot_id}

    cursor = db[CONVERSATIONS_COLLECTION].find(query).sort("last_message_at", -1)
    conversations = await cursor.to_list(length=None)
    return [serialize_doc(c) for c in conversations]


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get messages for a conversation"""
    oid = to_object_id(conversation_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    conversation = await db[CONVERSATIONS_COLLECTION].find_one({"_id": oid})
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    chatbot = await db[CHATBOTS_COLLECTION].find_one({
        "_id": to_object_id(conversation["chatbot_id"]),
        "organization_id": current_user["organization_id"]
    })
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = await chat_service.get_conversation_history(conversation_id, db)
    return messages


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a conversation"""
    oid = to_object_id(conversation_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    conversation = await db[CONVERSATIONS_COLLECTION].find_one({"_id": oid})
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    chatbot = await db[CHATBOTS_COLLECTION].find_one({
        "_id": to_object_id(conversation["chatbot_id"]),
        "organization_id": current_user["organization_id"]
    })
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    await db[MESSAGES_COLLECTION].delete_many({"conversation_id": conversation_id})
    await db[CONVERSATIONS_COLLECTION].delete_one({"_id": oid})

    return {"message": "Conversation deleted successfully"}
