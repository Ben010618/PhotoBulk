export type PageView =
  | 'landing'
  | 'auth'
  | 'user_dashboard'
  | 'admin_dashboard'
  | 'editor';

export interface ColorProfile {
  id: string;
  name: string;
  category: string;
  badge?: string;
  description: string;
  base_warmth?: number;
  base_contrast?: number;
  base_vibrance?: number;
  is_monochrome?: boolean;
}

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
  eyes_open?: boolean;
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
  auto_corrections?: {
    exposure_compensation_ev?: number;
    target_skin_luminance?: number;
    current_skin_luminance?: number;
    scaling_applied?: boolean;
    texture_scale?: number;
    spot_scale?: number;
  };
  white_balance_cast?: {
    has_cast?: boolean;
    cast_type?: string;
    delta_b?: number;
  };
  plain_summary?: string;
  ai_appraisal?: AiAppraisal;
}

export interface AiAppraisal {
  active: boolean;
  provider: string;
  model_used: string;
  skin_undertone: string;
  tone_label?: string;
  lighting_temperature: string;
  blemish_score: number;
  beautify_appraisal: string;
  recommended_preset: string;
  recommended_color_profile: string;
  auto_corrections?: Record<string, any>;
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
  has_face?: boolean;
  has_user_override?: boolean;
  review_needed?: boolean;
  review_reason?: string;
  settings?: Record<string, any>;
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
  spot_correction?: number;
  dark_spot_whitening?: number;
  shine_reduction: number;
  lip_intensity: number;
  lip_color?: string;
  glow_intensity: number;
  eye_catchlight?: number;
  catchlight_boost?: number;
  teeth_whitening: number;
  loose_hair_cleanup?: number;
  cleanup_loose_hair?: boolean;
}

export interface ProjectItem {
  id: string;
  title: string;
  photo_count: number;
  created_at: number;
}

export interface BulkExportRequest {
  selected_outputs: string[];
  filename_template: string;
  student_csv?: string;
  school_name: string;
  studio_name?: string;
  include_contact_sheet: boolean;
}

export interface ExportJobStatus {
  job_id: string;
  project_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  total?: number;
  processed?: number;
  message?: string;
  error?: string;
  result?: {
    zip_path: string;
    zip_size_bytes: number;
    total_images_rendered: number;
    latency_ms: number;
    total_files?: number;
    file_size_bytes?: number;
  };
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
  project_id?: string;
  job_id?: string;
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
  model: string;
  has_key: boolean;
  engine_label: string;
  provider: string;
  beautify_mode: string;
  status: string;
  api_key_masked?: string;
  last_tested?: string;
  // Legacy aliases for backward compatibility
  gemini_model?: string;
  is_key_configured?: boolean;
  active_engine?: string;
}

export interface AiKeyTestResponse {
  status: 'success' | 'active' | 'error';
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

