import React, { useEffect, useState } from "react";
import { api } from "../services/api";
import type { AnalysisResponse } from "../services/api";
import { ResumeUpload } from "../components/ResumeUpload";
import { JDInput } from "../components/JDInput";
import { ArrowRight, Check, FileSearch, Gauge, Loader, Play, ShieldCheck, Sparkles, Target } from "lucide-react";

interface AnalyzeProps { onAnalysisComplete: (result: AnalysisResponse) => void; }

const progressSteps = [
  { title: "Reading documents & extracting plain text", icon: FileSearch, note: "Parsing PDFs without judging the font choice..." },
  { title: "Mapping role requirements with LLM", icon: Target, note: "Asking the Groq model nicely to find true requirements..." },
  { title: "Comparing your evidence in vector space", icon: Gauge, note: "Vector database is hunting for your secret superpowers..." },
  { title: "Preparing your match report & RAG insights", icon: Sparkles, note: "Polishing scores with 0% hallucination..." },
];

export const Analyze: React.FC<AnalyzeProps> = ({ onAnalysisComplete }) => {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [progressIndex, setProgressIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading) { setProgressIndex(0); return; }
    const timer = window.setInterval(() => setProgressIndex((prev) => Math.min(prev + 1, progressSteps.length - 1)), 2500);
    return () => window.clearInterval(timer);
  }, [loading]);

  const handleAnalyze = async () => {
    if (!resumeFile) { setError("Please upload your resume."); return; }
    if (!jdText && !jdFile) { setError("Please add a job description."); return; }
    setError(null); setLoading(true);
    try { onAnalysisComplete(await api.analyze(resumeFile, jdText || undefined, jdFile || undefined)); }
    catch (err: any) { setError(err.message || "An unexpected error occurred during processing."); }
    finally { setLoading(false); }
  };

  if (loading) return (
    <div className="max-w-xl mx-auto py-12">
      <div className="glass-panel rounded-2xl p-6 md:p-8 space-y-6 shadow-2xl border border-white/10">
        <div className="flex items-center gap-3 pb-5 border-b border-border">
          <div className="w-10 h-10 rounded-xl bg-brandYellow/10 border border-brandYellow/30 text-brandYellow flex items-center justify-center flex-shrink-0">
            <Loader className="w-5 h-5 animate-spin" />
          </div>
          <div>
            <p className="text-base font-semibold text-textPrimary">Analyzing your candidate fit...</p>
            <p className="text-xs text-textSecondary mt-0.5">Resume JD Matcher is hard at work 🚀</p>
          </div>
        </div>

        {/* Humorous Free Tier Notice */}
        <div className="p-3.5 rounded-xl bg-brandYellow/10 border border-brandYellow/25 text-xs text-brandYellow flex items-start gap-3">
          <span className="text-base">🐢</span>
          <div>
            <span className="font-semibold block mb-0.5">Free-Tier Model Disclaimer</span>
            <p className="opacity-90 leading-relaxed">
              We're running on free tier AI models, so processing might be a little bit slow (~20-40 seconds).
              Hang tight or grab a quick sip of coffee ☕ — good things take time!
            </p>
          </div>
        </div>

        <div className="space-y-2.5">
          {progressSteps.map((step, index) => {
            const Icon = step.icon;
            const done = index < progressIndex;
            const active = index === progressIndex;
            return (
              <div key={step.title} className={`p-3.5 rounded-xl border transition-all ${active ? "bg-white/[0.06] border-brandYellow/40 shadow-sm" : "border-transparent"}`}>
                <div className="flex items-center gap-3">
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold ${done ? "bg-brandGreen/20 text-brandGreen" : active ? "bg-brandYellow/20 text-brandYellow" : "bg-white/5 text-textSecondary/50"}`}>
                    {done ? <Check className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium ${active || done ? "text-textPrimary" : "text-textSecondary/60"}`}>{step.title}</p>
                    {active && <p className="text-[11px] text-brandYellow/90 mt-0.5 italic animate-pulse">{step.note}</p>}
                  </div>
                  {active && <ArrowRight className="w-4 h-4 text-brandYellow flex-shrink-0 animate-pulse" />}
                </div>
              </div>
            );
          })}
        </div>

        <div className="pt-2">
          <div className="h-1.5 rounded-full bg-white/[0.08] overflow-hidden">
            <div className="h-full rounded-full bg-brandYellow transition-all duration-700 ease-out" style={{ width: `${((progressIndex + 1) / progressSteps.length) * 100}%` }} />
          </div>
          <p className="text-[11px] text-center text-textSecondary mt-2">Built with care by @DIPXML</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-7">
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2 text-textSecondary text-xs font-medium">
            <ShieldCheck className="w-4 h-4 text-brandYellow" />
            <span>New Match Scan</span>
          </div>
          <a
            href="https://x.com/DIPXML"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] font-medium text-textSecondary hover:text-brandYellow transition-colors flex items-center gap-1 bg-white/[0.04] border border-white/10 px-2.5 py-1 rounded-full"
          >
            <span>by @DIPXML</span>
            <span className="text-[10px]">↗</span>
          </a>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-textPrimary">Match your resume with a job description</h1>
        <p className="text-sm text-textSecondary mt-2">Upload your resume and add the role details to get an instant, evidence-backed evaluation.</p>
      </div>

      {error && <div className="mb-5 p-3.5 rounded-xl bg-brandRed/10 border border-brandRed/30 text-brandRed text-sm flex items-center gap-2">⚠️ <span>{error}</span></div>}

      <div className="glass-panel rounded-2xl p-5 md:p-7 space-y-6 shadow-xl border border-white/10">
        <ResumeUpload selectedFile={resumeFile} onFileSelect={setResumeFile} />
        <div className="border-t border-border/80 pt-6"><JDInput jdText={jdText} onTextChange={setJdText} jdFile={jdFile} onFileChange={setJdFile} /></div>
        <button
          onClick={handleAnalyze}
          disabled={!resumeFile || (!jdText && !jdFile)}
          className="w-full py-3.5 px-4 bg-brandYellow hover:bg-white disabled:bg-white/[0.08] disabled:text-textSecondary text-background font-bold rounded-xl transition-all shadow-lg flex items-center justify-center gap-2 text-sm group"
        >
          <Play className="w-4 h-4 fill-current group-hover:scale-110 transition-transform" />
          <span>Analyze compatibility</span>
          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>
      <p className="text-center text-xs text-textSecondary mt-4 flex items-center justify-center gap-2">
        <span>🔒 Confidential & Secure</span>
        <span>·</span>
        <span>PDF, DOCX, or TXT</span>
        <span>·</span>
        <a href="https://x.com/DIPXML" target="_blank" rel="noopener noreferrer" className="hover:underline text-textPrimary font-medium">@DIPXML</a>
      </p>
    </div>
  );
};
