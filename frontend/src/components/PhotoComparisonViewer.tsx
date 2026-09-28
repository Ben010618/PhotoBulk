import React, { useRef } from 'react';
import { ZoomIn, ZoomOut, AlertCircle, CheckCircle2, Star, Sparkles, Download } from 'lucide-react';
import { PhotoItem } from '../types';

interface PhotoComparisonViewerProps {
  activePhoto: PhotoItem | null;
  printViewMode: 'master' | '8r' | '2x2';
  sliderPosition: number;
  isZoomed: boolean;
  onSliderChange: (pos: number) => void;
  onToggleZoom: () => void;
  onSetPrintViewMode: (mode: 'master' | '8r' | '2x2') => void;
  containerRef: React.RefObject<HTMLDivElement | null>;
  isDragging: boolean;
  setIsDragging: (dragging: boolean) => void;
  onDownloadActive?: () => void;
}

export const PhotoComparisonViewer: React.FC<PhotoComparisonViewerProps> = ({
  activePhoto,
  printViewMode,
  sliderPosition,
  isZoomed,
  onSliderChange,
  onToggleZoom,
  onSetPrintViewMode,
  containerRef,
  isDragging,
  setIsDragging,
  onDownloadActive,
}) => {
  const imageRef = useRef<HTMLImageElement>(null);
  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDragging || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
    onSliderChange((x / rect.width) * 100);
  };

  const handleTouchMove = (e: React.TouchEvent<HTMLDivElement>) => {
    if (!isDragging || !containerRef.current || !e.touches[0]) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(e.touches[0].clientX - rect.left, rect.width));
    onSliderChange((x / rect.width) * 100);
  };

  const currentEnhanced =
    printViewMode === '8r'
      ? activePhoto?.crop8rUrl || activePhoto?.enhancedUrl
      : printViewMode === '2x2'
      ? activePhoto?.crop2x2Url || activePhoto?.enhancedUrl
      : activePhoto?.enhancedUrl;

  const currentOriginal = activePhoto?.originalUrl;

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#0d1117] border-r border-[#30363d] relative select-none">
      {/* Top Toolbar */}
      <div className="h-11 border-b border-[#30363d] bg-[#161b22] px-4 flex items-center justify-between text-xs text-[#8b949e]">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-[#f0f6fc]">{activePhoto?.name || 'Portrait Master'}</span>
          {activePhoto?.analysis?.review_needed && (
            <span className="flex items-center gap-1 bg-amber-950/80 border border-amber-800 text-amber-200 text-[10px] px-2 py-0.5 rounded font-mono">
              <AlertCircle className="w-3 h-3 text-amber-400" />
              <span>Review: {activePhoto.analysis.review_reason}</span>
            </span>
          )}
        </div>

        {/* View Mode Tabs */}
        <div className="flex items-center gap-1 bg-[#0d1117] p-1 rounded border border-[#30363d]">
          <button
            onClick={() => onSetPrintViewMode('master')}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
              printViewMode === 'master' ? 'bg-[#21262d] text-[#f0f6fc]' : 'text-[#8b949e] hover:text-[#c9d1d9]'
            }`}
          >
            Full Master
          </button>
          <button
            onClick={() => onSetPrintViewMode('8r')}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
              printViewMode === '8r' ? 'bg-[#21262d] text-[#f0f6fc]' : 'text-[#8b949e] hover:text-[#c9d1d9]'
            }`}
          >
            8R Yearbook (4:5)
          </button>
          <button
            onClick={() => onSetPrintViewMode('2x2')}
            className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
              printViewMode === '2x2' ? 'bg-[#21262d] text-[#f0f6fc]' : 'text-[#8b949e] hover:text-[#c9d1d9]'
            }`}
          >
            2x2 ID (DFA/PRC)
          </button>
        </div>

        {/* Zoom Toggle */}
        <button
          onClick={onToggleZoom}
          className="p-1 rounded hover:bg-[#21262d] text-[#c9d1d9] hover:text-[#f0f6fc] transition"
          title="Toggle Zoom (Pore inspection)"
        >
          {isZoomed ? <ZoomOut className="w-4 h-4" /> : <ZoomIn className="w-4 h-4" />}
        </button>

        {/* Quick Download Active Photo */}
        {onDownloadActive && activePhoto?.enhancedUrl && (
          <button
            onClick={onDownloadActive}
            className="p-1 rounded hover:bg-[#21262d] text-[#58a6ff] hover:text-[#79c0ff] transition flex items-center gap-1 text-[11px] font-mono px-2 border border-[#30363d]"
            title="Download Active 300 DPI Portrait"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Download</span>
          </button>
        )}
      </div>

      {/* Main Canvas Comparison Area */}
      <div
        ref={containerRef as any}
        onMouseMove={handleMouseMove}
        onMouseUp={() => setIsDragging(false)}
        onTouchMove={handleTouchMove}
        onTouchEnd={() => setIsDragging(false)}
        className="flex-1 flex items-center justify-center p-4 relative overflow-hidden bg-[#0a0d12]"
      >
        {activePhoto && currentEnhanced ? (
          <div
            className={`relative max-w-full max-h-full transition-transform duration-150 ${
              isZoomed ? 'scale-150 cursor-grab active:cursor-grabbing' : ''
            }`}
            style={{ aspectRatio: printViewMode === '8r' ? '4/5' : printViewMode === '2x2' ? '1/1' : 'auto' }}
          >
            {/* Enhanced Image (Base Layer) */}
            <img
              ref={imageRef}
              src={currentEnhanced}
              alt="Enhanced Portrait"
              className="max-h-[70vh] object-contain rounded shadow-lg pointer-events-none"
            />

            {/* Original Image (Clipped Top Layer for Master View) */}
            {printViewMode === 'master' && currentOriginal && (
              <div
                className="absolute inset-0 overflow-hidden pointer-events-none"
                style={{ width: `${sliderPosition}%` }}
              >
                <img
                  src={currentOriginal}
                  alt="Original Portrait"
                  className="max-h-[70vh] object-contain rounded pointer-events-none max-w-none"
                  style={{ width: imageRef.current?.clientWidth }}
                />
              </div>
            )}

            {/* Split Slider Divider */}
            {printViewMode === 'master' && currentOriginal && (
              <div
                onMouseDown={() => setIsDragging(true)}
                onTouchStart={() => setIsDragging(true)}
                style={{ left: `${sliderPosition}%` }}
                className="absolute top-0 bottom-0 w-1 bg-white cursor-ew-resize flex items-center justify-center -ml-0.5 shadow-2xl"
              >
                <div className="w-6 h-6 rounded-full bg-white shadow-md border border-neutral-300 flex items-center justify-center text-[10px] text-neutral-800 font-bold select-none">
                  ↔
                </div>
              </div>
            )}

            {/* Corner Badges */}
            {printViewMode === 'master' && (
              <>
                <span className="absolute top-3 left-3 bg-black/60 backdrop-blur-sm text-white text-[10px] px-2 py-0.5 rounded font-mono">
                  ORIGINAL CAPTURE
                </span>
                <span className="absolute top-3 right-3 bg-[#238636]/80 backdrop-blur-sm text-white text-[10px] px-2 py-0.5 rounded font-mono font-semibold flex items-center gap-1">
                  <Sparkles className="w-2.5 h-2.5" />
                  KAMERAPH AI ENHANCED
                </span>
              </>
            )}
          </div>
        ) : (
          <div className="text-center text-[#8b949e] space-y-2">
            <p className="text-sm">No portrait loaded</p>
            <p className="text-xs">Select or upload a photo to begin batch retouching</p>
          </div>
        )}
      </div>
    </div>
  );
};
