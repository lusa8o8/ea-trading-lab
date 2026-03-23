'use client'

import { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import type { AccountSnapshot } from '@/lib/supabase'

export default function EquityCurve({
  snapshots,
  transitionMonth,
}: {
  snapshots: AccountSnapshot[]
  transitionMonth: string | null
}) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  const data = snapshots.map((s) => ({
    month: s.month,
    balance: s.balance,
  }))

  return (
    <section>
      <h2 className="text-xs font-mono uppercase tracking-widest text-muted mb-4">
        Equity Curve
      </h2>
      <div className="bg-card border border-line rounded p-4">
        {!mounted ? (
          <div className="h-[280px] flex items-center justify-center">
            <span className="text-xs font-mono text-muted">Loading chart…</span>
          </div>
        ) : data.length === 0 ? (
          <div className="h-[280px] flex items-center justify-center">
            <span className="text-xs font-mono text-muted">No data yet</span>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f1f1f" />
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
                tickFormatter={(v: number) =>
                  v >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${v}`
                }
                width={52}
              />
              <Tooltip
                contentStyle={{
                  background: '#111111',
                  border: '1px solid #1f1f1f',
                  borderRadius: 4,
                  padding: '8px 12px',
                }}
                labelStyle={{ color: '#666666', fontFamily: 'monospace', fontSize: 11 }}
                itemStyle={{ color: '#00ff88', fontFamily: 'monospace', fontSize: 12 }}
                formatter={(v: number) => [`$${v.toLocaleString()}`, 'Balance']}
              />
              {transitionMonth && (
                <ReferenceLine
                  x={transitionMonth}
                  stroke="#444444"
                  strokeDasharray="4 4"
                  label={{
                    value: 'LIVE ▸',
                    position: 'insideTopRight',
                    fill: '#666666',
                    fontSize: 10,
                    fontFamily: 'monospace',
                    dy: -6,
                  }}
                />
              )}
              <Line
                type="monotone"
                dataKey="balance"
                stroke="#00ff88"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: '#00ff88', strokeWidth: 0 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  )
}
