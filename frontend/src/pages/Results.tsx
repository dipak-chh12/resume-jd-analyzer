import React, { useState } from "react";
import type { AnalysisResponse, RequirementEvaluation } from "../services/api";
import { MatchScore } from "../components/MatchScore";
import { SkillMatch } from "../components/SkillMatch";
import { EvidencePanel } from "../components/EvidencePanel";
import { ATSAnalysis } from "../components/ATSAnalysis";
import { Recommendations } from "../components/Recommendations";
import { RAGChat } from "../components/RAGChat";
import { RadarChart } from "../components/RadarChart";
import { 
  Award, BriefcaseBusiness, Fingerprint, FolderKanban, GraduationCap, HelpCircle, KeyRound, Sparkles, Activity
} from "lucide-react";

interface ResultsProps {
  analysis: AnalysisResponse;
  activeTab: "overview" | "resume" | "skills" | "ats" | "suggestions" | "chat" | "questions";
}

const calculateDomainScores = (analysis: AnalysisResponse) => {
  const allSkills = [
    ...(analysis.resume_extract.skills || []),
    ...analysis.skills_analysis.strong_matches.map(s => s.requirement),
    ...analysis.skills_analysis.partial_matches.map(s => s.requirement)
  ].map(s => s.toLowerCase());

  const missing = analysis.skills_analysis.missing_skills.map(s => s.requirement.toLowerCase());

  const computeDomain = (keywords: string[]) => {
    const matched = keywords.filter(k => allSkills.some(s => s.includes(k)));
    const missed = keywords.filter(k => missing.some(s => s.includes(k)));
    const denom = matched.length + missed.length;
    if (denom === 0) return matched.length > 0 ? 85 : 60;
    return Math.round(Math.min(100, Math.max(25, (matched.length / denom) * 100)));
  };

  return [
    { label: "Languages & Core", score: computeDomain(["python", "c++", "sql", "javascript", "typescript", "java", "c#"]) },
    { label: "Frameworks & Libs", score: computeDomain(["fastapi", "react", "next.js", "django", "flask", "pytorch", "langchain"]) },
    { label: "Cloud & DevOps", score: computeDomain(["aws", "docker", "kubernetes", "gcp", "azure", "git", "github", "ci/cd"]) },
    { label: "AI/ML & GenAI", score: computeDomain(["llm", "rag", "genai", "embeddings", "vectordb", "nlp", "deep learning", "machine learning"]) },
    { label: "Databases & Storage", score: computeDomain(["postgresql", "mysql", "mongodb", "redis", "qdrant", "supabase", "rdbms"]) },
    { label: "Architecture & Design", score: computeDomain(["rest api", "system design", "microservices", "oops", "data structures", "dbms"]) },
  ];
};

const getResumeKeywords = (analysis: AnalysisResponse) => {
  const skillWords = analysis.resume_extract.skills || [];
  const jdWords = analysis.jd_requirements?.map((item) => item.skill) || [];
  const evidenceWords = [
    ...analysis.skills_analysis.strong_matches,
    ...analysis.skills_analysis.partial_matches
  ].flatMap((item) => [item.requirement, ...item.evidence]);

  return Array.from(
    new Set(
      [...skillWords, ...jdWords, ...evidenceWords]
        .flatMap((value) => value.split(/[,;/|•\n]/))
        .map((value) => value.trim())
        .filter((value) => value.length > 2 && value.length < 42)
    )
  ).slice(0, 28);
};

const EmptyState = ({ label }: { label: string }) => (
  <div className="border border-dashed border-border bg-black/15 px-4 py-3 text-xs text-textSecondary rounded-lg">
    {label}
  </div>
);

