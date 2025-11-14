#!/usr/bin/env python3
"""
Automated Model Validation and Promotion System

This script implements the Champion/Challenger pattern:
1. Train a new model (Challenger)
2. Load the current production model (Champion)
3. Compare performance metrics
4. Promote Challenger to Production if it's better
5. Otherwise, keep Champion

This ensures only better models reach production.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score

# Setup paths
# Script is in scripts/ directory, so go up one level to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

# Import MLflow
try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    print("⚠️  MLflow not available. Run: pip install mlflow")
    MLFLOW_AVAILABLE = False

from dz_customers_clustering.pipeline import (
    ensure_directories,
    create_clickhouse_client,
    ping_clickhouse,
    get_data,
    preprocess_data,
    _build_training_matrix,
    train_model,
    ARTIFACTS_DIR,
    DEFAULT_K,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


class ModelValidator:
    """Validates and compares ML models."""
    
    def __init__(self):
        self.champion_path = ARTIFACTS_DIR / "champion"
        self.challenger_path = ARTIFACTS_DIR / "challenger"
        self.backup_path = ARTIFACTS_DIR / "backup"
        
        # Ensure directories exist
        self.champion_path.mkdir(exist_ok=True)
        self.challenger_path.mkdir(exist_ok=True)
        self.backup_path.mkdir(exist_ok=True)
    
    def calculate_metrics(
        self,
        data_matrix: np.ndarray,
        labels: np.ndarray,
        model_cost: float,
        categorical_indices: list
    ) -> Dict[str, float]:
        """
        Calculate comprehensive model performance metrics.
        
        Args:
            data_matrix: Feature matrix
            labels: Cluster assignments
            model_cost: K-Prototypes cost
            categorical_indices: Indices of categorical features
        
        Returns:
            Dictionary of metrics
        """
        # Extract numeric features only for sklearn metrics
        mask = np.ones(data_matrix.shape[1], dtype=bool)
        mask[categorical_indices] = False
        numeric_data = data_matrix[:, mask]
        
        # Sample data for expensive metrics if dataset is large (>50k samples)
        # Silhouette score has O(n²) complexity and is very slow on large datasets
        max_samples_for_metrics = 50000
        if len(numeric_data) > max_samples_for_metrics:
            logger.info(f"📊 Dataset has {len(numeric_data):,} samples")
            logger.info(f"   Sampling {max_samples_for_metrics:,} for metric calculation (for speed)")
            np.random.seed(42)
            sample_indices = np.random.choice(
                len(numeric_data),
                size=max_samples_for_metrics,
                replace=False
            )
            numeric_data_sampled = numeric_data[sample_indices]
            labels_sampled = labels[sample_indices]
        else:
            numeric_data_sampled = numeric_data
            labels_sampled = labels
        
        try:
            # Silhouette Score (higher is better, range: -1 to 1)
            silhouette = silhouette_score(numeric_data_sampled, labels_sampled, metric='euclidean')
        except Exception as e:
            logger.warning(f"Could not calculate silhouette score: {e}")
            silhouette = 0.0
        
        try:
            # Davies-Bouldin Index (lower is better)
            davies_bouldin = davies_bouldin_score(numeric_data_sampled, labels_sampled)
        except Exception as e:
            logger.warning(f"Could not calculate Davies-Bouldin index: {e}")
            davies_bouldin = float('inf')
        
        try:
            # Calinski-Harabasz Index (higher is better)
            calinski = calinski_harabasz_score(numeric_data_sampled, labels_sampled)
        except Exception as e:
            logger.warning(f"Could not calculate Calinski-Harabasz score: {e}")
            calinski = 0.0
        
        # Cluster balance (standard deviation of cluster sizes)
        cluster_sizes = np.bincount(labels)
        cluster_balance = float(np.std(cluster_sizes) / np.mean(cluster_sizes))
        
        # Composite score (weighted combination)
        # Normalize each metric to 0-1 range
        silhouette_norm = (silhouette + 1) / 2  # -1 to 1 -> 0 to 1
        davies_bouldin_norm = 1 / (1 + davies_bouldin)  # lower is better
        calinski_norm = min(calinski / 10000, 1.0)  # cap at 10000
        balance_norm = 1 / (1 + cluster_balance)  # lower std is better
        
        # Weighted composite score
        composite_score = (
            0.3 * silhouette_norm +
            0.3 * davies_bouldin_norm +
            0.2 * calinski_norm +
            0.2 * balance_norm
        )
        
        return {
            "k_prototypes_cost": float(model_cost),
            "silhouette_score": float(silhouette),
            "davies_bouldin_index": float(davies_bouldin),
            "calinski_harabasz_score": float(calinski),
            "cluster_balance_std": float(cluster_balance),
            "composite_score": float(composite_score),
            "n_clusters": int(len(cluster_sizes)),
            "min_cluster_size": int(cluster_sizes.min()),
            "max_cluster_size": int(cluster_sizes.max()),
            "avg_cluster_size": float(cluster_sizes.mean()),
        }
    
    def compare_models(
        self,
        champion_metrics: Dict[str, float],
        challenger_metrics: Dict[str, float],
        improvement_threshold: float = 0.02  # 2% improvement required
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Compare champion and challenger models.
        
        Args:
            champion_metrics: Current production model metrics
            challenger_metrics: New model metrics
            improvement_threshold: Minimum improvement required (2% by default)
        
        Returns:
            (should_promote, comparison_details)
        """
        logger.info("=" * 60)
        logger.info("MODEL COMPARISON")
        logger.info("=" * 60)
        
        comparison = {
            "champion": champion_metrics,
            "challenger": challenger_metrics,
            "differences": {},
            "improvements": {},
            "decision": "",
            "reason": ""
        }
        
        # Compare key metrics
        logger.info("\n📊 Metric Comparison:")
        logger.info(f"{'Metric':<30} {'Champion':<15} {'Challenger':<15} {'Change':<15}")
        logger.info("-" * 75)
        
        key_metrics = [
            "composite_score",
            "silhouette_score",
            "davies_bouldin_index",
            "k_prototypes_cost",
            "cluster_balance_std"
        ]
        
        for metric in key_metrics:
            champion_val = champion_metrics.get(metric, 0)
            challenger_val = challenger_metrics.get(metric, 0)
            
            if champion_val != 0:
                change_pct = ((challenger_val - champion_val) / abs(champion_val)) * 100
            else:
                change_pct = 0
            
            comparison["differences"][metric] = challenger_val - champion_val
            comparison["improvements"][metric] = change_pct
            
            # Determine if this is an improvement (depends on metric)
            if metric in ["silhouette_score", "composite_score", "calinski_harabasz_score"]:
                is_better = "✅" if challenger_val > champion_val else "❌"
            else:  # davies_bouldin, cost, balance_std (lower is better)
                is_better = "✅" if challenger_val < champion_val else "❌"
            
            logger.info(
                f"{is_better} {metric:<27} "
                f"{champion_val:<15.4f} "
                f"{challenger_val:<15.4f} "
                f"{change_pct:>+14.2f}%"
            )
        
        # Decision based on composite score
        champion_score = champion_metrics.get("composite_score", 0)
        challenger_score = challenger_metrics.get("composite_score", 0)
        
        improvement = ((challenger_score - champion_score) / champion_score) * 100
        
        logger.info("\n" + "=" * 60)
        logger.info("DECISION")
        logger.info("=" * 60)
        
        should_promote = False
        
        if challenger_score > champion_score * (1 + improvement_threshold):
            should_promote = True
            comparison["decision"] = "PROMOTE"
            comparison["reason"] = (
                f"Challenger improved by {improvement:.2f}% "
                f"(threshold: {improvement_threshold*100:.0f}%)"
            )
            logger.info(f"✅ PROMOTE CHALLENGER TO PRODUCTION")
            logger.info(f"   Improvement: {improvement:+.2f}%")
            logger.info(f"   Threshold: {improvement_threshold*100:.0f}%")
        else:
            comparison["decision"] = "KEEP_CHAMPION"
            if improvement > 0:
                comparison["reason"] = (
                    f"Improvement {improvement:.2f}% below threshold "
                    f"({improvement_threshold*100:.0f}%)"
                )
                logger.info(f"⚠️  KEEP CURRENT CHAMPION")
                logger.info(f"   Improvement: {improvement:+.2f}%")
                logger.info(f"   Below threshold: {improvement_threshold*100:.0f}%")
            else:
                comparison["reason"] = f"Challenger performed worse by {improvement:.2f}%"
                logger.info(f"❌ KEEP CURRENT CHAMPION")
                logger.info(f"   Challenger performed worse: {improvement:.2f}%")
        
        logger.info("=" * 60)
        
        return should_promote, comparison
    
    def save_model(self, model, scaler, metadata, destination: Path):
        """Save model artifacts to specified location."""
        from joblib import dump
        
        destination.mkdir(exist_ok=True)
        dump(model, destination / "kmeans_cta_model.pkl")
        dump(scaler, destination / "scaler.pkl")
        (destination / "preprocess_config.json").write_text(
            metadata.to_json(),
            encoding="utf-8"
        )
        logger.info(f"✅ Model saved to {destination}")
    
    def backup_champion(self):
        """Backup current champion before replacement."""
        import shutil
        from datetime import datetime
        
        if (self.champion_path / "kmeans_cta_model.pkl").exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.backup_path / f"champion_{timestamp}"
            backup_dir.mkdir(exist_ok=True)
            
            for file in self.champion_path.glob("*"):
                if file.is_file():
                    shutil.copy2(file, backup_dir)
            
            logger.info(f"✅ Champion backed up to {backup_dir}")
    
    def promote_challenger(self):
        """Promote challenger to champion."""
        import shutil
        
        # Backup current champion
        self.backup_champion()
        
        # Copy challenger to champion
        for file in self.challenger_path.glob("*"):
            if file.is_file():
                shutil.copy2(file, self.champion_path)
        
        # Also update the main artifacts directory (for API)
        for file in self.challenger_path.glob("*"):
            if file.is_file():
                shutil.copy2(file, ARTIFACTS_DIR)
        
        logger.info(f"✅ Challenger promoted to Champion")


