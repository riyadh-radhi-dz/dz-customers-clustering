"""Integration tests for API endpoints."""
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_no_model_loaded(self, api_client):
        """Test health endpoint when model is not loaded."""
        response = api_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
        assert data["status"] == "ok"
        assert data["model_loaded"] is False

    @patch("app.routers.utils_router.ModelLoader")
    def test_health_model_loaded(self, mock_loader_class, api_client):
        """Test health endpoint when model is loaded."""
        mock_loader = MagicMock()
        mock_loader.artifacts = MagicMock()
        mock_loader_class.get_instance.return_value = mock_loader
        
        response = api_client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["model_loaded"] is True


class TestPredictEndpoint:
    """Test prediction endpoint."""

    @patch("app.services.predictor.PredictorService.predict_single")
    @patch("app.routers.utils_router.ModelLoader")
    def test_predict_success(
        self,
        mock_loader_class,
        mock_predict_single,
        api_client,
        sample_customer_data,
    ):
        """Test successful prediction."""
        mock_loader = MagicMock()
        mock_loader.artifacts = MagicMock()
        mock_loader_class.get_instance.return_value = mock_loader
        
        mock_predict_single.return_value = {"cluster": 2}
        
        response = api_client.post("/predict", json=sample_customer_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "cluster" in data
        assert data["cluster"] == 2
        assert "meta" in data

    def test_predict_invalid_data(self, api_client):
        """Test prediction with invalid data."""
        invalid_data = {
            "gender": "M",
            "age": -5,  # Invalid age
        }
        
        response = api_client.post("/predict", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_predict_missing_fields(self, api_client):
        """Test prediction with missing required fields."""
        incomplete_data = {
            "gender": "M",
            # Missing other required fields
        }
        
        response = api_client.post("/predict", json=incomplete_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("app.services.predictor.PredictorService.predict_single")
    def test_predict_model_not_loaded(self, mock_predict_single, api_client, sample_customer_data):
        """Test prediction when model is not loaded."""
        mock_predict_single.side_effect = RuntimeError("Model artifacts not loaded")
        
        response = api_client.post("/predict", json=sample_customer_data)
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    @patch("app.services.predictor.PredictorService.predict_single")
    def test_predict_internal_error(self, mock_predict_single, api_client, sample_customer_data):
        """Test prediction with internal error."""
        mock_predict_single.side_effect = Exception("Internal error")
        
        response = api_client.post("/predict", json=sample_customer_data)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestBatchPredictEndpoint:
    """Test batch prediction endpoint."""

    @patch("app.services.predictor.PredictorService.predict_batch")
    @patch("app.routers.utils_router.ModelLoader")
    def test_batch_predict_success(
        self,
        mock_loader_class,
        mock_predict_batch,
        api_client,
        batch_customer_data,
    ):
        """Test successful batch prediction."""
        mock_loader = MagicMock()
        mock_loader.artifacts = MagicMock()
        mock_loader_class.get_instance.return_value = mock_loader
        
        mock_predict_batch.return_value = [
            {"cluster": 2},
            {"cluster": 1},
        ]
        
        response = api_client.post(
            "/batch_predict",
            json={"customers": batch_customer_data}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_batch_predict_empty_list(self, api_client):
        """Test batch prediction with empty list."""
        response = api_client.post(
            "/batch_predict",
            json={"customers": []}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_batch_predict_invalid_data(self, api_client):
        """Test batch prediction with invalid data."""
        invalid_data = {
            "customers": [
                {"gender": "M", "age": -5}  # Invalid age
            ]
        }
        
        response = api_client.post("/batch_predict", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("app.services.predictor.PredictorService.predict_batch")
    def test_batch_predict_model_not_loaded(
        self, mock_predict_batch, api_client, batch_customer_data
    ):
        """Test batch prediction when model is not loaded."""
        mock_predict_batch.side_effect = RuntimeError("Model artifacts not loaded")
        
        response = api_client.post(
            "/batch_predict",
            json={"customers": batch_customer_data}
        )
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


class TestReloadModelEndpoint:
    """Test model reload endpoint."""

    @patch("app.routers.utils_router.ModelLoader")
    async def test_reload_model_success(self, mock_loader_class, api_client):
        """Test successful model reload."""
        mock_loader = MagicMock()
        mock_loader.reload = MagicMock()
        mock_loader_class.get_instance.return_value = mock_loader
        
        response = api_client.post("/reload_model")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "model reloaded"

    @patch("app.routers.utils_router.ModelLoader")
    async def test_reload_model_error(self, mock_loader_class, api_client):
        """Test model reload with error."""
        mock_loader = MagicMock()
        mock_loader.reload.side_effect = Exception("Reload failed")
        mock_loader_class.get_instance.return_value = mock_loader
        
        response = api_client.post("/reload_model")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root(self, api_client):
        """Test root endpoint."""
        response = api_client.get("/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data

