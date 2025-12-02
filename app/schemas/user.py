#app/schemas/user.py

from pydantic import BaseModel, EmailStr, computed_field
from typing import Optional, List
from enum import Enum
from datetime import datetime

class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

# Input schemas
class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str

class UserCreate(UserBase):
    password: Optional[str] = None
    role: UserRole
    user_class: Optional[str] = None   # for students
    subject: Optional[str] = None      # for teachers

class UserCreateByAdmin(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    user_class: Optional[str] = None
    subject: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    user_class: Optional[str] = None
    subject: Optional[str] = None

class TokenRefresh(BaseModel):
    refresh_token: str

# Output schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str  # UUID as string
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole
    is_verified: bool
    user_class: Optional[str] = None
    subject: Optional[str] = None
    # Optional: include security fields if needed (not recommended in public API)
    
    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    class Config:
        from_attributes = True

