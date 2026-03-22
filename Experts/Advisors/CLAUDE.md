# EA Trading Lab — Project Rules

## North Star
R-multiple (return per unit risk). Everything exists to serve this metric or it gets deleted.

## Philosophy
Boring = effective. Measure first, conclude later. Never guess — discover, diagnose, implement. If a feature does not serve the north star, it does not exist.

## Stack
- MQL5 EAs — signal execution and CSV logging (Advisors folder)
- Supabase (ea-trading-lab) — single source of truth, all data lives here
- Intelligence agent — queries Supabase, applies logic, returns conclusions, logs observations
- GitHub: https://github.com/lusa8o8/ea-trading-lab.git

## Current Phase
Phase 6 complete. Live EAs post trades directly to Supabase via WebRequest.

## Rules
1. Never guess. Discovery and diagnosis before any fix or new feature.
2. Signal logic is frozen. Do not modify entry conditions without data proof.
3. source field is always BACKTEST in backtest EA versions, LIVE in live versions.
4. One timeframe per pair. One position per pair maximum.
5. All EA files save directly to the Advisors folder.
6. The brain never stores logic in the database. Logic lives in the system prompt. Data lives in Supabase.

## Pair Configurations (LOCKED)

### EURJPY H4
- Broker: Native MT5
- Session: 06:00-12:00 server time (London only, Tue/Wed/Thu)
- Risk: 1.0% flat — scoring inverted on this pair, deferred until live sample justifies it
- MAE guard: UseMAEGuard=true | 85% trigger | 60% tighten
- Trail: UseTrailB=true | 60% activation | 0.5x ATR
- Breakeven: N/A
- EA file (backtest): Tri_Pair_v3_TrailB.mq5 (AllSession variant)
- EA file (live): Tri_Pair_v3_TrailB_Live.mq5
- Expected: ~0.77% monthly at 1% risk

### NZDUSD H2
- Broker: Native MT5
- Session: 06:00-17:00 server time (Tue/Wed/Thu)
- Risk: Scoring active — A+ 1.5% | Score 1 1.0% | Score 0 0.5%
- Scoring: Session hour 10, 14, or 16 = +1 | Thursday = +1
- MAE guard: UseMAEGuard=true | 75% trigger | 60% tighten
- Trail: Not applicable — float-then-win character confirmed by data
- Breakeven: Not applicable — 41% winner float risk, 2 reversals in 3 years at 90%+ MFE
- EA file (backtest): Tri_Pair_v3_TrailB_Sessioned.mq5
- EA file (live): Tri_Pair_v3_TrailB_Sessioned_Live.mq5
- Expected: ~0.76% monthly at flat 1% (higher with scoring)

### USDCAD H2
- Broker: Native MT5
- Session: 06:00-17:00 server time (Tue/Wed/Thu)
- Risk: Scoring active — A+ 1.5% | Score 1 1.0% | Score 0 0.5%
- Scoring: Session hour 14 or 16 = +1 | Tuesday = +1 | Hour 12 always 0.5% regardless of day
- MAE guard: Not applied — no meaningful improvement found at any threshold
- Trail: Not applicable
- EA file (backtest): Tri_Pair_v3_TrailB_Sessioned.mq5
- EA file (live): Tri_Pair_v3_TrailB_Sessioned_Live.mq5
- Expected: ~0.18% monthly baseline (higher with scoring)

### AUDUSD H4
- Broker: Native MT5
- Session: 06:00-17:00 server time (Tue/Wed/Thu)
- Risk: Scoring active — A+ 1.5% | Score 1 1.0% | Score 0 0.5%
- Scoring: Session hour 12 = +1 | Wednesday or Thursday = +1
- MAE guard: Not applied — no meaningful improvement found at any threshold
- Trail: Not applicable — float-then-win character confirmed by data
- Breakeven: Not applicable — 16 deep floaters, only 3 reversals at 1.5R+ in 3 years
- EA file (backtest): Tri_Pair_v3_TrailB_Sessioned.mq5
- EA file (live): Tri_Pair_v3_TrailB_Sessioned_Live.mq5
- Expected: ~0.29% monthly baseline (higher with scoring)

## System Monthly Projection
- Flat 1% risk all pairs: ~2.00% monthly
- With scoring active: ~2.40-2.60% monthly (estimated)
- Baseline (no management): ~1.27% monthly
- Target: 1-3% monthly — currently achieved at floor with management alone

## Seasonal Filters
### August — HARD RULE (50+ years of external research confirms structural hostility)
- Mechanism: institutional summer holidays, thin liquidity, choppy MA conditions
- Action: all pairs drop to 0.5% flat regardless of confluence score
- Agent does NOT override this for any macro catalyst
- Agent DOES log every August trade with its confluence score to brain_observations
- Agent generates August summary at month end to build evidence base over time

### November — MONITOR ONLY (insufficient proof from 3-year dataset)
- Our data shows 3/4 pairs negative but November 2024 was US election aftermath — one-off event
- Action: brain watches November performance, logs observations, no automatic risk reduction
- Revisit after 3 live Novembers of data

## Withdrawal Framework
- Interval: quarterly only — never mid-quarter
- Buffer: maintain minimum 6% above starting capital at all times
- Amount: withdraw profits above the 6% buffer at each quarter end
- Never withdraw during active drawdown (>5% from peak)
- Brain trigger: WITHDRAWAL_READY fires at quarter end when balance > buffer threshold
- Brain calculates exact safe withdrawal amount respecting prop firm consistency rules

## Consistency Rules (Prop Firm)
- Single day R must not exceed 40% of monthly total profit
- Score 0 trades at 0.5% naturally dilute big win day concentration — no additional action needed
- Brain monitors daily concentration and fires CONSISTENCY_RISK if single day approaches 35% threshold

## Database Schema (Supabase — ea-trading-lab)

### Table: trades (existing)
All 36 fields per trade — the raw data layer and primary source of truth.

### Table: account_snapshots (build in Phase 4)
Month-end account state: balance, peak, monthly R, monthly %, drawdown, trade counts,
consistency flag, biggest day R, withdrawal_safe boolean, withdrawal_amount, source.

### Table: brain_observations (build in Phase 4)
Agent memory across sessions: date, pair, observation_type, message, data_context (jsonb), resolved.
Observation types: WITHDRAWAL_READY, CONSISTENCY_RISK, SEASONAL_WARNING,
SCORING_SHIFT, DRAWDOWN_ALERT, STREAK_WARNING.

## Brain Triggers (Phase 4)
1. WITHDRAWAL_READY — quarter end + balance > starting_capital x 1.06
2. CONSISTENCY_RISK — single day R > 35% of month-to-date R
3. SEASONAL_WARNING — entering August (hard) or November (soft watch)
4. SCORING_SHIFT — quarterly: compare live A+ performance vs 3-year baseline per pair
5. DRAWDOWN_ALERT — drawdown from peak exceeds 5%
6. STREAK_WARNING — 5+ consecutive losses on any single pair

## Phase 2 Items (Post-Production, Earn Through Data)
- MAE guard tighten level (currently 60%) — test post 6 months live
- Trailing on NZDUSD/AUDUSD/USDCAD — revisit if live data changes float-then-win finding
- Time-based SL tightening on EURJPY — 8h threshold candidate, needs live data
- Scoring activation on EURJPY — deferred until live A+ sample reaches 50+ trades
- Scale-in logic — Phase 2 minimum, needs live confluence data
- November seasonal filter — revisit after 3 live Novembers
- Self-improving agent loop (MT5 CLI backtest automation) — Level 4 autonomy, earn through Level 3 proof
