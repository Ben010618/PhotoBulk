import React, { useState, useEffect } from 'react';
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
  CreditCard,
  FolderPlus
} from 'lucide-react';
import { PageView, UserSession } from './Navbar';
import { useUIStore } from '../store/useUIStore';
import { useEditorStore } from '../store/useEditorStore';
import { apiClient } from '../api/apiClient';
import { ProjectItem, PhotoItem } from '../types';

interface UserDashboardProps {
  onNavigate: (page: PageView) => void;
  currentUser: UserSession | null;
  onOpenTopUp?: () => void;
}

export const UserDashboard: React.FC<UserDashboardProps> = ({
  onNavigate,
  currentUser,
  onOpenTopUp,
}) => {
  const paymentsEnabled = useUIStore((state) => state.paymentsEnabled);
  const addToast = useUIStore((state) => state.addToast);
  const [searchQuery, setSearchQuery] = useState('');
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // New Project Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newProjectTitle, setNewProjectTitle] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchProjects = async () => {
    setIsLoading(true);
    try {
      const data = await apiClient.listProjects();
      setProjects(data.projects || []);
    } catch (err: unknown) {
      console.error('[UserDashboard] Failed to fetch projects:', err);
      addToast('error', 'Could not load studio projects.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectTitle.trim()) return;
    setIsSubmitting(true);
    try {
      const proj = await apiClient.createProject(newProjectTitle.trim());
      addToast('success', `Created project "${proj.title}"`);
      setIsModalOpen(false);
      setNewProjectTitle('');
      await fetchProjects();

      // Open the new project
      handleOpenProject(proj.id, proj.title);
    } catch (err: unknown) {
      console.error('[UserDashboard] Create project error:', err);
      addToast('error', 'Failed to create new project.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenProject = async (projectId: string, projectTitle: string) => {
    try {
      const data = await apiClient.getProject(projectId);
      useEditorStore.getState().setCurrentProjectId(projectId);
      useEditorStore.getState().setCurrentProjectTitle(projectTitle || projectId);

      const loadedPhotos: PhotoItem[] = (data.photos || []).map((p: any) => ({
        id: p.id,
        name: p.filename || `${p.id}.jpg`,
        originalUrl: `/api/projects/${projectId}/photos/${p.id}/original`,
        enhancedUrl: `/api/projects/${projectId}/photos/${p.id}/preview`,
        previewUrl: `/api/projects/${projectId}/photos/${p.id}/preview`,
        masterUrl: `/api/projects/${projectId}/photos/${p.id}/master`,
        status: p.status || 'ready',
        analysis: p.analysis,
        has_face: p.has_face,
        has_user_override: p.has_user_override,
        review_needed: p.review_needed,
        review_reason: p.review_reason,
        settings: p.settings,
      }));

      useEditorStore.getState().setPhotos(loadedPhotos);

      if (loadedPhotos.length > 0) {
        useEditorStore.getState().setActivePhotoId(loadedPhotos[0].id);
        useEditorStore.getState().setWorkflowStep('review');
      } else {
        useEditorStore.getState().setWorkflowStep('upload');
      }

      onNavigate('editor');
    } catch (err: unknown) {
      console.error('[UserDashboard] Failed to open project:', err);
      addToast('error', `Failed to open project ${projectId}`);
    }
  };

  const filteredProjects = projects.filter((p) =>
    p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalPortraits = projects.reduce((acc, p) => acc + (p.photo_count || 0), 0);

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
            Manage high-volume graduation cohorts, track active batch matting jobs, and export 300 DPI print packages.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2 rounded text-xs font-semibold bg-[#238636] hover:bg-[#2ea043] text-white transition flex items-center gap-1.5 shadow-sm"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Cohort Project</span>
          </button>

          <button
            onClick={() => onNavigate('editor')}
            className="px-4 py-2 rounded text-xs font-semibold bg-[#f0f6fc] text-[#0d1117] hover:bg-white transition flex items-center gap-1.5 shadow-sm"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Launch Studio Editor</span>
          </button>
        </div>
      </div>

      {/* METRICS ROW */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg border border-[#30363d] bg-[#161b22] space-y-1">
          <div className="flex items-center justify-between text-xs text-[#8b949e] font-mono">
            <span>PROCESSED PORTRAITS</span>
            <Layers className="w-4 h-4 text-[#8b949e]" />
          </div>
          <div className="text-2xl font-bold font-mono text-[#f0f6fc]">{totalPortraits}</div>
          <div className="text-[11px] text-[#8b949e]">across {projects.length} cohorts on disk</div>
        </div>

        {paymentsEnabled ? (
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
        ) : (
          <div className="p-4 rounded-lg border border-[#30363d] bg-[#161b22] space-y-1">
            <div className="flex items-center justify-between text-xs text-[#8b949e] font-mono">
              <span>BATCH PIPELINE</span>
              <Sparkles className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold font-mono text-emerald-400">
              UNLIMITED
            </div>
            <div className="text-[11px] text-[#8b949e]">
              Local Studio Processing Active
            </div>
          </div>
        )}

        <div className="p-4 rounded-lg border border-[#30363d] bg-[#161b22] space-y-1">
          <div className="flex items-center justify-between text-xs text-[#8b949e] font-mono">
            <span>PREVIEW LATENCY</span>
            <Clock className="w-4 h-4 text-[#8b949e]" />
          </div>
          <div className="text-2xl font-bold font-mono text-[#f0f6fc]">
            &lt; 500 ms
          </div>
          <div className="text-[11px] text-[#8b949e]">Cached feature slider preview</div>
        </div>

        <div className="p-4 rounded-lg border border-[#30363d] bg-[#161b22] space-y-1">
          <div className="flex items-center justify-between text-xs text-[#8b949e] font-mono">
            <span>PRINT EXPORT</span>
            <HardDrive className="w-4 h-4 text-[#8b949e]" />
          </div>
          <div className="text-2xl font-bold font-mono text-[#f0f6fc]">300 DPI</div>
          <div className="text-[11px] text-[#8b949e]">sRGB Master, 8R, 5R, 4R, 2x2 ID</div>
        </div>
      </div>

      {/* PROJECTS LIST */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h2 className="text-base font-semibold text-[#f0f6fc]">Studio Cohort Projects</h2>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-[#8b949e] absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter cohorts..."
                className="bg-[#161b22] border border-[#30363d] rounded p-1.5 pl-8 text-xs text-[#f0f6fc] focus:outline-none focus:border-[#8b949e] font-sans"
              />
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="rounded-lg border border-[#30363d] bg-[#161b22] overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-sans">
              <thead className="bg-[#0d1117] border-b border-[#30363d] text-[11px] font-mono text-[#8b949e]">
                <tr>
                  <th className="p-3">Cohort Title &amp; ID</th>
                  <th className="p-3">Portrait Count</th>
                  <th className="p-3">Workflow State</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#30363d]">
                {isLoading ? (
                  <tr>
                    <td colSpan={4} className="p-8 text-center text-[#8b949e]">
                      Loading cohorts from persistent project store...
                    </td>
                  </tr>
                ) : filteredProjects.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-8 text-center text-[#8b949e] space-y-2">
                      <p>No cohort projects found.</p>
                      <button
                        onClick={() => setIsModalOpen(true)}
                        className="px-3 py-1.5 bg-[#238636] hover:bg-[#2ea043] text-white rounded font-semibold text-xs transition"
                      >
                        Create Your First Cohort
                      </button>
                    </td>
                  </tr>
                ) : (
                  filteredProjects.map((proj) => (
                    <tr
                      key={proj.id}
                      onClick={() => handleOpenProject(proj.id, proj.title)}
                      className="hover:bg-[#21262d]/50 transition cursor-pointer"
                    >
                      <td className="p-3">
                        <div className="font-semibold text-[#f0f6fc]">{proj.title}</div>
                        <div className="text-[10px] text-[#8b949e] font-mono mt-0.5">
                          ID: {proj.id}
                        </div>
                      </td>
                      <td className="p-3 font-mono text-[#f0f6fc]">
                        {proj.photo_count} {proj.photo_count === 1 ? 'portrait' : 'portraits'}
                      </td>
                      <td className="p-3">
                        {proj.photo_count > 0 ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono border border-emerald-800 bg-emerald-950/70 text-emerald-300">
                            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                            <span>Active Batch</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono border border-[#30363d] bg-[#0d1117] text-[#8b949e]">
                            <span>Awaiting Upload</span>
                          </span>
                        )}
                      </td>
                      <td className="p-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => handleOpenProject(proj.id, proj.title)}
                          className="px-3 py-1.5 rounded border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-[#f0f6fc] text-xs font-semibold transition"
                        >
                          {proj.photo_count > 0 ? 'Open Review & Editor' : 'Upload Photos'}
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* CREATE NEW PROJECT MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm select-none">
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl w-full max-w-md p-6 shadow-2xl space-y-4 font-sans text-xs text-[#c9d1d9]">
            <div className="flex items-center justify-between border-b border-[#30363d] pb-3">
              <div className="flex items-center gap-2">
                <FolderPlus className="w-4 h-4 text-[#58a6ff]" />
                <h3 className="font-bold text-sm text-[#f0f6fc]">Create New Graduation Cohort</h3>
              </div>
            </div>

            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#f0f6fc] mb-1">
                  Cohort / School Title
                </label>
                <input
                  type="text"
                  autoFocus
                  required
                  value={newProjectTitle}
                  onChange={(e) => setNewProjectTitle(e.target.value)}
                  placeholder="e.g. UP Diliman College of Science 2026"
                  className="w-full bg-[#0d1117] border border-[#30363d] rounded p-2 text-xs text-[#f0f6fc] focus:border-[#58a6ff] focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  disabled={isSubmitting}
                  className="px-3 py-1.5 rounded border border-[#30363d] text-[#c9d1d9] hover:bg-[#21262d] transition disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || !newProjectTitle.trim()}
                  className="px-4 py-1.5 rounded bg-[#238636] hover:bg-[#2ea043] text-white font-semibold transition disabled:opacity-50"
                >
                  {isSubmitting ? 'Creating...' : 'Create & Open Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
