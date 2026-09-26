"""Unit tests of issue #3457: a child job that the check proves counts its devices as upgraded.

Why:
    Issue #3457. The multi-site check can prove that each device of an
    uncertain child job runs the target version. The portal then marks the
    child job completed. The counts came only from the stored cloud answer, and
    that answer names no upgraded device. The progress page therefore showed
    the status completed beside Upgraded 0. These tests drive the real device
    reader and the real summary with stored records.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.app.routes.org_upgrade import aggregate_summary
from src.upgrade_portal.upgrade.org_devices import OrgChildDevices
from tests.unit.upgrade_portal.test_org_child_controls import (
    AP,
    AP_TARGET,
    JUNOS_OLD,
    JUNOS_TARGET,
    SITE_ONE,
    SITE_TWO,
    child,
    record,
    target,
)

SWITCHES = ("000000000103", "000000000104")  # The two switches of one child job.
PROVEN = {"proven": True, "matched": 2, "total": 2, "unread": 0}  # The stored proof of a check.
NOT_PROVEN = {"proven": False, "matched": 0, "total": 2, "unread": 2}  # The stored evidence with no proof.
COUNT_FIELDS = ("total", "upgraded_count", "failed_count")  # The three counts of the operation block.


def proven_switches(failed: tuple[str, ...] = ()) -> dict[str, Any]:
    """Return a switch child job that the check proved.

    Args:
        failed: The devices that the stored cloud answer names as failed.

    Returns:
        One stored child row in the shape that the check leaves behind.
    """
    targets = [target(mac, SITE_ONE, "switch", JUNOS_OLD, JUNOS_TARGET) for mac in SWITCHES]  # Two devices.
    row = child("child-switch", "completed", targets, SITE_ONE)  # The check set the state completed.
    row["reconciliation"] = dict(PROVEN)  # The stored proof of the check.
    row["status_data"] = {"targets": {"failed": list(failed)}} if failed else {}  # No cloud answer by default.
    return row  # The caller builds the reader or the record.


def operation_counts(summary: dict[str, Any]) -> tuple[int, ...]:
    """Return the three counts of the operation block of one summary."""
    return tuple(summary[name] for name in COUNT_FIELDS)  # Total targets, Upgraded, and Failed.


def child_counts(summary: dict[str, Any]) -> list[tuple[int, int, int]]:
    """Return the Targets, Upgraded, and Failed counts of each child row of one summary."""
    return [(row["total"], row["upgraded"], row["failed"]) for row in summary["children"]]  # Plan order.


@pytest.mark.parametrize(
    ("state", "verdict", "expected"),
    [
        ("completed", {"proven": True}, True),  # The check proved the child job.
        ("Completed ", {"proven": True}, True),  # The reader reads the stored state in one form.
        ("completed", {"proven": False}, False),  # The check stored evidence with no proof.
        ("completed", {"proven": "true"}, False),  # Only a real Boolean value proves.
        ("completed", "proven", False),  # A damaged verdict proves nothing.
        ("completed", None, False),  # The cloud completed the child job, and no check ran.
        ("submission_unknown", {"proven": True}, False),  # A proof counts only in the completed state.
        ("failed", {"proven": True}, False),  # A later failure voids the proof.
    ],
)
def test_the_proof_needs_the_completed_state_and_a_true_verdict(state: str, verdict: Any, expected: bool) -> None:
    """Only a completed child job with a stored true proof counts as proven."""
    row = proven_switches()  # A proven child job.
    row["status"] = state  # The state under test.
    row["reconciliation"] = verdict  # The stored verdict under test.
    assert OrgChildDevices.is_proven(row) is expected  # The one rule of the proven counts.


def test_a_proven_child_job_counts_each_device_as_upgraded() -> None:
    """With no cloud list of failed devices, each device of a proven child job counts as upgraded."""
    assert OrgChildDevices(proven_switches()).proven_counts(2) == (2, 0)  # Upgraded 2 and Failed 0.


def test_a_device_that_the_cloud_lists_as_failed_stays_failed() -> None:
    """The device table shows a listed failure, so the counts keep that device as failed."""
    devices = OrgChildDevices(proven_switches(failed=(SWITCHES[1],)))  # The cloud names the second switch.
    assert devices.proven_counts(2) == (1, 1)  # Upgraded 1 and Failed 1.
    assert [devices.state_of(mac) for mac in SWITCHES] == ["completed", "failed"]  # The device table agrees.


def test_the_failed_count_cannot_exceed_the_target_count() -> None:
    """A damaged record with fewer target identities than listed failures counts no negative upgrade."""
    devices = OrgChildDevices(proven_switches(failed=SWITCHES))  # The cloud names both switches.
    assert devices.proven_counts(1) == (0, 1)  # The target count limits the failed count.


def test_the_summary_counts_a_proven_child_job_beside_a_cloud_child_job() -> None:
    """The operation adds the proven counts and the cloud counts in the same way."""
    access_points = [target(AP, SITE_TWO, "ap", "0.14.1", AP_TARGET)]  # One access point of the second site.
    access_point = child("child-ap", "completed", access_points, None)  # The access point job names no site.
    access_point["status_data"] = {"targets": {"upgraded": [AP], "failed": []}}  # The cloud answer of the job.
    summary = aggregate_summary(record([proven_switches(), access_point], state="completed"))  # The page summary.
    assert child_counts(summary) == [(2, 2, 0), (1, 1, 0)]  # The proven row and the cloud row.
    assert operation_counts(summary) == (3, 3, 0)  # The operation adds both kinds of row.


def test_the_summary_of_an_operation_with_no_child_job_counts_nothing() -> None:
    """An operation with no child row shows zero counts and no child row."""
    summary = aggregate_summary(record([], state="running"))  # A damaged record holds no child job.
    assert child_counts(summary) == []  # No child row appears.
    assert operation_counts(summary) == (0, 0, 0)  # The operation block shows zero counts.


def test_the_summary_keeps_the_counts_of_a_child_job_with_no_proof() -> None:
    """A check that proved nothing leaves the counts of the empty cloud answer."""
    row = proven_switches()  # Start from the proven shape.
    row["status"] = "submission_unknown"  # The check did not prove the child job.
    row["reconciliation"] = dict(NOT_PROVEN)  # The stored evidence with no proof.
    summary = aggregate_summary(record([row], state="attention_required"))  # The page summary.
    assert child_counts(summary) == [(2, 0, 0)]  # The row keeps the counts of the empty answer.
    assert operation_counts(summary) == (2, 0, 0)  # The operation block agrees.
