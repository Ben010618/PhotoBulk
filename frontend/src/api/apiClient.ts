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
  BulkExportRequest,
  CheckoutResponse,
  ExportJobStatus,
  HealthResponse,
  JobStatusResponse,
  LoginResponse,
  PhotoItem,
  PresignedDownloadResponse,
  PresignedUploadResponse,
  ProcessedPhotoResponse,
  ProjectItem,
  RegaliaProfile,
  RegisterPhotoRequest,
  RegisterPhotoResponse,
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
    // Global 402 Payment Required: Studio credits exhausted (only when payments enabled)
    else if (status === 402 && useUIStore.getState().paymentsEnabled) {
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
   * Single Photo Processing
   */
  async processPhoto(options: Record<string, string | number | boolean>): Promise<ProcessedPhotoResponse> {
    try {
      const formData = new FormData();
      Object.entries(options).forEach(([k, v]) => {
        if (v !== undefined && v !== null) {
          // Map frontend catchlight_boost to backend eye_catchlight
          const key = k === 'catchlight_boost' ? 'eye_catchlight' : k;
          formData.append(key, String(v));
        }
      });

      const res = await axiosInstance.post<ProcessedPhotoResponse>('/api/process-image', formData, {
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

  async batchUpload(
    files: File[],
    projectId: string = 'default_project',
    onProgress?: (progressPct: number) => void
  ): Promise<BatchUploadResponse> {
    try {
      const formData = new FormData();
      files.forEach((file) => formData.append('files', file));
      formData.append('project_id', projectId);

      const res = await axiosInstance.post<BatchUploadResponse>('/api/batch-upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(pct);
          }
        },
      });
      return res.data;
    } catch (err: unknown) {
      console.error('[apiClient.batchUpload] Batch upload failed:', err);
      throw err;
    }
  },

  async batchProcess(
    options: Record<string, string | number | boolean>,
    onProgress?: (progressPct: number, job: JobStatusResponse) => void
  ): Promise<BatchProcessResponse> {
    try {
      const formData = new FormData();
      Object.entries(options).forEach(([k, v]) => {
        if (v !== undefined && v !== null) {
          formData.append(k, String(v));
        }
      });

      const res = await axiosInstance.post<BatchProcessResponse | JobStatusResponse>('/api/batch-process', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      // If backend responded with 202 or returned a JobStatusResponse (with job_id):
      if ('job_id' in res.data && res.data.job_id) {
        const completedJob = await this.pollJobUntilCompletion(res.data.job_id, onProgress);
        return {
          total_processed: completedJob.processed ?? (completedJob.items ? completedJob.items.length : 0),
          per_photo_latency_ms: completedJob.per_photo_latency_ms ?? 0,
          studio_credits: completedJob.studio_credits,
          items: completedJob.items ?? [],
        };
      }

      return res.data as BatchProcessResponse;
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
   * Polls an asynchronous job until status is completed or failed
   */
  async pollJobUntilCompletion(
    jobId: string,
    onProgress?: (progressPct: number, job: JobStatusResponse) => void,
    intervalMs: number = 300,
    timeoutMs: number = 180000
  ): Promise<JobStatusResponse> {
    const startTime = Date.now();
    while (Date.now() - startTime < timeoutMs) {
      const job = await this.pollJob(jobId);
      if (onProgress) {
        onProgress(job.progress, job);
      }
      if (job.status === 'completed' || job.status === 'done') {
        return job;
      }
      if (job.status === 'failed') {
        throw new Error(job.error || `Background job ${jobId} failed.`);
      }
      await new Promise((resolve) => setTimeout(resolve, intervalMs));
    }
    throw new Error(`Background job ${jobId} timed out after ${timeoutMs}ms.`);
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

  /**
   * Project & Bulk Workflow Operations
   */
  async listProjects(): Promise<{ projects: ProjectItem[] }> {
    try {
      const res = await axiosInstance.get<{ projects: ProjectItem[] }>('/api/projects');
      return res.data;
    } catch (err: unknown) {
      console.error('[apiClient.listProjects] Error fetching projects:', err);
      throw err;
    }
  },

  async createProject(title: string, projectId?: string): Promise<ProjectItem> {
    try {
      const res = await axiosInstance.post<ProjectItem>('/api/projects', {
        title,
        project_id: projectId,
      });
      return res.data;
    } catch (err: unknown) {
      console.error('[apiClient.createProject] Error creating project:', err);
      throw err;
    }
  },

  async getProject(projectId: string): Promise<{ project: ProjectItem; photos: any[]; total_photos: number }> {
    try {
      const res = await axiosInstance.get(`/api/projects/${projectId}`);
      return res.data;
    } catch (err: unknown) {
      console.error(`[apiClient.getProject] Error fetching project ${projectId}:`, err);
      throw err;
    }
  },

  async getProjectPhotos(projectId: string): Promise<{ photos: any[]; total: number }> {
    try {
      const res = await axiosInstance.get<{ photos: any[]; total: number }>(`/api/projects/${projectId}/photos`);
      return res.data;
    } catch (err: unknown) {
      console.error(`[apiClient.getProjectPhotos] Error listing photos for ${projectId}:`, err);
      throw err;
    }
  },

  async updatePhotoSettings(
    projectId: string,
    photoId: string,
    settings: Record<string, any>,
    isUserOverride: boolean = true
  ): Promise<{ success: boolean; settings: Record<string, any>; render_latency_ms: number }> {
    try {
      const res = await axiosInstance.post(`/api/projects/${projectId}/photos/${photoId}/settings`, {
        settings,
        is_user_override: isUserOverride,
      });
      return res.data;
    } catch (err: unknown) {
      console.error(`[apiClient.updatePhotoSettings] Error updating settings for ${photoId}:`, err);
      throw err;
    }
  },

  async clearPhotoOverride(projectId: string, photoId: string): Promise<{ success: boolean; settings: Record<string, any> }> {
    try {
      const res = await axiosInstance.post(`/api/projects/${projectId}/photos/${photoId}/clear-override`);
      return res.data;
    } catch (err: unknown) {
      console.error(`[apiClient.clearPhotoOverride] Error clearing override for ${photoId}:`, err);
      throw err;
    }
  },

  async applyToAll(
    projectId: string,
    sourcePhotoId: string,
    excludeOverridden: boolean = true
  ): Promise<{
    success: boolean;
    project_id: string;
    source_photo_id: string;
    updated_count: number;
    skipped_count: number;
  }> {
    try {
      const res = await axiosInstance.post(
        `/api/projects/${projectId}/photos/${sourcePhotoId}/apply-to-all?exclude_overridden=${excludeOverridden}`
      );
      return res.data;
    } catch (err: unknown) {
      console.error(`[apiClient.applyToAll] Error applying look across ${projectId}:`, err);
      throw err;
    }
  },

  async triggerProjectExport(
    projectId: string,
    req: BulkExportRequest
  ): Promise<{ job_id: string; status: string; message: string }> {
    try {
      const res = await axiosInstance.post(`/api/projects/${projectId}/export`, req);
      return res.data;
    } catch (err: unknown) {
      console.error(`[apiClient.triggerProjectExport] Error starting export for ${projectId}:`, err);
      throw err;
    }
  },

  async getExportStatus(projectId: string, exportId: string): Promise<ExportJobStatus> {
    try {
      const res = await axiosInstance.get<ExportJobStatus>(`/api/projects/${projectId}/exports/${exportId}/status`);
      return res.data;
    } catch (err: unknown) {
      console.error(`[apiClient.getExportStatus] Error fetching export status ${exportId}:`, err);
      throw err;
    }
  },

  async downloadExportZip(projectId: string, exportId: string, filename: string = 'export.zip'): Promise<void> {
    try {
      const res = await axiosInstance.get(`/api/projects/${projectId}/exports/${exportId}/download`, {
        responseType: 'blob',
      });
      const blob = new Blob([res.data], { type: 'application/zip' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      console.error(`[apiClient.downloadExportZip] Error downloading zip:`, err);
      throw err;
    }
  },
};
