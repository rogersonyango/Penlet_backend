from datetime import date, datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
import secrets
import string
from fastapi.security import OAuth2PasswordBearer
from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

def get_password_hash(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

# Token & OTP generation
def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of given length (default: 6 digits)."""
    return ''.join(secrets.choice(string.digits) for _ in range(length))

def generate_token(length: int = 64) -> str:
    """Generate a secure random URL-safe token."""
    return secrets.token_urlsafe(length)

# JWT handling
def create_access_token( data:dict, expires_delta: timedelta = None) -> str:
    """
    Create a JWT access token.
    - `data`: payload (e.g., {"sub": email})
    - `expires_delta`: token lifetime (default: 15 minutes)
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token.
    - Valid for `REFRESH_TOKEN_EXPIRE_MINUTES` (default: 24 hours)
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode = {**data, "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(token: str, expected_type: str) -> dict | None:
    """
    Verify a JWT token and return its payload if valid.
    Returns `None` if:
    - Token is invalid/expired
    - Token type doesn't match `expected_type` ("access" or "refresh")
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload
    except Exception:
        return None
# app/utils/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.core.config import settings

# Security scheme
security = HTTPBearer(auto_error=False)

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Extracts the user_id from the JWT token and fetches the user from database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check if credentials provided
    if credentials is None:
        raise credentials_exception
    
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    # Extract user_id from token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current user and verify they are an admin"""
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def get_current_teacher(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get the current user and verify they are a teacher or admin"""
    if current_user.user_type not in ["teacher", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required"
        )
    return current_user

def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise return None.
    Useful for endpoints that work differently for authenticated vs anonymous users.
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        return None
    
    user_id: str = payload.get("sub")
    if user_id is None:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user
