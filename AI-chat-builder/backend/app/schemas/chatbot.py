from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict
from datetime import datetime


class ChatbotCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: str
    system_prompt: Optional[str] = None
    welcome_message: str = "Hello! How can I help you today?"
    tone: str = "professional"
    provider: str = "together"
    model_name: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    temperature: float = 0.7
    max_tokens: int = 1000
    streaming_enabled: bool = True
    theme_config: Optional[Dict] = None


class ChatbotUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: Optional[str] = None
    system_prompt: Optional[str] = None
    welcome_message: Optional[str] = None
    tone: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    streaming_enabled: Optional[bool] = None
    theme_config: Optional[Dict] = None
    is_active: Optional[bool] = None


class ChatbotResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: str
    organization_id: str
    name: str
    slug: str
    system_prompt: Optional[str] = None
    welcome_message: str
    tone: str
    provider: str
    model_name: str
    temperature: float
    max_tokens: int
    streaming_enabled: bool
    theme_config: Optional[Dict] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
