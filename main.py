from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth, subjects, videos  # videos must be here
from app.models import user, subject, video  # video model must be here
from app.api.v1.endpoints import auth, note
from app.models import user
from app.db.session import Base, engine
from app.api.v1.endpoints import timetable, alarms,reminder, quizzes, resource,chatbot

# Creates database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Penlet API", version="1.0.0")

# Allows frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(subjects.router, prefix="/api/v1")
app.include_router(videos.router, prefix="/api/v1")  # This line must be here
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["chatbot"])
app.include_router(note.router, prefix="/api/notes", tags=["notes"])
app.include_router(resource.router, prefix="/api/resource", tags=["resource"])
app.include_router(alarms.router, prefix="/api/alarms", tags=["alarms"])
app.include_router(quizzes.router, prefix="/api/quizzes", tags=["quizzes"])
app.include_router(reminder.router, prefix="/api/reminders", tags=["reminders"])
app.include_router(timetable.router, prefix="/api/timetable", tags=["timetable"])




@app.get("/")
def root():
    return {"message": "Welcome to Penlet API!", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}