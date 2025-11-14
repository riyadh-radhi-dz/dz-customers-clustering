"""MLflow integration for model tracking and versioning."""
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MLflowTracker:
    """
    MLflow integration for experiment tracking and model registry.
    
    This class provides methods to:
    - Log experiments and parameters
    - Track metrics
    - Register models
    - Load models from registry
    """
    
    def __init__(self, tracking_uri: str = "", experiment_name: str = "default"):
        """
        Initialize MLflow tracker.
        
        Args:
            tracking_uri: MLflow tracking server URI
            experiment_name: Name of the experiment
        """
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        self._mlflow_available = False
        
        try:
            import mlflow
            self.mlflow = mlflow
            self._mlflow_available = True
            
            if tracking_uri:
                mlflow.set_tracking_uri(tracking_uri)
            
            mlflow.set_experiment(experiment_name)
            logger.info("MLflow initialized with tracking URI: %s", tracking_uri)
        except ImportError:
            logger.warning("MLflow not available. Install with: pip install mlflow")
    
    def start_run(self, run_name: Optional[str] = None) -> Any:
        """Start a new MLflow run."""
        if not self._mlflow_available:
            return None
        return self.mlflow.start_run(run_name=run_name)
    
    def end_run(self):
        """End the current MLflow run."""
        if self._mlflow_available:
            self.mlflow.end_run()
    
    def log_params(self, params: Dict[str, Any]):
        """Log parameters to MLflow."""
        if not self._mlflow_available:
            return
        
        try:
            self.mlflow.log_params(params)
        except Exception as e:
            logger.error("Failed to log params to MLflow: %s", e)
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log metrics to MLflow."""
        if not self._mlflow_available:
            return
        
        try:
            self.mlflow.log_metrics(metrics, step=step)
        except Exception as e:
            logger.error("Failed to log metrics to MLflow: %s", e)
    
    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """Log an artifact to MLflow."""
        if not self._mlflow_available:
            return
        
        try:
            self.mlflow.log_artifact(local_path, artifact_path)
        except Exception as e:
            logger.error("Failed to log artifact to MLflow: %s", e)
    
    def log_model(
        self,
        model: Any,
        artifact_path: str,
        registered_model_name: Optional[str] = None,
        **kwargs
    ):
        """
        Log a model to MLflow.
        
        Args:
            model: Model object to log
            artifact_path: Path within the run to log the model
            registered_model_name: Name for model registry
            **kwargs: Additional arguments for mlflow.sklearn.log_model
        """
        if not self._mlflow_available:
            return
        
        try:
            self.mlflow.sklearn.log_model(
                model,
                artifact_path,
                registered_model_name=registered_model_name,
                **kwargs
            )
            logger.info("Model logged to MLflow: %s", artifact_path)
        except Exception as e:
            logger.error("Failed to log model to MLflow: %s", e)
    
    def load_model(self, model_uri: str) -> Any:
        """
        Load a model from MLflow.
        
        Args:
            model_uri: URI of the model to load (e.g., "models:/model_name/version")
        
        Returns:
            Loaded model
        """
        if not self._mlflow_available:
            return None
        
        try:
            return self.mlflow.sklearn.load_model(model_uri)
        except Exception as e:
            logger.error("Failed to load model from MLflow: %s", e)
            return None
    
    def register_model(self, model_uri: str, name: str) -> Any:
        """
        Register a model in MLflow Model Registry.
        
        Args:
            model_uri: URI of the model run
            name: Name to register the model under
        
        Returns:
            Registered model version
        """
        if not self._mlflow_available:
            return None
        
        try:
            from mlflow.tracking import MlflowClient
            
            client = MlflowClient()
            result = client.create_registered_model(name)
            logger.info("Model registered: %s", name)
            return result
        except Exception as e:
            logger.error("Failed to register model: %s", e)
            return None
    
    def transition_model_stage(
        self,
        name: str,
        version: int,
        stage: str
    ):
        """
        Transition a model to a different stage.
        
        Args:
            name: Registered model name
            version: Model version
            stage: Target stage (Staging, Production, Archived)
        """
        if not self._mlflow_available:
            return
        
        try:
            from mlflow.tracking import MlflowClient
            
            client = MlflowClient()
            client.transition_model_version_stage(
                name=name,
                version=version,
                stage=stage
            )
            logger.info("Model %s version %s transitioned to %s", name, version, stage)
        except Exception as e:
            logger.error("Failed to transition model stage: %s", e)
    
    def log_training_run(
        self,
        model: Any,
        params: Dict[str, Any],
        metrics: Dict[str, float],
        artifacts: Optional[Dict[str, Path]] = None,
        model_name: Optional[str] = None,
    ):
        """
        Log a complete training run.
        
        Args:
            model: Trained model
            params: Training parameters
            metrics: Performance metrics
            artifacts: Additional artifacts to log
            model_name: Name for model registry
        """
        if not self._mlflow_available:
            return
        
        with self.start_run():
            # Log parameters
            self.log_params(params)
            
            # Log metrics
            self.log_metrics(metrics)
            
            # Log artifacts
            if artifacts:
                for name, path in artifacts.items():
                    if path.exists():
                        self.log_artifact(str(path), name)
            
            # Log model
            if model_name:
                self.log_model(
                    model,
                    "model",
                    registered_model_name=model_name
                )
            
            logger.info("Training run logged to MLflow")

