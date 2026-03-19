from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from datetime import datetime
from bson import ObjectId
from app.core.database import get_db, to_object_id, serialize_doc
from app.core.dependencies import get_current_active_user
from app.schemas.chatbot import ChatbotCreate, ChatbotUpdate, ChatbotResponse
from app.models.chatbot import CHATBOTS_COLLECTION
from app.models.api_key import API_KEYS_COLLECTION

router = APIRouter(prefix="/api/chatbots", tags=["Chatbots"])


@router.get("/", response_model=List[ChatbotResponse])
async def list_chatbots(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List all chatbots for the organization"""
    cursor = db[CHATBOTS_COLLECTION].find(
        {"organization_id": current_user["organization_id"]}
    )
    chatbots = await cursor.to_list(length=None)
    return [serialize_doc(c) for c in chatbots]


@router.post("/", response_model=ChatbotResponse)
async def create_chatbot(
    request: ChatbotCreate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new chatbot"""
    # Validate that API key exists for the selected provider
    api_key_exists = await db[API_KEYS_COLLECTION].find_one({
        "organization_id": current_user["organization_id"],
        "provider": request.provider,
        "is_active": True
    })
    
    if not api_key_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No active API key configured for {request.provider}. Please add an API key in Provider Settings before creating a chatbot."
        )
    
    slug = request.name.lower().replace(" ", "-").replace("_", "-")
    base_slug = slug
    counter = 1
    while await db[CHATBOTS_COLLECTION].find_one({
        "organization_id": current_user["organization_id"],
        "slug": slug
    }):
        slug = f"{base_slug}-{counter}"
        counter += 1

    now = datetime.utcnow()
    chatbot_doc = {
        "organization_id": current_user["organization_id"],
        "name": request.name,
        "slug": slug,
        "system_prompt": request.system_prompt,
        "welcome_message": request.welcome_message or "Hello! How can I help you today?",
        "tone": request.tone or "professional",
        "provider": request.provider,
        "model_name": request.model_name,
        "temperature": request.temperature if request.temperature is not None else 0.7,
        "max_tokens": request.max_tokens or 1000,
        "streaming_enabled": request.streaming_enabled if request.streaming_enabled is not None else True,
        "theme_config": request.theme_config,
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    result = await db[CHATBOTS_COLLECTION].insert_one(chatbot_doc)
    chatbot_doc["id"] = str(result.inserted_id)
    return chatbot_doc


@router.get("/{chatbot_id}", response_model=ChatbotResponse)
async def get_chatbot(
    chatbot_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get chatbot details"""
    oid = to_object_id(chatbot_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")

    chatbot = await db[CHATBOTS_COLLECTION].find_one({
        "_id": oid,
        "organization_id": current_user["organization_id"]
    })
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")

    return serialize_doc(chatbot)


@router.put("/{chatbot_id}", response_model=ChatbotResponse)
async def update_chatbot(
    chatbot_id: str,
    request: ChatbotUpdate,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update chatbot"""
    oid = to_object_id(chatbot_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")

    chatbot = await db[CHATBOTS_COLLECTION].find_one({
        "_id": oid,
        "organization_id": current_user["organization_id"]
    })
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")

    update_data = request.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    await db[CHATBOTS_COLLECTION].update_one({"_id": oid}, {"$set": update_data})

    updated = await db[CHATBOTS_COLLECTION].find_one({"_id": oid})
    return serialize_doc(updated)


@router.delete("/{chatbot_id}")
async def delete_chatbot(
    chatbot_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete chatbot"""
    oid = to_object_id(chatbot_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")

    result = await db[CHATBOTS_COLLECTION].delete_one({
        "_id": oid,
        "organization_id": current_user["organization_id"]
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")

    return {"message": "Chatbot deleted successfully"}


@router.get("/{chatbot_id}/embed-code")
async def get_embed_code(
    chatbot_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get embed code for chatbot"""
    oid = to_object_id(chatbot_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")

    chatbot = await db[CHATBOTS_COLLECTION].find_one({
        "_id": oid,
        "organization_id": current_user["organization_id"]
    })
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")

    embed_code = f'<script src="https://yourapp.com/widget.js" data-bot-id="{chatbot_id}"></script>'
    return {
        "embed_code": embed_code,
        "chatbot_id": chatbot_id,
        "chatbot_slug": chatbot["slug"]
    }
