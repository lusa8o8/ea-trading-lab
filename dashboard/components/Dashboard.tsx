'use client'

import { useState, useEffect, useCallback } from 'react'
import { supabase } from '@/lib/supabase'
import type { Trade, AccountSnapshot, BrainObservation, Mode } from '@/lib/supabase'
import Header from './Header'
import ModeToggle from './ModeToggle'
import LiveStatsBar from './LiveStatsBar'
import EquityCurve from './EquityCurve'
import MonthlyBars from './MonthlyBars'
import PairTable from './PairTable'
import TradesFeed from './TradesFeed'
import ScoringImpact from './ScoringImpact'
import ContextSection from './ContextSection'
import Footer from './Footer'

export default function Dashboard() {
  const [mode, setMode] = useState<Mode>('LIVE')
  const [trades, setTrades] = useState<Trade[]>([])
  const [snapshots, setSnapshots] = useState<AccountSnapshot[]>([])
  const [latestObs, setLatestObs] = useState<BrainObservation | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    try {
      const [tradesRes, snapshotsRes, obsRes, latestTradeRes] = await Promise.all([
        supabase
          .from('trades')
          .select('*')
          .eq('source', mode)
          .order('exit_time', { ascending: false }),
        mode === 'BACKTEST'
          ? supabase
              .from('account_snapshots')
              .select('*')
              .order('month', { ascending: true })
          : Promise.resolve({ data: [] as AccountSnapshot[], error: null }),
        supabase
          .from('brain_observations')
          .select('*')
          .eq('resolved', false)
          .order('created_at', { ascending: false })
          .limit(1),
        supabase
          .from('trades')
          .select('exit_time')
          .order('exit_time', { ascending: false })
          .limit(1),
      ])

      setTrades((tradesRes.data ?? []) as Trade[])
      setSnapshots((snapshotsRes.data ?? []) as AccountSnapshot[])
      setLatestObs(((obsRes.data ?? [])[0] ?? null) as BrainObservation | null)

      const latest = (latestTradeRes.data ?? [])[0]?.exit_time
      if (latest) setLastUpdated(latest)
    } finally {
      setLoading(false)
    }
  }, [mode])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 60_000)
    return () => clearInterval(interval)
  }, [fetchData])

  // ── Derived stats ──────────────────────────────────────────────────

  const noLiveData = mode === 'LIVE' && trades.length === 0

  const totalR = trades.length > 0
    ? trades.reduce((s, t) => s + (t.r_multiple ?? 0), 0)
    : null

  const wins = trades.filter((t) => t.result === 'WIN').length
  const winRate = trades.length > 0 ? (wins / trades.length) * 100 : null
  const avgR = trades.length > 0
    ? trades.reduce((s, t) => s + (t.r_multiple ?? 0), 0) / trades.length
    : null

  // Drawdown
  let drawdown: number | null = null
  if (mode === 'BACKTEST' && snapshots.length > 0) {
    drawdown = snapshots[snapshots.length - 1]?.drawdown_pct ?? null
  } else if (mode === 'LIVE' && trades.length > 0) {
    const sorted = [...trades].sort(
      (a, b) => new Date(a.exit_time).getTime() - new Date(b.exit_time).getTime()
    )
    let cum = 0, peak = 0, maxDD = 0
    for (const t of sorted) {
      cum += t.r_multiple ?? 0
      if (cum > peak) peak = cum
      const dd = peak - cum
      if (dd > maxDD) maxDD = dd
    }
    drawdown = maxDD
  }

  // ── Equity curve data ──────────────────────────────────────────────

  const equityData: { x: string; y: number }[] =
    mode === 'BACKTEST'
      ? snapshots.map((s) => ({ x: s.month, y: s.balance }))
      : (() => {
          const sorted = [...trades].sort(
            (a, b) => new Date(a.exit_time).getTime() - new Date(b.exit_time).getTime()
          )
          let cum = 0
          return sorted.map((t) => {
            cum += t.r_multiple ?? 0
            return { x: t.exit_time.slice(0, 10), y: parseFloat(cum.toFixed(2)) }
          })
        })()

  // ── Monthly bars data ──────────────────────────────────────────────

  const monthlyData: { month: string; value: number }[] =
    mode === 'BACKTEST'
      ? snapshots.map((s) => ({ month: s.month, value: s.monthly_pct }))
      : (() => {
          const map = new Map<string, number>()
          for (const t of trades) {
            const month = t.exit_time?.slice(0, 7)
            if (!month) continue
            map.set(month, (map.get(month) ?? 0) + (t.r_multiple ?? 0))
          }
          return Array.from(map.entries())
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([month, value]) => ({ month, value: parseFloat(value.toFixed(2)) }))
        })()

  // ── Pair stats ─────────────────────────────────────────────────────

  const pairMap = new Map<
    string,
    { symbol: string; timeframe: string; wins: number; total: number; rSum: number }
  >()
  for (const t of trades) {
    const key = `${t.symbol}|${t.timeframe}`
    const p = pairMap.get(key) ?? {
      symbol: t.symbol,
      timeframe: t.timeframe,
      wins: 0,
      total: 0,
      rSum: 0,
    }
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

  // ── Scoring stats (LIVE only) ──────────────────────────────────────

  const flatAvgR = avgR

  const SCORE_TIERS = [
    { key: 2, label: 'A+ (1.5%)' },
    { key: 1, label: 'Score 1' },
    { key: 0, label: 'Score 0' },
  ]
  const scoringRows = SCORE_TIERS.map(({ key, label }) => {
    const tierTrades = trades.filter((t) => t.score === key)
    const count = tierTrades.length
    const tierAvgR =
      count > 0
        ? tierTrades.reduce((s, t) => s + (t.r_multiple ?? 0), 0) / count
        : null
    const vsFlat =
      tierAvgR !== null && flatAvgR !== null ? tierAvgR - flatAvgR : null
    return { label, count, avgR: tierAvgR, vsFlat }
  })

  return (
    <main className="min-h-screen bg-bg">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-10 fade-in">
        <Header latestObs={latestObs} />

        <ModeToggle mode={mode} onChange={setMode} />

        <LiveStatsBar
          mode={mode}
          totalR={totalR}
          winRate={winRate}
          avgR={avgR}
          drawdown={drawdown}
          noLiveData={noLiveData}
          loading={loading}
        />

        <EquityCurve mode={mode} data={equityData} loading={loading} />

        <MonthlyBars mode={mode} data={monthlyData} loading={loading} />

        <PairTable mode={mode} pairStats={pairStats} loading={loading} />

        <TradesFeed mode={mode} trades={trades.slice(0, 20)} loading={loading} />

        {mode === 'LIVE' && (
          <ScoringImpact rows={scoringRows} loading={loading} />
        )}

        <ContextSection />

        <Footer lastUpdated={lastUpdated} />
      </div>
    </main>
  )
}
