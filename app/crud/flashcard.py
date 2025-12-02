# app/crud/flashcard.py

from sqlalchemy.orm import Session
from app.models.flashcard import Deck, Flashcard
from app.schemas.flashcard import DeckCreate, FlashcardCreate, ReviewUpdate
from datetime import datetime, timedelta

def get_deck(db: Session, deck_id: int):
    return db.query(Deck).filter(Deck.id == deck_id).first()

def get_decks(db: Session, subject: str = None, level: str = None, public_only: bool = False):
    query = db.query(Deck)
    if public_only:
        query = query.filter(Deck.is_public == True)
    if subject:
        query = query.filter(Deck.subject == subject)
    if level:
        query = query.filter(Deck.level == level)
    return query.all()

def create_deck(db: Session, deck: DeckCreate):
    db_deck = Deck(**deck.model_dump())
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    return db_deck

def update_deck(db: Session, deck_id: int, deck_data: dict):
    db_deck = get_deck(db, deck_id)
    if db_deck:
        for key, value in deck_data.items():
            setattr(db_deck, key, value)
        db.commit()
        db.refresh(db_deck)
    return db_deck

def delete_deck(db: Session, deck_id: int):
    db_deck = get_deck(db, deck_id)
    if db_deck:
        db.delete(db_deck)
        db.commit()
    return db_deck

# Similar functions for flashcards: create_card, get_cards_by_deck, update_card, delete_card

def update_review(db: Session, card_id: int, quality: int):
    card = db.query(Flashcard).filter(Flashcard.id == card_id).first()
    if not card:
        return None
    # Simplified SM-2 algorithm
    if quality < 3:
        card.repetition = 0
        card.interval = 1
    else:
        if card.repetition == 0:
            card.interval = 1
        elif card.repetition == 1:
            card.interval = 6
        else:
            card.interval = int(card.interval * card.ease_factor)
        card.repetition += 1

    card.ease_factor = max(1.3, card.ease_factor + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    card.next_review = datetime.utcnow() + timedelta(days=card.interval)
    db.commit()
    db.refresh(card)
    return card