import logging
import re
from typing import Tuple, Optional
from backend.app.services.llm_service import llm_service
from backend.app.schemas.analysis import JDExtract

logger = logging.getLogger("app.services.jd_analyzer")

class JDAnalyzer:
    @staticmethod
    def clean_title(title: Optional[str]) -> Optional[str]:
        if not title:
            return None
        t = str(title).strip().rstrip(":- ,")
        # Remove leading phrasing like 'As an AI Engineer' -> 'AI Engineer'
        t = re.sub(r"^(?:as an?|seeking an?|looking for an?|hiring an?|opening for an?|role of an?)\s+", "", t, flags=re.I).strip(" ,:-")
        # Remove trailing transition words
        t = re.sub(r"\s+(?:you|we|the|our|with|who|to|and|in|at|will)\b.*$", "", t, flags=re.I).strip(" ,:-")
        if not t or t.lower() in ["job description", "job role", "position", "target role", "opportunity", "none"]:
            return None
        return t.title()

    @staticmethod
    def clean_company(company: Optional[str]) -> Optional[str]:
        if not company:
            return None
        c = str(company).strip().rstrip(":- ,")
        if not c or c.lower() in ["company", "confidential", "organization", "employer", "client", "none"]:
            return None
        return c.title()

    @classmethod
    def extract_fallback_title_company(cls, jd_text: str) -> Tuple[str, str]:
        """Heuristic regex extractor for Job Title and Company from raw JD text."""
        if not jd_text:
            return "Target Position", "Confidential"

        title = None
        company = None

        # --- Job Title Extraction ---
        # 1. Explicit headers
        m = re.search(r"(?:job title|position|role|title|designation|hiring for|opening for)\s*[:|-]\s*([^\n]+)", jd_text, re.I)
        if m:
            cand = cls.clean_title(m.group(1))
            if cand and len(cand) < 80:
                title = cand

        # 2. 'As an? <Role>, you will...' or 'Looking for an? <Role>' or 'seeking an? <Role>'
        if not title:
            m = re.search(r"\b(?:as an?|seeking an?|looking for an?|hiring an?|hire an?|hiring for an?)\s+([A-Za-z0-9/& -]{2,60}?)(?=\s*[,.\n]|,\s*you\b|\s+to\b|\s+who\b|\s+with\b|\s+will\b)", jd_text, re.I)
            if m:
                cand = cls.clean_title(m.group(1))
                if cand and any(term in cand.lower() for term in ["engineer", "developer", "designer", "manager", "analyst", "architect", "scientist", "specialist", "consultant", "intern", "lead", "head", "director", "administrator", "officer", "programmer", "associate", "cto", "vp", "president"]):
                    title = cand

        # 3. First 10 lines matching role keywords
        if not title:
            lines = [re.sub(r"\s+", " ", line).strip() for line in jd_text.splitlines() if line.strip()]
            role_terms = ("engineer", "developer", "designer", "manager", "analyst", "architect", "scientist", "specialist", "consultant", "intern", "lead", "head", "director", "administrator", "officer", "programmer", "associate", "cto", "vp", "president")
            for line in lines[:10]:
                clean = line.rstrip(":- ")
                if len(clean) <= 60 and any(term in clean.lower() for term in role_terms) and not any(skip in clean.lower() for skip in ["description", "overview", "summary", "responsibilities", "qualifications", "requirements", "about", "join"]):
                    cand = cls.clean_title(clean)
                    if cand:
                        title = cand
                        break

        # --- Company Extraction ---
        # 1. Explicit headers
        m = re.search(r"(?:company|organization|employer|client|bank|firm)\s*[:|-]\s*([^\n]+)", jd_text, re.I)
        if m:
            cand = cls.clean_company(m.group(1))
            if cand and len(cand) < 50:
                company = cand

        # 2. '<Company> Values', '<Company> Mindset', '<Company> Culture'
        if not company:
            m = re.search(r"\b([A-Z][A-Za-z0-9&., -]{1,30}?)\s+(?:Values|Mindset|Culture|Principles|Creed|is hiring|is looking|is seeking)\b", jd_text)
            if m:
                cand = cls.clean_company(m.group(1))
                if cand and not cand.lower().startswith(("the ", "our ", "these ", "all ")):
                    company = cand

        # 3. 'About <Company>', 'Join <Company>', 'at <Company>'
        if not company:
            m = re.search(r"\b(?:about|join|at|with)\s+([A-Z][A-Za-z0-9&,. -]{1,30}?)(?=\s+(?:is|are|values|team|we|in|to|as)|[.,!\n])", jd_text)
            if m:
                cand = cls.clean_company(m.group(1))
                if cand and not cand.lower().startswith(("a ", "the ", "our ", "this ", "code ", "pune", "bangalore", "mumbai", "london", "new york", "delhi")):
                    company = cand

        return title or "Target Position", company or "Confidential"

    @classmethod
    def analyze(cls, jd_text: str) -> JDExtract:
        """Analyze job description text and extract structured requirements using Groq LLM."""
        logger.info("Starting structured Job Description analysis...")
        
        system_prompt = (
            "You are a Lead Technical Recruiter and Job Architecture Specialist. "
            "Your objective is to dissect a Job Description into precise, structured role requirements.\n"
            "CRITICAL INSTRUCTIONS:\n"
            "1. Job Title (`job_title`): Official title or primary role name (e.g., 'AI Engineer', 'Agentic AI Engineer', 'Senior Software Engineer', 'Assistant Vice President - AI'). Infer the exact role name from phrases like 'As an AI Engineer...', 'We are seeking an...', or header lines. Must be concise and in Title Case. NEVER return null or generic text like 'Job Description'.\n"
            "2. Company (`company`): Name of the hiring company, bank, or organization (e.g., 'Barclays', 'Google', 'Amazon'). Infer from mentions like 'Barclays Values', 'About <Company>', or email signatures. NEVER return null or 'Company' if an organization is mentioned.\n"
            "3. Requirements (`requirements`): Extract every technical skill, framework, database, infrastructure tool, methodology, soft skill, or experience requirement. "
            "For each requirement:\n"
            "   - `skill`: Standardized name of skill or requirement (e.g., 'Python', 'FastAPI', 'AWS', 'System Architecture').\n"
            "   - `type`: 'required' for mandatory qualifications, 'preferred' for nice-to-have or bonus skills.\n"
            "   - `importance`: 'high' for core technologies, 'medium' for secondary requirements, 'low' for minor bonuses.\n"
            "   - `source_text`: The exact sentence or verbatim phrase from the job description where it appears.\n"
            "4. Minimum Experience (`experience_years_required`): Required years of experience (float, 0.0 if not specified).\n"
            "5. Education Requirements (`education_requirements`): Degrees or qualifications requested."
        )
        
        prompt = (
            f"Extract all structured requirements from the Job Description below:\n\n"
            f"--- START JOB DESCRIPTION ---\n"
            f"{jd_text}\n"
            f"--- END JOB DESCRIPTION ---\n\n"
            f"Return a complete JDExtract schema containing job_title, company, requirements (with verbatim source_text citations), experience_years_required, and education_requirements."
        )
        
        fb_title, fb_company = cls.extract_fallback_title_company(jd_text)

        try:
            result = llm_service.generate_structured_output(
                prompt=prompt,
                schema=JDExtract,
                system_prompt=system_prompt
            )
            
            cleaned_title = cls.clean_title(result.job_title)
            cleaned_company = cls.clean_company(result.company)
            
            result.job_title = cleaned_title or fb_title
            result.company = cleaned_company or fb_company
            
            logger.info(f"JD analysis complete. Role: {result.job_title} at {result.company}")
            return result
        except Exception as e:
            logger.error(f"Error extracting JD requirements: {e}")
            return JDExtract(job_title=fb_title, company=fb_company)
