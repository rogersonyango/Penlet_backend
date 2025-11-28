# app/schemas/alarm.py 
from pydantic import BaseModel, field_validator, Field
from datetime import datetime, timezone
from typing import Optional, Dict, Any

class AlarmBase(BaseModel):
    """Base schema for alarm data shared across create, update, and read operations."""
    
    title: str
    description: Optional[str] = None
    alarm_time: datetime
    is_active: bool = True
    is_recurring: bool = False
    recurrence_pattern: Optional[Dict[str, Any]] = None

    @field_validator('alarm_time')
    @classmethod
    def time_must_be_future(cls, value: datetime) -> datetime:
        """Ensure the alarm time is set in the future (UTC-aware)."""
        # Make value timezone-aware if naive
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if value <= now:
            raise ValueError('Alarm time must be in the future')
        return value


class AlarmCreate(AlarmBase):
    """Schema for creating a new alarm."""
    pass


class AlarmUpdate(BaseModel):
    """Schema for updating an existing alarm with optional fields."""
    
    title: Optional[str] = None
    description: Optional[str] = None
    alarm_time: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[Dict[str, Any]] = None

    @field_validator('alarm_time')
    @classmethod
    def validate_alarm_time_if_provided(cls, value: Optional[datetime]) -> Optional[datetime]:
        """Validate alarm time only if it is provided during update."""
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if value <= now:
                raise ValueError('Alarm time must be in the future')
        return value


class AlarmInDBBase(AlarmBase):
    """Base schema for alarm data as stored in the database."""
    
    id: int
    user_id: int
    snooze_count: int
    max_snooze: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic v2 ORM mode configuration."""
        from_attributes = True


class Alarm(AlarmInDBBase):
    """Public schema representing a full alarm object."""
    pass