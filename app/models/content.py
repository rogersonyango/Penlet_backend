from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

# Valid class levels
VALID_CLASSES = ["S1", "S2", "S3", "S4", "S5", "S6"]

class Content(Base):
    __tablename__ = "content"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False)  # note, video, assignment, quiz
    
    # Class and Subject relationship
    class_level = Column(String(10), nullable=False)  # S1, S2, S3, S4, S5, S6
    subject_id = Column(String, ForeignKey("subjects.id", ondelete="CASCADE"))
    
    # File information
    file_path = Column(String(500))  # Local file path
    file_url = Column(String(500))   # External URL (e.g., YouTube)
    file_size = Column(BigInteger)   # File size in bytes
    file_type = Column(String(100))  # MIME type
    
    # Status and approval
    status = Column(String(20), default="pending")  # pending, approved, rejected
    
    # Creator information
    created_by = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # subject = relationship("Subject", back_populates="content")
    # creator = relationship("User", back_populates="created_content")

class ContentAccess(Base):
    """Track who has viewed which content"""
    __tablename__ = "content_access"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    content_id = Column(String, ForeignKey("content.id", ondelete="CASCADE"))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    viewed_at = Column(DateTime, default=datetime.utcnow)