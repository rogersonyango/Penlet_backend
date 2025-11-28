# app/crud/alarm.py
from sqlalchemy.orm import Session
from app.models.alarm import Alarm as AlarmModel
from app.schemas.alarm import AlarmCreate, AlarmUpdate
from datetime import datetime

def get_alarm(db: Session, alarm_id: int, user_id: int):
    return db.query(AlarmModel).filter(
        AlarmModel.id == alarm_id,
        AlarmModel.user_id == user_id
    ).first()

def get_alarms(db: Session, user_id: int, skip: int = 0, limit: int = 100, is_active: bool = None):
    query = db.query(AlarmModel).filter(AlarmModel.user_id == user_id)
    if is_active is not None:
        query = query.filter(AlarmModel.is_active == is_active)
    return query.offset(skip).limit(limit).all()

def create_alarm(db: Session, alarm: AlarmCreate, user_id: int):
    db_alarm = AlarmModel(**alarm.model_dump(), user_id=user_id)
    db.add(db_alarm)
    db.commit()
    db.refresh(db_alarm)
    return db_alarm

def update_alarm(db: Session, alarm_id: int, alarm: AlarmUpdate, user_id: int):
    db_alarm = get_alarm(db, alarm_id, user_id)
    if not db_alarm:
        return None
    for key, value in alarm.model_dump(exclude_unset=True).items():
        setattr(db_alarm, key, value)
    db.commit()
    db.refresh(db_alarm)
    return db_alarm

def delete_alarm(db: Session, alarm_id: int, user_id: int):
    db_alarm = get_alarm(db, alarm_id, user_id)
    if db_alarm:
        db.delete(db_alarm)
        db.commit()
        return True
    return False

def toggle_alarm(db: Session, alarm_id: int, user_id: int):
    db_alarm = get_alarm(db, alarm_id, user_id)
    if db_alarm:
        db_alarm.is_active = not db_alarm.is_active
        db.commit()
        db.refresh(db_alarm)
        return db_alarm
    return None

def snooze_alarm(db: Session, alarm_id: int, user_id: int, snooze_minutes: int = 5):
    db_alarm = get_alarm(db, alarm_id, user_id)
    if db_alarm and db_alarm.is_active and db_alarm.snooze_count < db_alarm.max_snooze:
        from datetime import timedelta
        db_alarm.alarm_time += timedelta(minutes=snooze_minutes)
        db_alarm.snooze_count += 1
        db.commit()
        db.refresh(db_alarm)
        return db_alarm
    return None