from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationUpdate,
    NotificationStats
)
from app.crud import notification as notification_crud

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.post("/", response_model=NotificationResponse, status_code=201)
def create_notification(
    notification: NotificationCreate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Create a new notification.
    
    Notification types:
    - quiz_reminder: Quiz deadline reminder
    - video_added: New video available
    - assignment_due: Assignment deadline
    - study_reminder: Study session reminder
    - achievement: Achievement unlocked
    - alarm: From alarms module
    - system: System notifications
    - general: General notifications
    
    Priority levels: low, medium, high, urgent
    """
    try:
        return notification_crud.create_notification(db, user_id, notification)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create notification: {str(e)}")


@router.get("/", response_model=NotificationListResponse)
def get_notifications(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    is_archived: Optional[bool] = Query(None, description="Filter by archived status"),
    notification_type: Optional[str] = Query(None, description="Filter by type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get all notifications for a user with optional filters.
    
    Results are ordered by: pinned first, then newest first.
    """
    notifications, total, unread_count = notification_crud.get_user_notifications(
        db=db,
        user_id=user_id,
        is_read=is_read,
        is_archived=is_archived,
        notification_type=notification_type,
        priority=priority,
        page=page,
        page_size=page_size
    )
    
    return {
        "notifications": notifications,
        "total": total,
        "unread_count": unread_count,
        "page": page,
        "page_size": page_size
    }


@router.get("/recent")
def get_recent_notifications(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(10, ge=1, le=50, description="Max notifications to return"),
    db: Session = Depends(get_db)
):
    """
    Get recent notifications from the last N hours.
    Useful for notification dropdowns.
    """
    notifications = notification_crud.get_recent_notifications(db, user_id, hours, limit)
    return {"notifications": notifications, "count": len(notifications)}


@router.get("/statistics", response_model=NotificationStats)
def get_statistics(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Get notification statistics for the user.
    """
    return notification_crud.get_notification_statistics(db, user_id)


@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(
    notification_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Get a specific notification by ID.
    """
    notification = notification_crud.get_notification(db, notification_id, user_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return notification


@router.put("/{notification_id}", response_model=NotificationResponse)
def update_notification(
    notification_id: str,
    update: NotificationUpdate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Update a notification (read, archived, pinned status).
    """
    notification = notification_crud.update_notification(db, notification_id, user_id, update)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return notification


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Mark a notification as read.
    """
    notification = notification_crud.mark_as_read(db, notification_id, user_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return notification


@router.post("/read-all")
def mark_all_as_read(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Mark all unread notifications as read.
    """
    count = notification_crud.mark_all_as_read(db, user_id)
    return {"message": f"Marked {count} notifications as read"}


@router.post("/{notification_id}/pin", response_model=NotificationResponse)
def toggle_pin(
    notification_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Toggle pin status of a notification.
    Pinned notifications appear first in the list.
    """
    notification = notification_crud.toggle_pin(db, notification_id, user_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return notification


@router.post("/{notification_id}/archive", response_model=NotificationResponse)
def archive_notification(
    notification_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Archive a notification.
    Archived notifications are hidden from the main view.
    """
    notification = notification_crud.archive_notification(db, notification_id, user_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return notification


@router.post("/archive-all-read")
def archive_all_read(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Archive all read notifications.
    """
    count = notification_crud.archive_all_read(db, user_id)
    return {"message": f"Archived {count} notifications"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Delete a notification permanently.
    """
    success = notification_crud.delete_notification(db, notification_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification deleted successfully"}


@router.delete("/delete-all-read")
def delete_all_read(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Delete all read notifications permanently.
    """
    count = notification_crud.delete_all_read(db, user_id)
    return {"message": f"Deleted {count} notifications"}


@router.post("/cleanup-expired")
def cleanup_expired_notifications(
    db: Session = Depends(get_db)
):
    """
    Clean up expired notifications.
    This endpoint should be called periodically (e.g., daily cron job).
    """
    count = notification_crud.clean_expired_notifications(db)
    return {"message": f"Cleaned up {count} expired notifications"}