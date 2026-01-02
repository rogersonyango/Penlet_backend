# app/models/__init__.py
"""
Import all models to ensure they are registered with SQLAlchemy Base
"""
from app.db.session import Base
from app.models.user import User
from app.models.subject import Subject
from app.models.alarm import Alarm
from app.models.reminder import Reminder
from app.models.timetable import Timetable, TimeSlot
from app.models.flashcard import Deck, Flashcard
from app.models.note import Note, NoteLike, Favorite, Comment
from app.models.quiz import Quiz, QuizAttempt
from app.models.resource import ResourceCategory, Resource
from app.models.video import Video, VideoProgress, VideoLike, VideoComment

__all__ = [
    "Base",
    "User",
    "Subject",
    "Alarm",
    "Reminder",
    "Timetable",
    "TimeSlot",
    "Deck",
    "Flashcard",
    "Note",
    "NoteLike",
    "Favorite",
    "Comment",
    "Quiz",
    "QuizAttempt",
    "ResourceCategory",
    "Resource",
    "Video",
    "VideoProgress",
    "VideoLike",
    "VideoComment",
]