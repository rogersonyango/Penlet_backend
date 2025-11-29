from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
from app.db.session import Base
import uuid

class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Report details
    title = Column(String(200), nullable=False)
    report_type = Column(String(50), nullable=False)  # 'weekly', 'monthly', 'semester', 'subject', 'custom'
    description = Column(Text)
    
    # Date range
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Report data (JSON field to store all analytics)
    data = Column(JSON, nullable=False, default=dict)
    # Structure: {
    #   "subjects": [...],
    #   "videos": {...},
    #   "quizzes": {...},
    #   "notes": {...},
    #   "study_time": {...},
    #   "completion_rate": float,
    #   "average_score": float,
    #   "total_activities": int,
    #   "charts": {...}
    # }
    
    # Statistics summary
    total_study_hours = Column(Float, default=0.0)
    videos_watched = Column(Integer, default=0)
    quizzes_completed = Column(Integer, default=0)
    notes_created = Column(Integer, default=0)
    average_quiz_score = Column(Float, default=0.0)
    completion_rate = Column(Float, default=0.0)  # 0-100
    
    # File information (for PDF exports)
    pdf_generated = Column(Boolean, default=False)
    pdf_url = Column(String(500))
    file_size = Column(Integer)  # in bytes
    
    # Status
    status = Column(String(20), default='generated')  # 'generating', 'generated', 'failed'
    is_public = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    
    # Metadata
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    last_viewed = Column(DateTime(timezone=True))
    view_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Report(id={self.id}, title={self.title}, type={self.report_type})>"