"""Unit tests for the cancel outcome rows of a multi-site progress page.

Why:
    Issue #3246. The single-site stop shows three device lists after a cancel.
    The multi-site page showed one status word for each child job. These tests
    prove each rule that builds the three lists for each child job. No test
    opens a socket or reads a store.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.upgrade.org_cancel_outcomes import (
    ENDED_NOTE,
    NEVER_STARTED_NOTE,
    UNSORTED_NOTE,
    OrgCancelOutcomes,
)

AP_ONE = "001122334455"  # The access point at the first site.
AP_TWO = "001122334466"  # The access point at the second site.
SWITCH = "001122334477"  # The switch at the first site.


def child(child_id: str, status: str, cancellation: Any, **fields: Any) -> dict[str, Any]:
    """Build one stored child job with one cancel result."""
    row = {
        "child_id": child_id,
        "device_family": "switch",
        "site_id": "site-one",
        "site_name": "Site One",
        "status": status,
        "raw_status": 202,
        "targets": [{"mac": SWITCH, "site_id": "site-one"}],
        "target_ids": [SWITCH],
        "cancellation": cancellation,
    }
    row.update(fields)  # Replace the fields that one test changes.
    return row


def record(*children: dict[str, Any], claim: str | None = None) -> dict[str, Any]:
    """Build one stored operation with its child jobs."""
    return {"operation_id": "op-1", "submission_claim_id": claim, "children": list(children)}


def only_row(stored: dict[str, Any]) -> dict[str, Any]:
    """Return the one row that the stored operation gives."""
    rows = OrgCancelOutcomes.rows(stored)  # Build the rows of the page.
    assert len(rows) == 1  # The operation holds one cancelled child job.
    return rows[0]


@pytest.mark.parametrize(
    "stored",
    [
        pytest.param(record(child("child-1", "running", None)), id="no-cancel-yet"),
        pytest.param({"children": "damaged"}, id="damaged-children"),
        pytest.param(None, id="no-record"),
        pytest.param(record(child("child-1", "running", "requested")), id="damaged-cancel-result"),
    ],
)
def test_no_row_exists_before_a_cancel(stored: Any) -> None:
    """The panel stays empty until a child job holds a cancel result."""
    assert OrgCancelOutcomes.rows(stored) == []


def test_a_stored_result_keeps_its_three_lists() -> None:
    """The site child job stores its lists, and the row copies each one."""
    cancellation = {
        "status": "requested",
        "cancelled": [SWITCH],
        "already_writing": [],
        "no_cancel_available": [],
        "message": "The cloud stopped 1 device(s), and no device was writing firmware.",
    }
    assert only_row(record(child("child-1", "running", cancellation))) == {
        "child_id": "child-1",
        "label": "Site One",
        "device_family": "switch",
        "status": "requested",
        "message": "The cloud stopped 1 device(s), and no device was writing firmware.",
        "note": "",
        "ended": False,
        "cancelled": [SWITCH],
        "already_writing": [],
        "no_cancel_available": [],
    }


def ended_result(**fields: Any) -> dict[str, Any]:
    """Build the stored result of a child job that ended before the cancel (issue #3367)."""
    result: dict[str, Any] = {
        "status": "already_ended",
        "state": "completed",
        "cancelled": [],
        "already_writing": [],
        "no_cancel_available": [],
        "message": "The child job already ended: completed. The portal sent no cancel request.",
    }
    result.update(fields)  # Replace the fields that one test changes.
    return result


def test_an_ended_child_job_lists_no_device() -> None:
    """The child job ended before the cancel, so the row names no device and hides the lists."""
    row = only_row(record(child("child-1", "completed", ended_result())))
    assert (row["status"], row["note"], row["ended"]) == ("already_ended", ENDED_NOTE, True)
    assert (row["cancelled"], row["already_writing"], row["no_cancel_available"]) == ([], [], [])
    assert row["message"] == "The child job already ended: completed. The portal sent no cancel request."


def test_an_ended_result_with_a_damaged_list_still_lists_no_device() -> None:
    """The status proves that no cancel request went out, so no stored list can name a device."""
    row = only_row(record(child("child-1", "failed", ended_result(cancelled=[SWITCH], already_writing=None))))
    assert (row["cancelled"], row["already_writing"], row["note"]) == ([], [], ENDED_NOTE)


def test_a_partial_result_puts_every_device_in_the_writing_list() -> None:
    """A result with one list is not trusted, because the portal never guesses the other lists."""
    row = only_row(record(child("child-1", "running", {"status": "requested", "cancelled": [SWITCH]})))
    assert (row["cancelled"], row["already_writing"], row["note"]) == ([], [SWITCH], UNSORTED_NOTE)


def test_an_access_point_result_without_lists_names_each_access_point() -> None:
    """A result from an earlier release holds no list, so each access point can still write firmware."""
    ap_child = child(
        "child-ap",
        "running",
        {"status": "requested", "raw_status": 200, "message": None},
        device_family="ap",
        site_id=None,
        site_name="Site One, Site Two",
        targets=[{"mac": AP_ONE, "site_id": "site-one"}, {"mac": AP_TWO, "site_id": "site-two"}],
    )
    row = only_row(record(ap_child))
    assert (row["label"], row["message"], row["already_writing"]) == ("Site One, Site Two", "", [AP_ONE, AP_TWO])


@pytest.mark.parametrize(
    ("status", "raw_status", "claim"),
    [
        pytest.param("planned", 0, None, id="planned-with-no-live-submission"),
        pytest.param("not_submitted", 0, "claim-1", id="not-submitted"),
        pytest.param("rejected", 400, None, id="refused-by-the-cloud"),
        pytest.param("rejected", 499, None, id="refused-at-the-upper-bound"),
    ],
)
def test_a_child_job_that_never_started_lists_no_device(status: str, raw_status: int, claim: str | None) -> None:
    """No cloud job exists, so no device of the child job writes firmware."""
    unavailable = {"status": "unavailable", "message": "The child has no known upgrade identifier."}
    row = only_row(record(child("child-1", status, unavailable, raw_status=raw_status), claim=claim))
    assert (row["cancelled"], row["already_writing"], row["no_cancel_available"]) == ([], [], [])
    assert (row["status"], row["note"]) == ("unavailable", NEVER_STARTED_NOTE)


@pytest.mark.parametrize(
    ("status", "raw_status", "claim"),
    [
        pytest.param("planned", 0, "claim-1", id="planned-during-a-live-submission"),
        pytest.param("rejected", 500, None, id="a-server-error"),
        pytest.param("rejected", 200, None, id="a-damaged-success"),
        pytest.param("submission_unknown", 0, None, id="an-unknown-submission"),
    ],
)
def test_an_uncertain_child_job_lists_every_device_as_writing(status: str, raw_status: int, claim: str | None) -> None:
    """A cloud job can exist, so the portal claims no stop (issue #3327)."""
    unavailable = {"status": "unavailable", "message": "The child has no known upgrade identifier."}
    row = only_row(record(child("child-1", status, unavailable, raw_status=raw_status), claim=claim))
    assert (row["cancelled"], row["already_writing"], row["note"]) == ([], [SWITCH], UNSORTED_NOTE)


def test_an_earlier_record_uses_the_target_identifiers() -> None:
    """A record from before issue #3249 holds no target rows."""
    unknown = {"status": "unknown", "message": "The cancellation outcome is unknown: TimeoutError."}
    row = only_row(record(child("child-1", "running", unknown, targets=None, target_ids=[AP_ONE])))
    assert row["already_writing"] == [AP_ONE]


@pytest.mark.parametrize(
    ("fields", "label"),
    [
        pytest.param({"site_name": ""}, "site-one", id="the-site-identifier"),
        pytest.param({"site_name": None, "site_id": None}, "Multiple sites", id="no-site"),
    ],
)
def test_the_label_falls_back_to_the_site_identifier(fields: dict[str, Any], label: str) -> None:
    """A child job with no site name still gets a readable label."""
    row = only_row(record(child("child-1", "running", {"status": "unknown"}, **fields)))
    assert row["label"] == label


def test_the_rows_keep_the_plan_order() -> None:
    """The page lists each child job in the order of the plan."""
    stored = record(
        child("child-b", "running", {"status": "requested"}),
        child("child-c", "running", None),
        child("child-a", "planned", {"status": "unavailable"}),
    )
    assert [row["child_id"] for row in OrgCancelOutcomes.rows(stored)] == ["child-b", "child-a"]


def test_the_signature_names_each_cancel_status() -> None:
    """A second tab loads the page again when one cancel status changes."""
    stored = record(
        child("child-b", "running", {"status": "cancel_claimed"}),
        child("child-c", "running", None),
        child("child-a", "planned", {"status": "unavailable"}),
    )
    assert OrgCancelOutcomes.signature(stored) == "child-b:cancel_claimed,child-a:unavailable"
    assert OrgCancelOutcomes.signature(record(child("child-c", "running", None))) == ""
    assert OrgCancelOutcomes.signature({"children": "damaged"}) == ""
