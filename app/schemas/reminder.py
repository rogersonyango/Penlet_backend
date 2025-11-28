# app/schemas/reminder.py
from pydantic import BaseModel, field_validator
from datetime import datetime, timezone
from typing import Optional

class ReminderBase(BaseModel):
    """Base schema for reminder."""
    title: str
    description: Optional[str] = None
    due_date: datetime

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if v <= now:
            raise ValueError("Due date must be in the future")
        return v

class ReminderCreate(ReminderBase):
    """Schema for creating a reminder."""
    pass

class ReminderUpdate(BaseModel):
    """Schema for updating a reminder (partial update)."""
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None

    @field_validator('due_date')
    @classmethod
    def validate_due_date_if_provided(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None:
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if v <= now:
                raise ValueError("Due date must be in the future")
        return v

class ReminderInDBBase(ReminderBase):
    id: int
    user_id: int
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Reminder(ReminderInDBBase):
    pass