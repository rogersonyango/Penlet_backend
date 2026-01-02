"""
Tests for flashcard endpoints.
"""
import pytest
from fastapi.testclient import TestClient

class TestDeckCRUD:
    """Test flashcard deck CRUD operations."""
    
    def test_create_deck(self, client, auth_headers):
        """Test creating a new flashcard deck."""
        response = client.post(
            "/api/flashcards/decks/",
            json={
                "title": "Spanish Vocabulary",
                "subject": "Spanish",
                "level": "Beginner",
                "is_public": False
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Spanish Vocabulary"
        assert data["subject"] == "Spanish"
        assert data["level"] == "Beginner"
        assert "id" in data
    
    def test_list_decks(self, client, auth_headers, test_deck):
        """Test listing flashcard decks."""
        response = client.get(
            "/api/flashcards/decks/",
            headers=auth_headers
        )
        assert response.status_code == 200
        decks = response.json()
        assert isinstance(decks, list)
    
    def test_list_decks_with_filters(self, client, auth_headers):
        """Test listing decks with filters."""
        # Create a deck
        client.post(
            "/api/flashcards/decks/",
            json={
                "title": "Math Formulas",
                "subject": "Mathematics",
                "level": "Intermediate"
            },
            headers=auth_headers
        )
        
        # Filter by subject
        response = client.get(
            "/api/flashcards/decks/?subject=Mathematics",
            headers=auth_headers
        )
        assert response.status_code == 200
        decks = response.json()
        for deck in decks:
            assert deck["subject"] == "Mathematics"
    
    def test_list_public_decks(self, client, test_deck):
        """Test listing public decks without authentication."""
        # Make deck public
        test_deck.is_public = True
        
        response = client.get(
            "/api/flashcards/decks/public/"
        )
        assert response.status_code == 200
        decks = response.json()
        assert isinstance(decks, list)
    
    def test_get_single_deck(self, client, auth_headers, test_deck):
        """Test getting a single deck by ID."""
        response = client.get(
            f"/api/flashcards/decks/{test_deck.id}/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_deck.id
        assert data["title"] == test_deck.title
    
    def test_get_nonexistent_deck(self, client, auth_headers):
        """Test getting a nonexistent deck."""
        response = client.get(
            "/api/flashcards/decks/99999/",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    def test_update_deck(self, client, auth_headers, test_deck):
        """Test updating a deck."""
        response = client.put(
            f"/api/flashcards/decks/{test_deck.id}/",
            json={
                "title": "Updated Deck Title",
                "level": "Advanced"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Deck Title"
        assert data["level"] == "Advanced"
    
    def test_delete_deck(self, client, auth_headers, test_deck):
        """Test deleting a deck."""
        response = client.delete(
            f"/api/flashcards/decks/{test_deck.id}/",
            headers=auth_headers
        )
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(
            f"/api/flashcards/decks/{test_deck.id}/",
            headers=auth_headers
        )
        assert get_response.status_code == 404

class TestFlashcardCRUD:
    """Test flashcard CRUD operations."""
    
    def test_create_flashcard(self, client, auth_headers, test_deck):
        """Test creating a new flashcard."""
        response = client.post(
            f"/api/flashcards/decks/{test_deck.id}/cards/",
            json={
                "front": "What is the Spanish word for 'apple'?",
                "back": "Manzana"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["front"] == "What is the Spanish word for 'apple'?"
        assert data["back"] == "Manzana"
        assert data["deck_id"] == test_deck.id
    
    def test_create_multiple_flashcards(self, client, auth_headers, test_deck):
        """Test creating multiple flashcards."""
        cards = [
            {"front": "Hello", "back": "Hola"},
            {"front": "Goodbye", "back": "Adiós"},
            {"front": "Thank you", "back": "Gracias"}
        ]
        
        for card in cards:
            response = client.post(
                f"/api/flashcards/decks/{test_deck.id}/cards/",
                json=card,
                headers=auth_headers
            )
            assert response.status_code == 200
    
    def test_get_deck_cards(self, client, auth_headers, test_deck):
        """Test getting cards in a deck."""
        # Create a card first
        client.post(
            f"/api/flashcards/decks/{test_deck.id}/cards/",
            json={
                "front": "Test front",
                "back": "Test back"
            },
            headers=auth_headers
        )
        
        response = client.get(
            f"/api/flashcards/decks/{test_deck.id}/cards/",
            headers=auth_headers
        )
        assert response.status_code == 200
        cards = response.json()
        assert isinstance(cards, list)
    
    def test_update_flashcard(self, client, auth_headers, test_deck):
        """Test updating a flashcard."""
        # Create a card
        create_response = client.post(
            f"/api/flashcards/decks/{test_deck.id}/cards/",
            json={
                "front": "Original front",
                "back": "Original back"
            },
            headers=auth_headers
        )
        card_id = create_response.json()["id"]
        
        # Update the card
        response = client.put(
            f"/api/flashcards/cards/{card_id}/",
            json={
                "back": "Updated back"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["back"] == "Updated back"
    
    def test_delete_flashcard(self, client, auth_headers, test_deck):
        """Test deleting a flashcard."""
        # Create a card
        create_response = client.post(
            f"/api/flashcards/decks/{test_deck.id}/cards/",
            json={
                "front": "To be deleted",
                "back": "Deleted"
            },
            headers=auth_headers
        )
        card_id = create_response.json()["id"]
        
        # Delete the card
        response = client.delete(
            f"/api/flashcards/cards/{card_id}/",
            headers=auth_headers
        )
        assert response.status_code == 204

class TestStudySession:
    """Test study session functionality."""
    
    def test_start_study_session(self, client, auth_headers, test_deck):
        """Test starting a study session."""
        # Create some cards
        for i in range(5):
            client.post(
                f"/api/flashcards/decks/{test_deck.id}/cards/",
                json={
                    "front": f"Question {i}",
                    "back": f"Answer {i}"
                },
                headers=auth_headers
            )
        
        response = client.get(
            f"/api/flashcards/study/{test_deck.id}/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deck_id"] == test_deck.id
        assert "cards_due" in data
        assert "total_cards" in data
    
    def test_get_study_stats(self, client, auth_headers, test_deck):
        """Test getting study statistics."""
        response = client.get(
            f"/api/flashcards/study/stats/{test_deck.id}/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deck_id"] == test_deck.id
        assert "total_cards" in data
        assert "cards_due" in data
        assert "cards_learning" in data
        assert "cards_mastered" in data

class TestCardReview:
    """Test flashcard review functionality."""
    
    def test_review_card(self, client, auth_headers, test_deck):
        """Test reviewing a card with SM-2 algorithm."""
        # Create a card
        create_response = client.post(
            f"/api/flashcards/decks/{test_deck.id}/cards/",
            json={
                "front": "Review test",
                "back": "Review answer"
            },
            headers=auth_headers
        )
        card_id = create_response.json()["id"]
        
        # Review with quality rating (0-5)
        response = client.post(
            f"/api/flashcards/cards/{card_id}/review/",
            json={"quality": 4},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Card should have updated review data
        assert "next_review" in data
        assert "interval" in data
        assert "repetition" in data
        assert "ease_factor" in data

class TestDeckSharing:
    """Test deck sharing functionality."""
    
    def test_share_deck(self, client, auth_headers, test_deck):
        """Test generating a share token for a deck."""
        response = client.post(
            f"/api/flashcards/decks/{test_deck.id}/share/",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["deck_id"] == test_deck.id
        assert data["is_public"] == True
        assert "share_token" in data
        assert "share_url" in data
    
    def test_get_shared_deck(self, client, test_deck):
        """Test accessing a shared deck."""
        # First share the deck
        share_response = client.post(
            f"/api/flashcards/decks/{test_deck.id}/share/",
            headers={"Authorization": "Bearer test-token"}
        )
        share_token = share_response.json()["share_token"]
        
        # Access shared deck
        response = client.get(
            f"/api/flashcards/decks/shared/{share_token}/"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_deck.id

