# ingestion/fetcher.py
import logging
from datetime import date, timedelta, datetime
import pandas as pd
import pytz
import yfinance as yf
from sqlalchemy import text
from storage.db import engine

"""
Data ingestion module for fetching and preparing stock price data.

Responsibilities:
- Pull raw OHLCV data from Yahoo Finance (yfinance)
- Maintain incremental ingestion per ticker
- Produce:
    1. Raw dataset (audit trail → raw_prices table)
    2. Clean dataset (validated → prices table)

Design Notes:
- Raw data is never modified (append-only for traceability)
- Cleaning is minimal and deterministic
- Incremental fetch avoids re-downloading historical data
"""

logger = logging.getLogger(__name__)

TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "INTC", "AMD", "NFLX"]
HISTORICAL_DAYS = 730


def get_latest_date_per_ticker() -> dict[str, date]:
    """
    Fetch the most recent available date per ticker from the prices table.

    Returns:
        dict[str, date]: Mapping of symbol → latest stored date

    Purpose:
        Enables incremental ingestion by determining the correct start date
        for each ticker.
    """
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
    Fetch raw OHLCV data for a single ticker from Yahoo Finance.

    Args:
        symbol (str): Stock ticker (e.g., AAPL)
        start (date): Start date (inclusive)
        end (date): End date (inclusive)

    Returns:
        pd.DataFrame: Raw price data with standardized column names

    Notes:
        - No cleaning, filtering, or rounding is applied
        - Output is intended for audit storage (raw_prices)
        - Uses auto_adjust=True to account for splits/dividends
    """
    logger.info(f"Fetching {symbol} from {start} to {end}")
    try:
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

        df = pd.DataFrame({
            "date":   pd.to_datetime(raw["date"]).dt.date,
            "symbol": symbol,
            "open":   raw["open"],
            "high":   raw["high"],
            "low":    raw["low"],
            "close":  raw["close"],
            "volume": raw["volume"],
        })

        logger.info(f"Fetched {len(df)} raw rows for {symbol}")
        return df

    except Exception as e:
        logger.error(f"Failed to fetch {symbol}: {e}")
        return pd.DataFrame()


def clean_ticker(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply minimal cleaning to raw ticker data for downstream use.

    Args:
        df (pd.DataFrame): Raw OHLCV data

    Returns:
        pd.DataFrame: Cleaned dataset suitable for prices table

    Cleaning Rules:
        - Convert numeric columns to proper types
        - Round price fields to 4 decimal places
        - Remove rows with invalid or missing closing prices

    Design Principle:
        Only remove definitively invalid data — do not over-clean.
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
    Fetch and prepare data for multiple tickers.

    Args:
        tickers (list[str]): List of ticker symbols

    Returns:
        tuple:
            - raw_df   (pd.DataFrame): Unmodified raw data (for raw_prices)
            - clean_df (pd.DataFrame): Cleaned data (for prices)

    Behavior:
        - Determines per-ticker start date using existing DB state
        - Fetches only missing data (incremental ingestion)
        - Skips tickers already up-to-date
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