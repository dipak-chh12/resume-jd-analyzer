import re
import logging
from typing import List, Dict, Any
from backend.app.schemas.analysis import ResumeExtract, ATSAnalysis

logger = logging.getLogger("app.services.ats_analyzer")

class ATSAnalyzer:
    @staticmethod
    def analyze(resume: ResumeExtract, raw_text: str) -> ATSAnalysis:
        """Scan raw resume text and structured details to assess ATS formatting compliance."""
        logger.info("Starting ATS analysis...")
        issues = []
        base_score = 100

        # 1. Contact Information Checks
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        
        has_email = bool(re.search(email_pattern, raw_text))
        has_phone = bool(re.search(phone_pattern, raw_text))
        
        if not has_email:
            issues.append("Email address not found. Ensure contact details are visible to parsers.")
            base_score -= 15
        if not has_phone:
            issues.append("Phone number not found. Ensure recruiters can reach you easily.")
            base_score -= 10

        # 2. Structural Section Checks
        text_lower = raw_text.lower()
        
        if not any(header in text_lower for header in ["experience", "work history", "employment"]):
            issues.append("Missing standard 'Experience' header. ATS systems require a clear work history section.")
            base_score -= 15
            
        if not any(header in text_lower for header in ["education", "academic", "university", "college"]):
            issues.append("Missing standard 'Education' header. Include a dedicated section for degrees.")
            base_score -= 10

        if not any(header in text_lower for header in ["skill", "technologies", "proficiencies"]):
            issues.append("Missing standard 'Skills' header. List key skills clearly for automated filters.")
            base_score -= 15

        # 3. Formatting & Parsing Hazards
        # Check for very long blocks of text (lack of bullet points/lists)
        paragraphs = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 300]
        if paragraphs:
            issues.append("Identified large paragraphs (>300 chars). Use bullet points to break up dense descriptions for readability.")
            base_score -= 10

        # Check total length (typical ATS target is 1-2 pages: roughly 400 - 1500 words)
        words = raw_text.split()
        if len(words) < 150:
            issues.append("Resume length is unusually short (under 150 words). Provide more detailed descriptions.")
            base_score -= 15
        elif len(words) > 1800:
            issues.append("Resume exceeds recommended length (over 1800 words). Condense items to keep it under 2 pages.")
            base_score -= 10

        # Check for job title formatting issues (e.g. no years or generic names)
        if not resume.experience:
            issues.append("No professional work experience details could be parsed. Verify section layout.")
            base_score -= 10

        # Normalize score
        final_score = max(min(base_score, 100), 20)
        
        logger.info(f"ATS analysis complete. Score: {final_score}/100, Issues found: {len(issues)}")
        return ATSAnalysis(
            score=final_score,
            issues=issues
        )
