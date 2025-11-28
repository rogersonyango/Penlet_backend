# app/api/v1/endpoints/reminder.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
# from fastapi.security import OAuth2PasswordBearer
# from jose import JWTError, jwt

from app.schemas.reminder import Reminder, ReminderCreate, ReminderUpdate
from app import crud
from app.db.session import get_db

router = APIRouter()

def get_current_user_id() -> int:
    return 1


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# SECRET_KEY = "your-secret-key"
# ALGORITHM = "HS256"


# def get_current_user_id(
#     token: str = Depends(oauth2_scheme),
#     db: Session = Depends(get_db)
# ) -> int:
#     """Decode JWT token and return user ID."""
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id: str = payload.get("sub")
#         if user_id is None:
#             raise credentials_exception
#         return int(user_id)
#     except JWTError:
#         raise credentials_exception

@router.get("/", response_model=List[Reminder])
def read_reminders(
    completed: Optional[bool] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    reminders = crud.reminder.get_reminders(db, user_id, skip=skip, limit=limit, completed=completed)
    return reminders

@router.post("/", response_model=Reminder)
def create_reminder(
    reminder: ReminderCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return crud.reminder.create_reminder(db=db, reminder=reminder, user_id=user_id)

@router.get("/{reminderId}", response_model=Reminder)
def read_reminder(
    reminderId: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    db_reminder = crud.reminder.get_reminder(db, reminderId, user_id)
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return db_reminder

@router.put("/{reminderId}", response_model=Reminder)
def update_reminder(
    reminderId: int,
    reminder: ReminderUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    db_reminder = crud.reminder.update_reminder(db, reminderId, reminder, user_id)
    if not db_reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return db_reminder

@router.delete("/{reminderId}")
def delete_reminder(
    reminderId: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    success = crud.reminder.delete_reminder(db, reminderId, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"detail": "Reminder deleted"}

@router.post("/{reminderId}/complete", response_model=Reminder)
def complete_reminder(
    reminderId: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    db_reminder = crud.reminder.complete_reminder(db, reminderId, user_id)
    if not db_reminder:
        raise HTTPException(status_code=400, detail="Reminder not found or already completed")
    return db_reminder

@router.get("/upcoming/", response_model=List[Reminder])
def get_upcoming_reminders(
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    reminders = crud.reminder.get_upcoming_reminders(db, user_id, limit=limit)
    return reminders