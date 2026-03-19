from pydantic import BaseModel
from typing import List, Dict
from datetime import date


class OverviewStats(BaseModel):
    total_conversations: int
    total_messages: int
    total_tokens_used: int
    total_estimated_cost: float
    active_chatbots: int


class ProviderUsageStats(BaseModel):
    provider: str
    total_tokens: int
    total_requests: int
    total_cost: float
    percentage: float


class UsageByDateStats(BaseModel):
    date: date
    tokens_used: int
    requests: int
    cost: float


class ConversationStats(BaseModel):
    total_conversations: int
    avg_messages_per_conversation: float
    avg_response_time_ms: float


class PopularQuery(BaseModel):
    query: str
    count: int
