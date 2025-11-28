from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.models.subject import Subject
from app.schemas.subject import SubjectCreate, SubjectUpdate
from typing import Optional, Tuple, List

def create_subject(db: Session, subject: SubjectCreate, user_id: str) -> Subject:
    """Create a new subject"""
    db_subject = Subject(
        name=subject.name,
        code=subject.code,
        description=subject.description,
        color=subject.color,
        icon=subject.icon,
        user_id=user_id,
        grade_level=subject.grade_level,
        term=subject.term,
        teacher_name=subject.teacher_name,
        is_favorite=subject.is_favorite
    )
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject

def get_subject(db: Session, subject_id: str, user_id: str) -> Optional[Subject]:
    """Get a single subject by ID"""
    return db.query(Subject).filter(
        Subject.id == subject_id,
        Subject.user_id == user_id
    ).first()

def get_subject_by_code(db: Session, code: str, user_id: str) -> Optional[Subject]:
    """Get a subject by its code"""
    return db.query(Subject).filter(
        Subject.code == code,
        Subject.user_id == user_id
    ).first()

def get_user_subjects(
    db: Session,
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    grade_level: Optional[str] = None,
    term: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    is_active: Optional[bool] = None
) -> Tuple[List[Subject], int]:
    """Get user's subjects with filters and pagination"""
    query = db.query(Subject).filter(Subject.user_id == user_id)
    
    # Apply filters
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
    
    if grade_level:
        query = query.filter(Subject.grade_level == grade_level)
    
    if term:
        query = query.filter(Subject.term == term)
    
    if is_favorite is not None:
        query = query.filter(Subject.is_favorite == is_favorite)
    
    if is_active is not None:
        query = query.filter(Subject.is_active == is_active)
    
    # Get total count
    total = query.count()
    
    # Get paginated results, ordered by favorites first, then by name
    subjects = query.order_by(
        Subject.is_favorite.desc(),
        Subject.name.asc()
    ).offset(skip).limit(limit).all()
    
    return subjects, total

def get_active_subjects(db: Session, user_id: str) -> List[Subject]:
    """Get all active subjects for a user (for dropdowns, etc.)"""
    return db.query(Subject).filter(
        Subject.user_id == user_id,
        Subject.is_active == True
    ).order_by(Subject.name.asc()).all()

def update_subject(
    db: Session,
    subject_id: str,
    subject_update: SubjectUpdate,
    user_id: str
) -> Optional[Subject]:
    """Update a subject"""
    db_subject = get_subject(db, subject_id, user_id)
    
    if not db_subject:
        return None
    
    # Update only provided fields
    update_data = subject_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_subject, field, value)
    
    db.commit()
    db.refresh(db_subject)
    return db_subject

def delete_subject(db: Session, subject_id: str, user_id: str) -> bool:
    """Delete a subject"""
    db_subject = get_subject(db, subject_id, user_id)
    
    if not db_subject:
        return False
    
    db.delete(db_subject)
    db.commit()
    return True

def toggle_favorite(db: Session, subject_id: str, user_id: str) -> Optional[Subject]:
    """Toggle favorite status of a subject"""
    db_subject = get_subject(db, subject_id, user_id)
    
    if not db_subject:
        return None
    
    db_subject.is_favorite = not db_subject.is_favorite
    db.commit()
    db.refresh(db_subject)
    return db_subject

def update_subject_counts(db: Session, subject_id: str) -> Optional[Subject]:
    """
    Update the counts for notes, quizzes, and videos.
    This will be called when items are added/removed from other modules.
    
    For now, this is a placeholder that returns the subject.
    When Notes, Quizzes, and Videos modules are implemented,
    they will call this function to update counts.
    """
    db_subject = db.query(Subject).filter(Subject.id == subject_id).first()
    
    if not db_subject:
        return None
    
    # Placeholder for future implementation
    # When you build the Notes module, add:
    # from app.models.note import Note
    # notes_count = db.query(func.count(Note.id)).filter(
    #     Note.subject == db_subject.name,
    #     Note.user_id == db_subject.user_id
    # ).scalar()
    # db_subject.notes_count = notes_count
    
    # When you build the Quizzes module, add:
    # from app.models.quiz import Quiz
    # quizzes_count = db.query(func.count(Quiz.id)).filter(
    #     Quiz.subject_id == subject_id
    # ).scalar()
    # db_subject.quizzes_count = quizzes_count
    
    # When you build the Videos module, add:
    # from app.models.video import Video
    # videos_count = db.query(func.count(Video.id)).filter(
    #     Video.subject_id == subject_id
    # ).scalar()
    # db_subject.videos_count = videos_count
    
    db.commit()
    db.refresh(db_subject)
    return db_subject

def get_subjects_with_stats(db: Session, user_id: str) -> List[dict]:
    """Get subjects with aggregated statistics"""
    subjects = db.query(Subject).filter(
        Subject.user_id == user_id,
        Subject.is_active == True
    ).order_by(Subject.name.asc()).all()
    
    result = []
    for subject in subjects:
        result.append({
            "subject_id": subject.id,
            "subject_name": subject.name,
            "subject_code": subject.code,
            "color": subject.color,
            "total_notes": subject.notes_count,
            "total_quizzes": subject.quizzes_count,
            "total_videos": subject.videos_count,
            "is_favorite": subject.is_favorite
        })
    
    return result