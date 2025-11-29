from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.db.session import get_db
from app.models.subject import Subject
from app.models.video import Video
from app.models.note import Note

router = APIRouter(tags=["search"])

@router.get("/search/global")
def global_search(
    query: str = Query(..., min_length=1, description="Search query"),
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    limit: int = Query(10, ge=1, le=50, description="Max results per category"),
    db: Session = Depends(get_db)
):
    """
    Global search across all modules.
    
    Returns results from:
    - Subjects
    - Videos
    - Notes
    - Quizzes (when implemented)
    
    Results are categorized by type for easy rendering.
    """
    search_term = f"%{query}%"
    results = {
        "query": query,
        "subjects": [],
        "videos": [],
        "notes": [],
        "quizzes": [],
        "total_results": 0
    }
    
    # Search Subjects
    try:
        subjects = db.query(Subject).filter(
            Subject.user_id == user_id,
            or_(
                Subject.name.ilike(search_term),
                Subject.code.ilike(search_term),
                Subject.description.ilike(search_term),
                Subject.teacher_name.ilike(search_term)
            )
        ).limit(limit).all()
        
        results["subjects"] = [
            {
                "id": s.id,
                "type": "subject",
                "title": s.name,
                "subtitle": s.code,
                "description": s.description,
                "color": s.color,
                "url": f"/subjects"
            }
            for s in subjects
        ]
    except Exception as e:
        print(f"Subject search error: {e}")
    
    # Search Videos
    try:
        videos = db.query(Video).filter(
            Video.user_id == user_id,
            or_(
                Video.title.ilike(search_term),
                Video.description.ilike(search_term),
                Video.topic.ilike(search_term),
                Video.tags.ilike(search_term),
                Video.subject_name.ilike(search_term)
            )
        ).limit(limit).all()
        
        results["videos"] = [
            {
                "id": v.id,
                "type": "video",
                "title": v.title,
                "subtitle": v.subject_name or "No subject",
                "description": v.description,
                "thumbnail": v.thumbnail_url,
                "duration": v.duration,
                "url": f"/videos"
            }
            for v in videos
        ]
    except Exception as e:
        print(f"Video search error: {e}")
    
    # Search Notes
    try:
        notes = db.query(Note).filter(
            Note.author_id == user_id,
            Note.is_deleted == False,
            or_(
                Note.title.ilike(search_term),
                Note.content.ilike(search_term),
                Note.curriculum.ilike(search_term)
            )
        ).limit(limit).all()
        
        results["notes"] = [
            {
                "id": n.id,
                "type": "note",
                "title": n.title,
                "subtitle": n.curriculum or "No curriculum",
                "description": n.content[:100] + "..." if len(n.content) > 100 else n.content,
                "url": f"/notes/{n.id}"
            }
            for n in notes
        ]
    except Exception as e:
        print(f"Note search error: {e}")
    
    # Calculate total results
    results["total_results"] = (
        len(results["subjects"]) +
        len(results["videos"]) +
        len(results["notes"]) +
        len(results["quizzes"])
    )
    
    return results


@router.get("/search/suggestions")
def get_search_suggestions(
    query: str = Query(..., min_length=1, description="Search query"),
    user_id: str = Query(..., description="User ID (temporary - will use JWT)"),
    limit: int = Query(5, ge=1, le=20, description="Max suggestions"),
    db: Session = Depends(get_db)
):
    """
    Get quick search suggestions as user types.
    
    Returns simple list of titles for autocomplete.
    """
    search_term = f"%{query}%"
    suggestions = []
    
    # Get subject names
    try:
        subjects = db.query(Subject.name).filter(
            Subject.user_id == user_id,
            Subject.name.ilike(search_term)
        ).limit(limit).all()
        
        suggestions.extend([s[0] for s in subjects])
    except Exception as e:
        print(f"Subject suggestions error: {e}")
    
    # Get video titles
    try:
        videos = db.query(Video.title).filter(
            Video.user_id == user_id,
            Video.title.ilike(search_term)
        ).limit(limit).all()
        
        suggestions.extend([v[0] for v in videos])
    except Exception as e:
        print(f"Video suggestions error: {e}")
    
    # Get note titles
    try:
        notes = db.query(Note.title).filter(
            Note.author_id == user_id,
            Note.is_deleted == False,
            Note.title.ilike(search_term)
        ).limit(limit).all()
        
        suggestions.extend([n[0] for n in notes])
    except Exception as e:
        print(f"Note suggestions error: {e}")
    
    # Remove duplicates and limit
    suggestions = list(set(suggestions))[:limit]
    
    return {
        "query": query,
        "suggestions": suggestions
    }