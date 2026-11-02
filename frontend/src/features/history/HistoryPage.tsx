import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { studentsApi } from '@/services/api'
import { LoadingState, ErrorState, EmptyState, PageHeader, StatusBadge } from '@/components/ui'
import { MessageSquare, Bug, Clock, ArrowRight } from 'lucide-react'

export function HistoryPage() {
  const { data: progress, isLoading, error, refetch } = useQuery({
    queryKey: ['progress'],
    queryFn: studentsApi.progress,
  })

  if (isLoading) return <div className="p-6"><LoadingState /></div>
  if (error) return <div className="p-6"><ErrorState message="Could not load history" onRetry={refetch} /></div>

  const sessions = progress?.recent_sessions ?? []

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <PageHeader title="Session History" subtitle="Browse and resume your past tutoring and debugging sessions" />

      {sessions.length === 0 ? (
        <EmptyState
          title="No sessions yet"
          description="Start a tutoring or debugging session to see it here"
          action={<Link to="/tutor" className="btn-primary">Start a session</Link>}
        />
      ) : (
        <div className="space-y-3">
          {sessions.map((session) => (
            <Link
              key={session.id}
              to={session.session_type === 'debugging' ? `/debug/${session.id}` : `/tutor/${session.id}`}
              className="card p-4 flex items-center gap-4 hover:shadow-md transition-shadow group"
            >
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                session.session_type === 'debugging' ? 'bg-orange-50' : 'bg-brand-50'
              }`}>
                {session.session_type === 'debugging' ? (
                  <Bug className="w-5 h-5 text-orange-600" />
                ) : (
                  <MessageSquare className="w-5 h-5 text-brand-600" />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 truncate group-hover:text-brand-700">
                  {session.title || session.concept || 'Untitled session'}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <StatusBadge status={session.status} />
                  <span className="text-xs text-gray-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(session.created_at).toLocaleString()}
                  </span>
                  {session.course_id && (
                    <span className="text-xs text-gray-400">· {session.session_type}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {session.status === 'active' && (
                  <span className="text-xs font-medium text-green-600 bg-green-50 px-2 py-0.5 rounded-full">Resume</span>
                )}
                <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-brand-500 transition-colors" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

