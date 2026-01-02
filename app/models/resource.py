# app/models/resource.py
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class ResourceCategory(Base):
    __tablename__ = "resource_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    file_path = Column(String)  # Path to .glb, .gltf, or .obj 
    file_format = Column(String)  # e.g., "glb", "gltf", "obj"
    subject = Column(String, index=True)
    category_id = Column(Integer, ForeignKey("resource_categories.id"))
    is_featured = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # pylint: disable=not-callable
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) # pylint: disable=not-callable

    category = relationship("ResourceCategory")