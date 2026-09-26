import { create } from 'zustand';
import { PhotoItem } from '../types';

interface EditorState {
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

  // Sliders
  skinSmoothing: number;
  blemishRemoval: number;
  darkSpotWhitening: number;
  shineCut: number;
  glowIntensity: number;
  catchlightBoost: number;
  teethWhitening: number;
  lipColor: string;
  lipIntensity: number;
  lightingTemp: 'warm_3200k' | 'neutral_5500k' | 'cool_6500k';
  studioLightIntensity: number;
  rimLightBoost: number;
  togaIron: number;

  setSkinSmoothing: (v: number) => void;
  setBlemishRemoval: (v: number) => void;
  setDarkSpotWhitening: (v: number) => void;
  setShineCut: (v: number) => void;
  setGlowIntensity: (v: number) => void;
  setCatchlightBoost: (v: number) => void;
  setTeethWhitening: (v: number) => void;
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
  backdropType: 'royal_navy',
  regaliaProfile: 'ph_academic_toga',
  beautyPreset: 'morena_radiant',

  setBgReplacementEnabled: (enabled) => set({ bgReplacementEnabled: enabled }),
  setBackdropType: (type) => set({ backdropType: type }),
  setRegaliaProfile: (profile) => set({ regaliaProfile: profile }),
  setBeautyPreset: (preset) => set({ beautyPreset: preset }),

  skinSmoothing: 65,
  blemishRemoval: 70,
  darkSpotWhitening: 50,
  shineCut: 35,
  glowIntensity: 40,
  catchlightBoost: 40,
  teethWhitening: 45,
  lipColor: '#d87093',
  lipIntensity: 35,
  lightingTemp: 'neutral_5500k',
  studioLightIntensity: 20,
  rimLightBoost: 20,
  togaIron: 70,

  setSkinSmoothing: (v) => set({ skinSmoothing: v }),
  setBlemishRemoval: (v) => set({ blemishRemoval: v }),
  setDarkSpotWhitening: (v) => set({ darkSpotWhitening: v }),
  setShineCut: (v) => set({ shineCut: v }),
  setGlowIntensity: (v) => set({ glowIntensity: v }),
  setCatchlightBoost: (v) => set({ catchlightBoost: v }),
  setTeethWhitening: (v) => set({ teethWhitening: v }),
  setLipColor: (c) => set({ lipColor: c }),
  setLipIntensity: (v) => set({ lipIntensity: v }),
  setLightingTemp: (t) => set({ lightingTemp: t }),
  setStudioLightIntensity: (v) => set({ studioLightIntensity: v }),
  setRimLightBoost: (v) => set({ rimLightBoost: v }),
  setTogaIron: (v) => set({ togaIron: v }),

  printViewMode: 'master',
  sliderPosition: 50,
  isZoomed: false,
  engineMode: 'modal_cloud_gpu',
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
