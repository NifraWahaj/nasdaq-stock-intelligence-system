# ingestion/pipeline.py
from prefect import flow, task, get_run_logger
from ingestion.fetcher import fetch_all, TICKERS
from ingestion.loader import load_prices
from storage.db import init_db


@task
def task_init_db():
    init_db()


@task
def task_fetch(tickers):
    return fetch_all(tickers)


@task
def task_load(df):
    return load_prices(df)


@flow(name="nasdaq-ingestion-pipeline")
def ingestion_flow():

    logger = get_run_logger()

    task_init_db()

    df = task_fetch(TICKERS)

    if df.empty:
        logger.info("No new data")
        return {"inserted": 0, "skipped": 0}

    result = task_load(df)

    logger.info(f"Done: {result}")
    return result