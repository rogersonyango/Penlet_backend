# app/models/flashcard.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, text
from sqlalchemy.orm import relationship
import secrets
from app.db.session import Base

class Deck(Base):
    __tablename__ = "decks"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Deck Information
    title = Column(String, index=True, nullable=False)
    subject = Column(String, index=True)
    level = Column(String, index=True)
    is_public = Column(Boolean, default=False)
    share_token = Column(String, unique=True, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    cards = relationship("Flashcard", back_populates="deck", cascade="all, delete-orphan")

    def generate_share_token(self):
        """Generate a secure, random share token."""
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(16)


class Flashcard(Base):
    __tablename__ = "flashcards"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key
    deck_id = Column(Integer, ForeignKey("decks.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Flashcard Information
    front = Column(String, nullable=False)
    back = Column(String, nullable=False)
    
    # Spaced Repetition Data
    next_review = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    interval = Column(Integer, default=0)
    repetition = Column(Integer, default=0)
    ease_factor = Column(Float, default=2.5)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    deck = relationship("Deck", back_populates="cards")
