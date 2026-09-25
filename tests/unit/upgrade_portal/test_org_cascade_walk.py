"""Unit tests for the multi-site phase walk.

Why:
    Issue #3245. A multi-site upgrade must get the single-site cascade. The
    watch follows the gateways, the switches, the access points, and the
    wireless clients, in that order. These tests drive the shipped walk and the
    shipped settle gate against the stand-in cloud of the rehearsal kit. A
    driven clock moves the time, so no test waits in real time. No test opens
    a socket.
"""

from __future__ import annotations

import dataclasses
import threading
from typing import Any

import mistapi
import pytest

from src.upgrade_portal.runtime.runs import PHASE_ORDER
from src.upgrade_portal.upgrade.org_cascade import readers
from src.upgrade_portal.upgrade.org_cascade.record import (
    FAILED_NOTE,
    FINISHED_NOTE,
    STOPPED_NOTE,
    WATCH_KEY,
    OrgPhaseEntries,
)
from src.upgrade_portal.upgrade.org_cascade.walk import OrgCascade, OrgCascadeDeps, OrgCascadeRegistry, OrgPhaseGates
from src.upgrade_portal.upgrade.org_postcheck import OrgPostCheckRows
from tests.support.org_cascade import (
    OPERATION_ID,
    SITE_IDS,
    OrgRecordBuilder,
    StandInPostCheckTaker,
    VersionedStore,
)
from tests.support.rehearsal import (
    TYPE_ACCESS_POINT,
    TYPE_GATEWAY,
    TYPE_SWITCH,
    DeviceScript,
    FleetScript,
    RehearsalClock,
    RehearsalDeps,
    RehearsalHarness,
    cascade_fleet,
)

FAMILY_ORDER = [TYPE_GATEWAY, TYPE_SWITCH, TYPE_ACCESS_POINT]  # The cascade order of the three device families.
NEVER = 10**7  # A script offset that no test reaches, so the device never returns.


class CloudLog:
    """Record the family, the site, and the time of each statistics read."""

    def __init__(self, clock: RehearsalClock) -> None:
        """Start with no read."""
        self.clock = clock  # The time of each read.
        self.reads: list[tuple[str, Any, float]] = []  # The family, the site, and the time of each read.
        self.on_read: Any = None  # A test hook that runs inside each read.

    def families(self) -> list[str]:
        """Return the family of each read, in the read order."""
        return [family for family, _site, _at in self.reads]  # The caller receives the family order.


def attach(monkeypatch: pytest.MonkeyPatch, clock: RehearsalClock, fleet: FleetScript) -> CloudLog:
    """Attach the stand-in cloud, and record each statistics read."""
    cloud = RehearsalHarness(RehearsalDeps(clock=clock, fleet=fleet)).attach(monkeypatch)  # The stand-in answers.
    monkeypatch.setattr(readers, "resolve_page_limit", lambda: 1000)  # One page for each read.
    log = CloudLog(clock)  # The record of each read.

    def recording(session: Any, org_id: str, **keywords: Any) -> Any:
        log.reads.append((str(keywords.get("type")), keywords.get("site_id"), clock.now()))  # Keep the scope.
        if log.on_read is not None:  # A test writes the cancellation inside a read.
            log.on_read(keywords)  # The hook can cancel during a read.
        return cloud.list_org_devices_stats(session, org_id, **keywords)  # The stand-in answer.

    monkeypatch.setattr(mistapi.api.v1.orgs.stats, "listOrgDevicesStats", recording)  # Read through the log.
    return log  # The caller receives the read log.


def deps_of(store: VersionedStore, clock: RehearsalClock, deadline: int = 1800) -> OrgCascadeDeps:
    """Return the walk collaborators with the driven clock in every seat."""
    return OrgCascadeDeps(
        store=store, session=None, clock=clock.now, sleep=clock.sleep, deadline_seconds=deadline
    )  # The walk receives the test clock.


def run_walk(store: VersionedStore, clock: RehearsalClock, deadline: int = 1800) -> str:
    """Run one walk to its end, and return the final watch state."""
    return OrgCascade(deps_of(store, clock, deadline), OPERATION_ID).run()  # The caller receives the watch state.