const ResumeIntelligence = ({ analysis }: { analysis: AnalysisResponse }) => {
  const resume = analysis.resume_extract;
  const keywords = getResumeKeywords(analysis);
  const stats = [
    { label: "Extracted Skills", value: resume.skills.length },
    { label: "Key Projects", value: resume.projects.length },
    { label: "Work History Roles", value: resume.experience.length },
    { label: "Years Experience", value: resume.years_of_experience || 0 }
  ];

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {stats.map((stat) => (
          <div key={stat.label} className="glass-panel border border-border p-4 rounded-xl bg-black/40">
            <p className="text-[10px] uppercase tracking-widest text-textSecondary font-mono">{stat.label}</p>
            <p className="mt-2 text-2xl font-black text-textPrimary font-mono">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 items-start">
        <section className="xl:col-span-7 glass-panel border border-border rounded-xl p-5 bg-black/40">
          <div className="flex items-center gap-2 mb-4">
            <BriefcaseBusiness className="w-4 h-4 text-brandYellow" />
            <h3 className="text-sm font-bold text-textPrimary uppercase tracking-wider font-mono">Experience Timeline</h3>
          </div>
          {resume.experience.length === 0 ? (
            <EmptyState label="No experience entries were detected in the resume." />
          ) : (
            <div className="space-y-4">
              {resume.experience.map((item, idx) => (
                <article key={`${item.company}-${idx}`} className="border-l-2 border-brandYellow/50 pl-4 py-1">
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-1">
                    <div>
                      <h4 className="text-sm font-semibold text-textPrimary">{item.job_title}</h4>
                      <p className="text-xs text-textSecondary">{item.company}</p>
                    </div>
                    {item.duration && (
                      <span className="text-[10px] uppercase tracking-wider text-brandYellow font-mono bg-brandYellow/10 border border-brandYellow/20 px-2 py-0.5 rounded">{item.duration}</span>
                    )}
                  </div>
                  <ul className="mt-3 space-y-2">
                    {item.responsibilities.slice(0, 5).map((responsibility, responsibilityIdx) => (
                      <li key={responsibilityIdx} className="text-xs leading-relaxed text-textSecondary flex items-start gap-2">
                        <span className="text-brandYellow mt-1">•</span>
                        <span>{responsibility}</span>
                      </li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          )}
        </section>

        <div className="xl:col-span-5 space-y-5">
          <section className="glass-panel border border-border rounded-xl p-5 bg-black/40">
            <div className="flex items-center gap-2 mb-4">
              <Fingerprint className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-textPrimary uppercase tracking-wider font-mono">Parsed Technical Skills</h3>
            </div>
            {resume.skills.length === 0 ? (
              <EmptyState label="No skills were extracted." />
            ) : (
              <div className="flex flex-wrap gap-2">
                {resume.skills.map((skill) => (
                  <span key={skill} className="px-3 py-1.5 border border-border bg-black/40 text-xs text-textPrimary rounded-lg">
                    {skill}
                  </span>
                ))}
              </div>
            )}
          </section>

          <section className="glass-panel border border-border rounded-xl p-5 bg-black/40">
            <div className="flex items-center gap-2 mb-4">
              <KeyRound className="w-4 h-4 text-brandYellow" />
              <h3 className="text-sm font-bold text-textPrimary uppercase tracking-wider font-mono">Verified Keywords</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {keywords.map((keyword) => (
                <span key={keyword} className="px-2.5 py-1 border border-brandYellow/20 bg-brandYellow/10 text-[11px] text-textPrimary rounded-lg">
                  {keyword}
                </span>
              ))}
            </div>
          </section>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <section className="glass-panel border border-border rounded-xl p-5 lg:col-span-2 bg-black/40">
          <div className="flex items-center gap-2 mb-4">
            <FolderKanban className="w-4 h-4 text-brandYellow" />
            <h3 className="text-sm font-bold text-textPrimary uppercase tracking-wider font-mono">Projects Showcase</h3>
          </div>
          {resume.projects.length === 0 ? (
            <EmptyState label="No project section was detected." />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {resume.projects.map((project, idx) => (
                <article key={`${project.name}-${idx}`} className="border border-border bg-black/40 p-4 rounded-xl">
                  <h4 className="text-sm font-semibold text-textPrimary">{project.name}</h4>
                  <p className="mt-2 text-xs leading-relaxed text-textSecondary">{project.description}</p>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {project.technologies.map((tech) => (
                      <span key={tech} className="text-[10px] text-brandYellow border border-brandYellow/20 bg-brandYellow/10 px-2 py-0.5 rounded">
                        {tech}
                      </span>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="glass-panel border border-border rounded-xl p-5 bg-black/40">
          <div className="flex items-center gap-2 mb-4">
            <GraduationCap className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-bold text-textPrimary uppercase tracking-wider font-mono">Education & Proof</h3>
          </div>
          <div className="space-y-4">
            {resume.education.length === 0 ? <EmptyState label="No education details were detected." /> : resume.education.map((item, idx) => (
              <div key={`${item.institution}-${idx}`} className="border-b border-border pb-3 last:border-b-0 last:pb-0">
                <p className="text-sm font-semibold text-textPrimary">{item.degree}</p>
                <p className="text-xs text-textSecondary">{item.institution}{item.year ? `, ${item.year}` : ""}</p>
              </div>
            ))}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Award className="w-4 h-4 text-brandYellow" />
                <p className="text-xs font-bold uppercase tracking-wider text-textSecondary font-mono">Certifications</p>
              </div>
              {resume.certifications.length === 0 ? <EmptyState label="No certifications were detected." /> : (
                <div className="space-y-2">
                  {resume.certifications.map((certification) => (
                    <p key={certification} className="text-xs text-textPrimary border border-border bg-black/40 px-3 py-2 rounded-lg">{certification}</p>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export const Results: React.FC<ResultsProps> = ({ analysis, activeTab }) => {
  const [selectedSkill, setSelectedSkill] = useState<RequirementEvaluation | null>(null);

  const handleSelectSkill = (evaluation: RequirementEvaluation) => {
    setSelectedSkill(evaluation);
  };

  const domainScores = calculateDomainScores(analysis);

  return (
    <div className="space-y-6">
      {/* Profile Header Card */}
      <div className="glass-panel p-6 rounded-xl border border-border shadow-2xl grid grid-cols-1 lg:grid-cols-12 gap-5 items-center bg-black/40">
        <div className="min-w-0 lg:col-span-9">
          <span className="text-[9px] font-bold text-zinc-500 font-mono uppercase tracking-widest block mb-1.5">
            Verified Candidate Analysis Report
          </span>
          <h2 className="text-2xl font-extrabold text-textPrimary truncate leading-tight">
            {analysis.resume_name && analysis.resume_name !== "None" ? analysis.resume_name : "Candidate Profile"}
          </h2>
          <p className="text-xs text-textSecondary truncate mt-1">
            Target Role: <span className="text-white font-semibold">{analysis.jd_title && analysis.jd_title !== "None" ? analysis.jd_title : "Target Position"}</span> {analysis.jd_company && analysis.jd_company !== "None" ? `• ${analysis.jd_company}` : ""}
          </p>
          {analysis.resume_summary && (
            <p className="text-xs text-textSecondary mt-3 leading-relaxed border-t border-border pt-3 italic">
              "{analysis.resume_summary}"
            </p>
          )}
        </div>

        {/* Floating summary match score indicator */}
        <div className="lg:col-span-3 flex items-center justify-between gap-3 bg-brandYellow/10 border border-brandYellow/20 px-5 py-4 rounded-xl">
          <div className="text-right">
            <span className="text-[10px] text-textSecondary uppercase tracking-widest font-mono block">Overall Match</span>
            <span className="text-3xl font-black text-textPrimary font-mono">{analysis.overall_score}%</span>
          </div>
          <Sparkles className="w-6 h-6 text-brandYellow" />
        </div>
      </div>

      {/* Main Grid Content */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left/Main Column depending on tab content */}
        <div className={`${selectedSkill ? "lg:col-span-7" : "lg:col-span-12"} space-y-6 transition-all`}>
          
          {activeTab === "overview" && (
            <div className="space-y-6">
              {/* Summary Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  ["Overall Fit", `${analysis.overall_score}%`],
                  ["Strong Matches", analysis.skills_analysis.strong_matches.length],
                  ["Partial Fits", analysis.skills_analysis.partial_matches.length],
                  ["Skill Gaps", analysis.skills_analysis.missing_skills.length],
                ].map(([label, value]) => (
                  <div key={label} className="border border-border bg-black/40 p-4 rounded-xl">
                    <p className="text-xs text-textSecondary uppercase font-mono">{label}</p>
                    <p className="text-2xl font-black text-textPrimary mt-2 font-mono">{value}</p>
                  </div>
                ))}
              </div>

              {/* Match Score & Progress Bar breakdown */}
              <div className="glass-panel p-6 rounded-xl border border-border bg-black/40">
                <MatchScore score={analysis.overall_score} breakdown={analysis.scores_breakdown} />
              </div>

              {/* Radar Chart & Experience Comparison Grid */}
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-stretch">
                <div className="md:col-span-7">
                  <RadarChart categories={domainScores} title="6-Domain Skill Radar Map" />
                </div>

                <div className="md:col-span-5 glass-panel p-5 rounded-xl border border-border bg-black/40 flex flex-col justify-between space-y-4">
                  <div className="flex items-center gap-2 border-b border-border pb-3">
                    <Activity className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider font-mono">Role Fit Indicators</h3>
                  </div>

                  <div className="space-y-4">
                    <div className="p-3.5 bg-black border border-border/80 rounded-lg text-xs space-y-1.5">
                      <div className="flex justify-between font-mono text-[11px] text-textSecondary">
                        <span>Experience Requirement</span>
                        <span className="text-textPrimary font-bold">{analysis.scores_breakdown.experience}% Fit</span>
                      </div>
                      <p className="text-[11px] text-textSecondary leading-relaxed">
                        Candidate brings <strong className="text-textPrimary">{analysis.resume_extract.years_of_experience || 0} years</strong> vs role requirements.
                      </p>
                    </div>

                    <div className="p-3.5 bg-black border border-border/80 rounded-lg text-xs space-y-1.5">
                      <div className="flex justify-between font-mono text-[11px] text-textSecondary">
                        <span>ATS Compliance Rating</span>
                        <span className="text-emerald-400 font-bold">{analysis.ats_analysis.score}/100</span>
                      </div>
                      <p className="text-[11px] text-textSecondary leading-relaxed">
                        {analysis.ats_analysis.issues.length === 0 ? "Format fully compliant with ATS automated parsers." : `${analysis.ats_analysis.issues.length} minor formatting warnings detected.`}
                      </p>
                    </div>

                    <div className="p-3.5 bg-black border border-border/80 rounded-lg text-xs space-y-1.5">
                      <div className="flex justify-between font-mono text-[11px] text-textSecondary">
                        <span>Project Technical Alignment</span>
                        <span className="text-brandYellow font-bold">{analysis.scores_breakdown.projects}%</span>
                      </div>
                      <p className="text-[11px] text-textSecondary leading-relaxed">
                        {analysis.resume_extract.projects.length} project portfolio items analyzed.
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Recommendations & Education */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Recommendations recommendations={analysis.recommendations.slice(0, 4)} />
                <div className="glass-panel p-6 rounded-xl border border-border bg-black/40 space-y-4">
                  <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider font-mono flex items-center space-x-2">
                    <GraduationCap className="w-4 h-4 text-emerald-400" />
                    <span>Education Requirements</span>
                  </h3>
                  <div className="p-4 bg-black border border-border rounded-lg text-xs leading-relaxed text-textSecondary space-y-2">
                    <p><span className="text-white font-semibold">JD Requirements: </span>{analysis.scores_breakdown.education >= 80 ? "Matched Qualifications successfully" : "Partial match on educational background"}</p>
                    {analysis.resume_extract.education.length > 0 && (
                      <p className="text-[11px] text-zinc-400 font-mono">
                        Degree: {analysis.resume_extract.education[0].degree} ({analysis.resume_extract.education[0].institution})
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "resume" && (
            <ResumeIntelligence analysis={analysis} />
          )}

          {activeTab === "skills" && (
            <div>
              <div className="mb-4">
                <h3 className="text-base font-bold text-white">Skills Matrix Breakdown</h3>
                <p className="text-xs text-textSecondary mt-0.5">
                  Click any skill below to retrieve exact evidence passages from your resume.
                </p>
              </div>
              <SkillMatch
                skillsAnalysis={analysis.skills_analysis}
                onSelectSkill={handleSelectSkill}
              />
            </div>
          )}

          {activeTab === "ats" && (
            <div className="glass-panel p-5 rounded-xl border border-border bg-black/40">
              <ATSAnalysis atsData={analysis.ats_analysis} />
            </div>
          )}

          {activeTab === "suggestions" && (
            <Recommendations recommendations={analysis.recommendations} />
          )}

          {activeTab === "chat" && (
            <RAGChat analysisId={analysis.id} />
          )}

          {activeTab === "questions" && (
            <div className="glass-panel p-6 rounded-xl border border-border bg-black/40">
              <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider font-mono mb-4 flex items-center space-x-2">
                <HelpCircle className="w-4 h-4 text-brandYellow" />
                <span>Custom Tailored Interview Questions</span>
              </h3>
              <div className="space-y-4">
                {analysis.interview_questions.map((q, idx) => (
                  <div
                    key={idx}
                    className="p-4 bg-black border border-border rounded-xl text-xs text-textSecondary leading-relaxed border-l-4 border-l-brandYellow shadow-sm"
                  >
                    {q}
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

        {/* Evidence Side Panel (shown on skill selection click) */}
        {selectedSkill && (() => {
          const match = analysis.jd_requirements?.find(r => {
            const s1 = r.skill.toLowerCase();
            const s2 = selectedSkill.requirement.toLowerCase();
            return s1.includes(s2) || s2.includes(s1);
          });
          return (
            <div className="lg:col-span-5 lg:sticky lg:top-6 transition-all">
              <EvidencePanel
                selectedSkill={selectedSkill}
                sourceText={match?.source_text}
                onClose={() => setSelectedSkill(null)}
              />
            </div>
          );
        })()}
      </div>
    </div>
  );
};
