/**
 * KameraPh Centralized Axios API Client
 * Enterprise-grade HTTP client with strict type safety, zero silent failures,
 * and global interceptors for 401 (force logout) and 500 (UI error toast).
 */

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../store/useAuthStore';
import { useUIStore } from '../store/useUIStore';
import {
  AiConfigResponse,
  AiKeyTestResponse,
  ApiStandardError,
  BatchProcessResponse,
  BatchUploadResponse,
  CheckoutResponse,
  HealthResponse,
  JobStatusResponse,
  LoginResponse,
  PhotoItem,
  PresignedDownloadResponse,
  PresignedUploadResponse,
  ProcessedPhotoResponse,
  RegaliaProfile,
  RegisterPhotoRequest,
  RegisterPhotoResponse,
  SampleResponse,
  UserSession,
} from '../types';

// Create dedicated Axios instance
const axiosInstance: AxiosInstance = axios.create({
  baseURL: '/',
  timeout: 45000,
  headers: {
    'Accept': 'application/json',
  },
});

// Request Interceptor: Attach Bearer token from auth store or storage
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    try {
      const token = useAuthStore.getState().token || localStorage.getItem('kameraph_token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    } catch (err: unknown) {
      console.error('[API Client] Error setting request authorization header:', err);
      return config;
    }
  },
  (error: AxiosError): Promise<never> => {
    console.error('[API Client] Outbound request failure:', error);
    return Promise.reject(error);
  }
);

// Response Interceptor: Global 401 & 500 handler with UI toast notifications
axiosInstance.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiStandardError>): Promise<never> => {
    const status = error.response?.status;
    const detail =
      error.response?.data?.detail ||
      error.message ||
      'An unexpected network error occurred';

    console.error(
      `[API Client Error] HTTP ${status || 'Network'}: ${detail}\nStack:`,
      error.stack
    );

    // Global 401 Unauthorized: Force logout and route to auth
    if (status === 401) {
      try {
        useAuthStore.getState().logout();
        useUIStore.getState().setCurrentPage('auth');
        useUIStore.getState().addToast('error', 'Session expired or unauthorized. Please log in again.');
      } catch (storeErr: unknown) {
        console.error('[API Client] Failed to handle 401 state transition:', storeErr);
      }
    }
    // Global 402 Payment Required: Studio credits exhausted
    else if (status === 402) {
      try {
        useUIStore.getState().openTopUpModal();
        useUIStore.getState().addToast('error', 'Studio credits depleted. Please top up your balance to continue.');
      } catch (storeErr: unknown) {
        console.error('[API Client] Failed to trigger top-up modal on 402:', storeErr);
      }
    }
    // Global 500 Internal Server Error: Display structured error toast
    else if (status === 500) {
      try {
        useUIStore.getState().addToast('error', `Server Error (500): ${detail}`);
      } catch (storeErr: unknown) {
        console.error('[API Client] Failed to dispatch 500 toast notification:', storeErr);
      }
    }

    return Promise.reject(new Error(detail));
  }
);

