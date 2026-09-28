import { create } from 'zustand';
import { PhotoItem } from '../types';

export type WorkflowStep = 'projects' | 'upload' | 'review' | 'editor' | 'export';

interface EditorState {
  // Project & Workflow State
  currentProjectId: string;
  currentProjectTitle: string;
  workflowStep: WorkflowStep;
  setCurrentProjectId: (id: string) => void;
  setCurrentProjectTitle: (title: string) => void;
  setWorkflowStep: (step: WorkflowStep) => void;

  // Photos Queue
  photos: PhotoItem[];
  activePhotoId: string;
  setPhotos: (photos: PhotoItem[] | ((prev: PhotoItem[]) => PhotoItem[])) => void;
  setActivePhotoId: (id: string) => void;
  updatePhoto: (id: string, updates: Partial<PhotoItem>) => void;

  // Presets & Toggles
  bgReplacementEnabled: boolean;
  backdropType: string;
  regaliaProfile: string;
  beautyPreset: string;
  setBgReplacementEnabled: (enabled: boolean) => void;
  setBackdropType: (type: string) => void;
  setRegaliaProfile: (profile: string) => void;
  setBeautyPreset: (preset: string) => void;

  // Sliders (Accurate Step 6 & 9 Naming)
  skinSmoothing: number;
  blemishRemoval: number;
  spotCorrection: number;
  darkSpotWhitening: number; // backward-compat alias
  shineCut: number;
  glowIntensity: number;
  eyeCatchlight: number;
  catchlightBoost: number; // backward-compat alias
  teethWhitening: number;
  skinBrightening: number;
  keepMoles: boolean;
  looseHairCleanup: boolean;
  looseHairStrength: number;
  lipColor: string;
  lipIntensity: number;
  lightingTemp: 'warm_3200k' | 'neutral_5500k' | 'cool_6500k';
  studioLightIntensity: number;
  rimLightBoost: number;
  togaIron: number;
  colorProfile: string;
  colorWarmth: number;
  colorContrast: number;
  colorVibrance: number;

  setColorProfile: (profile: string) => void;
  setColorWarmth: (warmth: number) => void;
  setColorContrast: (contrast: number) => void;
  setColorVibrance: (vibrance: number) => void;

  setSkinSmoothing: (v: number) => void;
  setBlemishRemoval: (v: number) => void;
  setSpotCorrection: (v: number) => void;
  setDarkSpotWhitening: (v: number) => void;
  setShineCut: (v: number) => void;
  setGlowIntensity: (v: number) => void;
  setEyeCatchlight: (v: number) => void;
  setCatchlightBoost: (v: number) => void;
  setTeethWhitening: (v: number) => void;
  setSkinBrightening: (v: number) => void;
  setKeepMoles: (keep: boolean) => void;
  setLooseHairCleanup: (enabled: boolean) => void;
  setLooseHairStrength: (v: number) => void;
  setLipColor: (c: string) => void;
  setLipIntensity: (v: number) => void;
  setLightingTemp: (t: 'warm_3200k' | 'neutral_5500k' | 'cool_6500k') => void;
  setStudioLightIntensity: (v: number) => void;
  setRimLightBoost: (v: number) => void;
  setTogaIron: (v: number) => void;

  // Viewer State
  printViewMode: 'master' | '8r' | '2x2';
  sliderPosition: number;
  isZoomed: boolean;
  engineMode: 'local_cpu' | 'modal_cloud_gpu';
  isProcessing: boolean;
  isBatchRunning: boolean;
  batchProgress: number;

  setPrintViewMode: (mode: 'master' | '8r' | '2x2') => void;
  setSliderPosition: (pos: number) => void;
  setIsZoomed: (zoomed: boolean) => void;
  setEngineMode: (mode: 'local_cpu' | 'modal_cloud_gpu') => void;
  setIsProcessing: (processing: boolean) => void;
  setIsBatchRunning: (running: boolean) => void;
  setBatchProgress: (progress: number) => void;
}

