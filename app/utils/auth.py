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