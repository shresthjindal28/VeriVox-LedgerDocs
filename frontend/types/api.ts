// API Types matching backend contracts

// ============================================================================
// Common Types
// ============================================================================

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}

// ============================================================================
// Auth Types
// ============================================================================

export interface User {
  id: string;
  email?: string;
  phone?: string;
  role: 'student' | 'teacher' | 'admin';
  email_confirmed_at?: string;
  phone_confirmed_at?: string;
  created_at?: string;
  last_sign_in_at?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  expires_at?: number;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name?: string;
  role?: 'student' | 'teacher';
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface PhoneOTPRequest {
  phone: string;
}

export interface PhoneVerifyRequest {
  phone: string;
  token: string;
}

// ============================================================================
// Profile Types
// ============================================================================

export interface Profile {
  id: string;
  display_name?: string;
  avatar_url?: string;
  bio?: string;
  role: 'student' | 'teacher' | 'admin';
  created_at: string;
  updated_at: string;
}

export interface ProfileUpdate {
  display_name?: string;
  avatar_url?: string;
  bio?: string;
}

export interface StudyPreferences {
  user_id: string;
  voice?: 'nova' | 'alloy' | 'echo' | 'fable' | 'onyx' | 'shimmer';
  preferred_voice?: string;
  theme?: 'light' | 'dark' | 'system';
  language?: string;
  notifications_enabled?: boolean;
  auto_play_audio?: boolean;
  playback_speed?: number;
  subjects?: string[];
  study_goals?: string[];
  daily_study_time?: number;
  updated_at?: string;
}

export interface FullProfile {
  user: User;
  profile: Profile;
  preferences: StudyPreferences;
}

// ============================================================================
// Document Types
// ============================================================================

export interface DocumentInfo {
  document_id: string;
  filename: string;
  page_count: number;
  chunk_count?: number;
  content_hash?: string;
  upload_timestamp?: string;
  upload_date?: string;
  file_size?: number;
  status?: 'processing' | 'ready' | 'error';
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  content_hash: string;
  message: string;
}

export interface DocumentVerification {
  document_id: string;
  is_valid: boolean;
  stored_hash: string;
  computed_hash?: string;
  verification_timestamp: string;
}

// ============================================================================
// Chat Types
// ============================================================================

export interface ChatRequest {
  question: string;
}

export interface SourceReference {
  page: number;
  text: string;
  relevance_score?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: SourceReference[];
}

export interface ChatResponse {
  answer: string;
  sources: SourceReference[];
  confidence: number;
  reasoning?: string;
  document_id: string;
  question: string;
  timestamp: string;
}

export interface StreamingMessage {
  type: 'token' | 'complete' | 'error' | 'status';
  content?: string;
  response?: ChatResponse;
  message?: string;
}

// ============================================================================
// Voice Types
// ============================================================================

export interface VoiceInfo {
  name: string;
  voice_id: string;
  description: string;
}

export interface TranscriptionResponse {
  text: string;
  duration?: number;
}

export interface VoiceChatRequest {
  document_id: string;
  question?: string;
  voice?: string;
}

export interface VoiceChatResponse {
  text_response: string;
  audio_base64?: string;
  sources: SourceReference[];
}

// ============================================================================
// WebSocket Types
// ============================================================================

export interface WSChatMessage {
  question: string;
}

export interface WSVoiceMessage {
  type: 'audio_chunk' | 'end_speech' | 'interrupt' | 'ping';
  data?: string; // base64 audio
}

export interface WSServerMessage {
  type: 'state_change' | 'transcription' | 'text_response' | 'audio_chunk' | 'audio_end' | 'error' | 'pong' | 'token' | 'complete' | 'status';
  state?: string;
  text?: string;
  data?: string;
  content?: string;
  response?: ChatResponse;
  message?: string;
}

export type ConversationState = 
  | 'idle' 
  | 'listening' 
  | 'user_speaking' 
  | 'processing' 
  | 'speaking' 
  | 'ai_speaking' 
  | 'interrupted';

// ============================================================================
// Health Types
// ============================================================================

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  backends?: {
    pdf_service: { status: string };
    user_service: { status: string };
  };
}
