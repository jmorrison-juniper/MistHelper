"""Unit tests for the cloud submitter and the request readers of the wiring.

Why:
    Issue #1996 reports that ``app/wiring.py`` sits at 83 percent, under the 90
    percent floor that the aggregate hides. The audit of 2026-08-20 found defect
    11 and defect 12 in this same module. The uncovered half of a module is where
    a defect survives, and this module is the one that decides whether a firmware
    call leaves the portal at all.

    ``CloudUpgradeSubmitter`` is the sharpest example. `RunDriverDeps.submit`
    accepts None, and a driver built that way walks every phase and takes both
    captures while no firmware call ever leaves. Every refusal path of this class
    must therefore report one plain sentence rather than an exception, and no
    path may report success after the cloud refused.

    Issue #4020 changed the shape of this class. ``submit(record) -> bool`` sent
    every family of the site in one call, so a refused gateway group could not
    hold back the switch group that followed it. The class now answers
    ``submit_phase(record, phase) -> str | None``, which the driver calls once
    for each cascade phase, and a phase sends firmware only after the phase above
    it settled.

Warning:
    No test in this file reaches a cloud. Every test replaces ``load_module``,
    which is the one place where this module meets the upgrade seam.
"""

from __future__ import annotations

from threading import Event, Lock, Thread
from time import monotonic, sleep
from types import SimpleNamespace
from typing import Any

import pytest

from src.interfaces.portals.upgrade_portal.app import wiring
from src.interfaces.portals.upgrade_portal.runtime.signals import RunDispatchGate, StopRequestStore
from src.interfaces.portals.upgrade_portal.upgrade.driver import PHASE_ORDER

RUN_ID = "11111111-1111-1111-1111-111111111111"
UPGRADE_ID = "22222222-2222-2222-2222-222222222222"
MAC_SWITCH = "209339051780"

ACCEPTED_STATUS = (200, 202)
REFUSED_STATUS = 400

GATEWAY_PHASE = "gateways"
SWITCH_PHASE = "switches"
UNSUPPORTED_FAMILY = "camera"
STOP_REQUEST = {
    "requested_by": "sam@example.com",
    "requested_at": "2026-10-07T07:00:00+00:00",
    "confirmation_text": "STOP",
    "scope": "run",
}


