from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_, case, extract
from app.models.analytics import (
    AnalyticsEvent, DailyMetric, SubjectAnalytics, StudyGoal,
    ActivityType, MetricPeriod
)
from app.schemas.analytics import (
    AnalyticsEventCreate, StudyGoalCreate, StudyGoalUpdate
)
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import calendar

# Event Tracking
def track_event(db: Session, user_id: str, event: AnalyticsEventCreate) -> AnalyticsEvent:
    """Track an analytics event and update daily metrics."""
    # Create event
    db_event = AnalyticsEvent(
        user_id=user_id,
        event_date=date.today(),
        **event.dict()
    )
    
    db.add(db_event)
    
    # Update daily metrics
    update_daily_metrics(db, user_id, event)
    
    # Update subject analytics if applicable
    if event.subject_id:
        update_subject_analytics(db, user_id, event)
    
    # Update goals progress
    update_goals_progress(db, user_id, event)
    
    db.commit()
    db.refresh(db_event)
    
    return db_event


def update_daily_metrics(db: Session, user_id: str, event: AnalyticsEventCreate):
    """Update or create daily metrics based on event."""
    today = date.today()
    
    metric = db.query(DailyMetric).filter(
        DailyMetric.user_id == user_id,
        DailyMetric.metric_date == today
    ).first()
    
    if not metric:
        metric = DailyMetric(user_id=user_id, metric_date=today)
        db.add(metric)
    
    # Update based on event type
    if event.event_type == ActivityType.VIDEO_WATCHED:
        metric.videos_watched += 1
        if event.duration:
            metric.total_study_time += event.duration // 60  # convert to minutes
    
    elif event.event_type == ActivityType.QUIZ_COMPLETED:
        metric.quizzes_completed += 1
        if event.score is not None:
            # Recalculate average
            old_total = metric.average_quiz_score * (metric.quizzes_completed - 1)
            metric.average_quiz_score = (old_total + event.score) / metric.quizzes_completed
    
    elif event.event_type == ActivityType.NOTE_CREATED:
        metric.notes_created += 1
    
    elif event.event_type == ActivityType.GAME_PLAYED:
        metric.games_played += 1
        if event.score is not None:
            old_total = metric.average_game_score * (metric.games_played - 1)
            metric.average_game_score = (old_total + event.score) / metric.games_played
    
    elif event.event_type == ActivityType.DOCUMENT_SCANNED:
        metric.documents_scanned += 1
    
    # Update streak
    update_study_streak(db, user_id)


def update_subject_analytics(db: Session, user_id: str, event: AnalyticsEventCreate):
    """Update subject-specific analytics."""
    subject_analytics = db.query(SubjectAnalytics).filter(
        SubjectAnalytics.user_id == user_id,
        SubjectAnalytics.subject_id == event.subject_id
    ).first()
    
    if not subject_analytics:
        subject_analytics = SubjectAnalytics(
            user_id=user_id,
            subject_id=event.subject_id,
            subject_name=event.subject_name or "Unknown"
        )
        db.add(subject_analytics)
    
    # Update metrics
    if event.duration:
        subject_analytics.total_time_minutes += event.duration // 60
    
    subject_analytics.last_studied_at = datetime.utcnow()
    
    if event.event_type == ActivityType.VIDEO_WATCHED:
        subject_analytics.videos_watched += 1
    elif event.event_type == ActivityType.QUIZ_COMPLETED:
        subject_analytics.quizzes_completed += 1
        subject_analytics.quiz_count += 1
        if event.score is not None:
            old_total = subject_analytics.average_quiz_score * (subject_analytics.quiz_count - 1)
            subject_analytics.average_quiz_score = (old_total + event.score) / subject_analytics.quiz_count
    elif event.event_type == ActivityType.NOTE_CREATED:
        subject_analytics.notes_created += 1
    elif event.event_type == ActivityType.GAME_PLAYED:
        subject_analytics.games_played += 1
        subject_analytics.game_count += 1
        if event.score is not None:
            old_total = subject_analytics.average_game_score * (subject_analytics.game_count - 1)
            subject_analytics.average_game_score = (old_total + event.score) / subject_analytics.game_count
    
    # Calculate mastery level
    total_activities = (subject_analytics.videos_watched + subject_analytics.quizzes_completed +
                       subject_analytics.notes_created + subject_analytics.games_played)
    avg_performance = (subject_analytics.average_quiz_score + subject_analytics.average_game_score) / 2
    
    if total_activities < 5:
        subject_analytics.mastery_level = "beginner"
    elif total_activities < 15 or avg_performance < 60:
        subject_analytics.mastery_level = "intermediate"
    elif avg_performance < 85:
        subject_analytics.mastery_level = "advanced"
    else:
        subject_analytics.mastery_level = "expert"


