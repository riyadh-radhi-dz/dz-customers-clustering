# 📊 MLflow Training & Monitoring Guide

Complete guide for training your model with full MLflow tracking and monitoring.

---

## 🚀 Quick Start

### 1. Ensure Services Are Running

```bash
# Check docker services
docker ps

# Should see:
# - dz-clustering-api
# - dz-mlflow (port 5001)
# - dz-prometheus
# - dz-grafana

# If not running:
make docker-compose
```

### 2. Set Up Environment

```bash
# Create .env file with ClickHouse credentials
cat > .env << 'EOF'
# ClickHouse Configuration
CLICKHOUSE_HOST=your-clickhouse-host.com
CLICKHOUSE_PORT=8443
CLICKHOUSE_USERNAME=your-username
CLICKHOUSE_PASSWORD=your-password
CLICKHOUSE_DATABASE=your-database
CLICKHOUSE_SECURE=true

# MLflow Configuration
MLFLOW_TRACKING_URI=http://localhost:5001
MLFLOW_EXPERIMENT_NAME=dz-customers-clustering
EOF

# Edit with your actual credentials
nano .env
```

### 3. Install MLflow

```bash
# Install mlflow
pip install mlflow

# Or with uv
uv pip install mlflow
```

### 4. Run Training with MLflow

```bash
# Run the enhanced training script
make train-with-mlflow

# Or directly:
python3 scripts/train_with_mlflow.py
```

---

## 📈 What Gets Tracked

The training script automatically logs everything to MLflow:

### Parameters
- `n_clusters`: Number of clusters (7)
- `algorithm`: "k-prototypes"
- `init_method`: "Huang"
- `auto_select_k`: Whether k is auto-selected
- `numeric_columns`: Count of numeric features
- `categorical_columns`: Count of categorical features

### Metrics
- **Data Metrics**:
  - `raw_data_rows`: Number of raw rows
  - `preprocessed_rows`: Rows after preprocessing
  - `feature_matrix_rows/cols`: Final matrix dimensions

- **Training Metrics**:
  - `train_time_seconds`: Training duration
  - `final_cost`: K-Prototypes final cost
  - `n_iterations`: Number of iterations
  - `preprocess_time_seconds`: Preprocessing time
  - `total_pipeline_time_seconds`: End-to-end time

- **Cluster Metrics** (per cluster):
  - `cluster_N_size`: Number of customers
  - `cluster_N_percentage`: Percentage of total
  - `cluster_N_avg_age`: Average age
  - `cluster_N_avg_number_of_sessions`: Average sessions
  - `cluster_N_avg_number_of_successful_orders`: Average orders
  - `cluster_N_avg_days_since_first_joined`: Average tenure

### Artifacts
- **Models**:
  - `kmeans_cta_model.pkl`: Trained K-Prototypes model
  - `scaler.pkl`: StandardScaler for features
  - `preprocess_config.json`: Preprocessing configuration

- **Visualizations**:
  - `cluster_pca.png`: PCA visualization of clusters
  - `k_diagnostics.png`: Elbow plot (if k-selection enabled)

- **Data**:
  - `user_clusters.csv`: Customer assignments

---

## 🔍 Monitoring Training in Real-Time

### View Live Training Logs

```bash
# In one terminal, start training
python3 train_with_mlflow.py

# You'll see detailed progress:
# STEP 1: Setup and Data Extraction
# STEP 2: Data Preprocessing
# STEP 3: Model Training
# STEP 4: Cluster Analysis
# STEP 5: Saving Artifacts
# STEP 6: Logging to MLflow
```

### Monitor in MLflow UI

While training is running:

1. **Open MLflow**: http://localhost:5001
2. **Navigate to experiment**: "dz-customers-clustering"
3. **Watch the run appear** in real-time
4. **Click on the run** to see details updating live

---

## 📊 After Training: Analyze Results

### 1. View in MLflow UI

**Open**: http://localhost:5001

#### View Single Run
- Click on "dz-customers-clustering" experiment
- Click on your training run
- See all parameters, metrics, and artifacts

#### Compare Multiple Runs
- Train the model multiple times with different parameters
- Select multiple runs (checkboxes)
- Click "Compare"
- See side-by-side comparison

### 2. View Metrics in Prometheus

```bash
# Open Prometheus
open http://localhost:9090

# Query metrics:
ml_predictions_total
ml_model_load_time_seconds
http_requests_total
```

### 3. View Dashboards in Grafana

```bash
# Open Grafana (admin/admin)
open http://localhost:3000

# Create dashboard with:
# - Training metrics over time
# - Model performance
# - Cluster distributions
```

---

## 🎯 Advanced: Multiple Training Runs

### Run with Different Parameters

Edit `src/dz_customers_clustering/pipeline.py`:

```python
# Try different k values
DEFAULT_K = 5  # Change from 7 to 5

# Or enable auto k-selection
AUTO_SELECT_K = True
K_RANGE = range(3, 10)
```

Then run:
```bash
python3 train_with_mlflow.py
```

### Batch Training (Testing Multiple Configurations)

