# app/api/v1/endpoints/timetable.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.timetable import (
    TimetableCreate, TimetableUpdate, TimetableResponse,
    TimeSlotCreate, TimeSlotUpdate, TimeSlotResponse
)
from app.crud import timetable as crud_timetable

router = APIRouter()

@router.get("/", response_model=List[TimetableResponse])
def read_timetables(
    term: Optional[str] = Query(None, description="Filter by term"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[TimetableResponse]:
    """
    Retrieve user's timetables with optional filtering.
    """
    timetables, total = crud_timetable.get_user_timetables(
        db=db,
        user_id=current_user.id,
        term=term,
        skip=skip,
        limit=limit
    )
    return timetables

@router.post("/", response_model=TimetableResponse, status_code=status.HTTP_201_CREATED)
def create_timetable(
    timetable: TimetableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TimetableResponse:
    """
    Create a new timetable.
    """
    return crud_timetable.create_timetable(db=db, timetable=timetable, user_id=current_user.id)

@router.get("/{timetable_id}/", response_model=TimetableResponse)
def read_timetable(
    timetable_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TimetableResponse:
    """
    Retrieve a specific timetable by ID.
    """
    timetable = crud_timetable.get_timetable(db, timetable_id, current_user.id)
    if not timetable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timetable not found"
        )
    return timetable

@router.put("/{timetable_id}/", response_model=TimetableResponse)
def update_timetable(
    timetable_id: int,
    timetable_update: TimetableUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TimetableResponse:
    """
    Update an existing timetable.
    """
    update_data = timetable_update.model_dump(exclude_unset=True)
    timetable = crud_timetable.update_timetable(
        db=db,
        timetable_id=timetable_id,
        timetable_update=update_data,
        user_id=current_user.id
    )
    if not timetable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timetable not found"
        )
    return timetable

@router.delete("/{timetable_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_timetable(
    timetable_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a timetable.
    """
    success = crud_timetable.delete_timetable(db, timetable_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timetable not found"
        )

# TimeSlot endpoints
@router.post("/{timetable_id}/slots/", response_model=TimeSlotResponse, status_code=status.HTTP_201_CREATED)
def create_time_slot(
    timetable_id: int,
    slot: TimeSlotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TimeSlotResponse:
    """
    Create a new time slot in a timetable.
    """
    try:
        slot = crud_timetable.create_slot(
            db=db,
            slot=slot,
            timetable_id=timetable_id,
            user_id=current_user.id
        )
        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Timetable not found"
            )
        return slot
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{timetable_id}/slots/", response_model=List[TimeSlotResponse])
def get_timetable_slots(
    timetable_id: int,
    day_of_week: Optional[str] = Query(None, description="Filter by day of week"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[TimeSlotResponse]:
    """
    Get time slots for a timetable.
    """
    slots = crud_timetable.get_slots_by_timetable(
        db=db,
        timetable_id=timetable_id,
        user_id=current_user.id,
        day_of_week=day_of_week,
        is_active=is_active
    )
    return slots

@router.put("/slots/{slot_id}/", response_model=TimeSlotResponse)
def update_time_slot(
    slot_id: int,
    slot_update: TimeSlotUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TimeSlotResponse:
    """
    Update an existing time slot.
    """
    try:
        slot = crud_timetable.update_slot(
            db=db,
            slot_id=slot_id,
            slot_update=slot_update,
            user_id=current_user.id
        )
        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time slot not found"
            )
        return slot
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/slots/{slot_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_time_slot(
    slot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a time slot.
    """
    success = crud_timetable.delete_slot(db, slot_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot not found"
        )

@router.post("/slots/{slot_id}/toggle-active", response_model=TimeSlotResponse)
def toggle_slot_active(
    slot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TimeSlotResponse:
    """
    Toggle time slot active status.
    """
    slot = crud_timetable.toggle_slot_active(db, slot_id, current_user.id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot not found"
        )
    return slot

# Schedule endpoints
@router.get("/daily/", response_model=List[TimeSlotResponse])
def get_daily_schedule(
    target_date: Optional[date] = Query(None, description="Date for schedule (default: today)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[TimeSlotResponse]:
    """
    Get daily schedule for the user.
    """
    if not target_date:
        target_date = date.today()
    
    slots = crud_timetable.get_daily_schedule(db, current_user.id, target_date)
    return slots

@router.get("/weekly/", response_model=Dict[str, List[TimeSlotResponse]])
def get_weekly_schedule(
    start_date: Optional[date] = Query(None, description="Start date for week (default: today)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, List[TimeSlotResponse]]:
    """
    Get weekly schedule for the user.
    """
    if not start_date:
        start_date = date.today()
    
    schedule = crud_timetable.get_weekly_schedule(db, current_user.id, start_date)
    return schedule

@router.get("/current/", response_model=List[TimeSlotResponse])
def get_current_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[TimeSlotResponse]:
    """
    Get classes currently in session.
    """
    slots = crud_timetable.get_current_classes(db, current_user.id)
    return slots

@router.get("/next/", response_model=TimeSlotResponse)
def get_next_class(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Optional[TimeSlotResponse]:
    """
    Get the next upcoming class.
    """
    slot = crud_timetable.get_next_class(db, current_user.id)
    return slot

@router.get("/stats/")
def get_timetable_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get timetable statistics.
    """
    # Get current timetable
    timetables, _ = crud_timetable.get_user_timetables(db, current_user.id, limit=1)
    
    if not timetables:
        return {
            "total_timetables": 0,
            "current_timetable": None,
            "total_slots": 0,
            "active_slots": 0
        }
    
    current_timetable = timetables[0]
    slots = crud_timetable.get_slots_by_timetable(db, current_timetable.id, current_user.id)
    
    return {
        "total_timetables": len(timetables),
        "current_timetable": {
            "id": current_timetable.id,
            "term": current_timetable.term
        },
        "total_slots": len(slots),
        "active_slots": len([s for s in slots if s.is_active]),
        "slots_by_day": {
            day: len([s for s in slots if s.day_of_week == day])
            for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        }
    }