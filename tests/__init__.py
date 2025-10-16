"""Test package initialization with deterministic environment defaults."""

from __future__ import annotations

import os
from pathlib import Path

# Use an isolated SQLite database during tests so the core application can remain
# configured for PostgreSQL without pulling in the psycopg2 driver.
_TEST_DB_PATH = Path(os.environ.get("TEST_SQLITE_PATH", "./tests/test_app.db"))
_TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

os.environ.setdefault("DB_DRIVER", "sqlite")
os.environ.setdefault("DB_NAME", _TEST_DB_PATH.stem)
os.environ.setdefault("SQLALCHEMY_DATABASE_URI", f"sqlite:///{_TEST_DB_PATH}")
os.environ.setdefault("MPLBACKEND", "Agg")

# Disable telemetry-heavy defaults that slow tests when left enabled.
os.environ.setdefault("CACHE_ENABLED", "false")
os.environ.setdefault("METRICS_ENABLED", "false")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
