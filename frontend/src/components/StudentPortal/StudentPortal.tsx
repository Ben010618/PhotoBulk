import React, { useState } from 'react';
import {
  GraduationCap,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  QrCode,
  Download,
  Calendar,
  Building2,
  FileCheck,
  ArrowLeft,
} from 'lucide-react';
import { StudentProof } from '../../types';
import { useUIStore } from '../../store/useUIStore';

export const StudentPortal: React.FC = () => {
  const { setCurrentPage, addToast } = useUIStore();

  const [studentProof, setStudentProof] = useState<StudentProof>({
    studentId: '2026-CS-0941',
    studentName: 'Maria Santos',
    schoolName: 'Polytechnic University of the Philippines',
    degree: 'Bachelor of Science in Computer Science',
    academicYear: 'Class of 2026 (Summa Cum Laude)',
    watermarkedPreviewUrl: '/api/photos/sample_preview',
    qrCodeUrl: '/api/photos/sample_qr',
    approvalStatus: 'pending',
  });

  const [revisionNotes, setRevisionNotes] = useState<string>('');
  const [showRevisionModal, setShowRevisionModal] = useState<boolean>(false);

  const handleApprove = () => {
    setStudentProof((prev) => ({ ...prev, approvalStatus: 'approved' }));
    addToast('success', 'Graduation portrait proof approved! Your studio has been notified for final printing.');
  };

  const handleRequestRevision = () => {
    if (!revisionNotes.trim()) {
      addToast('error', 'Please provide specific feedback for the studio retoucher.');
      return;
    }
    setStudentProof((prev) => ({
      ...prev,
      approvalStatus: 'revision_requested',
      feedbackNotes: revisionNotes,
    }));
    setShowRevisionModal(false);
    addToast('info', 'Revision request submitted to the studio editing team.');
  };

  return (
    <div className="flex-1 bg-[#0d1117] text-[#c9d1d9] flex flex-col overflow-y-auto">
      {/* Top Banner */}
      <div className="bg-[#161b22] border-b border-[#30363d] px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setCurrentPage('editor')}
            className="p-1.5 rounded-md hover:bg-[#21262d] text-[#8b949e] hover:text-[#f0f6fc] transition"
            title="Return to Studio Editor"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <GraduationCap className="w-5 h-5 text-[#58a6ff]" />
              <h1 className="text-sm font-semibold text-[#f0f6fc]">
                Student Digital Proofing Portal
              </h1>
            </div>
            <p className="text-xs text-[#8b949e]">
              Official Academic Portrait Verification &amp; Printing Approval
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`px-2.5 py-1 rounded-full text-xs font-medium border ${
              studentProof.approvalStatus === 'approved'
                ? 'bg-green-950/40 border-green-800 text-green-300'
                : studentProof.approvalStatus === 'revision_requested'
                ? 'bg-amber-950/40 border-amber-800 text-amber-300'
                : 'bg-blue-950/40 border-blue-800 text-blue-300'
            }`}
          >
            {studentProof.approvalStatus === 'approved'
              ? '✓ Approved for Printing'
              : studentProof.approvalStatus === 'revision_requested'
              ? '⚠ Revision Requested'
              : '● Awaiting Student Approval'}
          </span>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-5xl mx-auto w-full p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Watermarked Photo Card */}
        <div className="lg:col-span-7 flex flex-col items-center">
          <div className="relative w-full max-w-md rounded-xl overflow-hidden border border-[#30363d] bg-[#161b22] shadow-2xl">
            {/* Watermark Diagonal Pattern Overlay */}
            <div className="relative aspect-4/5 w-full bg-[#0d1117] flex items-center justify-center overflow-hidden">
              <img
                src={studentProof.watermarkedPreviewUrl}
                alt={studentProof.studentName}
                className="w-full h-full object-cover"
                onError={(e) => {
                  // Fallback placeholder pattern if sample not loaded
                  const target = e.currentTarget;
                  target.style.display = 'none';
                }}
              />

              {/* Watermark Shield */}
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none select-none bg-black/20">
                <div className="rotate-[-25deg] text-center p-4 border border-white/20 bg-black/40 backdrop-blur-xs rounded-lg">
                  <p className="text-white/60 font-mono text-sm tracking-widest uppercase font-bold">
                    Official Student Proof
                  </p>
                  <p className="text-white/40 text-[10px] tracking-tight">
                    {studentProof.schoolName}
                  </p>
                  <p className="text-white/30 text-[9px] font-mono mt-0.5">
                    {studentProof.studentId} • KameraPh
                  </p>
                </div>
              </div>
            </div>

            {/* Card Footer Bar */}
            <div className="p-4 bg-[#161b22] border-t border-[#30363d] flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs text-[#8b949e]">
                <ShieldCheck className="w-4 h-4 text-[#3fb950]" />
                <span>Digitally Authenticated Proof</span>
              </div>
              <span className="text-[11px] font-mono text-[#8b949e]">
                8R Master &bull; 300 DPI
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Academic Details & Approval Actions */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 space-y-4 shadow-sm">
            <div>
              <h2 className="text-base font-bold text-[#f0f6fc]">
                {studentProof.studentName}
              </h2>
              <p className="text-xs text-[#58a6ff] font-medium mt-0.5">
                {studentProof.degree}
              </p>
            </div>

            <div className="space-y-2.5 pt-2 border-t border-[#30363d] text-xs">
              <div className="flex items-center gap-2 text-[#8b949e]">
                <Building2 className="w-4 h-4 text-[#8b949e] shrink-0" />
                <span className="text-[#f0f6fc]">{studentProof.schoolName}</span>
              </div>
              <div className="flex items-center gap-2 text-[#8b949e]">
                <Calendar className="w-4 h-4 text-[#8b949e] shrink-0" />
                <span className="text-[#f0f6fc]">{studentProof.academicYear}</span>
              </div>
              <div className="flex items-center gap-2 text-[#8b949e]">
                <FileCheck className="w-4 h-4 text-[#8b949e] shrink-0" />
                <span className="font-mono text-[#f0f6fc]">{studentProof.studentId}</span>
              </div>
            </div>

            {/* QR Verification Badge */}
            <div className="p-3 rounded-lg bg-[#0d1117] border border-[#30363d] flex items-center gap-3">
              <div className="w-10 h-10 rounded bg-[#21262d] flex items-center justify-center shrink-0 border border-[#30363d]">
                <QrCode className="w-6 h-6 text-[#58a6ff]" />
              </div>
              <div className="text-[11px]">
                <p className="font-semibold text-[#f0f6fc]">Graduation QR Credentials</p>
                <p className="text-[#8b949e] text-[10px] leading-tight">
                  Scannable on printed graduation packages for yearbook verification.
                </p>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="pt-3 border-t border-[#30363d] space-y-2">
              <button
                onClick={handleApprove}
                disabled={studentProof.approvalStatus === 'approved'}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-[#238636] hover:bg-[#2ea043] text-white font-semibold text-xs transition active:scale-98 disabled:opacity-50 shadow-sm"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Approve Portrait for Yearbook &amp; Print</span>
              </button>

              <button
                onClick={() => setShowRevisionModal(true)}
                className="w-full flex items-center justify-center gap-2 py-2 rounded-lg border border-[#30363d] bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] text-xs font-medium transition"
              >
                <AlertTriangle className="w-3.5 h-3.5 text-[#e3b341]" />
                <span>Request Retouch Revision</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Revision Request Modal */}
      {showRevisionModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div>
              <h3 className="text-sm font-semibold text-[#f0f6fc]">
                Request Retouching Revision
              </h3>
              <p className="text-xs text-[#8b949e] mt-1">
                Please specify any adjustments (e.g., stray hair cleanup, hood alignment, glare reduction) for our studio editors.
              </p>
            </div>

            <textarea
              rows={4}
              value={revisionNotes}
              onChange={(e) => setRevisionNotes(e.target.value)}
              placeholder="e.g. Please align the right shoulder toga fold slightly and reduce forehead lighting glare..."
              className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg p-3 text-xs text-[#f0f6fc] focus:outline-none focus:border-[#58a6ff] placeholder:text-[#8b949e]"
            />

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#30363d]">
              <button
                onClick={() => setShowRevisionModal(false)}
                className="px-3 py-1.5 rounded-lg border border-[#30363d] text-xs font-medium text-[#8b949e] hover:text-[#f0f6fc] transition"
              >
                Cancel
              </button>
              <button
                onClick={handleRequestRevision}
                className="px-4 py-1.5 rounded-lg bg-[#58a6ff] hover:bg-[#58a6ff]/90 text-[#0d1117] font-semibold text-xs transition"
              >
                Submit Request
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
