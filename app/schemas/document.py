from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class DocumentType(str, Enum):
    NOTE = "note"
    ASSIGNMENT = "assignment"
    TEXTBOOK = "textbook"
    WORKSHEET = "worksheet"
    CERTIFICATE = "certificate"
    ID_CARD = "id_card"
    RECEIPT = "receipt"
    OTHER = "other"

class ScanQuality(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Scanned Document Schemas
class ScannedDocumentBase(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    document_type: DocumentType = DocumentType.OTHER
    subject_id: Optional[str] = None
    subject_name: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = Field(None, max_length=500)
    folder: Optional[str] = Field(None, max_length=200)

class ScannedDocumentCreate(ScannedDocumentBase):
    original_image_url: str = Field(..., max_length=500)
    scan_quality: ScanQuality = ScanQuality.MEDIUM
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    file_size: Optional[int] = None

class ScannedDocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    document_type: Optional[DocumentType] = None
    subject_id: Optional[str] = None
    subject_name: Optional[str] = None
    tags: Optional[str] = None
    folder: Optional[str] = None
    is_favorite: Optional[bool] = None

class ScannedDocumentResponse(ScannedDocumentBase):
    id: str
    user_id: str
    original_image_url: str
    processed_image_url: Optional[str] = None
    pdf_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    file_size: Optional[int] = None
    page_count: int
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    scan_quality: ScanQuality
    has_ocr: bool
    extracted_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    ocr_language: str
    processing_status: ProcessingStatus
    processing_error: Optional[str] = None
    enhancement_applied: Dict[str, Any]
    is_favorite: bool
    is_shared: bool
    view_count: int
    download_count: int
    scanned_at: datetime
    processed_at: Optional[datetime] = None
    last_viewed: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScannedDocumentListResponse(BaseModel):
    documents: List[ScannedDocumentResponse]
    total: int
    page: int
    page_size: int

# OCR Request/Response
class OCRRequest(BaseModel):
    document_id: str
    language: str = Field(default='en', description="OCR language code")
    enhance_before_ocr: bool = Field(default=True, description="Apply enhancement before OCR")

class OCRResponse(BaseModel):
    document_id: str
    extracted_text: str
    confidence: float
    word_count: int
    processing_time: float  # in seconds

# Enhancement Request
class EnhancementRequest(BaseModel):
    document_id: str
    auto_crop: bool = Field(default=True)
    perspective_correction: bool = Field(default=True)
    brightness: float = Field(default=1.0, ge=0.5, le=2.0)
    contrast: float = Field(default=1.0, ge=0.5, le=2.0)
    apply_grayscale: bool = Field(default=False)
    apply_sharpen: bool = Field(default=True)

# PDF Conversion
class PDFConversionRequest(BaseModel):
    document_ids: List[str] = Field(..., description="List of document IDs to merge into PDF")
    output_filename: str = Field(..., max_length=200)
    page_size: str = Field(default="A4", description="PDF page size (A4, Letter, etc.)")
    quality: int = Field(default=85, ge=50, le=100, description="JPEG quality for images in PDF")

class PDFConversionResponse(BaseModel):
    pdf_url: str
    file_size: int
    page_count: int
    processing_time: float

# Scan Session Schemas
class ScanSessionCreate(BaseModel):
    session_name: str = Field(..., max_length=200)

class ScanSessionResponse(BaseModel):
    id: str
    user_id: str
    session_name: str
    document_ids: List[str]
    total_pages: int
    is_active: bool
    is_completed: bool
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Statistics
class ScanStatistics(BaseModel):
    total_documents: int
    total_pages: int
    total_size_mb: float
    documents_with_ocr: int
    by_type: Dict[str, int]
    by_quality: Dict[str, int]
    favorite_count: int
    recent_scans: List[ScannedDocumentResponse]
    storage_used_mb: float