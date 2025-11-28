from datetime import datetime
from sqlalchemy.orm import Session
from app.models.quiz import Quiz, QuizAttempt
from app.schemas.quiz import QuizCreate, QuizUpdate
from typing import List, Optional
import json

def create_quiz(db: Session, quiz: QuizCreate, created_by: str):
    db_quiz = Quiz(
        title=quiz.title,
        description=quiz.description,
        curriculum=quiz.curriculum,
        time_limit_minutes=quiz.time_limit_minutes,
        questions=quiz.questions,
        created_by=created_by
    )
    db.add(db_quiz)
    db.commit()
    db.refresh(db_quiz)
    return db_quiz

def get_quiz(db: Session, quiz_id: int):
    return db.query(Quiz).filter(Quiz.id == quiz_id).first()

def get_quizzes(db: Session, skip: int = 0, limit: int = 100, curriculum: Optional[str] = None):
    query = db.query(Quiz)
    if curriculum:
        query = query.filter(Quiz.curriculum == curriculum)
    return query.offset(skip).limit(limit).all()

def update_quiz(db: Session, quiz_id: int, quiz_update: QuizUpdate):
    db_quiz = get_quiz(db, quiz_id)
    if not db_quiz:
        return None
    for key, value in quiz_update.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(db_quiz, key, value)
    db.commit()
    db.refresh(db_quiz)
    return db_quiz

def delete_quiz(db: Session, quiz_id: int):
    db_quiz = get_quiz(db, quiz_id)
    if db_quiz:
        db.delete(db_quiz)
        db.commit()
    return db_quiz

def create_attempt(db: Session, quiz_id: int, user_id: str):
    db_attempt = QuizAttempt(quiz_id=quiz_id, user_id=user_id)
    db.add(db_attempt)
    db.commit()
    db.refresh(db_attempt)
    return db_attempt

def get_attempt(db: Session, attempt_id: int):
    return db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()

def get_user_attempts(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id).offset(skip).limit(limit).all()

def submit_answer(db: Session, attempt_id: int, question_id: str, answer: any):
    attempt = get_attempt(db, attempt_id)
    if not attempt:
        return None
    answers = attempt.answers or {}
    answers[question_id] = answer
    attempt.answers = answers
    db.commit()
    return attempt

def finalize_attempt(db: Session, attempt_id: int):
    attempt = get_attempt(db, attempt_id)
    if not attempt or attempt.is_submitted:
        return None
    quiz = db.query(Quiz).filter(Quiz.id == attempt.quiz_id).first()
    if not quiz:
        return None

    # Simple scoring: 1 point per correct answer
    user_answers = attempt.answers or {}
    questions = quiz.questions
    correct = 0
    total = len(questions)
    for q in questions:
        qid = q["id"]
        if user_answers.get(qid) == q["correct_answer"]:
            correct += 1

    attempt.score = correct
    attempt.max_score = total
    attempt.is_submitted = True
    attempt.end_time = datetime.utcnow()
    db.commit()
    db.refresh(attempt)
    return attempt

def get_leaderboard(db: Session, quiz_id: int):
    return (
        db.query(QuizAttempt)
        .filter(QuizAttempt.quiz_id == quiz_id, QuizAttempt.is_submitted == True)
        .order_by(QuizAttempt.score.desc())
        .limit(10)
        .all()
    )

def get_quiz_statistics(db: Session, quiz_id: int):
    attempts = db.query(QuizAttempt).filter(QuizAttempt.quiz_id == quiz_id, QuizAttempt.is_submitted == True).all()
    if not attempts:
        return {"total_attempts": 0, "average_score": 0}
    total = len(attempts)
    avg = sum(a.score for a in attempts if a.score) / total
    return {"total_attempts": total, "average_score": round(avg, 2)}