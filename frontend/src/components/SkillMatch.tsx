import React from "react";
import type { SkillsAnalysis, RequirementEvaluation } from "../services/api";
import { CheckCircle2, AlertCircle, XCircle, PieChart } from "lucide-react";

interface SkillMatchProps {
  skillsAnalysis: SkillsAnalysis;
  onSelectSkill: (evaluation: RequirementEvaluation) => void;
}

export const SkillMatch: React.FC<SkillMatchProps> = ({ skillsAnalysis, onSelectSkill }) => {
  const { strong_matches, partial_matches, missing_skills } = skillsAnalysis;

  const total = strong_matches.length + partial_matches.length + missing_skills.length;
  const strongPct = total > 0 ? Math.round((strong_matches.length / total) * 100) : 0;
  const partialPct = total > 0 ? Math.round((partial_matches.length / total) * 100) : 0;
  const missingPct = total > 0 ? 100 - strongPct - partialPct : 0;

  const sections = [
    {
      title: "Strong Matches",
      items: strong_matches,
      color: "text-emerald-400 font-mono uppercase tracking-wider text-[10px] font-bold",
      bgColor: "bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300",
      borderColor: "border-emerald-500/30",
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />
    },
    {
      title: "Partial Matches",
      items: partial_matches,
      color: "text-amber-400 font-mono uppercase tracking-wider text-[10px] font-bold",
      bgColor: "bg-amber-500/10 hover:bg-amber-500/20 text-amber-300",
      borderColor: "border-amber-500/30",
      icon: <AlertCircle className="w-4 h-4 text-amber-400" />
    },
    {
      title: "Missing Skills",
      items: missing_skills,
      color: "text-rose-400 font-mono uppercase tracking-wider text-[10px] font-bold",
      bgColor: "bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border-dashed",
      borderColor: "border-rose-500/30",
      icon: <XCircle className="w-4 h-4 text-rose-400" />
    }
  ];

  return (
    <div className="space-y-6">
      {/* Visual Skill Proportion Bar */}
      <div className="glass-panel p-5 rounded-xl border border-border bg-black/40 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <PieChart className="w-4 h-4 text-brandYellow" />
            <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider font-mono">Skill Match Breakdown</h3>
          </div>
          <span className="text-xs font-mono text-textSecondary">{total} Total Requirements</span>
        </div>

        {/* Multi-segment Segmented Bar Graph */}
        <div className="h-3 w-full bg-black border border-border rounded-full overflow-hidden flex">
          <div style={{ width: `${strongPct}%` }} className="bg-emerald-500 h-full transition-all duration-700" title={`Strong Matches: ${strongPct}%`} />
          <div style={{ width: `${partialPct}%` }} className="bg-amber-400 h-full transition-all duration-700" title={`Partial Matches: ${partialPct}%`} />
          <div style={{ width: `${missingPct}%` }} className="bg-rose-500 h-full transition-all duration-700" title={`Missing Skills: ${missingPct}%`} />
        </div>

        <div className="flex items-center justify-between text-[11px] font-mono pt-1 text-textSecondary">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
            <span>Strong: {strong_matches.length} ({strongPct}%)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
            <span>Partial: {partial_matches.length} ({partialPct}%)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
            <span>Missing: {missing_skills.length} ({missingPct}%)</span>
          </div>
        </div>
      </div>

      {/* Skill Category Lists */}
      {sections.map((section, idx) => (
        <div key={idx} className="glass-panel p-5 rounded-xl border border-border bg-black/40">
          <div className="flex items-center space-x-2 mb-3">
            {section.icon}
            <h3 className={`text-xs font-semibold ${section.color}`}>{section.title}</h3>
            <span className="text-[10px] text-zinc-400 bg-zinc-900 border border-zinc-800 px-2 py-0.5 rounded font-mono">
              {section.items.length}
            </span>
          </div>

          {section.items.length === 0 ? (
            <p className="text-xs text-textSecondary italic">No skills in this category.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {section.items.map((item, itemIdx) => (
                <button
                  key={itemIdx}
                  onClick={() => onSelectSkill(item)}
                  className={`px-3 py-1.5 rounded-lg border text-xs font-medium flex items-center space-x-1.5 transition-all ${section.bgColor} ${section.borderColor}`}
                >
                  <span>{item.requirement}</span>
                  {item.status !== "missing" && (
                    <span className="text-[10px] text-textSecondary opacity-80 font-mono">
                      {(parseFloat(item.confidence) * 100).toFixed(0)}%
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
