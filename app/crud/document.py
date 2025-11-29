from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_
from app.models.scanned_document import ScannedDocument, ScanSession, DocumentType, ProcessingStatus
from app.schemas.scanned_document import ScannedDocumentCreate, ScannedDocumentUpdate
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import time

# Document CRUD
def create_document(db: Session, user_id: str, document: ScannedDocumentCreate) -> ScannedDocument:
    """Create a new scanned document."""
    db_document = ScannedDocument(
        user_id=user_id,
        **document.dict()
    )
    
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return db_document


def get_document(db: Session, document_id: str, user_id: str) -> Optional[ScannedDocument]:
    """Get a specific document by ID and increment view count."""
    document = db.query(ScannedDocument).filter(
        ScannedDocument.id == document_id,
        ScannedDocument.user_id == user_id
    ).first()
    
    if document:
        document.view_count += 1
        document.last_viewed = datetime.utcnow()
        db.commit()
        db.refresh(document)
    
    return document


def get_user_documents(
    db: Session,
    user_id: str,
    document_type: Optional[str] = None,
    folder: Optional[str] = None,
    is_favorite: Optional[bool] = None,
    has_ocr: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[ScannedDocument], int]:
    """Get all documents for a user with filters."""
    query = db.query(ScannedDocument).filter(ScannedDocument.user_id == user_id)
    
    if document_type:
        query = query.filter(ScannedDocument.document_type == document_type)
    
    if folder:
        query = query.filter(ScannedDocument.folder == folder)
    
    if is_favorite is not None:
        query = query.filter(ScannedDocument.is_favorite == is_favorite)
    
    if has_ocr is not None:
        query = query.filter(ScannedDocument.has_ocr == has_ocr)
    
    if search:
        search_filter = or_(
            ScannedDocument.title.ilike(f'%{search}%'),
            ScannedDocument.description.ilike(f'%{search}%'),
            ScannedDocument.tags.ilike(f'%{search}%'),
            ScannedDocument.extracted_text.ilike(f'%{search}%')
        )
        query = query.filter(search_filter)
    
    total = query.count()
    
    documents = query.order_by(desc(ScannedDocument.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    return documents, total


def update_document(
    db: Session,
    document_id: str,
    user_id: str,
    update: ScannedDocumentUpdate
) -> Optional[ScannedDocument]:
    """Update a document."""
    document = db.query(ScannedDocument).filter(
        ScannedDocument.id == document_id,
        ScannedDocument.user_id == user_id
    ).first()
    
    if not document:
        return None
    
    for field, value in update.dict(exclude_unset=True).items():
        setattr(document, field, value)
    
    db.commit()
    db.refresh(document)
    
    return document


def delete_document(db: Session, document_id: str, user_id: str) -> bool:
    """Delete a document."""
    document = db.query(ScannedDocument).filter(
        ScannedDocument.id == document_id,
        ScannedDocument.user_id == user_id
    ).first()
    
    if not document:
        return False
    
    db.delete(document)
    db.commit()
    
    return True


def toggle_favorite(db: Session, document_id: str, user_id: str) -> Optional[ScannedDocument]:
    """Toggle favorite status of a document."""
    document = db.query(ScannedDocument).filter(
        ScannedDocument.id == document_id,
        ScannedDocument.user_id == user_id
    ).first()
    
    if not document:
        return None
    
    document.is_favorite = not document.is_favorite
    db.commit()
    db.refresh(document)
    
    return document


def increment_download_count(db: Session, document_id: str, user_id: str) -> bool:
    """Increment download count for a document."""
    document = db.query(ScannedDocument).filter(
        ScannedDocument.id == document_id,
        ScannedDocument.user_id == user_id
    ).first()
    
    if not document:
        return False
    
    document.download_count += 1
    db.commit()
    
    return True


# OCR Functions
def perform_ocr(
    db: Session,
    document_id: str,
    user_id: str,
    language: str = 'en',
    enhance_before_ocr: bool = True
) -> Dict[str, Any]:
    """
    Perform OCR on a document.
    This is a placeholder - actual implementation would use Tesseract OCR or cloud OCR API.
    """
    document = db.query(ScannedDocument).filter(
        ScannedDocument.id == document_id,
        ScannedDocument.user_id == user_id
    ).first()
    
    if not document:
        raise ValueError("Document not found")
    
    # Update status
    document.processing_status = ProcessingStatus.PROCESSING
    db.commit()
    
    start_time = time.time()
    
    try:
        # PLACEHOLDER: Actual OCR implementation would go here
        # Example using pytesseract:
        # from PIL import Image
        # import pytesseract
        # image = Image.open(document.original_image_url)
        # extracted_text = pytesseract.image_to_string(image, lang=language)
        # confidence = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # For now, simulate OCR
        extracted_text = "Simulated OCR text extraction. This is placeholder text."
        confidence = 85.5
        
        # Update document
        document.has_ocr = True
        document.extracted_text = extracted_text
        document.ocr_confidence = confidence
        document.ocr_language = language
        document.processing_status = ProcessingStatus.COMPLETED
        document.processed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(document)
        
        processing_time = time.time() - start_time
        
        return {
            "document_id": document_id,
            "extracted_text": extracted_text,
            "confidence": confidence,
            "word_count": len(extracted_text.split()),
            "processing_time": processing_time
        }
    
    except Exception as e:
        document.processing_status = ProcessingStatus.FAILED
        document.processing_error = str(e)
        db.commit()
        raise


def apply_enhancement(
    db: Session,
    document_id: str,
    user_id: str,
    enhancement_config: Dict[str, Any]
) -> ScannedDocument:
    """
    Apply image enhancement to a document.
    This is a placeholder - actual implementation would use PIL/OpenCV for image processing.
    """
    document = db.query(ScannedDocument).filter(
        ScannedDocument.id == document_id,
        ScannedDocument.user_id == user_id
    ).first()
    
    if not document:
        raise ValueError("Document not found")
    
    # Update status
    document.processing_status = ProcessingStatus.PROCESSING
    db.commit()
    
    try:
        # PLACEHOLDER: Actual image enhancement would go here
        # Example using PIL:
        # from PIL import Image, ImageEnhance
        # image = Image.open(document.original_image_url)
        # if enhancement_config.get('auto_crop'):
        #     image = auto_crop(image)
        # if enhancement_config.get('apply_grayscale'):
        #     image = image.convert('L')
        # enhancer = ImageEnhance.Brightness(image)
        #     image = enhancer.enhance(enhancement_config['brightness'])
        # processed_path = save_processed_image(image)
        
        # For now, simulate enhancement
        processed_url = document.original_image_url.replace('.jpg', '_processed.jpg')
        
        # Update document
        document.processed_image_url = processed_url
        document.enhancement_applied = enhancement_config
        document.processing_status = ProcessingStatus.COMPLETED
        document.processed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(document)
        
        return document
    
    except Exception as e:
        document.processing_status = ProcessingStatus.FAILED
        document.processing_error = str(e)
        db.commit()
        raise


def convert_to_pdf(
    db: Session,
    user_id: str,
    document_ids: List[str],
    output_filename: str,
    page_size: str = "A4",
    quality: int = 85
) -> Dict[str, Any]:
    """
    Convert multiple documents to a single PDF.
    This is a placeholder - actual implementation would use img2pdf or reportlab.
    """
    documents = db.query(ScannedDocument).filter(
        ScannedDocument.id.in_(document_ids),
        ScannedDocument.user_id == user_id
    ).all()
    
    if not documents:
        raise ValueError("No documents found")
    
    start_time = time.time()
    
    try:
        # PLACEHOLDER: Actual PDF conversion would go here
        # Example using img2pdf:
        # import img2pdf
        # image_paths = [doc.processed_image_url or doc.original_image_url for doc in documents]
        # with open(output_filename, "wb") as f:
        #     f.write(img2pdf.convert(image_paths))
        
        # For now, simulate conversion
        pdf_url = f"/scans/pdfs/{output_filename}"
        file_size = sum(doc.file_size or 0 for doc in documents)
        
        # Update documents with PDF URL
        for doc in documents:
            doc.pdf_url = pdf_url
        
        db.commit()
        
        processing_time = time.time() - start_time
        
        return {
            "pdf_url": pdf_url,
            "file_size": file_size,
            "page_count": len(documents),
            "processing_time": processing_time
        }
    
    except Exception as e:
        raise ValueError(f"PDF conversion failed: {str(e)}")


# Scan Session CRUD
def create_scan_session(db: Session, user_id: str, session_name: str) -> ScanSession:
    """Create a new scan session."""
    session = ScanSession(
        user_id=user_id,
        session_name=session_name
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session


def add_to_session(db: Session, session_id: str, user_id: str, document_id: str) -> ScanSession:
    """Add a document to a scan session."""
    session = db.query(ScanSession).filter(
        ScanSession.id == session_id,
        ScanSession.user_id == user_id
    ).first()
    
    if not session:
        raise ValueError("Session not found")
    
    if document_id not in session.document_ids:
        session.document_ids.append(document_id)
        session.total_pages += 1
    
    db.commit()
    db.refresh(session)
    
    return session


def complete_session(db: Session, session_id: str, user_id: str) -> ScanSession:
    """Mark a scan session as completed."""
    session = db.query(ScanSession).filter(
        ScanSession.id == session_id,
        ScanSession.user_id == user_id
    ).first()
    
    if not session:
        raise ValueError("Session not found")
    
    session.is_active = False
    session.is_completed = True
    session.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    
    return session


# Statistics
def get_scan_statistics(db: Session, user_id: str) -> Dict[str, Any]:
    """Get comprehensive scan statistics for a user."""
    total_documents = db.query(func.count(ScannedDocument.id)).filter(
        ScannedDocument.user_id == user_id
    ).scalar() or 0
    
    total_pages = db.query(func.sum(ScannedDocument.page_count)).filter(
        ScannedDocument.user_id == user_id
    ).scalar() or 0
    
    total_size = db.query(func.sum(ScannedDocument.file_size)).filter(
        ScannedDocument.user_id == user_id
    ).scalar() or 0
    
    documents_with_ocr = db.query(func.count(ScannedDocument.id)).filter(
        ScannedDocument.user_id == user_id,
        ScannedDocument.has_ocr == True
    ).scalar() or 0
    
    favorite_count = db.query(func.count(ScannedDocument.id)).filter(
        ScannedDocument.user_id == user_id,
        ScannedDocument.is_favorite == True
    ).scalar() or 0
    
    # Count by type
    by_type_query = db.query(
        ScannedDocument.document_type,
        func.count(ScannedDocument.id)
    ).filter(
        ScannedDocument.user_id == user_id
    ).group_by(ScannedDocument.document_type).all()
    
    by_type = dict(by_type_query)
    
    # Count by quality
    by_quality_query = db.query(
        ScannedDocument.scan_quality,
        func.count(ScannedDocument.id)
    ).filter(
        ScannedDocument.user_id == user_id
    ).group_by(ScannedDocument.scan_quality).all()
    
    by_quality = dict(by_quality_query)
    
    # Recent scans
    recent_scans = db.query(ScannedDocument).filter(
        ScannedDocument.user_id == user_id
    ).order_by(desc(ScannedDocument.created_at)).limit(5).all()
    
    return {
        "total_documents": total_documents,
        "total_pages": int(total_pages),
        "total_size_mb": round(total_size / (1024 * 1024), 2) if total_size else 0.0,
        "documents_with_ocr": documents_with_ocr,
        "by_type": by_type,
        "by_quality": by_quality,
        "favorite_count": favorite_count,
        "recent_scans": recent_scans,
        "storage_used_mb": round(total_size / (1024 * 1024), 2) if total_size else 0.0
    }


def get_folders(db: Session, user_id: str) -> List[Dict[str, Any]]:
    """Get all folders with document counts."""
    folders = db.query(
        ScannedDocument.folder,
        func.count(ScannedDocument.id)
    ).filter(
        ScannedDocument.user_id == user_id,
        ScannedDocument.folder.isnot(None)
    ).group_by(ScannedDocument.folder).all()
    
    return [
        {"name": folder, "count": count}
        for folder, count in folders
    ]