"""The statistics roll-up of one comparison.

Why:
    The operator reads the statistics region first and the two tables second.
    The region must therefore answer the upgrade questions on its own. How
    many devices took the new firmware? How many clients came back? How long
    did the whole run take?

    The client return rate counts a ``moved`` client as returned. A client
    that roamed to another access point is on the network. Counting the roam as
    a loss would raise a false alarm on every busy site.

    A digest match skips a section, and the comparison then reads no row
    there. The device counts still report the truth. The device comparison
    counts the devices of the skipped section, and the digest proves every
    one of them unchanged. A client count of zero after a skip still means
    the comparison did no work in that section. The comparison body carries
    ``skipped_sections`` beside these counts for that reason.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.upgrade_portal.compare import clients as client_compare
from src.upgrade_portal.compare import diff as device_compare

logger = logging.getLogger(__name__)

STARTED_AT_KEY = "started_at"
FINISHED_AT_KEY = "finished_at"
DURATION_KEY = "duration_seconds"

# WHY: The contract prints a rate such as 0.984. Three places hold a tenth of
# one percent, which is finer than any site the portal reads.
RETURN_RATE_PLACES = 3

# WHY: Nothing was lost when no client was there before, so the rate is whole.
# A zero rate would read as a total loss and would raise a false alarm.
EMPTY_RETURN_RATE = 1.0

# The flat statistic names, in report order. The template builds one test
# identifier for each name (contracts/ui-testids.md:132).
STATISTIC_NAMES = (
    "devices_unchanged",
    "devices_changed",
    "devices_added",
    "devices_removed",
    "devices_version_changed",
    "clients_present",
    "clients_moved",
    "clients_added",
    "clients_missing",
    "client_return_rate",
    "elapsed_seconds",
)


# ---------------------------------------------------------------------------
# The count records
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DeviceCounts:
    """The device counts of one comparison.

    Why:
        The four outcomes and the version count answer the upgrade question
        together. A device may change its address without taking new
        firmware, so the version count is its own number and never the same
        as ``changed``.

    Attributes:
        unchanged: Devices whose compared fields all match.
        changed: Devices with at least one differing field.
        added: Devices in the post-check capture only.
        removed: Devices in the pre-check capture only.
        version_changed: Devices whose firmware version differs.
    """

    unchanged: int = 0
    changed: int = 0
    added: int = 0
    removed: int = 0
    version_changed: int = 0

    def to_dict(self) -> dict[str, int]:
        """Return the device counts under their flat contract names.

        Why:
            The comparison body names each count with a ``devices_`` prefix.
            One converter keeps the prefix in a single place.

        Returns:
            A dictionary of five counts.
        """
        return {
            "devices_unchanged": self.unchanged,
            "devices_changed": self.changed,
            "devices_added": self.added,
            "devices_removed": self.removed,
            "devices_version_changed": self.version_changed,
        }


@dataclass(frozen=True, slots=True)
class ClientCounts:
    """The client counts of one comparison.

    Why:
        The four outcomes carry the whole client result. ``moved`` is its own
        number, so a reader can never add it into a loss by mistake.

    Attributes:
        present: Clients on the same serving device in both captures.
        moved: Clients on a different serving device.
        added: Clients in the post-check capture only.
        missing: Clients in the pre-check capture only.
    """

    present: int = 0
    moved: int = 0
    added: int = 0
    missing: int = 0

    @property
    def seen_before(self) -> int:
        """Return how many clients the pre-check capture held.

        Why:
            The return rate divides by this number. An added client was not
            there before, so it never joins the total.

        Returns:
            The number of clients in the pre-check capture.
        """
        return self.present + self.moved + self.missing

    @property
    def return_rate(self) -> float:
        """Return the share of pre-check clients that came back.

        Why:
            This is the headline number of the whole comparison. A client
            that roamed is on the network, so ``moved`` counts as a return.

        Returns:
            A value from 0.0 to 1.0, rounded to three places.
        """
        total = self.seen_before
        if total == 0:
            return EMPTY_RETURN_RATE
        return round((self.present + self.moved) / total, RETURN_RATE_PLACES)

    def to_dict(self) -> dict[str, Any]:
        """Return the client counts under their flat contract names.

        Why:
            The comparison body names each count with a ``clients_`` prefix
            and carries the rate beside them.

        Returns:
            A dictionary of four counts and the return rate.
        """
        return {
            "clients_present": self.present,
            "clients_moved": self.moved,
            "clients_added": self.added,
            "clients_missing": self.missing,
            "client_return_rate": self.return_rate,
        }


@dataclass(frozen=True, slots=True)
class ComparisonStatistics:
    """Every statistic of one comparison.

    Why:
        The Five-Item Rule caps a dataclass at 5 fields, and the comparison
        reports 11 numbers. Grouping the numbers by subject keeps each record
        inside the cap and lets a caller pass one group to one table.

    Attributes:
        devices: The device counts.
        clients: The client counts.
        elapsed_seconds: The time from the first capture start to the last
            capture finish.
    """

    devices: DeviceCounts = field(default_factory=DeviceCounts)
    clients: ClientCounts = field(default_factory=ClientCounts)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Return every statistic as one flat dictionary.

        Why:
            The comparison endpoint returns a flat ``statistics`` object, and
            the template reads the same flat names to build a test identifier
            for each number.

        Returns:
            A dictionary with every name of ``STATISTIC_NAMES``.
        """
        flat: dict[str, Any] = {}
        flat.update(self.devices.to_dict())
        flat.update(self.clients.to_dict())
        flat["elapsed_seconds"] = self.elapsed_seconds
        return flat


