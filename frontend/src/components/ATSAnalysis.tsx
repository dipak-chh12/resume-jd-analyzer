import React from "react";
import type { ATSAnalysis as ATSDataType } from "../services/api";
import { AlertTriangle, CheckCircle2, ShieldCheck, FileCheck, Mail, FileText, Layers, Hash } from "lucide-react";

interface ATSAnalysisProps {
  atsData: ATSDataType;
}

export const ATSAnalysis: React.FC<ATSAnalysisProps> = ({ atsData }) => {
  const { score, issues } = atsData;

  const strokeColor = score >= 85 ? "#10b981" : score >= 65 ? "#facc15" : "#f43f5e";
  const radius = 46;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  // Standard ATS Verification Checklist
  const checklist = [
    { label: "Contact Info Visibility", passed: !issues.some(i => i.toLowerCase().includes("email") || i.toLowerCase().includes("phone")), icon: <Mail className="w-3.5 h-3.5" /> },
    { label: "Standard Section Headers", passed: !issues.some(i => i.toLowerCase().includes("header") || i.toLowerCase().includes("missing")), icon: <Layers className="w-3.5 h-3.5" /> },
    { label: "Length & Word Count", passed: !issues.some(i => i.toLowerCase().includes("length") || i.toLowerCase().includes("words")), icon: <Hash className="w-3.5 h-3.5" /> },
    { label: "Formatting & Bullet Length", passed: !issues.some(i => i.toLowerCase().includes("paragraphs")), icon: <FileText className="w-3.5 h-3.5" /> },
    { label: "Experience Details", passed: !issues.some(i => i.toLowerCase().includes("work experience")), icon: <FileCheck className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
        {/* Radial Health Meter */}
        <div className="md:col-span-5 glass-panel p-6 rounded-xl border border-border flex flex-col items-center justify-center text-center bg-black/40">
          <h4 className="text-xs font-bold text-textSecondary uppercase tracking-widest font-mono mb-4">
            ATS Compliance Meter
          </h4>

          <div className="relative w-36 h-36 flex items-center justify-center">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r={radius} stroke="rgba(255, 255, 255, 0.08)" strokeWidth="8" fill="none" />
              <circle
                cx="60"
                cy="60"
                r={radius}
                stroke={strokeColor}
                strokeWidth="8"
                fill="none"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-4xl font-black text-textPrimary font-mono">{score}</span>
              <span className="text-[10px] text-textSecondary uppercase font-mono">out of 100</span>
            </div>
          </div>

          <div className="mt-4 inline-flex items-center gap-2 px-3 py-1 bg-black border border-border rounded-full text-xs font-medium">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: strokeColor }} />
            {score >= 85 ? "ATS Compliant" : score >= 65 ? "Fair Compatibility" : "High Formatting Risk"}
          </div>
        </div>

        {/* ATS Verification Checklist */}
        <div className="md:col-span-7 glass-panel p-6 rounded-xl border border-border bg-black/40 space-y-4">
          <div className="flex items-center space-x-2 border-b border-border pb-3">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider font-mono">
              ATS Compliance Checklist
            </h3>
          </div>

          <div className="space-y-2.5">
            {checklist.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-2.5 bg-black/40 border border-border/80 rounded-lg text-xs">
                <span className="flex items-center gap-2.5 text-textSecondary">
                  {item.icon}
                  {item.label}
                </span>
                {item.passed ? (
                  <span className="flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                    <CheckCircle2 className="w-3 h-3" /> Pass
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-[11px] font-mono text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded">
                    <AlertTriangle className="w-3 h-3" /> Warning
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Prioritized Warnings Box */}
      <div className="glass-panel p-6 rounded-xl border border-border bg-black/40">
        <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider font-mono mb-4 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400" />
          Prioritized ATS Warnings ({issues.length})
        </h3>

        {issues.length === 0 ? (
          <div className="flex items-center space-x-3 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-300 font-mono text-xs">
            <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-400" />
            <p>No structural formatting warnings detected. Your resume matches ATS parser standards!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {issues.map((issue, idx) => (
              <div
                key={idx}
                className="flex items-start space-x-3 p-3 bg-black border border-border rounded-lg text-xs leading-relaxed"
              >
                <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                <span className="text-textSecondary">{issue}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
