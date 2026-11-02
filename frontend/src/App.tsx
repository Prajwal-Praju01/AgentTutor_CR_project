import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { AuthProvider } from '@/features/auth/AuthContext'
import { RequireAuth } from '@/features/auth/RequireAuth'
import { AppLayout } from '@/components/AppLayout'
import { LoginPage } from '@/features/auth/LoginPage'
import { RegisterPage } from '@/features/auth/RegisterPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { CoursesPage } from '@/features/courses/CoursesPage'
import { CourseDetailPage } from '@/features/courses/CourseDetailPage'
import { TutoringPage } from '@/features/tutoring/TutoringPage'
import { DebuggingPage } from '@/features/debugging/DebuggingPage'
import { ProgressPage } from '@/features/learning-progress/ProgressPage'
import { KnowledgeBasePage } from '@/features/knowledge-base/KnowledgeBasePage'
import { HistoryPage } from '@/features/history/HistoryPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
})

function ProtectedLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <AppLayout>{children}</AppLayout>
    </RequireAuth>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Protected */}
            <Route path="/dashboard" element={<ProtectedLayout><DashboardPage /></ProtectedLayout>} />
            <Route path="/courses" element={<ProtectedLayout><CoursesPage /></ProtectedLayout>} />
            <Route path="/courses/:courseId" element={<ProtectedLayout><CourseDetailPage /></ProtectedLayout>} />
            <Route path="/tutor" element={<ProtectedLayout><TutoringPage /></ProtectedLayout>} />
            <Route path="/tutor/:sessionId" element={<ProtectedLayout><TutoringPage /></ProtectedLayout>} />
            <Route path="/debug" element={<ProtectedLayout><DebuggingPage /></ProtectedLayout>} />
            <Route path="/debug/:sessionId" element={<ProtectedLayout><DebuggingPage /></ProtectedLayout>} />
            <Route path="/progress" element={<ProtectedLayout><ProgressPage /></ProtectedLayout>} />
            <Route path="/knowledge" element={<ProtectedLayout><KnowledgeBasePage /></ProtectedLayout>} />
            <Route path="/knowledge/:courseId" element={<ProtectedLayout><KnowledgeBasePage /></ProtectedLayout>} />
            <Route path="/history" element={<ProtectedLayout><HistoryPage /></ProtectedLayout>} />

            {/* Redirect */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}

