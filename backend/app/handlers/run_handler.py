from mlflow import MlflowClient
from settings import MLFLOW_TRACKING_URI
from app.schemas.metric import MetricList, MetricDetail
from app.schemas.run import RunResponse, RunData, RunInfo
from mlflow.entities import ViewType


class RunHandler:
    def __init__(self):
        self.__client = MlflowClient(MLFLOW_TRACKING_URI)

    def get_run_list(self, eid):
        """Get runs with backend sorting"""
        run_ls = self.__client.search_runs(
            experiment_ids=[eid],
            run_view_type=ViewType.ACTIVE_ONLY,
            order_by=["start_time DESC"]
        )

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
                    start_time=r.info.start_time,
                    status=r.info.status,
                    user_id=r.info.user_id
                )
            )
            for r in run_ls
        ]

    def get_run_by_id(self, rid):
        return self.__client.get_run(run_id=rid)

    def get_metrics_by_id(self, rid: str):
        """OPTIMIZED: Batch metrics with sampling"""
        try:
            run = self.get_run_by_id(rid)
            metric_names = list(run.data.metrics.keys())
            
            if not metric_names:
                return MetricList(metrics=[])

            all_metrics = []
            for metric_name in metric_names:
                # Get metric history
                metric_history = self.__client.get_metric_history(run_id=rid, key=metric_name)
                
                # Convert to MetricDetail
                for metric_point in metric_history:
                    all_metrics.append(MetricDetail(
                        key=metric_name,
                        value=metric_point.value,
                        timestamp=metric_point.timestamp,
                        step=metric_point.step,
                        run_id=rid
                    ))

            return MetricList(metrics=all_metrics)
        except Exception as e:
            print(f"Error fetching metrics for {rid}: {e}")
            return MetricList(metrics=[])