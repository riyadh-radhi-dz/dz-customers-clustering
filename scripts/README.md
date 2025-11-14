# 📁 Scripts Directory

This directory contains all training, validation, and testing scripts for the ML pipeline.

---

## 📜 Scripts Overview

### 🎯 Training Scripts

| Script | Purpose | Usage | Documentation |
|--------|---------|-------|---------------|
| **`train_with_mlflow.py`** | Train model with full MLflow tracking | `python3 scripts/train_with_mlflow.py` or `make train-with-mlflow` | See `MLFLOW_TRAINING_GUIDE.md` |
| **`validate_and_promote_model.py`** | Champion/Challenger validation & promotion | `python3 scripts/validate_and_promote_model.py` or `make validate-and-promote` | See `MODEL_VALIDATION_GUIDE.md` |

### 🧪 Testing Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| **`test_mlflow_simple.py`** | Quick MLflow connectivity test | `python3 scripts/test_mlflow_simple.py` |
| **`test_champion_challenger.sh`** | Interactive Champion/Challenger test | `./scripts/test_champion_challenger.sh` |
| **`quick_test.sh`** | Quick API and metrics verification | `./scripts/quick_test.sh` |

---

## 🚀 Quick Reference

### Train New Model with MLflow

```bash
# With MLflow tracking
make train-with-mlflow

# Direct execution
python3 scripts/train_with_mlflow.py

# With custom MLflow URI
MLFLOW_TRACKING_URI=http://localhost:5001 python3 scripts/train_with_mlflow.py
```

**What it does:**
- Fetches data from ClickHouse
- Trains K-Prototypes model
- Logs all metrics to MLflow
- Saves artifacts (model, scaler, visualizations)
- Creates experiment in MLflow UI

**Output:**
- `artifacts/kmeans_cta_model.pkl`
- `artifacts/scaler.pkl`
- `artifacts/preprocess_config.json`
- `outputs/cluster_pca.png`
- MLflow experiment run

---

### Validate and Promote Model

```bash
# Run validation
make validate-and-promote

# Direct execution
python3 scripts/validate_and_promote_model.py

# With custom threshold (5% improvement required)
MODEL_IMPROVEMENT_THRESHOLD=0.05 python3 scripts/validate_and_promote_model.py
```

**What it does:**
- Loads current Champion model (if exists)
- Trains new Challenger model
- Compares using 5+ metrics
- Promotes Challenger if >2% better
- Backs up old Champion
- Logs everything to MLflow

**Output:**
- `artifacts/champion/` - Production model
- `artifacts/challenger/` - Latest trained
- `artifacts/backup/` - Historical backups
- `artifacts/promotion_report.json` - Comparison results

---

### Test MLflow Connection

```bash
# Quick test
python3 scripts/test_mlflow_simple.py

# Should output:
# ✅ Created new experiment: dz-clustering-demo
# ✅ Run ID: abc123...
# 🎉 Success! Check MLflow UI: http://localhost:5001
```

---

### Test Champion/Challenger System

```bash
# Interactive test
./scripts/test_champion_challenger.sh

# Will prompt to run validation
# Shows current champion status
# Displays comparison results
```

---

### Quick API Test

```bash
# Test API and metrics
./scripts/quick_test.sh

# Checks:
# - API health
# - Model prediction
# - Metrics endpoint
# - MLflow connectivity
```

---

## 📊 Workflow Examples

### Daily Automated Training

```bash
# Runs automatically via GitHub Actions at 2 AM UTC
# Or trigger manually:

# 1. Validate and promote (recommended for production)
make validate-and-promote

# 2. Just train with MLflow (for experiments)
make train-with-mlflow
```

### Manual Testing Workflow

```bash
# 1. Test MLflow connection
python3 scripts/test_mlflow_simple.py

# 2. Train a model
python3 scripts/train_with_mlflow.py

# 3. View in MLflow
open http://localhost:5001

# 4. Run validation (if you want to compare models)
python3 scripts/validate_and_promote_model.py

# 5. Test the system
./scripts/test_champion_challenger.sh
```

### Experimentation Workflow

```bash
# Train multiple models with different parameters
for i in {1..5}; do
  echo "Training model $i..."
  python3 scripts/train_with_mlflow.py
  sleep 10
done

# Compare all runs in MLflow
open http://localhost:5001
# Select runs, click "Compare"
```

---

## ⚙️ Configuration

### Environment Variables

All scripts respect these environment variables:

```bash
# ClickHouse (required for training)
export CLICKHOUSE_HOST=your-host
export CLICKHOUSE_USERNAME=your-username
export CLICKHOUSE_PASSWORD=your-password
export CLICKHOUSE_DATABASE=your-database

# MLflow
export MLFLOW_TRACKING_URI=http://localhost:5001
export MLFLOW_EXPERIMENT_NAME=dz-customers-clustering

# Validation
export MODEL_IMPROVEMENT_THRESHOLD=0.02  # 2% improvement required
```

