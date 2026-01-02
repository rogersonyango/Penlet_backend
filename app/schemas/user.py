# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    user_type: str = Field(default="student", pattern="^(student|teacher|admin)$")

class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Ensure password has minimum complexity."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    user_type: Optional[str] = Field(None, pattern="^(student|teacher|admin)$")

class UserResponse(BaseModel):
    """Schema for user data in responses."""
    id: str
    email: str
    username: str
    full_name: Optional[str]
    user_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse