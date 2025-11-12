from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import seaborn as sns
from clickhouse_connect.driver import Client
from joblib import dump
from kmodes.kprototypes import KPrototypes
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from dz_customers_clustering.artifacts import PreprocessArtifacts
from dz_customers_clustering.clickhouse import create_clickhouse_client, ping_clickhouse

sns.set_theme(style="whitegrid")

ARTIFACTS_DIR = Path("artifacts")
OUTPUTS_DIR = Path("outputs")
logger = logging.getLogger(__name__)

NUMERIC_COLUMNS = [
    "age",
    "bnpl_eligible",
    "number_of_sessions",
    "days_since_first_joined",
    "number_of_failed_orders",
    "number_of_successful_orders",
]

LOG_COLUMNS = [
    "number_of_sessions",
    "number_of_failed_orders",
    "number_of_successful_orders",
]

GENDER_CATEGORIES = ["M", "F", "Unknown"]
CATEGORICAL_COLUMNS = ["gender"]

DATA_EXTRACTION_QUERY = """
WITH
    bnpl AS (
        SELECT
            consumer_id,
            max(COALESCE(toInt32(bnpl_eligible), 0)) AS bnpl_eligible
        FROM digital_zone_user_cards
        GROUP BY consumer_id
    ),
    sessions AS (
        SELECT
            user_id,
            count(DISTINCT context_session_id) AS number_of_sessions
        FROM dz_rudderstack_staging.tracks
        GROUP BY user_id
    ),
    transactions AS (
        SELECT
            customer_id,
            countIf(status = 'FAILURE') AS number_of_failed_orders,
            countIf(status = 'SUCCESS') AS number_of_successful_orders
        FROM digital_zone_customer_transactions_local_v2
        GROUP BY customer_id
    )
SELECT
    u.system_consumer_id AS user_id,
    u.customer_id,
    u.gender,
    u.birth_date,
    u.system_created_at,
    bnpl.bnpl_eligible,
    sessions.number_of_sessions,
    transactions.number_of_failed_orders,
    transactions.number_of_successful_orders
FROM digital_zone_users_local AS u
LEFT JOIN bnpl ON bnpl.consumer_id = u.system_consumer_id
LEFT JOIN sessions ON sessions.user_id = u.system_consumer_id
LEFT JOIN transactions ON transactions.customer_id = u.customer_id
WHERE
    COALESCE(sessions.number_of_sessions, 0) > 0
    AND u.gender IS NOT NULL
    AND lowerUTF8(u.gender) != 'unidentified'
    AND (u.birth_date IS NULL OR u.birth_date != toDateTime('1925-01-01 00:00:00'))
"""


def ensure_directories() -> None:
    logger.info("Ensuring artifacts dir=%s and outputs dir=%s", ARTIFACTS_DIR, OUTPUTS_DIR)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def get_data(client: Client) -> pd.DataFrame:
    """Fetch raw user-level data from ClickHouse."""
    return client.query_df(DATA_EXTRACTION_QUERY)


def _normalize_gender(series: pd.Series) -> pd.Series:
    mapping = {"M": "M", "F": "F"}
    normalized = series.astype(str).str.upper().map(mapping)
    normalized = normalized.fillna("Unknown")
    normalized = normalized.replace({"UNIDENTIFIED": "Unknown"})
    normalized = normalized.where(normalized.isin(GENDER_CATEGORIES), "Unknown")
    return normalized


def _to_utc_naive(series: pd.Series) -> pd.Series:
    parsed = pd.to_datetime(series, errors="coerce", utc=True)
    return parsed.dt.tz_localize(None)


def _calculate_age(birth_dates: pd.Series) -> pd.Series:
    birth_series = _to_utc_naive(birth_dates)
    invalid_mask = birth_series == pd.Timestamp("1925-01-01")
    birth_series = birth_series.where(~invalid_mask, pd.NaT)
    today = pd.Timestamp.now(tz="UTC").normalize().tz_localize(None)
    age_years = ((today - birth_series).dt.days / 365.25).astype(float)
    return age_years


def _days_since_joined(created_at: pd.Series) -> pd.Series:
    created_series = _to_utc_naive(created_at)
    today = pd.Timestamp.now(tz="UTC").tz_localize(None)
    days = (today - created_series).dt.days.astype(float)
    return days.clip(lower=0)


