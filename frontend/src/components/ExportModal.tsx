import React, { useState, useEffect } from 'react';
import {
  X,
  FileArchive,
  Download,
  Check,
  AlertCircle,
  Sparkles,
  FileText,
  Sliders,
  CheckCircle2,
  Clock
} from 'lucide-react';
import { apiClient } from '../api/apiClient';
import { useUIStore } from '../store/useUIStore';
import { ExportJobStatus } from '../types';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  projectTitle: string;
  totalPhotos: number;
}

const AVAILABLE_OUTPUTS = [
  { id: 'master', label: 'Full Master (300 DPI sRGB)', desc: 'Original high-resolution graduation portrait with neural retouching.' },
  { id: '8r', label: '8R Yearbook Print (8x10)', desc: 'Standard 4:5 aspect ratio print crop for commencement framing.' },
  { id: '5r', label: '5R Print (5x7)', desc: 'Classical keepsake gift print format.' },
  { id: '4r', label: '4R Print (4x6)', desc: 'Pocket print standard for family albums.' },
  { id: 'wallet', label: 'Wallet Size (2.5x3.5)', desc: 'Classmate and relative wallet keepsake.' },
  { id: '2x2', label: '2x2 Formal ID (DFA/PRC)', desc: 'Centered face-crop meeting Philippine passport and board exam rules.' },
  { id: 'web', label: 'Web JPEG (High Quality 95)', desc: 'Optimized compressed JPEG for social media and online portfolios.' },
];

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  projectId,
  projectTitle,
  totalPhotos,
}) => {
  const [selectedOutputs, setSelectedOutputs] = useState<string[]>(['master', '8r', '2x2']);
  const [filenameTemplate, setFilenameTemplate] = useState('{section}_{last}_{first}_{size}.jpg');
  const [schoolName, setSchoolName] = useState('Graduation Batch 2026');
  const [studioName, setStudioName] = useState('AuraGrad Creative Studio');
  const [includeContactSheet, setIncludeContactSheet] = useState(true);
  const [studentCsv, setStudentCsv] = useState('');
  const [showCsvBox, setShowCsvBox] = useState(false);

  const [isExporting, setIsExporting] = useState(false);
  const [exportId, setExportId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<ExportJobStatus | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const addToast = useUIStore((s) => s.addToast);

  // Poll status while active
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;
    if (isExporting && exportId) {
      interval = setInterval(async () => {
        try {
          const status = await apiClient.getExportStatus(projectId, exportId);
          setJobStatus(status);
          if (status.status === 'completed') {
            setIsExporting(false);
            addToast('success', 'Bulk export package rendered and packaged into ZIP!');
            if (interval) clearInterval(interval);
          } else if (status.status === 'failed') {
            setIsExporting(false);
            addToast('error', status.error || 'Export failed');
            if (interval) clearInterval(interval);
          }
        } catch (err: unknown) {
          console.error('[ExportModal] Status poll error:', err);
        }
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isExporting, exportId, projectId, addToast]);

  if (!isOpen) return null;

  const toggleOutput = (id: string) => {
    setSelectedOutputs((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleStartExport = async () => {
    if (selectedOutputs.length === 0) {
      addToast('error', 'Please select at least one output size format.');
      return;
    }

    setIsExporting(true);
    setJobStatus(null);

    try {
      const res = await apiClient.triggerProjectExport(projectId, {
        selected_outputs: selectedOutputs,
        filename_template: filenameTemplate,
        student_csv: studentCsv.trim() || undefined,
        school_name: schoolName,
        studio_name: studioName,
        include_contact_sheet: includeContactSheet,
      });

      setExportId(res.job_id);
      addToast('info', 'Export job initiated in background worker pool...');
    } catch (err: unknown) {
      console.error('[ExportModal] Start export error:', err);
      const msg = err instanceof Error ? err.message : 'Failed to launch export job';
      addToast('error', msg);
      setIsExporting(false);
    }
  };

  const handleDownloadBlob = async () => {
    if (!exportId) return;
    setIsDownloading(true);
    try {
      const cleanSchool = schoolName.replace(/[^a-zA-Z0-9_-]/g, '_');
      const filename = `${cleanSchool}_Bulk_Export_300DPI.zip`;
      await apiClient.downloadExportZip(projectId, exportId, filename);
      addToast('success', 'Export archive downloaded successfully.');
    } catch (err: unknown) {
      console.error('[ExportModal] Blob download error:', err);
      addToast('error', 'Failed to download export archive.');
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm select-none">
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden font-sans text-xs text-[#c9d1d9]">
        {/* Header */}
        <div className="p-4 border-b border-[#30363d] flex items-center justify-between bg-[#1c2128]">
          <div className="flex items-center gap-2">
            <FileArchive className="w-4 h-4 text-[#f0883e]" />
            <h2 className="font-bold text-sm text-[#f0f6fc]">
              Bulk Export Package (300 DPI Master)
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-[#30363d] text-[#8b949e] hover:text-[#f0f6fc] transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Target Info */}
          <div className="flex items-center justify-between p-3 rounded border border-[#30363d] bg-[#0d1117]">
            <div>
              <span className="font-semibold text-[#f0f6fc] block">{projectTitle}</span>
              <span className="text-[10px] text-[#8b949e]">{totalPhotos} portraits in cohort</span>
            </div>
            <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#21262d] border border-[#30363d] text-[#58a6ff]">
              High-Res Render Engine
            </span>
          </div>

          {/* Output Size Formats */}
          <div className="space-y-2">
            <label className="font-semibold text-[#f0f6fc] block">1. Select Output Formats</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {AVAILABLE_OUTPUTS.map((out) => {
                const isChecked = selectedOutputs.includes(out.id);
                return (
                  <div
                    key={out.id}
                    onClick={() => !isExporting && toggleOutput(out.id)}
                    className={`p-2.5 rounded border cursor-pointer transition flex items-start gap-2.5 ${
                      isChecked
                        ? 'border-[#58a6ff] bg-[#1f6feb]/10 text-[#f0f6fc]'
                        : 'border-[#30363d] bg-[#0d1117] hover:border-[#8b949e]'
                    }`}
                  >
                    <div
                      className={`w-4 h-4 rounded border flex items-center justify-center shrink-0 mt-0.5 transition ${
                        isChecked
                          ? 'border-[#58a6ff] bg-[#58a6ff] text-[#0d1117]'
                          : 'border-[#30363d] bg-[#161b22]'
                      }`}
                    >
                      {isChecked && <Check className="w-3 h-3 stroke-[3]" />}
                    </div>
                    <div>
                      <span className="font-semibold block">{out.label}</span>
                      <span className="text-[10px] text-[#8b949e] leading-relaxed block">{out.desc}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Filename Template & Settings */}
          <div className="space-y-3">
            <label className="font-semibold text-[#f0f6fc] block">2. Filename Template &amp; Studio Branding</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <span className="text-[10px] text-[#8b949e] block mb-1">Filename Template</span>
                <input
                  type="text"
                  value={filenameTemplate}
                  onChange={(e) => setFilenameTemplate(e.target.value)}
                  disabled={isExporting}
                  placeholder="{section}_{last}_{first}_{size}.jpg"
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded p-2 text-xs text-[#f0f6fc] font-mono focus:border-[#58a6ff] focus:outline-none"
                />
              </div>

              <div>
                <span className="text-[10px] text-[#8b949e] block mb-1">School / Cohort Name</span>
                <input
                  type="text"
                  value={schoolName}
                  onChange={(e) => setSchoolName(e.target.value)}
                  disabled={isExporting}
                  placeholder="Graduation Batch 2026"
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded p-2 text-xs text-[#f0f6fc] focus:border-[#58a6ff] focus:outline-none"
                />
              </div>
            </div>

            {/* Contact Sheet Checkbox */}
            <label className="flex items-center gap-2 cursor-pointer pt-1">
              <input
                type="checkbox"
                checked={includeContactSheet}
                onChange={(e) => setIncludeContactSheet(e.target.checked)}
                disabled={isExporting}
                className="rounded border-[#30363d] bg-[#0d1117] text-[#1f6feb]"
              />
              <span className="text-xs text-[#f0f6fc]">
                Generate Contact Sheet PDF with student names and thumbnails
              </span>
            </label>

            {/* Student CSV Toggle */}
            <div className="pt-1">
              <button
                type="button"
                onClick={() => setShowCsvBox(!showCsvBox)}
                className="text-[11px] text-[#58a6ff] hover:underline flex items-center gap-1"
              >
                <FileText className="w-3 h-3" />
                <span>{showCsvBox ? 'Hide Student CSV Mapping' : '+ Add Student CSV Mapping (filename to name)'}</span>
              </button>

              {showCsvBox && (
                <div className="mt-2 space-y-1">
                  <textarea
                    rows={4}
                    value={studentCsv}
                    onChange={(e) => setStudentCsv(e.target.value)}
                    disabled={isExporting}
                    placeholder={"filename,first_name,last_name,section\nphoto_001.jpg,Maria,Santos,Section-A\nphoto_002.jpg,Juan,Dela Cruz,Section-A"}
                    className="w-full bg-[#0d1117] border border-[#30363d] rounded p-2 text-[11px] font-mono text-[#f0f6fc] focus:border-[#58a6ff] focus:outline-none"
                  />
                  <p className="text-[10px] text-[#8b949e]">
                    Format: filename, first_name, last_name, section. Used to populate filename template variables.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Live Export Progress Banner */}
          {(isExporting || jobStatus) && (
            <div className="p-4 rounded-lg border border-[#30363d] bg-[#0d1117] space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-[#f0f6fc] flex items-center gap-2">
                  {jobStatus?.status === 'completed' ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <Clock className="w-4 h-4 text-[#58a6ff] animate-spin" />
                  )}
                  <span>{jobStatus?.message || 'Executing bulk export in worker pool...'}</span>
                </span>
                <span className="font-mono text-[#8b949e]">{jobStatus?.progress || 0}%</span>
              </div>

              <div className="w-full bg-[#21262d] border border-[#30363d] h-2 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${
                    jobStatus?.status === 'completed' ? 'bg-emerald-500' : 'bg-[#58a6ff]'
                  }`}
                  style={{ width: `${jobStatus?.progress || 0}%` }}
                />
              </div>

              {jobStatus?.result && (
                <div className="pt-2 border-t border-[#30363d]/50 flex items-center justify-between text-[11px] font-mono text-[#8b949e]">
                  <span>Rendered: {jobStatus.result.total_images_rendered} files</span>
                  <span>Archive: {(jobStatus.result.zip_size_bytes / (1024 * 1024)).toFixed(1)} MB</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-[#30363d] bg-[#1c2128] flex items-center justify-between">
          <button
            onClick={onClose}
            disabled={isExporting}
            className="px-3 py-1.5 rounded border border-[#30363d] text-[#c9d1d9] hover:bg-[#21262d] transition disabled:opacity-50"
          >
            Close
          </button>

          <div className="flex items-center gap-2">
            {jobStatus?.status === 'completed' ? (
              <button
                onClick={handleDownloadBlob}
                disabled={isDownloading}
                className="px-4 py-2 bg-[#238636] hover:bg-[#2ea043] text-white font-semibold rounded transition flex items-center gap-2 shadow-sm disabled:opacity-50"
              >
                <Download className="w-3.5 h-3.5 text-white" />
                <span>{isDownloading ? 'Downloading ZIP...' : 'Download ZIP Archive'}</span>
              </button>
            ) : (
              <button
                onClick={handleStartExport}
                disabled={isExporting || totalPhotos === 0}
                className="px-4 py-2 bg-[#f0f6fc] hover:bg-white text-[#0d1117] font-semibold rounded transition flex items-center gap-2 shadow-sm disabled:opacity-50"
              >
                <Sparkles className="w-3.5 h-3.5 text-[#0d1117]" />
                <span>{isExporting ? 'Exporting Package...' : 'Start Bulk Export'}</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
