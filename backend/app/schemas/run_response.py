from typing import Optional

from pydantic import BaseModel


class RunMetrics(BaseModel):
    learning_rate: Optional[float] = None
    train_accuracy: Optional[float] = None
    train_loss: Optional[float] = None
    test_accuracy: Optional[float] = None
    test_loss: Optional[float] = None
    val_accuracy: Optional[float] = None
    val_loss: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    tpr: Optional[float] = None  # True Positive Rate
    fpr: Optional[float] = None  # False Positive Rate
    roc_auc: Optional[float] = None  # ROC AUC Score
    auc: Optional[float] = None


class RunParams(BaseModel):
    batch_size: Optional[str] = None
    device: Optional[str] = None
    epochs: Optional[str] = None
    learning_rate: Optional[str] = None
    model: Optional[str] = None
    optimizer: Optional[str] = None
    weight_decay: Optional[str] = None
    dropout: Optional[str] = None
    hidden_size: Optional[str] = None
    num_layers: Optional[str] = None


class RunInfo(BaseModel):
    artifact_uri: Optional[str] = None
    end_time: Optional[int] = None
    experiment_id: Optional[str] = None
    lifecycle_stage: Optional[str] = None
    run_id: Optional[str] = None
    run_name: Optional[str] = None
    run_uuid: Optional[str] = None
    start_time: Optional[int] = None
    status: Optional[str] = None
    user_id: Optional[str] = None


class RunData(BaseModel):
    # One per training, nested with other BaseModel
    metrics: Optional[RunMetrics] = None
    params: Optional[RunParams] = None


class RunResponse(BaseModel):
    """
    RunResponse:
        RunData -> RunMetrics,
                -> RunParams
        RunInfo
    """
    data: RunData
    info: RunInfo
