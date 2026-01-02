# app/schemas/flashcard.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class FlashcardBase(BaseModel):
    """Base flashcard schema."""
    front: str = Field(..., min_length=1, max_length=1000)
    back: str = Field(..., min_length=1, max_length=1000)

class FlashcardCreate(FlashcardBase):
    """Schema for creating a flashcard."""
    deck_id: int

class FlashcardUpdate(BaseModel):
    """Schema for updating a flashcard."""
    front: Optional[str] = Field(None, min_length=1, max_length=1000)
    back: Optional[str] = Field(None, min_length=1, max_length=1000)

class FlashcardResponse(FlashcardBase):
    """Schema for flashcard response."""
    id: int
    deck_id: int
    next_review: datetime
    interval: int
    repetition: int
    ease_factor: float
    created_at: datetime

    class Config:
        from_attributes = True

class DeckBase(BaseModel):
    """Base deck schema."""
    title: str = Field(..., min_length=1, max_length=200)
    subject: Optional[str] = Field(None, max_length=100)
    level: Optional[str] = Field(None, max_length=50)
    is_public: bool = False

class DeckCreate(DeckBase):
    """Schema for creating a deck."""
    pass

class DeckUpdate(BaseModel):
    """Schema for updating a deck."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    subject: Optional[str] = Field(None, max_length=100)
    level: Optional[str] = Field(None, max_length=50)
    is_public: Optional[bool] = None

class DeckResponse(DeckBase):
    """Schema for deck response."""
    id: int
    share_token: Optional[str]
    created_at: datetime
    cards: List[FlashcardResponse] = []

    class Config:
        from_attributes = True

class ReviewUpdate(BaseModel):
    """Schema for updating flashcard review."""
    quality: int = Field(..., ge=0, le=5, description="Quality rating (0-5) for SM-2 algorithm")

class StudySessionResponse(BaseModel):
    """Schema for study session response."""
    deck_id: int
    cards_due: List[FlashcardResponse]
    total_cards: int

class StudyStatsResponse(BaseModel):
    """Schema for study statistics."""
    deck_id: int
    total_cards: int
    cards_due: int
    cards_learning: int
    cards_mastered: int
    average_ease_factor: float