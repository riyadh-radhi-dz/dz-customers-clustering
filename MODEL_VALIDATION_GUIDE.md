# 🏆 Automated Model Validation & Promotion Guide

## Champion/Challenger Pattern for Production ML

This system ensures you always have the best-performing model in production by automatically comparing new models with the current one.

---

## 🎯 How It Works

```
┌──────────────────────────────────────────────────────────┐
│          Daily Automated Model Validation                │
└──────────────────────────────────────────────────────────┘

    Every Day at 2 AM UTC:

    ┌─────────────────┐
    │  1. Load        │  📦 Load current Champion model
    │     Champion    │     (if exists)
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  2. Train       │  🎯 Train new Challenger model
    │     Challenger  │     with fresh data
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  3. Compare     │  📊 Calculate metrics for both:
    │     Models      │     - Silhouette Score
    │                 │     - Davies-Bouldin Index
    │                 │     - Calinski-Harabasz Score
    │                 │     - Cluster Balance
    │                 │     - Composite Score
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  4. Decision    │  
    │                 │  
    │  Is Challenger  │───YES──▶ ┌──────────────────┐
    │  Better by 2%?  │          │  5. PROMOTE      │
    │                 │          │     Challenger   │
    └────────┬────────┘          │     becomes      │
             │                   │     Champion     │
             NO                  └──────────────────┘
             │
             ▼
    ┌─────────────────┐
    │  5. KEEP        │  🛡️ Keep current Champion
    │     Champion    │     Backup Challenger for
    │                 │     future reference
    └─────────────────┘
```

---

## 🚀 Quick Start

### Option 1: Run Manually

```bash
# Set up environment (if not already done)
cp .env.example .env
nano .env  # Add ClickHouse credentials

# Install dependencies
pip install mlflow scikit-learn

# Run validation and promotion
python3 validate_and_promote_model.py

# Or use Make
make validate-and-promote
```

### Option 2: Automated Daily Runs (GitHub Actions)

Already configured! The workflow runs automatically every day at 2 AM UTC.

To trigger manually:
1. Go to GitHub Actions
2. Select "Model Training Pipeline"
3. Click "Run workflow"
4. (Optional) Set improvement threshold

---

## 📊 Metrics Explained

### Primary Metrics

| Metric | Range | Better | Description |
|--------|-------|--------|-------------|
| **Composite Score** | 0-1 | Higher | Overall quality (weighted combination) |
| **Silhouette Score** | -1 to 1 | Higher | How well samples fit their clusters |
| **Davies-Bouldin Index** | 0 to ∞ | Lower | Separation between clusters |
| **Calinski-Harabasz** | 0 to ∞ | Higher | Variance ratio (between/within clusters) |
| **Cluster Balance** | 0 to ∞ | Lower | Standard deviation of cluster sizes |
| **K-Prototypes Cost** | 0 to ∞ | Lower | Training objective function |

### Composite Score Calculation

The system uses a weighted composite score:

```python
composite_score = (
    30% × Silhouette Score (normalized) +
    30% × Davies-Bouldin Index (inverted & normalized) +
    20% × Calinski-Harabasz Score (normalized) +
    20% × Cluster Balance (inverted & normalized)
)
```

---

## 🎛️ Configuration

### Improvement Threshold

Default: **2%** improvement required for promotion.

**Change the threshold:**

```bash
# Via environment variable
export MODEL_IMPROVEMENT_THRESHOLD=0.05  # 5% improvement required
python3 scripts/validate_and_promote_model.py

# Via GitHub Actions workflow input
# Set "improvement_threshold" to 0.05
```

**Recommended thresholds:**
- **0.01 (1%)**: Aggressive - promotes easily
- **0.02 (2%)**: Balanced - recommended (default)
- **0.05 (5%)**: Conservative - only significant improvements
- **0.10 (10%)**: Very conservative - rare promotions

---

## 📁 Directory Structure

