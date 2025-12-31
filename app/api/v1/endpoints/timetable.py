# app/api/v1/endpoints/timetable.py

"""
Timetable API endpoints for managing user timetables and time slots.
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

# Import schemas
from app.schemas.timetable import (
    Timetable,
    TimetableCreate,
    TimetableBase,
    TimeSlot,
    TimeSlotCreate,
    TimeSlotBase
)

# Import CRUD functions with aliases
from app.crud.timetable import (
    get_timetable as crud_get_timetable,
    get_user_timetables as crud_get_user_timetables,
    create_timetable as crud_create_timetable,
    update_timetable as crud_update_timetable,
    delete_timetable as crud_delete_timetable,
    create_slot as crud_create_slot,
    update_slot as crud_update_slot,
    delete_slot as crud_delete_slot,
    get_daily_schedule as crud_get_daily_schedule,
    get_weekly_schedule as crud_get_weekly_schedule
)

from app.db.session import get_db

router = APIRouter(prefix="/api/timetable", tags=["Timetable"])


def _parse_date(date_str: str, param_name: str) -> datetime:
    """Helper to safely parse ISO date strings."""
    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {param_name} format. Expected ISO 8601 (e.g., '2025-12-02')."
        )


@router.get("/", response_model=List[Timetable])
def read_timetables(
    user_id: int,
    term: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Retrieve all timetables for a user, optionally filtered by term."""
    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id must be a positive integer"
        )
    try:
        return crud_get_user_timetables(db, user_id=user_id, term=term)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching timetables"
        )


@router.post("/", response_model=Timetable, status_code=status.HTTP_201_CREATED)
def create_timetable(
    timetable: TimetableCreate,
    db: Session = Depends(get_db)
):
    """Create a new timetable for a user."""
    if timetable.user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id must be a positive integer"
        )
    try:
        return crud_create_timetable(db=db, timetable=timetable)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Timetable with this user_id and term may already exist"
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create timetable"
        )


@router.get("/{timetable_id}/", response_model=Timetable)
def read_timetable(timetable_id: int, db: Session = Depends(get_db)):
    """Fetch a specific timetable by ID."""
    if timetable_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="timetable_id must be a positive integer"
        )
    try:
        timetable = crud_get_timetable(db, timetable_id)
        if not timetable:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Timetable not found"
            )
        return timetable
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching timetable"
        )


@router.put("/{timetable_id}/", response_model=Timetable)
def update_timetable(
    timetable_id: int,
    timetable: TimetableBase,
    db: Session = Depends(get_db)
):
    """Update an existing timetable."""
    if timetable_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="timetable_id must be a positive integer"
        )
    try:
        updated = crud_update_timetable(db, timetable_id, timetable.model_dump())
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Timetable not found"
            )
        return updated
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Update conflicts with existing data"
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update timetable"
        )


@router.delete("/{timetable_id}/")
def delete_timetable(timetable_id: int, db: Session = Depends(get_db)):
    """Delete a timetable by ID."""
    if timetable_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="timetable_id must be a positive integer"
        )
    try:
        if not crud_delete_timetable(db, timetable_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Timetable not found"
            )
        return {"detail": "Timetable deleted"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete timetable"
        )


@router.get("/daily/", response_model=List[TimeSlot])
def get_daily_schedule(
    user_id: int,
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get today's (or specified date's) time slots for a user."""
    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id must be a positive integer"
        )
    try:
        target_date = _parse_date(date, "date") if date else datetime.utcnow()
        return crud_get_daily_schedule(db, user_id, target_date)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching daily schedule"
        )


@router.get("/weekly/", response_model=List[TimeSlot])
def get_weekly_schedule(
    user_id: int,
    start_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get the weekly schedule starting from today (or a given date)."""
    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id must be a positive integer"
        )
    try:
        target_start = _parse_date(start_date, "start_date") if start_date else datetime.utcnow()
        return crud_get_weekly_schedule(db, user_id, target_start)
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while fetching weekly schedule"
        )


@router.post("/slots/", response_model=TimeSlot, status_code=status.HTTP_201_CREATED)
def add_time_slot(
    slot: TimeSlotCreate,
    timetable_id: int,
    db: Session = Depends(get_db)
):
    """Add a new time slot to a timetable."""
    if timetable_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="timetable_id must be a positive integer"
        )
    try:
        return crud_create_slot(db, slot, timetable_id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot conflicts with existing slot (e.g., overlapping time)"
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add time slot"
        )


@router.put("/slots/{slot_id}/", response_model=TimeSlot)
def update_time_slot(
    slot_id: int,
    slot: TimeSlotBase,
    db: Session = Depends(get_db)
):
    """Update an existing time slot."""
    if slot_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="slot_id must be a positive integer"
        )
    try:
        updated = crud_update_slot(db, slot_id, slot.model_dump())
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time slot not found"
            )
        return updated
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Updated slot conflicts with another time slot"
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update time slot"
        )


@router.delete("/slots/{slot_id}/")
def delete_time_slot(slot_id: int, db: Session = Depends(get_db)):
    """Delete a time slot by ID."""
    if slot_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="slot_id must be a positive integer"
        )
    try:
        if not crud_delete_slot(db, slot_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Time slot not found"
            )
        return {"detail": "Time slot deleted"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete time slot"
        )