# app/services/model_loader.py
import asyncio
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

from joblib import load

# Ensure the src/ directory (where dz_customers_clustering lives) is importable.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from dz_customers_clustering.artifacts import PreprocessArtifacts  # noqa: E402

if TYPE_CHECKING:  # pragma: no cover
    from app.config import Settings

logger = logging.getLogger("uvicorn.error")


@dataclass
class LoadedArtifacts:
    model: Any
    scaler: Any
    metadata: PreprocessArtifacts


class ModelLoader:
    """
    Singleton loader that keeps clustering artifacts (model, scaler, metadata) in memory.
    """

    _instance: Optional["ModelLoader"] = None

    def __init__(self) -> None:
        self.artifacts: Optional[LoadedArtifacts] = None
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "ModelLoader":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def load(self, settings: "Settings") -> None:
        async with self._lock:
            if self.artifacts is not None:
                logger.info("Artifacts already loaded, skipping reload.")
                return
            self.artifacts = self._load_from_disk(settings)
            logger.info("Artifacts loaded successfully.")

    def _load_from_disk(self, settings: "Settings") -> LoadedArtifacts:
        model_path = Path(settings.MODEL_PATH)
        scaler_path = Path(settings.SCALER_PATH)
        metadata_path = Path(settings.METADATA_PATH)

        logger.info(
            "Loading artifacts from model=%s, scaler=%s, metadata=%s",
            model_path,
            scaler_path,
            metadata_path,
        )

        model = self._load_joblib(model_path)
        scaler = self._load_joblib(scaler_path)
        metadata_json = metadata_path.read_text(encoding="utf-8")
        metadata = PreprocessArtifacts.from_json(metadata_json)
        return LoadedArtifacts(model=model, scaler=scaler, metadata=metadata)

    @staticmethod
    def _load_joblib(path: Path) -> Any:
        if not path.exists():
            raise FileNotFoundError(f"Artifact not found at {path}")
        return load(path)

    async def reload(self, settings: "Settings") -> None:
        async with self._lock:
            logger.info("Reloading clustering artifacts.")
            self.artifacts = self._load_from_disk(settings)
            logger.info("Artifacts reloaded.")

    async def cleanup(self) -> None:
        async with self._lock:
            logger.info("Cleaning up loaded artifacts.")
            self.artifacts = None

    @property
    def model(self) -> Optional[Any]:
        if self.artifacts is None:
            return None
        return self.artifacts.model

    @property
    def scaler(self) -> Optional[Any]:
        if self.artifacts is None:
            return None
        return self.artifacts.scaler

    @property
    def metadata(self) -> Optional[PreprocessArtifacts]:
        if self.artifacts is None:
            return None
        return self.artifacts.metadata
