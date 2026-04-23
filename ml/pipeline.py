import logging
from prefect import flow

logger = logging.getLogger(__name__)



@flow(name="nasdaq-ml-pipeline")
def ml_flow():
    pass


if __name__ == "__main__":
    ml_flow()