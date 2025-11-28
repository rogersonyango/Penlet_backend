# app/utils/auth.py
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User

def get_current_user(db: Session = Depends(get_db)) -> User:
    """
    Simulated authentication dependency.
    In production, replace this with real JWT/OAuth2 logic.
    For demo purposes, returns a default admin user (id=1).
    """
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        # Create a default admin user if none exists
        user = User(
            email="admin@example.com",
            name="Default Admin",
            role="admin"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user