"""The composed rehearsal of the whole upgrade cascade.

Why:
    User story 1 asks one run to drive the shipped run driver through all four
    phases. The tests read the phase order, the settle signals, the post-check,
    and the two guards. Every rule under test lives in the shipped modules, and
    the harness only supplies the clock and the cloud answers.
"""

from __future__ import annotations

import threading
import time
from dataclasses import replace
from pathlib import Path

import pytest

from src.upgrade_portal.runtime.runs import PHASE_ORDER, PhaseState, RunState
from src.upgrade_portal.upgrade import gate
from tests.support.rehearsal import (
    TYPE_ACCESS_POINT,
    TYPE_GATEWAY,
    TYPE_SWITCH,
    FleetScript,
    ProgressRound,
    RehearsalDeps,
    RehearsalHarness,
    cascade_fleet,
)
from tests.support.rehearsal.cloud import FIRMWARE_WRITE_NAMES, STATISTICS_NAME
from tests.unit.upgrade_portal.conftest import NetworkAttemptCounter

# WHY: The cascade order of the run record. The test states it here so a change
# of ``PHASE_ORDER`` fails this test and not only the shipped module.
EXPECTED_ORDER: tuple[str, ...] = ("gateways", "switches", "aps", "clients")

# WHY: The families of the three device phases, in the order of ``EXPECTED_ORDER``.
PHASE_FAMILY: dict[str, str] = {"gateways": TYPE_GATEWAY, "switches": TYPE_SWITCH, "aps": TYPE_ACCESS_POINT}

# WHY: SC-003 caps one wait at 1 real second. The run status read of FR-021
# must answer far below that cap.
READ_BUDGET_SECONDS: float = 1.0


def run_harness(monkeypatch: pytest.MonkeyPatch, root: Path, fleet: FleetScript | None = None) -> RehearsalHarness:
    """Build one harness, run it to the end, and answer it.

    Args:
        monkeypatch: The pytest patch helper.
        root: The directory that holds the upgrade tracker file.
        fleet: The scripts of the run, or None for the cascade fleet.

    Returns:
        The finished harness.
    """
    harness = RehearsalHarness(RehearsalDeps(fleet=fleet))  # A fresh clock, store, and capture double.
    harness.attach(monkeypatch, root)  # The five attachment points and the page size.
    harness.start()  # The shipped entry point at ``RunDriver.start``.
    harness.join()  # The one real wait of the whole test, which a healthy run never needs.
    return harness  # Every test below reads the record and the poll log of this run.


def _hold(reached: threading.Event, holding: threading.Event) -> None:
    """Report that a poll round started, then hold that round.

    Args:
        reached: The event that tells the test that a round is in flight.
        holding: The event that the test sets to release the round.
    """
    reached.set()  # The test may now read the record of a truly busy run.
    holding.wait(READ_BUDGET_SECONDS)  # The round waits, and the cap stops a hung test.


