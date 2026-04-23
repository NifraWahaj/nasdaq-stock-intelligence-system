# ingestion/fetcher.py
import logging
from datetime import date, timedelta, datetime
import pandas as pd
import pytz
import yfinance as yf
from sqlalchemy import text
from storage.db import engine

logger = logging.getLogger(__name__)

TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "INTC", "AMD", "NFLX"]
HISTORICAL_DAYS = 730


def get_latest_date_per_ticker() -> dict[str, date]:
    """unchanged — still needed"""
    query = text("""
        SELECT symbol, MAX(date) AS latest
        FROM prices
        GROUP BY symbol
    """)
    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()
    return {row.symbol: row.latest for row in rows}


def fetch_ticker_raw(symbol: str, start: date, end: date) -> pd.DataFrame:
    """
    Replaces fetch_ticker.
    Returns raw yfinance data with minimal processing — no filtering,
    no rounding. Saved to raw_prices as audit trail.
    """
    logger.info(f"Fetching {symbol} from {start} to {end}")

    raw = yf.download(
        symbol,
        start=str(start),
        end=str(end + timedelta(days=1)),
        auto_adjust=True,
        progress=False
    )

    if raw.empty:
        logger.warning(f"No data returned for {symbol}")
        return pd.DataFrame()

    raw = raw.reset_index()
    raw.columns = [c[0] if isinstance(c, tuple) else c for c in raw.columns]
    raw.columns = [c.lower() for c in raw.columns]

    return pd.DataFrame({
        "date":   pd.to_datetime(raw["date"]).dt.date,
        "symbol": symbol,
        "open":   raw["open"],
        "high":   raw["high"],
        "low":    raw["low"],
        "close":  raw["close"],
        "volume": raw["volume"],
    })


def clean_ticker(df: pd.DataFrame) -> pd.DataFrame:
    """
    New function. Takes a raw DataFrame, returns cleaned version
    ready for the prices table.
    """
    df = df.copy()
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").round(4)
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce").astype("Int64")

    # Drop definitive data errors only
    df = df[df["close"].notna() & (df["close"] > 0)]
    return df


def fetch_all_raw(tickers: list[str] = TICKERS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Replaces fetch_all.
    Returns (raw_df, clean_df) — raw goes to raw_prices, clean goes to prices.
    """
    tz = pytz.timezone("America/New_York")
    today = datetime.now(tz).date()
    latest_dates = get_latest_date_per_ticker()

    raw_frames   = []
    clean_frames = []

    for symbol in tickers:
        start = (latest_dates[symbol] + timedelta(days=1)
                 if symbol in latest_dates
                 else today - timedelta(days=HISTORICAL_DAYS))

        if start > today:
            logger.info(f"{symbol} up to date, skipping.")
            continue

        raw_df = fetch_ticker_raw(symbol, start, today)
        if raw_df.empty:
            continue

        raw_frames.append(raw_df)
        clean_frames.append(clean_ticker(raw_df))

    raw   = pd.concat(raw_frames,   ignore_index=True) if raw_frames   else pd.DataFrame()
    clean = pd.concat(clean_frames, ignore_index=True) if clean_frames else pd.DataFrame()

    logger.info(f"Fetched {len(raw)} raw rows, {len(clean)} clean rows")
    return raw, clean