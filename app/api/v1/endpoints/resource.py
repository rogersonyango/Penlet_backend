"""
3D Resource API endpoints for listing, uploading, retrieving, updating, and deleting 3D educational resources.
Supports advanced filtering (title, description, format, featured, date ranges), search, and pagination.
"""

import os
from datetime import datetime
from pathlib import Path
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Query,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

# ✅ Correct imports - using the actual schema classes
from app.schemas.resource import (
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
    ResourceListResponse,
    ResourceCategoryResponse
)
from app.crud.resource import (
    get_resources,
    count_resources,
    create_resource,
    get_resource as crud_get_resource,
    update_resource,
    delete_resource as crud_delete_resource,
    increment_view_count,
    get_categories as crud_get_categories,
    search_resources,
    get_featured_resources
)
from app.db.session import get_db

UPLOAD_DIR = Path("uploads/3d")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/api/3d-resources", tags=["3D Resources"])


@router.get("/", response_model=ResourceListResponse)
def list_resources(
    title: Optional[str] = Query(None, description="Partial match on title"),
    description: Optional[str] = Query(None, description="Partial match on description"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    category_id: Optional[int] = Query(None, description="Category ID"),
    file_format: Optional[str] = Query(None, description="File format: glb, gltf, or obj"),
    is_featured: Optional[bool] = Query(None, description="Only featured resources"),
    created_after: Optional[str] = Query(None, description="ISO 8601: 2025-01-01T00:00:00"),
    created_before: Optional[str] = Query(None, description="ISO 8601 datetime"),
    page: int = Query(1, ge=1, description="Page number (≥1)"),
    size: int = Query(10, ge=1, le=100, description="Items per page (1–100)"),
    db: Session = Depends(get_db),
) -> ResourceListResponse:
    """List 3D resources with advanced filtering and pagination."""
    # Parse datetime strings
    after_dt = None
    before_dt = None
    if created_after:
        try:
            after_dt = datetime.fromisoformat(created_after.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid 'created_after' datetime format")
    if created_before:
        try:
            before_dt = datetime.fromisoformat(created_before.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid 'created_before' datetime format")

    skip = (page - 1) * size
    resources = get_resources(
        db,
        skip=skip,
        limit=size,
        title=title,
        description=description,
        subject=subject,
        category_id=category_id,
        file_format=file_format,
        is_featured=is_featured,
        created_after=after_dt,
        created_before=before_dt,
    )
    total = count_resources(
        db,
        title=title,
        description=description,
        subject=subject,
        category_id=category_id,
        file_format=file_format,
        is_featured=is_featured,
        created_after=after_dt,
        created_before=before_dt,
    )
    return ResourceListResponse(
        items=resources, 
        total=total, 
        page=page, 
        page_size=size
    )


@router.post("/", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def upload_new_resource(
    title: str,
    subject: str,
    category_id: int,
    description: Optional[str] = None,
    is_featured: bool = False,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ResourceResponse:
    """Upload a new 3D resource (GLB/GLTF/OBJ)."""
    allowed_ext = {".glb", ".gltf", ".obj"}
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in allowed_ext:
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Supported: .glb, .gltf, .obj"
        )

    # Generate a unique filename
    import uuid
    unique_id = uuid.uuid4().hex[:8]
    safe_filename = f"{unique_id}_{Path(filename).stem}{ext}"
    file_path = UPLOAD_DIR / safe_filename

    # Save the file
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    resource_in = ResourceCreate(
        title=title,
        description=description,
        subject=subject,
        category_id=category_id,
        is_featured=is_featured,
        file_format=ext[1:],  # Remove the dot
    )
    
    created_resource = create_resource(
        db=db, 
        resource=resource_in, 
        file_path=str(file_path)
    )
    return created_resource


@router.get("/{resourceId}/", response_model=ResourceResponse)
def get_resource_by_id(resourceId: int, db: Session = Depends(get_db)) -> ResourceResponse:
    """Get a specific 3D resource by ID."""
    resource = crud_get_resource(db, resourceId)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


@router.put("/{resourceId}/", response_model=ResourceResponse)
def update_existing_resource(
    resourceId: int,
    resource_update: ResourceUpdate,
    db: Session = Depends(get_db),
) -> ResourceResponse:
    """Update metadata of an existing resource."""
    resource = update_resource(db, resourceId, resource_update)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


@router.delete("/{resourceId}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_resource(resourceId: int, db: Session = Depends(get_db)) -> None:
    """Delete a resource and its file."""
    success = crud_delete_resource(db, resourceId)
    if not success:
        raise HTTPException(status_code=404, detail="Resource not found")
    return None


@router.post("/{resourceId}/view/", response_model=dict)
def track_resource_view(resourceId: int, db: Session = Depends(get_db)) -> dict:
    """Increment view count for a resource."""
    resource = increment_view_count(db, resourceId)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return {"view_count": resource.view_count}


@router.get("/categories/", response_model=List[ResourceCategoryResponse])
def get_resource_categories(db: Session = Depends(get_db)) -> List[ResourceCategoryResponse]:
    """List all resource categories."""
    categories = crud_get_categories(db)
    return categories


@router.get("/search/", response_model=List[ResourceResponse])
def search_3d_resources(
    q: str = Query(..., description="Search query"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    file_format: Optional[str] = Query(None, description="Filter by file format"),
    is_featured: Optional[bool] = Query(None, description="Filter featured resources"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=50, description="Items per page"),
    db: Session = Depends(get_db),
) -> List[ResourceResponse]:
    """Full-text search in title, description, or subject + optional filters."""
    skip = (page - 1) * size
    resources = search_resources(
        db,
        query=q,
        skip=skip,
        limit=size,
        category_id=category_id,
        file_format=file_format,
        is_featured=is_featured,
    )
    return resources


@router.get("/{resourceId}/download/")
def download_3d_resource(resourceId: int, db: Session = Depends(get_db)):
    """Download the 3D model file."""
    resource = crud_get_resource(db, resourceId)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    if not os.path.exists(resource.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
        
    return FileResponse(
        path=resource.file_path,
        filename=os.path.basename(resource.file_path),
        media_type="application/octet-stream"
    )


@router.get("/featured/", response_model=List[ResourceResponse])
def get_featured_resources_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=50, description="Items per page"),
    db: Session = Depends(get_db),
) -> List[ResourceResponse]:
    """Get paginated list of featured 3D resources."""
    skip = (page - 1) * size
    resources = get_featured_resources(db, skip=skip, limit=size)
    return resources