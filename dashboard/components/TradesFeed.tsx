import type { Trade, Mode } from '@/lib/supabase'

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: '2-digit',
    })
  } catch {
    return '—'
  }
}

function SkeletonRow() {
  return (
    <tr className="border-b border-line/40">
      {Array.from({ length: 6 }).map((_, i) => (
        <td key={i} className="px-4 py-2.5">
          <div
            className="h-3.5 bg-[#1a1a1a] rounded animate-pulse"
            style={{ width: [64, 52, 36, 36, 36, 72][i] }}
          />
        </td>
      ))}
    </tr>
  )
}

export default function TradesFeed({
  mode,
  trades,
  loading,
}: {
  mode: Mode
  trades: Trade[]
  loading: boolean
}) {
  const isLiveEmpty = mode === 'LIVE' && trades.length === 0 && !loading

  return (
    <section>
      <h2 className="text-xs font-mono uppercase tracking-widest text-muted mb-4">
        Recent Trades
      </h2>
      <div className="bg-card border border-line rounded overflow-hidden">
        {isLiveEmpty ? (
          <div className="px-4 py-10 text-center">
            <p className="text-xs font-mono text-muted">Waiting for first live trade…</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line">
                  {['Date', 'Pair', 'Dir', 'R', 'Result', 'Close Reason'].map((h) => (
                    <th
                      key={h}
                      className="text-left px-4 py-3 text-muted text-xs font-mono uppercase tracking-wider whitespace-nowrap"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading
                  ? Array.from({ length: 8 }).map((_, i) => <SkeletonRow key={i} />)
                  : trades.map((t, i) => {
                      const isWin = t.result === 'WIN'
                      return (
                        <tr
                          key={i}
                          className={`border-b border-line/40 last:border-b-0 hover:bg-white/[0.015] transition-colors ${
                            isWin ? 'border-l-2 border-l-positive' : 'border-l-2 border-l-negative'
                          }`}
                        >
                          <td className="px-4 py-2.5 font-mono text-muted text-xs whitespace-nowrap">
                            {t.exit_time ? formatDate(t.exit_time) : '—'}
                          </td>
                          <td className="px-4 py-2.5 font-mono text-white text-xs font-medium">
                            {t.symbol}
                          </td>
                          <td
                            className={`px-4 py-2.5 font-mono text-xs ${
                              t.direction === 'BUY' ? 'text-positive' : 'text-negative'
                            }`}
                          >
                            {t.direction}
                          </td>
                          <td
                            className={`px-4 py-2.5 font-mono text-xs ${
                              (t.r_multiple ?? 0) >= 0 ? 'text-positive' : 'text-negative'
                            }`}
                          >
                            {(t.r_multiple ?? 0) >= 0 ? '+' : ''}
                            {(t.r_multiple ?? 0).toFixed(2)}R
                          </td>
                          <td
                            className={`px-4 py-2.5 font-mono text-xs font-medium ${
                              isWin ? 'text-positive' : 'text-negative'
                            }`}
                          >
                            {t.result}
                          </td>
                          <td className="px-4 py-2.5 font-mono text-muted text-xs whitespace-nowrap">
                            {t.close_reason ?? '—'}
                          </td>
                        </tr>
                      )
                    })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  )
}
