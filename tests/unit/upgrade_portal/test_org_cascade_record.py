"""Unit tests for the durable phase record of a multi-site upgrade.

Why:
    Issue #3245. The multi-site record holds the four single-site phase
    entries, the anchors of each device, and the state of the watch. These
    tests prove each record rule with plain dictionaries. No test opens a
    socket or starts a thread.
"""

from __future__ import annotations

from typing import Any

import pytest

from src.upgrade_portal.runtime.runs import PHASE_ORDER
from src.upgrade_portal.upgrade.driver import CLIENT_GATE_SHUT_REASON, PhaseOutcome
from src.upgrade_portal.upgrade.org_cascade.record import (
    ANCHORS_KEY,
    NOT_STARTED_NOTE,
    PHASES_KEY,
    WATCH_KEY,
    OrgPhaseEntries,
    OrgPhaseStore,
    OrgPhaseTargets,
    OrgPhaseWatch,
    WatchState,
)
from tests.support.org_cascade import AP_CHILD_KEY, OPERATION_ID, SITE_IDS, OrgRecordBuilder, VersionedStore
from tests.support.rehearsal import cascade_fleet

FLEET = cascade_fleet(1.0)  # Two gateways, two switches, and two access points.


def entry(name: str, state: str, settled: int = 0, total: int = 0, note: str = "") -> dict[str, Any]:
    """Return one stored phase entry in the single-site shape."""
    return {  # The helper returns one phase entry.
        "name": name,
        "state": state,
        "settled": settled,
        "total": total,
        "settled_at": None,
        "note": note,
        "failures": [],
    }


def with_phases(*rows: dict[str, Any]) -> dict[str, Any]:
    """Return one prepared record that holds the given phase entries."""
    record = OrgRecordBuilder.build(FLEET)  # The prepared record of the cascade fleet.
    for row in rows:  # Replace each named entry.
        OrgPhaseEntries.put(record, row)  # The record receives the phase entry.
    return record  # The helper returns the prepared record.


def test_collect_follows_the_accepted_devices_and_counts_the_refused_devices() -> None:
    """FR-006 and FR-015. One gateway child job is refused, and the other gateway sits at the second site."""
    record = OrgRecordBuilder.build(FLEET, statuses={"aa0000000001": "rejected"})  # One gateway child job fails.
    chosen = OrgPhaseTargets.collect(record, "gateways")  # The collector reads the gateway phase.
    assert [row["mac"] for row in chosen.targets] == ["aa0000000002"]  # Only the accepted gateway remains.
    assert chosen.excluded == 1  # One refused child job gets counted.
    assert chosen.site_ids == (SITE_IDS[1],)  # The remaining target names its site.
    assert chosen.targets[0]["uptime_before"] == FLEET.scripts[1].uptime_before  # The anchor stays with the target.
    assert chosen.targets[0]["last_seen_before"] is None  # A missing anchor value stays null.


def test_collect_reads_the_access_points_of_the_organization_child_job() -> None:
    """The access point child job holds devices at both sites, so the read scope names both sites."""
    chosen = OrgPhaseTargets.collect(
        OrgRecordBuilder.build(FLEET), "aps"
    )  # The collector reads the access point phase.
    assert [row["mac"] for row in chosen.targets] == ["cc0000000001", "cc0000000002"]  # Both access points remain.
    assert chosen.site_ids == tuple(sorted(SITE_IDS))  # The read scope names both sites.


def test_collect_never_changes_the_stored_targets() -> None:
    """The retry path rebuilds each target from the stored entry, so the watch adds no key there."""
    record = OrgRecordBuilder.build(FLEET)  # The record holds the original targets.
    before = [dict(target) for target in record["children"][0]["targets"]]  # The test keeps the original targets.
    OrgPhaseTargets.collect(record, "gateways")  # The collector reads without a write.
    assert record["children"][0]["targets"] == before  # The stored targets stay unchanged.


@pytest.mark.parametrize(
    ("reboot_at", "expected"),
    [
        pytest.param(1_900_000_000, 1_900_000_000, id="scheduled"),
        pytest.param(0, None, id="zero"),
        pytest.param(True, None, id="bool"),
    ],
)
def test_collect_copies_a_real_reboot_time_only(reboot_at: Any, expected: Any) -> None:
    """FR-009. The gate waits for a scheduled reboot, and a damaged value moves no deadline."""
    record = OrgRecordBuilder.build(FLEET)  # The record starts with a gateway child job.
    record["children"][0]["reboot_at"] = reboot_at  # The child job carries the tested deadline.
    chosen = OrgPhaseTargets.collect(record, "gateways")  # The collector copies a valid deadline.
    assert chosen.targets[0].get("reboot_at") == expected  # Only a real time reaches the target.


def test_a_missing_anchor_reads_as_null() -> None:
    """FR-002. A device with no stored anchor still reaches the gate."""
    record = OrgRecordBuilder.build(FLEET)  # The record starts with valid switch targets.
    record[ANCHORS_KEY] = "damaged"  # The anchor map cannot be read.
    chosen = OrgPhaseTargets.collect(record, "switches")  # The collector still returns switch targets.
    assert [row["uptime_before"] for row in chosen.targets] == [None, None]  # Missing anchors become null values.


