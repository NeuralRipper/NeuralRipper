import os
from mlflow import MlflowClient
from .share_secret_client import get_secret_manager

_mlflow_client = None

def get_mlflow_client():
    global _mlflow_client
    if _mlflow_client is None:
        tracking_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')

        # Always add credentials from Secrets Manager (ignored if auth not required)
        try:
            secrets = get_secret_manager().get_secret()
            username = secrets.get('MLFLOW_SERVER_USERNAME')
            password = secrets.get('MLFLOW_SERVER_PASSWORD')

            if username and password:
                # Extract protocol and domain/path
                if '://' in tracking_uri:
                    protocol, domain_path = tracking_uri.split('://', 1)
                    tracking_uri = f"{protocol}://{username}:{password}@{domain_path}"
        except Exception as e:
            print(f"Warning: Failed to add MLflow credentials: {e}")

        _mlflow_client = MlflowClient(tracking_uri)
    return _mlflow_client
