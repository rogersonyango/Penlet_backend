# app/models/note.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, func, text
from sqlalchemy.orm import relationship
from app.db.session import Base

class Note(Base):
    __tablename__ = "notes"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key
    author_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Note Information
    title = Column(String, index=True, nullable=False)
    content = Column(Text, nullable=False)
    curriculum = Column(String, index=True)
    file_url = Column(String, nullable=True)
    view_count = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(timezone=True), server_onupdate=text('CURRENT_TIMESTAMP'))

    # Relationships
    author = relationship("User", back_populates="notes")
    likes = relationship("NoteLike", back_populates="note", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="note", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="note", cascade="all, delete-orphan")


class NoteLike(Base):
    __tablename__ = "note_likes"
    
    # Composite Primary Key
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    user = relationship("User", back_populates="note_likes")
    note = relationship("Note", back_populates="likes")


class Favorite(Base):
    __tablename__ = "favorites"
    
    # Composite Primary Key
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    note = relationship("Note", back_populates="favorites")


class Comment(Base):
    __tablename__ = "comments"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    note_id = Column(Integer, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Comment Information
    content = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    note = relationship("Note", back_populates="comments")
    author = relationship("User", back_populates="comments")