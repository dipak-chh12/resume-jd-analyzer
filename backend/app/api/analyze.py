import logging
import uuid
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from backend.app.database.connection import get_db
from backend.app.database import models
from backend.app.schemas.analysis import AnalysisResponse, ScoreBreakdown, SkillsAnalysis, ATSAnalysis, RequirementEvaluation, JDRequirementItem, ResumeExtract
from backend.app.services.document_parser import DocumentParser
from backend.app.services.resume_analyzer import ResumeAnalyzer
from backend.app.services.jd_analyzer import JDAnalyzer
from backend.app.services.embedding_service import embedding_service
from backend.app.services.vector_store import vector_store
from backend.app.services.rag import RAGService
from backend.app.services.scoring import MatchingEngine
from backend.app.services.ats_analyzer import ATSAnalyzer
from backend.app.services.insights import insights_service

logger = logging.getLogger("app.api.analyze")
router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_documents(
    resume_file: UploadFile = File(...),
    jd_text: Optional[str] = Form(None),
    jd_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Run the complete document analysis pipeline: parse, chunk, embed, index, RAG match, score, and persist."""
    logger.info("Received analysis request...")
    
    # 1. Validate Job Description inputs
    if not jd_text and not jd_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must provide a job description (either paste text or upload a file)."
        )
        
    try:
        # 2. Parse Resume
        resume_bytes = await resume_file.read()
        resume_raw = DocumentParser.parse_file(resume_file.filename, resume_bytes)
        
        # 3. Parse Job Description
        if jd_file:
            jd_bytes = await jd_file.read()
            jd_raw = DocumentParser.parse_file(jd_file.filename, jd_bytes)
        else:
            jd_raw = jd_text
            
        if not jd_raw.strip():
            raise ValueError("The provided job description text is empty.")
            
    except Exception as e:
        logger.error(f"Error parsing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Document parsing failed: {str(e)}"
        )
        
    try:
        # 4. Save parsed inputs to SQL DB to generate relational primary keys
        db_resume = models.Resume(
            filename=resume_file.filename,
            extracted_text=resume_raw
        )
        db.add(db_resume)
        db.flush()  # Populates db_resume.id
        
        db_jd = models.JobDescription(
            full_text=jd_raw
        )
        db.add(db_jd)
        db.flush()  # Populates db_jd.id
        
        # 5. Extract structured profiles using LLM
        resume_extract = ResumeAnalyzer.analyze(resume_raw)
        db_resume.candidate_name = resume_extract.name
        db_resume.summary = resume_extract.summary
        # Convert Pydantic model to dict for JSON column
        db_resume.structured_data = resume_extract.model_dump()
        
        jd_extract = JDAnalyzer.analyze(jd_raw)
        db_jd.title = jd_extract.job_title
        db_jd.company = jd_extract.company
        db_jd.structured_data = jd_extract.model_dump()
        
        # 6. Chunk documents
        resume_chunks, resume_metadata = RAGService.chunk_resume(db_resume.id, resume_extract)
        jd_chunks, jd_metadata = RAGService.chunk_jd(db_jd.id, jd_extract)
        
        # 7. Generate Embeddings
        resume_embeddings = embedding_service.embed_documents(resume_chunks)
        jd_embeddings = embedding_service.embed_documents(jd_chunks)
        
        # 8. Create collection and index in vector store
        # Qdrant client fallback to local/in-memory handles collection automatically
        # We index both resume and JD in Qdrant
        vector_store.recreate_collection("resumes", embedding_service.vector_dim)
        vector_store.index_chunks("resumes", resume_chunks, resume_metadata, resume_embeddings)
        vector_store.index_chunks("resumes", jd_chunks, jd_metadata, jd_embeddings)
        
        # 9. Perform RAG-based Requirement Evaluation
        # Loops through JD requirements, retrieves resume evidence, uses LLM to match
        evaluations = RAGService.evaluate_requirements(db_resume.id, jd_extract.requirements, resume_chunks)
        
        # Categorize evaluations into strong, partial, missing list categories
        strong_matches = [e for e in evaluations if e.status == "strong_match"]
        partial_matches = [e for e in evaluations if e.status in ["partial_match", "weak_match"]]
        missing_skills = [e for e in evaluations if e.status == "missing"]
        
        skills_analysis_dict = {
            "strong_matches": [e.model_dump() for e in strong_matches],
            "partial_matches": [e.model_dump() for e in partial_matches],
            "missing_skills": [e.model_dump() for e in missing_skills]
        }
        
        # 10. Perform ATS Scanning
        ats_res = ATSAnalyzer.analyze(resume_extract, resume_raw)
        
        # 11. Run Scoring Engine
        overall_score, score_breakdown = MatchingEngine.calculate_scores(
            evaluations=evaluations,
            resume=resume_extract,
            jd=jd_extract,
            ats_score=ats_res.score
        )
        
        # 12. Generate actionable improvements & Interview Questions
        from backend.app.services.insights import _normalize_string_list
        recommendations = _normalize_string_list(insights_service.generate_recommendations(resume_extract, evaluations))
        interview_questions = _normalize_string_list(insights_service.generate_interview_questions(resume_extract, jd_extract, evaluations))
        
        # 13. Persist analysis results in DB
        analysis_id = str(uuid.uuid4())
        db_analysis = models.Analysis(
            id=analysis_id,
            resume_id=db_resume.id,
            jd_id=db_jd.id,
            overall_score=overall_score,
            scores_breakdown=score_breakdown.model_dump(),
            skills_analysis=skills_analysis_dict,
            ats_analysis=ats_res.model_dump(),
            recommendations=recommendations,
            interview_questions=interview_questions
        )
        db.add(db_analysis)
        db.commit()
        
        logger.info(f"Analysis successfully completed and saved: ID {analysis_id}")
        
        # Assemble Response
        return AnalysisResponse(
            id=analysis_id,
            resume_id=db_resume.id,
            jd_id=db_jd.id,
            overall_score=overall_score,
            scores_breakdown=score_breakdown,
            skills_analysis=SkillsAnalysis(
                strong_matches=strong_matches,
                partial_matches=partial_matches,
                missing_skills=missing_skills
            ),
            ats_analysis=ats_res,
            recommendations=recommendations,
            interview_questions=interview_questions,
            created_at=db_analysis.created_at,
            resume_name=resume_extract.name or resume_file.filename,
            resume_summary=resume_extract.summary,
            resume_extract=resume_extract,
            jd_title=jd_extract.job_title or "Job Description",
            jd_company=jd_extract.company or "Company",
            jd_requirements=jd_extract.requirements
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in analysis pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during analysis: {str(e)}"
        )

@router.get("/analyze/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Retrieve details of a past analysis from the database."""
    from backend.app.services.insights import _normalize_string_list
    from backend.app.services.jd_analyzer import JDAnalyzer
    db_analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    if not db_analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis report not found."
        )
        
    db_resume = db_analysis.resume
    db_jd = db_analysis.job_description
    
    # Extract deserialized database maps
    breakdown = ScoreBreakdown(**db_analysis.scores_breakdown)
    
    sa = db_analysis.skills_analysis
    skills_analysis = SkillsAnalysis(
        strong_matches=[RequirementEvaluation(**e) for e in sa.get("strong_matches", [])],
        partial_matches=[RequirementEvaluation(**e) for e in sa.get("partial_matches", [])],
        missing_skills=[RequirementEvaluation(**e) for e in sa.get("missing_skills", [])]
    )
    
    ats = db_analysis.ats_analysis
    ats_analysis = ATSAnalysis(**ats)
    
    # Try parsing name/summary
    resume_extract = ResumeExtract()
    cand_name = "Candidate Profile"
    cand_summary = ""
    if db_resume.structured_data:
        resume_extract = ResumeExtract(**db_resume.structured_data)
        cand_name = resume_extract.name or db_resume.filename
        cand_summary = resume_extract.summary or ""
    elif db_resume.candidate_name:
        cand_name = db_resume.candidate_name
        
    jd_title = db_jd.title
    jd_company = db_jd.company
    if not jd_title or jd_title.lower() in ["job description", "none", ""]:
        fb_title, fb_comp = JDAnalyzer.extract_fallback_title_company(db_jd.full_text)
        jd_title = fb_title
        if not jd_company or jd_company.lower() in ["company", "none", ""]:
            jd_company = fb_comp

    reqs = []
    if db_jd.structured_data and "requirements" in db_jd.structured_data:
        reqs = db_jd.structured_data["requirements"]

    return AnalysisResponse(
        id=db_analysis.id,
        resume_id=db_analysis.resume_id,
        jd_id=db_analysis.jd_id,
        overall_score=db_analysis.overall_score,
        scores_breakdown=breakdown,
        skills_analysis=skills_analysis,
        ats_analysis=ats_analysis,
        recommendations=_normalize_string_list(db_analysis.recommendations),
        interview_questions=_normalize_string_list(db_analysis.interview_questions),
        created_at=db_analysis.created_at,
        resume_name=cand_name,
        resume_summary=cand_summary,
        resume_extract=resume_extract,
        jd_title=jd_title or "Target Position",
        jd_company=jd_company or "Confidential",
        jd_requirements=reqs
    )
