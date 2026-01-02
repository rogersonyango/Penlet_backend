from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.schemas.subject import (
    SubjectCreate, 
    SubjectUpdate, 
    SubjectResponse, 
    SubjectListResponse,
    VALID_CLASSES
)
from app.crud import subject as crud_subject
from app.utils.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/subjects", tags=["subjects"])

@router.post("/", response_model=SubjectResponse, status_code=201)
def create_subject(
    subject: SubjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new subject (admin only).
    
    - **name**: Subject name (required)
    - **code**: Unique subject code (required)
    - **class_level**: Class level S1-S6 (required)
    - **description**: Subject description
    - **color**: Hex color for UI display
    - **icon**: Lucide icon name
    - **term**: Academic term
    - **teacher_id**: Assigned teacher ID
    - **teacher_name**: Teacher's name
    """
    # Only admins can create subjects
    if current_user.user_type != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can create subjects")
    
    # Check if subject code already exists
    existing = crud_subject.get_subject_by_code(db, subject.code)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Subject with code '{subject.code}' already exists"
        )
    
    return crud_subject.create_subject(db, subject)

@router.get("/", response_model=SubjectListResponse)
def get_subjects(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in name, code, description"),
    class_level: Optional[str] = Query(None, description="Filter by class level (S1-S6)"),
    term: Optional[str] = Query(None, description="Filter by term"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get subjects based on user role:
    
    - **Students**: See subjects for their class only
    - **Teachers**: See subjects assigned to them
    - **Admins**: See all subjects
    """
    skip = (page - 1) * page_size
    
    # Students: only see subjects for their class
    if current_user.user_type == 'student':
        if not current_user.student_class:
            raise HTTPException(
                status_code=400,
                detail="Student class not set. Please update your profile."
            )
        
        subjects, total = crud_subject.get_subjects_by_class(
            db=db,
            class_level=current_user.student_class,
            skip=skip,
            limit=page_size,
            search=search,
            term=term,
            is_active=is_active if is_active is not None else True
        )
    
    # Teachers: see subjects assigned to them
    elif current_user.user_type == 'teacher':
        subjects, total = crud_subject.get_subjects_by_teacher(
            db=db,
            teacher_id=current_user.id,
            skip=skip,
            limit=page_size,
            class_level=class_level
        )
    
    # Admins: see all subjects
    else:
        subjects, total = crud_subject.get_all_subjects(
            db=db,
            skip=skip,
            limit=page_size,
            search=search,
            class_level=class_level,
            term=term,
            is_active=is_active
        )
    
    return {
        "subjects": subjects,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/active", response_model=List[SubjectResponse])
def get_active_subjects(
    class_level: Optional[str] = Query(None, description="Filter by class level"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active subjects for dropdowns and selectors.
    
    - Students: Returns subjects for their class
    - Teachers: Returns subjects assigned to them
    - Admins: Returns all active subjects (can filter by class)
    """
    if current_user.user_type == 'student':
        if not current_user.student_class:
            return []
        return crud_subject.get_active_subjects_for_class(db, current_user.student_class)
    
    elif current_user.user_type == 'teacher':
        subjects, _ = crud_subject.get_subjects_by_teacher(db, current_user.id)
        return [s for s in subjects if s.is_active]
    
    else:
        return crud_subject.get_active_subjects(db, class_level)

@router.get("/by-class/{class_level}", response_model=List[SubjectResponse])
def get_subjects_by_class(
    class_level: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all subjects for a specific class.
    
    - Students can only access their own class
    - Teachers and Admins can access any class
    """
    if class_level not in VALID_CLASSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid class level. Must be one of: {', '.join(VALID_CLASSES)}"
        )
    
    # Students can only see their own class
    if current_user.user_type == 'student' and current_user.student_class != class_level:
        raise HTTPException(status_code=403, detail="Not authorized to view other classes")
    
    subjects, _ = crud_subject.get_subjects_by_class(db, class_level)
    return subjects

@router.get("/stats")
def get_subjects_stats(
    class_level: Optional[str] = Query(None, description="Filter by class level"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get subjects with aggregated statistics.
    """
    # Students only see stats for their class
    if current_user.user_type == 'student':
        class_level = current_user.student_class
    
    return crud_subject.get_subjects_with_stats(db, class_level)

@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single subject by ID"""
    subject = crud_subject.get_subject(db, subject_id)
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Students can only see subjects for their class
    if current_user.user_type == 'student':
        if subject.class_level != current_user.student_class:
            raise HTTPException(status_code=404, detail="Subject not found")
    
    return subject

@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: str,
    subject_update: SubjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a subject (admin only).
    """
    if current_user.user_type != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can update subjects")
    
    # If updating code, check it's not already used
    if subject_update.code:
        existing = crud_subject.get_subject_by_code(db, subject_update.code)
        if existing and existing.id != subject_id:
            raise HTTPException(
                status_code=400,
                detail=f"Subject with code '{subject_update.code}' already exists"
            )
    
    subject = crud_subject.update_subject(db, subject_id, subject_update)
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    return subject

@router.delete("/{subject_id}", status_code=204)
def delete_subject(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a subject (admin only).
    
    Warning: Consider deactivating (is_active=false) instead of deleting.
    """
    if current_user.user_type != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can delete subjects")
    
    success = crud_subject.delete_subject(db, subject_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    return None

@router.post("/{subject_id}/assign-teacher", response_model=SubjectResponse)
def assign_teacher_to_subject(
    subject_id: str,
    teacher_id: str = Query(..., description="Teacher user ID"),
    teacher_name: str = Query(..., description="Teacher name"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Assign a teacher to a subject (admin only).
    """
    if current_user.user_type != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can assign teachers")
    
    subject = crud_subject.assign_teacher(db, subject_id, teacher_id, teacher_name)
    
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    return subject

@router.get("/classes/list", response_model=List[dict])
def get_available_classes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of available class levels with subject counts.
    """
    result = []
    for cls in VALID_CLASSES:
        subjects, count = crud_subject.get_subjects_by_class(db, cls)
        result.append({
            "class_level": cls,
            "name": f"Senior {cls[1]}",
            "subject_count": count
        })
    return result