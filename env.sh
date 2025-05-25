# MLflow Configuration, source env.sh
export MLFLOW_TRACKING_URI="http://localhost:5000"
export MLFLOW_BACKEND_STORE_URI="mysql+pymysql://root@localhost:3306/mlflow"
export MLFLOW_DEFAULT_ARTIFACT_ROOT="gs://neuralripper-mlflow-artifacts/"

echo "MLflow environment loaded - Server: $MLFLOW_TRACKING_URI"