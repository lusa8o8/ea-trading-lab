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
import type { AccountSnapshot } from '@/lib/supabase'

export default function MonthlyBars({ snapshots }: { snapshots: AccountSnapshot[] }) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  const data = snapshots.map((s) => ({
    month: s.month,
    pct: s.monthly_pct,
  }))

  return (
    <section>
      <h2 className="text-xs font-mono uppercase tracking-widest text-muted mb-4">
        Monthly Performance
      </h2>
      <div className="bg-card border border-line rounded p-4">
        {!mounted ? (
          <div className="h-[220px] flex items-center justify-center">
            <span className="text-xs font-mono text-muted">Loading chart…</span>
          </div>
        ) : data.length === 0 ? (
          <div className="h-[220px] flex items-center justify-center">
            <span className="text-xs font-mono text-muted">No data yet</span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f1f1f" vertical={false} />
              <XAxis
                dataKey="month"
                tick={{ fill: '#666666', fontSize: 10, fontFamily: 'monospace' }}
                tickLine={false}
                axisLine={{ stroke: '#1f1f1f' }}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fill: '#666666', fontSize: 10, fontFamily: 'monospace' }}
                tickLine={false}
                axisLine={{ stroke: '#1f1f1f' }}
                tickFormatter={(v: number) => `${v}%`}
                width={40}
              />
              <ReferenceLine y={0} stroke="#1f1f1f" />
              <Tooltip
                contentStyle={{
                  background: '#111111',
                  border: '1px solid #1f1f1f',
                  borderRadius: 4,
                  padding: '8px 12px',
                }}
                labelStyle={{ color: '#666666', fontFamily: 'monospace', fontSize: 11 }}
                itemStyle={{ fontFamily: 'monospace', fontSize: 12 }}
                formatter={(v: number) => [
                  `${v >= 0 ? '+' : ''}${v.toFixed(2)}%`,
                  'Monthly return',
                ]}
              />
              <Bar dataKey="pct" radius={[2, 2, 0, 0]} maxBarSize={40}>
                {data.map((entry, i) => (
                  <Cell
                    key={`cell-${i}`}
                    fill={entry.pct >= 0 ? '#00ff88' : '#ff4444'}
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
