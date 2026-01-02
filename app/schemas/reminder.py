# app/schemas/reminder.py
from pydantic import BaseModel, field_validator, Field
from datetime import datetime, timezone
from typing import Optional

class ReminderBase(BaseModel):
    """Base reminder schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: datetime

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: datetime) -> datetime:
        """Ensure due date is in the future."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if v <= now:
            raise ValueError('Due date must be in the future')
        return v

class ReminderCreate(ReminderBase):
    """Schema for creating a reminder."""
    pass

class ReminderUpdate(BaseModel):
    """Schema for updating a reminder."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None

    @field_validator('due_date')
    @classmethod
    def validate_due_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate due date if provided."""
        if v is not None:
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if v <= now:
                raise ValueError('Due date must be in the future')
        return v

class ReminderResponse(BaseModel):
    """Schema for reminder response."""
    id: int
    user_id: str
    title: str
    description: Optional[str]
    due_date: datetime
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

