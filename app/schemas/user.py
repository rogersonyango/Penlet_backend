from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from typing import Optional, List

# Valid class levels for students
VALID_CLASSES = ["S1", "S2", "S3", "S4", "S5", "S6"]

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str = None
    user_type: str = "student"
    student_class: Optional[str] = None  # Required for students, null for teachers/admins
    
    @field_validator('student_class')
    @classmethod
    def validate_student_class(cls, v, info):
        """Validate student_class field"""
        # Get user_type from the data being validated
        user_type = info.data.get('user_type', 'student') if info.data else 'student'
        if user_type == 'student':
            if not v:
                raise ValueError('Student class is required for students')
            if v not in VALID_CLASSES:
                raise ValueError(f'Invalid class. Must be one of: {", ".join(VALID_CLASSES)}')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    student_class: Optional[str] = None
    profile_image: Optional[str] = None
    
    @field_validator('student_class')
    @classmethod
    def validate_student_class(cls, v):
        """Validate student_class field"""
        if v and v not in VALID_CLASSES:
            raise ValueError(f'Invalid class. Must be one of: {", ".join(VALID_CLASSES)}')
        return v

class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str = None
    user_type: str
    student_class: Optional[str] = None
    profile_image: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse