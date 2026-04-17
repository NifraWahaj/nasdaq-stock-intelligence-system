from prefect import flow
from ingestion.pipeline import ingestion_flow

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
    master_pipeline()