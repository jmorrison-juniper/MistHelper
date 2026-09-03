"""Holds the last Mist reading and decides when to read again.

Why:
    A monitoring system polls on its own schedule. Ten pollers on a one minute
    interval would drive 14,400 Mist passes a day if each poll called Mist
    Cloud, and the Mist rate limit would stop the whole tool. The cache breaks
    that link. A poll reads memory, and only the refresh interval reaches Mist
    Cloud.

    The cache also decides what happens when a Mist call fails. It keeps the
    last good reading and reports its age, because a NOC that suddenly sees no
    devices cannot tell an outage from a failed refresh. The age and the
    `mist_scrape_success` reading make the difference visible.

    This module replaces the MongoDB store of the upstream `mist_snmp_gateway`.
    The upstream keeps the reading in a database that it never queries and never
    reads after the next refresh, so the database earns nothing and costs a
    second service, a second set of credentials, and an encryption key.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

from src.metrics_gateway.catalog import MetricCatalog, MetricScope
from src.metrics_gateway.collector import MistMetricsCollector
from src.metrics_gateway.samples import MetricSample, MetricSnapshot

logger = logging.getLogger(__name__)

DEFAULT_REFRESH_SECONDS = 900.0  # Fifteen minutes, which is the upstream default sync interval.
MINIMUM_REFRESH_SECONDS = 60.0  # A shorter interval would spend the Mist rate limit budget on repeat readings.

HEALTH_SUCCESS = "mist_scrape_success"  # 1 after a good pass, 0 after a failed one.
HEALTH_AGE = "mist_scrape_age_seconds"  # The age of the reading the caller is about to read.
HEALTH_DURATION = "mist_scrape_duration_seconds"  # The cost of the last pass, for capacity planning.


class MetricsCache:
    """Serves the last Mist reading and refreshes it when it grows stale."""

    def __init__(
        self,
        collector: MistMetricsCollector,
        refresh_seconds: float = DEFAULT_REFRESH_SECONDS,
        clock: Callable[[], float] = time.time,
    ) -> None:
        """Store the collector, the refresh interval, and the clock.

        Args:
            collector: The object that reads Mist Cloud.
            refresh_seconds: The age at which a reading becomes stale. A value
                below one minute is raised to one minute.
            clock: The source of the current time. A test passes a stand-in so
                that it can age the cache without waiting.
        """
        self._collector = collector  # The one object that touches Mist Cloud.
        self._refresh_seconds = max(refresh_seconds, MINIMUM_REFRESH_SECONDS)  # Hold the floor on the interval.
        self._clock = clock  # A test replaces this to age the cache in an instant.
        self._lock = threading.Lock()  # Two pollers can arrive together, and only one may start a pass.
        self._snapshot = MetricSnapshot()  # The last good reading. It starts empty.
        self._collected_at = 0.0  # The moment of the last good pass, read from the clock this cache was given.
        self._last_attempt = 0.0  # The moment of the last pass, good or failed.
        self._last_ok = False  # The outcome of the last pass.
        self._catalog = MetricCatalog()  # The definitions of the three health readings.
        if refresh_seconds < MINIMUM_REFRESH_SECONDS:  # Tell the operator that the request did not hold.
            logger.warning(
                "The refresh interval %.0f seconds is below the floor, so the cache uses %.0f seconds",
                refresh_seconds,
                MINIMUM_REFRESH_SECONDS,
            )

    @property
    def refresh_seconds(self) -> float:
        """Return the refresh interval the cache applies.

        Returns:
            The interval in seconds, after the one minute floor.
        """
        return self._refresh_seconds

    def age_seconds(self) -> float:
        """Return the age of the reading the cache holds.

        Why:
            The age is measured against the clock this cache was given, and not
            against the moment the collector stamped on the snapshot. The two
            can differ, because a test drives the cache with a stand-in clock.
            A mixed measurement would report an age of several hours during a
            test that moved its clock forward by two minutes.

        Returns:
            The seconds since the last good pass, or an infinity when the cache
            has never held a good reading.
        """
        if not self._collected_at:  # The cache has never held a good reading.
            return float("inf")
        return max(self._clock() - self._collected_at, 0.0)  # A clock that steps back must not go negative.

    def _is_stale(self) -> bool:
        """Report whether the cache must read Mist Cloud again.

        Returns:
            True when no pass has run, or when the last attempt is older than
            the refresh interval.
        """
        if not self._last_attempt:  # No pass has ever run, so the cache must fill itself.
            return True
        return (self._clock() - self._last_attempt) >= self._refresh_seconds

    def snapshot(self) -> MetricSnapshot:
        """Return the reading to serve, refreshing it first when it is stale.

        Why:
            The refresh runs under the lock. A second poller that arrives during
            a pass waits and then reads the fresh result, so two pollers never
            start two passes over the same organization.

        Returns:
            The snapshot, with the three gateway health readings appended.
        """
        with self._lock:  # Only one pass may run, however many pollers arrive.
            if self._is_stale():  # A fresh reading serves the poll without a Mist call.
                self._refresh_locked()
            return self._with_health(self._snapshot)

    def refresh_now(self) -> MetricSnapshot:
        """Read Mist Cloud at once, whatever the age of the cache.

        Why:
            A background thread calls this on its own schedule, and an operator
            calls it after a configuration change.

        Returns:
            The snapshot, with the three gateway health readings appended.
        """
        with self._lock:  # The same lock keeps a forced pass and a poll from overlapping.
            self._refresh_locked()
            return self._with_health(self._snapshot)

    def _refresh_locked(self) -> None:
        """Run one pass and keep the result only when the pass succeeded.

        Why:
            A failed pass must never replace a good reading with an empty one. A
            NOC that suddenly sees no devices cannot tell an outage from a
            failed refresh, so the cache keeps the last good reading and lets
            the age reading tell the truth.

        Warning:
            The caller must already hold the lock.
        """
        logger.info("Refresh the Mist metrics cache")  # Log before the pass.
        fresh = self._collector.collect()  # The collector never raises, so no guard is needed here.
        self._last_attempt = self._clock()  # Record the attempt, so a failure does not cause a retry storm.
        self._last_ok = fresh.ok
        if fresh.ok:  # Only a good pass may replace the reading the cache serves.
            self._snapshot = fresh
            self._collected_at = self._last_attempt  # The age runs from this moment, on this cache's own clock.
            logger.debug("The cache now holds %d samples", len(fresh.samples))  # Log the result count.
            return
        logger.error(
            "The metrics pass failed, so the cache keeps a reading that is %.0f seconds old. Reason: %s",
            self.age_seconds(),
            fresh.error or "unknown",
        )

    def _health_samples(self) -> tuple[MetricSample, ...]:
        """Build the three readings that describe the gateway itself.

        Returns:
            The success flag, the reading age, and the duration of the last pass.
        """
        values = {
            HEALTH_SUCCESS: 1.0 if self._last_ok else 0.0,
            HEALTH_AGE: self.age_seconds(),
            HEALTH_DURATION: self._snapshot.duration_seconds,
        }
        built: list[MetricSample] = []  # Collect the readings the catalog defines, and skip any it does not.
        for definition in self._catalog.for_scope(MetricScope.ORG):  # Walk the scalars so the columns stay in order.
            if definition.name in values:  # Only the three health readings are built here.
                built.append(MetricSample(definition=definition, labels=(), value=values[definition.name]))
        return tuple(built)

    def _with_health(self, snapshot: MetricSnapshot) -> MetricSnapshot:
        """Return the snapshot with the gateway health readings appended.

        Why:
            The age changes every second, so it cannot live inside a frozen
            snapshot that the collector built minutes ago. It is measured at
            read time instead, and both output paths therefore report the same
            age for the same poll.

        Args:
            snapshot: The reading the cache holds.

        Returns:
            A new snapshot that carries the health readings as well.
        """
        health = self._health_samples()  # Measure the gateway health at read time.
        # WHY: an infinite age cannot be rendered, and a monitoring system reads it as a parse
        # fault. A cache that never read reports no age at all, and `mist_scrape_success` at 0
        # already tells the operator that no reading exists.
        finite = tuple(item for item in health if item.value != float("inf"))
        return MetricSnapshot(
            samples=snapshot.samples + finite,
            collected_at=snapshot.collected_at,
            duration_seconds=snapshot.duration_seconds,
            ok=self._last_ok,
            error=snapshot.error,
        )
