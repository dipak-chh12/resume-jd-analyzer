import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database import models
from backend.app.schemas.analysis import RAGChatRequest, RAGChatResponse
from backend.app.services.rag import RAGService

logger = logging.getLogger("app.api.chat")
router = APIRouter()

@router.post("/chat", response_model=RAGChatResponse)
def chat_with_analysis(
    req: RAGChatRequest,
    db: Session = Depends(get_db)
):
    """Answer questions regarding the candidate's resume and target JD using localized RAG context."""
    logger.info(f"Received chat request for analysis ID {req.analysis_id}")
    
    # 1. Fetch analysis to verify existence and extract relation IDs
    analysis = db.query(models.Analysis).filter(models.Analysis.id == req.analysis_id).first()
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The associated analysis report does not exist."
        )
        
    try:
        # 2. Invoke RAG matching pipeline
        chat_resp = RAGService.chat_with_documents(
            resume_id=analysis.resume_id,
            jd_id=analysis.jd_id,
            message=req.message
        )
        return chat_resp
        
    except Exception as e:
        logger.error(f"Error in RAG chat interaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during chatbot search: {str(e)}"
        )
