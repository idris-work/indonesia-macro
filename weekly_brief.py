"""
Weekly AI Brief Generator
Uses Claude API (your enterprise subscription) to synthesize macro data
into an investor-grade weekly intelligence brief.
Schedule: Every Monday 07:00 WIB (00:00 UTC)
"""
import logging
import os
from datetime import date, timedelta
import anthropic
from base import get_supabase

log = logging.getLogger("weekly_brief")


def fetch_snapshot(db) -> dict:
    """Pull latest values from all key tables for the brief."""
    snapshot = {}

    # Latest FX
    fx = db.table("fx_rates")\
        .select("pair, rate, collected_at")\
        .order("collected_at", desc=True)\
        .limit(10)\
        .execute()
    snapshot["fx"] = {r["pair"]: r["rate"] for r in fx.data}

    # Latest BI rate
    bi = db.table("bi_rate")\
        .select("effective_date, rate_pct, decision")\
        .order("effective_date", desc=True)\
        .limit(1)\
        .execute()
    snapshot["bi_rate"] = bi.data[0] if bi.data else {}

    # Latest inflation
    inf = db.table("inflation")\
        .select("period, headline_pct, core_pct")\
        .order("period", desc=True)\
        .limit(2)\
        .execute()
    snapshot["inflation"] = inf.data

    # Latest trade
    trade = db.table("trade_balance")\
        .select("period, exports_usd_bn, imports_usd_bn, balance_usd_bn")\
        .order("period", desc=True)\
        .limit(2)\
        .execute()
    snapshot["trade"] = trade.data

    # Latest commodities
    comms = db.table("commodity_prices")\
        .select("commodity, price, unit, collected_at")\
        .order("collected_at", desc=True)\
        .limit(20)\
        .execute()
    # Deduplicate by commodity — take latest per commodity
    seen = {}
    for r in comms.data:
        if r["commodity"] not in seen:
            seen[r["commodity"]] = r
    snapshot["commodities"] = list(seen.values())

    # Latest global macro
    global_m = db.table("global_macro")\
        .select("indicator, value, collected_at")\
        .order("collected_at", desc=True)\
        .limit(20)\
        .execute()
    seen_g = {}
    for r in global_m.data:
        if r["indicator"] not in seen_g:
            seen_g[r["indicator"]] = r["value"]
    snapshot["global"] = seen_g

    # Latest foreign reserves
    res = db.table("foreign_reserves")\
        .select("period, reserves_usd_bn, months_import")\
        .order("period", desc=True)\
        .limit(1)\
        .execute()
    snapshot["reserves"] = res.data[0] if res.data else {}

    # SBN foreign ownership
    sbn = db.table("sbn_foreign_ownership")\
        .select("period, foreign_pct, foreign_idr_tn")\
        .order("period", desc=True)\
        .limit(1)\
        .execute()
    snapshot["sbn"] = sbn.data[0] if sbn.data else {}

    return snapshot


def build_prompt(snapshot: dict, week_start: str) -> str:
    return f"""
You are a senior macro analyst specializing in Indonesian and broader EM markets.
Write a concise weekly intelligence brief for professional investors and fund managers.

Week of: {week_start}

Current macro snapshot:
{snapshot}

Write the brief in this structure:

## Indonesia Macro Brief — Week of {week_start}

### Executive Summary (3 sentences max)
[Key takeaway — what is the dominant macro theme this week?]

### Currency & Monetary Policy
[USD/IDR level, trend, BI rate stance, any forward guidance signals]

### Inflation & Real Economy
[CPI reading, trajectory, implications for BI policy]

### External Sector
[Trade balance, commodity prices (CPO, coal, nickel, crude), implications for current account]

### Global Risk Factors
[Fed rate path, DXY, VIX, China PMI — and their specific transmission to Indonesia]

### Capital Flows
[SBN foreign ownership, reserves adequacy — any stress signals?]

### Key Risks to Watch
[2-3 bullet points max — specific, actionable]

Style guide:
- Professional, direct, no hedging unless genuinely uncertain
- Lead with the number, then interpret
- Flag divergences from historical norms explicitly
- Write in English
- Max 500 words total
"""


def generate():
    db = get_supabase()
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    week_start = date.today() - timedelta(days=date.today().weekday())
    week_start_str = week_start.isoformat()

    # Don't regenerate if already done this week
    existing = db.table("weekly_briefs")\
        .select("id")\
        .eq("week_start", week_start_str)\
        .execute()

    if existing.data:
        log.info(f"Brief already exists for week {week_start_str} — skipping")
        return

    log.info("Fetching macro snapshot...")
    snapshot = fetch_snapshot(db)

    log.info("Generating brief with Claude...")
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": build_prompt(snapshot, week_start_str)}],
    )

    brief_text = message.content[0].text

    db.table("weekly_briefs").insert({
        "week_start": week_start_str,
        "brief_text": brief_text,
        "model": "claude-sonnet-4-20250514",
    }).execute()

    log.info(f"Brief generated and stored for week {week_start_str}")
    print("\n" + brief_text)


if __name__ == "__main__":
    generate()
