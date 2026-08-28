import json
import logging
import re
from typing import Type, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from backend.app.config import settings
from backend.app.schemas.analysis import (
    ResumeExtract, JDExtract, ExperienceItem, ProjectItem, EducationItem, 
    JDRequirementItem, RequirementEvaluation
)

logger = logging.getLogger("app.services.llm_service")

T = TypeVar('T', bound=BaseModel)

class LLMService:
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
        self.model_name = settings.GROQ_MODEL
        self.fallback_models = ["llama-3.1-8b-instant"]
        self.mock_mode = settings.MOCK_AI or not self.groq_api_key
        
        if self.mock_mode:
            logger.info("LLMService initialized in MOCK MODE.")
        else:
            logger.info(f"LLMService initialized with Groq model: {self.model_name}")
            try:
                self.llm = ChatGroq(
                    api_key=self.groq_api_key,
                    model_name=self.model_name,
                    temperature=0.0,
                    max_retries=3,
                    request_timeout=45.0
                )
            except Exception as e:
                logger.error(f"Error initializing ChatGroq: {e}. Falling back to Mock Mode.")
                self.mock_mode = True

    def _get_llm_instance(self, model_name: str) -> ChatGroq:
        """Helper to get a ChatGroq instance for a specific model."""
        return ChatGroq(
            api_key=self.groq_api_key,
            model_name=model_name,
            temperature=0.0,
            max_retries=2,
            request_timeout=30.0
        )

    def generate_completion(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """General text completion with multi-model fallback."""
        if self.mock_mode:
            return self._mock_completion(prompt, system_prompt)
        
        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("user", prompt))

        # Try primary model first, then fallback models
        for m_name in [self.model_name] + self.fallback_models:
            try:
                llm = self._get_llm_instance(m_name)
                response = llm.invoke(messages)
                if response and response.content:
                    return response.content
            except Exception as e:
                logger.warning(f"Groq API call with model '{m_name}' failed: {e}. Trying next fallback...")

        logger.error("All Groq models failed. Falling back to Mock Mode.")
        return self._mock_completion(prompt, system_prompt)

    def generate_structured_output(
        self, 
        prompt: str, 
        schema: Type[T], 
        system_prompt: Optional[str] = None
    ) -> T:
        """Call LLM and return validated Pydantic object with multi-tier & multi-model fallback."""
        if self.mock_mode:
            return self._mock_structured_output(prompt, schema)
            
        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("user", prompt))

        # Tier 1: Try structured tool calling across available Groq models
        for m_name in [self.model_name] + self.fallback_models:
            try:
                llm = self._get_llm_instance(m_name)
                structured_llm = llm.with_structured_output(schema)
                result = structured_llm.invoke(messages)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Groq structured output failed for model '{m_name}': {e}.")

        # Tier 2: Direct completion prompting with robust regex JSON extraction
        try:
            json_system = (system_prompt or "") + "\nRespond strictly with a single valid JSON object matching the requested schema. Do not include markdown code block formatting or commentary."
            raw_text = self.generate_completion(prompt, json_system)
            
            # Robust JSON payload extraction
            json_match = re.search(r"(\{.*\})", raw_text, re.DOTALL)
            if json_match:
                clean_json = json_match.group(1).strip()
                parsed_data = json.loads(clean_json)
                return schema.model_validate(parsed_data)
        except Exception as e:
            logger.error(f"Groq direct JSON completion fallback failed: {e}. Falling back to Mock Mode.")

        return self._mock_structured_output(prompt, schema)

    # ==========================================
    # Mock Mode Implementation (High-Fidelity)
    # ==========================================
    def _mock_completion(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Simulate RAG chat queries based on prompt content."""
        prompt_lower = prompt.lower()
        
        # Determine chatbot query type and respond realistically
        if "weakness" in prompt_lower or "missing" in prompt_lower:
            return (
                "Based on the analysis of the Job Description and your Resume, your primary areas of growth are: \n\n"
                "1. **Cloud & Deployments**: The JD requests experience with AWS and Kubernetes, but your resume only mentions "
                "local Docker setups. Adding details about cloud pipelines would strengthen your profile.\n"
                "2. **Advanced Caching**: The JD highlights Redis for scaling REST APIs. Your current work details generic PostgreSQL "
                "queries without caching optimizations.\n\n"
                "To improve, highlight these technologies in past projects or list relevant certifications."
            )
        elif "match" in prompt_lower or "strength" in prompt_lower:
            return (
                "You are a strong match for this position because:\n\n"
                "- **FastAPI & REST APIs**: You have explicit experience building backend endpoints using FastAPI, which matches the JD's core requirement.\n"
                "- **Frontend Alignment**: Your React and TypeScript experience aligns perfectly with the JD's full-stack or frontend requirements.\n"
                "- **Deterministic Clean Code**: Your projects demonstrate a structured approach using Pydantic, standard databases, and robust schemas."
            )
        elif "change" in prompt_lower or "optimize" in prompt_lower or "improve" in prompt_lower:
            return (
                "Here are the top things you should adjust on your resume for this JD:\n\n"
                "1. **Highlight FastAPI achievements**: Instead of just listing it under skills, explicitly mention it in your first experience item (e.g., 'Designed and deployed REST APIs using FastAPI, decreasing API response times by 30%').\n"
                "2. **Add Docker / Containerization details**: Emphasize how you containerized your applications to showcase DevOps familiarity."
            )
        else:
            return (
                "Regarding your query, the resume displays strong competency in backend development, specifically Python, FastAPI, and PostgreSQL. "
                "However, the JD seeks experience with cloud orchestration (Kubernetes) and cache systems (Redis) that are not currently documented in your resume. "
                "I recommend updating your experience items to highlight any work involving load handling, containerization, or API performance tuning."
            )

    def _mock_structured_output(self, prompt: str, schema: Type[T]) -> T:
        """Generate high-fidelity structured Pydantic models depending on target schema."""
        # Find raw text in prompt using simple regex to make mocks contextual
        resume_text_match = re.search(r"(?:START RESUME|Resume text:)(.*?)(?:END RESUME|Job Description:|$)", prompt, re.DOTALL | re.IGNORECASE)
        jd_text_match = re.search(r"(?:START JOB DESCRIPTION|Job Description:)(.*?)(?:END JOB DESCRIPTION|$)", prompt, re.DOTALL | re.IGNORECASE)
        
        resume_text = resume_text_match.group(1) if resume_text_match else ""
        jd_text = jd_text_match.group(1) if jd_text_match else ""
        
        if schema == ResumeExtract:
            # Conservative fallback: extract candidate data strictly from available resume text
            lines = [re.sub(r"\s+", " ", line).strip() for line in resume_text.splitlines() if line.strip() and line.strip(" -")]
            heading_re = re.compile(r"^(summary|profile|objective|skills?|technical skills|experience|work experience|employment|projects?|education|certifications?|awards?)$", re.I)
            sections: Dict[str, List[str]] = {}
            current = "other"
            for line in lines:
                heading = line.rstrip(":- ")
                if heading_re.match(heading):
                    current = heading.lower()
                    sections.setdefault(current, [])
                else:
                    sections.setdefault(current, []).append(line)

            def section(*names: str) -> List[str]:
                for name in names:
                    if name in sections:
                        return sections[name]
                return []

            contact_re = re.compile(r"(resume|curriculum vitae|email|phone|linkedin|github|http|@|\+?\d[\d\s().-]{7,}|summary|experience)", re.I)
            name = None
            for line in lines[:8]:
                clean_line = re.sub(r"[\(\)\[\]\{\}]", "", line).strip()
                if not clean_line or contact_re.search(clean_line) or heading_re.match(clean_line):
                    continue
                # Pick line that looks like a name (2-4 words, capitalized or letters)
                words = clean_line.split()
                if 1 <= len(words) <= 4 and all(w[0].isupper() or w[0].isalpha() for w in words if w):
                    name = clean_line
                    break

            skill_catalog = ["Python", "FastAPI", "Django", "Flask", "React", "TypeScript", "JavaScript", "Node.js", "Express", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Git", "GitHub", "REST", "GraphQL", "PyTorch", "TensorFlow", "LLM", "RAG", "LangChain", "HTML", "CSS", "Tailwind CSS", "Java", "C++", "C#", "SQL"]
            skill_lines = section("skills", "skill", "technical skills")
            skill_values = [part.strip(" •-|\t") for line in skill_lines for part in re.split(r"[,;|•]", line) if part.strip()]
            found_skills: List[str] = []
            for skill in skill_catalog:
                if re.search(r"\b" + re.escape(skill) + r"\b", resume_text, re.I) and skill.lower() not in {item.lower() for item in found_skills}:
                    found_skills.append(skill)
            for value in skill_values:
                if len(value) <= 45 and value.lower() not in {item.lower() for item in found_skills}:
                    found_skills.append(value)

            date_re = re.compile(r"(?:19|20)\d{2}\s*(?:-|–|—|to)\s*(?:present|current|(?:19|20)\d{2})", re.I)
            experience_lines = section("experience", "work experience", "employment")
            exp_items: List[ExperienceItem] = []
            for index, line in enumerate(experience_lines):
                date_match = date_re.search(line)
                if not date_match:
                    continue
                duration = date_match.group(0)
                before = line[:date_match.start()].strip(" |,-")
                parts = [part.strip() for part in re.split(r"\s+[|@]\s+", before) if part.strip()]
                title = parts[0] if parts else ""
                company = parts[1] if len(parts) > 1 else ""
                responsibilities = [item.lstrip("•- ") for item in experience_lines[index + 1:index + 5] if len(item) > 20 and not date_re.search(item)]
                exp_items.append(ExperienceItem(job_title=title, company=company, duration=duration, responsibilities=responsibilities))

            project_lines = section("projects", "project")
            projects: List[ProjectItem] = []
            for index, line in enumerate(project_lines):
                if line.startswith(("•", "-")):
                    continue
                description = " ".join(item.lstrip("•- ") for item in project_lines[index + 1:index + 3])
                technologies = [skill for skill in skill_catalog if re.search(r"\b" + re.escape(skill) + r"\b", line + " " + description, re.I)]
                projects.append(ProjectItem(name=line[:100], description=description, technologies=technologies))

            education = [EducationItem(degree=line, institution="", year=(re.search(r"(?:19|20)\d{2}", line).group(0) if re.search(r"(?:19|20)\d{2}", line) else None)) for line in section("education")]
            certifications = [line.lstrip("•- ") for line in section("certifications", "awards")]
            explicit_years = re.search(r"(\d+(?:\.\d+)?)\+?\s*years?", resume_text, re.I)
            summary_lines = section("summary", "profile", "objective")
            return ResumeExtract(name=name, summary=(" ".join(summary_lines) or None), skills=found_skills, experience=exp_items, projects=projects, education=education, certifications=certifications, years_of_experience=float(explicit_years.group(1)) if explicit_years else 0.0)

        elif schema == JDExtract:
            lines = [re.sub(r"\s+", " ", line).strip() for line in jd_text.splitlines() if line.strip() and line.strip(" -")]
            
            # --- Job Title Extraction ---
            title = None
            title_header = re.search(r"(?:job title|position|role|title|designation|hiring for|opening for)\s*[:|-]\s*([^\n]+)", jd_text, re.I)
            if title_header:
                cand = title_header.group(1).strip().rstrip(":- ,")
                cand = re.sub(r"^(?:as an?|seeking an?|looking for an?|hiring an?)\s+", "", cand, flags=re.I).strip(" ,:-")
                cand = re.sub(r"\s+(?:you|we|the|our|with|who|to|and|in|at|will)\b.*$", "", cand, flags=re.I).strip(" ,:-")
                if cand and len(cand) <= 80:
                    title = cand.title()
            
            if not title:
                m = re.search(r"\b(?:as an?|seeking an?|looking for an?|hiring an?|hire an?|hiring for an?)\s+([A-Za-z0-9/& -]{2,60}?)(?=\s*[,.\n]|,\s*you\b|\s+to\b|\s+who\b|\s+with\b|\s+will\b)", jd_text, re.I)
                if m:
                    cand = m.group(1).strip().rstrip(":- ,")
                    cand = re.sub(r"\s+(?:you|we|the|our|with|who|to|and|in|at|will)\b.*$", "", cand, flags=re.I).strip(" ,:-")
                    if any(term in cand.lower() for term in ["engineer", "developer", "designer", "manager", "analyst", "architect", "scientist", "specialist", "consultant", "intern", "lead", "head", "director", "administrator", "officer", "programmer", "associate", "cto", "vp", "president"]):
                        title = cand.title()

            if not title:
                role_terms = ("engineer", "developer", "designer", "manager", "analyst", "architect", "scientist", "specialist", "consultant", "intern", "lead", "head", "director", "administrator", "officer", "programmer", "associate", "cto", "vp", "president")
                for line in lines[:10]:
                    clean = line.rstrip(":- ,")
                    clean = re.sub(r"^(?:as an?|seeking an?|looking for an?|hiring an?)\s+", "", clean, flags=re.I).strip(" ,:-")
                    clean = re.sub(r"\s+(?:you|we|the|our|with|who|to|and|in|at|will)\b.*$", "", clean, flags=re.I).strip(" ,:-")
                    if len(clean) <= 60 and any(term in clean.lower() for term in role_terms) and not any(skip in clean.lower() for skip in ["description", "overview", "summary", "responsibilities", "qualifications", "requirements"]):
                        title = clean.title()
                        break

            # --- Company Extraction ---
            company = None
            company_header = re.search(r"(?:company|organization|employer|client|bank|firm)\s*[:|-]\s*([^\n]+)", jd_text, re.I)
            if company_header:
                cand = company_header.group(1).strip().rstrip(":- ,")
                if len(cand) <= 50:
                    company = cand.title()
            
            if not company:
                m = re.search(r"\b([A-Z][A-Za-z0-9&., -]{1,30}?)\s+(?:Values|Mindset|Culture|Principles|Creed|is hiring|is looking|is seeking)\b", jd_text)
                if m:
                    cand = m.group(1).strip().rstrip(":- ,")
                    if not cand.lower().startswith(("the ", "our ", "these ", "all ")):
                        company = cand.title()

            if not company:
                company_match = re.search(r"\b(?:about|join|at|with)\s+([A-Z][A-Za-z0-9&,. -]{1,30}?)(?=\s+(?:is|are|values|team|we|in|to|as)|[.,!\n])", jd_text)
                if company_match:
                    comp_cand = company_match.group(1).strip().rstrip(":- ,")
                    if comp_cand and not comp_cand.lower().startswith(("code", "a ", "the ", "our ", "this ", "pune", "bangalore", "mumbai", "london", "new york", "delhi")):
                        company = comp_cand.title()

            experience_match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?(?:\s+of)?\s+(?:experience|professional experience)", jd_text, re.I)
            education_lines = [line for line in lines if re.search(r"\b(bachelor|master|ph\.?d|degree|b\.?(?:s|a)\.?|m\.?(?:s|a)\.?)\b", line, re.I)]
            skill_catalog = ["Python", "FastAPI", "Django", "Flask", "React", "TypeScript", "JavaScript", "Node.js", "Express", "Docker", "Kubernetes", "AWS", "Azure", "GCP", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Git", "GitHub", "REST", "GraphQL", "PyTorch", "TensorFlow", "LLM", "RAG", "LangChain", "HTML", "CSS", "Tailwind CSS", "Java", "C++", "C#", "SQL", "Figma", "Tableau", "Power BI", "Salesforce", "Generative AI", "Agentic AI"]
            requirements: List[JDRequirementItem] = []
            seen = set()
            section_hint = "required"
            for line in lines:
                lower = line.lower()
                if re.search(r"\b(preferred|nice to have|bonus|plus)\b", lower):
                    section_hint = "preferred"
                elif re.search(r"\b(requirements?|qualifications?|must have|what you bring|skills?)\b", lower):
                    section_hint = "required"
                elif re.search(r"\b(responsibilities|what you.?ll do|duties)\b", lower):
                    section_hint = "responsibility"
                for skill in skill_catalog:
                    if skill.lower() in seen or not re.search(r"(?<!\w)" + re.escape(skill) + r"(?!\w)", line, re.I):
                        continue
                    req_type = "preferred" if section_hint == "preferred" or re.search(r"\b(preferred|nice to have|bonus|plus)\b", lower) else "required"
                    importance = "high" if re.search(r"\b(must|required|mandatory|essential)\b", lower) else "low" if req_type == "preferred" else "medium"
                    requirements.append(JDRequirementItem(skill=skill, type=req_type, importance=importance, source_text=line))
                    seen.add(skill.lower())
            return JDExtract(job_title=title or "Target Position", company=company or "Confidential", requirements=requirements, experience_years_required=float(experience_match.group(1)) if experience_match else 0.0, education_requirements=" ".join(education_lines) or None)

        elif schema == RequirementEvaluation:
            req_match = re.search(r"Requirement:\s*(.*?)(?=\s*\(|$)", prompt)
            req_name = req_match.group(1).strip() if req_match else ""
            return RequirementEvaluation(requirement=req_name, status="missing", similarity="0.0", confidence="1.0", evidence=[], explanation=f"No verified resume evidence was supplied for '{req_name}'.")

        # Fallback empty model
        return schema()
# Initialize service instance
llm_service = LLMService()
