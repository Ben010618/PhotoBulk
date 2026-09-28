import React, { useState } from 'react';
import { Sliders, Sparkles, Shirt, Sun, Palette, Check, Scissors, Layers, CheckCircle2, Flame, Wand2 } from 'lucide-react';
import { BackdropPreset, BeautyPreset, RegaliaProfile, ColorProfile } from '../types';

interface SettingsPanelProps {
  bgReplacementEnabled: boolean;
  setBgReplacementEnabled: (v: boolean) => void;
  backdropType: string;
  setBackdropType: (t: string) => void;
  regaliaProfile: string;
  setRegaliaProfile: (p: string) => void;
  beautyPreset: string;
  setBeautyPreset: (p: string) => void;
  colorProfiles?: ColorProfile[];
  colorProfile?: string;
  setColorProfile?: (p: string) => void;
  colorWarmth?: number;
  setColorWarmth?: (v: number) => void;
  colorContrast?: number;
  setColorContrast?: (v: number) => void;
  colorVibrance?: number;
  setColorVibrance?: (v: number) => void;
  skinSmoothing: number;
  setSkinSmoothing: (v: number) => void;
  blemishRemoval: number;
  setBlemishRemoval: (v: number) => void;
  spotCorrection?: number;
  setSpotCorrection?: (v: number) => void;
  darkSpotWhitening?: number;
  setDarkSpotWhitening?: (v: number) => void;
  shineCut: number;
  setShineCut: (v: number) => void;
  glowIntensity: number;
  setGlowIntensity: (v: number) => void;
  eyeCatchlight?: number;
  setEyeCatchlight?: (v: number) => void;
  catchlightBoost?: number;
  setCatchlightBoost?: (v: number) => void;
  teethWhitening: number;
  setTeethWhitening: (v: number) => void;
  skinBrightening: number;
  setSkinBrightening: (v: number) => void;
  keepMoles: boolean;
  setKeepMoles: (keep: boolean) => void;
  looseHairCleanup?: boolean;
  setLooseHairCleanup?: (v: boolean) => void;
  looseHairStrength?: number;
  setLooseHairStrength?: (v: number) => void;
  lipColor: string;
  setLipColor: (c: string) => void;
  lipIntensity: number;
  setLipIntensity: (v: number) => void;
  lightingTemp: 'warm_3200k' | 'neutral_5500k' | 'cool_6500k';
  setLightingTemp: (t: 'warm_3200k' | 'neutral_5500k' | 'cool_6500k') => void;
  studioLightIntensity: number;
  setStudioLightIntensity: (v: number) => void;
  rimLightBoost: number;
  setRimLightBoost: (v: number) => void;
  togaIron: number;
  setTogaIron: (v: number) => void;
  backdrops: BackdropPreset[];
  beautyPresets: BeautyPreset[];
  regaliaProfiles: RegaliaProfile[];
  onApplySettings: () => void;
  onApplyToAll?: () => void;
  onAiAutoTune?: () => void;
  isAiAutoTuning?: boolean;
  aiAppraisal?: any;
  isProcessing: boolean;
  isApplyingToAll?: boolean;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
  bgReplacementEnabled,
  setBgReplacementEnabled,
  backdropType,
  setBackdropType,
  regaliaProfile,
  setRegaliaProfile,
  beautyPreset,
  setBeautyPreset,
  colorProfiles = [],
  colorProfile = 'clean_commercial',
  setColorProfile,
  colorWarmth = 0,
  setColorWarmth,
  colorContrast = 0,
  setColorContrast,
  colorVibrance = 0,
  setColorVibrance,
  skinSmoothing,
  setSkinSmoothing,
  blemishRemoval,
  setBlemishRemoval,
  spotCorrection = 35,
  setSpotCorrection,
  darkSpotWhitening = 35,
  setDarkSpotWhitening,
  shineCut,
  setShineCut,
  glowIntensity,
  setGlowIntensity,
  eyeCatchlight = 25,
  setEyeCatchlight,
  catchlightBoost = 25,
  setCatchlightBoost,
  teethWhitening,
  setTeethWhitening,
  skinBrightening,
  setSkinBrightening,
  keepMoles,
  setKeepMoles,
  looseHairCleanup = true,
  setLooseHairCleanup,
  looseHairStrength = 30,
  setLooseHairStrength,
  lipColor,
  setLipColor,
  lipIntensity,
  setLipIntensity,
  lightingTemp,
  setLightingTemp,
  studioLightIntensity,
  setStudioLightIntensity,
  rimLightBoost,
  setRimLightBoost,
  togaIron,
  setTogaIron,
  backdrops,
  beautyPresets,
  regaliaProfiles,
  onApplySettings,
  onApplyToAll,
  onAiAutoTune,
  isAiAutoTuning = false,
  aiAppraisal,
  isProcessing,
  isApplyingToAll = false,
}) => {
  const currentSpot = spotCorrection ?? darkSpotWhitening;
  const handleSpotChange = (val: number) => {
    if (setSpotCorrection) setSpotCorrection(val);
    if (setDarkSpotWhitening) setDarkSpotWhitening(val);
  };

  const currentCatchlight = eyeCatchlight ?? catchlightBoost;
  const handleCatchlightChange = (val: number) => {
    if (setEyeCatchlight) setEyeCatchlight(val);
    if (setCatchlightBoost) setCatchlightBoost(val);
  };

  const handleSelectPreset = (preset: BeautyPreset) => {
    // Normalize: backend presets use 0.0–1.0 floats, frontend sliders use 0–100 integers.
    const toPercent = (val: number) => Math.round(val <= 1.0 && val > 0 ? val * 100 : val);

    setBeautyPreset(preset.id);
    setSkinSmoothing(toPercent(preset.skin_smoothing));
    setBlemishRemoval(toPercent(preset.blemish_cut));
    const sc = preset.spot_correction ?? preset.dark_spot_whitening ?? 35;
    handleSpotChange(toPercent(sc));
    setShineCut(toPercent(preset.shine_reduction));
    setGlowIntensity(toPercent(preset.glow_intensity));
    const ec = preset.eye_catchlight ?? preset.catchlight_boost ?? 25;
    handleCatchlightChange(toPercent(ec));
    setTeethWhitening(toPercent(preset.teeth_whitening));
    setSkinBrightening(toPercent(preset.skin_brightening ?? 0));
    if (preset.lip_color) setLipColor(preset.lip_color);
    setLipIntensity(toPercent(preset.lip_intensity));
    if (preset.loose_hair_cleanup !== undefined && setLooseHairStrength) {
      setLooseHairStrength(toPercent(preset.loose_hair_cleanup));
    }
  };

  const activeProfiles: ColorProfile[] = colorProfiles && colorProfiles.length > 0 ? colorProfiles : [
    {
      id: 'clean_commercial',
      name: 'Clean Commercial Studio',
      category: 'Commercial',
      badge: 'Clean Tone',
      description: 'Clean neutral daylight balance, clean whites, balanced skin tones, and modern clarity.'
    },
    {
      id: 'warm_editorial',
      name: 'Warm Editorial Magazine',
      category: 'Editorial',
      badge: 'Vogue Style',
      description: 'Lush honeyed highlights, rich mocha shadow tone, and sun-kissed skin luminescence.'
    },
    {
      id: 'cool_executive',
      name: 'Cool Executive & Academic',
      category: 'Academic',
      badge: 'Corporate',
      description: 'Modern cool 6500K strobe contrast with sharp definition on suits and collars.'
    },
    {
      id: 'golden_hour',
      name: 'Golden Hour Radiance',
      category: 'Artistic',
      badge: 'Warm Glow',
      description: 'Subtle amber warmth in midtones, lifted shadows, and gentle peach glow.'
    },
    {
      id: 'vibrant_archival',
      name: 'Vibrant Archival Print',
      category: 'Print Standard',
      badge: '300 DPI Lab',
      description: 'Enhanced color depth optimized for archival photo lab printing and rich velvet.'
    },
    {
      id: 'cinematic_mood',
      name: 'Cinematic Split-Tone',
      category: 'Cinematic',
      badge: '3D LUT',
      description: 'Subtle split-toning with warm amber highlights and cool teal shadow depth.'
    },
    {
      id: 'monochrome_fine_art',
      name: 'Monochrome Fine Art',
      category: 'Monochrome',
      badge: 'B&W Classic',
      description: 'Timeless black-and-white tonal scale with deep blacks and luminous skin highlights.'
    }
  ];

  return (
    <div className="w-80 border-l border-[#30363d] bg-[#161b22] flex flex-col h-full overflow-y-auto text-[#c9d1d9] font-sans text-xs">
      {/* Header */}
      <div className="p-4 border-b border-[#30363d] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-[#58a6ff]" />
          <h2 className="font-bold text-[#f0f6fc]">Photographer Studio Retouch</h2>
        </div>
        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#1f6feb]/20 text-[#58a6ff] border border-[#58a6ff]/30">
          Aftershoot AI
        </span>
      </div>

      <div className="p-4 space-y-6 flex-1">
        {/* 0. AI Portrait Appraisal & Auto-Tune */}
        <div className="p-3 rounded-lg border border-[#30363d] bg-[#0d1117] space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-[#f0f6fc] flex items-center gap-1.5">
              <Wand2 className="w-3.5 h-3.5 text-amber-400" />
              <span>AI Vision &amp; Quality Appraisal</span>
            </span>
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-400/10 text-amber-300 border border-amber-400/20">
              {aiAppraisal?.provider === 'google_gemini' ? 'Gemini Vision AI' : 'Hybrid AI'}
            </span>
          </div>

          {aiAppraisal && (
            <div className="space-y-1.5 text-[11px] bg-[#161b22] p-2.5 rounded border border-[#30363d]">
              <div className="flex items-center justify-between text-[10px] font-mono">
                <span className="text-[#8b949e]">Melanin Undertone:</span>
                <span className="text-amber-200 font-semibold">{aiAppraisal.tone_label || aiAppraisal.skin_undertone || 'Morena Protected'}</span>
              </div>
              <div className="flex items-center justify-between text-[10px] font-mono">
                <span className="text-[#8b949e]">Studio Lighting:</span>
                <span className="text-[#58a6ff]">{aiAppraisal.lighting_temperature?.replace('_', ' ').toUpperCase() || '5500K STROBE'}</span>
              </div>
              <p className="text-[#8b949e] text-[10px] leading-relaxed pt-1 border-t border-[#30363d]">
                {aiAppraisal.beautify_appraisal}
              </p>
            </div>
          )}

          {onAiAutoTune && (
            <button
              onClick={onAiAutoTune}
              disabled={isAiAutoTuning || isProcessing}
              className="w-full py-2 px-3 rounded text-xs font-semibold bg-gradient-to-r from-amber-600 via-amber-500 to-amber-600 hover:from-amber-500 hover:to-amber-400 text-black transition flex items-center justify-center gap-1.5 shadow-sm disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5 text-black" />
              <span>{isAiAutoTuning ? 'Analyzing & Tuning...' : 'Run AI Auto-Tune & Harmonize'}</span>
            </button>
          )}
        </div>

        {/* 1. Aftershoot-Style AI Color Profiles & 3D LUTs */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-[#f0f6fc] flex items-center gap-1.5">
              <Palette className="w-3.5 h-3.5 text-[#58a6ff]" />
              <span>AI Color Profile &amp; LUT Grading</span>
            </span>
            <span className="text-[10px] text-[#8b949e] font-mono">Dynamic Tonal</span>
          </div>

          <div className="grid grid-cols-2 gap-1.5">
            {activeProfiles.map((p) => {
              const isSelected = colorProfile === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => setColorProfile && setColorProfile(p.id)}
                  className={`p-2 rounded border text-left transition relative flex flex-col justify-between ${
                    isSelected
                      ? 'border-[#58a6ff] bg-[#1f6feb]/15 text-[#f0f6fc]'
                      : 'border-[#30363d] bg-[#0d1117] hover:border-[#8b949e] text-[#8b949e]'
                  }`}
                >
                  <div className="flex items-center justify-between w-full mb-1">
                    <span className="text-[10px] font-mono font-semibold truncate">{p.name.split(' ')[0]}</span>
                    {p.badge && (
                      <span className="text-[8px] font-mono px-1 py-0.2 rounded bg-[#21262d] text-[#c9d1d9]">
                        {p.badge}
                      </span>
                    )}
                  </div>
                  <span className="text-[9px] text-[#8b949e] line-clamp-1">{p.description}</span>
                  {isSelected && (
                    <div className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[#58a6ff]" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Color Adjustments (Warmth, Contrast, Vibrance) */}
          <div className="p-2.5 rounded border border-[#30363d] bg-[#0d1117] space-y-2 font-mono text-[10px]">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-[#8b949e]">Color Temperature (Warmth)</span>
                <span className={colorWarmth > 0 ? 'text-amber-300' : colorWarmth < 0 ? 'text-sky-300' : 'text-[#c9d1d9]'}>
                  {colorWarmth > 0 ? `+${colorWarmth}` : colorWarmth}
                </span>
              </div>
              <input
                type="range"
                min="-50"
                max="50"
                value={colorWarmth}
                onChange={(e) => setColorWarmth && setColorWarmth(Number(e.target.value))}
                className="w-full h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-[#8b949e]">Parametric Contrast (S-Curve)</span>
                <span className="text-[#58a6ff]">{colorContrast > 0 ? `+${colorContrast}` : colorContrast}</span>
              </div>
              <input
                type="range"
                min="-50"
                max="50"
                value={colorContrast}
                onChange={(e) => setColorContrast && setColorContrast(Number(e.target.value))}
                className="w-full h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-[#8b949e]">Skin-Protected Smart Vibrance</span>
                <span className="text-[#58a6ff]">{colorVibrance > 0 ? `+${colorVibrance}` : colorVibrance}</span>
              </div>
              <input
                type="range"
                min="-50"
                max="50"
                value={colorVibrance}
                onChange={(e) => setColorVibrance && setColorVibrance(Number(e.target.value))}
                className="w-full h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* 2. Photographer Beautification Presets */}
        <div className="space-y-2 pt-2 border-t border-[#30363d]">
          <div className="flex items-center gap-1.5 text-[#f0f6fc] font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-[#58a6ff]" />
            <span>Retouching Preset</span>
          </div>
          <div className="grid grid-cols-3 gap-1.5">
            {beautyPresets.map((p) => {
              const isSelected = beautyPreset === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => handleSelectPreset(p)}
                  className={`p-2 rounded border text-center transition flex flex-col items-center justify-center ${
                    isSelected
                      ? 'border-[#58a6ff] bg-[#1f6feb]/15 text-[#f0f6fc] font-semibold'
                      : 'border-[#30363d] bg-[#0d1117] hover:border-[#8b949e] text-[#8b949e]'
                  }`}
                >
                  <span className="truncate text-[11px] block">{p.name.split(' ')[0]}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* 2. Academic Regalia Profile */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-[#f0f6fc] font-semibold">
            <Shirt className="w-3.5 h-3.5 text-[#58a6ff]" />
            <span>Academic Regalia Profile</span>
          </div>
          <div className="space-y-1.5">
            {regaliaProfiles.map((p) => {
              const isSelected = regaliaProfile === p.id;
              return (
                <div
                  key={p.id}
                  onClick={() => {
                    setRegaliaProfile(p.id);
                    setTogaIron(Math.round(p.iron_strength));
                  }}
                  className={`p-2 rounded border cursor-pointer transition flex items-center justify-between ${
                    isSelected ? 'border-[#58a6ff] bg-[#1f6feb]/15 text-[#f0f6fc]' : 'border-[#30363d] bg-[#0d1117] hover:border-[#8b949e]'
                  }`}
                >
                  <div>
                    <span className="font-semibold block">{p.name}</span>
                    <span className="text-[10px] text-[#8b949e]">{p.description}</span>
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-[#58a6ff] shrink-0" />}
                </div>
              );
            })}
          </div>
        </div>

        {/* 3. Studio Backdrop */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-[#f0f6fc] flex items-center gap-1.5">
              <Palette className="w-3.5 h-3.5 text-[#58a6ff]" />
              <span>Studio Muslin Backdrop</span>
            </span>
            <label className="flex items-center gap-1 text-[11px] cursor-pointer">
              <input
                type="checkbox"
                checked={bgReplacementEnabled}
                onChange={(e) => setBgReplacementEnabled(e.target.checked)}
                className="rounded border-[#30363d] bg-[#0d1117] text-[#1f6feb]"
              />
              <span>Matting On</span>
            </label>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {backdrops.map((b) => (
              <button
                key={b.id}
                onClick={() => setBackdropType(b.id)}
                title={b.description}
                className={`p-2 rounded border text-left transition flex items-center gap-2 ${
                  backdropType === b.id ? 'border-[#58a6ff] bg-[#1f6feb]/10 text-[#f0f6fc]' : 'border-[#30363d] bg-[#0d1117]'
                }`}
              >
                <span className="w-3.5 h-3.5 rounded-full shrink-0 border border-black/40" style={{ backgroundColor: b.hex }} />
                <span className="truncate text-[11px] font-medium">{b.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 4. Retouching Sliders */}
        <div className="space-y-4 pt-2 border-t border-[#30363d]">
          <span className="font-semibold text-[#f0f6fc] flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-[#58a6ff]" />
            <span>Semantic Micro-Texture Retouching</span>
          </span>

          <div className="space-y-3 font-mono text-[11px]">
            <div>
              <div className="flex justify-between mb-1">
                <span>Pore-Safe Frequency Smoothing</span>
                <span className="text-[#58a6ff]">{skinSmoothing}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={skinSmoothing}
                onChange={(e) => setSkinSmoothing(Number(e.target.value))}
                className="w-full h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span>Localized Blemish &amp; Acne Healing</span>
                <span className="text-[#58a6ff]">{blemishRemoval}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={blemishRemoval}
                onChange={(e) => setBlemishRemoval(Number(e.target.value))}
                className="w-full h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer"
              />
              <label className="flex items-center gap-1 mt-1 text-[10px] text-[#8b949e] cursor-pointer">
                <input
                  type="checkbox"
                  checked={keepMoles}
                  onChange={(e) => setKeepMoles(e.target.checked)}
                  className="rounded border-[#30363d] bg-[#161b22] text-[#1f6feb]"
                />
                <span>Keep moles &amp; beauty marks</span>
              </label>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span>Spot Correction &amp; Tone Evening</span>
                <span className="text-[#58a6ff]">{currentSpot}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={currentSpot}
                onChange={(e) => handleSpotChange(Number(e.target.value))}
                className="w-full h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span>Skin Brightening (Face &amp; Neck)</span>
                <span className="text-[#58a6ff]">{skinBrightening}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={skinBrightening}
                onChange={(e) => setSkinBrightening(Number(e.target.value))}
                className="w-full h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer"
              />
            </div>

            {/* Loose Hair Cleanup (New Feature Step 6) */}
            <div className="p-2 rounded border border-[#30363d] bg-[#0d1117] space-y-2">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1 text-[#f0f6fc] font-semibold text-[10px]">
                  <Scissors className="w-3 h-3 text-[#58a6ff]" />
                  <span>Loose Hair &amp; Flyaway Cleanup</span>
                </span>
                <label className="flex items-center gap-1 text-[10px] cursor-pointer">
                  <input
                    type="checkbox"
                    checked={looseHairCleanup}
                    onChange={(e) => setLooseHairCleanup && setLooseHairCleanup(e.target.checked)}
                    className="rounded border-[#30363d] bg-[#161b22] text-[#1f6feb]"
                  />
                  <span>Active</span>
                </label>
              </div>

              {looseHairCleanup && (
                <div>
                  <div className="flex justify-between mb-1 text-[10px]">
                    <span className="text-[#8b949e]">Flyaway Silhouette &amp; Forehead Cleanup</span>
                    <span className="text-[#58a6ff]">{looseHairStrength}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={looseHairStrength}
                    onChange={(e) => setLooseHairStrength && setLooseHairStrength(Number(e.target.value))}
                    className="w-full h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer"
                  />
                </div>
              )}
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span>T-Zone Specular De-Shine</span>
                <span className="text-[#58a6ff]">{shineCut}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={shineCut}
                onChange={(e) => setShineCut(Number(e.target.value))}
                className="w-full h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span>Sub-Surface Melanin Radiance</span>
                <span className="text-[#58a6ff]">{glowIntensity}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={glowIntensity}
                onChange={(e) => setGlowIntensity(Number(e.target.value))}
                className="w-full h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span>Eye Catchlights &amp; Iris Sharpness</span>
                <span className="text-[#58a6ff]">{currentCatchlight}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={currentCatchlight}
                onChange={(e) => handleCatchlightChange(Number(e.target.value))}
                className="w-full h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span>Natural Enamel Teeth Whitening</span>
                <span className="text-[#58a6ff]">{teethWhitening}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={teethWhitening}
                onChange={(e) => setTeethWhitening(Number(e.target.value))}
                className="w-full h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span>Toga Fabric Crease Ironing</span>
                <span className="text-[#58a6ff]">{togaIron}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="100"
                value={togaIron}
                onChange={(e) => setTogaIron(Number(e.target.value))}
                className="w-full h-1 bg-[#30363d] rounded-lg appearance-none cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* 5. Studio Environment Lighting */}
        <div className="space-y-3 pt-2 border-t border-[#30363d]">
          <span className="font-semibold text-[#f0f6fc] flex items-center gap-1.5">
            <Sun className="w-3.5 h-3.5 text-[#58a6ff]" />
            <span>Studio Lighting &amp; Strobe Temp</span>
          </span>

          <div className="grid grid-cols-3 gap-1 bg-[#0d1117] p-1 rounded border border-[#30363d]">
            <button
              onClick={() => setLightingTemp('warm_3200k')}
              className={`py-1 rounded text-[10px] font-mono transition ${
                lightingTemp === 'warm_3200k' ? 'bg-[#21262d] text-amber-300' : 'text-[#8b949e]'
              }`}
            >
              3200K Warm
            </button>
            <button
              onClick={() => setLightingTemp('neutral_5500k')}
              className={`py-1 rounded text-[10px] font-mono transition ${
                lightingTemp === 'neutral_5500k' ? 'bg-[#21262d] text-[#f0f6fc]' : 'text-[#8b949e]'
              }`}
            >
              5500K Strobe
            </button>
            <button
              onClick={() => setLightingTemp('cool_6500k')}
              className={`py-1 rounded text-[10px] font-mono transition ${
                lightingTemp === 'cool_6500k' ? 'bg-[#21262d] text-sky-300' : 'text-[#8b949e]'
              }`}
            >
              6500K Cool
            </button>
          </div>
        </div>

        {/* Triggers */}
        <div className="space-y-2 pt-2 border-t border-[#30363d]">
          <button
            onClick={onApplySettings}
            disabled={isProcessing}
            className="w-full py-2.5 px-4 bg-[#238636] hover:bg-[#2ea043] text-white rounded font-semibold text-xs transition shadow-md disabled:opacity-50"
          >
            {isProcessing ? 'Processing Preview (<1s)...' : 'Apply to Active Photo'}
          </button>

          {onApplyToAll && (
            <button
              onClick={onApplyToAll}
              disabled={isApplyingToAll || isProcessing}
              className="w-full py-2 px-4 border border-[#30363d] bg-[#21262d] hover:bg-[#30363d] text-[#f0f6fc] rounded font-semibold text-xs transition flex items-center justify-center gap-1.5 shadow-xs disabled:opacity-50"
              title="Apply look across all portraits with per-photo auto-exposure harmonization"
            >
              <Layers className="w-3.5 h-3.5 text-[#58a6ff]" />
              <span>{isApplyingToAll ? 'Harmonizing Cohort...' : 'Apply Look to All Photos'}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
