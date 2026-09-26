import { create } from 'zustand';
import { PageView, ToastNotification } from '../types';

interface UIState {
  currentPage: PageView;
  isTopUpModalOpen: boolean;
  paymentsEnabled: boolean;
  toasts: ToastNotification[];
  setCurrentPage: (page: PageView) => void;
  setPaymentsEnabled: (enabled: boolean) => void;
  openTopUpModal: () => void;
  closeTopUpModal: () => void;
  addToast: (type: 'success' | 'error' | 'info', message: string) => void;
  removeToast: (id: string) => void;
}

export const useUIStore = create<UIState>((set, get) => ({
  currentPage: (window.location.hash.replace('#', '') as PageView) || 'editor',
  isTopUpModalOpen: false,
  paymentsEnabled: false,
  toasts: [],

  setCurrentPage: (page: PageView) => {
    window.location.hash = page;
    set({ currentPage: page });
  },

  setPaymentsEnabled: (enabled: boolean) => set({ paymentsEnabled: enabled }),

  openTopUpModal: () => {
    if (get().paymentsEnabled) {
      set({ isTopUpModalOpen: true });
    }
  },
  closeTopUpModal: () => set({ isTopUpModalOpen: false }),

  addToast: (type, message) => {
    const id = `${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    set((state) => ({
      toasts: [...state.toasts, { id, type, message, timestamp: Date.now() }],
    }));

    // Auto-dismiss after 4 seconds
    setTimeout(() => {
      set((state) => ({
        toasts: state.toasts.filter((t) => t.id !== id),
      }));
    }, 4000);
  },

  removeToast: (id: string) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }));
  },
}));
