# app/schemas/video.py
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime

class VideoBase(BaseModel):
    """Base video schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    video_url: str = Field(..., min_length=1, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    subject_id: Optional[str] = None
    subject_name: Optional[str] = Field(None, max_length=100)
    topic: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=500)
    duration: int = Field(default=0, ge=0)
    file_size: Optional[int] = Field(None, ge=0)
    video_type: str = Field(default="upload", pattern="^(upload|youtube|vimeo|external)$")
    quality: Optional[str] = Field(None, pattern="^(360p|480p|720p|1080p|4K)$")
    is_public: bool = False
    is_favorite: bool = False

class VideoCreate(VideoBase):
    """Schema for creating a video."""
    pass

class VideoUpdate(BaseModel):
    """Schema for updating a video."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    video_url: Optional[str] = Field(None, min_length=1, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    subject_id: Optional[str] = None
    subject_name: Optional[str] = Field(None, max_length=100)
    topic: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=500)
    duration: Optional[int] = Field(None, ge=0)
    file_size: Optional[int] = Field(None, ge=0)
    video_type: Optional[str] = Field(None, pattern="^(upload|youtube|vimeo|external)$")
    quality: Optional[str] = Field(None, pattern="^(360p|480p|720p|1080p|4K)$")
    is_public: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_featured: Optional[bool] = None

class VideoResponse(BaseModel):
    """Schema for video response."""
    id: str
    title: str
    description: Optional[str]
    video_url: str
    thumbnail_url: Optional[str]
    subject_id: Optional[str]
    subject_name: Optional[str]
    topic: Optional[str]
    tags: Optional[str]
    duration: int
    file_size: Optional[int]
    video_type: str
    quality: Optional[str]
    user_id: str
    view_count: int
    like_count: int
    completion_rate: float
    is_public: bool
    is_favorite: bool
    is_featured: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class VideoListResponse(BaseModel):
    """Schema for paginated video list."""
    videos: List[VideoResponse]
    total: int
    page: int
    page_size: int

class ProgressUpdate(BaseModel):
    """Schema for updating video progress."""
    watched_duration: int = Field(..., ge=0)
    completion_percentage: float = Field(..., ge=0.0, le=100.0)

class ProgressResponse(BaseModel):
    """Schema for video progress response."""
    id: str
    video_id: str
    user_id: str
    watched_duration: int
    completion_percentage: float
    is_completed: bool
    last_watched_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class VideoCommentCreate(BaseModel):
    """Schema for creating a video comment."""
    content: str = Field(..., min_length=1, max_length=1000)

class VideoCommentResponse(BaseModel):
    """Schema for video comment response."""
    id: str
    video_id: str
    user_id: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class VideoLikeResponse(BaseModel):
    """Schema for video like response."""
    liked: bool
    like_count: int
