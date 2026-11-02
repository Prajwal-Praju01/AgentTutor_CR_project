import axios, { AxiosError } from 'axios'
import type {
  AuthResponse, Course, CourseDocument, Session,
  Message, StudentProgress, LearningState, ApiError,
} from '@/types'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach token from localStorage
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Refresh or logout on 401
apiClient.interceptors.response.use(
  (res) => res,
  async (err: AxiosError<ApiError>) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  },
)

// ── Auth ──────────────────────────────────────────────────────────────────────

export const authApi = {
  register: (data: { email: string; username: string; password: string; display_name?: string }) =>
    apiClient.post<AuthResponse>('/auth/register', data).then((r) => r.data),

  login: (data: { email: string; password: string }) =>
    apiClient.post<AuthResponse>('/auth/login', data).then((r) => r.data),

  me: () => apiClient.get<{ user: AuthResponse['user'] }>('/auth/me').then((r) => r.data.user),
}

// ── Courses ───────────────────────────────────────────────────────────────────

export const coursesApi = {
  list: () => apiClient.get<{ courses: Course[] }>('/courses').then((r) => r.data.courses),

  get: (id: string) => apiClient.get<{ course: Course }>(`/courses/${id}`).then((r) => r.data.course),

  create: (data: { title: string; code: string; description?: string; syllabus?: string }) =>
    apiClient.post<{ course: Course }>('/courses', data).then((r) => r.data.course),

  update: (id: string, data: Partial<Pick<Course, 'title' | 'description' | 'syllabus'>>) =>
    apiClient.patch<{ course: Course }>(`/courses/${id}`, data).then((r) => r.data.course),

  enroll: (id: string) =>
    apiClient.post<{ message: string }>(`/courses/${id}/enroll`).then((r) => r.data),
}

// ── Documents ─────────────────────────────────────────────────────────────────

export const documentsApi = {
  list: (courseId: string) =>
    apiClient.get<{ documents: CourseDocument[] }>(`/courses/${courseId}/documents`).then((r) => r.data.documents),

  upload: (courseId: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return apiClient
      .post<{ document: CourseDocument }>(`/courses/${courseId}/documents`, form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data.document)
  },

  delete: (courseId: string, docId: string) =>
    apiClient.delete<{ message: string }>(`/courses/${courseId}/documents/${docId}`).then((r) => r.data),
}

// ── Sessions ──────────────────────────────────────────────────────────────────

export const sessionsApi = {
  create: (data: {
    course_id?: string
    session_type?: string
    title?: string
    concept?: string
    buggy_code?: string
    language?: string
    description?: string
    expected_behavior?: string
  }) => apiClient.post<{ session: Session }>('/sessions', data).then((r) => r.data.session),

  get: (id: string) => apiClient.get<{ session: Session }>(`/sessions/${id}`).then((r) => r.data.session),

  history: (id: string) =>
    apiClient.get<{ session: Session; messages: Message[] }>(`/sessions/${id}/history`).then((r) => r.data),

  sendMessage: (sessionId: string, content: string) =>
    apiClient
      .post<{ student_message: Message; tutor_message: Message; assessment: unknown }>(
        `/sessions/${sessionId}/messages`,
        { content },
      )
      .then((r) => r.data),

  states: (sessionId: string) =>
    apiClient.get<{ states: LearningState[] }>(`/sessions/${sessionId}/states`).then((r) => r.data.states),

  end: (sessionId: string) =>
    apiClient.patch<{ session: Session }>(`/sessions/${sessionId}/end`).then((r) => r.data.session),
}

// ── Students ──────────────────────────────────────────────────────────────────

export const studentsApi = {
  progress: () =>
    apiClient.get<StudentProgress>('/students/me/progress').then((r) => r.data),
}

// ── Health ────────────────────────────────────────────────────────────────────

export const healthApi = {
  check: () => apiClient.get<{ status: string }>('/health').then((r) => r.data),
}
