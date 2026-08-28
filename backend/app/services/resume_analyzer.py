import logging
from backend.app.services.llm_service import llm_service
from backend.app.schemas.analysis import ResumeExtract

logger = logging.getLogger("app.services.resume_analyzer")

class ResumeAnalyzer:
    @staticmethod
    def analyze(resume_text: str) -> ResumeExtract:
        """Analyze raw resume text and extract structured information using Groq LLM."""
        logger.info("Starting structured resume analysis...")
        
        system_prompt = (
            "You are an expert Technical Executive Recruiter and Senior Resume Parser. "
            "Your objective is to extract complete, highly detailed structured information from raw resume text. "
            "CRITICAL INSTRUCTIONS:\n"
            "1. Candidate Name (`name`): Reconstruct the candidate's actual full name from top header lines, fixing any font kerning/spacing artifacts (e.g. convert 'D IPAKC HHETRI' or 'D I P A K C H H E T R I' to 'Dipak Chhetri'). Do NOT confuse headers like 'SUMMARY' or 'RESUME' for a name.\n"
            "2. Technical Skills (`skills`): Extract every single programming language, framework, database, cloud service, tool, library, methodology, and domain skill mentioned in the resume. Do NOT omit any skill.\n"
            "3. Work Experience (`experience`): Extract all employment history items with exact job titles, companies, dates/durations, and full list of bullet point responsibilities with metrics.\n"
            "4. Projects (`projects`): Extract all projects with their full title, description, and list of technologies used.\n"
            "5. Education (`education`): Degrees, universities, and graduation years.\n"
            "6. Years of Experience (`years_of_experience`): Compute total professional work experience in years (0.0 if student/entry-level)."
        )
        
        prompt = (
            f"Please extract structured resume content from the raw text below:\n\n"
            f"--- START RESUME TEXT ---\n"
            f"{resume_text}\n"
            f"--- END RESUME TEXT ---\n\n"
            f"Return a complete ResumeExtract schema containing name, summary, skills, experience, projects, education, certifications, and years_of_experience."
        )
        
        try:
            result = llm_service.generate_structured_output(
                prompt=prompt,
                schema=ResumeExtract,
                system_prompt=system_prompt
            )
            if result.name:
                import re
                clean = result.name.strip()
                clean = re.sub(r"\s+", " ", clean)
                # Fix split spacing kerning artifacts if present
                clean = re.sub(r"\b([A-Z])\s+([A-Z][a-z]+)k\s+HH", r"\1\2 Ch", clean, flags=re.I)
                result.name = clean.title()
            logger.info(f"Resume analysis complete. Candidate parsed: {result.name}")
            return result
        except Exception as e:
            logger.error(f"Error extracting resume details: {e}")
            # Fallback to an empty model
            return ResumeExtract()
