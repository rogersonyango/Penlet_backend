# app/schemas/note.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class NoteBase(BaseModel):
    """Base note schema."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    curriculum: str = Field(..., min_length=1, max_length=100)

class NoteCreate(NoteBase):
    """Schema for creating a note."""
    file_url: Optional[str] = Field(None, max_length=500)

class NoteUpdate(BaseModel):
    """Schema for updating a note."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    curriculum: Optional[str] = Field(None, min_length=1, max_length=100)
    file_url: Optional[str] = Field(None, max_length=500)

class NoteResponse(NoteBase):
    """Schema for note response."""
    id: int
    author_id: str
    file_url: Optional[str]
    view_count: int
    is_deleted: bool
    created_at: datetime
    updated_at: Optional[datetime]
    like_count: int = 0
    comment_count: int = 0

    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    """Base comment schema."""
    content: str = Field(..., min_length=1, max_length=1000)

class CommentCreate(CommentBase):
    """Schema for creating a comment."""
    pass

class CommentUpdate(BaseModel):
    """Schema for updating a comment."""
    content: str = Field(..., min_length=1, max_length=1000)

class CommentResponse(CommentBase):
    """Schema for comment response."""
    id: int
    note_id: int
    author_id: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True

class LikeToggleResponse(BaseModel):
    """Schema for like toggle response."""
    liked: bool
    total_likes: int

class FavoriteToggleResponse(BaseModel):
    """Schema for favorite toggle response."""
    favorited: bool