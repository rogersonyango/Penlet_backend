# app/crud/timetable.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, date, time, timedelta
from typing import List, Optional, Tuple, Dict, Any
from app.models.timetable import Timetable, TimeSlot
from app.schemas.timetable import TimetableCreate, TimeSlotCreate, TimeSlotUpdate
from app.models.user import User

def get_timetable(db: Session, timetable_id: int, user_id: str) -> Optional[Timetable]:
    """Get a timetable by ID for a specific user"""
    return db.query(Timetable).filter(
        Timetable.id == timetable_id,
        Timetable.user_id == user_id
    ).first()

def get_user_timetables(
    db: Session,
    user_id: str,
    term: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
) -> Tuple[List[Timetable], int]:
    """Get timetables for a user with optional term filter"""
    query = db.query(Timetable).filter(Timetable.user_id == user_id)
    
    if term:
        query = query.filter(Timetable.term.ilike(f"%{term}%"))
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    timetables = query.order_by(Timetable.created_at.desc()).offset(skip).limit(limit).all()
    
    return timetables, total

def create_timetable(db: Session, timetable: TimetableCreate, user_id: str) -> Timetable:
    """Create a new timetable"""
    db_timetable = Timetable(**timetable.model_dump(), user_id=user_id)
    db.add(db_timetable)
    db.commit()
    db.refresh(db_timetable)
    return db_timetable

def update_timetable(
    db: Session,
    timetable_id: int,
    timetable_update: dict,
    user_id: str
) -> Optional[Timetable]:
    """Update a timetable"""
    db_timetable = get_timetable(db, timetable_id, user_id)
    
    if not db_timetable:
        return None
    
    for key, value in timetable_update.items():
        if value is not None:
            setattr(db_timetable, key, value)
    
    db.commit()
    db.refresh(db_timetable)
    return db_timetable

def delete_timetable(db: Session, timetable_id: int, user_id: str) -> bool:
    """Delete a timetable"""
    db_timetable = get_timetable(db, timetable_id, user_id)
    
    if not db_timetable:
        return False
    
    db.delete(db_timetable)
    db.commit()
    return True

# TimeSlot CRUD functions
def create_slot(
    db: Session,
    slot: TimeSlotCreate,
    timetable_id: int,
    user_id: str
) -> Optional[TimeSlot]:
    """Create a new time slot"""
    # Verify the timetable belongs to the user
    timetable = get_timetable(db, timetable_id, user_id)
    if not timetable:
        return None
    
    # Check for overlapping slots
    overlapping_slots = db.query(TimeSlot).filter(
        TimeSlot.timetable_id == timetable_id,
        TimeSlot.day_of_week == slot.day_of_week,
        TimeSlot.is_active == True,
        or_(
            and_(
                TimeSlot.start_time <= slot.start_time,
                TimeSlot.end_time > slot.start_time
            ),
            and_(
                TimeSlot.start_time < slot.end_time,
                TimeSlot.end_time >= slot.end_time
            ),
            and_(
                TimeSlot.start_time >= slot.start_time,
                TimeSlot.end_time <= slot.end_time
            )
        )
    ).first()
    
    if overlapping_slots:
        raise ValueError("Time slot overlaps with existing slot")
    
    db_slot = TimeSlot(**slot.model_dump(), timetable_id=timetable_id)
    db.add(db_slot)
    db.commit()
    db.refresh(db_slot)
    return db_slot

def get_slot(db: Session, slot_id: int, user_id: str) -> Optional[TimeSlot]:
    """Get a time slot by ID"""
    return (
        db.query(TimeSlot)
        .join(Timetable)
        .filter(
            TimeSlot.id == slot_id,
            Timetable.user_id == user_id
        )
        .first()
    )

def get_slots_by_timetable(
    db: Session,
    timetable_id: int,
    user_id: str,
    day_of_week: Optional[str] = None,
    is_active: Optional[bool] = None
) -> List[TimeSlot]:
    """Get time slots for a timetable"""
    query = (
        db.query(TimeSlot)
        .join(Timetable)
        .filter(
            TimeSlot.timetable_id == timetable_id,
            Timetable.user_id == user_id
        )
    )
    
    if day_of_week:
        query = query.filter(TimeSlot.day_of_week == day_of_week.lower())
    
    if is_active is not None:
        query = query.filter(TimeSlot.is_active == is_active)
    
    return query.order_by(TimeSlot.day_of_week, TimeSlot.start_time).all()

