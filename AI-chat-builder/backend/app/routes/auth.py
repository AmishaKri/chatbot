from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse, UserResponse, UpdateProfileRequest, ChangePasswordRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Register a new organization and owner user"""
    try:
        result = await AuthService.register_organization(
            name=request.organization_name,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            db=db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # Log the actual error for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please check your input and try again."
        )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Login and get access token"""
    try:
        result = await AuthService.login(
            email=request.email,
            password=request.password,
            db=db
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        # Log the actual error for debugging
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update current user profile"""
    from app.models.user import USERS_COLLECTION
    from app.core.database import to_object_id
    update_fields = {}
    if request.full_name is not None:
        update_fields["full_name"] = request.full_name
    if update_fields:
        oid = to_object_id(current_user["id"])
        await db[USERS_COLLECTION].update_one({"_id": oid}, {"$set": update_fields})
        current_user.update(update_fields)
    return current_user


@router.put("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Change current user password"""
    try:
        await AuthService.update_password(
            user_id=current_user["id"],
            old_password=request.current_password,
            new_password=request.new_password,
            db=db
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_active_user)):
    """Logout (client-side token removal)"""
    return {"message": "Logged out successfully"}
