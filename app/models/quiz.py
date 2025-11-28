from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    curriculum = Column(String, index=True)  # e.g., "Uganda UCE Biology"
    time_limit_minutes = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    questions = Column(JSON)  # List of questions like {id, text, type, options, correct_answer}
    created_by = Column(String)  # e.g., "teacher@gmail.com" or the name

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    user_id = Column(Integer, index=True)  
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    is_submitted = Column(Boolean, default=False)
    answers = Column(JSON)  # {question_id: answer}
    score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)