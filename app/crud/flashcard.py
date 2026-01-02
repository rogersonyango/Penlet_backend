# app/crud/flashcard.py
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from sqlalchemy import func as sa_func
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from app.models.flashcard import Deck, Flashcard
from app.schemas.flashcard import DeckCreate, DeckUpdate, FlashcardCreate, FlashcardUpdate, ReviewUpdate

def get_deck(db: Session, deck_id: int) -> Optional[Deck]:
    """Get a single deck by ID"""
    return db.query(Deck).filter(Deck.id == deck_id).first()

def get_decks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    subject: Optional[str] = None,
    level: Optional[str] = None,
    public_only: bool = False,
    search: Optional[str] = None,
    user_id: Optional[str] = None
) -> List[Deck]:
    """Get decks with optional filters"""
    query = db.query(Deck)
    
    if public_only:
        query = query.filter(Deck.is_public == True)
    
    if subject:
        query = query.filter(Deck.subject.ilike(f"%{subject}%"))
    
    if level:
        query = query.filter(Deck.level == level)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Deck.title.ilike(search_term),
                Deck.subject.ilike(search_term)
            )
        )
    
    if user_id:
        # If you want to filter by user ownership in the future
        pass
    
    return query.order_by(Deck.created_at.desc()).offset(skip).limit(limit).all()

def create_deck(db: Session, deck: DeckCreate) -> Deck:
    """Create a new deck"""
    db_deck = Deck(**deck.model_dump())
    if db_deck.is_public and not db_deck.share_token:
        db_deck.generate_share_token()
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    return db_deck

def update_deck(
    db: Session,
    deck_id: int,
    deck_update: DeckUpdate
) -> Optional[Deck]:
    """Update a deck"""
    db_deck = get_deck(db, deck_id)
    
    if not db_deck:
        return None
    
    update_data = deck_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(db_deck, key, value)
    
    # Regenerate share token if deck becomes public and doesn't have one
    if db_deck.is_public and not db_deck.share_token:
        db_deck.generate_share_token()
    
    db.commit()
    db.refresh(db_deck)
    return db_deck

def delete_deck(db: Session, deck_id: int) -> bool:
    """Delete a deck and all its cards"""
    db_deck = get_deck(db, deck_id)
    
    if not db_deck:
        return False
    
    db.delete(db_deck)
    db.commit()
    return True

def get_deck_by_token(db: Session, share_token: str) -> Optional[Deck]:
    """Get a deck by its share token"""
    return db.query(Deck).filter(Deck.share_token == share_token).first()

def generate_share_token(db: Session, deck_id: int) -> Optional[Deck]:
    """Generate or regenerate a share token for a deck"""
    db_deck = get_deck(db, deck_id)
    
    if not db_deck:
        return None
    
    db_deck.generate_share_token()
    db.commit()
    db.refresh(db_deck)
    return db_deck

# Flashcard CRUD operations
def get_flashcard(db: Session, card_id: int) -> Optional[Flashcard]:
    """Get a single flashcard by ID"""
    return db.query(Flashcard).filter(Flashcard.id == card_id).first()

def get_cards_by_deck(
    db: Session,
    deck_id: int,
    skip: int = 0,
    limit: int = 100,
    due_only: bool = False
) -> List[Flashcard]:
    """Get flashcards by deck ID"""
    query = db.query(Flashcard).filter(Flashcard.deck_id == deck_id)
    
    if due_only:
        now = datetime.now(timezone.utc)
        query = query.filter(Flashcard.next_review <= now)
    
    return query.order_by(Flashcard.next_review).offset(skip).limit(limit).all()

def create_flashcard(db: Session, card: FlashcardCreate) -> Flashcard:
    """Create a new flashcard"""
    db_card = Flashcard(**card.model_dump())
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

def update_flashcard(
    db: Session,
    card_id: int,
    card_update: FlashcardUpdate
) -> Optional[Flashcard]:
    """Update a flashcard"""
    db_card = get_flashcard(db, card_id)
    
    if not db_card:
        return None
    
    update_data = card_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(db_card, key, value)
    
    db.commit()
    db.refresh(db_card)
    return db_card

def delete_flashcard(db: Session, card_id: int) -> bool:
    """Delete a flashcard"""
    db_card = get_flashcard(db, card_id)
    
    if not db_card:
        return False
    
    db.delete(db_card)
    db.commit()
    return True

# Spaced Repetition System (SRS) functions
def update_review(db: Session, card_id: int, review: ReviewUpdate) -> Optional[Flashcard]:
    """Update flashcard review using SM-2 algorithm"""
    db_card = get_flashcard(db, card_id)
    
    if not db_card:
        return None
    
    quality = review.quality
    
    # SM-2 algorithm implementation
    if quality < 3:
        # Incorrect response - reset repetitions
        db_card.repetition = 0
        db_card.interval = 1
    else:
        # Correct response
        if db_card.repetition == 0:
            db_card.interval = 1
        elif db_card.repetition == 1:
            db_card.interval = 6
        else:
            db_card.interval = int(db_card.interval * db_card.ease_factor)
        
        db_card.repetition += 1
    
    # Update ease factor
    db_card.ease_factor = max(
        1.3,
        db_card.ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
    )
    
    # Set next review date
    db_card.next_review = datetime.now(timezone.utc) + timedelta(days=db_card.interval)
    
    db.commit()
    db.refresh(db_card)
    return db_card

def get_due_cards(db: Session, deck_id: int, limit: int = 20) -> List[Flashcard]:
    """Get cards due for review"""
    now = datetime.now(timezone.utc)
    return (
        db.query(Flashcard)
        .filter(
            Flashcard.deck_id == deck_id,
            Flashcard.next_review <= now
        )
        .order_by(Flashcard.next_review)
        .limit(limit)
        .all()
    )
def get_study_stats(db: Session, deck_id: int) -> dict:
    """Get study statistics for a deck"""
    now = datetime.now(timezone.utc)
    
    total_cards = db.query(Flashcard).filter(
        Flashcard.deck_id == deck_id
    ).count() or 0
    
    cards_due = db.query(Flashcard).filter(
        Flashcard.deck_id == deck_id,
        Flashcard.next_review <= now
    ).count() or 0
    
    cards_learning = db.query(Flashcard).filter(
        Flashcard.deck_id == deck_id,
        Flashcard.interval == 0
    ).count() or 0
    
    cards_mastered = db.query(Flashcard).filter(
        Flashcard.deck_id == deck_id,
        Flashcard.interval >= 30
    ).count() or 0
    
    average_ease_factor = db.query(sa_func.avg(Flashcard.ease_factor)).filter(
        Flashcard.deck_id == deck_id
    ).scalar() or 2.5
    
    return {
        "deck_id": deck_id,
        "total_cards": total_cards,
        "cards_due": cards_due,
        "cards_learning": cards_learning,
        "cards_mastered": cards_mastered,
        "average_ease_factor": round(float(average_ease_factor), 2)
    }
    

