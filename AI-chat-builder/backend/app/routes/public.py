from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_db, to_object_id
from app.schemas.chat import ChatMessageRequest
from app.services.chat_service import ChatService
from app.models.chatbot import CHATBOTS_COLLECTION
import json

router = APIRouter(prefix="/api/public", tags=["Public"])
chat_service = ChatService()


@router.post("/chat/{chatbot_id}")
async def public_chat(
    chatbot_id: str,
    request: ChatMessageRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Public chat endpoint for embedded widgets"""
    oid = to_object_id(chatbot_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found or inactive")

    chatbot = await db[CHATBOTS_COLLECTION].find_one({"_id": oid, "is_active": True})
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found or inactive")

    async def generate():
        try:
            async for chunk in chat_service.send_message(
                chatbot_id=chatbot_id,
                user_message=request.message,
                session_id=request.session_id,
                user_identifier=request.user_identifier,
                db=db,
                streaming=True
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/bot/{chatbot_id}/config")
async def get_bot_config(
    chatbot_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get public chatbot configuration for widget"""
    oid = to_object_id(chatbot_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found or inactive")

    chatbot = await db[CHATBOTS_COLLECTION].find_one({"_id": oid, "is_active": True})
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found or inactive")

    return {
        "id": chatbot_id,
        "name": chatbot["name"],
        "welcome_message": chatbot.get("welcome_message", "Hello! How can I help you today?"),
        "theme_config": chatbot.get("theme_config") or {}
    }
