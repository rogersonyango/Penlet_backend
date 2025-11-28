from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.crud import user as crud_user
from app.core.security import create_access_token

router = APIRouter(prefix="/users", tags=["authentication"])

@router.post("/registration", response_model=TokenResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    if crud_user.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    db_user = crud_user.create_user(db, user)
    
    # Create token
    access_token = create_access_token(data={"sub": db_user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }

@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = crud_user.authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }