#app/schemas/flashcard.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class FlashcardCreate(BaseModel):
    front: str
    back: str
    deck_id: int

class FlashcardUpdate(BaseModel):
    front: Optional[str] = None
    back: Optional[str] = None
    next_review: Optional[datetime] = None
    interval: Optional[int] = None
    repetition: Optional[int] = None
    ease_factor: Optional[float] = None

class Flashcard(FlashcardCreate):
    id: int
    next_review: datetime
    interval: int = 0
    repetition: int = 0
    ease_factor: float = 2.5
    created_at: datetime

    class Config:
        from_attributes = True

class DeckCreate(BaseModel):
    title: str
    subject: Optional[str] = None
    level: Optional[str] = None
    is_public: bool = False

class Deck(DeckCreate):
    id: int
    card_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

class ReviewUpdate(BaseModel):
    quality: int  # 0–5 rating (SM-2 algorithm)

class StudySession(BaseModel):
    deck_id: int
    cards: List[Flashcard]

class StudyStats(BaseModel):
    total_cards: int
    cards_due: int
    mastery_level: float  # e.g., avg ease_factor