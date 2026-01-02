from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float
from datetime import datetime
import uuid
from app.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    video_url = Column(String(500), nullable=False)  # URL to video file or YouTube/Vimeo link
    thumbnail_url = Column(String(500))  # URL to thumbnail image
    
    # Categorization
    subject_id = Column(String)  # Link to subjects table
    subject_name = Column(String(100))  # Denormalized for quick access
    topic = Column(String(100))
    tags = Column(String(500))  # Comma-separated tags
    
    # Video metadata
    duration = Column(Integer, default=0)  # Duration in seconds
    file_size = Column(Integer)  # File size in bytes
    video_type = Column(String(50), default="upload")  # 'upload', 'youtube', 'vimeo', etc.
    quality = Column(String(20))  # '720p', '1080p', '4K', etc.
    
    # User tracking
    user_id = Column(String, nullable=False)
    
    # Statistics
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)  # Average completion rate (0-100)
    
    # Settings
    is_public = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VideoProgress(Base):
    """Track user progress for each video"""
    __tablename__ = "video_progress"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    video_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    
    # Progress tracking
    watched_duration = Column(Integer, default=0)  # Seconds watched
    completion_percentage = Column(Float, default=0.0)  # 0-100
    is_completed = Column(Boolean, default=False)
    
    # Timestamps
    last_watched_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class VideoLike(Base):
    """Track video likes"""
    __tablename__ = "video_likes"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    video_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class VideoComment(Base):
    """Video comments"""
    __tablename__ = "video_comments"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    video_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)