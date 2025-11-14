"""Predictor service with caching and performance optimizations."""
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from app.middleware.metrics import track_prediction, track_prediction_duration
from app.services.cache import get_cache
from app.services.model_loader import LoadedArtifacts, ModelLoader

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from dz_customers_clustering.inference import _prepare_features_from_record  # noqa: E402

logger = logging.getLogger("uvicorn.error")


class PredictorService:
    """Service for making predictions with caching and monitoring."""
    
    @staticmethod
    def _ensure_artifacts() -> LoadedArtifacts:
        """Ensure model artifacts are loaded."""
        loader = ModelLoader.get_instance()
        if loader.artifacts is None:
            raise RuntimeError("Model artifacts not loaded")
        return loader.artifacts

    @staticmethod
    def _predict_from_record(record: Dict[str, Any], use_cache: bool = True) -> Dict[str, Any]:
        """
        Predict cluster for a single record.
        
        Args:
            record: Customer features
            use_cache: Whether to use caching
        
        Returns:
            Prediction result with cluster ID
        """
        # Check cache first
        if use_cache:
            cache = get_cache()
            cached_result = cache.get(record)
            if cached_result is not None:
                logger.debug("Using cached prediction")
                return cached_result
        
        # Start timing
        start_time = time.time()
        
        # Get artifacts
        artifacts = PredictorService._ensure_artifacts()
        metadata = artifacts.metadata
        
        # Prepare features
        numeric_array, categorical_df = _prepare_features_from_record(record, metadata)

        # Scale numeric features
        scaled_numeric = artifacts.scaler.transform(numeric_array)
        scaled_numeric_df = pd.DataFrame(scaled_numeric, columns=metadata.numeric_columns)
        
        # Combine features
        feature_df = scaled_numeric_df.copy()
        for column in metadata.categorical_columns:
            feature_df[column] = categorical_df[column].values

        # Prepare for prediction
        feature_df = feature_df.loc[:, metadata.feature_columns]
        feature_matrix = feature_df.to_numpy()
        categorical_indices = [
            metadata.feature_columns.index(column)
            for column in metadata.categorical_columns
        ]
        
        # Predict
        predicted_cluster = int(
            artifacts.model.predict(feature_matrix, categorical=categorical_indices)[0]
        )
        
        # Track metrics
        duration = time.time() - start_time
        track_prediction(predicted_cluster, "single")
        track_prediction_duration(duration, "single")
        
        logger.debug("Predicted cluster %d in %.3fs", predicted_cluster, duration)
        
        result = {"cluster": predicted_cluster}
        
        # Cache result
        if use_cache:
            cache = get_cache()
            cache.set(record, result)
        
        return result

    @staticmethod
    def predict_single(features: Dict[str, Any], use_cache: bool = True) -> Dict[str, Any]:
        """
        Predict cluster for a single customer.
        
        Args:
            features: Customer features
            use_cache: Whether to use caching
        
        Returns:
            Prediction result
        """
        return PredictorService._predict_from_record(features, use_cache=use_cache)

    @staticmethod
    def predict_batch(
        features_batch: List[Dict[str, Any]], 
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Predict clusters for multiple customers.
        
        Args:
            features_batch: List of customer features
            use_cache: Whether to use caching
        
        Returns:
            List of prediction results
        """
        start_time = time.time()
        results = [
            PredictorService._predict_from_record(record, use_cache=use_cache) 
            for record in features_batch
        ]
        duration = time.time() - start_time
        track_prediction_duration(duration / len(features_batch) if features_batch else 0, "batch")
        
        logger.info("Batch prediction completed: %d records in %.3fs", len(features_batch), duration)
        return results
