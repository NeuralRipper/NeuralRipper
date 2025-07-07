from mlflow import MlflowClient
from settings import MLFLOW_TRACKING_URI
from app.schemas.run import RunResponse, RunData, RunInfo


class RunHandler:
    def __init__(self):
        self.__client = MlflowClient(MLFLOW_TRACKING_URI)

    def get_run_list(self, eid):
        run_ls = self.__client.search_runs(experiment_ids=eid)

        # Structure must match Nested BaseModel
        return [
            RunResponse(
                data=RunData(
                    metrics=r.data.metrics,     # direct assignment of dict to BaseModel
                    params=r.data.params        # direct assignment of dict to BaseModel
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

    def get_run_by_id(self, rid):
        return self.__client.get_run(run_id=rid)

    def get_metric_history_by_id(self, rid, key):
        """
        rid: run_id
        key: metric_name
        """
        return self.__client.get_metric_history(run_id=rid, key=key)
