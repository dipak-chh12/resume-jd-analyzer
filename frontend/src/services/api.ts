const API_BASE_URL = "http://localhost:8000/api";

export interface ScoreBreakdown {
  required_skills: number;
  preferred_skills: number;
  semantic_match: number;
  experience: number;
  projects: number;
  ats: number;
  education: number;
}

export interface RequirementEvaluation {
  requirement: string;
  status: "strong_match" | "partial_match" | "weak_match" | "missing";
  similarity: string;
  confidence: string;
  evidence: string[];
  explanation: string;
}

export interface JDRequirementItem {
  skill: string;
  type: string;
  importance: string;
  source_text: string;
}

export interface SkillsAnalysis {
  strong_matches: RequirementEvaluation[];
  partial_matches: RequirementEvaluation[];
  missing_skills: RequirementEvaluation[];
}

export interface ATSAnalysis {
  score: number;
  issues: string[];
}

export interface ExperienceItem {
  job_title: string;
  company: string;
  duration?: string | null;
  responsibilities: string[];
}

export interface ProjectItem {
  name: string;
  description: string;
  technologies: string[];
}

export interface EducationItem {
  degree: string;
  institution: string;
  year?: string | null;
}

export interface ResumeExtract {
  name?: string | null;
  summary?: string | null;
  skills: string[];
  experience: ExperienceItem[];
  projects: ProjectItem[];
  education: EducationItem[];
  certifications: string[];
  years_of_experience: number;
}

export interface AnalysisResponse {
  id: string;
  resume_id: number;
  jd_id: number;
  overall_score: number;
  scores_breakdown: ScoreBreakdown;
  skills_analysis: SkillsAnalysis;
  ats_analysis: ATSAnalysis;
  recommendations: string[];
  interview_questions: string[];
  created_at: string;
  resume_name: string;
  resume_summary: string;
  resume_extract: ResumeExtract;
  jd_title: string;
  jd_company: string;
  jd_requirements: JDRequirementItem[];
}

export interface AnalysisHistoryItem {
  id: string;
  resume_filename: string;
  jd_title: string;
  jd_company: string;
  overall_score: number;
  created_at: string;
}

export interface ChatMessage {
  sender: "user" | "bot";
  text: string;
  sources?: string[];
}

export const api = {
  async analyze(resumeFile: File, jdText?: string, jdFile?: File): Promise<AnalysisResponse> {
    const formData = new FormData();
    formData.append("resume_file", resumeFile);

    if (jdText) {
      formData.append("jd_text", jdText);
    }
    if (jdFile) {
      formData.append("jd_file", jdFile);
    }

    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({ detail: "Analysis failed" }));
      throw new Error(errData.detail || "Server error occurred during analysis.");
    }

    return response.json();
  },

  async getAnalysis(id: string): Promise<AnalysisResponse> {
    const response = await fetch(`${API_BASE_URL}/analyze/${id}`);
    if (!response.ok) {
      throw new Error("Failed to retrieve analysis report.");
    }
    return response.json();
  },

  async getHistory(): Promise<AnalysisHistoryItem[]> {
    const response = await fetch(`${API_BASE_URL}/analyses`);
    if (!response.ok) {
      throw new Error("Failed to retrieve history logs.");
    }
    return response.json();
  },

  async sendChatMessage(analysisId: string, message: string): Promise<{ response: string; sources: string[] }> {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        analysis_id: analysisId,
        message: message,
      }),
    });

    if (!response.ok) {
      throw new Error("Chatbot failed to respond.");
    }

    return response.json();
  },
};
