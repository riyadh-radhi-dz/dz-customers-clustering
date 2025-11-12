# app/services/model_loader.py
import asyncio
import os
from typing import Any, Optional
import logging

logger = logging.getLogger("uvicorn.error")

class ModelLoader:
    """
    Singleton loader. Keeps a loaded model in memory and exposes inference entrypoints.
    Modify `_load_from_disk` to support other formats (torch, transformers).
    """
    _instance = None

    def __init__(self):
        self.model: Optional[Any] = None
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "ModelLoader":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def load(self, path: str):
        async with self._lock:
            if self.model is not None:
                logger.info("Model already loaded, skipping reload.")
                return
            logger.info("Loading model from %s", path)
            self.model = self._load_from_disk(path)
            logger.info("Model loaded.")

    def _load_from_disk(self, path: str):
        # Example: scikit-learn/joblib; adapt for PyTorch/transformers
        if not os.path.exists(path):
            logger.warning("Model path %s not found — using dummy model", path)
            return DummyModel()

        try:
            import joblib
            model = joblib.load(path)
            return model
        except Exception as e:
            logger.exception("Failed to load model using joblib: %s", e)
            # fallback dummy
            return DummyModel()

    async def reload(self, path: str):
        async with self._lock:
            logger.info("Reloading model from %s", path)
            # drop old model if necessary
            self.model = None
            self.model = self._load_from_disk(path)
            logger.info("Reloaded model.")

    async def cleanup(self):
        async with self._lock:
            logger.info("Cleaning up model references")
            self.model = None

class DummyModel:
    """A tiny fake model to allow local testing while real model path is configured."""
    def predict(self, X):
        # return cluster id 0 for all
        return [0 for _ in X]

    def predict_proba(self, X):
        # fake scores
        return [[1.0] for _ in X]
