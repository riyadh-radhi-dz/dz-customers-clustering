import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from app.services.model_loader import LoadedArtifacts, ModelLoader

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from dz_customers_clustering.inference import _prepare_features_from_record  # noqa: E402

logger = logging.getLogger("uvicorn.error")


class PredictorService:
    @staticmethod
    def _ensure_artifacts() -> LoadedArtifacts:
        loader = ModelLoader.get_instance()
        if loader.artifacts is None:
            raise RuntimeError("Model artifacts not loaded")
        return loader.artifacts

    @staticmethod
    def _predict_from_record(record: Dict[str, Any]) -> Dict[str, Any]:
        artifacts = PredictorService._ensure_artifacts()
        metadata = artifacts.metadata
        numeric_array, categorical_df = _prepare_features_from_record(record, metadata)

        scaled_numeric = artifacts.scaler.transform(numeric_array)
        scaled_numeric_df = pd.DataFrame(scaled_numeric, columns=metadata.numeric_columns)
        feature_df = scaled_numeric_df.copy()
        for column in metadata.categorical_columns:
            feature_df[column] = categorical_df[column].values

        feature_df = feature_df.loc[:, metadata.feature_columns]
        feature_matrix = feature_df.to_numpy()
        categorical_indices = [
            metadata.feature_columns.index(column)
            for column in metadata.categorical_columns
        ]
        predicted_cluster = int(
            artifacts.model.predict(feature_matrix, categorical=categorical_indices)[0]
        )
        logger.debug("Predicted cluster %d for record.", predicted_cluster)
        return {"cluster": predicted_cluster}

    @staticmethod
    def predict_single(features: Dict[str, Any]) -> Dict[str, Any]:
        return PredictorService._predict_from_record(features)

    @staticmethod
    def predict_batch(features_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [PredictorService._predict_from_record(record) for record in features_batch]
