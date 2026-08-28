import logging
import json
import re
from typing import List, Dict, Any, Optional
from backend.app.config import settings
from backend.app.services.llm_service import llm_service
from backend.app.schemas.analysis import ResumeExtract, JDExtract, RequirementEvaluation

logger = logging.getLogger("app.services.insights")

def _normalize_string_list(data: Any) -> List[str]:
    """Ensure data is strictly a list of flat strings, flattening any dicts, nested lists, or objects returned by LLMs."""
    if data is None:
        return []
    if isinstance(data, str):
        # Try JSON parsing
        data_clean = data.strip()
        if (data_clean.startswith("[") and data_clean.endswith("]")) or (data_clean.startswith("{") and data_clean.endswith("}")):
            try:
                parsed = json.loads(data_clean)
                return _normalize_string_list(parsed)
            except Exception:
                pass
        lines = [line.strip() for line in data.splitlines() if line.strip()]
        return lines if lines else [data_clean]
        
    if isinstance(data, dict):
        flat = []
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                flat.extend(_normalize_string_list(v))
            elif isinstance(v, str) and v.strip():
                flat.append(f"{k}: {v.strip()}")
            elif v is not None:
                flat.append(f"{k}: {v}")
        return flat

    if not isinstance(data, list):
        return [str(data).strip()]

    flat = []
    for item in data:
        if isinstance(item, str):
            if item.strip():
                flat.append(item.strip())
        elif isinstance(item, dict):
            if "question" in item:
                cat = item.get("category") or item.get("type")
                q = item["question"]
                flat.append(f"{cat}: {q}" if cat else str(q))
            elif "recommendation" in item:
                t = item.get("type") or "DO"
                rec = item["recommendation"]
                flat.append(f"{t}: {rec}" if not str(rec).upper().startswith(("DO:", "AVOID:")) else str(rec))
            else:
                for k, v in item.items():
                    if isinstance(v, str) and v.strip():
                        flat.append(f"{k}: {v.strip()}")
                    elif isinstance(v, (list, dict)):
                        flat.extend(_normalize_string_list(v))
                    elif v is not None:
                        flat.append(f"{k}: {v}")
        elif isinstance(item, list):
            flat.extend(_normalize_string_list(item))
        elif item is not None:
            flat.append(str(item).strip())
    return flat

