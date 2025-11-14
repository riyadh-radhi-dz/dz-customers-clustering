#!/usr/bin/env python3
"""
Enhanced training script with MLflow tracking.

This script wraps the existing training pipeline and adds comprehensive MLflow tracking:
- Logs all hyperparameters
- Tracks training metrics
- Saves model artifacts
- Logs visualizations
- Records cluster statistics
"""

import logging
import os
import sys
import time
from pathlib import Path

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
    DEFAULT_K,
    AUTO_SELECT_K,
    K_RANGE,
    NUMERIC_COLUMNS,
    CATEGORICAL_COLUMNS,
    ensure_directories,
    create_clickhouse_client,
    ping_clickhouse,
    get_data,
    preprocess_data,
    _build_training_matrix,
    find_optimal_k,
    train_model,
    generate_insights,
    save_outputs,
    plot_k_diagnostics,
    plot_cluster_visualizations,
    ARTIFACTS_DIR,
    OUTPUTS_DIR,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_pipeline_with_mlflow(
    mlflow_tracking_uri: str = "http://localhost:5001",
    experiment_name: str = "dz-customers-clustering",
    run_name: str = None,
):
    """
    Run the complete training pipeline with MLflow tracking.
    
    Args:
        mlflow_tracking_uri: MLflow tracking server URI
        experiment_name: Name of the MLflow experiment
        run_name: Optional name for this run
    """
    
    # Initialize MLflow
    if MLFLOW_AVAILABLE:
        mlflow.set_tracking_uri(mlflow_tracking_uri)
        mlflow.set_experiment(experiment_name)
        logger.info(f"📊 MLflow tracking enabled: {mlflow_tracking_uri}")
        logger.info(f"📁 Experiment: {experiment_name}")
    else:
        logger.warning("MLflow not available - running without tracking")
    
    # Start MLflow run
    if MLFLOW_AVAILABLE:
        run_name = run_name or f"training-{int(time.time())}"
        mlflow_run = mlflow.start_run(run_name=run_name)
        run_id = mlflow_run.info.run_id
        logger.info(f"🏃 Started MLflow run: {run_id}")
    else:
        mlflow_run = None
    
    try:
        # === STEP 1: Setup ===
        logger.info("=" * 60)
        logger.info("STEP 1: Setup and Data Extraction")
        logger.info("=" * 60)
        
        start_time = time.time()
        ensure_directories()
        
        # Log hyperparameters
        if MLFLOW_AVAILABLE:
            mlflow.log_params({
                "n_clusters": DEFAULT_K,
                "auto_select_k": AUTO_SELECT_K,
                "k_range_min": min(K_RANGE) if AUTO_SELECT_K else None,
                "k_range_max": max(K_RANGE) if AUTO_SELECT_K else None,
                "algorithm": "k-prototypes",
                "init_method": "Huang",
                "n_init": 2,
                "max_iter": 10,
                "n_jobs": -1,
                "numeric_columns": len(NUMERIC_COLUMNS),
                "categorical_columns": len(CATEGORICAL_COLUMNS),
            })
        
        # === STEP 2: Data Extraction ===
        client = create_clickhouse_client()
        logger.info("🔌 Connecting to ClickHouse...")
        ping_clickhouse(client)
        logger.info("✅ Connection successful")
        
        logger.info("📥 Extracting customer data...")
        raw_df = get_data(client)
        logger.info(f"✅ Fetched {len(raw_df):,} rows and {len(raw_df.columns)} columns")
        
        if MLFLOW_AVAILABLE:
            mlflow.log_metric("raw_data_rows", len(raw_df))
            mlflow.log_metric("raw_data_columns", len(raw_df.columns))
        
        # === STEP 3: Preprocessing ===
        logger.info("=" * 60)
        logger.info("STEP 2: Data Preprocessing")
        logger.info("=" * 60)
        
        preprocess_start = time.time()
        insights_df, feature_df, numeric_scaled, scaler, artifacts = preprocess_data(raw_df)
        data_matrix, categorical_indices = _build_training_matrix(feature_df)
        preprocess_time = time.time() - preprocess_start
        
        logger.info(f"✅ Preprocessing complete in {preprocess_time:.2f}s")
        logger.info(f"   - Insights rows: {len(insights_df):,}")
        logger.info(f"   - Feature matrix shape: {data_matrix.shape}")
        logger.info(f"   - Categorical indices: {categorical_indices}")
        
        if MLFLOW_AVAILABLE:
            mlflow.log_metric("preprocessed_rows", len(insights_df))
            mlflow.log_metric("feature_matrix_rows", data_matrix.shape[0])
            mlflow.log_metric("feature_matrix_cols", data_matrix.shape[1])
            mlflow.log_metric("preprocess_time_seconds", preprocess_time)
        
        # === STEP 4: Model Training ===
        logger.info("=" * 60)
        logger.info("STEP 3: Model Training")
        logger.info("=" * 60)
        
        # K selection
        if AUTO_SELECT_K:
            logger.info("🔍 Running k-selection...")
            diagnostics = find_optimal_k(data_matrix, categorical_indices, K_RANGE)
            if not diagnostics["best_k"]:
                raise RuntimeError("Unable to determine optimal k")
            n_clusters = diagnostics["best_k"]
            logger.info(f"✅ Optimal k selected: {n_clusters}")
            logger.info(f"   Costs evaluated: {list(diagnostics['costs'].keys())}")
            
            if MLFLOW_AVAILABLE:
                for k, cost in diagnostics["costs"].items():
                    mlflow.log_metric(f"k_{k}_cost", cost)
                mlflow.log_metric("optimal_k", n_clusters)
        else:
            diagnostics = None
            n_clusters = DEFAULT_K
            logger.info(f"📌 Using fixed k={n_clusters}")
        
        # Train model
        logger.info(f"🎯 Training K-Prototypes model with k={n_clusters}...")
        train_start = time.time()
        model = train_model(data_matrix, categorical_indices, n_clusters)
        train_time = time.time() - train_start
        
        logger.info(f"✅ Training complete in {train_time:.2f}s")
        logger.info(f"   - Final cost: {model.cost_:.2f}")
        logger.info(f"   - Iterations: {model.n_iter_}")
        
        if MLFLOW_AVAILABLE:
            mlflow.log_metric("train_time_seconds", train_time)
            mlflow.log_metric("final_cost", model.cost_)
            mlflow.log_metric("n_iterations", model.n_iter_)
            mlflow.log_metric("actual_n_clusters", n_clusters)
        
        # === STEP 5: Generate Insights ===
        logger.info("=" * 60)
        logger.info("STEP 4: Cluster Analysis")
        logger.info("=" * 60)
        
        clustered_df = generate_insights(insights_df, model.labels_)
        
        # Calculate cluster statistics
        cluster_sizes = clustered_df.groupby('cluster').size()
        logger.info("\n📊 Cluster Distribution:")
        for cluster_id, size in cluster_sizes.items():
            percentage = (size / len(clustered_df)) * 100
            logger.info(f"   Cluster {cluster_id}: {size:,} customers ({percentage:.1f}%)")
            
            if MLFLOW_AVAILABLE:
                mlflow.log_metric(f"cluster_{cluster_id}_size", size)
                mlflow.log_metric(f"cluster_{cluster_id}_percentage", percentage)
        
        # Calculate average metrics per cluster
        logger.info("\n📈 Cluster Characteristics:")
        cluster_summary = clustered_df.groupby('cluster').agg({
            'age': 'mean',
            'number_of_sessions': 'mean',
            'number_of_successful_orders': 'mean',
            'days_since_first_joined': 'mean',
        }).round(2)
        
        print(cluster_summary)
        
        if MLFLOW_AVAILABLE:
            for cluster_id in cluster_summary.index:
                for col in cluster_summary.columns:
                    value = cluster_summary.loc[cluster_id, col]
                    mlflow.log_metric(f"cluster_{cluster_id}_avg_{col}", value)
        
        # === STEP 6: Save Outputs ===
        logger.info("=" * 60)
        logger.info("STEP 5: Saving Artifacts")
        logger.info("=" * 60)
        
        # Save to artifacts/challenger/ directory (not directly to artifacts/)
        challenger_dir = PROJECT_ROOT / "artifacts" / "challenger"
        challenger_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model artifacts to challenger directory
        from joblib import dump
        dump(model, challenger_dir / "kmeans_cta_model.pkl")
        dump(scaler, challenger_dir / "scaler.pkl")
        (challenger_dir / "preprocess_config.json").write_text(
            artifacts.to_json(),
            encoding="utf-8"
        )
        
        # Also save clustered results
        export_df = clustered_df.copy()
        export_df["cluster"] = model.labels_
        export_df.to_csv(OUTPUTS_DIR / "user_clusters.csv", index=False)
        
        # Generate visualizations
        if diagnostics:
            plot_k_diagnostics(diagnostics["costs"])
        plot_cluster_visualizations(numeric_scaled, model.labels_)
        
        logger.info("✅ Model artifacts saved to ./artifacts/challenger/")
        logger.info("✅ Outputs saved to ./outputs/")
        
        # === STEP 7: Log to MLflow ===
        if MLFLOW_AVAILABLE:
            logger.info("=" * 60)
            logger.info("STEP 6: Logging to MLflow")
            logger.info("=" * 60)
            
            # Add tags to identify this as a CHALLENGER model
            from datetime import datetime
            mlflow.set_tag("model_stage", "challenger")
            mlflow.set_tag("model_status", "pending_validation")
            mlflow.set_tag("training_timestamp", datetime.now().isoformat())
            mlflow.set_tag("saved_to", "artifacts/challenger/")
            
            # Log model
            logger.info("📦 Logging model to MLflow...")
            mlflow.sklearn.log_model(
                model,
                "model",
                registered_model_name="dz-customer-clustering"
            )
            
            # Log scaler
            mlflow.sklearn.log_model(scaler, "scaler")
            
            # Log artifacts from challenger directory
            logger.info("📎 Logging artifacts...")
            mlflow.log_artifact(str(challenger_dir / "kmeans_cta_model.pkl"))
            mlflow.log_artifact(str(challenger_dir / "scaler.pkl"))
            mlflow.log_artifact(str(challenger_dir / "preprocess_config.json"))
            
            # Log visualizations
            logger.info("📊 Logging visualizations...")
            if (OUTPUTS_DIR / "cluster_pca.png").exists():
                mlflow.log_artifact(str(OUTPUTS_DIR / "cluster_pca.png"))
            if (OUTPUTS_DIR / "k_diagnostics.png").exists():
                mlflow.log_artifact(str(OUTPUTS_DIR / "k_diagnostics.png"))
            if (OUTPUTS_DIR / "user_clusters.csv").exists():
                mlflow.log_artifact(str(OUTPUTS_DIR / "user_clusters.csv"))
            
            # Log total time
            total_time = time.time() - start_time
            mlflow.log_metric("total_pipeline_time_seconds", total_time)
            
            logger.info(f"✅ All artifacts logged to MLflow")
            logger.info(f"🏷️  Tagged as: CHALLENGER (pending validation)")
        
        # === STEP 8: Summary ===
        total_time = time.time() - start_time
        logger.info("=" * 60)
        logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Total time: {total_time:.2f}s ({total_time/60:.1f} minutes)")
        logger.info(f"Customers processed: {len(clustered_df):,}")
        logger.info(f"Clusters created: {n_clusters}")
        logger.info(f"Final cost: {model.cost_:.2f}")
        
        if MLFLOW_AVAILABLE:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            logger.info("\n📊 View Results:")
            logger.info(f"   MLflow UI: {mlflow_tracking_uri}")
            logger.info(f"   Run ID: {run_id}")
            logger.info(f"   Direct link: {mlflow_tracking_uri}/#/experiments/{experiment.experiment_id}/runs/{run_id}")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
        if MLFLOW_AVAILABLE and mlflow.active_run():
            mlflow.log_param("status", "failed")
            mlflow.log_param("error", str(e))
        raise
    
    finally:
        # End MLflow run
        if MLFLOW_AVAILABLE and mlflow.active_run():
            mlflow.end_run()
            logger.info("🏁 MLflow run ended")


if __name__ == "__main__":
    # Get MLflow URI from environment or use default
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5001")
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "dz-customers-clustering")
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║   DZ Customers Clustering - Training with MLflow         ║
╚═══════════════════════════════════════════════════════════╝
""")
    
    run_pipeline_with_mlflow(
        mlflow_tracking_uri=mlflow_uri,
        experiment_name=experiment_name,
    )

