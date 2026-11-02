import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { coursesApi } from '@/services/api'
import { LoadingState, ErrorState, EmptyState, PageHeader } from '@/components/ui'
import { BookOpen, Plus, Search, ChevronRight, FileText, X } from 'lucide-react'

export function CoursesPage() {
  const qc = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [search, setSearch] = useState('')
  const [form, setForm] = useState({ title: '', code: '', description: '', syllabus: '' })
  const [formError, setFormError] = useState('')

  const { data: courses, isLoading, error, refetch } = useQuery({
    queryKey: ['courses'],
    queryFn: coursesApi.list,
  })

  const createMutation = useMutation({
    mutationFn: coursesApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['courses'] })
      setShowCreate(false)
      setForm({ title: '', code: '', description: '', syllabus: '' })
    },
    onError: (err: unknown) => {
      const e = err as { response?: { data?: { error?: { message?: string } } } }
      setFormError(e.response?.data?.error?.message || 'Failed to create course')
    },
  })

  const filtered = (courses ?? []).filter((c) =>
    `${c.title} ${c.code} ${c.description ?? ''}`.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <PageHeader
        title="Courses"
        subtitle="Your enrolled courses and learning materials"
        actions={
          <button onClick={() => setShowCreate(true)} className="btn-primary">
            <Plus className="w-4 h-4" /> New Course
          </button>
        }
      />

      {/* Search */}
      <div className="relative mb-5">
        <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
        <input
          type="search"
          placeholder="Search courses…"
          className="input pl-9"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading ? <LoadingState /> : error ? <ErrorState message="Could not load courses" onRetry={refetch} /> : (
        <>
          {filtered.length === 0 ? (
            <EmptyState
              title="No courses found"
              description={search ? 'Try a different search' : 'Create your first course to get started'}
              action={!search && <button onClick={() => setShowCreate(true)} className="btn-primary">Create course</button>}
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filtered.map((course) => (
                <Link
                  key={course.id}
                  to={`/courses/${course.id}`}
                  className="card p-5 hover:shadow-md transition-shadow group"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center flex-shrink-0">
                      <BookOpen className="w-5 h-5 text-brand-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-mono font-medium text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">{course.code}</span>
                      </div>
                      <h3 className="text-sm font-semibold text-gray-900 group-hover:text-brand-700 truncate">{course.title}</h3>
                      {course.description && (
                        <p className="text-xs text-gray-400 mt-1 line-clamp-2">{course.description}</p>
                      )}
                      <div className="flex items-center gap-3 mt-3">
                        <span className="flex items-center gap-1 text-xs text-gray-400">
                          <FileText className="w-3 h-3" /> {course.document_count} docs
                        </span>
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-brand-500 flex-shrink-0 mt-1 transition-colors" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </>
      )}

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
            <div className="flex items-center justify-between p-5 border-b">
              <h2 className="text-base font-semibold text-gray-900">Create Course</h2>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 space-y-4">
              {formError && <div className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{formError}</div>}
              <div>
                <label className="label">Course Title *</label>
                <input className="input" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Introduction to Python" />
              </div>
              <div>
                <label className="label">Course Code *</label>
                <input className="input font-mono" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} placeholder="CS101" />
              </div>
              <div>
                <label className="label">Description</label>
                <textarea className="input resize-none" rows={2} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Brief course description…" />
              </div>
              <div>
                <label className="label">Syllabus</label>
                <textarea className="input resize-none" rows={3} value={form.syllabus} onChange={(e) => setForm({ ...form, syllabus: e.target.value })} placeholder="Week 1: Variables…" />
              </div>
            </div>
            <div className="flex justify-end gap-3 px-5 pb-5">
              <button onClick={() => setShowCreate(false)} className="btn-secondary">Cancel</button>
              <button
                className="btn-primary"
                disabled={!form.title || !form.code || createMutation.isPending}
                onClick={() => {
                  setFormError('')
                  createMutation.mutate(form)
                }}
              >
                {createMutation.isPending ? 'Creating…' : 'Create Course'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

