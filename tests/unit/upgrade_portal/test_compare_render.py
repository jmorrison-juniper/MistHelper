"""Unit tests for the comparison view models and the outcome filter.

Why:
    A template must hold no rule, so every decision of the comparison page
    lives in the view module and must be proved here. Two decisions matter
    most. A filter value from the address bar must never empty a table by
    accident, because an empty table reads as a site with no devices. A
    skipped section must reach the page as its own fact, because an empty
    table after a digest skip is not a table with no differences.

    Every test feeds plain records. No test opens a socket, reads the ``.env``
    file, or names a real credential.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.compare import clients as client_compare
from src.upgrade_portal.compare import diff as device_compare
from src.upgrade_portal.compare import render
from src.upgrade_portal.compare import statistics as statistics_module

MASTER_MAC = "0011220000aa"
MEMBER_MAC = "0011220000bb"
CLIENT_MAC = "aabbccddeeff"
OTHER_CLIENT_MAC = "aabbccddee00"


def _device_delta(mac: str, outcome: str) -> device_compare.DeviceDelta:
    """Return one device difference record.

    Why:
        The view reads the outcome and the address alone, so a builder with
        two arguments covers every filter case.

    Args:
        mac: The device address.
        outcome: One device outcome.

    Returns:
        One device difference record.
    """
    return device_compare.DeviceDelta(mac=mac, outcome=outcome, name="switch-01")


def _client_delta(mac: str, outcome: str) -> client_compare.ClientDelta:
    """Return one client difference record.

    Why:
        The view reads the outcome and the address alone, the same way it
        reads a device record.

    Args:
        mac: The client address.
        outcome: One client outcome.

    Returns:
        One client difference record.
    """
    return client_compare.ClientDelta(mac=mac, outcome=outcome, hostname="laptop-01")


def _device_comparison(*skipped: str) -> device_compare.DeviceComparison:
    """Return a device comparison with one record of each outcome.

    Why:
        Every filter test needs the same four rows. Building them once keeps
        each test to the one line that names the filter.

    Args:
        *skipped: Each section whose digest matched.

    Returns:
        One device comparison.
    """
    return device_compare.DeviceComparison(
        deltas=(
            _device_delta(MASTER_MAC, device_compare.OUTCOME_UNCHANGED),
            _device_delta(MEMBER_MAC, device_compare.OUTCOME_CHANGED),
            _device_delta("0011220000cc", device_compare.OUTCOME_ADDED),
            _device_delta("0011220000dd", device_compare.OUTCOME_REMOVED),
        ),
        skipped_sections=skipped,
    )


def _client_comparison(*skipped: str) -> client_compare.ClientComparison:
    """Return a client comparison with one record of each outcome.

    Why:
        Every client filter test needs the same four rows, for the same
        reason as the device builder.

    Args:
        *skipped: Each section whose digest matched.

    Returns:
        One client comparison.
    """
    return client_compare.ClientComparison(
        deltas=(
            _client_delta(CLIENT_MAC, client_compare.OUTCOME_PRESENT),
            _client_delta(OTHER_CLIENT_MAC, client_compare.OUTCOME_MOVED),
            _client_delta("000000000001", client_compare.OUTCOME_ADDED),
            _client_delta("000000000002", client_compare.OUTCOME_MISSING),
        ),
        skipped_sections=skipped,
    )


# ---------------------------------------------------------------------------
# The test identifiers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("clients_moved", "compare-stat-clients-moved"),
        ("client_return_rate", "compare-stat-client-return-rate"),
        ("devices_version_changed", "compare-stat-devices-version-changed"),
    ],
)
def test_the_statistic_test_id_replaces_each_underscore(name: str, expected: str) -> None:
    """The page identifier uses dashes where the contract uses underscores.

    Args:
        name: One flat statistic name.
        expected: The identifier the page must carry.
    """
    assert render.stat_test_id(name) == expected


def test_every_statistic_carries_a_page_identifier() -> None:
    """Each contract statistic reaches the page with its own identifier."""
    section = render.build_statistics_section(statistics_module.ComparisonStatistics())

    identifiers = [view.test_id for view in section.values]

    assert len(identifiers) == len(set(identifiers))
    assert all(name.startswith(render.STAT_TEST_ID_PREFIX) for name in identifiers)


def test_the_row_identifiers_carry_the_address() -> None:
    """A row identifier ends with the address the operator searched for."""
    assert render.device_row_test_id(MASTER_MAC) == "compare-device-row-" + MASTER_MAC
    assert render.client_row_test_id(CLIENT_MAC) == "compare-client-row-" + CLIENT_MAC


def test_the_filter_identifier_names_the_outcome() -> None:
    """A filter control identifier names the outcome it selects."""
    assert render.filter_test_id(client_compare.OUTCOME_MISSING) == "compare-filter-missing"
    assert render.filter_test_id(render.FILTER_ALL) == "compare-filter-all"


# ---------------------------------------------------------------------------
# The outcome filter
# ---------------------------------------------------------------------------


def test_the_filter_lists_hold_every_outcome_and_the_word_all() -> None:
    """Each filter list starts with ``all`` and then names every outcome."""
    assert render.DEVICE_FILTERS == ("all", "unchanged", "changed", "added", "removed")
    assert render.CLIENT_FILTERS == ("all", "present", "moved", "added", "missing")


@pytest.mark.parametrize(
    "raw",
    ["", None, "unknown", "MISSING", 12345, "present", ["missing"]],
)
def test_a_value_outside_the_device_list_shows_every_row(raw: Any) -> None:
    """An unknown filter value shows every row rather than an empty table.

    Args:
        raw: The raw filter value from the address bar.
    """
    assert render.normalize_filter(raw, render.DEVICE_FILTERS) == render.FILTER_ALL


def test_a_known_filter_value_survives() -> None:
    """A filter value of the list reaches the table unchanged."""
    assert render.normalize_filter("removed", render.DEVICE_FILTERS) == "removed"
    assert render.normalize_filter("moved", render.CLIENT_FILTERS) == "moved"


def test_a_client_outcome_never_filters_the_device_table() -> None:
    """A client outcome is not a device outcome, so the device table shows all."""
    rows = render.filter_devices(_device_comparison().deltas, client_compare.OUTCOME_MOVED)

    assert len(rows) == 4


def test_the_device_filter_keeps_one_outcome() -> None:
    """The device filter keeps the rows of the named outcome alone."""
    rows = render.filter_devices(_device_comparison().deltas, device_compare.OUTCOME_CHANGED)

    assert [row.mac for row in rows] == [MEMBER_MAC]


def test_the_client_filter_keeps_one_outcome() -> None:
    """The client filter keeps the rows of the named outcome alone."""
    rows = render.filter_clients(_client_comparison().deltas, client_compare.OUTCOME_MISSING)

    assert [row.mac for row in rows] == ["000000000002"]


def test_a_move_survives_the_missing_filter_untouched() -> None:
    """The missing filter never returns a client that only roamed."""
    rows = render.filter_clients(_client_comparison().deltas, client_compare.OUTCOME_MISSING)

    assert client_compare.OUTCOME_MOVED not in [row.outcome for row in rows]


def test_the_filter_keeps_the_original_row_order() -> None:
    """The filter never reorders the rows it keeps."""
    deltas = (
        _device_delta(MEMBER_MAC, device_compare.OUTCOME_CHANGED),
        _device_delta(MASTER_MAC, device_compare.OUTCOME_CHANGED),
    )

    rows = render.filter_devices(deltas, device_compare.OUTCOME_CHANGED)

    assert [row.mac for row in rows] == [MEMBER_MAC, MASTER_MAC]


# ---------------------------------------------------------------------------
# The table sections
# ---------------------------------------------------------------------------


def test_the_device_section_reports_the_count_before_the_filter() -> None:
    """A filtered table still reports how many rows the comparison found."""
    section = render.build_device_section(_device_comparison(), device_compare.OUTCOME_CHANGED)

    assert len(section.rows) == 1
    assert section.total == 4
    assert section.outcome == device_compare.OUTCOME_CHANGED


def test_a_skipped_device_section_says_so() -> None:
    """A device section that the digests proved equal reports the skip."""
    section = render.build_device_section(_device_comparison(device_compare.SECTION_DEVICES))

    assert section.skipped is True


def test_an_unskipped_device_section_says_so() -> None:
    """A device section that the comparison read reports no skip."""
    assert render.build_device_section(_device_comparison()).skipped is False


def test_one_matching_client_digest_never_skips_the_whole_table() -> None:
    """The client table counts as skipped only when all three digests match."""
    section = render.build_client_section(_client_comparison(client_compare.SECTION_CLIENTS_WIRED))

    assert section.skipped is False


def test_three_matching_client_digests_skip_the_whole_table() -> None:
    """Every client digest matching reports the client table as skipped."""
    section = render.build_client_section(_client_comparison(*client_compare.CLIENT_SECTIONS))

    assert section.skipped is True


def test_an_unknown_filter_reaches_the_section_as_all() -> None:
    """A section built with a bad filter value reports ``all``."""
    section = render.build_client_section(_client_comparison(), "not an outcome")

    assert section.outcome == render.FILTER_ALL
    assert len(section.rows) == 4


# ---------------------------------------------------------------------------
# The header
# ---------------------------------------------------------------------------


def test_the_header_names_both_captures() -> None:
    """The header carries the identifier and the moment of both captures."""
    before: dict[str, Any] = {"capture_id": "cap-1", "started_at": "2026-08-19T01:00:00+00:00", "role": "pre"}
    after: dict[str, Any] = {"capture_id": "cap-2", "started_at": "2026-08-19T01:30:00+00:00", "role": "post"}

    header = render.build_header(before, after)

    assert header.before.capture_id == "cap-1"
    assert header.after.capture_id == "cap-2"
    assert header.before.role == "pre"
    assert header.after.role == "post"


def test_the_header_prefers_the_later_site_name() -> None:
    """The post-check capture names the site, because it is the later truth."""
    before: dict[str, Any] = {"site_name": "old name", "org_name": "Example"}
    after: dict[str, Any] = {"site_name": "new name"}

    header = render.build_header(before, after)

    assert header.site_name == "new name"
    assert header.org_name == "Example"


def test_a_partial_capture_still_builds_a_header() -> None:
    """A capture with a missing or broken field raises nothing."""
    header = render.build_header({}, {"capture_id": 12345, "site_name": None})

    assert header.after.capture_id == ""
    assert header.site_name == ""


def test_the_capture_summary_body_holds_the_two_contract_keys() -> None:
    """The comparison body names ``capture_id`` and ``started_at`` alone."""
    summary = render.CaptureSummary(capture_id="cap-1", started_at="2026-08-19T01:00:00+00:00", role="pre")

    assert set(summary.to_dict()) == {"capture_id", "started_at"}


def test_the_header_carries_the_skipped_section_list() -> None:
    """A reader of an empty table learns that the digests skipped the work."""
    header = render.build_header({}, {}, (device_compare.SECTION_DEVICES,))

    assert header.to_dict()["skipped_sections"] == ["devices"]


# ---------------------------------------------------------------------------
# The statistics region
# ---------------------------------------------------------------------------


def test_the_statistics_region_prints_in_contract_order() -> None:
    """The region names the statistics in the order of the contract."""
    section = render.build_statistics_section(statistics_module.ComparisonStatistics())

    assert [view.name for view in section.values] == list(statistics_module.STATISTIC_NAMES)


def test_every_statistic_carries_words_for_the_page() -> None:
    """No number reaches the page without a label a reader understands."""
    section = render.build_statistics_section(statistics_module.ComparisonStatistics())

    assert all(view.label and view.label != view.name for view in section.values)


def test_the_statistics_region_carries_the_real_numbers() -> None:
    """The region shows the counts of the roll-up, not a default."""
    counts = statistics_module.ClientCounts(present=1840, moved=96, added=12, missing=30)
    statistics = statistics_module.ComparisonStatistics(clients=counts)

    values = {view.name: view.value for view in render.build_statistics_section(statistics).values}

    assert values["clients_moved"] == 96
    assert values["client_return_rate"] == pytest.approx(0.985)


# ---------------------------------------------------------------------------
# The whole view
# ---------------------------------------------------------------------------


def test_the_view_joins_the_skipped_sections_of_both_halves() -> None:
    """The header reports a device skip and a client skip together."""
    devices = _device_comparison(device_compare.SECTION_DEVICES)
    clients = _client_comparison(client_compare.SECTION_CLIENTS_WIRED)

    view = render.build_view(({}, {}), devices, clients, statistics_module.ComparisonStatistics())

    assert view.header.skipped_sections == ("devices", "clients_wired")


def test_the_view_applies_one_filter_to_both_tables() -> None:
    """The one filter value reaches the device table and the client table."""
    view = render.build_view(
        ({}, {}),
        _device_comparison(),
        _client_comparison(),
        statistics_module.ComparisonStatistics(),
        outcome=device_compare.OUTCOME_ADDED,
    )

    assert [row.outcome for row in view.devices.rows] == ["added"]
    assert [row.outcome for row in view.clients.rows] == ["added"]


def test_the_view_body_holds_every_contract_key() -> None:
    """The body of the comparison endpoint names each key of the contract."""
    view = render.build_view(
        ({"capture_id": "cap-1"}, {"capture_id": "cap-2"}),
        _device_comparison(),
        _client_comparison(),
        statistics_module.ComparisonStatistics(),
    )

    body = view.to_dict()

    expected = {"before", "after", "site_name", "org_name", "skipped_sections"}
    assert expected <= set(body)
    assert {"statistics", "device_deltas", "client_deltas"} <= set(body)


def test_the_view_body_carries_the_filtered_rows_alone() -> None:
    """A filter narrows the table that knows the outcome and no other.

    Why:
        ``missing`` is a client outcome, so the client table narrows to the
        missing clients. The device table does not know that outcome, so it
        shows every row. An empty device table would read as a site with no
        device differences and would hide a failed upgrade.
    """
    view = render.build_view(
        ({}, {}),
        _device_comparison(),
        _client_comparison(),
        statistics_module.ComparisonStatistics(),
        outcome=client_compare.OUTCOME_MISSING,
    )

    body = view.to_dict()

    assert [row["outcome"] for row in body["client_deltas"]] == ["missing"]
    assert len(body["device_deltas"]) == 4
    assert view.devices.outcome == render.FILTER_ALL


def test_an_empty_view_raises_nothing() -> None:
    """A comparison of two empty captures builds a whole page."""
    view = render.build_view(
        ({}, {}),
        device_compare.DeviceComparison(),
        client_compare.ClientComparison(),
        statistics_module.ComparisonStatistics(),
    )

    assert view.devices.rows == ()
    assert view.clients.rows == ()
    assert len(view.statistics.values) == len(statistics_module.STATISTIC_NAMES)
