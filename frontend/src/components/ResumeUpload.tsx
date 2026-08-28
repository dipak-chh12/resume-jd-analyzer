import React, { useRef, useState } from "react";
import { Upload, FileText, X } from "lucide-react";

interface ResumeUploadProps {
  selectedFile: File | null;
  onFileSelect: (file: File | null) => void;
}

export const ResumeUpload: React.FC<ResumeUploadProps> = ({ selectedFile, onFileSelect }) => {
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
      onFileSelect(file);
    } else {
      alert("Invalid file format. Please upload PDF, DOCX, or TXT.");
    }
  };

  const triggerInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="w-full">
      <div className="flex items-start justify-between mb-3"><div><p className="text-sm font-semibold text-textPrimary">Resume</p><p className="text-xs text-textSecondary mt-1">PDF, DOCX, or TXT up to 10MB</p></div><span className="text-xs text-textSecondary">Required</span></div>

      {!selectedFile ? (
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={triggerInput}
          className={`w-full min-h-[120px] py-6 px-4 border border-dashed rounded-xl cursor-pointer flex flex-col items-center justify-center transition-all ${
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
          <div className="p-3 bg-white/5 rounded-full text-white mb-3">
            <Upload className="w-5 h-5" />
          </div>
          <p className="text-sm text-textPrimary font-semibold mb-1">
            Drag & Drop or Click to Upload
          </p>
          <p className="text-xs text-textSecondary">
            Supports PDF, DOCX or TXT up to 10MB
          </p>
        </div>
      ) : (
          <div className="w-full p-4 rounded-xl flex items-center justify-between border border-border bg-background">
          <div className="flex items-center space-x-3 overflow-hidden">
            <div className="p-2 bg-brandYellow/10 rounded-lg text-brandYellow flex-shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-medium text-textPrimary truncate">
                {selectedFile.name}
              </p>
              <p className="text-xs text-textSecondary font-mono">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
          </div>
          <button
            onClick={() => onFileSelect(null)}
            className="p-1.5 hover:bg-white/5 rounded-full text-textSecondary hover:text-white transition-colors"
            title="Remove File"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
