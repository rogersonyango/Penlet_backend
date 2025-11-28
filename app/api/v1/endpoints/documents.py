from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.schemas.scanned_document import (
    ScannedDocumentCreate,
    ScannedDocumentUpdate,
    ScannedDocumentResponse,
    ScannedDocumentListResponse,
    OCRRequest,
    OCRResponse,
    EnhancementRequest,
    PDFConversionRequest,
    PDFConversionResponse,
    ScanSessionCreate,
    ScanSessionResponse,
    ScanStatistics
)
from app.crud import scanned_document as scan_crud

router = APIRouter(prefix="/scanner", tags=["scanner"])

# Document Endpoints
@router.post("/documents", response_model=ScannedDocumentResponse, status_code=201)
def create_document(
    document: ScannedDocumentCreate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Create a new scanned document record.
    
    Document types: note, assignment, textbook, worksheet, certificate, id_card, receipt, other
    Scan quality: low, medium, high, ultra
    
    Note: This endpoint creates the database record. 
    Actual file upload should be handled separately via multipart/form-data.
    """
    try:
        return scan_crud.create_document(db, user_id, document)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.get("/documents", response_model=ScannedDocumentListResponse)
def get_documents(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    folder: Optional[str] = Query(None, description="Filter by folder"),
    is_favorite: Optional[bool] = Query(None, description="Filter favorites"),
    has_ocr: Optional[bool] = Query(None, description="Filter documents with OCR"),
    search: Optional[str] = Query(None, description="Search in title, description, tags, OCR text"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all scanned documents with filters.
    Results are ordered by creation date (newest first).
    """
    documents, total = scan_crud.get_user_documents(
        db=db,
        user_id=user_id,
        document_type=document_type,
        folder=folder,
        is_favorite=is_favorite,
        has_ocr=has_ocr,
        search=search,
        page=page,
        page_size=page_size
    )
    
    return {
        "documents": documents,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/documents/{document_id}", response_model=ScannedDocumentResponse)
def get_document(
    document_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Get a specific document by ID.
    Automatically increments view count.
    """
    document = scan_crud.get_document(db, document_id, user_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.put("/documents/{document_id}", response_model=ScannedDocumentResponse)
def update_document(
    document_id: str,
    update: ScannedDocumentUpdate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """Update a document's metadata."""
    document = scan_crud.update_document(db, document_id, user_id, update)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """Delete a document permanently."""
    success = scan_crud.delete_document(db, document_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}


@router.post("/documents/{document_id}/favorite", response_model=ScannedDocumentResponse)
def toggle_favorite(
    document_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """Toggle favorite status of a document."""
    document = scan_crud.toggle_favorite(db, document_id, user_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document


@router.post("/documents/{document_id}/download")
def track_download(
    document_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Track document download.
    Increments download count.
    """
    success = scan_crud.increment_download_count(db, document_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Download tracked"}


# OCR Endpoints
@router.post("/ocr", response_model=OCRResponse)
def perform_ocr(
    request: OCRRequest,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Perform OCR (text extraction) on a document.
    
    Supported languages: en (English), fr (French), es (Spanish), etc.
    Processing may take a few seconds depending on image size.
    
    NOTE: This is a placeholder implementation. 
    Production version should integrate Tesseract OCR or cloud OCR API.
    """
    try:
        result = scan_crud.perform_ocr(
            db=db,
            document_id=request.document_id,
            user_id=user_id,
            language=request.language,
            enhance_before_ocr=request.enhance_before_ocr
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")


# Enhancement Endpoints
@router.post("/enhance/{document_id}", response_model=ScannedDocumentResponse)
def enhance_document(
    document_id: str,
    request: EnhancementRequest,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Apply image enhancement to a document.
    
    Available enhancements:
    - Auto crop: Automatically crop borders
    - Perspective correction: Fix skewed images
    - Brightness adjustment: 0.5 to 2.0
    - Contrast adjustment: 0.5 to 2.0
    - Grayscale: Convert to black & white
    - Sharpen: Improve text clarity
    
    NOTE: This is a placeholder implementation.
    Production version should use PIL/OpenCV for image processing.
    """
    try:
        enhancement_config = request.dict(exclude={'document_id'})
        document = scan_crud.apply_enhancement(db, document_id, user_id, enhancement_config)
        return document
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")


# PDF Conversion
@router.post("/convert-to-pdf", response_model=PDFConversionResponse)
def convert_to_pdf(
    request: PDFConversionRequest,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Convert one or more scanned documents to a single PDF.
    
    Supports merging multiple images into one PDF with customizable settings.
    Page sizes: A4, Letter, Legal, etc.
    Quality: 50-100 (JPEG quality for embedded images)
    
    NOTE: This is a placeholder implementation.
    Production version should use img2pdf or reportlab.
    """
    try:
        result = scan_crud.convert_to_pdf(
            db=db,
            user_id=user_id,
            document_ids=request.document_ids,
            output_filename=request.output_filename,
            page_size=request.page_size,
            quality=request.quality
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF conversion failed: {str(e)}")


# Scan Session Endpoints
@router.post("/sessions", response_model=ScanSessionResponse, status_code=201)
def create_session(
    session: ScanSessionCreate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Create a new scan session.
    Use sessions to group multiple scans together (e.g., multi-page document).
    """
    return scan_crud.create_scan_session(db, user_id, session.session_name)


@router.post("/sessions/{session_id}/add/{document_id}", response_model=ScanSessionResponse)
def add_to_session(
    session_id: str,
    document_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """Add a document to an active scan session."""
    try:
        return scan_crud.add_to_session(db, session_id, user_id, document_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/sessions/{session_id}/complete", response_model=ScanSessionResponse)
def complete_session(
    session_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """Mark a scan session as completed."""
    try:
        return scan_crud.complete_session(db, session_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Statistics & Organization
@router.get("/statistics", response_model=ScanStatistics)
def get_statistics(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive scan statistics.
    Includes document counts, storage usage, and type breakdown.
    """
    return scan_crud.get_scan_statistics(db, user_id)


@router.get("/folders")
def get_folders(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """Get all folders with document counts."""
    folders = scan_crud.get_folders(db, user_id)
    return {"folders": folders}