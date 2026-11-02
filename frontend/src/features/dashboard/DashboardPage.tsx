import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { studentsApi } from '@/services/api'
import { useAuth } from '@/features/auth/AuthContext'
import { LoadingState, ErrorState, UnderstandingBadge, StatusBadge, PageHeader } from '@/components/ui'
import { BookOpen, MessageSquare, Bug, TrendingUp, Clock, Plus, ArrowRight } from 'lucide-react'

export function DashboardPage() {
  const { user } = useAuth()
  const { data: progress, isLoading, error, refetch } = useQuery({
    queryKey: ['progress'],
    queryFn: studentsApi.progress,
  })

  if (isLoading) return (
    <div className="p-6">
      <PageHeader title="Dashboard" subtitle="Welcome back!" />
      <LoadingState message="Loading your progress…" />
    </div>
  )

  if (error) return (
    <div className="p-6">
      <PageHeader title="Dashboard" />
      <ErrorState message="Could not load progress data" onRetry={refetch} />
    </div>
  )

  const strongConcepts = Object.entries(progress?.concept_scores ?? {})
    .filter(([, score]) => score >= 2.5)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)

  const weakConcepts = Object.entries(progress?.concept_scores ?? {})
    .filter(([, score]) => score < 1.5)
    .sort((a, b) => a[1] - b[1])
    .slice(0, 5)

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <PageHeader
        title={`Welcome back, ${user?.display_name?.split(' ')[0] ?? 'Student'}!`}
        subtitle="Here's your learning summary"
        actions={
          <Link to="/tutor" className="btn-primary">
            <Plus className="w-4 h-4" />
            Start Tutoring
          </Link>
        }
      />

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total Sessions', value: progress?.total_sessions ?? 0, icon: MessageSquare, color: 'text-brand-600 bg-brand-50' },
          { label: 'Messages Exchanged', value: progress?.total_messages ?? 0, icon: TrendingUp, color: 'text-green-600 bg-green-50' },
          { label: 'Concepts Tracked', value: Object.keys(progress?.concept_scores ?? {}).length, icon: BookOpen, color: 'text-blue-600 bg-blue-50' },
          { label: 'Misconceptions Found', value: progress?.misconceptions?.length ?? 0, icon: Bug, color: 'text-orange-600 bg-orange-50' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card p-4">
            <div className={`w-9 h-9 rounded-lg ${color} flex items-center justify-center mb-3`}>
              <Icon className="w-5 h-5" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <p className="text-xs text-gray-500 mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent sessions */}
        <div className="lg:col-span-2 card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-900">Recent Sessions</h2>
            <Link to="/history" className="text-xs text-brand-600 hover:text-brand-700 flex items-center gap-1">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          {!progress?.recent_sessions?.length ? (
            <div className="text-center py-8">
              <p className="text-sm text-gray-400">No sessions yet</p>
              <Link to="/tutor" className="btn-primary mt-3 text-xs">Start your first session</Link>
            </div>
          ) : (
            <div className="space-y-2">
              {progress.recent_sessions.map((session) => (
                <Link
                  key={session.id}
                  to={session.session_type === 'debugging' ? `/debug/${session.id}` : `/tutor/${session.id}`}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors group"
                >
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    session.session_type === 'debugging' ? 'bg-orange-50' : 'bg-brand-50'
                  }`}>
                    {session.session_type === 'debugging' ? (
                      <Bug className="w-4 h-4 text-orange-600" />
                    ) : (
                      <MessageSquare className="w-4 h-4 text-brand-600" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">
                      {session.title || session.concept || 'Untitled session'}
                    </p>
                    <p className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                      <Clock className="w-3 h-3" />
                      {new Date(session.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <StatusBadge status={session.status} />
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Concept summary */}
        <div className="space-y-4">
          <div className="card p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Strong Concepts</h2>
            {strongConcepts.length === 0 ? (
              <p className="text-xs text-gray-400">No concepts mastered yet</p>
            ) : (
              <div className="space-y-2">
                {strongConcepts.map(([concept, score]) => (
                  <div key={concept} className="flex items-center gap-2">
                    <span className="text-xs text-gray-700 flex-1 truncate capitalize">{concept}</span>
                    <UnderstandingBadge level={Math.round(score)} />
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card p-5">
            <h2 className="text-sm font-semibold text-gray-900 mb-3">Needs Work</h2>
            {weakConcepts.length === 0 ? (
              <p className="text-xs text-gray-400">No struggling areas detected</p>
            ) : (
              <div className="space-y-2">
                {weakConcepts.map(([concept]) => (
                  <div key={concept} className="flex items-center gap-2">
                    <span className="text-xs text-gray-700 flex-1 truncate capitalize">{concept}</span>
                    <Link to="/tutor" className="text-xs text-brand-600 hover:underline">Practice</Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
