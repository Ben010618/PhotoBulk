import React from 'react';
import {
  Sparkles,
  Shirt,
  Smile,
  Layers,
  FileArchive,
  Palette,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  Zap,
  Cpu,
  Download,
  Users,
  Award,
  ChevronRight,
  LogIn,
  UserPlus
} from 'lucide-react';
import { PageView } from './Navbar';

interface LandingPageProps {
  onNavigate: (page: PageView, authMode?: 'signin' | 'signup') => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigate }) => {
  return (
    <div className="flex-1 overflow-y-auto bg-[#0d1117] text-[#c9d1d9] font-sans selection:bg-[#30363d] selection:text-[#f0f6fc]">
      {/* TOP STUDIO ACCESS STRIP WITH LOGIN & SIGNUP */}
      <div className="bg-[#161b22] border-b border-[#30363d] px-6 py-2 flex items-center justify-between text-xs">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span className="text-[#8b949e] font-mono text-[11px]">
            PH Academic Season 2026 Batch Matting &amp; Portrait Engine Online
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate('auth', 'signin')}
            className="flex items-center gap-1.5 px-3 py-1 rounded border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-[#f0f6fc] font-mono transition text-xs"
          >
            <LogIn className="w-3.5 h-3.5 text-[#8b949e]" />
            <span>Login</span>
          </button>
          <button
            onClick={() => onNavigate('auth', 'signup')}
            className="flex items-center gap-1.5 px-3 py-1 rounded bg-[#f0f6fc] hover:bg-white text-[#0d1117] font-semibold font-mono transition text-xs shadow-sm"
          >
            <UserPlus className="w-3.5 h-3.5 text-[#0d1117]" />
            <span>Sign Up</span>
          </button>
        </div>
      </div>

      {/* HERO SECTION */}
      <section className="relative border-b border-[#30363d] py-16 px-6 lg:px-12 bg-gradient-to-b from-[#161b22] to-[#0d1117]">
        <div className="max-w-5xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#30363d] bg-[#0d1117] text-xs font-mono text-[#8b949e]">
            <span className="w-2 h-2 rounded-full bg-[#f0f6fc] animate-pulse"></span>
            <span>Commercial-Safe Permissive AI Architecture</span>
          </div>

          <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-[#f0f6fc] tracking-tight leading-tight">
            High-Volume AI Portrait Studio Suite for the Philippines
          </h1>

          <p className="max-w-3xl mx-auto text-base md:text-lg text-[#8b949e] leading-relaxed">
            Eliminate weeks of manual Photoshop cutout labor. Automatically detach subjects, apply authentic Philippine graduation studio backdrops, preserve rich Morena skin tones with AI neural frequency separation, and generate lab-ready 8R and 2x2 print packages in seconds.
          </p>

          {/* Action CTAs: Studio Editor, Sign In, Sign Up, Dashboard */}
          <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
            <button
              onClick={() => onNavigate('editor')}
              className="px-6 py-3 rounded text-sm font-semibold border border-[#f0f6fc] bg-[#f0f6fc] text-[#0d1117] hover:bg-transparent hover:text-[#f0f6fc] transition flex items-center gap-2 shadow-lg"
            >
              <span>Launch Studio Editor</span>
              <ArrowRight className="w-4 h-4" />
            </button>

            <button
              onClick={() => onNavigate('auth', 'signin')}
              className="px-5 py-3 rounded text-sm font-medium border border-[#30363d] bg-[#161b22] text-[#f0f6fc] hover:bg-[#21262d] hover:border-[#8b949e] transition flex items-center gap-2"
            >
              <LogIn className="w-4 h-4 text-[#8b949e]" />
              <span>Studio Login</span>
            </button>

            <button
              onClick={() => onNavigate('auth', 'signup')}
              className="px-5 py-3 rounded text-sm font-medium border border-[#30363d] bg-[#161b22] text-[#f0f6fc] hover:bg-[#21262d] hover:border-[#8b949e] transition flex items-center gap-2"
            >
              <UserPlus className="w-4 h-4 text-[#8b949e]" />
              <span>Sign Up New Studio</span>
            </button>

            <button
              onClick={() => onNavigate('user_dashboard')}
              className="px-5 py-3 rounded text-sm font-medium border border-[#30363d] bg-[#0d1117] text-[#8b949e] hover:text-[#f0f6fc] hover:bg-[#161b22] transition flex items-center gap-2"
            >
              <span>View Dashboard</span>
            </button>
          </div>

          {/* Key Metric Tags */}
          <div className="pt-8 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto text-left">
            <div className="p-3 rounded border border-[#30363d] bg-[#161b22]">
              <div className="text-xs font-mono text-[#8b949e]">BATCH THROUGHPUT</div>
              <div className="text-xl font-bold text-[#f0f6fc] font-mono mt-0.5">&gt; 1,200 / hr</div>
              <div className="text-[11px] text-[#8b949e] mt-1">Nvidia A10G Cloud Fleet</div>
            </div>
            <div className="p-3 rounded border border-[#30363d] bg-[#161b22]">
              <div className="text-xs font-mono text-[#8b949e]">EDGE MATTING</div>
              <div className="text-xl font-bold text-[#f0f6fc] font-mono mt-0.5">Sub-Pixel</div>
              <div className="text-[11px] text-[#8b949e] mt-1">BiRefNet hair transparency</div>
            </div>
            <div className="p-3 rounded border border-[#30363d] bg-[#161b22]">
              <div className="text-xs font-mono text-[#8b949e]">PRINT ACCURACY</div>
              <div className="text-xl font-bold text-[#f0f6fc] font-mono mt-0.5">300 DPI</div>
              <div className="text-[11px] text-[#8b949e] mt-1">Masters, 8R &amp; 2x2 IDs</div>
            </div>
            <div className="p-3 rounded border border-[#30363d] bg-[#161b22]">
              <div className="text-xs font-mono text-[#8b949e]">IP SAFETY</div>
              <div className="text-xl font-bold text-[#f0f6fc] font-mono mt-0.5">100% Permissive</div>
              <div className="text-[11px] text-[#8b949e] mt-1">Apache 2.0 &amp; MIT Certified</div>
            </div>
          </div>
        </div>
      </section>

      {/* 6-STEP COMPLETE WORKFLOW */}
      <section className="py-16 px-6 lg:px-12 border-b border-[#30363d] max-w-6xl mx-auto">
        <div className="text-center space-y-2 mb-12">
          <div className="text-xs font-mono text-[#8b949e] uppercase tracking-wider">The Standardized Studio Pipeline</div>
          <h2 className="text-2xl md:text-3xl font-bold text-[#f0f6fc]">Six Steps from Raw Camera Capture to Print Package</h2>
          <p className="text-sm text-[#8b949e] max-w-xl mx-auto">
            Engineered specifically to solve the bottleneck of Philippine graduation seasons.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {/* Step 1 */}
          <div className="p-5 rounded-lg border border-[#30363d] bg-[#161b22] space-y-3 hover:border-[#8b949e] transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-[#8b949e] border border-[#30363d] px-2 py-0.5 rounded bg-[#0d1117]">
                STEP 01
              </span>
              <Layers className="w-4 h-4 text-[#8b949e]" />
            </div>
            <h3 className="text-base font-semibold text-[#f0f6fc]">Bulk Multi-Upload</h3>
            <p className="text-xs text-[#8b949e] leading-relaxed">
              Upload hundreds of portraits from full-frame camera tethering in seconds. Automatic thumbnail rendering and batch ID queue tracking.
            </p>
          </div>

          {/* Step 2 */}
          <div className="p-5 rounded-lg border border-[#30363d] bg-[#161b22] space-y-3 hover:border-[#8b949e] transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-[#8b949e] border border-[#30363d] px-2 py-0.5 rounded bg-[#0d1117]">
                STEP 02
              </span>
              <Sparkles className="w-4 h-4 text-[#8b949e]" />
            </div>
            <h3 className="text-base font-semibold text-[#f0f6fc]">Subject Detachment</h3>
            <p className="text-xs text-[#8b949e] leading-relaxed">
              Deep neural segmentation isolates flyaway hair strands, mortarboard caps, and shoulder contours with color despill to eradicate green/gray fringe.
            </p>
          </div>

          {/* Step 3 */}
          <div className="p-5 rounded-lg border border-[#30363d] bg-[#161b22] space-y-3 hover:border-[#8b949e] transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-[#8b949e] border border-[#30363d] px-2 py-0.5 rounded bg-[#0d1117]">
                STEP 03
              </span>
              <Palette className="w-4 h-4 text-[#8b949e]" />
            </div>
            <h3 className="text-base font-semibold text-[#f0f6fc]">Studio Backdrop Replacement</h3>
            <p className="text-xs text-[#8b949e] leading-relaxed">
              Instant swap to industry standards: Signature Royal Navy Muslin, Warm Amber Radial Spotlight, Organic Hand-Painted Canvas, or PRC Crimson.
            </p>
          </div>

          {/* Step 4 */}
          <div className="p-5 rounded-lg border border-[#30363d] bg-[#161b22] space-y-3 hover:border-[#8b949e] transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-[#8b949e] border border-[#30363d] px-2 py-0.5 rounded bg-[#0d1117]">
                STEP 04
              </span>
              <Smile className="w-4 h-4 text-[#8b949e]" />
            </div>
            <h3 className="text-base font-semibold text-[#f0f6fc]">Smart Beautification Presets</h3>
            <p className="text-xs text-[#8b949e] leading-relaxed">
              Frequency separation preserves authentic skin pores while eliminating acne and studio strobe T-zone glare with Morena-tuned golden warmth.
            </p>
          </div>

          {/* Step 5 */}
          <div className="p-5 rounded-lg border border-[#30363d] bg-[#161b22] space-y-3 hover:border-[#8b949e] transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-[#8b949e] border border-[#30363d] px-2 py-0.5 rounded bg-[#0d1117]">
                STEP 05
              </span>
              <Shirt className="w-4 h-4 text-[#8b949e]" />
            </div>
            <h3 className="text-base font-semibold text-[#f0f6fc]">Attire De-Wrinkling &amp; Smoothing</h3>
            <p className="text-xs text-[#8b949e] leading-relaxed">
              Intelligently irons gown creases and fabric wrinkles with boundary erosion while preserving delicate weave, lace embroidery, and collar crispness.
            </p>
          </div>

          {/* Step 6 */}
          <div className="p-5 rounded-lg border border-[#30363d] bg-[#161b22] space-y-3 hover:border-[#8b949e] transition">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-[#8b949e] border border-[#30363d] px-2 py-0.5 rounded bg-[#0d1117]">
                STEP 06
              </span>
              <FileArchive className="w-4 h-4 text-[#8b949e]" />
            </div>
            <h3 className="text-base font-semibold text-[#f0f6fc]">Structured Bulk Export</h3>
            <p className="text-xs text-[#8b949e] leading-relaxed">
              One-click ZIP generation with separated print folders: 300DPI Full-Res Masters, 8R Yearbook Frames (4:5), and 2x2 Formal ID prints.
            </p>
          </div>
        </div>
      </section>

      {/* PHILIPPINE STUDIO BACKDROP & LIGHTING SHOWCASE */}
      <section className="py-16 px-6 lg:px-12 border-b border-[#30363d] bg-[#161b22]">
        <div className="max-w-5xl mx-auto space-y-8">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <div className="text-xs font-mono text-[#8b949e] uppercase">Built for Philippine Portraiture</div>
              <h2 className="text-2xl md:text-3xl font-bold text-[#f0f6fc] mt-1">Authentic Graduation Studio Backdrops</h2>
            </div>
            <button
              onClick={() => onNavigate('editor')}
              className="text-xs font-mono text-[#f0f6fc] hover:underline flex items-center gap-1 self-start md:self-end"
            >
              <span>Test backdrops in editor</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 1. Signature Royal Navy */}
            <div className="p-4 rounded border border-[#30363d] bg-[#0d1117] flex flex-col justify-between space-y-3">
              <div className="space-y-3">
                <div className="w-full h-28 rounded bg-gradient-to-br from-[#152238] via-[#0b1320] to-[#04080e] border border-[#30363d] flex items-center justify-center p-2 relative overflow-hidden">
                  <div className="w-20 h-20 rounded-full bg-[#203a66]/40 blur-xl absolute"></div>
                  <span className="text-xs font-mono text-[#8b949e] z-10">Royal Navy Muslin</span>
                </div>
                <div>
                  <div className="text-sm font-semibold text-[#f0f6fc]">Signature Royal Navy</div>
                  <span className="text-[9px] font-mono text-[#3fb950] bg-[#238636]/20 border border-[#238636]/40 px-1 rounded">Classic Standard</span>
                </div>
              </div>
              <p className="text-xs text-[#8b949e]">
                Deep academic cobalt &amp; navy mottled muslin texture. Standard for UST, Ateneo, and DLSU graduations.
              </p>
              <div className="text-[10px] font-mono text-[#8b949e] border-t border-[#30363d] pt-2">
                4:5 Portrait &bull; 300 DPI
              </div>
            </div>

            {/* 2. Warm Amber Radial */}
            <div className="p-4 rounded border border-[#30363d] bg-[#0d1117] flex flex-col justify-between space-y-3">
              <div className="space-y-3">
                <div className="w-full h-28 rounded bg-gradient-to-br from-[#7c4a1e] via-[#3a200a] to-[#120a02] border border-[#30363d] flex items-center justify-center p-2 relative overflow-hidden">
                  <div className="w-20 h-20 rounded-full bg-[#d97706]/30 blur-xl absolute"></div>
                  <span className="text-xs font-mono text-[#f0f6fc] z-10">Amber Spotlight</span>
                </div>
                <div>
                  <div className="text-sm font-semibold text-[#f0f6fc]">Warm Amber Spotlight</div>
                  <span className="text-[9px] font-mono text-[#d29922] bg-[#9e6a03]/20 border border-[#9e6a03]/40 px-1 rounded">Warm Strobe</span>
                </div>
              </div>
              <p className="text-xs text-[#8b949e]">
                Golden bronze radial studio strobe falloff. Highlights warm Morena skin tones with dramatic editorial depth.
              </p>
              <div className="text-[10px] font-mono text-[#8b949e] border-t border-[#30363d] pt-2">
                3200K Color Temp Match
              </div>
            </div>

            {/* 3. Organic Hand-Painted Canvas */}
            <div className="p-4 rounded border border-[#30363d] bg-[#0d1117] flex flex-col justify-between space-y-3">
              <div className="space-y-3">
                <div className="w-full h-28 rounded bg-gradient-to-br from-[#374151] via-[#1f2937] to-[#111827] border border-[#30363d] flex items-center justify-center p-2 relative overflow-hidden">
                  <div className="w-16 h-16 rounded bg-[#4b5563]/40 blur-lg absolute"></div>
                  <span className="text-xs font-mono text-[#8b949e] z-10">Fine Art Canvas</span>
                </div>
                <div>
                  <div className="text-sm font-semibold text-[#f0f6fc]">Organic Hand-Painted</div>
                  <span className="text-[9px] font-mono text-[#58a6ff] bg-[#388bfd]/20 border border-[#388bfd]/40 px-1 rounded">Editorial Grade</span>
                </div>
              </div>
              <p className="text-xs text-[#8b949e]">
                Neutral charcoal brushed oil texture with feathered vignetting. Ideal for executive, medical, and faculty headshots.
              </p>
              <div className="text-[10px] font-mono text-[#8b949e] border-t border-[#30363d] pt-2">
                Yearbook &amp; Faculty Bios
              </div>
            </div>

            {/* 4. PRC Official Crimson */}
            <div className="p-4 rounded border border-[#30363d] bg-[#0d1117] flex flex-col justify-between space-y-3">
              <div className="space-y-3">
                <div className="w-full h-28 rounded bg-gradient-to-br from-[#800020] via-[#4a0012] to-[#200007] border border-[#30363d] flex items-center justify-center p-2 relative overflow-hidden">
                  <div className="w-20 h-20 rounded-full bg-[#dc2626]/30 blur-xl absolute"></div>
                  <span className="text-xs font-mono text-[#f0f6fc] z-10">Official Crimson</span>
                </div>
                <div>
                  <div className="text-sm font-semibold text-[#f0f6fc]">PRC Official Crimson</div>
                  <span className="text-[9px] font-mono text-[#f85149] bg-[#da3633]/20 border border-[#da3633]/40 px-1 rounded">Licensure Ready</span>
                </div>
              </div>
              <p className="text-xs text-[#8b949e]">
                Vibrant scarlet studio backdrop meeting exact Professional Regulation Commission board exam photo standards.
              </p>
              <div className="text-[10px] font-mono text-[#8b949e] border-t border-[#30363d] pt-2">
                Official 2x2 ID Spec
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* PRICING PLANS */}
      <section className="py-16 px-6 lg:px-12 border-b border-[#30363d] max-w-5xl mx-auto">
        <div className="text-center space-y-2 mb-12">
          <div className="text-xs font-mono text-[#8b949e] uppercase">Simple Studio Credits</div>
          <h2 className="text-2xl md:text-3xl font-bold text-[#f0f6fc]">Flexible Studio Pricing for Graduation Seasons</h2>
          <p className="text-sm text-[#8b949e]">
            Pay only for processed portraits. No recurring subscription lock-in.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Starter Plan */}
          <div className="p-6 rounded-lg border border-[#30363d] bg-[#161b22] space-y-4">
            <div className="space-y-1">
              <h3 className="text-base font-semibold text-[#f0f6fc]">Studio Starter</h3>
              <p className="text-xs text-[#8b949e]">For independent photographers</p>
            </div>
            <div className="text-2xl font-bold font-mono text-[#f0f6fc]">
              ₱1,499 <span className="text-xs font-normal text-[#8b949e]">/ 300 credits</span>
            </div>
            <ul className="text-xs space-y-2 text-[#8b949e] border-t border-[#30363d] pt-4">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#f0f6fc]" />
                <span>300 High-Res AI Portraits</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#f0f6fc]" />
                <span>All 4 Philippine Studio Backdrops</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#f0f6fc]" />
                <span>AI Neural Frequency Beautification</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#8b949e]" />
                <span>Bulk ZIP Export (8R + 2x2)</span>
              </li>
            </ul>
            <button
              onClick={() => onNavigate('auth')}
              className="w-full py-2 rounded text-xs font-medium border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-[#f0f6fc] transition"
            >
              Get Started
            </button>
          </div>

          {/* Pro Studio Plan */}
          <div className="p-6 rounded-lg border-2 border-[#f0f6fc] bg-[#161b22] space-y-4 relative shadow-lg">
            <div className="absolute -top-3 right-4 px-2 py-0.5 rounded bg-[#f0f6fc] text-[#0d1117] text-[10px] font-bold font-mono uppercase">
              Most Popular
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-semibold text-[#f0f6fc]">High-Volume Studio</h3>
              <p className="text-xs text-[#8b949e]">For commercial graduation studios</p>
            </div>
            <div className="text-2xl font-bold font-mono text-[#f0f6fc]">
              ₱4,999 <span className="text-xs font-normal text-[#8b949e]">/ 1,500 credits</span>
            </div>
            <ul className="text-xs space-y-2 text-[#c9d1d9] border-t border-[#30363d] pt-4">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#f0f6fc]" />
                <span>1,500 High-Res AI Portraits</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#f0f6fc]" />
                <span>Priority Cloud GPU Processing (&lt;250ms)</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#f0f6fc]" />
                <span>Bulk Master ZIP Downloads</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#f0f6fc]" />
                <span>Multi-Operator Studio Dashboard</span>
              </li>
            </ul>
            <button
              onClick={() => onNavigate('editor')}
              className="w-full py-2 rounded text-xs font-semibold bg-[#f0f6fc] hover:bg-white text-[#0d1117] transition"
            >
              Start Processing Batch
            </button>
          </div>

          {/* Enterprise Plan */}
          <div className="p-6 rounded-lg border border-[#30363d] bg-[#161b22] space-y-4">
            <div className="space-y-1">
              <h3 className="text-base font-semibold text-[#f0f6fc]">University Enterprise</h3>
              <p className="text-xs text-[#8b949e]">For nationwide university contracts</p>
            </div>
            <div className="text-2xl font-bold font-mono text-[#f0f6fc]">
              Custom <span className="text-xs font-normal text-[#8b949e]">/ 10k+ credits</span>
            </div>
            <ul className="text-xs space-y-2 text-[#8b949e] border-t border-[#30363d] pt-4">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#f0f6fc]" />
                <span>10,000+ Batch Queue</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#f0f6fc]" />
                <span>Dedicated Nvidia A10G Cluster</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#f0f6fc]" />
                <span>Custom Studio Backdrops &amp; Presets</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-[#f0f6fc]" />
                <span>SLA &amp; Direct Studio Support</span>
              </li>
            </ul>
            <button
              onClick={() => onNavigate('auth')}
              className="w-full py-2 rounded text-xs font-medium border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-[#f0f6fc] transition"
            >
              Contact Sales
            </button>
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-[#30363d] py-10 px-6 lg:px-12 bg-[#0d1117] text-xs text-[#8b949e]">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm text-[#f0f6fc]">KameraPh Studio Suite</span>
            <span>&bull;</span>
            <span>Manila, Philippines</span>
          </div>
          <div className="font-mono text-[11px]">
            Commercial-Safe &bull; Apache 2.0 &amp; MIT Certified Stack &bull; 2026
          </div>
        </div>
      </footer>
    </div>
  );
};
