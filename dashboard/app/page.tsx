import { supabase, type AccountSnapshot, type Trade } from '@/lib/supabase'
import Header from '@/components/Header'
import LiveStatsBar from '@/components/LiveStatsBar'
import EquityCurve from '@/components/EquityCurve'
import MonthlyBars from '@/components/MonthlyBars'
import PairTable from '@/components/PairTable'
import TradesFeed from '@/components/TradesFeed'
import ContextSection from '@/components/ContextSection'
import Footer from '@/components/Footer'

export const dynamic = 'force-dynamic'

async function getPageData() {
  const [
    { data: snapshots },
    { data: trades },
    { data: latestObservation },
  ] = await Promise.all([
    supabase
      .from('account_snapshots')
      .select('*')
      .order('month', { ascending: true }),
    supabase
      .from('trades')
      .select('*')
      .order('exit_time', { ascending: false }),
    supabase
      .from('brain_observations')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(1),
  ])

  return {
    snapshots: (snapshots ?? []) as AccountSnapshot[],
    trades: (trades ?? []) as Trade[],
    latestObservation: latestObservation?.[0] ?? null,
  }
}

export default async function Page() {
  const { snapshots, trades, latestObservation } = await getPageData()

  // Live vs backtest split
  const liveTrades = trades.filter((t) => t.source === 'LIVE')
  const sourceTrades = liveTrades.length > 0 ? liveTrades : trades

  // Live stats
  const totalR = sourceTrades.reduce((sum, t) => sum + (t.r_multiple ?? 0), 0)
  const wins = trades.filter((t) => t.result === 'WIN').length
  const winRate = trades.length > 0 ? (wins / trades.length) * 100 : 0
  const avgR = trades.length > 0
    ? trades.reduce((s, t) => s + (t.r_multiple ?? 0), 0) / trades.length
    : 0
  const latestSnapshot = snapshots[snapshots.length - 1]
  const drawdown = latestSnapshot?.drawdown_pct ?? 0

  // Pair performance (top 4 by total R)
  const pairMap = new Map<string, {
    symbol: string; timeframe: string; wins: number; total: number; rSum: number
  }>()
  for (const t of trades) {
    const key = `${t.symbol}|${t.timeframe}`
    const p = pairMap.get(key) ?? { symbol: t.symbol, timeframe: t.timeframe, wins: 0, total: 0, rSum: 0 }
    pairMap.set(key, {
      ...p,
      wins: p.wins + (t.result === 'WIN' ? 1 : 0),
      total: p.total + 1,
      rSum: p.rSum + (t.r_multiple ?? 0),
    })
  }
  const pairStats = Array.from(pairMap.values())
    .sort((a, b) => b.rSum - a.rSum)
    .slice(0, 4)
    .map((p) => ({
      symbol: p.symbol,
      timeframe: p.timeframe,
      trades: p.total,
      win_rate: p.total > 0 ? (p.wins / p.total) * 100 : 0,
      avg_r: p.total > 0 ? p.rSum / p.total : 0,
      total_r: p.rSum,
    }))

  // BACKTEST→LIVE transition month
  const firstLiveSnapshot = snapshots.find((s) => s.source === 'LIVE')
  const firstLiveTrade = [...trades].reverse().find((t) => t.source === 'LIVE')
  const transitionMonth =
    firstLiveSnapshot?.month ??
    firstLiveTrade?.exit_time?.slice(0, 7) ??
    null

  // Status badge
  const obs = latestObservation as { alert_active?: boolean; status?: string } | null
  const hasAlert = obs?.alert_active === true || obs?.status === 'alert'

  const lastUpdated = new Date().toISOString()

  return (
    <main className="min-h-screen bg-bg">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-10 fade-in">
        <Header hasAlert={hasAlert} />

        <LiveStatsBar
          totalR={totalR}
          winRate={winRate}
          avgR={avgR}
          drawdown={drawdown}
          isLive={liveTrades.length > 0}
        />

        <EquityCurve snapshots={snapshots} transitionMonth={transitionMonth} />

        <MonthlyBars snapshots={snapshots} />

        <PairTable pairStats={pairStats} />

        <TradesFeed trades={trades.slice(0, 20)} />

        <ContextSection />

        <Footer lastUpdated={lastUpdated} />
      </div>
    </main>
  )
}
