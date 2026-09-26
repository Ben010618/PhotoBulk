import { create } from 'zustand';
import { UserSession } from '../types';

interface AuthState {
  currentUser: UserSession | null;
  token: string | null;
  setCurrentUser: (user: UserSession | null) => void;
  setCredits: (credits: number) => void;
  deductCredits: (amount: number) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  currentUser: {
    name: 'Juan Dela Cruz',
    email: 'editor@auragrad-studio.ph',
    role: 'photographer',
    studioName: 'AuraGrad Creative Studio Manila',
    credits: 150,
  },
  token: localStorage.getItem('kameraph_token'),

  setCurrentUser: (user) => set({ currentUser: user }),

  setCredits: (credits) =>
    set((state) => ({
      currentUser: state.currentUser
        ? { ...state.currentUser, credits }
        : null,
    })),

  deductCredits: (amount) =>
    set((state) => ({
      currentUser: state.currentUser
        ? { ...state.currentUser, credits: Math.max(0, state.currentUser.credits - amount) }
        : null,
    })),

  logout: () => {
    localStorage.removeItem('kameraph_token');
    set({ currentUser: null, token: null });
  },
}));
