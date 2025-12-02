from sqlalchemy import (
    Column, String, Boolean, DateTime, Enum, ForeignKey, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.db.session import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=True)
    role = Column(Enum(UserRole, name="userrole"), nullable=False)
    is_verified = Column(Boolean, default=False)
    
    # OTP fields (for admin)
    otp_code = Column(String, nullable=True)
    otp_created_at = Column(DateTime, nullable=True)
    
    # Token fields (for email verification & password reset)
    reset_token = Column(String, nullable=True)
    reset_token_created_at = Column(DateTime, nullable=True)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    
    # Extra fields
    user_class = Column(String, nullable=True)   
    subject = Column(String, nullable=True)     

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    token = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="refresh_tokens")