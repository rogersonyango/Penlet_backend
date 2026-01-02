# app/schemas/subject.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class SubjectBase(BaseModel):
    """Base subject schema."""
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None
    color: str = Field(default="#6366f1", pattern="^#[0-9A-Fa-f]{6}$")
    icon: str = Field(default="BookOpen", max_length=50)
    grade_level: Optional[str] = Field(None, max_length=50)
    term: Optional[str] = Field(None, max_length=20)
    teacher_name: Optional[str] = Field(None, max_length=100)

class SubjectCreate(SubjectBase):
    """Schema for creating a subject."""
    pass

class SubjectUpdate(BaseModel):
    """Schema for updating a subject."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)
    grade_level: Optional[str] = Field(None, max_length=50)
    term: Optional[str] = Field(None, max_length=20)
    teacher_name: Optional[str] = Field(None, max_length=100)
    is_favorite: Optional[bool] = None
    is_active: Optional[bool] = None

class SubjectResponse(BaseModel):
    """Schema for subject response."""
    id: str
    name: str
    code: str
    description: Optional[str]
    color: str
    icon: str
    user_id: str
    grade_level: Optional[str]
    term: Optional[str]
    teacher_name: Optional[str]
    notes_count: int
    quizzes_count: int
    videos_count: int
    is_active: bool
    is_favorite: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SubjectListResponse(BaseModel):
    """Schema for paginated subject list."""
    subjects: list[SubjectResponse]
    total: int
    page: int
    page_size: int

class SubjectStatsResponse(BaseModel):
    """Schema for subject statistics."""
    subject_id: str
    subject_name: str
    total_notes: int
    total_quizzes: int
    total_videos: int
    last_activity: Optional[datetime]
