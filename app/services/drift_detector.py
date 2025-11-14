"""Data drift detection for model monitoring."""
import logging
from collections import deque
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

from app.middleware.metrics import set_data_drift

logger = logging.getLogger(__name__)


class DriftDetector:
    """
    Detects data drift in incoming predictions.
    
    Uses statistical tests to compare incoming data distributions
    with the training data distribution.
    """
    
    def __init__(
        self,
        reference_data: Optional[pd.DataFrame] = None,
        threshold: float = 0.05,
        min_samples: int = 100,
        window_size: int = 1000,
    ):
        """
        Initialize drift detector.
        
        Args:
            reference_data: Reference dataset (training data)
            threshold: P-value threshold for statistical tests
            min_samples: Minimum samples before checking drift
            window_size: Size of rolling window for recent data
        """
        self.reference_data = reference_data
        self.threshold = threshold
        self.min_samples = min_samples
        self.window_size = window_size
        
        # Rolling window of recent predictions
        self.recent_data: deque = deque(maxlen=window_size)
        
        # Reference statistics
        self.reference_stats: Dict[str, Dict[str, float]] = {}
        if reference_data is not None:
            self._compute_reference_stats()
    
    def _compute_reference_stats(self):
        """Compute statistics for reference data."""
        if self.reference_data is None:
            return
        
        for column in self.reference_data.columns:
            if pd.api.types.is_numeric_dtype(self.reference_data[column]):
                self.reference_stats[column] = {
                    "mean": float(self.reference_data[column].mean()),
                    "std": float(self.reference_data[column].std()),
                    "min": float(self.reference_data[column].min()),
                    "max": float(self.reference_data[column].max()),
                    "median": float(self.reference_data[column].median()),
                }
    
    def add_sample(self, sample: Dict[str, Any]):
        """Add a new sample to the rolling window."""
        self.recent_data.append(sample)
    
    def check_drift(self) -> Dict[str, Any]:
        """
        Check for data drift.
        
        Returns:
            Dictionary with drift detection results
        """
        if len(self.recent_data) < self.min_samples:
            return {
                "drift_detected": False,
                "reason": f"Insufficient samples ({len(self.recent_data)} < {self.min_samples})",
                "features": {}
            }
        
        if not self.reference_stats:
            return {
                "drift_detected": False,
                "reason": "No reference data available",
                "features": {}
            }
        
        # Convert recent data to DataFrame
        recent_df = pd.DataFrame(list(self.recent_data))
        
        # Check drift for each feature
        drift_results = {}
        features_with_drift = []
        
        for column in self.reference_stats.keys():
            if column not in recent_df.columns:
                continue
            
            # Perform Kolmogorov-Smirnov test
            recent_values = recent_df[column].dropna()
            reference_values = self.reference_data[column].dropna()
            
            if len(recent_values) < 2 or len(reference_values) < 2:
                continue
            
            try:
                statistic, p_value = stats.ks_2samp(recent_values, reference_values)
                
                drift_detected = p_value < self.threshold
                drift_results[column] = {
                    "drift_detected": drift_detected,
                    "p_value": float(p_value),
                    "statistic": float(statistic),
                    "recent_mean": float(recent_values.mean()),
                    "reference_mean": self.reference_stats[column]["mean"],
                    "recent_std": float(recent_values.std()),
                    "reference_std": self.reference_stats[column]["std"],
                }
                
                if drift_detected:
                    features_with_drift.append(column)
                
                # Update Prometheus metric
                set_data_drift(column, statistic)
                
            except Exception as e:
                logger.error("Error checking drift for column %s: %s", column, e)
        
        drift_detected = len(features_with_drift) > 0
        
        if drift_detected:
            logger.warning(
                "Data drift detected in features: %s",
                ", ".join(features_with_drift)
            )
        
        return {
            "drift_detected": drift_detected,
            "features_with_drift": features_with_drift,
            "features": drift_results,
            "total_samples": len(self.recent_data),
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics for recent data."""
        if not self.recent_data:
            return {"message": "No data available"}
        
        recent_df = pd.DataFrame(list(self.recent_data))
        
        summary = {
            "total_samples": len(self.recent_data),
            "features": {}
        }
        
        for column in recent_df.columns:
            if pd.api.types.is_numeric_dtype(recent_df[column]):
                summary["features"][column] = {
                    "mean": float(recent_df[column].mean()),
                    "std": float(recent_df[column].std()),
                    "min": float(recent_df[column].min()),
                    "max": float(recent_df[column].max()),
                    "median": float(recent_df[column].median()),
                }
        
        return summary
    
    def reset(self):
        """Reset the drift detector."""
        self.recent_data.clear()
        logger.info("Drift detector reset")


# Global drift detector instance
_drift_detector: Optional[DriftDetector] = None


def get_drift_detector() -> Optional[DriftDetector]:
    """Get the global drift detector instance."""
    return _drift_detector


def initialize_drift_detector(
    reference_data: Optional[pd.DataFrame] = None,
    threshold: float = 0.05,
    min_samples: int = 100,
) -> DriftDetector:
    """Initialize the global drift detector."""
    global _drift_detector
    _drift_detector = DriftDetector(
        reference_data=reference_data,
        threshold=threshold,
        min_samples=min_samples,
    )
    logger.info("Drift detector initialized")
    return _drift_detector