export const apiClient = {
  // Underlying Axios instance for custom requests
  instance: axiosInstance,

  /**
   * Health & System Diagnostics
   */
  async fetchHealth(): Promise<HealthResponse> {
    try {
      const res = await axiosInstance.get<HealthResponse>('/api/health');
      return res.data;
    } catch (err: unknown) {
      console.error('[apiClient.fetchHealth] Error checking server health:', err);
      throw err;
    }
  },

  /**
   * Authentication & User Verification
   */
  async getCurrentUser(): Promise<UserSession | null> {
    try {
      const res = await axiosInstance.get<UserSession>('/api/auth/me');
      return res.data;
    } catch (err: unknown) {
      console.warn('[apiClient.getCurrentUser] Not authenticated or offline:', err);
      return null;
    }
  },

  async login(formData: FormData): Promise<LoginResponse> {
    try {
      const res = await axiosInstance.post<LoginResponse>('/api/auth/login', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      if (res.data.token) {
        localStorage.setItem('kameraph_token', res.data.token);
      }
      return res.data;
    } catch (err: unknown) {
      console.error('[apiClient.login] Authentication failure:', err);
      throw err;
    }
  },

  logout(): void {
    try {
      localStorage.removeItem('kameraph_token');
      useAuthStore.getState().logout();
    } catch (err: unknown) {
      console.error('[apiClient.logout] Logout error:', err);
    }
  },

  /**
   * Regalia Profiles
   */
  async fetchRegaliaProfiles(): Promise<RegaliaProfile[]> {
    try {
      const res = await axiosInstance.get<RegaliaProfile[]>('/api/regalia-profiles');
      return res.data;
    } catch (err: unknown) {
      console.warn('[apiClient.fetchRegaliaProfiles] Falling back to default profiles:', err);
      return [];
    }
  },

  /**
   * Sample Portrait Retrieval
   */
  async getSample(params: Record<string, string | number | boolean>): Promise<SampleResponse> {
    try {
      const query = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => query.append(k, String(v)));
      const res = await axiosInstance.get<SampleResponse>(`/api/sample?${query.toString()}`);
      return res.data;
    } catch (err: unknown) {
      console.error('[apiClient.getSample] Error fetching sample portrait:', err);
      throw err;
    }
  },

  /**
   * Single Photo Processing
   */
  async processPhoto(options: Record<string, string | number | boolean>): Promise<ProcessedPhotoResponse> {
    try {
      const formData = new FormData();
      Object.entries(options).forEach(([k, v]) => {
        if (v !== undefined && v !== null) {
          formData.append(k, String(v));
        }
      });

      const res = await axiosInstance.post<ProcessedPhotoResponse>('/api/process', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    } catch (err: unknown) {
      console.error('[apiClient.processPhoto] Processing error:', err);
      throw err;
    }
  },

  /**
   * Cloudflare R2 Direct Edge Storage & Upload Operations
   */
  async getPresignedUploadUrl(filename: string, contentType: string = 'image/jpeg'): Promise<PresignedUploadResponse> {
    try {
      const res = await axiosInstance.get<PresignedUploadResponse>('/api/storage/presigned-url', {
        params: {
          file_key: filename,
          action: 'upload',
          content_type: contentType,
        },
      });
      return res.data;
    } catch (err: unknown) {
      console.error('[apiClient.getPresignedUploadUrl] Failed to get presigned upload URL:', err);
      throw err;
    }
  },

  async getPresignedDownloadUrl(fileKey: string): Promise<PresignedDownloadResponse> {
    try {
      const res = await axiosInstance.get<PresignedDownloadResponse>('/api/storage/presigned-url', {
        params: {
          file_key: fileKey,
          action: 'download',
        },
      });
      return res.data;
    } catch (err: unknown) {
      console.error('[apiClient.getPresignedDownloadUrl] Failed to get presigned download URL:', err);
      throw err;
    }
  },

  async registerUploadedPhoto(data: RegisterPhotoRequest): Promise<RegisterPhotoResponse> {
    try {
      const res = await axiosInstance.post<RegisterPhotoResponse>('/api/storage/register-photo', data);
      return res.data;
    } catch (err: unknown) {
      console.error('[apiClient.registerUploadedPhoto] Failed to register uploaded photo:', err);
      throw err;
    }
  },

  async uploadDirectToStorage(file: File, onProgress?: (pct: number) => void): Promise<PhotoItem> {
    try {
      const presigned = await this.getPresignedUploadUrl(file.name, file.type || 'image/jpeg');

      // Direct PUT of binary payload to Cloudflare R2 or local fallback endpoint
      await axios.put(presigned.upload_url, file, {
        headers: {
          'Content-Type': file.type || 'image/jpeg',
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total && onProgress) {
            const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(pct);
          }
        },
      });

      const registerResult = await this.registerUploadedPhoto({
        file_key: presigned.file_key,
        filename: file.name,
      });

      return registerResult.item;
    } catch (err: unknown) {
      console.error(`[apiClient.uploadDirectToStorage] Direct edge upload failed for ${file.name}:`, err);
      throw err;
    }
  },

  async batchUploadDirect(
    files: File[],
    onProgress?: (completed: number, total: number) => void
  ): Promise<BatchUploadResponse> {
    try {
      let completed = 0;
      const total = files.length;
      const items: PhotoItem[] = [];

      for (const file of files) {
        const item = await this.uploadDirectToStorage(file);
        items.push(item);
        completed += 1;
        if (onProgress) {
          onProgress(completed, total);
        }
      }

      return {
        uploaded_count: items.length,
        items,
      };
    } catch (err: unknown) {
      console.error('[apiClient.batchUploadDirect] Direct batch upload error:', err);
      throw err;
    }
  },

  /**
   * Batch Operations (with direct edge upload and standard multipart fallback)
   */
  async batchUpload(files: File[]): Promise<BatchUploadResponse> {
    try {
      // First attempt zero-egress, non-blocking direct edge upload
      return await this.batchUploadDirect(files);
    } catch (edgeErr: unknown) {
      console.warn('[apiClient.batchUpload] Direct edge upload encountered error, falling back to standard multipart batch upload:', edgeErr);
      try {
        const formData = new FormData();
        files.forEach((file) => formData.append('files', file));

        const res = await axiosInstance.post<BatchUploadResponse>('/api/batch-upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        return res.data;
      } catch (err: unknown) {
        console.error('[apiClient.batchUpload] Standard batch upload fallback also failed:', err);
        throw err;
      }
    }
  },

  async batchProcess(options: Record<string, string | number | boolean>): Promise<BatchProcessResponse> {
    try {
      const formData = new FormData();
      Object.entries(options).forEach(([k, v]) => {
        if (v !== undefined && v !== null) {
          formData.append(k, String(v));
        }
      });

      const res = await axiosInstance.post<BatchProcessResponse>('/api/batch-process', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    } catch (err: unknown) {
      console.error('[apiClient.batchProcess] Batch processing failed:', err);
      throw err;
    }
  },

  /**
   * PayMongo Payment & Top-Up
   */
  async createCheckout(packageId: string): Promise<CheckoutResponse> {
    try {
      const formData = new FormData();
      formData.append('package_id', packageId);

      const res = await axiosInstance.post<CheckoutResponse>('/api/checkout', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    } catch (err: unknown) {
      console.error('[apiClient.createCheckout] Failed to create PayMongo checkout:', err);
      throw err;
    }
  },

  /**
   * Background Async Job Polling
   */
  async pollJob(jobId: string): Promise<JobStatusResponse> {
    try {
      const res = await axiosInstance.get<JobStatusResponse>(`/api/jobs/${jobId}`);
      return res.data;
    } catch (err: unknown) {
      console.error(`[apiClient.pollJob] Failed to poll job ${jobId}:`, err);
      throw err;
    }
  },

  /**
   * Admin Operations
   */
  async getAiConfig(): Promise<AiConfigResponse> {
    try {
      const res = await axiosInstance.get<AiConfigResponse>('/api/admin/ai-config');
      return res.data;
    } catch (err: unknown) {
      console.error('[apiClient.getAiConfig] Failed to fetch AI config:', err);
      throw err;
    }
  },

  async updateAiConfig(config: Record<string, string>): Promise<AiConfigResponse> {
    try {
      const formData = new FormData();
      Object.entries(config).forEach(([k, v]) => formData.append(k, v));

      const res = await axiosInstance.post<AiConfigResponse>('/api/admin/ai-config', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    } catch (err: unknown) {
      console.error('[apiClient.updateAiConfig] Failed to update AI config:', err);
      throw err;
    }
  },

  async testAiKey(apiKey: string): Promise<AiKeyTestResponse> {
    try {
      const formData = new FormData();
      formData.append('api_key', apiKey);

      const res = await axiosInstance.post<AiKeyTestResponse>('/api/admin/test-ai-key', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data;
    } catch (err: unknown) {
      console.error('[apiClient.testAiKey] AI key probe failed:', err);
      throw err;
    }
  },
};
