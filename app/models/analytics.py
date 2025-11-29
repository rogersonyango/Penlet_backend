from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, JSON, Date, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.session import Base
import uuid
import enum
from datetime import datetime

class ActivityType(str, enum.Enum):
    """Activity types for tracking"""
    VIDEO_WATCHED = "video_watched"
    QUIZ_COMPLETED = "quiz_completed"
    NOTE_CREATED = "note_created"
    SUBJECT_STUDIED = "subject_studied"
    GAME_PLAYED = "game_played"
    DOCUMENT_SCANNED = "document_scanned"
    STUDY_SESSION = "study_session"

class MetricPeriod(str, enum.Enum):
    """Time periods for metrics"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SEMESTER = "semester"

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Event information
    event_type = Column(SQLEnum(ActivityType), nullable=False, index=True)
    event_category = Column(String(50))  # 'learning', 'assessment', 'productivity'
    
    # Context
    subject_id = Column(String, index=True)
    subject_name = Column(String(100))
    related_entity_id = Column(String)  # ID of video, quiz, note, etc.
    related_entity_type = Column(String(50))  # 'video', 'quiz', 'note', etc.
    
    # Metrics
    duration = Column(Integer)  # in seconds
    score = Column(Float)  # 0-100 for quizzes/games
    completion_rate = Column(Float)  # 0-100
    
    # Event data (JSON field)
    event_data = Column(JSON, default=dict)
    # Example: {
    #   "quiz_questions": 10,
    #   "correct_answers": 8,
    #   "difficulty": "medium",
    #   "tags": ["algebra", "equations"]
    # }
    
    # Session tracking
    session_id = Column(String)  # Group related events
    device_type = Column(String(50))  # 'mobile', 'tablet', 'desktop'
    
    # Timestamps
    event_date = Column(Date, nullable=False, index=True)
    event_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<AnalyticsEvent(id={self.id}, type={self.event_type}, user={self.user_id})>"


class DailyMetric(Base):
    __tablename__ = "daily_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    metric_date = Column(Date, nullable=False, index=True)
    
    # Study metrics
    total_study_time = Column(Integer, default=0)  # minutes
    videos_watched = Column(Integer, default=0)
    quizzes_completed = Column(Integer, default=0)
    notes_created = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    documents_scanned = Column(Integer, default=0)
    
    # Performance metrics
    average_quiz_score = Column(Float, default=0.0)
    average_game_score = Column(Float, default=0.0)
    completion_rate = Column(Float, default=0.0)
    
    # Engagement
    subjects_studied = Column(Integer, default=0)
    active_time_minutes = Column(Integer, default=0)
    sessions_count = Column(Integer, default=0)
    
    # Goals
    daily_goal_met = Column(Boolean, default=False)
    streak_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<DailyMetric(user={self.user_id}, date={self.metric_date}, time={self.total_study_time})>"


class SubjectAnalytics(Base):
    __tablename__ = "subject_analytics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    subject_id = Column(String, nullable=False, index=True)
    subject_name = Column(String(100), nullable=False)
    
    # Time spent
    total_time_minutes = Column(Integer, default=0)
    last_studied_at = Column(DateTime(timezone=True))
    
    # Activities count
    videos_watched = Column(Integer, default=0)
    quizzes_completed = Column(Integer, default=0)
    notes_created = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    
    # Performance
    average_quiz_score = Column(Float, default=0.0)
    quiz_count = Column(Integer, default=0)
    average_game_score = Column(Float, default=0.0)
    game_count = Column(Integer, default=0)
    
    # Progress
    completion_percentage = Column(Float, default=0.0)  # Overall subject completion
    mastery_level = Column(String(20))  # 'beginner', 'intermediate', 'advanced', 'expert'
    
    # Engagement
    study_streak = Column(Integer, default=0)  # consecutive days
    sessions_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<SubjectAnalytics(user={self.user_id}, subject={self.subject_name})>"


class StudyGoal(Base):
    __tablename__ = "study_goals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Goal details
    goal_type = Column(String(50), nullable=False)  # 'daily_time', 'weekly_quizzes', 'subject_mastery'
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Target
    target_value = Column(Float, nullable=False)
    target_unit = Column(String(50))  # 'minutes', 'count', 'percentage'
    current_value = Column(Float, default=0.0)
    
    # Period
    period = Column(SQLEnum(MetricPeriod), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    completion_percentage = Column(Float, default=0.0)
    
    # Context
    subject_id = Column(String)  # Optional: subject-specific goal
    
    # Timestamps
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<StudyGoal(id={self.id}, title={self.title}, progress={self.completion_percentage}%)>"