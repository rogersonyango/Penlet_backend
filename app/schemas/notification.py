from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums
class NotificationType(str, Enum):
    QUIZ_REMINDER = "quiz_reminder"
    VIDEO_ADDED = "video_added"
    ASSIGNMENT_DUE = "assignment_due"
    STUDY_REMINDER = "study_reminder"
    ACHIEVEMENT = "achievement"
    ALARM = "alarm"
    SYSTEM = "system"
    GENERAL = "general"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# Base schema
class NotificationBase(BaseModel):
    title: str = Field(..., max_length=200, description="Notification title")
    message: str = Field(..., description="Notification message")
    type: NotificationType = Field(default=NotificationType.GENERAL)
    priority: NotificationPriority = Field(default=NotificationPriority.MEDIUM)
    related_entity_type: Optional[str] = Field(None, max_length=50)
    related_entity_id: Optional[str] = None
    action_url: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=50, description="Lucide icon name")
    color: Optional[str] = Field(None, max_length=20, description="Badge color")
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None

# Create schema
class NotificationCreate(NotificationBase):
    pass

# Update schema
class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_archived: Optional[bool] = None
    is_pinned: Optional[bool] = None

# Response schema
class NotificationResponse(NotificationBase):
    id: str
    user_id: str
    is_read: bool
    is_archived: bool
    is_pinned: bool
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# List response
class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int

# Statistics
class NotificationStats(BaseModel):
    total: int
    unread: int
    read: int
    archived: int
    by_type: dict
    by_priority: dict
    recent_count: int  # Last 24 hours