from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Import routes
from app.api.v1.endpoints import (
    auth, note, subjects, videos, search, analytics, documents, 
    games, notifications, reports, timetable, alarms, reminder, quizzes,
    content  # Import content endpoint (has router)
)

# Import models (for SQLAlchemy table creation)
from app.models import (
    user, subject, video, analytics as analytics_model, document, game, 
    notification, report
    # Note: Don't import content model here to avoid name conflict
    # The model will still be created because it's imported in models/__init__.py
)
from app.db.session import Base, engine

# Creates database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Penlet API", version="1.0.0")

# Create upload directories
os.makedirs("uploads/notes", exist_ok=True)
os.makedirs("uploads/videos", exist_ok=True)
os.makedirs("uploads/assignments", exist_ok=True)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(subjects.router, prefix="/api/v1")
app.include_router(games.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(videos.router, prefix="/api/v1")
app.include_router(content.router, prefix="/api/v1")  # Content routes
app.include_router(note.router, prefix="/api/notes", tags=["notes"])
app.include_router(alarms.router, prefix="/api/alarms", tags=["alarms"])
app.include_router(quizzes.router, prefix="/api/quizzes", tags=["quizzes"])
app.include_router(reminder.router, prefix="/api/reminders", tags=["reminders"])
app.include_router(timetable.router, prefix="/api/timetable", tags=["timetable"])
app.include_router(search.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Welcome to Penlet API!", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}