from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.schemas.subject import (
    SubjectCreate, 
    SubjectUpdate, 
    SubjectResponse, 
    SubjectListResponse
)
from app.crud import subject as crud_subject

router = APIRouter(prefix="/subjects", tags=["subjects"])

@router.post("/", response_model=SubjectResponse, status_code=201)
def create_subject(
    subject: SubjectCreate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Create a new subject.
    
    - **name**: Subject name (required)
    - **code**: Unique subject code (required)
    - **description**: Subject description
    - **color**: Hex color for UI display
    - **icon**: Lucide icon name
    - **grade_level**: Grade/class level
    - **term**: Academic term
    - **teacher_name**: Teacher's name
    - **is_favorite**: Mark as favorite
    """
    # Check if subject code already exists for this user
    existing = crud_subject.get_subject_by_code(db, subject.code, user_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Subject with code '{subject.code}' already exists"
        )
    
    return crud_subject.create_subject(db, subject, user_id)

@router.get("/", response_model=SubjectListResponse)
def get_subjects(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in name, code, description"),
    grade_level: Optional[str] = Query(None, description="Filter by grade level"),
    term: Optional[str] = Query(None, description="Filter by term"),
    is_favorite: Optional[bool] = Query(None, description="Filter favorites only"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    Get user's subjects with filters and pagination.
    
    Returns subjects ordered by favorite status first, then alphabetically.
    """
    skip = (page - 1) * page_size
    
    subjects, total = crud_subject.get_user_subjects(
        db=db,
        user_id=user_id,
        skip=skip,
        limit=page_size,
        search=search,
        grade_level=grade_level,
        term=term,
        is_favorite=is_favorite,
        is_active=is_active
    )
    
    return {
        "subjects": subjects,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/active", response_model=list[SubjectResponse])
def get_active_subjects(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Get all active subjects for dropdowns and selectors.
    
    Returns a simple list of active subjects without pagination.
    """
    subjects = crud_subject.get_active_subjects(db, user_id)
    return subjects

@router.get("/stats")
def get_subjects_stats(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Get subjects with aggregated statistics.
    
    Returns subjects with counts of notes, quizzes, and videos.
    """
    return crud_subject.get_subjects_with_stats(db, user_id)

@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(
    subject_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """Get a single subject by ID"""
    subject = crud_subject.get_subject(db, subject_id, user_id)
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    return subject

@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: str,
    subject_update: SubjectUpdate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Update a subject.
    
    Only the fields you provide will be updated.
    """
    # If updating code, check it's not already used
    if subject_update.code:
        existing = crud_subject.get_subject_by_code(db, subject_update.code, user_id)
        if existing and existing.id != subject_id:
            raise HTTPException(
                status_code=400,
                detail=f"Subject with code '{subject_update.code}' already exists"
            )
    
    subject = crud_subject.update_subject(db, subject_id, subject_update, user_id)
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    return subject

@router.delete("/{subject_id}", status_code=204)
def delete_subject(
    subject_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Delete a subject.
    
    Warning: This will not delete related notes, quizzes, etc.
    Consider archiving (is_active=false) instead.
    """
    success = crud_subject.delete_subject(db, subject_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    return None

@router.post("/{subject_id}/favorite", response_model=SubjectResponse)
def toggle_favorite(
    subject_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """Toggle favorite status of a subject"""
    subject = crud_subject.toggle_favorite(db, subject_id, user_id)
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    return subject

@router.post("/{subject_id}/refresh-counts", response_model=SubjectResponse)
def refresh_subject_counts(
    subject_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Manually refresh the counts for notes, quizzes, and videos.
    
    This is automatically done when items are added/removed,
    but can be called manually if counts seem incorrect.
    """
    subject = crud_subject.update_subject_counts(db, subject_id)
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    return subject