from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.schemas.notification import NotificationCreate, NotificationUpdate
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

def create_notification(db: Session, user_id: str, notification: NotificationCreate) -> Notification:
    """
    Create a new notification.
    """
    db_notification = Notification(
        user_id=user_id,
        **notification.dict()
    )
    
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    return db_notification


def get_notification(db: Session, notification_id: str, user_id: str) -> Optional[Notification]:
    """
    Get a specific notification by ID.
    """
    return db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()


def get_user_notifications(
    db: Session,
    user_id: str,
    is_read: Optional[bool] = None,
    is_archived: Optional[bool] = None,
    notification_type: Optional[str] = None,
    priority: Optional[str] = None,
    page: int = 1,
    page_size: int = 50
) -> tuple[List[Notification], int, int]:
    """
    Get all notifications for a user with optional filters.
    Returns (notifications, total_count, unread_count).
    """
    query = db.query(Notification).filter(Notification.user_id == user_id)
    
    # Apply filters
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)
    
    if is_archived is not None:
        query = query.filter(Notification.is_archived == is_archived)
    
    if notification_type:
        query = query.filter(Notification.type == notification_type)
    
    if priority:
        query = query.filter(Notification.priority == priority)
    
    # Get total count
    total = query.count()
    
    # Get unread count
    unread_count = db.query(func.count(Notification.id)).filter(
        Notification.user_id == user_id,
        Notification.is_read == False,
        Notification.is_archived == False
    ).scalar()
    
    # Apply ordering: pinned first, then by created_at desc
    notifications = query.order_by(
        desc(Notification.is_pinned),
        desc(Notification.created_at)
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    return notifications, total, unread_count


def get_recent_notifications(
    db: Session,
    user_id: str,
    hours: int = 24,
    limit: int = 10
) -> List[Notification]:
    """
    Get recent notifications from the last N hours.
    """
    time_threshold = datetime.utcnow() - timedelta(hours=hours)
    
    return db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.created_at >= time_threshold,
        Notification.is_archived == False
    ).order_by(desc(Notification.created_at)).limit(limit).all()


def update_notification(
    db: Session,
    notification_id: str,
    user_id: str,
    update: NotificationUpdate
) -> Optional[Notification]:
    """
    Update a notification.
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if not notification:
        return None
    
    # Update fields
    if update.is_read is not None:
        notification.is_read = update.is_read
        if update.is_read and not notification.read_at:
            notification.read_at = datetime.utcnow()
    
    if update.is_archived is not None:
        notification.is_archived = update.is_archived
    
    if update.is_pinned is not None:
        notification.is_pinned = update.is_pinned
    
    db.commit()
    db.refresh(notification)
    
    return notification


def mark_as_read(db: Session, notification_id: str, user_id: str) -> Optional[Notification]:
    """
    Mark a notification as read.
    """
    return update_notification(
        db,
        notification_id,
        user_id,
        NotificationUpdate(is_read=True)
    )


def mark_all_as_read(db: Session, user_id: str) -> int:
    """
    Mark all unread notifications as read.
    Returns the count of notifications marked as read.
    """
    result = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({
        "is_read": True,
        "read_at": datetime.utcnow()
    })
    
    db.commit()
    return result


def delete_notification(db: Session, notification_id: str, user_id: str) -> bool:
    """
    Delete a notification.
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if not notification:
        return False
    
    db.delete(notification)
    db.commit()
    
    return True


def delete_all_read(db: Session, user_id: str) -> int:
    """
    Delete all read notifications.
    Returns the count of deleted notifications.
    """
    result = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == True
    ).delete()
    
    db.commit()
    return result


def archive_notification(db: Session, notification_id: str, user_id: str) -> Optional[Notification]:
    """
    Archive a notification.
    """
    return update_notification(
        db,
        notification_id,
        user_id,
        NotificationUpdate(is_archived=True)
    )


def archive_all_read(db: Session, user_id: str) -> int:
    """
    Archive all read notifications.
    Returns the count of archived notifications.
    """
    result = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == True,
        Notification.is_archived == False
    ).update({"is_archived": True})
    
    db.commit()
    return result


def toggle_pin(db: Session, notification_id: str, user_id: str) -> Optional[Notification]:
    """
    Toggle pin status of a notification.
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    
    if not notification:
        return None
    
    notification.is_pinned = not notification.is_pinned
    db.commit()
    db.refresh(notification)
    
    return notification


def get_notification_statistics(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Get statistics about user's notifications.
    """
    total = db.query(func.count(Notification.id)).filter(
        Notification.user_id == user_id
    ).scalar()
    
    unread = db.query(func.count(Notification.id)).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).scalar()
    
    read = db.query(func.count(Notification.id)).filter(
        Notification.user_id == user_id,
        Notification.is_read == True
    ).scalar()
    
    archived = db.query(func.count(Notification.id)).filter(
        Notification.user_id == user_id,
        Notification.is_archived == True
    ).scalar()
    
    # Count by type
    by_type = db.query(
        Notification.type,
        func.count(Notification.id)
    ).filter(
        Notification.user_id == user_id
    ).group_by(Notification.type).all()
    
    # Count by priority
    by_priority = db.query(
        Notification.priority,
        func.count(Notification.id)
    ).filter(
        Notification.user_id == user_id
    ).group_by(Notification.priority).all()
    
    # Recent count (last 24 hours)
    time_threshold = datetime.utcnow() - timedelta(hours=24)
    recent_count = db.query(func.count(Notification.id)).filter(
        Notification.user_id == user_id,
        Notification.created_at >= time_threshold
    ).scalar()
    
    return {
        "total": total,
        "unread": unread,
        "read": read,
        "archived": archived,
        "by_type": dict(by_type),
        "by_priority": dict(by_priority),
        "recent_count": recent_count
    }


def clean_expired_notifications(db: Session) -> int:
    """
    Delete all expired notifications.
    This should be run periodically (e.g., daily cron job).
    Returns the count of deleted notifications.
    """
    now = datetime.utcnow()
    
    result = db.query(Notification).filter(
        Notification.expires_at.isnot(None),
        Notification.expires_at <= now
    ).delete()
    
    db.commit()
    return result