from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    organization_name: str
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72, description="Password must be 8-72 characters")
    full_name: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot exceed 72 bytes when UTF-8 encoded')
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=72, description="Password must not exceed 72 characters")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot exceed 72 bytes when UTF-8 encoded')
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    role: str
    organization_id: str
    created_at: datetime


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    subscription_tier: str
    is_active: bool
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    organization: OrganizationResponse


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., max_length=72)
    new_password: str = Field(..., min_length=8, max_length=72)
