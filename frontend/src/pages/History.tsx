import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import type { AnalysisHistoryItem } from "../services/api";
import { History, FileText, ArrowRight, Loader } from "lucide-react";

interface HistoryPageProps {
  onSelectAnalysis: (id: string) => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({ onSelectAnalysis }) => {
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await api.getHistory();
        setHistory(data);
      } catch (err: any) {
        setError(err.message || "Failed to load past analyses.");
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 space-y-4">
        <Loader className="w-6 h-6 text-white animate-spin" />
        <p className="text-xs text-textSecondary font-mono">Loading analysis log history...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3 mb-2">
        <History className="w-5 h-5 text-white" />
        <h2 className="text-lg font-bold font-mono tracking-widest text-white">ANALYSIS HISTORY</h2>
      </div>

      {error && (
        <div className="p-4 bg-zinc-950 border border-border text-zinc-400 rounded-lg text-xs font-mono">
          {error}
        </div>
      )}

      {history.length === 0 ? (
        <div className="glass-panel p-12 text-center rounded-xl border border-border space-y-2">
          <FileText className="w-12 h-12 text-brandYellow/40 mx-auto mb-2" />
          <p className="text-sm font-semibold text-textPrimary">No past scans yet</p>
          <p className="text-xs text-textSecondary max-w-sm mx-auto">
            Upload your resume and a job description to get your first match report. Crafted with ❤️ by <a href="https://x.com/DIPXML" target="_blank" rel="noopener noreferrer" className="text-brandYellow hover:underline">@DIPXML</a>.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {history.map((item) => (
            <div
              key={item.id}
              onClick={() => onSelectAnalysis(item.id)}
              className="glass-panel p-5 rounded-lg border border-border hover:border-zinc-700 bg-card hover:bg-card-hover cursor-pointer transition-colors flex items-center justify-between group"
            >
              <div className="space-y-1 overflow-hidden pr-4">
                <h3 className="text-sm font-bold text-white truncate">
                  {item.jd_title}
                </h3>
                <p className="text-xs text-textSecondary truncate">
                  {item.jd_company} • {item.resume_filename}
                </p>
                <p className="text-[10px] text-textSecondary opacity-60 font-mono">
                  {new Date(item.created_at).toLocaleDateString()} at{" "}
                  {new Date(item.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </p>
              </div>

              <div className="flex items-center space-x-4 flex-shrink-0">
                {/* Score badge */}
                <div className="text-right">
                  <div className="text-lg font-bold font-mono text-white">
                    {item.overall_score}%
                  </div>
                  <span className="text-[9px] text-textSecondary font-mono uppercase tracking-widest">
                    Score
                  </span>
                </div>

                <div className="p-2 bg-white/5 rounded-lg text-textSecondary group-hover:text-white group-hover:bg-white/10 transition-colors">
                  <ArrowRight className="w-4 h-4" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
