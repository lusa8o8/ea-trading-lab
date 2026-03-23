import type { Mode } from '@/lib/supabase'

function Skeleton() {
  return <div className="h-8 bg-[#1a1a1a] rounded animate-pulse mt-1" />
}

function StatCard({
  label,
  value,
  valueColor,
  subtext,
  loading,
}: {
  label: string
  value: string | null
  valueColor?: string
  subtext?: string
  loading: boolean
}) {
  return (
    <div className="bg-card border border-line rounded p-4">
      <p className="text-muted text-xs font-mono uppercase tracking-widest mb-2">{label}</p>
      {loading ? (
        <Skeleton />
      ) : (
        <p
          className={`font-mono text-2xl font-bold ${
            value !== null ? (valueColor ?? 'text-white') : 'text-[#444]'
          }`}
        >
          {value ?? '—'}
        </p>
      )}
      {!loading && subtext && <p className="text-muted text-xs mt-1.5">{subtext}</p>}
    </div>
  )
}

export default function LiveStatsBar({
  mode,
  totalR,
  winRate,
  avgR,
  drawdown,
  noLiveData,
  loading,
}: {
  mode: Mode
  totalR: number | null
  winRate: number | null
  avgR: number | null
  drawdown: number | null
  noLiveData: boolean
  loading: boolean
}) {
  return (
    <section className="space-y-3">
      {noLiveData && !loading && (
        <div className="flex items-center gap-2.5 px-4 py-3 bg-card border border-line rounded">
          <span className="relative flex h-2 w-2 shrink-0">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-positive opacity-60" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-positive" />
          </span>
          <p className="text-xs font-mono text-muted">
            No live trades recorded yet. System is active and monitoring.
          </p>
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          label="Total R"
          value={
            totalR !== null
              ? `${totalR >= 0 ? '+' : ''}${totalR.toFixed(2)}R`
              : null
          }
          valueColor={totalR !== null ? (totalR >= 0 ? 'text-positive' : 'text-negative') : undefined}
          subtext={mode === 'LIVE' ? 'Live trades' : 'Backtest total'}
          loading={loading}
        />
        <StatCard
          label="Win Rate"
          value={winRate !== null ? `${winRate.toFixed(1)}%` : null}
          valueColor={winRate !== null ? (winRate >= 50 ? 'text-positive' : 'text-negative') : undefined}
          subtext="All trades"
          loading={loading}
        />
        <StatCard
          label="Avg R / Trade"
          value={
            avgR !== null
              ? `${avgR >= 0 ? '+' : ''}${avgR.toFixed(3)}R`
              : null
          }
          valueColor={avgR !== null ? (avgR >= 0 ? 'text-positive' : 'text-negative') : undefined}
          subtext="All trades"
          loading={loading}
        />
        <StatCard
          label={mode === 'LIVE' ? 'Max Drawdown' : 'Drawdown'}
          value={
            drawdown !== null
              ? mode === 'LIVE'
                ? `${drawdown.toFixed(2)}R`
                : `${drawdown.toFixed(1)}%`
              : null
          }
          valueColor={
            drawdown !== null
              ? drawdown > (mode === 'LIVE' ? 3 : 10)
                ? 'text-negative'
                : 'text-white'
              : undefined
          }
          subtext="Current"
          loading={loading}
        />
      </div>
    </section>
  )
}
