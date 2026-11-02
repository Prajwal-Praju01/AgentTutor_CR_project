// Core TypeScript types for AgentTutor

export interface User {
  id: string
  email: string
  username: string
  display_name: string
  role: 'student' | 'instructor' | 'admin'
  created_at: string
}

export interface Course {
  id: string
  title: string
  code: string
  description?: string
  syllabus?: string
  created_at: string
  document_count: number
}

export interface CourseDocument {
  id: string
  course_id: string
  original_filename: string
  mime_type?: string
  file_size_bytes?: number
  status: 'pending' | 'processing' | 'ready' | 'failed'
  error_message?: string
  page_count?: number
  created_at: string
}

export interface Session {
  id: string
  student_id: string
  course_id?: string
  session_type: 'tutoring' | 'debugging'
  status: 'active' | 'completed' | 'abandoned'
  title?: string
  concept?: string
  created_at: string
  ended_at?: string
}

export interface MessageMetadata {
  understanding_level?: number
  hint_depth?: number
  assessment?: Assessment
  citations?: Citation[]
  next_question?: string
}

export interface Message {
  id: string
  session_id: string
  role: 'student' | 'tutor' | 'system'
  content: string
  metadata?: MessageMetadata
  created_at: string
}

export interface Assessment {
  understanding_level: number
  justification: string
  confidence: number
  misconceptions: string[]
  recommended_hint_depth: number
}

export interface Citation {
  document: string
  section?: string
  page?: number
  relevance: number
}

export interface StudentProgress {
  concept_scores: Record<string, number>
  misconceptions: { concept: string; description: string; count: number }[]
  total_sessions: number
  total_messages: number
  course_states: Record<string, unknown>
  recent_sessions: Session[]
}

export interface LearningState {
  id: string
  name: string
  description?: string
  order_index: number
  status: 'pending' | 'in_progress' | 'resolved' | 'unresolved'
  resolution_evidence?: string
}

export interface AuthResponse {
  user: User
  access_token: string
  refresh_token: string
}

export interface ApiError {
  error: {
    code: string
    message: string
    details?: unknown[]
  }
}

export type UnderstandingLevel = 0 | 1 | 2 | 3
export const UNDERSTANDING_LABELS: Record<number, string> = {
  0: 'Confused',
  1: 'Beginner',
  2: 'Developing',
  3: 'Mastered',
}
export const HINT_DEPTH_LABELS: Record<number, string> = {
  1: 'Conceptual',
  2: 'Directional',
  3: 'Partial Reveal',
  4: 'Full Solution',
}

