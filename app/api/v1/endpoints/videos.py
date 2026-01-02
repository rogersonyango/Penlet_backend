from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.schemas.video import (
    VideoCreate,
    VideoUpdate,
    VideoResponse,
    VideoListResponse,
    ProgressUpdate,
    ProgressResponse,
    VideoCommentCreate,
    VideoCommentResponse,
    # LikeResponse
)
from app.crud import video as crud_video

router = APIRouter(prefix="/videos", tags=["videos"])

# ============= VIDEO ENDPOINTS =============

@router.post("/", response_model=VideoResponse, status_code=201)
def create_video(
    video: VideoCreate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Create a new video.
    
    - **title**: Video title (required)
    - **video_url**: URL to video file or YouTube/Vimeo link
    - **thumbnail_url**: URL to thumbnail image
    - **subject_id**: Link to subject
    - **duration**: Duration in seconds
    - **video_type**: 'upload', 'youtube', 'vimeo', etc.
    """
    return crud_video.create_video(db, video, user_id)

@router.get("/", response_model=VideoListResponse)
def get_videos(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title, description, tags"),
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    subject_name: Optional[str] = Query(None, description="Filter by subject name"),
    video_type: Optional[str] = Query(None, description="Filter by video type"),
    is_favorite: Optional[bool] = Query(None, description="Filter favorites only"),
    db: Session = Depends(get_db)
):
    """
    Get user's videos with filters and pagination.
    
    Returns videos ordered by creation date (newest first).
    """
    skip = (page - 1) * page_size
    
    videos, total = crud_video.get_user_videos(
        db=db,
        user_id=user_id,
        skip=skip,
        limit=page_size,
        search=search,
        subject_id=subject_id,
        subject_name=subject_name,
        video_type=video_type,
        is_favorite=is_favorite
    )
    
    return {
        "videos": videos,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/public", response_model=VideoListResponse)
def get_public_videos(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get public videos.
    
    Returns public videos ordered by view count.
    """
    skip = (page - 1) * page_size
    
    videos, total = crud_video.get_public_videos(
        db=db,
        skip=skip,
        limit=page_size,
        search=search,
        subject_id=subject_id
    )
    
    return {
        "videos": videos,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/featured", response_model=list[VideoResponse])
def get_featured_videos(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get featured videos"""
    return crud_video.get_featured_videos(db, limit)

@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: str,
    user_id: Optional[str] = Query(None, description="User ID (optional)"),
    db: Session = Depends(get_db)
):
    """
    Get a single video by ID.
    
    Automatically increments view count.
    If user_id provided, checks access permissions.
    """
    video = crud_video.get_video(db, video_id, user_id)
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found or access denied")
    
    return video

@router.put("/{video_id}", response_model=VideoResponse)
def update_video(
    video_id: str,
    video_update: VideoUpdate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Update a video.
    
    Only the video owner can update it.
    """
    video = crud_video.update_video(db, video_id, video_update, user_id)
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video

@router.delete("/{video_id}", status_code=204)
def delete_video(
    video_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Delete a video.
    
    Also deletes all related progress, likes, and comments.
    """
    success = crud_video.delete_video(db, video_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return None

@router.post("/{video_id}/favorite", response_model=VideoResponse)
def toggle_favorite(
    video_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """Toggle favorite status of a video"""
    video = crud_video.toggle_favorite(db, video_id, user_id)
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video

# ============= PROGRESS ENDPOINTS =============

@router.post("/{video_id}/progress", response_model=ProgressResponse)
def update_progress(
    video_id: str,
    progress: ProgressUpdate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Update watch progress for a video.
    
    Automatically marks as completed when completion_percentage >= 90%.
    """
    return crud_video.update_progress(db, video_id, user_id, progress)

@router.get("/{video_id}/progress", response_model=ProgressResponse)
def get_progress(
    video_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """Get user's progress for a video"""
    progress = crud_video.get_progress(db, video_id, user_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail="No progress found for this video")
    
    return progress

@router.get("/progress/all", response_model=list[ProgressResponse])
def get_all_progress(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """Get all video progress for a user"""
    return crud_video.get_user_progress_list(db, user_id)

# ============= LIKE ENDPOINTS =============

# @router.post("/{video_id}/like", response_model=LikeResponse)
# def toggle_like(
#     video_id: str,
#     user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
#     db: Session = Depends(get_db)
# ):
#     """Toggle like on a video"""
#     liked, like_count = crud_video.toggle_like(db, video_id, user_id)
    
#     return {
#         "liked": liked,
#         "like_count": like_count
#     }

# ============= COMMENT ENDPOINTS =============

@router.post("/{video_id}/comments", response_model=VideoCommentResponse, status_code=201)
def add_comment(
    video_id: str,
    comment: VideoCommentCreate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """Add a comment to a video"""
    return crud_video.add_comment(db, video_id, user_id, comment)

@router.get("/{video_id}/comments", response_model=list[VideoCommentResponse])
def get_comments(
    video_id: str,
    db: Session = Depends(get_db)
):
    """Get all comments for a video"""
    return crud_video.get_comments(db, video_id)

@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(
    comment_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """Delete a comment (owner only)"""
    success = crud_video.delete_comment(db, comment_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    return None