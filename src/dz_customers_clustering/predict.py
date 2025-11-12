from __future__ import annotations

import logging
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[2]
    src_dir = project_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.append(str(src_dir))

from dz_customers_clustering.inference import (
    load_preprocess_artifacts,
    predict_cluster,
)

SAMPLE_RECORD = {
    "gender": "F",
    "age": 35,
    "bnpl_eligible": 1,
    "number_of_sessions": 4,
    "days_since_first_joined": 420,
    "number_of_failed_orders": 0,
    "number_of_successful_orders": 3,
}


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.info("Predicting cluster for hard-coded sample: %s", SAMPLE_RECORD)
    model, scaler, metadata = load_preprocess_artifacts()
    cluster = predict_cluster(SAMPLE_RECORD, model, scaler, metadata)
    logging.info("Predicted cluster: %d", cluster)


if __name__ == "__main__":
    main()
