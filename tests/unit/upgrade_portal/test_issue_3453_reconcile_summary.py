"""Unit tests of issue #3453: the grammar of the multi-site check result.

Why:
    Issue #3453. The result of each check of an uncertain child job used the
    fixed noun "devices" and the fixed verb "run". A child job of one device
    then read "0 of 1 devices run the target version". These tests drive the
    real check class with stored records, and each test compares the whole
    result text. A change to a count, to a noun, or to another sentence
    therefore fails the test.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.interfaces.portals.upgrade_portal.upgrade.org_reconcile import OrgReconcileCheck
from tests.unit.upgrade_portal.test_org_child_controls import (
    JUNOS_OLD,
    JUNOS_TARGET,
    SITE_ONE,
    child,
    record,
    target,
)

SWITCHES = ("000000000103", "000000000104", "000000000105")  # Three switches of one child job.
ADVICE = "Check the Mist dashboard before you act on this child job."  # The last sentence of an open result.
REINSTALL = "A device ran the target version before the upgrade, so the reading proves nothing."  # The reinstall.
PROVEN = "The portal marks this child job completed."  # The last sentence of a proven result.
NO_DEVICE = "The child job names no device. The portal cannot prove its outcome."  # FR-004: this text stays.


def switch_targets(count: int, before: str = JUNOS_OLD) -> list[dict[str, str]]:
    """Return the stored targets of one switch child job.

    Args:
        count: How many switches the child job holds.
        before: The version that each switch ran before the upgrade.

    Returns:
        One stored target record for each switch.
    """
    return [target(mac, SITE_ONE, "switch", before, JUNOS_TARGET) for mac in SWITCHES[:count]]  # One each.


def summary_of(targets: list[dict[str, str]], readings: dict[str, str]) -> str:
    """Run the real check on one uncertain child job, and return its result text.

    Args:
        targets: The stored targets of the child job.
        readings: The running version of each device that answered.

    Returns:
        The result text that the progress page shows after "Last check".
    """
    uncertain = child("child-switch", "submission_unknown", targets, SITE_ONE)  # One uncertain child job.
    stored: dict[str, Any] = record([uncertain], state="attention_required")  # The durable operation record.
    return str(OrgReconcileCheck(stored).verdicts(readings)[0]["summary"])  # The first and only verdict.


def test_one_proven_device_reads_as_one_device() -> None:
    """FR-001: a child job of one device on the target version uses the singular noun."""
    text = summary_of(switch_targets(1), {SWITCHES[0]: JUNOS_TARGET})  # The switch runs the target.
    assert text == f"The target version runs on 1 of 1 device. {PROVEN}"  # The whole result text.


def test_one_device_with_no_reading_reads_as_one_device() -> None:
    """FR-001 and FR-002: a child job of one device with no reading uses the singular noun twice."""
    text = summary_of(switch_targets(1), {})  # The site of the switch answered nothing.
    assert text == f"The target version runs on 0 of 1 device. The portal could not read 1 of 1 device. {ADVICE}"


def test_one_reinstalled_device_reads_as_one_device() -> None:
    """FR-001 and FR-003: a reinstall of one device keeps the reinstall note and uses the singular noun."""
    text = summary_of(switch_targets(1, before=JUNOS_TARGET), {SWITCHES[0]: JUNOS_TARGET})  # A reinstall.
    assert text == f"The target version runs on 1 of 1 device. {REINSTALL} {ADVICE}"  # The whole result text.


def test_one_match_of_three_devices_reads_as_devices() -> None:
    """FR-001: a child job of three devices uses the plural noun, also when one device matches."""
    readings = {SWITCHES[0]: JUNOS_TARGET, SWITCHES[1]: JUNOS_OLD, SWITCHES[2]: JUNOS_OLD}  # One match.
    assert summary_of(switch_targets(3), readings) == f"The target version runs on 1 of 3 devices. {ADVICE}"


def test_two_matches_and_one_unread_device_of_three_read_as_devices() -> None:
    """FR-001 and FR-002: the unread sentence of three devices uses the plural noun."""
    readings = {SWITCHES[0]: JUNOS_TARGET, SWITCHES[1]: JUNOS_TARGET}  # The third switch gave no reading.
    expected = f"The target version runs on 2 of 3 devices. The portal could not read 1 of 3 devices. {ADVICE}"
    assert summary_of(switch_targets(3), readings) == expected  # The whole result text.


def test_three_proven_devices_read_as_devices() -> None:
    """FR-001: a proven child job of three devices uses the plural noun."""
    readings = dict.fromkeys(SWITCHES, JUNOS_TARGET)  # Each switch runs the target version.
    assert summary_of(switch_targets(3), readings) == f"The target version runs on 3 of 3 devices. {PROVEN}"


def test_a_child_job_with_no_device_keeps_its_text() -> None:
    """FR-004: a child job that names no device keeps the old text."""
    assert summary_of([], {}) == NO_DEVICE  # No count, so no noun changes.


@pytest.mark.parametrize(
    ("matched", "total", "first_sentence"),
    [
        (0, 1, "The target version runs on 0 of 1 device."),
        (0, 2, "The target version runs on 0 of 2 devices."),
        (1, 2, "The target version runs on 1 of 2 devices."),
        (0, 3, "The target version runs on 0 of 3 devices."),
        (2, 3, "The target version runs on 2 of 3 devices."),
    ],
)
def test_the_first_sentence_reads_correctly_for_each_count(matched: int, total: int, first_sentence: str) -> None:
    """SC-001: the first sentence reads as correct English for each count from 0 to 3."""
    readings = {mac: JUNOS_TARGET if index < matched else JUNOS_OLD for index, mac in enumerate(SWITCHES[:total])}
    assert summary_of(switch_targets(total), readings) == f"{first_sentence} {ADVICE}"  # Each device answered.
