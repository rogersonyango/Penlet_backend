# app/api/v1/endpoints/note.py
from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path

from app.api.deps import get_current_user, get_current_teacher_or_admin, get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.note import (
    NoteCreate, NoteUpdate, NoteResponse,
    CommentCreate, CommentUpdate, CommentResponse,
    LikeToggleResponse, FavoriteToggleResponse
)
from app.crud import note as crud_note

router = APIRouter()

# File upload configuration
UPLOAD_DIR = Path("uploads/notes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_upload_file(file: UploadFile) -> str:
    """Save uploaded file and return file URL/path"""
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    return f"/uploads/notes/{file.filename}"

@router.get("/", response_model=List[NoteResponse])
def read_notes(
    curriculum: Optional[str] = Query(None, description="Filter by curriculum"),
    search: Optional[str] = Query(None, description="Search in title/content"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[NoteResponse]:
    """
    Retrieve notes with optional filtering.
    """
    notes = crud_note.get_notes(
        db=db,
        skip=skip,
        limit=limit,
        curriculum=curriculum,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )
    return notes

@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    note: NoteCreate,
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher_or_admin)
) -> NoteResponse:
    """
    Create a new note (teachers/admins only).
    """
    file_url = None
    if file:
        file_url = save_upload_file(file)
    
    db_note = crud_note.create_note(db=db, note=note, author_id=current_user.id)
    
    if file_url:
        db_note.file_url = file_url
        db.commit()
        db.refresh(db_note)
    
    return db_note

@router.get("/{note_id}/", response_model=NoteResponse)
def read_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> NoteResponse:
    """
    Retrieve a specific note by ID.
    """
    note = crud_note.get_note(db, note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Increment view count
    crud_note.increment_view_count(db, note_id)
    
    return note

@router.put("/{note_id}/", response_model=NoteResponse)
def update_note(
    note_id: int,
    note_update: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> NoteResponse:
    """
    Update a note (author or admin only).
    """
    is_admin = current_user.user_type == "admin"
    note = crud_note.update_note(db, note_id, note_update, current_user.id)
    
    if not note:
        if is_admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this note"
            )
    
    return note

@router.delete("/{note_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a note (author or admin only).
    """
    is_admin = current_user.user_type == "admin"
    success = crud_note.delete_note(db, note_id, current_user.id, is_admin)
    
    if not success:
        if is_admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this note"
            )

@router.post("/{note_id}/like/", response_model=LikeToggleResponse)
def toggle_like(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> LikeToggleResponse:
    """
    Toggle like on a note.
    """
    result = crud_note.toggle_like(db, note_id, current_user.id)
    return result

@router.post("/{note_id}/favorite/", response_model=FavoriteToggleResponse)
def toggle_favorite(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FavoriteToggleResponse:
    """
    Toggle favorite status for a note.
    """
    result = crud_note.toggle_favorite(db, note_id, current_user.id)
    return result

# Comments endpoints
@router.get("/{note_id}/comments/", response_model=List[CommentResponse])
def get_comments(
    note_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[CommentResponse]:
    """
    Get comments for a note.
    """
    note = crud_note.get_note(db, note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    return crud_note.get_comments(db, note_id, skip, limit)

@router.post("/{note_id}/comments/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    note_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CommentResponse:
    """
    Add a comment to a note.
    """
    note = crud_note.get_note(db, note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    return crud_note.create_comment(db, note_id, current_user.id, comment.content)

@router.put("/{note_id}/comments/{comment_id}/", response_model=CommentResponse)
def update_comment(
    note_id: int,
    comment_id: int,
    comment_update: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CommentResponse:
    """
    Update a comment (author or admin only).
    """
    # Fetch comments for the note and locate the specific comment by id
    comments = crud_note.get_comments(db, note_id, skip=0, limit=1000)
    comment = next((c for c in comments if getattr(c, "id", None) == comment_id), None)
    if not comment or comment.note_id != note_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )
    
    is_admin = current_user.user_type == "admin"
    if not is_admin and comment.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this comment"
        )
    
    # Use CRUD update function or direct update
    comment.content = comment_update.content
    db.commit()
    db.refresh(comment)
    
    return comment

@router.delete("/{note_id}/comments/{comment_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    note_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a comment (author or admin only).
    """
    is_admin = current_user.user_type == "admin"
    success = crud_note.delete_comment(db, comment_id, current_user.id, is_admin)
    
    if not success:
        if is_admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this comment"
            )

# User-specific endpoints
@router.get("/my-notes/", response_model=List[NoteResponse])
def get_my_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[NoteResponse]:
    """
    Get notes created by the current user.
    """
    return crud_note.get_user_notes(db, current_user.id, skip, limit)

@router.get("/favorites/", response_model=List[NoteResponse])
def get_favorites(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[NoteResponse]:
    """
    Get notes favorited by the current user.
    """
    return crud_note.get_user_favorites(db, current_user.id, skip, limit)

@router.get("/search/", response_model=List[NoteResponse])
def search_notes(
    q: str = Query(..., description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[NoteResponse]:
    """
    Search notes by title or content.
    """
    notes = crud_note.get_notes(db, skip=skip, limit=limit, search=q)
    return notes

@router.get("/{note_id}/download/")
def download_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download note file if available.
    """
    note = crud_note.get_note(db, note_id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    if not note.file_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No file available for download"
        )
    
    file_path = Path(note.file_url.lstrip("/"))
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # FileResponse expects the path as the first argument and does not accept a 'filename'
    # keyword; provide the download filename via the Content-Disposition header.
    return FileResponse(
        str(file_path),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{file_path.name}"'}
    )