from mlflow import MlflowClient
from settings import MLFLOW_TRACKING_URI

_mlflow_client = None

def get_mlflow_client():
    global _mlflow_client
    if _mlflow_client is None:
        _mlflow_client = MlflowClient(MLFLOW_TRACKING_URI)
    return _mlflow_client
