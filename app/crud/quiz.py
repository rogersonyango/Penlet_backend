# app/crud/quiz.py
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional, Dict, Any
import json
from app.models.quiz import Quiz, QuizAttempt
from app.schemas.quiz import QuizCreate, QuizUpdate
from app.models.user import User

def create_quiz(db: Session, quiz: QuizCreate, created_by: str) -> Quiz:
    """Create a new quiz"""
    db_quiz = Quiz(
        title=quiz.title,
        description=quiz.description,
        curriculum=quiz.curriculum,
        time_limit_minutes=quiz.time_limit_minutes,
        questions=json.dumps([q.model_dump() for q in quiz.questions]),
        created_by=created_by,
        is_active=quiz.is_active if hasattr(quiz, 'is_active') else True
    )
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    return db_quiz

def get_quiz(db: Session, quiz_id: int) -> Optional[Quiz]:
    """Get a single quiz by ID"""
    return db.query(Quiz).filter(Quiz.id == quiz_id).first()

def get_quizzes(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    curriculum: Optional[str] = None,
    search: Optional[str] = None,
    created_by: Optional[str] = None,
    is_active: Optional[bool] = None
) -> List[Quiz]:
    """Get quizzes with optional filters"""
    query = db.query(Quiz)
    
    if curriculum:
        query = query.filter(Quiz.curriculum.ilike(f"%{curriculum}%"))
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Quiz.title.ilike(search_term),
                Quiz.description.ilike(search_term)
            )
        )
    
    if created_by:
        query = query.filter(Quiz.created_by == created_by)
    
    if is_active is not None:
        query = query.filter(Quiz.is_active == is_active)
    
    return query.order_by(Quiz.created_at.desc()).offset(skip).limit(limit).all()

def update_quiz(
    db: Session,
    quiz_id: int,
    quiz_update: QuizUpdate
) -> Optional[Quiz]:
    """Update a quiz"""
    db_quiz = get_quiz(db, quiz_id)
    
    if not db_quiz:
        return None
    
    update_data = quiz_update.model_dump(exclude_unset=True)
    
    # Handle questions serialization
    if 'questions' in update_data and update_data['questions'] is not None:
        update_data['questions'] = json.dumps([q.model_dump() for q in update_data['questions']])
    
    for key, value in update_data.items():
        if value is not None:
            setattr(db_quiz, key, value)
    
    db.commit()
    db.refresh(db_quiz)
    return db_quiz

def delete_quiz(db: Session, quiz_id: int) -> bool:
    """Delete a quiz"""
    db_quiz = get_quiz(db, quiz_id)
    
    if not db_quiz:
        return False
    
    db.delete(db_quiz)
    db.commit()
    return True

def toggle_quiz_active(db: Session, quiz_id: int) -> Optional[Quiz]:
    """Toggle quiz active status"""
    db_quiz = get_quiz(db, quiz_id)
    
    if not db_quiz:
        return None
    
    db_quiz.is_active = not db_quiz.is_active
    db.commit()
    db.refresh(db_quiz)
    return db_quiz

# Quiz Attempt functions
def create_attempt(db: Session, quiz_id: int, user_id: str) -> Optional[QuizAttempt]:
    """Create a new quiz attempt"""
    quiz = get_quiz(db, quiz_id)
    if not quiz or not quiz.is_active:
        return None
    
    db_attempt = QuizAttempt(
        quiz_id=quiz_id,
        user_id=user_id,
        start_time=datetime.utcnow()
    )
    db.add(db_attempt)
    db.commit()
    db.refresh(db_attempt)
    return db_attempt

def get_attempt(db: Session, attempt_id: int) -> Optional[QuizAttempt]:
    """Get a quiz attempt by ID"""
    return db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()

def get_user_attempts(
    db: Session,
    user_id: str,
    quiz_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
) -> List[QuizAttempt]:
    """Get quiz attempts for a user"""
    query = db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id)
    
    if quiz_id:
        query = query.filter(QuizAttempt.quiz_id == quiz_id)
    
    return query.order_by(QuizAttempt.start_time.desc()).offset(skip).limit(limit).all()

