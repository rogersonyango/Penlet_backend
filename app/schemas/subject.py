from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

# Valid class levels
VALID_CLASSES = ["S1", "S2", "S3", "S4", "S5", "S6"]

class SubjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None
    color: str = "#6366f1"
    icon: str = "BookOpen"
    class_level: str  # S1, S2, S3, S4, S5, S6
    term: Optional[str] = None
    teacher_name: Optional[str] = None
    teacher_id: Optional[str] = None
    
    @field_validator('class_level')
    @classmethod
    def validate_class_level(cls, v):
        """Validate class_level field"""
        if v not in VALID_CLASSES:
            raise ValueError(f'Invalid class level. Must be one of: {", ".join(VALID_CLASSES)}')
        return v

class SubjectCreate(SubjectBase):
    pass

class SubjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    class_level: Optional[str] = None
    term: Optional[str] = None
    teacher_name: Optional[str] = None
    teacher_id: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator('class_level')
    @classmethod
    def validate_class_level(cls, v):
        """Validate class_level field"""
        if v and v not in VALID_CLASSES:
            raise ValueError(f'Invalid class level. Must be one of: {", ".join(VALID_CLASSES)}')
        return v

class SubjectResponse(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str]
    color: str
    icon: str
    class_level: str
    term: Optional[str]
    teacher_name: Optional[str]
    teacher_id: Optional[str]
    notes_count: int
    quizzes_count: int
    videos_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SubjectListResponse(BaseModel):
    subjects: List[SubjectResponse]
    total: int
    page: int
    page_size: int

class SubjectStatsResponse(BaseModel):
    subject_id: str
    subject_name: str
    class_level: str
    total_notes: int
    total_quizzes: int
    total_videos: int
    last_activity: Optional[datetime]