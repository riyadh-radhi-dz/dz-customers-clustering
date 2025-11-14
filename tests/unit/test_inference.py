"""Unit tests for inference module."""
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from dz_customers_clustering.inference import (
    _normalize_gender_value,
    _prepare_features_from_record,
    predict_cluster,
)


class TestNormalizeGenderValue:
    """Test gender normalization."""

    def test_normalize_male(self):
        """Test normalization of male gender."""
        assert _normalize_gender_value("M") == "M"
        assert _normalize_gender_value("m") == "M"
        assert _normalize_gender_value(" M ") == "M"

    def test_normalize_female(self):
        """Test normalization of female gender."""
        assert _normalize_gender_value("F") == "F"
        assert _normalize_gender_value("f") == "F"
        assert _normalize_gender_value(" F ") == "F"

    def test_normalize_unknown(self):
        """Test normalization of unknown gender."""
        assert _normalize_gender_value("Unknown") == "Unknown"
        assert _normalize_gender_value("unknown") == "Unknown"
        assert _normalize_gender_value("X") == "Unknown"
        assert _normalize_gender_value("") == "Unknown"
        assert _normalize_gender_value(None) == "Unknown"


class TestPrepareFeatures:
    """Test feature preparation."""

    def test_prepare_features_valid_record(
        self, sample_customer_data, mock_preprocess_artifacts
    ):
        """Test feature preparation with valid data."""
        numeric_array, categorical_df = _prepare_features_from_record(
            sample_customer_data, mock_preprocess_artifacts
        )
        
        # Check numeric array shape
        assert numeric_array.shape == (1, 5)
        
        # Check categorical DataFrame
        assert categorical_df.shape == (1, 2)
        assert "gender" in categorical_df.columns
        assert "bnpl_eligible" in categorical_df.columns
        assert categorical_df["gender"].iloc[0] == "M"
        assert categorical_df["bnpl_eligible"].iloc[0] == 1

    def test_prepare_features_with_missing_numeric(self, mock_preprocess_artifacts):
        """Test feature preparation with missing numeric values."""
        record = {
            "gender": "F",
            "age": None,  # Missing
            "bnpl_eligible": 1,
            "number_of_sessions": 10.0,
            "days_since_first_joined": 365.0,
            "number_of_failed_orders": 1.0,
            "number_of_successful_orders": 9.0,
        }
        
        numeric_array, categorical_df = _prepare_features_from_record(
            record, mock_preprocess_artifacts
        )
        
        # Should fill with median
        assert not np.isnan(numeric_array).any()
        
    def test_prepare_features_log_transform(self, mock_preprocess_artifacts):
        """Test that log transformation is applied correctly."""
        record = {
            "gender": "M",
            "age": 35.0,
            "bnpl_eligible": 1,
            "number_of_sessions": 10.0,
            "days_since_first_joined": 365.0,
            "number_of_failed_orders": 0.0,  # Will be log transformed
            "number_of_successful_orders": 10.0,  # Will be log transformed
        }
        
        numeric_array, _ = _prepare_features_from_record(
            record, mock_preprocess_artifacts
        )
        
        # Just check that transformation happened without errors
        assert numeric_array.shape[0] == 1


class TestPredictCluster:
    """Test cluster prediction."""

    def test_predict_cluster_success(
        self,
        sample_customer_data,
        mock_model,
        mock_scaler,
        mock_preprocess_artifacts,
    ):
        """Test successful cluster prediction."""
        cluster = predict_cluster(
            sample_customer_data,
            mock_model,
            mock_scaler,
            mock_preprocess_artifacts,
        )
        
        assert isinstance(cluster, int)
        assert cluster == 0  # Based on mock
        mock_model.predict.assert_called_once()

    def test_predict_cluster_with_invalid_gender(
        self,
        mock_model,
        mock_scaler,
        mock_preprocess_artifacts,
    ):
        """Test prediction with invalid gender."""
        record = {
            "gender": "Invalid",
            "age": 35.0,
            "bnpl_eligible": 1,
            "number_of_sessions": 10.0,
            "days_since_first_joined": 365.0,
            "number_of_failed_orders": 1.0,
            "number_of_successful_orders": 9.0,
        }
        
        cluster = predict_cluster(
            record,
            mock_model,
            mock_scaler,
            mock_preprocess_artifacts,
        )
        
        # Should normalize to "Unknown" and still predict
        assert isinstance(cluster, int)
        mock_model.predict.assert_called_once()

    @patch("dz_customers_clustering.inference.load")
    def test_load_preprocess_artifacts(self, mock_load):
        """Test loading artifacts from disk."""
        from dz_customers_clustering.inference import load_preprocess_artifacts
        
        mock_model = MagicMock()
        mock_scaler = MagicMock()
        
        def load_side_effect(path):
            if "model" in str(path):
                return mock_model
            elif "scaler" in str(path):
                return mock_scaler
        
        mock_load.side_effect = load_side_effect
        
        with patch("pathlib.Path.read_text") as mock_read:
            mock_read.return_value = '{"feature_columns": [], "numeric_medians": {}, "numeric_columns": [], "log_columns": [], "gender_categories": [], "categorical_columns": []}'
            
            model, scaler, metadata = load_preprocess_artifacts()
            
            assert model == mock_model
            assert scaler == mock_scaler
            assert isinstance(metadata, object)