def submit_answer(
    db: Session,
    attempt_id: int,
    question_id: str,
    answer: Any
) -> Optional[QuizAttempt]:
    """Submit an answer for a quiz question"""
    attempt = get_attempt(db, attempt_id)
    
    if not attempt or attempt.is_submitted:
        return None
    
    answers = attempt.answers or {}
    answers[question_id] = answer
    attempt.answers = answers
    db.commit()
    db.refresh(attempt)
    return attempt

def submit_attempt(
    db: Session,
    attempt_id: int,
    answers: Dict[str, Any]
) -> Optional[QuizAttempt]:
    """Submit a quiz attempt with all answers"""
    attempt = get_attempt(db, attempt_id)
    
    if not attempt or attempt.is_submitted:
        return None
    
    quiz = get_quiz(db, attempt.quiz_id)
    if not quiz:
        return None
    
    # Update answers
    attempt.answers = answers
    
    # Calculate score
    questions = json.loads(quiz.questions) if isinstance(quiz.questions, str) else quiz.questions
    correct = 0
    total = len(questions)
    
    for question in questions:
        qid = question['id']
        if answers.get(qid) == question['correct_answer']:
            correct += 1
    
    attempt.score = correct
    attempt.max_score = total
    attempt.is_submitted = True
    attempt.end_time = datetime.utcnow()
    
    db.commit()
    db.refresh(attempt)
    return attempt

def finalize_attempt(db: Session, attempt_id: int) -> Optional[QuizAttempt]:
    """Finalize a quiz attempt (calculate score)"""
    attempt = get_attempt(db, attempt_id)
    
    if not attempt or attempt.is_submitted or not attempt.answers:
        return None
    
    quiz = get_quiz(db, attempt.quiz_id)
    if not quiz:
        return None
    
    questions = json.loads(quiz.questions) if isinstance(quiz.questions, str) else quiz.questions
    answers = attempt.answers or {}
    correct = 0
    total = len(questions)
    
    for question in questions:
        qid = question['id']
        if answers.get(qid) == question['correct_answer']:
            correct += 1
    
    attempt.score = correct
    attempt.max_score = total
    attempt.is_submitted = True
    attempt.end_time = datetime.utcnow()
    
    db.commit()
    db.refresh(attempt)
    return attempt

def get_leaderboard(db: Session, quiz_id: int, limit: int = 10) -> List[Dict]:
    """Get quiz leaderboard"""
    return (
        db.query(
            User.username,
            User.full_name,
            QuizAttempt.score,
            QuizAttempt.max_score,
            QuizAttempt.end_time
        )
        .join(User, QuizAttempt.user_id == User.id)
        .filter(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.is_submitted == True,
            QuizAttempt.score.isnot(None)
        )
        .order_by(QuizAttempt.score.desc(), QuizAttempt.end_time.asc())
        .limit(limit)
        .all()
    )

def get_quiz_statistics(db: Session, quiz_id: int) -> Dict[str, Any]:
    """Get statistics for a quiz"""
    attempts = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.is_submitted == True
        )
        .all()
    )
    
    if not attempts:
        return {
            "total_attempts": 0,
            "average_score": 0,
            "completion_rate": 0,
            "score_distribution": {}
        }
    
    total = len(attempts)
    avg_score = sum(a.score for a in attempts if a.score is not None) / total
    
    # Calculate score distribution
    distribution = {}
    for attempt in attempts:
        if attempt.score is not None:
            percentage = (attempt.score / attempt.max_score) * 100
            range_key = f"{int(percentage // 10 * 10)}-{int(percentage // 10 * 10 + 9)}%"
            distribution[range_key] = distribution.get(range_key, 0) + 1
    
    # Calculate completion rate (attempts with score vs total attempts)
    completed = sum(1 for a in attempts if a.score is not None)
    completion_rate = (completed / total) * 100
    
    return {
        "total_attempts": total,
        "average_score": round(avg_score, 2),
        "completion_rate": round(completion_rate, 2),
        "score_distribution": distribution
    }