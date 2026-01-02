# app/models/video.py
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class Video(Base):
    __tablename__ = "videos"
    
    # Primary Key
    id = Column(String, primary_key=True, default=generate_uuid)
    
    # Foreign Keys
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(String, ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Video Information
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    video_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500))
    subject_name = Column(String(100))
    topic = Column(String(100))
    tags = Column(String(500))
    
    # Video Metadata
    duration = Column(Integer, default=0)
    file_size = Column(Integer)
    video_type = Column(String(50), default="upload")
    quality = Column(String(20))
    
    # Statistics
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)
    
    # Settings
    is_public = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="videos")
    progress_records = relationship("VideoProgress", back_populates="video", cascade="all, delete-orphan")
    likes = relationship("VideoLike", back_populates="video", cascade="all, delete-orphan")
    comments = relationship("VideoComment", back_populates="video", cascade="all, delete-orphan")


class VideoProgress(Base):
    __tablename__ = "video_progress"
    
    # Primary Key
    id = Column(String, primary_key=True, default=generate_uuid)
    
    # Foreign Keys
    video_id = Column(String, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Progress Information
    watched_duration = Column(Integer, default=0)
    completion_percentage = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    
    # Timestamps
    last_watched_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    video = relationship("Video", back_populates="progress_records")
    user = relationship("User", back_populates="video_progress")


class VideoLike(Base):
    __tablename__ = "video_likes"
    
    # Primary Key
    id = Column(String, primary_key=True, default=generate_uuid)
    
    # Foreign Keys
    video_id = Column(String, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    video = relationship("Video", back_populates="likes")
    user = relationship("User", back_populates="video_likes")


class VideoComment(Base):
    __tablename__ = "video_comments"
    
    # Primary Key
    id = Column(String, primary_key=True, default=generate_uuid)
    
    # Foreign Keys
    video_id = Column(String, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Comment Information
    content = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    video = relationship("Video", back_populates="comments")
    user = relationship("User", back_populates="video_comments")
