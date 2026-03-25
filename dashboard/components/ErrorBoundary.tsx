'use client'

import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  message: string
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, message: '' }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error?.message ?? 'Unknown error' }
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="min-h-screen bg-bg flex items-center justify-center px-4">
          <div className="bg-card border border-line rounded p-8 max-w-md w-full text-center space-y-4">
            <p className="text-xs font-mono uppercase tracking-widest text-muted">
              Dashboard Error
            </p>
            <p className="font-mono text-white text-sm">
              Something went wrong loading the dashboard.
            </p>
            <p className="font-mono text-[#555] text-xs break-all">{this.state.message}</p>
            <button
              onClick={() => this.setState({ hasError: false, message: '' })}
              className="mt-2 px-4 py-2 text-xs font-mono bg-positive/10 text-positive border border-positive/30 rounded hover:bg-positive/20 transition-colors"
            >
              Retry
            </button>
          </div>
        </main>
      )
    }
    return this.props.children
  }
}
