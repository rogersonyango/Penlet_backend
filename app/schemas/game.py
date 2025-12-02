from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class GameCategory(str, Enum):
    MATH = "math"
    SCIENCE = "science"
    LANGUAGE = "language"
    GEOGRAPHY = "geography"
    HISTORY = "history"
    QUIZ = "quiz"
    MEMORY = "memory"
    PUZZLE = "puzzle"
    TYPING = "typing"
    GENERAL = "general"

class GameDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

# Game Schemas
class GameBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: str
    category: GameCategory = GameCategory.GENERAL
    difficulty: GameDifficulty = GameDifficulty.MEDIUM
    instructions: Optional[str] = None
    game_type: Optional[str] = Field(None, max_length=50)
    subject_id: Optional[str] = None
    subject_name: Optional[str] = Field(None, max_length=100)
    config: Dict[str, Any] = Field(default_factory=dict)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=20)

class GameCreate(GameBase):
    pass

class GameUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    instructions: Optional[str] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None

class GameResponse(GameBase):
    id: str
    play_count: int
    average_score: float
    completion_rate: float
    is_active: bool
    is_featured: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class GameListResponse(BaseModel):
    games: List[GameResponse]
    total: int
    page: int
    page_size: int

# Game Score Schemas
class GameScoreCreate(BaseModel):
    game_id: str
    score: int = Field(..., ge=0)
    max_score: int = Field(..., ge=1)
    time_taken: Optional[int] = Field(None, ge=0, description="Time in seconds")
    session_data: Dict[str, Any] = Field(default_factory=dict)

class GameScoreResponse(BaseModel):
    id: str
    game_id: str
    user_id: str
    score: int
    max_score: int
    percentage: float
    time_taken: Optional[int] = None
    session_data: Dict[str, Any]
    is_perfect_score: bool
    is_high_score: bool
    earned_achievement: bool
    played_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class GameScoreListResponse(BaseModel):
    scores: List[GameScoreResponse]
    total: int
    page: int
    page_size: int

# Achievement Schemas
class GameAchievementResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    achievement_type: str
    game_id: Optional[str] = None
    category: Optional[str] = None
    requirement: Dict[str, Any]
    icon: Optional[str] = None
    badge_color: Optional[str] = None
    current_progress: int
    target_progress: int
    is_unlocked: bool
    unlocked_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Statistics
class GameStatistics(BaseModel):
    total_games: int
    games_played: int
    total_score: int
    average_score: float
    perfect_scores: int
    total_time_played: int  # seconds
    achievements_unlocked: int
    favorite_category: Optional[str] = None
    by_category: Dict[str, int]
    by_difficulty: Dict[str, int]
    recent_scores: List[GameScoreResponse]

# Leaderboard
class LeaderboardEntry(BaseModel):
    user_id: str
    username: Optional[str] = None
    score: int
    percentage: float
    time_taken: Optional[int] = None
    rank: int
    played_at: datetime

class LeaderboardResponse(BaseModel):
    game_id: str
    game_title: str
    entries: List[LeaderboardEntry]
    total_players: int
    user_rank: Optional[int] = None