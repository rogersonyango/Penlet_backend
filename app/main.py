from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth, subjects, videos  # videos must be here
from app.models import user, subject, video  # video model must be here
from app.db.session import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Penlet API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth.router, prefix="/api/v1")
app.include_router(subjects.router, prefix="/api/v1")
app.include_router(videos.router, prefix="/api/v1")  # This line must be here

@app.get("/")
def root():
    return {"message": "Welcome to Penlet API!", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}