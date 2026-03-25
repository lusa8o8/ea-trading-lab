"""
EA Trading Lab — Intelligence Agent
CLI agent powered by Claude. Queries Supabase trades table, detects brain triggers,
writes brain_observations, and maintains memory across sessions.

Run: python agent.py
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime, date
import anthropic

# Force UTF-8 output on Windows so emoji in Claude responses don't crash the terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Load credentials
# ---------------------------------------------------------------------------
env_path = Path(__file__).parent / ".env"
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

SUPABASE_URL  = os.environ["SUPABASE_URL"]
SUPABASE_KEY  = os.environ["SUPABASE_SERVICE_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

REST = f"{SUPABASE_URL}/rest/v1"

REST_HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=representation",
}

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
MODEL  = "claude-sonnet-4-20250514"

# ---------------------------------------------------------------------------
# System prompt — full strategy context
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """
You are the EA Trading Lab Intelligence Agent. Your north star metric is R-multiple
(return per unit risk). You analyse backtest and live trade data stored in Supabase,
identify patterns, detect triggers, and write persistent brain observations.

PHILOSOPHY: Boring = effective. Measure first, conclude later. Never guess — discover,
diagnose, report. Only conclude what the data supports.

=== PAIR CONFIGURATIONS (LOCKED) ===

EURJPY H4
- Session: 06:00-12:00 server time (London only, Tue/Wed/Thu)
- Risk: 1.0% flat — scoring inverted, deferred until live sample justifies it
- MAE guard: 85% trigger | 60% tighten
- Trail: TrailB active | 60% activation | 0.5x ATR
- Expected: ~0.77% monthly at 1% risk

NZDUSD H2
- Session: 06:00-17:00 server time (Tue/Wed/Thu)
- Risk: Scoring — A+ 1.5% | Score 1 1.0% | Score 0 0.5%
- Scoring: Session hour 10, 14, or 16 = +1 | Thursday = +1
- MAE guard: 75% trigger | 60% tighten
- Trail: Not applicable — float-then-win character confirmed
- Expected: ~0.76% monthly at flat 1%

USDCAD H2
- Session: 06:00-17:00 server time (Tue/Wed/Thu)
- Risk: Scoring — A+ 1.5% | Score 1 1.0% | Score 0 0.5%
- Scoring: Session hour 14 or 16 = +1 | Tuesday = +1 | Hour 12 always 0.5%
- MAE guard: Not applied — no improvement found
- Trail: Not applicable
- Expected: ~0.18% monthly baseline

AUDUSD H4
- Session: 06:00-17:00 server time (Tue/Wed/Thu)
- Risk: Scoring — A+ 1.5% | Score 1 1.0% | Score 0 0.5%
- Scoring: Session hour 12 = +1 | Wednesday or Thursday = +1
- MAE guard: Not applied — no improvement found
- Trail: Not applicable — float-then-win character confirmed
- Expected: ~0.29% monthly baseline

SYSTEM PROJECTION
- Flat 1% all pairs: ~2.00% monthly
- With scoring: ~2.40-2.60% monthly
- Target: 1-3% monthly — currently achieved at floor

=== SEASONAL FILTERS ===
August — HARD RULE: all pairs 0.5% flat. Institutional summer holidays, thin liquidity.
  - Log every August trade with confluence score to brain_observations
  - Generate August summary at month end
November — MONITOR ONLY: brain watches, logs observations, no automatic risk reduction

=== WITHDRAWAL FRAMEWORK ===
- Quarterly only — never mid-quarter
- Maintain minimum 6% above starting capital at all times
- Withdraw profits above 6% buffer at each quarter end
- Never withdraw during active drawdown (>5% from peak)
- WITHDRAWAL_READY fires at quarter end when balance > buffer threshold

=== CONSISTENCY RULES (Prop Firm) ===
- Single day R must not exceed 40% of monthly total profit
- Brain fires CONSISTENCY_RISK if single day approaches 35% threshold
- Score 0 trades at 0.5% naturally dilute big win day concentration

=== BRAIN TRIGGERS — AUTO-DETECT THESE ===
1. WITHDRAWAL_READY — quarter end + balance > starting_capital × 1.06
2. CONSISTENCY_RISK — single day R > 35% of month-to-date R
3. SEASONAL_WARNING — entering August (hard) or November (soft watch)
4. SCORING_SHIFT — quarterly: compare live A+ performance vs 3-year baseline per pair
5. DRAWDOWN_ALERT — drawdown from peak exceeds 5%
6. STREAK_WARNING — 5+ consecutive losses on any single pair
7. VALIDATION_PENDING — standing reminders that scoring models and seasonal filters are
   unproven on live data; auto-seeded at startup; cleared only when sample thresholds met

=== RULES ===
1. Never guess. Discovery and diagnosis before any conclusion.
2. Signal logic is frozen. Do not suggest modifying entry conditions without data proof.
3. The brain never stores logic in the database. Logic lives here. Data lives in Supabase.
4. One timeframe per pair. One position per pair maximum.
5. All conclusions must cite specific data from the query results.
6. When brain triggers fire, always write a brain_observation with full context.

