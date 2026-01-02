# app/api/v1/endpoints/flashcards.py
from secrets import token_urlsafe
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional
from urllib.parse import urljoin

from app.api.deps import get_current_user, get_current_teacher_or_admin
from app.db.session import get_db
from app.models.user import User
from app.schemas.flashcard import (
    DeckCreate, DeckUpdate, DeckResponse,
    FlashcardCreate, FlashcardUpdate, FlashcardResponse,
    ReviewUpdate, StudySessionResponse, StudyStatsResponse
)
from app.crud import flashcard as crud_flashcard

router = APIRouter()

@router.get("/decks/", response_model=List[DeckResponse])
def list_decks(
    subject: Optional[str] = Query(None, description="Filter by subject"),
    level: Optional[str] = Query(None, description="Filter by level"),
    public_only: bool = Query(False, description="Show only public decks"),
    search: Optional[str] = Query(None, description="Search in title/subject"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> List[DeckResponse]:
    """
    List flashcard decks with optional filtering.
    """
    decks = crud_flashcard.get_decks(
        db=db,
        skip=skip,
        limit=limit,
        subject=subject,
        level=level,
        public_only=public_only,
        search=search,
        user_id=current_user.id if current_user else None
    )
    return decks

@router.post("/decks/", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
def create_deck_endpoint(
    deck: DeckCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DeckResponse:
    """
    Create a new flashcard deck.
    """
    return crud_flashcard.create_deck(db=db, deck=deck)

@router.get("/decks/{deck_id}/", response_model=DeckResponse)
def get_deck_endpoint(
    deck_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> DeckResponse:
    """
    Retrieve a specific flashcard deck by ID.
    """
    deck = crud_flashcard.get_deck(db, deck_id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    
    # Check access if not public
    if not deck.is_public and (not current_user or current_user.id != deck.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this deck"
        )
    
    return deck

@router.put("/decks/{deck_id}/", response_model=DeckResponse)
def update_deck_endpoint(
    deck_id: int,
    deck_update: DeckUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> DeckResponse:
    """
    Update a flashcard deck.
    """
    # Check ownership
    deck = crud_flashcard.get_deck(db, deck_id)
    if not deck or deck.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found or not authorized"
        )
    
    return crud_flashcard.update_deck(db=db, deck_id=deck_id, deck_update=deck_update)

@router.delete("/decks/{deck_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_deck_endpoint(
    deck_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a flashcard deck.
    """
    # Check ownership
    deck = crud_flashcard.get_deck(db, deck_id)
    if not deck or deck.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found or not authorized"
        )
    
    success = crud_flashcard.delete_deck(db, deck_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )

# Flashcard endpoints
@router.post("/decks/{deck_id}/cards/", response_model=FlashcardResponse, status_code=status.HTTP_201_CREATED)
def create_flashcard(
    deck_id: int,
    card: FlashcardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FlashcardResponse:
    """
    Create a new flashcard in a deck.
    """
    # Check deck ownership
    deck = crud_flashcard.get_deck(db, deck_id)
    if not deck or deck.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found or not authorized"
        )
    
    return crud_flashcard.create_flashcard(db=db, card=card)

@router.get("/decks/{deck_id}/cards/", response_model=List[FlashcardResponse])
def get_deck_cards(
    deck_id: int,
    due_only: bool = Query(False, description="Only show cards due for review"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> List[FlashcardResponse]:
    """
    Get flashcards in a deck.
    """
    deck = crud_flashcard.get_deck(db, deck_id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    
    # Check access
    if not deck.is_public and (not current_user or current_user.id != deck.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this deck"
        )
    
    return crud_flashcard.get_cards_by_deck(
        db=db,
        deck_id=deck_id,
        skip=skip,
        limit=limit,
        due_only=due_only
    )

@router.put("/cards/{card_id}/", response_model=FlashcardResponse)
def update_flashcard(
    card_id: int,
    card_update: FlashcardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FlashcardResponse:
    """
    Update a flashcard.
    """
    card = crud_flashcard.get_flashcard(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Check deck ownership
    deck = crud_flashcard.get_deck(db, card.deck_id)
    if not deck or deck.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this card"
        )
    
    return crud_flashcard.update_flashcard(db=db, card_id=card_id, card_update=card_update)

@router.delete("/cards/{card_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_flashcard(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a flashcard.
    """
    card = crud_flashcard.get_flashcard(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Check deck ownership
    deck = crud_flashcard.get_deck(db, card.deck_id)
    if not deck or deck.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this card"
        )
    
    success = crud_flashcard.delete_flashcard(db, card_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )

@router.post("/cards/{card_id}/review/", response_model=FlashcardResponse)
def review_card(
    card_id: int,
    review: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FlashcardResponse:
    """
    Update card review using spaced repetition.
    """
    card = crud_flashcard.update_review(db, card_id, review)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    return card

@router.get("/study/{deck_id}/", response_model=StudySessionResponse)
def start_study_session(
    deck_id: int,
    limit: int = Query(20, ge=1, le=100, description="Number of cards to study"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> StudySessionResponse:
    """
    Start a study session with cards due for review.
    """
    deck = crud_flashcard.get_deck(db, deck_id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    
    # Check access
    if not deck.is_public and (not current_user or current_user.id != deck.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this deck"
        )
    
    cards_due = crud_flashcard.get_due_cards(db, deck_id, limit)
    total_cards = len(crud_flashcard.get_cards_by_deck(db, deck_id))
    
    return StudySessionResponse(
        deck_id=deck_id,
        cards_due=cards_due,
        total_cards=total_cards
    )

@router.get("/study/stats/{deck_id}/", response_model=StudyStatsResponse)
def get_study_stats(
    deck_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
) -> StudyStatsResponse:
    """
    Get study statistics for a deck.
    """
    deck = crud_flashcard.get_deck(db, deck_id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    
    # Check access
    if not deck.is_public and (not current_user or current_user.id != deck.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this deck"
        )
    
    return crud_flashcard.get_study_stats(db, deck_id)

@router.post("/decks/{deck_id}/share/")
def share_deck(
    deck_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a share token for a deck.
    """
    deck = crud_flashcard.get_deck(db, deck_id)
    if not deck or deck.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found or not authorized"
        )
    
    # Generate or regenerate share token
    if not deck.share_token:
        deck.share_token = token_urlsafe(16)
    
    deck.is_public = True
    db.commit()
    db.refresh(deck)
    
    # Build shareable URL
    base_url = str(request.base_url).rstrip('/')
    share_url = f"{base_url}/api/v1/flashcards/decks/shared/{deck.share_token}/"
    
    return {
        "message": f"Deck '{deck.title}' is now shared!",
        "deck_id": deck.id,
        "is_public": True,
        "share_token": deck.share_token,
        "share_url": share_url
    }

@router.get("/decks/shared/{share_token}/", response_model=DeckResponse)
def get_shared_deck(
    share_token: str,
    db: Session = Depends(get_db)
) -> DeckResponse:
    """
    Access a shared deck using its share token.
    """
    deck = crud_flashcard.get_deck_by_token(db, share_token)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared deck not found"
        )
    
    if not deck.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This deck is no longer publicly accessible"
        )
    
    return deck

@router.get("/decks/public/", response_model=List[DeckResponse])
def browse_public_decks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
) -> List[DeckResponse]:
    """
    Browse publicly available decks.
    """
    return crud_flashcard.get_decks(db, skip=skip, limit=limit, public_only=True)