def test_the_accepted_count_ignores_the_refused_child_jobs() -> None:
    """FR-005. The watch needs at least one child job that the cloud accepted."""
    refused = dict.fromkeys([*FLEET.macs(), AP_CHILD_KEY], "rejected")  # Most child jobs fail.
    refused["bb0000000001"] = "accepted"  # One switch child job remains accepted.
    assert (
        OrgPhaseTargets.accepted_count(OrgRecordBuilder.build(FLEET, statuses=refused)) == 1
    )  # One accepted job counts.
    assert OrgPhaseTargets.accepted_count({"children": "damaged"}) == 0  # A damaged list yields no child jobs.


def test_the_start_moment_reads_the_latest_start_of_an_accepted_child_job() -> None:
    """FR-010. A refused child job and a damaged value do not move the start time."""
    record = OrgRecordBuilder.build(
        FLEET, statuses={"aa0000000001": "rejected"}, start_time=1_900_000_000
    )  # One accepted job sets the start.
    record["children"][0]["body"]["start_time"] = 1_999_999_999  # The refused child job has a later start.
    record["children"][1]["body"]["start_time"] = True  # A damaged value cannot set the start.
    assert OrgPhaseTargets.start_moment(record) == 1_900_000_000  # The accepted child job sets the start.
    assert OrgPhaseTargets.start_moment(OrgRecordBuilder.build(FLEET)) is None  # No start reads as null.


def test_the_entries_keep_the_fixed_order_and_fill_each_gap() -> None:
    """FR-003. A record with one stored entry still shows four entries."""
    record = {PHASES_KEY: [entry("aps", "settled", 2, 2), "damaged"]}  # One phase entry is valid.
    rows = OrgPhaseEntries.of(record)  # The reader fills each missing phase entry.
    assert [row["name"] for row in rows] == list(PHASE_ORDER)  # The fixed phase order stays.
    assert [row["state"] for row in rows] == [
        "pending",
        "pending",
        "settled",
        "pending",
    ]  # Missing entries start pending.


def test_reset_waiting_puts_each_waiting_entry_back_to_pending() -> None:
    """A stopped watch leaves no entry that claims a wait."""
    record = with_phases(entry("gateways", "settled", 1, 1), OrgPhaseEntries.waiting("switches", 2))  # One phase waits.
    OrgPhaseEntries.reset_waiting(record)  # The stopped watch clears waiting state.
    assert [row["state"] for row in OrgPhaseEntries.of(record)] == [
        "settled",
        "pending",
        "pending",
        "pending",
    ]  # Waiting becomes pending.


def test_with_exclusions_keeps_a_phase_with_no_refused_device() -> None:
    """A phase whose devices all reached the cloud keeps the verdict of the gate."""
    outcome = PhaseOutcome("switches", "settled", 2, 2)  # The phase has no refused child job.
    assert OrgPhaseEntries.with_exclusions(outcome, 0) is outcome  # A clean phase keeps its outcome.


def test_with_exclusions_fails_the_phase_and_keeps_the_gate_note_first() -> None:
    """US2 scenario 4. The note names the gate cause and then the refused count."""
    outcome = OrgPhaseEntries.with_exclusions(
        PhaseOutcome("switches", "settled", 1, 1, note="Gate note."), 2
    )  # Refusals fail the phase.
    assert (outcome.state, outcome.settled, outcome.total) == ("failed", 1, 3)  # The refused devices raise the total.
    assert (
        outcome.note == "Gate note. The cloud did not accept the upgrade of 2 device(s) of this phase."
    )  # The gate note stays first.


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        pytest.param((), None, id="no-failure"),
        pytest.param((entry("switches", "failed", 1, 3, "Cause."),), "The switches phase failed. Cause.", id="note"),
        pytest.param(
            (entry("aps", "failed", 1, 4),),
            "The access point phase failed. 3 device(s) did not return before the phase limit.",
            id="count",
        ),
        pytest.param(
            (entry("aps", "failed", 0, 2), entry("gateways", "failed", 0, 1, "First.")),
            "The gateways phase failed. First.",
            id="first-in-order",
        ),
        pytest.param((entry("clients", "failed"),), CLIENT_GATE_SHUT_REASON, id="client-gate"),
    ],
)
def test_first_failure_uses_the_single_site_sentence(rows: tuple[dict[str, Any], ...], expected: str | None) -> None:
    """FR-007. The reason names the first failed phase in the fixed order, as the single-site driver does."""
    assert (
        OrgPhaseEntries.first_failure(with_phases(*rows)) == expected
    )  # The first failure matches the single-site page.


def test_the_active_label_names_the_waiting_phase() -> None:
    """FR-019. The summary names the phase that the watch follows now."""
    assert (
        OrgPhaseEntries.active_label(with_phases(OrgPhaseEntries.waiting("aps", 2))) == "Access points"
    )  # The label names the waiting phase.
    assert OrgPhaseEntries.active_label(with_phases()) is None  # No waiting phase gives no label.


