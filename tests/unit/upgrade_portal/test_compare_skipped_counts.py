"""Unit tests for the device counts of a skipped comparison section.

Why:
    The comparison is the artifact that proves an upgrade did no harm. The
    number that proves it is the count of devices that came back. A matching
    device digest proves every device unchanged, so the count must report the
    whole device section. A bare zero there reads as one of three untrue
    things: no device was compared, no device is present, or every device
    changed.

    A measured zero must still read as zero. A fix that fills every zero would
    hide a real empty section, which is the opposite fault.

    Every test feeds plain dictionaries. No test opens a socket, reads the
    ``.env`` file, or names a real credential.
"""

from __future__ import annotations

from typing import Any

from src.upgrade_portal.compare import clients as client_compare
from src.upgrade_portal.compare import diff as device_compare
from src.upgrade_portal.compare import render, statistics

# WHY: Obviously fake addresses. A reader sees at once that no test reaches a
#      real site.
MAC_PREFIX = "00112200"

# WHY: The live report of issue #2102 held eight devices and printed a zero.
#      The same number here keeps the test beside the defect it repairs.
SITE_DEVICE_COUNT = 8

MATCHING_DIGEST = "b1946ac92492d2347c6235b4d2611184"
OTHER_DIGEST = "591785b794601e212b260e25925636fd"

OLD_VERSION = "21.4R3.15"
NEW_VERSION = "23.4R2.13"

DEVICE_STATISTIC_NAMES = (
    "devices_unchanged",
    "devices_changed",
    "devices_added",
    "devices_removed",
    "devices_version_changed",
)


def _device_index(total: int, version: str = OLD_VERSION) -> dict[str, Any]:
    """Return a device index that holds one row for each of ``total`` devices.

    Why:
        The defect needs a site with several devices, and every test states
        that size as one number. Building the index here keeps each test to
        the difference it proves.

    Args:
        total: How many device rows to build.
        version: The firmware version of every row.

    Returns:
        One device index, keyed by address.
    """
    return {
        f"{MAC_PREFIX}{index:04x}": {
            "name": f"switch-{index:02d}",
            "model": "EX4400-24T",
            "version": version,
            "status": "connected",
        }
        for index in range(total)
    }


def _capture(index: dict[str, Any], digest: str | None = None) -> dict[str, Any]:
    """Return one capture document around a device index.

    Why:
        The device comparison reads two keys of a large document. A small
        builder keeps every test to the two keys that matter.

    Args:
        index: The device index of the capture.
        digest: The device section digest, when the test needs one.

    Returns:
        One capture document.
    """
    capture: dict[str, Any] = {"device_index": index}
    if digest is not None:
        capture["digests"] = {device_compare.SECTION_DEVICES: digest}
    return capture


