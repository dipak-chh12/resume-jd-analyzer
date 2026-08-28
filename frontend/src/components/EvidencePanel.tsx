import React from "react";
import type { RequirementEvaluation } from "../services/api";
import { X, Award, Percent, BookOpen, Quote } from "lucide-react";

interface EvidencePanelProps {
  selectedSkill: RequirementEvaluation | null;
  sourceText?: string;
  onClose: () => void;
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ selectedSkill, sourceText, onClose }) => {
  if (!selectedSkill) return null;

  const { requirement, status, similarity, confidence, evidence, explanation } = selectedSkill;

  const getStatusColor = (s: string) => {
    switch (s) {
      case "strong_match":
        return { text: "Strong Match", class: "text-white bg-zinc-900 border-zinc-700" };
      case "partial_match":
      case "weak_match":
        return { text: "Partial Match", class: "text-zinc-300 bg-zinc-950 border-zinc-800" };
      default:
        return { text: "Missing Skill", class: "text-zinc-500 bg-black border-zinc-800 border-dashed" };
    }
  };

  const statusInfo = getStatusColor(status);

  return (
    <div className="glass-panel p-6 rounded-lg border border-border relative shadow-lg">
      {/* Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <h4 className="text-xs text-textSecondary uppercase tracking-wider font-semibold font-mono">
            Requirement Evidence
          </h4>
          <h3 className="text-xl font-bold text-white mt-1">{requirement}</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 hover:bg-white/5 rounded-full text-textSecondary hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Badges */}
      <div className="flex flex-wrap gap-2.5 mb-5">
        <span className={`px-2.5 py-1 rounded text-xs font-semibold border ${statusInfo.class}`}>
          {statusInfo.text}
        </span>
        {status !== "missing" && (
          <>
            <span className="px-2.5 py-1 rounded text-xs font-mono bg-zinc-950 border border-zinc-850 text-zinc-400 flex items-center space-x-1">
              <Award className="w-3.5 h-3.5 text-zinc-400" />
              <span>Confidence: {(parseFloat(confidence) * 100).toFixed(0)}%</span>
            </span>
            <span className="px-2.5 py-1 rounded text-xs font-mono bg-zinc-950 border border-zinc-850 text-zinc-400 flex items-center space-x-1">
              <Percent className="w-3.5 h-3.5 text-zinc-400" />
              <span>Similarity: {(parseFloat(similarity) * 100).toFixed(0)}%</span>
            </span>
          </>
        )}
      </div>

      {/* JD Source Text Citation */}
      {sourceText && (
        <div className="mb-5 p-3.5 bg-white/[0.02] border border-border rounded-lg">
          <h5 className="text-[10px] font-bold text-textSecondary uppercase tracking-wider mb-1.5 flex items-center space-x-1 font-mono">
            <Quote className="w-3 h-3 text-zinc-500" />
            <span>Job Description Citation</span>
          </h5>
          <p className="text-xs text-textSecondary leading-relaxed italic">
            "{sourceText}"
          </p>
        </div>
      )}

      {/* Explanation */}
      <div className="mb-6">
        <h5 className="text-sm font-semibold text-textPrimary mb-2">Analysis Explanation</h5>
        <p className="text-sm text-textSecondary leading-relaxed">{explanation}</p>
      </div>

      {/* Evidence Chunks */}
      <div>
        <h5 className="text-sm font-semibold text-textPrimary mb-2 flex items-center space-x-2">
          <BookOpen className="w-4 h-4 text-white" />
          <span>Retrieved Resume Context</span>
        </h5>
        
        {evidence.length === 0 ? (
          <div className="p-4 bg-zinc-950 border border-border rounded-lg text-sm text-textSecondary italic">
            No relevant evidence found in the resume.
          </div>
        ) : (
          <div className="space-y-3">
            {evidence.map((chunk, idx) => (
              <div
                key={idx}
                className="p-4 bg-zinc-950 border border-border rounded-lg text-sm text-textSecondary leading-relaxed relative overflow-hidden shadow-inner font-sans border-l-2 border-l-white"
              >
                {/* Clean out segment tags if visible */}
                <span className="whitespace-pre-wrap">
                  {chunk.replace(/^(Work Experience|Project|Education):\s*/, "")}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
