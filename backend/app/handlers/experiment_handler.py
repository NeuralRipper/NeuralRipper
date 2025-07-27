from app.utils.share_mlflow_client import get_mlflow_client
from app.schemas.experiment import ExperimentResponse
from app.utils.time_convert import convert

class ExperimentHandler:
    def __init__(self):
        self.__client = get_mlflow_client()  # Shared client

    def get_experiment_list(self):
        """Simple experiment list - no pagination needed for 10-30 experiments"""
        exp_ls = self.__client.search_experiments(
            order_by=["last_update_time DESC"]
        )

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