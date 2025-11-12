# %%
from __future__ import annotations
# %%
from pathlib import Path
import sys

import clickhouse_connect
from clickhouse_connect.driver import Client
# %%
if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[1]
    sys.path.append(str(project_root))

from dz_customers_clustering.settings import (
    ClickHouseSettings,
    get_clickhouse_settings,
)
# %%

def create_clickhouse_client(
    settings: ClickHouseSettings | None = None,
) -> Client:
    """Return an authenticated ClickHouse client using env-driven settings."""
    settings = settings or get_clickhouse_settings()
    return clickhouse_connect.get_client(
        host=settings.host,
        port=settings.port,
        username=settings.username,
        password=settings.password,
        database=settings.database,
        secure=settings.secure,
    )


def ping_clickhouse(client: Client | None = None) -> bool:
    """Return True if the ClickHouse connection succeeds."""
    client = client or create_clickhouse_client()
    client.command("SELECT 1")
    return True
