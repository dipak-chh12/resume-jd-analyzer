import React from "react";
import type { ScoreBreakdown } from "../services/api";
import { Sparkles, ShieldCheck, Zap, BookOpen, Briefcase, FileCode, CheckCircle2 } from "lucide-react";

interface MatchScoreProps {
  score: number;
  breakdown: ScoreBreakdown;
}

export const MatchScore: React.FC<MatchScoreProps> = ({ score, breakdown }) => {
  const metrics = [
    { label: "Required Skills", value: breakdown.required_skills, icon: <Zap className="w-3.5 h-3.5 text-brandYellow" /> },
    { label: "Preferred Skills", value: breakdown.preferred_skills, icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> },
    { label: "Semantic Alignment", value: breakdown.semantic_match, icon: <Sparkles className="w-3.5 h-3.5 text-sky-400" /> },
    { label: "Work Experience", value: breakdown.experience, icon: <Briefcase className="w-3.5 h-3.5 text-amber-400" /> },
    { label: "Project Relevance", value: breakdown.projects, icon: <FileCode className="w-3.5 h-3.5 text-purple-400" /> },
    { label: "ATS Readiness", value: breakdown.ats, icon: <ShieldCheck className="w-3.5 h-3.5 text-teal-400" /> },
    { label: "Education Match", value: breakdown.education, icon: <BookOpen className="w-3.5 h-3.5 text-indigo-400" /> },
  ];

  const level = score >= 80 ? "Strong Match" : score >= 55 ? "Good Match" : score >= 35 ? "Partial Match" : "Needs Optimization";
  const strokeColor = score >= 80 ? "#10b981" : score >= 55 ? "#facc15" : "#f59e0b";

  // SVG Radial Gauge Calculations
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="grid md:grid-cols-[240px_1fr] gap-8 items-center">
      {/* SVG Radial Score Meter Gauge */}
      <div className="flex flex-col items-center justify-center border-r-0 md:border-r border-border pr-0 md:pr-8 py-2">
        <div className="relative w-36 h-36 flex items-center justify-center">
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
            {/* Track Circle */}
            <circle
              cx="60"
              cy="60"
              r={radius}
              stroke="rgba(255, 255, 255, 0.08)"
              strokeWidth="10"
              fill="none"
            />
            {/* Progress Radial Arc */}
            <circle
              cx="60"
              cy="60"
              r={radius}
              stroke={strokeColor}
              strokeWidth="10"
              fill="none"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              className="transition-all duration-1000 ease-out"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
            <span className="text-4xl font-black text-textPrimary font-mono tracking-tight">{score}%</span>
            <span className="text-[10px] uppercase tracking-widest text-textSecondary font-mono mt-0.5">Match</span>
          </div>
        </div>

        <div className="mt-4 inline-flex items-center gap-2 px-3 py-1 bg-black/40 border border-border rounded-full text-xs font-medium text-textPrimary">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: strokeColor }} />
          {level}
        </div>
      </div>

      {/* Comparative Score Metric Progress Bars */}
      <div className="grid sm:grid-cols-2 gap-x-8 gap-y-4">
        {metrics.map((m) => (
          <div key={m.label} className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-2 text-textSecondary">
                {m.icon}
                {m.label}
              </span>
              <span className="font-mono font-bold text-textPrimary">{m.value}%</span>
            </div>
            <div className="h-2 bg-black/40 border border-border/60 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700 ease-out"
                style={{
                  width: `${Math.max(0, Math.min(100, m.value))}%`,
                  backgroundColor: m.value >= 80 ? "#10b981" : m.value >= 55 ? "#facc15" : "#f59e0b"
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