def run_validation_pipeline(
    mlflow_tracking_uri: str = "http://localhost:5001",
    experiment_name: str = "dz-customers-clustering",
    improvement_threshold: float = 0.02
):
    """
    Complete model validation and promotion pipeline.
    
    Args:
        mlflow_tracking_uri: MLflow server URI
        experiment_name: MLflow experiment name
        improvement_threshold: Minimum improvement to promote (default: 2%)
    """
    print("""
╔═══════════════════════════════════════════════════════════╗
║   Model Validation & Promotion Pipeline                  ║
║   Champion vs Challenger                                  ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    validator = ModelValidator()
    
    # Initialize MLflow
    if MLFLOW_AVAILABLE:
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        mlflow.set_experiment(experiment_name)
        mlflow_run = mlflow.start_run(run_name=f"validation-{int(time.time())}")
    
    try:
        # === STEP 1: Load Champion Model ===
        logger.info("=" * 60)
        logger.info("STEP 1: Load Champion Model")
        logger.info("=" * 60)
        
        champion_exists = (validator.champion_path / "kmeans_cta_model.pkl").exists()
        
        if not champion_exists:
            logger.warning("⚠️  No champion model found. First run will become champion.")
            champion_metrics = None
        else:
            from joblib import load
            from dz_customers_clustering.artifacts import PreprocessArtifacts
            
            champion_model = load(validator.champion_path / "kmeans_cta_model.pkl")
            champion_metadata = PreprocessArtifacts.from_json(
                (validator.champion_path / "preprocess_config.json").read_text()
            )
            logger.info("✅ Champion model loaded")
        
        # === STEP 2: Train Challenger Model ===
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: Train Challenger Model")
        logger.info("=" * 60)
        
        ensure_directories()
        client = create_clickhouse_client()
        ping_clickhouse(client)
        
        logger.info("📥 Fetching data...")
        raw_df = get_data(client)
        logger.info(f"✅ Fetched {len(raw_df):,} rows")
        
        logger.info("🔄 Preprocessing...")
        insights_df, feature_df, numeric_scaled, scaler, metadata = preprocess_data(raw_df)
        data_matrix, categorical_indices = _build_training_matrix(feature_df)
        
        logger.info("🎯 Training challenger model...")
        train_start = time.time()
        challenger_model = train_model(data_matrix, categorical_indices, DEFAULT_K)
        train_time = time.time() - train_start
        
        logger.info(f"✅ Challenger trained in {train_time:.2f}s")
        logger.info(f"   Cost: {challenger_model.cost_:.2f}")
        
        # Calculate challenger metrics
        logger.info("📊 Calculating challenger metrics...")
        challenger_metrics = validator.calculate_metrics(
            data_matrix,
            challenger_model.labels_,
            challenger_model.cost_,
            categorical_indices
        )
        
        # Save challenger
        validator.save_model(
            challenger_model,
            scaler,
            metadata,
            validator.challenger_path
        )
        
        # === STEP 3: Compare Models ===
        if champion_exists:
            logger.info("\n" + "=" * 60)
            logger.info("STEP 3: Evaluate Champion Model on New Data")
            logger.info("=" * 60)
            
            # Evaluate champion on same data for fair comparison
            champion_predictions = champion_model.predict(
                data_matrix,
                categorical=categorical_indices
            )
            
            logger.info("📊 Calculating champion metrics...")
            champion_metrics = validator.calculate_metrics(
                data_matrix,
                champion_predictions,
                champion_model.cost_,
                categorical_indices
            )
            
            # Compare
            should_promote, comparison = validator.compare_models(
                champion_metrics,
                challenger_metrics,
                improvement_threshold
            )
            
            # Log to MLflow
            if MLFLOW_AVAILABLE:
                from datetime import datetime
                
                mlflow.log_param("has_champion", True)
                mlflow.log_param("improvement_threshold", improvement_threshold)
                
                for key, value in challenger_metrics.items():
                    mlflow.log_metric(f"challenger_{key}", value)
                for key, value in champion_metrics.items():
                    mlflow.log_metric(f"champion_{key}", value)
                
                mlflow.log_metric("composite_improvement_pct", 
                    comparison["improvements"]["composite_score"])
                mlflow.log_param("decision", comparison["decision"])
                mlflow.log_param("reason", comparison["reason"])
                
                # Add tags for easy filtering
                mlflow.set_tag("pipeline_type", "validation")
                mlflow.set_tag("validation_timestamp", datetime.now().isoformat())
            
            # === STEP 4: Promotion Decision ===
            logger.info("\n" + "=" * 60)
            logger.info("STEP 4: Promotion Decision")
            logger.info("=" * 60)
            
            if should_promote:
                logger.info("🏆 Promoting challenger to production...")
                validator.promote_challenger()
                logger.info("✅ NEW MODEL IN PRODUCTION")
                
                # Save comparison report
                report_path = ARTIFACTS_DIR / "promotion_report.json"
                with open(report_path, 'w') as f:
                    json.dump(comparison, f, indent=2)
                logger.info(f"📄 Report saved: {report_path}")
                
                if MLFLOW_AVAILABLE:
                    mlflow.set_tag("model_stage", "champion")
                    mlflow.set_tag("model_status", "promoted_to_production")
                    mlflow.set_tag("promotion_timestamp", datetime.now().isoformat())
                
                result = "PROMOTED"
            else:
                logger.info("🛡️  Keeping current champion...")
                logger.info("✅ CHAMPION RETAINED")
                
                if MLFLOW_AVAILABLE:
                    mlflow.set_tag("model_stage", "challenger")
                    mlflow.set_tag("model_status", "rejected")
                    mlflow.set_tag("rejection_reason", comparison["reason"])
                
                result = "RETAINED"
        
        else:
            # First run - automatically promote
            logger.info("\n" + "=" * 60)
            logger.info("STEP 3: First Run - Auto Promotion")
            logger.info("=" * 60)
            
            logger.info("🏆 No champion exists. Promoting challenger...")
            validator.promote_challenger()
            logger.info("✅ FIRST MODEL DEPLOYED")
            
            if MLFLOW_AVAILABLE:
                from datetime import datetime
                
                mlflow.log_param("has_champion", False)
                for key, value in challenger_metrics.items():
                    mlflow.log_metric(f"challenger_{key}", value)
                mlflow.log_param("decision", "PROMOTED")
                mlflow.log_param("reason", "First model deployment")
                
                # Add tags for first deployment
                mlflow.set_tag("pipeline_type", "validation")
                mlflow.set_tag("model_stage", "champion")
                mlflow.set_tag("model_status", "first_deployment")
                mlflow.set_tag("promotion_timestamp", datetime.now().isoformat())
            
            result = "FIRST_DEPLOYMENT"
        
        # === FINAL SUMMARY ===
        logger.info("\n" + "=" * 60)
        logger.info("🎉 VALIDATION PIPELINE COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Result: {result}")
        logger.info(f"Champion path: {validator.champion_path}")
        logger.info(f"Production artifacts: {ARTIFACTS_DIR}")
        
        if MLFLOW_AVAILABLE:
            logger.info(f"\n📊 MLflow: {mlflow_tracking_uri}")
            logger.info(f"Run ID: {mlflow_run.info.run_id}")
        
        logger.info("=" * 60)
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
        if MLFLOW_AVAILABLE:
            mlflow.log_param("status", "failed")
            mlflow.log_param("error", str(e))
        raise
    
    finally:
        if MLFLOW_AVAILABLE and mlflow.active_run():
            mlflow.end_run()


if __name__ == "__main__":
    # Configuration
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "dz-customers-clustering")
    
    # Improvement threshold (2% by default)
    # Can be configured via environment variable
    threshold = float(os.getenv("MODEL_IMPROVEMENT_THRESHOLD", "0.02"))
    
    run_validation_pipeline(
        mlflow_tracking_uri=mlflow_uri,
        experiment_name=experiment_name,
        improvement_threshold=threshold
    )

