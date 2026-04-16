import logging
from datetime import date, timedelta
import pandas as pd
import yfinance as yf
from sqlalchemy import text
from storage.db import engine

logger = logging.getLogger(__name__)

TICKERS = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "INTC", "AMD", "NFLX"]

HISTORICAL_DAYS = 730  # 2 years


def get_latest_date_per_ticker() -> dict[str, date]:
    """
    Query DB for the most recent date we have per ticker.
    Returns e.g. {"AAPL": date(2024, 3, 1), ...}
    Tickers with no data at all won't appear in the dict.
    """
    query = text("""
        SELECT symbol, MAX(date) AS latest
        FROM prices
        GROUP BY symbol
    """)
    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()
    return {row.symbol: row.latest for row in rows}


def fetch_ticker(symbol: str, start: date, end: date) -> pd.DataFrame:
    """
    Fetch OHLCV for one ticker between start and end (inclusive).
    Returns a clean DataFrame with columns:
        date, symbol, open, high, low, close, volume
    Returns empty DataFrame if yfinance returns nothing.
    """
    logger.info(f"Fetching {symbol} from {start} to {end}")
    
    # yfinance end date is exclusive, so add 1 day
    raw = yf.download(
        symbol,
        start=str(start),
        end=str(end + timedelta(days=1)),
        auto_adjust=True,   # adjusts OHLCV for splits/dividends
        progress=False
    )

    if raw.empty:
        logger.warning(f"No data returned for {symbol}")
        return pd.DataFrame()

    raw = raw.reset_index()

    # yfinance column names are inconsistent across versions
    raw.columns = [c[0] if isinstance(c, tuple) else c for c in raw.columns]
    raw.columns = [c.lower() for c in raw.columns]

    df = pd.DataFrame({
        "date":   pd.to_datetime(raw["date"]).dt.date,
        "symbol": symbol,
        "open":   raw["open"].round(4),
        "high":   raw["high"].round(4),
        "low":    raw["low"].round(4),
        "close":  raw["close"].round(4),
        "volume": raw["volume"].astype("Int64"),  # nullable int
    })

    # Drop any rows where close is null or zero (data glitch)
    df = df[df["close"].notna() & (df["close"] > 0)]

    logger.info(f"Fetched {len(df)} rows for {symbol}")
    return df


def fetch_all(tickers: list[str] = TICKERS) -> pd.DataFrame:
    """
    Smart fetch for all tickers:
    - First-time ticker: pulls full 2-year history
    - Known ticker: pulls only rows after the latest date in DB
    Returns a single concatenated DataFrame for all tickers.
    """
    latest_dates = get_latest_date_per_ticker()
    today = date.today()
    frames = []

    for symbol in tickers:
        if symbol in latest_dates:
            # Incremental — only fetch what's missing
            start = latest_dates[symbol] + timedelta(days=1)
        else:
            # First run — full historical backfill
            start = today - timedelta(days=HISTORICAL_DAYS)

        if start > today:
            logger.info(f"{symbol} is already up to date, skipping.")
            continue

        df = fetch_ticker(symbol, start, today)
        if not df.empty:
            frames.append(df)

    if not frames:
        logger.info("Nothing new to fetch across all tickers.")
        return pd.DataFrame()

    result = pd.concat(frames, ignore_index=True)
    logger.info(f"Total rows fetched across all tickers: {len(result)}")
    return result