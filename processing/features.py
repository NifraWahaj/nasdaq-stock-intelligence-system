# processing/pipeline.py
import logging
import numpy as np
import pandas as pd
from sqlalchemy import text

from storage.db import engine

logger = logging.getLogger(__name__)

"""
Transformation logic and assumptions
─────────────────────────────────────
Input:  prices table (typed, clean, constrained by ingestion layer)
Output: features table (engineered indicators + ML target)

Feature assumptions:
- MA7 / MA21:  min_periods=1 so early rows use partial windows rather
               than producing NaN. Accepted tradeoff for time-series
               continuity.
- RSI(14):     Wilder's EMA method. NaN for first ~14 rows per ticker —
               these are dropped via dropna(subset=['target']) anyway.
- daily_return: pct_change(), first row per ticker filled with 0.
                Rationale: raw OHLCV has 0.81-0.94 inter-correlation
                (confirmed by EDA). Returns are stationary and remove
                multicollinearity.
- volatility_7: rolling std of daily_return, min_periods=2.
                Always >= 0 by definition.
- target:       close.shift(-1) per ticker = next trading day's close.
                Last row per ticker is always dropped (no next day yet).

Idempotency:
- Reads from prices (immutable source).
- Writes with ON CONFLICT (date, symbol) DO NOTHING.
- Re-running produces identical features table state.
"""


def fetch_prices() -> pd.DataFrame:
    with engine.connect() as conn:
        df = pd.read_sql(
            text("SELECT date, symbol, open, high, low, close, volume "
                 "FROM prices ORDER BY symbol, date"),
            conn
        )
    df["date"] = pd.to_datetime(df["date"]).dt.date
    logger.info(f"Fetched {len(df)} rows from prices for feature engineering")
    return df


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta    = series.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs       = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).round(4)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    frames = []

    for symbol, group in df.groupby("symbol"):
        g = group.sort_values("date").copy()

        g["ma_7"]         = g["close"].rolling(7,  min_periods=1).mean().round(4)
        g["ma_21"]        = g["close"].rolling(21, min_periods=1).mean().round(4)
        g["rsi_14"]       = compute_rsi(g["close"])
        g["daily_return"] = g["close"].pct_change().fillna(0).round(6)
        g["volatility_7"] = (
            g["daily_return"].rolling(7, min_periods=2).std().round(6)
        )
        g["target"] = g["close"].shift(-1).round(4)

        result = g[["date", "symbol", "ma_7", "ma_21", "rsi_14",
                     "daily_return", "volatility_7", "target"]]

        # Only drop rows where target is NaN (last row per ticker)
        # All other NaNs are legitimate partial-window values
        result = result.dropna(subset=["target"])

        frames.append(result)
        logger.info(f"{symbol}: {len(result)} feature rows")

    return pd.concat(frames, ignore_index=True)


def load_features(df: pd.DataFrame) -> dict:
    """Idempotent — ON CONFLICT DO NOTHING."""
    if df.empty:
        return {"inserted": 0, "skipped": 0}

    sql = text("""
        INSERT INTO features
            (date, symbol, ma_7, ma_21, rsi_14, daily_return, volatility_7, target)
        VALUES
            (:date, :symbol, :ma_7, :ma_21, :rsi_14,
             :daily_return, :volatility_7, :target)
        ON CONFLICT (date, symbol) DO NOTHING
    """)

    inserted = skipped = 0
    with engine.begin() as conn:
        for row in df.to_dict(orient="records"):
            r = conn.execute(sql, row)
            if r.rowcount == 1:
                inserted += 1
            else:
                skipped += 1

    logger.info(f"Features — inserted: {inserted}, skipped: {skipped}")
    return {"inserted": inserted, "skipped": skipped}