# app/schemas/timetable.py

from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class TimeSlotBase(BaseModel):
    day_of_week: str
    start_time: datetime
    end_time: datetime
    course: str
    room: str

class TimeSlotCreate(TimeSlotBase):
    pass

class TimeSlot(TimeSlotBase):
    id: int
    timetable_id: int
    is_active: bool

    class Config:
        from_attributes = True  # for SQLAlchemy compatibility (Pydantic v2)

class TimetableBase(BaseModel):
    user_id: int
    term: str

class TimetableCreate(TimetableBase):
    pass

class Timetable(TimetableBase):
    id: int
    created_at: datetime
    slots: List[TimeSlot] = []

    class Config:
        from_attributes = True