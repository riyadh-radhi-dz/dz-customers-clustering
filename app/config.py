# app/config.py
# Use pydantic-settings package for BaseSettings (Pydantic v2.12+)
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    MODEL_PATH: str = "models/customer_clustering.pkl"
    CORS_ORIGINS: List[str] = ["*"]
    MAX_WORKERS: int = 4

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
