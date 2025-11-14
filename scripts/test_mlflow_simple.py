#!/usr/bin/env python3
"""Simple MLflow test - creates an experiment and logs data."""

import mlflow
import time

# Set tracking URI
mlflow.set_tracking_uri("http://localhost:5001")

print("🚀 Testing MLflow at http://localhost:5001")
print("=" * 50)

# Create or get experiment
experiment_name = "dz-clustering-demo"
try:
    experiment_id = mlflow.create_experiment(experiment_name)
    print(f"✅ Created new experiment: {experiment_name} (ID: {experiment_id})")
except Exception as e:
    experiment = mlflow.get_experiment_by_name(experiment_name)
    experiment_id = experiment.experiment_id if experiment else None
    print(f"📌 Using existing experiment: {experiment_name} (ID: {experiment_id})")

# Set the experiment
mlflow.set_experiment(experiment_name)

# Start a run and log data
print("\n📝 Logging run data...")
with mlflow.start_run(run_name=f"test-run-{int(time.time())}") as run:
    # Log parameters
    mlflow.log_param("n_clusters", 7)
    mlflow.log_param("algorithm", "k-prototypes")
    mlflow.log_param("init_method", "Huang")
    mlflow.log_param("max_iter", 10)
    
    # Log metrics
    mlflow.log_metric("cost", 1234.56)
    mlflow.log_metric("silhouette_score", 0.65)
    mlflow.log_metric("train_time_seconds", 45.2)
    
    # Log additional metrics over "steps"
    for step in range(5):
        mlflow.log_metric("iteration_cost", 1000 - step * 50, step=step)
    
    print(f"✅ Run ID: {run.info.run_id}")
    print(f"✅ Experiment ID: {run.info.experiment_id}")

print("\n🎉 Success! Check MLflow UI:")
print(f"   http://localhost:5001")
print(f"\n📊 Navigate to experiment: {experiment_name}")
print("=" * 50)

