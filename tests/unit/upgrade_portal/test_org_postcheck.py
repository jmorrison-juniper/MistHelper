"""Unit tests for the post-check rows and the post-check stage of a multi-site upgrade.

Why:
    Issue #3244. A multi-site upgrade must take a post-check capture of each
    site after the last phase, as a single-site run does. These tests drive the
    shipped rows and the shipped stage against the versioned test store and a
    stand-in taker. No test reads a cloud or opens a socket.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest

from src.upgrade_portal.upgrade.org_cascade.close import OrgPostCheckStage
from src.upgrade_portal.upgrade.org_cascade.record import WATCH_KEY, OrgPhaseStore
from src.upgrade_portal.upgrade.org_postcheck import (
    FAILED_MESSAGE,
    FAILURE_REASON,
    HELD_MESSAGE,
    POSTCHECK_FIELD,
    RUNNING_MESSAGE,
    SKIPPED_MESSAGE,
    STAGE_NOTE,
    OrgPostCheckRows,
    PostCheckResult,
    PostCheckSite,
    PostCheckState,
)
from tests.support.org_cascade import (
    OPERATION_ID,
    SITE_IDS,
    SITE_NAMES,
    VERIFIED_TEXT,
    OrgRecordBuilder,
    StandInPostCheckTaker,
    VersionedStore,
)
from tests.support.rehearsal import RehearsalClock, cascade_fleet

ALPHA, BRAVO = SITE_IDS  # The two sites of the plan, in the plan order.
NOW_TEXT = "2026-09-24T00:00:00+00:00"  # The fixed clock text of every write.
BRAVO_REFUSED = {"aa0000000002": "rejected", "bb0000000002": "rejected", "ap": "rejected"}  # No write reaches Bravo.
STOPPED_TEXT = "The capture stopped. Read the portal log for the cause."  # The capture failure text.


def planned_record(statuses: dict[str, str] | None = None, tiers: tuple[int, int] = (3, 2)) -> dict[str, Any]:
    """Return one operation record with the site plan of two sites."""
    fleet = cascade_fleet(RehearsalClock().now())  # Each site holds one gateway, one switch, and one access point.
    return OrgRecordBuilder.with_site_plan(OrgRecordBuilder.build(fleet, statuses), tiers)  # The plan fields.


def stage_of(record: dict[str, Any], taker: StandInPostCheckTaker | None) -> tuple[VersionedStore, OrgPostCheckStage]:
    """Return the test store and the stage that writes into it."""
    store = VersionedStore(record)  # The store holds the record.
    records = OrgPhaseStore(store, OPERATION_ID, lambda: NOW_TEXT)  # The bounded writer of the watch.
    return store, OrgPostCheckStage(taker, records, OPERATION_ID)  # The caller runs the stage.


def rows(store: VersionedStore) -> dict[str, tuple[str, str, str]]:
    """Return the state, the message, and the capture key of each stored row."""
    stored = OrgPostCheckRows.of(store.read_run(OPERATION_ID) or {})  # The rows keyed by site.
    return {
        site: (row["state"], row["message"], row["capture_id"]) for site, row in stored.items()
    }  # The caller compares the summary.


def keys(taker: StandInPostCheckTaker) -> list[str]:
    """Return the capture key of each capture, in the capture order."""
    return [capture_id for _site, capture_id, _tier in taker.taken]  # The caller compares the keys.


def sites(taker: StandInPostCheckTaker) -> list[str]:
    """Return the site of each capture, in the capture order."""
    return [site for site, _capture_id, _tier in taker.taken]  # The caller compares the order.


def test_the_sites_follow_the_plan_order_with_the_precheck_tier() -> None:
    """Each site keeps its plan position, its readable name, and the tier of its pre-check capture."""
    assert OrgPostCheckRows.sites_of(planned_record()) == [
        PostCheckSite(ALPHA, SITE_NAMES[ALPHA], 3, True),
        PostCheckSite(BRAVO, SITE_NAMES[BRAVO], 2, True),
    ]  # The comparison needs the pre-check tier.


def test_a_site_with_no_accepted_write_reads_as_not_accepted() -> None:
    """The cloud refused every child job of Bravo, so Bravo received no firmware write."""
    found = OrgPostCheckRows.sites_of(planned_record(BRAVO_REFUSED))  # The sites of the refused plan.
    assert [(site.site_id, site.accepted) for site in found] == [(ALPHA, True), (BRAVO, False)]  # Bravo got no write.


def test_the_access_point_child_job_marks_the_site_of_each_target() -> None:
    """The organization child job names no site, so the reader reads the site of each access point."""
    refused = dict.fromkeys(("aa0000000001", "aa0000000002", "bb0000000001", "bb0000000002"), "rejected")  # No wire.
    found = OrgPostCheckRows.sites_of(planned_record(refused))  # Only the access point child job remains.
    assert [site.accepted for site in found] == [True, True]  # Both sites hold an access point.


def test_an_earlier_record_reads_the_sites_from_the_precheck_rows() -> None:
    """A record from an earlier release holds no site order and no name map."""
    record = planned_record()  # The record of the current release.
    del record["site_ids"], record["site_names"]  # An earlier release stored neither field.
    record["pre_captures"].reverse()  # The pre-check order decides now.
    found = OrgPostCheckRows.sites_of(record)  # The sites of the earlier record.
    assert [(site.site_id, site.site_name) for site in found] == [
        (BRAVO, SITE_NAMES[BRAVO]),
        (ALPHA, SITE_NAMES[ALPHA]),
    ]  # The pre-check rows supply the order and the names.


def test_a_site_with_no_precheck_row_gets_the_default_tier_and_shows_its_key() -> None:
    """A site with no pre-check row still gets a row, and a repeated site appears one time."""
    record = planned_record()  # The record of the current release.
    record["site_names"] = {}  # No name map.
    record["pre_captures"] = record["pre_captures"][:1]  # Only Alpha holds a pre-check capture.
    record["site_ids"] = [ALPHA, BRAVO, ALPHA]  # A damaged plan repeats a site.
    found = OrgPostCheckRows.sites_of(record)  # The sites of the damaged record.
    assert found == [
        PostCheckSite(ALPHA, SITE_NAMES[ALPHA], 3, True),
        PostCheckSite(BRAVO, BRAVO, 2, True),
    ]  # Bravo shows its key and the default tier.


def test_put_replaces_the_row_of_a_site_in_its_position() -> None:
    """A later row of a site replaces its earlier row, and the page order stays."""
    record = planned_record()  # The record of the current release.
    alpha, bravo = OrgPostCheckRows.sites_of(record)  # The two sites in the plan order.
    OrgPostCheckRows.put(record, alpha.row(PostCheckState.RUNNING, RUNNING_MESSAGE, "cap-1"))  # The first row.
    OrgPostCheckRows.put(record, bravo.row(PostCheckState.HELD, HELD_MESSAGE))  # The second row.
    OrgPostCheckRows.put(record, alpha.ended_row(PostCheckResult("cap-1", True, VERIFIED_TEXT)))  # A replacement.
    assert [(row["site_id"], row["state"]) for row in record[POSTCHECK_FIELD]] == [
        (ALPHA, "verified"),
        (BRAVO, "held"),
    ]  # Alpha keeps the first position.


def test_put_replaces_a_damaged_stored_value() -> None:
    """A damaged row list never breaks a write, and a damaged row reads as absent."""
    record = planned_record()  # The record of the current release.
    record[POSTCHECK_FIELD] = "damaged"  # The stored value is not a list.
    alpha = OrgPostCheckRows.sites_of(record)[0]  # The first site.
    OrgPostCheckRows.put(record, alpha.row(PostCheckState.HELD, HELD_MESSAGE))  # One write on the damaged value.
    assert [row["site_id"] for row in record[POSTCHECK_FIELD]] == [ALPHA]  # The list now holds one row.
    assert OrgPostCheckRows.of({POSTCHECK_FIELD: [None, {"state": "failed"}]}) == {}  # Each damaged row drops.


def test_first_failure_names_the_first_failed_site() -> None:
    """The finish reason names the first site whose capture did not verify."""
    record = planned_record()  # The record of the current release.
    alpha, bravo = OrgPostCheckRows.sites_of(record)  # The two sites in the plan order.
    OrgPostCheckRows.put(record, alpha.ended_row(PostCheckResult("cap-1", True, VERIFIED_TEXT)))  # A verified row.
    assert OrgPostCheckRows.first_failure(record) is None  # A verified row is no failure.
    OrgPostCheckRows.put(record, bravo.ended_row(PostCheckResult("cap-2", False, "")))  # A silent failure.
    assert OrgPostCheckRows.first_failure(record) == FAILURE_REASON.format(site=SITE_NAMES[BRAVO])  # Name Bravo.
    assert record[POSTCHECK_FIELD][1]["message"] == FAILED_MESSAGE  # A silent failure gets the default text.


def test_the_stage_takes_one_capture_of_each_site_in_the_plan_order() -> None:
    """FR-004 and FR-005. The stage visits each site in the plan order, at the tier of its pre-check capture."""
    taker = StandInPostCheckTaker()  # Every capture verifies.
    store, stage = stage_of(planned_record(), taker)  # The stage writes into the test store.
    stage.run()  # Take every capture.
    assert [(site, tier) for site, _key, tier in taker.taken] == [(ALPHA, 3), (BRAVO, 2)]  # The order and the tiers.
    first, second = keys(taker)  # The key of each capture.
    assert rows(store) == {
        ALPHA: ("verified", VERIFIED_TEXT, first),
        BRAVO: ("verified", VERIFIED_TEXT, second),
    }  # Each row names its capture.
    assert (store.watch_history[0]["state"], store.watch_history[0]["note"]) == ("running", STAGE_NOTE)  # First.


def test_the_stage_writes_a_running_row_before_the_capture_ends() -> None:
    """FR-006 and FR-015. The page shows the running row and the stage note while a capture reads the site."""
    taker = StandInPostCheckTaker()  # Every capture verifies.
    store, stage = stage_of(planned_record(), taker)  # The stage writes into the test store.
    seen: list[tuple[str, str, str]] = []  # The row state, the row text, and the watch note inside each capture.

    def inspect(site: PostCheckSite) -> None:
        record = store.read_run(OPERATION_ID) or {}  # The record during the capture.
        row = OrgPostCheckRows.of(record)[site.site_id]  # The row of the site under capture.
        seen.append((row["state"], row["message"], record[WATCH_KEY]["note"]))  # Keep the three values.

    taker.on_take = inspect  # Read the store inside each capture.
    stage.run()  # Take every capture.
    assert seen == [("running", RUNNING_MESSAGE, STAGE_NOTE)] * 2  # Both captures ran under a running row.


def test_the_stage_keeps_a_final_row_and_takes_no_second_capture() -> None:
    """FR-008. A resumed stage keeps each final row, so no site gets a second capture."""
    record = planned_record()  # The record of the current release.
    alpha = OrgPostCheckRows.sites_of(record)[0]  # The first site.
    OrgPostCheckRows.put(record, alpha.ended_row(PostCheckResult("cap-old", True, VERIFIED_TEXT)))  # A final row.
    taker = StandInPostCheckTaker()  # Every capture verifies.
    store, stage = stage_of(record, taker)  # The stage writes into the test store.
    stage.run()  # Resume the stage.
    assert sites(taker) == [BRAVO]  # Only Bravo gets a capture.
    assert rows(store)[ALPHA] == ("verified", VERIFIED_TEXT, "cap-old")  # Alpha keeps its row.


def test_the_stage_takes_again_a_capture_that_a_restart_left_running() -> None:
    """FR-008. A restart can stop a capture before it ends, so the resumed stage takes a new capture."""
    record = planned_record()  # The record of the current release.
    alpha = OrgPostCheckRows.sites_of(record)[0]  # The first site.
    OrgPostCheckRows.put(record, alpha.row(PostCheckState.RUNNING, RUNNING_MESSAGE, "cap-lost"))  # A lost capture.
    taker = StandInPostCheckTaker()  # Every capture verifies.
    store, stage = stage_of(record, taker)  # The stage writes into the test store.
    stage.run()  # Resume the stage.
    assert sites(taker) == [ALPHA, BRAVO]  # Alpha gets a new capture.
    assert rows(store)[ALPHA] == ("verified", VERIFIED_TEXT, keys(taker)[0])  # The new key replaces the lost key.


def test_the_manual_mode_holds_each_site_and_takes_no_capture() -> None:
    """FR-009. The manual mode takes no capture, and each row says why."""
    taker = StandInPostCheckTaker(mode="manual")  # The operator takes the second capture.
    store, stage = stage_of(planned_record(), taker)  # The stage writes into the test store.
    stage.run()  # Visit every site.
    assert taker.taken == []  # No capture ran.
    assert rows(store) == dict.fromkeys(SITE_IDS, ("held", HELD_MESSAGE, ""))  # Each site holds.


def test_a_site_with_no_accepted_write_is_skipped() -> None:
    """FR-010. A site that received no firmware write needs no proof of an upgrade."""
    taker = StandInPostCheckTaker()  # Every capture verifies.
    store, stage = stage_of(planned_record(BRAVO_REFUSED), taker)  # The cloud refused every Bravo child job.
    stage.run()  # Visit every site.
    assert sites(taker) == [ALPHA]  # Bravo gets no capture.
    assert rows(store)[BRAVO] == ("skipped", SKIPPED_MESSAGE, "")  # The row says why.


def test_a_capture_fault_fails_that_site_and_the_next_site_still_runs() -> None:
    """FR-011. A fault inside one capture never stops the capture of the next site."""
    taker = StandInPostCheckTaker(faults={ALPHA: RuntimeError("stand-in fault")})  # Alpha raises.
    store, stage = stage_of(planned_record(), taker)  # The stage writes into the test store.
    stage.run()  # Visit every site.
    first, second = keys(taker)  # The key of each capture.
    assert rows(store) == {
        ALPHA: ("failed", FAILED_MESSAGE, first),
        BRAVO: ("verified", VERIFIED_TEXT, second),
    }  # Only Alpha failed.


def test_a_capture_that_did_not_verify_keeps_its_own_text() -> None:
    """The row shows the failure text of the capture itself."""
    taker = StandInPostCheckTaker(faults={BRAVO: STOPPED_TEXT})  # Bravo answers a failure.
    store, stage = stage_of(planned_record(), taker)  # The stage writes into the test store.
    stage.run()  # Visit every site.
    assert rows(store)[BRAVO] == ("failed", STOPPED_TEXT, keys(taker)[1])  # The capture text stays.


def test_no_taker_writes_nothing_and_logs_a_warning(caplog: pytest.LogCaptureFixture) -> None:
    """A walk with no capture seam keeps the watch of issue #3245 unchanged."""
    store, stage = stage_of(planned_record(), None)  # No seam.
    with caplog.at_level(logging.WARNING):  # The warning names the gap.
        stage.run()  # Nothing to take.
    assert store.writes == 0  # The stage wrote nothing.
    assert "no post-check seam" in caplog.text  # The log names the gap.


def test_the_stage_ignores_a_cancellation() -> None:
    """FR-018. A single-site stop takes the post-check capture too, so a cancellation never skips it."""
    record = planned_record()  # The record of the current release.
    record["cancellation"] = {"requested": True, "results": []}  # The operator cancelled.
    taker = StandInPostCheckTaker()  # Every capture verifies.
    store, stage = stage_of(record, taker)  # The stage writes into the test store.
    stage.run()  # Visit every site.
    assert sites(taker) == [ALPHA, BRAVO]  # Both captures ran.
    assert [row[0] for row in rows(store).values()] == ["verified", "verified"]  # Both rows verified.


def test_a_plan_with_no_site_writes_nothing() -> None:
    """A damaged plan with no site gets no stage note."""
    record = planned_record()  # The record of the current release.
    record["site_ids"] = []  # The plan names no site.
    record["pre_captures"] = []  # No pre-check row either.
    store, stage = stage_of(record, StandInPostCheckTaker())  # The stage writes into the test store.
    stage.run()  # Nothing to visit.
    assert store.writes == 0  # The stage wrote nothing.
