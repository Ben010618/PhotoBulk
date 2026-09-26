export type PageView =
  | 'landing'
  | 'auth'
  | 'user_dashboard'
  | 'admin_dashboard'
  | 'editor'
  | 'student_portal';

export interface UserSession {
  name: string;
  email: string;
  role: 'photographer' | 'admin';
  studioName: string;
  credits: number;
}

export interface PhotoAnalysis {
  sharpness_score?: number;
  sharpness_grade?: string;
  blink_status?: 'open' | 'blink';
  is_best_shot?: boolean;
  star_rating?: number;
  review_needed?: boolean;
  review_reason?: string;
  flag_reason?: string;
  face_count?: number;
  head_pose?: {
    roll_deg?: number;
    pitch_deg?: number;
    yaw_deg?: number;
  };
}

export interface PhotoItem {
  id: string;
  name: string;
  originalUrl: string;
  enhancedUrl: string;
  crop8rUrl?: string;
  crop2x2Url?: string;
  previewUrl?: string;
  masterUrl?: string;
  status: 'pending' | 'processing' | 'ready' | 'done';
  analysis?: PhotoAnalysis;
  latency_ms?: number;
  engine_used?: string;
}

export interface BackdropPreset {
  id: string;
  name: string;
  description: string;
  hex: string;
}

export interface BeautyPreset {
  id: string;
  name: string;
  description: string;
  skin_smoothing: number;
  blemish_cut: number;
  dark_spot_whitening: number;
  shine_reduction: number;
  lip_intensity: number;
  lip_color: string;
  glow_intensity: number;
  catchlight_boost: number;
  teeth_whitening: number;
}

export interface RegaliaProfile {
  id: string;
  name: string;
  iron_strength: number;
  skin_smoothing: number;
  shine_reduction: number;
  edge_protection_level: string;
  description: string;
}

export interface ToastNotification {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
  timestamp: number;
}

export interface StudentProof {
  studentId: string;
  studentName: string;
  schoolName: string;
  degree: string;
  academicYear: string;
  watermarkedPreviewUrl: string;
  qrCodeUrl: string;
  approvalStatus: 'pending' | 'approved' | 'revision_requested';
  feedbackNotes?: string;
}

export interface ApiStandardError {
  detail: string;
  code?: string;
  status_code?: number;
}

export interface HealthResponse {
  status: string;
  engine: string;
  database: string;
  version?: string;
}

export interface LoginResponse {
  token: string;
  user: UserSession;
}

export interface SampleResponse {
  id: string;
  filename: string;
  original_data_uri: string;
  enhanced_data_uri: string;
  crop_8r_data_uri?: string;
  crop_2x2_data_uri?: string;
  studio_credits?: number;
  analysis?: PhotoAnalysis;
  dimensions?: { width: number; height: number };
}

export interface ProcessedPhotoResponse {
  id: string;
  original_data_uri?: string;
  enhanced_data_uri: string;
  crop_8r_data_uri?: string;
  crop_2x2_data_uri?: string;
  studio_credits?: number;
  analysis?: PhotoAnalysis;
  latency_ms?: number;
}

export interface BatchUploadResponse {
  uploaded_count: number;
  items: PhotoItem[];
}

export interface BatchProcessResponse {
  total_processed: number;
  per_photo_latency_ms: number;
  studio_credits?: number;
  items: PhotoItem[];
}

export interface CheckoutResponse {
  checkout_url: string;
  session_id: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'done';
  progress: number;
  total?: number;
  processed?: number;
  created_at?: number;
  updated_at?: number;
  message?: string;
  error?: string;
  items?: PhotoItem[];
  studio_credits?: number;
  total_time_ms?: number;
  per_photo_latency_ms?: number;
  engine_used?: string;
  result?: Record<string, unknown>;
}

export interface AiConfigResponse {
  gemini_model: string;
  is_key_configured: boolean;
  active_engine: string;
}

export interface AiKeyTestResponse {
  status: 'success' | 'error';
  message: string;
  latency_ms?: number;
  detail?: string;
}

export interface PresignedUploadResponse {
  upload_url: string;
  file_key: string;
  storage: string;
  expires_in: number;
  content_type: string;
}

export interface PresignedDownloadResponse {
  download_url: string;
  file_key: string;
  storage: string;
  expires_in: number;
}

export interface RegisterPhotoRequest {
  file_key: string;
  filename: string;
}

export interface RegisterPhotoResponse {
  success: boolean;
  item: PhotoItem;
}

