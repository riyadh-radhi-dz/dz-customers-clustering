"""Unit tests for pipeline module."""
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from dz_customers_clustering.pipeline import (
    _build_training_matrix,
    _calculate_age,
    _days_since_joined,
    _normalize_gender,
    _to_utc_naive,
    find_optimal_k,
    generate_insights,
    preprocess_data,
    train_model,
)


class TestGenderNormalization:
    """Test gender normalization."""

    def test_normalize_gender_male(self):
        """Test normalization of male gender."""
        series = pd.Series(["M", "m", "male", "MALE"])
        result = _normalize_gender(series)
        assert (result == pd.Series(["M", "M", "Unknown", "Unknown"])).all()

    def test_normalize_gender_female(self):
        """Test normalization of female gender."""
        series = pd.Series(["F", "f", "female", "FEMALE"])
        result = _normalize_gender(series)
        assert (result == pd.Series(["F", "F", "Unknown", "Unknown"])).all()

    def test_normalize_gender_unknown(self):
        """Test normalization of unknown gender."""
        series = pd.Series(["Unknown", "unidentified", "X", None, ""])
        result = _normalize_gender(series)
        assert (result == "Unknown").all()


class TestDateUtilities:
    """Test date utility functions."""

    def test_to_utc_naive(self):
        """Test UTC naive conversion."""
        series = pd.Series([
            "2023-01-01 00:00:00",
            "2023-06-15 12:30:00",
        ])
        result = _to_utc_naive(series)
        
        assert result.dt.tz is None
        assert len(result) == 2

    def test_calculate_age(self):
        """Test age calculation."""
        # Create dates that should give known ages
        birth_dates = pd.Series([
            pd.Timestamp.now() - pd.DateOffset(years=30),
            pd.Timestamp.now() - pd.DateOffset(years=25),
        ])
        
        result = _calculate_age(birth_dates)
        
        # Ages should be approximately 30 and 25
        assert 29 < result.iloc[0] < 31
        assert 24 < result.iloc[1] < 26

    def test_calculate_age_with_invalid_date(self):
        """Test age calculation with invalid date."""
        birth_dates = pd.Series([
            pd.Timestamp("1925-01-01"),  # Invalid marker date
            pd.Timestamp("1990-01-01"),
        ])
        
        result = _calculate_age(birth_dates)
        
        # First should be NaN, second should be valid
        assert pd.isna(result.iloc[0])
        assert result.iloc[1] > 0

    def test_days_since_joined(self):
        """Test days since joined calculation."""
        created_at = pd.Series([
            pd.Timestamp.now() - pd.DateOffset(days=365),
            pd.Timestamp.now() - pd.DateOffset(days=180),
        ])
        
        result = _days_since_joined(created_at)
        
        # Should be approximately 365 and 180 days
        assert 364 <= result.iloc[0] <= 366
        assert 179 <= result.iloc[1] <= 181


class TestPreprocessData:
    """Test data preprocessing."""

    def test_preprocess_data_basic(self, sample_dataframe):
        """Test basic preprocessing."""
        insights_df, feature_df, numeric_scaled, scaler, artifacts = preprocess_data(
            sample_dataframe
        )
        
        # Check shapes
        assert len(insights_df) == len(sample_dataframe)
        assert len(feature_df) == len(sample_dataframe)
        
        # Check that numeric data is scaled
        assert numeric_scaled.shape[1] == 5  # 5 numeric columns
        
        # Check artifacts
        assert artifacts.numeric_columns is not None
        assert artifacts.categorical_columns is not None
        assert len(artifacts.numeric_medians) > 0

    def test_preprocess_data_with_nulls(self):
        """Test preprocessing with null values."""
        df = pd.DataFrame({
            "user_id": ["user1", "user2"],
            "gender": ["M", None],
            "age": [35.0, None],
            "bnpl_eligible": [1, None],
            "number_of_sessions": [10.0, None],
            "days_since_first_joined": [365.0, None],
            "number_of_failed_orders": [1.0, None],
            "number_of_successful_orders": [9.0, None],
            "birth_date": pd.to_datetime(["1988-01-01", "1995-06-15"]),
            "system_created_at": pd.to_datetime(["2023-01-01", "2023-06-01"]),
            "customer_id": ["cust1", "cust2"],
        })
        
        insights_df, feature_df, numeric_scaled, scaler, artifacts = preprocess_data(df)
        
        # Should handle nulls without errors
        assert len(insights_df) == 2
        # Numeric columns should be filled
        assert not insights_df[artifacts.numeric_columns].isna().any().any()


class TestBuildTrainingMatrix:
    """Test training matrix construction."""

    def test_build_training_matrix(self, sample_dataframe):
        """Test building training matrix."""
        _, feature_df, _, _, _ = preprocess_data(sample_dataframe)
        
        data_matrix, categorical_indices = _build_training_matrix(feature_df)
        
        assert isinstance(data_matrix, np.ndarray)
        assert isinstance(categorical_indices, list)
        assert len(categorical_indices) == 2  # gender and bnpl_eligible


class TestFindOptimalK:
    """Test optimal k finding."""

    @patch("dz_customers_clustering.pipeline.KPrototypes")
    def test_find_optimal_k(self, mock_kprototypes_class):
        """Test finding optimal k."""
        # Mock the model
        mock_model = MagicMock()
        mock_model.cost_ = 100.0
        mock_kprototypes_class.return_value = mock_model
        
        data_matrix = np.random.rand(100, 7)
        categorical_indices = [5, 6]
        
        result = find_optimal_k(data_matrix, categorical_indices, k_values=range(3, 5))
        
        assert "costs" in result
        assert "best_k" in result
        assert isinstance(result["costs"], dict)
        assert len(result["costs"]) > 0


class TestTrainModel:
    """Test model training."""

    @patch("dz_customers_clustering.pipeline.KPrototypes")
    def test_train_model(self, mock_kprototypes_class):
        """Test model training."""
        mock_model = MagicMock()
        mock_kprototypes_class.return_value = mock_model
        
        data_matrix = np.random.rand(100, 7)
        categorical_indices = [5, 6]
        
        result = train_model(data_matrix, categorical_indices, n_clusters=4)
        
        assert result == mock_model
        mock_model.fit.assert_called_once()


class TestGenerateInsights:
    """Test insight generation."""

    def test_generate_insights(self, sample_dataframe):
        """Test generating cluster insights."""
        insights_df, _, _, _, _ = preprocess_data(sample_dataframe)
        labels = np.array([0, 1, 0])
        
        result_df = generate_insights(insights_df, labels)
        
        assert "cluster" in result_df.columns
        assert len(result_df) == len(insights_df)
        assert (result_df["cluster"] == labels).all()

