import logging
import re
from typing import List, Dict, Any, Tuple
from backend.app.schemas.analysis import (
    ResumeExtract, JDExtract, JDRequirementItem, RequirementEvaluation, RAGChatResponse
)
from backend.app.services.embedding_service import embedding_service
from backend.app.services.vector_store import vector_store
from backend.app.services.llm_service import llm_service
from backend.app.config import settings

logger = logging.getLogger("app.services.rag")

class RAGService:
    @staticmethod
    def chunk_resume(resume_id: int, resume: ResumeExtract) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Convert structured resume into contextual hierarchical text chunks with metadata."""
        chunks = []
        metadata = []
        
        # Chunk 1: Summary
        if resume.summary:
            chunks.append(f"Candidate Profile Summary:\n{resume.summary}")
            metadata.append({
                "document_id": resume_id,
                "document_type": "resume",
                "section": "summary"
            })
            
        # Chunk 2: Skills
        if resume.skills:
            chunks.append(f"Candidate Technical Skills & Tools:\n" + ", ".join(resume.skills))
            metadata.append({
                "document_id": resume_id,
                "document_type": "resume",
                "section": "skills"
            })
            
        # Chunk 3+: Work Experience Items (Full block + individual high-signal achievement bullets)
        for exp in resume.experience:
            full_text = (
                f"Work Experience: {exp.job_title} at {exp.company}\n"
                f"Duration: {exp.duration or 'Not Specified'}\n"
                f"Responsibilities & Achievements:\n" + "\n".join([f"- {r}" for r in exp.responsibilities])
            )
            chunks.append(full_text)
            metadata.append({
                "document_id": resume_id,
                "document_type": "resume",
                "section": "experience",
                "role": exp.job_title,
                "company": exp.company
            })
            
            # Sub-chunk individual responsibilities for high-precision retrieval
            for r in exp.responsibilities:
                if len(r.strip()) > 15:
                    chunks.append(f"[{exp.company} - {exp.job_title}]: {r.strip()}")
                    metadata.append({
                        "document_id": resume_id,
                        "document_type": "resume",
                        "section": "experience_detail",
                        "role": exp.job_title
                    })
            
        # Chunk 4+: Project Items (Full project + technology mapping)
        for proj in resume.projects:
            text = (
                f"Project: {proj.name}\n"
                f"Description: {proj.description}\n"
                f"Technologies Used: " + ", ".join(proj.technologies)
            )
            chunks.append(text)
            metadata.append({
                "document_id": resume_id,
                "document_type": "resume",
                "section": "projects",
                "project_name": proj.name
            })
            
        # Chunk 5+: Education & Certifications
        for edu in resume.education:
            text = (
                f"Education:\n"
                f"Degree: {edu.degree}\n"
                f"Institution: {edu.institution}\n"
                f"Graduation Year: {edu.year or 'Not Specified'}"
            )
            chunks.append(text)
            metadata.append({
                "document_id": resume_id,
                "document_type": "resume",
                "section": "education"
            })
            
        if resume.certifications:
            chunks.append(f"Certifications & Credentials:\n" + "\n".join([f"- {c}" for c in resume.certifications]))
            metadata.append({
                "document_id": resume_id,
                "document_type": "resume",
                "section": "certifications"
            })
            
        return chunks, metadata

    @staticmethod
    def chunk_jd(jd_id: int, jd: JDExtract) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Convert structured job description into contextual text chunks with metadata."""
        chunks = []
        metadata = []
        
        # Chunk 1: Title & Company
        chunks.append(f"Job Opportunity: {jd.job_title or 'Developer'} at {jd.company or 'Confidential'}")
        metadata.append({
            "document_id": jd_id,
            "document_type": "job_description",
            "section": "overview"
        })
        
        # Chunk 2: Core Requirements list
        if jd.requirements:
            req_text = "Key Job Requirements:\n" + "\n".join(
                [f"- {r.skill} ({r.type}, importance: {r.importance})" for r in jd.requirements]
            )
            chunks.append(req_text)
            metadata.append({
                "document_id": jd_id,
                "document_type": "job_description",
                "section": "requirements"
            })
            
        # Chunk 3: Education/Experience summary
        edu_exp = (
            f"Role Expectations:\n"
            f"Experience Required: {jd.experience_years_required} years\n"
            f"Education Required: {jd.education_requirements or 'Not Specified'}"
        )
        chunks.append(edu_exp)
        metadata.append({
            "document_id": jd_id,
            "document_type": "job_description",
            "section": "qualifications"
        })
        
        return chunks, metadata

    @staticmethod
    def evaluate_requirements(
        resume_id: int, 
        requirements: List[JDRequirementItem],
        resume_chunks: List[str] | None = None,
    ) -> List[RequirementEvaluation]:
        """Evaluate JD requirements against resume chunks using fast, single-batch hybrid retrieval & LLM evaluation."""
        logger.info(f"Evaluating {len(requirements)} requirements in batch...")
        if not requirements:
            return []

        # 1. Gather all resume context & hybrid evidence for the requirements
        all_chunks = resume_chunks or []
        evidence_map = {}
        for req in requirements:
            evs = []
            if all_chunks:
                escaped = re.escape(req.skill.strip())
                for c in all_chunks:
                    if re.search(r"\b" + escaped + r"\b", c, re.I):
                        evs.append(c)
            # Try vector search
            try:
                req_vector = embedding_service.embed_text(req.skill)
                similar_chunks = vector_store.search_similar_chunks(
                    collection_name="resumes",
                    query_vector=req_vector,
                    filter_doc_id=resume_id,
                    doc_type="resume",
                    limit=3
                )
                for m in similar_chunks:
                    if m["score"] > 0.35 and m["text"] not in evs:
                        evs.append(m["text"])
            except Exception:
                pass
            evidence_map[req.skill] = evs[:3]

        # 2. If not mock mode, execute single batch structured output LLM call
        if not settings.MOCK_AI:
            try:
                from backend.app.schemas.analysis import BatchEvaluationResponse
                context_summary = "\n\n".join(all_chunks[:8])
                req_list_str = "\n".join([
                    f"{idx+1}. Requirement: {r.skill} (Type: {r.type}, Priority: {r.importance})"
                    for idx, r in enumerate(requirements)
                ])

                prompt = (
                    f"Candidate Resume Context:\n"
                    f"{context_summary}\n\n"
                    f"Job Requirements To Evaluate:\n"
                    f"{req_list_str}\n\n"
                    f"Evaluate EVERY requirement above against the candidate's skills, experience, and projects.\n"
                    f"For each requirement:\n"
                    f"- `requirement`: exact name of requirement from the list\n"
                    f"- `status`: 'strong_match' if candidate clearly demonstrates the skill/technology, "
                    f"'partial_match' if candidate has related/foundational background, 'missing' if absent.\n"
                    f"- `similarity`: '0.95' for strong_match, '0.70' for partial_match, '0.0' for missing.\n"
                    f"- `confidence`: '0.95'\n"
                    f"- `evidence`: exact quotes or bullet references from the resume context\n"
                    f"- `explanation`: 1-2 sentence detailed assessment."
                )

                system_prompt = (
                    "You are a Lead Technical Recruiter. Accurately verify every requirement against candidate evidence. "
                    "Assign 'strong_match' whenever the candidate has hands-on experience, projects, or clear proficiency in the technology."
                )

                batch_res = llm_service.generate_structured_output(
                    prompt=prompt,
                    schema=BatchEvaluationResponse,
                    system_prompt=system_prompt
                )

                if batch_res and batch_res.evaluations and len(batch_res.evaluations) >= len(requirements) // 2:
                    eval_dict = {e.requirement.lower().strip(): e for e in batch_res.evaluations if e.requirement}
                    ordered_evals = []
                    for req in requirements:
                        matched_eval = eval_dict.get(req.skill.lower().strip())
                        if not matched_eval:
                            # Fuzzy fallback match in dict
                            for k, v in eval_dict.items():
                                if k in req.skill.lower() or req.skill.lower() in k:
                                    matched_eval = v
                                    break
                        if matched_eval:
                            matched_eval.requirement = req.skill
                            ordered_evals.append(matched_eval)
                        else:
                            ordered_evals.append(RAGService._mock_evaluate_single_requirement(req.skill, all_chunks))
                    logger.info(f"Batch evaluation completed successfully ({len(ordered_evals)} requirements).")
                    return ordered_evals
            except Exception as e:
                logger.warning(f"Batch LLM evaluation failed: {e}. Falling back to fuzzy matching.")

        # Fallback offline mode
        evaluations = [RAGService._mock_evaluate_single_requirement(req.skill, all_chunks) for req in requirements]
        return evaluations

    @staticmethod
    def _mock_evaluate_single_requirement(
        requirement: str,
        resume_chunks: List[str],
    ) -> RequirementEvaluation:
        """Fuzzy/evidence requirement evaluation for offline mode."""
        # Clean requirement for safe regex searching
        escaped_req = re.escape(requirement.strip())
        tokens = [t for t in re.split(r"[/,;\s]+", requirement) if len(t) >= 2]
        
        evidence = []
        for chunk in resume_chunks:
            lines = [line.strip(" -•") for line in chunk.splitlines() if line.strip()]
            for line in lines:
                # Direct match or multi-token match
                if re.search(escaped_req, line, re.I) or any(re.search(r"\b" + re.escape(tok) + r"\b", line, re.I) for tok in tokens):
                    if line not in evidence:
                        evidence.append(line)
        
        if evidence:
            # Check if exact requirement term is found
            has_exact = any(re.search(escaped_req, line, re.I) for line in evidence)
            status = "strong_match" if has_exact else "partial_match"
            return RequirementEvaluation(
                requirement=requirement,
                status=status,
                similarity="0.85" if has_exact else "0.55",
                confidence="0.90",
                evidence=evidence[:3],
                explanation=f"Resume contains verified evidence matching '{requirement}'." if has_exact else f"Resume contains related skills or partial evidence matching '{requirement}'."
            )
            
        return RequirementEvaluation(
            requirement=requirement,
            status="missing",
            similarity="0.0",
            confidence="1.0",
            evidence=[],
            explanation=f"No direct mention or clear evidence of '{requirement}' was found in the parsed resume."
        )

    @staticmethod
    def chat_with_documents(
        resume_id: int,
        jd_id: int,
        message: str
    ) -> RAGChatResponse:
        """Answer questions by retrieving contextual chunks from both resume and job description."""
        # 1. Embed query message
        query_vector = embedding_service.embed_text(message)
        
        # 2. Retrieve resume chunks
        resume_matches = vector_store.search_similar_chunks(
            collection_name="resumes",
            query_vector=query_vector,
            filter_doc_id=resume_id,
            doc_type="resume",
            limit=3
        )
        
        # 3. Retrieve JD chunks
        jd_matches = vector_store.search_similar_chunks(
            collection_name="resumes",  # We put both in the same vector store
            query_vector=query_vector,
            filter_doc_id=jd_id,
            doc_type="job_description",
            limit=2
        )
        
        # Compile contexts
        context_chunks = []
        sources = []
        
        for m in resume_matches:
            if m["score"] > 0.15:
                context_chunks.append(f"[Resume - {m['metadata'].get('section', 'info')}]: {m['text']}")
                sources.append(f"Resume Section: {m['metadata'].get('section', 'general')}")
                
        for m in jd_matches:
            if m["score"] > 0.15:
                context_chunks.append(f"[Job Description - {m['metadata'].get('section', 'info')}]: {m['text']}")
                sources.append(f"Job Description: {m['metadata'].get('section', 'general')}")
                
        if not context_chunks:
            return RAGChatResponse(
                response="I couldn't find any relevant details in either the Resume or Job Description to answer your query.",
                sources=[]
            )
            
        context_text = "\n\n".join(context_chunks)
        
        # Construct RAG prompt
        system_prompt = (
            "You are an elite AI Technical Executive Recruiter & Career Strategist. "
            "Your objective is to provide comprehensive, detailed, highly technical, and actionable answers to the candidate's query "
            "based strictly on the provided context segments from the candidate's Resume and Job Description.\n"
            "FORMATTING & STYLE RULES:\n"
            "- Use clean GitHub markdown formatting with bold headers, concise bullet points, and clear spacing.\n"
            "- Highlight key skills, technologies, and achievements in **bold**.\n"
            "- Directly reference evidence or quotes from the candidate's experience or the JD requirements.\n"
            "- If gaps or weaknesses are asked about, state them objectively and give exact 1-2 sentence rephrasing advice.\n"
            "- Never hallucinate credentials or facts outside the provided segments."
        )
        
        prompt = (
            f"Context Segments:\n{context_text}\n\n"
            f"User Question: {message}\n\n"
            f"Please formulate a clear, detailed, and structured response addressing the user's question."
        )
        
        answer = llm_service.generate_completion(prompt=prompt, system_prompt=system_prompt)
        
        return RAGChatResponse(
            response=answer,
            sources=list(set(sources))
        )
