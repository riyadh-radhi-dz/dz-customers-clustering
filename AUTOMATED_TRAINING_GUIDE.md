# 🤖 Automated Model Training Guide

## Overview

This guide explains how to automatically retrain and update your customer clustering model when new users arrive in your system.

## 🎯 Training Strategy

Your system uses the **Champion/Challenger Pattern** to ensure production models only get better:

1. **Daily Training**: Model automatically retrains with latest data
2. **Smart Comparison**: New model (Challenger) is compared against current production model (Champion)
3. **Automatic Promotion**: Challenger only replaces Champion if it's significantly better (>2% improvement)
4. **Safe Rollback**: Old models are backed up before any changes

---

## 🚀 How to Train When New Users Arrive

### Option 1: Manual Training (Immediate)

When you get new users and want to update the model right away:

```bash
# Step 1: Train new model with MLflow tracking
make train-with-mlflow

# Step 2: Validate and promote if better
make validate-and-promote

# Step 3: Restart API to load new model
docker-compose restart api
```

**What happens:**
- ✅ Pulls latest data from ClickHouse (including new users)
- ✅ Trains new model with optimal hyperparameters
- ✅ Logs everything to MLflow (metrics, artifacts, visualizations)
- ✅ Compares new model vs current production model
- ✅ Automatically promotes if better (>2% improvement)
- ✅ Creates backup of old model before replacement

### Option 2: Automated Daily Training (GitHub Actions)

Your system is already configured for daily automatic retraining at 2 AM UTC.

**Location:** `.github/workflows/model-training.yml`

```yaml
schedule:
  - cron: '0 2 * * *'  # Daily at 2 AM UTC
```

**To change the schedule:**

```yaml
# Every 6 hours
- cron: '0 */6 * * *'

# Twice daily (2 AM and 2 PM UTC)
- cron: '0 2,14 * * *'

# Every Monday at 3 AM UTC
- cron: '0 3 * * 1'

# Every hour
- cron: '0 * * * *'
```

**What GitHub Actions does automatically:**
1. Sets up environment (Python, dependencies)
2. Connects to ClickHouse with latest data
3. Trains new model with MLflow tracking
4. Validates against current production model
5. Promotes if better (Champion/Challenger pattern)
6. Uploads new artifacts if promoted
7. Sends notifications on failure

### Option 3: API Trigger (On-Demand)

Train the model programmatically via API call:

```bash
# Option A: Using curl
curl -X POST "http://localhost:8000/api/v1/train" \
  -H "X-API-Key: your-api-key"

# Option B: Using httpie
http POST http://localhost:8000/api/v1/train \
  X-API-Key:your-api-key
```

**Note:** You'll need to add a training endpoint to your API if you want this option.

---

## 📊 Monitor Training with MLflow

After training, view all experiments and metrics:

```bash
# Access MLflow UI
open http://localhost:5001

# Or if running in Docker
docker-compose up -d mlflow
```

**MLflow Dashboard shows:**
- 📈 Training metrics (Silhouette, Davies-Bouldin, Calinski-Harabasz)
- 🎯 Cluster quality metrics
- 📊 Cluster distribution and balance
- 🖼️ Visualization artifacts (PCA plots, elbow curves)
- 🏆 Champion vs Challenger comparisons
- ⏱️ Training duration and performance
- 📦 Model artifacts and versions

---

## 🔍 How Champion/Challenger Works

### Metrics Evaluated

The system compares 5 key metrics:

| Metric | Description | Better When |
|--------|-------------|-------------|
| **Silhouette Score** | Cluster separation quality | Higher ↑ |
| **Davies-Bouldin Index** | Cluster compactness | Lower ↓ |
| **Calinski-Harabasz Score** | Cluster definition | Higher ↑ |
| **Cluster Balance** | Even distribution | Higher ↑ |
| **Composite Score** | Weighted combination | Higher ↑ |

### Promotion Logic

```python
# Challenger is promoted if:
composite_improvement > IMPROVEMENT_THRESHOLD  # Default: 2%

# Composite score formula:
composite = (
    silhouette_weight * silhouette_score +
    davies_bouldin_weight * (1 / davies_bouldin) +
    calinski_weight * calinski_harabasz +
    balance_weight * cluster_balance
) / total_weight
```

### Artifacts Structure

```
artifacts/
├── champion/              # Current production model
│   ├── model.pkl
│   ├── scaler.pkl
│   └── metadata.json
├── challenger/            # Newly trained model (being evaluated)
│   ├── model.pkl
│   ├── scaler.pkl
│   └── metadata.json
└── backup/               # Historical backups
    ├── backup_20250114_120530/
    │   ├── model.pkl
    │   ├── scaler.pkl
    │   └── metadata.json
    └── backup_20250115_020145/
        └── ...
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# .env file

# ClickHouse (Data Source)
CLICKHOUSE_HOST=your-clickhouse-host
CLICKHOUSE_USERNAME=your-username
CLICKHOUSE_PASSWORD=your-password
CLICKHOUSE_DATABASE=digital_zone_snapshots

# MLflow (Experiment Tracking)
MLFLOW_TRACKING_URI=http://localhost:5001
MLFLOW_EXPERIMENT_NAME=dz-customers-clustering
MLFLOW_MODEL_NAME=customer-clustering-model

# Validation Thresholds
IMPROVEMENT_THRESHOLD=0.02          # 2% minimum improvement
MIN_SILHOUETTE_SCORE=0.3           # Minimum acceptable quality
MAX_DAVIES_BOULDIN_SCORE=2.0       # Maximum acceptable dispersion
```

