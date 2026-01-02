from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

# Valid class levels
VALID_CLASSES = ["S1", "S2", "S3", "S4", "S5", "S6"]

class ContentType(str, Enum):
    NOTE = "note"
    VIDEO = "video"
    ASSIGNMENT = "assignment"
    QUIZ = "quiz"

class ContentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ContentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    type: ContentType
    class_level: str  # S1, S2, S3, S4, S5, S6
    subject_id: str
    file_url: Optional[str] = None  # For YouTube videos
    
    @field_validator('class_level')
    @classmethod
    def validate_class_level(cls, v):
        """Validate class_level field"""
        if v not in VALID_CLASSES:
            raise ValueError(f'Invalid class level. Must be one of: {", ".join(VALID_CLASSES)}')
        return v

class ContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[ContentType] = None
    class_level: Optional[str] = None
    subject_id: Optional[str] = None
    file_url: Optional[str] = None
    status: Optional[ContentStatus] = None
    
    @field_validator('class_level')
    @classmethod
    def validate_class_level(cls, v):
        """Validate class_level field"""
        if v and v not in VALID_CLASSES:
            raise ValueError(f'Invalid class level. Must be one of: {", ".join(VALID_CLASSES)}')
        return v

class ContentResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    type: ContentType
    class_level: str
    subject_id: str
    file_path: Optional[str]
    file_url: Optional[str]
    file_size: Optional[int]
    file_type: Optional[str]
    status: ContentStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ContentListResponse(BaseModel):
    content: List[ContentResponse]
    total: int
    page: int
    page_size: int