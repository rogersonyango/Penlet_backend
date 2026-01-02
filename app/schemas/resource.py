from pydantic import BaseModel, field_validator, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class ResourceCategoryBase(BaseModel):
    """Base schema for resource category."""
    name: str = Field(..., min_length=1, max_length=100)

class ResourceCategoryCreate(ResourceCategoryBase):
    """Schema for creating a resource category."""
    pass

class ResourceCategoryResponse(ResourceCategoryBase):
    """Schema for resource category response."""
    id: int

    model_config = ConfigDict(from_attributes=True)

class ResourceBase(BaseModel):
    """Base schema for 3D resources."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    subject: str = Field(..., min_length=1, max_length=100)
    category_id: int
    is_featured: bool = False

class ResourceCreate(ResourceBase):
    """Schema for creating a new 3D resource."""
    file_format: str

    @field_validator('file_format')
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate file format."""
        allowed = {"glb", "gltf", "obj"}
        if v.lower() not in allowed:
            raise ValueError(f"Format must be one of {allowed}")
        return v.lower()

class ResourceUpdate(BaseModel):
    """Schema for updating an existing 3D resource."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    subject: Optional[str] = Field(None, min_length=1, max_length=100)
    category_id: Optional[int] = None
    is_featured: Optional[bool] = None

class ResourceResponse(ResourceBase):
    """Schema for resource response."""
    id: int
    file_path: str
    file_format: str
    view_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class ResourceListResponse(BaseModel):
    """Schema for paginated resource list."""
    items: List[ResourceResponse]
    total: int
    page: int
    page_size: int