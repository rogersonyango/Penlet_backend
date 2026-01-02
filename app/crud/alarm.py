# app/crud/alarm.py
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from app.models.alarm import Alarm as AlarmModel
from app.schemas.alarm import AlarmCreate, AlarmUpdate
from app.models.user import User

def get_alarm(db: Session, alarm_id: int, user_id: str) -> Optional[AlarmModel]:
    """Get a single alarm by ID for a specific user"""
    return db.query(AlarmModel).filter(
        AlarmModel.id == alarm_id,
        AlarmModel.user_id == user_id
    ).first()

def get_alarms(
    db: Session,
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    is_recurring: Optional[bool] = None,
    search: Optional[str] = None,
    upcoming: Optional[bool] = None
) -> List[AlarmModel]:
    """Get alarms with optional filters"""
    query = db.query(AlarmModel).filter(AlarmModel.user_id == user_id)
    
    if is_active is not None:
        query = query.filter(AlarmModel.is_active == is_active)
    
    if is_recurring is not None:
        query = query.filter(AlarmModel.is_recurring == is_recurring)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                AlarmModel.title.ilike(search_term),
                AlarmModel.description.ilike(search_term)
            )
        )
    
    if upcoming:
        now = datetime.utcnow()
        query = query.filter(AlarmModel.alarm_time > now)
    
    return query.order_by(AlarmModel.alarm_time).offset(skip).limit(limit).all()

def get_upcoming_alarms(db: Session, user_id: str, limit: int = 10) -> List[AlarmModel]:
    """Get upcoming alarms for the user"""
    now = datetime.utcnow()
    return (
        db.query(AlarmModel)
        .filter(
            AlarmModel.user_id == user_id,
            AlarmModel.is_active == True,
            AlarmModel.alarm_time > now
        )
        .order_by(AlarmModel.alarm_time)
        .limit(limit)
        .all()
    )

def create_alarm(db: Session, alarm: AlarmCreate, user_id: str) -> AlarmModel:
    """Create a new alarm"""
    db_alarm = AlarmModel(**alarm.model_dump(), user_id=user_id)
    db.add(db_alarm)
    db.commit()
    db.refresh(db_alarm)
    return db_alarm

def update_alarm(
    db: Session,
    alarm_id: int,
    alarm_update: AlarmUpdate,
    user_id: str
) -> Optional[AlarmModel]:
    """Update an existing alarm"""
    db_alarm = get_alarm(db, alarm_id, user_id)
    
    if not db_alarm:
        return None
    
    update_data = alarm_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(db_alarm, key, value)
    
    db.commit()
    db.refresh(db_alarm)
    return db_alarm

def delete_alarm(db: Session, alarm_id: int, user_id: str) -> bool:
    """Delete an alarm"""
    db_alarm = get_alarm(db, alarm_id, user_id)
    
    if not db_alarm:
        return False
    
    db.delete(db_alarm)
    db.commit()
    return True

def toggle_alarm(db: Session, alarm_id: int, user_id: str) -> Optional[AlarmModel]:
    """Toggle alarm active status"""
    db_alarm = get_alarm(db, alarm_id, user_id)
    
    if not db_alarm:
        return None
    
    db_alarm.is_active = not db_alarm.is_active
    db.commit()
    db.refresh(db_alarm)
    return db_alarm

def snooze_alarm(
    db: Session,
    alarm_id: int,
    user_id: str,
    snooze_minutes: int = 5
) -> Optional[AlarmModel]:
    """Snooze an alarm"""
    db_alarm = get_alarm(db, alarm_id, user_id)
    
    if not db_alarm or not db_alarm.is_active:
        return None
    
    if db_alarm.snooze_count >= db_alarm.max_snooze:
        return None
    
    # Snooze the alarm
    db_alarm.alarm_time += timedelta(minutes=snooze_minutes)
    db_alarm.snooze_count += 1
    db.commit()
    db.refresh(db_alarm)
    return db_alarm

def reset_snooze_count(db: Session, alarm_id: int, user_id: str) -> Optional[AlarmModel]:
    """Reset snooze count for an alarm"""
    db_alarm = get_alarm(db, alarm_id, user_id)
    
    if not db_alarm:
        return None
    
    db_alarm.snooze_count = 0
    db.commit()
    db.refresh(db_alarm)
    return db_alarm

def get_due_alarms(db: Session) -> List[AlarmModel]:
    """Get all alarms that are due (for scheduler/worker)"""
    now = datetime.utcnow()
    return (
        db.query(AlarmModel)
        .filter(
            AlarmModel.is_active == True,
            AlarmModel.alarm_time <= now
        )
        .all()
    )