def test_prepared_keeps_the_plan_and_adds_the_watch_fields() -> None:
    """FR-001 and FR-004. The submission stores the anchors, four pending entries, and the first watch state."""
    plan = {"operation_id": OPERATION_ID, "children": [], "record_version": 3}  # The plan carries the source version.
    record = OrgPhaseWatch.prepared(
        plan, {"aa0000000001": {"uptime_before": 5, "last_seen_before": 6}}, "Gap."
    )  # The watch adds the anchor gap.
    assert record["record_version"] == 3  # The record keeps the source version.
    assert record[ANCHORS_KEY] == {"aa0000000001": {"uptime_before": 5, "last_seen_before": 6}}  # The anchor is stored.
    assert [row["state"] for row in record[PHASES_KEY]] == ["pending"] * 4  # Every phase entry starts pending.
    assert record[WATCH_KEY] == {  # The watch starts in the first state.
        "state": "not_started",
        "note": NOT_STARTED_NOTE,
        "reason": None,
        "anchor_note": "Gap.",
    }
    assert "phase_watch" not in plan  # The source plan stays unchanged.


def test_set_state_keeps_the_anchor_gap_note() -> None:
    """FR-002. Every later watch write keeps the gap note of the anchor read."""
    record = OrgPhaseWatch.prepared({"operation_id": OPERATION_ID}, {}, "Gap.")  # The record starts with an anchor gap.
    OrgPhaseWatch.set_state(record, WatchState.RUNNING, "Running.", None)  # The watch moves to running.
    assert record[WATCH_KEY] == {
        "state": "running",
        "note": "Running.",
        "reason": None,
        "anchor_note": "Gap.",
    }  # The gap note stays.
    assert OrgPhaseWatch.state_of({}) == "not_started"  # A missing watch reads as not started.


def store_of() -> tuple[VersionedStore, OrgPhaseStore]:
    """Return a store with one prepared record, and the phase store over it."""
    store = VersionedStore(OrgRecordBuilder.build(FLEET))  # The store starts with one prepared record.
    return store, OrgPhaseStore(
        store, OPERATION_ID, lambda: "2026-09-24T00:00:00+00:00"
    )  # The helper returns the store pair.


def test_update_writes_one_new_version() -> None:
    """FR-014. One change advances the version by one and stamps the update time."""
    store, phases = store_of()  # One prepared record at version 1.
    written = phases.update(
        lambda record: OrgPhaseEntries.put(record, OrgPhaseEntries.waiting("gateways", 2))
    )  # One phase entry changes.
    assert written == store.read_run(OPERATION_ID)  # The update returns the record that the store now holds.
    assert (written["record_version"], written["updated_at"]) == (2, "2026-09-24T00:00:00+00:00")  # One step.
    assert store.writes == 1  # One change costs one write.


def test_update_reads_again_after_a_conflict() -> None:
    """FR-014. Another writer moves the version, so the watch reads again and writes the next version."""
    store, phases = store_of()  # One prepared record at version 1.
    store.conflicts = 2  # Another writer moves the version two times.
    written = phases.update(
        lambda record: OrgPhaseEntries.put(record, OrgPhaseEntries.waiting("gateways", 2))
    )  # The retry writes the phase entry.
    assert written == store.read_run(OPERATION_ID)  # The third try wrote the record that the store now holds.
    assert written["record_version"] == 4  # Two moves by the other writer, then one step by the watch.
    assert store.writes == 1  # The two conflicts wrote nothing.


def test_update_gives_up_after_five_conflicts() -> None:
    """FR-014. The walk never loops for ever against another writer."""
    store, phases = store_of()  # The store starts at the first version.
    store.conflicts = 5  # Another writer wins every retry.
    assert (
        phases.update(lambda record: OrgPhaseEntries.put(record, OrgPhaseEntries.waiting("gateways", 2))) is None
    )  # The update stops.
    assert store.writes == 0  # No failed retry writes the record.


def test_update_writes_nothing_when_the_record_already_holds_the_change() -> None:
    """A change that changes nothing keeps the version and the update time."""
    store, phases = store_of()  # One prepared record at version 1.
    before = store.read_run(OPERATION_ID)  # The record before the empty change.
    assert phases.update(lambda record: None) == before  # The update returns the current record as it is.
    assert store.read_run(OPERATION_ID) == before  # The version and the update time stay.
    assert store.writes == 0  # An empty change costs no write.


@pytest.mark.parametrize("version", [None, "3", True])
def test_update_refuses_a_record_with_a_damaged_version(version: Any) -> None:
    """A record with no integer version cannot take a compare-and-set write."""
    record = OrgRecordBuilder.build(FLEET)  # The record starts with a valid shape.
    record["record_version"] = version  # The version becomes invalid.
    store = VersionedStore(record)  # The store exposes the damaged record.
    phases = OrgPhaseStore(store, OPERATION_ID, lambda: "now")  # The phase store reads the damaged version.
    assert phases.update(lambda row: OrgPhaseEntries.reset_waiting(row)) is None  # The store refuses the update.
    assert store.writes == 0  # A damaged version writes nothing.
