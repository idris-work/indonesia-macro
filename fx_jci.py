"""
FX + JCI Collector
Sources: Yahoo Finance (yfinance) — free, no API key needed
Collects: USD/IDR, DXY, JCI (^JKSE)
Schedule: Every 15min during market hours via GitHub Actions
"""
import logging
import yfinance as yf
from base import get_supabase, now_utc

log = logging.getLogger("fx_jci")

TICKERS = {
    "IDR=X":  {"pair": "USD/IDR", "table": "fx_rates", "source": "yahoo"},
    "DX-Y.NYB": {"pair": "DXY",   "table": "fx_rates", "source": "yahoo"},
    "^JKSE":  {"pair": "JCI",     "table": "jci",      "source": "yahoo"},
}

def collect():
    db = get_supabase()
    collected_at = now_utc()

    for ticker_sym, meta in TICKERS.items():
        try:
            ticker = yf.Ticker(ticker_sym)
            info = ticker.fast_info

            price = info.last_price
            if price is None:
                log.warning(f"No price for {ticker_sym}, skipping")
                continue

            if meta["table"] == "fx_rates":
                row = {
                    "collected_at": collected_at,
                    "pair": meta["pair"],
                    "rate": float(price),
                    "source": meta["source"],
                }
                db.table("fx_rates").insert(row).execute()
                log.info(f"FX {meta['pair']} = {price:.4f}")

            elif meta["table"] == "jci":
                prev_close = info.previous_close or price
                change_pct = ((price - prev_close) / prev_close) * 100
                row = {
                    "collected_at": collected_at,
                    "close": float(price),
                    "change_pct": round(change_pct, 2),
                    "source": meta["source"],
                }
                db.table("jci").insert(row).execute()
                log.info(f"JCI = {price:.2f} ({change_pct:+.2f}%)")

        except Exception as e:
            log.error(f"Error collecting {ticker_sym}: {e}")

if __name__ == "__main__":
    collect()