def update_study_streak(db: Session, user_id: str):
    """Calculate and update study streak."""
    today = date.today()
    
    # Get recent metrics ordered by date desc
    recent_metrics = db.query(DailyMetric).filter(
        DailyMetric.user_id == user_id
    ).order_by(desc(DailyMetric.metric_date)).limit(30).all()
    
    if not recent_metrics:
        return
    
    # Calculate streak
    streak = 0
    current_date = today
    
    for metric in recent_metrics:
        if metric.metric_date == current_date and metric.total_study_time > 0:
            streak += 1
            current_date -= timedelta(days=1)
        elif metric.metric_date < current_date:
            break
    
    # Update today's metric
    today_metric = db.query(DailyMetric).filter(
        DailyMetric.user_id == user_id,
        DailyMetric.metric_date == today
    ).first()
    
    if today_metric:
        today_metric.streak_count = streak


# Goals
def create_goal(db: Session, user_id: str, goal: StudyGoalCreate) -> StudyGoal:
    """Create a new study goal."""
    db_goal = StudyGoal(user_id=user_id, **goal.dict())
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal


def update_goals_progress(db: Session, user_id: str, event: AnalyticsEventCreate):
    """Update progress for relevant active goals."""
    active_goals = db.query(StudyGoal).filter(
        StudyGoal.user_id == user_id,
        StudyGoal.is_active == True,
        StudyGoal.is_completed == False
    ).all()
    
    for goal in active_goals:
        updated = False
        
        if goal.goal_type == "daily_time" and event.duration:
            goal.current_value += event.duration / 60  # minutes
            updated = True
        
        elif goal.goal_type == "weekly_quizzes" and event.event_type == ActivityType.QUIZ_COMPLETED:
            goal.current_value += 1
            updated = True
        
        elif goal.goal_type == "videos_watched" and event.event_type == ActivityType.VIDEO_WATCHED:
            goal.current_value += 1
            updated = True
        
        if updated:
            goal.completion_percentage = min((goal.current_value / goal.target_value) * 100, 100)
            
            if goal.completion_percentage >= 100:
                goal.is_completed = True
                goal.completed_at = datetime.utcnow()


def get_user_goals(db: Session, user_id: str, active_only: bool = False) -> List[StudyGoal]:
    """Get user's study goals."""
    query = db.query(StudyGoal).filter(StudyGoal.user_id == user_id)
    
    if active_only:
        query = query.filter(StudyGoal.is_active == True)
    
    return query.order_by(desc(StudyGoal.created_at)).all()


