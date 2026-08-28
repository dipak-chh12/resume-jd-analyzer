import React, { useState, useRef } from "react";
import { FileText, Clipboard, Upload, X } from "lucide-react";

interface JDInputProps {
  jdText: string;
  onTextChange: (text: string) => void;
  jdFile: File | null;
  onFileChange: (file: File | null) => void;
}

export const JDInput: React.FC<JDInputProps> = ({
  jdText,
  onTextChange,
  jdFile,
  onFileChange,
}) => {
  const [inputMode, setInputMode] = useState<"paste" | "upload">("paste");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file: File) => {
    const validExtensions = [".pdf", ".docx", ".doc", ".txt"];
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
    
    if (validExtensions.includes(ext)) {
      onFileChange(file);
      onTextChange(""); // Clear pasted text when file uploaded
    } else {
      alert("Invalid file format. Please upload PDF, DOCX, or TXT.");
    }
  };

  const toggleMode = (mode: "paste" | "upload") => {
    setInputMode(mode);
    if (mode === "paste") {
      onFileChange(null);
    } else {
      onTextChange("");
    }
  };

  return (
    <div className="w-full">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div><label className="block text-sm font-semibold text-textPrimary">Job description</label><p className="text-xs text-textSecondary mt-1">Paste text or upload the original file</p></div>
        
        <div className="flex bg-background/70 p-1 rounded-xl border border-border text-xs">
          <button
            type="button"
            onClick={() => toggleMode("paste")}
            className={`px-3 py-1.5 rounded-md flex items-center space-x-1.5 transition-colors ${
              inputMode === "paste"
                ? "bg-brandYellow text-background shadow-sm font-semibold"
                : "text-textSecondary hover:text-white"
            }`}
          >
            <Clipboard className="w-3.5 h-3.5" />
            <span>Paste Text</span>
          </button>
          <button
            type="button"
            onClick={() => toggleMode("upload")}
            className={`px-3 py-1.5 rounded-md flex items-center space-x-1.5 transition-colors ${
              inputMode === "upload"
                ? "bg-brandYellow text-background shadow-sm font-semibold"
                : "text-textSecondary hover:text-white"
            }`}
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload File</span>
          </button>
        </div>
      </div>

      {inputMode === "paste" ? (
        <textarea
          value={jdText}
          onChange={(e) => onTextChange(e.target.value)}
          placeholder="Paste the job description or role requirements here..."
          className="w-full h-28 p-4 glass-input rounded-lg text-sm font-sans resize-none leading-6"
        />
      ) : (
        <div>
          {!jdFile ? (
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
                className={`w-full h-52 border border-dashed rounded-xl cursor-pointer flex flex-col items-center justify-center transition-all ${
                isDragActive
                  ? "border-brandYellow bg-brandYellow/[0.06]"
                  : "border-border hover:border-brandYellow/60 bg-card hover:bg-card-hover"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".pdf,.docx,.doc,.txt"
                onChange={handleChange}
              />
              <div className="p-3 bg-white/5 rounded-full text-white mb-2">
                <Upload className="w-5 h-5" />
              </div>
              <p className="text-sm text-textPrimary font-semibold mb-1">
                Drag & Drop or Click to Upload JD
              </p>
              <p className="text-xs text-textSecondary">
                Supports PDF, DOCX or TXT
              </p>
            </div>
          ) : (
            <div className="w-full p-4 glass-panel rounded-lg flex items-center justify-between border border-border bg-card">
              <div className="flex items-center space-x-3 overflow-hidden">
                <div className="p-2 bg-white/5 rounded-lg text-white flex-shrink-0">
                  <FileText className="w-5 h-5" />
                </div>
                <div className="overflow-hidden">
                  <p className="text-sm font-medium text-textPrimary truncate">
                    {jdFile.name}
                  </p>
                  <p className="text-xs text-textSecondary font-mono">
                    {(jdFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
              <button
                onClick={() => onFileChange(null)}
                className="p-1.5 hover:bg-white/5 rounded-full text-textSecondary hover:text-white transition-colors"
                title="Remove File"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
