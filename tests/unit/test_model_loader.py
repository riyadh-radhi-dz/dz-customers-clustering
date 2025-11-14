"""Unit tests for model loader."""
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from app.services.model_loader import LoadedArtifacts, ModelLoader


class TestModelLoader:
    """Test ModelLoader singleton."""

    def test_singleton_instance(self):
        """Test that ModelLoader is a singleton."""
        loader1 = ModelLoader.get_instance()
        loader2 = ModelLoader.get_instance()
        
        assert loader1 is loader2

    def test_initial_state(self):
        """Test initial state of ModelLoader."""
        ModelLoader._instance = None  # Reset
        loader = ModelLoader.get_instance()
        
        assert loader.artifacts is None
        assert loader.model is None
        assert loader.scaler is None
        assert loader.metadata is None

    @pytest.mark.asyncio
    @patch("app.services.model_loader.load")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    async def test_load_success(
        self,
        mock_read_text,
        mock_exists,
        mock_joblib_load,
        mock_preprocess_artifacts,
    ):
        """Test successful artifact loading."""
        ModelLoader._instance = None  # Reset
        loader = ModelLoader.get_instance()
        
        # Setup mocks
        mock_exists.return_value = True
        mock_joblib_load.side_effect = [
            MagicMock(),  # model
            MagicMock(),  # scaler
        ]
        mock_read_text.return_value = mock_preprocess_artifacts.to_json()
        
        mock_settings = MagicMock()
        mock_settings.MODEL_PATH = "artifacts/model.pkl"
        mock_settings.SCALER_PATH = "artifacts/scaler.pkl"
        mock_settings.METADATA_PATH = "artifacts/metadata.json"
        
        await loader.load(mock_settings)
        
        assert loader.artifacts is not None
        assert loader.model is not None
        assert loader.scaler is not None
        assert loader.metadata is not None

    @pytest.mark.asyncio
    async def test_load_already_loaded(self):
        """Test that load doesn't reload if already loaded."""
        ModelLoader._instance = None  # Reset
        loader = ModelLoader.get_instance()
        
        # Set artifacts
        mock_artifacts = MagicMock()
        loader.artifacts = mock_artifacts
        
        mock_settings = MagicMock()
        
        await loader.load(mock_settings)
        
        # Should still be the same artifacts
        assert loader.artifacts is mock_artifacts

    @pytest.mark.asyncio
    @patch("pathlib.Path.exists")
    async def test_load_file_not_found(self, mock_exists):
        """Test load with missing file."""
        ModelLoader._instance = None  # Reset
        loader = ModelLoader.get_instance()
        
        mock_exists.return_value = False
        
        mock_settings = MagicMock()
        mock_settings.MODEL_PATH = "missing.pkl"
        
        with pytest.raises(FileNotFoundError):
            await loader.load(mock_settings)

    @pytest.mark.asyncio
    @patch("app.services.model_loader.load")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    async def test_reload(
        self,
        mock_read_text,
        mock_exists,
        mock_joblib_load,
        mock_preprocess_artifacts,
    ):
        """Test artifact reloading."""
        ModelLoader._instance = None  # Reset
        loader = ModelLoader.get_instance()
        
        # Setup mocks
        mock_exists.return_value = True
        mock_model_1 = MagicMock()
        mock_model_2 = MagicMock()
        mock_scaler = MagicMock()
        
        mock_joblib_load.side_effect = [
            mock_model_1,
            mock_scaler,
            mock_model_2,
            mock_scaler,
        ]
        mock_read_text.return_value = mock_preprocess_artifacts.to_json()
        
        mock_settings = MagicMock()
        mock_settings.MODEL_PATH = "artifacts/model.pkl"
        mock_settings.SCALER_PATH = "artifacts/scaler.pkl"
        mock_settings.METADATA_PATH = "artifacts/metadata.json"
        
        await loader.load(mock_settings)
        first_model = loader.model
        
        await loader.reload(mock_settings)
        second_model = loader.model
        
        # Models should be different instances
        assert first_model is not second_model

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup."""
        ModelLoader._instance = None  # Reset
        loader = ModelLoader.get_instance()
        
        loader.artifacts = MagicMock()
        
        await loader.cleanup()
        
        assert loader.artifacts is None


class TestLoadedArtifacts:
    """Test LoadedArtifacts dataclass."""

    def test_loaded_artifacts_creation(
        self, mock_model, mock_scaler, mock_preprocess_artifacts
    ):
        """Test creating LoadedArtifacts."""
        artifacts = LoadedArtifacts(
            model=mock_model,
            scaler=mock_scaler,
            metadata=mock_preprocess_artifacts,
        )
        
        assert artifacts.model is mock_model
        assert artifacts.scaler is mock_scaler
        assert artifacts.metadata is mock_preprocess_artifacts

