from pydantic import BaseModel, Field
from typing import List, Any, Optional

class PredictRequest(BaseModel):
    features: List[float] = Field(..., description="Feature vector for single item")

class BatchPredictRequest(BaseModel):
    features_batch: List[List[float]]

class PredictResponse(BaseModel):
    cluster: Optional[int] = None
    scores: Optional[Any] = None
    meta: Optional[dict] = None

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
