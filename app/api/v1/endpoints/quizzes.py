# app/api/v1/endpoints/quiz.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.api.deps import get_current_user, get_current_teacher_or_admin, get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.quiz import (
    QuizCreate, QuizUpdate, QuizResponse,
    QuizAttemptStart, QuizAttemptResponse, AttemptSubmit,
    QuestionSchema, AnswerSubmit
)
from app.crud import quiz as crud_quiz

router = APIRouter()

@router.get("/", response_model=List[QuizResponse])
def list_quizzes(
    curriculum: Optional[str] = Query(None, description="Filter by curriculum"),
    search: Optional[str] = Query(None, description="Search in title/description"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[QuizResponse]:
    """
    List quizzes with optional filtering.
    """
    quizzes = crud_quiz.get_quizzes(
        db=db,
        skip=skip,
        limit=limit,
        curriculum=curriculum,
        search=search,
        created_by=created_by,
        is_active=is_active
    )
    return quizzes

@router.post("/", response_model=QuizResponse)
def create_new_quiz(
    quiz: QuizCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher_or_admin)
) -> QuizResponse:
    """
    Create a new quiz (teachers/admins only).
    """
    return crud_quiz.create_quiz(db=db, quiz=quiz, created_by=current_user.id)

@router.get("/{quiz_id}/", response_model=QuizResponse)
def get_quiz_by_id(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> QuizResponse:
    """
    Retrieve a specific quiz by ID.
    """
    quiz = crud_quiz.get_quiz(db, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Check if quiz is active or user is creator/admin
    if not quiz.is_active and current_user.id != quiz.created_by and current_user.user_type != "admin":
        raise HTTPException(
            status_code=403,
            detail="This quiz is not active"
        )
    
    return quiz

@router.put("/{quiz_id}/", response_model=QuizResponse)
def update_existing_quiz(
    quiz_id: int,
    quiz_update: QuizUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> QuizResponse:
    """
    Update a quiz (creator or admin only).
    """
    quiz = crud_quiz.get_quiz(db, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Check authorization
    if current_user.id != quiz.created_by and current_user.user_type != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update this quiz"
        )
    
    return crud_quiz.update_quiz(db, quiz_id, quiz_update)

@router.delete("/{quiz_id}/")
def delete_existing_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a quiz (creator or admin only).
    """
    quiz = crud_quiz.get_quiz(db, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Check authorization
    if current_user.id != quiz.created_by and current_user.user_type != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not authorized to delete this quiz"
        )
    
    success = crud_quiz.delete_quiz(db, quiz_id)
    if not success:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return {"detail": "Quiz deleted"}

@router.post("/{quiz_id}/toggle-active/", response_model=QuizResponse)
def toggle_quiz_active(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> QuizResponse:
    """
    Toggle quiz active status (creator or admin only).
    """
    quiz = crud_quiz.get_quiz(db, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Check authorization
    if current_user.id != quiz.created_by and current_user.user_type != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not authorized to modify this quiz"
        )
    
    updated = crud_quiz.toggle_quiz_active(db, quiz_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return updated

# Quiz Attempt endpoints
@router.post("/{quiz_id}/attempts/", response_model=QuizAttemptResponse)
def start_new_attempt(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> QuizAttemptResponse:
    """
    Start a new quiz attempt.
    """
    attempt = crud_quiz.create_attempt(db, quiz_id, current_user.id)
    if not attempt:
        raise HTTPException(
            status_code=400,
            detail="Cannot start attempt (quiz not found or not active)"
        )
    return attempt

@router.get("/attempts/{attempt_id}/", response_model=QuizAttemptResponse)
def get_attempt_by_id(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> QuizAttemptResponse:
    """
    Get a specific quiz attempt.
    """
    attempt = crud_quiz.get_attempt(db, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    # Check ownership
    if attempt.user_id != current_user.id and current_user.user_type != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this attempt"
        )
    
    return attempt

@router.post("/attempts/{attempt_id}/answers/", response_model=QuizAttemptResponse)
def submit_answer(
    attempt_id: int,
    answer: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> QuizAttemptResponse:
    """
    Submit an answer for a quiz question.
    """
    attempt = crud_quiz.get_attempt(db, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    # Check ownership
    if attempt.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to submit answers for this attempt"
        )
    
    # Check if already submitted
    if attempt.is_submitted:
        raise HTTPException(
            status_code=400,
            detail="Cannot submit answers to a completed attempt"
        )
    
    return crud_quiz.submit_answer(db, attempt_id, answer.question_id, answer.answer)

@router.post("/attempts/{attempt_id}/submit/", response_model=QuizAttemptResponse)
def finalize_quiz_attempt(
    attempt_id: int,
    answers: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> QuizAttemptResponse:
    """
    Finalize and submit a quiz attempt.
    """
    attempt = crud_quiz.get_attempt(db, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    # Check ownership
    if attempt.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to submit this attempt"
        )
    
    # If answers are provided, submit them all at once
    if answers:
        attempt = crud_quiz.submit_attempt(db, attempt_id, answers)
    else:
        # Otherwise finalize with existing answers
        attempt = crud_quiz.finalize_attempt(db, attempt_id)
    
    if not attempt:
        raise HTTPException(
            status_code=400,
            detail="Cannot submit attempt (no answers or already submitted)"
        )
    
    return attempt

@router.get("/users/{user_id}/attempts/", response_model=List[QuizAttemptResponse])
def get_user_attempts_history(
    user_id: str,
    quiz_id: Optional[int] = Query(None, description="Filter by quiz"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[QuizAttemptResponse]:
    """
    Get quiz attempts for a user.
    """
    # Check authorization (users can only see their own attempts unless admin)
    if user_id != current_user.id and current_user.user_type != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view other users' attempts"
        )
    
    return crud_quiz.get_user_attempts(db, user_id, quiz_id, skip, limit)

@router.get("/{quiz_id}/leaderboard/")
def get_quiz_leaderboard(
    quiz_id: int,
    limit: int = Query(10, ge=1, le=100, description="Number of top scores"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get leaderboard for a quiz.
    """
    quiz = crud_quiz.get_quiz(db, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return crud_quiz.get_leaderboard(db, quiz_id, limit)

@router.get("/{quiz_id}/statistics/")
def get_quiz_statistics_endpoint(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher_or_admin)
) -> Dict[str, Any]:
    """
    Get statistics for a quiz (teachers/admins only).
    """
    quiz = crud_quiz.get_quiz(db, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Check authorization (creator or admin)
    if current_user.id != quiz.created_by and current_user.user_type != "admin":
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view quiz statistics"
        )
    
    return crud_quiz.get_quiz_statistics(db, quiz_id)

@router.get("/practice/questions/")
def get_practice_questions(
    curriculum: str = Query(..., description="Curriculum to practice"),
    difficulty: Optional[str] = Query("medium", description="Difficulty level"),
    limit: int = Query(10, ge=1, le=50, description="Number of questions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get practice questions from various quizzes.
    """
    quizzes = crud_quiz.get_quizzes(db, curriculum=curriculum, is_active=True)
    
    all_questions = []
    for quiz in quizzes:
        if quiz.questions:
            # Parse questions from JSON string if needed
            questions = quiz.questions
            if isinstance(questions, str):
                import json
                questions = json.loads(questions)
            
            for question in questions:
                question["quiz_title"] = quiz.title
                question["quiz_id"] = quiz.id
                all_questions.append(question)
    
    # Simple difficulty filtering (you can implement more sophisticated logic)
    filtered_questions = all_questions
    if difficulty == "easy":
        filtered_questions = [q for q in all_questions if not q.get("difficulty") or q.get("difficulty") == "easy"]
    elif difficulty == "hard":
        filtered_questions = [q for q in all_questions if q.get("difficulty") == "hard"]
    
    return {"questions": filtered_questions[:limit]}