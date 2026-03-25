import Dashboard from '@/components/Dashboard'
import ErrorBoundary from '@/components/ErrorBoundary'

export const dynamic = 'force-dynamic'

export default function Page() {
  return (
    <ErrorBoundary>
      <Dashboard />
    </ErrorBoundary>
  )
}
