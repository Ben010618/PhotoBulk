import React, { useEffect, useRef, useState } from 'react';
import {
  Upload,
  Download,
  FileArchive,
  Cloud,
  Cpu,
  ArrowRight,
  Play,
  Layers,
  Sliders,
  CheckCircle2,
  FolderOpen
} from 'lucide-react';

import { Navbar } from './components/Navbar';
import { LandingPage } from './components/LandingPage';
import { AuthPage } from './components/AuthPage';
import { UserDashboard } from './components/UserDashboard';
import { AdminPanel } from './components/Admin';
import { PhotoComparisonViewer } from './components/PhotoComparisonViewer';
import { SettingsPanel } from './components/SettingsPanel';
import { BatchFilmstrip } from './components/BatchFilmstrip';
import { ReviewGrid } from './components/ReviewGrid';
import { UploadView } from './components/UploadView';
import { ExportModal } from './components/ExportModal';
import { ToastContainer } from './components/Common/ToastContainer';

import { api } from './api/client';
import { useUIStore } from './store/useUIStore';
import { useAuthStore } from './store/useAuthStore';
import { useEditorStore, WorkflowStep } from './store/useEditorStore';
import {
  BackdropPreset,
  BeautyPreset,
  PhotoItem,
  RegaliaProfile,
} from './types';

