"""
Tests for reminders endpoints.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

class TestRemindersCRUD:
    """Test reminders CRUD operations."""
    
    def test_create_reminder(self, client, auth_headers):
        """Test creating a new reminder."""
        due_date = (datetime.now() + timedelta(days=3)).isoformat()
        
        response = client.post(
            "/api/reminders/",
            json={
                "title": "Submit Assignment",
                "description": "Complete the math assignment",
                "due_date": due_date
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Submit Assignment"
        assert data["is_completed"] == False
        assert "id" in data
    
    def test_list_reminders(self, client, auth_headers):
        """Test listing reminders."""
        response = client.get(
            "/api/reminders/",
            headers=auth_headers
        )
        assert response.status_code == 200
        reminders = response.json()
        assert isinstance(reminders, list)
    
    def test_list_reminders_with_filters(self, client, auth_headers):
        """Test filtering reminders."""
        # Create a reminder first
        due_date = (datetime.now() + timedelta(days=7)).isoformat()
        client.post(
            "/api/reminders/",
            json={
                "title": "High Priority Task",
                "due_date": due_date
            },
            headers=auth_headers
        )
        
        # Filter by completion status
        response = client.get(
            "/api/reminders/?completed=false",
            headers=auth_headers
        )
        assert response.status_code == 200
        reminders = response.json()
        for reminder in reminders:
            assert reminder["is_completed"] == False
    
    def test_filter_reminders_by_status(self, client, auth_headers):
        """Test filtering reminders by completion status."""
        # Filter incomplete
        response = client.get(
            "/api/reminders/?completed=false",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Filter completed
        response = client.get(
            "/api/reminders/?completed=true",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_get_upcoming_reminders(self, client, auth_headers):
        """Test getting upcoming reminders."""
        response = client.get(
            "/api/reminders/upcoming/",
            headers=auth_headers
        )
        assert response.status_code == 200
        reminders = response.json()
        assert isinstance(reminders, list)
    
    def test_get_overdue_reminders(self, client, auth_headers):
        """Test getting overdue reminders."""
        response = client.get(
            "/api/reminders/overdue/",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_get_single_reminder(self, client, auth_headers):
        """Test getting a single reminder by ID."""
        # Create a reminder first
        due_date = (datetime.now() + timedelta(days=10)).isoformat()
        create_response = client.post(
            "/api/reminders/",
            json={
                "title": "Single Reminder",
                "due_date": due_date
            },
            headers=auth_headers
        )
        reminder_id = create_response.json()["id"]
        
        response = client.get(
            f"/api/reminders/{reminder_id}/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == reminder_id
        assert data["title"] == "Single Reminder"
    
    def test_get_nonexistent_reminder(self, client, auth_headers):
        """Test getting a nonexistent reminder."""
        response = client.get(
            "/api/reminders/99999/",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_update_reminder(self, client, auth_headers):
        """Test updating a reminder."""
        # Create a reminder
        due_date = (datetime.now() + timedelta(days=15)).isoformat()
        create_response = client.post(
            "/api/reminders/",
            json={
                "title": "Original Title",
                "due_date": due_date
            },
            headers=auth_headers
        )
        reminder_id = create_response.json()["id"]
        
        # Update the reminder
        response = client.put(
            f"/api/reminders/{reminder_id}/",
            json={
                "title": "Updated Title",
                "description": "Updated description"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
    
    def test_delete_reminder(self, client, auth_headers):
        """Test deleting a reminder."""
        # Create a reminder
        due_date = (datetime.now() + timedelta(days=20)).isoformat()
        create_response = client.post(
            "/api/reminders/",
            json={
                "title": "To Be Deleted",
                "due_date": due_date
            },
            headers=auth_headers
        )
        reminder_id = create_response.json()["id"]
        
        # Delete the reminder
        response = client.delete(
            f"/api/reminders/{reminder_id}/",
            headers=auth_headers
        )
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(
            f"/api/reminders/{reminder_id}/",
            headers=auth_headers
        )
        assert get_response.status_code == 404

class TestReminderActions:
    """Test reminder actions like complete, uncomplete."""
    
    def test_complete_reminder(self, client, auth_headers):
        """Test marking a reminder as complete."""
        # Create a reminder
        due_date = (datetime.now() + timedelta(days=25)).isoformat()
        create_response = client.post(
            "/api/reminders/",
            json={
                "title": "Task to Complete",
                "due_date": due_date
            },
            headers=auth_headers
        )
        reminder_id = create_response.json()["id"]
        
        # Mark as complete
        response = client.post(
            f"/api/reminders/{reminder_id}/complete",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_completed"] == True
    
    def test_uncomplete_reminder(self, client, auth_headers):
        """Test marking a reminder as not completed."""
        # Create a reminder
        due_date = (datetime.now() + timedelta(days=30)).isoformat()
        create_response = client.post(
            "/api/reminders/",
            json={
                "title": "Task to Uncomplete",
                "due_date": due_date
            },
            headers=auth_headers
        )
        reminder_id = create_response.json()["id"]
        
        # Complete it first
        client.post(
            f"/api/reminders/{reminder_id}/complete",
            headers=auth_headers
        )
        
        # Uncomplete it
        response = client.post(
            f"/api/reminders/{reminder_id}/uncomplete",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_completed"] == False
    
    def test_get_reminder_stats(self, client, auth_headers):
        """Test getting reminder statistics."""
        response = client.get(
            "/api/reminders/stats/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "completed" in data
        assert "overdue" in data
        assert "upcoming" in data
        assert "completion_rate" in data
    
    def test_get_todays_reminders(self, client, auth_headers):
        """Test getting today's reminders."""
        response = client.get(
            "/api/reminders/today/",
            headers=auth_headers
        )
        assert response.status_code == 200
        reminders = response.json()
        assert isinstance(reminders, list)

