"""
ea-trading-lab — Supabase setup + CSV import
- Creates account_snapshots and brain_observations tables via Management API
- Imports four backtest CSV files into the trades table via PostgREST
- Skips duplicate rows (trade_id + symbol + timeframe)
"""

import os
import csv
import sys
import json
import requests
from pathlib import Path

# ---------------------------------------------------------------------------
# Load credentials from .env
# ---------------------------------------------------------------------------
env_path = Path(__file__).parent / ".env"
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

URL  = os.environ["SUPABASE_URL"]                  # https://jzkjsocburpoaxtrkuix.supabase.co
KEY  = os.environ["SUPABASE_SERVICE_KEY"]          # service_role JWT
REF  = URL.split("//")[1].split(".")[0]            # jzkjsocburpoaxtrkuix

REST   = f"{URL}/rest/v1"
MGMT   = f"https://api.supabase.com/v1/projects/{REF}/database/query"

REST_HEADERS = {
    "apikey":        KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=minimal",
}
MGMT_HEADERS = {
    "Authorization": f"Bearer {KEY}",
    "Content-Type":  "application/json",
}

# ---------------------------------------------------------------------------
# Step 1 — Create tables via Management API
# ---------------------------------------------------------------------------
print("=" * 60)
print("STEP 1 — Creating tables")
print("=" * 60)

DDL_ACCOUNT_SNAPSHOTS = """
CREATE TABLE IF NOT EXISTS account_snapshots (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  month            text,
  balance          numeric,
  peak_balance     numeric,
  monthly_r        numeric,
  monthly_pct      numeric,
  drawdown_pct     numeric,
  trades_count     integer,
  wins             integer,
  losses           integer,
  consistency_flag boolean,
  biggest_day_r    numeric,
  withdrawal_safe  boolean,
  withdrawal_amt   numeric,
  source           text,
  created_at       timestamptz DEFAULT now()
);
"""

DDL_BRAIN_OBSERVATIONS = """
CREATE TABLE IF NOT EXISTS brain_observations (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  observation_date date,
  pair             text,
  observation_type text,
  message          text,
  data_context     jsonb,
  resolved         boolean     DEFAULT false,
  created_at       timestamptz DEFAULT now()
);
"""

for table_name, ddl in [
    ("account_snapshots",  DDL_ACCOUNT_SNAPSHOTS),
    ("brain_observations", DDL_BRAIN_OBSERVATIONS),
]:
    resp = requests.post(MGMT, headers=MGMT_HEADERS, json={"query": ddl})
    if resp.status_code in (200, 201):
        print(f"  [OK] {table_name} created (or already exists)")
    else:
        print(f"  [FAIL] {table_name}: {resp.status_code} — {resp.text[:200]}")
        print("  NOTE: Run the DDL manually in Supabase SQL editor if this fails.")

# ---------------------------------------------------------------------------
# Step 2 — Verify tables exist by listing all tables
# ---------------------------------------------------------------------------
print()
print("=" * 60)
print("STEP 2 — Listing tables in public schema")
print("=" * 60)

list_resp = requests.post(
    MGMT,
    headers=MGMT_HEADERS,
    json={"query": "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;"},
)
if list_resp.status_code == 200:
    tables = [r["tablename"] for r in list_resp.json()]
    for t in tables:
        print(f"  • {t}")
else:
    print(f"  Could not list tables: {list_resp.status_code} — {list_resp.text[:200]}")

# ---------------------------------------------------------------------------
# Step 3 — Import CSV files
# ---------------------------------------------------------------------------
BASE = Path(r"C:\Users\Lusa\AppData\Roaming\MetaQuotes\Terminal\Common\Files")

FILES = [
    BASE / "Native data"              / "trade_log_EURJPY_H4 combined_B_MAE.csv",
    BASE / "trail b sessioned nzdusd" / "trade_log_NZDUSD_H2 trailb sessioned  mae at 75%.csv",
    BASE / "Native data"              / "trade_log_USDCAD_H2 trailb sessioned All things off.csv",
    BASE / "trail b sessioned audusd" / "trade_log_AUDUSD_H4 trailb all off.csv",
]

INT_COLS = {"trade_id", "session_hour", "day_of_week"}
FLOAT_COLS = {
    "duration_hours", "entry_price", "sl_price", "tp_price", "exit_price",
    "lot_size", "risk_amount", "rr_target", "r_multiple",
    "mfe_pips", "mae_pips", "mfe_pct_tp", "mae_pct_sl",
    "ma_value", "atr14", "atr5", "atr_ratio",
    "adx14", "di_plus", "di_minus",
    "candle_body_pct", "price_ma_distance_pips", "prev_candle_range_pct",
}

def coerce(row):
    out = {}
    for k, v in row.items():
        v = v.strip() if isinstance(v, str) else v
        if v == "":
            out[k] = None
        elif k in INT_COLS:
            out[k] = int(v)
        elif k in FLOAT_COLS:
            out[k] = float(v)
        else:
            out[k] = v
    return out

BATCH_SIZE = 200

print()
print("=" * 60)
print("STEP 3 — Importing CSV files")
print("=" * 60)

total_imported = 0
total_skipped  = 0

for csv_path in FILES:
    if not csv_path.exists():
        print(f"\n[SKIP] Not found: {csv_path}")
        continue

    print(f"\n  File: {csv_path.name}")

    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))

    if not rows:
        print("    Empty — skipped.")
        continue

    symbol    = rows[0]["symbol"]
    timeframe = rows[0]["timeframe"]

    # Fetch existing trade_ids for this symbol+timeframe
    # Use pagination to get all (PostgREST returns max 1000 by default)
    existing_ids = set()
    offset = 0
    while True:
        r = requests.get(
            f"{REST}/trades",
            headers={**REST_HEADERS, "Prefer": "count=none"},
            params={
                "select":    "trade_id",
                "symbol":    f"eq.{symbol}",
                "timeframe": f"eq.{timeframe}",
                "limit":     1000,
                "offset":    offset,
            },
        )
        batch = r.json()
        if not batch:
            break
        existing_ids.update(b["trade_id"] for b in batch)
        if len(batch) < 1000:
            break
        offset += 1000

    new_rows   = [coerce(r) for r in rows if int(r["trade_id"]) not in existing_ids]
    skip_count = len(rows) - len(new_rows)

    inserted = 0
    for i in range(0, len(new_rows), BATCH_SIZE):
        batch = new_rows[i : i + BATCH_SIZE]
        resp  = requests.post(
            f"{REST}/trades",
            headers=REST_HEADERS,
            data=json.dumps(batch),
        )
        if resp.status_code not in (200, 201):
            print(f"    [ERROR] batch {i//BATCH_SIZE + 1}: {resp.status_code} — {resp.text[:300]}")
            break
        inserted += len(batch)

    print(f"    Imported: {inserted}  |  Skipped (duplicates): {skip_count}")
    total_imported += inserted
    total_skipped  += skip_count

# ---------------------------------------------------------------------------
# Step 4 — Final row counts
# ---------------------------------------------------------------------------
print()
print("=" * 60)
print("STEP 4 — Row counts")
print("=" * 60)

for table in ["trades", "account_snapshots", "brain_observations"]:
    r = requests.get(
        f"{REST}/{table}",
        headers={**REST_HEADERS, "Prefer": "count=exact"},
        params={"select": "*", "limit": 0},
    )
    count = r.headers.get("content-range", "?/?").split("/")[-1]
    print(f"  {table}: {count} rows")

print()
print(f"Import complete — {total_imported} rows inserted, {total_skipped} duplicates skipped.")
