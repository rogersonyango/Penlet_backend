# app/crud/video.py
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc, asc
from app.models.video import Video, VideoProgress, VideoLike, VideoComment
from app.schemas.video import VideoCreate, VideoUpdate, ProgressUpdate, VideoCommentCreate
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, timedelta

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

def get_video(
    db: Session,
    video_id: str,
    user_id: Optional[str] = None,
    include_progress: bool = False
) -> Optional[Video]:
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
        
        # Update completion rate if needed
        if include_progress and user_id:
            progress = get_progress(db, video_id, user_id)
            if progress and progress.completion_percentage > video.completion_rate:
                video.completion_rate = progress.completion_percentage
        
        db.commit()
        db.refresh(video)
    
    return video

def get_video_with_progress(
    db: Session,
    video_id: str,
    user_id: str
) -> Tuple[Optional[Video], Optional[VideoProgress]]:
    """Get video along with user's progress"""
    video = get_video(db, video_id, user_id)
    progress = get_progress(db, video_id, user_id) if video else None
    return video, progress

def get_user_videos(
    db: Session,
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    subject_id: Optional[str] = None,
    subject_name: Optional[str] = None,
    topic: Optional[str] = None,
    video_type: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    is_public: Optional[bool] = None,
    is_featured: Optional[bool] = None,
    min_duration: Optional[int] = None,
    max_duration: Optional[int] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Tuple[List[Video], int]:
    """Get user's videos with comprehensive filters and sorting"""
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
        query = query.filter(Video.subject_name.ilike(f"%{subject_name}%"))
    
    if topic:
        query = query.filter(Video.topic.ilike(f"%{topic}%"))
    
    if video_type:
        query = query.filter(Video.video_type == video_type)
    
    if is_favorite is not None:
        query = query.filter(Video.is_favorite == is_favorite)
    
    if is_public is not None:
        query = query.filter(Video.is_public == is_public)
    
    if is_featured is not None:
        query = query.filter(Video.is_featured == is_featured)
    
    if min_duration:
        query = query.filter(Video.duration >= min_duration)
    
    if max_duration:
        query = query.filter(Video.duration <= max_duration)
    
    if created_after:
        query = query.filter(Video.created_at >= created_after)
    
    if created_before:
        query = query.filter(Video.created_at <= created_before)
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(Video, sort_by, Video.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Get paginated results
    videos = query.offset(skip).limit(limit).all()
    
    return videos, total

def get_public_videos(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    subject_id: Optional[str] = None,
    subject_name: Optional[str] = None,
    topic: Optional[str] = None,
    video_type: Optional[str] = None,
    is_featured: Optional[bool] = None,
    min_duration: Optional[int] = None,
    max_duration: Optional[int] = None,
    min_views: Optional[int] = None,
    min_completion: Optional[float] = None,
    sort_by: str = "view_count",
    sort_order: str = "desc"
) -> Tuple[List[Video], int]:
    """Get public videos with comprehensive filters"""
    query = db.query(Video).filter(Video.is_public == True)
    
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
        query = query.filter(Video.subject_name.ilike(f"%{subject_name}%"))
    
    if topic:
        query = query.filter(Video.topic.ilike(f"%{topic}%"))
    
    if video_type:
        query = query.filter(Video.video_type == video_type)
    
    if is_featured is not None:
        query = query.filter(Video.is_featured == is_featured)
    
    if min_duration:
        query = query.filter(Video.duration >= min_duration)
    
    if max_duration:
        query = query.filter(Video.duration <= max_duration)
    
    if min_views:
        query = query.filter(Video.view_count >= min_views)
    
    if min_completion:
        query = query.filter(Video.completion_rate >= min_completion)
    
    # Apply sorting
    sort_column = getattr(Video, sort_by, Video.view_count)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    total = query.count()
    videos = query.offset(skip).limit(limit).all()
    
    return videos, total

def get_recommended_videos(
    db: Session,
    user_id: str,
    limit: int = 10
) -> List[Video]:
    """Get recommended videos based on user's viewing history and preferences"""
    # Get user's favorite subjects/topics from progress
    favorite_subjects = (
        db.query(Video.subject_name)
        .join(VideoProgress, Video.id == VideoProgress.video_id)
        .filter(
            VideoProgress.user_id == user_id,
            VideoProgress.completion_percentage >= 50
        )
        .group_by(Video.subject_name)
        .order_by(func.count(Video.id).desc())  # ✅ Fixed: added argument
        .limit(3)
        .all()
    )
    
    favorite_topics = (
        db.query(Video.topic)
        .join(VideoProgress, Video.id == VideoProgress.video_id)
        .filter(
            VideoProgress.user_id == user_id,
            VideoProgress.completion_percentage >= 50
        )
        .group_by(Video.topic)
        .order_by(func.count(Video.id).desc())  # ✅ Fixed: added argument
        .limit(5)
        .all()
    )
    
    # Build recommendation query
    query = db.query(Video).filter(
        Video.is_public == True,
        Video.id.notin_(
            db.query(VideoProgress.video_id).filter(VideoProgress.user_id == user_id)
        )
    )
    
    # Add subject/topic filters if available
    if favorite_subjects or favorite_topics:
        filters = []
        if favorite_subjects:
            filters.append(Video.subject_name.in_([s[0] for s in favorite_subjects if s[0]]))
        if favorite_topics:
            filters.append(Video.topic.in_([t[0] for t in favorite_topics if t[0]]))
        
        if filters:
            query = query.filter(or_(*filters))
    
    # Fallback to popular videos if no preferences
    if (not favorite_subjects and not favorite_topics) or query.count() == 0:
        query = db.query(Video).filter(
            Video.is_public == True,
            Video.view_count >= 100
        )
    
    return query.order_by(
        desc(Video.view_count),
        desc(Video.completion_rate)
    ).limit(limit).all()

def get_featured_videos(
    db: Session,
    limit: int = 10,
    subject_id: Optional[str] = None
) -> List[Video]:
    """Get featured videos"""
    query = db.query(Video).filter(
        Video.is_featured == True,
        Video.is_public == True
    )
    
    if subject_id:
        query = query.filter(Video.subject_id == subject_id)
    
    return query.order_by(
        desc(Video.view_count),
        desc(Video.created_at)
    ).limit(limit).all()

def update_video(
    db: Session,
    video_id: str,
    video_update: VideoUpdate,
    user_id: str,
    is_admin: bool = False
) -> Optional[Video]:
    """Update a video"""
    query = db.query(Video).filter(Video.id == video_id)
    
    if not is_admin:
        query = query.filter(Video.user_id == user_id)
    
    db_video = query.first()
    
    if not db_video:
        return None
    
    # Update only provided fields
    update_data = video_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(db_video, field, value)
    
    db.commit()
    db.refresh(db_video)
    return db_video

def delete_video(
    db: Session,
    video_id: str,
    user_id: str,
    is_admin: bool = False
) -> bool:
    """Delete a video and all related data"""
    query = db.query(Video).filter(Video.id == video_id)
    
    if not is_admin:
        query = query.filter(Video.user_id == user_id)
    
    db_video = query.first()
    
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

def toggle_featured(db: Session, video_id: str, is_admin: bool = False) -> Optional[Video]:
    """Toggle featured status (admin only)"""
    if not is_admin:
        return None
    
    db_video = db.query(Video).filter(Video.id == video_id).first()
    
    if not db_video:
        return None
    
    db_video.is_featured = not db_video.is_featured
    db.commit()
    db.refresh(db_video)
    return db_video

def toggle_public(db: Session, video_id: str, user_id: str) -> Optional[Video]:
    """Toggle public/private status"""
    db_video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == user_id
    ).first()
    
    if not db_video:
        return None
    
    db_video.is_public = not db_video.is_public
    db.commit()
    db.refresh(db_video)
    return db_video

def search_videos(
    db: Session,
    query_str: str,
    user_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[Video], int]:
    """Search videos by title, description, tags, or topic"""
    search_term = f"%{query_str}%"
    
    if user_id:
        # Search user's videos plus public videos
        base_query = db.query(Video).filter(
            or_(
                Video.user_id == user_id,
                Video.is_public == True
            )
        )
    else:
        # Search only public videos
        base_query = db.query(Video).filter(Video.is_public == True)
    
    query = base_query.filter(
        or_(
            Video.title.ilike(search_term),
            Video.description.ilike(search_term),
            Video.tags.ilike(search_term),
            Video.topic.ilike(search_term),
            Video.subject_name.ilike(search_term)
        )
    )
    
    total = query.count()
    videos = query.order_by(desc(Video.view_count)).offset(skip).limit(limit).all()
    
    return videos, total

def get_video_statistics(db: Session, video_id: str) -> Dict[str, Any]:
    """Get detailed statistics for a video"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        return {}
    
    # Get like count
    like_count = db.query(func.count(VideoLike.id)).filter(
        VideoLike.video_id == video_id
    ).scalar()
    
    # Get comment count
    comment_count = db.query(func.count(VideoComment.id)).filter(
        VideoComment.video_id == video_id
    ).scalar()
    
    # Get progress statistics
    progress_stats = db.query(
        func.count(VideoProgress.id),
        func.avg(VideoProgress.completion_percentage),
        func.max(VideoProgress.completion_percentage),
        func.min(VideoProgress.completion_percentage)
    ).filter(VideoProgress.video_id == video_id).first()
    
    total_watchers, avg_completion, max_completion, min_completion = progress_stats
    
    # Get completion distribution
    completion_distribution = {}
    for threshold in [25, 50, 75, 90, 100]:
        count = db.query(func.count(VideoProgress.id)).filter(
            VideoProgress.video_id == video_id,
            VideoProgress.completion_percentage >= threshold
        ).scalar()
        completion_distribution[f"above_{threshold}%"] = count
    
    return {
        "video_id": video_id,
        "title": video.title,
        "view_count": video.view_count,
        "like_count": like_count,
        "comment_count": comment_count,
        "total_watchers": total_watchers or 0,
        "average_completion": round(avg_completion or 0, 2),
        "completion_distribution": completion_distribution,
        "duration": video.duration,
        "created_at": video.created_at,
        "updated_at": video.updated_at
    }

def get_user_video_statistics(db: Session, user_id: str) -> Dict[str, Any]:
    """Get video statistics for a user"""
    # Total videos
    total_videos = db.query(func.count(Video.id)).filter(
        Video.user_id == user_id
    ).scalar()
    
    # Public videos
    public_videos = db.query(func.count(Video.id)).filter(
        Video.user_id == user_id,
        Video.is_public == True
    ).scalar()
    
    # Favorite videos
    favorite_videos = db.query(func.count(Video.id)).filter(
        Video.user_id == user_id,
        Video.is_favorite == True
    ).scalar()
    
    # Total views
    total_views = db.query(func.sum(Video.view_count)).filter(
        Video.user_id == user_id
    ).scalar() or 0
    
    # Total duration
    total_duration = db.query(func.sum(Video.duration)).filter(
        Video.user_id == user_id
    ).scalar() or 0
    
    # Average completion rate
    avg_completion = db.query(func.avg(Video.completion_rate)).filter(
        Video.user_id == user_id
    ).scalar() or 0
    
    return {
        "total_videos": total_videos,
        "public_videos": public_videos,
        "favorite_videos": favorite_videos,
        "total_views": total_views,
        "total_duration_minutes": round(total_duration / 60, 2),
        "average_completion_rate": round(avg_completion, 2),
        "public_percentage": round((public_videos / total_videos * 100) if total_videos > 0 else 0, 2)
    }

def batch_update_videos(
    db: Session,
    video_ids: List[str],
    update_data: Dict[str, Any],
    user_id: str,
    is_admin: bool = False
) -> int:
    """Batch update multiple videos"""
    query = db.query(Video).filter(Video.id.in_(video_ids))
    
    if not is_admin:
        query = query.filter(Video.user_id == user_id)
    
    updated_count = query.update(update_data, synchronize_session=False)
    db.commit()
    return updated_count

# ============= PROGRESS CRUD =============

def update_progress(
    db: Session,
    video_id: str,
    user_id: str,
    progress: ProgressUpdate
) -> Optional[VideoProgress]:
    """Update or create video progress"""
    # Verify video exists and is accessible
    video = get_video(db, video_id, user_id)
    if not video:
        return None
    
    db_progress = db.query(VideoProgress).filter(
        VideoProgress.video_id == video_id,
        VideoProgress.user_id == user_id
    ).first()
    
    now = datetime.utcnow()
    
    if db_progress:
        # Update existing progress
        db_progress.watched_duration = progress.watched_duration
        db_progress.completion_percentage = progress.completion_percentage
        db_progress.last_watched_at = now
        
        if progress.completion_percentage >= 90 and not db_progress.is_completed:
            db_progress.is_completed = True
            db_progress.completed_at = now
    else:
        # Create new progress
        db_progress = VideoProgress(
            video_id=video_id,
            user_id=user_id,
            watched_duration=progress.watched_duration,
            completion_percentage=progress.completion_percentage,
            is_completed=progress.completion_percentage >= 90,
            completed_at=now if progress.completion_percentage >= 90 else None
        )
        db.add(db_progress)
    
    # Update video's completion rate if this is higher
    if progress.completion_percentage > video.completion_rate:
        video.completion_rate = progress.completion_percentage
    
    db.commit()
    db.refresh(db_progress)
    return db_progress

def get_progress(db: Session, video_id: str, user_id: str) -> Optional[VideoProgress]:
    """Get user's progress for a video"""
    return db.query(VideoProgress).filter(
        VideoProgress.video_id == video_id,
        VideoProgress.user_id == user_id
    ).first()

def get_user_progress_list(
    db: Session,
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    completed_only: Optional[bool] = None,
    min_completion: Optional[float] = None,
    subject_id: Optional[str] = None
) -> Tuple[List[VideoProgress], int]:
    """Get all progress for a user with filters"""
    query = db.query(VideoProgress).filter(VideoProgress.user_id == user_id)
    
    if completed_only is not None:
        query = query.filter(VideoProgress.is_completed == completed_only)
    
    if min_completion:
        query = query.filter(VideoProgress.completion_percentage >= min_completion)
    
    if subject_id:
        query = query.join(Video).filter(Video.subject_id == subject_id)
    
    total = query.count()
    progress_list = query.order_by(
        desc(VideoProgress.last_watched_at)
    ).offset(skip).limit(limit).all()
    
    return progress_list, total

def get_recently_watched(
    db: Session,
    user_id: str,
    limit: int = 10
) -> List[VideoProgress]:
    """Get user's recently watched videos"""
    return (
        db.query(VideoProgress)
        .filter(VideoProgress.user_id == user_id)
        .order_by(desc(VideoProgress.last_watched_at))
        .limit(limit)
        .all()
    )

def get_continue_watching(
    db: Session,
    user_id: str,
    limit: int = 10
) -> List[VideoProgress]:
    """Get videos to continue watching (incomplete progress)"""
    return (
        db.query(VideoProgress)
        .filter(
            VideoProgress.user_id == user_id,
            VideoProgress.is_completed == False,
            VideoProgress.completion_percentage < 90
        )
        .order_by(desc(VideoProgress.last_watched_at))
        .limit(limit)
        .all()
    )

def reset_progress(db: Session, video_id: str, user_id: str) -> bool:
    """Reset progress for a video"""
    db_progress = get_progress(db, video_id, user_id)
    
    if not db_progress:
        return False
    
    db_progress.watched_duration = 0
    db_progress.completion_percentage = 0
    db_progress.is_completed = False
    db_progress.completed_at = None
    db_progress.last_watched_at = datetime.utcnow()
    
    db.commit()
    return True

def delete_progress(db: Session, video_id: str, user_id: str) -> bool:
    """Delete progress for a video"""
    db_progress = get_progress(db, video_id, user_id)
    
    if not db_progress:
        return False
    
    db.delete(db_progress)
    db.commit()
    return True

def get_watch_history(
    db: Session,
    user_id: str,
    days: int = 30
) -> Dict[str, Any]:
    """Get user's watch history for the last N days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Daily watch time
    daily_stats = (
        db.query(
            func.date(VideoProgress.last_watched_at).label('date'),
            func.sum(VideoProgress.watched_duration).label('total_watch_time'),
            func.count(VideoProgress.id).label('videos_watched')  # ✅ Fixed
        )
        .filter(
            VideoProgress.user_id == user_id,
            VideoProgress.last_watched_at >= cutoff_date
        )
        .group_by(func.date(VideoProgress.last_watched_at))
        .order_by(desc(func.date(VideoProgress.last_watched_at)))
        .all()
    )
    
    # Subject distribution
    subject_stats = (
        db.query(
            Video.subject_name,
            func.count(Video.id).label('videos_watched'),  # ✅ Fixed
            func.sum(VideoProgress.watched_duration).label('total_watch_time'),
            func.avg(VideoProgress.completion_percentage).label('avg_completion')
        )
        .join(VideoProgress, Video.id == VideoProgress.video_id)
        .filter(
            VideoProgress.user_id == user_id,
            VideoProgress.last_watched_at >= cutoff_date
        )
        .group_by(Video.subject_name)
        .order_by(desc(func.sum(VideoProgress.watched_duration)))
        .all()
    )
    
    return {
        "daily_stats": [
            {
                "date": str(stat.date),
                "total_watch_time": stat.total_watch_time or 0,
                "videos_watched": stat.videos_watched or 0
            }
            for stat in daily_stats
        ],
        "subject_stats": [
            {
                "subject_name": stat.subject_name,
                "videos_watched": stat.videos_watched or 0,
                "total_watch_time": stat.total_watch_time or 0,
                "average_completion": round(stat.avg_completion or 0, 2)
            }
            for stat in subject_stats
        ]
    }

# ============= LIKES CRUD =============

def toggle_like(db: Session, video_id: str, user_id: str) -> Tuple[bool, int]:
    """Toggle like on a video. Returns (liked status, like count)"""
    # Check if video exists and is accessible
    video = get_video(db, video_id, user_id)
    if not video:
        return False, 0
    
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
    video.like_count = db.query(func.count(VideoLike.id)).filter(
        VideoLike.video_id == video_id
    ).scalar()
    
    db.commit()
    
    return liked, video.like_count

def has_liked(db: Session, video_id: str, user_id: str) -> bool:
    """Check if user has liked a video"""
    like = db.query(VideoLike).filter(
        VideoLike.video_id == video_id,
        VideoLike.user_id == user_id
    ).first()
    return like is not None

def get_liked_videos(
    db: Session,
    user_id: str,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[Video], int]:
    """Get videos liked by a user"""
    query = db.query(Video).join(VideoLike).filter(
        VideoLike.user_id == user_id,
        Video.is_public == True
    )
    
    total = query.count()
    videos = query.order_by(desc(VideoLike.created_at)).offset(skip).limit(limit).all()
    
    return videos, total

# ============= COMMENTS CRUD =============

def add_comment(
    db: Session,
    video_id: str,
    user_id: str,
    comment: VideoCommentCreate
) -> Optional[VideoComment]:
    """Add a comment to a video"""
    # Verify video exists and is accessible
    video = get_video(db, video_id, user_id)
    if not video:
        return None
    
    db_comment = VideoComment(
        video_id=video_id,
        user_id=user_id,
        content=comment.content
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_comment(db: Session, comment_id: str) -> Optional[VideoComment]:
    """Get a comment by ID"""
    return db.query(VideoComment).filter(VideoComment.id == comment_id).first()

def get_comments(
    db: Session,
    video_id: str,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Tuple[List[VideoComment], int]:
    """Get all comments for a video with pagination"""
    query = db.query(VideoComment).filter(VideoComment.video_id == video_id)
    
    # Apply sorting
    sort_column = getattr(VideoComment, sort_by, VideoComment.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    total = query.count()
    comments = query.offset(skip).limit(limit).all()
    
    return comments, total

def update_comment(
    db: Session,
    comment_id: str,
    user_id: str,
    new_content: str
) -> Optional[VideoComment]:
    """Update a comment"""
    db_comment = db.query(VideoComment).filter(
        VideoComment.id == comment_id,
        VideoComment.user_id == user_id
    ).first()
    
    if not db_comment:
        return None
    
    db_comment.content = new_content
    db.commit()
    db.refresh(db_comment)
    return db_comment

def delete_comment(
    db: Session,
    comment_id: str,
    user_id: str,
    is_admin: bool = False
) -> bool:
    """Delete a comment"""
    query = db.query(VideoComment).filter(VideoComment.id == comment_id)
    
    if not is_admin:
        query = query.filter(VideoComment.user_id == user_id)
    
    db_comment = query.first()
    
    if not db_comment:
        return False
    
    db.delete(db_comment)
    db.commit()
    return True

def get_user_comments(
    db: Session,
    user_id: str,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[VideoComment], int]:
    """Get all comments made by a user"""
    query = db.query(VideoComment).filter(VideoComment.user_id == user_id)
    
    total = query.count()
    comments = query.order_by(desc(VideoComment.created_at)).offset(skip).limit(limit).all()
    
    return comments, total

# ============= BULK OPERATIONS =============

def get_videos_by_ids(db: Session, video_ids: List[str]) -> List[Video]:
    """Get multiple videos by their IDs"""
    return db.query(Video).filter(Video.id.in_(video_ids)).all()

def delete_user_videos(db: Session, user_id: str) -> int:
    """Delete all videos owned by a user"""
    # Get all video IDs first
    video_ids = [video.id for video in db.query(Video.id).filter(Video.user_id == user_id).all()]
    
    if not video_ids:
        return 0
    
    # Delete related data
    db.query(VideoProgress).filter(VideoProgress.video_id.in_(video_ids)).delete()
    db.query(VideoLike).filter(VideoLike.video_id.in_(video_ids)).delete()
    db.query(VideoComment).filter(VideoComment.video_id.in_(video_ids)).delete()
    
    # Delete videos
    deleted_count = db.query(Video).filter(Video.user_id == user_id).delete()
    db.commit()
    
    return deleted_count

def get_video_completion_analytics(
    db: Session,
    video_id: str
) -> Dict[str, Any]:
    """Get analytics about video completion patterns"""
    # Get completion distribution in 10% increments
    completion_distribution = {}
    for i in range(0, 101, 10):
        lower_bound = i
        upper_bound = i + 9 if i < 100 else 100
        
        count = db.query(func.count(VideoProgress.id)).filter(
            VideoProgress.video_id == video_id,
            VideoProgress.completion_percentage >= lower_bound,
            VideoProgress.completion_percentage <= upper_bound
        ).scalar()
        
        range_key = f"{lower_bound}-{upper_bound}%"
        completion_distribution[range_key] = count
    
    # Get average watch time
    avg_watch_time = db.query(func.avg(VideoProgress.watched_duration)).filter(
        VideoProgress.video_id == video_id
    ).scalar() or 0
    
    # Get retention rate (users who watched > 50%)
    total_watchers = db.query(func.count(VideoProgress.id)).filter(
        VideoProgress.video_id == video_id
    ).scalar() or 0
    
    retained_watchers = db.query(func.count(VideoProgress.id)).filter(
        VideoProgress.video_id == video_id,
        VideoProgress.completion_percentage >= 50
    ).scalar() or 0
    
    retention_rate = (retained_watchers / total_watchers * 100) if total_watchers > 0 else 0
    
    return {
        "completion_distribution": completion_distribution,
        "average_watch_time_seconds": round(avg_watch_time, 2),
        "total_watchers": total_watchers,
        "retained_watchers": retained_watchers,
        "retention_rate": round(retention_rate, 2),
        "completion_rates": {
            "quarter_completion": completion_distribution.get("25-34%", 0),
            "half_completion": completion_distribution.get("50-59%", 0),
            "three_quarters_completion": completion_distribution.get("75-84%", 0),
            "full_completion": completion_distribution.get("90-100%", 0)
        }
    }

def get_subject_video_analytics(
    db: Session,
    subject_id: str
) -> Dict[str, Any]:
    """Get analytics for all videos in a subject"""
    # Get all videos for the subject
    videos = db.query(Video).filter(Video.subject_id == subject_id).all()
    
    if not videos:
        return {}
    
    video_data = []
    total_views = 0
    total_likes = 0
    total_comments = 0
    total_duration = 0
    
    for video in videos:
        video_stats = {
            "video_id": video.id,
            "title": video.title,
            "views": video.view_count,
            "likes": video.like_count,
            "comments": db.query(func.count(VideoComment.id)).filter(
                VideoComment.video_id == video.id
            ).scalar() or 0,
            "duration": video.duration,
            "completion_rate": video.completion_rate,
            "created_at": video.created_at
        }
        
        video_data.append(video_stats)
        total_views += video.view_count
        total_likes += video.like_count
        total_duration += video.duration
    
    # Sort videos by views (most popular first)
    video_data.sort(key=lambda x: x["views"], reverse=True)
    
    return {
        "subject_id": subject_id,
        "total_videos": len(videos),
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_duration_minutes": round(total_duration / 60, 2),
        "average_completion_rate": round(
            sum(v["completion_rate"] for v in video_data) / len(video_data) if video_data else 0, 2
        ),
        "average_views_per_video": round(total_views / len(videos), 2),
        "top_videos": video_data[:5]  # Top 5 most viewed videos
    }

def cleanup_orphaned_progress(db: Session, batch_size: int = 100) -> int:
    """Clean up progress records for deleted videos"""
    # Find progress records where the video no longer exists
    subquery = db.query(Video.id)
    orphaned_progress = db.query(VideoProgress).filter(
        ~VideoProgress.video_id.in_(subquery)
    ).limit(batch_size).all()
    
    deleted_count = 0
    for progress in orphaned_progress:
        db.delete(progress)
        deleted_count += 1
    
    if deleted_count > 0:
        db.commit()
    
    return deleted_count