from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.session import Base
import uuid
import enum

class GameCategory(str, enum.Enum):
    """Game categories"""
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

class GameDifficulty(str, enum.Enum):
    """Game difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

class Game(Base):
    __tablename__ = "games"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Game information
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(SQLEnum(GameCategory), nullable=False, default=GameCategory.GENERAL)
    difficulty = Column(SQLEnum(GameDifficulty), nullable=False, default=GameDifficulty.MEDIUM)
    
    # Game details
    instructions = Column(Text)
    game_type = Column(String(50))  # 'quiz', 'flashcard', 'memory', 'puzzle', etc.
    subject_id = Column(String)  # Link to subject (optional)
    subject_name = Column(String(100))
    
    # Game configuration (JSON field)
    config = Column(JSON, default=dict)
    # Example config: {
    #   "time_limit": 60,
    #   "questions_count": 10,
    #   "levels": 5,
    #   "scoring_type": "points" or "time"
    # }
    
    # Metadata
    thumbnail_url = Column(String(500))
    icon = Column(String(50))  # Lucide icon name
    color = Column(String(20))  # Badge color
    
    # Statistics
    play_count = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    completion_rate = Column(Float, default=0.0)  # 0-100
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Game(id={self.id}, title={self.title}, category={self.category})>"


class GameScore(Base):
    __tablename__ = "game_scores"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    
    # Score details
    score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)  # score/max_score * 100
    time_taken = Column(Integer)  # in seconds
    
    # Game session data
    session_data = Column(JSON, default=dict)
    # Example: {
    #   "correct_answers": 8,
    #   "wrong_answers": 2,
    #   "hints_used": 3,
    #   "level_reached": 5,
    #   "answers": [...]
    # }
    
    # Achievement flags
    is_perfect_score = Column(Boolean, default=False)
    is_high_score = Column(Boolean, default=False)  # User's best score for this game
    earned_achievement = Column(Boolean, default=False)
    
    # Timestamps
    played_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<GameScore(id={self.id}, game={self.game_id}, score={self.score}/{self.max_score})>"


class GameAchievement(Base):
    __tablename__ = "game_achievements"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Achievement details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    achievement_type = Column(String(50), nullable=False)  # 'perfect_score', 'streak', 'speed', 'master'
    
    # Requirements
    game_id = Column(String)  # Specific game (optional)
    category = Column(String(50))  # Category-wide achievement (optional)
    requirement = Column(JSON, default=dict)
    # Example: {
    #   "perfect_scores": 5,
    #   "games_played": 50,
    #   "category": "math",
    #   "difficulty": "hard"
    # }
    
    # Visual
    icon = Column(String(50))
    badge_color = Column(String(20))
    
    # Progress
    current_progress = Column(Integer, default=0)
    target_progress = Column(Integer, nullable=False)
    is_unlocked = Column(Boolean, default=False)
    
    # Timestamps
    unlocked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<GameAchievement(id={self.id}, title={self.title}, unlocked={self.is_unlocked})>"