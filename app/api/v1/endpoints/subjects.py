# app/api/v1/endpoints/subject.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.subject import (
    SubjectCreate, SubjectUpdate, SubjectResponse,
    SubjectListResponse, SubjectStatsResponse
)
from app.crud import subject as crud_subject

router = APIRouter()

@router.post("/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    subject: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SubjectResponse:
    """
    Create a new subject.
    """
    # Check if subject code already exists for this user
    existing = crud_subject.get_subject_by_code(db, subject.code, current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subject with code '{subject.code}' already exists"
        )
    
    return crud_subject.create_subject(db, subject, current_user.id)

@router.get("/", response_model=SubjectListResponse)
def get_subjects(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in name, code, description, teacher"),
    grade_level: Optional[str] = Query(None, description="Filter by grade level"),
    term: Optional[str] = Query(None, description="Filter by term"),
    is_favorite: Optional[bool] = Query(None, description="Filter favorites only"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SubjectListResponse:
    """
    Get user's subjects with filters and pagination.
    """
    skip = (page - 1) * page_size
    
    subjects, total = crud_subject.get_user_subjects(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=page_size,
        search=search,
        grade_level=grade_level,
        term=term,
        is_favorite=is_favorite,
        is_active=is_active
    )
    
    return SubjectListResponse(
        subjects=subjects,
        total=total,
        page=page,
        page_size=page_size
    )

@router.get("/active", response_model=List[SubjectResponse])
def get_active_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[SubjectResponse]:
    """
    Get all active subjects for dropdowns and selectors.
    """
    subjects = crud_subject.get_active_subjects(db, current_user.id)
    return subjects

@router.get("/stats", response_model=List[SubjectStatsResponse])
def get_subjects_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[SubjectStatsResponse]:
    """
    Get subjects with aggregated statistics.
    """
    stats = crud_subject.get_subjects_with_stats(db, current_user.id)
    return stats

@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(
    subject_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SubjectResponse:
    """
    Get a single subject by ID.
    """
    subject = crud_subject.get_subject(db, subject_id, current_user.id)
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    return subject

@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: str,
    subject_update: SubjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SubjectResponse:
    """
    Update a subject.
    """
    # If updating code, check it's not already used by another subject
    if subject_update.code:
        existing = crud_subject.get_subject_by_code(db, subject_update.code, current_user.id)
        if existing and existing.id != subject_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subject with code '{subject_update.code}' already exists"
            )
    
    subject = crud_subject.update_subject(db, subject_id, subject_update, current_user.id)
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    return subject

@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a subject.
    
    Note: Consider archiving (is_active=false) instead of deletion.
    """
    success = crud_subject.delete_subject(db, subject_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )

@router.post("/{subject_id}/favorite", response_model=SubjectResponse)
def toggle_favorite(
    subject_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SubjectResponse:
    """
    Toggle favorite status of a subject.
    """
    subject = crud_subject.toggle_favorite(db, subject_id, current_user.id)
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    return subject

@router.post("/{subject_id}/archive", response_model=SubjectResponse)
def archive_subject(
    subject_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SubjectResponse:
    """
    Archive a subject (set is_active=false).
    """
    subject = crud_subject.get_subject(db, subject_id, current_user.id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    subject.is_active = False
    db.commit()
    db.refresh(subject)
    
    return subject

@router.post("/{subject_id}/activate", response_model=SubjectResponse)
def activate_subject(
    subject_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SubjectResponse:
    """
    Activate a subject (set is_active=true).
    """
    subject = crud_subject.get_subject(db, subject_id, current_user.id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    subject.is_active = True
    db.commit()
    db.refresh(subject)
    
    return subject

@router.post("/{subject_id}/refresh-counts", response_model=SubjectResponse)
def refresh_subject_counts(
    subject_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> SubjectResponse:
    """
    Manually refresh the counts for notes, quizzes, and videos.
    """
    subject = crud_subject.update_subject_counts(db, subject_id)
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    return subject