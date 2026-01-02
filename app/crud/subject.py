from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.models.subject import Subject
from app.schemas.subject import SubjectCreate, SubjectUpdate, VALID_CLASSES
from typing import Optional, Tuple, List

def create_subject(db: Session, subject: SubjectCreate, created_by: str = None) -> Subject:
    """Create a new subject (admin only)"""
    db_subject = Subject(
        name=subject.name,
        code=subject.code,
        description=subject.description,
        color=subject.color,
        icon=subject.icon,
        class_level=subject.class_level,
        term=subject.term,
        teacher_name=subject.teacher_name,
        teacher_id=subject.teacher_id
    )
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

def get_subject(db: Session, subject_id: str) -> Optional[Subject]:
    """Get a single subject by ID"""
    return db.query(Subject).filter(Subject.id == subject_id).first()

def get_subject_by_code(db: Session, code: str) -> Optional[Subject]:
    """Get a subject by its code"""
    return db.query(Subject).filter(Subject.code == code).first()

def get_subjects_by_class(
    db: Session,
    class_level: str,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    term: Optional[str] = None,
    is_active: Optional[bool] = True
) -> Tuple[List[Subject], int]:
    """Get subjects for a specific class (for students)"""
    query = db.query(Subject).filter(Subject.class_level == class_level)
    
    if is_active is not None:
        query = query.filter(Subject.is_active == is_active)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Subject.name.ilike(search_term),
                Subject.code.ilike(search_term),
                Subject.description.ilike(search_term)
            )
        )
    
    if term:
        query = query.filter(Subject.term == term)
    
    total = query.count()
    subjects = query.order_by(Subject.name.asc()).offset(skip).limit(limit).all()
    
    return subjects, total

def get_subjects_by_teacher(
    db: Session,
    teacher_id: str,
    skip: int = 0,
    limit: int = 100,
    class_level: Optional[str] = None
) -> Tuple[List[Subject], int]:
    """Get subjects assigned to a specific teacher"""
    query = db.query(Subject).filter(Subject.teacher_id == teacher_id)
    
    if class_level:
        query = query.filter(Subject.class_level == class_level)
    
    total = query.count()
    subjects = query.order_by(Subject.class_level.asc(), Subject.name.asc()).offset(skip).limit(limit).all()
    
    return subjects, total

def get_all_subjects(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    class_level: Optional[str] = None,
    term: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Tuple[List[Subject], int]:
    """Get all subjects with filters (for admins)"""
    query = db.query(Subject)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Subject.name.ilike(search_term),
                Subject.code.ilike(search_term),
                Subject.description.ilike(search_term),
                Subject.teacher_name.ilike(search_term)
            )
        )
    
    if class_level:
        query = query.filter(Subject.class_level == class_level)
    
    if term:
        query = query.filter(Subject.term == term)
    
    if is_active is not None:
        query = query.filter(Subject.is_active == is_active)
    
    total = query.count()
    subjects = query.order_by(
        Subject.class_level.asc(),
        Subject.name.asc()
    ).offset(skip).limit(limit).all()
    
    return subjects, total

def get_active_subjects_for_class(db: Session, class_level: str) -> List[Subject]:
    """Get all active subjects for a specific class (for dropdowns, etc.)"""
    return db.query(Subject).filter(
        Subject.class_level == class_level,
        Subject.is_active == True
    ).order_by(Subject.name.asc()).all()

def get_active_subjects(db: Session, class_level: Optional[str] = None) -> List[Subject]:
    """Get all active subjects, optionally filtered by class"""
    query = db.query(Subject).filter(Subject.is_active == True)
    
    if class_level:
        query = query.filter(Subject.class_level == class_level)
    
    return query.order_by(Subject.class_level.asc(), Subject.name.asc()).all()

def update_subject(
    db: Session,
    subject_id: str,
    subject_update: SubjectUpdate
) -> Optional[Subject]:
    """Update a subject"""
    db_subject = get_subject(db, subject_id)
    
    if not db_subject:
        return None
    
    # Update only provided fields
    update_data = subject_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_subject, field, value)
    
    db.commit()
    db.refresh(db_subject)
    return db_subject

def delete_subject(db: Session, subject_id: str) -> bool:
    """Delete a subject"""
    db_subject = get_subject(db, subject_id)
    
    if not db_subject:
        return False
    
    db.delete(db_subject)
    db.commit()
    return True

def assign_teacher(db: Session, subject_id: str, teacher_id: str, teacher_name: str) -> Optional[Subject]:
    """Assign a teacher to a subject"""
    db_subject = get_subject(db, subject_id)
    
    if not db_subject:
        return None
    
    db_subject.teacher_id = teacher_id
    db_subject.teacher_name = teacher_name
    db.commit()
    db.refresh(db_subject)
    return db_subject

def update_subject_counts(db: Session, subject_id: str) -> Optional[Subject]:
    """
    Update the counts for notes, quizzes, and videos.
    """
    db_subject = db.query(Subject).filter(Subject.id == subject_id).first()
    
    if not db_subject:
        return None
    
    # TODO: Implement actual counting from Content table
    # notes_count = db.query(func.count(Content.id)).filter(
    #     Content.subject_id == subject_id,
    #     Content.type == 'note'
    # ).scalar()
    # db_subject.notes_count = notes_count
    
    db.commit()
    db.refresh(db_subject)
    return db_subject

def get_subjects_with_stats(db: Session, class_level: Optional[str] = None) -> List[dict]:
    """Get subjects with aggregated statistics"""
    query = db.query(Subject).filter(Subject.is_active == True)
    
    if class_level:
        query = query.filter(Subject.class_level == class_level)
    
    subjects = query.order_by(Subject.class_level.asc(), Subject.name.asc()).all()
    
    result = []
    for subject in subjects:
        result.append({
            "subject_id": subject.id,
            "subject_name": subject.name,
            "subject_code": subject.code,
            "class_level": subject.class_level,
            "color": subject.color,
            "total_notes": subject.notes_count,
            "total_quizzes": subject.quizzes_count,
            "total_videos": subject.videos_count,
            "teacher_name": subject.teacher_name
        })
    
    return result