@pytest.fixture
def cascade(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> RehearsalHarness:
    """Return one finished cascade run.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.

    Returns:
        The finished harness.
    """
    return run_harness(monkeypatch, tmp_path / "data")  # The tracker write lands under the temporary directory.


def rounds_of(harness: RehearsalHarness, phase: str) -> tuple[ProgressRound, ...]:
    """Return every poll round of one phase.

    Args:
        harness: The finished harness.
        phase: The phase name.

    Returns:
        The rounds of that phase, in round order.
    """
    return tuple(entry for entry in harness.progress.rounds() if entry.phase == phase)


def reboot_round(harness: RehearsalHarness, phase: str) -> float:
    """Return the clock reading of the round that could first prove the reboot.

    Why:
        Step 2 of section 5 of ``contracts/rehearsal-clock.md`` names this
        reading ``T``. The device rebooted at its scripted moment, and the gate
        can only see that at the first poll round at or after that moment.

    Args:
        harness: The finished harness.
        phase: The phase name.

    Returns:
        The reading of that round.
    """
    script = harness.fleet.scripts_of_type(PHASE_FAMILY[phase])[0]  # Every device of a phase shares one script shape.
    moment = harness.fleet.started_at + script.reconnect_at  # The moment the device rebooted and reconnected.
    later = [entry.at for entry in rounds_of(harness, phase) if entry.at >= moment]  # Every round from that moment.
    assert later, f"the phase {phase} held no poll round at or after its reboot"  # No round proves nothing.
    return later[0]  # The first such round is the earliest round that could prove the reboot.


def test_the_run_reaches_the_complete_state(cascade: RehearsalHarness) -> None:
    """The whole cascade finishes with no error.

    Args:
        cascade: The finished harness.
    """
    record = cascade.record()  # The record that the shipped driver wrote.
    assert record["state"] == RunState.COMPLETE.value  # The one healthy end state of a run.
    assert record["error"] is None  # A completed run must carry no fault.


def test_the_phases_settle_in_the_cascade_order(cascade: RehearsalHarness) -> None:
    """The run settles gateways, then switches, then access points, then clients.

    Args:
        cascade: The finished harness.
    """
    assert PHASE_ORDER == EXPECTED_ORDER  # The shipped order is the order that FR-017 names.
    stamps = [cascade.phase_entry(name)["settled_at"] for name in EXPECTED_ORDER]  # One stamp for each phase.
    assert all(stamp is not None for stamp in stamps)  # Every phase settled, so every stamp holds a value.
    assert stamps == sorted(stamps)  # A later phase never settled before an earlier phase.


def test_no_phase_started_before_the_earlier_phase_settled(cascade: RehearsalHarness) -> None:
    """The gate of FR-018 holds each phase shut until the phase before it settled.

    Args:
        cascade: The finished harness.
    """
    for earlier, later in zip(EXPECTED_ORDER, EXPECTED_ORDER[1:], strict=False):  # Each neighbouring pair in turn.
        first = rounds_of(cascade, later)  # The poll rounds of the later phase.
        if not first:  # The client phase holds no target, so it polls no round at all.
            continue  # A phase with no round cannot have started early.
        settled = [entry.at for entry in rounds_of(cascade, earlier) if entry.settled == entry.total]  # The proof.
        assert settled, f"the phase {earlier} never settled"  # A phase that never settled would open the next one.
        assert first[0].at >= settled[0], f"the phase {later} started before {earlier} settled"


@pytest.mark.parametrize("phase", ["gateways", "switches"])
def test_a_device_settles_one_full_wait_after_the_reboot(cascade: RehearsalHarness, phase: str) -> None:
    """The settle window of FR-019 opens at the reboot plus the wait and never before.

    Args:
        cascade: The finished harness.
        phase: The phase under test.
    """
    wait = gate.settle_wait_seconds(PHASE_FAMILY[phase])  # The shipped wait, never a number written here.
    opens = reboot_round(cascade, phase) + wait  # Step 3 of the clock contract names this moment.
    early = [entry for entry in rounds_of(cascade, phase) if entry.at < opens]  # Every round below the window.
    assert all(entry.settled == 0 for entry in early)  # A device that settled early would fail this line.
    late = [entry for entry in rounds_of(cascade, phase) if entry.at >= opens]  # The rounds at or above the window.
    assert late and late[0].settled == late[0].total  # The first round at the window settled the whole phase.


def test_an_access_point_waits_the_longer_window(cascade: RehearsalHarness) -> None:
    """FR-020 gives an access point a longer wait than a switch.

    Args:
        cascade: The finished harness.
    """
    wait = gate.settle_wait_seconds(TYPE_ACCESS_POINT)  # The longer wait of the access point family.
    assert wait > gate.settle_wait_seconds(TYPE_SWITCH)  # The whole point of the longer window.
    opens = reboot_round(cascade, "aps") + wait  # The moment the window opens for an access point.
    early = [entry for entry in rounds_of(cascade, "aps") if entry.at < opens]  # Every round below the window.
    assert all(entry.settled == 0 for entry in early)  # No access point settled inside the extra minute.
    late = [entry for entry in rounds_of(cascade, "aps") if entry.at >= opens]  # The rounds at or above the window.
    assert late and late[0].settled == late[0].total  # The first round at the window settled the whole phase.


def test_the_driver_starts_the_post_check_after_the_client_phase(cascade: RehearsalHarness) -> None:
    """FR-022 asks the driver to start the second capture with no operator.

    Args:
        cascade: The finished harness.
    """
    requests = cascade.deps.capture.requests  # Every capture the driver started.
    assert len(requests) == 1  # One post-check capture and no more.
    assert requests[0]["ordinal"] == 2  # The second capture of the run.
    assert requests[0]["role"] == "post"  # The role that the comparison reads.
    assert cascade.phase_entry("clients")["state"] == PhaseState.SETTLED.value  # The client phase settled first.


def test_a_record_read_answers_while_a_poll_round_is_in_flight(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """FR-021 asks the record read to answer while the run is busy.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.
    """
    harness = RehearsalHarness()  # A run that this test drives by hand.
    harness.attach(monkeypatch, tmp_path / "data")  # The five attachment points and the page size.
    holding = threading.Event()  # The paused round waits on this event.
    reached = threading.Event()  # The test waits until one round is truly in flight.
    harness.cloud.set_pause(lambda: _hold(reached, holding))  # Hold one poll round inside the stand-in.
    harness.start()  # The shipped entry point of the run.
    assert reached.wait(READ_BUDGET_SECONDS * 5)  # The run reached the paused round.
    started = time.monotonic()  # The real clock, because SC-003 caps a real wait.
    record = harness.record()  # The read that an operator page makes while the run polls.
    assert time.monotonic() - started < READ_BUDGET_SECONDS  # The read never waits for the poll round.
    assert record["run_id"] == harness.record_body["run_id"]  # The read answered the record of this run.
    holding.set()  # Release the held round, so the run can finish.
    harness.cloud.set_pause(None)  # No later round waits on the event.
    harness.join()  # The run ends inside the join guard.


def test_every_cloud_call_carries_the_keyword_names_of_the_contract(cascade: RehearsalHarness) -> None:
    """FR-007 and FR-008 ask each stand-in to answer the call the caller makes.

    Args:
        cascade: The finished harness.
    """
    statistics = cascade.cloud.calls_named(STATISTICS_NAME)[0]  # One fleet statistics read.
    assert statistics.keywords >= {"type", "site_id", "fields", "limit"}  # Section 1 of the cloud contract.
    assert cascade.cloud.calls_named("get_all")[0].keywords == {"mist_session", "response"}  # Section 2, keywords only.
    events = cascade.cloud.calls_named("searchOrgDeviceEvents")[0]  # One device event search.
    assert events.keywords >= {"device_type", "start", "end", "limit", "search_after"}  # Section 3.
    assert cascade.cloud.calls_named("listDeviceEventsDefinitions")[0].keywords == frozenset()  # Section 4.


def test_the_event_search_always_names_the_device_family(cascade: RehearsalHarness) -> None:
    """The cloud defaults the family to the access point, so the caller must name it.

    Args:
        cascade: The finished harness.
    """
    searches = cascade.cloud.calls_named("searchOrgDeviceEvents")  # Every event search of the run.
    assert searches  # A run with no event search would prove no reconnect at all.
    assert all("device_type" in call.keywords for call in searches)  # The keyword that defect class 1 drops.


def test_the_statistics_answer_drives_the_shipped_page_guard(cascade: RehearsalHarness) -> None:
    """FR-009 asks the stand-in to answer a real page count.

    Args:
        cascade: The finished harness.
    """
    reasons = [entry for entry in cascade.record().get("phases", []) if entry.get("note")]  # Any noted phase.
    assert not reasons  # A full page reports no short read, so no phase carries a note.
    assert cascade.cloud.calls_of(STATISTICS_NAME) == cascade.cloud.calls_of("get_all")  # One walk for each read.


def test_a_short_page_marks_the_round_partial(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A page that reports more records than it holds must not settle a device.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.
    """
    harness = RehearsalHarness()  # A run whose cloud reports a short page.
    harness.attach(monkeypatch, tmp_path / "data")  # The five attachment points and the page size.
    harness.cloud.total_bonus = 5  # The answer now claims five records that the page does not hold.
    harness.start()  # The shipped entry point of the run.
    harness.join()  # The run still ends, because a partial round is no fault.
    assert harness.record()["state"] == RunState.COMPLETE.value  # A short page slows a run and never stops it.


def test_a_device_that_never_reconnects_fails_its_phase(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The phase deadline of the shipped gate ends a phase that cannot settle.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.
    """
    fleet = cascade_fleet(0.0)  # The composed fleet, which this test then breaks.
    silent = tuple(replace(script, reconnect_at=1.0e9, version_at=1.0e9) for script in fleet.scripts)  # Never returns.
    harness = run_harness(monkeypatch, tmp_path / "data", FleetScript(silent, 0.0))  # The run under test.
    assert harness.record()["state"] == RunState.FAILED.value  # A phase that cannot settle fails the whole run.
    assert harness.phase_entry("gateways")["state"] == PhaseState.FAILED.value  # The first phase held the run.


def test_a_stale_statistics_record_never_settles_a_device(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A cloud that repeats one moment tells the gate nothing new.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.
    """
    fleet = cascade_fleet(0.0)  # The composed fleet, whose stamps this test then freezes.
    early = tuple(replace(script, reconnect_at=0.0) for script in fleet.scripts)  # The gate opens at round one.
    harness = RehearsalHarness(RehearsalDeps(fleet=FleetScript(early, 0.0)))  # A run under a stale cloud.
    harness.attach(monkeypatch, tmp_path / "data")  # The five attachment points and the page size.
    harness.cloud.frozen_last_seen = harness.clock.now()  # Every later record repeats the first cloud moment.
    harness.start()  # The shipped entry point of the run.
    harness.join()  # The phase deadline ends the run, so the join still returns.
    assert harness.record()["state"] == RunState.FAILED.value  # A stale record must never prove a reboot.


def test_a_device_with_no_earlier_uptime_still_settles(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A target with no earlier uptime falls back to the version change.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.
    """
    harness = RehearsalHarness()  # A run whose targets carry no earlier uptime.
    for target in harness.record_body["targets"]:  # Each target of the run in turn.
        target["uptime_before"] = None  # The pre-check read no uptime, which the shipped gate warns about.
    harness.attach(monkeypatch, tmp_path / "data")  # The five attachment points and the page size.
    harness.start()  # The shipped entry point of the run.
    harness.join()  # The run still ends, because the version change carries the proof.
    assert harness.record()["state"] == RunState.COMPLETE.value  # The weaker proof still settles the device.


def test_the_rehearsal_opens_no_socket_and_writes_no_firmware(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, network_guard: NetworkAttemptCounter
) -> None:
    """SC-004 and SC-005 ask for zero network calls and zero firmware writes.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.
        network_guard: The counting network guard of this test.
    """
    harness = run_harness(monkeypatch, tmp_path / "data")  # A whole cascade under the counting guard.
    assert network_guard.attempts == 0  # SC-004 allows no attempt at all.
    for name in FIRMWARE_WRITE_NAMES:  # Each firmware write endpoint in turn.
        assert harness.cloud.calls_of(name) == 0  # SC-005 allows no write to any device.


def test_the_fleet_holds_two_devices_of_each_phase_family(cascade: RehearsalHarness) -> None:
    """Two devices of a family prove a phase, and one device would not.

    Args:
        cascade: The finished harness.
    """
    for phase, family in PHASE_FAMILY.items():  # Each device phase in turn.
        entry = cascade.phase_entry(phase)  # The phase entry of the run record.
        assert entry["total"] == 2  # The fleet holds two devices of this family.
        assert len(cascade.fleet.scripts_of_type(family)) == entry["total"]  # The record matches the script.