# ---------------------------------------------------------------------------
# The elapsed time
# ---------------------------------------------------------------------------


def _parse_moment(value: object) -> datetime | None:
    """Return one stored moment as a date and time.

    Why:
        A capture writes a moment as text. A record written by an older build
        may hold a form this reader cannot parse, and the comparison must
        still render. The reader therefore reports the gap and returns None.

    Args:
        value: The stored text.

    Returns:
        The moment, or None when the value is not a readable moment.
    """
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        logger.warning("Upgrade portal could not read a capture moment")
        return None


def _duration_of(capture: Mapping[str, Any]) -> float:
    """Return the stored duration of one capture in seconds.

    Why:
        The elapsed time falls back to the two stored durations when the two
        moments do not subtract. The fallback under reports the wait between
        the captures, which is safer than reporting nothing.

    Args:
        capture: One capture document.

    Returns:
        The duration in seconds, or 0.0 when the capture holds none.
    """
    value = capture.get(DURATION_KEY)
    if isinstance(value, bool) or not isinstance(value, int | float):
        return 0.0
    return float(value)


def _comparable(start: datetime, end: datetime) -> bool:
    """Return whether two moments subtract without an error.

    Why:
        Python refuses to subtract a moment with a time zone from a moment
        without one. The guard keeps that refusal out of the comparison.

    Args:
        start: The earlier moment.
        end: The later moment.

    Returns:
        True when both moments carry a time zone or neither does.
    """
    return (start.tzinfo is None) == (end.tzinfo is None)


def elapsed_seconds_between(before: Mapping[str, Any], after: Mapping[str, Any]) -> float:
    """Return the elapsed time of the whole run in seconds.

    Why:
        The operator wants the length of the maintenance window, not the
        length of one read. The window runs from the start of the pre-check
        to the finish of the post-check and includes the upgrade itself.

    Args:
        before: The pre-check capture.
        after: The post-check capture.

    Returns:
        The elapsed seconds, never below zero.
    """
    start = _parse_moment(before.get(STARTED_AT_KEY))
    end = _parse_moment(after.get(FINISHED_AT_KEY)) or _parse_moment(after.get(STARTED_AT_KEY))
    if start is None or end is None or not _comparable(start, end):
        return _duration_of(before) + _duration_of(after)
    return max((end - start).total_seconds(), 0.0)


