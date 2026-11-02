import { clsx } from 'clsx'

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-gray-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </div>
  )
}

export function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeMap = { sm: 'h-4 w-4', md: 'h-8 w-8', lg: 'h-12 w-12' }
  return (
    <div className={clsx('animate-spin rounded-full border-b-2 border-brand-600', sizeMap[size])} />
  )
}

export function LoadingState({ message = 'Loading…' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3">
      <LoadingSpinner />
      <p className="text-sm text-gray-500">{message}</p>
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3">
      <div className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center">
        <span className="text-red-500 text-xl">⚠</span>
      </div>
      <p className="text-sm text-gray-700 font-medium">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary text-xs">Try again</button>
      )}
    </div>
  )
}

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3">
      <div className="w-16 h-16 rounded-2xl bg-gray-100 flex items-center justify-center text-3xl">
        📭
      </div>
      <p className="text-base font-medium text-gray-700">{title}</p>
      {description && <p className="text-sm text-gray-400 text-center max-w-xs">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

export function UnderstandingBadge({ level }: { level: number }) {
  const configs = [
    { label: 'Confused', cls: 'level-0' },
    { label: 'Beginner', cls: 'level-1' },
    { label: 'Developing', cls: 'level-2' },
    { label: 'Mastered', cls: 'level-3' },
  ]
  const config = configs[level] ?? configs[1]
  return <span className={config.cls}>{config.label}</span>
}

export function HintDepthBadge({ depth }: { depth: number }) {
  const labels = ['', 'Conceptual', 'Directional', 'Partial Reveal', 'Full Solution']
  const colors = ['', 'badge-green', 'badge-blue', 'badge-yellow', 'badge-red']
  return <span className={colors[depth] ?? 'badge-gray'}>{labels[depth] ?? `Depth ${depth}`}</span>
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    active: 'badge-green',
    completed: 'badge-blue',
    abandoned: 'badge-gray',
    pending: 'badge-yellow',
    processing: 'badge-blue',
    ready: 'badge-green',
    failed: 'badge-red',
    resolved: 'badge-green',
    unresolved: 'badge-red',
    in_progress: 'badge-blue',
  }
  return <span className={map[status] ?? 'badge-gray'}>{status.replace('_', ' ')}</span>
}
