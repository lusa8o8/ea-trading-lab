// score-trade — EA Trading Lab Phase 7
// Receives trade context, returns scored risk percentage.
//
// POST body: { symbol, session_hour, day_of_week, month }
// Response:  { risk_pct, score, reason }
//
// Scoring rules (from CLAUDE.md):
//   EURJPY : flat 1.0% (scoring deferred — live sample too small)
//   NZDUSD : hour ∈ {10,14,16} → +1 | Thursday (dow=4) → +1
//   USDCAD : hour ∈ {14,16}    → +1 | Tuesday (dow=2)  → +1 | hour=12 → hard 0.5%
//   AUDUSD : hour = 12         → +1 | Wed/Thu (dow ∈ {3,4}) → +1
//   Score 2 → 1.5% | Score 1 → 1.0% | Score 0 → 0.5%
//   August (month=8) : all pairs → 0.5% (hard seasonal rule)

import { serve } from "https://deno.land/std@0.208.0/http/server.ts";

interface ScoreRequest {
  symbol:       string;
  session_hour: number;
  day_of_week:  number;
  month:        number;
}

interface ScoreResponse {
  risk_pct: number;
  score:    number;
  reason:   string;
}

function scoreRisk(req: ScoreRequest): ScoreResponse {
  const { symbol, session_hour, day_of_week, month } = req;

  // August hard rule — all pairs drop to 0.5%
  if (month === 8) {
    return { risk_pct: 0.005, score: 0, reason: "August seasonal filter" };
  }

  // EURJPY — flat 1% until live A+ sample reaches 50+ trades
  if (symbol.includes("EURJPY")) {
    return { risk_pct: 0.01, score: 0, reason: "EURJPY flat risk — scoring deferred" };
  }

  // USDCAD — hour 12 is a hard override to 0.5% regardless of day
  if (symbol.includes("USDCAD") && session_hour === 12) {
    return { risk_pct: 0.005, score: 0, reason: "USDCAD hour 12 override" };
  }

  let score = 0;
  const reasons: string[] = [];

  if (symbol.includes("NZDUSD")) {
    if ([10, 14, 16].includes(session_hour)) {
      score++;
      reasons.push(`Hour ${session_hour}`);
    }
    if (day_of_week === 4) {
      score++;
      reasons.push("Thursday");
    }
  } else if (symbol.includes("USDCAD")) {
    if ([14, 16].includes(session_hour)) {
      score++;
      reasons.push(`Hour ${session_hour}`);
    }
    if (day_of_week === 2) {
      score++;
      reasons.push("Tuesday");
    }
  } else if (symbol.includes("AUDUSD")) {
    if (session_hour === 12) {
      score++;
      reasons.push("Hour 12");
    }
    if ([3, 4].includes(day_of_week)) {
      score++;
      reasons.push(day_of_week === 3 ? "Wednesday" : "Thursday");
    }
  }

  const risk_pct = score >= 2 ? 0.015 : score === 1 ? 0.01 : 0.005;
  const reason   = reasons.length > 0 ? reasons.join(" + ") : "No confluence";

  return { risk_pct, score, reason };
}

serve(async (req) => {
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: { "Content-Type": "application/json" },
    });
  }

  try {
    const body: ScoreRequest = await req.json();

    if (
      typeof body.symbol       !== "string"  ||
      typeof body.session_hour !== "number"  ||
      typeof body.day_of_week  !== "number"  ||
      typeof body.month        !== "number"
    ) {
      return new Response(
        JSON.stringify({ error: "Missing or invalid fields: symbol, session_hour, day_of_week, month required" }),
        { status: 400, headers: { "Content-Type": "application/json" } }
      );
    }

    const result = scoreRisk(body);
    return new Response(JSON.stringify(result), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: String(err) }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }
});
