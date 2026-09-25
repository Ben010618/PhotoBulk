/**
 * KameraPh API Client
 * Centralized, type-safe API communication with the FastAPI backend.
 */

import { PhotoItem, RegaliaProfile, UserSession } from '../types';

const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('kameraph_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const api = {
  async fetchHealth() {
    const res = await fetch('/api/health');
    return res.json();
  },

  async getCurrentUser(): Promise<UserSession | null> {
    try {
      const res = await fetch('/api/auth/me', {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        return res.json();
      }
    } catch {
      // offline / not logged in
    }
    return null;
  },

  logout() {
    localStorage.removeItem('kameraph_token');
  },

  async login(formData: FormData) {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Authentication failed' }));
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    if (data.token) {
      localStorage.setItem('kameraph_token', data.token);
    }
    return data;
  },

  async fetchRegaliaProfiles(): Promise<RegaliaProfile[]> {
    try {
      const res = await fetch('/api/regalia-profiles');
      if (res.ok) return res.json();
    } catch (e) {
      console.warn('Failed to fetch regalia profiles from server:', e);
    }
    return [];
  },

  async getSample(params: Record<string, string | boolean | number>) {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => query.append(k, String(v)));
    const res = await fetch(`/api/sample?${query.toString()}`);
    if (!res.ok) throw new Error('Failed to load sample');
    return res.json();
  },

  async fetchSample(params: Record<string, string | boolean | number>) {
    return this.getSample(params);
  },

  async processPhoto(options: Record<string, any>) {
    const formData = new FormData();
    Object.entries(options).forEach(([k, v]) => {
      if (v !== undefined && v !== null) {
        formData.append(k, String(v));
      }
    });

    const res = await fetch('/api/process', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    });

    if (res.status === 402) {
      throw new Error('Insufficient studio credits. Please top up.');
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Processing error' }));
      throw new Error(err.detail || 'Failed to process image');
    }
    return res.json();
  },

  async processImage(formData: FormData) {
    const res = await fetch('/api/process-image', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    });
    if (res.status === 402) {
      throw new Error('Insufficient studio credits. Please top up to continue processing.');
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Processing error' }));
      throw new Error(err.detail || 'Failed to process image');
    }
    return res.json();
  },

  async batchUpload(files: File[]): Promise<{ uploaded_count: number; items: PhotoItem[] }> {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const res = await fetch('/api/batch-upload', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload error' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async uploadBatch(files: File[]) {
    return this.batchUpload(files);
  },

  async batchProcess(options: Record<string, any>) {
    const formData = new FormData();
    Object.entries(options).forEach(([k, v]) => {
      if (v !== undefined && v !== null) {
        formData.append(k, String(v));
      }
    });

    const res = await fetch('/api/batch-process', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    });
    if (res.status === 402) {
      throw new Error('Insufficient studio credits for batch. Please top up.');
    }
    if (!res.ok) throw new Error('Batch processing failed');
    return res.json();
  },

  async processBatch(formData: FormData) {
    const res = await fetch('/api/batch-process', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    });
    if (res.status === 402) {
      throw new Error('Insufficient studio credits for batch. Please top up.');
    }
    if (!res.ok) throw new Error('Batch processing failed');
    return res.json();
  },

  async createCheckout(packageId: string) {
    const formData = new FormData();
    formData.append('package_id', packageId);
    const res = await fetch('/api/checkout', {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    });
    if (!res.ok) throw new Error('Failed to create checkout session');
    return res.json();
  },

  async pollJob(jobId: string) {
    const res = await fetch(`/api/jobs/${jobId}`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Job lookup failed');
    return res.json();
  },
};
