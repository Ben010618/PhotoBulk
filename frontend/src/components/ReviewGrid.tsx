import React, { useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Sliders,
  Upload,
  Download,
  Filter,
  Search,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Eye,
  ShieldAlert,
  Zap,
  Check,
  FileArchive
} from 'lucide-react';
import { PhotoItem } from '../types';

interface ReviewGridProps {
  photos: PhotoItem[];
  projectId: string;
  projectTitle: string;
  activePhotoId: string;
  onSelectPhoto: (id: string) => void;
  onOpenEditor: (id?: string) => void;
  onOpenUpload: () => void;
  onOpenExport: () => void;
  onBackToProjects: () => void;
}

export const ReviewGrid: React.FC<ReviewGridProps> = ({
  photos,
  projectId,
  projectTitle,
  activePhotoId,
  onSelectPhoto,
  onOpenEditor,
  onOpenUpload,
  onOpenExport,
  onBackToProjects,
}) => {
  const [filterMode, setFilterMode] = useState<'all' | 'needs_review' | 'ready'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const flaggedPhotos = photos.filter((p) => p.analysis?.review_needed || p.review_needed);
  const readyPhotos = photos.filter((p) => !p.analysis?.review_needed && !p.review_needed);

  const filtered = photos.filter((p) => {
    const isFlagged = p.analysis?.review_needed || p.review_needed;
    if (filterMode === 'needs_review' && !isFlagged) return false;
    if (filterMode === 'ready' && isFlagged) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchName = p.name.toLowerCase().includes(q);
      const matchReason = p.analysis?.review_reason?.toLowerCase().includes(q) || false;
      return matchName || matchReason;
    }
    return true;
  });

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#0d1117] text-[#c9d1d9] font-sans select-none overflow-hidden">
      {/* Header Bar */}
      <div className="h-14 border-b border-[#30363d] bg-[#161b22] px-6 flex items-center justify-between z-20 shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={onBackToProjects}
            className="p-1.5 rounded hover:bg-[#21262d] text-[#8b949e] hover:text-[#f0f6fc] transition"
            title="Return to Projects List"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold text-[#f0f6fc] tracking-tight">{projectTitle}</h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#21262d] border border-[#30363d] text-[#8b949e]">
                {projectId}
              </span>
            </div>
            <p className="text-[11px] text-[#8b949e]">
              Cohort Review Grid • {photos.length} total portraits • {flaggedPhotos.length} flagged for review
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={onOpenUpload}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium border border-[#30363d] bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] hover:text-[#f0f6fc] transition"
          >
            <Upload className="w-3.5 h-3.5 text-[#58a6ff]" />
            <span>Upload More</span>
          </button>

          <button
            onClick={() => onOpenEditor(activePhotoId || photos[0]?.id)}
            disabled={photos.length === 0}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-[#238636] hover:bg-[#2ea043] text-white transition disabled:opacity-50 shadow-sm"
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Open Studio Editor</span>
          </button>

          <button
            onClick={onOpenExport}
            disabled={photos.length === 0}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded text-xs font-semibold bg-[#f0f6fc] hover:bg-[#ffffff] text-[#0d1117] transition disabled:opacity-50 shadow-sm"
          >
            <FileArchive className="w-3.5 h-3.5 text-[#f0883e]" />
            <span>Bulk Export (300 DPI)</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="border-b border-[#30363d] bg-[#0d1117] px-6 py-2.5 flex items-center justify-between gap-4">
        {/* Filter Tabs */}
        <div className="flex items-center gap-1.5 bg-[#161b22] p-1 rounded-md border border-[#30363d]">
          <button
            onClick={() => setFilterMode('all')}
            className={`px-3 py-1 rounded text-xs font-medium transition ${
              filterMode === 'all'
                ? 'bg-[#21262d] text-[#f0f6fc] border border-[#30363d]'
                : 'text-[#8b949e] hover:text-[#c9d1d9]'
            }`}
          >
            All Photos ({photos.length})
          </button>
          <button
            onClick={() => setFilterMode('needs_review')}
            className={`px-3 py-1 rounded text-xs font-medium transition flex items-center gap-1.5 ${
              filterMode === 'needs_review'
                ? 'bg-amber-950/70 text-amber-200 border border-amber-800'
                : 'text-[#8b949e] hover:text-[#c9d1d9]'
            }`}
          >
            <AlertCircle className="w-3 h-3 text-amber-400" />
            <span>Needs Review ({flaggedPhotos.length})</span>
          </button>
          <button
            onClick={() => setFilterMode('ready')}
            className={`px-3 py-1 rounded text-xs font-medium transition flex items-center gap-1.5 ${
              filterMode === 'ready'
                ? 'bg-emerald-950/70 text-emerald-200 border border-emerald-800'
                : 'text-[#8b949e] hover:text-[#c9d1d9]'
            }`}
          >
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>Ready ({readyPhotos.length})</span>
          </button>
        </div>

        {/* Search */}
        <div className="relative w-64">
          <Search className="w-3.5 h-3.5 text-[#8b949e] absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by student or flag..."
            className="w-full bg-[#161b22] border border-[#30363d] rounded pl-8 pr-3 py-1 text-xs text-[#f0f6fc] focus:outline-none focus:border-[#58a6ff]"
          />
        </div>
      </div>

      {/* Grid Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {filtered.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center text-center text-[#8b949e] space-y-3">
            <Filter className="w-8 h-8 text-[#30363d]" />
            <p className="text-sm font-medium">No portraits matching filter &quot;{filterMode}&quot;</p>
            {photos.length === 0 && (
              <button
                onClick={onOpenUpload}
                className="px-4 py-2 bg-[#238636] hover:bg-[#2ea043] text-white rounded text-xs font-semibold transition"
              >
                Upload Portraits Now
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
            {filtered.map((photo) => {
              const isSelected = photo.id === activePhotoId;
              const isFlagged = photo.analysis?.review_needed || photo.review_needed;
              const reason = photo.analysis?.review_reason || photo.review_reason;
              const autoEv = photo.analysis?.auto_corrections?.exposure_compensation_ev;
              const sharpness = photo.analysis?.sharpness_score;
              const previewSrc =
                photo.previewUrl ||
                `/api/projects/${projectId}/photos/${photo.id}/preview`;

              return (
                <div
                  key={photo.id}
                  onClick={() => onSelectPhoto(photo.id)}
                  className={`group relative rounded-lg border bg-[#161b22] overflow-hidden flex flex-col cursor-pointer transition shadow-sm hover:border-[#8b949e] ${
                    isSelected
                      ? 'border-[#58a6ff] ring-1 ring-[#58a6ff]'
                      : 'border-[#30363d]'
                  }`}
                >
                  {/* Thumbnail Container */}
                  <div className="relative aspect-[4/5] bg-[#0d1117] overflow-hidden">
                    <img
                      src={previewSrc}
                      alt={photo.name}
                      className="w-full h-full object-cover group-hover:scale-102 transition duration-200"
                      loading="lazy"
                      onError={(e) => {
                        // Fallback to enhancedUrl or originalUrl if preview not ready
                        const target = e.currentTarget;
                        if (target.src !== photo.originalUrl) {
                          target.src = photo.originalUrl;
                        }
                      }}
                    />

                    {/* Status Badge */}
                    <div className="absolute top-2 left-2 right-2 flex items-center justify-between gap-1 pointer-events-none">
                      {isFlagged ? (
                        <span className="flex items-center gap-1 bg-amber-950/90 backdrop-blur-sm border border-amber-800/80 text-amber-300 text-[10px] px-1.5 py-0.5 rounded font-medium truncate">
                          <AlertCircle className="w-2.5 h-2.5 text-amber-400 shrink-0" />
                          <span className="truncate">{reason || 'Needs Review'}</span>
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 bg-emerald-950/80 backdrop-blur-sm border border-emerald-800 text-emerald-300 text-[10px] px-1.5 py-0.5 rounded font-medium">
                          <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400 shrink-0" />
                          <span>Ready</span>
                        </span>
                      )}

                      {photo.has_user_override && (
                        <span className="bg-[#1f6feb]/80 backdrop-blur-sm text-white text-[9px] px-1.5 py-0.5 rounded font-mono">
                          Custom
                        </span>
                      )}
                    </div>

                    {/* Hover Overlay Button */}
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectPhoto(photo.id);
                          onOpenEditor(photo.id);
                        }}
                        className="px-3 py-1.5 rounded bg-white text-[#0d1117] text-xs font-semibold shadow-lg hover:scale-105 transition flex items-center gap-1"
                      >
                        <Sliders className="w-3 h-3 text-[#0d1117]" />
                        <span>Tune Look</span>
                      </button>
                    </div>
                  </div>

                  {/* Card Meta & Analysis Summary */}
                  <div className="p-2.5 space-y-1">
                    <p className="text-xs font-semibold text-[#f0f6fc] truncate" title={photo.name}>
                      {photo.name}
                    </p>

                    <div className="flex items-center justify-between text-[10px] font-mono text-[#8b949e]">
                      {sharpness !== undefined && (
                        <span>Sharp: {Math.round(sharpness)}</span>
                      )}
                      {autoEv !== undefined && (
                        <span className={autoEv !== 0 ? 'text-[#58a6ff]' : ''}>
                          {autoEv > 0 ? `+${autoEv.toFixed(1)}` : autoEv.toFixed(1)} EV
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
