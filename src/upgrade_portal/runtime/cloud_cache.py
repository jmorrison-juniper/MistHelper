"""Keep one organization list read for a short period.

Why:
    Issue #3210. The site picker, the site post, and the multi-site options
    steps each read the site list and the site statistics of the organization
    again. A live organization of 144 sites answered in 2.2 to 4.0 seconds on
    each view. One short period of reuse removes the repeated reads and keeps
    the list fresh enough for a picker.

    The key holds the operator and the cloud session, so no operator reads a
    list that another credential fetched. An empty answer is never kept,
    because a read that failed once must not hide the sites for the whole
    period. Each answer leaves the cache as a copy, so no caller can change a
    stored record.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import logging  # The portal logs with the standard library only.
import threading  # The server answers requests on several threads.
import time  # The monotonic clock ages each entry.
from collections import OrderedDict  # The oldest entry leaves first when the cache is full.
from collections.abc import Callable  # Types the injected clock.
from typing import Any  # A cloud record is free-form.

logger = logging.getLogger(__name__)  # Keep the cache records under this module name.

CacheKey = tuple[str, str, str, int]  # The operator key, the read name, the organization, and the session identity.


class CloudReadCache:
    """Keep each organization list read for a short period, for one operator."""

    def __init__(self, ttl_seconds: float, limit: int, clock: Callable[[], float] = time.monotonic) -> None:
        """Build one empty cache.

        Args:
            ttl_seconds: The seconds that one answer stays valid.
            limit: The most entries that the cache keeps.
            clock: The time source. A test passes a clock that it can move.
        """
        self._ttl = ttl_seconds  # The age at which an answer is too old.
        self._limit = limit  # The size bound of the cache.
        self._clock = clock  # The one time source of the cache.
        self._entries: OrderedDict[CacheKey, tuple[float, list[dict[str, Any]]]] = OrderedDict()  # Oldest first.
        self._guard = threading.Lock()  # One reader or writer at a time keeps the entries whole.

    def get(self, key: CacheKey) -> list[dict[str, Any]] | None:
        """Return a copy of a fresh answer, or None.

        Args:
            key: The key of the read.

        Returns:
            The kept records, or None when no fresh answer exists.
        """
        with self._guard:  # A writer may change the entries at this moment.
            entry = self._entries.get(key)  # None when the cache holds no answer.
            if entry is None:  # The read never ran, or its answer left the cache.
                return None  # The caller reads the cloud.
            stored_at, records = entry  # The age and the records of the answer.
            if self._clock() - stored_at > self._ttl:  # The answer is too old.
                del self._entries[key]  # Drop it, so the next read refreshes it.
                return None  # The caller reads the cloud.
        logger.debug("cloud cache: reused %s record(s) of %s", len(records), key[1])  # Name the read only.
        return [dict(record) for record in records]  # A copy, so no caller can change the kept records.

    def put(self, key: CacheKey, records: list[dict[str, Any]]) -> None:
        """Keep one answer, unless it is empty.

        Args:
            key: The key of the read.
            records: The records that the cloud answered.
        """
        if not records:  # An empty answer can mean a failed read.
            return  # Never keep it, so the next view reads the cloud again.
        with self._guard:  # A reader may use the entries at this moment.
            self._entries[key] = (self._clock(), [dict(record) for record in records])  # A copy with its age.
            self._entries.move_to_end(key)  # The newest entry leaves last.
            while len(self._entries) > self._limit:  # The cache is full.
                self._entries.popitem(last=False)  # The oldest entry leaves first.
        logger.debug("cloud cache: kept %s record(s) of %s", len(records), key[1])  # Name the read only.

    def clear(self) -> None:
        """Drop every kept answer."""
        with self._guard:  # A reader may use the entries at this moment.
            self._entries.clear()  # The next read of each list reaches the cloud.
