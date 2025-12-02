from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.schemas.analytics import (
    AnalyticsEventCreate,
    AnalyticsEventResponse,
    DashboardSummary,
    TimeSeriesData,
    StudyGoalCreate,
    StudyGoalUpdate,
    StudyGoalResponse,
    SubjectAnalyticsResponse,
    AnalyticsInsights
)
from app.crud import analytics as analytics_crud

router = APIRouter(prefix="/analytics", tags=["analytics"])

# Event Tracking
@router.post("/events", response_model=AnalyticsEventResponse, status_code=201)
def track_event(
    event: AnalyticsEventCreate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Track an analytics event.
    
    Event types:
    - video_watched: User watched a video
    - quiz_completed: User completed a quiz
    - note_created: User created a note
    - subject_studied: General subject study session
    - game_played: User played an educational game
    - document_scanned: User scanned a document
    - study_session: General study session
    
    Automatically updates daily metrics, subject analytics, and goal progress.
    """
    try:
        return analytics_crud.track_event(db, user_id, event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to track event: {str(e)}")


# Dashboard
@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard summary.
    
    Includes:
    - Total study time and activities
    - Current and longest streaks
    - Weekly metrics
    - Performance averages
    - Top subjects
    - Recent activity
    - Goals progress
    """
    return analytics_crud.get_dashboard_summary(db, user_id)


@router.get("/time-series", response_model=TimeSeriesData)
def get_time_series(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    metric: str = Query(..., description="Metric type: study_time, activities, performance"),
    days: int = Query(30, ge=7, le=365, description="Number of days"),
    db: Session = Depends(get_db)
):
    """
    Get time series data for charts.
    
    Metrics:
    - study_time: Daily study time in minutes
    - activities: Videos, quizzes, notes breakdown
    - performance: Average quiz scores over time
    
    Returns Chart.js compatible format.
    """
    if metric not in ['study_time', 'activities', 'performance']:
        raise HTTPException(status_code=400, detail="Invalid metric type")
    
    return analytics_crud.get_time_series_data(db, user_id, metric, days)


# Subject Analytics
@router.get("/subjects")
def get_subject_analytics(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Get analytics for all subjects studied by the user.
    
    Includes time spent, activity counts, performance, and mastery levels.
    """
    subjects = analytics_crud.get_subject_analytics_list(db, user_id)
    return {"subjects": subjects}


# Goals
@router.post("/goals", response_model=StudyGoalResponse, status_code=201)
def create_goal(
    goal: StudyGoalCreate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Create a new study goal.
    
    Goal types:
    - daily_time: Daily study time target (minutes)
    - weekly_quizzes: Weekly quiz completion target
    - videos_watched: Video watching target
    - subject_mastery: Subject-specific mastery goal
    
    Periods: daily, weekly, monthly, semester
    """
    try:
        return analytics_crud.create_goal(db, user_id, goal)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create goal: {str(e)}")


@router.get("/goals")
def get_goals(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    active_only: bool = Query(False, description="Show only active goals"),
    db: Session = Depends(get_db)
):
    """Get user's study goals."""
    goals = analytics_crud.get_user_goals(db, user_id, active_only)
    return {"goals": goals}


@router.put("/goals/{goal_id}", response_model=StudyGoalResponse)
def update_goal(
    goal_id: str,
    update: StudyGoalUpdate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """Update a study goal."""
    # Implementation would go here
    raise HTTPException(status_code=501, detail="Not implemented")


# Insights
@router.get("/insights", response_model=AnalyticsInsights)
def get_insights(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Get AI-generated insights and recommendations.
    
    Includes:
    - Study trends (increasing/decreasing)
    - Performance insights
    - Achievement notifications
    - Personalized recommendations
    - Subject-specific suggestions
    """
    return analytics_crud.generate_insights(db, user_id)


# Export/Reports
@router.get("/export")
def export_data(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    format: str = Query("json", description="Export format: json, csv"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Export analytics data.
    
    Formats: json, csv
    Can filter by date range.
    """
    # Placeholder for export functionality
    raise HTTPException(status_code=501, detail="Export feature coming soon")