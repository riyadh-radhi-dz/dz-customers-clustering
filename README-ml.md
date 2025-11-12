
## Setup

1. Create a virtual environment that uses Python 3.13 or newer (e.g. `uv venv`).
2. Install/update dependencies with `uv sync` (or add new ones via `uv add package-name`).
3. Copy `.env.example` to `.env` and fill in the real credentials.

## Environment Variables

| Variable | Description |
| --- | --- |
| `CLICKHOUSE_HOST` | ClickHouse hostname supplied by Altinity. |
| `CLICKHOUSE_PORT` | ClickHouse HTTPS port (defaults to `8443`). |
| `CLICKHOUSE_USERNAME` | ClickHouse username. |
| `CLICKHOUSE_PASSWORD` | ClickHouse password. |
| `CLICKHOUSE_DATABASE` | Target ClickHouse database (e.g. `digital_zone_snapshots`). |
| `CLICKHOUSE_SECURE` | Set to `true` for TLS connections, `false` otherwise. |

The `.env` file is ignored by Git so that production credentials never leave your workstation.

## Running the Clustering Pipeline

The full ClickHouse → feature engineering → K-Prototypes workflow is bundled in `dz_customers_clustering.pipeline`. Run it end-to-end with:

```bash
uv run main.py
```

The script:

- pulls ~1M user rows from ClickHouse with all required joins,
- engineers the behavioral features (age, sessions, BNPL eligibility, order counts, etc.),
- filters out users with zero sessions, `unidentified` gender, or invalid birth dates (`1925-01-01`) directly in the ClickHouse query,
- encodes + scales the data (log transforms + StandardScaler on numeric features; gender and BNPL eligibility stay categorical for K-Prototypes),
- (optionally) searches for the optimal `k` (3–6) via the K-Prototypes cost curve (n_init=2, max_iter=10 for faster tuning); currently the pipeline is configured to use a fixed `k=4` for faster experimentation,
- trains the final K-Prototypes model,
- saves artifacts under `./artifacts/` (`kmeans_cta_model.pkl`, `scaler.pkl`, `preprocess_config.json`),
- exports cluster assignments and visuals under `./outputs/` (`user_clusters.csv`, diagnostic plots, PCA scatter).

Feel free to import `run_pipeline`, `get_data`, `preprocess_data`, etc. directly from `dz_customers_clustering.pipeline` when iterating in notebooks.

## Cluster Summaries

Once `uv run main.py` finishes and writes `outputs/user_clusters.csv`, you can review the descriptive statistics per cluster by running:

```bash
uv run src/dz_customers_clustering/summary.py
```

This helper loads the CSV, computes the same aggregate metrics (averages, BNPL rate, gender mix), and prints the table so you can inspect the clusters without re-running the full pipeline.

## Production Prediction Example

After artifacts are generated (`uv run main.py`), you can see how to score a new user record in production with:

```bash
uv run src/dz_customers_clustering/predict.py
```

The script hard-codes a representative user dictionary, loads the saved scaler/model, and prints the assigned cluster. Replace `SAMPLE_RECORD` in `predict.py` with values sourced from your application to build real-time scoring.

