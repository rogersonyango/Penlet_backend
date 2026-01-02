# app/models/timetable.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Time
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class Timetable(Base):
    __tablename__ = "timetables"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Timetable Information
    term = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="timetables")
    time_slots = relationship("TimeSlot", back_populates="timetable", cascade="all, delete-orphan")


class TimeSlot(Base):
    __tablename__ = "time_slots"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key
    timetable_id = Column(Integer, ForeignKey("timetables.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Time Slot Information
    day_of_week = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    course = Column(String)
    room = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    timetable = relationship("Timetable", back_populates="time_slots")