import React, { useState, useEffect } from 'react';
import {
  Server,
  Cpu,
  Zap,
  Activity,
  Users,
  ShieldCheck,
  AlertTriangle,
  RefreshCw,
  Search,
  HardDrive,
  Clock,
  CheckCircle2,
  Sliders,
  DollarSign,
  ChevronRight,
  Eye,
  EyeOff,
  Sparkles,
  Key,
  Save,
  ShieldAlert,
  Lock,
  Check,
  AlertCircle
} from 'lucide-react';
import { PageView, UserSession } from './Navbar';
import { apiClient } from '../api/apiClient';

interface AdminDashboardProps {
  onNavigate: (page: PageView) => void;
  currentUser: UserSession | null;
}

interface StudioAccount {
  id: string;
  name: string;
  location: string;
  plan: 'Enterprise' | 'Pro Studio' | 'Starter';
  credits: number;
  totalProcessed: number;
  status: 'active' | 'suspended';
}

interface JobTelemetry {
  jobId: string;
  studio: string;
  model: string;
  batchSize: number;
  latencyMs: number;
  status: 'PROCESSING' | 'COMPLETED' | 'QUEUED';
  time: string;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ onNavigate, currentUser }) => {
  const [activeTab, setActiveTab] = useState<'studios' | 'queue' | 'ai_engine' | 'config'>('ai_engine');
  const [searchTerm, setSearchTerm] = useState('');

  // AI API Key & Engine States (for Beautification & Diagnostics)
  const [apiKey, setApiKey] = useState<string>('');
  const [apiKeyMasked, setApiKeyMasked] = useState<string>('');
  const [hasKey, setHasKey] = useState<boolean>(false);
  const [showKey, setShowKey] = useState<boolean>(false);
  const [provider, setProvider] = useState<string>('google_gemini');
  const [model, setModel] = useState<string>('gemini-2.5-flash');
  const [beautifyMode, setBeautifyMode] = useState<string>('ai_neural_frequency');
  const [aiStatus, setAiStatus] = useState<string>('local_fallback');
  const [engineLabel, setEngineLabel] = useState<string>('Local OpenCV DNN Hybrid Active');
  const [lastTested, setLastTested] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchAiConfig();
  }, []);

  const fetchAiConfig = async () => {
    try {
      const res = await apiClient.instance.get('/api/admin/ai-config');
      const data = res.data;
      setHasKey(data.has_key);
      setApiKeyMasked(data.api_key_masked);
      setProvider(data.provider || 'google_gemini');
      setModel(data.model || 'gemini-2.5-flash');
      setBeautifyMode(data.beautify_mode || 'ai_neural_frequency');
      setAiStatus(data.status || 'local_fallback');
      setEngineLabel(data.engine_label || 'Local OpenCV DNN Hybrid Active');
      setLastTested(data.last_tested);
    } catch (e: unknown) {
      console.error('Failed to load AI config:', e);
    }
  };

  const handleSaveAiConfig = async () => {
    setIsSaving(true);
    setSaveSuccess(null);
    setTestResult(null);
    try {
      const formData = new FormData();
      formData.append('api_key', apiKey);
      formData.append('provider', provider);
      formData.append('model', model);
      formData.append('beautify_mode', beautifyMode);

      const res = await apiClient.instance.post('/api/admin/ai-config', formData);
      const data = res.data;
      setSaveSuccess('AI Engine and API Key configuration saved successfully!');
      setHasKey(data.has_key);
      setApiKeyMasked(data.api_key_masked);
      setAiStatus(data.status);
      setEngineLabel(data.status === 'active' ? 'Google Gemini Multimodal AI (Active)' : 'Local OpenCV DNN Hybrid (Active)');
      setApiKey('');
    } catch (e: unknown) {
      console.error('[AdminDashboard.saveAiConfig] Error:', e);
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestAiKey = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const formData = new FormData();
      formData.append('api_key', apiKey);

      const res = await apiClient.instance.post('/api/admin/test-ai-key', formData);
      const data = res.data;
      setTestResult({
        success: data.success,
        message: data.message,
      });
      if (data.success) {
        setAiStatus('active');
        setLastTested(new Date().toLocaleTimeString());
      }
    } catch (e: unknown) {
      setTestResult({
        success: false,
        message: 'Network request error while testing AI API Key.',
      });
    } finally {
      setIsTesting(false);
    }
  };

  const [studios, setStudios] = useState<StudioAccount[]>([
    {
      id: 'std-01',
      name: 'AuraGrad Creative Studio Manila',
      location: 'Sampaloc, Manila',
      plan: 'Enterprise',
      credits: 2450,
      totalProcessed: 18450,
      status: 'active',
    },
    {
      id: 'std-02',
      name: 'Lumina Graduation Portraits',
      location: 'Quezon City',
      plan: 'Pro Studio',
      credits: 890,
      totalProcessed: 9200,
      status: 'active',
    },
    {
      id: 'std-03',
      name: 'Aura Studio Visayas',
      location: 'Cebu City',
      plan: 'Pro Studio',
      credits: 120,
      totalProcessed: 6410,
      status: 'active',
    },
    {
      id: 'std-04',
      name: 'Southern Grad Photography',
      location: 'Davao City',
      plan: 'Starter',
      credits: 45,
      totalProcessed: 1820,
      status: 'active',
    },
    {
      id: 'std-05',
      name: 'UP Diliman Student Council Yearbook',
      location: 'Diliman, QC',
      plan: 'Enterprise',
      credits: 5000,
      totalProcessed: 12400,
      status: 'active',
    },
  ]);

  const [queueJobs] = useState<JobTelemetry[]>([
    {
      jobId: 'job-9821',
      studio: 'AuraGrad Creative Studio Manila',
      model: 'BiRefNet-HR + FreqSep',
      batchSize: 342,
      latencyMs: 238,
      status: 'PROCESSING',
      time: '15:12:04',
    },
    {
      jobId: 'job-9820',
      studio: 'Lumina Portraits',
      model: 'BiRefNet-HR + MorenaRetouch',
      batchSize: 180,
      latencyMs: 280,
      status: 'COMPLETED',
      time: '15:08:42',
    },
    {
      jobId: 'job-9819',
      studio: 'UP Diliman Yearbook',
      model: 'BiRefNet-HR + RoyalNavy',
      batchSize: 520,
      latencyMs: 219,
      status: 'COMPLETED',
      time: '14:55:10',
    },
    {
      jobId: 'job-9818',
      studio: 'Aura Studio Visayas',
      model: 'BiRefNet-HR + AmberStrobe',
      batchSize: 95,
      latencyMs: 260,
      status: 'QUEUED',
      time: '15:13:30',
    },
  ]);

  const handleGrantCredits = (id: string) => {
    setStudios((prev) =>
      prev.map((s) => (s.id === id ? { ...s, credits: s.credits + 500 } : s))
    );
  };

  const handleToggleStatus = (id: string) => {
    setStudios((prev) =>
      prev.map((s) =>
        s.id === id ? { ...s, status: s.status === 'active' ? 'suspended' : 'active' } : s
      )
    );
  };

  const filteredStudios = studios.filter((s) =>
    s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.location.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // ADMIN-ONLY ACCESS RESTRICTION GUARD
  if (currentUser?.role !== 'admin') {
    return (
      <div className="flex-1 overflow-y-auto bg-[#0d1117] flex items-center justify-center p-6 text-[#c9d1d9] font-sans">
        <div className="max-w-md w-full p-6 rounded-lg border border-red-900/60 bg-[#161b22] space-y-5 text-center shadow-2xl">
          <div className="w-14 h-14 rounded-full border border-red-800 bg-red-950/40 flex items-center justify-center mx-auto text-red-300 shadow-md">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <div className="space-y-1">
            <h2 className="text-xl font-bold text-[#f0f6fc] tracking-tight">
              Administrator Access Restricted
            </h2>
            <p className="text-xs text-[#8b949e] leading-relaxed">
              This console contains proprietary GPU fleet telemetry, studio billing controls, and sensitive AI API keys for Studio Beautification &amp; Matting.
            </p>
          </div>

          <div className="p-3.5 rounded bg-[#0d1117] border border-[#30363d] text-left text-xs font-mono space-y-1.5">
            <div className="flex justify-between">
              <span className="text-[#8b949e]">Current User:</span>
              <span className="text-[#f0f6fc]">{currentUser?.name || 'Guest User'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8b949e]">Current Role:</span>
              <span className="text-amber-400 font-semibold">{currentUser?.role || 'Guest'} (Non-Admin)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#8b949e]">Required Role:</span>
              <span className="text-red-400 font-semibold">Admin (Owner)</span>
            </div>
          </div>

          <div className="space-y-2 pt-2">
            <button
              onClick={() => onNavigate('auth')}
              className="w-full py-2.5 rounded text-xs font-semibold bg-[#f0f6fc] hover:bg-white text-[#0d1117] transition shadow-sm font-sans"
            >
              Sign In with Admin Account (admin@kameraph.com)
            </button>
            <button
              onClick={() => onNavigate('editor')}
              className="w-full py-2 rounded text-xs font-medium border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-[#8b949e] hover:text-[#f0f6fc] transition"
            >
              Return to Studio Editor
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto bg-[#0d1117] text-[#c9d1d9] font-sans selection:bg-[#30363d] selection:text-[#f0f6fc] p-6 lg:p-10 space-y-8">
      {/* HEADER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#30363d] pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-[#f0f6fc] tracking-tight">
              Admin Fleet &amp; Operations Console
            </h1>
            <span className="text-xs font-mono border border-green-800 bg-green-950/40 text-green-300 px-2 py-0.5 rounded">
              All Systems Operational
            </span>
          </div>
          <p className="text-xs text-[#8b949e] mt-1">
            Global studio account management, cloud GPU inference telemetry, and platform safety settings.
          </p>
        </div>

        <button
          onClick={() => onNavigate('editor')}
          className="px-4 py-2 rounded text-xs font-semibold border border-[#30363d] bg-[#161b22] hover:bg-[#21262d] text-[#f0f6fc] transition flex items-center gap-1.5 self-start md:self-auto"
        >
          <Sliders className="w-3.5 h-3.5 text-[#8b949e]" />
          <span>Switch to Studio Editor</span>
        </button>
      </div>

      {/* CLOUD INFRASTRUCTURE METRICS ROW */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg border border-[#30363d] bg-[#161b22] space-y-1">
          <div className="flex items-center justify-between text-xs text-[#8b949e] font-mono">
            <span>ACTIVE ML ENGINE</span>
            <Server className="w-4 h-4 text-[#8b949e]" />
          </div>
          <div className="text-2xl font-bold font-mono text-[#f0f6fc]">Production ML Cluster</div>
          <div className="text-[11px] text-[#8b949e]">Modal Cloud GPU &amp; Local Fallback</div>
        </div>

        <div className="p-4 rounded-lg border border-[#30363d] bg-[#161b22] space-y-1">
          <div className="flex items-center justify-between text-xs text-[#8b949e] font-mono">
            <span>TOTAL RETOUCHED</span>
            <Activity className="w-4 h-4 text-[#8b949e]" />
          </div>
          <div className="text-2xl font-bold font-mono text-[#f0f6fc]">48,280</div>
          <div className="text-[11px] text-[#8b949e]">Current Academic Season</div>
        </div>

        <div className="p-4 rounded-lg border border-[#30363d] bg-[#161b22] space-y-1">
          <div className="flex items-center justify-between text-xs text-[#8b949e] font-mono">
            <span>ACTIVE STUDIOS</span>
            <Users className="w-4 h-4 text-[#8b949e]" />
          </div>
          <div className="text-2xl font-bold font-mono text-[#f0f6fc]">14 Studios</div>
          <div className="text-[11px] text-[#8b949e]">Metro Manila, Cebu, Davao</div>
        </div>

        <div className="p-4 rounded-lg border border-[#30363d] bg-[#161b22] space-y-1">
          <div className="flex items-center justify-between text-xs text-[#8b949e] font-mono">
            <span>AVG INFERENCE TIME</span>
            <Clock className="w-4 h-4 text-[#8b949e]" />
          </div>
          <div className="text-2xl font-bold font-mono text-[#f0f6fc]">241 ms</div>
          <div className="text-[11px] text-[#8b949e]">P95 Latency &bull; 300 DPI Output</div>
        </div>
      </div>

      {/* ADMIN TABS */}
      <div className="space-y-4">
        <div className="flex items-center gap-1 border-b border-[#30363d] text-xs font-mono">
          <button
            onClick={() => setActiveTab('studios')}
            className={`px-4 py-2 border-b-2 font-medium transition ${
              activeTab === 'studios'
                ? 'border-[#f0f6fc] text-[#f0f6fc]'
                : 'border-transparent text-[#8b949e] hover:text-[#f0f6fc]'
            }`}
          >
            Registered Studios ({studios.length})
          </button>
          <button
            onClick={() => setActiveTab('queue')}
            className={`px-4 py-2 border-b-2 font-medium transition ${
              activeTab === 'queue'
                ? 'border-[#f0f6fc] text-[#f0f6fc]'
                : 'border-transparent text-[#8b949e] hover:text-[#f0f6fc]'
            }`}
          >
            Live GPU Batch Queue ({queueJobs.length})
          </button>
          <button
            onClick={() => setActiveTab('ai_engine')}
            className={`px-4 py-2 border-b-2 font-medium transition flex items-center gap-1.5 ${
              activeTab === 'ai_engine'
                ? 'border-[#f0f6fc] text-[#f0f6fc]'
                : 'border-transparent text-[#8b949e] hover:text-[#f0f6fc]'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>AI Engine &amp; API Key</span>
            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#0d1117] border border-amber-800 text-amber-300">
              Beautify &amp; Matting
            </span>
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={`px-4 py-2 border-b-2 font-medium transition ${
              activeTab === 'config'
                ? 'border-[#f0f6fc] text-[#f0f6fc]'
                : 'border-transparent text-[#8b949e] hover:text-[#f0f6fc]'
            }`}
          >
            Engine Configuration
          </button>
        </div>

        {/* TAB 1: STUDIOS */}
        {activeTab === 'studios' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="relative w-72">
                <Search className="w-3.5 h-3.5 text-[#8b949e] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search studios..."
                  className="w-full bg-[#161b22] border border-[#30363d] rounded p-1.5 pl-9 text-xs text-[#f0f6fc] focus:outline-none focus:border-[#8b949e] font-sans"
                />
              </div>
              <button
                onClick={() => handleGrantCredits('std-01')}
                className="px-3 py-1.5 rounded text-xs font-mono border border-[#30363d] bg-[#161b22] hover:bg-[#21262d] text-[#f0f6fc] transition"
              >
                + Grant 500 Credits to AuraGrad
              </button>
            </div>

            <div className="rounded-lg border border-[#30363d] bg-[#161b22] overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-sans">
                  <thead className="bg-[#0d1117] border-b border-[#30363d] text-[11px] font-mono text-[#8b949e]">
                    <tr>
                      <th className="p-3">Studio Name</th>
                      <th className="p-3">Location</th>
                      <th className="p-3">Subscription</th>
                      <th className="p-3">Credits</th>
                      <th className="p-3">Total Volume</th>
                      <th className="p-3">Status</th>
                      <th className="p-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#30363d]">
                    {filteredStudios.map((s) => (
                      <tr key={s.id} className="hover:bg-[#21262d]/50 transition">
                        <td className="p-3 font-medium text-[#f0f6fc]">{s.name}</td>
                        <td className="p-3 text-[#8b949e]">{s.location}</td>
                        <td className="p-3 font-mono">
                          <span className="border border-[#30363d] px-1.5 py-0.5 rounded bg-[#0d1117] text-[#c9d1d9] text-[10px]">
                            {s.plan}
                          </span>
                        </td>
                        <td className="p-3 font-mono text-[#f0f6fc]">{s.credits}</td>
                        <td className="p-3 font-mono text-[#8b949e]">{s.totalProcessed.toLocaleString()}</td>
                        <td className="p-3">
                          <span
                            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono ${
                              s.status === 'active'
                                ? 'bg-green-950/40 text-green-300 border border-green-800'
                                : 'bg-red-950/40 text-red-300 border border-red-800'
                            }`}
                          >
                            {s.status}
                          </span>
                        </td>
                        <td className="p-3 text-right">
                          <div className="flex items-center justify-end gap-1.5 font-mono">
                            <button
                              onClick={() => handleGrantCredits(s.id)}
                              className="px-2 py-1 rounded border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-[#f0f6fc] text-[10px]"
                            >
                              +500 Credits
                            </button>
                            <button
                              onClick={() => handleToggleStatus(s.id)}
                              className="px-2 py-1 rounded border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-[#8b949e] hover:text-[#f0f6fc] text-[10px]"
                            >
                              {s.status === 'active' ? 'Suspend' : 'Activate'}
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: LIVE QUEUE */}
        {activeTab === 'queue' && (
          <div className="rounded-lg border border-[#30363d] bg-[#161b22] overflow-hidden">
            <div className="p-3 bg-[#0d1117] border-b border-[#30363d] flex items-center justify-between text-xs">
              <span className="font-mono text-[#8b949e]">ML Vision Pipeline Inference Queue</span>
              <button
                onClick={() => {}}
                className="flex items-center gap-1 text-[11px] font-mono text-[#8b949e] hover:text-[#f0f6fc]"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Refresh Queue</span>
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-sans">
                <thead className="bg-[#0d1117] border-b border-[#30363d] text-[11px] font-mono text-[#8b949e]">
                  <tr>
                    <th className="p-3">Job ID</th>
                    <th className="p-3">Studio</th>
                    <th className="p-3">Pipeline</th>
                    <th className="p-3">Batch Size</th>
                    <th className="p-3">Latency</th>
                    <th className="p-3">Time</th>
                    <th className="p-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#30363d]">
                  {queueJobs.map((j) => (
                    <tr key={j.jobId} className="hover:bg-[#21262d]/50 transition">
                      <td className="p-3 font-mono text-[#f0f6fc]">{j.jobId}</td>
                      <td className="p-3 text-[#f0f6fc]">{j.studio}</td>
                      <td className="p-3 text-[#8b949e] font-mono">{j.model}</td>
                      <td className="p-3 font-mono text-[#f0f6fc]">{j.batchSize} photos</td>
                      <td className="p-3 font-mono text-[#f0f6fc]">{j.latencyMs} ms</td>
                      <td className="p-3 font-mono text-[#8b949e]">{j.time}</td>
                      <td className="p-3 text-right">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono ${
                            j.status === 'COMPLETED'
                              ? 'border border-[#30363d] bg-[#0d1117] text-[#f0f6fc]'
                              : j.status === 'PROCESSING'
                              ? 'border border-amber-800 bg-amber-950/40 text-amber-200 animate-pulse'
                              : 'border border-[#30363d] bg-[#0d1117] text-[#8b949e]'
                          }`}
                        >
                          {j.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB: AI ENGINE & API KEY CONFIGURATION */}
        {activeTab === 'ai_engine' && (
          <div className="space-y-6">
            {/* Real-time Status Card */}
            <div className="p-4 rounded-lg border border-[#30363d] bg-[#161b22] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded border border-[#30363d] bg-[#0d1117] flex items-center justify-center text-amber-400">
                  <Sparkles className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-[#f0f6fc]">AI Engine Pipeline Status</h3>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                      aiStatus === 'active'
                        ? 'border-emerald-800 bg-emerald-950/40 text-emerald-300'
                        : 'border-amber-800 bg-amber-950/40 text-amber-300'
                    }`}>
                      {aiStatus === 'active' ? '● Cloud AI Active' : '○ Local Hybrid Fallback'}
                    </span>
                  </div>
                  <p className="text-xs text-[#8b949e] font-mono mt-0.5">
                    Current Engine: <span className="text-[#f0f6fc]">{engineLabel}</span> &bull; Model: <span className="text-[#f0f6fc]">{model}</span>
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={fetchAiConfig}
                  className="px-3 py-1.5 rounded border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-xs font-mono text-[#8b949e] hover:text-[#f0f6fc] transition flex items-center gap-1.5"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Sync Status</span>
                </button>
              </div>
            </div>

            {/* Main Form Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* CARD 1: AI API KEY CONFIGURATION */}
              <div className="p-5 rounded-lg border border-[#30363d] bg-[#161b22] space-y-4">
                <div className="flex items-center justify-between border-b border-[#30363d] pb-3">
                  <div className="flex items-center gap-2">
                    <Key className="w-4 h-4 text-amber-400" />
                    <h3 className="text-sm font-semibold text-[#f0f6fc]">
                      AI API Key Configuration
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-[#8b949e] border border-[#30363d] px-1.5 py-0.5 rounded bg-[#0d1117]">
                    Admin Secret
                  </span>
                </div>

                <p className="text-xs text-[#8b949e] leading-relaxed">
                  This API key powers <strong>Google Gemini AI Vision</strong> (melanin tone detection, studio lighting temperature appraisal, and skin health diagnostics) and <strong>AI Beautification</strong> (neural frequency separation, pore preservation, blemish erasure, and studio de-glare).
                </p>

                {/* Staged Key Status Banner */}
                <div className="p-3 rounded bg-[#0d1117] border border-[#30363d] text-xs font-mono flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-[#8b949e]">Staged Key:</span>
                    <span className="text-[#f0f6fc] font-semibold">
                      {hasKey ? apiKeyMasked : 'None configured (Local fallback active)'}
                    </span>
                  </div>
                  {hasKey && (
                    <span className="text-[10px] font-mono text-emerald-400 border border-emerald-900 px-1.5 py-0.2 rounded bg-emerald-950/30">
                      SECURED
                    </span>
                  )}
                </div>

                {/* API Key Input with Placeholder */}
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-[#f0f6fc] flex items-center justify-between">
                    <span>Google Gemini API Key Placeholder</span>
                    <span className="text-[10px] text-[#8b949e] font-mono">Starts with AIzaSy...</span>
                  </label>
                  <div className="relative">
                    <input
                      type={showKey ? 'text' : 'password'}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="Enter Google Gemini API Key (e.g., AIzaSy...)..."
                      className="w-full bg-[#0d1117] border border-[#30363d] hover:border-[#8b949e] rounded p-2.5 pr-20 text-xs font-mono text-[#f0f6fc] focus:outline-none focus:border-[#f0f6fc] transition"
                    />
                    <button
                      type="button"
                      onClick={() => setShowKey(!showKey)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-[11px] font-mono text-[#8b949e] hover:text-[#f0f6fc] px-2 py-1 rounded hover:bg-[#21262d] transition flex items-center gap-1"
                    >
                      {showKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                      <span>{showKey ? 'Hide' : 'Show'}</span>
                    </button>
                  </div>
                  <p className="text-[11px] text-[#8b949e]">
                    Obtain your key from Google AI Studio. Stored securely on the studio server and never exposed to clients.
                  </p>
                </div>

                {/* Feedback Alerts */}
                {saveSuccess && (
                  <div className="p-3 rounded bg-emerald-950/40 border border-emerald-800 text-xs text-emerald-200 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>{saveSuccess}</span>
                  </div>
                )}

                {testResult && (
                  <div className={`p-3 rounded border text-xs flex items-start gap-2 ${
                    testResult.success
                      ? 'bg-emerald-950/40 border-emerald-800 text-emerald-200'
                      : 'bg-red-950/40 border-red-800 text-red-200'
                  }`}>
                    {testResult.success ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                    )}
                    <span>{testResult.message}</span>
                  </div>
                )}

                {/* Action Buttons */}
                <div className="grid grid-cols-2 gap-3 pt-2">
                  <button
                    type="button"
                    onClick={handleSaveAiConfig}
                    disabled={isSaving}
                    className="flex items-center justify-center gap-1.5 py-2 px-3 rounded text-xs font-semibold bg-[#f0f6fc] hover:bg-white text-[#0d1117] transition disabled:opacity-50 shadow-sm"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>{isSaving ? 'Saving...' : 'Save AI Configuration'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={handleTestAiKey}
                    disabled={isTesting}
                    className="flex items-center justify-center gap-1.5 py-2 px-3 rounded text-xs font-medium border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-[#f0f6fc] transition disabled:opacity-50"
                  >
                    <Zap className="w-3.5 h-3.5 text-amber-400" />
                    <span>{isTesting ? 'Testing...' : 'Test AI Key Connection'}</span>
                  </button>
                </div>
              </div>

              {/* CARD 2: MODEL SELECTION & AI PIPELINE CONTROLS */}
              <div className="p-5 rounded-lg border border-[#30363d] bg-[#161b22] space-y-4">
                <div className="flex items-center justify-between border-b border-[#30363d] pb-3">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-[#8b949e]" />
                    <h3 className="text-sm font-semibold text-[#f0f6fc]">
                      AI Models &amp; Pipeline Modes
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-[#8b949e] border border-[#30363d] px-1.5 py-0.5 rounded bg-[#0d1117]">
                    Execution Mode
                  </span>
                </div>

                <div className="space-y-3.5 text-xs">
                  {/* AI Provider */}
                  <div>
                    <label className="text-[#8b949e] block mb-1 font-medium">AI Multimodal Provider</label>
                    <select
                      value={provider}
                      onChange={(e) => setProvider(e.target.value)}
                      className="w-full bg-[#0d1117] border border-[#30363d] rounded p-2 text-[#f0f6fc] font-mono focus:outline-none focus:border-[#f0f6fc]"
                    >
                      <option value="google_gemini">Google Gemini API (Official Multimodal Recommended)</option>
                      <option value="stability">Stability AI (SDXL Virtual Dressing)</option>
                      <option value="openai">OpenAI (GPT-4o Multimodal Vision)</option>
                      <option value="local_cv">Local OpenCV DNN + BiRefNet (Zero-Cost Offline)</option>
                    </select>
                  </div>

                  {/* Vision Model */}
                  <div>
                    <label className="text-[#8b949e] block mb-1 font-medium">Target Neural Model</label>
                    <select
                      value={model}
                      onChange={(e) => setModel(e.target.value)}
                      className="w-full bg-[#0d1117] border border-[#30363d] rounded p-2 text-[#f0f6fc] font-mono focus:outline-none focus:border-[#f0f6fc]"
                    >
                      <option value="gemini-3.1-flash-lite">gemini-3.1-flash-lite (Active &amp; Recommended - Sub-second throughput)</option>
                      <option value="gemini-flash-latest">gemini-flash-latest (Multimodal Vision Production)</option>
                      <option value="gemini-3.8-flash">gemini-3.8-flash (Extended Multimodal Reasoning)</option>
                      <option value="gemini-3.1-pro-preview">gemini-3.1-pro-preview (Master High-Precision Rendering)</option>
                    </select>
                  </div>

                  {/* Beautification AI Mode */}
                  <div>
                    <label className="text-[#8b949e] block mb-1 font-medium">AI Beautification Engine</label>
                    <select
                      value={beautifyMode}
                      onChange={(e) => setBeautifyMode(e.target.value)}
                      className="w-full bg-[#0d1117] border border-[#30363d] rounded p-2 text-[#f0f6fc] font-mono focus:outline-none focus:border-[#f0f6fc]"
                    >
                      <option value="ai_neural_frequency">AI-Driven Neural Frequency Separation &amp; Melanin Protection</option>
                      <option value="deep_melanin_protect">Adaptive Studio Skin Tone Retouching (Local CV)</option>
                    </select>
                  </div>
                </div>

                {/* Quick Diagnostics Strip */}
                <div className="pt-2 border-t border-[#30363d] text-[11px] font-mono text-[#8b949e] space-y-1">
                  <div className="flex justify-between">
                    <span>API Endpoint:</span>
                    <span className="text-[#f0f6fc]">https://generativelanguage.googleapis.com</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Privacy Safeguard:</span>
                    <span className="text-green-400">Zero PII / Student LRN Retained</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: CONFIGURATION */}
        {activeTab === 'config' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-5 rounded-lg border border-[#30363d] bg-[#161b22] space-y-4">
              <h3 className="text-sm font-semibold text-[#f0f6fc]">AI Segmentation Backend</h3>
              <div className="space-y-3 text-xs">
                <div>
                  <label className="text-[#8b949e] block mb-1">Primary Neural Matting Model</label>
                  <select className="w-full bg-[#0d1117] border border-[#30363d] rounded p-2 text-[#f0f6fc] font-mono focus:outline-none">
                    <option>BiRefNet-general-epoch_244.pth (Recommended - MIT)</option>
                    <option>U2Net-portrait-fp16.onnx (Fallback - Apache 2.0)</option>
                  </select>
                </div>
                <div>
                  <label className="text-[#8b949e] block mb-1">Edge Feathering Radius</label>
                  <input
                    type="range"
                    min="1"
                    max="8"
                    defaultValue="3"
                    className="w-full"
                  />
                  <div className="flex justify-between text-[11px] text-[#8b949e] font-mono mt-1">
                    <span>1px (Hard edge)</span>
                    <span>3px (Optimal hair matting)</span>
                    <span>8px (Soft glow)</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-5 rounded-lg border border-[#30363d] bg-[#161b22] space-y-4">
              <h3 className="text-sm font-semibold text-[#f0f6fc]">Licensing &amp; Legal Guardrails</h3>
              <div className="space-y-2 text-xs text-[#8b949e]">
                <div className="p-2.5 rounded bg-[#0d1117] border border-[#30363d] flex items-center justify-between">
                  <span>Non-Commercial Blacklist (CodeFormer / CatVTON)</span>
                  <span className="text-[10px] font-mono text-green-400">ENFORCED</span>
                </div>
                <div className="p-2.5 rounded bg-[#0d1117] border border-[#30363d] flex items-center justify-between">
                  <span>Commercial-Safe Permissive Models (MIT / Apache)</span>
                  <span className="text-[10px] font-mono text-[#f0f6fc]">ACTIVE</span>
                </div>
                <div className="p-2.5 rounded bg-[#0d1117] border border-[#30363d] flex items-center justify-between">
                  <span>Student PII / LRN Scrubbing</span>
                  <span className="text-[10px] font-mono text-[#f0f6fc]">PURGED</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
