from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, Tuple, List
from app.models.content import Content
from app.schemas.content import ContentCreate, ContentUpdate, ContentStatus, ContentType
import os

def create_content(
    db: Session,
    content: ContentCreate,
    user_id: str,
    file_path: Optional[str] = None,
    file_size: Optional[int] = None,
    file_type: Optional[str] = None
) -> Content:
    """Create new content"""
    db_content = Content(
        title=content.title,
        description=content.description,
        type=content.type,
        class_level=content.class_level,  # Add class level
        subject_id=content.subject_id,
        file_path=file_path,
        file_url=content.file_url,
        file_size=file_size,
        file_type=file_type,
        created_by=user_id,
        status=ContentStatus.PENDING  # Teachers' content needs approval
    )
    
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content

def get_content(db: Session, content_id: str) -> Optional[Content]:
    """Get content by ID"""
    return db.query(Content).filter(Content.id == content_id).first()

def get_all_content(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    content_type: Optional[str] = None,
    subject_id: Optional[str] = None,
    status: Optional[str] = None,
    created_by: Optional[str] = None,
    class_level: Optional[str] = None,  # Add class level filter
) -> Tuple[List[Content], int]:
    """Get all content with filters"""
    query = db.query(Content)
    
    # Apply filters
    if search:
        search_filter = or_(
            Content.title.ilike(f"%{search}%"),
            Content.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if content_type:
        query = query.filter(Content.type == content_type)
    
    if subject_id:
        query = query.filter(Content.subject_id == subject_id)
    
    if status:
        query = query.filter(Content.status == status)
    
    if created_by:
        query = query.filter(Content.created_by == created_by)
    
    if class_level:
        query = query.filter(Content.class_level == class_level)
    
    total = query.count()
    content = query.order_by(Content.created_at.desc()).offset(skip).limit(limit).all()
    
    return content, total

def get_content_for_student(
    db: Session,
    student_class: str,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    content_type: Optional[str] = None,
    subject_id: Optional[str] = None,
) -> Tuple[List[Content], int]:
    """Get approved content filtered by student's class"""
    query = db.query(Content).filter(
        Content.class_level == student_class,
        Content.status == ContentStatus.APPROVED
    )
    
    if search:
        search_filter = or_(
            Content.title.ilike(f"%{search}%"),
            Content.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if content_type:
        query = query.filter(Content.type == content_type)
    
    if subject_id:
        query = query.filter(Content.subject_id == subject_id)
    
    total = query.count()
    content = query.order_by(Content.created_at.desc()).offset(skip).limit(limit).all()
    
    return content, total

def get_teacher_content(
    db: Session,
    teacher_id: str,
    skip: int = 0,
    limit: int = 20,
    class_level: Optional[str] = None,
) -> Tuple[List[Content], int]:
    """Get content created by a specific teacher"""
    query = db.query(Content).filter(Content.created_by == teacher_id)
    
    if class_level:
        query = query.filter(Content.class_level == class_level)
    
    total = query.count()
    content = query.order_by(Content.created_at.desc()).offset(skip).limit(limit).all()
    return content, total

def get_pending_content(db: Session, class_level: Optional[str] = None) -> List[Content]:
    """Get all pending content for moderation"""
    query = db.query(Content).filter(Content.status == ContentStatus.PENDING)
    
    if class_level:
        query = query.filter(Content.class_level == class_level)
    
    return query.order_by(Content.created_at.desc()).all()

def update_content(
    db: Session,
    content_id: str,
    content_update: ContentUpdate,
    user_id: str
) -> Optional[Content]:
    """Update content"""
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        return None
    
    # Update fields
    update_data = content_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(content, field, value)
    
    db.commit()
    db.refresh(content)
    return content

def update_content_status(
    db: Session,
    content_id: str,
    status: ContentStatus
) -> Optional[Content]:
    """Update content status (for moderation)"""
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        return None
    
    content.status = status
    db.commit()
    db.refresh(content)
    return content

def delete_content(
    db: Session,
    content_id: str,
    user_id: str
) -> bool:
    """Delete content"""
    content = db.query(Content).filter(Content.id == content_id).first()
    
    if not content:
        return False
    
    # Delete file if exists
    if content.file_path and os.path.exists(content.file_path):
        try:
            os.remove(content.file_path)
        except:
            pass  # Continue even if file deletion fails
    
    db.delete(content)
    db.commit()
    return True

def get_content_stats(db: Session, user_id: Optional[str] = None, class_level: Optional[str] = None) -> dict:
    """Get content statistics"""
    query = db.query(Content)
    
    if user_id:
        query = query.filter(Content.created_by == user_id)
    
    if class_level:
        query = query.filter(Content.class_level == class_level)
    
    total = query.count()
    notes = query.filter(Content.type == ContentType.NOTE).count()
    videos = query.filter(Content.type == ContentType.VIDEO).count()
    assignments = query.filter(Content.type == ContentType.ASSIGNMENT).count()
    pending = query.filter(Content.status == ContentStatus.PENDING).count()
    
    return {
        "total": total,
        "notes": notes,
        "videos": videos,
        "assignments": assignments,
        "pending": pending
    }

def get_content_by_class_and_subject(
    db: Session,
    class_level: str,
    subject_id: str,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[Content], int]:
    """Get approved content for specific class and subject"""
    query = db.query(Content).filter(
        Content.class_level == class_level,
        Content.subject_id == subject_id,
        Content.status == ContentStatus.APPROVED
    )
    
    total = query.count()
    content = query.order_by(Content.created_at.desc()).offset(skip).limit(limit).all()
    
    return content, total