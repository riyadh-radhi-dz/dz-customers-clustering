from typing import List, Dict, Any
from app.services.model_loader import ModelLoader
import numpy as np
import logging

logger = logging.getLogger("uvicorn.error")

class PredictorService:
    @staticmethod
    def predict_single(features: List[float]) -> Dict[str, Any]:
        loader = ModelLoader.get_instance()
        model = loader.model
        if model is None:
            raise RuntimeError("Model not loaded")

        X = np.array(features, dtype=float).reshape(1, -1)
        logger.debug("Running predict for input shape %s", X.shape)
        pred = model.predict(X)
        response = {"cluster": int(pred[0])}

        if hasattr(model, "predict_proba"):
            try:
                proba = model.predict_proba(X)
                response["scores"] = proba.tolist()
            except Exception:
                logger.debug("predict_proba failed or not supported")
        return response

    @staticmethod
    def predict_batch(features_batch: List[List[float]]):
        loader = ModelLoader.get_instance()
        model = loader.model
        if model is None:
            raise RuntimeError("Model not loaded")

        X = np.array(features_batch, dtype=float)
        preds = model.predict(X)
        out = []
        for i, p in enumerate(preds):
            entry = {"cluster": int(p)}
            if hasattr(model, "predict_proba"):
                try:
                    entry["scores"] = model.predict_proba(X[i:i+1]).tolist()
                except Exception:
                    pass
            out.append(entry)
        return out
