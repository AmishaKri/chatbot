from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_identifier: Optional[str] = None


class ChatMessageResponse(BaseModel):
    type: str
    content: Optional[str] = None
    session_id: Optional[str] = None
    tokens_used: Optional[int] = None
    response_time_ms: Optional[int] = None


class ConversationResponse(BaseModel):
    id: str
    chatbot_id: str
    session_id: str
    user_identifier: Optional[str] = None
    started_at: datetime
    last_message_at: datetime


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    tokens_used: int = 0
    created_at: datetime
