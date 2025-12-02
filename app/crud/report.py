from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from app.models.report import Report
from app.models.subject import Subject
from app.models.video import Video, VideoProgress
from app.schemas.report import ReportCreate, ReportUpdate, GenerateReportRequest
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

def generate_report_analytics(
    db: Session,
    user_id: str,
    start_date: datetime,
    end_date: datetime,
    subject_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate comprehensive analytics for a report.
    Aggregates data from subjects, videos, quizzes, and notes.
    """
    analytics = {
        "subjects": [],
        "videos": {
            "total_watched": 0,
            "total_duration": 0,
            "by_subject": {},
            "completion_rate": 0.0,
            "most_watched": []
        },
        "quizzes": {
            "total_completed": 0,
            "average_score": 0.0,
            "by_subject": {},
            "best_scores": []
        },
        "notes": {
            "total_created": 0,
            "by_subject": {},
            "recent": []
        },
        "study_time": {
            "total_hours": 0.0,
            "by_day": {},
            "by_subject": {}
        },
        "completion_rate": 0.0,
        "average_score": 0.0,
        "total_activities": 0
    }
    
    # Get subjects (filter by subject_id if provided)
    subjects_query = db.query(Subject).filter(Subject.user_id == user_id)
    if subject_id:
        subjects_query = subjects_query.filter(Subject.id == subject_id)
    
    subjects = subjects_query.all()
    analytics["subjects"] = [
        {
            "id": s.id,
            "name": s.name,
            "code": s.code,
            "color": s.color,
            "notes_count": s.notes_count,
            "videos_count": s.videos_count,
            "quizzes_count": s.quizzes_count
        }
        for s in subjects
    ]
    
    # Get video watch data
    video_progress_query = db.query(VideoProgress).join(Video).filter(
        Video.user_id == user_id,
        VideoProgress.last_watched_at >= start_date,
        VideoProgress.last_watched_at <= end_date
    )
    
    if subject_id:
        video_progress_query = video_progress_query.filter(Video.subject_id == subject_id)
    
    video_progress = video_progress_query.all()
    
    analytics["videos"]["total_watched"] = len(video_progress)
    analytics["videos"]["total_duration"] = sum(vp.watched_duration for vp in video_progress)
    analytics["videos"]["completion_rate"] = (
        sum(vp.completion_percentage for vp in video_progress) / len(video_progress)
        if video_progress else 0.0
    )
    
    # Calculate study time
    analytics["study_time"]["total_hours"] = analytics["videos"]["total_duration"] / 3600
    
    # Get most watched videos
    most_watched = db.query(Video).filter(
        Video.user_id == user_id,
        Video.created_at >= start_date,
        Video.created_at <= end_date
    ).order_by(desc(Video.view_count)).limit(5).all()
    
    analytics["videos"]["most_watched"] = [
        {
            "id": v.id,
            "title": v.title,
            "subject_name": v.subject_name,
            "view_count": v.view_count,
            "duration": v.duration
        }
        for v in most_watched
    ]
    
    # TODO: Add quiz analytics when Quiz model is implemented
    # TODO: Add notes analytics when Note model is implemented
    
    # Calculate total activities
    analytics["total_activities"] = (
        analytics["videos"]["total_watched"] +
        analytics["quizzes"]["total_completed"] +
        analytics["notes"]["total_created"]
    )
    
    return analytics


def create_report(db: Session, user_id: str, request: GenerateReportRequest) -> Report:
    """
    Generate a new report with analytics data.
    """
    # Generate analytics
    analytics = generate_report_analytics(
        db=db,
        user_id=user_id,
        start_date=request.start_date,
        end_date=request.end_date,
        subject_id=request.subject_id
    )
    
    # Create report
    report = Report(
        user_id=user_id,
        title=request.title,
        report_type=request.report_type,
        description=request.description,
        start_date=request.start_date,
        end_date=request.end_date,
        data=analytics,
        total_study_hours=analytics["study_time"]["total_hours"],
        videos_watched=analytics["videos"]["total_watched"],
        quizzes_completed=analytics["quizzes"]["total_completed"],
        notes_created=analytics["notes"]["total_created"],
        average_quiz_score=analytics["quizzes"]["average_score"],
        completion_rate=analytics["videos"]["completion_rate"],
        status="generated"
    )
    
    # TODO: Generate PDF if requested
    if request.generate_pdf:
        # This would call a PDF generation service
        # For now, just mark as not generated
        report.pdf_generated = False
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return report


def get_report(db: Session, report_id: str, user_id: str) -> Optional[Report]:
    """
    Get a specific report and increment view count.
    """
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == user_id
    ).first()
    
    if report:
        report.view_count += 1
        report.last_viewed = datetime.utcnow()
        db.commit()
        db.refresh(report)
    
    return report


def get_user_reports(
    db: Session,
    user_id: str,
    report_type: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[Report], int]:
    """
    Get all reports for a user with optional filters.
    """
    query = db.query(Report).filter(Report.user_id == user_id)
    
    # Apply filters
    if report_type:
        query = query.filter(Report.report_type == report_type)
    
    if is_favorite is not None:
        query = query.filter(Report.is_favorite == is_favorite)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    reports = query.order_by(desc(Report.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    return reports, total


def update_report(db: Session, report_id: str, user_id: str, update: ReportUpdate) -> Optional[Report]:
    """
    Update a report.
    """
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == user_id
    ).first()
    
    if not report:
        return None
    
    # Update fields
    if update.title is not None:
        report.title = update.title
    if update.description is not None:
        report.description = update.description
    if update.is_favorite is not None:
        report.is_favorite = update.is_favorite
    
    db.commit()
    db.refresh(report)
    
    return report


def delete_report(db: Session, report_id: str, user_id: str) -> bool:
    """
    Delete a report.
    """
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == user_id
    ).first()
    
    if not report:
        return False
    
    db.delete(report)
    db.commit()
    
    return True


def toggle_favorite(db: Session, report_id: str, user_id: str) -> Optional[Report]:
    """
    Toggle favorite status of a report.
    """
    report = db.query(Report).filter(
        Report.id == report_id,
        Report.user_id == user_id
    ).first()
    
    if not report:
        return None
    
    report.is_favorite = not report.is_favorite
    db.commit()
    db.refresh(report)
    
    return report


def get_report_statistics(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Get overall statistics about user's reports.
    """
    total_reports = db.query(func.count(Report.id)).filter(
        Report.user_id == user_id
    ).scalar()
    
    favorite_reports = db.query(func.count(Report.id)).filter(
        Report.user_id == user_id,
        Report.is_favorite == True
    ).scalar()
    
    reports_by_type = db.query(
        Report.report_type,
        func.count(Report.id)
    ).filter(
        Report.user_id == user_id
    ).group_by(Report.report_type).all()
    
    total_study_hours = db.query(func.sum(Report.total_study_hours)).filter(
        Report.user_id == user_id
    ).scalar() or 0.0
    
    return {
        "total_reports": total_reports,
        "favorite_reports": favorite_reports,
        "reports_by_type": dict(reports_by_type),
        "total_study_hours": total_study_hours
    }