"""
Tests for subjects endpoints.
"""
import pytest
from fastapi.testclient import TestClient

class TestSubjectsCRUD:
    """Test subjects CRUD operations."""
    
    def test_create_subject(self, client, auth_headers):
        """Test creating a new subject."""
        response = client.post(
            "/api/v1/subjects/",
            json={
                "name": "Mathematics",
                "code": "MATH101",
                "description": "Introduction to Mathematics",
                "color": "#3b82f6",
                "grade_level": "College",
                "term": "Fall 2024",
                "teacher_name": "Dr. Smith"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Mathematics"
        assert data["code"] == "MATH101"
        assert "id" in data
        assert "user_id" in data
    
    def test_create_duplicate_subject_code(self, client, auth_headers):
        """Test creating subject with duplicate code."""
        # Create first subject
        client.post(
            "/api/v1/subjects/",
            json={
                "name": "Physics",
                "code": "PHYS101"
            },
            headers=auth_headers
        )
        
        # Try to create another with same code
        response = client.post(
            "/api/v1/subjects/",
            json={
                "name": "Advanced Physics",
                "code": "PHYS101"  # Same code
            },
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_list_subjects(self, client, auth_headers):
        """Test listing subjects."""
        # Create some subjects
        for i in range(3):
            client.post(
                "/api/v1/subjects/",
                json={
                    "name": f"Subject {i}",
                    "code": f"SUBJ{i}"
                },
                headers=auth_headers
            )
        
        response = client.get(
            "/api/v1/subjects/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "subjects" in data
        assert "total" in data
        assert data["total"] >= 3
    
    def test_list_subjects_with_pagination(self, client, auth_headers):
        """Test subjects pagination."""
        response = client.get(
            "/api/v1/subjects/?page=1&page_size=2",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
    
    def test_list_subjects_with_search(self, client, auth_headers):
        """Test searching subjects."""
        response = client.get(
            "/api/v1/subjects/?search=Mathematics",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_list_subjects_by_grade_level(self, client, auth_headers):
        """Test filtering subjects by grade level."""
        response = client.get(
            "/api/v1/subjects/?grade_level=College",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_list_subjects_by_term(self, client, auth_headers):
        """Test filtering subjects by term."""
        response = client.get(
            "/api/v1/subjects/?term=Fall 2024",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_list_favorite_subjects(self, client, auth_headers):
        """Test filtering favorite subjects."""
        response = client.get(
            "/api/v1/subjects/?is_favorite=true",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_list_active_subjects(self, client, auth_headers):
        """Test getting only active subjects."""
        response = client.get(
            "/api/v1/subjects/?is_active=true",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_get_active_subjects_dropdown(self, client, auth_headers):
        """Test getting active subjects for dropdowns."""
        response = client.get(
            "/api/v1/subjects/active",
            headers=auth_headers
        )
        assert response.status_code == 200
        subjects = response.json()
        assert isinstance(subjects, list)
    
    def test_get_subject_stats(self, client, auth_headers):
        """Test getting subject statistics."""
        response = client.get(
            "/api/v1/subjects/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        stats = response.json()
        assert isinstance(stats, list)
    
    def test_get_single_subject(self, client, auth_headers):
        """Test getting a single subject by ID."""
        # Create a subject first
        create_response = client.post(
            "/api/v1/subjects/",
            json={
                "name": "Chemistry",
                "code": "CHEM101"
            },
            headers=auth_headers
        )
        subject_id = create_response.json()["id"]
        
        response = client.get(
            f"/api/v1/subjects/{subject_id}/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == subject_id
        assert data["name"] == "Chemistry"
    
    def test_get_nonexistent_subject(self, client, auth_headers):
        """Test getting a nonexistent subject."""
        response = client.get(
            "/api/v1/subjects/nonexistent-id/",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_update_subject(self, client, auth_headers):
        """Test updating a subject."""
        # Create a subject
        create_response = client.post(
            "/api/v1/subjects/",
            json={
                "name": "Biology",
                "code": "BIO101"
            },
            headers=auth_headers
        )
        subject_id = create_response.json()["id"]
        
        # Update the subject
        response = client.put(
            f"/api/v1/subjects/{subject_id}/",
            json={
                "name": "Advanced Biology",
                "description": "Updated description"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Advanced Biology"
    
    def test_delete_subject(self, client, auth_headers):
        """Test deleting a subject."""
        # Create a subject
        create_response = client.post(
            "/api/v1/subjects/",
            json={
                "name": "To Be Deleted",
                "code": "DEL101"
            },
            headers=auth_headers
        )
        subject_id = create_response.json()["id"]
        
        # Delete the subject
        response = client.delete(
            f"/api/v1/subjects/{subject_id}/",
            headers=auth_headers
        )
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(
            f"/api/v1/subjects/{subject_id}/",
            headers=auth_headers
        )
        assert get_response.status_code == 404

class TestSubjectActions:
    """Test subject actions like favorite, archive, etc."""
    
    def test_toggle_favorite(self, client, auth_headers):
        """Test toggling subject favorite status."""
        # Create a subject
        create_response = client.post(
            "/api/v1/subjects/",
            json={
                "name": "Art",
                "code": "ART101"
            },
            headers=auth_headers
        )
        subject_id = create_response.json()["id"]
        
        # Toggle favorite
        response = client.post(
            f"/api/v1/subjects/{subject_id}/favorite",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_favorite"] == True
        
        # Toggle again
        response = client.post(
            f"/api/v1/subjects/{subject_id}/favorite",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_favorite"] == False
    
    def test_archive_subject(self, client, auth_headers):
        """Test archiving a subject."""
        # Create a subject
        create_response = client.post(
            "/api/v1/subjects/",
            json={
                "name": "Old Subject",
                "code": "OLD101"
            },
            headers=auth_headers
        )
        subject_id = create_response.json()["id"]
        
        # Archive the subject
        response = client.post(
            f"/api/v1/subjects/{subject_id}/archive",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False
    
    def test_activate_subject(self, client, auth_headers):
        """Test activating a subject."""
        # Create a subject
        create_response = client.post(
            "/api/v1/subjects/",
            json={
                "name": "Inactive Subject",
                "code": "INACT101"
            },
            headers=auth_headers
        )
        subject_id = create_response.json()["id"]
        
        # Archive first
        client.post(
            f"/api/v1/subjects/{subject_id}/archive",
            headers=auth_headers
        )
        
        # Activate the subject
        response = client.post(
            f"/api/v1/subjects/{subject_id}/activate",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == True