def _statistics(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Return the flat statistics of one comparison of two captures.

    Why:
        The page and the endpoint both read the flat form, so a test that
        reads the same form proves what the operator sees.

    Args:
        before: The pre-check capture.
        after: The post-check capture.

    Returns:
        The flat statistics of the comparison.
    """
    devices = device_compare.compare_devices(before, after)
    clients = client_compare.compare_clients(before, after)
    return statistics.build_statistics(devices, clients).to_dict()


# ---------------------------------------------------------------------------
# The true count after a digest skip
# ---------------------------------------------------------------------------


def test_a_skipped_device_section_reports_the_true_unchanged_count() -> None:
    """A matching digest reports every device of the site as unchanged."""
    index = _device_index(SITE_DEVICE_COUNT)
    before = _capture(index, MATCHING_DIGEST)
    after = _capture(index, MATCHING_DIGEST)

    flat = _statistics(before, after)

    assert flat["devices_unchanged"] == SITE_DEVICE_COUNT


def test_a_skipped_device_section_carries_the_count_on_the_comparison() -> None:
    """The device comparison reports the count that the digest proved."""
    index = _device_index(SITE_DEVICE_COUNT)

    result = device_compare.compare_devices(_capture(index, MATCHING_DIGEST), _capture(index, MATCHING_DIGEST))

    assert result.proved_unchanged == SITE_DEVICE_COUNT


def test_a_skipped_device_section_still_names_the_skip() -> None:
    """The repair leaves the skipped section list and the empty row list."""
    index = _device_index(SITE_DEVICE_COUNT)

    result = device_compare.compare_devices(_capture(index, MATCHING_DIGEST), _capture(index, MATCHING_DIGEST))

    assert result.skipped_sections == (device_compare.SECTION_DEVICES,)
    assert result.deltas == ()
    assert result.to_dict()["device_deltas"] == []


def test_a_skipped_device_section_reports_no_other_device_outcome() -> None:
    """A matching digest proves no device changed, joined the site, or left."""
    index = _device_index(SITE_DEVICE_COUNT)

    flat = _statistics(_capture(index, MATCHING_DIGEST), _capture(index, MATCHING_DIGEST))

    assert flat["devices_changed"] == 0
    assert flat["devices_added"] == 0
    assert flat["devices_removed"] == 0
    assert flat["devices_version_changed"] == 0


def test_a_partial_capture_falls_back_to_the_other_device_index() -> None:
    """A digest match proves the two sections equal, so either count serves."""
    index = _device_index(SITE_DEVICE_COUNT)

    result = device_compare.compare_devices(_capture(index, MATCHING_DIGEST), _capture({}, MATCHING_DIGEST))

    assert result.proved_unchanged == SITE_DEVICE_COUNT


# ---------------------------------------------------------------------------
# The measured zero
# ---------------------------------------------------------------------------


def test_a_measured_empty_section_still_reports_zero() -> None:
    """A site with no device reports zero, because the zero is measured."""
    before = _capture({}, MATCHING_DIGEST)
    after = _capture({}, MATCHING_DIGEST)

    flat = _statistics(before, after)

    assert flat["devices_unchanged"] == 0


def test_a_compared_section_counts_only_the_unchanged_rows() -> None:
    """A section that the comparison read reports the rows it found."""
    before = _capture(_device_index(SITE_DEVICE_COUNT), MATCHING_DIGEST)
    after = _capture(_device_index(SITE_DEVICE_COUNT, version=NEW_VERSION), OTHER_DIGEST)

    flat = _statistics(before, after)

    assert flat["devices_unchanged"] == 0
    assert flat["devices_changed"] == SITE_DEVICE_COUNT
    assert flat["devices_version_changed"] == SITE_DEVICE_COUNT


def test_a_compared_section_never_adds_a_proved_count() -> None:
    """A comparison that read every row carries no proved count to add."""
    before = _capture(_device_index(SITE_DEVICE_COUNT), MATCHING_DIGEST)
    after = _capture(_device_index(SITE_DEVICE_COUNT), OTHER_DIGEST)

    result = device_compare.compare_devices(before, after)

    assert result.proved_unchanged == 0
    assert statistics.count_devices(result).unchanged == SITE_DEVICE_COUNT


# ---------------------------------------------------------------------------
# The page
# ---------------------------------------------------------------------------


def test_the_page_shows_the_true_count_beside_the_skip_note() -> None:
    """The statistics region prints the count, and the header keeps the note."""
    index = _device_index(SITE_DEVICE_COUNT)
    before = _capture(index, MATCHING_DIGEST)
    after = _capture(index, MATCHING_DIGEST)
    devices = device_compare.compare_devices(before, after)
    clients = client_compare.compare_clients(before, after)

    view = render.build_view((before, after), devices, clients, statistics.build_statistics(devices, clients))
    shown = {value.name: value.value for value in view.statistics.values}

    assert shown["devices_unchanged"] == SITE_DEVICE_COUNT
    assert device_compare.SECTION_DEVICES in view.header.skipped_sections
    assert view.devices.skipped is True


def test_every_device_statistic_stays_in_the_report() -> None:
    """The repair adds no name and drops no name from the statistics region."""
    assert set(DEVICE_STATISTIC_NAMES) <= set(statistics.STATISTIC_NAMES)