def update_slot(
    db: Session,
    slot_id: int,
    slot_update: TimeSlotUpdate,
    user_id: str
) -> Optional[TimeSlot]:
    """Update a time slot"""
    db_slot = get_slot(db, slot_id, user_id)
    
    if not db_slot:
        return None
    
    # If updating time or day, check for overlaps
    update_data = slot_update.model_dump(exclude_unset=True)
    
    if 'start_time' in update_data or 'end_time' in update_data or 'day_of_week' in update_data:
        start_time = update_data.get('start_time', db_slot.start_time)
        end_time = update_data.get('end_time', db_slot.end_time)
        day_of_week = update_data.get('day_of_week', db_slot.day_of_week)
        
        # Check for overlapping slots (excluding current slot)
        overlapping_slots = db.query(TimeSlot).filter(
            TimeSlot.timetable_id == db_slot.timetable_id,
            TimeSlot.id != slot_id,
            TimeSlot.day_of_week == day_of_week,
            TimeSlot.is_active == True,
            or_(
                and_(
                    TimeSlot.start_time <= start_time,
                    TimeSlot.end_time > start_time
                ),
                and_(
                    TimeSlot.start_time < end_time,
                    TimeSlot.end_time >= end_time
                ),
                and_(
                    TimeSlot.start_time >= start_time,
                    TimeSlot.end_time <= end_time
                )
            )
        ).first()
        
        if overlapping_slots:
            raise ValueError("Updated time slot would overlap with existing slot")
    
    for key, value in update_data.items():
        if value is not None:
            setattr(db_slot, key, value)
    
    db.commit()
    db.refresh(db_slot)
    return db_slot

def delete_slot(db: Session, slot_id: int, user_id: str) -> bool:
    """Delete a time slot"""
    db_slot = get_slot(db, slot_id, user_id)
    
    if not db_slot:
        return False
    
    db.delete(db_slot)
    db.commit()
    return True

def toggle_slot_active(db: Session, slot_id: int, user_id: str) -> Optional[TimeSlot]:
    """Toggle time slot active status"""
    db_slot = get_slot(db, slot_id, user_id)
    
    if not db_slot:
        return None
    
    db_slot.is_active = not db_slot.is_active
    db.commit()
    db.refresh(db_slot)
    return db_slot

# Schedule helper functions
def get_daily_schedule(
    db: Session,
    user_id: str,
    date: date
) -> List[TimeSlot]:
    """Get schedule for a specific day"""
    # Convert date to day of week
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    day_of_week = days[date.weekday()].lower()
    
    # Get current term or most recent timetable
    current_term = "Current Term"  # You might want to implement term detection logic
    
    return (
        db.query(TimeSlot)
        .join(Timetable)
        .filter(
            Timetable.user_id == user_id,
            Timetable.term == current_term,
            TimeSlot.day_of_week == day_of_week,
            TimeSlot.is_active == True
        )
        .order_by(TimeSlot.start_time)
        .all()
    )

def get_weekly_schedule(
    db: Session,
    user_id: str,
    start_date: date
) -> Dict[str, List[TimeSlot]]:
    """Get schedule for a week"""
    result = {}
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    # Get current term or most recent timetable
    current_term = "Current Term"
    
    slots = (
        db.query(TimeSlot)
        .join(Timetable)
        .filter(
            Timetable.user_id == user_id,
            Timetable.term == current_term,
            TimeSlot.is_active == True
        )
        .order_by(TimeSlot.day_of_week, TimeSlot.start_time)
        .all()
    )
    
    # Group slots by day
    for slot in slots:
        day = slot.day_of_week.lower()
        if day not in result:
            result[day] = []
        result[day].append(slot)
    
    # Ensure all days are in the result
    for day in days:
        if day not in result:
            result[day] = []
    
    return result

def get_current_classes(
    db: Session,
    user_id: str,
    current_time: Optional[datetime] = None
) -> List[TimeSlot]:
    """Get classes currently in session"""
    if current_time is None:
        current_time = datetime.now()
    
    day_of_week = current_time.strftime('%A').lower()
    current_time_only = current_time.time()
    
    return (
        db.query(TimeSlot)
        .join(Timetable)
        .filter(
            Timetable.user_id == user_id,
            TimeSlot.day_of_week == day_of_week,
            TimeSlot.is_active == True,
            TimeSlot.start_time <= current_time_only,
            TimeSlot.end_time > current_time_only
        )
        .order_by(TimeSlot.start_time)
        .all()
    )

def get_next_class(
    db: Session,
    user_id: str,
    current_time: Optional[datetime] = None
) -> Optional[TimeSlot]:
    """Get the next upcoming class"""
    if current_time is None:
        current_time = datetime.now()
    
    day_of_week = current_time.strftime('%A').lower()
    current_time_only = current_time.time()
    
    # First check for classes later today
    next_class = (
        db.query(TimeSlot)
        .join(Timetable)
        .filter(
            Timetable.user_id == user_id,
            TimeSlot.day_of_week == day_of_week,
            TimeSlot.is_active == True,
            TimeSlot.start_time > current_time_only
        )
        .order_by(TimeSlot.start_time)
        .first()
    )
    
    if next_class:
        return next_class
    
    # If no classes today, get first class tomorrow
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    current_day_index = days.index(day_of_week)
    next_day_index = (current_day_index + 1) % 7
    
    for i in range(1, 7):  # Check next 6 days
        check_day_index = (current_day_index + i) % 7
        check_day = days[check_day_index]
        
        next_class = (
            db.query(TimeSlot)
            .join(Timetable)
            .filter(
                Timetable.user_id == user_id,
                TimeSlot.day_of_week == check_day,
                TimeSlot.is_active == True
            )
            .order_by(TimeSlot.start_time)
            .first()
        )
        
        if next_class:
            return next_class
    
    return None