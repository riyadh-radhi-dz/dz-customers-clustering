"""Unit tests for predictor service."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.predictor import PredictorService


class TestPredictorService:
    """Test PredictorService."""

    @patch("app.services.predictor.ModelLoader")
    @patch("app.services.predictor._prepare_features_from_record")
    def test_predict_single_success(
        self,
        mock_prepare_features,
        mock_loader_class,
        sample_customer_data,
        mock_model,
        mock_scaler,
        mock_preprocess_artifacts,
    ):
        """Test successful single prediction."""
        # Setup mocks
        mock_loader = MagicMock()
        mock_artifacts = MagicMock()
        mock_artifacts.model = mock_model
        mock_artifacts.scaler = mock_scaler
        mock_artifacts.metadata = mock_preprocess_artifacts
        mock_loader.artifacts = mock_artifacts
        mock_loader_class.get_instance.return_value = mock_loader
        
        import pandas as pd
        import numpy as np
        mock_prepare_features.return_value = (
            np.random.rand(1, 5),
            pd.DataFrame({"gender": ["M"], "bnpl_eligible": [1]})
        )
        
        result = PredictorService.predict_single(sample_customer_data)
        
        assert "cluster" in result
        assert isinstance(result["cluster"], int)

    @patch("app.services.predictor.ModelLoader")
    def test_predict_single_no_artifacts(
        self, mock_loader_class, sample_customer_data
    ):
        """Test prediction when artifacts are not loaded."""
        mock_loader = MagicMock()
        mock_loader.artifacts = None
        mock_loader_class.get_instance.return_value = mock_loader
        
        with pytest.raises(RuntimeError, match="Model artifacts not loaded"):
            PredictorService.predict_single(sample_customer_data)

    @patch("app.services.predictor.ModelLoader")
    @patch("app.services.predictor._prepare_features_from_record")
    def test_predict_batch_success(
        self,
        mock_prepare_features,
        mock_loader_class,
        batch_customer_data,
        mock_model,
        mock_scaler,
        mock_preprocess_artifacts,
    ):
        """Test successful batch prediction."""
        # Setup mocks
        mock_loader = MagicMock()
        mock_artifacts = MagicMock()
        mock_artifacts.model = mock_model
        mock_artifacts.scaler = mock_scaler
        mock_artifacts.metadata = mock_preprocess_artifacts
        mock_loader.artifacts = mock_artifacts
        mock_loader_class.get_instance.return_value = mock_loader
        
        import pandas as pd
        import numpy as np
        mock_prepare_features.return_value = (
            np.random.rand(1, 5),
            pd.DataFrame({"gender": ["M"], "bnpl_eligible": [1]})
        )
        
        result = PredictorService.predict_batch(batch_customer_data)
        
        assert isinstance(result, list)
        assert len(result) == len(batch_customer_data)
        for item in result:
            assert "cluster" in item
            assert isinstance(item["cluster"], int)

    @patch("app.services.predictor.ModelLoader")
    def test_ensure_artifacts_success(
        self, mock_loader_class, mock_preprocess_artifacts
    ):
        """Test _ensure_artifacts when artifacts are loaded."""
        mock_loader = MagicMock()
        mock_artifacts = MagicMock()
        mock_loader.artifacts = mock_artifacts
        mock_loader_class.get_instance.return_value = mock_loader
        
        result = PredictorService._ensure_artifacts()
        
        assert result == mock_artifacts

    @patch("app.services.predictor.ModelLoader")
    def test_ensure_artifacts_failure(self, mock_loader_class):
        """Test _ensure_artifacts when artifacts are not loaded."""
        mock_loader = MagicMock()
        mock_loader.artifacts = None
        mock_loader_class.get_instance.return_value = mock_loader
        
        with pytest.raises(RuntimeError, match="Model artifacts not loaded"):
            PredictorService._ensure_artifacts()

