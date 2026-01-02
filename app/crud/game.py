from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_
from app.models.game import Game, GameScore, GameAchievement, GameCategory, GameDifficulty
from app.schemas.game import GameCreate, GameUpdate, GameScoreCreate
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Game CRUD
def create_game(db: Session, game: GameCreate) -> Game:
    """Create a new game."""
    db_game = Game(**game.dict())
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


def get_game(db: Session, game_id: str) -> Optional[Game]:
    """Get a specific game by ID."""
    return db.query(Game).filter(Game.id == game_id).first()


def get_games(
    db: Session,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    is_active: bool = True,
    is_featured: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[Game], int]:
    """Get all games with filters."""
    query = db.query(Game)
    
    if is_active is not None:
        query = query.filter(Game.is_active == is_active)
    
    if is_featured is not None:
        query = query.filter(Game.is_featured == is_featured)
    
    if category:
        query = query.filter(Game.category == category)
    
    if difficulty:
        query = query.filter(Game.difficulty == difficulty)
    
    total = query.count()
    
    games = query.order_by(
        desc(Game.is_featured),
        desc(Game.play_count)
    ).offset((page - 1) * page_size).limit(page_size).all()
    
    return games, total


def update_game(db: Session, game_id: str, update: GameUpdate) -> Optional[Game]:
    """Update a game."""
    game = db.query(Game).filter(Game.id == game_id).first()
    
    if not game:
        return None
    
    for field, value in update.dict(exclude_unset=True).items():
        setattr(game, field, value)
    
    db.commit()
    db.refresh(game)
    return game


def delete_game(db: Session, game_id: str) -> bool:
    """Delete a game."""
    game = db.query(Game).filter(Game.id == game_id).first()
    
    if not game:
        return False
    
    # Delete related scores and achievements
    db.query(GameScore).filter(GameScore.game_id == game_id).delete()
    db.query(GameAchievement).filter(GameAchievement.game_id == game_id).delete()
    
    db.delete(game)
    db.commit()
    return True


# Game Score CRUD
def create_score(db: Session, user_id: str, score_data: GameScoreCreate) -> GameScore:
    """
    Create a new game score and update game statistics.
    """
    # Calculate percentage
    percentage = (score_data.score / score_data.max_score) * 100
    
    # Check if perfect score
    is_perfect = score_data.score == score_data.max_score
    
    # Check if high score for this user/game
    existing_high_score = db.query(func.max(GameScore.score)).filter(
        GameScore.user_id == user_id,
        GameScore.game_id == score_data.game_id
    ).scalar() or 0
    
    is_high_score = score_data.score > existing_high_score
    
    # Create score
    db_score = GameScore(
        user_id=user_id,
        game_id=score_data.game_id,
        score=score_data.score,
        max_score=score_data.max_score,
        percentage=percentage,
        time_taken=score_data.time_taken,
        session_data=score_data.session_data,
        is_perfect_score=is_perfect,
        is_high_score=is_high_score
    )
    
    db.add(db_score)
    
    # Update game statistics
    game = db.query(Game).filter(Game.id == score_data.game_id).first()
    if game:
        game.play_count += 1
        
        # Recalculate average score
        avg_score = db.query(func.avg(GameScore.percentage)).filter(
            GameScore.game_id == score_data.game_id
        ).scalar() or 0.0
        game.average_score = float(avg_score)
        
        # Recalculate completion rate (scores >= 50%)
        total_plays = game.play_count
        completed_plays = db.query(func.count(GameScore.id)).filter(
            GameScore.game_id == score_data.game_id,
            GameScore.percentage >= 50
        ).scalar() or 0
        game.completion_rate = (completed_plays / total_plays * 100) if total_plays > 0 else 0.0
    
    # Mark old high scores as not high score
    if is_high_score:
        db.query(GameScore).filter(
            GameScore.user_id == user_id,
            GameScore.game_id == score_data.game_id,
            GameScore.id != db_score.id
        ).update({"is_high_score": False})
    
    # Check for achievements
    db_score.earned_achievement = check_and_award_achievements(db, user_id, db_score)
    
    db.commit()
    db.refresh(db_score)
    
    return db_score


