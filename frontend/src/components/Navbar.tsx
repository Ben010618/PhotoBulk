import React from 'react';
import {
  Layers,
  LayoutDashboard,
  ShieldAlert,
  Camera,
  LogIn,
  LogOut,
  Sparkles,
  Home,
  User,
  Zap,
  ChevronDown
} from 'lucide-react';

import { PageView, UserSession } from '../types';
import { useUIStore } from '../store/useUIStore';
export type { PageView, UserSession };

interface NavbarProps {
  currentPage: PageView;
  onNavigate: (page: PageView) => void;
  currentUser: UserSession | null;
  onLogout: () => void;
  onOpenTopUp?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentPage,
  onNavigate,
  currentUser,
  onLogout,
  onOpenTopUp,
}) => {
  const paymentsEnabled = useUIStore((s) => s.paymentsEnabled);
  return (
    <header className="h-14 border-b border-[#30363d] bg-[#161b22] px-4 flex items-center justify-between z-30 shrink-0 select-none">
      {/* Brand & Main Nav */}
      <div className="flex items-center gap-6">
        <div
          onClick={() => onNavigate('landing')}
          className="flex items-center gap-2.5 cursor-pointer group"
        >
          <div className="w-8 h-8 rounded border border-[#30363d] bg-[#0d1117] flex items-center justify-center text-[#f0f6fc] group-hover:border-[#8b949e] transition shadow-sm">
            <Camera className="w-4 h-4 text-[#f0f6fc]" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-sm text-[#f0f6fc] tracking-tight">KameraPh</span>
              <span className="text-[10px] font-mono border border-[#30363d] px-1 py-0.2 rounded bg-[#0d1117] text-[#8b949e]">
                v5.0
              </span>
            </div>
            <p className="text-[10px] text-[#8b949e] hidden sm:block">PH Studio Portrait Suite</p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-1 font-mono text-xs">
          <button
            onClick={() => onNavigate('landing')}
            className={`px-3 py-1.5 rounded transition flex items-center gap-1.5 ${
              currentPage === 'landing'
                ? 'bg-[#21262d] text-[#f0f6fc] border border-[#30363d]'
                : 'text-[#8b949e] hover:text-[#f0f6fc] hover:bg-[#21262d]/50'
            }`}
          >
            <Home className="w-3.5 h-3.5" />
            <span>Home</span>
          </button>

          <button
            onClick={() => onNavigate('editor')}
            className={`px-3 py-1.5 rounded transition flex items-center gap-1.5 ${
              currentPage === 'editor'
                ? 'bg-[#21262d] text-[#f0f6fc] border border-[#30363d]'
                : 'text-[#8b949e] hover:text-[#f0f6fc] hover:bg-[#21262d]/50'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Studio Editor</span>
          </button>

          <button
            onClick={() => onNavigate('user_dashboard')}
            className={`px-3 py-1.5 rounded transition flex items-center gap-1.5 ${
              currentPage === 'user_dashboard'
                ? 'bg-[#21262d] text-[#f0f6fc] border border-[#30363d]'
                : 'text-[#8b949e] hover:text-[#f0f6fc] hover:bg-[#21262d]/50'
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span>Studio Dashboard</span>
          </button>

          <button
            onClick={() => onNavigate('admin_dashboard')}
            className={`px-3 py-1.5 rounded transition flex items-center gap-1.5 ${
              currentPage === 'admin_dashboard'
                ? 'bg-[#21262d] text-[#f0f6fc] border border-[#30363d]'
                : 'text-[#8b949e] hover:text-[#f0f6fc] hover:bg-[#21262d]/50'
            }`}
            title={currentUser?.role === 'admin' ? 'Admin Console' : 'Admin Console (Administrator Privileges Required)'}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Admin Console</span>
            {currentUser?.role !== 'admin' && (
              <span className="text-[9px] font-mono px-1 rounded bg-[#0d1117] text-amber-400 border border-[#30363d]">
                Admin
              </span>
            )}
          </button>
        </nav>
      </div>

      {/* Right Controls / Auth / Credits */}
      <div className="flex items-center gap-3">
        {currentUser ? (
          <>
            {/* Studio Credits Badge */}
            {paymentsEnabled && (
              <div
                onClick={onOpenTopUp}
                className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded bg-[#0d1117] border border-[#30363d] cursor-pointer hover:border-[#8b949e] transition text-xs font-mono"
                title="Click to manage studio credits"
              >
                <Zap className="w-3.5 h-3.5 text-[#f0f6fc]" />
                <span className="text-[#8b949e]">Credits:</span>
                <span className="text-[#f0f6fc] font-semibold">{currentUser.credits}</span>
              </div>
            )}

            {/* User Profile Badge */}
            <div className="flex items-center gap-2 pl-2 border-l border-[#30363d]">
              <div className="w-7 h-7 rounded border border-[#30363d] bg-[#21262d] flex items-center justify-center text-[#f0f6fc] text-xs font-mono font-semibold">
                {currentUser.name.charAt(0)}
              </div>
              <div className="hidden lg:block text-left text-xs">
                <div className="text-[#f0f6fc] font-medium leading-none">{currentUser.name}</div>
                <div className="text-[10px] text-[#8b949e] font-mono leading-none mt-1">
                  {currentUser.role === 'admin' ? 'Studio Owner' : 'Lead Editor'}
                </div>
              </div>
              <button
                onClick={onLogout}
                className="p-1.5 rounded hover:bg-[#21262d] text-[#8b949e] hover:text-[#f0f6fc] transition"
                title="Sign out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </>
        ) : (
          <button
            onClick={() => onNavigate('auth')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-mono font-medium border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-[#f0f6fc] transition shadow-sm"
          >
            <LogIn className="w-3.5 h-3.5 text-[#8b949e]" />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </header>
  );
};
