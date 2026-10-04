"""Shared runtime settings for source packages.

Why:
    Source packages must not read tuning values through ``MistHelper``.
    This module owns the settings that source packages can import directly.
"""

from __future__ import annotations  # Allow modern annotations without runtime cost.

import os  # Read operator-provided settings from the environment.
from typing import Any  # Type the shared mutable API usage cache.

CSV_FRESHNESS_MINUTES: int = int(os.getenv("CSV_FRESHNESS_MINUTES", "15"))  # Keep the cache age setting in src.
DEFAULT_API_PAGE_LIMIT: int = 1000  # Keep the safe Mist API page size available before startup.
API_REQUEST_MAX_RETRIES: int = int(os.getenv("API_REQUEST_MAX_RETRIES", "3"))  # Keep API retry count in src.
API_REQUEST_RETRY_DELAY: float = float(os.getenv("API_REQUEST_RETRY_DELAY", "5.0"))  # Keep API retry delay in src.
DATABASE_PATH: str = os.getenv("MISTHELPER_DB_PATH", "data/mist_data.db")  # Keep the SQLite path with settings.
IS_TEST_MODE: bool = False  # Keep the default test mode state out of MistHelper.
LAST_SELECTED_SITE_ID: str | None = None  # Keep prompt selection state available to source packages.
api_usage_cache: dict[str, Any] = {}  # Share one quota cache across source packages.
