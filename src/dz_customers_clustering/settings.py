from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


def _get_bool_env(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in {"1", "true", "t", "yes", "y"}


@dataclass(frozen=True)
class ClickHouseSettings:
    host: str
    port: int
    username: str
    password: str
    database: str
    secure: bool = True


def get_clickhouse_settings() -> ClickHouseSettings:
    return ClickHouseSettings(
        host=_require_env("CLICKHOUSE_HOST"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
        username=_require_env("CLICKHOUSE_USERNAME"),
        password=_require_env("CLICKHOUSE_PASSWORD"),
        database=_require_env("CLICKHOUSE_DATABASE"),
        secure=_get_bool_env("CLICKHOUSE_SECURE", True),
    )
