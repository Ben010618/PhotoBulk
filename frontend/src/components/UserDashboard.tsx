import React, { useState } from 'react';
import {
  Sparkles,
  Layers,
  FileArchive,
  Download,
  Plus,
  Clock,
  CheckCircle2,
  HardDrive,
  Zap,
  ArrowUpRight,
  Filter,
  Search,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  CreditCard
} from 'lucide-react';
import { PageView, UserSession } from './Navbar';

interface UserDashboardProps {
  onNavigate: (page: PageView) => void;
  currentUser: UserSession | null;
  onOpenTopUp: () => void;
}

interface BatchProject {
  id: string;
  name: string;
  count: number;
  backdrop: string;
  preset: string;
  status: 'completed' | 'processing' | 'queued';
  date: string;
  fileSize: string;
}

export const UserDashboard: React.FC<UserDashboardProps> = ({
  onNavigate,
  currentUser,
  onOpenTopUp,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'processing'>('all');

  const [projects] = useState<BatchProject[]>([
    {
      id: 'proj-001',
      name: 'UST Faculty of Engineering 2026',
      count: 342,
      backdrop: 'Signature Royal Navy',
      preset: 'Morena Radiant (65% Smooth)',
      status: 'completed',
      date: '2026-09-24',
      fileSize: '4.8 GB',
    },
    {
      id: 'proj-002',
      name: 'UP Diliman College of Science',
      count: 218,
      backdrop: 'Warm Amber Spotlight',
      preset: 'Natural Clean (45% Smooth)',
      status: 'completed',
      date: '2026-09-23',
      fileSize: '3.1 GB',
    },
    {
      id: 'proj-003',
      name: 'Ateneo Senior High Batch Horizon',
      count: 185,
      backdrop: 'Organic Painted Canvas',
      preset: 'Studio Glamour (80% Smooth)',
      status: 'processing',
      date: '2026-09-25',
      fileSize: '2.6 GB',
    },
    {
      id: 'proj-004',
      name: 'DLSU Ramon V. Del Rosario College',
      count: 420,
      backdrop: 'Signature Royal Navy',
      preset: 'High-Key Crisp (60% Smooth)',
      status: 'completed',
      date: '2026-09-21',
      fileSize: '5.9 GB',
    },
    {
      id: 'proj-005',
      name: 'PRC Board Licensure Examinees Batch 4',
      count: 96,
      backdrop: 'PRC Official Crimson',
      preset: 'Morena Radiant (65% Smooth)',
      status: 'completed',
      date: '2026-09-20',
      fileSize: '1.2 GB',
    },
  ]);

  const filteredProjects = projects.filter((p) => {
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === 'all' || p.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="flex-1 overflow-y-auto bg-[#0d1117] text-[#c9d1d9] font-sans selection:bg-[#30363d] selection:text-[#f0f6fc] p-6 lg:p-10 space-y-8">
      {/* HEADER BAR */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#30363d] pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-[#f0f6fc] tracking-tight">Studio Operations Dashboard</h1>
            <span className="text-xs font-mono border border-[#30363d] px-2 py-0.5 rounded bg-[#161b22] text-[#8b949e]">
              {currentUser?.studioName || 'AuraGrad Creative Studio Manila'}
            </span>
          </div>
          <p className="text-xs text-[#8b949e] mt-1">
            Manage high-volume graduation cohorts, track active batch matting jobs, and export 300DPI print packages.
          </p>
        </div>

        {/* Quick Launch Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => onNavigate('editor')}
            className="px-4 py-2 rounded text-xs font-semibold bg-[#f0f6fc] text-[#0d1117] hover:bg-white transition flex items-center gap-1.5 shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Launch Studio Editor</span>
          </button>
          <a
            href="/api/export-zip?school_name=AuraGrad_Recent_Batches"
            className="px-3.5 py-2 rounded text-xs font-medium border border-[#30363d] bg-[#161b22] hover:bg-[#21262d] text-[#f0f6fc] transition flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5 text-[#8b949e]" />
            <span>Export Master Archive</span>
          </a>
        </div>
      </div>

      {/* METRICS ROW */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg border border-[#30363d] bg-[#161b22] space-y-1">
          <div className="flex items-center justify-between text-xs text-[#8b949e] font-mono">
            <span>PROCESSED PORTRAITS</span>
            <Layers className="w-4 h-4 text-[#8b949e]" />
          </div>
          <div className="text-2xl font-bold font-mono text-[#f0f6fc]">1,261</div>
          <div className="text-[11px] text-[#8b949e]">across 5 active cohorts</div>
        </div>

        <div className="p-4 rounded-lg border border-[#30363d] bg-[#161b22] space-y-1">
          <div className="flex items-center justify-between text-xs text-[#8b949e] font-mono">
            <span>AVAILABLE CREDITS</span>
            <Zap className="w-4 h-4 text-[#8b949e]" />
          </div>
          <div className="text-2xl font-bold font-mono text-[#f0f6fc]">
            {currentUser?.credits ?? 150}
          </div>
          <div className="text-[11px] text-[#8b949e] flex items-center justify-between">
            <span>High-Res Master Units</span>
            <button onClick={onOpenTopUp} className="text-[#f0f6fc] hover:underline font-mono text-[10px]">
              + Top up
            </button>
          </div>
        </div>

        <div className="p-4 rounded-lg border border-[#30363d] bg-[#161b22] space-y-1">
          <div className="flex items-center justify-between text-xs text-[#8b949e] font-mono">
            <span>AVERAGE LATENCY</span>
            <Clock className="w-4 h-4 text-[#8b949e]" />
          </div>
          <div className="text-2xl font-bold font-mono text-[#f0f6fc]">245 ms</div>
          <div className="text-[11px] text-[#8b949e]">BiRefNet on A10G Cloud</div>
        </div>

        <div className="p-4 rounded-lg border border-[#30363d] bg-[#161b22] space-y-1">
          <div className="flex items-center justify-between text-xs text-[#8b949e] font-mono">
            <span>STUDIO STORAGE</span>
            <HardDrive className="w-4 h-4 text-[#8b949e]" />
          </div>
          <div className="text-2xl font-bold font-mono text-[#f0f6fc]">17.6 GB</div>
          <div className="text-[11px] text-[#8b949e]">of 50.0 GB Tier Quota (35%)</div>
        </div>
      </div>

      {/* SAVED STUDIO PRESETS & WORKFLOW SHORTCUTS */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {/* Projects Table Filter Bar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <h2 className="text-base font-semibold text-[#f0f6fc]">Graduation Batch Projects</h2>
            <div className="flex items-center gap-2">
              {/* Search */}
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-[#8b949e] absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter batches..."
                  className="bg-[#161b22] border border-[#30363d] rounded p-1.5 pl-8 text-xs text-[#f0f6fc] focus:outline-none focus:border-[#8b949e] font-sans"
                />
              </div>

              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                className="bg-[#161b22] border border-[#30363d] rounded p-1.5 text-xs text-[#f0f6fc] focus:outline-none focus:border-[#8b949e] font-sans cursor-pointer"
              >
                <option value="all">All Status</option>
                <option value="completed">Completed</option>
                <option value="processing">Processing</option>
              </select>
            </div>
          </div>

          {/* Table */}
          <div className="rounded-lg border border-[#30363d] bg-[#161b22] overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-sans">
                <thead className="bg-[#0d1117] border-b border-[#30363d] text-[11px] font-mono text-[#8b949e]">
                  <tr>
                    <th className="p-3">Cohort / School</th>
                    <th className="p-3">Count</th>
                    <th className="p-3">Backdrop &amp; Preset</th>
                    <th className="p-3">Status</th>
                    <th className="p-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#30363d]">
                  {filteredProjects.map((proj) => (
                    <tr key={proj.id} className="hover:bg-[#21262d]/50 transition">
                      <td className="p-3">
                        <div className="font-medium text-[#f0f6fc]">{proj.name}</div>
                        <div className="text-[10px] text-[#8b949e] font-mono mt-0.5">
                          {proj.date} &bull; {proj.fileSize}
                        </div>
                      </td>
                      <td className="p-3 font-mono text-[#f0f6fc]">{proj.count} portraits</td>
                      <td className="p-3">
                        <div className="text-[#f0f6fc]">{proj.backdrop}</div>
                        <div className="text-[10px] text-[#8b949e]">{proj.preset}</div>
                      </td>
                      <td className="p-3">
                        {proj.status === 'completed' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono border border-[#30363d] bg-[#0d1117] text-[#f0f6fc]">
                            <CheckCircle2 className="w-3 h-3 text-[#f0f6fc]" />
                            <span>Done</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono border border-[#30363d] bg-[#0d1117] text-[#8b949e] animate-pulse">
                            <Clock className="w-3 h-3 text-[#8b949e]" />
                            <span>Processing</span>
                          </span>
                        )}
                      </td>
                      <td className="p-3 text-right">
                        <div className="flex items-center justify-end gap-1.5 font-mono">
                          <button
                            onClick={() => onNavigate('editor')}
                            className="px-2 py-1 rounded border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-[#f0f6fc] text-[11px] transition"
                            title="Open batch in editor"
                          >
                            Edit
                          </button>
                          <a
                            href={`/api/export-zip?school_name=${encodeURIComponent(proj.name)}`}
                            className="p-1 rounded border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-[#8b949e] hover:text-[#f0f6fc] transition"
                            title="Download print ZIP"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </a>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* SIDE COLUMN: STUDIO RECIPES & TELEMETRY */}
        <div className="space-y-4">
          <h2 className="text-base font-semibold text-[#f0f6fc]">Saved Studio Presets</h2>
          <div className="space-y-2.5">
            <div className="p-3 rounded-lg border border-[#30363d] bg-[#161b22] space-y-1.5 hover:border-[#8b949e] transition">
              <div className="flex items-center justify-between">
                <span className="font-medium text-xs text-[#f0f6fc]">UST Engineering Honors</span>
                <span className="text-[10px] font-mono text-[#8b949e] border border-[#30363d] px-1 rounded bg-[#0d1117]">
                  Preset #1
                </span>
              </div>
              <p className="text-[11px] text-[#8b949e] leading-snug">
                Signature Royal Navy + Morena Radiant (65% smooth / 35% de-shine) + 8R &amp; 2x2 Crops.
              </p>
              <button
                onClick={() => onNavigate('editor')}
                className="w-full text-center py-1 mt-1 rounded text-[11px] font-mono border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-[#f0f6fc] transition"
              >
                Apply to Next Batch
              </button>
            </div>

            <div className="p-3 rounded-lg border border-[#30363d] bg-[#161b22] space-y-1.5 hover:border-[#8b949e] transition">
              <div className="flex items-center justify-between">
                <span className="font-medium text-xs text-[#f0f6fc]">UP Diliman Classic</span>
                <span className="text-[10px] font-mono text-[#8b949e] border border-[#30363d] px-1 rounded bg-[#0d1117]">
                  Preset #2
                </span>
              </div>
              <p className="text-[11px] text-[#8b949e] leading-snug">
                Warm Amber Radial Spotlight + Natural Clean (45% smooth) + 300 DPI Lab Export.
              </p>
              <button
                onClick={() => onNavigate('editor')}
                className="w-full text-center py-1 mt-1 rounded text-[11px] font-mono border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-[#f0f6fc] transition"
              >
                Apply to Next Batch
              </button>
            </div>

            <div className="p-3 rounded-lg border border-[#30363d] bg-[#161b22] space-y-1.5 hover:border-[#8b949e] transition">
              <div className="flex items-center justify-between">
                <span className="font-medium text-xs text-[#f0f6fc]">PRC Board Licensure Pack</span>
                <span className="text-[10px] font-mono text-[#8b949e] border border-[#30363d] px-1 rounded bg-[#0d1117]">
                  Preset #3
                </span>
              </div>
              <p className="text-[11px] text-[#8b949e] leading-snug">
                Official PRC Crimson Red + Formal Barong / Filipiniana + 2x2 Centered Formal Crop export.
              </p>
              <button
                onClick={() => onNavigate('editor')}
                className="w-full text-center py-1 mt-1 rounded text-[11px] font-mono border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-[#f0f6fc] transition"
              >
                Apply to Next Batch
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
