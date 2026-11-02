import { useState, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { coursesApi, documentsApi } from '@/services/api'
import { LoadingState, ErrorState, StatusBadge, PageHeader, EmptyState } from '@/components/ui'
import { Upload, Trash2, FileText, AlertCircle, CheckCircle, Clock, RefreshCw } from 'lucide-react'
import { clsx } from 'clsx'

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

export function KnowledgeBasePage() {
  const { courseId } = useParams<{ courseId?: string }>()
  const { data: courses } = useQuery({ queryKey: ['courses'], queryFn: coursesApi.list })
  const [selectedCourseId, setSelectedCourseId] = useState(courseId ?? '')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const qc = useQueryClient()

  const {
    data: docs,
    isLoading: docsLoading,
    error: docsError,
    refetch,
  } = useQuery({
    queryKey: ['documents', selectedCourseId],
    queryFn: () => documentsApi.list(selectedCourseId),
    enabled: !!selectedCourseId,
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => documentsApi.upload(selectedCourseId, file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents', selectedCourseId] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (docId: string) => documentsApi.delete(selectedCourseId, docId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['documents', selectedCourseId] }),
  })

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const files = Array.from(e.dataTransfer.files)
    files.forEach((f) => uploadMutation.mutate(f))
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? [])
    files.forEach((f) => uploadMutation.mutate(f))
    e.target.value = ''
  }

  const statusIcon = (status: string) => {
    const map: Record<string, React.ReactNode> = {
      ready: <CheckCircle className="w-4 h-4 text-green-500" />,
      processing: <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />,
      pending: <Clock className="w-4 h-4 text-yellow-500" />,
      failed: <AlertCircle className="w-4 h-4 text-red-500" />,
    }
    return map[status] ?? <FileText className="w-4 h-4 text-gray-400" />
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <PageHeader
        title="Knowledge Base"
        subtitle="Upload course documents for AI-grounded tutoring and source citations"
      />

      {/* Course selector */}
      <div className="card p-4 mb-6">
        <label className="label">Select Course</label>
        <select
          className="input max-w-sm"
          value={selectedCourseId}
          onChange={(e) => setSelectedCourseId(e.target.value)}
        >
          <option value="">— Select a course —</option>
          {courses?.map((c) => <option key={c.id} value={c.id}>{c.code} — {c.title}</option>)}
        </select>
      </div>

      {!selectedCourseId ? (
        <EmptyState title="Select a course" description="Choose a course above to manage its knowledge base" />
      ) : (
        <>
          {/* Upload zone */}
          <div
            className={clsx(
              'border-2 border-dashed rounded-xl p-8 text-center mb-6 transition-colors',
              uploadMutation.isPending ? 'border-brand-300 bg-brand-50' : 'border-gray-200 hover:border-brand-300 cursor-pointer',
            )}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input ref={fileInputRef} type="file" multiple accept=".pdf,.txt,.md,.docx" className="hidden" onChange={handleFileSelect} />
            {uploadMutation.isPending ? (
              <div className="flex items-center justify-center gap-3 text-brand-600">
                <RefreshCw className="w-5 h-5 animate-spin" />
                <span className="text-sm font-medium">Uploading…</span>
              </div>
            ) : (
              <>
                <Upload className="w-8 h-8 text-gray-300 mx-auto mb-3" />
                <p className="text-sm font-medium text-gray-600">Drop files here or click to upload</p>
                <p className="text-xs text-gray-400 mt-1">PDF, TXT, MD, DOCX · Max 25MB per file</p>
              </>
            )}
          </div>

          {uploadMutation.isError && (
            <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              Upload failed: {(uploadMutation.error as { response?: { data?: { error?: { message?: string } } } })?.response?.data?.error?.message ?? 'Unknown error'}
            </div>
          )}

          {/* Document list */}
          {docsLoading ? <LoadingState /> : docsError ? <ErrorState message="Could not load documents" onRetry={refetch} /> : (
            <>
              {(!docs || docs.length === 0) ? (
                <EmptyState
                  title="No documents uploaded"
                  description="Upload course materials to enable grounded AI responses with source citations"
                />
              ) : (
                <div className="space-y-2">
                  {docs.map((doc) => (
                    <div key={doc.id} className="card p-4 flex items-start gap-4">
                      {statusIcon(doc.status)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-800 truncate">{doc.original_filename}</p>
                        <div className="flex items-center gap-3 mt-1">
                          <StatusBadge status={doc.status} />
                          {doc.file_size_bytes && <span className="text-xs text-gray-400">{formatBytes(doc.file_size_bytes)}</span>}
                          {doc.page_count && <span className="text-xs text-gray-400">{doc.page_count} pages</span>}
                          <span className="text-xs text-gray-400">{new Date(doc.created_at).toLocaleDateString()}</span>
                        </div>
                        {doc.error_message && (
                          <p className="text-xs text-red-600 mt-1 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" /> {doc.error_message}
                          </p>
                        )}
                      </div>
                      <button
                        onClick={() => {
                          if (confirm(`Delete "${doc.original_filename}"?`)) deleteMutation.mutate(doc.id)
                        }}
                        disabled={deleteMutation.isPending}
                        className="p-1.5 rounded hover:bg-red-50 text-gray-400 hover:text-red-600 transition-colors flex-shrink-0"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}
