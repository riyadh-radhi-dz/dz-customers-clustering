# Customer Segmentation Model – Backend Handover

This document explains how to run the clustering pipeline, manage artifacts, and integrate the trained K-Prototypes model into backend services that expose HTTP endpoints for the frontend.

---

## 1. Stack Overview

| Item | Details |
| --- | --- |
| Language | Python 3.13 (managed with `uv`) |
| Database | ClickHouse (`digital_zone_snapshots` schema) |
| Key libs | `clickhouse-connect`, `pandas`, `kmodes` (K-Prototypes), `scikit-learn`, `joblib`, `seaborn`, `matplotlib` |
| Entry points | `main.py` (training pipeline), `src/dz_customers_clustering/predict.py` (sample inference) |

---

## 2. Environment Setup

1. Clone the repo and install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate
   uv sync
   ```
2. Copy `.env.example` → `.env` and fill in ClickHouse credentials.
3. Ensure the working directory contains:
   - `artifacts/` (model + scaler + metadata)
   - `outputs/` (cluster CSV + plots)

---

## 3. Training Pipeline (batch refresh)

Command:
```bash
uv run main.py
```

What happens:
1. Connects to ClickHouse with credentials from `.env`.
2. Extracts users with behavioral features (sessions, BNPL flag, order counts, etc.), filtering out:
   - zero-session users
   - `unidentified` gender
   - invalid birth dates (`1925-01-01`)
3. Engineers/cleans features:
   - numeric columns log-transformed + standardized
   - categorical: gender (`M`, `F`, `Unknown`) and BNPL eligibility (`0`, `1`)
4. Uses K-Prototypes with **k = 4** (manual setting) to cluster ~1M users.
5. Saves artifacts under `./artifacts/`:
   - `kmeans_cta_model.pkl` (actually the `KPrototypes` model)
   - `scaler.pkl` (StandardScaler for numeric features)
   - `preprocess_config.json` (feature order, medians, categorical columns)
6. Writes outputs to `./outputs/`
   - `user_clusters.csv` (user_id + features + cluster)
   - `k_diagnostics.png` (if auto-k search enabled)
   - `cluster_pca.png` (2D visualization)
7. Logs progress at each stage for observability.

To change `k` or re-enable automatic tuning, edit `src/dz_customers_clustering/pipeline.py` (`DEFAULT_K`, `AUTO_SELECT_K`, `K_RANGE`).

---

## 4. Artifacts & Directory Contracts

| Path | Description |
| --- | --- |
| `artifacts/kmeans_cta_model.pkl` | `KPrototypes` model used for inference |
| `artifacts/scaler.pkl` | StandardScaler (trained only on numeric features) |
| `artifacts/preprocess_config.json` | JSON with feature ordering, medians for imputation, log-transform metadata, categorical column names |
| `outputs/user_clusters.csv` | Latest cluster assignments; downstream analytics/BI can consume this |

These three files (`model`, `scaler`, `preprocess_config.json`) must be deployed together for consistent predictions.

---

## 5. Inference Workflow

### 5.1 Local script

 `uv run src/dz_customers_clustering/predict.py` can be used as a reference. It:
1. Loads the artifacts.
2. Hard codes a sample payload (dict shaped like the database schema).
3. Calls `predict_cluster(sample_record, model, scaler, metadata)` from `dz_customers_clustering.inference`.
4. Prints the predicted cluster.

Use it as a template for backend services.

### 5.2 Backend integration steps

1. **Load artifacts once on service startup**:
   ```python
   from dz_customers_clustering.inference import load_preprocess_artifacts
   model, scaler, metadata = load_preprocess_artifacts()
   ```
   Cache these objects in memory for reuse.

2. **Feature pipeline for incoming requests**:
   - Required fields per user:
     ```json
     {
       "gender": "M|F|Unknown",
       "age": <float>,
       "bnpl_eligible": 0|1,
       "number_of_sessions": <int>,
       "days_since_first_joined": <int>,
       "number_of_failed_orders": <int>,
       "number_of_successful_orders": <int>
     }
     ```
   - Optional: allow `null`/missing numeric values; fill with medians from `metadata.numeric_medians`.
   - Normalize gender to uppercase, default to `"Unknown"`.

3. **Transform & predict**:
   ```python
   from dz_customers_clustering.inference import predict_cluster

   cluster = predict_cluster(sample_record, model, scaler, metadata)
   ```
   For a custom service, replicate what `predict_cluster` does:
   - Convert inputs to DataFrame.
   - Fill missing numeric values using `metadata`.
   - Apply log1p to skewed numeric features (same columns as training).
   - Scale numerics with `scaler`.
   - Append categorical columns (`gender`, `bnpl_eligible`) without scaling.
   - Ensure resulting feature matrix columns match `metadata.feature_columns`.
   - Call `model.predict(feature_matrix, categorical=categorical_indices)`.

4. **API response schema**:
   ```json
   {
     "cluster": 0,
     "confidence": null,
     "payload": { ... original user features ... }
   }
   ```
   (Confidence not available from K-Prototypes; omit or compute heuristics if needed.)

5. **Error handling**:
   - Validate required fields, return `400` on malformed data.
   - If artifacts missing, return `503` until training job populates them.

---

## 6. Deployment Suggestions

- Package the repo as a Docker image containing:
  - Python runtime + dependencies (`uv sync` output cached via `requirements.txt` or `uv export requirements`)
  - `artifacts/` directory for the latest model snapshot.
- Expose a FastAPI/Flask endpoint (`POST /predict`) that wraps the inference flow.
- Schedule the training pipeline (main.py) via Airflow/Cron to refresh clusters weekly/monthly. After training:
  1. Upload new artifacts to object storage (e.g., S3).
  2. Trigger backend redeploy or provide a hot-reload endpoint to pull new artifacts.

---

## 7. Testing & Monitoring

- **Unit tests**: add tests around `dz_customers_clustering.inference.predict_cluster` with synthetic payloads to ensure deterministic outputs after upgrades.
- **Smoke tests**: after redeploying artifacts, run `predict.py` or a synthetic API call using known payloads to confirm cluster IDs remain sensible.
- **Logging/metrics**:
  - Track number of predictions per cluster to detect distribution drift.
  - Optionally log feature ranges to identify missing data issues.
