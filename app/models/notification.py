from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.session import Base
import uuid
import enum

class NotificationType(str, enum.Enum):
    """Notification types"""
    QUIZ_REMINDER = "quiz_reminder"
    VIDEO_ADDED = "video_added"
    ASSIGNMENT_DUE = "assignment_due"
    STUDY_REMINDER = "study_reminder"
    ACHIEVEMENT = "achievement"
    ALARM = "alarm"
    SYSTEM = "system"
    GENERAL = "general"

class NotificationPriority(str, enum.Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Notification content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(SQLEnum(NotificationType), nullable=False, default=NotificationType.GENERAL)
    priority = Column(SQLEnum(NotificationPriority), nullable=False, default=NotificationPriority.MEDIUM)
    
    # Linking to other entities (optional)
    related_entity_type = Column(String(50))  # 'video', 'quiz', 'note', 'subject', etc.
    related_entity_id = Column(String)
    action_url = Column(String(500))  # URL to navigate to when clicked
    
    # Icon and styling
    icon = Column(String(50))  # Icon name from lucide-react
    color = Column(String(20))  # Color for the notification badge
    
    # Status
    is_read = Column(Boolean, default=False, index=True)
    is_archived = Column(Boolean, default=False, index=True)
    is_pinned = Column(Boolean, default=False)
    
    # Scheduling
    scheduled_for = Column(DateTime(timezone=True))  # For future notifications
    expires_at = Column(DateTime(timezone=True))  # Auto-delete after this time
    
    # Metadata
    read_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Notification(id={self.id}, title={self.title}, type={self.type}, is_read={self.is_read})>"