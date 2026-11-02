import { useQuery } from '@tanstack/react-query'
import { studentsApi } from '@/services/api'
import { LoadingState, ErrorState, PageHeader, UnderstandingBadge } from '@/components/ui'
import { TrendingUp, Brain, AlertTriangle, Target } from 'lucide-react'

export function ProgressPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['progress'],
    queryFn: studentsApi.progress,
  })

  if (isLoading) return <div className="p-6"><LoadingState /></div>
  if (error) return <div className="p-6"><ErrorState message="Could not load progress" onRetry={refetch} /></div>

  const concepts = Object.entries(data?.concept_scores ?? {}).sort((a, b) => b[1] - a[1])
  const strong = concepts.filter(([, s]) => s >= 2.5)
  const developing = concepts.filter(([, s]) => s >= 1.5 && s < 2.5)
  const struggling = concepts.filter(([, s]) => s < 1.5)

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <PageHeader
        title="Learning Progress"
        subtitle="Your personalised learning profile and concept mastery"
      />

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Sessions', value: data?.total_sessions ?? 0, icon: Target, color: 'text-brand-600 bg-brand-50' },
          { label: 'Messages', value: data?.total_messages ?? 0, icon: TrendingUp, color: 'text-green-600 bg-green-50' },
          { label: 'Mastered', value: strong.length, icon: Brain, color: 'text-emerald-600 bg-emerald-50' },
          { label: 'Struggling', value: struggling.length, icon: AlertTriangle, color: 'text-red-600 bg-red-50' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card p-4">
            <div className={`w-9 h-9 rounded-lg ${color} flex items-center justify-center mb-3`}>
              <Icon className="w-5 h-5" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <p className="text-xs text-gray-500">{label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Concept breakdown */}
        <div className="lg:col-span-2 space-y-4">
          {[
            { title: '✅ Mastered Concepts', items: strong, empty: 'Keep studying to master concepts!' },
            { title: '📈 Developing', items: developing, empty: 'No concepts at developing stage yet.' },
            { title: '⚠ Needs Practice', items: struggling, empty: 'Great — no struggling areas!' },
          ].map(({ title, items, empty }) => (
            <div key={title} className="card p-5">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">{title}</h3>
              {items.length === 0 ? (
                <p className="text-xs text-gray-400">{empty}</p>
              ) : (
                <div className="space-y-2">
                  {items.map(([concept, score]) => (
                    <div key={concept} className="flex items-center gap-3">
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-medium text-gray-700 capitalize">{concept}</span>
                          <UnderstandingBadge level={Math.round(score)} />
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-1.5">
                          <div
                            className="bg-brand-500 h-1.5 rounded-full transition-all"
                            style={{ width: `${(score / 3) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Misconceptions */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-500" />
            Recurring Misconceptions
          </h3>
          {(!data?.misconceptions || data.misconceptions.length === 0) ? (
            <p className="text-xs text-gray-400">No misconceptions recorded yet — keep up the great work!</p>
          ) : (
            <div className="space-y-3">
              {data.misconceptions.slice(0, 10).map((m, i) => (
                <div key={i} className="rounded-lg bg-orange-50 border border-orange-100 p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-orange-700 capitalize">{m.concept}</span>
                    <span className="text-xs text-orange-500">×{m.count}</span>
                  </div>
                  <p className="text-xs text-gray-600">{m.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
