import logging
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta

from ingestion.fetcher import fetch_all, TICKERS
from ingestion.loader import load_prices
from storage.db import init_db

logger = logging.getLogger(__name__)


@task(
    name="initialise-database",
    retries=3,
    retry_delay_seconds=10
)
def task_init_db():
    """Ensure all tables exist before doing anything else."""
    init_db()


@task(
    name="fetch-stock-data",
    retries=3,
    retry_delay_seconds=30,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1)
)
def task_fetch(tickers: list[str]):
    df = fetch_all(tickers)
    logger.info(f"Fetch task returned {len(df)} rows")
    return df


@task(
    name="load-to-database",
    retries=2,
    retry_delay_seconds=15
)
def task_load(df):
    summary = load_prices(df)
    return summary


@flow(
    name="nasdaq-ingestion-pipeline",
    description="Daily ingestion of NASDAQ OHLCV data for 10 tickers."
)
def ingestion_flow(tickers: list[str] = TICKERS):
    task_init_db()
    df = task_fetch(tickers)
    summary = task_load(df)
    logger.info(f"Ingestion flow complete: {summary}")
    return summary


if __name__ == "__main__":
    ingestion_flow()