# Analytics Queries
def get_dashboard_summary(db: Session, user_id: str) -> Dict[str, Any]:
    """Get comprehensive dashboard summary."""
    # Total study time
    total_study_time = db.query(func.sum(DailyMetric.total_study_time)).filter(
        DailyMetric.user_id == user_id
    ).scalar() or 0
    
    # Total activities
    total_activities = db.query(func.count(AnalyticsEvent.id)).filter(
        AnalyticsEvent.user_id == user_id
    ).scalar() or 0
    
    # Current streak
    today_metric = db.query(DailyMetric).filter(
        DailyMetric.user_id == user_id,
        DailyMetric.metric_date == date.today()
    ).first()
    current_streak = today_metric.streak_count if today_metric else 0
    
    # Longest streak
    longest_streak = db.query(func.max(DailyMetric.streak_count)).filter(
        DailyMetric.user_id == user_id
    ).scalar() or 0
    
    # This week
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_metrics = db.query(DailyMetric).filter(
        DailyMetric.user_id == user_id,
        DailyMetric.metric_date >= week_start
    ).all()
    
    week_study_time = sum(m.total_study_time for m in week_metrics)
    week_activities = sum(m.videos_watched + m.quizzes_completed + m.notes_created + 
                         m.games_played for m in week_metrics)
    week_avg_score = sum(m.average_quiz_score for m in week_metrics) / len(week_metrics) if week_metrics else 0
    
    # Overall performance
    all_metrics = db.query(DailyMetric).filter(DailyMetric.user_id == user_id).all()
    overall_avg_score = sum(m.average_quiz_score for m in all_metrics) / len(all_metrics) if all_metrics else 0
    quizzes_completed = sum(m.quizzes_completed for m in all_metrics)
    games_played = sum(m.games_played for m in all_metrics)
    
    # Subjects
    subject_analytics = db.query(SubjectAnalytics).filter(
        SubjectAnalytics.user_id == user_id
    ).order_by(desc(SubjectAnalytics.total_time_minutes)).limit(5).all()
    
    top_subjects = [
        {
            "name": s.subject_name,
            "time": s.total_time_minutes,
            "mastery": s.mastery_level,
            "score": s.average_quiz_score
        }
        for s in subject_analytics
    ]
    
    # Recent events
    recent_events = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.user_id == user_id
    ).order_by(desc(AnalyticsEvent.event_timestamp)).limit(10).all()
    
    # Goals
    active_goals = db.query(func.count(StudyGoal.id)).filter(
        StudyGoal.user_id == user_id,
        StudyGoal.is_active == True
    ).scalar() or 0
    
    goals_completed = db.query(func.count(StudyGoal.id)).filter(
        StudyGoal.user_id == user_id,
        StudyGoal.is_completed == True
    ).scalar() or 0
    
    goals_in_progress = db.query(StudyGoal).filter(
        StudyGoal.user_id == user_id,
        StudyGoal.is_active == True,
        StudyGoal.is_completed == False
    ).limit(5).all()
    
    return {
        "total_study_time_minutes": int(total_study_time),
        "total_activities": total_activities,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "week_study_time": week_study_time,
        "week_activities": week_activities,
        "week_avg_score": round(week_avg_score, 1),
        "overall_avg_score": round(overall_avg_score, 1),
        "quizzes_completed": quizzes_completed,
        "games_played": games_played,
        "subjects_studied": len(subject_analytics),
        "top_subjects": top_subjects,
        "recent_events": recent_events,
        "active_goals": active_goals,
        "goals_completed": goals_completed,
        "goals_in_progress": goals_in_progress
    }


