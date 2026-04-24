#orchestration/flows.py
from prefect import flow, task
from ingestion.pipeline import ingestion_flow
from prefect.client.schemas.schedules import CronSchedule
from ml.pipeline import ml_flow
from processing.pipeline import processing_flow
from storage.db import init_db

@task(name="initialise-database", retries=3, retry_delay_seconds=10)
def task_init_db():
    init_db()

@task(name="initialise-ge-suite", retries=2, retry_delay_seconds=10)
def task_init_ge():
    """
    Ensures Great Expectations suite exists.
    Runs only if suite file is missing or empty.
    """
    import json
    import os
    from gx.create_suite import create_nasdaq_suite
    
    # suite_path = "gx/expectations/prices_suite.json"
    path = "gx/expectations/prices_suite.json"

    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
            if data.get("expectations"):
                return  # already initialized

    create_nasdaq_suite()



@flow(name="nasdaq-master-pipeline")
def master_pipeline():
    """
    End-to-end pipeline:
    1. Initialize DB + GE
    2. Ingest raw + clean data
    3. Validate + engineer features
    4. Train ML + generate predictions
    """

    # SETUP
    task_init_db()
    task_init_ge() 
    
    # Stage 1: Ingestion 
    ingestion_flow()
    
    # Stage 2: Feature engineering
    processing_flow()
    
    # Stage 3: ML 
    # ml_flow()
    
    # Stage 4: Generate predictions
    # prediction_flow()

    # Advance Extension
    # train_result = ml_flow()
    # task_monitor(train_result)   # runs after ML, uses today's model version

if __name__ == "__main__":
    # 1. Trigger an immediate run in the background (Optional but helpful)
    # master_pipeline() 

    # 2. Start the permanent server/worker
    master_pipeline.serve(
        name="nasdaq-manual-deployment",
        tags=["dev", "nasdaq"],
        description="Manual trigger for the full Nasdaq pipeline",
        schedule=CronSchedule(cron="30 17 * * 1-5", timezone="America/New_York") # runs at 5:30 PM New York time
    )
