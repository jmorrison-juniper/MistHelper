import os
from datetime import datetime, timedelta
from .collector import Collector
from .cache import CacheManager
from .exporter import Exporter
import logging


class SSIDTemplateConsolidationManager:
    """High-level manager orchestrating Phase 1 collection, cache, and export."""

    def __init__(self, collector: Collector = None, cache: CacheManager = None, exporter: Exporter = None, cache_minutes: int = 60):
        self.collector = collector or Collector()
        self.cache = cache or CacheManager()
        self.exporter = exporter or Exporter()
        try:
            self.cache_minutes = int(os.environ.get("SSID_CONSOLIDATION_CACHE_MINUTES", str(cache_minutes)))
        except Exception:
            self.cache_minutes = cache_minutes

    def phase1_collect(self, target_ssid: str, force_refresh: bool = False):
        """Collect Phase 1 data; use cache if fresh unless `force_refresh` is True.

        Returns (rows, meta) where `meta` contains keys `cached` and `out`.
        """
        now = datetime.utcnow()
        cached = self.cache.get_all()
        if cached and not force_refresh:
            # check freshness by examining first item's collected_at
            try:
                collected_at = cached[0].get("collected_at")
                collected_dt = datetime.fromisoformat(collected_at)
                age = now - collected_dt
                if age < timedelta(minutes=self.cache_minutes):
                    logging.info("Using cached data collected %s ago", age)
                    return [c["data"] for c in cached], {"cached": True, "collected_at": collected_at}
            except Exception:
                logging.exception("Failed to validate cache freshness; falling back to fresh collection")

        # perform collection
        rows = self.collector.collect(target_ssid)

        # persist to cache
        try:
            self.cache.save_rows(rows, collected_at=now.isoformat())
        except Exception:
            logging.exception("Failed to save rows to cache")

        # export
        out = None
        try:
            out = self.exporter.write(rows)
        except Exception:
            logging.exception("Export failed")

        return rows, {"cached": False, "out": out}
