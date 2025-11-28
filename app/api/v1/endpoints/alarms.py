
# app/api/v1/endpoints/alarm.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
# from fastapi.security import OAuth2PasswordBearer
# from jose import JWTError, jwt
from app.schemas.alarm import Alarm, AlarmCreate, AlarmUpdate
from app import crud
from app.db.session import get_db

router = APIRouter()

def get_current_user_id() -> int:
    return 1  # placeholder


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


@router.get("/", response_model=List[Alarm]) 
def read_alarms(
    is_active: Optional[bool] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    alarms = crud.alarm.get_alarms(db, user_id, skip=skip, limit=limit, is_active=is_active)
    return alarms


@router.post("/", response_model=Alarm)
def create_alarm(
    alarm: AlarmCreate,  
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    return crud.alarm.create_alarm(db=db, alarm=alarm, user_id=user_id)


@router.get("/{alarmId}", response_model=Alarm)
def read_alarm(
    alarmId: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    db_alarm = crud.alarm.get_alarm(db, alarmId, user_id)
    if not db_alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    return db_alarm


@router.put("/{alarmId}", response_model=Alarm)
def update_alarm(
    alarmId: int,
    alarm: AlarmUpdate,  # ✅
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    db_alarm = crud.alarm.update_alarm(db, alarmId, alarm, user_id)
    if not db_alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    return db_alarm


@router.delete("/{alarmId}")
def delete_alarm(
    alarmId: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    success = crud.alarm.delete_alarm(db, alarmId, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alarm not found")
    return {"detail": "Alarm deleted"}


@router.post("/{alarmId}/toggle", response_model=Alarm)
def toggle_alarm(
    alarmId: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    db_alarm = crud.alarm.toggle_alarm(db, alarmId, user_id)
    if not db_alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    return db_alarm


@router.post("/{alarmId}/snooze", response_model=Alarm)
def snooze_alarm(
    alarmId: int,
    snooze_minutes: int = 5,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    db_alarm = crud.alarm.snooze_alarm(db, alarmId, user_id, snooze_minutes)
    if not db_alarm:
        raise HTTPException(
            status_code=400,
            detail="Cannot snooze alarm (inactive, max snoozes reached, or not found)"
        )
    return db_alarm