from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth, notes  # Add notes here
from app.models import user, note  # Add note here
from app.db.session import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Penlet API", version="1.0.0")

# Allow your frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth.router, prefix="/api/v1")
app.include_router(notes.router, prefix="/api/v1")  # Add this line

@app.get("/")
def root():
    return {"message": "Welcome to Penlet API!", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}