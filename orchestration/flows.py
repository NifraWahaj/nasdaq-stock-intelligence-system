from prefect import flow
from ingestion.pipeline import ingestion_flow
from prefect.client.schemas.schedules import CronSchedule

@flow(name="nasdaq-master-pipeline")
def master_pipeline():
    # Stage 1: Ingestion (done)
    ingestion_flow()
    
    # Stage 2: Feature engineering
    # processing_flow()
    
    # Stage 3: ML training + champion/challenger 
    # ml_flow()
    
    # Stage 4: Generate predictions
    # prediction_flow()

if __name__ == "__main__":
    # This turns the script into a permanent 'worker' 
    # that creates a Deployment in the UI
    master_pipeline.serve(
        name="nasdaq-manual-deployment",
        tags=["dev", "nasdaq"],
        description="Manual trigger for the full Nasdaq pipeline",
        # Optional: Add a schedule here if you want it to run every morning
        # schedule=CronSchedule(cron="0 9 * * 1-5") 
    )