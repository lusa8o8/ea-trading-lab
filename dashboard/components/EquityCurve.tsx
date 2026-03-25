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
import type { Mode } from '@/lib/supabase'

type Point = { x: string; y: number }

function ChartSkeleton() {
  return (
    <div className="h-[280px] bg-[#0d0d0d] rounded animate-pulse flex items-center justify-center">
      <span className="text-xs font-mono text-[#333]">Loading…</span>
    </div>
  )
}

export default function EquityCurve({
  mode,
  data,
  loading,
}: {
  mode: Mode
  data: Point[]
  loading: boolean
}) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  const isLive = mode === 'LIVE'
  const title = isLive ? 'Equity Curve — Cumulative R' : 'Equity Curve — Balance'

  return (
    <section>
      <h2 className="text-xs font-mono uppercase tracking-widest text-muted mb-4">{title}</h2>
      <div className="bg-card border border-line rounded p-4">
        {loading || !mounted ? (
          <ChartSkeleton />
        ) : data.length === 0 ? (
          <div className="h-[280px] flex items-center justify-center">
            <p className="text-xs font-mono text-muted text-center">
              {isLive
                ? 'Waiting for first live trade to start the curve.'
                : 'No snapshot data available.'}
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data ?? []} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a1a1a" />
              <XAxis
                dataKey="x"
                tick={{ fill: '#555', fontSize: 10, fontFamily: 'monospace' }}
                tickLine={false}
                axisLine={{ stroke: '#1f1f1f' }}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fill: '#555', fontSize: 10, fontFamily: 'monospace' }}
                tickLine={false}
                axisLine={{ stroke: '#1f1f1f' }}
                width={isLive ? 44 : 52}
                tickFormatter={(v: number) =>
                  isLive
                    ? `${v >= 0 ? '' : ''}${v.toFixed(1)}R`
                    : v >= 1000
                    ? `$${(v / 1000).toFixed(0)}k`
                    : `$${v}`
                }
              />
              {isLive && (
                <ReferenceLine
                  y={0}
                  stroke="#2a2a2a"
                  strokeDasharray="4 4"
                />
              )}
              <Tooltip
                contentStyle={{
                  background: '#111',
                  border: '1px solid #1f1f1f',
                  borderRadius: 4,
                  padding: '8px 12px',
                }}
                labelStyle={{ color: '#555', fontFamily: 'monospace', fontSize: 11 }}
                itemStyle={{ color: '#00ff88', fontFamily: 'monospace', fontSize: 12 }}
                formatter={(v: number) =>
                  isLive
                    ? [`${v >= 0 ? '+' : ''}${v.toFixed(2)}R`, 'Cumulative R']
                    : [`$${v.toLocaleString()}`, 'Balance']
                }
              />
              <Line
                type="monotone"
                dataKey="y"
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