=== DATABASE SCHEMA ===
Table: trades
  trade_id, symbol, timeframe, direction, open_time, close_time,
  duration_hours, entry_price, sl_price, tp_price, exit_price,
  lot_size, risk_amount, rr_target, r_multiple,
  close_reason, session_hour, day_of_week,
  mfe_pips, mae_pips, mfe_pct_tp, mae_pct_sl,
  ma_value, atr14, atr5, atr_ratio,
  adx14, di_plus, di_minus,
  candle_body_pct, price_ma_distance_pips, prev_candle_range_pct,
  confluence_score, source

Table: account_snapshots
  id, month, balance, peak_balance, monthly_r, monthly_pct, drawdown_pct,
  trades_count, wins, losses, consistency_flag, biggest_day_r,
  withdrawal_safe, withdrawal_amt, source, created_at

Table: brain_observations
  id, observation_date, pair, observation_type, message, data_context, resolved, created_at
  Observation types: WITHDRAWAL_READY, CONSISTENCY_RISK, SEASONAL_WARNING,
                     SCORING_SHIFT, DRAWDOWN_ALERT, STREAK_WARNING, VALIDATION_PENDING

=== SCORING BASELINES (BACKTEST — used for SCORING_SHIFT comparisons) ===
NZDUSD: A+ avg R = 0.95 | Score 1 avg R = 0.45 | Score 0 avg R = -0.14
USDCAD: A+ avg R = 0.45 | Score 1 avg R = 0.06 | Score 0 avg R = -0.17
AUDUSD: A+ avg R = 1.18 | Score 1 avg R = 0.09 | Score 0 avg R = -0.13
SCORING_SHIFT fires when live tier avg R diverges more than 0.3R below baseline.
Insufficient sample (< 30 trades per tier): report count only — no SCORING_SHIFT fired.

=== TOOLS ADDED IN PHASE 7+ ===
- run_quarterly_review(): full quarterly report — trades vs backtest, validation pending
  status, score tier sample sizes, month performance vs expectations.
- check_all_triggers(): now includes SCORING_SHIFT detection per pair.

