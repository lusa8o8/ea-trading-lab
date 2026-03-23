import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

export type AccountSnapshot = {
  id?: number
  month: string
  balance: number
  drawdown_pct: number
  monthly_pct: number
  source?: string
}

export type Trade = {
  id?: number
  symbol: string
  timeframe: string
  direction: string
  r_multiple: number
  result: string
  source: string
  exit_time: string
  close_reason: string
  score?: number | null
}

export type BrainObservation = {
  id?: number
  created_at: string
  observation_type?: string
  resolved?: boolean
  message?: string
}

export type Mode = 'LIVE' | 'BACKTEST'
