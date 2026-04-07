"""High-level orchestration for phase 1 SSID consolidation collection."""

from __future__ import annotations

import logging
import os
import sqlite3
from datetime import UTC, datetime, timedelta
from typing import Any

from .cache import CacheManager
from .collector import Collector
from .exporter import Exporter

LOGGER = logging.getLogger(__name__)


class SSIDTemplateConsolidationManager:
    """Coordinate collection, cache refresh, and export generation for phase 1."""

    def __init__(
        self,
        collector: Collector | None = None,
        cache: CacheManager | None = None,
        exporter: Exporter | None = None,
        cache_minutes: int = 60,
    ) -> None:
        """Construct the manager with injectable collector, cache, and exporter helpers."""
        self.collector = collector or Collector()
        self.cache = cache or CacheManager()
        self.exporter = exporter or Exporter()
        self.cache_minutes = self._resolve_cache_minutes(cache_minutes)

    def _resolve_cache_minutes(self, default_minutes: int) -> int:
        """Resolve the cache freshness threshold from the environment or fallback value."""
        try:
            return int(
                os.environ.get(
                    "SSID_CONSOLIDATION_CACHE_MINUTES",
                    str(default_minutes),
                )
            )
        except ValueError:
            LOGGER.warning(
                "SSIDTemplateConsolidationManager: invalid cache minutes; using %d",
                default_minutes,
            )
            return default_minutes

    def _now(self) -> datetime:
        """Return the current UTC time as a timezone-aware datetime."""
        return datetime.now(UTC)

    def _parse_collected_at(self, collected_at: str) -> datetime:
        """Parse a cached timestamp and normalize naive timestamps to UTC."""
        parsed = datetime.fromisoformat(collected_at)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed

    def _extract_cached_rows(self, cached_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return cached row payloads from the stored cache structure."""
        return [entry["data"] for entry in cached_rows if isinstance(entry.get("data"), dict)]

    def _get_cached_result(
        self,
        now: datetime,
        force_refresh: bool,
    ) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]:
        """Return cached rows and metadata when the cache is fresh enough to reuse."""
        cached_rows = self.cache.get_all()
        if force_refresh or not cached_rows:
            return None, None
        collected_at = cached_rows[0].get("collected_at")
        if not isinstance(collected_at, str):
            raise ValueError("Invalid cached collected_at value")
        age = now - self._parse_collected_at(collected_at)
        if age < timedelta(minutes=self.cache_minutes):
            LOGGER.info("Using cached data collected %s ago", age)
            return self._extract_cached_rows(cached_rows), {
                "cached": True,
                "collected_at": collected_at,
            }
        return None, None

    def _save_cache(self, rows: list[dict[str, Any]], collected_at: str) -> None:
        """Persist collected rows to the phase 1 cache, logging recoverable failures."""
        try:
            self.cache.save_rows(rows, collected_at=collected_at)
        except (OSError, sqlite3.Error, TypeError, ValueError):
            LOGGER.exception("SSIDTemplateConsolidationManager: failed to save rows to cache")

    def _export_rows(self, rows: list[dict[str, Any]]) -> dict[str, str] | None:
        """Write export artifacts and return their paths when successful."""
        try:
            return self.exporter.write(rows)
        except (OSError, sqlite3.Error, TypeError, ValueError):
            LOGGER.exception("SSIDTemplateConsolidationManager: export failed")
            return None

    def clear_cache(self) -> None:
        """Clear cached phase 1 data so the next collection must refresh from source."""
        self.cache.clear()

    def phase1_collect(
        self,
        target_ssid: str,
        force_refresh: bool = False,
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """Collect phase 1 data, reusing fresh cache entries unless refresh is forced."""
        now = self._now()
        try:
            cached_rows, cached_meta = self._get_cached_result(now, force_refresh)
        except (TypeError, ValueError):
            LOGGER.exception(
                "SSIDTemplateConsolidationManager: failed to validate cache freshness",
            )
        else:
            if cached_rows is not None and cached_meta is not None:
                return cached_rows, cached_meta
        rows = self.collector.collect(target_ssid)
        self._save_cache(rows, now.isoformat())
        return rows, {"cached": False, "out": self._export_rows(rows)}
