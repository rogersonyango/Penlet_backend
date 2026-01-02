# app/models/quiz.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class Quiz(Base):
    __tablename__ = "quizzes"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Quiz Information
    title = Column(String, index=True, nullable=False)
    description = Column(String)
    curriculum = Column(String, index=True)
    time_limit_minutes = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    questions = Column(JSON, nullable=False)
    created_by = Column(String, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    quiz_id = Column(Integer, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Attempt Information
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    is_submitted = Column(Boolean, default=False)
    answers = Column(JSON)
    score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    
    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    user = relationship("User", back_populates="quiz_attempts")
