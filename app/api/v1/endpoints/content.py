from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import shutil
import time
from app.db.session import get_db
from app.schemas.content import (
    ContentCreate,
    ContentUpdate,
    ContentResponse,
    ContentListResponse,
    ContentType,
    ContentStatus,
    VALID_CLASSES
)
from app.crud import content as crud_content
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/content", tags=["content"])

# File upload configuration
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

os.makedirs(f"{UPLOAD_DIR}/notes", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/videos", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/assignments", exist_ok=True)
os.makedirs(f"{UPLOAD_DIR}/quizzes", exist_ok=True)

@router.post("/", response_model=ContentResponse, status_code=201)
async def create_content(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    type: ContentType = Form(...),
    class_level: str = Form(...),  # Required: S1, S2, S3, S4, S5, S6
    subject_id: str = Form(...),
    file: Optional[UploadFile] = File(None),
    video_url: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new content (teachers and admins only)
    
    - **title**: Content title (required)
    - **description**: Content description
    - **type**: Content type (note/video/assignment/quiz)
    - **class_level**: Target class (S1/S2/S3/S4/S5/S6) - required
    - **subject_id**: Subject ID
    - **file**: File upload (for notes and assignments)
    - **video_url**: Video URL (for videos, e.g., YouTube)
    """
    # Check authorization
    if current_user.user_type not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="Not authorized to create content")
    
    # Validate class level
    if class_level not in VALID_CLASSES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid class level. Must be one of: {', '.join(VALID_CLASSES)}"
        )
    
    file_path = None
    file_size = None
    file_type = None
    
    # Handle file upload
    if file:
        # Validate file size
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size is {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Create unique filename
        timestamp = int(time.time())
        filename = f"{timestamp}_{file.filename}"
        type_dir = f"{type.value}s"  # notes, videos, assignments, quizzes
        file_path = f"{UPLOAD_DIR}/{type_dir}/{filename}"
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = size
        file_type = file.content_type
    
    # Create content object
    content_data = ContentCreate(
        title=title,
        description=description,
        type=type,
        class_level=class_level,
        subject_id=subject_id,
        file_url=video_url
    )
    
    content = crud_content.create_content(
        db=db,
        content=content_data,
        user_id=current_user.id,
        file_path=file_path,
        file_size=file_size,
        file_type=file_type
    )
    
    return content

@router.get("/", response_model=ContentListResponse)
def get_all_content(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    class_level: Optional[str] = Query(None),  # Filter by class
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all content with filters
    
    - Students see only approved content for their class
    - Teachers see only their own content
    - Admins see all content
    """
    skip = (page - 1) * page_size
    
    # Students: only see approved content for their class
    if current_user.user_type == 'student':
        if not current_user.student_class:
            raise HTTPException(
                status_code=400, 
                detail="Student class not set. Please update your profile."
            )
        
        content, total = crud_content.get_content_for_student(
            db=db,
            student_class=current_user.student_class,
            skip=skip,
            limit=page_size,
            search=search,
            content_type=type,
            subject_id=subject
        )
    
    # Teachers: see their own content
    elif current_user.user_type == 'teacher':
        content, total = crud_content.get_teacher_content(
            db=db,
            teacher_id=current_user.id,
            skip=skip,
            limit=page_size,
            class_level=class_level
        )
    
    # Admins: see all content
    else:
        content, total = crud_content.get_all_content(
            db=db,
            skip=skip,
            limit=page_size,
            search=search,
            content_type=type,
            subject_id=subject,
            status=status,
            class_level=class_level
        )
    
    return {
        "content": content,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/my", response_model=ContentListResponse)
def get_my_content(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get content created by current user"""
    skip = (page - 1) * page_size
    
    content, total = crud_content.get_teacher_content(
        db=db,
        teacher_id=current_user.id,
        skip=skip,
        limit=page_size
    )
    
    return {
        "content": content,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/pending", response_model=list[ContentResponse])
def get_pending_content(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all pending content (admins only)"""
    if current_user.user_type != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    content = crud_content.get_pending_content(db)
    return content

@router.get("/stats")
def get_content_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get content statistics"""
    user_id = current_user.id if current_user.user_type == 'teacher' else None
    stats = crud_content.get_content_stats(db, user_id)
    return stats

@router.get("/{content_id}", response_model=ContentResponse)
def get_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single content by ID"""
    content = crud_content.get_content(db, content_id)
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Check access
    if current_user.user_type == 'student' and content.status != ContentStatus.APPROVED:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if current_user.user_type == 'teacher' and content.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return content

@router.put("/{content_id}", response_model=ContentResponse)
def update_content(
    content_id: str,
    content_update: ContentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update content"""
    # Check if content exists
    content = crud_content.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Check authorization
    if current_user.user_type == 'teacher' and content.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    updated_content = crud_content.update_content(
        db=db,
        content_id=content_id,
        content_update=content_update,
        user_id=current_user.id
    )
    
    return updated_content

@router.post("/{content_id}/approve", response_model=ContentResponse)
def approve_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve content (admins only)"""
    if current_user.user_type != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    content = crud_content.update_content_status(
        db=db,
        content_id=content_id,
        status=ContentStatus.APPROVED
    )
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return content

@router.post("/{content_id}/reject", response_model=ContentResponse)
def reject_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject content (admins only)"""
    if current_user.user_type != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    content = crud_content.update_content_status(
        db=db,
        content_id=content_id,
        status=ContentStatus.REJECTED
    )
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return content

@router.delete("/{content_id}", status_code=204)
def delete_content(
    content_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete content"""
    # Check if content exists
    content = crud_content.get_content(db, content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Check authorization
    if current_user.user_type == 'teacher' and content.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    success = crud_content.delete_content(
        db=db,
        content_id=content_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return None

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    type: ContentType = Form(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload file endpoint
    
    Returns file path for use in content creation
    """
    if current_user.user_type not in ['teacher', 'admin']:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Validate file size
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size is {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Create unique filename
    timestamp = int(time.time())
    filename = f"{timestamp}_{file.filename}"
    type_dir = f"{type.value}s"
    file_path = f"{UPLOAD_DIR}/{type_dir}/{filename}"
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {
        "file_path": f"/{file_path}",
        "file_size": size,
        "file_type": file.content_type
    }