```
artifacts/
├── champion/                    # Current production model
│   ├── kmeans_cta_model.pkl
│   ├── scaler.pkl
│   └── preprocess_config.json
│
├── challenger/                  # Latest trained model
│   ├── kmeans_cta_model.pkl
│   ├── scaler.pkl
│   └── preprocess_config.json
│
├── backup/                      # Historical backups
│   ├── champion_20240115_143022/
│   ├── champion_20240116_143015/
│   └── champion_20240117_143010/
│
├── kmeans_cta_model.pkl         # Active production model
├── scaler.pkl                   # Active production scaler
├── preprocess_config.json       # Active production config
└── promotion_report.json        # Latest comparison report
```

---

## 📈 Example Output

### Successful Promotion

```
MODEL COMPARISON
============================================================

📊 Metric Comparison:
Metric                        Champion        Challenger      Change         
---------------------------------------------------------------------------
✅ composite_score             0.6542          0.6813          +4.14%
✅ silhouette_score            0.4521          0.4892          +8.21%
✅ davies_bouldin_index        1.2345          1.1234          -9.00%
✅ k_prototypes_cost           12345.67        11234.56        -9.00%
✅ cluster_balance_std         0.2345          0.2145          -8.53%

============================================================
DECISION
============================================================
✅ PROMOTE CHALLENGER TO PRODUCTION
   Improvement: +4.14%
   Threshold: 2.0%
============================================================
```

### Keep Champion

```
MODEL COMPARISON
============================================================

📊 Metric Comparison:
Metric                        Champion        Challenger      Change         
---------------------------------------------------------------------------
❌ composite_score             0.6542          0.6589          +0.72%
✅ silhouette_score            0.4521          0.4612          +2.01%
❌ davies_bouldin_index        1.2345          1.2456          +0.90%
❌ k_prototypes_cost           12345.67        12456.78        +0.90%
✅ cluster_balance_std         0.2345          0.2298          -2.00%

============================================================
DECISION
============================================================
⚠️  KEEP CURRENT CHAMPION
   Improvement: +0.72%
   Below threshold: 2.0%
============================================================
```

---

## 🔍 Monitoring & Tracking

### View in MLflow

All validations are logged to MLflow:

1. **Open**: http://localhost:5001
2. **Navigate to**: "dz-customers-clustering" experiment
3. **Look for runs**: named "validation-TIMESTAMP"

**Logged Information:**
- Champion metrics (prefixed with `champion_`)
- Challenger metrics (prefixed with `challenger_`)
- Improvement percentages
- Decision (PROMOTE/KEEP_CHAMPION)
- Reason for decision

### View Comparison Report

After each run:

```bash
# View the latest comparison report
cat artifacts/promotion_report.json | jq
```

### Check Current Champion

```bash
# See what's in production
ls -la artifacts/champion/

# Check when it was last updated
stat artifacts/champion/kmeans_cta_model.pkl
```

---

## 🔄 Complete Workflow

### Day 1: Initial Deployment

```bash
# First run - no champion exists
python3 scripts/validate_and_promote_model.py

# Output:
# ⚠️  No champion model found. First run will become champion.
# 🏆 No champion exists. Promoting challenger...
# ✅ FIRST MODEL DEPLOYED
```

### Day 2: Model Improves

```bash
# Second run - challenger is better
python3 scripts/validate_and_promote_model.py

# Output:
# ✅ PROMOTE CHALLENGER TO PRODUCTION
# Improvement: +3.45%
# 🏆 Promoting challenger to production...
# ✅ Champion backed up to artifacts/backup/champion_20240115_143022
# ✅ NEW MODEL IN PRODUCTION
```

### Day 3: Model Doesn't Improve

```bash
# Third run - challenger is worse or marginal
python3 scripts/validate_and_promote_model.py

# Output:
# ⚠️  KEEP CURRENT CHAMPION
# Improvement: +1.23%
# Below threshold: 2.0%
# ✅ CHAMPION RETAINED
```

---

## 🛠️ Advanced Usage

### Custom Validation Logic

Edit `scripts/validate_and_promote_model.py` to customize:

```python
# Change metric weights in composite score
composite_score = (
    0.4 * silhouette_norm +      # Increase silhouette weight
    0.3 * davies_bouldin_norm +
    0.2 * calinski_norm +
    0.1 * balance_norm
)

# Add custom business metrics
if min_cluster_size < 1000:  # Require minimum cluster size
    should_promote = False
```

