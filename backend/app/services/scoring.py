import logging
from typing import List, Dict, Any
from backend.app.schemas.analysis import RequirementEvaluation, ResumeExtract, JDExtract, ScoreBreakdown

logger = logging.getLogger("app.services.scoring")

# Configurable scoring weights
SCORING_WEIGHTS = {
    "required_skills": 0.35,
    "preferred_skills": 0.15,
    "semantic_match": 0.15,
    "experience": 0.15,
    "projects": 0.10,
    "ats": 0.10
}

class MatchingEngine:
    @staticmethod
    def calculate_scores(
        evaluations: List[RequirementEvaluation],
        resume: ResumeExtract,
        jd: JDExtract,
        ats_score: int
    ) -> tuple[int, ScoreBreakdown]:
        """Calculate deterministic scores based on RAG evaluations, experience, projects, and ATS results."""
        logger.info("Running deterministic scoring calculation...")
        
        # 1. Required Skills Score (35%)
        required_reqs = [r for r in evaluations if r.requirement in [j.skill for j in jd.requirements if j.type == "required"]]
        if not required_reqs:
            required_reqs = evaluations
            
        req_score = 0.0
        if required_reqs:
            matches = {
                "strong_match": 1.0,
                "partial_match": 0.65,
                "weak_match": 0.25,
                "missing": 0.0
            }
            total_points = sum(matches.get(r.status, 0.0) for r in required_reqs)
            req_score = (total_points / len(required_reqs)) * 100.0
            
        # 2. Preferred Skills Score (15%)
        preferred_reqs = [r for r in evaluations if r.requirement in [j.skill for j in jd.requirements if j.type == "preferred"]]
        if preferred_reqs:
            matches = {
                "strong_match": 1.0,
                "partial_match": 0.65,
                "weak_match": 0.25,
                "missing": 0.0
            }
            total_points = sum(matches.get(r.status, 0.0) for r in preferred_reqs)
            pref_score = (total_points / len(preferred_reqs)) * 100.0
        else:
            # If no preferred skills are specified in the JD, mirror the required score
            pref_score = req_score
            
        # 3. Semantic Match Score (15%)
        valid_similarities = [float(r.similarity) for r in evaluations if r.status != "missing" and float(r.similarity or 0) > 0]
        if valid_similarities:
            avg_sim = sum(valid_similarities) / len(valid_similarities)
            # Scale cosine similarity (0.50 -> 70%, 0.70 -> 88%, 0.85+ -> 98%)
            scaled_sim = min(100.0, max(40.0, (avg_sim * 100.0) * 1.15))
            semantic_score = scaled_sim
        else:
            semantic_score = req_score * 0.85
            
        # 4. Experience Match Score (15%)
        req_years = jd.experience_years_required
        act_years = resume.years_of_experience
        if req_years <= 0:
            exp_score = 100.0
        else:
            exp_score = min((act_years / req_years) * 100.0, 100.0)
            
        # 5. Project Relevance Score (10%)
        proj_score = 0.0
        if resume.projects:
            jd_keywords = [r.skill.lower().strip() for r in jd.requirements if r.skill]
            matching_projects = 0
            for proj in resume.projects:
                proj_text = f"{proj.name} {proj.description} {' '.join(proj.technologies)}".lower()
                if any(k in proj_text or any(tok in proj_text for tok in k.split() if len(tok) >= 3) for k in jd_keywords if len(k) >= 2):
                    matching_projects += 1
            if matching_projects > 0:
                base = (matching_projects / len(resume.projects)) * 100.0
                proj_score = min(100.0, max(75.0, base * 1.25))
            else:
                proj_score = 50.0 if len(resume.projects) > 0 else 0.0
        else:
            proj_score = 0.0
            
        # 6. Education Score (100% if candidate has relevant degree or no strict degree requested)
        edu_score = 100.0
        if jd.education_requirements:
            jd_edu = jd.education_requirements.lower()
            cand_edu_str = " ".join([f"{e.degree} {e.institution}".lower() for e in resume.education])
            if ("phd" in jd_edu or "doctorate" in jd_edu) and not any(x in cand_edu_str for x in ["phd", "doctor"]):
                edu_score = 60.0
            elif ("master" in jd_edu or "ms" in jd_edu) and not any(x in cand_edu_str for x in ["master", "ms", "mba", "phd"]):
                edu_score = 75.0
            elif ("bachelor" in jd_edu or "bs" in jd_edu) and not any(x in cand_edu_str for x in ["bachelor", "bs", "ba", "b.tech", "be", "master", "ms"]):
                edu_score = 80.0
        elif resume.education:
            edu_score = 100.0

        # Calculate Overall Weighted Score
        breakdown = ScoreBreakdown(
            required_skills=int(round(req_score)),
            preferred_skills=int(round(pref_score)),
            semantic_match=int(round(semantic_score)),
            experience=int(round(exp_score)),
            projects=int(round(proj_score)),
            ats=ats_score,
            education=int(round(edu_score))
        )
        
        overall = (
            req_score * SCORING_WEIGHTS["required_skills"] +
            pref_score * SCORING_WEIGHTS["preferred_skills"] +
            semantic_score * SCORING_WEIGHTS["semantic_match"] +
            exp_score * SCORING_WEIGHTS["experience"] +
            proj_score * SCORING_WEIGHTS["projects"] +
            ats_score * SCORING_WEIGHTS["ats"]
        )
        
        return int(round(overall)), breakdown
