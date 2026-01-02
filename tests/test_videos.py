"""
Tests for videos endpoints.
"""
import pytest
from fastapi.testclient import TestClient

class TestVideosCRUD:
    """Test videos CRUD operations."""
    
    def test_create_video(self, client, auth_headers):
        """Test creating a new video."""
        response = client.post(
            "/api/v1/videos/",
            json={
                "title": "Introduction to Python",
                "video_url": "https://youtube.com/watch?v=test",
                "description": "Learn Python basics",
                "duration": 3600,
                "video_type": "youtube"
            },
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Introduction to Python"
        assert "id" in data
    
    def test_list_videos(self, client, auth_headers):
        """Test listing videos."""
        response = client.get(
            "/api/v1/videos/",
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "videos" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
    
    def test_list_videos_with_search(self, client, auth_headers):
        """Test searching videos."""
        response = client.get(
            "/api/v1/videos/",
            params={"user_id": "test-user-id", "search": "Python"},
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_list_videos_by_type(self, client, auth_headers):
        """Test filtering videos by type."""
        response = client.get(
            "/api/v1/videos/",
            params={"user_id": "test-user-id", "video_type": "youtube"},
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_list_public_videos(self, client):
        """Test listing public videos."""
        response = client.get(
            "/api/v1/videos/public"
        )
        assert response.status_code == 200
        data = response.json()
        assert "videos" in data
    
    def test_get_featured_videos(self, client):
        """Test getting featured videos."""
        response = client.get(
            "/api/v1/videos/featured"
        )
        assert response.status_code == 200
        videos = response.json()
        assert isinstance(videos, list)
    
    def test_get_single_video(self, client, auth_headers):
        """Test getting a single video by ID."""
        # Create a video first
        create_response = client.post(
            "/api/v1/videos/",
            json={
                "title": "Test Video",
                "video_url": "https://youtube.com/watch?v=test123"
            },
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        video_id = create_response.json()["id"]
        
        response = client.get(
            f"/api/v1/videos/{video_id}",
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == video_id
        assert data["title"] == "Test Video"
    
    def test_update_video(self, client, auth_headers):
        """Test updating a video."""
        # Create a video
        create_response = client.post(
            "/api/v1/videos/",
            json={
                "title": "Original Title",
                "video_url": "https://youtube.com/watch?v=original"
            },
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        video_id = create_response.json()["id"]
        
        # Update the video
        response = client.put(
            f"/api/v1/videos/{video_id}",
            json={
                "title": "Updated Title",
                "description": "Updated description"
            },
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
    
    def test_delete_video(self, client, auth_headers):
        """Test deleting a video."""
        # Create a video
        create_response = client.post(
            "/api/v1/videos/",
            json={
                "title": "To Be Deleted",
                "video_url": "https://youtube.com/watch?v=delete"
            },
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        video_id = create_response.json()["id"]
        
        # Delete the video
        response = client.delete(
            f"/api/v1/videos/{video_id}",
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        assert response.status_code == 204
    
    def test_toggle_video_favorite(self, client, auth_headers):
        """Test toggling video favorite status."""
        # Create a video
        create_response = client.post(
            "/api/v1/videos/",
            json={
                "title": "Favorite Test",
                "video_url": "https://youtube.com/watch?v=fav"
            },
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        video_id = create_response.json()["id"]
        
        # Toggle favorite
        response = client.post(
            f"/api/v1/videos/{video_id}/favorite",
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_favorite"] == True

class TestVideoProgress:
    """Test video progress functionality."""
    
    def test_update_video_progress(self, client, auth_headers):
        """Test updating video progress."""
        # Create a video
        create_response = client.post(
            "/api/v1/videos/",
            json={
                "title": "Progress Test",
                "video_url": "https://youtube.com/watch?v=progress"
            },
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        video_id = create_response.json()["id"]
        
        # Update progress
        response = client.post(
            f"/api/v1/videos/{video_id}/progress",
            json={
                "current_time": 1800,
                "completion_percentage": 50
            },
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == video_id
        assert data["current_time"] == 1800
    
    def test_get_video_progress(self, client, auth_headers):
        """Test getting video progress."""
        # Create a video
        create_response = client.post(
            "/api/v1/videos/",
            json={
                "title": "Get Progress Test",
                "video_url": "https://youtube.com/watch?v=getprogress"
            },
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        video_id = create_response.json()["id"]
        
        # Update progress first
        client.post(
            f"/api/v1/videos/{video_id}/progress",
            json={"current_time": 600, "completion_percentage": 20},
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        
        # Get progress
        response = client.get(
            f"/api/v1/videos/{video_id}/progress",
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["video_id"] == video_id
    
    def test_get_all_progress(self, client, auth_headers):
        """Test getting all video progress for user."""
        response = client.get(
            "/api/v1/videos/progress/all",
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        assert response.status_code == 200
        progress_list = response.json()
        assert isinstance(progress_list, list)

class TestVideoComments:
    """Test video comments functionality."""
    
    def test_add_comment(self, client, auth_headers):
        """Test adding a comment to a video."""
        # Create a video
        create_response = client.post(
            "/api/v1/videos/",
            json={
                "title": "Comment Test",
                "video_url": "https://youtube.com/watch?v=comment"
            },
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        video_id = create_response.json()["id"]
        
        # Add comment
        response = client.post(
            f"/api/v1/videos/{video_id}/comments",
            json={
                "content": "This is a great video!"
            },
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "This is a great video!"
        assert data["video_id"] == video_id
    
    def test_get_video_comments(self, client, auth_headers):
        """Test getting comments for a video."""
        # Create a video
        create_response = client.post(
            "/api/v1/videos/",
            json={
                "title": "Get Comments Test",
                "video_url": "https://youtube.com/watch?v=getcomments"
            },
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        video_id = create_response.json()["id"]
        
        response = client.get(
            f"/api/v1/videos/{video_id}/comments",
            headers=auth_headers
        )
        assert response.status_code == 200
        comments = response.json()
        assert isinstance(comments, list)
    
    def test_delete_comment(self, client, auth_headers):
        """Test deleting a comment."""
        # Create a video
        create_response = client.post(
            "/api/v1/videos/",
            json={
                "title": "Delete Comment Test",
                "video_url": "https://youtube.com/watch?v=deletecomment"
            },
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        video_id = create_response.json()["id"]
        
        # Add comment
        comment_response = client.post(
            f"/api/v1/videos/{video_id}/comments",
            json={"content": "Comment to delete"},
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        comment_id = comment_response.json()["id"]
        
        # Delete comment
        response = client.delete(
            f"/api/v1/videos/comments/{comment_id}",
            params={"user_id": "test-user-id"},
            headers=auth_headers
        )
        assert response.status_code == 204