def preprocess_data(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray, StandardScaler, PreprocessArtifacts]:
    """Feature engineering, encoding, and scaling."""
    work_df = df.copy()
    work_df["gender"] = _normalize_gender(work_df["gender"])
    work_df["age"] = _calculate_age(work_df["birth_date"])
    work_df["bnpl_eligible"] = (
        work_df["bnpl_eligible"].fillna(0).clip(lower=0, upper=1).astype(int)
    )
    work_df["number_of_sessions"] = work_df["number_of_sessions"].fillna(0)
    work_df["number_of_failed_orders"] = work_df["number_of_failed_orders"].fillna(0)
    work_df["number_of_successful_orders"] = work_df[
        "number_of_successful_orders"
    ].fillna(0)
    work_df["days_since_first_joined"] = _days_since_joined(
        work_df["system_created_at"]
    )

    insights_df = work_df[
        ["user_id", "gender"]
        + NUMERIC_COLUMNS
    ].copy()

    numeric_medians: dict[str, float] = {}
    for column in NUMERIC_COLUMNS:
        median_value = float(insights_df[column].median(skipna=True))
        if np.isnan(median_value):
            median_value = 0.0
        numeric_medians[column] = median_value
        insights_df[column] = insights_df[column].fillna(median_value)

    model_df = insights_df.copy()
    for column in LOG_COLUMNS:
        model_df[column] = np.log1p(model_df[column].clip(lower=0))

    numeric_data = model_df[NUMERIC_COLUMNS].copy()
    scaler = StandardScaler()
    numeric_scaled = scaler.fit_transform(numeric_data.values)
    numeric_scaled_df = pd.DataFrame(
        numeric_scaled, columns=NUMERIC_COLUMNS, index=model_df.index
    )

    feature_df = numeric_scaled_df.copy()
    for category_column in CATEGORICAL_COLUMNS:
        feature_df[category_column] = model_df[category_column]

    artifacts = PreprocessArtifacts(
        feature_columns=feature_df.columns.tolist(),
        numeric_medians=numeric_medians,
        numeric_columns=NUMERIC_COLUMNS,
        log_columns=LOG_COLUMNS,
        gender_categories=GENDER_CATEGORIES,
        categorical_columns=CATEGORICAL_COLUMNS,
    )

    return insights_df, feature_df, numeric_scaled, scaler, artifacts


def _build_training_matrix(
    feature_df: pd.DataFrame,
) -> tuple[np.ndarray, list[int]]:
    data_matrix = feature_df.to_numpy()
    categorical_indices = [
        feature_df.columns.get_loc(column) for column in CATEGORICAL_COLUMNS
    ]
    return data_matrix, categorical_indices


def find_optimal_k(
    data_matrix: np.ndarray,
    categorical_indices: list[int],
    k_values: Iterable[int] = range(2, 11),
) -> dict[str, dict[int, float] | int]:
    """Compute K-Prototypes cost for a range of k."""
    logger.info("Searching for optimal k in range %s", list(k_values))
    costs: dict[int, float] = {}
    best_k = None
    best_cost = float("inf")

    for k in k_values:
        if k >= len(data_matrix):
            continue
        model = KPrototypes(
            n_clusters=k,
            init="Huang",
            random_state=42,
            n_init=5,
            n_jobs=-1,
        )
        model.fit(data_matrix, categorical=categorical_indices)
        costs[k] = float(model.cost_)
        if model.cost_ < best_cost:
            best_cost = model.cost_
            best_k = k

    return {"costs": costs, "best_k": best_k}


def train_model(
    data_matrix: np.ndarray,
    categorical_indices: list[int],
    n_clusters: int,
) -> KPrototypes:
    """Fit the final K-Prototypes model."""
    model = KPrototypes(
        n_clusters=n_clusters,
        init="Huang",
        random_state=42,
        n_init=5,
        n_jobs=-1,
    )
    model.fit(data_matrix, categorical=categorical_indices)
    logger.info("Trained K-Prototypes model with k=%d", n_clusters)
    return model


def generate_insights(insights_df: pd.DataFrame, labels: np.ndarray) -> pd.DataFrame:
    """Produce descriptive statistics per cluster."""
    result_df = insights_df.copy()
    result_df["cluster"] = labels
    summary = (
        result_df.groupby("cluster")
        .agg(
            user_count=("user_id", "count"),
            avg_age=("age", "mean"),
            avg_sessions=("number_of_sessions", "mean"),
            avg_failed_orders=("number_of_failed_orders", "mean"),
            avg_successful_orders=("number_of_successful_orders", "mean"),
            avg_days_since_joined=("days_since_first_joined", "mean"),
            bnpl_rate=("bnpl_eligible", "mean"),
        )
        .round(2)
    )

    gender_mix = (
        result_df.pivot_table(
            index="cluster",
            columns="gender",
            values="user_id",
            aggfunc="count",
            fill_value=0,
        )
        .div(summary["user_count"], axis=0)
        .round(2)
    )
    summary = summary.join(gender_mix, how="left").fillna(0)
    print("Cluster insights:")
    print(summary)
    logger.info("Generated insights for %d clusters", summary.shape[0])
    return result_df


