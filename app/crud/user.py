# app/crud/user.py
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password

def get_user(db: Session, user_id: str) -> Optional[User]:
    """Get a user by ID"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email"""
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get a user by username"""
    return db.query(User).filter(User.username == username).first()

def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    user_type: Optional[str] = None,
    is_active: Optional[bool] = None
) -> List[User]:
    """Get users with optional filters"""
    query = db.query(User)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.email.ilike(search_term),
                User.username.ilike(search_term),
                User.full_name.ilike(search_term)
            )
        )
    
    if user_type:
        query = query.filter(User.user_type == user_type)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    return query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user"""
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        password_hash=get_password_hash(user.password),
        user_type=user.user_type
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(
    db: Session,
    user_id: str,
    user_update: UserUpdate,
    is_admin: bool = False
) -> Optional[User]:
    """Update a user"""
    db_user = get_user(db, user_id)
    
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Only admins can change user_type
    if 'user_type' in update_data and not is_admin:
        del update_data['user_type']
    
    for key, value in update_data.items():
        if value is not None:
            setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: str) -> bool:
    """Delete a user"""
    db_user = get_user(db, user_id)
    
    if not db_user:
        return False
    
    db.delete(db_user)
    db.commit()
    return True

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user"""
    user = get_user_by_email(db, email)
    
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    if not user.is_active:
        return None
    
    return user

def change_password(
    db: Session,
    user_id: str,
    current_password: str,
    new_password: str
) -> Optional[User]:
    """Change user password"""
    user = get_user(db, user_id)
    
    if not user or not verify_password(current_password, user.password_hash):
        return None
    
    user.password_hash = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user

def toggle_user_active(db: Session, user_id: str, is_admin: bool = False) -> Optional[User]:
    """Toggle user active status (admin only)"""
    if not is_admin:
        return None
    
    user = get_user(db, user_id)
    
    if not user:
        return None
    
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user

def update_user_last_login(db: Session, user_id: str) -> Optional[User]:
    """Update user's last login time"""
    user = get_user(db, user_id)
    
    if not user:
        return None
    
    # The updated_at field will automatically update
    db.commit()
    db.refresh(user)
    return user