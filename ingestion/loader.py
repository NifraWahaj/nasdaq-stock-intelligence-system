# injestion/loader.py
import logging
import pandas as pd
from sqlalchemy import text
from storage.db import engine

logger = logging.getLogger(__name__)

def load_raw(df: pd.DataFrame) -> None:
    """
    Append-only insert into raw_prices.
    No conflict handling — we want every fetch attempt recorded.
    This is the audit trail.
    """
    if df.empty:
        return

    sql = text("""
        INSERT INTO raw_prices (date, symbol, open, high, low, close, volume)
        VALUES (:date, :symbol, :open, :high, :low, :close, :volume)
    """)
    with engine.begin() as conn:
        conn.execute(sql, df.to_dict(orient="records"))
    logger.info(f"Raw load: {len(df)} rows appended to raw_prices")


def load_prices(df: pd.DataFrame) -> dict:
    """
    Insert cleaned rows into prices table.
    ON CONFLICT DO NOTHING — idempotent.
    """
    if df.empty:
        logger.info("Nothing to load.")
        return {"inserted": 0, "skipped": 0}

    sql = text("""
        INSERT INTO prices (date, symbol, open, high, low, close, volume)
        VALUES (:date, :symbol, :open, :high, :low, :close, :volume)
        ON CONFLICT (date, symbol) DO NOTHING
    """)

    rows     = df.to_dict(orient="records")
    inserted = 0
    skipped  = 0

    with engine.begin() as conn:
        for row in rows:
            result = conn.execute(sql, row)
            if result.rowcount == 1:
                inserted += 1
            else:
                skipped += 1

    logger.info(f"Prices load — inserted: {inserted}, skipped: {skipped}")
    return {"inserted": inserted, "skipped": skipped}