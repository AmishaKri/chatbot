from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from datetime import datetime
from app.core.database import get_db, to_object_id, serialize_doc
from app.core.dependencies import get_current_active_user, require_role
from app.core.security import encrypt_api_key, decrypt_api_key
from app.schemas.api_key import APIKeyCreate, APIKeyUpdate, APIKeyResponse, APIKeyTestResponse
from app.models.user import UserRole
from app.models.api_key import API_KEYS_COLLECTION
from app.services.llm.factory import LLMProviderFactory

router = APIRouter(prefix="/api/api-keys", tags=["API Keys"])


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List all API keys for the organization"""
    cursor = db[API_KEYS_COLLECTION].find(
        {"organization_id": current_user["organization_id"]}
    )
    keys = await cursor.to_list(length=None)
    return [serialize_doc(k) for k in keys]


@router.post("/", response_model=APIKeyResponse)
async def create_api_key(
    request: APIKeyCreate,
    current_user: dict = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new API key"""
    encrypted_key = encrypt_api_key(request.api_key)

    if request.is_default:
        await db[API_KEYS_COLLECTION].update_many(
            {"organization_id": current_user["organization_id"], "provider": request.provider},
            {"$set": {"is_default": False}}
        )

    now = datetime.utcnow()
    key_doc = {
        "organization_id": current_user["organization_id"],
        "provider": request.provider,
        "encrypted_key": encrypted_key,
        "is_active": True,
        "is_default": request.is_default,
        "created_at": now,
        "last_used_at": None
    }
    result = await db[API_KEYS_COLLECTION].insert_one(key_doc)
    key_doc["id"] = str(result.inserted_id)
    return key_doc


@router.put("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: str,
    request: APIKeyUpdate,
    current_user: dict = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update API key"""
    oid = to_object_id(key_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    api_key = await db[API_KEYS_COLLECTION].find_one({
        "_id": oid,
        "organization_id": current_user["organization_id"]
    })
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    update_fields = {}
    if request.api_key:
        update_fields["encrypted_key"] = encrypt_api_key(request.api_key)
    if request.is_active is not None:
        update_fields["is_active"] = request.is_active
    if request.is_default:
        await db[API_KEYS_COLLECTION].update_many(
            {
                "organization_id": current_user["organization_id"],
                "provider": api_key["provider"]
            },
            {"$set": {"is_default": False}}
        )
        update_fields["is_default"] = True

    if update_fields:
        await db[API_KEYS_COLLECTION].update_one({"_id": oid}, {"$set": update_fields})

    updated = await db[API_KEYS_COLLECTION].find_one({"_id": oid})
    return serialize_doc(updated)


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: dict = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete API key"""
    oid = to_object_id(key_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    result = await db[API_KEYS_COLLECTION].delete_one({
        "_id": oid,
        "organization_id": current_user["organization_id"]
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    return {"message": "API key deleted successfully"}


@router.post("/{key_id}/test", response_model=APIKeyTestResponse)
async def test_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Test API key connection"""
    oid = to_object_id(key_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    api_key = await db[API_KEYS_COLLECTION].find_one({
        "_id": oid,
        "organization_id": current_user["organization_id"]
    })
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    try:
        decrypted_key = decrypt_api_key(api_key["encrypted_key"])
        provider = LLMProviderFactory.get_provider(api_key["provider"], decrypted_key)
        success = await provider.test_connection()
        if success:
            return {"success": True, "message": "Connection successful"}
        return {"success": False, "message": "Connection failed"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


@router.put("/{key_id}/set-default", response_model=APIKeyResponse)
async def set_default_api_key(
    key_id: str,
    current_user: dict = Depends(require_role([UserRole.OWNER, UserRole.ADMIN])),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Set API key as default for its provider"""
    oid = to_object_id(key_id)
    if not oid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    api_key = await db[API_KEYS_COLLECTION].find_one({
        "_id": oid,
        "organization_id": current_user["organization_id"]
    })
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")

    await db[API_KEYS_COLLECTION].update_many(
        {"organization_id": current_user["organization_id"], "provider": api_key["provider"]},
        {"$set": {"is_default": False}}
    )
    await db[API_KEYS_COLLECTION].update_one({"_id": oid}, {"$set": {"is_default": True}})

    updated = await db[API_KEYS_COLLECTION].find_one({"_id": oid})
    return serialize_doc(updated)