class InsightsService:
    @staticmethod
    def generate_recommendations(
        resume: ResumeExtract,
        evaluations: List[RequirementEvaluation]
    ) -> List[str]:
        """Generate actionable resume optimization tips partitioned into DO and AVOID groups."""
        logger.info("Generating resume improvement recommendations...")
        
        missing_skills = [e.requirement for e in evaluations if e.status == "missing"]
        partial_skills = [e.requirement for e in evaluations if e.status == "partial_match"]
        
        if settings.MOCK_AI:
            recs = []
            if missing_skills:
                recs.append(f"DO: Add verified evidence for {', '.join(missing_skills[:3])} only if you have actually used it in work, coursework, or a project.")
            if partial_skills:
                recs.append(f"DO: Add a concrete outcome or responsibility that shows your level of experience with {', '.join(partial_skills[:3])}.")
            if resume.projects:
                recs.append("DO: Keep each project’s technologies and your specific contribution in the same project entry.")
            if not resume.skills:
                recs.append("DO: Add a clearly labeled Skills section using the exact tools and languages you have used.")
            if not resume.experience:
                recs.append("DO: Use a standard Experience heading and include dates, role titles, employers, and concise achievement bullets.")
            recs.append("AVOID: Adding tools or metrics you cannot explain in an interview.")
            return recs[:6]

        # Generate using LLM
        prompt = (
            f"Candidate Name: {resume.name or 'John Doe'}\n"
            f"Candidate Summary: {resume.summary or ''}\n"
            f"Missing Skills: {', '.join(missing_skills)}\n"
            f"Partial Match Skills: {', '.join(partial_skills)}\n\n"
            f"Based on the resume matching analysis, generate exactly 6 specific, highly detailed, and verbose recommendations to optimize the candidate's resume.\n"
            f"The recommendations must be divided into exactly 3 'DO' recommendations and 3 'AVOID' recommendations.\n"
            f"Each recommendation must be structured as a verbose sentence (at least 2-3 lines long) starting with either 'DO: ' or 'AVOID: ':\n"
            f"- 'DO: <actionable advice on what the candidate should add, highlight, or rephrase with exact examples based on their projects>'\n"
            f"- 'AVOID: <what the candidate should NOT do, such as formatting traps, generic phrasing, listing buzzwords without context, or bad practices to avoid in their resume>'\n\n"
            f"Return the response as a valid JSON list of strings."
        )
        
        system_prompt = "You are a professional resume writer and career coach. Return the response as a valid JSON list of strings."
        
        try:
            raw = llm_service.generate_completion(prompt, system_prompt)
            clean_raw = raw.strip()
            # Strip markdown fences if present
            if clean_raw.startswith("```"):
                clean_raw = re.sub(r"^```(?:json)?\n?", "", clean_raw)
                clean_raw = re.sub(r"\n?```$", "", clean_raw).strip()
            
            json_match = re.search(r"(\[.*\])", clean_raw, re.DOTALL)
            if json_match:
                clean_raw = json_match.group(1).strip()
            result = json.loads(clean_raw)
            norm = _normalize_string_list(result)
            if norm:
                return norm
        except Exception as e:
            logger.error(f"Error generating LLM recommendations: {e}")
            
        return [
            "DO: Add your core programming language proficiencies directly into the work experience bullets.",
            "AVOID: Do not list skills in a single long block without categorization."
        ]

    @staticmethod
    def generate_interview_questions(
        resume: ResumeExtract,
        jd: JDExtract,
        evaluations: List[RequirementEvaluation]
    ) -> List[str]:
        """Generate tailored interview questions targeting gaps and candidate experience."""
        logger.info("Generating interview questions...")
        
        missing_skills = [e.requirement for e in evaluations if e.status == "missing"]
        projects = [p.name for p in resume.projects]
        
        if settings.MOCK_AI:
            questions = []
            if projects:
                questions.append(f"Project-Specific: In your project '{projects[0]}', what decision had the greatest impact on the outcome?")
            if missing_skills:
                questions.append(f"Role-Specific: This role asks for {missing_skills[0]}. What relevant experience or learning plan would you bring to it?")
            if resume.experience:
                questions.append(f"Resume-Specific: What impact did you have in your role as {resume.experience[0].job_title}?")
            questions.append("Behavioral: Tell me about a time you had to make a difficult trade-off in your work.")
            return questions

        # Generate using LLM
        prompt = (
            f"Job Title: {jd.job_title}\n"
            f"Candidate Skills: {', '.join(resume.skills)}\n"
            f"Candidate Projects: {', '.join(projects)}\n"
            f"Missing Skills: {', '.join(missing_skills)}\n\n"
            f"Generate 5 customized interview questions for this candidate. "
            f"Include one Technical question, one Project-specific question (reference a project name), "
            f"one Role-specific question targeting a missing skill, one Behavioral question, and one Resume-specific question."
        )
        
        system_prompt = "You are a senior technical interviewer. Return the questions as a JSON list of plain strings. Do not use dictionaries or objects."
        
        try:
            raw = llm_service.generate_completion(prompt, system_prompt)
            clean_raw = raw.strip()
            if clean_raw.startswith("```"):
                clean_raw = re.sub(r"^```(?:json)?\n?", "", clean_raw)
                clean_raw = re.sub(r"\n?```$", "", clean_raw).strip()
            
            json_match = re.search(r"(\[.*\])", clean_raw, re.DOTALL)
            if json_match:
                clean_raw = json_match.group(1).strip()
            result = json.loads(clean_raw)
            norm = _normalize_string_list(result)
            if norm:
                return norm
        except Exception as e:
            logger.error(f"Error generating LLM interview questions: {e}")
            
        return ["Describe your experience building web applications in Python."]

# Initialize service instance
insights_service = InsightsService()
