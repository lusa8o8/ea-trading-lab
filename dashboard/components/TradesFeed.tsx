import type { Trade } from '@/lib/supabase'

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

export default function TradesFeed({ trades }: { trades: Trade[] }) {
  if (trades.length === 0) {
    return (
      <section>
        <h2 className="text-xs font-mono uppercase tracking-widest text-muted mb-4">
          Recent Trades
        </h2>
        <div className="bg-card border border-line rounded p-8 text-center">
          <span className="text-xs font-mono text-muted">No trades logged yet</span>
        </div>
      </section>
    )
  }

  return (
    <section>
      <h2 className="text-xs font-mono uppercase tracking-widest text-muted mb-4">
        Recent Trades
      </h2>
      <div className="bg-card border border-line rounded overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line">
                {['Date', 'Pair', 'Dir', 'R', 'Result', 'Close Reason', 'Source'].map((h) => (
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
              {trades.map((t, i) => {
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
                    <td className="px-4 py-2.5 text-xs">
                      <span
                        className={`inline-block font-mono px-1.5 py-0.5 rounded text-xs ${
                          t.source === 'LIVE'
                            ? 'bg-positive/10 text-positive border border-positive/20'
                            : 'bg-white/5 text-muted border border-white/10'
                        }`}
                      >
                        {t.source}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}
