type PairStats = {
  symbol: string
  timeframe: string
  trades: number
  win_rate: number
  avg_r: number
  total_r: number
}

export default function PairTable({ pairStats }: { pairStats: PairStats[] }) {
  if (pairStats.length === 0) {
    return (
      <section>
        <h2 className="text-xs font-mono uppercase tracking-widest text-muted mb-4">
          Pair Performance
        </h2>
        <div className="bg-card border border-line rounded p-8 text-center">
          <span className="text-xs font-mono text-muted">No trade data yet</span>
        </div>
      </section>
    )
  }

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
                {['Pair', 'Timeframe', 'Trades', 'WR%', 'Avg R', 'Total R'].map((h) => (
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
              {pairStats.map((row, i) => (
                <tr
                  key={i}
                  className="border-b border-line/50 last:border-b-0 hover:bg-white/[0.015] transition-colors"
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
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}