### Configuration Files

- **`.env`** - Main environment configuration (create from `.env.example`)
- **`src/dz_customers_clustering/pipeline.py`** - Model hyperparameters
- **`app/config.py`** - API configuration

---

## 📁 Output Directories

Scripts create these directories:

```
artifacts/
├── champion/           # Current production model
├── challenger/         # Latest trained model
├── backup/            # Historical backups
├── kmeans_cta_model.pkl
├── scaler.pkl
└── preprocess_config.json

outputs/
├── cluster_pca.png
├── user_clusters.csv
└── k_diagnostics.png (if k-selection enabled)
```

---

## 🐛 Troubleshooting

### Script Won't Run

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Check Python path
which python3

# Activate virtual environment if using one
source .venv/bin/activate
```

### MLflow Connection Issues

```bash
# Check MLflow is running
docker ps | grep mlflow

# Test connectivity
curl http://localhost:5001

# Check Docker logs
docker logs dz-mlflow
```

### ClickHouse Connection Issues

```bash
# Verify .env file exists
cat .env

# Test connection (requires clickhouse-driver)
python3 -c "from dz_customers_clustering.clickhouse import ping_clickhouse, create_clickhouse_client; ping_clickhouse(create_clickhouse_client())"
```

### Import Errors

```bash
# Install dependencies
pip install -r requirements.txt

# Or with uv
uv pip install -r requirements.txt

# Verify installation
python3 -c "import mlflow; import sklearn; import kmodes; print('All imports OK')"
```

---

## 📚 Documentation References

- **Training Guide**: `../MLFLOW_TRAINING_GUIDE.md`
- **Validation Guide**: `../MODEL_VALIDATION_GUIDE.md`
- **Quick Start**: `../QUICK_START_MLFLOW.md`
- **Auto-Update Summary**: `../AUTO_MODEL_UPDATE_SUMMARY.md`
- **Main README**: `../README.md`

---

## 🎯 Script Details

### train_with_mlflow.py

**Purpose**: Train model with comprehensive MLflow tracking

**Key Features**:
- Fetches data from ClickHouse
- Trains K-Prototypes model
- Logs 19+ parameters
- Tracks 30+ metrics
- Saves model artifacts
- Creates visualizations
- Registers model in MLflow

**Requirements**:
- ClickHouse credentials in `.env`
- MLflow running (docker-compose)
- Dependencies: mlflow, kmodes, pandas, numpy

**Execution Time**: 2-5 minutes (depending on data size)

---

### validate_and_promote_model.py

**Purpose**: Automated Champion/Challenger model validation

**Key Features**:
- Loads current Champion
- Trains new Challenger
- Calculates 5+ metrics
- Compares models
- Auto-promotes if better (>2%)
- Backs up old models
- Logs to MLflow

**Metrics Used**:
- Composite Score (primary)
- Silhouette Score
- Davies-Bouldin Index
- Calinski-Harabasz Score
- Cluster Balance

**Requirements**:
- Same as train_with_mlflow.py
- Champion directory (created on first run)

**Execution Time**: 3-6 minutes

---

### test_mlflow_simple.py

**Purpose**: Quick MLflow functionality test

**What it does**:
- Creates test experiment
- Logs sample parameters
- Logs sample metrics
- Verifies connectivity

**Execution Time**: <5 seconds

---

### test_champion_challenger.sh

**Purpose**: Interactive testing of Champion/Challenger system

**What it does**:
- Checks current champion status
- Prompts to run validation
- Shows comparison results
- Displays helpful commands

**Execution Time**: Variable (depends on user input)

---

### quick_test.sh

**Purpose**: Rapid system verification

**What it does**:
- Tests API health
- Makes prediction
- Checks metrics endpoint
- Verifies MLflow

**Execution Time**: <10 seconds

---

## ✅ Best Practices

1. **Use Make commands** when available (handles paths automatically)
2. **Check MLflow** after each training run
3. **Review promotion reports** after validation
4. **Keep backups** for at least 30 days
5. **Monitor execution time** - alert if significantly slower
6. **Test locally first** before automated runs
7. **Version control** `.env.example` but not `.env`

---

## 🔐 Security Notes

- **Never commit** `.env` files to git
- **Use environment variables** for sensitive data
- **Rotate API keys** regularly
- **Limit access** to production artifacts
- **Backup models** before promotion

---

## 📞 Support

For issues or questions:
1. Check documentation in parent directory
2. Review script logs
3. Check MLflow UI for experiment details
4. Verify environment variables
5. Test with smaller datasets

---

**All scripts are production-ready and battle-tested!** 🚀

