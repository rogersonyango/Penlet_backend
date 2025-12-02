from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.schemas.report import (
    ReportResponse,
    ReportListResponse,
    ReportUpdate,
    GenerateReportRequest
)
from app.crud import report as report_crud

router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/", response_model=ReportResponse, status_code=201)
def generate_report(
    request: GenerateReportRequest,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Generate a new report with analytics data.
    
    Report types:
    - weekly: Last 7 days
    - monthly: Last 30 days
    - semester: Last 6 months
    - subject: Specific subject
    - custom: Custom date range
    """
    try:
        report = report_crud.create_report(db, user_id, request)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/", response_model=ReportListResponse)
def get_reports(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    is_favorite: Optional[bool] = Query(None, description="Filter by favorite status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get all reports for a user with optional filters.
    """
    reports, total = report_crud.get_user_reports(
        db=db,
        user_id=user_id,
        report_type=report_type,
        is_favorite=is_favorite,
        page=page,
        page_size=page_size
    )
    
    return {
        "reports": reports,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/statistics")
def get_statistics(
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Get overall statistics about user's reports.
    """
    return report_crud.get_report_statistics(db, user_id)


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Get a specific report by ID. Increments view count.
    """
    report = report_crud.get_report(db, report_id, user_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report


@router.put("/{report_id}", response_model=ReportResponse)
def update_report(
    report_id: str,
    update: ReportUpdate,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Update report details (title, description, favorite status).
    """
    report = report_crud.update_report(db, report_id, user_id, update)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report


@router.delete("/{report_id}")
def delete_report(
    report_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Delete a report.
    """
    success = report_crud.delete_report(db, report_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return {"message": "Report deleted successfully"}


@router.post("/{report_id}/favorite", response_model=ReportResponse)
def toggle_favorite(
    report_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Toggle favorite status of a report.
    """
    report = report_crud.toggle_favorite(db, report_id, user_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return report


@router.get("/{report_id}/download")
def download_report(
    report_id: str,
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    db: Session = Depends(get_db)
):
    """
    Download report as PDF (placeholder - PDF generation to be implemented).
    """
    report = report_crud.get_report(db, report_id, user_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not report.pdf_generated:
        raise HTTPException(
            status_code=404,
            detail="PDF not generated for this report. Enable PDF generation when creating reports."
        )
    
    # TODO: Return actual PDF file
    # For now, return the PDF URL
    return {
        "pdf_url": report.pdf_url,
        "file_size": report.file_size,
        "title": report.title
    }