from mlflow import MlflowClient

# all the mlflow variables are well defined, use get() and it reads env or default
from mlflow.environment_variables import MLFLOW_TRACKING_URI


class ExperimentHandler:
    def __init__(self):
        self.__client = MlflowClient(MLFLOW_TRACKING_URI.get())

    def get_experiment_list(self):
        return self.__client.search_experiments()

    def get_experiment_by_id(self):
        # TODO: get exp by id
        pass



