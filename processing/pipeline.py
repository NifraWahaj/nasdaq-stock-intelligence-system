# processing/pipeline.py
import logging
from prefect import flow, task

from processing.features import fetch_prices as fetch_for_features
from processing.features import engineer_features, load_features
from processing.validation import run_validation

logger = logging.getLogger(__name__)


@task(name="validate-prices", retries=1, retry_delay_seconds=10)
def task_validate():
    return run_validation()   # no df argument anymore — GE reads DB directly


@task(name="engineer-features", retries=2, retry_delay_seconds=15)
def task_engineer():
    df = fetch_for_features()
    return engineer_features(df)


@task(name="load-features", retries=2, retry_delay_seconds=15)
def task_load(features_df):
    return load_features(features_df)


@flow(name="nasdaq-processing-pipeline")
def processing_flow():
    task_validate()                    # halt pipeline if prices data is bad
    features_df = task_engineer()
    summary     = task_load(features_df)
    logger.info(f"Processing complete: {summary}")
    return summary


if __name__ == "__main__":
    processing_flow()