from app.utils.share_mlflow_client import get_mlflow_client
from mlflow.entities import ViewType
from app.schemas.metric import MetricDetail
from app.schemas.run import RunResponse, RunData, RunInfo

class RunHandler:
    def __init__(self):
        self.__client = get_mlflow_client()

    def get_run_list(self, eid):
        run_ls = self.__client.search_runs(
            experiment_ids=[eid],
            run_view_type=ViewType.ACTIVE_ONLY,
            order_by=["start_time DESC"]
        )
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
                    start_time=r.info.start_time,
                    status=r.info.status,
                    user_id=r.info.user_id
                )
            )
            for r in run_ls
        ]

    def get_run_by_id(self, rid):
        return self.__client.get_run(run_id=rid)

    def get_metric_names(self, rid: str):
        """Fast: Just get metric names and final values"""
        try:
            run = self.get_run_by_id(rid)
            return {
                "metric_names": list(run.data.metrics.keys()),
                "final_values": run.data.metrics
            }
        except Exception as e:
            print(f"Error fetching metric names: {e}")
            return {"metric_names": [], "final_values": {}}

    def get_single_metric(self, rid: str, metric_name: str):
        """Get single metric history with sampling"""
        try:
            metric_history = self.__client.get_metric_history(run_id=rid, key=metric_name)
            
            return [
                MetricDetail(
                    key=metric_name,
                    value=point.value,
                    timestamp=point.timestamp,
                    step=point.step,
                    run_id=rid
                )
                for point in metric_history
            ]
        except Exception as e:
            print(f"Error fetching {metric_name}: {e}")
            return []
