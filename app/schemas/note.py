# app/schemas/note.py
from pydantic import BaseModel, validator
from typing import Optional, List, Literal
from datetime import datetime

class NoteBase(BaseModel):
    title: str
    content: str
    curriculum: str

class NoteCreate(NoteBase):
    file_url: Optional[str] = None

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    curriculum: Optional[str] = None
    file_url: Optional[str] = None

class NoteOut(NoteBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    view_count: int
    file_url: Optional[str] = None

    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class CommentOut(CommentBase):
    id: int
    author_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class LikeToggleResponse(BaseModel):
    liked: bool
    total_likes: int

class FavoriteToggleResponse(BaseModel):
    favorited: bool