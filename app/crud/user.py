from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()

def create_user(db: Session, user: UserCreate):
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        password_hash=get_password_hash(user.password),
        user_type=user.user_type,
        student_class=user.student_class if user.user_type == 'student' else None
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def get_users_by_class(db: Session, student_class: str):
    """Get all students in a specific class"""
    return db.query(User).filter(
        User.user_type == 'student',
        User.student_class == student_class,
        User.is_active == True
    ).all()

def get_all_users(db: Session, skip: int = 0, limit: int = 100, user_type: str = None):
    """Get all users with optional type filter"""
    query = db.query(User)
    if user_type:
        query = query.filter(User.user_type == user_type)
    return query.offset(skip).limit(limit).all()