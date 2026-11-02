import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { sessionsApi, coursesApi } from '@/services/api'
import { UnderstandingBadge, HintDepthBadge, LoadingState, ErrorState } from '@/components/ui'
import type { Message } from '@/types'
import {
  Send, Lightbulb, ChevronDown, ChevronUp,
  Quote, Plus, MessageSquare,
} from 'lucide-react'
import { clsx } from 'clsx'

// ── New session form ───────────────────────────────────────────────────────────

function NewSessionForm({ onStart }: { onStart: (sessionId: string) => void }) {
  const { data: courses } = useQuery({ queryKey: ['courses'], queryFn: coursesApi.list })
  const [courseId, setCourseId] = useState('')
  const [concept, setConcept] = useState('')
  const createMutation = useMutation({
    mutationFn: sessionsApi.create,
    onSuccess: (session) => onStart(session.id),
  })

  return (
    <div className="flex-1 flex items-center justify-center p-8">
      <div className="card p-8 w-full max-w-md">
        <div className="w-12 h-12 rounded-xl bg-brand-50 flex items-center justify-center mb-4">
          <MessageSquare className="w-6 h-6 text-brand-600" />
        </div>
        <h2 className="text-lg font-semibold text-gray-900 mb-1">Start a Tutoring Session</h2>
        <p className="text-sm text-gray-500 mb-6">Ask about any concept — I'll guide you through Socratic questioning.</p>

        <div className="space-y-4">
          <div>
            <label className="label">Course (optional)</label>
            <select className="input" value={courseId} onChange={(e) => setCourseId(e.target.value)}>
              <option value="">General tutoring</option>
              {courses?.map((c) => (
                <option key={c.id} value={c.id}>{c.code} — {c.title}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Topic or concept</label>
            <input
              className="input"
              placeholder="e.g., recursion, binary search, pointers…"
              value={concept}
              onChange={(e) => setConcept(e.target.value)}
            />
          </div>
          <button
            className="btn-primary w-full justify-center"
            disabled={createMutation.isPending}
            onClick={() => createMutation.mutate({
              course_id: courseId || undefined,
              session_type: 'tutoring',
              concept: concept || undefined,
              title: concept ? `Tutoring: ${concept}` : 'Tutoring Session',
            })}
          >
            {createMutation.isPending ? 'Starting…' : 'Start Session'}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Message bubble ─────────────────────────────────────────────────────────────

function MessageBubble({ msg }: { msg: Message }) {
  const [showDetails, setShowDetails] = useState(false)
  const isStudent = msg.role === 'student'

  return (
    <div className={clsx('flex gap-3', isStudent ? 'flex-row-reverse' : 'flex-row')}>
      {/* Avatar */}
      <div className={clsx(
        'w-7 h-7 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold mt-1',
        isStudent ? 'bg-brand-600 text-white' : 'bg-gray-100 text-gray-600',
      )}>
        {isStudent ? 'S' : 'T'}
      </div>

      <div className={clsx('max-w-[75%] space-y-1', isStudent ? 'items-end' : 'items-start')}>
        <div className={isStudent ? 'chat-bubble-student' : 'chat-bubble-tutor'}>
          <div className="prose prose-sm max-w-none prose-p:my-1 prose-pre:my-2 whitespace-pre-wrap break-words">
            {msg.content}
          </div>
        </div>

        {/* Metadata (tutor messages only) */}
        {!isStudent && msg.metadata && (
          <div className="ml-0.5">
            <button
              onClick={() => setShowDetails((v) => !v)}
              className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-600"
            >
              <Lightbulb className="w-3 h-3" />
              Explanation details
              {showDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>

            {showDetails && (
              <div className="mt-2 rounded-lg border border-gray-100 bg-gray-50 p-3 text-xs space-y-2 animate-fade-in">
                {msg.metadata.understanding_level !== undefined && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 w-28">Understanding:</span>
                    <UnderstandingBadge level={msg.metadata.understanding_level} />
                  </div>
                )}
                {msg.metadata.hint_depth !== undefined && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 w-28">Hint depth:</span>
                    <HintDepthBadge depth={msg.metadata.hint_depth} />
                  </div>
                )}
                {msg.metadata.assessment?.justification && (
                  <div>
                    <span className="text-gray-500 block mb-1">Assessment:</span>
                    <p className="text-gray-700">{msg.metadata.assessment.justification}</p>
                  </div>
                )}
                {(msg.metadata.assessment?.misconceptions ?? []).length > 0 && (
                  <div>
                    <span className="text-gray-500 block mb-1">Identified misconceptions:</span>
                    <ul className="list-disc list-inside text-gray-600 space-y-0.5">
                      {(msg.metadata.assessment?.misconceptions ?? []).map((m: string, i: number) => (
                        <li key={i}>{m}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {(msg.metadata.citations ?? []).length > 0 && (
                  <div>
                    <span className="text-gray-500 block mb-1 flex items-center gap-1">
                      <Quote className="w-3 h-3" /> Sources:
                    </span>
                    <ul className="space-y-1">
                      {(msg.metadata.citations ?? []).map((c, i) => (
                        <li key={i} className="text-gray-600">
                          📄 {c.document}{c.section ? ` › ${c.section}` : ''}{c.page ? ` (p.${c.page})` : ''}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        <p className="text-[10px] text-gray-300 px-1">
          {new Date(msg.created_at).toLocaleTimeString()}
        </p>
      </div>
    </div>
  )
}

// ── Chat workspace ─────────────────────────────────────────────────────────────

function ChatWorkspace({ sessionId }: { sessionId: string }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)
  const qc = useQueryClient()

  const { data, isLoading, error } = useQuery({
    queryKey: ['session-history', sessionId],
    queryFn: () => sessionsApi.history(sessionId),
  })

  const sendMutation = useMutation({
    mutationFn: (content: string) => sessionsApi.sendMessage(sessionId, content),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['session-history', sessionId] })
    },
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [data?.messages])

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed || sendMutation.isPending) return
    setInput('')
    sendMutation.mutate(trimmed)
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (isLoading) return <LoadingState message="Loading session…" />
  if (error) return <ErrorState message="Could not load session" />

  const messages = data?.messages ?? []
  const session = data?.session

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-gray-200 bg-white px-5 py-3 flex items-center gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900 truncate">
            {session?.title || session?.concept || 'Tutoring Session'}
          </p>
          <p className="text-xs text-gray-400">{messages.length} messages · {session?.status}</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4 scrollbar-thin">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="w-12 h-12 rounded-xl bg-brand-50 flex items-center justify-center mx-auto mb-3">
              <Lightbulb className="w-6 h-6 text-brand-600" />
            </div>
            <p className="text-sm text-gray-500">Ask your first question — I'll guide you with Socratic hints.</p>
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}
        {sendMutation.isPending && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-gray-100 flex-shrink-0 flex items-center justify-center text-xs">T</div>
            <div className="chat-bubble-tutor flex items-center gap-1.5 text-gray-400">
              <span className="animate-pulse">●</span>
              <span className="animate-pulse" style={{ animationDelay: '0.2s' }}>●</span>
              <span className="animate-pulse" style={{ animationDelay: '0.4s' }}>●</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex-shrink-0 border-t border-gray-200 bg-white p-4">
        <div className="flex gap-3 items-end">
          <div className="flex-1 relative">
            <textarea
              className="input resize-none pr-4 min-h-[44px] max-h-32 py-2.5"
              rows={1}
              placeholder="Ask a question… (Enter to send, Shift+Enter for newline)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              disabled={sendMutation.isPending}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={!input.trim() || sendMutation.isPending}
            className="btn-primary flex-shrink-0 h-11 px-4"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-[10px] text-gray-300 mt-1.5 text-center">
          Type "I give up, show me the solution" to reveal a full worked solution.
        </p>
      </div>
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────────────────

export function TutoringPage() {
  const { sessionId } = useParams<{ sessionId?: string }>()
  const navigate = useNavigate()

  const handleStart = (id: string) => navigate(`/tutor/${id}`)

  return (
    <div className="h-full flex flex-col">
      <div className="flex-shrink-0 px-5 py-3 border-b border-gray-200 bg-white flex items-center gap-3">
        <div className="w-7 h-7 rounded-lg bg-brand-50 flex items-center justify-center">
          <MessageSquare className="w-4 h-4 text-brand-600" />
        </div>
        <h1 className="text-base font-semibold text-gray-900">AI Tutoring Workspace</h1>
        {sessionId && (
          <button onClick={() => navigate('/tutor')} className="ml-auto btn-ghost text-xs gap-1">
            <Plus className="w-3 h-3" /> New Session
          </button>
        )}
      </div>

      <div className="flex-1 overflow-hidden">
        {!sessionId ? (
          <NewSessionForm onStart={handleStart} />
        ) : (
          <ChatWorkspace sessionId={sessionId} />
        )}
      </div>
    </div>
  )
}
