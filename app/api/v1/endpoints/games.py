from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.schemas.game import (
    GameCreate,
    GameUpdate,
    GameResponse,
    GameListResponse,
    GameScoreCreate,
    GameScoreResponse,
    GameScoreListResponse,
    GameStatistics,
    LeaderboardResponse,
    LeaderboardEntry
)
from app.crud import game as game_crud

router = APIRouter(prefix="/games", tags=["games"])

# Game Endpoints
@router.post("/", response_model=GameResponse, status_code=201)
def create_game(
    game: GameCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new game (admin function).
    
    Categories: math, science, language, geography, history, quiz, memory, puzzle, typing, general
    Difficulty: easy, medium, hard, expert
    """
    try:
        return game_crud.create_game(db, game)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create game: {str(e)}")


@router.get("/", response_model=GameListResponse)
def get_games(
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    is_featured: Optional[bool] = Query(None, description="Filter featured games"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all active games with optional filters.
    Results are ordered by: featured first, then by play count.
    """
    games, total = game_crud.get_games(
        db=db,
        category=category,
        difficulty=difficulty,
        is_featured=is_featured,
        page=page,
        page_size=page_size
    )
    
    return {
        "games": games,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{game_id}", response_model=GameResponse)
def get_game(
    game_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific game by ID."""
    game = game_crud.get_game(db, game_id)
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return game


@router.put("/{game_id}", response_model=GameResponse)
def update_game(
    game_id: str,
    update: GameUpdate,
    db: Session = Depends(get_db)
):
    """Update a game (admin function)."""
    game = game_crud.update_game(db, game_id, update)
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return game


@router.delete("/{game_id}")
def delete_game(
    game_id: str,
    db: Session = Depends(get_db)
):
    """Delete a game (admin function). Also deletes all related scores and achievements."""
    success = game_crud.delete_game(db, game_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return {"message": "Game deleted successfully"}


# Score Endpoints
@router.post("/scores", response_model=GameScoreResponse, status_code=201)
def submit_score(
    score: GameScoreCreate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Submit a game score.
    Automatically calculates percentage, checks for perfect score and high score.
    Updates game statistics and checks for achievements.
    """
    try:
        return game_crud.create_score(db, user_id, score)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit score: {str(e)}")


@router.get("/scores/user", response_model=GameScoreListResponse)
def get_user_scores(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    game_id: Optional[str] = Query(None, description="Filter by game"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all scores for a user, optionally filtered by game."""
    scores, total = game_crud.get_user_scores(
        db=db,
        user_id=user_id,
        game_id=game_id,
        page=page,
        page_size=page_size
    )
    
    return {
        "scores": scores,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{game_id}/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(
    game_id: str,
    limit: int = Query(10, ge=1, le=100, description="Number of top scores to return"),
    user_id: Optional[str] = Query(None, description="User ID to get rank"),
    db: Session = Depends(get_db)
):
    """
    Get leaderboard for a game.
    Shows top scores (one per user) and optionally the user's rank.
    """
    game = game_crud.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    top_scores, user_rank = game_crud.get_leaderboard(db, game_id, limit, user_id)
    
    # Convert to leaderboard entries with ranks
    entries = [
        LeaderboardEntry(
            user_id=score.user_id,
            score=score.score,
            percentage=score.percentage,
            time_taken=score.time_taken,
            rank=idx + 1,
            played_at=score.played_at
        )
        for idx, score in enumerate(top_scores)
    ]
    
    return {
        "game_id": game_id,
        "game_title": game.title,
        "entries": entries,
        "total_players": len(entries),
        "user_rank": user_rank
    }


# Statistics Endpoints
@router.get("/statistics/user", response_model=GameStatistics)
def get_user_statistics(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive game statistics for a user.
    Includes total games, scores, achievements, and breakdowns by category.
    """
    return game_crud.get_game_statistics(db, user_id)


# Achievement Endpoints
@router.get("/achievements/user")
def get_user_achievements(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """Get all achievements for a user."""
    achievements = game_crud.get_user_achievements(db, user_id)
    return {"achievements": achievements}


@router.post("/achievements/initialize")
def initialize_achievements(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Initialize default achievements for a user.
    Call this when a user first accesses the games section.
    """
    game_crud.create_default_achievements(db, user_id)
    return {"message": "Default achievements created"}