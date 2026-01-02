# app/schemas/timetable.py
from pydantic import BaseModel, field_validator, Field
from datetime import datetime, time
from typing import List, Optional

class TimeSlotBase(BaseModel):
    """Base time slot schema."""
    day_of_week: str = Field(..., pattern="^(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$")
    start_time: time
    end_time: time
    course: str = Field(..., min_length=1, max_length=100)
    room: str = Field(..., min_length=1, max_length=50)

    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v: time, info) -> time:
        """Ensure end time is after start time."""
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('End time must be after start time')
        return v

class TimeSlotCreate(TimeSlotBase):
    """Schema for creating a time slot."""
    pass

class TimeSlotUpdate(BaseModel):
    """Schema for updating a time slot."""
    day_of_week: Optional[str] = Field(None, pattern="^(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$")
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    course: Optional[str] = Field(None, min_length=1, max_length=100)
    room: Optional[str] = Field(None, min_length=1, max_length=50)
    is_active: Optional[bool] = None

class TimeSlotResponse(TimeSlotBase):
    """Schema for time slot response."""
    id: int
    timetable_id: int
    is_active: bool

    class Config:
        from_attributes = True

class TimetableBase(BaseModel):
    """Base timetable schema."""
    term: str = Field(..., min_length=1, max_length=50)

class TimetableCreate(TimetableBase):
    """Schema for creating a timetable."""
    pass

class TimetableUpdate(BaseModel):
    """Schema for updating a timetable."""
    term: Optional[str] = Field(None, min_length=1, max_length=50)

class TimetableResponse(TimetableBase):
    """Schema for timetable response."""
    id: int
    user_id: str
    created_at: datetime
    time_slots: List[TimeSlotResponse] = []

    class Config:
        from_attributes = True