# 🚀 Quick Start: Train Model with MLflow

## 📋 Prerequisites
- ✅ Docker services running (`make docker-compose`)
- ✅ MLflow accessible at http://localhost:5001
- ✅ ClickHouse credentials in `.env` file

---

## ⚡ 3-Step Training

### Step 1: Set Up Environment
```bash
# Copy and edit .env file
cp .env.example .env
nano .env

# Add your ClickHouse credentials:
# CLICKHOUSE_HOST=your-host
# CLICKHOUSE_USERNAME=your-username
# CLICKHOUSE_PASSWORD=your-password
# CLICKHOUSE_DATABASE=your-database
```

### Step 2: Run Training
```bash
# Install MLflow (if not already)
pip install mlflow

# Run training with full MLflow tracking
python3 scripts/train_with_mlflow.py

# Or use Make command
make train-with-mlflow
```

### Step 3: View Results
```bash
# Open MLflow UI
open http://localhost:5001

# Click on "dz-customers-clustering" experiment
# See your training run with all metrics and artifacts
```

---

## 📊 What You'll See in MLflow

### Run Information
- **Parameters**: n_clusters, algorithm, features used
- **Metrics**: Training time, model cost, cluster sizes
- **Artifacts**: Model files, visualizations, data exports

### Direct Links After Training
The script will output direct links like:
```
📊 View Results:
   MLflow UI: http://localhost:5001
   Run ID: abc123...
   Direct link: http://localhost:5001/#/experiments/123/runs/abc123
```

---

## 🎯 During Training

You'll see 6 steps with detailed logging:

```
STEP 1: Setup and Data Extraction
  ✅ Connected to ClickHouse
  ✅ Fetched X,XXX rows

STEP 2: Data Preprocessing  
  ✅ Preprocessing complete in X.XXs
  ✅ Feature matrix shape: (X, Y)

STEP 3: Model Training
  ✅ Training complete in X.XXs
  ✅ Final cost: XXX.XX

STEP 4: Cluster Analysis
  📊 Cluster Distribution:
     Cluster 0: X,XXX customers (XX.X%)
     Cluster 1: X,XXX customers (XX.X%)
     ...

STEP 5: Saving Artifacts
  ✅ Artifacts saved to ./artifacts/
  ✅ Outputs saved to ./outputs/

STEP 6: Logging to MLflow
  ✅ All artifacts logged to MLflow
```

---

## 🔍 Quick Verification

After training, verify everything worked:

```bash
# 1. Check artifacts were created
ls -la artifacts/
# Should see: kmeans_cta_model.pkl, scaler.pkl, preprocess_config.json

# 2. Check visualizations
ls -la outputs/
# Should see: cluster_pca.png, user_clusters.csv

# 3. Check MLflow
curl http://localhost:5001/api/2.0/mlflow/experiments/list
# Should return list including "dz-customers-clustering"

# 4. Reload model in API
curl -X POST http://localhost:8000/reload_model
# Should return: {"detail":"model reloaded"}

# 5. Test prediction
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"gender":"M","age":35,"bnpl_eligible":1,"number_of_sessions":10,"days_since_first_joined":365,"number_of_failed_orders":1,"number_of_successful_orders":9}'
```

---

## 📈 Next: Compare Multiple Runs

```bash
# Run training multiple times
python3 scripts/train_with_mlflow.py
sleep 5
python3 scripts/train_with_mlflow.py
sleep 5
python3 scripts/train_with_mlflow.py

# Then in MLflow UI:
# 1. Select multiple runs (checkboxes)
# 2. Click "Compare"
# 3. See metrics side-by-side
```

---

## 🎛️ Customize Training

Edit parameters in `src/dz_customers_clustering/pipeline.py`:

```python
# Change number of clusters
DEFAULT_K = 5  # Try 5 instead of 7

# Enable auto k-selection
AUTO_SELECT_K = True
K_RANGE = range(3, 10)
```

Then retrain:
```bash
python3 scripts/train_with_mlflow.py
```

---

## 🆘 Quick Troubleshooting

### "ModuleNotFoundError: No module named 'mlflow'"
```bash
pip install mlflow
# or
uv pip install mlflow
```

### "Connection refused" to ClickHouse
- Check `.env` file has correct credentials
- Test connection: `ping your-clickhouse-host`

### MLflow UI not loading
```bash
# Check MLflow container
docker ps | grep mlflow

# Restart if needed
docker restart dz-mlflow
```

### No experiments showing in MLflow
- Refresh the page
- Check training completed successfully
- Look for error messages in terminal

---

## 📚 Full Documentation

- **Complete Guide**: `MLFLOW_TRAINING_GUIDE.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **API Docs**: `docs/API.md`
- **Deployment**: `docs/DEPLOYMENT.md`

---

## ✅ Success Checklist

- [ ] Docker services running
- [ ] MLflow accessible at http://localhost:5001
- [ ] .env file configured with ClickHouse credentials
- [ ] MLflow package installed
- [ ] Training script executed successfully
- [ ] Artifacts created in ./artifacts/
- [ ] Visualizations in ./outputs/
- [ ] Run visible in MLflow UI
- [ ] Model reloaded in API
- [ ] Predictions working

---

## 🎉 You're Ready!

Your MLOps workflow is complete:
- ✅ Automated tracking
- ✅ Full observability  
- ✅ Model versioning
- ✅ Experiment comparison
- ✅ Production-ready deployment

**Happy training!** 🚀

