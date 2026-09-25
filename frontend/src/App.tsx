import React, { useState, useEffect, useRef } from 'react';
import {
  Upload,
  Download,
  FileArchive,
  Cloud,
  Cpu,
  ArrowRight,
  Play,
} from 'lucide-react';

import { Navbar } from './components/Navbar';
import { LandingPage } from './components/LandingPage';
import { AuthPage } from './components/AuthPage';
import { UserDashboard } from './components/UserDashboard';
import { AdminDashboard } from './components/AdminDashboard';
import { PhotoComparisonViewer } from './components/PhotoComparisonViewer';
import { SettingsPanel } from './components/SettingsPanel';
import { BatchFilmstrip } from './components/BatchFilmstrip';
import { TopUpModal } from './components/TopUpModal';

import { api } from './api/client';
import {
  PageView,
  UserSession,
  PhotoItem,
  BackdropPreset,
  BeautyPreset,
  RegaliaProfile,
} from './types';

export default function App() {
  // Page Routing & User Session State
  const [currentPage, setCurrentPage] = useState<PageView>(() => {
    const hash = window.location.hash.replace('#', '') as PageView;
    if (['landing', 'auth', 'user_dashboard', 'admin_dashboard', 'editor'].includes(hash)) {
      return hash;
    }
    return 'editor';
  });

  const [currentUser, setCurrentUser] = useState<UserSession | null>({
    name: 'Juan Dela Cruz',
    email: 'editor@auragrad-studio.ph',
    role: 'photographer',
    studioName: 'AuraGrad Creative Studio Manila',
    credits: 150,
  });

  const [authInitialMode, setAuthInitialMode] = useState<'signin' | 'signup'>('signin');

  // Verify server session on initial load
  useEffect(() => {
    api.getCurrentUser()
      .then((user) => {
        if (user) {
          setCurrentUser(user);
          setCredits(user.credits);
        }
      })
      .catch(() => {
        // Fall back to default local user if offline or unauthenticated
      });
  }, []);

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '') as PageView;
      if (['landing', 'auth', 'user_dashboard', 'admin_dashboard', 'editor'].includes(hash)) {
        setCurrentPage(hash);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const handleNavigate = (page: PageView, authMode?: 'signin' | 'signup') => {
    if (authMode) {
      setAuthInitialMode(authMode);
    }
    setCurrentPage(page);
    window.location.hash = page;
  };

  // Workflow Settings
  const [bgReplacementEnabled, setBgReplacementEnabled] = useState<boolean>(true);
  const [backdropType, setBackdropType] = useState<string>('royal_navy');
  const [regaliaProfile, setRegaliaProfile] = useState<string>('ph_academic_toga');
  const [beautyPreset, setBeautyPreset] = useState<string>('morena_radiant');
  const [skinSmoothing, setSkinSmoothing] = useState<number>(65);
  const [blemishRemoval, setBlemishRemoval] = useState<number>(70);
  const [darkSpotWhitening, setDarkSpotWhitening] = useState<number>(50);
  const [shineCut, setShineCut] = useState<number>(35);
  const [glowIntensity, setGlowIntensity] = useState<number>(40);
  const [catchlightBoost, setCatchlightBoost] = useState<number>(40);
  const [teethWhitening, setTeethWhitening] = useState<number>(45);

  const [lipColor, setLipColor] = useState<string>('#d87093');
  const [lipIntensity, setLipIntensity] = useState<number>(35);

  const [lightingTemp, setLightingTemp] = useState<'warm_3200k' | 'neutral_5500k' | 'cool_6500k'>('neutral_5500k');
  const [studioLightIntensity, setStudioLightIntensity] = useState<number>(20);
  const [rimLightBoost, setRimLightBoost] = useState<number>(20);
  const [togaIron, setTogaIron] = useState<number>(70);

  // Print Mode & Engine
  const [printViewMode, setPrintViewMode] = useState<'master' | '8r' | '2x2'>('master');
  const [engineMode, setEngineMode] = useState<'local_cpu' | 'modal_cloud_gpu'>('modal_cloud_gpu');
  const [credits, setCredits] = useState<number>(150);
  const [showTopUpModal, setShowTopUpModal] = useState<boolean>(false);

  // Canvas / Viewer States
  const [sliderPosition, setSliderPosition] = useState<number>(50);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isZoomed, setIsZoomed] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [batchProgress, setBatchProgress] = useState<number>(0);
  const [isBatchRunning, setIsBatchRunning] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>('');

  // Photos State
  const [photos, setPhotos] = useState<PhotoItem[]>([]);
  const [activePhotoId, setActivePhotoId] = useState<string>('');

  const containerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Presets
  const backdrops: BackdropPreset[] = [
    {
      id: 'royal_navy',
      name: 'Signature Royal Navy & Cobalt Muslin',
      description: 'The standard academic graduation palette used by premier portrait studios (AuraGrad, Lumina).',
      hex: '#122a4d',
    },
    {
      id: 'warm_amber',
      name: 'Warm Amber Radial Strobe Spotlight',
      description: "Replicates a 45-degree overhead studio key-light to naturally separate the subject's cap and tassel.",
      hex: '#b8864a',
    },
    {
      id: 'organic_texture',
      name: 'Organic Hand-Painted Texture',
      description: 'Hand-painted canvas brushstrokes providing analog depth and painterly graduation portraiture.',
      hex: '#4a5359',
    },
    {
      id: 'prc_red',
      name: 'PRC Crimson (Board Exam Standard)',
      description: 'Official Philippine Professional Regulation Commission (PRC) Board Exam crimson red background.',
      hex: '#8a141b',
    },
    {
      id: 'studio_white',
      name: 'Studio Pure White (Passport & Formal)',
      description: 'Crisp high-key pure white seamless background with subtle vignette for official DFA applications.',
      hex: '#f5f6f8',
    },
    {
      id: 'slate_gray',
      name: 'Minimalist Slate Gray',
      description: 'Editorial neutral slate gray backdrop with gentle center spotlight falloff.',
      hex: '#3b4252',
    },
  ];

  const beautyPresets: BeautyPreset[] = [
    {
      id: 'morena_radiant',
      name: 'Morena Radiant (Filipino Gold)',
      description: 'Blemish healing, warm golden melanin balancing & soft studio glow without skin bleaching.',
      skin_smoothing: 65,
      blemish_cut: 70,
      dark_spot_whitening: 50,
      shine_reduction: 35,
      lip_intensity: 35,
      lip_color: '#d87093',
      glow_intensity: 40,
      catchlight_boost: 40,
      teeth_whitening: 45,
    },
    {
      id: 'studio_glamour',
      name: 'Studio Glamour',
      description: 'Eye catchlight accentuation, rosy lip tint, enamel brightening & studio radiance.',
      skin_smoothing: 80,
      blemish_cut: 85,
      dark_spot_whitening: 70,
      shine_reduction: 45,
      lip_intensity: 55,
      lip_color: '#c71585',
      glow_intensity: 55,
      catchlight_boost: 55,
      teeth_whitening: 60,
    },
    {
      id: 'natural_clean',
      name: 'Natural Clean',
      description: 'Preserves 100% authentic skin pore micro-texture, matte T-zone, mild lip tint & subtle iris glint.',
      skin_smoothing: 45,
      blemish_cut: 50,
      dark_spot_whitening: 35,
      shine_reduction: 25,
      lip_intensity: 20,
      lip_color: '#d87093',
      glow_intensity: 20,
      catchlight_boost: 25,
      teeth_whitening: 30,
    },
    {
      id: 'high_key_crisp',
      name: 'High-Key Crisp',
      description: 'High clarity, coral lips, limbal ring accentuation & bright highlights for yearbook print.',
      skin_smoothing: 60,
      blemish_cut: 65,
      dark_spot_whitening: 55,
      shine_reduction: 30,
      lip_intensity: 40,
      lip_color: '#e07a5f',
      glow_intensity: 25,
      catchlight_boost: 50,
      teeth_whitening: 50,
    },
  ];

  const regaliaProfiles: RegaliaProfile[] = [
    {
      id: 'ph_academic_toga',
      name: 'Philippine Academic Toga & Hood',
      iron_strength: 75,
      skin_smoothing: 60,
      shine_reduction: 40,
      edge_protection_level: 'strict',
      description: 'Protects mortarboard caps, tassels, gold cords, and satin hood folds from edge clipping.',
    },
    {
      id: 'up_sablay',
      name: 'UP Sablay Indigenous Sash',
      iron_strength: 50,
      skin_smoothing: 55,
      shine_reduction: 35,
      edge_protection_level: 'ultra_strict',
      description: 'Preserves indigenous hand-woven geometric patterns and gold baybayin embroidery.',
    },
    {
      id: 'barong_tagalog',
      name: 'Barong Tagalog (Piña / Jusi)',
      iron_strength: 60,
      skin_smoothing: 65,
      shine_reduction: 45,
      edge_protection_level: 'strict',
      description: 'Maintains delicate calado embroidery transparency over the camisa de chino undershirt.',
    },
    {
      id: 'formal_blazer',
      name: 'Corporate Formal Suit & Blazer',
      iron_strength: 85,
      skin_smoothing: 60,
      shine_reduction: 30,
      edge_protection_level: 'standard',
      description: 'Flattens lapel wrinkles and lapel pins with crisp pressed shoulder lines.',
    },
  ];

  // Fetch sample portrait on mount
  useEffect(() => {
    fetchSample();
  }, []);

  const fetchSample = async () => {
    try {
      const data = await api.getSample({
        bg_replacement_enabled: bgReplacementEnabled,
        backdrop_type: backdropType,
        beauty_preset: beautyPreset,
      });

      const sampleItem: PhotoItem = {
        id: data.id,
        name: data.filename,
        originalUrl: data.original_data_uri,
        enhancedUrl: data.enhanced_data_uri,
        crop8rUrl: data.crop_8r_data_uri,
        crop2x2Url: data.crop_2x2_data_uri,
        status: 'done',
        analysis: data.analysis,
      };

      setPhotos([sampleItem]);
      setActivePhotoId(sampleItem.id);
      if (data.studio_credits !== undefined) {
        setCredits(data.studio_credits);
      }
    } catch {
      console.warn('API error fetching sample');
    }
  };

  const activePhoto = photos.find((p) => p.id === activePhotoId) || photos[0] || null;

  // Process single active photo
  const handleProcessActive = async () => {
    if (!activePhoto) return;
    setIsProcessing(true);
    setStatusMessage('Processing photo with neural retouching...');

    try {
      const result = await api.processPhoto({
        photo_id: activePhoto.id,
        bg_replacement_enabled: bgReplacementEnabled,
        backdrop_type: backdropType,
        regalia_profile: regaliaProfile,
        beauty_preset: beautyPreset,
        skin_smoothing: skinSmoothing / 100,
        blemish_cut: blemishRemoval / 100,
        dark_spot_whitening: darkSpotWhitening / 100,
        shine_reduction: shineCut / 100,
        lip_color: lipColor,
        lip_intensity: lipIntensity / 100,
        glow_intensity: glowIntensity / 100,
        catchlight_boost: catchlightBoost / 100,
        teeth_whitening: teethWhitening / 100,
        lighting_temp: lightingTemp,
        studio_light_intensity: studioLightIntensity / 100,
        rim_light_boost: rimLightBoost / 100,
        iron_strength: togaIron / 100,
      });

      setPhotos((prev) =>
        prev.map((p) =>
          p.id === activePhoto.id
            ? {
                ...p,
                originalUrl: result.original_data_uri || p.originalUrl,
                enhancedUrl: result.enhanced_data_uri,
                crop8rUrl: result.crop_8r_data_uri,
                crop2x2Url: result.crop_2x2_data_uri,
                analysis: result.analysis || p.analysis,
                status: 'done',
              }
            : p
        )
      );

      if (result.studio_credits !== undefined) {
        setCredits(result.studio_credits);
      }
    } catch (err: any) {
      if (err?.message?.includes('402') || err?.message?.includes('Insufficient')) {
        setShowTopUpModal(true);
      } else {
        console.error('Process active error:', err);
      }
    } finally {
      setIsProcessing(false);
      setStatusMessage('');
    }
  };

  // Bulk Apply to All Photos
  const handleBulkApply = async () => {
    if (photos.length === 0) return;
    setIsBatchRunning(true);
    setBatchProgress(10);

    try {
      setBatchProgress(40);
      const data = await api.batchProcess({
        bg_replacement_enabled: bgReplacementEnabled,
        backdrop_type: backdropType,
        regalia_profile: regaliaProfile,
        beauty_preset: beautyPreset,
        skin_smoothing: skinSmoothing / 100,
        blemish_cut: blemishRemoval / 100,
        dark_spot_whitening: darkSpotWhitening / 100,
        shine_reduction: shineCut / 100,
        lip_color: lipColor,
        lip_intensity: lipIntensity / 100,
        glow_intensity: glowIntensity / 100,
        catchlight_boost: catchlightBoost / 100,
        teeth_whitening: teethWhitening / 100,
        lighting_temp: lightingTemp,
        studio_light_intensity: studioLightIntensity / 100,
        rim_light_boost: rimLightBoost / 100,
        iron_strength: togaIron / 100,
        engine: engineMode,
      });

      setBatchProgress(85);
      const resultMap = new Map(data.items.map((item: any) => [item.id, item]));

      setPhotos((prev) =>
        prev.map((p) => {
          const res: any = resultMap.get(p.id);
          if (res) {
            return {
              ...p,
              originalUrl: res.originalUrl || p.originalUrl,
              enhancedUrl: res.enhancedUrl,
              crop8rUrl: res.crop8rUrl,
              crop2x2Url: res.crop2x2Url,
              analysis: res.analysis || p.analysis,
              status: 'done',
            };
          }
          return { ...p, status: 'done' };
        })
      );

      if (data.studio_credits !== undefined) {
        setCredits(data.studio_credits);
      }
    } catch (err: any) {
      if (err?.message?.includes('402')) {
        setShowTopUpModal(true);
      }
      console.error('Bulk process error:', err);
    } finally {
      setIsBatchRunning(false);
      setBatchProgress(100);
    }
  };

  // Upload Photos
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const files = Array.from(e.target.files);

    try {
      const data = await api.batchUpload(files);
      const uploaded: PhotoItem[] = data.items.map((item: any) => ({
        id: item.id,
        name: item.name,
        originalUrl: item.originalUrl,
        enhancedUrl: item.enhancedUrl,
        crop8rUrl: item.crop8rUrl,
        crop2x2Url: item.crop2x2Url,
        analysis: item.analysis,
        status: 'done',
      }));

      setPhotos((prev) => [...prev, ...uploaded]);
      if (uploaded.length > 0) {
        setActivePhotoId(uploaded[0].id);
      }
    } catch (err) {
      console.error('Batch upload error:', err);
    }
  };

  // Download Single Photo
  const handleDownload = () => {
    if (!activePhoto || !activePhoto.enhancedUrl) return;
    const targetUrl =
      printViewMode === '8r' && activePhoto.crop8rUrl
        ? activePhoto.crop8rUrl
        : printViewMode === '2x2' && activePhoto.crop2x2Url
        ? activePhoto.crop2x2Url
        : activePhoto.enhancedUrl;

    const suffix = printViewMode === '8r' ? '8R_Print' : printViewMode === '2x2' ? '2x2_ID' : 'Master';
    const a = document.createElement('a');
    a.href = targetUrl;
    a.download = `${activePhoto.name.replace(/\.[^/.]+$/, '')}_${suffix}.jpg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  // Download Structured Print Package ZIP
  const handleDownloadZip = () => {
    window.location.href = '/api/export-zip?school_name=Graduation_Batch_2026';
  };

  return (
    <div
      className="flex flex-col h-screen bg-[#0d1117] text-[#c9d1d9] select-none overflow-hidden font-sans"
      onMouseUp={() => setIsDragging(false)}
    >
      {/* 1. Global Navbar */}
      <Navbar
        currentPage={currentPage}
        onNavigate={handleNavigate}
        currentUser={currentUser}
        onLogout={() => {
          api.logout();
          setCurrentUser(null);
        }}
        onOpenTopUp={() => setShowTopUpModal(true)}
      />

      {/* 2. Routing Views */}
      {currentPage === 'landing' && <LandingPage onNavigate={handleNavigate} />}

      {currentPage === 'auth' && (
        <AuthPage
          onNavigate={handleNavigate}
          initialMode={authInitialMode}
          onLoginSuccess={(user) => {
            setCurrentUser(user);
            setCredits(user.credits);
          }}
        />
      )}

      {currentPage === 'user_dashboard' && (
        <UserDashboard
          onNavigate={handleNavigate}
          currentUser={currentUser}
          onOpenTopUp={() => setShowTopUpModal(true)}
        />
      )}

      {currentPage === 'admin_dashboard' && (
        <AdminDashboard onNavigate={handleNavigate} currentUser={currentUser} />
      )}

      {currentPage === 'editor' && (
        <div className="flex-1 flex flex-col overflow-hidden relative">
          {/* Breadcrumb Header */}
          <div className="h-12 border-b border-[#30363d] bg-[#161b22] px-4 flex items-center justify-between z-20 shrink-0 gap-3">
            <div className="flex items-center gap-1.5 text-[11px] overflow-hidden">
              <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-[#21262d] border border-[#30363d] text-[#f0f6fc] font-medium shrink-0">
                <span className="w-3.5 h-3.5 rounded-full bg-[#f0f6fc] text-[#0d1117] flex items-center justify-center text-[9px] font-bold">1</span>
                <span>Bulk Upload ({photos.length})</span>
              </div>
              <ArrowRight className="w-3 h-3 text-[#8b949e] shrink-0" />
              <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-[#21262d] border border-[#30363d] text-[#f0f6fc] font-medium shrink-0">
                <span className="w-3.5 h-3.5 rounded-full bg-[#58a6ff] text-[#0d1117] flex items-center justify-center text-[9px] font-bold">2</span>
                <span>AI Matting &amp; Analysis</span>
              </div>
              <ArrowRight className="w-3 h-3 text-[#8b949e] shrink-0" />
              <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-[#21262d] border border-[#30363d] text-[#f0f6fc] font-medium shrink-0">
                <span className="w-3.5 h-3.5 rounded-full bg-[#3fb950] text-[#0d1117] flex items-center justify-center text-[9px] font-bold">3</span>
                <span>Regalia &amp; Lighting</span>
              </div>
              <ArrowRight className="w-3 h-3 text-[#8b949e] shrink-0" />
              <div className="flex items-center gap-1 px-2 py-0.5 rounded bg-[#21262d] border border-[#30363d] text-[#f0f6fc] font-medium shrink-0">
                <span className="w-3.5 h-3.5 rounded-full bg-[#f0883e] text-[#0d1117] flex items-center justify-center text-[9px] font-bold">4</span>
                <span>Structured Export</span>
              </div>
            </div>

            {/* Right: Engine Switcher & Export Actions */}
            <div className="flex items-center gap-2 shrink-0">
              <div className="hidden lg:flex items-center bg-[#0d1117] p-0.5 rounded-md border border-[#30363d]">
                <button
                  onClick={() => setEngineMode('modal_cloud_gpu')}
                  className={`flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium transition ${
                    engineMode === 'modal_cloud_gpu'
                      ? 'bg-[#21262d] text-[#f0f6fc] border border-[#30363d]'
                      : 'text-[#8b949e] hover:text-[#f0f6fc]'
                  }`}
                >
                  <Cloud className="w-3 h-3 text-[#58a6ff]" />
                  <span>Cloud GPU</span>
                </button>
                <button
                  onClick={() => setEngineMode('local_cpu')}
                  className={`flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium transition ${
                    engineMode === 'local_cpu'
                      ? 'bg-[#21262d] text-[#f0f6fc] border border-[#30363d]'
                      : 'text-[#8b949e] hover:text-[#f0f6fc]'
                  }`}
                >
                  <Cpu className="w-3 h-3 text-[#8b949e]" />
                  <span>Local</span>
                </button>
              </div>

              <input
                type="file"
                multiple
                ref={fileInputRef}
                onChange={handleFileUpload}
                className="hidden"
                accept="image/*"
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-md border border-[#30363d] bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] hover:text-[#f0f6fc] transition shadow-xs"
              >
                <Upload className="w-3.5 h-3.5 text-[#58a6ff]" />
                <span>Upload</span>
                {photos.length > 0 && (
                  <span className="bg-[#30363d] text-[#f0f6fc] text-[10px] px-1.5 py-0.2 rounded-full font-mono">
                    {photos.length}
                  </span>
                )}
              </button>

              <button
                onClick={handleDownloadZip}
                className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-md border border-[#30363d] bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] hover:text-[#f0f6fc] transition shadow-xs"
                title="Download full batch ZIP (Full-Res, 8R, 2x2 IDs, Gang Sheet)"
              >
                <FileArchive className="w-3.5 h-3.5 text-[#f0883e]" />
                <span>Export ZIP</span>
              </button>

              <button
                onClick={handleDownload}
                className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-md bg-[#f0f6fc] hover:bg-[#ffffff] text-[#0d1117] transition active:scale-98 shadow-sm"
              >
                <Download className="w-3.5 h-3.5 text-[#0d1117]" />
                <span>Export Active</span>
              </button>
            </div>
          </div>

          {/* Main Editor Center: Viewer + Right Settings */}
          <div className="flex flex-1 overflow-hidden relative">
            <PhotoComparisonViewer
              activePhoto={activePhoto}
              printViewMode={printViewMode}
              sliderPosition={sliderPosition}
              isZoomed={isZoomed}
              onSliderChange={setSliderPosition}
              onToggleZoom={() => setIsZoomed(!isZoomed)}
              onSetPrintViewMode={setPrintViewMode}
              containerRef={containerRef}
              isDragging={isDragging}
              setIsDragging={setIsDragging}
            />

            <SettingsPanel
              bgReplacementEnabled={bgReplacementEnabled}
              setBgReplacementEnabled={setBgReplacementEnabled}
              backdropType={backdropType}
              setBackdropType={setBackdropType}
              regaliaProfile={regaliaProfile}
              setRegaliaProfile={setRegaliaProfile}
              beautyPreset={beautyPreset}
              setBeautyPreset={setBeautyPreset}
              skinSmoothing={skinSmoothing}
              setSkinSmoothing={setSkinSmoothing}
              blemishRemoval={blemishRemoval}
              setBlemishRemoval={setBlemishRemoval}
              darkSpotWhitening={darkSpotWhitening}
              setDarkSpotWhitening={setDarkSpotWhitening}
              shineCut={shineCut}
              setShineCut={setShineCut}
              glowIntensity={glowIntensity}
              setGlowIntensity={setGlowIntensity}
              catchlightBoost={catchlightBoost}
              setCatchlightBoost={setCatchlightBoost}
              teethWhitening={teethWhitening}
              setTeethWhitening={setTeethWhitening}
              lipColor={lipColor}
              setLipColor={setLipColor}
              lipIntensity={lipIntensity}
              setLipIntensity={setLipIntensity}
              lightingTemp={lightingTemp}
              setLightingTemp={setLightingTemp}
              studioLightIntensity={studioLightIntensity}
              setStudioLightIntensity={setStudioLightIntensity}
              rimLightBoost={rimLightBoost}
              setRimLightBoost={setRimLightBoost}
              togaIron={togaIron}
              setTogaIron={setTogaIron}
              backdrops={backdrops}
              beautyPresets={beautyPresets}
              regaliaProfiles={regaliaProfiles}
              onApplySettings={handleProcessActive}
              isProcessing={isProcessing}
            />
          </div>

          {/* Batch Processing Overlay */}
          {isBatchRunning && (
            <div className="absolute bottom-20 inset-x-12 z-30 bg-[#161b22] border border-[#30363d] p-4 rounded-md shadow-2xl flex items-center gap-4">
              <div className="w-7 h-7 rounded bg-[#21262d] border border-[#30363d] text-[#f0f6fc] flex items-center justify-center shrink-0">
                <Play className="w-3.5 h-3.5" />
              </div>
              <div className="flex-1 space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-[#f0f6fc]">Bulk Batch Processing ({batchProgress}%)</span>
                  <span className="font-mono text-[#8b949e]">
                    {photos.length} Photos • {engineMode === 'modal_cloud_gpu' ? 'Cloud GPU Fleet' : 'Local Engine'}
                  </span>
                </div>
                <div className="w-full bg-[#21262d] border border-[#30363d] h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-[#f0f6fc] h-full transition-all duration-300"
                    style={{ width: `${batchProgress}%` }}
                  ></div>
                </div>
              </div>
            </div>
          )}

          {/* Bottom Batch Filmstrip */}
          <BatchFilmstrip
            photos={photos}
            activePhotoId={activePhotoId}
            onSelectPhoto={setActivePhotoId}
            onUploadClick={() => fileInputRef.current?.click()}
            onProcessAll={handleBulkApply}
            onExportZip={handleDownloadZip}
            isBatchRunning={isBatchRunning}
          />
        </div>
      )}

      {/* Top-Up Modal */}
      <TopUpModal
        isOpen={showTopUpModal}
        onClose={() => setShowTopUpModal(false)}
        onSuccess={(addedCredits) => {
          setCredits((c) => c + addedCredits);
          if (currentUser) {
            setCurrentUser({ ...currentUser, credits: currentUser.credits + addedCredits });
          }
        }}
      />
    </div>
  );
}
