import os
from mlflow import MlflowClient

_mlflow_client = None

def get_mlflow_client():
    global _mlflow_client
    if _mlflow_client is None:
        tracking_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')
        _mlflow_client = MlflowClient(tracking_uri)
    return _mlflow_client
