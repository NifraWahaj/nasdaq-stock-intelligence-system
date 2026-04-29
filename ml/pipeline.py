import logging
from prefect import flow, task
from ml.trainer import train_model
from ml.predictor import make_predictions

logger = logging.getLogger(__name__)

@task(retries=1, retry_delay_seconds=30)
def train_task():
    logger.info("Executing Model Training Task...")
    return train_model()

@task(retries=2, retry_delay_seconds=15)
def predict_task():
    logger.info("Executing Prediction Generation Task...")
    make_predictions()

@flow(name="nasdaq-ml-pipeline")
def ml_flow():
    train_results = train_task()
    predict_task()    
    return train_results

if __name__ == "__main__":
    ml_flow()