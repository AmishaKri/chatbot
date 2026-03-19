from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.analytics import (
    OverviewStats, ProviderUsageStats, UsageByDateStats,
    ConversationStats, PopularQuery
)
from app.models.chatbot import CHATBOTS_COLLECTION
from app.models.conversation import CONVERSATIONS_COLLECTION
from app.models.message import MESSAGES_COLLECTION, MessageRole
from app.models.usage_log import USAGE_LOGS_COLLECTION

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview", response_model=OverviewStats)
async def get_overview_stats(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get overview statistics"""
    org_id = current_user["organization_id"]

    chatbot_cursor = db[CHATBOTS_COLLECTION].find({"organization_id": org_id}, {"_id": 1})
    chatbot_docs = await chatbot_cursor.to_list(length=None)
    chatbot_ids = [str(c["_id"]) for c in chatbot_docs]

    total_conversations = await db[CONVERSATIONS_COLLECTION].count_documents(
        {"chatbot_id": {"$in": chatbot_ids}}
    )

    total_messages = await db[MESSAGES_COLLECTION].count_documents(
        {"conversation_id": {"$exists": True}}
    )

    usage_pipeline = [
        {"$match": {"organization_id": org_id}},
        {"$group": {
            "_id": None,
            "total_tokens": {"$sum": "$tokens_used"},
            "total_cost": {"$sum": "$estimated_cost"}
        }}
    ]
    usage_result = await db[USAGE_LOGS_COLLECTION].aggregate(usage_pipeline).to_list(1)
    total_tokens = usage_result[0]["total_tokens"] if usage_result else 0
    total_cost = usage_result[0]["total_cost"] if usage_result else 0.0

    active_chatbots = await db[CHATBOTS_COLLECTION].count_documents(
        {"organization_id": org_id, "is_active": True}
    )

    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "total_tokens_used": total_tokens,
        "total_estimated_cost": float(total_cost),
        "active_chatbots": active_chatbots
    }


@router.get("/usage", response_model=List[ProviderUsageStats])
async def get_provider_usage(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get usage statistics by provider"""
    org_id = current_user["organization_id"]
    start_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()

    pipeline = [
        {"$match": {"organization_id": org_id, "date": {"$gte": start_date}}},
        {"$group": {
            "_id": "$provider",
            "total_tokens": {"$sum": "$tokens_used"},
            "total_requests": {"$sum": 1},
            "total_cost": {"$sum": "$estimated_cost"}
        }}
    ]
    rows = await db[USAGE_LOGS_COLLECTION].aggregate(pipeline).to_list(length=None)
    total_tokens = sum(r["total_tokens"] for r in rows)

    result = []
    for row in rows:
        percentage = (row["total_tokens"] / total_tokens * 100) if total_tokens > 0 else 0
        result.append({
            "provider": row["_id"],
            "total_tokens": row["total_tokens"],
            "total_requests": row["total_requests"],
            "total_cost": float(row["total_cost"]),
            "percentage": round(percentage, 2)
        })
    return result


@router.get("/costs", response_model=List[UsageByDateStats])
async def get_cost_breakdown(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get cost breakdown by date"""
    org_id = current_user["organization_id"]
    start_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()

    pipeline = [
        {"$match": {"organization_id": org_id, "date": {"$gte": start_date}}},
        {"$group": {
            "_id": "$date",
            "tokens_used": {"$sum": "$tokens_used"},
            "requests": {"$sum": 1},
            "cost": {"$sum": "$estimated_cost"}
        }},
        {"$sort": {"_id": 1}}
    ]
    rows = await db[USAGE_LOGS_COLLECTION].aggregate(pipeline).to_list(length=None)
    return [
        {
            "date": row["_id"],
            "tokens_used": row["tokens_used"],
            "requests": row["requests"],
            "cost": float(row["cost"])
        }
        for row in rows
    ]


@router.get("/conversations/stats", response_model=ConversationStats)
async def get_conversation_stats(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get conversation statistics"""
    org_id = current_user["organization_id"]

    chatbot_cursor = db[CHATBOTS_COLLECTION].find({"organization_id": org_id}, {"_id": 1})
    chatbot_docs = await chatbot_cursor.to_list(length=None)
    chatbot_ids = [str(c["_id"]) for c in chatbot_docs]

    total_conversations = await db[CONVERSATIONS_COLLECTION].count_documents(
        {"chatbot_id": {"$in": chatbot_ids}}
    )

    conv_cursor = db[CONVERSATIONS_COLLECTION].find(
        {"chatbot_id": {"$in": chatbot_ids}}, {"_id": 1}
    )
    conv_docs = await conv_cursor.to_list(length=None)
    conv_ids = [str(c["_id"]) for c in conv_docs]

    avg_msgs = 0.0
    if conv_ids:
        msg_pipeline = [
            {"$match": {"conversation_id": {"$in": conv_ids}}},
            {"$group": {"_id": "$conversation_id", "count": {"$sum": 1}}},
            {"$group": {"_id": None, "avg": {"$avg": "$count"}}}
        ]
        msg_result = await db[MESSAGES_COLLECTION].aggregate(msg_pipeline).to_list(1)
        avg_msgs = float(msg_result[0]["avg"]) if msg_result else 0.0

    rt_pipeline = [
        {"$match": {
            "conversation_id": {"$in": conv_ids},
            "role": MessageRole.ASSISTANT.value,
            "response_time_ms": {"$ne": None}
        }},
        {"$group": {"_id": None, "avg_rt": {"$avg": "$response_time_ms"}}}
    ]
    rt_result = await db[MESSAGES_COLLECTION].aggregate(rt_pipeline).to_list(1)
    avg_rt = float(rt_result[0]["avg_rt"]) if rt_result else 0.0

    return {
        "total_conversations": total_conversations,
        "avg_messages_per_conversation": avg_msgs,
        "avg_response_time_ms": avg_rt
    }


@router.get("/popular-queries", response_model=List[PopularQuery])
async def get_popular_queries(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get most common user queries"""
    org_id = current_user["organization_id"]

    chatbot_cursor = db[CHATBOTS_COLLECTION].find({"organization_id": org_id}, {"_id": 1})
    chatbot_docs = await chatbot_cursor.to_list(length=None)
    chatbot_ids = [str(c["_id"]) for c in chatbot_docs]

    conv_cursor = db[CONVERSATIONS_COLLECTION].find(
        {"chatbot_id": {"$in": chatbot_ids}}, {"_id": 1}
    )
    conv_docs = await conv_cursor.to_list(length=None)
    conv_ids = [str(c["_id"]) for c in conv_docs]

    pipeline = [
        {"$match": {"conversation_id": {"$in": conv_ids}, "role": MessageRole.USER.value}},
        {"$group": {"_id": "$content", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    rows = await db[MESSAGES_COLLECTION].aggregate(pipeline).to_list(length=None)
    return [{"query": row["_id"][:100], "count": row["count"]} for row in rows]
