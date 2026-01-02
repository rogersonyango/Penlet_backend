"""
Tests for resource endpoints.
"""
import pytest
from fastapi.testclient import TestClient

class TestResourcesCRUD:
    """Test resources CRUD operations."""
    
    def test_create_resource(self, client, auth_headers):
        """Test creating a new resource."""
        response = client.post(
            "/api/resource/",
            json={
                "title": "Python Documentation",
                "description": "Official Python 3 documentation",
                "resource_type": "link",
                "url": "https://docs.python.org/3/",
                "subject_id": None,
                "tags": ["programming", "python", "documentation"]
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Python Documentation"
        assert data["resource_type"] == "link"
        assert "id" in data
    
    def test_create_document_resource(self, client, auth_headers):
        """Test creating a document resource."""
        response = client.post(
            "/api/resource/",
            json={
                "title": "Lecture Notes",
                "description": "Week 1 lecture notes",
                "resource_type": "document",
                "file_path": "/uploads/notes/lecture1.pdf",
                "subject_id": None
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Lecture Notes"
        assert data["resource_type"] == "document"
    
    def test_list_resources(self, client, auth_headers):
        """Test listing resources."""
        response = client.get(
            "/api/resource/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
    
    def test_list_resources_with_filters(self, client, auth_headers):
        """Test filtering resources."""
        # Create a resource
        client.post(
            "/api/resource/",
            json={
                "title": "Tutorial Link",
                "resource_type": "link",
                "url": "https://example.com"
            },
            headers=auth_headers
        )
        
        # Filter by type
        response = client.get(
            "/api/resource/?resource_type=link",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for resource in data["resources"]:
            assert resource["resource_type"] == "link"
    
    def test_filter_resources_by_subject(self, client, auth_headers):
        """Test filtering resources by subject."""
        response = client.get(
            "/api/resource/?subject_id=test-id",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_search_resources(self, client, auth_headers):
        """Test searching resources."""
        response = client.get(
            "/api/resource/?search=Python",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_get_public_resources(self, client):
        """Test getting public resources."""
        response = client.get(
            "/api/resource/public"
        )
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data
    
    def test_get_featured_resources(self, client):
        """Test getting featured resources."""
        response = client.get(
            "/api/resource/featured"
        )
        assert response.status_code == 200
        resources = response.json()
        assert isinstance(resources, list)
    
    def test_get_single_resource(self, client, auth_headers):
        """Test getting a single resource by ID."""
        # Create a resource first
        create_response = client.post(
            "/api/resource/",
            json={
                "title": "Single Resource",
                "resource_type": "link",
                "url": "https://example.com/single"
            },
            headers=auth_headers
        )
        resource_id = create_response.json()["id"]
        
        response = client.get(
            f"/api/resource/{resource_id}/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == resource_id
        assert data["title"] == "Single Resource"
    
    def test_get_nonexistent_resource(self, client, auth_headers):
        """Test getting a nonexistent resource."""
        response = client.get(
            "/api/resource/99999/",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_update_resource(self, client, auth_headers):
        """Test updating a resource."""
        # Create a resource
        create_response = client.post(
            "/api/resource/",
            json={
                "title": "Original Title",
                "resource_type": "link",
                "url": "https://example.com/original"
            },
            headers=auth_headers
        )
        resource_id = create_response.json()["id"]
        
        # Update the resource
        response = client.put(
            f"/api/resource/{resource_id}/",
            json={
                "title": "Updated Title",
                "description": "Updated description"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
    
    def test_delete_resource(self, client, auth_headers):
        """Test deleting a resource."""
        # Create a resource
        create_response = client.post(
            "/api/resource/",
            json={
                "title": "To Be Deleted",
                "resource_type": "link",
                "url": "https://example.com/delete"
            },
            headers=auth_headers
        )
        resource_id = create_response.json()["id"]
        
        # Delete the resource
        response = client.delete(
            f"/api/resource/{resource_id}/",
            headers=auth_headers
        )
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(
            f"/api/resource/{resource_id}/",
            headers=auth_headers
        )
        assert get_response.status_code == 404

class TestResourceActions:
    """Test resource actions like favorite, share."""
    
    def test_toggle_resource_favorite(self, client, auth_headers):
        """Test toggling resource favorite status."""
        # Create a resource
        create_response = client.post(
            "/api/resource/",
            json={
                "title": "Favorite Test",
                "resource_type": "link",
                "url": "https://example.com/favorite"
            },
            headers=auth_headers
        )
        resource_id = create_response.json()["id"]
        
        # Toggle favorite
        response = client.post(
            f"/api/resource/{resource_id}/favorite",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_favorite"] == True
        
        # Toggle again
        response = client.post(
            f"/api/resource/{resource_id}/favorite",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_favorite"] == False
    
    def test_share_resource(self, client, auth_headers):
        """Test sharing a resource."""
        # Create a resource
        create_response = client.post(
            "/api/resource/",
            json={
                "title": "Share Test",
                "resource_type": "link",
                "url": "https://example.com/share"
            },
            headers=auth_headers
        )
        resource_id = create_response.json()["id"]
        
        # Share the resource
        response = client.post(
            f"/api/resource/{resource_id}/share",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "share_token" in data
        assert "share_url" in data
    
    def test_get_shared_resource(self, client, auth_headers):
        """Test accessing a shared resource."""
        # Create and share a resource
        create_response = client.post(
            "/api/resource/",
            json={
                "title": "Shared Resource",
                "resource_type": "link",
                "url": "https://example.com/shared"
            },
            headers=auth_headers
        )
        resource_id = create_response.json()["id"]
        
        share_response = client.post(
            f"/api/resource/{resource_id}/share",
            headers=auth_headers
        )
        share_token = share_response.json()["share_token"]
        
        # Access shared resource
        response = client.get(
            f"/api/resource/shared/{share_token}/"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == resource_id

