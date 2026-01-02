# app/schemas/alarm.py
from pydantic import BaseModel, field_validator, Field
from datetime import datetime, timezone
from typing import Optional, Dict, Any

class AlarmBase(BaseModel):
    """Base alarm schema."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    alarm_time: datetime
    is_active: bool = True
    is_recurring: bool = False
    recurrence_pattern: Optional[Dict[str, Any]] = None

    @field_validator('alarm_time')
    @classmethod
    def validate_alarm_time(cls, v: datetime) -> datetime:
        """Ensure alarm time is in the future."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if v <= now:
            raise ValueError('Alarm time must be in the future')
        return v

    @field_validator('recurrence_pattern')
    @classmethod
    def validate_recurrence_pattern(cls, v: Optional[Dict[str, Any]], info) -> Optional[Dict[str, Any]]:
        """Validate recurrence pattern if alarm is recurring."""
        if info.data.get('is_recurring') and v is None:
            raise ValueError('Recurrence pattern required for recurring alarms')
        if v is not None:
            required_keys = {'frequency', 'interval'}
            if not required_keys.issubset(v.keys()):
                raise ValueError(f'Recurrence pattern must include: {required_keys}')
        return v

class AlarmCreate(AlarmBase):
    """Schema for creating an alarm."""
    max_snooze: int = Field(default=3, ge=0, le=10)

class AlarmUpdate(BaseModel):
    """Schema for updating an alarm."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    alarm_time: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[Dict[str, Any]] = None
    max_snooze: Optional[int] = Field(None, ge=0, le=10)

    @field_validator('alarm_time')
    @classmethod
    def validate_alarm_time(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate alarm time if provided."""
        if v is not None:
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            if v <= now:
                raise ValueError('Alarm time must be in the future')
        return v

class AlarmResponse(BaseModel):
    """Schema for alarm response."""
    id: int
    user_id: str
    title: str
    description: Optional[str]
    alarm_time: datetime
    is_active: bool
    is_recurring: bool
    recurrence_pattern: Optional[Dict[str, Any]]
    snooze_count: int
    max_snooze: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True