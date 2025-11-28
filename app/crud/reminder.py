# app/crud/reminder.py
from sqlalchemy.orm import Session
from app.models.reminder import Reminder as ReminderModel
from app.schemas.reminder import ReminderCreate, ReminderUpdate
from datetime import datetime, timezone

def get_reminder(db: Session, reminder_id: int, user_id: int):
    return db.query(ReminderModel).filter(
        ReminderModel.id == reminder_id,
        ReminderModel.user_id == user_id
    ).first()

def get_reminders(db: Session, user_id: int, skip: int = 0, limit: int = 100, completed: bool = None):
    query = db.query(ReminderModel).filter(ReminderModel.user_id == user_id)
    if completed is not None:
        query = query.filter(ReminderModel.is_completed == completed)
    return query.order_by(ReminderModel.due_date).offset(skip).limit(limit).all()

def get_upcoming_reminders(db: Session, user_id: int, limit: int = 10):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return (
        db.query(ReminderModel)
        .filter(
            ReminderModel.user_id == user_id,
            ReminderModel.is_completed == False,
            ReminderModel.due_date > now
        )
        .order_by(ReminderModel.due_date)
        .limit(limit)
        .all()
    )

def create_reminder(db: Session, reminder: ReminderCreate, user_id: int):
    db_reminder = ReminderModel(**reminder.model_dump(), user_id=user_id)
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder

def update_reminder(db: Session, reminder_id: int, reminder: ReminderUpdate, user_id: int):
    db_reminder = get_reminder(db, reminder_id, user_id)
    if not db_reminder:
        return None
    update_data = reminder.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(db_reminder, key, value)
    db.commit()
    db.refresh(db_reminder)
    return db_reminder

def delete_reminder(db: Session, reminder_id: int, user_id: int):
    db_reminder = get_reminder(db, reminder_id, user_id)
    if db_reminder:
        db.delete(db_reminder)
        db.commit()
        return True
    return False

def complete_reminder(db: Session, reminder_id: int, user_id: int):
    db_reminder = get_reminder(db, reminder_id, user_id)
    if db_reminder and not db_reminder.is_completed:
        db_reminder.is_completed = True
        db.commit()
        db.refresh(db_reminder)
        return db_reminder
    return None