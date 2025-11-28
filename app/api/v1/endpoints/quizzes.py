from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

# Schemas
from app.schemas.quiz import (
    QuizOut,
    QuizCreate,
    QuizUpdate,
    QuizAttemptStart,
    QuizAttemptOut,
    AnswerSubmit
)

# CRUD functions , these have been given aliased to avoid name conflicts
from app.crud.quiz import (
    get_quizzes,
    get_quiz,
    create_quiz as crud_create_quiz,
    update_quiz as crud_update_quiz,
    delete_quiz as crud_delete_quiz,
    create_attempt as crud_create_attempt,
    get_attempt,
    get_user_attempts,
    submit_answer as crud_submit_answer,
    finalize_attempt as crud_finalize_attempt,
    get_leaderboard,
    get_quiz_statistics
)

from app.db.session import get_db
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])


def require_teacher_or_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Not authorized")



@router.get("/", response_model=List[QuizOut])
def list_quizzes(
    curriculum: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return get_quizzes(db, skip=skip, limit=limit, curriculum=curriculum)


@router.post("/", response_model=QuizOut, dependencies=[Depends(require_teacher_or_admin)])
def create_new_quiz(
    quiz: QuizCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return crud_create_quiz(db, quiz, created_by=current_user["email"])


@router.get("/{quizId}/", response_model=QuizOut)
def get_quiz_by_id(quizId: int, db: Session = Depends(get_db)):
    quiz = get_quiz(db, quizId)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@router.put("/{quizId}/", response_model=QuizOut, dependencies=[Depends(require_teacher_or_admin)])
def update_existing_quiz(
    quizId: int,
    quiz_update: QuizUpdate,
    db: Session = Depends(get_db)
):
    quiz = crud_update_quiz(db, quizId, quiz_update)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@router.delete("/{quizId}/", dependencies=[Depends(require_teacher_or_admin)])
def delete_existing_quiz(quizId: int, db: Session = Depends(get_db)):
    quiz = crud_delete_quiz(db, quizId)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return {"detail": "Quiz deleted"}


# === Attempt Endpoints ===

@router.post("/{quizId}/start/", response_model=QuizAttemptOut)
def start_new_attempt(
    quizId: int,
    attempt: QuizAttemptStart,
    db: Session = Depends(get_db)
):
    quiz = get_quiz(db, quizId)
    if not quiz or not quiz.is_active:
        raise HTTPException(status_code=404, detail="Quiz not available")
    return crud_create_attempt(db, quizId, attempt.user_id)


@router.post("/attempts/{attemptId}/answer/", response_model=QuizAttemptOut)
def record_answer(
    attemptId: int,
    answer: AnswerSubmit,
    db: Session = Depends(get_db)
):
    attempt = crud_submit_answer(db, attemptId, answer.question_id, answer.answer)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    return attempt


@router.post("/attempts/{attemptId}/submit/", response_model=QuizAttemptOut)
def finalize_quiz_attempt(
    attemptId: int,
    db: Session = Depends(get_db)
):
    attempt = crud_finalize_attempt(db, attemptId)
    if not attempt:
        raise HTTPException(status_code=400, detail="Invalid or already submitted attempt")
    return attempt


@router.get("/attempts/{attemptId}/results/", response_model=QuizAttemptOut)
def get_attempt_results(attemptId: int, db: Session = Depends(get_db)):
    attempt = get_attempt(db, attemptId)
    if not attempt or not attempt.is_submitted:
        raise HTTPException(status_code=404, detail="Results not available")
    return attempt


@router.get("/attempts/", response_model=List[QuizAttemptOut])
def get_user_attempts_history(
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    return get_user_attempts(db, user_id)


@router.get("/{quizId}/leaderboard/", response_model=List[QuizAttemptOut])
def get_quiz_leaderboard(quizId: int, db: Session = Depends(get_db)):
    return get_leaderboard(db, quizId)


@router.get("/practice/")
def get_practice_questions(
    curriculum: str = Query(...),
    difficulty: str = Query("medium"),
    db: Session = Depends(get_db)
):
    quizzes = get_quizzes(db, curriculum=curriculum)
    all_questions = []
    for q in quizzes:
        if q.questions:
            all_questions.extend(q.questions)
    return {"questions": all_questions[:5]}


@router.get("/{quizId}/statistics/", dependencies=[Depends(require_teacher_or_admin)])
def get_quiz_statistics_endpoint(quizId: int, db: Session = Depends(get_db)):
    stats = get_quiz_statistics(db, quizId)
    return stats