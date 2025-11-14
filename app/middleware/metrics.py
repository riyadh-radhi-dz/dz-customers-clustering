"""Prometheus metrics middleware."""
import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse


# Define metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

REQUEST_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint"]
)

PREDICTION_COUNT = Counter(
    "ml_predictions_total",
    "Total ML predictions",
    ["cluster", "prediction_type"]
)

PREDICTION_DURATION = Histogram(
    "ml_prediction_duration_seconds",
    "ML prediction duration in seconds",
    ["prediction_type"]
)

MODEL_LOAD_TIME = Gauge(
    "ml_model_load_time_seconds",
    "Time taken to load ML model"
)

MODEL_INFO = Gauge(
    "ml_model_info",
    "ML model information",
    ["model_version", "model_type"]
)

DATA_DRIFT_SCORE = Gauge(
    "ml_data_drift_score",
    "Data drift score",
    ["feature"]
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting Prometheus metrics."""
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Collect metrics for each request."""
        method = request.method
        endpoint = request.url.path
        
        # Track in-progress requests
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
        
        # Start timer
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Record duration
            duration = time.time() - start_time
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
            
            # Record request count
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=response.status_code
            ).inc()
            
            return response
            
        finally:
            # Decrement in-progress requests
            REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()


async def metrics_endpoint(request: Request) -> StarletteResponse:
    """Expose Prometheus metrics."""
    return StarletteResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


def track_prediction(cluster: int, prediction_type: str = "single") -> None:
    """Track a prediction in metrics."""
    PREDICTION_COUNT.labels(
        cluster=str(cluster),
        prediction_type=prediction_type
    ).inc()


def track_prediction_duration(duration: float, prediction_type: str = "single") -> None:
    """Track prediction duration."""
    PREDICTION_DURATION.labels(prediction_type=prediction_type).observe(duration)


def set_model_load_time(duration: float) -> None:
    """Set model load time metric."""
    MODEL_LOAD_TIME.set(duration)


def set_model_info(version: str, model_type: str) -> None:
    """Set model information metric."""
    MODEL_INFO.labels(model_version=version, model_type=model_type).set(1)


def set_data_drift(feature: str, score: float) -> None:
    """Set data drift score for a feature."""
    DATA_DRIFT_SCORE.labels(feature=feature).set(score)

