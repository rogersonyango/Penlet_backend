from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class QuestionSchema(BaseModel):
    """Schema for a quiz question."""
    id: str
    text: str = Field(..., min_length=1)
    type: str = Field(..., pattern="^(multiple_choice|true_false|short_answer)$")
    options: Optional[List[str]] = None
    correct_answer: str

    @field_validator('options')
    @classmethod
    def validate_options(cls, v: Optional[List[str]], info) -> Optional[List[str]]:
        """Ensure multiple choice questions have options."""
        if info.data.get('type') == 'multiple_choice' and (v is None or len(v) < 2):
            raise ValueError('Multiple choice questions must have at least 2 options')
        return v

class QuizBase(BaseModel):
    """Base quiz schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    curriculum: str = Field(..., min_length=1, max_length=100)
    time_limit_minutes: int = Field(default=30, ge=1, le=180)
    questions: List[QuestionSchema] = Field(..., min_length=1)

class QuizCreate(QuizBase):
    """Schema for creating a quiz."""
    pass

class QuizUpdate(BaseModel):
    """Schema for updating a quiz."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    curriculum: Optional[str] = Field(None, min_length=1, max_length=100)
    time_limit_minutes: Optional[int] = Field(None, ge=1, le=180)
    questions: Optional[List[QuestionSchema]] = Field(None, min_length=1)
    is_active: Optional[bool] = None

class QuizResponse(QuizBase):
    """Schema for quiz response."""
    id: int
    created_by: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class QuizAttemptStart(BaseModel):
    """Schema for starting a quiz attempt."""
    pass

class AnswerSubmit(BaseModel):
    """Schema for submitting an answer."""
    question_id: str
    answer: Any

class AttemptSubmit(BaseModel):
    """Schema for submitting quiz attempt."""
    answers: Dict[str, Any] = Field(..., min_length=1)

class QuizAttemptResponse(BaseModel):
    """Schema for quiz attempt response."""
    id: int
    quiz_id: int
    user_id: str
    start_time: datetime
    end_time: Optional[datetime]
    is_submitted: bool
    score: Optional[float]
    max_score: Optional[float]
    answers: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True
