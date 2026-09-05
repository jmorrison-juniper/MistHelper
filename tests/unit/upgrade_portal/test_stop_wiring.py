"""Prove the stop seam of the upgrade portal cancels the devices that it names.

Why:
    Before this wiring a stop cancelled nothing. The route read an empty
    `STOP_RUNNER` seam, answered with three empty lists, and every device kept
    on upgrading. These tests read the seam straight, with a stand-in store, a
    stand-in session, and a stand-in cloud. No test here opens a socket.

    FR-038f forbids a claim of a cancel that never happened. Three tests below
    hold that rule: a run with no accepted call, a stored row that names no
    plan, and a cancel call that the cloud refused.
"""

from types import SimpleNamespace  # The stand-in operator record and the stand-in plan.
from typing import Any  # The run record and the cloud answers are free-form.

import pytest  # The test framework of the project.

from src.firmware.upgrade_service import (  # The upgrade seam that the stop module calls.
    ENDPOINT_ORG_SSRS,  # The organization call of a session smart router.
    ENDPOINT_SITE_DEVICES,  # The site call of every other device.
    CancelOutcome,  # The answer shape of one cancel call.
    GatewayFamily,  # The family that the status read of the stop needs.
)
from src.upgrade_portal.app import factory, wiring  # The units under test.
from src.upgrade_portal.upgrade import stop  # The module that owns every cancel call.

RUN_ID = "run-1"  # One run key for every test of this module.
ORG_ID = "org-a"  # One organization name for every test of this module.
SITE_ID = "site-a"  # One site name for every test of this module.
MAC_ONE = "5c5b350e0001"  # The one device of the first upgrade plan.
MAC_TWO = "5c5b350e0002"  # The one device of the second upgrade plan.
MAC_ABSENT = "5c5b350e0009"  # A device that no plan of the run holds.
UPGRADE_ONE = "cloud-upgrade-1"  # The cloud identifier of the first accepted call.
UPGRADE_TWO = "cloud-upgrade-2"  # The cloud identifier of the second accepted call.


