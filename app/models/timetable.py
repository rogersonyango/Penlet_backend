#app/models/timetable.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Timetable(Base):
    __tablename__ = "timetables"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)  # or ForeignKey if you have User model
    term = Column(String, index=True)
    created_at = Column(DateTime)

class TimeSlot(Base):
    __tablename__ = "time_slots"
    id = Column(Integer, primary_key=True, index=True)
    timetable_id = Column(Integer, ForeignKey("timetables.id"))
    day_of_week = Column(String)  # e.g., "monday"
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    course = Column(String)
    room = Column(String)
    is_active = Column(Boolean, default=True)