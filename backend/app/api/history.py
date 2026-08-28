import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from backend.app.database.connection import get_db
from backend.app.database import models
from backend.app.schemas.analysis import AnalysisHistoryItem

logger = logging.getLogger("app.api.history")
router = APIRouter()

@router.get("/analyses", response_model=List[AnalysisHistoryItem])
def get_analysis_history(db: Session = Depends(get_db)):
    """Retrieve lists of previous analyses from the database for historical logs."""
    logger.info("Fetching analysis history logs...")
    
    # Query analyses in reverse chronological order
    analyses = db.query(models.Analysis).order_by(models.Analysis.created_at.desc()).all()
    
    history_items = []
    from backend.app.services.jd_analyzer import JDAnalyzer
    for item in analyses:
        resume_name = item.resume.filename
        jd_title = item.job_description.title
        jd_company = item.job_description.company
        
        if not jd_title or jd_title.lower() in ["job description", "none", ""]:
            fb_title, fb_comp = JDAnalyzer.extract_fallback_title_company(item.job_description.full_text)
            jd_title = fb_title
            if not jd_company or jd_company.lower() in ["company", "none", ""]:
                jd_company = fb_comp
        
        # Try retrieving extracted structured candidate name
        if item.resume.structured_data:
            candidate_name = item.resume.structured_data.get("name")
            if candidate_name:
                resume_name = f"{candidate_name} ({item.resume.filename})"
        elif item.resume.candidate_name:
            resume_name = f"{item.resume.candidate_name} ({item.resume.filename})"
                
        history_items.append(
            AnalysisHistoryItem(
                id=item.id,
                resume_filename=resume_name,
                jd_title=jd_title or "Target Position",
                jd_company=jd_company or "Confidential",
                overall_score=item.overall_score,
                created_at=item.created_at
            )
        )
        
    return history_items
