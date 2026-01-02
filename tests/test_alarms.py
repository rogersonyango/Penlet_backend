"""
Tests for alarms endpoints.
"""
import pytest
from datetime import datetime, time, timedelta
from fastapi.testclient import TestClient

class TestAlarmsCRUD:
    """Test alarms CRUD operations."""
    
    def test_create_alarm(self, client, auth_headers):
        """Test creating a new alarm."""
        # Calculate a time in the future
        alarm_time = (datetime.now() + timedelta(hours=1)).isoformat()
        
        response = client.post(
            "/api/alarms/",
            json={
                "title": "Morning Workout",
                "description": "Time to exercise",
                "alarm_time": alarm_time,
                "is_recurring": False
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Morning Workout"
        assert data["is_recurring"] == False
        assert "id" in data
    
    def test_create_recurring_alarm(self, client, auth_headers):
        """Test creating a recurring alarm."""
        alarm_time = (datetime.now() + timedelta(hours=2)).isoformat()
        
        response = client.post(
            "/api/alarms/",
            json={
                "title": "Weekly Meeting",
                "alarm_time": alarm_time,
                "is_recurring": True,
                "recurrence_pattern": {"frequency": "weekly", "interval": 1}
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Weekly Meeting"
        assert data["is_recurring"] == True
    
    def test_list_alarms(self, client, auth_headers):
        """Test listing alarms."""
        response = client.get(
            "/api/alarms/",
            headers=auth_headers
        )
        assert response.status_code == 200
        alarms = response.json()
        assert isinstance(alarms, list)
    
    def test_list_alarms_with_filters(self, client, auth_headers):
        """Test filtering alarms."""
        # Create an alarm first
        alarm_time = (datetime.now() + timedelta(hours=3)).isoformat()
        client.post(
            "/api/alarms/",
            json={
                "title": "Active Alarm",
                "alarm_time": alarm_time,
                "is_active": True
            },
            headers=auth_headers
        )
        
        # Filter by active status
        response = client.get(
            "/api/alarms/?is_active=true",
            headers=auth_headers
        )
        assert response.status_code == 200
        alarms = response.json()
        for alarm in alarms:
            assert alarm["is_active"] == True
    
    def test_filter_alarms_by_recurring(self, client, auth_headers):
        """Test filtering alarms by recurring status."""
        response = client.get(
            "/api/alarms/?is_recurring=true",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_get_upcoming_alarms(self, client, auth_headers):
        """Test getting upcoming alarms."""
        response = client.get(
            "/api/alarms/upcoming/",
            headers=auth_headers
        )
        assert response.status_code == 200
        alarms = response.json()
        assert isinstance(alarms, list)
    
    def test_get_single_alarm(self, client, auth_headers):
        """Test getting a single alarm by ID."""
        # Create an alarm first
        alarm_time = (datetime.now() + timedelta(hours=4)).isoformat()
        create_response = client.post(
            "/api/alarms/",
            json={
                "title": "Single Alarm",
                "alarm_time": alarm_time
            },
            headers=auth_headers
        )
        alarm_id = create_response.json()["id"]
        
        response = client.get(
            f"/api/alarms/{alarm_id}/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == alarm_id
        assert data["title"] == "Single Alarm"
    
    def test_get_nonexistent_alarm(self, client, auth_headers):
        """Test getting a nonexistent alarm."""
        response = client.get(
            "/api/alarms/99999/",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_update_alarm(self, client, auth_headers):
        """Test updating an alarm."""
        # Create an alarm
        alarm_time = (datetime.now() + timedelta(hours=5)).isoformat()
        create_response = client.post(
            "/api/alarms/",
            json={
                "title": "Original Title",
                "alarm_time": alarm_time
            },
            headers=auth_headers
        )
        alarm_id = create_response.json()["id"]
        
        # Update the alarm
        response = client.put(
            f"/api/alarms/{alarm_id}/",
            json={
                "title": "Updated Title",
                "description": "Updated description"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
    
    def test_delete_alarm(self, client, auth_headers):
        """Test deleting an alarm."""
        # Create an alarm
        alarm_time = (datetime.now() + timedelta(hours=6)).isoformat()
        create_response = client.post(
            "/api/alarms/",
            json={
                "title": "To Be Deleted",
                "alarm_time": alarm_time
            },
            headers=auth_headers
        )
        alarm_id = create_response.json()["id"]
        
        # Delete the alarm
        response = client.delete(
            f"/api/alarms/{alarm_id}/",
            headers=auth_headers
        )
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(
            f"/api/alarms/{alarm_id}/",
            headers=auth_headers
        )
        assert get_response.status_code == 404

class TestAlarmActions:
    """Test alarm actions like toggle and snooze."""
    
    def test_toggle_alarm(self, client, auth_headers):
        """Test toggling alarm active status."""
        # Create an alarm
        alarm_time = (datetime.now() + timedelta(hours=7)).time()
        
        # First create with datetime instead of time
        alarm_datetime = (datetime.now() + timedelta(hours=7)).isoformat()
        create_response = client.post(
            "/api/alarms/",
            json={
                "title": "Toggle Test",
                "alarm_time": alarm_datetime,
                "is_active": True
            },
            headers=auth_headers
        )
        alarm_id = create_response.json()["id"]
        
        # Toggle off
        response = client.post(
            f"/api/alarms/{alarm_id}/toggle",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False
        
        # Toggle on
        response = client.post(
            f"/api/alarms/{alarm_id}/toggle",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == True
    
    def test_snooze_alarm(self, client, auth_headers):
        """Test snoozing an alarm."""
        # Create an alarm
        alarm_datetime = (datetime.now() + timedelta(hours=1)).isoformat()
        create_response = client.post(
            "/api/alarms/",
            json={
                "title": "Snooze Test",
                "alarm_time": alarm_datetime,
                "is_active": True
            },
            headers=auth_headers
        )
        alarm_id = create_response.json()["id"]
        original_alarm_time = create_response.json()["alarm_time"]
        
        # Snooze for 10 minutes
        response = client.post(
            f"/api/alarms/{alarm_id}/snooze?snooze_minutes=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Alarm should be snoozed (snooze_count increased)
        assert data["snooze_count"] == 1
        # Alarm time should be delayed
        assert data["alarm_time"] != original_alarm_time
    
    def test_snooze_with_custom_duration(self, client, auth_headers):
        """Test snoozing with different durations."""
        # Create an alarm
        alarm_datetime = (datetime.now() + timedelta(hours=2)).isoformat()
        create_response = client.post(
            "/api/alarms/",
            json={
                "title": "Custom Snooze",
                "alarm_time": alarm_datetime,
                "is_active": True
            },
            headers=auth_headers
        )
        alarm_id = create_response.json()["id"]
        
        # Snooze for 15 minutes
        response = client.post(
            f"/api/alarms/{alarm_id}/snooze?snooze_minutes=15",
            headers=auth_headers
        )
        assert response.status_code == 200

