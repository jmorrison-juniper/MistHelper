"""Shared API usage cache for source packages.

Why:
    Rate limiting needs one mutable cache. Source packages must import that
    cache from a leaf module instead of reading ``MistHelper._api_usage_cache``.
"""

from __future__ import annotations  # Keep annotations stable across Python versions.

from typing import Any  # Type the mutable cache values.

api_usage_cache: dict[str, Any] = {}  # Keep one process-local quota view for all source package callers.
