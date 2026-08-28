import React, { useState, useRef, useEffect } from "react";
import { api } from "../services/api";
import type { ChatMessage } from "../services/api";
import { Send, Bot, User, Loader, HelpCircle, CheckCircle2, ChevronRight, BrainCircuit } from "lucide-react";

interface RAGChatProps {
  analysisId: string;
}

const ThinkingAnimation = () => {
  const [step, setStep] = useState(0);
  
  const steps = [
    "Analyzing query intent...",
    "Querying vector database for matching chunks...",
    "Retrieving candidate evidence...",
    "Synthesizing response context..."
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setStep((prev) => (prev < steps.length - 1 ? prev + 1 : prev));
    }, 800);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-start space-x-3 text-xs leading-relaxed mr-auto max-w-[85%]">
      <div className="w-8 h-8 rounded-full bg-black border border-zinc-800 text-zinc-400 flex items-center justify-center flex-shrink-0 shadow-inner">
        <BrainCircuit className="w-4 h-4 animate-pulse" />
      </div>
      <div className="p-4 bg-zinc-950/60 border border-zinc-800/80 rounded-lg rounded-tl-none shadow-sm space-y-3 min-w-[240px]">
        {steps.map((text, idx) => (
          <div 
            key={idx} 
            className={`flex items-center space-x-2 text-[11px] font-mono transition-opacity duration-300 ${
              idx > step ? "opacity-0 h-0 overflow-hidden" : "opacity-100"
            }`}
          >
            {idx < step ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-zinc-500" />
            ) : (
              <Loader className="w-3.5 h-3.5 text-zinc-400 animate-spin" />
            )}
            <span className={idx < step ? "text-zinc-500" : "text-zinc-300"}>{text}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export const RAGChat: React.FC<RAGChatProps> = ({ analysisId }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: "bot",
      text: "Ask me anything about your resume and how it matches this job description. I can search through the parsed vectors to give you precise answers."
    }
  ]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;

    const userMessage = inputText.trim();
    setInputText("");
    setMessages((prev) => [...prev, { sender: "user", text: userMessage }]);
    setLoading(true);

    try {
      const response = await api.sendChatMessage(analysisId, userMessage);
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: response.response,
          sources: response.sources
        }
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "bot",
          text: `Error: ${err.message || "Something went wrong. Please try again."}`
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const sampleQuestions = [
    "Why am I a good match?",
    "What are my biggest weaknesses?",
    "Which skills am I missing?",
    "How can I improve my project descriptions?"
  ];

  return (
    <div className="glass-panel rounded-xl border border-border flex flex-col h-[600px] overflow-hidden shadow-2xl bg-black/40">
      {/* Header */}
      <div className="flex items-center space-x-3 p-4 border-b border-border bg-black/40 flex-shrink-0">
        <div className="p-1.5 bg-zinc-900 border border-zinc-800 rounded-md">
          <Bot className="w-4 h-4 text-zinc-100" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-textPrimary leading-tight">Agentic AI Copilot</h3>
          <p className="text-[10px] text-zinc-500 font-mono mt-0.5">RAG-powered intelligence</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex items-start space-x-3 text-xs leading-relaxed max-w-[85%] ${
              msg.sender === "user" ? "ml-auto flex-row-reverse space-x-reverse" : "mr-auto"
            }`}
          >
            {/* Avatar */}
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm border ${
                msg.sender === "user"
                  ? "bg-zinc-100 border-zinc-300 text-zinc-900"
                  : "bg-black border-zinc-800 text-zinc-300"
              }`}
            >
              {msg.sender === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            {/* Bubble */}
            <div className="space-y-2 mt-1">
              <div
                className={`px-4 py-3 rounded-2xl border shadow-sm ${
                  msg.sender === "user"
                    ? "bg-zinc-100 border-zinc-200 text-zinc-900 rounded-tr-sm"
                    : "bg-zinc-950/80 border-zinc-800/80 text-zinc-300 rounded-tl-sm"
                }`}
              >
                <p className="whitespace-pre-wrap">{msg.text}</p>
              </div>

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-1 pl-1">
                  <span className="text-[10px] text-zinc-600 font-medium uppercase tracking-widest mt-0.5">Sources:</span>
                  {msg.sources.map((src, srcIdx) => (
                    <span
                      key={srcIdx}
                      className="text-[10px] bg-zinc-900/50 border border-zinc-800 text-zinc-400 px-2 py-0.5 rounded font-mono flex items-center gap-1"
                    >
                      <ChevronRight className="w-3 h-3 text-zinc-600" />
                      {src}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && <ThinkingAnimation />}
        
        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-zinc-950/80 border-t border-border flex-shrink-0">
        {/* Suggested Questions */}
        {messages.length === 1 && !loading && (
          <div className="mb-4">
            <div className="flex flex-wrap gap-2">
              {sampleQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => setInputText(q)}
                  className="text-[11px] bg-black hover:bg-zinc-900 border border-zinc-800 hover:border-zinc-600 text-zinc-400 hover:text-zinc-200 px-3 py-1.5 rounded-full transition-all flex items-center gap-1.5 shadow-sm"
                >
                  <HelpCircle className="w-3 h-3 opacity-50" />
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSend} className="relative flex items-center">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Ask a question about the analysis..."
            className="w-full pl-5 pr-12 py-3.5 bg-black border border-zinc-800 rounded-xl text-xs text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500 transition-all shadow-inner"
          />
          <button
            type="submit"
            disabled={!inputText.trim() || loading}
            className="absolute right-2 p-2 bg-zinc-100 hover:bg-white disabled:opacity-30 disabled:bg-zinc-800 text-black disabled:text-zinc-500 rounded-lg transition-all"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
