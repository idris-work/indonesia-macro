"""
BPS (Badan Pusat Statistik) Collector
Source: api.bps.go.id — free, requires free registration for API key
Collects: CPI/Inflation, Trade Balance (monthly)
Schedule: Monthly (data released ~mid-month for prior month)
Docs: https://webapi.bps.go.id/documentation/
"""
import logging
import httpx
import os
from datetime import date
from base import get_supabase

log = logging.getLogger("bps")

BPS_BASE = "https://webapi.bps.go.id/v1/api"
BPS_API_KEY = os.environ.get("BPS_API_KEY", "")

# BPS variable IDs (look these up in BPS API explorer)
# These are stable IDs for headline CPI and trade balance
BPS_VARS = {
    "cpi_headline": {
        "var": "2212",   # CPI YoY — verify current ID at webapi.bps.go.id
        "table": "inflation",
        "field": "headline_pct",
    },
    "trade_exports": {
        "var": "1756",   # Total exports USD
        "table": "trade_balance",
        "field": "exports_usd_bn",
    },
    "trade_imports": {
        "var": "1757",   # Total imports USD
        "table": "trade_balance",
        "field": "imports_usd_bn",
    },
}


def fetch_bps(var_id: str, domain: str = "0000") -> list[dict]:
    """
    Fetch data from BPS API.
    domain='0000' means national level.
    Returns list of {period, value} dicts.
    """
    try:
        resp = httpx.get(
            f"{BPS_BASE}/list/model/data/lang/ind/domain/{domain}/var/{var_id}",
            params={"key": BPS_API_KEY},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        # BPS returns nested structure — flatten to {period, value}
        results = []
        datacontent = data.get("datacontent", {})
        for period_key, val in datacontent.items():
            try:
                results.append({
                    "period": period_key,
                    "value": float(str(val).replace(",", ".")),
                })
            except (ValueError, TypeError):
                continue
        return sorted(results, key=lambda x: x["period"], reverse=True)

    except Exception as e:
        log.error(f"BPS fetch error for var {var_id}: {e}")
        return []


def collect_inflation():
    """Collect latest CPI data from BPS."""
    if not BPS_API_KEY:
        log.error("BPS_API_KEY not set")
        return

    db = get_supabase()
    rows = fetch_bps(BPS_VARS["cpi_headline"]["var"])

    if not rows:
        log.warning("No CPI data returned from BPS")
        return

    latest = rows[0]
    # BPS period format is typically 'YYYYMM' — convert to date
    try:
        year = int(latest["period"][:4])
        month = int(latest["period"][4:6])
        period_date = date(year, month, 1).isoformat()
    except Exception:
        log.error(f"Could not parse period: {latest['period']}")
        return

    row = {
        "period": period_date,
        "headline_pct": latest["value"],
        "source": "bps",
    }

    # Upsert — BPS data gets revised occasionally
    db.table("inflation").upsert(row, on_conflict="period").execute()
    log.info(f"Inflation {period_date}: {latest['value']}% YoY")


def collect_trade():
    """Collect latest trade balance data from BPS."""
    if not BPS_API_KEY:
        log.error("BPS_API_KEY not set")
        return

    db = get_supabase()

    exports_rows = fetch_bps(BPS_VARS["trade_exports"]["var"])
    imports_rows = fetch_bps(BPS_VARS["trade_imports"]["var"])

    if not exports_rows or not imports_rows:
        log.warning("Incomplete trade data from BPS")
        return

    latest_exp = exports_rows[0]
    latest_imp = imports_rows[0]

    # Only upsert if same period
    if latest_exp["period"] != latest_imp["period"]:
        log.warning("Export/import period mismatch — skipping")
        return

    try:
        year = int(latest_exp["period"][:4])
        month = int(latest_exp["period"][4:6])
        period_date = date(year, month, 1).isoformat()
    except Exception:
        return

    exports = latest_exp["value"] / 1000  # convert to USD bn if in USD mn
    imports = latest_imp["value"] / 1000
    balance = exports - imports

    row = {
        "period": period_date,
        "exports_usd_bn": round(exports, 3),
        "imports_usd_bn": round(imports, 3),
        "balance_usd_bn": round(balance, 3),
        "source": "bps",
    }

    db.table("trade_balance").upsert(row, on_conflict="period").execute()
    log.info(f"Trade {period_date}: balance = {balance:+.3f}B USD")


def collect():
    collect_inflation()
    collect_trade()


if __name__ == "__main__":
    collect()
