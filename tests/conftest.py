"""Pytest configuration and fixtures for testing."""
import sys
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.preprocessing import StandardScaler

# Add src to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))

from dz_customers_clustering.artifacts import PreprocessArtifacts


@pytest.fixture
def sample_customer_data() -> Dict[str, Any]:
    """Sample customer data for testing."""
    return {
        "gender": "M",
        "age": 35.0,
        "bnpl_eligible": 1,
        "number_of_sessions": 10.0,
        "days_since_first_joined": 365.0,
        "number_of_failed_orders": 1.0,
        "number_of_successful_orders": 9.0,
    }


@pytest.fixture
def batch_customer_data() -> list[Dict[str, Any]]:
    """Batch of customer data for testing."""
    return [
        {
            "gender": "M",
            "age": 35.0,
            "bnpl_eligible": 1,
            "number_of_sessions": 10.0,
            "days_since_first_joined": 365.0,
            "number_of_failed_orders": 1.0,
            "number_of_successful_orders": 9.0,
        },
        {
            "gender": "F",
            "age": 28.0,
            "bnpl_eligible": 0,
            "number_of_sessions": 5.0,
            "days_since_first_joined": 180.0,
            "number_of_failed_orders": 0.0,
            "number_of_successful_orders": 3.0,
        },
    ]


@pytest.fixture
def mock_preprocess_artifacts() -> PreprocessArtifacts:
    """Mock preprocessing artifacts for testing."""
    return PreprocessArtifacts(
        feature_columns=[
            "age",
            "number_of_sessions",
            "days_since_first_joined",
            "number_of_failed_orders",
            "number_of_successful_orders",
            "gender",
            "bnpl_eligible",
        ],
        numeric_medians={
            "age": 30.0,
            "number_of_sessions": 5.0,
            "days_since_first_joined": 200.0,
            "number_of_failed_orders": 0.0,
            "number_of_successful_orders": 2.0,
        },
        numeric_columns=[
            "age",
            "number_of_sessions",
            "days_since_first_joined",
            "number_of_failed_orders",
            "number_of_successful_orders",
        ],
        log_columns=[
            "number_of_sessions",
            "number_of_failed_orders",
            "number_of_successful_orders",
        ],
        gender_categories=["M", "F", "Unknown"],
        categorical_columns=["gender", "bnpl_eligible"],
    )


@pytest.fixture
def mock_scaler() -> StandardScaler:
    """Mock scaler for testing."""
    scaler = StandardScaler()
    # Fit on dummy data
    dummy_data = np.random.rand(100, 5)
    scaler.fit(dummy_data)
    return scaler


@pytest.fixture
def mock_model() -> MagicMock:
    """Mock KPrototypes model for testing."""
    model = MagicMock()
    model.predict.return_value = np.array([0])
    model.cost_ = 100.0
    model.labels_ = np.array([0, 1, 2, 0, 1])
    return model


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Sample DataFrame for testing."""
    return pd.DataFrame({
        "user_id": ["user1", "user2", "user3"],
        "gender": ["M", "F", "Unknown"],
        "age": [35.0, 28.0, 42.0],
        "bnpl_eligible": [1, 0, 1],
        "number_of_sessions": [10.0, 5.0, 15.0],
        "days_since_first_joined": [365.0, 180.0, 730.0],
        "number_of_failed_orders": [1.0, 0.0, 2.0],
        "number_of_successful_orders": [9.0, 3.0, 12.0],
        "birth_date": pd.to_datetime(["1988-01-01", "1995-06-15", "1981-03-20"]),
        "system_created_at": pd.to_datetime(["2023-01-01", "2023-06-01", "2021-01-01"]),
        "customer_id": ["cust1", "cust2", "cust3"],
    })


@pytest.fixture
def api_client() -> Generator[TestClient, None, None]:
    """FastAPI test client."""
    # Import here to avoid circular imports
    from app.main import app
    from app.services.model_loader import ModelLoader

    # Reset the singleton for testing
    ModelLoader._instance = None
    
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_clickhouse_client() -> MagicMock:
    """Mock ClickHouse client for testing."""
    client = MagicMock()
    client.query_df.return_value = pd.DataFrame({
        "user_id": ["user1", "user2"],
        "customer_id": ["cust1", "cust2"],
        "gender": ["M", "F"],
        "birth_date": pd.to_datetime(["1988-01-01", "1995-06-15"]),
        "system_created_at": pd.to_datetime(["2023-01-01", "2023-06-01"]),
        "bnpl_eligible": [1, 0],
        "number_of_sessions": [10, 5],
        "number_of_failed_orders": [1, 0],
        "number_of_successful_orders": [9, 3],
    })
    client.command.return_value = None
    return client


@pytest.fixture(autouse=True)
def cleanup_model_loader():
    """Clean up ModelLoader singleton after each test."""
    yield
    from app.services.model_loader import ModelLoader
    ModelLoader._instance = None

