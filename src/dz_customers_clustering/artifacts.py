from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass
class PreprocessArtifacts:
    feature_columns: list[str]
    numeric_medians: dict[str, float]
    numeric_columns: list[str]
    log_columns: list[str]
    gender_categories: list[str]
    categorical_columns: list[str]

    def to_json(self) -> str:
        return json.dumps(
            {
                "feature_columns": self.feature_columns,
                "numeric_medians": self.numeric_medians,
                "numeric_columns": self.numeric_columns,
                "log_columns": self.log_columns,
                "gender_categories": self.gender_categories,
                "categorical_columns": self.categorical_columns,
            },
            indent=2,
        )

    @staticmethod
    def from_json(payload: str) -> "PreprocessArtifacts":
        data = json.loads(payload)
        return PreprocessArtifacts(
            feature_columns=data["feature_columns"],
            numeric_medians=data["numeric_medians"],
            numeric_columns=data["numeric_columns"],
            log_columns=data["log_columns"],
            gender_categories=data["gender_categories"],
            categorical_columns=data.get("categorical_columns", []),
        )
