from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import pandas as pd

OUTPUTS_DIR = Path("outputs")
DEFAULT_DATASET = OUTPUTS_DIR / "user_clusters.csv"

SUMMARY_COLUMNS: Iterable[str] = (
    "age",
    "bnpl_eligible",
    "number_of_sessions",
    "days_since_first_joined",
    "number_of_failed_orders",
    "number_of_successful_orders",
)

logger = logging.getLogger(__name__)


def load_clustered_data(csv_path: Path = DEFAULT_DATASET) -> pd.DataFrame:
    """Load clustered dataset exported by the pipeline."""
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{csv_path} not found. Run uv run main.py to generate the clustered data first."
        )
    logger.info("Loading clustered data from %s", csv_path)
    return pd.read_csv(csv_path)


def summarize_clusters(df: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive statistics per cluster."""
    required_columns = {"cluster", "gender", *SUMMARY_COLUMNS}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing required columns: {missing}")

    summary = (
        df.groupby("cluster")
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
        df.pivot_table(
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
    return summary


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    df = load_clustered_data()
    summary = summarize_clusters(df)
    logger.info("Summary statistics per cluster:")
    print(summary)


if __name__ == "__main__":
    main()
