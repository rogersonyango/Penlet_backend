#app/models/flashcard.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import secrets
from app.db.session import Base  # Assume you have a database.py

class Deck(Base):
    __tablename__ = "decks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    subject = Column(String, index=True)
    level = Column(String, index=True)
    is_public = Column(Boolean, default=False)
    share_token = Column(String, unique=True, nullable=True)  # Optional: for private share links
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=not-callable
    cards = relationship("Flashcard", back_populates="deck", cascade="all, delete-orphan")



    def generate_share_token(self):
        """Generate a secure, random share token."""
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(16)

class Flashcard(Base):
    __tablename__ = "flashcards"
    id = Column(Integer, primary_key=True, index=True)
    front = Column(String)
    back = Column(String)
    deck_id = Column(Integer, ForeignKey("decks.id", ondelete="CASCADE"))
    next_review = Column(DateTime(timezone=True), default=func.now()) # pylint: disable=not-callable
    interval = Column(Integer, default=0)
    repetition = Column(Integer, default=0)
    ease_factor = Column(Float, default=2.5)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=not-callable
    deck = relationship("Deck", back_populates="cards")