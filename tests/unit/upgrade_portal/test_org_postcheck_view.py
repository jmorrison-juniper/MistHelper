"""Unit tests for the post-check card rows of a multi-site upgrade.

Why:
    Issue #3244. The progress page and the status poll show one post-check row
    for each site. Each row must tell the operator what the portal did. The
    compare link must appear only when both captures of a site exist. These
    tests read the shipped view with plain records. No test reads a store or a
    cloud.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.upgrade.org_cascade.record import WATCH_KEY
from src.upgrade_portal.upgrade.org_postcheck import (
    HELD_MESSAGE,
    RUNNING_MESSAGE,
    SKIPPED_MESSAGE,
    OrgPostCheckRows,
    PostCheckSite,
    PostCheckState,
)
from src.upgrade_portal.upgrade.org_postcheck_view import (
    LOST_MESSAGE,
    NO_PAIR_MESSAGE,
    NOT_TAKEN_MESSAGE,
    VERIFIED_MESSAGE,
    WAITING_MESSAGE,
    OrgPostCheckView,
)
from tests.support.org_cascade import PRE_CAPTURE_KEYS, SITE_IDS, SITE_NAMES, VERIFIED_TEXT, OrgRecordBuilder
from tests.support.rehearsal import RehearsalClock, cascade_fleet

ALPHA, BRAVO = SITE_IDS  # The two sites of the plan, in the plan order.
POST_KEY = "cap-" + "c" * 32 + "-02"  # One post-check key in the run-less form.
BRAVO_REFUSED = {"aa0000000002": "rejected", "bb0000000002": "rejected", "ap": "rejected"}  # No write reaches Bravo.


def planned_record(statuses: dict[str, str] | None = None) -> dict[str, Any]:
    """Return one operation record with the watch fields and the site plan of two sites."""
    fleet = cascade_fleet(RehearsalClock().now())  # Each site holds one gateway, one switch, and one access point.
    return OrgRecordBuilder.with_site_plan(OrgRecordBuilder.build(fleet, statuses))  # The plan fields.


def with_row(record: dict[str, Any], state: PostCheckState, message: str = "", capture_id: str = "") -> dict[str, Any]:
    """Store one post-check row for the Alpha site, and return the record."""
    site = PostCheckSite(ALPHA, SITE_NAMES[ALPHA], 2, True)  # The first site of the plan.
    OrgPostCheckRows.put(record, site.row(state, message, capture_id))  # The shipped writer of the rows.
    return record  # The caller builds the view.


def shown(record: dict[str, Any], active: bool) -> dict[str, dict[str, Any]]:
    """Return the view row of each site, keyed by the site identifier."""
    return {row["site_id"]: row for row in OrgPostCheckView.rows(record, active)}  # One row for each site.


def test_a_record_with_no_watch_shows_no_postcheck_row() -> None:
    """FR-016: a record of an earlier release gets no post-check card."""
    record = planned_record()  # A record with the watch fields.
    record.pop(WATCH_KEY)  # A record of an earlier release holds no watch.
    assert OrgPostCheckView.rows(record, active=False) == []  # The page then shows no card.


def test_an_active_watch_shows_each_site_waiting_in_the_plan_order() -> None:
    """FR-012: each site gets a row, and the rows follow the site selection."""
    rows = OrgPostCheckView.rows(planned_record(), active=True)  # No stage ran yet.
    summary = [(row["site_id"], row["site_name"], row["state_label"], row["message"]) for row in rows]  # The text.
    assert summary == [
        (ALPHA, SITE_NAMES[ALPHA], "Waiting", WAITING_MESSAGE),
        (BRAVO, SITE_NAMES[BRAVO], "Waiting", WAITING_MESSAGE),
    ]  # Each row tells the operator when the capture comes.
    assert {row["capture_href"] for row in rows} == {""}  # No capture exists yet, so no row links one.


def test_an_ended_watch_with_no_row_shows_not_taken() -> None:
    """User story 2: a row with no capture states why no capture exists."""
    row = shown(planned_record(), active=False)[ALPHA]  # The watch ended, and the stage stored no row.
    assert (row["state"], row["state_label"], row["message"]) == ("not_taken", "Not taken", NOT_TAKEN_MESSAGE)


def test_a_site_with_no_accepted_write_reads_skipped_before_the_stage() -> None:
    """FR-010: a site that received no firmware write never waits for a capture."""
    rows = shown(planned_record(BRAVO_REFUSED), active=True)  # The cloud refused every child job of Bravo.
    assert (rows[BRAVO]["state"], rows[BRAVO]["message"]) == ("skipped", SKIPPED_MESSAGE)  # No capture comes.
    assert rows[ALPHA]["state"] == "waiting"  # Alpha still waits for its capture.


def test_an_open_submission_keeps_a_site_with_no_write_waiting() -> None:
    """A submission that can still accept a child job decides nothing about a site yet."""
    record = planned_record(BRAVO_REFUSED)  # Bravo holds no accepted child job yet.
    record["state"] = "submission_claimed"  # The submission still writes the child jobs.
    assert shown(record, active=True)[BRAVO]["state"] == "waiting"  # The site can still receive a write.


def test_a_verified_row_links_the_capture_and_the_comparison() -> None:
    """FR-013: a verified row with a pre-check capture links the two captures."""
    record = with_row(planned_record(), PostCheckState.VERIFIED, VERIFIED_TEXT, POST_KEY)  # Alpha verified.
    row = shown(record, active=False)[ALPHA]  # The row after the watch ended.
    assert (row["state_label"], row["message"]) == ("Verified", VERIFIED_TEXT)  # The capture text of the row.
    assert row["capture_href"] == f"/captures/{POST_KEY}"  # The capture page of the post-check.
    assert row["pre_capture_id"] == PRE_CAPTURE_KEYS[ALPHA]  # The first half of the comparison.
    assert row["compare_href"] == f"/compare?before={PRE_CAPTURE_KEYS[ALPHA]}&after={POST_KEY}"  # Both halves.


def test_a_verified_row_with_no_text_gets_the_verified_sentence() -> None:
    """A verified row always gives the operator one sentence."""
    record = with_row(planned_record(), PostCheckState.VERIFIED, "", POST_KEY)  # The capture gave no text.
    assert shown(record, active=False)[ALPHA]["message"] == VERIFIED_MESSAGE  # The default sentence.


def test_a_verified_row_with_no_precheck_shows_no_comparison() -> None:
    """FR-013: with no pre-check capture, the row names the gap and links no comparison."""
    record = with_row(planned_record(), PostCheckState.VERIFIED, VERIFIED_TEXT, POST_KEY)  # Alpha verified.
    record["pre_captures"] = []  # The operation holds no pre-check capture.
    row = shown(record, active=False)[ALPHA]  # The row after the watch ended.
    assert (row["message"], row["pre_capture_id"], row["compare_href"]) == (NO_PAIR_MESSAGE, "", "")  # The gap.
    assert row["capture_href"] == f"/captures/{POST_KEY}"  # The capture itself still opens.


def test_a_failed_row_links_the_capture_and_no_comparison() -> None:
    """FR-013: a failed capture never enters a comparison."""
    record = with_row(planned_record(), PostCheckState.FAILED, "The capture stopped.", POST_KEY)  # Alpha failed.
    row = shown(record, active=False)[ALPHA]  # The row after the watch ended.
    assert (row["state_label"], row["message"], row["compare_href"]) == ("Failed", "The capture stopped.", "")
    assert row["capture_href"] == f"/captures/{POST_KEY}"  # The capture page shows the cause.


@pytest.mark.parametrize(
    ("active", "expected"),
    [(True, ("running", "Running", RUNNING_MESSAGE)), (False, ("failed", "Failed", LOST_MESSAGE))],
)
def test_a_running_row_reads_failed_after_the_watch_ended(active: bool, expected: tuple[str, str, str]) -> None:
    """A running row with no watch thread can never end, so the row reads failed."""
    record = with_row(planned_record(), PostCheckState.RUNNING, RUNNING_MESSAGE, POST_KEY)  # A capture in flight.
    row = shown(record, active)[ALPHA]  # The row while the watch runs, or after it ended.
    assert (row["state"], row["state_label"], row["message"]) == expected  # The watch decides the reading.


def test_a_held_row_shows_the_mode_and_no_link() -> None:
    """FR-009: the manual mode takes no capture, so the row links nothing."""
    record = with_row(planned_record(), PostCheckState.HELD, HELD_MESSAGE)  # The mode held Alpha.
    row = shown(record, active=False)[ALPHA]  # The row after the watch ended.
    assert (row["state_label"], row["message"], row["capture_href"], row["compare_href"]) == (
        "Held",
        HELD_MESSAGE,
        "",
        "",
    )  # The page links no capture.


def test_the_links_quote_each_capture_key() -> None:
    """A stored key with special characters cannot change the link target."""
    odd = "cap-<x>&y=1"  # A damaged key with markup and query characters.
    record = with_row(planned_record(), PostCheckState.VERIFIED, VERIFIED_TEXT, odd)  # Alpha holds the key.
    row = shown(record, active=False)[ALPHA]  # The row after the watch ended.
    assert row["capture_href"] == "/captures/cap-%3Cx%3E%26y%3D1"  # One quoted path segment.
    assert row["compare_href"].endswith("&after=cap-%3Cx%3E%26y%3D1")  # One quoted query value.
