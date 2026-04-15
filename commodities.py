"""
Commodity Prices Collector
Sources: Yahoo Finance (yfinance) — free
Collects: CPO (crude palm oil), Coal, Nickel, Brent Crude
Schedule: Daily (commodities don't need intraday for macro view)
"""
import logging
import yfinance as yf
from base import get_supabase, now_utc

log = logging.getLogger("commodities")

COMMODITIES = {
    # CPO — Malaysia futures as proxy (most liquid CPO market)
    "FCPO.KL": {
        "commodity": "cpo",
        "unit": "MYR/MT",
        "source": "bursa_via_yahoo",
    },
    # Coal — Newcastle futures via ETF proxy or use Trading Economics scrape
    # Using GlobalCoalNewcastle as best free proxy
    "MTF=F": {
        "commodity": "coal_newcastle",
        "unit": "USD/MT",
        "source": "yahoo",
    },
    # Nickel — LME via CME futures
    "NI=F": {
        "commodity": "nickel",
        "unit": "USD/MT",
        "source": "yahoo",
    },
    # Brent Crude
    "BZ=F": {
        "commodity": "crude_brent",
        "unit": "USD/BBL",
        "source": "yahoo",
    },
}


def collect():
    db = get_supabase()
    collected_at = now_utc()

    for ticker_sym, meta in COMMODITIES.items():
        try:
            ticker = yf.Ticker(ticker_sym)
            price = ticker.fast_info.last_price

            if price is None:
                log.warning(f"No price for {ticker_sym}, skipping")
                continue

            row = {
                "collected_at": collected_at,
                "commodity": meta["commodity"],
                "price": float(price),
                "unit": meta["unit"],
                "source": meta["source"],
            }
            db.table("commodity_prices").insert(row).execute()
            log.info(f"{meta['commodity']} = {price:.2f} {meta['unit']}")

        except Exception as e:
            log.error(f"Error collecting {ticker_sym}: {e}")


if __name__ == "__main__":
    collect()
