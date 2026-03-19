from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class APIKeyCreate(BaseModel):
    provider: str
    api_key: str
    is_default: bool = False


class APIKeyUpdate(BaseModel):
    api_key: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class APIKeyResponse(BaseModel):
    id: str
    organization_id: str
    provider: str
    is_active: bool
    is_default: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None


class APIKeyTestResponse(BaseModel):
    success: bool
    message: str
