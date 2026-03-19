from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from bson import ObjectId
from app.models.user import UserRole, USERS_COLLECTION
from app.models.organization import ORGANIZATIONS_COLLECTION
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.database import serialize_doc


class AuthService:
    """Service for authentication operations"""

    @staticmethod
    async def register_organization(
        name: str,
        email: str,
        password: str,
        full_name: str,
        db: AsyncIOMotorDatabase
    ) -> dict:
        """Register a new organization with owner user"""
        existing_user = await db[USERS_COLLECTION].find_one({"email": email})
        if existing_user:
            raise ValueError("Email already registered")

        slug = name.lower().replace(" ", "-").replace("_", "-")
        base_slug = slug
        counter = 1
        while await db[ORGANIZATIONS_COLLECTION].find_one({"slug": slug}):
            slug = f"{base_slug}-{counter}"
            counter += 1

        now = datetime.utcnow()
        org_doc = {
            "name": name,
            "slug": slug,
            "subscription_tier": "free",
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        org_result = await db[ORGANIZATIONS_COLLECTION].insert_one(org_doc)
        org_id = org_result.inserted_id

        hashed_password = get_password_hash(password)
        user_doc = {
            "email": email,
            "hashed_password": hashed_password,
            "full_name": full_name,
            "role": UserRole.OWNER.value,
            "organization_id": str(org_id),
            "created_at": now,
            "last_login": None
        }
        user_result = await db[USERS_COLLECTION].insert_one(user_doc)
        user_id = user_result.inserted_id

        access_token = create_access_token(data={"sub": str(user_id)})

        user_data = {**user_doc, "id": str(user_id)}
        org_data = {**org_doc, "id": str(org_id)}

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_data,
            "organization": org_data
        }

    @staticmethod
    async def login(
        email: str,
        password: str,
        db: AsyncIOMotorDatabase
    ) -> dict:
        """Authenticate user and return token"""
        user_doc = await db[USERS_COLLECTION].find_one({"email": email})

        if not user_doc or not verify_password(password, user_doc["hashed_password"]):
            raise ValueError("Invalid email or password")

        org_doc = await db[ORGANIZATIONS_COLLECTION].find_one(
            {"_id": ObjectId(user_doc["organization_id"])}
        )
        if not org_doc or not org_doc.get("is_active", True):
            raise ValueError("Organization is inactive")

        await db[USERS_COLLECTION].update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )

        access_token = create_access_token(data={"sub": str(user_doc["_id"])})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": serialize_doc(user_doc),
            "organization": serialize_doc(org_doc)
        }

    @staticmethod
    async def create_user(
        email: str,
        password: str,
        full_name: str,
        role: UserRole,
        organization_id: str,
        db: AsyncIOMotorDatabase
    ) -> dict:
        """Create a new user in an organization"""
        existing_user = await db[USERS_COLLECTION].find_one({"email": email})
        if existing_user:
            raise ValueError("Email already registered")

        hashed_password = get_password_hash(password)
        now = datetime.utcnow()
        user_doc = {
            "email": email,
            "hashed_password": hashed_password,
            "full_name": full_name,
            "role": role.value,
            "organization_id": organization_id,
            "created_at": now,
            "last_login": None
        }
        result = await db[USERS_COLLECTION].insert_one(user_doc)
        return {**user_doc, "id": str(result.inserted_id)}

    @staticmethod
    async def update_password(
        user_id: str,
        old_password: str,
        new_password: str,
        db: AsyncIOMotorDatabase
    ) -> bool:
        """Update user password"""
        user_doc = await db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})

        if not user_doc or not verify_password(old_password, user_doc["hashed_password"]):
            raise ValueError("Invalid old password")

        await db[USERS_COLLECTION].update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"hashed_password": get_password_hash(new_password)}}
        )
        return True
