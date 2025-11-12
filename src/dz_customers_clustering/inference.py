from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from joblib import load
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from dz_customers_clustering.artifacts import PreprocessArtifacts

ARTIFACTS_DIR = Path("artifacts")
logger = logging.getLogger(__name__)


def load_preprocess_artifacts() -> tuple[KMeans, StandardScaler, PreprocessArtifacts]:
    """Load persisted model, scaler, and preprocessing metadata."""
    model = load(ARTIFACTS_DIR / "kmeans_cta_model.pkl")
    scaler = load(ARTIFACTS_DIR / "scaler.pkl")
    metadata_json = (ARTIFACTS_DIR / "preprocess_config.json").read_text(encoding="utf-8")
    metadata = PreprocessArtifacts.from_json(metadata_json)
    logger.info("Loaded artifacts from %s", ARTIFACTS_DIR)
    return model, scaler, metadata


def _normalize_gender_value(value: Any) -> str:
    if value is None:
        return "Unknown"
    normalized = str(value).strip().upper()
    if normalized not in {"M", "F"}:
        return "Unknown"
    return normalized


def _prepare_features_from_record(
    record: dict[str, float | int | str],
    metadata: PreprocessArtifacts,
) -> tuple[np.ndarray, pd.DataFrame]:
    sample_df = pd.DataFrame([record])
    sample_df["gender"] = sample_df["gender"].apply(_normalize_gender_value)
    numeric_df = pd.DataFrame()
    for column in metadata.numeric_columns:
        numeric_df[column] = pd.to_numeric(sample_df.get(column), errors="coerce")
        fill_value = metadata.numeric_medians.get(column, 0.0)
        numeric_df[column] = numeric_df[column].fillna(fill_value)

    for column in metadata.log_columns:
        numeric_df[column] = np.log1p(numeric_df[column].clip(lower=0))

    numeric_array = numeric_df[metadata.numeric_columns].to_numpy()
    return numeric_array, sample_df[metadata.categorical_columns]


def predict_cluster(
    sample_record: dict[str, float | int | str] | None = None,
) -> int:
    """Predict a user cluster for a new record."""
    model, scaler, metadata = load_preprocess_artifacts()
    if sample_record is None:
        sample_record = {
            "gender": "Unknown",
            "age": metadata.numeric_medians["age"],
            "bnpl_eligible": 0,
            "number_of_sessions": metadata.numeric_medians["number_of_sessions"],
            "days_since_first_joined": metadata.numeric_medians["days_since_first_joined"],
            "number_of_failed_orders": 0,
            "number_of_successful_orders": metadata.numeric_medians[
                "number_of_successful_orders"
            ],
        }

    numeric_array, categorical_df = _prepare_features_from_record(sample_record, metadata)
    scaled_numeric = scaler.transform(numeric_array)
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
    cluster = int(model.predict(feature_matrix, categorical=categorical_indices)[0])
    logger.info("Sample record predicted to cluster %d", cluster)
    print(f"Sample record assigned to cluster {cluster}")
    return cluster
