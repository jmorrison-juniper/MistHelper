"""Unit tests for the statistics roll-up of one comparison.

Why:
    The statistics region is the first thing an operator reads, so a wrong
    number here sends a healthy upgrade back or lets a broken one through. The
    client return rate is the number that decides, and it must count a
    ``moved`` client as returned. A rate that treats a roam as a loss reports a
    failure on every busy site.

    Every test feeds plain records. No test opens a socket, reads the ``.env``
    file, or names a real credential.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.compare import clients as client_compare
from src.upgrade_portal.compare import diff as device_compare
from src.upgrade_portal.compare import statistics

MASTER_MAC = "0011220000aa"
MEMBER_MAC = "0011220000bb"
CLIENT_MAC = "aabbccddeeff"

OLD_VERSION = "21.4R3.15"
NEW_VERSION = "23.4R2.13"

# WHY: The nine names of contracts/http-api.md, plus the two that
#      data-model.md section 7.4 adds.
CONTRACT_NAMES = (
    "devices_unchanged",
    "devices_changed",
    "devices_added",
    "devices_removed",
    "clients_present",
    "clients_moved",
    "clients_added",
    "clients_missing",
    "client_return_rate",
)


def _device_delta(mac: str, outcome: str, field: str = "") -> device_compare.DeviceDelta:
    """Return one device difference record.

    Why:
        The roll-up reads the outcome and the change list alone, so a builder
        with two arguments covers every case the counters meet.

    Args:
        mac: The device address.
        outcome: One device outcome.
        field: The name of one changed field, when the record holds one.

    Returns:
        One device difference record.
    """
    changes: tuple[device_compare.FieldChange, ...] = ()
    if field:
        changes = (device_compare.FieldChange(field=field, before=OLD_VERSION, after=NEW_VERSION),)
    return device_compare.DeviceDelta(mac=mac, outcome=outcome, changes=changes)


def _client_deltas(present: int, moved: int, added: int, missing: int) -> tuple[client_compare.ClientDelta, ...]:
    """Return one client difference record for each requested outcome.

    Why:
        Every rate test states four counts. Building the records from the four
        counts keeps the arithmetic under test on one line.

    Args:
        present: How many ``present`` records to build.
        moved: How many ``moved`` records to build.
        added: How many ``added`` records to build.
        missing: How many ``missing`` records to build.

    Returns:
        The client difference records.
    """
    counts = (
        (client_compare.OUTCOME_PRESENT, present),
        (client_compare.OUTCOME_MOVED, moved),
        (client_compare.OUTCOME_ADDED, added),
        (client_compare.OUTCOME_MISSING, missing),
    )
    deltas: list[client_compare.ClientDelta] = []
    for outcome, total in counts:
        deltas.extend(client_compare.ClientDelta(mac=CLIENT_MAC, outcome=outcome) for _ in range(total))
    return tuple(deltas)


# ---------------------------------------------------------------------------
# The client return rate
# ---------------------------------------------------------------------------


def test_a_moved_client_counts_as_a_return() -> None:
    """A client that roamed is on the network, so the rate stays whole."""
    counts = statistics.ClientCounts(present=0, moved=100, added=0, missing=0)

    assert counts.return_rate == 1.0


def test_a_missing_client_lowers_the_rate() -> None:
    """A client that never came back lowers the rate."""
    counts = statistics.ClientCounts(present=1840, moved=96, added=12, missing=30)

    assert counts.return_rate == pytest.approx(0.985)


def test_an_added_client_never_joins_the_rate() -> None:
    """A client that was not there before never changes the rate."""
    with_added = statistics.ClientCounts(present=50, moved=0, added=1000, missing=50)
    without_added = statistics.ClientCounts(present=50, moved=0, added=0, missing=50)

    assert with_added.return_rate == without_added.return_rate == 0.5


def test_a_site_with_no_client_reports_a_whole_rate() -> None:
    """Nothing was lost when no client was there before."""
    assert statistics.ClientCounts().return_rate == statistics.EMPTY_RETURN_RATE
    assert statistics.ClientCounts().return_rate == 1.0


def test_a_total_loss_reports_a_rate_of_zero() -> None:
    """Every client of the pre-check capture missing gives a rate of zero."""
    assert statistics.ClientCounts(missing=40).return_rate == 0.0


def test_the_rate_rounds_to_three_places() -> None:
    """The rate holds a tenth of one percent and no more."""
    counts = statistics.ClientCounts(present=2, moved=0, added=0, missing=1)

    assert counts.return_rate == 0.667


def test_the_pre_check_total_skips_the_added_clients() -> None:
    """The divisor counts the clients of the pre-check capture alone."""
    counts = statistics.ClientCounts(present=10, moved=5, added=99, missing=5)

    assert counts.seen_before == 20


# ---------------------------------------------------------------------------
# The roll-up
# ---------------------------------------------------------------------------


def test_the_roll_up_counts_every_device_outcome() -> None:
    """The device counts follow the outcome of each device record."""
    comparison = device_compare.DeviceComparison(
        deltas=(
            _device_delta(MASTER_MAC, device_compare.OUTCOME_UNCHANGED),
            _device_delta(MEMBER_MAC, device_compare.OUTCOME_CHANGED, field="version"),
            _device_delta("0011220000cc", device_compare.OUTCOME_CHANGED, field="ip"),
            _device_delta("0011220000dd", device_compare.OUTCOME_ADDED),
            _device_delta("0011220000ee", device_compare.OUTCOME_REMOVED),
        )
    )

    counts = statistics.count_devices(comparison)

    assert counts.unchanged == 1
    assert counts.changed == 2
    assert counts.added == 1
    assert counts.removed == 1


def test_the_version_count_never_matches_the_changed_count() -> None:
    """A device that changed only its address never counts as upgraded."""
    comparison = device_compare.DeviceComparison(
        deltas=(
            _device_delta(MASTER_MAC, device_compare.OUTCOME_CHANGED, field="version"),
            _device_delta(MEMBER_MAC, device_compare.OUTCOME_CHANGED, field="ip"),
        )
    )

    counts = statistics.count_devices(comparison)

    assert counts.changed == 2
    assert counts.version_changed == 1


def test_the_roll_up_counts_every_client_outcome() -> None:
    """The client counts follow the outcome of each client record."""
    comparison = client_compare.ClientComparison(deltas=_client_deltas(present=3, moved=2, added=1, missing=4))

    counts = statistics.count_clients(comparison)

    assert (counts.present, counts.moved, counts.added, counts.missing) == (3, 2, 1, 4)


def test_the_whole_roll_up_carries_both_halves_and_the_time() -> None:
    """One call returns the device counts, the client counts, and the time."""
    devices = device_compare.DeviceComparison(deltas=(_device_delta(MASTER_MAC, device_compare.OUTCOME_UNCHANGED),))
    clients = client_compare.ClientComparison(deltas=_client_deltas(present=1, moved=1, added=0, missing=0))

    result = statistics.build_statistics(devices, clients, elapsed_seconds=1800.0)

    assert result.devices.unchanged == 1
    assert result.clients.moved == 1
    assert result.elapsed_seconds == 1800.0


def test_a_negative_elapsed_time_never_reaches_the_report() -> None:
    """A clock that ran backwards reports zero rather than a negative time."""
    empty_devices = device_compare.DeviceComparison()
    empty_clients = client_compare.ClientComparison()

    result = statistics.build_statistics(empty_devices, empty_clients, elapsed_seconds=-10.0)

    assert result.elapsed_seconds == 0.0


# ---------------------------------------------------------------------------
# The flat dictionary form
# ---------------------------------------------------------------------------


def test_the_flat_form_holds_every_contract_name() -> None:
    """The flat form names each statistic of the comparison contract."""
    flat = statistics.ComparisonStatistics().to_dict()

    assert set(CONTRACT_NAMES) <= set(flat)


def test_the_flat_form_holds_the_version_count_and_the_elapsed_time() -> None:
    """The data model adds the version count and the elapsed time."""
    flat = statistics.ComparisonStatistics().to_dict()

    assert "devices_version_changed" in flat
    assert "elapsed_seconds" in flat


def test_the_name_list_matches_the_flat_form() -> None:
    """The report order names every key of the flat form and no other."""
    flat = statistics.ComparisonStatistics().to_dict()

    assert set(statistics.STATISTIC_NAMES) == set(flat)


def test_the_flat_form_reports_the_rate_beside_the_counts() -> None:
    """The rate travels with the four client counts."""
    counts = statistics.ClientCounts(present=1840, moved=96, added=12, missing=30)

    flat = statistics.ComparisonStatistics(clients=counts).to_dict()

    assert flat["clients_moved"] == 96
    assert flat["client_return_rate"] == pytest.approx(0.985)


# ---------------------------------------------------------------------------
# The elapsed time
# ---------------------------------------------------------------------------


def test_the_elapsed_time_spans_the_whole_maintenance_window() -> None:
    """The window runs from the pre-check start to the post-check finish."""
    before: dict[str, Any] = {"started_at": "2026-08-19T01:00:00+00:00"}
    after: dict[str, Any] = {"finished_at": "2026-08-19T01:30:00+00:00"}

    assert statistics.elapsed_seconds_between(before, after) == 1800.0


def test_the_elapsed_time_falls_back_to_the_post_check_start() -> None:
    """A post-check capture with no finish moment still reports a window."""
    before: dict[str, Any] = {"started_at": "2026-08-19T01:00:00+00:00"}
    after: dict[str, Any] = {"started_at": "2026-08-19T01:20:00+00:00"}

    assert statistics.elapsed_seconds_between(before, after) == 1200.0


def test_an_unreadable_moment_falls_back_to_the_two_durations() -> None:
    """A record with no readable moment reports the sum of the durations."""
    before: dict[str, Any] = {"started_at": "not a moment", "duration_seconds": 12.5}
    after: dict[str, Any] = {"finished_at": "not a moment", "duration_seconds": 7.5}

    assert statistics.elapsed_seconds_between(before, after) == 20.0


def test_a_mixed_time_zone_falls_back_rather_than_raising() -> None:
    """One moment with a time zone and one without never raises."""
    before: dict[str, Any] = {"started_at": "2026-08-19T01:00:00+00:00", "duration_seconds": 5.0}
    after: dict[str, Any] = {"finished_at": "2026-08-19T01:30:00", "duration_seconds": 5.0}

    assert statistics.elapsed_seconds_between(before, after) == 10.0


def test_a_clock_that_ran_backwards_reports_zero() -> None:
    """A post-check moment before the pre-check moment reports zero."""
    before: dict[str, Any] = {"started_at": "2026-08-19T02:00:00+00:00"}
    after: dict[str, Any] = {"finished_at": "2026-08-19T01:00:00+00:00"}

    assert statistics.elapsed_seconds_between(before, after) == 0.0


def test_a_capture_with_no_moment_at_all_reports_zero() -> None:
    """A record with no moment and no duration reports zero."""
    assert statistics.elapsed_seconds_between({}, {}) == 0.0


def test_a_true_duration_never_reads_as_one_second() -> None:
    """A stored true value is not a duration."""
    before: dict[str, Any] = {"duration_seconds": True}

    assert statistics.elapsed_seconds_between(before, {}) == 0.0
