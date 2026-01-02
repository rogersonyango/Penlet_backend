# app/models/note.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid

class Note(Base):
    __tablename__ = "notes"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)
    curriculum = Column(String, index=True)  # e.g., "O-Level", "A-Level", "University"
    file_url = Column(String, nullable=True)
    author_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # pylint: disable=not-callable
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # pylint: disable=not-callable
    view_count = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)  # for Soft delete

    likes = relationship("NoteLike", back_populates="note", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="note", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="note", cascade="all, delete-orphan")


class NoteLike(Base):
    __tablename__ = "note_likes"
    user_id = Column(String, ForeignKey("users.id"), primary_key=True, index=True)  
    note_id = Column(String, ForeignKey("notes.id"), primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # pylint: disable=not-callable

    note = relationship("Note", back_populates="likes")


class Favorite(Base):
    __tablename__ = "favorites"
    user_id = Column(String, ForeignKey("users.id"), primary_key=True, index=True) 
    note_id = Column(String, ForeignKey("notes.id"), primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # pylint: disable=not-callable

    note = relationship("Note", back_populates="favorites")


class Comment(Base):
    __tablename__ = "comments"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    content = Column(Text, nullable=False)
    note_id = Column(String, ForeignKey("notes.id"), index=True, nullable=False)
    author_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)  # Also String
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # pylint: disable=not-callable
    is_deleted = Column(Boolean, default=False)  # Soft delete

    note = relationship("Note", back_populates="comments")
    # author = relationship("User")