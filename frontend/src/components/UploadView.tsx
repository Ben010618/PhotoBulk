import React, { useState, useRef } from 'react';
import {
  Upload,
  FileImage,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
  Sparkles,
  Layers,
  Cpu
} from 'lucide-react';
import { apiClient } from '../api/apiClient';
import { useUIStore } from '../store/useUIStore';

interface UploadViewProps {
  projectId: string;
  projectTitle: string;
  onUploadSuccess: () => void;
  onCancel: () => void;
}

export const UploadView: React.FC<UploadViewProps> = ({
  projectId,
  projectTitle,
  onUploadSuccess,
  onCancel,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [fileCount, setFileCount] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const addToast = useUIStore((s) => s.addToast);

  const handleFiles = async (files: File[]) => {
    const validFiles = files.filter((f) =>
      ['image/jpeg', 'image/png', 'image/webp'].includes(f.type) ||
      f.name.match(/\.(jpe?g|png|webp)$/i)
    );

    if (validFiles.length === 0) {
      addToast('error', 'Please select valid JPEG, PNG, or WebP portrait files.');
      return;
    }

    setIsUploading(true);
    setProgress(5);
    setFileCount(validFiles.length);
    setStatusMessage(`Uploading ${validFiles.length} photos and caching neural features...`);

      await apiClient.batchUpload(validFiles, projectId, (completed, total, pct) => {
        setProgress(pct);
        setStatusMessage(`Uploading: ${completed} of ${total} photos completed (${pct}%)...`);
      });

      setProgress(100);
      setStatusMessage('Upload complete! Background analysis active.');
      addToast('success', `Successfully uploaded ${validFiles.length} portraits into ${projectTitle}.`);

      setTimeout(() => {
        onUploadSuccess();
      }, 600);
    } catch (err: unknown) {
      console.error('[UploadView] Upload error:', err);
      const msg = err instanceof Error ? err.message : 'Batch upload failed';
      addToast('error', msg);
      setIsUploading(false);
      setProgress(0);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-[#0d1117] text-[#c9d1d9] font-sans select-none overflow-y-auto">
      {/* Top Header */}
      <div className="h-14 border-b border-[#30363d] bg-[#161b22] px-6 flex items-center justify-between z-20 shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={onCancel}
            disabled={isUploading}
            className="p-1.5 rounded hover:bg-[#21262d] text-[#8b949e] hover:text-[#f0f6fc] transition disabled:opacity-50"
            title="Cancel"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <h1 className="text-sm font-bold text-[#f0f6fc]">Batch Portrait Ingestion</h1>
            <p className="text-[11px] text-[#8b949e]">Target Cohort: {projectTitle} ({projectId})</p>
          </div>
        </div>
      </div>

      {/* Main Upload Body */}
      <div className="flex-1 flex items-center justify-center p-6 lg:p-12">
        <div className="max-w-2xl w-full space-y-6">
          {/* Drag & Drop Card */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => !isUploading && fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center text-center cursor-pointer transition ${
              isDragging
                ? 'border-[#58a6ff] bg-[#1f6feb]/10 scale-101'
                : 'border-[#30363d] bg-[#161b22] hover:border-[#8b949e] hover:bg-[#1c2128]'
            } ${isUploading ? 'pointer-events-none opacity-80' : ''}`}
          >
            <input
              type="file"
              multiple
              ref={fileInputRef}
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  handleFiles(Array.from(e.target.files));
                }
              }}
              className="hidden"
              accept="image/jpeg,image/png,image/webp"
            />

            <div className="w-16 h-16 rounded-full bg-[#21262d] border border-[#30363d] flex items-center justify-center mb-4 text-[#58a6ff] shadow-sm">
              <Upload className="w-8 h-8" />
            </div>

            <h2 className="text-lg font-bold text-[#f0f6fc] tracking-tight mb-1">
              Drag & Drop Graduation Portraits
            </h2>
            <p className="text-xs text-[#8b949e] max-w-md mb-4">
              Select high-resolution graduation photos (up to 24 MP). AI will automatically separate backgrounds, analyze sharpness, and cache landmarks.
            </p>

            <button
              type="button"
              disabled={isUploading}
              className="px-4 py-2 bg-[#238636] hover:bg-[#2ea043] text-white rounded text-xs font-semibold shadow-sm transition disabled:opacity-50"
            >
              Select Files from Computer
            </button>
          </div>

          {/* Upload & Precompute Progress Bar */}
          {isUploading && (
            <div className="p-4 rounded-lg border border-[#30363d] bg-[#161b22] space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-[#f0f6fc] flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-[#58a6ff] animate-pulse" />
                  <span>{statusMessage}</span>
                </span>
                <span className="font-mono text-[#8b949e]">{progress}%</span>
              </div>
              <div className="w-full bg-[#21262d] border border-[#30363d] h-2 rounded-full overflow-hidden">
                <div
                  className="bg-[#238636] h-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-[10px] text-[#8b949e] font-mono">
                {fileCount} portraits • Saving original.jpg, preview.jpg &amp; computing alpha.png
              </p>
            </div>
          )}

          {/* Architecture Benefits Note */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-[#8b949e]">
            <div className="p-3 rounded border border-[#30363d] bg-[#161b22]/50 flex items-start gap-2">
              <Layers className="w-4 h-4 text-[#58a6ff] shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-[#f0f6fc] block">Persistent Cache</span>
                <span className="text-[10px]">Landmarks and masks are saved on disk. Survives server restarts.</span>
              </div>
            </div>

            <div className="p-3 rounded border border-[#30363d] bg-[#161b22]/50 flex items-start gap-2">
              <Cpu className="w-4 h-4 text-[#3fb950] shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-[#f0f6fc] block">Fast Previews</span>
                <span className="text-[10px]">Instant slider response on ~1600px preview without re-matting.</span>
              </div>
            </div>

            <div className="p-3 rounded border border-[#30363d] bg-[#161b22]/50 flex items-start gap-2">
              <CheckCircle2 className="w-4 h-4 text-[#f0883e] shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-[#f0f6fc] block">Smart Review</span>
                <span className="text-[10px]">Flags blinks, blur, or head tilt automatically for quality control.</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