```bash
# Create a script to test multiple k values
cat > batch_train.sh << 'EOF'
#!/bin/bash
for k in 5 6 7 8; do
  echo "Training with k=$k"
  # You'd need to modify DEFAULT_K in code
  python3 train_with_mlflow.py
  sleep 5
done
EOF

chmod +x batch_train.sh
./batch_train.sh
```

---

## 📝 Interpreting Results

### Key Metrics to Watch

1. **Final Cost**: Lower is better
   - Measures cluster compactness
   - Compare across runs

2. **Cluster Sizes**: Should be balanced
   - Check `cluster_N_percentage` metrics
   - Avoid clusters with <5% or >50%

3. **Training Time**: Performance indicator
   - Compare `train_time_seconds` across runs
   - Optimize if too slow

4. **Cluster Characteristics**: Business insights
   - Look at `cluster_N_avg_*` metrics
   - Identify customer segments:
     - High-value customers
     - Churn risks
     - Growth opportunities

### Example Interpretation

```
Cluster 0 (23%): Young, new customers
- avg_age: 25
- avg_days_since_joined: 45
- avg_successful_orders: 2

Cluster 1 (18%): High-value customers  
- avg_age: 35
- avg_days_since_joined: 520
- avg_successful_orders: 25

Cluster 2 (31%): Regular customers
- avg_age: 30
- avg_days_since_joined: 280
- avg_successful_orders: 12
```

---

## 🔄 Complete Workflow Example

### End-to-End MLOps Cycle

```bash
# 1. Start services
make docker-compose

# 2. Verify MLflow is accessible
curl http://localhost:5001
# Should return HTML page

# 3. Set up environment
cp .env.example .env
# Edit .env with ClickHouse credentials

# 4. Run training with MLflow
python3 train_with_mlflow.py

# 5. Monitor in MLflow UI
# Open: http://localhost:5001

# 6. Check artifacts were created
ls -la artifacts/
ls -la outputs/

# 7. Test the new model
curl -X POST http://localhost:8000/reload_model

# 8. Make a prediction
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "gender": "M",
    "age": 35,
    "bnpl_eligible": 1,
    "number_of_sessions": 10,
    "days_since_first_joined": 365,
    "number_of_failed_orders": 1,
    "number_of_successful_orders": 9
  }'

# 9. Monitor predictions in Prometheus
curl http://localhost:8000/metrics | grep ml_predictions

# 10. Visualize in Grafana
# Open: http://localhost:3000
```

---

## 🎛️ Configuration Options

### Environment Variables

```bash
# MLflow Configuration
export MLFLOW_TRACKING_URI=http://localhost:5001
export MLFLOW_EXPERIMENT_NAME=my-custom-experiment

# Run training
python3 train_with_mlflow.py
```

### Model Parameters

Edit `src/dz_customers_clustering/pipeline.py`:

```python
# Number of clusters
DEFAULT_K = 7

# Auto k-selection
AUTO_SELECT_K = False  # Set to True to enable
K_RANGE = range(3, 10)  # Range to test

# KPrototypes parameters (in train_model function)
n_init = 2      # Number of initializations
max_iter = 10   # Maximum iterations
```

---

## 📊 Model Registry (Advanced)

### Register Model in MLflow

The training script automatically registers the model as "dz-customer-clustering".

```bash
# View registered models
mlflow models list

# Promote to production
mlflow models transition-stage \
  --model-name dz-customer-clustering \
  --version 1 \
  --stage Production
```

### Load Model from Registry

```python
import mlflow

# Load latest production model
model_uri = "models:/dz-customer-clustering/Production"
model = mlflow.sklearn.load_model(model_uri)
```

---

## 🐛 Troubleshooting

### MLflow Connection Issues

```bash
# Check if MLflow is running
docker ps | grep mlflow

# Check MLflow logs
docker logs dz-mlflow

# Test connection
curl http://localhost:5001/health
```

### Training Fails

```bash
# Check ClickHouse connection
# Verify credentials in .env

# Check logs
tail -f logs/training.log

# Try with verbose logging
PYTHONPATH=. python3 -v train_with_mlflow.py
```

### Artifacts Not Appearing

```bash
# Check directories exist
ls -la artifacts/
ls -la outputs/

# Verify MLflow can access files
docker exec dz-mlflow ls -la /mlflow
```

---

## 📚 Next Steps

1. **Set up automated training**: 
   - GitHub Actions workflow (already configured)
   - Schedule: Weekly retraining

2. **A/B Testing**:
   - Train multiple models
   - Compare in MLflow
   - Deploy best performer

3. **Model Monitoring**:
   - Track prediction accuracy
   - Monitor data drift
   - Alert on performance degradation

4. **Production Deployment**:
   - Deploy to Kubernetes
   - Use model from MLflow registry
   - Implement canary deployment

---

## 🎉 Summary

You now have:
- ✅ Complete training pipeline with MLflow tracking
- ✅ All metrics and artifacts logged automatically
- ✅ Real-time monitoring capabilities
- ✅ Model versioning and registry
- ✅ Comparison tools for multiple runs
- ✅ Production-ready MLOps workflow

**Your MLflow setup is enterprise-grade!** 🚀

