from mlflow import MlflowClient
# all the mlflow variables are well defined, use get() and it reads env or default
from mlflow.environment_variables import MLFLOW_TRACKING_URI

from backend.app.schemas.experiment import ExperimentResponse
from backend.app.utils.time_convert import convert


class ExperimentHandler:
    def __init__(self):
        self.__client = MlflowClient(MLFLOW_TRACKING_URI.get())

    def get_experiment_list(self):
        exp_ls = self.__client.search_experiments()

        # wrap up with basemodel for fastapi
        return [
            ExperimentResponse(
                id=exp.experiment_id,
                name=exp.name,
                artifact_location=exp.artifact_location,
                lifecycle_stage=exp.lifecycle_stage,
                tags=exp.tags,
                creation_time=convert(exp.creation_time),
                last_update_time=convert(exp.last_update_time)
            )
            for exp in exp_ls
        ]

    def get_experiment_by_id(self, eid):
        return self.__client.get_experiment(experiment_id=eid)
