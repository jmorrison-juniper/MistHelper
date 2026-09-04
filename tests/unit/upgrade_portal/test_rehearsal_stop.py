"""The rehearsal of the stop control in the middle of a run.

Why:
    User story 2 asks the suite to prove that a stop cancels the devices that
    have not started, spares the device that writes firmware, and reports a
    plain message. Every rule under test lives in
    ``src/upgrade_portal/upgrade/stop.py`` and in
    ``src/firmware/upgrade_service.py``.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from src.firmware.upgrade_service import DeviceTarget, GatewayFamily, PlanRoute, UpgradePlan
from src.upgrade_portal.runtime.runs import RunState
from src.upgrade_portal.runtime.signals import StopOutcome, StopRequestStore
from src.upgrade_portal.upgrade import options, stop
from tests.support.rehearsal import (
    ORG_ID,
    SITE_ID,
    VERSION_AFTER,
    FleetScript,
    RehearsalDeps,
    RehearsalHarness,
    stop_fleet,
)
from tests.support.rehearsal.cloud import FIRMWARE_WRITE_NAMES, UPGRADE_ID
from tests.unit.upgrade_portal.conftest import NetworkAttemptCounter

# WHY: The switch that already writes firmware when the operator presses stop.
# FR-038d forbids an interrupt, so this device must never read as cancelled.
WRITING_MAC: str = "bb0000000001"

# WHY: The session smart router of the organization scope plan. Its status read
# answers device statistics and no upgrade job, which is the case of FR-027.
ROUTER_MAC: str = "dd0000000001"

# WHY: The exact text that FR-038b asks the operator to type. Any other text
# must leave the run untouched.
CONFIRMATION: str = "STOP"


def _device_target(mac: str, device_type: str) -> DeviceTarget:
    """Return one plan target of the stop fleet.

    Args:
        mac: The address of the device.
        device_type: The family of the device.

    Returns:
        The plan target.
    """
    return DeviceTarget(mac, mac, device_type, "model", "0.14.29562", VERSION_AFTER, SITE_ID)


def site_plan(fleet: FleetScript) -> UpgradePlan:
    """Return the site scope plan of the six cascade devices.

    Args:
        fleet: The scripts of the run.

    Returns:
        The plan that the run submitted for the site.
    """
    route = PlanRoute("site", "upgradeSiteDevices", SITE_ID)  # The route that ``_cancel_endpoint_name`` reads.
    devices = [script for script in fleet.scripts if script.mac != ROUTER_MAC]  # Every device but the router.
    targets = tuple(_device_target(script.mac, script.device_type) for script in devices)  # The plan targets.
    return UpgradePlan(route, targets, {}, ())  # The body and the warnings play no part in a cancel.


def router_plan() -> UpgradePlan:
    """Return the organization scope plan of the session smart router.

    Returns:
        The plan that the run submitted for the router.
    """
    route = PlanRoute("org", "upgradeOrgSsrs", ORG_ID)  # The organization scope route of FR-027.
    return UpgradePlan(route, (_device_target(ROUTER_MAC, "gateway"),), {}, ())


def stop_targets(fleet: FleetScript) -> list[stop.StopTarget]:
    """Return one stop target for each plan of the run.

    Args:
        fleet: The scripts of the run.

    Returns:
        The site plan and the router plan, in that order.
    """
    return [
        stop.StopTarget(site_plan(fleet), UPGRADE_ID, GatewayFamily.JUNOS),  # The six cascade devices.
        stop.StopTarget(router_plan(), UPGRADE_ID, GatewayFamily.SSR),  # The router of the organization scope.
    ]


class StoppedRun:
    """One rehearsal run that an operator stopped in the middle.

    Why:
        Four tests read the same run. One class holds the harness and the
        outcome together, so each test reads one member and states one rule.
    """

    def __init__(self, harness: RehearsalHarness, outcome: StopOutcome) -> None:
        """Build one stopped run.

        Args:
            harness: The finished harness.
            outcome: The answer of the shipped stop control.
        """
        self.harness = harness  # The run record, the cloud, and the call log.
        self.outcome = outcome  # The three device lists and the plain message.


def run_and_stop(monkeypatch: pytest.MonkeyPatch, root: Path, writing: set[str]) -> StoppedRun:
    """Start one run, stop it inside a poll round, and answer the result.

    Why:
        A stop before the first phase would prove nothing about a run in
        flight. The pause hook holds one poll round, so the stop reaches a run
        that is truly upgrading.

    Args:
        monkeypatch: The pytest patch helper.
        root: The directory that holds the upgrade tracker file.
        writing: The devices that already write firmware.

    Returns:
        The finished harness and the stop outcome.
    """
    harness = RehearsalHarness(RehearsalDeps(fleet=stop_fleet(0.0)))  # The fleet that holds the router.
    harness.attach(monkeypatch, root)  # The five attachment points and the page size.
    harness.cloud.writing = set(writing)  # The status answer names these devices as mid-write.
    reached, holding = threading.Event(), threading.Event()  # The handshake of the held round.
    harness.cloud.set_pause(lambda: _hold(reached, holding))  # Hold the first poll round of the run.
    harness.start()  # The shipped entry point at ``RunDriver.start``.
    assert reached.wait(5.0)  # The run reached a poll round, so the stop lands in mid-run.
    outcome = _press_stop(harness)  # The shipped stop control, with no route and no browser.
    holding.set()  # Release the held round, so the driver can read the stop request.
    harness.cloud.set_pause(None)  # No later round waits on the event.
    harness.join()  # The run ends inside the join guard.
    return StoppedRun(harness, outcome)


def _hold(reached: threading.Event, holding: threading.Event) -> None:
    """Report that a poll round started, then hold that round.

    Args:
        reached: The event that tells the test that a round is in flight.
        holding: The event that the test sets to release the round.
    """
    reached.set()  # The test may now press stop against a truly busy run.
    holding.wait(5.0)  # The round waits, and the cap stops a hung test.


def _press_stop(harness: RehearsalHarness) -> StopOutcome:
    """Write the stop request and run the shipped stop control.

    Args:
        harness: The running harness.

    Returns:
        The three device lists and the plain message.
    """
    run_id = str(harness.record_body["run_id"])  # The key of the run under test.
    StopRequestStore(harness.deps.store).request(run_id, "operator@example.com", CONFIRMATION)  # The route write.
    return stop.stop_run_and_record(harness.deps.store, run_id, None, stop_targets(harness.fleet), CONFIRMATION)


@pytest.fixture
def stopped(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> StoppedRun:
    """Return one run that an operator stopped while one switch wrote firmware.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.

    Returns:
        The finished harness and the stop outcome.
    """
    return run_and_stop(monkeypatch, tmp_path / "data", {WRITING_MAC})


def test_the_stop_cancels_every_device_that_had_not_started(stopped: StoppedRun) -> None:
    """FR-024 asks the stop to cancel each device that holds its old firmware.

    Args:
        stopped: The stopped run.
    """
    quiet = {script.mac for script in stopped.harness.fleet.scripts} - {WRITING_MAC, ROUTER_MAC}  # The waiting five.
    assert set(stopped.outcome.cancelled) == quiet  # Every waiting device stopped and no other device.


def test_the_stop_never_interrupts_a_device_that_writes_firmware(stopped: StoppedRun) -> None:
    """FR-025 forbids an interrupt of a write, because that can brick a device.

    Args:
        stopped: The stopped run.
    """
    assert WRITING_MAC in stopped.outcome.already_writing  # The device that writes joins the honest list.
    assert WRITING_MAC not in stopped.outcome.cancelled  # A stop that the portal cannot prove is never claimed.


def test_the_message_states_that_the_writing_device_finishes(stopped: StoppedRun) -> None:
    """FR-026 asks for one plain sentence that an operator can act on.

    Args:
        stopped: The stopped run.
    """
    assert "never interrupts a write" in stopped.outcome.message  # The rule that keeps the device safe.
    assert "2 devices that write firmware" in stopped.outcome.message  # The switch and the unreadable router.


def test_the_router_cancel_travels_the_organization_scope_call(stopped: StoppedRun) -> None:
    """FR-027 asks the router of the organization scope to reach its own call.

    Why:
        This test once read ``router_plan().route.scope``, which is a constant
        of this module. That assertion passed whatever the shipped code did, so
        it proved nothing. FR-027 names the run record, so the test now reads
        the record, and the shipped ``options.resolve_family_scope`` is the
        function that put the value there.

    Args:
        stopped: The stopped run.
    """
    targets = stopped.harness.record()["targets"]  # The record that the shipped driver carried through the run.
    router = next(entry for entry in targets if entry["mac"] == ROUTER_MAC)  # The one session smart router.
    others = [entry for entry in targets if entry["mac"] != ROUTER_MAC]  # Every other device of the fleet.
    assert router["scope"] == "org"  # The record shows the organization scope for the router, as FR-027 asks.
    assert all(entry["scope"] == "site" for entry in others)  # No other device took the organization scope.
    assert stopped.harness.cloud.calls_of("cancelOrgSsrUpgrade") == 1  # The one cancel call of that scope.
    assert stopped.harness.cloud.calls_of("cancelSiteDeviceUpgrade") == 1  # The site plan kept its own call.


def test_the_shipped_classifier_decides_the_router_scope() -> None:
    """The scope of the record comes from the shipped code and not from this test.

    Why:
        The test above reads a field of the run record. That field is only
        honest while the shipped classifier writes it. This test names the
        shipped function and proves that the model of the router, and nothing
        else, produces the organization scope.
    """
    router_row = {"type": "gateway", "model": "SSR120"}  # The row that the target builder hands the classifier.
    junos_row = {"type": "gateway", "model": "SRX345"}  # A gateway of the other family.

    assert options.resolve_family_scope("gateway", router_row)[1] == "org"  # The shipped rule, not a constant here.
    assert options.resolve_family_scope("gateway", junos_row)[1] == "site"  # A Junos gateway stays at the site.
    assert options.resolve_family_scope("switch", junos_row)[1] == "site"  # A switch is never a gateway family.


def test_the_router_status_read_reports_an_unknown_state(stopped: StoppedRun) -> None:
    """The organization scope read answers statistics, so the portal must not guess.

    Args:
        stopped: The stopped run.
    """
    assert ROUTER_MAC in stopped.outcome.already_writing  # An unreadable state never reads as stopped.
    assert "could not read" in stopped.outcome.message  # The message names the plan the portal could not read.


def test_the_run_record_holds_the_stop_outcome(stopped: StoppedRun) -> None:
    """A page reload must show the same three lists and the same message.

    Args:
        stopped: The stopped run.
    """
    request = stopped.harness.record()["stop_request"]  # The stop request that the store holds.
    assert request is not None  # The route wrote the request before the cancel calls ran.
    assert request["outcome"]["message"] == stopped.outcome.message  # The record repeats the answer of the control.


def test_the_stopped_run_reaches_the_stopped_state(stopped: StoppedRun) -> None:
    """The driver reads the stop request and closes the run.

    Args:
        stopped: The stopped run.
    """
    assert stopped.harness.record()["state"] == RunState.STOPPED.value  # The one end state of a stopped run.


def test_a_stop_before_the_first_phase_still_closes_the_run(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The early stop of the edge case list ends the run with no phase at all.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.
    """
    harness = RehearsalHarness(RehearsalDeps(fleet=stop_fleet(0.0)))  # A run that stops before it polls.
    harness.attach(monkeypatch, tmp_path / "data")  # The five attachment points and the page size.
    run_id = str(harness.record_body["run_id"])  # The key of the run under test.
    harness.deps.store.write_run(dict(harness.record_body))  # The route reads the record before it writes a request.
    StopRequestStore(harness.deps.store).request(run_id, "operator@example.com", CONFIRMATION)  # Before the start.
    harness.start()  # The shipped entry point of the run.
    harness.join()  # The driver reads the request at the top of the first phase.
    assert harness.record()["state"] == RunState.STOPPED.value  # The run closed with no phase settled.


