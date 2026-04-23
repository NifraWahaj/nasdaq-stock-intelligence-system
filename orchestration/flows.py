#orchestration/flows.py
from prefect import flow
from ingestion.pipeline import ingestion_flow
from prefect.client.schemas.schedules import CronSchedule
from processing.pipeline import processing_flow
from storage.db import init_db

@flow(name="nasdaq-master-pipeline")
def master_pipeline():
    # SETUP: Ensure tables exist before running logic
    init_db()
    
    # Stage 1: Ingestion (done)
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
