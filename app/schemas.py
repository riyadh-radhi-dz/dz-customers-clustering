from typing import Any, List, Optional

from pydantic import BaseModel, Field


class CustomerFeatures(BaseModel):
    gender: str = Field(..., description="Gender code such as 'M', 'F', or 'Unknown'")
    age: float = Field(..., ge=0, description="Age in years")
    bnpl_eligible: int = Field(..., ge=0, le=1, description="1 if BNPL eligible else 0")
    number_of_sessions: float = Field(..., ge=0, description="Total number of sessions")
    days_since_first_joined: float = Field(..., ge=0, description="Days since first joined")
    number_of_failed_orders: float = Field(..., ge=0, description="Failed orders count")
    number_of_successful_orders: float = Field(..., ge=0, description="Successful orders count")


class PredictRequest(CustomerFeatures):
    """Single-customer prediction request."""


class BatchPredictRequest(BaseModel):
    customers: List[CustomerFeatures]

class PredictResponse(BaseModel):
    cluster: Optional[int] = None
    scores: Optional[Any] = None
    meta: Optional[dict] = None

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
