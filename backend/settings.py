import os

# Read from environment variable, fallback to default, set by docker-compose.yml
MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000')

print(f"Backend using MLflow URI: {MLFLOW_TRACKING_URI}")