# app/api/v1/endpoints/reminder.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.reminder import ReminderCreate, ReminderUpdate, ReminderResponse
from app.crud import reminder as crud_reminder

router = APIRouter()

@router.get("/", response_model=List[ReminderResponse])
def read_reminders(
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    search: Optional[str] = Query(None, description="Search in title/description"),
    due_before: Optional[datetime] = Query(None, description="Filter by due date before"),
    due_after: Optional[datetime] = Query(None, description="Filter by due date after"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ReminderResponse]:
    """
    Retrieve user's reminders with optional filtering.
    """
    reminders = crud_reminder.get_reminders(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        completed=completed,
        search=search,
        due_before=due_before,
        due_after=due_after
    )
    return reminders

@router.post("/", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
    reminder: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ReminderResponse:
    """
    Create a new reminder.
    """
    return crud_reminder.create_reminder(db=db, reminder=reminder, user_id=current_user.id)

@router.get("/{reminder_id}", response_model=ReminderResponse)
def read_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ReminderResponse:
    """
    Retrieve a specific reminder by ID.
    """
    reminder = crud_reminder.get_reminder(db, reminder_id, current_user.id)
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    return reminder

@router.put("/{reminder_id}", response_model=ReminderResponse)
def update_reminder(
    reminder_id: int,
    reminder_update: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ReminderResponse:
    """
    Update an existing reminder.
    """
    reminder = crud_reminder.update_reminder(
        db=db,
        reminder_id=reminder_id,
        reminder_update=reminder_update,
        user_id=current_user.id
    )
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )
    return reminder

@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a reminder.
    """
    success = crud_reminder.delete_reminder(db, reminder_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found"
        )

@router.post("/{reminder_id}/complete", response_model=ReminderResponse)
def complete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ReminderResponse:
    """
    Mark a reminder as completed.
    """
    reminder = crud_reminder.complete_reminder(db, reminder_id, current_user.id)
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reminder not found or already completed"
        )
    return reminder

@router.post("/{reminder_id}/uncomplete", response_model=ReminderResponse)
def uncomplete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ReminderResponse:
    """
    Mark a reminder as not completed.
    """
    reminder = crud_reminder.uncomplete_reminder(db, reminder_id, current_user.id)
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reminder not found or not completed"
        )
    return reminder

@router.get("/upcoming/", response_model=List[ReminderResponse])
def get_upcoming_reminders(
    days_ahead: int = Query(7, ge=1, le=90, description="Days to look ahead"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of reminders"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ReminderResponse]:
    """
    Get upcoming reminders within specified days.
    """
    reminders = crud_reminder.get_upcoming_reminders(
        db=db,
        user_id=current_user.id,
        days_ahead=days_ahead,
        limit=limit
    )
    return reminders

@router.get("/overdue/", response_model=List[ReminderResponse])
def get_overdue_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ReminderResponse]:
    """
    Get overdue reminders.
    """
    reminders = crud_reminder.get_overdue_reminders(db, current_user.id)
    return reminders

@router.get("/today/", response_model=List[ReminderResponse])
def get_todays_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[ReminderResponse]:
    """
    Get reminders due today.
    """
    reminders = crud_reminder.get_todays_reminders(db, current_user.id)
    return reminders

@router.get("/stats/")
def get_reminder_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get reminder statistics for the user.
    """
    stats = crud_reminder.get_reminder_stats(db, current_user.id)
    return stats