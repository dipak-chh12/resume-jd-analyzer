import React from "react";
import { Sparkles, Check, AlertTriangle } from "lucide-react";

interface RecommendationsProps {
  recommendations: string[];
}

export const Recommendations: React.FC<RecommendationsProps> = ({ recommendations }) => {
  return (
    <div className="glass-panel p-6 rounded-lg border border-border">
      <h3 className="text-sm font-semibold text-textPrimary mb-4 flex items-center space-x-2">
        <Sparkles className="w-4.5 h-4.5 text-white animate-pulse" />
        <span>Actionable Optimization Guidelines</span>
      </h3>

      {recommendations.length === 0 ? (
        <p className="text-xs text-textSecondary italic">No suggestions generated.</p>
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec, idx) => {
            const isDo = rec.trim().toUpperCase().startsWith("DO:");
            const isAvoid = rec.trim().toUpperCase().startsWith("AVOID:");
            
            let displayType = "INFO";
            let displayClass = "border-zinc-800 bg-zinc-950";
            let icon = <Sparkles className="w-3.5 h-3.5 text-zinc-400" />;
            let text = rec;

            if (isDo) {
              displayType = "DO";
              displayClass = "border-zinc-800 bg-zinc-900/20";
              icon = <Check className="w-3.5 h-3.5 text-white" />;
              text = rec.substring(rec.indexOf(":") + 1).trim();
            } else if (isAvoid) {
              displayType = "AVOID";
              displayClass = "border-zinc-900 bg-black";
              icon = <AlertTriangle className="w-3.5 h-3.5 text-zinc-500" />;
              text = rec.substring(rec.indexOf(":") + 1).trim();
            }

            return (
              <div
                key={idx}
                className={`p-4 border rounded-lg flex items-start space-x-3.5 text-xs leading-relaxed transition-all ${displayClass}`}
              >
                <div className="flex-shrink-0 mt-0.5">
                  <div className="w-6 h-6 rounded-full border border-zinc-800 bg-black flex items-center justify-center">
                    {icon}
                  </div>
                </div>
                <div>
                  <span className={`inline-block font-mono text-[9px] uppercase tracking-widest font-bold px-1.5 py-0.5 rounded mb-1.5 ${
                    isDo ? "bg-white text-black" : isAvoid ? "bg-zinc-800 text-zinc-400" : "bg-zinc-900 text-zinc-500"
                  }`}>
                    {displayType}
                  </span>
                  <p className="text-textSecondary">{text}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
