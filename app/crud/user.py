#app/crud/user.py

from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from typing import Optional, List
import uuid
from app.models.user import User, UserRole, RefreshToken

from app.utils.auth import get_password_hash, verify_password, generate_otp, generate_token

from app.config import settings

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def create_user(
    db: Session,
    email: str,
    role: UserRole,
    first_name: str,
    last_name: str,
    password: Optional[str] = None,
    user_class: Optional[str] = None,
    subject: Optional[str] = None
) -> User:
    if role == UserRole.STUDENT and not user_class:
        raise ValueError("Student must have a class")
    if role == UserRole.TEACHER and not subject:
        raise ValueError("Teacher must have a subject")

    hashed_password = get_password_hash(password) if password else None
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        hashed_password=hashed_password,
        role=role,
        is_verified=False,
        user_class=user_class,
        subject=subject
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_admin_with_otp(
    db: Session, email: str, first_name: str, last_name: str, password: str
) -> tuple[User, str]:
    hashed_password = get_password_hash(password) 
    otp = generate_otp()
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=UserRole.ADMIN,
        otp_code=otp,
        hashed_password=hashed_password,
        otp_created_at=datetime.utcnow(),
        is_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, otp

def verify_otp(db: Session, email: str, otp: str) -> bool:
    user = get_user_by_email(db, email)
    if not user or user.role != UserRole.ADMIN:
        return False
    if not user.otp_code or not user.otp_created_at:
        return False
    if datetime.utcnow() - user.otp_created_at > timedelta(minutes=settings.OTP_EXPIRE_MINUTES):
        return False
    if user.otp_code != otp:
        return False
    user.is_verified = True
    user.otp_code = None
    user.otp_created_at = None
    user.last_login = datetime.utcnow()
    db.commit()
    return True

def generate_new_otp(db: Session, user: User) -> str:
    otp = generate_otp()
    user.otp_code = otp
    user.otp_created_at = datetime.utcnow()
    db.commit()
    return otp

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user or not user.hashed_password:
        return None
    if user.locked_until and user.locked_until > datetime.utcnow():
        return None
    if not verify_password(password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        db.commit()
        return None
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    db.commit()
    return user

def set_verification_token(db: Session, user: User) -> str:
    token = generate_token()
    user.reset_token = token
    user.reset_token_created_at = datetime.utcnow()
    db.commit()
    return token

def verify_email_token(db: Session, token: str) -> bool:
    user = db.query(User).filter(User.reset_token == token).first()
    if not user or not user.reset_token_created_at:
        return False
    if datetime.utcnow() - user.reset_token_created_at > timedelta(hours=24):
        return False
    user.is_verified = True
    user.reset_token = None
    user.reset_token_created_at = None
    db.commit()
    return True

def create_password_reset_token(db: Session, user: User) -> str:
    token = generate_token()
    user.reset_token = token
    user.reset_token_created_at = datetime.utcnow()
    db.commit()
    return token

def reset_password_with_token(db: Session, token: str, new_password: str) -> bool:
    user = db.query(User).filter(User.reset_token == token).first()
    if not user or not user.reset_token_created_at:
        return False
    if datetime.utcnow() - user.reset_token_created_at > timedelta(hours=1):
        return False
    user.hashed_password = get_password_hash(new_password)
    user.reset_token = None
    user.reset_token_created_at = None
    db.commit()
    return True

def update_user_profile(
    db: Session,
    user: User,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    user_class: Optional[str] = None,
    subject: Optional[str] = None
) -> User:
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if email is not None:
        user.email = email
    if user_class is not None:
        user.user_class = user_class
    if subject is not None:
        user.subject = subject
    db.commit()
    db.refresh(user)
    return user

# === Refresh Token Management ===
def create_refresh_token_db(db: Session, user_id: str, token: str) -> RefreshToken:
    expires_at = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token

def get_refresh_token(db: Session, token: str) -> Optional[RefreshToken]:
    return db.query(RefreshToken).filter(
        RefreshToken.token == token,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()

def revoke_refresh_token(db: Session, token: str) -> bool:
    rt = db.query(RefreshToken).filter(RefreshToken.token == token).first()
    if rt:
        rt.is_revoked = True
        db.commit()
        return True
    return False

def revoke_all_user_tokens(db: Session, user_id: str):
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.is_revoked == False
    ).update({RefreshToken.is_revoked: True})
    db.commit()

# === Search ===
def search_users(
    db: Session,
    name: str = None,
    user_class: str = None,
    subject: str = None
) -> List[User]:
    query = db.query(User)
    if name:
        name = name.strip().lower()
        query = query.filter(
            or_(
                (User.first_name + " " + User.last_name).ilike(f"%{name}%"),
                User.first_name.ilike(f"%{name}%"),
                User.last_name.ilike(f"%{name}%")
            )
        )
    if user_class:
        query = query.filter(User.user_class.ilike(f"%{user_class}%"))
    if subject:
        query = query.filter(User.subject.ilike(f"%{subject}%"))
    return query.all()