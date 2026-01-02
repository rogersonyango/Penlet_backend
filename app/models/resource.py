# app/models/resource.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, text
from sqlalchemy.orm import relationship
from app.db.session import Base

class ResourceCategory(Base):
    __tablename__ = "resource_categories"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Category Information
    name = Column(String, unique=True, index=True, nullable=False)
    
    # Relationships
    resources = relationship("Resource", back_populates="category", cascade="all, delete-orphan")


class Resource(Base):
    __tablename__ = "resources"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key
    category_id = Column(Integer, ForeignKey("resource_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Resource Information
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String, nullable=False)
    file_format = Column(String, nullable=False)
    subject = Column(String, index=True)
    is_featured = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    category = relationship("ResourceCategory", back_populates="resources")
