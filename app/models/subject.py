# app/models/subject.py
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class Subject(Base):
    __tablename__ = "subjects"
    
    # Primary Key
    id = Column(String, primary_key=True, default=generate_uuid)
    
    # Foreign Key
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Subject Information
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    description = Column(Text)
    color = Column(String(20), default="#6366f1")
    icon = Column(String(50), default="BookOpen")
    
    # Academic Details
    grade_level = Column(String(50))
    term = Column(String(20))
    teacher_name = Column(String(100))
    
    # Statistics
    notes_count = Column(Integer, default=0)
    quizzes_count = Column(Integer, default=0)
    videos_count = Column(Integer, default=0)
    
    # Settings
    is_active = Column(Boolean, default=True)
    is_favorite = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="subjects")