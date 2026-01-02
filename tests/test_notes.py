"""
Tests for notes endpoints.
"""
import pytest
from fastapi.testclient import TestClient

class TestNotesCRUD:
    """Test notes CRUD operations."""
    
    def test_create_note(self, client, auth_headers):
        """Test creating a new note."""
        response = client.post(
            "/api/notes/",
            json={
                "title": "My First Note",
                "content": "This is the content of my first note.",
                "subject": "General"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "My First Note"
        assert data["content"] == "This is the content of my first note."
        assert "id" in data
        assert "author_id" in data
    
    def test_create_note_with_tags(self, client, auth_headers):
        """Test creating a note with tags."""
        response = client.post(
            "/api/notes/",
            json={
                "title": "Tagged Note",
                "content": "This note has tags.",
                "tags": ["important", "study", "python"]
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "tags" in data
    
    def test_list_notes(self, client, auth_headers):
        """Test listing notes."""
        # Create some notes first
        for i in range(3):
            client.post(
                "/api/notes/",
                json={
                    "title": f"Note {i}",
                    "content": f"Content {i}"
                },
                headers=auth_headers
            )
        
        response = client.get(
            "/api/notes/",
            headers=auth_headers
        )
        assert response.status_code == 200
        notes = response.json()
        assert isinstance(notes, list)
        assert len(notes) >= 3
    
    def test_list_notes_with_pagination(self, client, auth_headers):
        """Test notes pagination."""
        response = client.get(
            "/api/notes/?skip=0&limit=2",
            headers=auth_headers
        )
        assert response.status_code == 200
        notes = response.json()
        assert len(notes) <= 2
    
    def test_get_single_note(self, client, auth_headers):
        """Test getting a single note by ID."""
        # Create a note first
        create_response = client.post(
            "/api/notes/",
            json={
                "title": "Single Note",
                "content": "Content for single note test"
            },
            headers=auth_headers
        )
        note_id = create_response.json()["id"]
        
        response = client.get(
            f"/api/notes/{note_id}/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == note_id
        assert data["title"] == "Single Note"
    
    def test_update_note(self, client, auth_headers):
        """Test updating a note."""
        # Create a note
        create_response = client.post(
            "/api/notes/",
            json={
                "title": "Original Title",
                "content": "Original content"
            },
            headers=auth_headers
        )
        note_id = create_response.json()["id"]
        
        # Update the note
        response = client.put(
            f"/api/notes/{note_id}/",
            json={
                "title": "Updated Title",
                "content": "Updated content"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated content"
    
    def test_delete_note(self, client, auth_headers):
        """Test deleting a note."""
        # Create a note
        create_response = client.post(
            "/api/notes/",
            json={
                "title": "To Be Deleted",
                "content": "This note will be deleted"
            },
            headers=auth_headers
        )
        note_id = create_response.json()["id"]
        
        # Delete the note
        response = client.delete(
            f"/api/notes/{note_id}/",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify deletion
        get_response = client.get(
            f"/api/notes/{note_id}/",
            headers=auth_headers
        )
        assert get_response.status_code == 404
    
    def test_search_notes(self, client, auth_headers):
        """Test searching notes."""
        # Create notes with specific content
        client.post(
            "/api/notes/",
            json={
                "title": "Python Tutorial",
                "content": "Learn Python programming"
            },
            headers=auth_headers
        )
        
        response = client.get(
            "/api/notes/?search=Python",
            headers=auth_headers
        )
        assert response.status_code == 200
        notes = response.json()
        # Should contain notes matching search
    
    def test_filter_notes_by_subject(self, client, auth_headers):
        """Test filtering notes by subject."""
        # Create notes with subjects
        client.post(
            "/api/notes/",
            json={
                "title": "Math Note",
                "content": "Mathematics content",
                "subject": "Mathematics"
            },
            headers=auth_headers
        )
        
        response = client.get(
            "/api/notes/?subject=Mathematics",
            headers=auth_headers
        )
        assert response.status_code == 200
        notes = response.json()
        for note in notes:
            assert note["subject"] == "Mathematics"