### Rollback to Previous Champion

```bash
# List backups
ls -la artifacts/backup/

# Restore a specific backup
cp -r artifacts/backup/champion_20240115_143022/* artifacts/champion/
cp -r artifacts/backup/champion_20240115_143022/* artifacts/

# Reload in API
curl -X POST http://localhost:8000/reload_model
```

### Manual Promotion Override

```bash
# Force promotion regardless of metrics
cp -r artifacts/challenger/* artifacts/champion/
cp -r artifacts/challenger/* artifacts/

# Reload in API
curl -X POST http://localhost:8000/reload_model
```

---

## 📊 Best Practices

### 1. **Set Appropriate Threshold**
- Start with 2% (default)
- Increase if models change too frequently
- Decrease if improvements are rare

### 2. **Monitor Promotion Frequency**
- Daily promotions = threshold too low
- No promotions for weeks = threshold too high or data not changing
- 1-2 promotions per week = good balance

### 3. **Review Rejected Models**
- Check MLflow for challenger metrics
- Understand why they didn't promote
- Adjust hyperparameters if needed

### 4. **Keep Backup History**
- Backups are automatic
- Keep at least 30 days
- Useful for debugging and rollback

### 5. **Alert on Anomalies**
- Set up alerts for:
  - No promotions for > 30 days
  - Metrics degrading over time
  - Validation pipeline failures

---

## 🐛 Troubleshooting

### "No champion model found" (First Run)

**This is normal!**
- First run automatically becomes champion
- Subsequent runs will compare against it

### Metrics Don't Make Sense

**Check:**
- Data quality (outliers, missing values)
- Feature distribution changes
- Number of samples used for validation

### Too Many Promotions

**Solutions:**
- Increase threshold (e.g., 0.05 for 5%)
- Check if data is changing too much
- Review if metrics are stable

### No Promotions Ever

**Solutions:**
- Decrease threshold (e.g., 0.01 for 1%)
- Check if model is already optimal
- Try different hyperparameters

### Validation Pipeline Fails

```bash
# Check logs
python3 scripts/validate_and_promote_model.py 2>&1 | tee validation.log

# Verify ClickHouse connection
echo "Check .env file has correct credentials"

# Test MLflow connection
curl http://localhost:5001/health
```

---

## 📋 Checklist

### Initial Setup
- [ ] Configure .env with ClickHouse credentials
- [ ] Install dependencies (mlflow, scikit-learn)
- [ ] Run first validation (creates champion)
- [ ] Verify artifacts in `artifacts/champion/`

### Daily Operations
- [ ] Check GitHub Actions for daily runs
- [ ] Review MLflow for validation results
- [ ] Monitor promotion frequency
- [ ] Check API is using latest model

### Monthly Review
- [ ] Review promotion history
- [ ] Analyze metric trends
- [ ] Adjust threshold if needed
- [ ] Clean old backups (keep last 30 days)

---

## 🎯 Integration with Production

### After Promotion

The validation system automatically:
1. ✅ Backs up old champion
2. ✅ Copies challenger to champion directory
3. ✅ Updates production artifacts directory
4. ✅ Creates promotion report

### Reload in API

```bash
# After validation completes, reload the API
curl -X POST http://localhost:8000/reload_model

# Verify new model is loaded
curl http://localhost:8000/health
# {"status":"ok","model_loaded":true}

# Test prediction
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"gender":"M","age":35,"bnpl_eligible":1,"number_of_sessions":10,"days_since_first_joined":365,"number_of_failed_orders":1,"number_of_successful_orders":9}'
```

---

## 📚 Additional Resources

- **MLflow UI**: http://localhost:5001
- **Prometheus Metrics**: http://localhost:9090
- **Grafana Dashboards**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs

---

## 🎉 Summary

You now have:
- ✅ Automated daily model validation
- ✅ Champion/Challenger comparison
- ✅ Automatic promotion of better models
- ✅ Safety through improvement thresholds
- ✅ Complete tracking in MLflow
- ✅ Automatic backups for rollback
- ✅ Production-ready MLOps workflow

**Your model stays up-to-date and performant automatically!** 🚀

