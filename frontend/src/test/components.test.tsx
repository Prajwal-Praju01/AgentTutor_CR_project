import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React from 'react'

// ── Component helpers ──────────────────────────────────────────────────────────

function wrapper(children: React.ReactNode) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={qc}>
      <MemoryRouter>{children}</MemoryRouter>
    </QueryClientProvider>
  )
}

// ── UI component tests ─────────────────────────────────────────────────────────

import { UnderstandingBadge, HintDepthBadge, StatusBadge, EmptyState, ErrorState } from '../components/ui'

describe('UnderstandingBadge', () => {
  it('renders Confused for level 0', () => {
    render(wrapper(<UnderstandingBadge level={0} />))
    expect(screen.getByText('Confused')).toBeInTheDocument()
  })

  it('renders Mastered for level 3', () => {
    render(wrapper(<UnderstandingBadge level={3} />))
    expect(screen.getByText('Mastered')).toBeInTheDocument()
  })

  it('renders Developing for level 2', () => {
    render(wrapper(<UnderstandingBadge level={2} />))
    expect(screen.getByText('Developing')).toBeInTheDocument()
  })
})

describe('HintDepthBadge', () => {
  it('renders Conceptual for depth 1', () => {
    render(wrapper(<HintDepthBadge depth={1} />))
    expect(screen.getByText('Conceptual')).toBeInTheDocument()
  })

  it('renders Full Solution for depth 4', () => {
    render(wrapper(<HintDepthBadge depth={4} />))
    expect(screen.getByText('Full Solution')).toBeInTheDocument()
  })
})

describe('StatusBadge', () => {
  it('renders active status', () => {
    render(wrapper(<StatusBadge status="active" />))
    expect(screen.getByText('active')).toBeInTheDocument()
  })

  it('renders completed status', () => {
    render(wrapper(<StatusBadge status="completed" />))
    expect(screen.getByText('completed')).toBeInTheDocument()
  })
})

describe('EmptyState', () => {
  it('renders title and description', () => {
    render(wrapper(<EmptyState title="Nothing here" description="Add something to get started" />))
    expect(screen.getByText('Nothing here')).toBeInTheDocument()
    expect(screen.getByText('Add something to get started')).toBeInTheDocument()
  })

  it('renders action button when provided', () => {
    render(wrapper(<EmptyState title="Empty" action={<button>Click me</button>} />))
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })
})

describe('ErrorState', () => {
  it('renders error message', () => {
    render(wrapper(<ErrorState message="Something went wrong" />))
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
  })

  it('calls onRetry when button clicked', async () => {
    const onRetry = vi.fn()
    render(wrapper(<ErrorState message="Error" onRetry={onRetry} />))
    fireEvent.click(screen.getByText('Try again'))
    expect(onRetry).toHaveBeenCalledOnce()
  })
})
