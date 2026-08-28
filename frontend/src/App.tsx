import { useState } from "react";
import { Analyze } from "./pages/Analyze";
import { Results } from "./pages/Results";
import { HistoryPage } from "./pages/History";
import { api } from "./services/api";
import type { AnalysisResponse } from "./services/api";
import {
  BarChart3, BrainCircuit, FileText, History,
  LayoutDashboard, Loader, MessageSquare, Plus, ShieldAlert, Sparkles,
} from "lucide-react";

type PageType = "analyze" | "history" | "report-overview" | "report-resume" | "report-skills" | "report-ats" | "report-suggestions" | "report-questions" | "report-chat";

const reportTabs = [
  { id: "report-overview", label: "Dashboard", icon: LayoutDashboard },
  { id: "report-resume", label: "Resume data", icon: FileText },
  { id: "report-skills", label: "Skills", icon: BrainCircuit },
  { id: "report-ats", label: "ATS", icon: ShieldAlert },
  { id: "report-suggestions", label: "Suggestions", icon: Sparkles },
  { id: "report-questions", label: "Interview", icon: MessageSquare },
  { id: "report-chat", label: "Ask Assistant", icon: BarChart3 },
];

function App() {
  const [currentPage, setCurrentPage] = useState<PageType>("analyze");
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResponse | null>(null);
  const [loadingHistoryItem, setLoadingHistoryItem] = useState(false);
  const [navError, setNavError] = useState<string | null>(null);

  const navigateToNewScan = () => {
    setCurrentAnalysis(null);
    setNavError(null);
    setCurrentPage("analyze");
  };

  const handleSelectHistoryAnalysis = async (id: string) => {
    setLoadingHistoryItem(true);
    setNavError(null);
    try {
      const report = await api.getAnalysis(id);
      setCurrentAnalysis(report);
      setCurrentPage("report-overview");
    } catch (err: any) {
      setNavError(err.message || "Failed to load the selected analysis.");
    } finally {
      setLoadingHistoryItem(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-textPrimary flex flex-col justify-between">
      <div>
        <header className="border-b border-border bg-card/90 sticky top-0 z-40 backdrop-blur-md">
          <div className="max-w-[1240px] mx-auto px-5 md:px-8 h-16 flex items-center justify-between gap-6">
            <button onClick={navigateToNewScan} className="flex items-center gap-2.5 group" aria-label="Resume JD Matcher home">
              <span className="w-7 h-7 rounded-lg bg-brandYellow text-background flex items-center justify-center font-bold text-sm">
                <BrainCircuit className="w-4 h-4" />
              </span>
              <span className="text-base font-bold tracking-tight text-textPrimary group-hover:text-brandYellow transition-colors">
                Resume JD Matcher
              </span>
              <span className="hidden sm:inline-block text-[11px] font-medium text-textSecondary bg-white/[0.06] border border-white/10 px-2 py-0.5 rounded-full">
                RAG Engine
              </span>
            </button>

            <div className="flex items-center gap-2">
              <button onClick={() => { setNavError(null); setCurrentPage("history"); }} className="h-9 px-3 rounded-lg text-xs font-medium text-textSecondary hover:text-textPrimary hover:bg-white/[0.06] transition-colors flex items-center gap-2">
                <History className="w-4 h-4" />
                <span className="hidden sm:inline">History</span>
              </button>
              <button onClick={navigateToNewScan} className="h-9 px-3.5 rounded-lg bg-brandYellow text-background text-xs font-semibold hover:bg-white transition-colors flex items-center gap-2">
                <Plus className="w-4 h-4" />
                <span>New scan</span>
              </button>
            </div>
          </div>

          {currentAnalysis && currentPage.startsWith("report-") && (
            <div className="max-w-[1240px] mx-auto px-5 md:px-8 border-t border-border overflow-x-auto">
              <nav className="h-12 flex items-center gap-1 min-w-max" aria-label="Report sections">
                {reportTabs.map(({ id, label, icon: Icon }) => (
                  <button
                    key={id}
                    onClick={() => setCurrentPage(id as PageType)}
                    className={`h-8 px-3 rounded-md text-xs font-medium flex items-center gap-2 transition-colors ${currentPage === id ? "bg-white/[0.1] text-textPrimary" : "text-textSecondary hover:text-textPrimary hover:bg-white/[0.05]"}`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {label}
                  </button>
                ))}
              </nav>
            </div>
          )}
        </header>

        <main className="max-w-[1240px] mx-auto px-5 md:px-8 py-8 md:py-10">
          {navError && <div className="max-w-xl mx-auto mb-6 p-3 rounded-lg bg-brandRed/10 border border-brandRed/30 text-brandRed text-sm">{navError}</div>}
          {loadingHistoryItem ? (
            <div className="flex flex-col items-center justify-center py-24 gap-3">
              <Loader className="w-5 h-5 text-brandYellow animate-spin" />
              <p className="text-sm text-textSecondary">Loading analysis...</p>
            </div>
          ) : (
            <>
              {currentPage === "analyze" && <Analyze onAnalysisComplete={(res) => { setCurrentAnalysis(res); setCurrentPage("report-overview"); }} />}
              {currentPage === "history" && <HistoryPage onSelectAnalysis={handleSelectHistoryAnalysis} />}
              {currentPage.startsWith("report-") && currentAnalysis && <Results analysis={currentAnalysis} activeTab={currentPage.replace("report-", "") as any} />}
            </>
          )}
        </main>
      </div>

      <footer className="border-t border-border/80 bg-black/40 backdrop-blur-sm mt-12">
        <div className="max-w-[1240px] mx-auto px-5 md:px-8 py-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-textSecondary">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-textPrimary">Resume JD Matcher</span>
            <span>•</span>
            <span>Intelligent AI Matcher</span>
          </div>

          <div className="flex items-center gap-3">
            <span>by <strong className="text-textPrimary font-semibold">DIPXML</strong></span>
            <a
              href="https://x.com/DIPXML"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/[0.06] hover:bg-white/[0.12] border border-white/10 text-brandYellow hover:text-white font-medium transition-all group"
            >
              <span>@DIPXML</span>
              <span className="text-[10px] opacity-70 group-hover:translate-x-0.5 transition-transform">↗</span>
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
