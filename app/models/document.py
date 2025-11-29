from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, Float, Enum as SQLEnum
from sqlalchemy.sql import func
from app.db.session import Base
import uuid
import enum

class DocumentType(str, enum.Enum):
    """Document types"""
    NOTE = "note"
    ASSIGNMENT = "assignment"
    TEXTBOOK = "textbook"
    WORKSHEET = "worksheet"
    CERTIFICATE = "certificate"
    ID_CARD = "id_card"
    RECEIPT = "receipt"
    OTHER = "other"

class ScanQuality(str, enum.Enum):
    """Scan quality levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"

class ProcessingStatus(str, enum.Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ScannedDocument(Base):
    __tablename__ = "scanned_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Document information
    title = Column(String(200), nullable=False)
    description = Column(Text)
    document_type = Column(SQLEnum(DocumentType), nullable=False, default=DocumentType.OTHER)
    
    # Subject/Category linking
    subject_id = Column(String)
    subject_name = Column(String(100))
    tags = Column(String(500))  # Comma-separated tags
    
    # File information
    original_image_url = Column(String(500), nullable=False)
    processed_image_url = Column(String(500))  # After enhancement
    pdf_url = Column(String(500))  # Converted PDF
    thumbnail_url = Column(String(500))
    
    # File metadata
    file_size = Column(Integer)  # in bytes
    page_count = Column(Integer, default=1)
    image_width = Column(Integer)
    image_height = Column(Integer)
    scan_quality = Column(SQLEnum(ScanQuality), default=ScanQuality.MEDIUM)
    
    # OCR (Optical Character Recognition)
    has_ocr = Column(Boolean, default=False)
    extracted_text = Column(Text)  # Full extracted text
    ocr_confidence = Column(Float)  # 0-100
    ocr_language = Column(String(10), default='en')
    
    # Processing
    processing_status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    processing_error = Column(Text)
    
    # Enhancement metadata (JSON field)
    enhancement_applied = Column(JSON, default=dict)
    # Example: {
    #   "auto_crop": true,
    #   "perspective_correction": true,
    #   "brightness_adjustment": 1.2,
    #   "contrast_adjustment": 1.1,
    #   "filters": ["grayscale", "sharpen"]
    # }
    
    # Organization
    folder = Column(String(200))  # Folder/category
    is_favorite = Column(Boolean, default=False)
    is_shared = Column(Boolean, default=False)
    
    # Statistics
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    
    # Timestamps
    scanned_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    last_viewed = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ScannedDocument(id={self.id}, title={self.title}, type={self.document_type})>"


class ScanSession(Base):
    __tablename__ = "scan_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    
    # Session information
    session_name = Column(String(200))
    document_ids = Column(JSON, default=list)  # List of document IDs in this session
    total_pages = Column(Integer, default=0)
    
    # Session status
    is_active = Column(Boolean, default=True)
    is_completed = Column(Boolean, default=False)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ScanSession(id={self.id}, name={self.session_name}, pages={self.total_pages})>"