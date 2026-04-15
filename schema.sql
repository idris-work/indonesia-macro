-- ============================================================
-- Indonesia Macro Dashboard — Supabase Schema
-- ============================================================

-- Enable TimescaleDB if available, else use standard Postgres timestamps
-- Run this in Supabase SQL Editor

-- ── FX / Currency ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fx_rates (
    id          BIGSERIAL PRIMARY KEY,
    collected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    pair        TEXT NOT NULL,          -- e.g. 'USD/IDR', 'DXY'
    rate        NUMERIC(18, 4) NOT NULL,
    source      TEXT NOT NULL           -- 'jisdor', 'yahoo', 'fred'
);
CREATE INDEX idx_fx_pair_time ON fx_rates (pair, collected_at DESC);

-- ── BI Policy Rate ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bi_rate (
    id              BIGSERIAL PRIMARY KEY,
    effective_date  DATE NOT NULL UNIQUE,
    rate_pct        NUMERIC(5, 2) NOT NULL,   -- e.g. 6.25
    decision        TEXT,                      -- 'hold', 'hike', 'cut'
    notes           TEXT,
    source          TEXT NOT NULL DEFAULT 'bi.go.id'
);

-- ── Inflation (CPI) — BPS ────────────────────────────────────
CREATE TABLE IF NOT EXISTS inflation (
    id              BIGSERIAL PRIMARY KEY,
    period          DATE NOT NULL UNIQUE,      -- first day of month
    headline_pct    NUMERIC(6, 2),             -- YoY
    core_pct        NUMERIC(6, 2),             -- YoY core
    mom_pct         NUMERIC(6, 2),             -- MoM
    source          TEXT NOT NULL DEFAULT 'bps'
);

-- ── Trade Balance — BPS ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS trade_balance (
    id              BIGSERIAL PRIMARY KEY,
    period          DATE NOT NULL UNIQUE,
    exports_usd_bn  NUMERIC(10, 3),
    imports_usd_bn  NUMERIC(10, 3),
    balance_usd_bn  NUMERIC(10, 3),
    source          TEXT NOT NULL DEFAULT 'bps'
);

-- ── Foreign Reserves — BI ────────────────────────────────────
CREATE TABLE IF NOT EXISTS foreign_reserves (
    id              BIGSERIAL PRIMARY KEY,
    period          DATE NOT NULL UNIQUE,
    reserves_usd_bn NUMERIC(10, 3) NOT NULL,
    months_import   NUMERIC(5, 1),             -- months of import coverage
    source          TEXT NOT NULL DEFAULT 'bi.go.id'
);

-- ── Commodity Prices ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS commodity_prices (
    id              BIGSERIAL PRIMARY KEY,
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    commodity       TEXT NOT NULL,             -- 'cpo', 'coal', 'nickel', 'crude_brent'
    price           NUMERIC(18, 4) NOT NULL,
    unit            TEXT NOT NULL,             -- 'USD/MT', 'USD/BBL', etc.
    source          TEXT NOT NULL
);
CREATE INDEX idx_commodity_time ON commodity_prices (commodity, collected_at DESC);

-- ── JCI / IHSG ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS jci (
    id              BIGSERIAL PRIMARY KEY,
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    close           NUMERIC(12, 2) NOT NULL,
    volume          BIGINT,
    change_pct      NUMERIC(6, 2),
    source          TEXT NOT NULL DEFAULT 'yahoo'
);

-- ── Global Macro (Fed, VIX, China PMI) ──────────────────────
CREATE TABLE IF NOT EXISTS global_macro (
    id              BIGSERIAL PRIMARY KEY,
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    indicator       TEXT NOT NULL,             -- 'fed_rate', 'vix', 'china_pmi', 'dxy'
    value           NUMERIC(18, 4) NOT NULL,
    source          TEXT NOT NULL
);
CREATE INDEX idx_global_macro_time ON global_macro (indicator, collected_at DESC);

-- ── SBN Foreign Ownership ────────────────────────────────────
CREATE TABLE IF NOT EXISTS sbn_foreign_ownership (
    id              BIGSERIAL PRIMARY KEY,
    period          DATE NOT NULL UNIQUE,
    foreign_pct     NUMERIC(5, 2),             -- % of total SBN held by foreigners
    foreign_idr_tn  NUMERIC(12, 3),            -- IDR trillion
    source          TEXT NOT NULL DEFAULT 'djppr'
);

-- ── AI Weekly Brief ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS weekly_briefs (
    id              BIGSERIAL PRIMARY KEY,
    week_start      DATE NOT NULL UNIQUE,
    brief_text      TEXT NOT NULL,
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    model           TEXT NOT NULL DEFAULT 'claude-sonnet-4-20250514'
);

-- ── Useful Views ─────────────────────────────────────────────

-- Latest value per indicator (global macro)
CREATE OR REPLACE VIEW latest_global_macro AS
SELECT DISTINCT ON (indicator)
    indicator, value, collected_at, source
FROM global_macro
ORDER BY indicator, collected_at DESC;

-- Latest commodity prices
CREATE OR REPLACE VIEW latest_commodities AS
SELECT DISTINCT ON (commodity)
    commodity, price, unit, collected_at, source
FROM commodity_prices
ORDER BY commodity, collected_at DESC;

-- Latest FX rates
CREATE OR REPLACE VIEW latest_fx AS
SELECT DISTINCT ON (pair)
    pair, rate, collected_at, source
FROM fx_rates
ORDER BY pair, collected_at DESC;
