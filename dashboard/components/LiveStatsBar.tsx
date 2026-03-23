function StatCard({
  label,
  value,
  valueColor,
  subtext,
}: {
  label: string
  value: string
  valueColor?: string
  subtext?: string
}) {
  return (
    <div className="bg-card border border-line rounded p-4">
      <p className="text-muted text-xs font-mono uppercase tracking-widest mb-2">{label}</p>
      <p className={`font-mono text-2xl font-bold ${valueColor ?? 'text-white'}`}>{value}</p>
      {subtext && <p className="text-muted text-xs mt-1.5">{subtext}</p>}
    </div>
  )
}

export default function LiveStatsBar({
  totalR,
  winRate,
  avgR,
  drawdown,
  isLive,
}: {
  totalR: number
  winRate: number
  avgR: number
  drawdown: number
  isLive: boolean
}) {
  return (
    <section>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatCard
          label="Total R"
          value={`${totalR >= 0 ? '+' : ''}${totalR.toFixed(2)}R`}
          valueColor={totalR >= 0 ? 'text-positive' : 'text-negative'}
          subtext={isLive ? 'Live trades only' : 'Backtest total'}
        />
        <StatCard
          label="Win Rate"
          value={`${winRate.toFixed(1)}%`}
          valueColor={winRate >= 50 ? 'text-positive' : 'text-negative'}
          subtext="All trades"
        />
        <StatCard
          label="Avg R / Trade"
          value={`${avgR >= 0 ? '+' : ''}${avgR.toFixed(3)}R`}
          valueColor={avgR >= 0 ? 'text-positive' : 'text-negative'}
          subtext="All trades"
        />
        <StatCard
          label="Drawdown"
          value={`${drawdown.toFixed(1)}%`}
          valueColor={drawdown > 10 ? 'text-negative' : 'text-white'}
          subtext="Current"
        />
      </div>
    </section>
  )
}
