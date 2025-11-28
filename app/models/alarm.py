# app/models/alarm.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Alarm(Base):
    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)  # or use ForeignKey if you have a User model
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    alarm_time = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)  # e.g., {"frequency": "daily", "interval": 1}
    snooze_count = Column(Integer, default=0)
    max_snooze = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)