import React from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';
import { useUIStore } from '../../store/useUIStore';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useUIStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`pointer-events-auto flex items-start justify-between gap-2.5 p-3 rounded-lg border shadow-xl backdrop-blur-md transition-all duration-200 animate-in fade-in slide-in-from-bottom-2 ${
            toast.type === 'error'
              ? 'bg-[#1f1315]/95 border-[#f85149]/40 text-[#f85149]'
              : toast.type === 'success'
              ? 'bg-[#101b14]/95 border-[#3fb950]/40 text-[#3fb950]'
              : 'bg-[#161b22]/95 border-[#58a6ff]/40 text-[#58a6ff]'
          }`}
        >
          <div className="flex items-start gap-2.5 mt-0.5">
            {toast.type === 'error' && <AlertCircle className="w-4 h-4 shrink-0 text-[#f85149]" />}
            {toast.type === 'success' && <CheckCircle2 className="w-4 h-4 shrink-0 text-[#3fb950]" />}
            {toast.type === 'info' && <Info className="w-4 h-4 shrink-0 text-[#58a6ff]" />}
            <span className="text-xs font-medium text-[#c9d1d9] leading-tight">
              {toast.message}
            </span>
          </div>
          <button
            onClick={() => removeToast(toast.id)}
            className="text-[#8b949e] hover:text-[#f0f6fc] p-0.5 transition"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
};
