"""
EA Trading Lab — Backfill account_snapshots
Simulates month-by-month compound growth from $5000 at 1% flat risk.
Inserts one row per month into account_snapshots (source = BACKTEST).
"""

import os
import json
import requests
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------
env_path = Path(__file__).parent / ".env"
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

URL = os.environ["SUPABASE_URL"]
KEY = os.environ["SUPABASE_SERVICE_KEY"]
REST = f"{URL}/rest/v1"

HEADERS = {
    "apikey":        KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=representation",
}

# ---------------------------------------------------------------------------
# Fetch all trades ordered by open_time
# ---------------------------------------------------------------------------
print("Fetching trades from Supabase...")

trades = []
offset = 0
while True:
    r = requests.get(
        f"{REST}/trades",
        headers=HEADERS,
        params={
            "select": "trade_id,symbol,entry_time,r_multiple",
            "order":  "entry_time.asc",
            "limit":  1000,
            "offset": offset,
        },
    )
    r.raise_for_status()
    batch = r.json()
    if not batch:
        break
    trades.extend(batch)
    if len(batch) < 1000:
        break
    offset += 1000

# Drop any rows without r_multiple or open_time
trades = [t for t in trades if t.get("r_multiple") is not None and t.get("entry_time")]
print(f"  {len(trades)} trades loaded (with r_multiple).\n")

if not trades:
    print("No trades found. Exiting.")
    raise SystemExit(1)

# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
STARTING_CAPITAL = 5000.0
RISK_PCT         = 0.01          # 1% flat
BUFFER_MULT      = 1.06          # 6% above starting capital

balance  = STARTING_CAPITAL
peak     = STARTING_CAPITAL

# Group trades by month, preserving open_time and keeping them sorted
monthly_trades: dict[str, list] = defaultdict(list)
for t in trades:
    month = t["entry_time"][:7]   # YYYY-MM
    monthly_trades[month].append(t)

months = sorted(monthly_trades.keys())

snapshots      = []
summary_rows   = []

for month in months:
    month_start_balance = balance
    bucket = monthly_trades[month]

    # Group by trade date for daily R calcs
    daily_r: dict[str, float] = defaultdict(float)
    wins = 0
    losses = 0
    month_r_total = 0.0

    for trade in bucket:
        r      = trade["r_multiple"]
        day    = trade["entry_time"][:10]   # YYYY-MM-DD
        dollar = balance * RISK_PCT * r
        balance += dollar
        peak = max(peak, balance)

        month_r_total    += r
        daily_r[day]     += r
        if r > 0:
            wins += 1
        else:
            losses += 1

    month_end_balance = balance
    drawdown_pct = (peak - balance) / peak * 100 if peak > 0 else 0.0
    monthly_pct  = (month_end_balance - month_start_balance) / month_start_balance * 100

    biggest_day_r = max(daily_r.values()) if daily_r else 0.0

    # Consistency flag: any single day R > 40% of monthly total
    # Only meaningful when monthly total is positive
    consistency_flag = False
    if month_r_total > 0:
        for day_r in daily_r.values():
            if day_r > 0.40 * month_r_total:
                consistency_flag = True
                break

    withdrawal_safe = balance > STARTING_CAPITAL * BUFFER_MULT
    withdrawal_amt  = (balance - STARTING_CAPITAL * BUFFER_MULT) if withdrawal_safe else 0.0

    row = {
        "month":            month,
        "balance":          round(balance, 2),
        "peak_balance":     round(peak, 2),
        "monthly_r":        round(month_r_total, 3),
        "monthly_pct":      round(monthly_pct, 3),
        "drawdown_pct":     round(drawdown_pct, 3),
        "trades_count":     len(bucket),
        "wins":             wins,
        "losses":           losses,
        "consistency_flag": consistency_flag,
        "biggest_day_r":    round(biggest_day_r, 3),
        "withdrawal_safe":  withdrawal_safe,
        "withdrawal_amt":   round(withdrawal_amt, 2),
        "source":           "BACKTEST",
    }
    snapshots.append(row)
    summary_rows.append((
        month,
        len(bucket),
        wins,
        losses,
        round(month_r_total, 2),
        round(monthly_pct, 2),
        round(balance, 2),
        round(drawdown_pct, 2),
        "YES" if withdrawal_safe else "no",
        "!" if consistency_flag else "",
    ))

# ---------------------------------------------------------------------------
# Insert into account_snapshots
# ---------------------------------------------------------------------------
print("Inserting snapshots into account_snapshots...")

# Check for existing months and skip duplicates
existing_resp = requests.get(
    f"{REST}/account_snapshots",
    headers=HEADERS,
    params={"select": "month", "source": "eq.BACKTEST", "limit": 1000},
)
existing_resp.raise_for_status()
existing_months = {r["month"] for r in existing_resp.json()}

new_snapshots = [s for s in snapshots if s["month"] not in existing_months]
skipped       = len(snapshots) - len(new_snapshots)

if new_snapshots:
    resp = requests.post(
        f"{REST}/account_snapshots",
        headers=HEADERS,
        json=new_snapshots,
    )
    if resp.status_code not in (200, 201):
        print(f"  [ERROR] {resp.status_code} — {resp.text[:400]}")
        raise SystemExit(1)
    print(f"  Inserted: {len(new_snapshots)} months | Skipped (duplicates): {skipped}\n")
else:
    print(f"  All {skipped} months already exist — nothing to insert.\n")

# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------
header = f"{'Month':<9} {'Tr':>3} {'W':>3} {'L':>3} {'R':>6} {'%':>7} {'Balance':>10} {'DD%':>6} {'WDraw':>6} {'Con':>4}"
divider = "-" * len(header)
print(divider)
print(header)
print(divider)
for row in summary_rows:
    month, tr, w, l, r, pct, bal, dd, wd, con = row
    print(f"{month:<9} {tr:>3} {w:>3} {l:>3} {r:>6.2f} {pct:>7.2f}% ${bal:>9,.2f} {dd:>5.1f}% {wd:>6} {con:>4}")
print(divider)
print(f"\nFinal balance: ${balance:,.2f}  |  Peak: ${peak:,.2f}  |  Total months: {len(months)}")
print(f"Starting capital: ${STARTING_CAPITAL:,.2f}  |  Gain: ${balance - STARTING_CAPITAL:,.2f} ({(balance/STARTING_CAPITAL - 1)*100:.1f}%)")
