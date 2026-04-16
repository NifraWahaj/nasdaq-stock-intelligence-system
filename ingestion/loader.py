import logging
import pandas as pd
from sqlalchemy import text
from storage.db import engine

logger = logging.getLogger(__name__)


def load_prices(df: pd.DataFrame) -> dict:
    """
    Insert rows into the prices table.
    Uses ON CONFLICT DO NOTHING — safe to re-run (idempotent).
    Returns a summary dict with inserted/skipped counts.
    """
    if df.empty:
        logger.info("Nothing to load — empty DataFrame.")
        return {"inserted": 0, "skipped": 0}

    insert_sql = text("""
        INSERT INTO prices (date, symbol, open, high, low, close, volume)
        VALUES (:date, :symbol, :open, :high, :low, :close, :volume)
        ON CONFLICT (date, symbol) DO NOTHING
    """)

    rows = df.to_dict(orient="records")
    inserted = 0
    skipped = 0

    with engine.begin() as conn:           # begin() auto-commits on exit
        for row in rows:
            result = conn.execute(insert_sql, row)
            if result.rowcount == 1:
                inserted += 1
            else:
                skipped += 1

    logger.info(f"Load complete — inserted: {inserted}, skipped: {skipped}")
    return {"inserted": inserted, "skipped": skipped}