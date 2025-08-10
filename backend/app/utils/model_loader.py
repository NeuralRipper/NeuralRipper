import boto3
from mlflow.tracking import MlflowClient
import dotenv
import os
from pathlib import Path


class ModelLoader:
    def __init__(self):
        # use actual script location to load env variables
        script_dir = Path(__file__).parent      
        dotenv.load_dotenv(script_dir / "../../../.env")

        self.s3_client = boto3.client('s3')
        self.__mlflow_server_username=os.getenv('MLFLOW_SERVER_USERNAME')
        self.__mlflow_server_password=os.getenv('MLFLOW_SERVER_PASSWORD')
        
        # https://username:password@hostname/path
        self.mlflow_client = MlflowClient(f"https://{self.__mlflow_server_username}:{self.__mlflow_server_password}@neuralripper.com/mlflow")

    def get_model_s3_path(self, run_id: str) -> str:
        """
        Get S3 path for the trained model artifacts
        """
        run = self.mlflow_client.get_run(run_id)
        artifact_uri = run.info.artifact_uri
        return f"{artifact_uri}/model/"

    def list_available_models_by_exp(self, exp_name: str = None):
        """
        Show all trained model artifacts
        """
        experiment = self.mlflow_client.get_experiment_by_name(name=exp_name)
        runs = self.mlflow_client.search_runs(experiment.experiment_id)

        return [{
            "run_id": run.info.run_id,
            "model_name": run.data.params.get("model_name", "unknown"),
            "accuracy": run.data.metrics.get("accuracy", 0),
            "path": self.get_model_s3_path(run.info.run_id)
        } for run in runs]