export const useEditorStore = create<EditorState>((set) => ({
  currentProjectId: 'default_project',
  currentProjectTitle: 'Graduation Cohort 2026',
  workflowStep: 'projects',
  setCurrentProjectId: (id) => set({ currentProjectId: id }),
  setCurrentProjectTitle: (title) => set({ currentProjectTitle: title }),
  setWorkflowStep: (step) => set({ workflowStep: step }),

  photos: [],
  activePhotoId: '',
  setPhotos: (photos) =>
    set((state) => ({
      photos: typeof photos === 'function' ? photos(state.photos) : photos,
    })),
  setActivePhotoId: (id) => set({ activePhotoId: id }),
  updatePhoto: (id, updates) =>
    set((state) => ({
      photos: state.photos.map((p) => (p.id === id ? { ...p, ...updates } : p)),
    })),

  bgReplacementEnabled: true,
  backdropType: 'classic_blue',
  regaliaProfile: 'ph_academic_toga',
  beautyPreset: 'natural',

  setBgReplacementEnabled: (enabled) => set({ bgReplacementEnabled: enabled }),
  setBackdropType: (type) => set({ backdropType: type }),
  setRegaliaProfile: (profile) => set({ regaliaProfile: profile }),
  setBeautyPreset: (preset) => set({ beautyPreset: preset }),

  skinSmoothing: 45,
  blemishRemoval: 50,
  spotCorrection: 35,
  darkSpotWhitening: 35,
  shineCut: 25,
  glowIntensity: 15,
  eyeCatchlight: 25,
  catchlightBoost: 25,
  teethWhitening: 30,
  skinBrightening: 0,
  keepMoles: true,
  looseHairCleanup: true,
  looseHairStrength: 30,
  lipColor: '#d87093',
  lipIntensity: 0,
  lightingTemp: 'neutral_5500k',
  studioLightIntensity: 15,
  rimLightBoost: 12,
  togaIron: 60,
  colorProfile: 'clean_commercial',
  colorWarmth: 0,
  colorContrast: 0,
  colorVibrance: 0,

  setColorProfile: (profile) => set({ colorProfile: profile }),
  setColorWarmth: (v) => set({ colorWarmth: v }),
  setColorContrast: (v) => set({ colorContrast: v }),
  setColorVibrance: (v) => set({ colorVibrance: v }),

  setSkinSmoothing: (v) => set({ skinSmoothing: v }),
  setBlemishRemoval: (v) => set({ blemishRemoval: v }),
  setSpotCorrection: (v) => set({ spotCorrection: v, darkSpotWhitening: v }),
  setDarkSpotWhitening: (v) => set({ spotCorrection: v, darkSpotWhitening: v }),
  setShineCut: (v) => set({ shineCut: v }),
  setGlowIntensity: (v) => set({ glowIntensity: v }),
  setEyeCatchlight: (v) => set({ eyeCatchlight: v, catchlightBoost: v }),
  setCatchlightBoost: (v) => set({ eyeCatchlight: v, catchlightBoost: v }),
  setTeethWhitening: (v) => set({ teethWhitening: v }),
  setSkinBrightening: (v) => set({ skinBrightening: v }),
  setKeepMoles: (keep) => set({ keepMoles: keep }),
  setLooseHairCleanup: (enabled) => set({ looseHairCleanup: enabled }),
  setLooseHairStrength: (v) => set({ looseHairStrength: v }),
  setLipColor: (c) => set({ lipColor: c }),
  setLipIntensity: (v) => set({ lipIntensity: v }),
  setLightingTemp: (t) => set({ lightingTemp: t }),
  setStudioLightIntensity: (v) => set({ studioLightIntensity: v }),
  setRimLightBoost: (v) => set({ rimLightBoost: v }),
  setTogaIron: (v) => set({ togaIron: v }),

  printViewMode: 'master',
  sliderPosition: 50,
  isZoomed: false,
  engineMode: 'local_cpu',
  isProcessing: false,
  isBatchRunning: false,
  batchProgress: 0,

  setPrintViewMode: (mode) => set({ printViewMode: mode }),
  setSliderPosition: (pos) => set({ sliderPosition: pos }),
  setIsZoomed: (zoomed) => set({ isZoomed: zoomed }),
  setEngineMode: (mode) => set({ engineMode: mode }),
  setIsProcessing: (processing) => set({ isProcessing: processing }),
  setIsBatchRunning: (running) => set({ isBatchRunning: running }),
  setBatchProgress: (progress) => set({ batchProgress: progress }),
}));