def get_user_scores(
    db: Session,
    user_id: str,
    game_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[GameScore], int]:
    """Get all scores for a user."""
    query = db.query(GameScore).filter(GameScore.user_id == user_id)
    
    if game_id:
        query = query.filter(GameScore.game_id == game_id)
    
    total = query.count()
    
    scores = query.order_by(desc(GameScore.played_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    return scores, total


def get_leaderboard(
    db: Session,
    game_id: str,
    limit: int = 10,
    user_id: Optional[str] = None
) -> tuple[List[GameScore], Optional[int]]:
    """
    Get top scores for a game (leaderboard).
    Returns (top_scores, user_rank).
    """
    # Get top scores (best score per user)
    subquery = db.query(
        GameScore.user_id,
        func.max(GameScore.score).label('best_score')
    ).filter(
        GameScore.game_id == game_id
    ).group_by(GameScore.user_id).subquery()
    
    top_scores = db.query(GameScore).join(
        subquery,
        and_(
            GameScore.user_id == subquery.c.user_id,
            GameScore.score == subquery.c.best_score,
            GameScore.game_id == game_id
        )
    ).order_by(
        desc(GameScore.score),
        GameScore.time_taken  # Tiebreaker: faster time wins
    ).limit(limit).all()
    
    # Get user's rank if provided
    user_rank = None
    if user_id:
        user_best = db.query(func.max(GameScore.score)).filter(
            GameScore.user_id == user_id,
            GameScore.game_id == game_id
        ).scalar()
        
        if user_best:
            # Count how many users have better scores
            better_count = db.query(func.count(func.distinct(GameScore.user_id))).filter(
                GameScore.game_id == game_id,
                GameScore.score > user_best
            ).scalar() or 0
            
            user_rank = better_count + 1
    
    return top_scores, user_rank


# Achievements
def check_and_award_achievements(db: Session, user_id: str, score: GameScore) -> bool:
    """
    Check if score qualifies for any achievements and award them.
    Returns True if any achievement was unlocked.
    """
    achievements_unlocked = False
    
    # Perfect Score Achievement
    if score.is_perfect_score:
        perfect_achievement = db.query(GameAchievement).filter(
            GameAchievement.user_id == user_id,
            GameAchievement.achievement_type == "perfect_score",
            GameAchievement.game_id == score.game_id,
            GameAchievement.is_unlocked == False
        ).first()
        
        if perfect_achievement:
            perfect_achievement.current_progress += 1
            if perfect_achievement.current_progress >= perfect_achievement.target_progress:
                perfect_achievement.is_unlocked = True
                perfect_achievement.unlocked_at = datetime.utcnow()
                achievements_unlocked = True
    
    # Speed Achievement (if time_taken is very low)
    if score.time_taken and score.time_taken < 30 and score.percentage >= 80:
        speed_achievement = db.query(GameAchievement).filter(
            GameAchievement.user_id == user_id,
            GameAchievement.achievement_type == "speed",
            GameAchievement.is_unlocked == False
        ).first()
        
        if speed_achievement:
            speed_achievement.current_progress += 1
            if speed_achievement.current_progress >= speed_achievement.target_progress:
                speed_achievement.is_unlocked = True
                speed_achievement.unlocked_at = datetime.utcnow()
                achievements_unlocked = True
    
    return achievements_unlocked


def get_user_achievements(db: Session, user_id: str) -> List[GameAchievement]:
    """Get all achievements for a user."""
    return db.query(GameAchievement).filter(
        GameAchievement.user_id == user_id
    ).order_by(
        desc(GameAchievement.is_unlocked),
        desc(GameAchievement.unlocked_at)
    ).all()


def create_default_achievements(db: Session, user_id: str):
    """Create default achievements for a new user."""
    default_achievements = [
        {
            "title": "Perfect Starter",
            "description": "Get a perfect score on your first game",
            "achievement_type": "perfect_score",
            "target_progress": 1,
            "icon": "Trophy",
            "badge_color": "gold"
        },
        {
            "title": "Speed Demon",
            "description": "Complete 5 games in under 30 seconds with 80%+ score",
            "achievement_type": "speed",
            "target_progress": 5,
            "icon": "Zap",
            "badge_color": "yellow"
        },
        {
            "title": "Math Master",
            "description": "Play 10 math games",
            "achievement_type": "category_master",
            "category": "math",
            "target_progress": 10,
            "icon": "Calculator",
            "badge_color": "blue"
        }
    ]
    
    for ach_data in default_achievements:
        achievement = GameAchievement(
            user_id=user_id,
            **ach_data
        )
        db.add(achievement)
    
    db.commit()


def get_game_statistics(db: Session, user_id: str) -> Dict[str, Any]:
    """Get comprehensive game statistics for a user."""
    total_games = db.query(func.count(Game.id)).filter(Game.is_active == True).scalar() or 0
    
    games_played = db.query(func.count(func.distinct(GameScore.game_id))).filter(
        GameScore.user_id == user_id
    ).scalar() or 0
    
    total_score = db.query(func.sum(GameScore.score)).filter(
        GameScore.user_id == user_id
    ).scalar() or 0
    
    avg_score = db.query(func.avg(GameScore.percentage)).filter(
        GameScore.user_id == user_id
    ).scalar() or 0.0
    
    perfect_scores = db.query(func.count(GameScore.id)).filter(
        GameScore.user_id == user_id,
        GameScore.is_perfect_score == True
    ).scalar() or 0
    
    total_time = db.query(func.sum(GameScore.time_taken)).filter(
        GameScore.user_id == user_id
    ).scalar() or 0
    
    achievements_unlocked = db.query(func.count(GameAchievement.id)).filter(
        GameAchievement.user_id == user_id,
        GameAchievement.is_unlocked == True
    ).scalar() or 0
    
    # Get scores by category
    by_category_query = db.query(
        Game.category,
        func.count(GameScore.id)
    ).join(GameScore, Game.id == GameScore.game_id).filter(
        GameScore.user_id == user_id
    ).group_by(Game.category).all()
    
    by_category = dict(by_category_query)
    
    # Get favorite category
    favorite_category = max(by_category.items(), key=lambda x: x[1])[0] if by_category else None
    
    # Get recent scores
    recent_scores = db.query(GameScore).filter(
        GameScore.user_id == user_id
    ).order_by(desc(GameScore.played_at)).limit(5).all()
    
    return {
        "total_games": total_games,
        "games_played": games_played,
        "total_score": int(total_score),
        "average_score": float(avg_score),
        "perfect_scores": perfect_scores,
        "total_time_played": int(total_time),
        "achievements_unlocked": achievements_unlocked,
        "favorite_category": favorite_category,
        "by_category": by_category,
        "recent_scores": recent_scores
    }