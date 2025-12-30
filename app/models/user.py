from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime
import uuid
from app.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

# Valid class levels for students
VALID_CLASSES = ["S1", "S2", "S3", "S4", "S5", "S6"]

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    full_name = Column(String)
    password_hash = Column(String, nullable=False)
    user_type = Column(String, default="student")  # student, teacher, admin
    student_class = Column(String(10), nullable=True)  # S1, S2, S3, S4, S5, S6 (null for teachers/admins)
    profile_image = Column(String(500), nullable=True)  # Profile image URL/path
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)