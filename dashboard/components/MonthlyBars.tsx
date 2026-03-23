'use client'

import { useState, useEffect } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts'
import type { Mode } from '@/lib/supabase'

type MonthPoint = { month: string; value: number }

function ChartSkeleton() {
  return (
    <div className="h-[220px] bg-[#0d0d0d] rounded animate-pulse flex items-center justify-center">
      <span className="text-xs font-mono text-[#333]">Loading…</span>
    </div>
  )
}

export default function MonthlyBars({
  mode,
  data,
  loading,
}: {
  mode: Mode
  data: MonthPoint[]
  loading: boolean
}) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  const isLive = mode === 'LIVE'

  return (
    <section>
      <h2 className="text-xs font-mono uppercase tracking-widest text-muted mb-4">
        Monthly Performance
      </h2>
      <div className="bg-card border border-line rounded p-4">
        {loading || !mounted ? (
          <ChartSkeleton />
        ) : data.length === 0 ? (
          <div className="h-[220px] flex items-center justify-center">
            <p className="text-xs font-mono text-muted">
              {isLive ? 'No monthly data yet.' : 'No monthly data available.'}
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" vertical={false} />
              <XAxis
                dataKey="month"
                tick={{ fill: '#555', fontSize: 10, fontFamily: 'monospace' }}
                tickLine={false}
                axisLine={{ stroke: '#1f1f1f' }}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fill: '#555', fontSize: 10, fontFamily: 'monospace' }}
                tickLine={false}
                axisLine={{ stroke: '#1f1f1f' }}
                tickFormatter={(v: number) => (isLive ? `${v}R` : `${v}%`)}
                width={40}
              />
              <ReferenceLine y={0} stroke="#2a2a2a" />
              <Tooltip
                contentStyle={{
                  background: '#111',
                  border: '1px solid #1f1f1f',
                  borderRadius: 4,
                  padding: '8px 12px',
                }}
                labelStyle={{ color: '#555', fontFamily: 'monospace', fontSize: 11 }}
                itemStyle={{ fontFamily: 'monospace', fontSize: 12 }}
                formatter={(v: number) =>
                  isLive
                    ? [`${v >= 0 ? '+' : ''}${v.toFixed(2)}R`, 'Monthly R']
                    : [`${v >= 0 ? '+' : ''}${v.toFixed(2)}%`, 'Monthly return']
                }
              />
              <Bar dataKey="value" radius={[2, 2, 0, 0]} maxBarSize={40}>
                {data.map((entry, i) => (
                  <Cell
                    key={`cell-${i}`}
                    fill={entry.value >= 0 ? '#00ff88' : '#ff4444'}
                    fillOpacity={0.8}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  )
}
