# app/config.py
"""Application configuration with environment variable support."""
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Model paths
    MODEL_PATH: str = "artifacts/kmeans_cta_model.pkl"
    SCALER_PATH: str = "artifacts/scaler.pkl"
    METADATA_PATH: str = "artifacts/preprocess_config.json"
    
    # API Configuration
    CORS_ORIGINS: List[str] = ["*"]
    MAX_WORKERS: int = 4
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # Authentication
    AUTH_ENABLED: bool = False
    API_KEYS: List[str] = []
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # MLflow Configuration
    MLFLOW_TRACKING_URI: str = ""
    MLFLOW_EXPERIMENT_NAME: str = "dz-customers-clustering"
    MLFLOW_MODEL_NAME: str = "customer-clustering"
    
    # Feature Flags
    ENABLE_METRICS: bool = True
    ENABLE_DRIFT_DETECTION: bool = True
    
    # Model Monitoring
    DRIFT_DETECTION_THRESHOLD: float = 0.1
    MIN_SAMPLES_FOR_DRIFT: int = 100
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
