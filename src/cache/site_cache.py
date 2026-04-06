"""Simple per-site in-memory cache with TTL.

This cache is intentionally minimal and test-friendly: accepts an optional
fetcher callable to populate entries when absent or stale.
"""
import threading
import time
from typing import Optional, List, Dict

DEFAULT_TTL = 3600


class SiteCache:
    def __init__(self, ttl_seconds: int = DEFAULT_TTL):
        self.ttl = ttl_seconds
        self._store = {}  # key -> (value, fetched_at)
        self._locks = {}
        self._global_lock = threading.Lock()

    def _get_lock(self, key: str):
        with self._global_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]

    def get(self, key: str, force_refresh: bool = False, fetcher: Optional[callable] = None) -> Optional[List[Dict]]:
        """Return cached value or populate via fetcher when provided.

        - key: arbitrary cache key (e.g., 'all_sites' or site_id)
        - fetcher: callable that returns the value when cache miss/refresh required
        """
        if not force_refresh:
            entry = self._store.get(key)
            if entry and (time.time() - entry[1]) < self.ttl:
                return entry[0]
        lock = self._get_lock(key)
        with lock:
            entry = self._store.get(key)
            if not force_refresh and entry and (time.time() - entry[1]) < self.ttl:
                return entry[0]
            if fetcher is None:
                return None
            value = fetcher()
            self._store[key] = (value, time.time())
            return value

    def set(self, key: str, value: List[Dict]) -> None:
        with self._get_lock(key):
            self._store[key] = (value, time.time())

    def is_fresh(self, key: str) -> bool:
        entry = self._store.get(key)
        if not entry:
            return False
        return (time.time() - entry[1]) < self.ttl

    def age_seconds(self, key: str) -> Optional[float]:
        entry = self._store.get(key)
        if not entry:
            return None
        return time.time() - entry[1]

    def force_refresh(self, key: str) -> None:
        if key in self._store:
            del self._store[key]

    def clear(self) -> None:
        with self._global_lock:
            self._store.clear()
            self._locks.clear()
