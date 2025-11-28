# app/api/v1/endpoints/note.py
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.crud import note as crud_note
from app.schemas.note import (
    NoteCreate, NoteOut, NoteUpdate,
    CommentCreate, CommentOut,
    LikeToggleResponse, FavoriteToggleResponse
)
from app.utils.auth import get_current_user 
from app.utils.file_upload import save_upload_file  # e.g., saves to /uploads/
from app.models.user import User

router = APIRouter()

@router.get("/", response_model=List[NoteOut])
def read_notes(
    db: Session = Depends(get_db),
    curriculum: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    skip: int = 0,
    limit: int = 20
):
    notes = crud_note.get_notes(db, skip, limit, curriculum, search, sort_by, sort_order)
    return notes

@router.post("/", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(
    note: NoteCreate,
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # TODO: validate role (teacher/admin) — assume role in User model
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized to create notes")
    
    file_url = None
    if file:
        file_url = save_upload_file(file)  # Implement this in utils

    db_note = crud_note.create_note(db, note, current_user.id)
    if file_url:
        db_note.file_url = file_url
        db.commit()
        db.refresh(db_note)
    return db_note

@router.get("/{noteId}/", response_model=NoteOut)
def read_note(noteId: int, db: Session = Depends(get_db)):
    note = crud_note.increment_view_count(db, noteId)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.put("/{noteId}/", response_model=NoteOut)
def update_note(
    noteId: int,
    note_update: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_note = crud_note.update_note(db, noteId, note_update, current_user.id)
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found or not authorized")
    return db_note

@router.delete("/{noteId}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    noteId: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    is_admin = current_user.role == "admin"
    success = crud_note.delete_note(db, noteId, current_user.id, is_admin)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found or not authorized")
    return

@router.post("/{noteId}/like/", response_model=LikeToggleResponse)
def toggle_like(
    noteId: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = crud_note.toggle_like(db, noteId, current_user.id)
    return result

@router.get("/{noteId}/download/")
def download_note(noteId: int):
    
    # TODO: integrate with PDF/DOCX generator (e.g., WeasyPrint, python-docx)
    raise HTTPException(status_code=501, detail="Download feature not implemented")

@router.get("/search/", response_model=List[NoteOut])
def search_notes(
    q: str,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    notes = crud_note.get_notes(db, skip=skip, limit=limit, search=q)
    return notes

# Comments
@router.get("/{noteId}/comments/", response_model=List[CommentOut])
def get_comments(
    noteId: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    return crud_note.get_comments(db, noteId, skip, limit)

@router.post("/{noteId}/comments/", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    noteId: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud_note.create_comment(db, noteId, current_user.id, comment.content)

@router.delete("/{noteId}/comments/{commentId}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    noteId: int,
    commentId: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    is_admin = current_user.role == "admin"
    success = crud_note.delete_comment(db, commentId, current_user.id, is_admin)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found or not authorized")
    return

# User-specific
@router.get("/my-notes/", response_model=List[NoteOut])
def get_my_notes(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud_note.get_user_notes(db, current_user.id, skip, limit)

@router.get("/favorites/", response_model=List[NoteOut])
def get_favorites(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud_note.get_user_favorites(db, current_user.id, skip, limit)

@router.post("/{noteId}/favorite/", response_model=FavoriteToggleResponse)
def toggle_favorite(
    noteId: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = crud_note.toggle_favorite(db, noteId, current_user.id)
    return result