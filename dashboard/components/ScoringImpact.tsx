type ScoringRow = {
  label: string
  count: number
  avgR: number | null
  vsFlat: number | null
}

function SkeletonCell({ width = 40 }: { width?: number }) {
  return (
    <td className="px-4 py-3">
      <div className="h-4 bg-[#1a1a1a] rounded animate-pulse" style={{ width }} />
    </td>
  )
}

export default function ScoringImpact({
  rows,
  loading,
}: {
  rows: ScoringRow[]
  loading: boolean
}) {
  return (
    <section>
      <h2 className="text-xs font-mono uppercase tracking-widest text-muted mb-1">
        Scoring Model — Live Performance
      </h2>
      <p className="text-xs font-mono text-[#444] mb-4">
        Populates as live trades accumulate.
      </p>

      <div className="bg-card border border-line rounded overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line">
                {['Score Tier', 'Trades', 'Avg R', 'vs Flat 1%'].map((h) => (
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
                ? rows.map((_, i) => (
                    <tr key={i} className="border-b border-line/40 last:border-b-0">
                      <SkeletonCell width={80} />
                      <SkeletonCell width={32} />
                      <SkeletonCell width={48} />
                      <SkeletonCell width={56} />
                    </tr>
                  ))
                : rows.map((row, i) => (
                    <tr
                      key={i}
                      className="border-b border-line/40 last:border-b-0"
                    >
                      <td className="px-4 py-3 font-mono text-white text-sm font-medium">
                        {row.label}
                      </td>
                      <td className="px-4 py-3 font-mono text-muted text-sm">
                        {row.count > 0 ? row.count : '—'}
                      </td>
                      <td className="px-4 py-3 font-mono text-sm">
                        {row.avgR !== null ? (
                          <span className={row.avgR >= 0 ? 'text-positive' : 'text-negative'}>
                            {row.avgR >= 0 ? '+' : ''}
                            {row.avgR.toFixed(3)}R
                          </span>
                        ) : (
                          <span className="text-[#444]">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 font-mono text-sm">
                        {row.vsFlat !== null ? (
                          <span className={row.vsFlat >= 0 ? 'text-positive' : 'text-negative'}>
                            {row.vsFlat >= 0 ? '+' : ''}
                            {row.vsFlat.toFixed(3)}R
                          </span>
                        ) : (
                          <span className="text-[#444]">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>

        <div className="px-4 py-3 border-t border-line">
          <p className="text-xs font-mono text-muted leading-relaxed">
            Flat 1% risk crushes during losing streaks. Scoring reduces size on low-confidence
            setups automatically.
          </p>
        </div>
      </div>
    </section>
  )
}
