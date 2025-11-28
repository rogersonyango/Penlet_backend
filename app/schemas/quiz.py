from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class QuizBase(BaseModel):
    title: str
    description: Optional[str] = None
    curriculum: str
    time_limit_minutes: Optional[int] = 30
    questions: List[Dict[str, Any]]

class QuizCreate(QuizBase):
    pass

class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    curriculum: Optional[str] = None
    time_limit_minutes: Optional[int] = None
    questions: Optional[List[Dict[str, Any]]] = None

class QuizOut(QuizBase):
    id: int
    created_by: str
    is_active: bool

    class Config:
        from_attributes = True

class QuizAttemptStart(BaseModel):
    user_id: str

class AnswerSubmit(BaseModel):
    question_id: str
    answer: Any

class AttemptSubmit(BaseModel):
    answers: Dict[str, Any]  # Optional if auto-saved incrementally

class QuizAttemptOut(BaseModel):
    id: int
    quiz_id: int
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    is_submitted: bool
    score: Optional[float] = None
    max_score: Optional[float] = None

    class Config:
        from_attributes = True