class MemoryRunStore:
    """Hold one run record in memory, as the run store seam does.

    Why:
        The stop reads the run and writes the outcome back. A real store would
        need ArangoDB, so this class answers both calls from one dictionary.
    """

    def __init__(self, record: dict[str, Any]) -> None:
        """Hold the one run record of the test.

        Args:
            record: The run record that every read answers with.
        """
        self.record = record  # The stop reads this record and writes it back.
        self.writes = 0  # Counts each write, so a test can prove that nothing landed.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return the held record when the key matches.

        Args:
            run_id: The run key of the read.

        Returns:
            The record, or None when the key names another run.
        """
        return self.record if self.record.get("run_id") == run_id else None  # One run only.

    def write_run(self, run: dict[str, Any]) -> bool:
        """Hold one written record and report a landed write.

        Args:
            run: The whole run record.

        Returns:
            True, because this store accepts every write.
        """
        self.record = run  # The next read then answers with the changed record.
        self.writes += 1  # A test reads this count to prove that the outcome landed.
        return True  # The stop store raises when a write reports False.


class CancelRecorder:
    """Record each cancel call and report every device of the plan as stopped.

    Why:
        The test must prove that the seam sends the right cloud identifier for
        the right plan. This recorder holds both values and reaches no cloud.
    """

    def __init__(self) -> None:
        """Start with no recorded call."""
        self.calls: list[tuple[str, tuple[str, ...]]] = []  # One entry for each cancel call.

    def __call__(self, session: Any, plan: Any, upgrade_id: str, last_status: Any = None) -> CancelOutcome:
        """Record one cancel call and answer as a cloud that stopped every device.

        Args:
            session: The cloud session. This recorder reads none of it.
            plan: The plan of the cancel call.
            upgrade_id: The cloud identifier of the upgrade.
            last_status: The status that the portal read first.

        Returns:
            An outcome that names every device of the plan as cancelled.
        """
        macs = stop.plan_macs(plan)  # The addresses that this one plan sent.
        self.calls.append((upgrade_id, macs))  # A test reads the pair of both values.
        return CancelOutcome(macs, (), (), "The portal cancelled the devices.")  # A clean stop.


def refuse_cancel(*args: Any, **kwargs: Any) -> Any:
    """Raise, to stand for a cloud that refused the cancel call.

    Args:
        *args: The arguments of the call. This stand-in reads none of them.
        **kwargs: The keyword arguments of the call.

    Returns:
        Nothing. This function always raises.

    Raises:
        RuntimeError: Always.
    """
    raise RuntimeError("The cloud did not answer the cancel call.")  # `cancel_target` holds this fault.


def stop_request_record() -> dict[str, Any]:
    """Build the stop request that the route already wrote onto the run.

    Why:
        `stop_run_and_record` adds the outcome to a request that already exists.
        A record with no request would make that write raise, and the seam would
        then answer None for a reason that no test here means to read.

    Returns:
        The stop request record.
    """
    return {  # The five fields of one recorded stop request.
        "requested_by": "operator@example.com",  # The operator who asked for the stop.
        "requested_at": "2026-08-19T11:00:00+00:00",  # One fixed moment, so no test reads a clock.
        "confirmation_text": stop.STOP_CONFIRMATION_TEXT,  # The exact word that FR-038b demands.
        "scope": "run",  # A stop always covers the whole run.
        "outcome": None,  # Empty until the cancel calls report.
    }


def upgrade_row(upgrade_id: str, macs: tuple[str, ...]) -> dict[str, Any]:
    """Build one stored row of an accepted cloud upgrade call.

    Why:
        `CloudUpgradeSubmitter` writes this shape for each accepted call. The
        pair of the identifier and the address list is the whole input of the
        stop seam, so every test builds its rows here.

    Args:
        upgrade_id: The cloud identifier of the accepted call.
        macs: The addresses that the accepted call carried.

    Returns:
        The stored row.
    """
    return {  # The four fields that `_submission_row` writes.
        "upgrade_id": upgrade_id,  # The stop reads this identifier back.
        "scope": "site",  # The word site or the word org.
        "accepted": list(macs),  # The addresses that went out, which name the plan.
        "raw_status": 202,  # The true status, never a success flag.
    }


def sample_record(upgrades: list[dict[str, Any]]) -> dict[str, Any]:
    """Build one run record that holds two upgrade plans and one stop request.

    Why:
        Two target versions make two groups, so `plan_upgrade` answers with two
        plans. A test can then prove that the seam pairs each stored row with
        the plan that sent it, and not with the plan at the same position.

    Args:
        upgrades: The stored rows of the accepted cloud calls.

    Returns:
        The run record.
    """
    return {  # The fields that the stop seam reads out of a run record.
        "run_id": RUN_ID,  # Names the run in each log line.
        "org_id": ORG_ID,  # The organization of the plan.
        "site_id": SITE_ID,  # The site that owns every device of the run.
        "state": "upgrading",  # A state that a stop can still change.
        "targets": [  # Two versions, so the plan holds two groups.
            {"mac": MAC_ONE, "device_type": "ap", "version_target": "0.14.29"},  # The first group.
            {"mac": MAC_TWO, "device_type": "ap", "version_target": "0.15.30"},  # The second group.
        ],
        "options": {},  # The default upgrade choices.
        "stop_request": stop_request_record(),  # The request that the outcome joins.
        "upgrades": upgrades,  # One row for each call that the cloud accepted.
    }


def arm_seam(monkeypatch: pytest.MonkeyPatch, store: MemoryRunStore, canceller: Any) -> None:
    """Point every read of the stop seam at a stand-in.

    Why:
        `cancel_run` reads the run store seam, the signed session, and the two
        cloud calls of the stop module. A test replaces all four, so the seam
        runs whole and still reaches no cloud.

    Args:
        monkeypatch: The pytest patch helper.
        store: The store that answers the run read and the outcome write.
        canceller: The stand-in for the cancel call of the cloud.
    """
    monkeypatch.setattr(wiring, "bound_store", lambda default: store)  # The store that the route reads.
    monkeypatch.setattr(wiring, "current_operator", lambda: SimpleNamespace(cloud_session=object()))
    monkeypatch.setattr(stop, "read_upgrade_status", lambda *args: {})  # No cloud read of the state.
    monkeypatch.setattr(stop, "cancel_upgrade", canceller)  # No cloud cancel call leaves this test.


def test_install_seams_fills_the_stop_runner() -> None:
    """A fresh application must hold the seam that cancels the devices of a run.

    Why:
        `routes/upgrade.cancel_outcome` reads `STOP_RUNNER`. An empty seam makes
        the route answer with three empty lists while every device keeps on
        upgrading, so the operator reads a stop that never happened.
    """
    app = factory.create_app()  # The factory calls `install_seams` inside `arm_application`.
    assert app.config.get(wiring.STOP_RUNNER_KEY) is wiring.cancel_run  # The one cancel worker.


def test_install_seams_keeps_an_injected_stop_runner() -> None:
    """A caller that already chose a stop runner must keep it.

    Why:
        Every contract test injects its own recording stop runner. A wiring that
        replaced it would drive those tests onto a live cloud.
    """
    app = factory.create_app()  # Already armed once, with the stop runner in place.
    app.config[wiring.STOP_RUNNER_KEY] = "the choice of the test"  # A caller sets its own value.
    wiring.install_seams(app)  # A second arm must change nothing.
    assert app.config[wiring.STOP_RUNNER_KEY] == "the choice of the test"  # `setdefault`, never a replacement.


def test_the_targets_carry_the_plan_and_the_identifier_and_the_family() -> None:
    """One stored row must build one target that holds all three values.

    Why:
        `StopTarget` needs the plan, the cloud identifier, and the family. The
        run record holds the identifier alone, so the pairing rebuilds the plan
        and reads the family out of the endpoint of that plan.
    """
    record = sample_record([upgrade_row(UPGRADE_ONE, (MAC_ONE,))])  # One accepted call of two plans.
    targets = wiring.stop_targets(stop, record)  # The pairing, with no cloud and no store.
    assert len(targets) == 1  # One row, so one cancel target.
    assert targets[0].upgrade_id == UPGRADE_ONE  # The identifier travels whole.
    assert stop.plan_macs(targets[0].plan) == (MAC_ONE,)  # The plan of that one device.
    assert targets[0].family is GatewayFamily.JUNOS  # An access point rides the site device call.


def test_the_pairing_reads_the_addresses_and_never_the_position() -> None:
    """A row of a later plan must reach the plan that sent it.

    Why:
        The cloud refuses a call now and then, so the run record may hold fewer
        rows than the run holds plans. A pair by position would then cancel the
        wrong plan and would name the wrong devices to the operator.
    """
    record = sample_record([upgrade_row(UPGRADE_TWO, (MAC_TWO,))])  # The cloud refused the first call.
    targets = wiring.stop_targets(stop, record)  # The first plan holds MAC_ONE, so position would fail.
    assert stop.plan_macs(targets[0].plan) == (MAC_TWO,)  # The second plan, which sent this row.


def test_the_seam_cancels_every_accepted_upgrade(monkeypatch: pytest.MonkeyPatch) -> None:
    """The seam must send one cancel call for each accepted upgrade call.

    Why:
        This is the whole repair. The operator asked to cancel the remaining
        devices, so every identifier that the cloud handed back must come back
        to the cloud on a cancel call.

    Args:
        monkeypatch: The pytest patch helper.
    """
    rows = [upgrade_row(UPGRADE_ONE, (MAC_ONE,)), upgrade_row(UPGRADE_TWO, (MAC_TWO,))]  # Two calls.
    recorder = CancelRecorder()  # Records the identifier and the addresses of each call.
    arm_seam(monkeypatch, MemoryRunStore(sample_record(rows)), recorder)  # No cloud, no store.
    outcome = wiring.cancel_run(RUN_ID)  # The call that `routes/upgrade.cancel_outcome` makes.
    assert dict(recorder.calls) == {UPGRADE_ONE: (MAC_ONE,), UPGRADE_TWO: (MAC_TWO,)}  # Right pairs.
    assert outcome.cancelled == (MAC_ONE, MAC_TWO)  # Both devices, named to the operator.


def test_the_stop_writes_the_outcome_onto_the_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """A finished stop must leave the outcome inside the run record.

    Why:
        FR-038h asks the portal to record every stop. A page reload and a poll
        both read the run record, so both must show the same three lists.

    Args:
        monkeypatch: The pytest patch helper.
    """
    store = MemoryRunStore(sample_record([upgrade_row(UPGRADE_ONE, (MAC_ONE,))]))  # One accepted call.
    arm_seam(monkeypatch, store, CancelRecorder())  # No cloud, no store, one clean cancel.
    wiring.cancel_run(RUN_ID)  # The call that `routes/upgrade.cancel_outcome` makes.
    assert store.record["stop_request"]["outcome"]["cancelled"] == [MAC_ONE]  # The record holds it.


def test_a_run_with_no_upgrade_row_cancels_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """A run that sent no accepted call must cancel nothing and claim nothing.

    Why:
        FR-038f forbids a claim of a cancel that never happened. The seam answers
        None here, and the route then keeps its own honest answer, which holds
        three empty lists.

    Args:
        monkeypatch: The pytest patch helper.
    """
    store = MemoryRunStore(sample_record([]))  # No call reached the cloud yet.
    recorder = CancelRecorder()  # This recorder must stay empty.
    arm_seam(monkeypatch, store, recorder)  # No cloud, no store.
    assert wiring.cancel_run(RUN_ID) is None  # The route then claims no cancelled device.
    assert recorder.calls == []  # No cancel call left the portal.
    assert store.writes == 0  # No outcome landed, because no stop happened.


def test_a_row_that_matches_no_plan_cancels_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """A stored row that names no plan of the run must reach no cancel call.

    Why:
        A cancel call needs the plan, because the plan carries the scope and the
        route. A guess at the plan could cancel a device that the operator never
        selected, so an unpaired row builds no target at all.

    Args:
        monkeypatch: The pytest patch helper.
    """
    store = MemoryRunStore(sample_record([upgrade_row(UPGRADE_ONE, (MAC_ABSENT,))]))  # No plan holds it.
    recorder = CancelRecorder()  # This recorder must stay empty.
    arm_seam(monkeypatch, store, recorder)  # No cloud, no store.
    assert wiring.cancel_run(RUN_ID) is None  # The route then claims no cancelled device.
    assert recorder.calls == []  # No cancel call left the portal.


def test_a_failed_cancel_never_becomes_a_claimed_cancel(monkeypatch: pytest.MonkeyPatch) -> None:
    """A cancel call that the cloud refused must claim no cancelled device.

    Why:
        FR-038f forbids a claim of a cancel that never happened. The device keeps
        on upgrading, so the operator must read that device in the group that
        continues, and never in the cancelled group.

    Args:
        monkeypatch: The pytest patch helper.
    """
    store = MemoryRunStore(sample_record([upgrade_row(UPGRADE_ONE, (MAC_ONE,))]))  # One accepted call.
    arm_seam(monkeypatch, store, refuse_cancel)  # The cloud refuses the cancel call.
    outcome = wiring.cancel_run(RUN_ID)  # The seam must survive the refusal.
    assert outcome.cancelled == ()  # No device stopped, so the portal claims none.
    assert outcome.already_writing == (MAC_ONE,)  # The device continues the upgrade.


def test_a_request_with_no_session_cancels_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """A request that holds no signed session must reach no cancel call.

    Why:
        A cancel call needs the token of the operator. A stop with no session
        sends nothing, so the portal must say that it cancelled nothing.

    Args:
        monkeypatch: The pytest patch helper.
    """
    store = MemoryRunStore(sample_record([upgrade_row(UPGRADE_ONE, (MAC_ONE,))]))  # One accepted call.
    recorder = CancelRecorder()  # This recorder must stay empty.
    arm_seam(monkeypatch, store, recorder)  # First the healthy stand-ins.
    monkeypatch.setattr(wiring, "current_operator", lambda: None)  # Then no signed session at all.
    assert wiring.cancel_run(RUN_ID) is None  # The route then claims no cancelled device.
    assert recorder.calls == []  # No cancel call left the portal.


def test_the_seam_answers_none_instead_of_raising(monkeypatch: pytest.MonkeyPatch) -> None:
    """A fault inside the stop must leave the seam answering None.

    Why:
        `routes/upgrade.cancel_outcome` guards this callable with nothing, so a
        fault that escaped would turn the stop of the operator into a 500 answer.
        A run with no stop request makes the outcome write raise.

    Args:
        monkeypatch: The pytest patch helper.
    """
    record = sample_record([upgrade_row(UPGRADE_ONE, (MAC_ONE,))])  # One accepted call.
    record.pop("stop_request")  # The outcome write then raises, because no request exists.
    arm_seam(monkeypatch, MemoryRunStore(record), CancelRecorder())  # No cloud, no store.
    assert wiring.cancel_run(RUN_ID) is None  # One warning line, and never a fault.


def test_the_family_of_a_router_plan_reads_the_router_call() -> None:
    """The family must follow the endpoint that the plan already holds.

    Why:
        `UpgradePlan` holds no family field, and the status read of the stop
        needs one. A session smart router always rides the organization call, so
        the endpoint names the family with no second source.
    """
    assert wiring.plan_family(SimpleNamespace(endpoint=ENDPOINT_ORG_SSRS)) is GatewayFamily.SSR  # A router.
    assert wiring.plan_family(SimpleNamespace(endpoint=ENDPOINT_SITE_DEVICES)) is GatewayFamily.JUNOS  # The rest.