class RecordingRunStore:
    """Persist submitter writes and optionally inject one durable stop request."""

    def __init__(
        self,
        record: dict[str, Any] | None = None,
        *,
        stop_after_first_row: bool = False,
        fail_writes: bool = False,
    ) -> None:
        """Hold the initial record and the scripted store behavior.

        Args:
            record: The durable run before the submitter starts.
            stop_after_first_row: Add a stop after the first accepted row lands.
            fail_writes: Refuse every persistence attempt.
        """
        self.record = dict(record) if record is not None else None
        self.stop_after_first_row = stop_after_first_row
        self.fail_writes = fail_writes
        self.writes: list[dict[str, Any]] = []

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one copy of the durable run.

        Args:
            run_id: The run key. This store holds one run only.

        Returns:
            A copy of the record, or None before the first write.
        """
        return dict(self.record) if self.record is not None else None

    def write_run(self, record: dict[str, Any]) -> bool:
        """Persist one record and inject the scripted concurrent stop.

        Args:
            record: The run record with one newly accepted row.

        Returns:
            False for a scripted store fault, or True after persistence.
        """
        if self.fail_writes:
            return False  # A destructive call with no durable row must stop the phase.
        self.record = dict(record)  # The accepted identifier becomes durable before another call.
        self.writes.append(dict(record))  # The test reads the exact sequence of durable rows.
        if self.stop_after_first_row and len(record.get("upgrades", ())) == 1:
            self.record["stop_request"] = dict(STOP_REQUEST)  # The route wins immediately after persistence.
        return True

    def append_accepted_upgrade(self, run_id: str, row: dict[str, Any]) -> bool:
        """Append one accepted row without changing another durable field.

        Args:
            run_id: The run key. This store holds one run only.
            row: The accepted cloud response.

        Returns:
            False for a scripted store fault, or True after persistence.
        """
        if self.fail_writes:
            return False  # A destructive call with no durable row must stop the phase.
        current = dict(self.record) if self.record is not None else {"run_id": run_id}  # Keep the durable fields.
        rows = list(current.get("upgrades", ()))  # Preserve the accepted groups of earlier phases.
        rows.append(dict(row))  # Add only the new cloud identifier.
        current["upgrades"] = rows  # Change no stop or state field.
        self.record = current  # Publish the narrow mutation.
        self.writes.append(dict(current))  # The test reads the exact sequence of durable rows.
        if self.stop_after_first_row and len(rows) == 1:
            self.record["stop_request"] = dict(STOP_REQUEST)  # The route wins immediately after persistence.
        return True

    def append_dispatch_failure(self, run_id: str, failure: dict[str, Any]) -> bool:
        """Append one refusal record and change no other field.

        Args:
            run_id: The run key. This store holds one run only.
            failure: The refusal evidence of one plan.

        Returns:
            True after the refusal becomes durable.
        """
        del run_id  # This store holds one run only.
        if self.record is None:
            return False  # An absent run cannot carry durable refusal evidence.
        current = dict(self.record)  # Preserve every accepted row and every stop field.
        rows = list(current.get("dispatch_failures", ()))  # Preserve every earlier refusal.
        rows.append(dict(failure))  # Add only the new refusal.
        current["dispatch_failures"] = rows  # Change no stop, state, or accepted row field.
        self.record = current  # Publish the narrow mutation.
        return True  # The refusal survives a concurrent stop write.

    def apply_state_transition(self, run_id: str, state: str, updated_at: str) -> bool:
        """Write only the state fields of one run.

        Args:
            run_id: The run key. This store holds one run only.
            state: The new run state value.
            updated_at: The fresh change time in ISO 8601 UTC.

        Returns:
            True after the move becomes durable.
        """
        del run_id  # This store holds one run only.
        if self.record is None:
            return False  # An absent run cannot hold a state.
        current = dict(self.record)  # Preserve every accepted row and every stop field.
        current["state"] = state  # Change only the state field.
        current["updated_at"] = updated_at  # The poll route reads the fresh change time.
        self.record = current  # Publish the narrow mutation.
        return True  # Every concurrent driver field survived the move.

    def apply_stop_request(self, run_id: str, stop_request: dict[str, Any], updated_at: str) -> bool:
        """Write only the stop fields and preserve every accepted row.

        Args:
            run_id: The run key. This store holds one run only.
            stop_request: The stop request record.
            updated_at: The fresh change time in ISO 8601 UTC.

        Returns:
            False when this store holds no run, or True after the narrow write.
        """
        if self.record is None:
            return False  # An absent run cannot carry a durable stop request.
        current = dict(self.record)  # Preserve the accepted rows of every earlier phase.
        current["stop_request"] = dict(stop_request)  # Change only the stop request field.
        current["updated_at"] = updated_at  # The poll route reads the fresh change time.
        self.record = current  # Publish the narrow mutation.
        return True  # The stop is durable beside every concurrent accepted row.


class PausingAcceptedRowStore(RecordingRunStore):
    """Pause one accepted-row mutation while the real stop path writes."""

    def __init__(self) -> None:
        """Start with one running record and two deterministic race signals."""
        super().__init__({"run_id": RUN_ID, "state": "upgrade_submitting", "upgrades": []})
        self.accepted_row_observed = Event()  # The test waits until persistence observed the old run.
        self.accepted_row_release = Event()  # The test releases persistence after the stop becomes durable.
        self.guard = Lock()  # The stop write and the accepted-row mutation share one store guard.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one guarded copy of the durable run."""
        del run_id  # This store holds one run only.
        with self.guard:  # A stop route can read while accepted-row persistence waits.
            return dict(self.record) if self.record is not None else None  # Return a detached record.

    def write_run(self, record: dict[str, Any]) -> bool:
        """Persist the whole record through the same guarded stop path."""
        with self.guard:  # The real stop store writes one complete record under this guard.
            self.record = dict(record)  # Detach the durable record from the stop route.
        return True  # The in-memory durable path accepted the stop request.

    def append_accepted_upgrade(self, run_id: str, row: dict[str, Any]) -> bool:
        """Append one row after a concurrent stop commits."""
        del run_id  # This store holds one run only.
        with self.guard:  # Observe the old record before the stop route writes.
            observed = dict(self.record) if self.record is not None else None  # Preserve the stale snapshot.
        self.accepted_row_observed.set()  # Let the test write the stop in the vulnerable interval.
        if not self.accepted_row_release.wait(timeout=2):  # A missing release must fail the test quickly.
            return False  # Do not claim that the accepted row became durable.
        with self.guard:  # Mutate the current record, not the stale observed snapshot.
            current = dict(self.record) if self.record is not None else observed  # Keep the concurrent stop.
            if current is None:
                return False  # An absent run cannot hold the accepted identifier.
            rows = list(current.get("upgrades", ()))  # Preserve each earlier accepted group.
            rows.append(dict(row))  # Add only the new accepted group.
            current["upgrades"] = rows  # Change no other durable field.
            self.record = current  # Publish the narrow mutation after the stop write.
        return True  # Both the stop and the accepted row are now durable.


