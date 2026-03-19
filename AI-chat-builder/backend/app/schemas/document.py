from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentResponse(BaseModel):
    id: str
    chatbot_id: str
    organization_id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    uploaded_at: datetime
    processed_at: Optional[datetime] = None


class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    message: str
