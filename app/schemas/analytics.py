from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum

# Enums
class ActivityType(str, Enum):
    VIDEO_WATCHED = "video_watched"
    QUIZ_COMPLETED = "quiz_completed"
    NOTE_CREATED = "note_created"
    SUBJECT_STUDIED = "subject_studied"
    GAME_PLAYED = "game_played"
    DOCUMENT_SCANNED = "document_scanned"
    STUDY_SESSION = "study_session"

class MetricPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SEMESTER = "semester"

# Analytics Event Schemas
class AnalyticsEventCreate(BaseModel):
    event_type: ActivityType
    event_category: Optional[str] = Field(None, max_length=50)
    subject_id: Optional[str] = None
    subject_name: Optional[str] = Field(None, max_length=100)
    related_entity_id: Optional[str] = None
    related_entity_type: Optional[str] = Field(None, max_length=50)
    duration: Optional[int] = Field(None, ge=0)
    score: Optional[float] = Field(None, ge=0, le=100)
    completion_rate: Optional[float] = Field(None, ge=0, le=100)
    event_data: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None
    device_type: Optional[str] = Field(None, max_length=50)

class AnalyticsEventResponse(BaseModel):
    id: str
    user_id: str
    event_type: ActivityType
    event_category: Optional[str] = None
    subject_id: Optional[str] = None
    subject_name: Optional[str] = None
    related_entity_id: Optional[str] = None
    related_entity_type: Optional[str] = None
    duration: Optional[int] = None
    score: Optional[float] = None
    completion_rate: Optional[float] = None
    event_data: Dict[str, Any]
    session_id: Optional[str] = None
    device_type: Optional[str] = None
    event_date: date
    event_timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# Daily Metrics
class DailyMetricResponse(BaseModel):
    id: str
    user_id: str
    metric_date: date
    total_study_time: int
    videos_watched: int
    quizzes_completed: int
    notes_created: int
    games_played: int
    documents_scanned: int
    average_quiz_score: float
    average_game_score: float
    completion_rate: float
    subjects_studied: int
    active_time_minutes: int
    sessions_count: int
    daily_goal_met: bool
    streak_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Subject Analytics
class SubjectAnalyticsResponse(BaseModel):
    id: str
    user_id: str
    subject_id: str
    subject_name: str
    total_time_minutes: int
    last_studied_at: Optional[datetime] = None
    videos_watched: int
    quizzes_completed: int
    notes_created: int
    games_played: int
    average_quiz_score: float
    quiz_count: int
    average_game_score: float
    game_count: int
    completion_percentage: float
    mastery_level: Optional[str] = None
    study_streak: int
    sessions_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Study Goals
class StudyGoalCreate(BaseModel):
    goal_type: str = Field(..., max_length=50)
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    target_value: float = Field(..., gt=0)
    target_unit: str = Field(..., max_length=50)
    period: MetricPeriod
    start_date: date
    end_date: Optional[date] = None
    subject_id: Optional[str] = None

class StudyGoalUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    target_value: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None

class StudyGoalResponse(BaseModel):
    id: str
    user_id: str
    goal_type: str
    title: str
    description: Optional[str] = None
    target_value: float
    target_unit: str
    current_value: float
    period: MetricPeriod
    start_date: date
    end_date: Optional[date] = None
    is_active: bool
    is_completed: bool
    completion_percentage: float
    subject_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Dashboard Summary
class DashboardSummary(BaseModel):
    # Overview
    total_study_time_minutes: int
    total_activities: int
    current_streak: int
    longest_streak: int
    
    # This week
    week_study_time: int
    week_activities: int
    week_avg_score: float
    
    # Performance
    overall_avg_score: float
    quizzes_completed: int
    games_played: int
    
    # Subject breakdown
    subjects_studied: int
    top_subjects: List[Dict[str, Any]]
    
    # Recent activity
    recent_events: List[AnalyticsEventResponse]
    
    # Goals
    active_goals: int
    goals_completed: int
    goals_in_progress: List[StudyGoalResponse]

# Time Series Data
class TimeSeriesData(BaseModel):
    labels: List[str]  # Dates or time periods
    datasets: List[Dict[str, Any]]  # Chart.js compatible format
    # Example: {
    #   "label": "Study Time",
    #   "data": [60, 45, 90, 120],
    #   "backgroundColor": "#3B82F6"
    # }

# Performance Report
class PerformanceReport(BaseModel):
    period_start: date
    period_end: date
    
    # Study metrics
    total_study_time: int
    daily_average: float
    most_productive_day: str
    most_productive_hour: int
    
    # Activity counts
    videos_watched: int
    quizzes_completed: int
    notes_created: int
    games_played: int
    
    # Performance
    average_quiz_score: float
    quiz_improvement: float  # percentage change
    best_subject: str
    needs_improvement: List[str]
    
    # Engagement
    study_days: int
    total_days: int
    engagement_rate: float
    
    # Comparison
    vs_previous_period: Dict[str, float]  # percentage changes

# Insights
class StudyInsight(BaseModel):
    type: str  # 'achievement', 'warning', 'suggestion', 'trend'
    title: str
    message: str
    icon: str
    color: str
    action: Optional[str] = None
    action_url: Optional[str] = None

class AnalyticsInsights(BaseModel):
    insights: List[StudyInsight]
    recommendations: List[str]
    achievements: List[str]