# ---------------------------------------------------------------------------
# The roll-up
# ---------------------------------------------------------------------------


def count_devices(comparison: device_compare.DeviceComparison) -> DeviceCounts:
    """Return the device counts of one device comparison.

    Why:
        The counter reads the outcome of each record, so the counts can never
        drift from the table that the operator reads beside them.

        A digest match leaves no record to read. The counter then adds the
        proved count, because the match proves every device of that section
        unchanged. This count is the number that shows an upgrade did no
        harm, so it must never read as zero for a site full of devices.

    Args:
        comparison: The device half of the comparison.

    Returns:
        The five device counts.
    """
    deltas = comparison.deltas
    read = device_compare.count_outcome(deltas, device_compare.OUTCOME_UNCHANGED)  # WHY: The rows the counter saw.
    return DeviceCounts(
        unchanged=read + comparison.proved_unchanged,  # WHY: One of the two numbers is always zero.
        changed=device_compare.count_outcome(deltas, device_compare.OUTCOME_CHANGED),
        added=device_compare.count_outcome(deltas, device_compare.OUTCOME_ADDED),
        removed=device_compare.count_outcome(deltas, device_compare.OUTCOME_REMOVED),
        version_changed=device_compare.count_version_changes(deltas),
    )


def count_clients(comparison: client_compare.ClientComparison) -> ClientCounts:
    """Return the client counts of one client comparison.

    Why:
        The counter reads the outcome of each record, so ``moved`` stays its
        own number and never joins the loss count.

        A digest match leaves no record to read. The counter then adds the
        proved count to the present count, because the match proves every
        client of that section present. This count is the number that shows an
        upgrade returned the clients, so it must never read as zero for a busy
        site.

    Args:
        comparison: The client half of the comparison.

    Returns:
        The four client counts.
    """
    deltas = comparison.deltas
    read = client_compare.count_outcome(deltas, client_compare.OUTCOME_PRESENT)  # WHY: The rows the counter saw.
    return ClientCounts(
        present=read + comparison.proved_present,  # WHY: One of the two numbers is always zero.
        moved=client_compare.count_outcome(deltas, client_compare.OUTCOME_MOVED),
        added=client_compare.count_outcome(deltas, client_compare.OUTCOME_ADDED),
        missing=client_compare.count_outcome(deltas, client_compare.OUTCOME_MISSING),
    )


def build_statistics(
    devices: device_compare.DeviceComparison,
    clients: client_compare.ClientComparison,
    elapsed_seconds: float = 0.0,
) -> ComparisonStatistics:
    """Return every statistic of one comparison.

    Why:
        The route lane builds the two halves and then needs one call for the
        whole statistics region. Keeping the roll-up here keeps the counting
        rules out of the route.

    Args:
        devices: The device half of the comparison.
        clients: The client half of the comparison.
        elapsed_seconds: The elapsed time of the whole run.

    Returns:
        The device counts, the client counts, and the elapsed time.
    """
    statistics = ComparisonStatistics(
        devices=count_devices(devices),
        clients=count_clients(clients),
        elapsed_seconds=max(elapsed_seconds, 0.0),
    )
    logger.info(
        "Upgrade portal rolled up %s unchanged devices, %s changed devices, and %s missing clients",
        statistics.devices.unchanged,
        statistics.devices.changed,
        statistics.clients.missing,
    )
    return statistics


__all__ = [
    "DURATION_KEY",
    "EMPTY_RETURN_RATE",
    "FINISHED_AT_KEY",
    "RETURN_RATE_PLACES",
    "STARTED_AT_KEY",
    "STATISTIC_NAMES",
    "ClientCounts",
    "ComparisonStatistics",
    "DeviceCounts",
    "build_statistics",
    "count_clients",
    "count_devices",
    "elapsed_seconds_between",
]
