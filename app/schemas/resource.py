# app/schemas/resource.py
from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime

class ResourceCategoryBase(BaseModel):
    """Base schema for resource category."""
    name: str

class ResourceCategory(ResourceCategoryBase):
    """Schema for reading a resource category."""
    id: int

    model_config = ConfigDict(from_attributes=True)

class ResourceBase(BaseModel):
    """Base schema for 3D resources."""
    title: str
    description: Optional[str] = None
    subject: str
    category_id: int
    is_featured: Optional[bool] = False

class ResourceCreate(ResourceBase):
    """Schema for creating a new 3D resource."""
    file_format: str

    @field_validator('file_format')
    @classmethod
    def valid_format(cls, v: str) -> str:
        """Validate that the file format is allowed (glb, gltf, obj)."""
        allowed = {"glb", "gltf", "obj"}
        if v.lower() not in allowed:
            raise ValueError(f"Format must be one of {allowed}")
        return v.lower()

class ResourceUpdate(BaseModel):
    """Schema for updating an existing 3D resource."""
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    category_id: Optional[int] = None
    is_featured: Optional[bool] = None

class Resource(ResourceBase):
    """Schema for reading a full 3D resource."""
    id: int
    file_format: str
    view_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ResourceList(BaseModel):
    """Schema for paginated list of resources."""
    items: List[Resource]
    total: int
    page: int
    size: int