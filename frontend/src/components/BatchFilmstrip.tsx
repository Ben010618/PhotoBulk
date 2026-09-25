import React from 'react';
import { Layers, Plus, Play, FileArchive, AlertTriangle } from 'lucide-react';
import { PhotoItem } from '../types';

interface BatchFilmstripProps {
  photos: PhotoItem[];
  activePhotoId: string;
  onSelectPhoto: (id: string) => void;
  onUploadClick: () => void;
  onProcessAll: () => void;
  onExportZip: () => void;
  isBatchRunning: boolean;
}

export const BatchFilmstrip: React.FC<BatchFilmstripProps> = ({
  photos,
  activePhotoId,
  onSelectPhoto,
  onUploadClick,
  onProcessAll,
  onExportZip,
  isBatchRunning,
}) => {
  return (
    <footer className="h-16 border-t border-[#30363d] bg-[#161b22] px-4 flex items-center gap-4 z-20 shrink-0">
      <div className="flex items-center gap-2 shrink-0 pr-3 border-r border-[#30363d]">
        <Layers className="w-4 h-4 text-[#8b949e]" />
        <span className="text-xs font-mono text-[#c9d1d9]">
          Queue: {photos.length}
        </span>
      </div>

      {/* Thumbnails Row */}
      <div className="flex-1 flex items-center gap-2 overflow-x-auto py-1">
        {photos.map((item) => (
          <div
            key={item.id}
            onClick={() => onSelectPhoto(item.id)}
            className={`relative h-11 w-12 rounded overflow-hidden cursor-pointer border transition shrink-0 ${
              activePhotoId === item.id
                ? 'border-[#f0f6fc] ring-2 ring-[#f0f6fc]'
                : 'border-[#30363d] hover:border-[#8b949e] opacity-70 hover:opacity-100'
            }`}
          >
            <img
              src={item.enhancedUrl || item.originalUrl}
              alt={item.name}
              className="w-full h-full object-cover"
            />
            {/* Quality Badges */}
            {item.analysis?.is_best_shot && (
              <span
                className="absolute top-0.5 right-0.5 px-1 py-0.2 text-[8px] font-bold bg-[#f0f6fc] text-[#0d1117] rounded shadow-xs leading-none"
                title="Smart Pick (Optimal Focus & Open Eyes)"
              >
                ★
              </span>
            )}
            {item.analysis?.blink_status === 'blink' && (
              <span
                className="absolute bottom-0.5 left-0.5 px-1 py-0.2 text-[7px] font-mono font-bold bg-[#8a141b] text-[#f0f6fc] rounded shadow-xs leading-tight"
                title="Eye Blink Detected"
              >
                Blink
              </span>
            )}
            {item.analysis?.review_needed && (
              <span
                className="absolute top-0.5 left-0.5 px-1 py-0.2 text-[7px] font-mono font-bold bg-[#d29922] text-[#0d1117] rounded shadow-xs flex items-center gap-0.5"
                title={item.analysis.flag_reason || 'Review Needed'}
              >
                <AlertTriangle className="w-2.5 h-2.5" />
              </span>
            )}
            {item.status === 'processing' && (
              <div className="absolute inset-0 bg-[#0d1117]/70 flex items-center justify-center">
                <div className="w-3 h-3 border border-[#f0f6fc] border-t-transparent rounded-full animate-spin"></div>
              </div>
            )}
          </div>
        ))}

        <button
          onClick={onUploadClick}
          className="h-11 w-12 rounded border border-dashed border-[#30363d] hover:border-[#8b949e] flex items-center justify-center text-[#8b949e] hover:text-[#f0f6fc] transition shrink-0"
          title="Add photos to batch"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {/* Bulk Action Buttons */}
      <div className="flex items-center gap-2 shrink-0 pl-3 border-l border-[#30363d]">
        <button
          onClick={onProcessAll}
          disabled={isBatchRunning || photos.length === 0}
          className="flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-md border border-[#30363d] bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] hover:text-[#f0f6fc] transition disabled:opacity-50"
        >
          <Play className="w-3.5 h-3.5 text-[#58a6ff]" />
          <span>Process All ({photos.length})</span>
        </button>

        <button
          onClick={onExportZip}
          className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-md bg-[#f0883e] hover:bg-[#f0883e]/90 text-[#0d1117] transition active:scale-98 shadow-sm"
        >
          <FileArchive className="w-3.5 h-3.5 text-[#0d1117]" />
          <span>Bulk Export</span>
        </button>
      </div>
    </footer>
  );
};
