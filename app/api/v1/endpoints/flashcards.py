# app/api/v1/endpoints/flashcard.py
from fastapi import Request

from urllib.parse import urljoin
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import secrets

# Database dependency
from app.db.session import get_db



from app.crud.flashcard import (
    get_deck,
    get_decks,
    create_deck,
    update_deck,
    delete_deck,
    
    update_review,
)



# Schemas (explicit imports like your `note` example)
from app.schemas.flashcard import (
    Deck,
    DeckCreate,
    Flashcard,
    FlashcardCreate,
    ReviewUpdate,
    StudySession,
    StudyStats,
)

# Models (needed for querying)
from app.models.flashcard import Flashcard as FlashcardModel

router = APIRouter()

# --- Deck Endpoints ---

# @router.get("/decks/", response_model=list[Deck])
# def list_decks(
#     subject: str | None = None,
#     level: str | None = None,
#     db: Session = Depends(get_db)
# ):
#     return get_decks(db, subject=subject, level=level)

@router.get("/decks/", response_model=list[Deck])
def list_decks(
    subject: str | None = None,
    level: str | None = None,
    db: Session = Depends(get_db)
):
    """List all flashcard decks, optionally filtered by subject or level."""
    return get_decks(db, subject=subject, level=level)


@router.post("/decks/", response_model=Deck)
def create_deck_endpoint(deck: DeckCreate, db: Session = Depends(get_db)):
    """Create a new flashcard deck."""
    return create_deck(db, deck)  # ← calls CRUD function


@router.get("/decks/{deckId}/", response_model=Deck)
def get_deck_endpoint(deckId: int, db: Session = Depends(get_db)):
    """Retrieve a specific flashcard deck by ID."""
    deck = get_deck(db, deckId)  # ← calls CRUD function
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck

@router.put("/decks/{deckId}/", response_model=Deck)
def update_deck_endpoint(deckId: int, deck_update: DeckCreate, db: Session = Depends(get_db)):
    deck = update_deck(db, deckId, deck_update.model_dump())
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck

@router.delete("/decks/{deckId}/")
def delete_deck_endpoint(deckId: int, db: Session = Depends(get_db)):
    deleted = delete_deck(db, deckId)
    if not deleted:
        raise HTTPException(status_code=404, detail="Deck not found")
    return {"message": "Deck deleted successfully"}



@router.post("/cards/{cardId}/review/", response_model=Flashcard)
def review_card(cardId: int, review: ReviewUpdate, db: Session = Depends(get_db)):
    updated = update_review(db, cardId, review.quality)
    if not updated:
        raise HTTPException(status_code=404, detail="Card not found")
    return updated

@router.get("/study/{deckId}/", response_model=StudySession)
def start_study(deckId: int, db: Session = Depends(get_db)):
    deck = get_deck(db, deckId)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    
    cards = db.query(FlashcardModel).filter(
        FlashcardModel.deck_id == deckId,
        FlashcardModel.next_review <= datetime.utcnow()
    ).all()
    
    return StudySession(deck_id=deckId, cards=cards)

@router.get("/study/stats/", response_model=StudyStats)
def get_study_stats(db: Session = Depends(get_db)):
    # Placeholder logic — implement based on your analytics
    total_cards = db.query(FlashcardModel).count()
    cards_due = db.query(FlashcardModel).filter(
        FlashcardModel.next_review <= datetime.utcnow()
    ).count()
    mastery_level = 0.0  # Replace with real calculation
    return StudyStats(total_cards=total_cards, cards_due=cards_due, mastery_level=mastery_level)





@router.post("/decks/{deckId}/share/")
def share_deck(
    deckId: int,
    db: Session = Depends(get_db),
    request: Request = None  # To build full URL
):
    """
    Make a deck publicly accessible and return a shareable link.
    If the deck already has a share token, reuse it. Otherwise, generate one.
    """
    deck = get_deck(db, deckId)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    # Ensure the deck instance is the ORM model (not Pydantic)
    if not isinstance(deck, Deck):
        # If your CRUD returns Pydantic, re-fetch as ORM
        deck = db.query(Deck).filter(Deck.id == deckId).first()
        if not deck:
            raise HTTPException(status_code=404, detail="Deck not found")

    # Generate or reuse share token
    if not deck.share_token:
        deck.share_token = secrets.token_urlsafe(16)

    # Make deck discoverable (optional: you could keep is_public=False and rely only on token)
    deck.is_public = True

    db.commit()
    db.refresh(deck)

    # Build shareable URL
    base_url = str(request.base_url) if request else "https://api.yourapp.com/"
    share_url = urljoin(base_url.rstrip('/') + "/", f"decks/shared/{deck.share_token}/")

    return {
        "message": f"Deck '{deck.title}' is now shared!",
        "deck_id": deck.id,
        "is_public": True,
        "share_token": deck.share_token,
        "share_url": share_url
    }





@router.get("/decks/public/", response_model=list[Deck])
def browse_public_decks(db: Session = Depends(get_db)):
    # Reuse get_decks with public filter
    return get_decks(db, public_only=True)