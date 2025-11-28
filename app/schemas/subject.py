from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SubjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None
    color: str = "#6366f1"
    icon: str = "BookOpen"
    grade_level: Optional[str] = None
    term: Optional[str] = None
    teacher_name: Optional[str] = None
    is_favorite: bool = False

class SubjectCreate(SubjectBase):
    pass

class SubjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    grade_level: Optional[str] = None
    term: Optional[str] = None
    teacher_name: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_active: Optional[bool] = None

class SubjectResponse(BaseModel):
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
    subjects: list[SubjectResponse]
    total: int
    page: int
    page_size: int

class SubjectStatsResponse(BaseModel):
    subject_id: str
    subject_name: str
    total_notes: int
    total_quizzes: int
    total_videos: int
    last_activity: Optional[datetime]