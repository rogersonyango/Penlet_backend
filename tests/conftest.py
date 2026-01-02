"""
Pytest configuration and fixtures for Penlet API tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Generator
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import Base, get_db
from main import app
from app.models.user import User
from app.core.security import get_password_hash
from app.api.deps import get_current_user

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    """Override database dependency for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user():
    """Override current user dependency for tests."""
    user = User(
        id="test-user-id",
        email="test@example.com",
        username="testuser",
        password_hash=get_password_hash("TestPassword123"),
        user_type="student",
        is_active=True
    )
    return user

# Apply overrides
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

@pytest.fixture(scope="session")
def db_engine():
    """Provide database engine for tests."""
    return engine

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Provide database session for tests."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Provide test client."""
    def override_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user."""
    user = User(
        id="test-user-id",
        email="test@example.com",
        username="testuser",
        password_hash=get_password_hash("TestPassword123"),
        user_type="student",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def auth_token(test_user):
    """Generate authentication token for test user."""
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": test_user.id})
    return token

@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """Provide authentication headers."""
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture(scope="function")
def test_timetable(db_session, test_user):
    """Create a test timetable."""
    from app.models.timetable import Timetable
    timetable = Timetable(
        term="Fall 2024",
        user_id=test_user.id
    )
    db_session.add(timetable)
    db_session.commit()
    db_session.refresh(timetable)
    return timetable

@pytest.fixture(scope="function")
def test_deck(db_session, test_user):
    """Create a test flashcard deck."""
    from app.models.flashcard import Deck
    deck = Deck(
        title="Test Deck",
        subject="Test Subject",
        level="Beginner",
        is_public=False
    )
    db_session.add(deck)
    db_session.commit()
    db_session.refresh(deck)
    return deck

