from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from datetime import datetime
import uuid
from app.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)  # e.g., "MATH101", "PHY201"
    description = Column(Text)
    color = Column(String(20), default="#6366f1")  # Hex color for UI
    icon = Column(String(50), default="BookOpen")  # Lucide icon name
    user_id = Column(String, nullable=False)  # Owner of the subject
    
    # Academic details
    grade_level = Column(String(50))  # e.g., "S1", "S2", "A-Level"
    term = Column(String(20))  # e.g., "Term 1", "Term 2"
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