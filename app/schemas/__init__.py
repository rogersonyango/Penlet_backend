# app/schemas/__init__.py
"""
Export all schemas for easy importing.
"""
from app.schemas.user import (
    UserBase, UserCreate, UserLogin, UserUpdate, UserResponse, TokenResponse
)
from app.schemas.subject import (
    SubjectBase, SubjectCreate, SubjectUpdate, SubjectResponse,
    SubjectListResponse, SubjectStatsResponse
)
from app.schemas.alarm import (
    AlarmBase, AlarmCreate, AlarmUpdate, AlarmResponse
)
from app.schemas.reminder import (
    ReminderBase, ReminderCreate, ReminderUpdate, ReminderResponse
)
from app.schemas.timetable import (
    TimeSlotBase, TimeSlotCreate, TimeSlotUpdate, TimeSlotResponse,
    TimetableBase, TimetableCreate, TimetableResponse
)
from app.schemas.flashcard import (
    FlashcardBase, FlashcardCreate, FlashcardUpdate, FlashcardResponse,
    DeckBase, DeckCreate, DeckUpdate, DeckResponse,
    ReviewUpdate, StudySessionResponse, StudyStatsResponse
)
from app.schemas.note import (
    NoteBase, NoteCreate, NoteUpdate, NoteResponse,
    CommentBase, CommentCreate, CommentUpdate, CommentResponse,
    LikeToggleResponse, FavoriteToggleResponse
)
from app.schemas.quiz import (
    QuestionSchema, QuizBase, QuizCreate, QuizUpdate, QuizResponse,
    QuizAttemptStart, AnswerSubmit, AttemptSubmit, QuizAttemptResponse
)
from app.schemas.resource import (
    ResourceCategoryBase, ResourceCategoryCreate, ResourceCategoryResponse,
    ResourceBase, ResourceCreate, ResourceUpdate, ResourceResponse,
    ResourceListResponse
)
from app.schemas.video import (
    VideoBase, VideoCreate, VideoUpdate, VideoResponse, VideoListResponse,
    ProgressUpdate, ProgressResponse,
    VideoCommentCreate, VideoCommentResponse, VideoLikeResponse
)

__all__ = [
    # User schemas
    "UserBase", "UserCreate", "UserLogin", "UserUpdate", "UserResponse", "TokenResponse",
    # Subject schemas
    "SubjectBase", "SubjectCreate", "SubjectUpdate", "SubjectResponse",
    "SubjectListResponse", "SubjectStatsResponse",
    # Alarm schemas
    "AlarmBase", "AlarmCreate", "AlarmUpdate", "AlarmResponse",
    # Reminder schemas
    "ReminderBase", "ReminderCreate", "ReminderUpdate", "ReminderResponse",
    # Timetable schemas
    "TimeSlotBase", "TimeSlotCreate", "TimeSlotUpdate", "TimeSlotResponse",
    "TimetableBase", "TimetableCreate", "TimetableResponse",
    # Flashcard schemas
    "FlashcardBase", "FlashcardCreate", "FlashcardUpdate", "FlashcardResponse",
    "DeckBase", "DeckCreate", "DeckUpdate", "DeckResponse",
    "ReviewUpdate", "StudySessionResponse", "StudyStatsResponse",
    # Note schemas
    "NoteBase", "NoteCreate", "NoteUpdate", "NoteResponse",
    "CommentBase", "CommentCreate", "CommentUpdate", "CommentResponse",
    "LikeToggleResponse", "FavoriteToggleResponse",
    # Quiz schemas
    "QuestionSchema", "QuizBase", "QuizCreate", "QuizUpdate", "QuizResponse",
    "QuizAttemptStart", "AnswerSubmit", "AttemptSubmit", "QuizAttemptResponse",
    # Resource schemas
    "ResourceCategoryBase", "ResourceCategoryCreate", "ResourceCategoryResponse",
    "ResourceBase", "ResourceCreate", "ResourceUpdate", "ResourceResponse",
    "ResourceListResponse",
    # Video schemas
    "VideoBase", "VideoCreate", "VideoUpdate", "VideoResponse", "VideoListResponse",
    "ProgressUpdate", "ProgressResponse",
    "VideoCommentCreate", "VideoCommentResponse", "VideoLikeResponse",
]