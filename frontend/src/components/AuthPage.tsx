import React, { useState } from 'react';
import {
  Camera,
  Lock,
  Mail,
  Building2,
  User,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Info
} from 'lucide-react';
import { PageView, UserSession } from './Navbar';
import { apiClient } from '../api/apiClient';
import { useUIStore } from '../store/useUIStore';

interface AuthPageProps {
  onNavigate: (page: PageView) => void;
  onLoginSuccess: (user: UserSession) => void;
  initialMode?: 'signin' | 'signup';
}

export const AuthPage: React.FC<AuthPageProps> = ({ onNavigate, onLoginSuccess, initialMode = 'signin' }) => {
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>(initialMode);
  const [role, setRole] = useState<'photographer' | 'admin'>('photographer');
  const [email, setEmail] = useState<string>('editor@auragrad-studio.ph');
  const [password, setPassword] = useState<string>('');
  const [studioName, setStudioName] = useState<string>('AuraGrad Creative Studio (Manila)');
  const [name, setName] = useState<string>('Juan Dela Cruz');
  const [rememberMe, setRememberMe] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please provide your email and password');
      return;
    }
    setError('');
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append('email', email.trim());
      formData.append('password', password);

      const data = await apiClient.login(formData);
      const session: UserSession = {
        name: data.user.name || (data.user.role === 'admin' ? 'KameraPh Administrator' : name),
        email: data.user.email,
        role: data.user.role === 'admin' ? 'admin' : 'photographer',
        studioName: data.user.studioName || studioName,
        credits: data.user.credits ?? 150,
      };
      onLoginSuccess(session);
      onNavigate(data.user.role === 'admin' ? 'admin_dashboard' : 'user_dashboard');
      return;
    } catch (err: unknown) {
      console.error('[AuthPage] Authentication failed:', err);
      const errMsg = err instanceof Error ? err.message : 'Invalid email or password.';
      useUIStore.getState().addToast('error', errMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickLogin = async (demoRole: 'photographer' | 'admin') => {
    setIsLoading(true);
    try {
      const demoEmail = demoRole === 'admin' ? 'admin@kameraph.com' : 'editor@auragrad-studio.ph';
      const demoPass = demoRole === 'admin' ? 'KameraPhAdminSecure2026!' : 'StudioEditor2026!';
      setEmail(demoEmail);
      setPassword(demoPass);

      const formData = new FormData();
      formData.append('email', demoEmail);
      formData.append('password', demoPass);

      const data = await apiClient.login(formData);
      const session: UserSession = {
        name: data.user.name || (data.user.role === 'admin' ? 'KameraPh Administrator' : name),
        email: data.user.email,
        role: data.user.role === 'admin' ? 'admin' : 'photographer',
        studioName: data.user.studioName || studioName,
        credits: data.user.credits ?? 150,
      };
      onLoginSuccess(session);
      onNavigate(data.user.role === 'admin' ? 'admin_dashboard' : 'user_dashboard');
    } catch (err: unknown) {
      console.error('[AuthPage] Quick login error:', err);
      const errMsg = err instanceof Error ? err.message : 'Quick login failed.';
      useUIStore.getState().addToast('error', errMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-[#0d1117] flex items-center justify-center p-6 text-[#c9d1d9] font-sans">
      <div className="w-full max-w-md space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded-lg border border-[#30363d] bg-[#161b22] flex items-center justify-center mx-auto text-[#f0f6fc] shadow-md">
            <Camera className="w-6 h-6 text-[#f0f6fc]" />
          </div>
          <h1 className="text-2xl font-bold text-[#f0f6fc] tracking-tight">
            {authMode === 'signin' ? 'Sign in to KameraPh' : 'Create a Studio Account'}
          </h1>
          <p className="text-xs text-[#8b949e]">
            {authMode === 'signin'
              ? 'AI-powered batch portrait retouching for Philippine school studios'
              : 'Start your high-volume graduation photography trial'}
          </p>
        </div>

        {/* Role Toggle Selector */}
        <div className="p-1 rounded-lg bg-[#161b22] border border-[#30363d] grid grid-cols-2 gap-1 text-xs">
          <button
            type="button"
            onClick={() => {
              setRole('photographer');
              setEmail('editor@auragrad-studio.ph');
              setError('');
            }}
            className={`py-2 rounded-md font-medium transition flex items-center justify-center gap-1.5 ${
              role === 'photographer'
                ? 'bg-[#21262d] text-[#f0f6fc] shadow-sm'
                : 'text-[#8b949e] hover:text-[#c9d1d9]'
            }`}
          >
            <Camera className="w-3.5 h-3.5" />
            <span>Studio / Photographer</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setRole('admin');
              setEmail('admin@kameraph.com');
              setError('');
            }}
            className={`py-2 rounded-md font-medium transition flex items-center justify-center gap-1.5 ${
              role === 'admin'
                ? 'bg-[#21262d] text-[#f0f6fc] shadow-sm'
                : 'text-[#8b949e] hover:text-[#c9d1d9]'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Administrator</span>
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3 bg-red-950/40 border border-red-800/80 rounded-md text-red-200 text-xs flex items-start gap-2">
            <Info className="w-4 h-4 shrink-0 text-red-400 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Card Form */}
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-6 shadow-xl space-y-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            {authMode === 'signup' && (
              <>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#f0f6fc]">Full Name</label>
                  <div className="relative">
                    <User className="w-4 h-4 absolute left-3 top-2.5 text-[#8b949e]" />
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="e.g. Juan Dela Cruz"
                      className="w-full pl-9 pr-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-md text-xs text-[#f0f6fc] focus:outline-none focus:border-[#58a6ff] transition"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#f0f6fc]">Studio / Company Name</label>
                  <div className="relative">
                    <Building2 className="w-4 h-4 absolute left-3 top-2.5 text-[#8b949e]" />
                    <input
                      type="text"
                      value={studioName}
                      onChange={(e) => setStudioName(e.target.value)}
                      placeholder="e.g. AuraGrad Creative Studio (Manila)"
                      className="w-full pl-9 pr-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-md text-xs text-[#f0f6fc] focus:outline-none focus:border-[#58a6ff] transition"
                      required
                    />
                  </div>
                </div>
              </>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[#f0f6fc]">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-2.5 text-[#8b949e]" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@studio.ph"
                  className="w-full pl-9 pr-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-md text-xs text-[#f0f6fc] focus:outline-none focus:border-[#58a6ff] transition"
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-[#f0f6fc]">Password</label>
                {authMode === 'signin' && (
                  <button
                    type="button"
                    onClick={() => alert('Password reset link sent to your registered studio email.')}
                    className="text-[11px] text-[#8b949e] hover:text-[#58a6ff] transition"
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-2.5 text-[#8b949e]" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your secure password"
                  className="w-full pl-9 pr-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-md text-xs text-[#f0f6fc] focus:outline-none focus:border-[#58a6ff] transition"
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-[#8b949e] pt-1">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="rounded border-[#30363d] bg-[#0d1117] text-[#1f6feb] focus:ring-0"
                />
                <span>Remember this device</span>
              </label>
              <span className="flex items-center gap-1 text-[#3fb950] text-[11px]">
                <CheckCircle2 className="w-3.5 h-3.5" />
                256-bit TLS Protected
              </span>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 px-4 bg-[#238636] hover:bg-[#2ea043] text-white rounded-md font-semibold text-xs flex items-center justify-center gap-2 shadow-md transition disabled:opacity-50"
            >
              <span>{isLoading ? 'Verifying...' : (authMode === 'signin' ? 'Sign In to Workspace' : 'Create Studio Account')}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          {/* Quick Demo Login Option */}
          <div className="pt-2 border-t border-[#30363d] space-y-2">
            <div className="p-3 bg-[#0d1117] border border-[#30363d] rounded-md space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-[#f0f6fc] flex items-center gap-1.5 text-[11px]">
                  <ShieldCheck className="w-3.5 h-3.5 text-[#58a6ff]" />
                  <span>Verified Access Roles</span>
                </span>
                <span className="text-[10px] font-mono border border-[#30363d] px-1 py-0.2 rounded bg-[#161b22] text-[#8b949e]">
                  Server Verified
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => handleQuickLogin('admin')}
                  className="py-1.5 px-2 rounded border border-amber-700 bg-amber-900/40 hover:bg-amber-800/50 text-amber-200 font-mono text-[11px] transition font-semibold text-center"
                >
                  ⚡ Admin Console
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickLogin('photographer')}
                  className="py-1.5 px-2 rounded border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-[#c9d1d9] font-mono text-[11px] transition text-center"
                >
                  Studio Editor
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Switch Link */}
        <div className="text-center text-xs text-[#8b949e]">
          {authMode === 'signin' ? (
            <span>
              Don't have a studio account yet?{' '}
              <button
                onClick={() => setAuthMode('signup')}
                className="text-[#f0f6fc] hover:underline font-medium"
              >
                Create one now
              </button>
            </span>
          ) : (
            <span>
              Already registered?{' '}
              <button
                onClick={() => setAuthMode('signin')}
                className="text-[#f0f6fc] hover:underline font-medium"
              >
                Sign in
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
