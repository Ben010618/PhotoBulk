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