def submitter(store: RecordingRunStore | None = None) -> wiring.CloudUpgradeSubmitter:
    """Return the cloud submitter with a durable run store.

    Args:
        store: The scripted store, or None for a healthy empty store.

    Returns:
        The submitter under test.
    """
    return wiring.CloudUpgradeSubmitter(object(), store or RecordingRunStore())


def answer(status: int = 200, upgrade_id: str = UPGRADE_ID) -> Any:
    """Return one stand-in for the submission record of the upgrade seam.

    Args:
        status: The HTTP status that the cloud answered.
        upgrade_id: The cloud identifier of the call.

    Returns:
        One record with the four fields that `_submission_row` reads.
    """
    return SimpleNamespace(upgrade_id=upgrade_id, scope="site", accepted=(MAC_SWITCH,), raw_status=status)


def plan_for(device_type: str) -> Any:
    """Return one stand-in upgrade plan of one device family.

    Args:
        device_type: The family the plan holds, for example ``gateway``.

    Returns:
        One object with the ``targets`` attribute that `plan_phase` reads.
    """
    return SimpleNamespace(targets=(SimpleNamespace(device_type=device_type),))


def walk_phases(submitter: Any, record: dict[str, Any]) -> list[str]:
    """Drive one submitter the way the cascade drives it and name each phase.

    Why:
        The driver sends one phase, settles it, and only then sends the next
        phase. This helper repeats that loop with no gate and no cloud, so a
        test can read which phases reached the submitter before the run stopped.

    Args:
        submitter: The submitter under test.
        record: The run record.

    Returns:
        The phase names that reached the submitter, in the order of the cascade.
    """
    seen: list[str] = []  # The phases the cascade handed to the submitter.
    for phase in PHASE_ORDER:  # The driver walks this same fixed order.
        seen.append(phase)
        if submitter.submit_phase(record, phase) is not None:  # A sentence stops the run at once.
            break  # Issue #4020: no later family may receive a destructive write.
    return seen


def service_that(invoke: Any) -> Any:
    """Return a stand-in upgrade seam module.

    Args:
        invoke: The callable that stands in for ``invoke_upgrade``.

    Returns:
        One module-like object with the two names the wiring reads.
    """
    return SimpleNamespace(invoke_upgrade=invoke, ACCEPTED_STATUS=ACCEPTED_STATUS)


def install_modules(monkeypatch: pytest.MonkeyPatch, table: dict[str, Any]) -> None:
    """Replace the module loader of the wiring with a fixed table.

    Args:
        monkeypatch: The pytest patch helper.
        table: The module to answer for each module name.
    """
    monkeypatch.setattr(wiring, "load_module", table.get)