When you have data from a tool call, analyse it thoroughly before responding.
Always check for brain triggers after any performance analysis.
Be concise and direct. Lead with conclusions, follow with supporting data.
""".strip()

# ---------------------------------------------------------------------------
# Supabase helper
# ---------------------------------------------------------------------------
def supabase_query(table: str, params: dict = None, method: str = "GET",
                   body: dict | list = None, prefer: str = None) -> dict | list:
    headers = dict(REST_HEADERS)
    if prefer:
        headers["Prefer"] = prefer
    url = f"{REST}/{table}"
    if method == "GET":
        r = requests.get(url, headers=headers, params=params)
    elif method == "POST":
        r = requests.post(url, headers=headers, json=body)
    elif method == "PATCH":
        r = requests.patch(url, headers=headers, params=params, json=body)
    r.raise_for_status()
    if r.content:
        return r.json()
    return []

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def get_pair_summary(symbol: str, source: str = None) -> dict:
    """Win rate, avg R, total trades, total R for a pair."""
    params = {"symbol": f"eq.{symbol}", "select": "*"}
    if source:
        params["source"] = f"eq.{source}"
    trades = supabase_query("trades", params)
    if not trades:
        return {"error": f"No trades found for {symbol}"}
    wins   = [t for t in trades if t.get("r_multiple") is not None and t["r_multiple"] > 0]
    losses = [t for t in trades if t.get("r_multiple") is not None and t["r_multiple"] <= 0]
    r_vals = [t["r_multiple"] for t in trades if t.get("r_multiple") is not None]
    return {
        "symbol":        symbol,
        "source":        source or "ALL",
        "total_trades":  len(trades),
        "wins":          len(wins),
        "losses":        len(losses),
        "win_rate_pct":  round(len(wins) / len(trades) * 100, 1) if trades else 0,
        "total_r":       round(sum(r_vals), 2),
        "avg_r":         round(sum(r_vals) / len(r_vals), 3) if r_vals else 0,
        "best_r":        round(max(r_vals), 2) if r_vals else 0,
        "worst_r":       round(min(r_vals), 2) if r_vals else 0,
    }


def get_monthly_breakdown(symbol: str, source: str = None) -> list:
    """R-multiple breakdown by month (derived from open_time)."""
    params = {"symbol": f"eq.{symbol}", "select": "open_time,r_multiple,close_reason"}
    if source:
        params["source"] = f"eq.{source}"
    trades = supabase_query("trades", params)
    if not trades:
        return []
    monthly: dict[str, list] = {}
    for t in trades:
        if not t.get("open_time") or t.get("r_multiple") is None:
            continue
        month = t["open_time"][:7]  # YYYY-MM
        monthly.setdefault(month, []).append(t["r_multiple"])
    result = []
    for month in sorted(monthly):
        vals = monthly[month]
        wins = sum(1 for v in vals if v > 0)
        result.append({
            "month":       month,
            "trades":      len(vals),
            "wins":        wins,
            "win_rate":    round(wins / len(vals) * 100, 1),
            "monthly_r":   round(sum(vals), 2),
            "avg_r":       round(sum(vals) / len(vals), 3),
        })
    return result


def get_confluence_analysis(symbol: str, source: str = None) -> dict:
    """Compare A+ (score ≥2) vs Score 1 vs Score 0 trades."""
    params = {"symbol": f"eq.{symbol}", "select": "confluence_score,r_multiple"}
    if source:
        params["source"] = f"eq.{source}"
    trades = supabase_query("trades", params)
    if not trades:
        return {"error": f"No trades found for {symbol}"}
    buckets: dict[str, list] = {"A+": [], "Score1": [], "Score0": [], "Unknown": []}
    for t in trades:
        score = t.get("confluence_score")
        r     = t.get("r_multiple")
        if r is None:
            continue
        if score is None:
            buckets["Unknown"].append(r)
        elif score >= 2:
            buckets["A+"].append(r)
        elif score == 1:
            buckets["Score1"].append(r)
        else:
            buckets["Score0"].append(r)
    result = {}
    for label, vals in buckets.items():
        if not vals:
            continue
        wins = sum(1 for v in vals if v > 0)
        result[label] = {
            "trades":    len(vals),
            "wins":      wins,
            "win_rate":  round(wins / len(vals) * 100, 1),
            "total_r":   round(sum(vals), 2),
            "avg_r":     round(sum(vals) / len(vals), 3),
        }
    return {"symbol": symbol, "source": source or "ALL", "confluence_breakdown": result}


def get_drawdown_analysis(symbol: str, source: str = None) -> dict:
    """Sequential R drawdown — deepest consecutive loss run."""
    params = {
        "symbol": f"eq.{symbol}",
        "select": "open_time,r_multiple",
        "order":  "open_time.asc",
    }
    if source:
        params["source"] = f"eq.{source}"
    trades = supabase_query("trades", params)
    r_vals = [t["r_multiple"] for t in trades if t.get("r_multiple") is not None]
    if not r_vals:
        return {"error": "No data"}

    # Max consecutive losses and deepest drawdown from running equity curve
    max_consec_losses = 0
    cur_consec = 0
    equity = 0.0
    peak   = 0.0
    max_dd = 0.0
    for r in r_vals:
        equity += r
        peak = max(peak, equity)
        dd   = peak - equity
        max_dd = max(max_dd, dd)
        if r <= 0:
            cur_consec += 1
            max_consec_losses = max(max_consec_losses, cur_consec)
        else:
            cur_consec = 0

    return {
        "symbol":              symbol,
        "source":              source or "ALL",
        "max_consec_losses":   max_consec_losses,
        "max_drawdown_r":      round(max_dd, 2),
        "final_equity_r":      round(equity, 2),
        "streak_warning":      max_consec_losses >= 5,
    }


def get_session_analysis(symbol: str, source: str = None) -> dict:
    """R-multiple breakdown by session_hour and day_of_week."""
    params = {"symbol": f"eq.{symbol}", "select": "session_hour,day_of_week,r_multiple"}
    if source:
        params["source"] = f"eq.{source}"
    trades = supabase_query("trades", params)
    if not trades:
        return {"error": "No data"}

    by_hour: dict = {}
    by_day:  dict = {}
    day_names = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}

    for t in trades:
        r = t.get("r_multiple")
        if r is None:
            continue
        h = t.get("session_hour")
        d = t.get("day_of_week")
        if h is not None:
            by_hour.setdefault(h, []).append(r)
        if d is not None:
            by_day.setdefault(d, []).append(r)

    def summarise(groups):
        out = {}
        for k in sorted(groups):
            vals = groups[k]
            wins = sum(1 for v in vals if v > 0)
            out[k] = {
                "trades":   len(vals),
                "win_rate": round(wins / len(vals) * 100, 1),
                "avg_r":    round(sum(vals) / len(vals), 3),
                "total_r":  round(sum(vals), 2),
            }
        return out

    return {
        "symbol":   symbol,
        "by_hour":  summarise(by_hour),
        "by_day":   {day_names.get(k, k): v for k, v in summarise(by_day).items()},
    }


def get_mae_mfe_analysis(symbol: str, source: str = None) -> dict:
    """MAE/MFE distribution — float-then-win characterisation."""
    params = {
        "symbol": f"eq.{symbol}",
        "select": "mfe_pct_tp,mae_pct_sl,r_multiple,close_reason",
    }
    if source:
        params["source"] = f"eq.{source}"
    trades = supabase_query("trades", params)
    if not trades:
        return {"error": "No data"}

    winners = [t for t in trades if t.get("r_multiple") and t["r_multiple"] > 0]
    deep_float_winners = [
        t for t in winners
        if t.get("mae_pct_sl") is not None and t["mae_pct_sl"] >= 70
    ]
    high_mfe_losers = [
        t for t in trades
        if t.get("r_multiple") and t["r_multiple"] <= 0
        and t.get("mfe_pct_tp") is not None and t["mfe_pct_tp"] >= 80
    ]
    mae_vals = [t["mae_pct_sl"] for t in trades if t.get("mae_pct_sl") is not None]
    mfe_vals = [t["mfe_pct_tp"] for t in trades if t.get("mfe_pct_tp") is not None]

    return {
        "symbol":              symbol,
        "total_trades":        len(trades),
        "winners":             len(winners),
        "deep_float_winners":  len(deep_float_winners),   # Won but MAE ≥70% of SL dist
        "high_mfe_losers":     len(high_mfe_losers),      # MFE ≥80% TP but still lost
        "avg_mae_pct_sl":      round(sum(mae_vals)/len(mae_vals), 1) if mae_vals else None,
        "avg_mfe_pct_tp":      round(sum(mfe_vals)/len(mfe_vals), 1) if mfe_vals else None,
    }


def get_recent_trades(symbol: str = None, limit: int = 20, source: str = None) -> list:
    """Most recent trades, optionally filtered by symbol."""
    params = {
        "select": "trade_id,symbol,timeframe,direction,open_time,r_multiple,close_reason,confluence_score,source",
        "order":  "open_time.desc",
        "limit":  limit,
    }
    if symbol:
        params["symbol"] = f"eq.{symbol}"
    if source:
        params["source"] = f"eq.{source}"
    return supabase_query("trades", params)


def write_brain_observation(
    observation_type: str,
    message: str,
    pair: str = None,
    data_context: dict = None,
) -> dict:
    """Write a brain observation to Supabase."""
    row = {
        "observation_date": date.today().isoformat(),
        "pair":             pair,
        "observation_type": observation_type,
        "message":          message,
        "data_context":     data_context or {},
        "resolved":         False,
    }
    result = supabase_query("brain_observations", method="POST", body=row,
                            prefer="return=representation")
    if isinstance(result, list) and result:
        return {"written": True, "id": result[0].get("id"), "type": observation_type}
    return {"written": True, "type": observation_type}


def get_brain_observations(observation_type: str = None, resolved: bool = False,
                            pair: str = None, limit: int = 20) -> list:
    """Read brain observations, newest first."""
    params = {
        "select": "id,observation_date,pair,observation_type,message,data_context,resolved",
        "order":  "created_at.desc",
        "limit":  limit,
    }
    if observation_type:
        params["observation_type"] = f"eq.{observation_type}"
    if pair:
        params["pair"] = f"eq.{pair}"
    params["resolved"] = f"eq.{'true' if resolved else 'false'}"
    return supabase_query("brain_observations", params)


def get_account_snapshots(limit: int = 12) -> list:
    """Most recent account snapshots."""
    params = {
        "select": "*",
        "order":  "month.desc",
        "limit":  limit,
    }
    return supabase_query("account_snapshots", params)


def resolve_brain_observation(observation_id: str) -> dict:
    """Mark a brain observation as resolved."""
    supabase_query(
        "brain_observations",
        params={"id": f"eq.{observation_id}"},
        method="PATCH",
        body={"resolved": True},
        prefer="return=minimal",
    )
    return {"resolved": True, "id": observation_id}


# ---------------------------------------------------------------------------
# Validation seed observations — standing reminders about unproven models
# ---------------------------------------------------------------------------
VALIDATION_SEEDS = [
    {
        "pair": "NZDUSD",
        "message": (
            "Scoring model (Hr 10/14/16 + Thursday) never backtested. "
            "Minimum 30 trades per score tier required before conclusions."
        ),
    },
    {
        "pair": "USDCAD",
        "message": (
            "Scoring model (Hr 14/16 + Tuesday) never backtested. "
            "Minimum 30 trades per score tier required before conclusions."
        ),
    },
    {
        "pair": "AUDUSD",
        "message": (
            "Scoring model (Hr 12 + Wed/Thu) never backtested. "
            "Minimum 30 trades per score tier required before conclusions."
        ),
    },
    {
        "pair": "EURJPY",
        "message": (
            "Trail B + MAE guard live performance unproven. "
            "Minimum 50 live trades required before conclusions."
        ),
    },
    {
        "pair": "ALL",
        "message": (
            "August 0.5% seasonal filter unproven on live data. "
            "Requires 3 live Augusts to validate."
        ),
    },
    {
        "pair": "ALL",
        "message": (
            "November hostile pattern based on 3 backtest years only. "
            "Requires 3 live Novembers to validate."
        ),
    },
]


def seed_validation_observations() -> dict:
    """
    Insert VALIDATION_PENDING observations for unproven models/filters.
    Checks all existing rows (resolved or not) to avoid duplicates.
    Safe to call every startup — idempotent.
    """
    existing_rows = supabase_query("brain_observations", {
        "observation_type": "eq.VALIDATION_PENDING",
        "select": "message",
        "limit": 100,
    })
    existing_messages = {r["message"] for r in existing_rows}

    inserted = []
    for seed in VALIDATION_SEEDS:
        if seed["message"] not in existing_messages:
            write_brain_observation(
                observation_type="VALIDATION_PENDING",
                message=seed["message"],
                pair=seed["pair"],
            )
            inserted.append(seed["pair"])

    return {
        "seeded": len(inserted),
        "pairs_inserted": inserted,
        "already_existed": len(VALIDATION_SEEDS) - len(inserted),
    }


def _derive_score_tier(session_hour, day_of_week, symbol: str) -> int:
    """
    Derive score tier (0/1/2) from session_hour and day_of_week
    using the locked scoring model for each pair.
    Returns -1 if inputs are missing.
    """
    if session_hour is None or day_of_week is None:
        return -1

    h = int(session_hour)
    d = int(day_of_week)  # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri

    if symbol == "NZDUSD":
        hour_hit = h in (10, 14, 16)
        day_hit  = d == 3  # Thursday
    elif symbol == "USDCAD":
        if h == 12:
            return 0  # Hour 12 always Score 0 regardless of day
        hour_hit = h in (14, 16)
        day_hit  = d == 1  # Tuesday
    elif symbol == "AUDUSD":
        hour_hit = h == 12
        day_hit  = d in (2, 3)  # Wed or Thu
    else:
        return -1

    return int(hour_hit) + int(day_hit)


# Backtest avg R baselines per pair per tier — used for SCORING_SHIFT
_SCORING_BASELINES = {
    "NZDUSD": {2: 0.95,  1: 0.45,  0: -0.14},
    "USDCAD": {2: 0.45,  1: 0.06,  0: -0.17},
    "AUDUSD": {2: 1.18,  1: 0.09,  0: -0.13},
}
_SCORING_SHIFT_THRESHOLD = 0.30   # fire if live avg R is this far below baseline
_SCORING_MIN_SAMPLE      = 30     # minimum trades per tier before comparison is valid


def check_all_triggers() -> dict:
    """
    Run a full trigger sweep across all pairs.
    Checks: SEASONAL_WARNING, STREAK_WARNING, SCORING_SHIFT.
    Returns a summary of any triggers that fired.
    """
    pairs = ["EURJPY", "NZDUSD", "USDCAD", "AUDUSD"]
    fired = []
    today = date.today()
    month = today.month

    # ── SEASONAL_WARNING ────────────────────────────────────────────
    if month == 8:
        fired.append({
            "trigger": "SEASONAL_WARNING",
            "pair":    "ALL",
            "detail":  "August — HARD RULE. All pairs drop to 0.5% flat. Log all trades.",
        })
    elif month == 11:
        fired.append({
            "trigger": "SEASONAL_WARNING",
            "pair":    "ALL",
            "detail":  "November — MONITOR ONLY. Watch performance, no automatic reduction.",
        })

    # ── STREAK_WARNING per pair ──────────────────────────────────────
    for sym in pairs:
        dd = get_drawdown_analysis(sym, source="LIVE")
        if dd.get("streak_warning"):
            fired.append({
                "trigger": "STREAK_WARNING",
                "pair":    sym,
                "detail":  f"{dd['max_consec_losses']} consecutive losses on {sym} (LIVE).",
            })

    # ── SCORING_SHIFT — NZDUSD, USDCAD, AUDUSD ──────────────────────
    scoring_pairs = ["NZDUSD", "USDCAD", "AUDUSD"]
    for sym in scoring_pairs:
        trades = supabase_query("trades", {
            "symbol":  f"eq.{sym}",
            "source":  "eq.LIVE",
            "select":  "session_hour,day_of_week,r_multiple",
        })
        if not trades:
            continue

        # Group by derived score tier
        tiers: dict[int, list] = {0: [], 1: [], 2: []}
        skipped = 0
        for t in trades:
            r = t.get("r_multiple")
            if r is None:
                continue
            tier = _derive_score_tier(t.get("session_hour"), t.get("day_of_week"), sym)
            if tier == -1:
                skipped += 1
                continue
            tiers[tier].append(r)

        baselines = _SCORING_BASELINES[sym]
        tier_summaries = {}
        shift_detected = False

        for tier_key in (2, 1, 0):
            r_vals    = tiers[tier_key]
            n         = len(r_vals)
            baseline  = baselines[tier_key]
            label     = {2: "A+", 1: "Score1", 0: "Score0"}[tier_key]

            if n == 0:
                tier_summaries[label] = {
                    "trades": 0, "avg_r": None, "baseline": baseline,
                    "status": f"INSUFFICIENT SAMPLE (0/{_SCORING_MIN_SAMPLE}) — monitoring only",
                }
                continue

            avg_r = round(sum(r_vals) / n, 3)

            if n < _SCORING_MIN_SAMPLE:
                tier_summaries[label] = {
                    "trades": n, "avg_r": avg_r, "baseline": baseline,
                    "status": (
                        f"INSUFFICIENT SAMPLE ({n}/{_SCORING_MIN_SAMPLE}) — monitoring only"
                    ),
                }
            else:
                divergence = avg_r - baseline
                if divergence < -_SCORING_SHIFT_THRESHOLD:
                    shift_detected = True
                    status = (
                        f"SHIFT DETECTED — live {avg_r:+.3f}R vs baseline {baseline:+.3f}R "
                        f"(divergence {divergence:+.3f}R)"
                    )
                else:
                    status = f"OK — live {avg_r:+.3f}R vs baseline {baseline:+.3f}R"

                tier_summaries[label] = {
                    "trades": n, "avg_r": avg_r, "baseline": baseline,
                    "status": status,
                }

        if shift_detected:
            fired.append({
                "trigger": "SCORING_SHIFT",
                "pair":    sym,
                "detail":  f"Live scoring divergence detected on {sym}.",
                "tiers":   tier_summaries,
            })
        else:
            # Still report scoring status even when no shift
            fired.append({
                "trigger": "SCORING_STATUS",
                "pair":    sym,
                "detail":  f"No scoring shift on {sym}.",
                "tiers":   tier_summaries,
            })

    return {
        "checked_at":     today.isoformat(),
        "triggers_fired": sum(1 for f in fired if f["trigger"] != "SCORING_STATUS"),
        "details":        fired,
    }


def run_quarterly_review() -> dict:
    """
    Full quarterly performance review.
    - Current quarter dates
    - Live trades for the quarter vs backtest quarterly avg
    - VALIDATION_PENDING observation status with current live trade counts
    - Score tier sample sizes and 30-trade threshold progress
    - Monthly performance vs backtest expectations
    """
    today  = date.today()
    year   = today.year
    q      = (today.month - 1) // 3 + 1
    q_start_month = (q - 1) * 3 + 1
    q_start = date(year, q_start_month, 1).isoformat()
    # Quarter end is last day of the 3rd month of the quarter
    q_end_month = q_start_month + 2
    q_end_day   = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][q_end_month - 1]
    if q_end_month == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
        q_end_day = 29
    q_end = date(year, q_end_month, q_end_day).isoformat()

    # ── Live trades for the quarter ──────────────────────────────────
    quarter_trades = supabase_query("trades", {
        "source":    "eq.LIVE",
        "open_time": f"gte.{q_start}",
        "select":    "symbol,r_multiple,open_time,session_hour,day_of_week",
        "order":     "open_time.asc",
    })

    # Total quarter R per pair
    pair_q_totals: dict[str, list] = {}
    for t in quarter_trades:
        sym = t.get("symbol", "UNKNOWN")
        r   = t.get("r_multiple")
        if r is not None:
            pair_q_totals.setdefault(sym, []).append(r)

    # Backtest monthly expectations (R at flat 1% risk)
    backtest_monthly_r = {
        "EURJPY": 0.77,
        "NZDUSD": 0.76,
        "USDCAD": 0.18,
        "AUDUSD": 0.29,
    }
    pair_quarterly_summary = {}
    for sym, r_list in pair_q_totals.items():
        actual_q_r   = round(sum(r_list), 2)
        expected_q_r = round(backtest_monthly_r.get(sym, 0) * 3, 2)  # 3 months
        pair_quarterly_summary[sym] = {
            "trades":          len(r_list),
            "actual_r":        actual_q_r,
            "expected_q_r":    expected_q_r,
            "vs_expectation":  round(actual_q_r - expected_q_r, 2),
        }

    # ── Monthly breakdown for the quarter ───────────────────────────
    monthly_actual: dict[str, dict] = {}
    for t in quarter_trades:
        ot = t.get("open_time")
        r  = t.get("r_multiple")
        if not ot or r is None:
            continue
        month_key = ot[:7]
        monthly_actual.setdefault(month_key, {"trades": 0, "total_r": 0.0})
        monthly_actual[month_key]["trades"]  += 1
        monthly_actual[month_key]["total_r"] += r
    for mk in monthly_actual:
        monthly_actual[mk]["total_r"] = round(monthly_actual[mk]["total_r"], 2)

    # ── VALIDATION_PENDING status ────────────────────────────────────
    pending_obs = supabase_query("brain_observations", {
        "observation_type": "eq.VALIDATION_PENDING",
        "resolved":         "eq.false",
        "select":           "id,pair,message",
        "limit":            20,
    })

    # Score tier sample sizes (all LIVE trades, not just this quarter)
    scoring_pairs  = ["NZDUSD", "USDCAD", "AUDUSD"]
    tier_samples   = {}
    for sym in scoring_pairs:
        all_live = supabase_query("trades", {
            "symbol": f"eq.{sym}",
            "source": "eq.LIVE",
            "select": "session_hour,day_of_week,r_multiple",
        })
        counts = {2: 0, 1: 0, 0: 0}
        for t in all_live:
            if t.get("r_multiple") is None:
                continue
            tier = _derive_score_tier(t.get("session_hour"), t.get("day_of_week"), sym)
            if tier in counts:
                counts[tier] += 1
        tier_samples[sym] = {
            "A+":     {"count": counts[2], "threshold": 30, "met": counts[2] >= 30},
            "Score1": {"count": counts[1], "threshold": 30, "met": counts[1] >= 30},
            "Score0": {"count": counts[0], "threshold": 30, "met": counts[0] >= 30},
        }

    # EURJPY live trade count vs 50-trade threshold
    eurjpy_live_count = len(supabase_query("trades", {
        "symbol": "eq.EURJPY",
        "source": "eq.LIVE",
        "select": "trade_id",
    }))

    return {
        "quarter":              f"Q{q} {year}",
        "quarter_range":        f"{q_start} → {q_end}",
        "today":                today.isoformat(),
        "quarter_trades_total": len(quarter_trades),
        "pair_quarterly_vs_expectation": pair_quarterly_summary,
        "monthly_breakdown":    monthly_actual,
        "validation_pending_open": len(pending_obs),
        "validation_pending_obs":  [
            {"pair": o["pair"], "message": o["message"]} for o in pending_obs
        ],
        "score_tier_samples":   tier_samples,
        "eurjpy_live_trades":   eurjpy_live_count,
        "eurjpy_threshold":     50,
        "eurjpy_threshold_met": eurjpy_live_count >= 50,
    }


# ---------------------------------------------------------------------------
# Tool definitions for Claude
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name":        "get_pair_summary",
        "description": "Get win rate, avg R, total R, and trade count for a symbol.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "e.g. EURJPY"},
                "source": {"type": "string", "description": "BACKTEST or LIVE (optional)"},
            },
            "required": ["symbol"],
        },
    },
    {
        "name":        "get_monthly_breakdown",
        "description": "R-multiple breakdown by calendar month for a symbol.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "source": {"type": "string"},
            },
            "required": ["symbol"],
        },
    },
    {
        "name":        "get_confluence_analysis",
        "description": "Compare A+ (score≥2) vs Score1 vs Score0 trade performance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "source": {"type": "string"},
            },
            "required": ["symbol"],
        },
    },
    {
        "name":        "get_drawdown_analysis",
        "description": "Max consecutive losses and deepest R drawdown for a symbol.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "source": {"type": "string"},
            },
            "required": ["symbol"],
        },
    },
    {
        "name":        "get_session_analysis",
        "description": "R breakdown by session hour and day of week.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "source": {"type": "string"},
            },
            "required": ["symbol"],
        },
    },
    {
        "name":        "get_mae_mfe_analysis",
        "description": "MAE/MFE distribution — float-then-win characterisation, deep floaters, high MFE losers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "source": {"type": "string"},
            },
            "required": ["symbol"],
        },
    },
    {
        "name":        "get_recent_trades",
        "description": "Fetch the N most recent trades, optionally filtered by symbol.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "limit":  {"type": "integer", "default": 20},
                "source": {"type": "string"},
            },
            "required": [],
        },
    },
    {
        "name":        "write_brain_observation",
        "description": "Persist a brain observation to Supabase. Use when a trigger fires or a notable pattern is found.",
        "input_schema": {
            "type": "object",
            "properties": {
                "observation_type": {
                    "type": "string",
                    "enum": ["WITHDRAWAL_READY", "CONSISTENCY_RISK", "SEASONAL_WARNING",
                             "SCORING_SHIFT", "DRAWDOWN_ALERT", "STREAK_WARNING",
                             "VALIDATION_PENDING"],
                },
                "message":     {"type": "string"},
                "pair":        {"type": "string"},
                "data_context": {"type": "object"},
            },
            "required": ["observation_type", "message"],
        },
    },
    {
        "name":        "get_brain_observations",
        "description": "Read existing brain observations (unresolved by default).",
        "input_schema": {
            "type": "object",
            "properties": {
                "observation_type": {"type": "string"},
                "pair":             {"type": "string"},
                "resolved":         {"type": "boolean", "default": False},
                "limit":            {"type": "integer", "default": 20},
            },
            "required": [],
        },
    },
    {
        "name":        "get_account_snapshots",
        "description": "Read monthly account snapshots (balance, drawdown, withdrawal status).",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 12},
            },
            "required": [],
        },
    },
    {
        "name":        "resolve_brain_observation",
        "description": "Mark a brain observation as resolved.",
        "input_schema": {
            "type": "object",
            "properties": {
                "observation_id": {"type": "string"},
            },
            "required": ["observation_id"],
        },
    },
    {
        "name":        "check_all_triggers",
        "description": (
            "Run a full trigger sweep — seasonal warnings, streak warnings, and "
            "SCORING_SHIFT detection — across all pairs. Includes per-tier live vs "
            "backtest comparison for NZDUSD, USDCAD, AUDUSD."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name":        "run_quarterly_review",
        "description": (
            "Full quarterly performance report: live R vs backtest expectation per pair, "
            "monthly breakdown, all VALIDATION_PENDING observation statuses with current "
            "live trade counts, score tier sample sizes vs 30-trade threshold, "
            "EURJPY live count vs 50-trade threshold."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

TOOL_FN_MAP = {
    "get_pair_summary":        get_pair_summary,
    "get_monthly_breakdown":   get_monthly_breakdown,
    "get_confluence_analysis": get_confluence_analysis,
    "get_drawdown_analysis":   get_drawdown_analysis,
    "get_session_analysis":    get_session_analysis,
    "get_mae_mfe_analysis":    get_mae_mfe_analysis,
    "get_recent_trades":       get_recent_trades,
    "write_brain_observation": write_brain_observation,
    "get_brain_observations":  get_brain_observations,
    "get_account_snapshots":   get_account_snapshots,
    "resolve_brain_observation": resolve_brain_observation,
    "check_all_triggers":      check_all_triggers,
    "run_quarterly_review":    run_quarterly_review,
}

# ---------------------------------------------------------------------------
# Session startup — load brain observations for memory continuity
# ---------------------------------------------------------------------------
def load_session_memory() -> str:
    """Load unresolved brain observations for context injection at session start."""
    try:
        obs = get_brain_observations(limit=10)
        if not obs:
            return ""
        lines = ["=== UNRESOLVED BRAIN OBSERVATIONS (session memory) ==="]
        for o in obs:
            lines.append(
                f"[{o['observation_date']}] {o['observation_type']} | "
                f"{o.get('pair','ALL')} — {o['message']}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"(Could not load brain observations: {e})"

# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------
def run_agent(user_message: str, conversation_history: list) -> str:
    conversation_history.append({"role": "user", "content": user_message})

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=conversation_history,
        )

        # Collect all text and tool_use blocks
        tool_uses   = []
        text_blocks = []
        for block in response.content:
            if block.type == "tool_use":
                tool_uses.append(block)
            elif block.type == "text":
                text_blocks.append(block.text)

        # Append assistant message to history
        conversation_history.append({"role": "assistant", "content": response.content})

        # If no tool calls, we're done
        if response.stop_reason == "end_turn" or not tool_uses:
            return "\n".join(text_blocks)

        # Execute all tool calls and collect results
        tool_results = []
        for tool_use in tool_uses:
            fn   = TOOL_FN_MAP.get(tool_use.name)
            args = tool_use.input or {}
            print(f"  [tool] {tool_use.name}({', '.join(f'{k}={v!r}' for k,v in args.items())})")
            try:
                result = fn(**args)
            except Exception as e:
                result = {"error": str(e)}
            tool_results.append({
                "type":        "tool_result",
                "tool_use_id": tool_use.id,
                "content":     json.dumps(result),
            })

        conversation_history.append({"role": "user", "content": tool_results})


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("EA Trading Lab — Intelligence Agent")
    print(f"Model: {MODEL}")
    print("=" * 60)

    # Load memory at session start
    memory_context = load_session_memory()
    if memory_context:
        print("\n" + memory_context)
    else:
        print("\n(No unresolved brain observations.)")

    # Seed VALIDATION_PENDING observations for unproven models/filters
    try:
        seed_result = seed_validation_observations()
        if seed_result["seeded"] > 0:
            print(f"\n[startup] Seeded {seed_result['seeded']} VALIDATION_PENDING "
                  f"observation(s): {', '.join(seed_result['pairs_inserted'])}")
        else:
            print(f"\n[startup] All {seed_result['already_existed']} VALIDATION_PENDING "
                  f"observations already exist — nothing to seed.")
    except Exception as e:
        print(f"\n[startup] Could not seed validation observations: {e}")

    print("\nType your question. Type 'exit' or 'quit' to end the session.")
    print("-" * 60)

    conversation_history: list = []

    # Inject memory as first user message if there are observations
    if memory_context:
        conversation_history.append({
            "role":    "user",
            "content": memory_context + "\n\nMemory loaded. Ready for your questions.",
        })
        conversation_history.append({
            "role":    "assistant",
            "content": "Memory loaded. I have the unresolved observations in context. What would you like to know?",
        })

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession ended.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Session ended.")
            break

        try:
            answer = run_agent(user_input, conversation_history)
            print(f"\nAgent: {answer}")
        except requests.exceptions.HTTPError as e:
            print(f"\n[Supabase error] {e}")
        except anthropic.APIError as e:
            print(f"\n[Anthropic API error] {e}")
        except Exception as e:
            print(f"\n[Error] {e}")
            raise


if __name__ == "__main__":
    main()
