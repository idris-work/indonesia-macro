"""
FRED Collector — Global Macro Indicators
Source: St. Louis Federal Reserve FRED API (free, no cost)
Get your free API key: https://fred.stlouisfed.org/docs/api/api_key.html
Collects: Fed Funds Rate, VIX, China PMI (NBS Manufacturing)
Schedule: Daily
"""
import logging
import httpx
import os
from base import get_supabase, now_utc

log = logging.getLogger("fred")

FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")

# FRED series IDs → our indicator names
SERIES = {
    "FEDFUNDS":    {"indicator": "fed_rate",   "source": "fred"},
    "VIXCLS":      {"indicator": "vix",        "source": "fred"},
    # China NBS Manufacturing PMI (via FRED)
    "CHNFPMANPISMEI": {"indicator": "china_pmi", "source": "fred"},
}


def fetch_latest(series_id: str) -> float | None:
    """Fetch the most recent observation for a FRED series."""
    try:
        resp = httpx.get(
            FRED_BASE,
            params={
                "series_id": series_id,
                "api_key": FRED_API_KEY,
                "file_type": "json",
                "sort_order": "desc",
                "limit": 1,
            },
            timeout=10,
        )
        resp.raise_for_status()
        obs = resp.json().get("observations", [])
        if obs and obs[0]["value"] != ".":
            return float(obs[0]["value"])
    except Exception as e:
        log.error(f"FRED fetch error for {series_id}: {e}")
    return None


def collect():
    if not FRED_API_KEY:
        log.error("FRED_API_KEY not set — skipping FRED collection")
        return

    db = get_supabase()
    collected_at = now_utc()

    for series_id, meta in SERIES.items():
        value = fetch_latest(series_id)
        if value is None:
            continue

        row = {
            "collected_at": collected_at,
            "indicator": meta["indicator"],
            "value": value,
            "source": meta["source"],
        }
        db.table("global_macro").insert(row).execute()
        log.info(f"{meta['indicator']} = {value}")


if __name__ == "__main__":
    collect()