class TestTheSubmitterRefuses:
    """Tests for every path where no firmware call may leave the portal."""

    def test_reports_a_reason_when_the_run_builds_no_plan(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A run with no plan never reads as a sent upgrade.

        Why:
            A silent success here would carry the run into the settle phases and
            both captures while no firmware call ever left. The driver must fail
            the run instead.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(wiring, "build_plans", lambda record: ())
        record: dict[str, Any] = {"run_id": RUN_ID}
        assert submitter().submit_phase(record, GATEWAY_PHASE) == wiring.NO_PLAN_REASON

    def test_reports_a_reason_when_the_upgrade_seam_is_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A host with no upgrade seam sends nothing and says so.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("gateway"),))
        install_modules(monkeypatch, {})
        record: dict[str, Any] = {"run_id": RUN_ID}
        reason = submitter().submit_phase(record, GATEWAY_PHASE)
        assert reason == wiring.PHASE_REFUSED_REASON.format(phase=GATEWAY_PHASE)
        assert record["upgrades"] == []

    def test_reports_a_reason_when_the_cloud_call_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A cloud fault ends the phase and never reads as an accepted write.

        Args:
            monkeypatch: The pytest patch helper.
        """

        def explode(session: Any, plan: Any) -> Any:
            """Raise the way a timed out cloud call does.

            Args:
                session: The cloud session.
                plan: The plan to send.

            Raises:
                RuntimeError: Always.
            """
            raise RuntimeError("the cloud did not answer")

        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("gateway"),))
        install_modules(monkeypatch, {wiring.SERVICE_MODULE: service_that(explode)})
        record: dict[str, Any] = {"run_id": RUN_ID}
        reason = submitter().submit_phase(record, GATEWAY_PHASE)
        assert reason == wiring.PHASE_REFUSED_REASON.format(phase=GATEWAY_PHASE)
        assert record["upgrades"] == []

    def test_reports_a_reason_when_the_cloud_refuses(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A refused status never reads as an accepted call.

        Why:
            The seam never raises for a cloud error status. It records the true
            status instead, so this module owns the decision. A refused group
            carries no identifier that the stop path could use.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("gateway"),))
        install_modules(
            monkeypatch,
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: answer(REFUSED_STATUS))},
        )
        record: dict[str, Any] = {"run_id": RUN_ID}
        reason = submitter().submit_phase(record, GATEWAY_PHASE)
        assert reason == wiring.PHASE_REFUSED_REASON.format(phase=GATEWAY_PHASE)
        assert record["upgrades"] == []

    def test_reports_a_reason_for_an_unroutable_plan_without_a_cloud_write(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An unknown device family fails before one destructive write.

        Args:
            monkeypatch: The pytest patch helper.
        """
        sent: list[Any] = []  # An entry would prove that validation happened after a cloud write.
        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for(UNSUPPORTED_FAMILY),))
        install_modules(
            monkeypatch,
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: sent.append(plan) or answer())},
        )
        record: dict[str, Any] = {"run_id": RUN_ID}
        reason = submitter().submit_phase(record, GATEWAY_PHASE)
        assert reason == wiring.UNROUTABLE_PLAN_REASON  # The operator gets one visible validation reason.
        assert sent == []  # No plan reaches the cloud when any plan has no supported phase.

    def test_reports_a_reason_for_an_empty_plan_without_a_cloud_write(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A plan with no target fails before one destructive write.

        Args:
            monkeypatch: The pytest patch helper.
        """
        sent: list[Any] = []  # An empty group has no safe cascade phase.
        empty = SimpleNamespace(targets=())  # This is a plan object, not the separate no-plan case.
        monkeypatch.setattr(wiring, "build_plans", lambda record: (empty,))
        install_modules(
            monkeypatch,
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: sent.append(plan) or answer())},
        )
        record: dict[str, Any] = {"run_id": RUN_ID}
        reason = submitter().submit_phase(record, GATEWAY_PHASE)
        assert reason == wiring.UNROUTABLE_PLAN_REASON  # Empty plans fail visibly instead of disappearing.
        assert sent == []  # Validation happens before the upgrade seam loads.

    def test_reports_a_reason_for_a_mixed_family_plan_without_a_cloud_write(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """One plan that mixes two families fails before one destructive write.

        Args:
            monkeypatch: The pytest patch helper.
        """
        sent: list[Any] = []  # A mixed plan must not borrow the phase of its first target.
        targets = (SimpleNamespace(device_type="gateway"), SimpleNamespace(device_type="switch"))
        mixed = SimpleNamespace(targets=targets)  # The upgrade seam must never build this shape.
        monkeypatch.setattr(wiring, "build_plans", lambda record: (mixed,))
        install_modules(
            monkeypatch,
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: sent.append(plan) or answer())},
        )
        record: dict[str, Any] = {"run_id": RUN_ID}
        reason = submitter().submit_phase(record, GATEWAY_PHASE)
        assert reason == wiring.UNROUTABLE_PLAN_REASON  # Mixed families have no single safe cascade phase.
        assert sent == []  # The invalid group is never silently omitted and never sent.


class TestTheSubmitterSends:
    """Tests for the paths where the cloud accepted at least one call."""

    def test_reports_none_and_keeps_the_cloud_identifier(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An accepted call writes the row that the stop path reads.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("gateway"),))
        install_modules(
            monkeypatch,
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: answer())},
        )
        record: dict[str, Any] = {"run_id": RUN_ID}
        assert submitter().submit_phase(record, GATEWAY_PHASE) is None
        assert record["upgrades"] == [
            {"upgrade_id": UPGRADE_ID, "scope": "site", "accepted": [MAC_SWITCH], "raw_status": 200}
        ]

    def test_a_phase_with_no_plan_sends_nothing_and_stops_no_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A site that holds no gateway reaches the cloud for no gateway.

        Why:
            FR-058 skips an absent family. The submitter must therefore answer
            None without one cloud call, so the driver marks the phase skipped
            and opens the next gate.

        Args:
            monkeypatch: The pytest patch helper.
        """
        sent: list[Any] = []  # Any entry here would be a firmware call for a family the site does not hold.
        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("switch"),))
        install_modules(
            monkeypatch,
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: sent.append(plan) or answer())},
        )
        record: dict[str, Any] = {"run_id": RUN_ID}
        assert submitter().submit_phase(record, GATEWAY_PHASE) is None
        assert sent == []

    def test_a_refused_gateway_group_sends_no_switch_firmware(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Issue #4020: a refused family holds the firmware of every later family.

        Why:
            This test replaces ``test_keeps_the_group_that_worked_when_another
            _group_fails``, which asserted the defect. That test accepted one
            refused group followed by one accepted group and reported success,
            because the old ``submit`` sent every family of the site in one
            comprehension. Measured against that code, this same selection
            produced ``calls == ["gateways", "switches"]`` with a true result.
            The switch firmware therefore left the portal while the gateways of
            the site had taken none, which is the outage this issue repairs.

            The replacement is deliberate. The old assertion cannot hold beside
            the new one, because the two describe opposite behavior.

        Args:
            monkeypatch: The pytest patch helper.
        """
        plans = (plan_for("gateway"), plan_for("switch"))  # One family for each of the first two phases.
        calls: list[str] = []  # Records the family of every plan that reached the cloud seam.

        def send(session: Any, plan: Any) -> Any:
            """Answer one cloud call and record the family it carried.

            Args:
                session: The cloud session.
                plan: The plan the submitter sent.

            Returns:
                A refused answer for the gateways, and an accepted answer for
                every other family.
            """
            phase = wiring.plan_phase(plan)
            calls.append(phase)
            return answer(REFUSED_STATUS) if phase == GATEWAY_PHASE else answer()

        monkeypatch.setattr(wiring, "build_plans", lambda record: plans)
        install_modules(monkeypatch, {wiring.SERVICE_MODULE: service_that(send)})
        record: dict[str, Any] = {"run_id": RUN_ID}
        seen = walk_phases(submitter(), record)
        assert calls == ["gateways"]  # The switch firmware never left the portal.
        assert seen == ["gateways"]  # The cascade stopped before the switch phase.
        assert record["upgrades"] == []  # A refused group leaves no identifier for the stop path.

    def test_an_accepted_gateway_phase_keeps_its_rows_when_the_switches_fail(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A later refusal never drops the identifiers of the family above it.

        Why:
            The gateways are already writing firmware when the switch call is
            refused. The stop path needs the gateway upgrade identifier to
            cancel that work, so the record must keep it.

        Args:
            monkeypatch: The pytest patch helper.
        """
        plans = (plan_for("gateway"), plan_for("switch"))

        def send(session: Any, plan: Any) -> Any:
            """Accept the gateway call and refuse the switch call.

            Args:
                session: The cloud session.
                plan: The plan the submitter sent.

            Returns:
                The cloud answer for this family.
            """
            return answer() if wiring.plan_phase(plan) == GATEWAY_PHASE else answer(REFUSED_STATUS)

        monkeypatch.setattr(wiring, "build_plans", lambda record: plans)
        install_modules(monkeypatch, {wiring.SERVICE_MODULE: service_that(send)})
        record: dict[str, Any] = {"run_id": RUN_ID}
        seen = walk_phases(submitter(), record)
        assert seen == ["gateways", "switches"]  # The gateways settled, so the switches tried.
        assert len(record["upgrades"]) == 1  # The accepted gateway row survived the switch refusal.

    def test_accepts_the_second_accepted_status(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The cloud may answer 202, and the seam names both codes.

        Args:
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("switch"),))
        install_modules(
            monkeypatch,
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: answer(202))},
        )
        assert submitter().submit_phase({"run_id": RUN_ID}, SWITCH_PHASE) is None

    def test_a_stop_after_the_first_version_group_blocks_the_second_group(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A durable stop between version groups blocks the second cloud write.

        Args:
            monkeypatch: The pytest patch helper.
        """
        plans = (plan_for("switch"), plan_for("switch"))  # Two versions of one family share one phase.
        calls: list[Any] = []  # Only the first plan may reach the destructive seam.
        store = RecordingRunStore(stop_after_first_row=True)  # The route stops after row one becomes durable.
        monkeypatch.setattr(wiring, "build_plans", lambda record: plans)
        install_modules(
            monkeypatch,
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: calls.append(plan) or answer())},
        )
        record: dict[str, Any] = {"run_id": RUN_ID}
        reason = submitter(store).submit_phase(record, SWITCH_PHASE)
        assert reason == wiring.STOP_REQUESTED_REASON  # A stop is not an ordinary cloud refusal.
        assert len(calls) == 1  # The second version group receives no firmware write.
        assert len(store.record["upgrades"]) == 1  # The accepted row is durable for cancellation and evidence.
        assert store.record["stop_request"] == STOP_REQUEST  # The concurrent route request survives persistence.

    def test_a_stop_during_accepted_row_persistence_survives_the_narrow_mutation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A stop raised during accepted-row persistence waits and then blocks the next call.

        Why:
            Issue #4020: the stop write and the accepted-row write once raced in
            the store. ``RunDispatchGate`` now makes the stop check, the cloud
            call, and the durable row one action. The stop therefore cannot
            commit inside persistence at all. It waits for the gate, and it
            takes the gate before the second version group may dispatch.

        Args:
            monkeypatch: The pytest patch helper.
        """
        plans = (plan_for("switch"), plan_for("switch"))  # The second version exposes a lost-stop defect.
        calls: list[Any] = []  # A preserved stop must block the second destructive call.
        store = PausingAcceptedRowStore()  # The store pauses in the former stale-write interval.
        monkeypatch.setattr(wiring, "build_plans", lambda record: plans)
        install_modules(
            monkeypatch,
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: calls.append(plan) or answer())},
        )
        record: dict[str, Any] = {"run_id": RUN_ID}
        result: dict[str, str | None] = {}  # The worker publishes the visible stop reason.

        def send_phase() -> None:
            """Run the destructive phase while the store controls the race."""
            result["reason"] = submitter(store).submit_phase(record, SWITCH_PHASE)  # Use the production submitter.

        def request_stop() -> None:
            """Ask for the durable stop through the real route path."""
            StopRequestStore(store).request(RUN_ID, "sam@example.com", "STOP")  # The gate holds this call.

        worker = Thread(target=send_phase, name="accepted-row-worker")  # Keep the phase off the test thread.
        worker.start()  # The first cloud response reaches accepted-row persistence.
        assert store.accepted_row_observed.wait(timeout=2)  # Persistence observed the record without a stop.
        stopper = Thread(target=request_stop, name="stop-route")  # The route thread now asks for the stop.
        stopper.start()  # The stop blocks on the gate that the first dispatch holds.
        deadline = monotonic() + 2  # Bound the wait, so a defect fails the test instead of hanging it.
        while RunDispatchGate.stops_waiting(RUN_ID) == 0 and monotonic() < deadline:  # Wait for the claim.
            sleep(0.01)  # Yield to the stop route thread, which registers its claim on the gate.
        assert RunDispatchGate.stops_waiting(RUN_ID) == 1  # The stop claimed the gate before the release.
        assert store.record.get("stop_request") is None  # The gate held the stop out of persistence.
        store.accepted_row_release.set()  # Let accepted-row persistence continue and release the gate.
        stopper.join(timeout=2)  # The stop commits as soon as the first dispatch finished.
        worker.join(timeout=2)  # The preserved stop must end the phase without a wait.
        assert worker.is_alive() is False  # The deterministic race completed.
        assert stopper.is_alive() is False  # The stop route never hangs on the gate.
        assert result["reason"] == wiring.STOP_REQUESTED_REASON  # The driver selects stopped finalization.
        assert len(calls) == 1  # The second version group receives no firmware write.
        assert len(store.record["upgrades"]) == 1  # The accepted row remains durable for cancellation.
        assert store.record["stop_request"]["requested_by"] == "sam@example.com"  # The stop was not erased.

    def test_a_stop_before_the_first_version_group_sends_nothing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A durable stop before the phase blocks its first cloud write.

        Args:
            monkeypatch: The pytest patch helper.
        """
        calls: list[Any] = []  # A preexisting stop must keep this collection empty.
        store = RecordingRunStore({"run_id": RUN_ID, "stop_request": dict(STOP_REQUEST)})
        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("switch"), plan_for("switch")))
        install_modules(
            monkeypatch,
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: calls.append(plan) or answer())},
        )
        record: dict[str, Any] = {"run_id": RUN_ID}
        reason = submitter(store).submit_phase(record, SWITCH_PHASE)
        assert reason == wiring.STOP_REQUESTED_REASON  # The direct caller can distinguish a stop from refusal.
        assert calls == []  # No firmware leaves after an operator already asked to stop.
        assert record["stop_request"] == STOP_REQUEST  # The driver receives the durable request in its copy.

    def test_a_lost_accepted_row_stops_before_the_second_version_group(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A store fault after one accepted call blocks every later call.

        Args:
            monkeypatch: The pytest patch helper.
        """
        calls: list[Any] = []  # Only the accepted call whose row failed to persist may leave.
        store = RecordingRunStore(fail_writes=True)  # Cancellation cannot find a row this store refused.
        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("switch"), plan_for("switch")))
        install_modules(
            monkeypatch,
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: calls.append(plan) or answer())},
        )
        record: dict[str, Any] = {"run_id": RUN_ID}
        reason = submitter(store).submit_phase(record, SWITCH_PHASE)
        assert reason == wiring.ACCEPTED_ROW_STORE_REASON  # The persistence loss is visible and terminal.
        assert len(calls) == 1  # No second destructive write starts without a durable first identifier.
        assert len(record["upgrades"]) == 1  # The driver still holds the row for evidence in this process.


