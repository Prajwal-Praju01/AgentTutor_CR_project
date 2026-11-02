import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { coursesApi, documentsApi } from '@/services/api'
import { LoadingState, ErrorState, PageHeader, StatusBadge } from '@/components/ui'
import { Link } from 'react-router-dom'
import { MessageSquare, FileText, BookOpen, Play } from 'lucide-react'

export function CourseDetailPage() {
  const { courseId } = useParams<{ courseId: string }>()

  const { data: course, isLoading: cLoading, error: cError } = useQuery({
    queryKey: ['course', courseId],
    queryFn: () => coursesApi.get(courseId!),
    enabled: !!courseId,
  })
  const { data: docs } = useQuery({
    queryKey: ['documents', courseId],
    queryFn: () => documentsApi.list(courseId!),
    enabled: !!courseId,
  })

  if (cLoading) return <div className="p-6"><LoadingState /></div>
  if (cError || !course) return <div className="p-6"><ErrorState message="Could not load course" /></div>

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <PageHeader
        title={course.title}
        subtitle={course.code}
        actions={
          <Link to="/tutor" state={{ courseId: course.id }} className="btn-primary">
            <Play className="w-4 h-4" /> Start Tutoring
          </Link>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          {course.description && (
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-brand-500" /> Description
              </h3>
              <p className="text-sm text-gray-600">{course.description}</p>
            </div>
          )}
          {course.syllabus && (
            <div className="card p-5">
              <h3 className="text-sm font-semibold text-gray-900 mb-2">Syllabus</h3>
              <pre className="text-sm text-gray-600 whitespace-pre-wrap font-sans">{course.syllabus}</pre>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="card p-5">
            <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <FileText className="w-4 h-4 text-brand-500" /> Documents ({docs?.length ?? 0})
            </h3>
            {!docs?.length ? (
              <p className="text-xs text-gray-400 mb-3">No documents uploaded yet</p>
            ) : (
              <div className="space-y-2 mb-3">
                {docs.slice(0, 5).map((d) => (
                  <div key={d.id} className="flex items-center gap-2">
                    <StatusBadge status={d.status} />
                    <span className="text-xs text-gray-600 truncate">{d.original_filename}</span>
                  </div>
                ))}
                {docs.length > 5 && <p className="text-xs text-gray-400">+{docs.length - 5} more</p>}
              </div>
            )}
            <Link to={`/knowledge/${courseId}`} className="btn-secondary w-full justify-center text-xs">
              Manage Documents
            </Link>
          </div>

          <div className="card p-5 space-y-2">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Quick Actions</h3>
            <Link to="/tutor" className="btn-secondary w-full justify-center text-xs gap-2">
              <MessageSquare className="w-3.5 h-3.5" /> Start Tutoring Session
            </Link>
            <Link to="/debug" className="btn-secondary w-full justify-center text-xs gap-2">
              Start Debug Session
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