def test_a_stop_after_the_run_finished_changes_no_device(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The late stop of the edge case list must not claim a cancel of a finished run.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.
    """
    harness = RehearsalHarness(RehearsalDeps(fleet=stop_fleet(0.0)))  # A run that reaches its end first.
    harness.attach(monkeypatch, tmp_path / "data")  # The five attachment points and the page size.
    harness.cloud.writing = set(harness.fleet.macs())  # Every device already finished its write.
    harness.start()  # The shipped entry point of the run.
    harness.join()  # The run completes before the operator presses stop.
    outcome = stop.stop_run(None, stop_targets(harness.fleet), CONFIRMATION)  # The late stop.
    assert outcome.cancelled == ()  # A finished run offers no device to cancel.


def test_a_stop_with_the_wrong_text_reaches_no_cloud_call(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """FR-038b asks for the exact text, in the exact letter case.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.
    """
    harness = RehearsalHarness(RehearsalDeps(fleet=stop_fleet(0.0)))  # A run that no operator confirms.
    harness.attach(monkeypatch, tmp_path / "data")  # The five attachment points and the page size.
    with pytest.raises(Exception, match="STOP"):  # The shipped control refuses the wrong text.
        stop.stop_run(None, stop_targets(harness.fleet), "stop")
    assert harness.cloud.calls_of("cancelSiteDeviceUpgrade") == 0  # A refused stop reaches no cloud call.


def test_the_stop_run_opens_no_socket_and_writes_no_firmware(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, network_guard: NetworkAttemptCounter
) -> None:
    """SC-004 and SC-005 hold for the stop run as well as for the cascade.

    Args:
        monkeypatch: The pytest patch helper.
        tmp_path: The temporary directory of this test.
        network_guard: The counting network guard of this test.
    """
    stopped_run = run_and_stop(monkeypatch, tmp_path / "data", {WRITING_MAC})  # A whole stop under the guard.
    assert network_guard.attempts == 0  # SC-004 allows no attempt at all.
    for name in FIRMWARE_WRITE_NAMES:  # Each firmware write endpoint in turn.
        assert stopped_run.harness.cloud.calls_of(name) == 0  # SC-005 allows no write to any device.
