from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

# Base schema
class ReportBase(BaseModel):
    title: str = Field(..., max_length=200, description="Report title")
    report_type: str = Field(..., description="Report type: weekly, monthly, semester, subject, custom")
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime

# Create schema
class ReportCreate(ReportBase):
    pass

# Update schema
class ReportUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    is_favorite: Optional[bool] = None

# Response schema
class ReportResponse(ReportBase):
    id: str
    user_id: str
    
    # Statistics
    total_study_hours: float
    videos_watched: int
    quizzes_completed: int
    notes_created: int
    average_quiz_score: float
    completion_rate: float
    
    # Report data
    data: Dict[str, Any]
    
    # File info
    pdf_generated: bool
    pdf_url: Optional[str] = None
    file_size: Optional[int] = None
    
    # Status
    status: str
    is_public: bool
    is_favorite: bool
    
    # Metadata
    generated_at: datetime
    last_viewed: Optional[datetime] = None
    view_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# List response
class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int
    page: int
    page_size: int

# Analytics summary for report generation
class ReportAnalytics(BaseModel):
    subjects: List[Dict[str, Any]] = []
    videos: Dict[str, Any] = {}
    quizzes: Dict[str, Any] = {}
    notes: Dict[str, Any] = {}
    study_time: Dict[str, Any] = {}
    completion_rate: float = 0.0
    average_score: float = 0.0
    total_activities: int = 0
    charts: Dict[str, Any] = {}

# Report generation request
class GenerateReportRequest(BaseModel):
    title: str = Field(..., max_length=200)
    report_type: str = Field(..., description="weekly, monthly, semester, subject, custom")
    start_date: datetime
    end_date: datetime
    description: Optional[str] = None
    subject_id: Optional[str] = None  # For subject-specific reports
    generate_pdf: bool = Field(default=True, description="Generate PDF file")