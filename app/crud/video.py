from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from app.models.video import Video, VideoProgress, VideoLike, VideoComment
from app.schemas.video import VideoCreate, VideoUpdate, ProgressUpdate, CommentCreate
from typing import Optional, Tuple, List
from datetime import datetime

# ============= VIDEO CRUD =============

def create_video(db: Session, video: VideoCreate, user_id: str) -> Video:
    """Create a new video"""
    db_video = Video(
        title=video.title,
        description=video.description,
        video_url=video.video_url,
        thumbnail_url=video.thumbnail_url,
        subject_id=video.subject_id,
        subject_name=video.subject_name,
        topic=video.topic,
        tags=video.tags,
        duration=video.duration,
        file_size=video.file_size,
        video_type=video.video_type,
        quality=video.quality,
        user_id=user_id,
        is_public=video.is_public,
        is_favorite=video.is_favorite
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video

def get_video(db: Session, video_id: str, user_id: Optional[str] = None) -> Optional[Video]:
    """
    Get a single video by ID.
    If user_id is provided, only return if video is public or owned by user.
    """
    query = db.query(Video).filter(Video.id == video_id)
    
    if user_id:
        query = query.filter(
            or_(
                Video.user_id == user_id,
                Video.is_public == True
            )
        )
    
    video = query.first()
    
    # Increment view count
    if video:
        video.view_count += 1
        db.commit()
        db.refresh(video)
    
    return video

def get_user_videos(
    db: Session,
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    subject_id: Optional[str] = None,
    subject_name: Optional[str] = None,
    video_type: Optional[str] = None,
    is_favorite: Optional[bool] = None
) -> Tuple[List[Video], int]:
    """Get user's videos with filters and pagination"""
    query = db.query(Video).filter(Video.user_id == user_id)
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Video.title.ilike(search_term),
                Video.description.ilike(search_term),
                Video.tags.ilike(search_term),
                Video.topic.ilike(search_term)
            )
        )
    
    if subject_id:
        query = query.filter(Video.subject_id == subject_id)
    
    if subject_name:
        query = query.filter(Video.subject_name == subject_name)
    
    if video_type:
        query = query.filter(Video.video_type == video_type)
    
    if is_favorite is not None:
        query = query.filter(Video.is_favorite == is_favorite)
    
    # Get total count
    total = query.count()
    
    # Get paginated results, ordered by created date
    videos = query.order_by(Video.created_at.desc()).offset(skip).limit(limit).all()
    
    return videos, total

def get_public_videos(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    subject_id: Optional[str] = None
) -> Tuple[List[Video], int]:
    """Get public videos with filters"""
    query = db.query(Video).filter(Video.is_public == True)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Video.title.ilike(search_term),
                Video.description.ilike(search_term),
                Video.tags.ilike(search_term)
            )
        )
    
    if subject_id:
        query = query.filter(Video.subject_id == subject_id)
    
    total = query.count()
    videos = query.order_by(Video.view_count.desc()).offset(skip).limit(limit).all()
    
    return videos, total

def get_featured_videos(db: Session, limit: int = 10) -> List[Video]:
    """Get featured videos"""
    return db.query(Video).filter(
        Video.is_featured == True,
        Video.is_public == True
    ).order_by(Video.view_count.desc()).limit(limit).all()

def update_video(
    db: Session,
    video_id: str,
    video_update: VideoUpdate,
    user_id: str
) -> Optional[Video]:
    """Update a video"""
    db_video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == user_id
    ).first()
    
    if not db_video:
        return None
    
    # Update only provided fields
    update_data = video_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_video, field, value)
    
    db.commit()
    db.refresh(db_video)
    return db_video

def delete_video(db: Session, video_id: str, user_id: str) -> bool:
    """Delete a video and all related data"""
    db_video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == user_id
    ).first()
    
    if not db_video:
        return False
    
    # Delete related data
    db.query(VideoProgress).filter(VideoProgress.video_id == video_id).delete()
    db.query(VideoLike).filter(VideoLike.video_id == video_id).delete()
    db.query(VideoComment).filter(VideoComment.video_id == video_id).delete()
    
    db.delete(db_video)
    db.commit()
    return True

