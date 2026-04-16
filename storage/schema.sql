-- 1. RAW DATA LAYER (ELT: Ingestion writes here)
CREATE TABLE IF NOT EXISTS prices (
    id          SERIAL PRIMARY KEY,
    date        DATE NOT NULL,
    symbol      VARCHAR(10) NOT NULL,
    open        NUMERIC(12, 4),
    high        NUMERIC(12, 4),
    low         NUMERIC(12, 4),
    close       NUMERIC(12, 4),
    volume      BIGINT,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (date, symbol) -- Critical for idempotency
);

-- 2. ANALYTICS LAYER (ELT: Transform writes here)
CREATE TABLE IF NOT EXISTS features (
    id          SERIAL PRIMARY KEY,
    date        DATE NOT NULL,
    symbol      VARCHAR(10) NOT NULL,
    ma_7        NUMERIC(12, 4),
    ma_21       NUMERIC(12, 4),
    rsi_14      NUMERIC(8, 4),
    daily_return NUMERIC(10, 6), 
    volatility_7 NUMERIC(10, 6), -- for risk analysis
    target      NUMERIC(12, 4), -- Next day's close
    UNIQUE (date, symbol)
);

-- 3. GOVERNANCE LAYER (MLOps: Registry & Performance)
CREATE TABLE IF NOT EXISTS model_registry (
    id            SERIAL PRIMARY KEY,
    model_version VARCHAR(50) NOT NULL,
    symbol        VARCHAR(10) NOT NULL,
    rmse          NUMERIC(10, 6),
    mae           NUMERIC(10, 6),
    r2            NUMERIC(6, 4),
    is_champion   BOOLEAN DEFAULT FALSE,
    trained_at    TIMESTAMPTZ DEFAULT NOW(),
    model_path    TEXT -- e.g., /app/models/xgboost_v1.bin
);

-- 4. SERVING LAYER (Predictions for Dashboard)
CREATE TABLE IF NOT EXISTS predictions (
    id              SERIAL PRIMARY KEY,
    date            DATE NOT NULL,
    symbol          VARCHAR(10) NOT NULL,
    predicted_close NUMERIC(12, 4),
    actual_close    NUMERIC(12, 4), -- Updated by pipeline after market close
    model_version   VARCHAR(50),
    predicted_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (date, symbol)
);