export default function App() {
  // Global Stores
  const { currentPage, setCurrentPage, addToast } = useUIStore();
  const { currentUser, setCurrentUser, setCredits, logout } = useAuthStore();
  const {
    currentProjectId,
    currentProjectTitle,
    workflowStep,
    setWorkflowStep,
    setCurrentProjectId,
    setCurrentProjectTitle,
    photos,
    setPhotos,
    activePhotoId,
    setActivePhotoId,
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
    spotCorrection,
    setSpotCorrection,
    darkSpotWhitening,
    setDarkSpotWhitening,
    shineCut,
    setShineCut,
    glowIntensity,
    setGlowIntensity,
    eyeCatchlight,
    setEyeCatchlight,
    catchlightBoost,
    setCatchlightBoost,
    teethWhitening,
    setTeethWhitening,
    looseHairCleanup,
    setLooseHairCleanup,
    looseHairStrength,
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
    printViewMode,
    setPrintViewMode,
    sliderPosition,
    setSliderPosition,
    isZoomed,
    setIsZoomed,
    engineMode,
    setEngineMode,
    isProcessing,
    setIsProcessing,
    isBatchRunning,
    setIsBatchRunning,
    batchProgress,
    setBatchProgress,
  } = useEditorStore();

  const [authInitialMode, setAuthInitialMode] = useState<'signin' | 'signup'>('signin');
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isExportModalOpen, setIsExportModalOpen] = useState<boolean>(false);
  const [isApplyingToAll, setIsApplyingToAll] = useState<boolean>(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 1. Studio Backdrops (Matching Step 4 & background_engine.py)
  const backdrops: BackdropPreset[] = [
    {
      id: 'classic_blue',
      name: 'Classic Graduation Blue Gradient',
      description: 'Rich cobalt and royal blue radial gradient with soft strobe key-light falloff.',
      hex: '#1d457a',
    },
    {
      id: 'deep_navy',
      name: 'Deep Academic Navy',
      description: 'Formal deep navy muslin with subtle strobe vignette behind the head.',
      hex: '#101e33',
    },
    {
      id: 'neutral_grey',
      name: 'Neutral Studio Grey',
      description: 'Clean contemporary editorial studio grey with smooth light center.',
      hex: '#5e656d',
    },
    {
      id: 'studio_white',
      name: 'Studio Pure White (Formal / Passport)',
      description: 'High-key clean seamless white studio background with gentle corner falloff.',
      hex: '#f5f6f8',
    },
    {
      id: 'warm_brown',
      name: 'Warm Studio Brown Canvas',
      description: 'Traditional warm mocha/chestnut painted portrait canvas with soft strobe backlight.',
      hex: '#3d2a1d',
    },
  ];

  // 2. 3 Photographer Presets (Matching Step 6 & beautification_presets.py)
  const beautyPresets: BeautyPreset[] = [
    {
      id: 'natural',
      name: 'Natural Clean',
      description: 'Authentic clean graduation portrait. Natural skin texture, authentic pores, zero plastic smoothing, and subtle eye clarity.',
      skin_smoothing: 45,
      blemish_cut: 50,
      spot_correction: 35,
      dark_spot_whitening: 35,
      shine_reduction: 25,
      lip_intensity: 0,
      glow_intensity: 15,
      eye_catchlight: 25,
      catchlight_boost: 25,
      teeth_whitening: 30,
      loose_hair_cleanup: 30,
      cleanup_loose_hair: true,
    },
    {
      id: 'studio_glow',
      name: 'Studio Glow',
      description: 'Flattering soft key-light bloom, delicate cheekbone glow, polished blemish correction, and subtle eye brightness.',
      skin_smoothing: 60,
      blemish_cut: 65,
      spot_correction: 45,
      dark_spot_whitening: 45,
      shine_reduction: 35,
      lip_intensity: 20,
      glow_intensity: 35,
      eye_catchlight: 35,
      catchlight_boost: 35,
      teeth_whitening: 45,
      loose_hair_cleanup: 50,
      cleanup_loose_hair: true,
    },
    {
      id: 'yearbook_classic',
      name: 'Yearbook Classic',
      description: 'Crisp archival print calibration for commencement framing. Balanced contrast, natural teeth whitening, and formal posture clarity.',
      skin_smoothing: 50,
      blemish_cut: 55,
      spot_correction: 40,
      dark_spot_whitening: 40,
      shine_reduction: 30,
      lip_intensity: 15,
      glow_intensity: 20,
      eye_catchlight: 30,
      catchlight_boost: 30,
      teeth_whitening: 50,
      loose_hair_cleanup: 40,
      cleanup_loose_hair: true,
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

  // Load user session on mount
  useEffect(() => {
    let isMounted = true;
    api.getCurrentUser()
      .then((user) => {
        if (isMounted && user) {
          setCurrentUser(user);
          setCredits(user.credits);
        }
      })
      .catch((err: unknown) => {
        console.warn('Session check skipped, using local studio defaults:', err);
      });
    return () => {
      isMounted = false;
    };
  }, [setCurrentUser, setCredits]);

  // Synchronize system configuration
  useEffect(() => {
    let isMounted = true;
    const fetchConfig = async () => {
      try {
        const res = await api.instance.get('/api/config');
        if (isMounted && res.data) {
          useUIStore.getState().setPaymentsEnabled(Boolean(res.data.payments_enabled));
        }
      } catch (err: unknown) {
        console.warn('[App] Could not fetch system config:', err);
      }
    };
    fetchConfig();
    return () => {
      isMounted = false;
    };
  }, []);

  // Load active project photos on mount
  const refreshProjectPhotos = async (projId: string) => {
    try {
      const data = await api.getProjectPhotos(projId);
      const items: PhotoItem[] = (data.photos || []).map((p: any) => ({
        id: p.id,
        name: p.filename || `${p.id}.jpg`,
        originalUrl: `/api/projects/${projId}/photos/${p.id}/original`,
        enhancedUrl: `/api/projects/${projId}/photos/${p.id}/preview`,
        previewUrl: `/api/projects/${projId}/photos/${p.id}/preview`,
        masterUrl: `/api/projects/${projId}/photos/${p.id}/master`,
        status: p.status || 'ready',
        analysis: p.analysis,
        has_face: p.has_face,
        has_user_override: p.has_user_override,
        review_needed: p.review_needed,
        review_reason: p.review_reason,
        settings: p.settings,
      }));

      setPhotos(items);
      if (items.length > 0 && !activePhotoId) {
        setActivePhotoId(items[0].id);
      }
      return items;
    } catch (err: unknown) {
      console.warn(`[App] Notice refreshing photos for ${projId}:`, err);
      return [];
    }
  };

  useEffect(() => {
    refreshProjectPhotos(currentProjectId).then((items) => {
      if (items.length === 0) {
        setWorkflowStep('upload');
      }
    });
  }, [currentProjectId]);

  const activePhoto = photos.find((p) => p.id === activePhotoId) || photos[0] || null;

  // 1. Process Active Photo Tuning (<1s fast preview update on disk)
  const handleProcessActive = async () => {
    if (!activePhoto) return;
    setIsProcessing(true);

    try {
      const activeSettings = {
        bg_replacement_enabled: bgReplacementEnabled,
        backdrop_type: backdropType,
        regalia_profile: regaliaProfile,
        beauty_preset: beautyPreset,
        skin_smoothing: skinSmoothing / 100,
        blemish_cut: blemishRemoval / 100,
        spot_correction: (spotCorrection ?? darkSpotWhitening) / 100,
        dark_spot_whitening: (spotCorrection ?? darkSpotWhitening) / 100,
        shine_reduction: shineCut / 100,
        lip_color: lipColor,
        lip_intensity: lipIntensity / 100,
        glow_intensity: glowIntensity / 100,
        eye_catchlight: (eyeCatchlight ?? catchlightBoost) / 100,
        teeth_whitening: teethWhitening / 100,
        loose_hair_cleanup: (looseHairStrength ?? 30) / 100,
        cleanup_loose_hair: looseHairCleanup,
        lighting_temp: lightingTemp,
        studio_light_intensity: studioLightIntensity / 100,
        rim_light_boost: rimLightBoost / 100,
        iron_strength: togaIron / 100,
      };

      const res = await api.updatePhotoSettings(
        currentProjectId,
        activePhoto.id,
        activeSettings,
        true
      );

      // Force image cache bust with timestamp
      const cacheBustUrl = `/api/projects/${currentProjectId}/photos/${activePhoto.id}/preview?t=${Date.now()}`;

      setPhotos((prev) =>
        prev.map((p) =>
          p.id === activePhoto.id
            ? {
                ...p,
                enhancedUrl: cacheBustUrl,
                previewUrl: cacheBustUrl,
                has_user_override: true,
                status: 'done',
              }
            : p
        )
      );

      addToast('success', `Adjustments saved in ${res.render_latency_ms || 250} ms.`);
    } catch (err: unknown) {
      console.error('[App] Process photo error:', err);
      const msg = err instanceof Error ? err.message : 'Error applying settings';
      addToast('error', msg);
    } finally {
      setIsProcessing(false);
    }
  };

  // 2. Single to Bulk Apply (Step 7)
  const handleBulkApply = async () => {
    if (!activePhoto || photos.length === 0) return;
    setIsApplyingToAll(true);

    try {
      const res = await api.applyToAll(currentProjectId, activePhoto.id, true);
      addToast(
        'success',
        `Applied look to all! Updated ${res.updated_count} portraits (${res.skipped_count} customized overrides preserved).`
      );

      // Reload project photos to show newly harmonized previews
      await refreshProjectPhotos(currentProjectId);
    } catch (err: unknown) {
      console.error('[App] Apply to all error:', err);
      const msg = err instanceof Error ? err.message : 'Apply to all failed';
      addToast('error', msg);
    } finally {
      setIsApplyingToAll(false);
    }
  };

  const handleDownloadActive = () => {
    if (!activePhoto || !activePhoto.enhancedUrl) return;
    const a = document.createElement('a');
    a.href = activePhoto.enhancedUrl;
    a.download = `${activePhoto.name.replace(/\.[^/.]+$/, '')}_Master_300DPI.jpg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div
      className="flex flex-col h-screen bg-[#0d1117] text-[#c9d1d9] select-none overflow-hidden font-sans"
      onMouseUp={() => setIsDragging(false)}
    >
      {/* Global Toast Notifications */}
      <ToastContainer />

      {/* Global Navbar */}
      <Navbar
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        currentUser={currentUser}
        onLogout={logout}
      />

      {/* Main Page Routing */}
      {currentPage === 'landing' && <LandingPage onNavigate={setCurrentPage} />}

      {currentPage === 'auth' && (
        <AuthPage
          onNavigate={setCurrentPage}
          initialMode={authInitialMode}
          onLoginSuccess={(user) => {
            setCurrentUser(user);
            setCredits(user.credits);
            addToast('success', `Welcome back, ${user.name}!`);
          }}
        />
      )}

      {currentPage === 'user_dashboard' && (
        <UserDashboard
          onNavigate={setCurrentPage}
          currentUser={currentUser}
        />
      )}

      {currentPage === 'admin_dashboard' && (
        <AdminPanel onNavigate={setCurrentPage} />
      )}

      {currentPage === 'editor' && (
        <div className="flex-1 flex flex-col overflow-hidden relative">
          {/* Breadcrumb Header Bar (Step 9 Flow: Projects -> Upload -> Review grid -> Editor -> Bulk Export) */}
          <div className="h-12 border-b border-[#30363d] bg-[#161b22] px-4 flex items-center justify-between z-20 shrink-0 gap-3">
            {/* Step Breadcrumbs */}
            <div className="flex items-center gap-1.5 text-[11px] overflow-x-auto py-1">
              {/* Step 1: Projects */}
              <button
                onClick={() => setCurrentPage('user_dashboard')}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#0d1117] border border-[#30363d] text-[#8b949e] hover:text-[#f0f6fc] hover:border-[#8b949e] font-medium shrink-0 transition"
              >
                <FolderOpen className="w-3.5 h-3.5 text-[#8b949e]" />
                <span className="max-w-[120px] truncate">{currentProjectTitle}</span>
              </button>

              <ArrowRight className="w-3 h-3 text-[#30363d] shrink-0" />

              {/* Step 2: Upload */}
              <button
                onClick={() => setWorkflowStep('upload')}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded font-medium shrink-0 transition border ${
                  workflowStep === 'upload'
                    ? 'bg-[#21262d] border-[#58a6ff] text-[#f0f6fc]'
                    : 'bg-[#0d1117] border-[#30363d] text-[#8b949e] hover:text-[#f0f6fc]'
                }`}
              >
                <span className="w-3.5 h-3.5 rounded-full bg-[#58a6ff] text-[#0d1117] flex items-center justify-center text-[9px] font-bold">
                  1
                </span>
                <span>Upload</span>
              </button>

              <ArrowRight className="w-3 h-3 text-[#30363d] shrink-0" />

              {/* Step 3: Review Grid */}
              <button
                onClick={() => setWorkflowStep('review')}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded font-medium shrink-0 transition border ${
                  workflowStep === 'review'
                    ? 'bg-[#21262d] border-[#58a6ff] text-[#f0f6fc]'
                    : 'bg-[#0d1117] border-[#30363d] text-[#8b949e] hover:text-[#f0f6fc]'
                }`}
              >
                <span className="w-3.5 h-3.5 rounded-full bg-[#f0883e] text-[#0d1117] flex items-center justify-center text-[9px] font-bold">
                  2
                </span>
                <span>Review Grid ({photos.length})</span>
              </button>

              <ArrowRight className="w-3 h-3 text-[#30363d] shrink-0" />

              {/* Step 4: Editor */}
              <button
                onClick={() => setWorkflowStep('editor')}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded font-medium shrink-0 transition border ${
                  workflowStep === 'editor'
                    ? 'bg-[#21262d] border-[#58a6ff] text-[#f0f6fc]'
                    : 'bg-[#0d1117] border-[#30363d] text-[#8b949e] hover:text-[#f0f6fc]'
                }`}
              >
                <span className="w-3.5 h-3.5 rounded-full bg-[#3fb950] text-[#0d1117] flex items-center justify-center text-[9px] font-bold">
                  3
                </span>
                <span>Editor &amp; Presets</span>
              </button>
            </div>

            {/* Right Action Buttons */}
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => setWorkflowStep('upload')}
                className="flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-md border border-[#30363d] bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] hover:text-[#f0f6fc] transition shadow-xs"
              >
                <Upload className="w-3.5 h-3.5 text-[#58a6ff]" />
                <span>Upload Photos</span>
              </button>

              <button
                onClick={() => setIsExportModalOpen(true)}
                className="flex items-center gap-1.5 text-xs font-semibold px-3 py-1 rounded-md bg-[#f0f6fc] hover:bg-[#ffffff] text-[#0d1117] transition shadow-sm"
              >
                <FileArchive className="w-3.5 h-3.5 text-[#f0883e]" />
                <span>Bulk Export (300 DPI)</span>
              </button>
            </div>
          </div>

          {/* Workflow View Switcher */}
          {workflowStep === 'upload' && (
            <UploadView
              projectId={currentProjectId}
              projectTitle={currentProjectTitle}
              onUploadSuccess={() => {
                refreshProjectPhotos(currentProjectId).then(() => {
                  setWorkflowStep('review');
                });
              }}
              onCancel={() => {
                if (photos.length > 0) setWorkflowStep('review');
                else setCurrentPage('user_dashboard');
              }}
            />
          )}

          {workflowStep === 'review' && (
            <ReviewGrid
              photos={photos}
              projectId={currentProjectId}
              projectTitle={currentProjectTitle}
              activePhotoId={activePhotoId}
              onSelectPhoto={(id) => setActivePhotoId(id)}
              onOpenEditor={(id) => {
                if (id) setActivePhotoId(id);
                setWorkflowStep('editor');
              }}
              onOpenUpload={() => setWorkflowStep('upload')}
              onOpenExport={() => setIsExportModalOpen(true)}
              onBackToProjects={() => setCurrentPage('user_dashboard')}
            />
          )}

          {workflowStep === 'editor' && (
            <>
              {photos.length === 0 ? (
                /* Empty Project: Show clean Upload Screen directly as required by Step 9 */
                <UploadView
                  projectId={currentProjectId}
                  projectTitle={currentProjectTitle}
                  onUploadSuccess={() => {
                    refreshProjectPhotos(currentProjectId).then(() => {
                      setWorkflowStep('editor');
                    });
                  }}
                  onCancel={() => setCurrentPage('user_dashboard')}
                />
              ) : (
                <>
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
                      spotCorrection={spotCorrection ?? darkSpotWhitening}
                      setSpotCorrection={setSpotCorrection}
                      darkSpotWhitening={darkSpotWhitening}
                      setDarkSpotWhitening={setDarkSpotWhitening}
                      shineCut={shineCut}
                      setShineCut={setShineCut}
                      glowIntensity={glowIntensity}
                      setGlowIntensity={setGlowIntensity}
                      eyeCatchlight={eyeCatchlight ?? catchlightBoost}
                      setEyeCatchlight={setEyeCatchlight}
                      catchlightBoost={catchlightBoost}
                      setCatchlightBoost={setCatchlightBoost}
                      teethWhitening={teethWhitening}
                      setTeethWhitening={setTeethWhitening}
                      looseHairCleanup={looseHairCleanup}
                      setLooseHairCleanup={setLooseHairCleanup}
                      looseHairStrength={looseHairStrength}
                      setLooseHairStrength={setLooseHairStrength}
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
                      onApplyToAll={handleBulkApply}
                      isProcessing={isProcessing}
                      isApplyingToAll={isApplyingToAll}
                    />
                  </div>

                  {/* Bottom Filmstrip */}
                  <BatchFilmstrip
                    photos={photos}
                    activePhotoId={activePhotoId}
                    onSelectPhoto={setActivePhotoId}
                    onUploadClick={() => setWorkflowStep('upload')}
                    onProcessAll={handleBulkApply}
                    onExportZip={() => setIsExportModalOpen(true)}
                    isBatchRunning={isApplyingToAll}
                  />
                </>
              )}
            </>
          )}
        </div>
      )}

      {/* Bulk Export Modal (Step 8 & 9) */}
      <ExportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        projectId={currentProjectId}
        projectTitle={currentProjectTitle}
        totalPhotos={photos.length}
      />
    </div>
  );
}
