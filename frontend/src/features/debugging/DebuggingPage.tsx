import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { sessionsApi } from '@/services/api'
import { LoadingState, StatusBadge } from '@/components/ui'
import { Bug, Send, CheckCircle, Code2 } from 'lucide-react'
import Editor from '@monaco-editor/react'
import { clsx } from 'clsx'

function NewDebugForm({ onStart }: { onStart: (id: string) => void }) {
  const [form, setForm] = useState({
    title: '',
    description: '',
    buggy_code: '# Paste your buggy code here\ndef example(n):\n    pass\n',
    language: 'python',
    expected_behavior: '',
  })
  const createMutation = useMutation({
    mutationFn: (data: typeof form) => sessionsApi.create({ ...data, session_type: 'debugging' }),
    onSuccess: (session) => onStart(session.id),
  })

  return (
    <div className="h-full overflow-y-auto p-6 max-w-3xl mx-auto">
      <div className="card p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-orange-50 flex items-center justify-center">
            <Bug className="w-5 h-5 text-orange-600" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-gray-900">New Debugging Session</h2>
            <p className="text-xs text-gray-500">TreeInstruct-powered Socratic debugging</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="label">Task title</label>
            <input className="input" placeholder="Fix the binary search bug" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </div>
          <div>
            <label className="label">Bug description *</label>
            <textarea className="input resize-none" rows={2} placeholder="Describe what the code should do vs. what it actually does…" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>
          <div>
            <label className="label">Language</label>
            <select className="input" value={form.language} onChange={(e) => setForm({ ...form, language: e.target.value })}>
              {['python', 'javascript', 'typescript', 'java', 'cpp', 'c'].map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Buggy code *</label>
            <div className="border border-gray-300 rounded-lg overflow-hidden">
              <Editor
                height="200px"
                language={form.language}
                value={form.buggy_code}
                onChange={(v) => setForm({ ...form, buggy_code: v ?? '' })}
                theme="vs"
                options={{ minimap: { enabled: false }, fontSize: 13, lineNumbers: 'on', scrollBeyondLastLine: false }}
              />
            </div>
          </div>
          <div>
            <label className="label">Expected behavior</label>
            <input className="input" placeholder="Should return sorted array in ascending order…" value={form.expected_behavior} onChange={(e) => setForm({ ...form, expected_behavior: e.target.value })} />
          </div>
          <button
            className="btn-primary w-full justify-center"
            disabled={!form.description || !form.buggy_code || createMutation.isPending}
            onClick={() => createMutation.mutate(form)}
          >
            {createMutation.isPending ? 'Starting…' : 'Start Debugging Session'}
          </button>
        </div>
      </div>
    </div>
  )
}

function DebuggingWorkspace({ sessionId }: { sessionId: string }) {
  const [response, setResponse] = useState('')
  const [fixCode, setFixCode] = useState('')
  const [tab, setTab] = useState<'qa' | 'fix'>('qa')
  const qc = useQueryClient()

  const { data: histData, isLoading } = useQuery({
    queryKey: ['session-history', sessionId],
    queryFn: () => sessionsApi.history(sessionId),
  })
  const { data: states } = useQuery({
    queryKey: ['session-states', sessionId],
    queryFn: () => sessionsApi.states(sessionId),
  })

  const sendMutation = useMutation({
    mutationFn: (content: string) => sessionsApi.sendMessage(sessionId, content),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['session-history', sessionId] })
      qc.invalidateQueries({ queryKey: ['session-states', sessionId] })
      setResponse('')
    },
  })

  if (isLoading) return <LoadingState />

  const messages = histData?.messages ?? []
  const session = histData?.session
  const tutor_messages = messages.filter((m) => m.role === 'tutor')
  const last_tutor = tutor_messages[tutor_messages.length - 1]

  const buggyCode = (session as unknown as { buggy_code?: string })?.buggy_code ?? ''

  return (
    <div className="h-full flex">
      {/* Left panel: code + states */}
      <div className="w-80 flex-shrink-0 border-r border-gray-200 bg-white flex flex-col">
        <div className="px-4 py-3 border-b border-gray-200">
          <h3 className="text-xs font-semibold text-gray-900 uppercase tracking-wide">Task Overview</h3>
        </div>

        {/* Learning states */}
        <div className="px-4 py-3 border-b border-gray-100">
          <p className="text-xs text-gray-500 mb-2 font-medium">Learning States</p>
          {(!states || states.length === 0) ? (
            <p className="text-xs text-gray-400">States will appear as the session progresses</p>
          ) : (
            <div className="space-y-1.5">
              {states.map((s) => (
                <div key={s.id} className="flex items-center gap-2">
                  <div className={clsx(
                    'w-2 h-2 rounded-full flex-shrink-0',
                    s.status === 'resolved' ? 'bg-green-500' :
                    s.status === 'in_progress' ? 'bg-blue-500' :
                    s.status === 'unresolved' ? 'bg-red-400' : 'bg-gray-300'
                  )} />
                  <span className="text-xs text-gray-700 truncate flex-1">{s.name}</span>
                  <StatusBadge status={s.status} />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Buggy code */}
        <div className="flex-1 overflow-hidden flex flex-col">
          <p className="text-xs text-gray-500 font-medium px-4 py-2">Original Code</p>
          <div className="flex-1 overflow-hidden">
            <Editor
              height="100%"
              language={session?.session_type === 'debugging' ? 'python' : 'python'}
              value={buggyCode || '// Code not loaded'}
              theme="vs"
              options={{ readOnly: true, minimap: { enabled: false }, fontSize: 12, lineNumbers: 'on' }}
            />
          </div>
        </div>
      </div>

      {/* Right: Q&A + Fix */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Tabs */}
        <div className="flex-shrink-0 border-b border-gray-200 bg-white px-4 flex gap-1 pt-2">
          {(['qa', 'fix'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={clsx(
                'px-4 py-2 text-sm font-medium rounded-t-lg border-b-2 transition-colors',
                tab === t
                  ? 'border-brand-600 text-brand-700 bg-brand-50'
                  : 'border-transparent text-gray-500 hover:text-gray-700',
              )}
            >
              {t === 'qa' ? '💬 Q&A' : '🔧 Propose Fix'}
            </button>
          ))}
        </div>

        {tab === 'qa' ? (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Current question */}
            {last_tutor && (
              <div className="flex-shrink-0 border-b border-gray-100 bg-amber-50 p-4">
                <p className="text-xs text-amber-700 font-semibold mb-1 flex items-center gap-1.5">
                  <Bug className="w-3.5 h-3.5" /> Current Question
                </p>
                <p className="text-sm text-gray-800">{last_tutor.content}</p>
              </div>
            )}

            {/* History */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={clsx(
                    'rounded-lg p-3 text-sm',
                    m.role === 'student' ? 'bg-brand-50 text-brand-900 ml-8' : 'bg-gray-50 text-gray-800 mr-8',
                  )}
                >
                  <span className="text-xs font-semibold block mb-1 text-gray-400">
                    {m.role === 'student' ? 'You' : 'Tutor'}
                  </span>
                  {m.content}
                  {m.metadata?.assessment && (
                    <div className="mt-2 text-xs text-gray-500">
                      Verdict: <span className="font-medium">{m.metadata.assessment.justification}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Response input */}
            <div className="flex-shrink-0 border-t border-gray-200 bg-white p-4">
              <div className="flex gap-3">
                <textarea
                  className="input flex-1 resize-none"
                  rows={2}
                  placeholder="Your response to the question…"
                  value={response}
                  onChange={(e) => setResponse(e.target.value)}
                />
                <button
                  className="btn-primary flex-shrink-0 h-11 px-4 self-end"
                  disabled={!response.trim() || sendMutation.isPending}
                  onClick={() => sendMutation.mutate(response)}
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="p-4 border-b border-gray-100 bg-green-50">
              <p className="text-xs text-green-700 font-semibold flex items-center gap-1.5">
                <CheckCircle className="w-3.5 h-3.5" /> Propose Your Fix
              </p>
              <p className="text-xs text-green-600 mt-0.5">Submit your corrected code to validate it</p>
            </div>
            <div className="flex-1 overflow-hidden">
              <Editor
                height="100%"
                language="python"
                value={fixCode || buggyCode}
                onChange={(v) => setFixCode(v ?? '')}
                theme="vs"
                options={{ minimap: { enabled: false }, fontSize: 13 }}
              />
            </div>
            <div className="flex-shrink-0 border-t border-gray-200 p-4 flex justify-end gap-3">
              <button
                className="btn-primary"
                disabled={!fixCode.trim() || sendMutation.isPending}
                onClick={() => sendMutation.mutate(`[PROPOSED FIX]\n\`\`\`\n${fixCode}\n\`\`\``)}
              >
                <Code2 className="w-4 h-4" />
                Submit Fix for Validation
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export function DebuggingPage() {
  const { sessionId } = useParams<{ sessionId?: string }>()
  const navigate = useNavigate()

  return (
    <div className="h-full flex flex-col">
      <div className="flex-shrink-0 px-5 py-3 border-b border-gray-200 bg-white flex items-center gap-3">
        <div className="w-7 h-7 rounded-lg bg-orange-50 flex items-center justify-center">
          <Bug className="w-4 h-4 text-orange-600" />
        </div>
        <h1 className="text-base font-semibold text-gray-900">Code Debugging Workspace</h1>
        <span className="badge-blue text-xs">TreeInstruct</span>
        {sessionId && (
          <button onClick={() => navigate('/debug')} className="ml-auto btn-ghost text-xs">New Task</button>
        )}
      </div>

      <div className="flex-1 overflow-hidden">
        {!sessionId ? (
          <NewDebugForm onStart={(id) => navigate(`/debug/${id}`)} />
        ) : (
          <DebuggingWorkspace sessionId={sessionId} />
        )}
      </div>
    </div>
  )
}