### Training Parameters

Edit `scripts/train_with_mlflow.py`:

```python
# Clustering parameters
OPTIMAL_K_RANGE = range(3, 8)  # Test 3-7 clusters
N_INIT = 10                     # Number of initializations
MAX_ITER = 100                  # Maximum iterations
INIT_METHOD = 'Huang'           # Initialization method

# Feature engineering
LOG_TRANSFORM_FEATURES = [
    'age', 'sessions_count', 'orders_count',
    'total_amount', 'products_count'
]

# PCA for visualization
PCA_COMPONENTS = 2
```

---

## 🧪 Testing the System

### Quick Test

```bash
# Test the entire workflow
bash scripts/test_champion_challenger.sh
```

This interactive script will:
1. ✅ Train initial Champion model
2. ✅ Train Challenger model with different params
3. ✅ Run validation and comparison
4. ✅ Show promotion decision
5. ✅ Display MLflow experiment results

### API Health Check

```bash
# Quick API test
bash scripts/quick_test.sh
```

---

## 📋 Best Practices

### 1. Training Frequency

**Recommendations based on user growth:**

| New Users/Day | Recommended Frequency |
|---------------|----------------------|
| < 100 | Weekly |
| 100 - 1,000 | Daily |
| 1,000 - 10,000 | Twice daily |
| > 10,000 | Every 6 hours |

### 2. Data Quality Checks

Before training, ensure:
- ✅ ClickHouse connection is healthy
- ✅ Minimum data volume (e.g., >10,000 users)
- ✅ No data quality issues (nulls, outliers)
- ✅ Recent data is present (not stale)

### 3. Monitor These Metrics

Keep an eye on:
- 📊 Cluster sizes (should be relatively balanced)
- 📈 Silhouette score (>0.3 is good, >0.5 is excellent)
- ⏱️ Training duration (sudden increases indicate issues)
- 🎯 Promotion rate (too many/few promotions suggests threshold issues)

### 4. Rollback Procedure

If a promoted model causes issues:

```bash
# Step 1: Navigate to artifacts
cd artifacts/

# Step 2: Find latest backup
ls -lt backup/

# Step 3: Copy backup to champion
cp -r backup/backup_YYYYMMDD_HHMMSS/* champion/

# Step 4: Restart API
docker-compose restart api
```

---

## 🚨 Troubleshooting

### Problem: Training Takes Too Long

**Solutions:**
- Reduce `OPTIMAL_K_RANGE` (test fewer cluster counts)
- Decrease `N_INIT` (fewer random starts)
- Reduce `MAX_ITER` (stop earlier)
- Filter data (e.g., only active users from last 6 months)

### Problem: Models Never Get Promoted

**Possible causes:**
- `IMPROVEMENT_THRESHOLD` is too high (try 1% instead of 2%)
- Data isn't changing enough between runs
- Champion model is already optimal

**Check:**
```bash
# View comparison details
cat artifacts/challenger/metadata.json | grep -A 5 "metrics"
cat artifacts/champion/metadata.json | grep -A 5 "metrics"
```

### Problem: New Model is Worse

**This is expected!** The Champion/Challenger pattern protects you:
- ✅ Bad model is automatically rejected
- ✅ Champion stays in production
- ✅ Backup is preserved

**View rejection reason:**
```bash
# Check MLflow run
open http://localhost:5001
# Look for "validation_decision" tag
```

### Problem: ClickHouse Connection Fails

**Check:**
```bash
# Test connection
python3 -c "
from src.dz_customers_clustering.clickhouse import get_data
df = get_data()
print(f'Loaded {len(df)} rows')
"

# Verify credentials
cat .env | grep CLICKHOUSE
```

---

## 📞 Support

For issues or questions:

1. Check MLflow UI for training logs: http://localhost:5001
2. Review training output: `docker-compose logs api`
3. Examine validation logs: `cat artifacts/challenger/metadata.json`
4. Check GitHub Actions runs: https://github.com/your-repo/actions

---

## 🎯 Quick Reference

```bash
# Full workflow
make train-with-mlflow && make validate-and-promote

# View MLflow experiments
open http://localhost:5001

# Test workflow
bash scripts/test_champion_challenger.sh

# Check current model version
cat artifacts/champion/metadata.json

# View recent backups
ls -lt artifacts/backup/

# Restart API with new model
docker-compose restart api
```

---

## 📚 Related Documentation

- [`MODEL_VALIDATION_GUIDE.md`](MODEL_VALIDATION_GUIDE.md) - Detailed validation logic
- [`AUTO_MODEL_UPDATE_SUMMARY.md`](AUTO_MODEL_UPDATE_SUMMARY.md) - Quick reference
- [`MLFLOW_TRAINING_GUIDE.md`](MLFLOW_TRAINING_GUIDE.md) - MLflow integration details
- [`QUICK_START_MLFLOW.md`](QUICK_START_MLFLOW.md) - Getting started with MLflow
- [`README.md`](README.md) - Full project documentation

