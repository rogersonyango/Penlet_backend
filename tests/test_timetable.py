"""
Tests for timetable endpoints.
"""
import pytest
from datetime import time
from fastapi.testclient import TestClient

class TestTimetableCRUD:
    """Test basic timetable CRUD operations."""
    
    def test_create_timetable(self, client, auth_headers):
        """Test creating a new timetable."""
        response = client.post(
            "/api/v1/timetable/",
            json={"term": "Spring 2025"},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["term"] == "Spring 2025"
        assert "id" in data
        assert "user_id" in data
    
    def test_create_multiple_timetables(self, client, auth_headers):
        """Test creating multiple timetables."""
        # Create first timetable
        response1 = client.post(
            "/api/v1/timetable/",
            json={"term": "Fall 2024"},
            headers=auth_headers
        )
        assert response1.status_code == 201
        
        # Create second timetable
        response2 = client.post(
            "/api/v1/timetable/",
            json={"term": "Spring 2025"},
            headers=auth_headers
        )
        assert response2.status_code == 201
        
        # List should show both
        list_response = client.get(
            "/api/v1/timetable/",
            headers=auth_headers
        )
        assert list_response.status_code == 200
        timetables = list_response.json()
        assert len(timetables) >= 2
    
    def test_get_timetables_list(self, client, auth_headers, test_timetable):
        """Test getting list of timetables."""
        response = client.get(
            "/api/v1/timetable/",
            headers=auth_headers
        )
        assert response.status_code == 200
        timetables = response.json()
        assert isinstance(timetables, list)
    
    def test_get_timetables_with_pagination(self, client, auth_headers):
        """Test timetables pagination."""
        # Create multiple timetables
        for i in range(3):
            client.post(
                "/api/v1/timetable/",
                json={"term": f"Term {i}"},
                headers=auth_headers
            )
        
        # Test skip/limit
        response = client.get(
            "/api/v1/timetable/?skip=0&limit=2",
            headers=auth_headers
        )
        assert response.status_code == 200
        timetables = response.json()
        assert len(timetables) <= 2
    
    def test_get_single_timetable(self, client, auth_headers, test_timetable):
        """Test getting a single timetable by ID."""
        response = client.get(
            f"/api/v1/timetable/{test_timetable.id}/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_timetable.id
        assert data["term"] == test_timetable.term
    
    def test_get_nonexistent_timetable(self, client, auth_headers):
        """Test getting a nonexistent timetable."""
        response = client.get(
            "/api/v1/timetable/99999/",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_update_timetable(self, client, auth_headers, test_timetable):
        """Test updating a timetable."""
        response = client.put(
            f"/api/v1/timetable/{test_timetable.id}/",
            json={"term": "Updated Term"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["term"] == "Updated Term"
    
    def test_delete_timetable(self, client, auth_headers, test_timetable):
        """Test deleting a timetable."""
        response = client.delete(
            f"/api/v1/timetable/{test_timetable.id}/",
            headers=auth_headers
        )
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(
            f"/api/v1/timetable/{test_timetable.id}/",
            headers=auth_headers
        )
        assert get_response.status_code == 404

class TestTimeSlots:
    """Test time slot operations."""
    
    def test_create_time_slot(self, client, auth_headers, test_timetable):
        """Test creating a time slot."""
        response = client.post(
            f"/api/v1/timetable/{test_timetable.id}/slots/",
            json={
                "day_of_week": "monday",
                "start_time": "09:00:00",
                "end_time": "10:30:00",
                "course": "Introduction to Programming",
                "room": "Room 101"
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["day_of_week"] == "monday"
        assert data["course"] == "Introduction to Programming"
        assert data["room"] == "Room 101"
    
    def test_create_time_slot_invalid_time(self, client, auth_headers, test_timetable):
        """Test creating a time slot with invalid time (end before start)."""
        response = client.post(
            f"/api/v1/timetable/{test_timetable.id}/slots/",
            json={
                "day_of_week": "monday",
                "start_time": "10:00:00",
                "end_time": "09:00:00",  # Invalid: end before start
                "course": "Test Course",
                "room": "Room 101"
            },
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_create_time_slot_invalid_day(self, client, auth_headers, test_timetable):
        """Test creating a time slot with invalid day."""
        response = client.post(
            f"/api/v1/timetable/{test_timetable.id}/slots/",
            json={
                "day_of_week": "funday",  # Invalid day
                "start_time": "09:00:00",
                "end_time": "10:00:00",
                "course": "Test Course",
                "room": "Room 101"
            },
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_get_time_slots(self, client, auth_headers, test_timetable):
        """Test getting time slots for a timetable."""
        # Create a time slot first
        client.post(
            f"/api/v1/timetable/{test_timetable.id}/slots/",
            json={
                "day_of_week": "tuesday",
                "start_time": "14:00:00",
                "end_time": "15:30:00",
                "course": "Data Structures",
                "room": "Room 202"
            },
            headers=auth_headers
        )
        
        response = client.get(
            f"/api/v1/timetable/{test_timetable.id}/slots/",
            headers=auth_headers
        )
        assert response.status_code == 200
        slots = response.json()
        assert isinstance(slots, list)
    
    def test_filter_slots_by_day(self, client, auth_headers, test_timetable):
        """Test filtering time slots by day of week."""
        # Create slots for different days
        for day in ["monday", "wednesday", "friday"]:
            client.post(
                f"/api/v1/timetable/{test_timetable.id}/slots/",
                json={
                    "day_of_week": day,
                    "start_time": "10:00:00",
                    "end_time": "11:00:00",
                    "course": f"Course on {day}",
                    "room": "Room 101"
                },
                headers=auth_headers
            )
        
        # Filter by monday
        response = client.get(
            f"/api/v1/timetable/{test_timetable.id}/slots/?day_of_week=monday",
            headers=auth_headers
        )
        assert response.status_code == 200
        slots = response.json()
        for slot in slots:
            assert slot["day_of_week"] == "monday"
    
    def test_update_time_slot(self, client, auth_headers, test_timetable):
        """Test updating a time slot."""
        # Create a slot
        create_response = client.post(
            f"/api/v1/timetable/{test_timetable.id}/slots/",
            json={
                "day_of_week": "wednesday",
                "start_time": "11:00:00",
                "end_time": "12:30:00",
                "course": "Algorithms",
                "room": "Room 303"
            },
            headers=auth_headers
        )
        slot_id = create_response.json()["id"]
        
        # Update the slot
        response = client.put(
            f"/api/v1/timetable/slots/{slot_id}/",
            json={
                "course": "Advanced Algorithms",
                "room": "Room 404"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["course"] == "Advanced Algorithms"
        assert data["room"] == "Room 404"
    
    def test_delete_time_slot(self, client, auth_headers, test_timetable):
        """Test deleting a time slot."""
        # Create a slot
        create_response = client.post(
            f"/api/v1/timetable/{test_timetable.id}/slots/",
            json={
                "day_of_week": "thursday",
                "start_time": "15:00:00",
                "end_time": "16:30:00",
                "course": "To Be Deleted",
                "room": "Room 101"
            },
            headers=auth_headers
        )
        slot_id = create_response.json()["id"]
        
        # Delete the slot
        response = client.delete(
            f"/api/v1/timetable/slots/{slot_id}/",
            headers=auth_headers
        )
        assert response.status_code == 204
    
    def test_toggle_slot_active(self, client, auth_headers, test_timetable):
        """Test toggling time slot active status."""
        # Create a slot
        create_response = client.post(
            f"/api/v1/timetable/{test_timetable.id}/slots/",
            json={
                "day_of_week": "friday",
                "start_time": "09:00:00",
                "end_time": "10:00:00",
                "course": "Toggle Test",
                "room": "Room 101"
            },
            headers=auth_headers
        )
        slot_id = create_response.json()["id"]
        
        # Toggle off
        response = client.post(
            f"/api/v1/timetable/slots/{slot_id}/toggle-active",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False

class TestScheduleEndpoints:
    """Test schedule-related endpoints."""
    
    def test_get_daily_schedule(self, client, auth_headers, test_timetable):
        """Test getting daily schedule."""
        response = client.get(
            "/api/v1/timetable/daily/",
            headers=auth_headers
        )
        assert response.status_code == 200
        schedule = response.json()
        assert isinstance(schedule, list)
    
    def test_get_weekly_schedule(self, client, auth_headers, test_timetable):
        """Test getting weekly schedule."""
        response = client.get(
            "/api/v1/timetable/weekly/",
            headers=auth_headers
        )
        assert response.status_code == 200
        schedule = response.json()
        assert isinstance(schedule, dict)
        # Check for all days
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in days:
            assert day in schedule
    
    def test_get_current_classes(self, client, auth_headers):
        """Test getting current classes."""
        response = client.get(
            "/api/v1/timetable/current/",
            headers=auth_headers
        )
        assert response.status_code == 200
        classes = response.json()
        assert isinstance(classes, list)
    
    def test_get_next_class(self, client, auth_headers):
        """Test getting next class."""
        response = client.get(
            "/api/v1/timetable/next/",
            headers=auth_headers
        )
        assert response.status_code == 200
        # Can be null if no upcoming classes
    
    def test_get_timetable_stats(self, client, auth_headers, test_timetable):
        """Test getting timetable statistics."""
        response = client.get(
            "/api/v1/timetable/stats/",
            headers=auth_headers
        )
        assert response.status_code == 200
        stats = response.json()
        assert "total_timetables" in stats
        assert "total_slots" in stats
        assert "active_slots" in stats
        assert "slots_by_day" in stats

