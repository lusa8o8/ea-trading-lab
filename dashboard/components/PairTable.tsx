import type { Mode } from '@/lib/supabase'

type PairStats = {
  symbol: string
  timeframe: string
  trades: number
  win_rate: number
  avg_r: number
  total_r: number
}

function SkeletonRow() {
  return (
    <tr className="border-b border-line/50">
      {Array.from({ length: 6 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 bg-[#1a1a1a] rounded animate-pulse" style={{ width: i === 0 ? 64 : 40 }} />
        </td>
      ))}
    </tr>
  )
}

function EmptyRow({ index }: { index: number }) {
  const placeholders = ['EURUSD', 'GBPUSD', 'EURJPY', 'USDJPY']
  return (
    <tr className="border-b border-line/40 last:border-b-0">
      <td className="px-4 py-3 font-mono text-[#333] text-sm">{placeholders[index] ?? '—'}</td>
      {Array.from({ length: 5 }).map((_, i) => (
        <td key={i} className="px-4 py-3 font-mono text-[#333] text-sm">—</td>
      ))}
    </tr>
  )
}

export default function PairTable({
  mode,
  pairStats,
  loading,
}: {
  mode: Mode
  pairStats: PairStats[]
  loading: boolean
}) {
  const isLiveEmpty = mode === 'LIVE' && pairStats.length === 0 && !loading

  return (
    <section>
      <h2 className="text-xs font-mono uppercase tracking-widest text-muted mb-4">
        Pair Performance
      </h2>
      <div className="bg-card border border-line rounded overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line">
                {['Pair', 'TF', 'Trades', 'WR%', 'Avg R', 'Total R'].map((h) => (
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
              {loading ? (
                Array.from({ length: 4 }).map((_, i) => <SkeletonRow key={i} />)
              ) : isLiveEmpty ? (
                Array.from({ length: 4 }).map((_, i) => <EmptyRow key={i} index={i} />)
              ) : (
                pairStats.map((row, i) => (
                  <tr
                    key={i}
                    className="border-b border-line/40 last:border-b-0 hover:bg-white/[0.015] transition-colors"
                  >
                    <td className="px-4 py-3 font-mono text-white font-semibold text-sm">
                      {row.symbol}
                    </td>
                    <td className="px-4 py-3 font-mono text-muted text-xs">{row.timeframe}</td>
                    <td className="px-4 py-3 font-mono text-muted text-sm">{row.trades}</td>
                    <td className="px-4 py-3 font-mono text-sm">
                      <span className={row.win_rate >= 50 ? 'text-positive' : 'text-negative'}>
                        {row.win_rate.toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-sm">
                      <span className={row.avg_r >= 0 ? 'text-positive' : 'text-negative'}>
                        {row.avg_r >= 0 ? '+' : ''}
                        {row.avg_r.toFixed(3)}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-sm">
                      <span className={row.total_r >= 0 ? 'text-positive' : 'text-negative'}>
                        {row.total_r >= 0 ? '+' : ''}
                        {row.total_r.toFixed(2)}R
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}