class TestBoundStore:
    """Tests for the reader that keeps one run store for the whole run."""

    def test_answers_the_default_with_no_route_module(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No route module means no seam, so the default store stands.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_modules(monkeypatch, {})
        default = object()
        assert wiring.bound_store(default) is default  # type: ignore[arg-type]

    def test_answers_the_default_when_the_seam_read_fails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A seam that needs an application answers None outside a request.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_modules(monkeypatch, {wiring.UPGRADE_ROUTES: SimpleNamespace(run_store=lambda: None)})
        monkeypatch.setattr(wiring, "read_safely", lambda read, subject: None)
        default = object()
        assert wiring.bound_store(default) is default  # type: ignore[arg-type]

    def test_answers_the_seam_store_when_one_exists(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An injected store wins, so the driver writes where the poll reads.

        Why:
            A driver that held a second store would write where the poll route
            never reads, and the run would look frozen on the progress page.

        Args:
            monkeypatch: The pytest patch helper.
        """
        injected = object()
        install_modules(monkeypatch, {wiring.UPGRADE_ROUTES: SimpleNamespace(run_store=lambda: injected)})
        monkeypatch.setattr(wiring, "read_safely", lambda read, subject: injected)
        assert wiring.bound_store(object()) is injected  # type: ignore[arg-type]


class TestCurrentOperator:
    """Tests for the one accessor of the signed session."""

    def test_answers_none_with_no_identity_module(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A host with no identity module reports an absent operator.

        Args:
            monkeypatch: The pytest patch helper.
        """
        install_modules(monkeypatch, {})
        assert wiring.current_operator() is None

    def test_answers_the_record_of_the_present_request(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The accessor returns what the identity module holds.

        Args:
            monkeypatch: The pytest patch helper.
        """
        record = SimpleNamespace(cloud_session=object())
        install_modules(monkeypatch, {wiring.IDENTITY_MODULE: SimpleNamespace(current_session=lambda: record)})
        monkeypatch.setattr(wiring, "read_safely", lambda read, subject: read())
        assert wiring.current_operator() is record


class TestTheStorageBootstrapRunsOnce:
    """Tests for the guard that keeps the bootstrap to one run for each process.

    Why:
        A contract test builds one application for each test, and every
        application called the bootstrap. Each call reached
        ``DatabaseConfig.from_env``, which resolves the database host and the
        lock store host to decide the standalone mode. On a runner where the host
        name does not resolve quickly, each call took about 20 seconds, and the
        whole test job reached its 15 minute limit and reported as a test
        failure. Issue #2036 holds that record.

        Every step of the bootstrap repeats without harm, so one run for each
        process is enough.
    """

    def test_calls_the_store_one_time_for_many_applications(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Five calls reach the capture store one time.

        Args:
            monkeypatch: The pytest patch helper.
        """
        wiring.reset_storage_bootstrap()
        seen: list[str] = []
        store = SimpleNamespace(bootstrap_storage=lambda: seen.append("run") or "report")
        install_modules(monkeypatch, {wiring.CAPTURE_STORE_MODULE: store})
        for _ in range(5):  # Five applications, as a contract file builds.
            wiring.prepare_storage()
        assert len(seen) == 1

    def test_a_reset_lets_the_next_application_build_again(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A worker that meets a database restart can clear the guard.

        Args:
            monkeypatch: The pytest patch helper.
        """
        wiring.reset_storage_bootstrap()
        seen: list[str] = []
        store = SimpleNamespace(bootstrap_storage=lambda: seen.append("run") or "report")
        install_modules(monkeypatch, {wiring.CAPTURE_STORE_MODULE: store})
        wiring.prepare_storage()
        wiring.reset_storage_bootstrap()
        wiring.prepare_storage()
        assert len(seen) == 2

    def test_a_failed_bootstrap_never_retries_on_every_application(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A store that raises still costs one call and not one for each application.

        Why:
            The guard is set before the call, so a raise leaves no retry loop.
            A store that is out of reach is the exact case that made the runner
            stall, so the guard must hold for it above every other case.

        Args:
            monkeypatch: The pytest patch helper.
        """
        wiring.reset_storage_bootstrap()
        seen: list[str] = []

        def explode() -> Any:
            """Raise the way an unreachable store does.

            Returns:
                Never returns.

            Raises:
                RuntimeError: Always.
            """
            seen.append("run")
            raise RuntimeError("the document store is out of reach")

        install_modules(monkeypatch, {wiring.CAPTURE_STORE_MODULE: SimpleNamespace(bootstrap_storage=explode)})
        for _ in range(4):
            wiring.prepare_storage()
        assert len(seen) == 1

    def test_an_absent_store_still_leaves_a_portal_that_reads(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A host with no capture store builds an application and raises nothing.

        Args:
            monkeypatch: The pytest patch helper.
        """
        wiring.reset_storage_bootstrap()
        install_modules(monkeypatch, {})
        wiring.prepare_storage()  # Raises nothing, which is the whole assertion.
        assert wiring._STORAGE_PREPARED is True  # WHY: prove the absent store still completed setup.
        wiring.reset_storage_bootstrap()
