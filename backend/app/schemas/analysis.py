from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import json

# ==========================================
# Resume Extraction Schemas
# ==========================================
class ExperienceItem(BaseModel):
    job_title: Optional[str] = Field(default="", description="Title of the job")
    company: Optional[str] = Field(default="", description="Name of the company")
    duration: Optional[str] = Field(default=None, description="Start date and end date or duration")
    responsibilities: List[str] = Field(default=[], description="List of duties, actions, and achievements")

    @field_validator("job_title", "company", "duration", mode="before")
    @classmethod
    def normalize_str(cls, v):
        if v is None:
            return "" if cls != "duration" else None
        return str(v).strip()

    @field_validator("responsibilities", mode="before")
    @classmethod
    def normalize_responsibilities(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            lines = [line.strip(" -•*") for line in v.splitlines() if line.strip()]
            return lines if lines else [v.strip()]
        if isinstance(v, list):
            flat = []
            for item in v:
                if isinstance(item, str):
                    if item.strip():
                        flat.append(item.strip(" -•*"))
                elif isinstance(item, dict):
                    flat.append(" ".join(str(val) for val in item.values() if val))
                elif item is not None:
                    flat.append(str(item).strip())
            return flat
        return [str(v)]

class ProjectItem(BaseModel):
    name: Optional[str] = Field(default="", description="Name of the project")
    description: Optional[str] = Field(default="", description="Description of what was built and why")
    technologies: List[str] = Field(default=[], description="Languages, databases, frameworks, or tools used")

    @field_validator("name", "description", mode="before")
    @classmethod
    def normalize_str(cls, v):
        return "" if v is None else str(v).strip()

    @field_validator("technologies", mode="before")
    @classmethod
    def normalize_techs(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            parts = [p.strip() for p in re.split(r"[,;/|]", v) if p.strip()]
            return parts if parts else [v.strip()]
        if isinstance(v, list):
            flat = []
            for item in v:
                if isinstance(item, str) and item.strip():
                    flat.append(item.strip())
                elif item is not None:
                    flat.append(str(item).strip())
            return flat
        return [str(v)]

class EducationItem(BaseModel):
    degree: Optional[str] = Field(default="", description="Degree or certificate name")
    institution: Optional[str] = Field(default="", description="Name of school or university")
    year: Optional[str] = Field(default=None, description="Graduation year")

    @field_validator("degree", "institution", "year", mode="before")
    @classmethod
    def normalize_edu_str(cls, v):
        if v is None:
            return ""
        return str(v).strip()

class ResumeExtract(BaseModel):
    name: Optional[str] = Field(default=None, description="Candidate's full name")
    summary: Optional[str] = Field(default=None, description="Candidate's profile summary")
    skills: List[str] = Field(default=[], description="Extracted skills, tools, languages, frameworks")
    experience: List[ExperienceItem] = Field(default=[], description="Work history details")
    projects: List[ProjectItem] = Field(default=[], description="Projects undertaken")
    education: List[EducationItem] = Field(default=[], description="Education qualifications")
    certifications: List[str] = Field(default=[], description="Certifications and awards")
    years_of_experience: float = Field(default=0.0, description="Total computed years of professional work experience")

    @field_validator("skills", "certifications", mode="before")
    @classmethod
    def normalize_str_lists(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            parts = [p.strip() for p in re.split(r"[,;/|\n]", v) if p.strip()]
            return parts if parts else [v.strip()]
        if isinstance(v, list):
            flat = []
            for item in v:
                if isinstance(item, str) and item.strip():
                    flat.append(item.strip())
                elif item is not None:
                    flat.append(str(item).strip())
            return flat
        return [str(v)]

    @field_validator("years_of_experience", mode="before")
    @classmethod
    def normalize_years(cls, v):
        if v is None:
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            m = re.search(r"(\d+(?:\.\d+)?)", v)
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    pass
        return 0.0

# ==========================================
# Job Description Extraction Schemas
# ==========================================
class JDRequirementItem(BaseModel):
    skill: Optional[str] = Field(default="", description="Name of the skill, technology, or requirement")
    type: Optional[str] = Field(default="required", description="Classification: 'required', 'preferred', 'responsibility', 'qualification'")
    importance: Optional[str] = Field(default="medium", description="Priority: 'high', 'medium', 'low'")
    source_text: Optional[str] = Field(default="", description="The exact sentence or context from the job description where this requirement is mentioned")

    @field_validator("skill", "type", "importance", "source_text", mode="before")
    @classmethod
    def normalize_req_str(cls, v):
        return "" if v is None else str(v).strip()

class JDExtract(BaseModel):
    job_title: Optional[str] = Field(default=None, description="Title of the job role")
    company: Optional[str] = Field(default=None, description="Company name")
    requirements: List[JDRequirementItem] = Field(default=[], description="Structured list of requirements, skills, and responsibilities")
    experience_years_required: float = Field(default=0.0, description="Minimum years of experience required (0.0 if not specified)")
    education_requirements: Optional[str] = Field(default=None, description="Education requirements (e.g. BS, MS in CS)")

    @field_validator("experience_years_required", mode="before")
    @classmethod
    def normalize_jd_years(cls, v):
        if v is None:
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            m = re.search(r"(\d+(?:\.\d+)?)", v)
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    pass
        return 0.0

# ==========================================
# RAG Evaluation Schemas
# ==========================================
class RequirementEvaluation(BaseModel):
    requirement: Optional[str] = Field(default="", description="The requirement from the JD")
    status: Optional[str] = Field(default="missing", description="Match status: 'strong_match', 'partial_match', 'weak_match', 'missing'")
    similarity: Optional[str] = Field(default="0.0", description="Semantic similarity score from vector store (0.0 to 1.0)")
    confidence: Optional[str] = Field(default="1.0", description="Confidence rating of the LLM model evaluation (0.0 to 1.0)")
    evidence: List[str] = Field(default=[], description="Exact sentences/paragraphs extracted from the resume acting as proof")
    explanation: Optional[str] = Field(default="", description="Explanation of why this status was assigned")

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        if not v or not isinstance(v, str):
            return "missing"
        cleaned = v.strip().lower().replace(" ", "_").replace("-", "_")
        if "strong" in cleaned:
            return "strong_match"
        if "partial" in cleaned or "moderate" in cleaned or "medium" in cleaned:
            return "partial_match"
        if "weak" in cleaned or "low" in cleaned:
            return "weak_match"
        if "missing" in cleaned or "none" in cleaned or "absent" in cleaned or "not" in cleaned:
            return "missing"
        return cleaned

    @field_validator("similarity", "confidence", mode="before")
    @classmethod
    def normalize_float_to_str(cls, v):
        if v is None:
            return "0.0"
        return str(v)

    @field_validator("evidence", mode="before")
    @classmethod
    def normalize_evidence_list(cls, v):
        if isinstance(v, str):
            return [v.strip()] if v.strip() else []
        if not isinstance(v, list):
            return []
        return [str(x).strip() for x in v if str(x).strip()]

    @field_validator("requirement", "explanation", mode="before")
    @classmethod
    def normalize_req_text(cls, v):
        return "" if v is None else str(v).strip()

class BatchEvaluationResponse(BaseModel):
    evaluations: List[RequirementEvaluation] = Field(default=[], description="List of evaluated requirements")

# ==========================================
# API Request / Response Schemas
# ==========================================
class RAGChatRequest(BaseModel):
    analysis_id: str
    message: str

class RAGChatResponse(BaseModel):
    response: str
    sources: List[str] = Field(default=[])

class ScoreBreakdown(BaseModel):
    required_skills: int = Field(default=0)
    preferred_skills: int = Field(default=0)
    semantic_match: int = Field(default=0)
    experience: int = Field(default=0)
    projects: int = Field(default=0)
    ats: int = Field(default=0)
    education: int = Field(default=0)

    @field_validator("required_skills", "preferred_skills", "semantic_match", "experience", "projects", "ats", "education", mode="before")
    @classmethod
    def normalize_score_int(cls, v):
        if v is None:
            return 0
        try:
            return int(round(float(v)))
        except (ValueError, TypeError):
            return 0

class SkillsAnalysis(BaseModel):
    strong_matches: List[RequirementEvaluation] = Field(default=[])
    partial_matches: List[RequirementEvaluation] = Field(default=[])
    missing_skills: List[RequirementEvaluation] = Field(default=[])

class ATSAnalysis(BaseModel):
    score: int = Field(default=100)
    issues: List[str] = Field(default=[])

    @field_validator("score", mode="before")
    @classmethod
    def normalize_ats_score(cls, v):
        if v is None:
            return 100
        try:
            return int(round(float(v)))
        except (ValueError, TypeError):
            return 100

    @field_validator("issues", mode="before")
    @classmethod
    def normalize_ats_issues(cls, v):
        if not isinstance(v, list):
            return [str(v)] if v else []
        return [str(x) for x in v if str(x).strip()]

class AnalysisResponse(BaseModel):
    id: str
    resume_id: int
    jd_id: int
    overall_score: int
    scores_breakdown: ScoreBreakdown
    skills_analysis: SkillsAnalysis
    ats_analysis: ATSAnalysis
    recommendations: List[str] = Field(default=[])
    interview_questions: List[str] = Field(default=[])
    created_at: datetime = Field(default_factory=datetime.now)
    resume_name: Optional[str] = Field(default="Candidate Profile")
    resume_summary: Optional[str] = Field(default="")
    resume_extract: ResumeExtract = Field(default_factory=ResumeExtract)
    jd_title: Optional[str] = Field(default="Target Position")
    jd_company: Optional[str] = Field(default="")
    jd_requirements: List[JDRequirementItem] = Field(default=[])

    @field_validator("overall_score", mode="before")
    @classmethod
    def normalize_overall_score(cls, v):
        if v is None:
            return 0
        try:
            return int(round(float(v)))
        except (ValueError, TypeError):
            return 0

    @field_validator("recommendations", "interview_questions", mode="before")
    @classmethod
    def normalize_list_strings(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, (list, dict)):
                    return cls.normalize_list_strings(parsed)
            except Exception:
                pass
            lines = [line.strip() for line in v.splitlines() if line.strip()]
            return lines if lines else [v.strip()]
        if isinstance(v, dict):
            flat = []
            for key, val in v.items():
                if isinstance(val, (dict, list)):
                    flat.extend(cls.normalize_list_strings(val))
                elif val is not None:
                    flat.append(f"{key}: {str(val).strip()}")
            return flat
        if not isinstance(v, list):
            return [str(v).strip()]
        flat = []
        for item in v:
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
                    for key, val in item.items():
                        if isinstance(val, (dict, list)):
                            flat.append(f"{key}: {val}")
                        else:
                            flat.append(f"{key}: {str(val).strip()}")
            elif isinstance(item, list):
                flat.extend(cls.normalize_list_strings(item))
            elif item is not None:
                flat.append(str(item).strip())
        return flat

    class Config:
        from_attributes = True

class AnalysisHistoryItem(BaseModel):
    id: str
    resume_filename: str
    jd_title: str
    jd_company: str
    overall_score: int
    created_at: datetime

    @field_validator("overall_score", mode="before")
    @classmethod
    def normalize_history_score(cls, v):
        if v is None:
            return 0
        try:
            return int(round(float(v)))
        except (ValueError, TypeError):
            return 0
