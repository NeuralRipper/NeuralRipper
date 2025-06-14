from pydantic import BaseModel
from typing import List


# metric: epoch 1...n
class MetricDetail(BaseModel):
    key: str
    value: float
    timestamp: int
    step: int       # epoch num
    run_id: str


class MetricList(BaseModel):
   metrics: List[MetricDetail]
