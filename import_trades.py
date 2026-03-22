import os
import csv
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Load credentials from .env in the same folder as this script
# ---------------------------------------------------------------------------
env_path = Path(__file__).parent / ".env"
if not env_path.exists():
    print(f"ERROR: .env not found at {env_path}")
    sys.exit(1)

with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_KEY missing from .env")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Import supabase-py (install if missing)
# ---------------------------------------------------------------------------
try:
    from supabase import create_client
except ImportError:
    print("supabase-py not found — installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "supabase", "-q"])
    from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------------------------
# CSV files to import
# ---------------------------------------------------------------------------
BASE = Path(r"C:\Users\Lusa\AppData\Roaming\MetaQuotes\Terminal\Common\Files")

FILES = [
    BASE / "Native data"              / "trade_log_EURJPY_H4 combined_B_MAE.csv",
    BASE / "trail b sessioned nzdusd" / "trade_log_NZDUSD_H2 trailb sessioned  mae at 75%.csv",
    BASE / "Native data"              / "trade_log_USDCAD_H2 trailb sessioned All things off.csv",
    BASE / "trail b sessioned audusd" / "trade_log_AUDUSD_H4 trailb all off.csv",
]

# ---------------------------------------------------------------------------
# Type coercions — CSV is all strings, Supabase expects correct types
# ---------------------------------------------------------------------------
INT_COLS    = {"trade_id", "session_hour", "day_of_week", "trades_count"}
FLOAT_COLS  = {
    "duration_hours", "entry_price", "sl_price", "tp_price", "exit_price",
    "lot_size", "risk_amount", "rr_target", "r_multiple",
    "mfe_pips", "mae_pips", "mfe_pct_tp", "mae_pct_sl",
    "ma_value", "atr14", "atr5", "atr_ratio",
    "adx14", "di_plus", "di_minus",
    "candle_body_pct", "price_ma_distance_pips", "prev_candle_range_pct",
}

def coerce(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        if k in INT_COLS:
            out[k] = int(v) if v not in ("", None) else None
        elif k in FLOAT_COLS:
            out[k] = float(v) if v not in ("", None) else None
        else:
            out[k] = v if v != "" else None
    return out

# ---------------------------------------------------------------------------
# Import loop
# ---------------------------------------------------------------------------
BATCH_SIZE = 200

for csv_path in FILES:
    if not csv_path.exists():
        print(f"\n[SKIP] File not found: {csv_path}")
        continue

    print(f"\n{'='*60}")
    print(f"Importing: {csv_path.name}")

    # Read all rows from CSV
    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))

    if not rows:
        print("  Empty file — skipped.")
        continue

    # Determine symbol + timeframe from first row (all rows in a file are the same pair)
    sample     = rows[0]
    symbol     = sample["symbol"]
    timeframe  = sample["timeframe"]

    # Fetch all existing trade_ids for this symbol+timeframe in one query
    existing_resp = (
        supabase.table("trades")
        .select("trade_id")
        .eq("symbol", symbol)
        .eq("timeframe", timeframe)
        .execute()
    )
    existing_ids = {r["trade_id"] for r in existing_resp.data}

    # Split into new vs duplicate
    new_rows  = []
    skip_count = 0
    for row in rows:
        tid = int(row["trade_id"])
        if tid in existing_ids:
            skip_count += 1
        else:
            new_rows.append(coerce(row))

    if not new_rows:
        print(f"  Imported: 0  |  Skipped (duplicates): {skip_count}")
        continue

    # Insert in batches
    inserted = 0
    for i in range(0, len(new_rows), BATCH_SIZE):
        batch = new_rows[i : i + BATCH_SIZE]
        supabase.table("trades").insert(batch).execute()
        inserted += len(batch)

    print(f"  Imported: {inserted}  |  Skipped (duplicates): {skip_count}")

print(f"\n{'='*60}")
print("Done.")