def phases(store: VersionedStore) -> dict[str, tuple[str, int, int, str]]:
    """Return the state, the counts, and the note of each stored phase."""
    rows = OrgPhaseEntries.of(store.read_run(OPERATION_ID) or {})  # The four entries in the fixed order.
    return {
        row["name"]: (row["state"], row["settled"], row["total"], row["note"]) for row in rows
    }  # The caller receives the phase summary.


def watch(store: VersionedStore) -> dict[str, Any]:
    """Return the stored watch fields."""
    return dict((store.read_run(OPERATION_ID) or {})[WATCH_KEY])  # The caller receives the watch fields.


def fleet_of(clock: RehearsalClock, *scripts: DeviceScript) -> FleetScript:
    """Return a fleet that starts at the present reading of the clock."""
    return FleetScript(scripts=scripts, started_at=clock.now())  # The fleet starts at this time.


def join_watch() -> None:
    """Wait for the watch thread of the test operation to end."""
    for thread in [
        thread for thread in threading.enumerate() if thread.name == "org-cascade-00003245"
    ]:  # The test waits for the watch thread.
        thread.join(5)  # The driven clock makes every wait short.


def test_the_walk_settles_the_four_phases_in_the_cascade_order(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every device returns, so each phase settles, and each family waits for the family above it."""
    clock = RehearsalClock()  # The clock controls the test time.
    fleet = cascade_fleet(clock.now())  # The fleet defines the test devices.
    log = attach(monkeypatch, clock, fleet)  # The log records the cloud reads.
    store = VersionedStore(OrgRecordBuilder.build(fleet))  # The store holds the record.
    assert run_walk(store, clock) == "finished"  # The walk must finish.
    assert phases(store) == {  # The phases must match the cascade.
        "gateways": ("settled", 2, 2, ""),
        "switches": ("settled", 2, 2, ""),
        "aps": ("settled", 2, 2, ""),
        "clients": ("settled", 0, 0, ""),
    }
    assert log.families() == sorted(log.families(), key=FAMILY_ORDER.index)  # The reads must follow the cascade order.
    assert set(log.families()) == set(FAMILY_ORDER)  # The watch must read each family.
    assert watch(store)["state"] == "finished"  # The watch state must finish.
    assert watch(store)["note"] == FINISHED_NOTE  # The watch note must show success.
    assert watch(store)["reason"] is None  # No phase failed in this case.


def test_each_read_names_one_family_and_narrows_to_one_site(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-015. Two gateways sit at two sites, and one switch sits at one site."""
    clock = RehearsalClock()  # The clock controls the test time.
    scripts = (
        DeviceScript("aa0000000001", TYPE_GATEWAY),
        DeviceScript("aa0000000002", TYPE_GATEWAY),
    )  # The scripts define the gateways.
    fleet = fleet_of(clock, *scripts, DeviceScript("bb0000000001", TYPE_SWITCH))  # The fleet defines the test devices.
    log = attach(monkeypatch, clock, fleet)  # The log records the cloud reads.
    store = VersionedStore(OrgRecordBuilder.build(fleet))  # The store holds the record.
    assert run_walk(store, clock) == "finished"  # The walk must finish.
    scopes = {(family, site) for family, site, _at in log.reads}  # The scopes collect the cloud reads.
    assert scopes == {(TYPE_GATEWAY, None), (TYPE_SWITCH, SITE_IDS[0])}  # The scopes must match the planned reads.


def test_a_family_that_the_operation_does_not_hold_is_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-008. The operation holds no switch, so the switch phase reads skipped and nothing reads a switch."""
    clock = RehearsalClock()  # The clock controls the test time.
    fleet = fleet_of(
        clock, DeviceScript("aa0000000001", TYPE_GATEWAY), DeviceScript("cc0000000001", TYPE_ACCESS_POINT)
    )  # The fleet defines the test devices.
    log = attach(monkeypatch, clock, fleet)  # The log records the cloud reads.
    store = VersionedStore(OrgRecordBuilder.build(fleet))  # The store holds the record.
    assert run_walk(store, clock) == "finished"  # The walk must finish.
    assert phases(store)["switches"] == ("skipped", 0, 0, "")  # The switch phase must match the case.
    assert TYPE_SWITCH not in log.families()  # The watch must skip the switch reads.
    assert phases(store)["clients"] == ("settled", 0, 0, "")  # The client phase must match the case.


def test_a_lost_access_point_family_shuts_the_client_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    """No access point returns, so the client phase fails, and the reason names the first failure."""
    clock = RehearsalClock()  # The clock controls the test time.
    lost = (
        DeviceScript("cc0000000001", TYPE_ACCESS_POINT, reconnect_at=NEVER, version_at=NEVER),
    )  # The lost device never settles.
    fleet = fleet_of(clock, DeviceScript("aa0000000001", TYPE_GATEWAY), *lost)  # The fleet defines the test devices.
    attach(monkeypatch, clock, fleet)  # The stand-in cloud handles the reads.
    store = VersionedStore(OrgRecordBuilder.build(fleet))  # The store holds the record.
    assert run_walk(store, clock, deadline=300) == "finished"  # The walk must finish after the limit.
    assert phases(store)["aps"] == ("failed", 0, 1, "")  # The access point phase must match the case.
    assert phases(store)["clients"] == ("failed", 0, 0, "")  # The client phase must match the case.
    reason = "The access point phase failed. 1 device(s) did not return before the phase limit."  # The reason text.
    assert watch(store)["reason"] == reason  # The watch reason must name the phase.
    assert watch(store)["note"] == reason  # The watch note must name the phase.


def test_a_failed_phase_does_not_stop_the_later_phases(monkeypatch: pytest.MonkeyPatch) -> None:
    """The single-site cascade continues after a failure, and the multi-site watch does the same."""
    clock = RehearsalClock()  # The clock controls the test time.
    lost = DeviceScript(
        "aa0000000001", TYPE_GATEWAY, reconnect_at=NEVER, version_at=NEVER
    )  # The lost device never settles.
    fleet = fleet_of(clock, lost, DeviceScript("bb0000000001", TYPE_SWITCH))  # The fleet defines the test devices.
    log = attach(monkeypatch, clock, fleet)  # The log records the cloud reads.
    store = VersionedStore(OrgRecordBuilder.build(fleet))  # The store holds the record.
    assert run_walk(store, clock, deadline=300) == "finished"  # The walk must finish after the limit.
    assert phases(store)["gateways"][0] == "failed"  # The gateway phase must match the case.
    assert phases(store)["switches"][0] == "settled"  # The switch phase must settle.
    assert TYPE_SWITCH in log.families()  # The watch must read the switch family.
    assert str(watch(store)["reason"]).startswith(
        "The gateways phase failed."
    )  # The reason must name the gateway phase.


def test_a_refused_child_job_fails_its_phase_and_names_the_count(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-006. The cloud refused one gateway, so the gate follows the other gateway only."""
    clock = RehearsalClock()  # The clock controls the test time.
    fleet = cascade_fleet(clock.now())  # The fleet defines the test devices.
    attach(monkeypatch, clock, fleet)  # The stand-in cloud handles the reads.
    store = VersionedStore(
        OrgRecordBuilder.build(fleet, statuses={"aa0000000002": "rejected"})
    )  # The store holds the record.
    assert run_walk(store, clock) == "finished"  # The walk must finish.
    note = "The cloud did not accept the upgrade of 1 device(s) of this phase."  # The note names the refusal.
    assert phases(store)["gateways"] == ("failed", 1, 2, note)  # The gateway phase must match the case.
    assert watch(store)["reason"] == f"The gateways phase failed. {note}"  # The watch reason must name the refusal.


def test_a_phase_with_every_child_job_refused_fails_with_no_read(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-006. The watch does not wait 30 minutes for a device that cannot upgrade."""
    clock = RehearsalClock()  # The clock controls the test time.
    fleet = cascade_fleet(clock.now())  # The fleet defines the test devices.
    log = attach(monkeypatch, clock, fleet)  # The log records the cloud reads.
    refused = {"bb0000000001": "rejected", "bb0000000002": "not_submitted"}  # The refusals block the child jobs.
    store = VersionedStore(OrgRecordBuilder.build(fleet, statuses=refused))  # The store holds the record.
    assert run_walk(store, clock) == "finished"  # The walk must finish.
    assert phases(store)["switches"] == (  # The switch phase must match the case.
        "failed",
        0,
        2,
        "The cloud did not accept the upgrade of 2 device(s) of this phase.",
    )
    assert TYPE_SWITCH not in log.families()  # The watch must skip the switch reads.
    assert phases(store)["aps"][0] == "settled"  # The access point phase must match the case.


def test_a_scheduled_start_reads_no_statistics_before_the_start(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-010. The watch shows the start time, and it reads the cloud only after that time."""
    clock = RehearsalClock()  # The clock controls the test time.
    start = int(clock.now()) + 600  # The start time delays the watch.
    fleet = cascade_fleet(float(start))  # The fleet defines the test devices.
    log = attach(monkeypatch, clock, fleet)  # The log records the cloud reads.
    store = VersionedStore(OrgRecordBuilder.build(fleet, start_time=start))  # The store holds the record.
    assert run_walk(store, clock) == "finished"  # The walk must finish.
    assert min(at for _family, _site, at in log.reads) >= start  # The first read must follow the start.
    states = [row["state"] for row in store.watch_history]  # The states show the watch sequence.
    assert states[0] == "waiting_for_start"  # The first state must wait for start.
    assert (
        "UTC. The portal watches the first phase after that time." in store.watch_history[0]["note"]
    )  # The note must name the scheduled start.
    assert states[-1] == "finished"  # The last state must finish.


def test_a_cancellation_during_the_start_wait_stops_the_watch(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-011. The operator cancels a scheduled upgrade, so the watch reads nothing and stops."""
    clock = RehearsalClock()  # The clock controls the test time.
    start = int(clock.now()) + 3600  # The start time delays the watch.
    fleet = cascade_fleet(float(start))  # The fleet defines the test devices.
    log = attach(monkeypatch, clock, fleet)  # The log records the cloud reads.
    store = VersionedStore(OrgRecordBuilder.build(fleet, start_time=start))  # The store holds the record.

    def cancelling_sleep(seconds: float) -> None:
        clock.sleep(seconds)  # Move the driven clock one slice.
        store.cancel(OPERATION_ID)  # The operator cancels during the wait.

    deps = OrgCascadeDeps(
        store=store, session=None, clock=clock.now, sleep=cancelling_sleep
    )  # The dependencies use the test clock.
    assert OrgCascade(deps, OPERATION_ID).run() == "stopped"  # The start wait must stop.
    assert log.reads == []  # The watch must read no statistics.
    assert watch(store)["note"] == STOPPED_NOTE  # The watch note must show cancellation.
    assert {name: row[0] for name, row in phases(store).items()} == dict.fromkeys(
        PHASE_ORDER, "pending"
    )  # Each phase must return to pending.


def test_a_cancellation_during_a_phase_puts_the_waiting_entry_back_to_pending(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-011. The operator cancels while the switch gate waits, so no later phase starts."""
    clock = RehearsalClock()  # The clock controls the test time.
    lost = (
        DeviceScript("bb0000000001", TYPE_SWITCH, reconnect_at=NEVER, version_at=NEVER),
    )  # The lost device never settles.
    fleet = fleet_of(  # The fleet defines the test devices.
        clock, DeviceScript("aa0000000001", TYPE_GATEWAY), *lost, DeviceScript("cc0000000001", TYPE_ACCESS_POINT)
    )
    log = attach(monkeypatch, clock, fleet)  # The log records the cloud reads.
    store = VersionedStore(OrgRecordBuilder.build(fleet))  # The store holds the record.
    log.on_read = lambda keywords: (
        store.cancel(OPERATION_ID) if keywords.get("type") == TYPE_SWITCH else None
    )  # The hook cancels the switch phase.
    assert run_walk(store, clock) == "stopped"  # The cancellation must stop the watch.
    assert phases(store)["gateways"][0] == "settled"  # The gateway phase must match the case.
    assert phases(store)["switches"] == ("pending", 0, 0, "")  # The switch phase must match the case.
    assert phases(store)["aps"][0] == "pending"  # The access point phase must match the case.
    assert TYPE_ACCESS_POINT not in log.families()  # The watch must skip access point reads.
    assert "waiting" in [
        row.get("state") for row in store.phase_history("switches")
    ]  # The switch history must show waiting.


def test_a_resumed_walk_keeps_the_ended_phases(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-013. A walk that starts again after a restart continues with the first open phase."""
    clock = RehearsalClock()  # The clock controls the test time.
    fleet = cascade_fleet(clock.now())  # The fleet defines the test devices.
    log = attach(monkeypatch, clock, fleet)  # The log records the cloud reads.
    record = OrgRecordBuilder.build(fleet)  # The record starts the watch.
    ended = {  # The ended phase simulates a restart.
        "name": "gateways",
        "state": "settled",
        "settled": 2,
        "total": 2,
        "settled_at": "kept",
        "note": "",
        "failures": [],
    }
    OrgPhaseEntries.put(record, ended)  # The record stores the ended phase.
    record[WATCH_KEY]["state"] = "running"  # The watch state permits a restart.
    store = VersionedStore(record)  # The store holds the record.
    assert run_walk(store, clock) == "finished"  # The walk must finish.
    assert TYPE_GATEWAY not in log.families()  # The watch must skip the gateway reads.
    assert (
        OrgPhaseEntries.entry(store.read_run(OPERATION_ID) or {}, "gateways")["settled_at"] == "kept"
    )  # The resume must keep the end marker.
    assert phases(store)["switches"][0] == "settled"  # The switch phase must settle.


@pytest.mark.parametrize("state", ["finished", "stopped", "failed"])
def test_a_final_watch_never_runs_again(monkeypatch: pytest.MonkeyPatch, state: str) -> None:
    """FR-012. A walk that meets a final watch state reads nothing and writes nothing."""
    clock = RehearsalClock()  # The clock controls the test time.
    fleet = cascade_fleet(clock.now())  # The fleet defines the test devices.
    log = attach(monkeypatch, clock, fleet)  # The log records the cloud reads.
    record = OrgRecordBuilder.build(fleet)  # The record starts the watch.
    record[WATCH_KEY]["state"] = state  # The case sets the final state.
    store = VersionedStore(record)  # The store holds the record.
    assert run_walk(store, clock) == state  # The final state must remain unchanged.
    assert log.reads == []  # The watch must read no statistics.
    assert store.writes == 0  # The final watch must write nothing.


def test_an_internal_error_writes_the_failed_state(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-004. A fault inside a phase ends the thread with a state that the page shows."""
    clock = RehearsalClock()  # The clock controls the test time.
    fleet = cascade_fleet(clock.now())  # The fleet defines the test devices.
    attach(monkeypatch, clock, fleet)  # The stand-in cloud handles the reads.
    store = VersionedStore(OrgRecordBuilder.build(fleet))  # The store holds the record.

    def broken(_gates: OrgPhaseGates, _chosen: Any) -> Any:
        raise RuntimeError("the gate did not build")  # The fault tests the failed watch state.

    monkeypatch.setattr(OrgPhaseGates, "build", broken)  # The patch makes the phase build fail.
    assert (
        OrgCascadeRegistry.ensure_running(store.read_run(OPERATION_ID) or {}, deps_of(store, clock)) is True
    )  # The registry must start the watch.
    join_watch()  # The join waits for thread failure.
    assert watch(store)["state"] == "failed"  # The watch state must fail.
    assert watch(store)["note"] == FAILED_NOTE  # The watch note must show failure.
    assert phases(store)["gateways"] == ("pending", 0, 0, "")  # The gateway phase must match the case.


def test_the_failed_state_write_never_raises() -> None:
    """The thread must end even when the store fails."""

    class BrokenStore:
        def read_run(self, _run_id: str) -> dict[str, Any]:
            raise OSError("the store is not reachable")  # The fault tests store failure.

    deps = OrgCascadeDeps(store=BrokenStore(), session=None)  # The dependencies use the test clock.
    assert OrgCascade(deps, OPERATION_ID).fail() is None  # The failed write must not escape.


def test_a_long_read_stretches_the_wait_between_two_rounds(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-016. Three pages cost four calls in a round, so the wait between two rounds doubles."""
    clock = RehearsalClock()  # The clock controls the test time.
    lost = DeviceScript(
        "aa0000000001", TYPE_GATEWAY, reconnect_at=NEVER, version_at=NEVER
    )  # The lost device never settles.
    fleet = fleet_of(
        clock, lost, *(DeviceScript(f"aa00000000{index:02d}", TYPE_GATEWAY) for index in range(2, 7))
    )  # The fleet defines the test devices.
    attach(monkeypatch, clock, fleet)  # The stand-in cloud handles the reads.
    monkeypatch.setattr(readers, "resolve_page_limit", lambda: 2)  # The page limit creates extra reads.
    store = VersionedStore(OrgRecordBuilder.build(fleet))  # The store holds the record.
    assert run_walk(store, clock, deadline=300) == "finished"  # The walk must finish after the limit.
    assert 40.0 in clock.sleeps()  # The wait must grow after long reads.
    assert 20.0 not in clock.sleeps()  # The short wait must not remain.


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        pytest.param({}, True, id="ready"),
        pytest.param({"drop_watch": True}, False, id="no-watch"),
        pytest.param({"watch_state": "finished"}, False, id="final-watch"),
        pytest.param({"state": "submission_claimed"}, False, id="submission-open"),
        pytest.param({"refuse_all": True}, False, id="no-accepted-child"),
    ],
)
def test_the_registry_starts_a_watch_only_when_it_has_work(change: dict[str, Any], expected: bool) -> None:
    """FR-005 and FR-012. The registry refuses a record that holds no work for a watch."""
    fleet = cascade_fleet(1.0)  # The fleet defines the test devices.
    refused = (
        dict.fromkeys([*fleet.macs(), "ap"], "rejected") if change.get("refuse_all") else {}
    )  # The refusals block the child jobs.
    record = OrgRecordBuilder.build(fleet, statuses=refused)  # The record starts the watch.
    record["state"] = change.get("state", record["state"])  # The case sets the operation state.
    record[WATCH_KEY]["state"] = change.get(
        "watch_state", record[WATCH_KEY]["state"]
    )  # The watch state permits a restart.
    if change.get("drop_watch"):  # The case removes the watch when requested.
        del record[WATCH_KEY]  # The case removes the watch.
    assert OrgCascadeRegistry.may_run(record) is expected  # The registry decision must match the case.


def test_the_registry_keeps_one_thread_for_each_operation(monkeypatch: pytest.MonkeyPatch) -> None:
    """FR-012. Two polls that arrive together start one watch thread."""
    clock = RehearsalClock()  # The clock controls the test time.
    fleet = cascade_fleet(clock.now() + 3600)  # The fleet defines the test devices.
    attach(monkeypatch, clock, fleet)  # The stand-in cloud handles the reads.
    record = OrgRecordBuilder.build(fleet, start_time=int(clock.now()) + 3600)  # The record starts the watch.
    store = VersionedStore(record)  # The store holds the record.
    release = threading.Event()  # The event holds the watch thread.

    def held_sleep(_seconds: float) -> None:
        release.wait(5)  # Hold the thread in the start wait until the test releases it.
        store.cancel(OPERATION_ID)  # Then end the walk at once.

    deps = OrgCascadeDeps(
        store=store, session=None, clock=clock.now, sleep=held_sleep
    )  # The dependencies use the test clock.
    assert OrgCascadeRegistry.ensure_running(record, deps) is True  # The registry must start the watch.
    assert OrgCascadeRegistry.ensure_running(record, deps) is False  # The registry must reject the watch.
    release.set()  # The event lets the watch stop.
    join_watch()  # The join waits for thread failure.
    assert watch(store)["state"] == "stopped"  # The watch state must stop.
    assert (
        OrgCascadeRegistry.ensure_running(store.read_run(OPERATION_ID) or {}, deps) is False
    )  # The registry must reject the watch.


def post_rows(store: VersionedStore) -> list[str]:
    """Return the state of each stored post-check row, in the plan order (issue #3244)."""
    return [row["state"] for row in OrgPostCheckRows.of(store.read_run(OPERATION_ID) or {}).values()]  # The states.


def test_the_walk_takes_each_postcheck_after_the_last_phase(monkeypatch: pytest.MonkeyPatch) -> None:
    """Issue #3244, FR-001. The post-check capture of each site starts only after every phase ended."""
    clock = RehearsalClock()  # The clock controls the test time.
    fleet = cascade_fleet(clock.now())  # The fleet defines the test devices.
    attach(monkeypatch, clock, fleet)  # The stand-in cloud handles the reads.
    store = VersionedStore(OrgRecordBuilder.with_site_plan(OrgRecordBuilder.build(fleet)))  # The plan of two sites.
    taker = StandInPostCheckTaker()  # Every capture verifies.
    ended: list[dict[str, str]] = []  # The phase states inside each capture.
    taker.on_take = lambda site: ended.append({name: row[0] for name, row in phases(store).items()})  # Read.
    deps = dataclasses.replace(deps_of(store, clock), post_check=taker)  # The walk receives the seam.
    assert OrgCascade(deps, OPERATION_ID).run() == "finished"  # The walk must finish.
    assert ended == [dict.fromkeys(PHASE_ORDER, "settled")] * 2  # Every phase ended before each capture.
    assert [site for site, _key, _tier in taker.taken] == list(SITE_IDS)  # One capture for each site.
    assert post_rows(store) == ["verified", "verified"]  # Both rows verified.
    assert watch(store)["note"] == FINISHED_NOTE  # No failure, so the finished note stays.


def test_a_cancellation_during_a_phase_still_takes_each_postcheck(monkeypatch: pytest.MonkeyPatch) -> None:
    """Issue #3244, FR-002. A cancel during the switch phase takes the captures, then stops the watch."""
    clock = RehearsalClock()  # The clock controls the test time.
    lost = (DeviceScript("bb0000000001", TYPE_SWITCH, reconnect_at=NEVER, version_at=NEVER),)  # Never settles.
    fleet = fleet_of(  # The fleet defines the test devices.
        clock, DeviceScript("aa0000000001", TYPE_GATEWAY), *lost, DeviceScript("cc0000000001", TYPE_ACCESS_POINT)
    )
    log = attach(monkeypatch, clock, fleet)  # The log records the cloud reads.
    store = VersionedStore(OrgRecordBuilder.with_site_plan(OrgRecordBuilder.build(fleet)))  # The plan of two sites.
    log.on_read = lambda keywords: (
        store.cancel(OPERATION_ID) if keywords.get("type") == TYPE_SWITCH else None
    )  # The hook cancels the switch phase.
    taker = StandInPostCheckTaker()  # Every capture verifies.
    deps = dataclasses.replace(deps_of(store, clock), post_check=taker)  # The walk receives the seam.
    assert OrgCascade(deps, OPERATION_ID).run() == "stopped"  # The cancellation must stop the watch.
    assert [site for site, _key, _tier in taker.taken] == list(SITE_IDS)  # One capture for each site.
    assert phases(store)["switches"] == ("pending", 0, 0, "")  # The switch phase went back to pending.
    assert watch(store)["note"] == STOPPED_NOTE  # The page shows the stop.


def test_a_cancelled_schedule_still_takes_each_postcheck(monkeypatch: pytest.MonkeyPatch) -> None:
    """Issue #3244, FR-002. A cancel during the start wait takes the captures, then stops the watch."""
    clock = RehearsalClock()  # The clock controls the test time.
    start = int(clock.now()) + 3600  # The upgrade starts in one hour.
    fleet = cascade_fleet(clock.now() + 3600)  # The fleet defines the test devices.
    log = attach(monkeypatch, clock, fleet)  # The log records the cloud reads.
    store = VersionedStore(OrgRecordBuilder.with_site_plan(OrgRecordBuilder.build(fleet, start_time=start)))  # Plan.

    def cancelling_sleep(seconds: float) -> None:
        clock.sleep(seconds)  # Move the driven clock one slice.
        store.cancel(OPERATION_ID)  # The operator cancels during the wait.

    taker = StandInPostCheckTaker()  # Every capture verifies.
    deps = OrgCascadeDeps(
        store=store, session=None, clock=clock.now, sleep=cancelling_sleep, post_check=taker
    )  # The dependencies use the test clock and the seam.
    assert OrgCascade(deps, OPERATION_ID).run() == "stopped"  # The start wait must stop.
    assert log.reads == []  # The watch read no statistics.
    assert post_rows(store) == ["verified", "verified"]  # Both captures ran.
    assert watch(store)["note"] == STOPPED_NOTE  # The page shows the stop.
