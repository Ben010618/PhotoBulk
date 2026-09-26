import React from 'react';
import { Sliders, Sparkles, Shirt, Sun, Palette, Check, Scissors, Layers, CheckCircle2 } from 'lucide-react';
import { BackdropPreset, BeautyPreset, RegaliaProfile } from '../types';

interface SettingsPanelProps {
  bgReplacementEnabled: boolean;
  setBgReplacementEnabled: (v: boolean) => void;
  backdropType: string;
  setBackdropType: (t: string) => void;
  regaliaProfile: string;
  setRegaliaProfile: (p: string) => void;
  beautyPreset: string;
  setBeautyPreset: (p: string) => void;
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
    setBeautyPreset(preset.id);
    setSkinSmoothing(Math.round(preset.skin_smoothing));
    setBlemishRemoval(Math.round(preset.blemish_cut));
    const sc = preset.spot_correction ?? preset.dark_spot_whitening ?? 35;
    handleSpotChange(Math.round(sc));
    setShineCut(Math.round(preset.shine_reduction));
    setGlowIntensity(Math.round(preset.glow_intensity));
    const ec = preset.eye_catchlight ?? preset.catchlight_boost ?? 25;
    handleCatchlightChange(Math.round(ec));
    setTeethWhitening(Math.round(preset.teeth_whitening));
    if (preset.lip_color) setLipColor(preset.lip_color);
    setLipIntensity(Math.round(preset.lip_intensity));
    if (preset.loose_hair_cleanup !== undefined && setLooseHairStrength) {
      setLooseHairStrength(Math.round(preset.loose_hair_cleanup * 100));
    }
  };

  return (
    <div className="w-80 border-l border-[#30363d] bg-[#161b22] flex flex-col h-full overflow-y-auto text-[#c9d1d9] font-sans text-xs">
      {/* Header */}
      <div className="p-4 border-b border-[#30363d] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-[#58a6ff]" />
          <h2 className="font-bold text-[#f0f6fc]">Retouching &amp; Studio Controls</h2>
        </div>
      </div>

      <div className="p-4 space-y-6 flex-1">
        {/* 1. Photographer Presets */}
        <div className="space-y-2">
          <div className="flex items-center gap-1.5 text-[#f0f6fc] font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-[#58a6ff]" />
            <span>Photographer Preset</span>
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
                className={`p-2 rounded border text-left transition flex items-center gap-2 ${
                  backdropType === b.id ? 'border-[#58a6ff] bg-[#1f6feb]/10 text-[#f0f6fc]' : 'border-[#30363d] bg-[#0d1117]'
                }`}
              >
                <span className="w-3.5 h-3.5 rounded-full shrink-0 border border-black/40" style={{ backgroundColor: b.hex }} />
                <span className="truncate text-[11px] font-medium">{b.name.split(' ')[0]}</span>
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
