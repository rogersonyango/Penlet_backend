#app/crud/timetable.py

from sqlalchemy.orm import Session
from app.models import timetable as models
from app.schemas import timetable as schemas
from datetime import datetime, timedelta
from typing import List, Optional

def get_timetable(db: Session, timetable_id: int):
    return db.query(models.Timetable).filter(models.Timetable.id == timetable_id).first()

def get_user_timetables(db: Session, user_id: int, term: Optional[str] = None):
    query = db.query(models.Timetable).filter(models.Timetable.user_id == user_id)
    if term:
        query = query.filter(models.Timetable.term == term)
    return query.all()

def create_timetable(db: Session, timetable: schemas.TimetableCreate):
    db_timetable = models.Timetable(**timetable.model_dump())
    db.add(db_timetable)
    db.commit()
    db.refresh(db_timetable)
    return db_timetable

def update_timetable(db: Session, timetable_id: int, timetable_data: dict):
    db_timetable = get_timetable(db, timetable_id)
    if db_timetable:
        for key, value in timetable_data.items():
            setattr(db_timetable, key, value)
        db.commit()
        db.refresh(db_timetable)
    return db_timetable

def delete_timetable(db: Session, timetable_id: int):
    db_timetable = get_timetable(db, timetable_id)
    if db_timetable:
        db.delete(db_timetable)
        db.commit()
    return db_timetable

# Slot-related CRUD
def create_slot(db: Session, slot: schemas.TimeSlotCreate, timetable_id: int):
    db_slot = models.TimeSlot(**slot.model_dump(), timetable_id=timetable_id)
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot

def get_slot(db: Session, slot_id: int):
    return db.query(models.TimeSlot).filter(models.TimeSlot.id == slot_id).first()

def update_slot(db: Session, slot_id: int, slot_data: dict):
    db_slot = get_slot(db, slot_id)
    if db_slot:
        for key, value in slot_data.items():
            setattr(db_slot, key, value)
        db.commit()
        db.refresh(db_slot)
    return db_slot

def delete_slot(db: Session, slot_id: int):
    db_slot = get_slot(db, slot_id)
    if db_slot:
        db.delete(db_slot)
        db.commit()
    return db_slot

# Daily/Weekly helpers
def get_daily_schedule(db: Session, user_id: int, date: datetime):
    start = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return db.query(models.TimeSlot)\
        .join(models.Timetable)\
        .filter(models.Timetable.user_id == user_id,
                models.TimeSlot.start_time >= start,
                models.TimeSlot.end_time <= end,
                models.TimeSlot.is_active == True).all()

def get_weekly_schedule(db: Session, user_id: int, start_date: datetime):
    end_date = start_date + timedelta(days=7)
    return db.query(models.TimeSlot)\
        .join(models.Timetable)\
        .filter(models.Timetable.user_id == user_id,
                models.TimeSlot.start_time >= start_date,
                models.TimeSlot.start_time < end_date,
                models.TimeSlot.is_active == True).all()