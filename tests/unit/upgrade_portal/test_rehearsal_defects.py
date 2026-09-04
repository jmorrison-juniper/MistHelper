"""The three known defect classes, applied against the shipped code.

Why:
    A harness that passes against broken code is worse than no harness. Each
    test below breaks one shipped rule, runs the same rehearsal, and asserts
    that the rehearsal reports the break. The drill lives in
    ``tests/support/rehearsal/defects.py``, and ``monkeypatch`` reverts every
    break at the end of the test.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from src.firmware import upgrade_service
from src.upgrade_portal.runtime.runs import PhaseState, RunState
from src.upgrade_portal.upgrade import gate, stop
from tests.support.rehearsal import (
    DEFECT_NAMES,
    DefectDrill,
    FleetScript,
    RehearsalDeps,
    RehearsalHarness,
    cascade_fleet,
)
from tests.unit.upgrade_portal.test_rehearsal_stop import UPGRADE_ID, site_plan

# WHY: The cloud publishes the target version at this offset, and the device
# only reboots much later. The honest gate must wait for the second moment.
VERSION_OFFSET_SECONDS: float = 20.0
REBOOT_OFFSET_SECONDS: float = 200.0


@pytest.fixture
def drill() -> DefectDrill:
    """Return one drill that has applied no defect.

    Returns:
        The drill of this test.
    """
    return DefectDrill()  # Each test starts from a clean record of applied defects.


def _harness(monkeypatch: pytest.MonkeyPatch, root: Path, fleet: FleetScript | None = None) -> RehearsalHarness:
    """Build one attached harness that has not started yet.

    Args:
        monkeypatch: The pytest patch helper.
        root: The directory that holds the upgrade tracker file.
        fleet: The scripts of the run, or None for the cascade fleet.

    Returns:
        The attached harness, ready for a drill and a start.
    """
    harness = RehearsalHarness(RehearsalDeps(fleet=fleet))  # A fresh clock, store, and capture double.
    harness.attach(monkeypatch, root)  # The drill patches the seams that this call filled.
    return harness  # The caller applies the defect and then starts the run.


def _early_version_fleet() -> FleetScript:
    """Return a fleet whose cloud publishes the new version before the reboot.

    Why:
        The honest gate holds two real uptime readings that did not fall, so it
        waits. A gate that reads a clock instead settles at once.

    Returns:
        The scripted fleet.
    """
    fleet = cascade_fleet(0.0)  # The composed fleet, whose stamps this helper then moves.
    scripts = tuple(  # Each device reconnects and shows the new version early, and reboots late.
        replace(script, reconnect_at=VERSION_OFFSET_SECONDS, version_at=VERSION_OFFSET_SECONDS)
        for script in fleet.scripts
    )
    late = tuple(replace(script, uptime_reset_at=REBOOT_OFFSET_SECONDS) for script in scripts)  # The true reboot.
    return FleetScript(late, 0.0)  # The run starts at the first clock reading of the harness.


def test_an_event_search_without_the_family_fails_the_first_two_phases(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, drill: DefectDrill
) -> None:
    """The first defect class hides every gateway event and every switch event.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.
        drill: The defect drill of this test.
    """
    harness = _harness(monkeypatch, tmp_path / "data")  # The healthy run under the stand-in cloud.
    drill.event_family_ignored(monkeypatch, harness.cloud)  # The search now reads access points alone.
    harness.start()  # The shipped entry point at ``RunDriver.start``.
    harness.join()  # The phase deadline ends the run, so the join still returns.
    assert harness.record()["state"] == RunState.FAILED.value  # The rehearsal caught the defect.
    assert harness.phase_entry("gateways")["state"] == PhaseState.FAILED.value  # No gateway event arrived.
    assert harness.phase_entry("switches")["state"] != PhaseState.SETTLED.value  # No switch settled either.


def test_an_uptime_rule_that_reads_the_clock_settles_a_device_too_early(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, drill: DefectDrill
) -> None:
    """The second defect class proves a reboot that never happened.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.
        drill: The defect drill of this test.
    """
    harness = _harness(monkeypatch, tmp_path / "data", _early_version_fleet())  # The late reboot fleet.
    started_at = harness.clock.now()  # The anchor of every scripted offset of the run.
    drill.uptime_rule_reads_the_clock(monkeypatch, harness.cloud)  # The gate now believes every reading.
    harness.start()  # The shipped entry point at ``RunDriver.start``.
    harness.join()  # The broken gate settles fast, so the join returns at once.
    rounds = harness.progress.rounds()  # The poll record of the whole run, in round order.
    settled = [entry for entry in rounds if entry.phase == "gateways" and entry.settled == 2]  # Both gateways.
    assert settled  # The broken gate settled the phase, which the honest gate could not.
    assert settled[0].at < started_at + REBOOT_OFFSET_SECONDS  # The phase settled before the device rebooted.


def test_a_status_reader_that_takes_the_wrong_name_reports_no_phase(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, drill: DefectDrill
) -> None:
    """The third defect class loses the field that names the state of the write.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.
        drill: The defect drill of this test.
    """
    harness = _harness(monkeypatch, tmp_path / "data")  # The stand-in cloud answers the status read.
    target = stop.StopTarget(site_plan(harness.fleet), UPGRADE_ID)  # The site plan of the six devices.
    honest = stop.read_last_status(None, target)  # The shipped reader against the healthy code.
    assert honest is not None and honest["current_phase"]  # The cloud names the phase, and the reader takes it.
    drill.status_field_renamed(monkeypatch, harness.cloud)  # The reader now takes the name ``phase``.
    broken = stop.read_last_status(None, target)  # The same shipped reader against the broken code.
    assert broken is not None and broken["current_phase"] is None  # The rehearsal caught the missing field.


def test_the_drill_applies_three_defects_and_leaves_none_behind(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, drill: DefectDrill
) -> None:
    """Every defect class made a rehearsal fail, and no patch outlived its test.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.
        drill: The defect drill of this test.
    """
    honest_rule, honest_reader = gate.uptime_decreased, upgrade_service._normalize_status  # The shipped answers.
    with monkeypatch.context() as patch:  # The context reverts each patch at the end of the block.
        harness = _harness(patch, tmp_path / "data")  # One harness carries all three drills.
        drill.event_family_ignored(patch, harness.cloud)  # The first defect class.
        drill.uptime_rule_reads_the_clock(patch, harness.cloud)  # The second defect class.
        drill.status_field_renamed(patch, harness.cloud)  # The third defect class.
        assert tuple(drill.applied) == DEFECT_NAMES  # All 3 defect classes ran against the shipped code.
    assert gate.uptime_decreased is honest_rule  # The gate holds its shipped rule again.
    assert upgrade_service._normalize_status is honest_reader  # The reader holds its shipped name again.
