"""
Tests for authentication endpoints.
"""
import pytest
from fastapi.testclient import TestClient

class TestAuthRegistration:
    """Test user registration endpoints."""
    
    def test_register_user_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/users/registration",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "NewPassword123",
                "full_name": "New User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["username"] == "newuser"
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        response = client.post(
            "/api/v1/users/registration",
            json={
                "email": "test@example.com",  # Already exists
                "username": "anotheruser",
                "password": "AnotherPassword123"
            }
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_invalid_password(self, client):
        """Test registration with invalid password."""
        response = client.post(
            "/api/v1/users/registration",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "weak"  # No uppercase, no digit
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_register_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = client.post(
            "/api/v1/users/registration",
            json={
                "email": "test@example.com"
                # Missing username and password
            }
        )
        assert response.status_code == 422

class TestAuthLogin:
    """Test user login endpoints."""
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/users/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/users/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123"
            }
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post(
            "/api/v1/users/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Password123"
            }
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

class TestAuthToken:
    """Test token-related functionality."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Welcome to Penlet API!"
        assert data["status"] == "running"
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

