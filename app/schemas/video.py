from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime

class VideoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    video_url: str = Field(..., min_length=1, max_length=500)
    thumbnail_url: Optional[str] = None
    subject_id: Optional[str] = None
    subject_name: Optional[str] = None
    topic: Optional[str] = None
    tags: Optional[str] = None
    duration: int = 0
    file_size: Optional[int] = None
    video_type: str = "upload"
    quality: Optional[str] = None
    is_public: bool = False
    is_favorite: bool = False

class VideoCreate(VideoBase):
    pass

class VideoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    subject_id: Optional[str] = None
    subject_name: Optional[str] = None
    topic: Optional[str] = None
    tags: Optional[str] = None
    duration: Optional[int] = None
    file_size: Optional[int] = None
    video_type: Optional[str] = None
    quality: Optional[str] = None
    is_public: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_featured: Optional[bool] = None

class VideoResponse(BaseModel):
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
    videos: list[VideoResponse]
    total: int
    page: int
    page_size: int

# Progress schemas
class ProgressUpdate(BaseModel):
    watched_duration: int
    completion_percentage: float

class ProgressResponse(BaseModel):
    id: str
    video_id: str
    user_id: str
    watched_duration: int
    completion_percentage: float
    is_completed: bool
    last_watched_at: datetime
    
    class Config:
        from_attributes = True

# Comment schemas
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1)

class CommentResponse(BaseModel):
    id: str
    video_id: str
    user_id: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Like response
class LikeResponse(BaseModel):
    liked: bool
    like_count: int