def plot_k_diagnostics(costs: dict[int, float]) -> None:
    """Save elbow plot based on K-Prototypes cost."""
    if not costs:
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(list(costs.keys()), list(costs.values()), marker="o")
    ax.set_title("K-Prototypes Cost by k")
    ax.set_xlabel("k")
    ax.set_ylabel("Cost")

    fig.tight_layout()
    output_path = OUTPUTS_DIR / "k_diagnostics.png"
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    logger.info("Saved k diagnostics plot to %s", output_path)


def plot_cluster_visualizations(numeric_scaled: np.ndarray, labels: np.ndarray) -> None:
    """Project clusters via PCA for visualization."""
    pca = PCA(n_components=2, random_state=42)
    components = pca.fit_transform(numeric_scaled)
    plot_df = pd.DataFrame(
        {"pc1": components[:, 0], "pc2": components[:, 1], "cluster": labels}
    )
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.scatterplot(
        data=plot_df,
        x="pc1",
        y="pc2",
        hue="cluster",
        palette="tab10",
        ax=ax,
        s=10,
        linewidth=0,
    )
    ax.set_title("Cluster projection (PCA)")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(OUTPUTS_DIR / "cluster_pca.png", dpi=200)
    plt.close(fig)
    logger.info("Saved PCA cluster projection to %s", OUTPUTS_DIR / "cluster_pca.png")


def save_outputs(
    clustered_df: pd.DataFrame,
    labels: np.ndarray,
    scaler: StandardScaler,
    model: KMeans,
    artifacts: PreprocessArtifacts,
) -> None:
    """Persist CSV outputs and artifacts."""
    ensure_directories()
    export_df = clustered_df.copy()
    export_df["cluster"] = labels
    export_df.to_csv(OUTPUTS_DIR / "user_clusters.csv", index=False)
    logger.info("Wrote clustered dataset with %d rows to %s", len(export_df), OUTPUTS_DIR / "user_clusters.csv")

    dump(model, ARTIFACTS_DIR / "kmeans_cta_model.pkl")
    dump(scaler, ARTIFACTS_DIR / "scaler.pkl")
    logger.info("Persisted model and scaler artifacts under %s", ARTIFACTS_DIR)

    metadata_path = ARTIFACTS_DIR / "preprocess_config.json"
    metadata_path.write_text(artifacts.to_json(), encoding="utf-8")


def run_pipeline(client: Client | None = None) -> None:
    """End-to-end orchestration for clustering pipeline."""
    logger.info("Starting clustering pipeline run")
    ensure_directories()
    client = client or create_clickhouse_client()
    logger.info("Pinging ClickHouse to verify credentials")
    ping_clickhouse(client)
    logger.info("Connection successful; extracting data")
    raw_df = get_data(client)
    logger.info("Fetched %d rows and %d columns from ClickHouse", len(raw_df), len(raw_df.columns))
    insights_df, feature_df, numeric_scaled, scaler, artifacts = preprocess_data(raw_df)
    data_matrix, categorical_indices = _build_training_matrix(feature_df)
    logger.info(
        "Completed preprocessing; insight rows=%d, feature matrix shape=%s",
        len(insights_df),
        data_matrix.shape,
    )
    diagnostics = find_optimal_k(data_matrix, categorical_indices)
    if not diagnostics["best_k"]:
        raise RuntimeError("Unable to determine optimal k from diagnostics.")
    logger.info(
        "Diagnostics finished; best_k=%s, evaluated ks=%s",
        diagnostics["best_k"],
        list(diagnostics["costs"].keys()),
    )
    model = train_model(data_matrix, categorical_indices, diagnostics["best_k"])
    clustered_df = generate_insights(insights_df, model.labels_)
    save_outputs(clustered_df, model.labels_, scaler, model, artifacts)
    plot_k_diagnostics(diagnostics["costs"])
    plot_cluster_visualizations(numeric_scaled, model.labels_)
    logger.info("Pipeline run completed successfully")
