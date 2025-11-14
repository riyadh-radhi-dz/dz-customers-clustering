"""Unit tests for artifacts module."""
import json

import pytest

from dz_customers_clustering.artifacts import PreprocessArtifacts


class TestPreprocessArtifacts:
    """Test PreprocessArtifacts dataclass."""

    def test_to_json(self, mock_preprocess_artifacts):
        """Test serialization to JSON."""
        json_str = mock_preprocess_artifacts.to_json()
        assert isinstance(json_str, str)
        
        # Verify it's valid JSON
        data = json.loads(json_str)
        assert "feature_columns" in data
        assert "numeric_medians" in data
        assert "numeric_columns" in data
        assert "log_columns" in data
        assert "gender_categories" in data
        assert "categorical_columns" in data

    def test_from_json(self, mock_preprocess_artifacts):
        """Test deserialization from JSON."""
        json_str = mock_preprocess_artifacts.to_json()
        reconstructed = PreprocessArtifacts.from_json(json_str)
        
        assert reconstructed.feature_columns == mock_preprocess_artifacts.feature_columns
        assert reconstructed.numeric_medians == mock_preprocess_artifacts.numeric_medians
        assert reconstructed.numeric_columns == mock_preprocess_artifacts.numeric_columns
        assert reconstructed.log_columns == mock_preprocess_artifacts.log_columns
        assert reconstructed.gender_categories == mock_preprocess_artifacts.gender_categories
        assert reconstructed.categorical_columns == mock_preprocess_artifacts.categorical_columns

    def test_roundtrip_serialization(self, mock_preprocess_artifacts):
        """Test that serialization and deserialization are inverses."""
        json_str = mock_preprocess_artifacts.to_json()
        reconstructed = PreprocessArtifacts.from_json(json_str)
        json_str_2 = reconstructed.to_json()
        
        assert json_str == json_str_2

    def test_from_json_missing_categorical_columns(self):
        """Test backward compatibility when categorical_columns is missing."""
        data = {
            "feature_columns": ["col1", "col2"],
            "numeric_medians": {"col1": 1.0},
            "numeric_columns": ["col1"],
            "log_columns": ["col1"],
            "gender_categories": ["M", "F"],
        }
        json_str = json.dumps(data)
        
        artifacts = PreprocessArtifacts.from_json(json_str)
        assert artifacts.categorical_columns == []