def get_time_series_data(
    db: Session,
    user_id: str,
    metric: str,
    days: int = 30
) -> Dict[str, Any]:
    """Get time series data for charts."""
    end_date = date.today()
    start_date = end_date - timedelta(days=days-1)
    
    metrics = db.query(DailyMetric).filter(
        DailyMetric.user_id == user_id,
        DailyMetric.metric_date >= start_date,
        DailyMetric.metric_date <= end_date
    ).order_by(DailyMetric.metric_date).all()
    
    # Create labels (dates)
    labels = [(start_date + timedelta(days=i)).strftime('%b %d') for i in range(days)]
    
    # Create data map
    data_map = {m.metric_date.strftime('%b %d'): m for m in metrics}
    
    # Build datasets based on metric
    datasets = []
    
    if metric == "study_time":
        data = [data_map.get(label, type('obj', (), {'total_study_time': 0})()).total_study_time for label in labels]
        datasets.append({
            "label": "Study Time (minutes)",
            "data": data,
            "backgroundColor": "#3B82F6",
            "borderColor": "#3B82F6"
        })
    
    elif metric == "activities":
        videos_data = [data_map.get(label, type('obj', (), {'videos_watched': 0})()).videos_watched for label in labels]
        quizzes_data = [data_map.get(label, type('obj', (), {'quizzes_completed': 0})()).quizzes_completed for label in labels]
        notes_data = [data_map.get(label, type('obj', (), {'notes_created': 0})()).notes_created for label in labels]
        
        datasets = [
            {"label": "Videos", "data": videos_data, "backgroundColor": "#8B5CF6"},
            {"label": "Quizzes", "data": quizzes_data, "backgroundColor": "#10B981"},
            {"label": "Notes", "data": notes_data, "backgroundColor": "#F59E0B"}
        ]
    
    elif metric == "performance":
        data = [data_map.get(label, type('obj', (), {'average_quiz_score': 0})()).average_quiz_score for label in labels]
        datasets.append({
            "label": "Average Score (%)",
            "data": data,
            "backgroundColor": "#10B981",
            "borderColor": "#10B981"
        })
    
    return {
        "labels": labels,
        "datasets": datasets
    }


def get_subject_analytics_list(db: Session, user_id: str) -> List[SubjectAnalytics]:
    """Get analytics for all subjects."""
    return db.query(SubjectAnalytics).filter(
        SubjectAnalytics.user_id == user_id
    ).order_by(desc(SubjectAnalytics.total_time_minutes)).all()


def generate_insights(db: Session, user_id: str) -> Dict[str, Any]:
    """Generate AI-like insights and recommendations."""
    insights = []
    recommendations = []
    achievements = []
    
    # Get recent data
    recent_metrics = db.query(DailyMetric).filter(
        DailyMetric.user_id == user_id
    ).order_by(desc(DailyMetric.metric_date)).limit(7).all()
    
    if not recent_metrics:
        return {"insights": [], "recommendations": [], "achievements": []}
    
    # Streak achievement
    current_streak = recent_metrics[0].streak_count if recent_metrics else 0
    if current_streak >= 7:
        achievements.append(f"🔥 {current_streak}-day study streak!")
    
    # Study time trend
    if len(recent_metrics) >= 2:
        recent_avg = sum(m.total_study_time for m in recent_metrics[:3]) / 3
        older_avg = sum(m.total_study_time for m in recent_metrics[3:6]) / 3 if len(recent_metrics) >= 6 else recent_avg
        
        if recent_avg > older_avg * 1.2:
            insights.append({
                "type": "trend",
                "title": "Study Time Increasing",
                "message": f"Your study time has increased by {int((recent_avg - older_avg) / older_avg * 100)}% this week!",
                "icon": "TrendingUp",
                "color": "green"
            })
        elif recent_avg < older_avg * 0.8:
            insights.append({
                "type": "warning",
                "title": "Study Time Decreasing",
                "message": "Your study time has decreased. Try to maintain consistency!",
                "icon": "AlertCircle",
                "color": "orange"
            })
    
    # Performance insights
    avg_score = sum(m.average_quiz_score for m in recent_metrics) / len(recent_metrics)
    if avg_score >= 85:
        achievements.append("⭐ Excellent performance! Average score above 85%")
    elif avg_score < 60:
        recommendations.append("Consider reviewing difficult topics and practicing more quizzes")
    
    # Subject recommendations
    subject_analytics = db.query(SubjectAnalytics).filter(
        SubjectAnalytics.user_id == user_id
    ).order_by(SubjectAnalytics.average_quiz_score).limit(3).all()
    
    for subject in subject_analytics:
        if subject.average_quiz_score < 65:
            recommendations.append(f"Focus on {subject.subject_name} - current score: {subject.average_quiz_score:.0f}%")
    
    return {
        "insights": insights,
        "recommendations": recommendations,
        "achievements": achievements
    }