def toggle_favorite(db: Session, video_id: str, user_id: str) -> Optional[Video]:
    """Toggle favorite status"""
    db_video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == user_id
    ).first()
    
    if not db_video:
        return None
    
    db_video.is_favorite = not db_video.is_favorite
    db.commit()
    db.refresh(db_video)
    return db_video

# ============= PROGRESS CRUD =============

def update_progress(
    db: Session,
    video_id: str,
    user_id: str,
    progress: ProgressUpdate
) -> VideoProgress:
    """Update or create video progress"""
    db_progress = db.query(VideoProgress).filter(
        VideoProgress.video_id == video_id,
        VideoProgress.user_id == user_id
    ).first()
    
    if db_progress:
        # Update existing progress
        db_progress.watched_duration = progress.watched_duration
        db_progress.completion_percentage = progress.completion_percentage
        db_progress.last_watched_at = datetime.utcnow()
        
        if progress.completion_percentage >= 90 and not db_progress.is_completed:
            db_progress.is_completed = True
            db_progress.completed_at = datetime.utcnow()
    else:
        # Create new progress
        db_progress = VideoProgress(
            video_id=video_id,
            user_id=user_id,
            watched_duration=progress.watched_duration,
            completion_percentage=progress.completion_percentage,
            is_completed=progress.completion_percentage >= 90,
            completed_at=datetime.utcnow() if progress.completion_percentage >= 90 else None
        )
        db.add(db_progress)
    
    db.commit()
    db.refresh(db_progress)
    return db_progress

def get_progress(db: Session, video_id: str, user_id: str) -> Optional[VideoProgress]:
    """Get user's progress for a video"""
    return db.query(VideoProgress).filter(
        VideoProgress.video_id == video_id,
        VideoProgress.user_id == user_id
    ).first()

def get_user_progress_list(db: Session, user_id: str) -> List[VideoProgress]:
    """Get all progress for a user"""
    return db.query(VideoProgress).filter(
        VideoProgress.user_id == user_id
    ).order_by(VideoProgress.last_watched_at.desc()).all()

# ============= LIKES CRUD =============

def toggle_like(db: Session, video_id: str, user_id: str) -> Tuple[bool, int]:
    """Toggle like on a video. Returns (liked status, like count)"""
    # Check if already liked
    existing_like = db.query(VideoLike).filter(
        VideoLike.video_id == video_id,
        VideoLike.user_id == user_id
    ).first()
    
    if existing_like:
        # Unlike
        db.delete(existing_like)
        liked = False
    else:
        # Like
        new_like = VideoLike(video_id=video_id, user_id=user_id)
        db.add(new_like)
        liked = True
    
    # Update like count on video
    video = db.query(Video).filter(Video.id == video_id).first()
    if video:
        video.like_count = db.query(func.count(VideoLike.id)).filter(
            VideoLike.video_id == video_id
        ).scalar()
        
    db.commit()
    
    return liked, video.like_count if video else 0

# ============= COMMENTS CRUD =============

def add_comment(
    db: Session,
    video_id: str,
    user_id: str,
    comment: CommentCreate
) -> VideoComment:
    """Add a comment to a video"""
    db_comment = VideoComment(
        video_id=video_id,
        user_id=user_id,
        content=comment.content
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_comments(db: Session, video_id: str) -> List[VideoComment]:
    """Get all comments for a video"""
    return db.query(VideoComment).filter(
        VideoComment.video_id == video_id
    ).order_by(VideoComment.created_at.desc()).all()

def delete_comment(db: Session, comment_id: str, user_id: str) -> bool:
    """Delete a comment"""
    db_comment = db.query(VideoComment).filter(
        VideoComment.id == comment_id,
        VideoComment.user_id == user_id
    ).first()
    
    if not db_comment:
        return False
    
    db.delete(db_comment)
    db.commit()
    return True