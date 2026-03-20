# EA Trading Lab — Project Rules

## What This Is
Mechanical forex EA rebuild with intelligence layer. MQL5 strategy + Supabase data pipeline + confluence analysis agent.

## North Star
Average R-multiple per trade. Everything exists to serve this metric or it gets deleted.

## Philosophy
Boring = effective. If a feature does not serve the north star, it does not exist. Scope creep is deleted, not deprioritised.

## Stack
- MQL5 — strategy execution and CSV trade logging
- Supabase (ea-trading-lab) — trade log database, edge functions
- MT5 Advisors folder — C:\Users\Lusa\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD88BF550E51FF075\MQL5\Experts\Advisors

## Rules
1. Never guess. Discovery and diagnosis before any fix or new feature. Find the cause before touching code.
2. No trailing stop, no breakeven, no partial exit until MFE/MAE data justifies it.
3. Signal logic is frozen. Do not modify entry conditions until backtest data says otherwise.
4. Every MQL5 file gets saved directly to the Advisors folder above.
5. source field is always hardcoded to BACKTEST in the backtest EA version.
6. OnTradeTransaction stays for live trading. OnTick fallback handles close detection in backtesting.

## Current Phase
Phase 1 — Data collection. EA logs all 36 fields to CSV on every trade close. No intelligence layer yet.
