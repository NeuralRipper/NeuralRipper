from mlflow import MlflowClient
from mlflow.environment_variables import MLFLOW_TRACKING_URI

from backend.app.schemas.run_response import RunResponse, RunData, RunInfo

client = MlflowClient(MLFLOW_TRACKING_URI.get())


class RunHandler:
    def __init__(self):
        self.__client = MlflowClient(MLFLOW_TRACKING_URI.get())

    def get_run_list(self, eid):
        run_ls = self.__client.search_runs(experiment_ids=eid)

        # Structure must match Nested BaseModel
        return [
            RunResponse(
                data=RunData(
                    metrics=r.data.metrics,
                    params=r.data.params
                ),
                info=RunInfo(
                    artifact_uri=r.info.artifact_uri,
                    end_time=r.info.end_time,
                    experiment_id=r.info.experiment_id,
                    lifecycle_stage=r.info.lifecycle_stage,
                    run_id=r.info.run_id,
                    run_name=r.info.run_name,
                    run_uuid=r.info.run_uuid,
                    start_time=r.info.start_time,
                    status=r.info.status,
                    user_id=r.info.user_id
                )
            )
            for r in run_ls
        ]
