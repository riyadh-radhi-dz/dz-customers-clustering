# app/config.py
# Use pydantic-settings package for BaseSettings (Pydantic v2.12+)
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    MODEL_PATH: str = "artifacts/kmeans_cta_model.pkl"
    SCALER_PATH: str = "artifacts/scaler.pkl"
    METADATA_PATH: str = "artifacts/preprocess_config.json"
    CORS_ORIGINS: List[str] = ["*"]
    MAX_WORKERS: int = 4

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
