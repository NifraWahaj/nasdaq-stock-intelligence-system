#orchestration/flows.py
from prefect import flow, task
from ingestion.pipeline import ingestion_flow
from prefect.client.schemas.schedules import CronSchedule
from processing.pipeline import processing_flow
from storage.db import init_db

@task(name="initialise-database", retries=3, retry_delay_seconds=10)
def task_init_db():
    init_db()


@task(name="initialise-ge-suite")
def task_init_ge():
    import json
    import os
    from gx.create_suite import create_nasdaq_suite
    
    suite_path = "/app/gx/expectations/prices_suite.json"
    
    # Check if file exists AND if it actually has expectations
    if os.path.exists(suite_path):
        with open(suite_path, 'r') as f:
            data = json.load(f)
            if data.get("expectations"): # If list is not empty
                return 
    
    # If file is missing or empty, run the creation logic
    create_nasdaq_suite()



@flow(name="nasdaq-master-pipeline")
def master_pipeline():
    # SETUP: Ensure tables exist before running logic
    task_init_db()
    
    task_init_ge() # one-time setup for GE suite
    
    # Stage 1: Ingestion 
    ingestion_flow()
    
    # Stage 2: Feature engineering
    processing_flow()
    
    # Stage 3: ML training + champion/challenger 
    # ml_flow()
    
    # Stage 4: Generate predictions
    # prediction_flow()

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
