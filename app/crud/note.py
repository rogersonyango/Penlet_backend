# app/crud/note.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.note import Note, NoteLike, Favorite, Comment
from app.schemas.note import NoteCreate, NoteUpdate
from typing import List, Optional

def get_notes(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    curriculum: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    query = db.query(Note)
    if curriculum:
        query = query.filter(Note.curriculum.ilike(f"%{curriculum}%"))
    if search:
        query = query.filter(
            or_(
                Note.title.ilike(f"%{search}%"),
                Note.content.ilike(f"%{search}%")
            )
        )
    order_col = getattr(Note, sort_by, Note.created_at)
    if sort_order == "desc":
        order_col = order_col.desc()
    return query.order_by(order_col).offset(skip).limit(limit).all()

def get_note(db: Session, note_id: int):
    return db.query(Note).filter(Note.id == note_id).first()

def create_note(db: Session, note: NoteCreate, author_id: int):
    db_note = Note(**note.model_dump(), author_id=author_id)
    db.add(db_note)
    
    db.commit()
    db.refresh(db_note)
    return db_note

def update_note(db: Session, note_id: int, note_update: NoteUpdate, author_id: int):
    db_note = db.query(Note).filter(Note.id == note_id, Note.author_id == author_id).first()
    if not db_note:
        return None
    for key, value in note_update.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(db_note, key, value)
    db.commit()
    db.refresh(db_note)
    return db_note

def delete_note(db: Session, note_id: int, author_id: int, is_admin: bool = False):
    query = db.query(Note).filter(Note.id == note_id)
    if not is_admin:
        query = query.filter(Note.author_id == author_id)
    note = query.first()
    if note:
        db.delete(note)
        db.commit()
        return True
    return False

def increment_view_count(db: Session, note_id: int):
    note = db.query(Note).filter(Note.id == note_id).first()
    if note:
        note.view_count += 1
        db.commit()
        db.refresh(note)
    return note

# Likes
def toggle_like(db: Session, note_id: int, user_id: int):
    like = db.query(NoteLike).filter_by(note_id=note_id, user_id=user_id).first()
    if like:
        db.delete(like)
        liked = False
    else:
        like = NoteLike(note_id=note_id, user_id=user_id)
        db.add(like)
        liked = True
    db.commit()
    total_likes = db.query(NoteLike).filter_by(note_id=note_id).count()
    return {"liked": liked, "total_likes": total_likes}

# Favorites
def toggle_favorite(db: Session, note_id: int, user_id: int):
    fav = db.query(Favorite).filter_by(note_id=note_id, user_id=user_id).first()
    if fav:
        db.delete(fav)
        favorited = False
    else:
        fav = Favorite(note_id=note_id, user_id=user_id)
        db.add(fav)
        favorited = True
    db.commit()
    return {"favorited": favorited}

def get_user_favorites(db: Session, user_id: int, skip: int = 0, limit: int = 20):
    return (
        db.query(Note)
        .join(Favorite)
        .filter(Favorite.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_user_notes(db: Session, user_id: int, skip: int = 0, limit: int = 20):
    return db.query(Note).filter(Note.author_id == user_id).offset(skip).limit(limit).all()

# Comments
def get_comments(db: Session, note_id: int, skip: int = 0, limit: int = 20):
    return (
        db.query(Comment)
        .filter(Comment.note_id == note_id)
        .order_by(Comment.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_comment(db: Session, note_id: int, author_id: int, content: str):
    comment = Comment(content=content, note_id=note_id, author_id=author_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment

def delete_comment(db: Session, comment_id: int, author_id: int, is_admin: bool = False):
    query = db.query(Comment).filter(Comment.id == comment_id)
    if not is_admin:
        query = query.filter(Comment.author_id == author_id)
    comment = query.first()
    if comment:
        db.delete(comment)
        db.commit()
        return True
    return False