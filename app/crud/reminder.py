# app/crud/reminder.py
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
from app.models.reminder import Reminder as ReminderModel
from app.schemas.reminder import ReminderCreate, ReminderUpdate
from app.models.user import User

def get_reminder(db: Session, reminder_id: int, user_id: str) -> Optional[ReminderModel]:
    """Get a single reminder by ID for a specific user"""
    return db.query(ReminderModel).filter(
        ReminderModel.id == reminder_id,
        ReminderModel.user_id == user_id
    ).first()

def get_reminders(
    db: Session,
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    completed: Optional[bool] = None,
    search: Optional[str] = None,
    due_before: Optional[datetime] = None,
    due_after: Optional[datetime] = None
) -> List[ReminderModel]:
    """Get reminders with optional filters"""
    query = db.query(ReminderModel).filter(ReminderModel.user_id == user_id)
    
    if completed is not None:
        query = query.filter(ReminderModel.is_completed == completed)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                ReminderModel.title.ilike(search_term),
                ReminderModel.description.ilike(search_term)
            )
        )
    
    if due_before:
        query = query.filter(ReminderModel.due_date <= due_before)
    
    if due_after:
        query = query.filter(ReminderModel.due_date >= due_after)
    
    return query.order_by(ReminderModel.due_date).offset(skip).limit(limit).all()

def get_upcoming_reminders(
    db: Session,
    user_id: str,
    days_ahead: int = 7,
    limit: int = 10
) -> List[ReminderModel]:
    """Get upcoming reminders within specified days"""
    now = datetime.now(timezone.utc)
    future_date = now + timedelta(days=days_ahead)
    
    return (
        db.query(ReminderModel)
        .filter(
            ReminderModel.user_id == user_id,
            ReminderModel.is_completed == False,
            ReminderModel.due_date > now,
            ReminderModel.due_date <= future_date
        )
        .order_by(ReminderModel.due_date)
        .limit(limit)
        .all()
    )

def get_overdue_reminders(db: Session, user_id: str) -> List[ReminderModel]:
    """Get overdue reminders"""
    now = datetime.now(timezone.utc)
    
    return (
        db.query(ReminderModel)
        .filter(
            ReminderModel.user_id == user_id,
            ReminderModel.is_completed == False,
            ReminderModel.due_date < now
        )
        .order_by(ReminderModel.due_date)
        .all()
    )

def create_reminder(db: Session, reminder: ReminderCreate, user_id: str) -> ReminderModel:
    """Create a new reminder"""
    db_reminder = ReminderModel(**reminder.model_dump(), user_id=user_id)
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder

def update_reminder(
    db: Session,
    reminder_id: int,
    reminder_update: ReminderUpdate,
    user_id: str
) -> Optional[ReminderModel]:
    """Update an existing reminder"""
    db_reminder = get_reminder(db, reminder_id, user_id)
    
    if not db_reminder:
        return None
    
    update_data = reminder_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(db_reminder, key, value)
    
    db.commit()
    db.refresh(db_reminder)
    return db_reminder

def delete_reminder(db: Session, reminder_id: int, user_id: str) -> bool:
    """Delete a reminder"""
    db_reminder = get_reminder(db, reminder_id, user_id)
    
    if not db_reminder:
        return False
    
    db.delete(db_reminder)
    db.commit()
    return True

def complete_reminder(db: Session, reminder_id: int, user_id: str) -> Optional[ReminderModel]:
    """Mark a reminder as completed"""
    db_reminder = get_reminder(db, reminder_id, user_id)
    
    if not db_reminder:
        return None
    
    db_reminder.is_completed = True
    db.commit()
    db.refresh(db_reminder)
    return db_reminder

def uncomplete_reminder(db: Session, reminder_id: int, user_id: str) -> Optional[ReminderModel]:
    """Mark a reminder as not completed"""
    db_reminder = get_reminder(db, reminder_id, user_id)
    
    if not db_reminder:
        return None
    
    db_reminder.is_completed = False
    db.commit()
    db.refresh(db_reminder)
    return db_reminder

def get_todays_reminders(db: Session, user_id: str) -> List[ReminderModel]:
    """Get reminders due today"""
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    
    return (
        db.query(ReminderModel)
        .filter(
            ReminderModel.user_id == user_id,
            ReminderModel.is_completed == False,
            ReminderModel.due_date >= start_of_day,
            ReminderModel.due_date < end_of_day
        )
        .order_by(ReminderModel.due_date)
        .all()
    )

def get_reminder_stats(db: Session, user_id: str) -> Dict[str, int]:
    """Get reminder statistics for a user"""
    total = db.query(ReminderModel).filter(ReminderModel.user_id == user_id).count()
    completed = db.query(ReminderModel).filter(
        ReminderModel.user_id == user_id,
        ReminderModel.is_completed == True
    ).count()
    overdue = len(get_overdue_reminders(db, user_id))
    upcoming = len(get_upcoming_reminders(db, user_id, days_ahead=30))
    
    return {
        "total": total,
        "completed": completed,
        "overdue": overdue,
        "upcoming": upcoming,
        "completion_rate": round((completed / total * 100) if total > 0 else 0, 2)
    }
