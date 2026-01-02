# app/api/v1/endpoints/alarm.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.alarm import AlarmCreate, AlarmUpdate, AlarmResponse
from app.crud import alarm as crud_alarm

router = APIRouter()

@router.get("/", response_model=List[AlarmResponse])
def read_alarms(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_recurring: Optional[bool] = Query(None, description="Filter by recurring status"),
    search: Optional[str] = Query(None, description="Search in title/description"),
    upcoming: Optional[bool] = Query(None, description="Only show upcoming alarms"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[AlarmResponse]:
    """
    Retrieve user's alarms with optional filtering.
    """
    alarms = crud_alarm.get_alarms(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        is_active=is_active,
        is_recurring=is_recurring,
        search=search,
        upcoming=upcoming
    )
    return alarms

@router.post("/", response_model=AlarmResponse, status_code=status.HTTP_201_CREATED)
def create_alarm(
    alarm: AlarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AlarmResponse:
    """
    Create a new alarm.
    """
    return crud_alarm.create_alarm(db=db, alarm=alarm, user_id=current_user.id)

@router.get("/{alarm_id}", response_model=AlarmResponse)
def read_alarm(
    alarm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AlarmResponse:
    """
    Retrieve a specific alarm by ID.
    """
    alarm = crud_alarm.get_alarm(db, alarm_id, current_user.id)
    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm not found"
        )
    return alarm

@router.put("/{alarm_id}", response_model=AlarmResponse)
def update_alarm(
    alarm_id: int,
    alarm_update: AlarmUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AlarmResponse:
    """
    Update an existing alarm.
    """
    alarm = crud_alarm.update_alarm(
        db=db,
        alarm_id=alarm_id,
        alarm_update=alarm_update,
        user_id=current_user.id
    )
    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm not found"
        )
    return alarm

@router.delete("/{alarm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alarm(
    alarm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete an alarm.
    """
    success = crud_alarm.delete_alarm(db, alarm_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm not found"
        )

@router.post("/{alarm_id}/toggle", response_model=AlarmResponse)
def toggle_alarm(
    alarm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AlarmResponse:
    """
    Toggle alarm active status.
    """
    alarm = crud_alarm.toggle_alarm(db, alarm_id, current_user.id)
    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alarm not found"
        )
    return alarm

@router.post("/{alarm_id}/snooze", response_model=AlarmResponse)
def snooze_alarm(
    alarm_id: int,
    snooze_minutes: int = Query(5, ge=1, le=60, description="Minutes to snooze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> AlarmResponse:
    """
    Snooze an alarm.
    """
    alarm = crud_alarm.snooze_alarm(
        db=db,
        alarm_id=alarm_id,
        user_id=current_user.id,
        snooze_minutes=snooze_minutes
    )
    if not alarm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot snooze alarm (inactive, max snoozes reached, or not found)"
        )
    return alarm

@router.get("/upcoming/", response_model=List[AlarmResponse])
def get_upcoming_alarms(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of alarms"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[AlarmResponse]:
    """
    Get upcoming alarms for the user.
    """
    return crud_alarm.get_upcoming_alarms(db, current_user.id, limit)