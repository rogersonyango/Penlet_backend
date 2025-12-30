from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from datetime import datetime
import uuid
from app.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

# Valid class levels
VALID_CLASSES = ["S1", "S2", "S3", "S4", "S5", "S6"]

class Subject(Base):
    __tablename__ = "subjects"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)  # e.g., "MATH-S1", "PHY-S3"
    description = Column(Text)
    color = Column(String(20), default="#6366f1")  # Hex color for UI
    icon = Column(String(50), default="BookOpen")  # Lucide icon name
    
    # Class level - which class this subject is for
    class_level = Column(String(10), nullable=False)  # S1, S2, S3, S4, S5, S6
    
    # Teacher assignment
    teacher_id = Column(String, nullable=True)  # Assigned teacher
    teacher_name = Column(String(100))
    
    # Academic details
    term = Column(String(20))  # e.g., "Term 1", "Term 2", "Term 3"
    
    # Statistics
    notes_count = Column(Integer, default=0)
    quizzes_count = Column(Integer, default=0)
    videos_count = Column(Integer, default=0)
    
    # Settings
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)