"""
Indonesia Macro Dashboard — FastAPI Backend
Deploy on Render free tier (https://render.com)
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from supabase import create_client

app = FastAPI(title="Indonesia Macro API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your Vercel domain in production
    allow_methods=["GET"],
    allow_headers=["*"],
)

def db():
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_KEY"]
    )


@app.get("/snapshot")
def get_snapshot():
    """Single endpoint — returns all latest values for the dashboard."""
    client = db()

    def latest(table, fields, order_col="collected_at", limit=1):
        try:
            r = client.table(table).select(fields)\
                .order(order_col, desc=True).limit(limit).execute()
            return r.data
        except Exception:
            return []

    def latest_per(table, fields, group_col, order_col="collected_at"):
        """Get latest row per unique value of group_col."""
        try:
            rows = client.table(table).select(fields)\
                .order(order_col, desc=True).limit(50).execute().data
            seen, result = set(), []
            for r in rows:
                key = r[group_col]
                if key not in seen:
                    seen.add(key)
                    result.append(r)
            return result
        except Exception:
            return []

    return {
        "fx": latest_per("fx_rates", "pair,rate,collected_at", "pair"),
        "jci": latest("jci", "close,change_pct,collected_at"),
        "bi_rate": latest("bi_rate", "effective_date,rate_pct,decision", "effective_date"),
        "inflation": latest("inflation", "period,headline_pct,core_pct,mom_pct", "period"),
        "trade": latest("trade_balance", "period,exports_usd_bn,imports_usd_bn,balance_usd_bn", "period"),
        "reserves": latest("foreign_reserves", "period,reserves_usd_bn,months_import", "period"),
        "commodities": latest_per("commodity_prices", "commodity,price,unit,collected_at", "commodity"),
        "global_macro": latest_per("global_macro", "indicator,value,collected_at", "indicator"),
        "sbn": latest("sbn_foreign_ownership", "period,foreign_pct,foreign_idr_tn", "period"),
        "weekly_brief": latest("weekly_briefs", "week_start,brief_text,generated_at", "week_start"),
    }


@app.get("/history/{table}")
def get_history(table: str, days: int = 90):
    """Return time-series history for charting."""
    allowed = {
        "fx_rates", "jci", "commodity_prices",
        "global_macro", "inflation", "trade_balance",
        "foreign_reserves", "sbn_foreign_ownership",
    }
    if table not in allowed:
        raise HTTPException(status_code=400, detail="Table not allowed")

    client = db()
    try:
        r = client.table(table).select("*")\
            .order("collected_at" if "collected_at" in ["fx_rates", "jci", "commodity_prices", "global_macro"] else "period", desc=False)\
            .limit(500).execute()
        return r.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
