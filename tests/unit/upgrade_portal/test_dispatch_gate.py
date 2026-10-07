"""Tests for the two inverse firmware stop races of issue #4020.

Why:
    The accepted-row append became one narrow atomic mutation, so a firmware
    write can no longer erase a concurrent stop. The final review of that repair
    found the two inverse orders that the narrow append does not cover.

    The first inverse race lives in ``StopRequestStore.request``. It read one
    whole run record, merged the stop into that local copy, and then wrote the
    whole copy back. An accepted row that committed between the read and the
    write disappeared, and the same stale write could erase ``state``, ``phase``,
    the outcome, and the post-check evidence.

    The second inverse race lives at the seam between the durable stop check and
    the cloud call. The submitter read the stop and then sent firmware as two
    separate actions, so a stop that committed between them could not stop the
    destructive call that followed it.

Warning:
    No test in this file reaches a cloud or a database. Every cloud call is one
    local callable, and every store is either the production in-memory store or
    one scripted double.
"""

from __future__ import annotations

from threading import Event, Lock, RLock, Thread
from time import sleep
from types import SimpleNamespace
from typing import Any, cast

import pytest

from src.interfaces.portals.upgrade_portal.app import wiring
from src.interfaces.portals.upgrade_portal.app.routes import upgrade
from src.interfaces.portals.upgrade_portal.runtime.signals import (
    RunDispatchGate,
    StopRequestStore,
)

RUN_ID = "44444444-4444-4444-4444-444444444444"
UPGRADE_ID = "55555555-5555-5555-5555-555555555555"
MAC_SWITCH = "209339051780"
ACCEPTED_STATUS = (200, 202)
OPERATOR = "sam@example.com"
WAIT_SECONDS = 2.0  # A missing deterministic signal must fail the test, never hang the suite.


def running_record() -> dict[str, Any]:
    """Return one nonfinal run record that a stop may still change.

    Returns:
        The durable record shape that the stop store and the submitter read.
    """
    return {"run_id": RUN_ID, "state": "upgrade_submitting", "upgrades": []}


def accepted_row(upgrade_id: str = UPGRADE_ID) -> dict[str, Any]:
    """Return one accepted cloud response row.

    Args:
        upgrade_id: The cloud identifier of the accepted call.

    Returns:
        The plain row that the store persists.
    """
    return {"upgrade_id": upgrade_id, "scope": "site", "accepted": [MAC_SWITCH]}


def plan_for(device_type: str) -> Any:
    """Return one stand-in upgrade plan of one device family.

    Args:
        device_type: The family the plan holds, for example ``switch``.

    Returns:
        One object with the ``targets`` attribute that `plan_phase` reads.
    """
    return SimpleNamespace(targets=(SimpleNamespace(device_type=device_type),))


def answer(upgrade_id: str = UPGRADE_ID) -> Any:
    """Return one accepted stand-in submission record of the upgrade seam.

    Args:
        upgrade_id: The cloud identifier of the call.

    Returns:
        One record with the four fields that `_submission_row` reads.
    """
    return SimpleNamespace(upgrade_id=upgrade_id, scope="site", accepted=(MAC_SWITCH,), raw_status=200)


class NarrowRunStore:
    """Hold one run and change only the field that each mutation names.

    Why:
        The production stores both mutate one field at a time. This double keeps
        that contract under one guard, so a test can prove the ordering of two
        concurrent narrow mutations without a database.
    """

    def __init__(self) -> None:
        """Start with one nonfinal run and no durable stop."""
        self.record: dict[str, Any] = running_record()  # The durable record every caller reads.
        self.guard = Lock()  # One guard serializes every narrow mutation of this store.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one detached copy of the durable run.

        Args:
            run_id: The run key. This store holds one run only.

        Returns:
            A copy of the record.
        """
        del run_id  # This store holds one run only.
        with self.guard:  # A concurrent mutation must never publish a half-written record.
            return dict(self.record)  # A copy stops a caller edit of the stored record.

    def write_run(self, run: dict[str, Any]) -> bool:
        """Write one whole run record.

        Args:
            run: The whole record, with the changed fields already in place.

        Returns:
            True, because this double always accepts a write.
        """
        with self.guard:  # The whole-record write shares the guard with every narrow mutation.
            self.record = dict(run)  # Detach the durable record from the caller.
        return True  # The in-memory durable path accepted the record.

    def append_accepted_upgrade(self, run_id: str, row: dict[str, Any]) -> bool:
        """Append one accepted row and change no other field.

        Args:
            run_id: The run key. This store holds one run only.
            row: The accepted cloud response.

        Returns:
            True after the row becomes durable.
        """
        del run_id  # This store holds one run only.
        with self.guard:  # The append and a concurrent stop mutation cannot interleave.
            rows = list(self.record.get("upgrades", ()))  # Preserve every earlier accepted group.
            rows.append(dict(row))  # Add only the new cloud identifier.
            self.record["upgrades"] = rows  # Change no stop, state, or post-check field.
        return True  # The accepted identifier is durable before another cloud write.

    def append_dispatch_failure(self, run_id: str, failure: dict[str, Any]) -> bool:
        """Append one refusal record and change no other field.

        Args:
            run_id: The run key. This store holds one run only.
            failure: The refusal evidence of one plan.

        Returns:
            True after the refusal becomes durable.
        """
        del run_id  # This store holds one run only.
        with self.guard:  # The append and a concurrent stop mutation cannot interleave.
            rows = list(self.record.get("dispatch_failures", ()))  # Preserve every earlier refusal.
            rows.append(dict(failure))  # Add only the new refusal.
            self.record["dispatch_failures"] = rows  # Change no stop, state, or accepted row field.
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
        with self.guard:  # The move and a concurrent append cannot interleave.
            self.record["state"] = state  # Change only the state field.
            self.record["updated_at"] = updated_at  # The poll route reads the fresh change time.
        return True  # Every concurrent driver field survived the move.

    def apply_stop_request(self, run_id: str, stop_request: dict[str, Any], updated_at: str) -> bool:
        """Write only the stop fields of one run.

        Args:
            run_id: The run key. This store holds one run only.
            stop_request: The stop request record.
            updated_at: The fresh change time.

        Returns:
            True after the stop becomes durable.
        """
        del run_id  # This store holds one run only.
        with self.guard:  # The stop mutation and a concurrent append cannot interleave.
            self.record["stop_request"] = dict(stop_request)  # Change only the stop request field.
            self.record["updated_at"] = updated_at  # The data model asks for a fresh change time.
        return True  # The stop is durable and every other field survived.


class PausingStopStore(NarrowRunStore):
    """Pause the stop request after its record read, the old unsafe point."""

    def __init__(self) -> None:
        """Start with one running record and two deterministic race signals."""
        super().__init__()  # Reuse the narrow mutation contract of the production stores.
        self.stop_read = Event()  # The test waits until the stop observed the old record.
        self.stop_release = Event()  # The test releases the stop after the accepted row lands.
        self.pause_next_read = False  # Only the stop request read of the test pauses.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one copy and pause inside the vulnerable interval.

        Args:
            run_id: The run key. This store holds one run only.

        Returns:
            A copy of the record as the caller observed it.
        """
        observed = super().read_run(run_id)  # Observe the record exactly where the old code observed it.
        if self.pause_next_read:  # Pause one read only, so the stop guard read runs at full speed.
            self.pause_next_read = False  # Never pause a later read of the same test.
            self.stop_read.set()  # Let the test commit the accepted row in this interval.
            self.stop_release.wait(timeout=WAIT_SECONDS)  # Release after the concurrent row is durable.
        return observed  # The caller continues with the record it read before the append.


def service_that(invoke: Any) -> Any:
    """Return a stand-in upgrade seam module.

    Args:
        invoke: The callable that stands in for ``invoke_upgrade``.

    Returns:
        One module-like object with the two names the wiring reads.
    """
    return SimpleNamespace(invoke_upgrade=invoke, ACCEPTED_STATUS=ACCEPTED_STATUS)


class TestTheNarrowStopMutation:
    """Tests that prove one stop write changes only the stop fields."""

    def test_memory_run_store_applies_a_stop_without_erasing_accepted_rows(self) -> None:
        """The guarded memory mutation preserves every field outside the stop."""
        store = upgrade.MemoryRunStore()  # Use the production in-memory lock.
        run_id = "stop-memory-row"  # Keep this test record separate from route records.
        row = accepted_row()  # Model the firmware call that the cloud already accepted.
        initial = {"run_id": run_id, "state": "upgrade_submitting", "upgrades": [row], "phase": "switches"}
        assert store.write_run(initial) is True  # Seed the current durable record.
        stop = {"requested_by": OPERATOR, "confirmation_text": "STOP"}  # Model the route stop record.
        assert store.apply_stop_request(run_id, stop, "2026-10-07T08:00:00+00:00") is True  # Change stop only.
        stored = store.read_run(run_id)  # Read the complete record after the narrow mutation.
        assert stored["stop_request"] == stop  # The stop reached the durable record.
        assert stored["upgrades"] == [row]  # The stop write cannot erase cancellation evidence.
        assert stored["phase"] == "switches"  # The stop write cannot erase the phase field.
        assert stored["state"] == "upgrade_submitting"  # The state machine still owns the state field.

    def test_memory_run_store_refuses_a_stop_for_an_absent_run(self) -> None:
        """An absent run can hold no stop, so the mutation fails closed."""
        store = upgrade.MemoryRunStore()  # Use the production in-memory lock.
        assert store.apply_stop_request("no-such-run", {}, "2026-10-07T08:00:00+00:00") is False  # Fail closed.

    def test_document_run_store_applies_a_stop_with_one_field_update(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The document mutation patches the stop fields and replaces no record."""
        stored = {"run_id": "run-a", "_key": "run-a", "upgrades": [accepted_row()]}  # The durable document.
        aql = SimpleNamespace(calls=[])  # Record the one atomic statement that the store runs.

        def execute(query: str, *, bind_vars: dict[str, Any]) -> list[dict[str, Any]]:
            """Record and answer one query."""
            aql.calls.append((query, bind_vars))  # Preserve the exact atomic statement.
            return [stored]  # Return the atomically updated document.

        aql.execute = execute  # Publish the recorder as the database query seam.
        module = SimpleNamespace(  # Supply the production module fields used by the store.
            RUN_COLLECTION="upgrade_runs",  # Bind the real collection name.
            connect_database=lambda: SimpleNamespace(aql=aql),  # Return an online database.
        )
        monkeypatch.setattr(wiring, "load_module", lambda name: module)  # Keep the test offline.
        store = wiring.DocumentRunStore()  # Use the production document mutation.
        stop = {"requested_by": OPERATOR, "confirmation_text": "STOP"}  # Model the route stop record.
        assert store.apply_stop_request("run-a", stop, "2026-10-07T08:00:00+00:00") is True  # Patch the stop.
        query, bind_vars = aql.calls[0]  # Inspect the one database action.
        assert "UPDATE run WITH" in query  # Patch the stored document instead of replacing it.
        assert "stop_request:" in query  # Change the stop request field.
        assert "REPLACE run" not in query  # A stale whole record must never erase an accepted row.
        assert bind_vars["stop"] == stop  # Bind the detached stop record.

    def test_document_run_store_fails_closed_without_a_database(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A file fallback cannot preserve a concurrent accepted row."""
        module = SimpleNamespace(RUN_COLLECTION="upgrade_runs", connect_database=lambda: None)  # Offline store.
        monkeypatch.setattr(wiring, "load_module", lambda name: module)  # Keep the test offline.
        store = wiring.DocumentRunStore()  # Use the production document mutation.
        assert store.apply_stop_request("run-a", {}, "2026-10-07T08:00:00+00:00") is False  # Never claim success.


class TestTheInverseStopOrder:
    """Tests for a stop that commits after a concurrent accepted row."""

    def test_a_concurrent_accepted_row_survives_the_stop_request_write(self) -> None:
        """A row that lands during the stop write stays durable.

        Why:
            The old stop path read one whole record, merged the stop into that
            copy, and wrote the copy back. The accepted row of a firmware call
            that the cloud already took committed inside that interval and the
            stale write erased it. The operator then held a stop that could
            cancel nothing, because the record named no accepted upgrade.
        """
        store = PausingStopStore()  # Pause the stop exactly where the old code read the record.
        stops = StopRequestStore(store)  # Use the production stop path, not a copy of it.
        failures: list[BaseException] = []  # Carry a worker fault back to the test thread.

        def request_stop() -> None:
            """Run the real stop request through the paused store."""
            try:  # A fault inside the worker must fail the test, never hang it.
                stops.request(RUN_ID, OPERATOR, "STOP")  # The production stop write under test.
            except BaseException as fault:  # Record every fault for the assertion below.
                failures.append(fault)  # The test thread reports the worker fault.

        store.pause_next_read = True  # Only the record read of the stop request pauses.
        worker = Thread(target=request_stop)  # Run the stop in the worker, like the route thread.
        worker.start()  # Start the stop request.
        assert store.stop_read.wait(timeout=WAIT_SECONDS)  # Wait until the stop observed the old record.
        assert store.append_accepted_upgrade(RUN_ID, accepted_row()) is True  # Commit the row inside the gap.
        store.stop_release.set()  # Let the stop finish its write with a stale observation.
        worker.join(timeout=WAIT_SECONDS)  # The stop must finish, never hang.
        assert not worker.is_alive()  # A live worker means the stop never completed.
        assert failures == []  # The production stop path raised nothing.
        stored = store.read_run(RUN_ID)  # Read the record after both concurrent mutations.
        assert stored["stop_request"]["requested_by"] == OPERATOR  # The stop is durable.
        assert stored["upgrades"] == [accepted_row()]  # The concurrent accepted row survived the stop write.
        assert stored["state"] == "upgrade_submitting"  # The stop write erased no unrelated field.


class TestTheDispatchGate:
    """Tests for the seam between the durable stop check and the cloud call."""

    def test_a_stop_that_wins_the_gate_sends_no_firmware_call(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A stop that holds the gate blocks every later firmware request."""
        store = NarrowRunStore()  # Share one durable record between the stop and the submitter.
        stops = StopRequestStore(store)  # Use the production stop path.
        calls: list[Any] = []  # Record every cloud call that the submitter attempted.
        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("switch"),))  # One switch group.
        monkeypatch.setattr(
            wiring,
            "load_module",
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: calls.append(plan) or answer())}.get,
        )  # Keep every call local to this process.
        released = Event()  # Prove that the submitter started only after the stop committed.

        def commit_stop() -> None:
            """Commit one durable stop while holding the run dispatch gate."""
            with RunDispatchGate.stop(RUN_ID):  # The stop wins the run-scoped gate.
                stops.request(RUN_ID, OPERATOR, "STOP")  # Commit the durable stop inside the gate.
                released.set()  # Report that the durable stop landed.

        worker = Thread(target=commit_stop)  # Run the stop like the route thread.
        worker.start()  # Start the stop request.
        assert released.wait(timeout=WAIT_SECONDS)  # Wait until the stop is durable.
        worker.join(timeout=WAIT_SECONDS)  # Release the gate before the submitter runs.
        record = store.read_run(RUN_ID)  # The driver carries the durable record into the phase.
        reason = wiring.CloudUpgradeSubmitter(object(), store).submit_phase(record, "switches")
        assert reason == wiring.STOP_REQUESTED_REASON  # The phase reports the visible stop reason.
        assert calls == []  # No destructive firmware request left the portal after the stop.
        assert store.read_run(RUN_ID)["upgrades"] == []  # The stopped phase accepted nothing.

    def test_a_stop_waits_for_the_dispatch_that_won_the_gate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A dispatch in flight completes and only then may a stop commit.

        Why:
            The durable stop check and the cloud call were two separate actions.
            A stop that committed between them could not stop the destructive
            call that had already passed the check, and the operator then read a
            committed stop while a firmware write was still in flight.
        """
        store = NarrowRunStore()  # Share one durable record between the stop and the submitter.
        stops = StopRequestStore(store)  # Use the production stop path.
        calls: list[Any] = []  # Record every cloud call that the submitter attempted.
        in_flight = Event()  # Set while the one cloud call runs inside the gate.
        stop_attempted = Event()  # Set after the stop thread started its gate wait.

        def invoke(session: Any, plan: Any) -> Any:
            """Stand in for one destructive cloud call."""
            del session  # The stand-in reaches no cloud.
            calls.append(plan)  # Record the one firmware request.
            in_flight.set()  # Let the test start the concurrent stop.
            assert stop_attempted.wait(timeout=WAIT_SECONDS)  # Hold the gate while the stop waits.
            return answer()  # The cloud accepted this group.

        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("switch"),))  # One switch group.
        monkeypatch.setattr(
            wiring,
            "load_module",
            {wiring.SERVICE_MODULE: service_that(invoke)}.get,
        )  # Keep every call local to this process.
        committed = Event()  # Set after the stop request returned.

        def request_stop() -> None:
            """Request one stop while a dispatch holds the run gate."""
            assert in_flight.wait(timeout=WAIT_SECONDS)  # Start only while the cloud call runs.
            stop_attempted.set()  # Report that the stop now waits for the gate.
            with RunDispatchGate.stop(RUN_ID):  # The stop must wait for the dispatch to finish.
                stops.request(RUN_ID, OPERATOR, "STOP")  # Commit the durable stop after the dispatch.
            committed.set()  # Report the durable stop to the test thread.

        worker = Thread(target=request_stop)  # Run the stop like the route thread.
        worker.start()  # Start the concurrent stop.
        record = store.read_run(RUN_ID)  # The driver carries the durable record into the phase.
        reason = wiring.CloudUpgradeSubmitter(object(), store).submit_phase(record, "switches")
        assert calls != []  # The dispatch that won the gate completed its one call.
        assert len(calls) == 1  # The phase never repeated the destructive write.
        durable = store.read_run(RUN_ID)["upgrades"]  # The accepted row must be durable before the stop commits.
        assert len(durable) == 1  # Exactly one accepted row reached the store.
        assert durable[0]["upgrade_id"] == accepted_row()["upgrade_id"]  # The row names the accepted call.
        assert committed.wait(timeout=WAIT_SECONDS)  # The stop commits only after the dispatch finished.
        worker.join(timeout=WAIT_SECONDS)  # The stop thread must finish, never hang.
        stored = store.read_run(RUN_ID)  # Read the record after both actions completed.
        assert stored["stop_request"]["requested_by"] == OPERATOR  # The stop became durable.
        assert len(stored["upgrades"]) == 1  # The stop write preserved the accepted row.
        assert stored["upgrades"][0]["upgrade_id"] == accepted_row()["upgrade_id"]  # No evidence was lost.
        assert reason is None or reason == wiring.STOP_REQUESTED_REASON  # Either outcome stops the next phase.


class BarrierLock:
    """Signal the first lock acquisition, then behave as one reentrant lock.

    Why:
        Issue #4020: the dispatch path read the waiting-stop count, dropped the
        table guard, and only then asked for the run lock. This proxy stops the
        very first acquisition inside that gap, so a test can register a stop
        there and prove that the stop still wins the gate.
    """

    def __init__(self) -> None:
        """Start with one real reentrant lock and two deterministic signals."""
        self.inner = RLock()  # The real lock that the gate registry would have created.
        self.reached = Event()  # Set when the first dispatch entered the acquisition gap.
        self.release_gap = Event()  # The test sets this after it registered the stop.
        self.first = True  # Only the first acquisition pauses inside the gap.

    def acquire(self, *args: Any, **kwargs: Any) -> bool:
        """Pause the first acquisition inside the gap, then take the real lock.

        Args:
            *args: The arguments of ``threading.RLock.acquire``.
            **kwargs: The keyword arguments of ``threading.RLock.acquire``.

        Returns:
            The result of the real reentrant lock acquisition.
        """
        taken = bool(self.inner.acquire(*args, **kwargs))  # Take the real lock from this point.
        if self.first:  # Only the first dispatch pauses, so the retry loop can finish.
            self.first = False  # Every later acquisition runs at full speed.
            self.reached.set()  # Report that the dispatch sits inside the acquisition gap.
            assert self.release_gap.wait(timeout=WAIT_SECONDS)  # Wait until the stop registered.
        return taken  # Report the real acquisition result to the gate.

    def release(self) -> None:
        """Give the real reentrant lock back."""
        self.inner.release()  # The waiting stop may now take the gate.

    def __enter__(self) -> BarrierLock:
        """Take the lock for a ``with`` block.

        Returns:
            This proxy, so the stop path may nest the same gate.
        """
        self.acquire()  # Reuse the one acquisition path of this proxy.
        return self  # The stop path uses ``with gate:`` and needs an object back.

    def __exit__(self, *details: Any) -> None:
        """Give the lock back at the end of a ``with`` block.

        Args:
            *details: The exception details Python supplies. This proxy ignores them.
        """
        del details  # A fault inside the block still releases the gate.
        self.release()  # The next caller of this run may take the gate.


class TestTheDispatchAcquisitionGap:
    """Tests for the gap between the stop check and the run lock acquisition."""

    def test_a_stop_that_registers_in_the_acquisition_gap_still_wins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A stop announced inside the acquisition gap blocks the firmware call.

        Why:
            The first version of the gate read the waiting-stop count, released
            the table guard, and only then asked for the run lock. A stop that
            registered inside that gap raced the free lock and could lose, so a
            destructive call could start after the operator sent the stop.
        """
        run_id = "gap-run-0001"  # Keep this gate registry entry away from every other test.
        store = NarrowRunStore()  # Share one durable record between the stop and the submitter.
        store.record["run_id"] = run_id  # The submitter reads the run key from the record.
        stops = StopRequestStore(store)  # Use the production stop path.
        calls: list[Any] = []  # Record every cloud call that the submitter attempted.
        barrier = BarrierLock()  # Pause the first acquisition inside the gap.
        RunDispatchGate.forget(run_id)  # Start from a clean registry for this run.
        with RunDispatchGate._REGISTRY_GUARD:  # Seed the proxy as the lock of this run.
            RunDispatchGate._LOCKS[run_id] = cast(Any, barrier)  # `_lock_for` keeps it.
        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("switch"),))  # One switch group.
        monkeypatch.setattr(
            wiring,
            "load_module",
            {wiring.SERVICE_MODULE: service_that(lambda session, plan: calls.append(plan) or answer())}.get,
        )  # Keep every call local to this process.
        committed = Event()  # Set after the durable stop landed.
        outcome: list[Any] = []  # Hold the reason that the phase reported.

        def commit_stop() -> None:
            """Register and commit one stop while the dispatch sits in the gap."""
            with RunDispatchGate.stop(run_id):  # The announcement must make the dispatch give way.
                stops.request(run_id, OPERATOR, "STOP")  # Commit the durable stop.
            committed.set()  # Report the durable stop to the test thread.

        def send_phase() -> None:
            """Send one switch phase, which pauses inside the acquisition gap."""
            record = store.read_run(run_id)  # The driver carries the durable record into the phase.
            outcome.append(wiring.CloudUpgradeSubmitter(object(), store).submit_phase(record, "switches"))

        sender = Thread(target=send_phase)  # The dispatch runs like the driver thread.
        sender.start()  # Start the phase, which stops inside the acquisition gap.
        assert barrier.reached.wait(timeout=WAIT_SECONDS)  # Wait until the dispatch sits in the gap.
        worker = Thread(target=commit_stop)  # Run the stop like the route thread.
        worker.start()  # Announce the stop inside the gap the dispatch already entered.
        while RunDispatchGate.stops_waiting(run_id) == 0:  # Wait until the stop announced itself.
            sleep(0.01)  # A short pause keeps this loop cheap and deterministic.
        barrier.release_gap.set()  # Let the paused dispatch take the lock and recheck the count.
        assert committed.wait(timeout=WAIT_SECONDS)  # The stop committed, so it won the gate.
        worker.join(timeout=WAIT_SECONDS)  # The stop thread must finish, never hang.
        sender.join(timeout=WAIT_SECONDS)  # The dispatch thread must finish, never hang.
        assert calls == []  # No destructive firmware request left the portal after the stop.
        assert outcome == [wiring.STOP_REQUESTED_REASON]  # The phase reports the visible stop reason.
        assert store.read_run(run_id)["upgrades"] == []  # The stopped phase accepted nothing.
        RunDispatchGate.forget(run_id)  # Leave no proxy lock behind for another test.


class TestTheDurableRefusal:
    """Tests that prove a refused firmware call survives a concurrent stop."""

    def test_a_refusal_is_durable_before_a_waiting_stop_may_commit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A refused call writes its evidence inside the gate, ahead of a stop.

        Why:
            The submitter returned the refusal and the driver wrote it after the
            gate reopened. A stop that committed in that interval sent the driver
            down the stopped path, and the operator then read a stopped run that
            never named the destructive call the cloud lost.
        """
        run_id = "refusal-run-0001"  # Keep this gate registry entry away from every other test.
        store = NarrowRunStore()  # Share one durable record between the stop and the submitter.
        store.record["run_id"] = run_id  # The submitter reads the run key from the record.
        stops = StopRequestStore(store)  # Use the production stop path.
        calls: list[Any] = []  # Record every cloud call that the submitter attempted.
        refused = Event()  # Set while the refused call is still inside the gate.
        stop_waiting = Event()  # Set after the stop announced itself to the gate.
        RunDispatchGate.forget(run_id)  # Start from a clean registry for this run.

        def invoke(session: Any, plan: Any) -> Any:
            """Stand in for one destructive cloud call that the cloud refuses."""
            del session  # The stand-in reaches no cloud.
            calls.append(plan)  # Record the one firmware request the portal attempted.
            refused.set()  # Let the test start the concurrent stop.
            assert stop_waiting.wait(timeout=WAIT_SECONDS)  # Hold the gate while the stop waits.
            return None  # The cloud refused this group, so the submitter must record the loss.

        monkeypatch.setattr(wiring, "build_plans", lambda record: (plan_for("switch"),))  # One switch group.
        monkeypatch.setattr(
            wiring,
            "load_module",
            {wiring.SERVICE_MODULE: service_that(invoke)}.get,
        )  # Keep every call local to this process.
        committed = Event()  # Set after the durable stop landed.

        def request_stop() -> None:
            """Request one stop while the refused dispatch holds the run gate."""
            assert refused.wait(timeout=WAIT_SECONDS)  # Start only while the refused call runs.
            stop_waiting.set()  # Report that the stop now waits for the gate.
            with RunDispatchGate.stop(run_id):  # The stop must wait for the refusal evidence.
                stops.request(run_id, OPERATOR, "STOP")  # Commit the durable stop after the refusal.
            committed.set()  # Report the durable stop to the test thread.

        worker = Thread(target=request_stop)  # Run the stop like the route thread.
        worker.start()  # Start the concurrent stop.
        record = store.read_run(run_id)  # The driver carries the durable record into the phase.
        reason = wiring.CloudUpgradeSubmitter(object(), store).submit_phase(record, "switches")
        assert reason == wiring.PHASE_REFUSED_REASON.format(phase="switches")  # The refusal ends the phase.
        failures = store.read_run(run_id)["dispatch_failures"]  # The evidence must already be durable.
        assert len(failures) == 1  # Exactly one refusal reached the store before the stop could commit.
        assert failures[0]["phase"] == "switches"  # The evidence names the phase that lost the call.
        assert committed.wait(timeout=WAIT_SECONDS)  # The stop commits only after the refusal is durable.
        worker.join(timeout=WAIT_SECONDS)  # The stop thread must finish, never hang.
        stored = store.read_run(run_id)  # Read the record after both actions completed.
        assert stored["stop_request"]["requested_by"] == OPERATOR  # The stop became durable.
        assert len(stored["dispatch_failures"]) == 1  # The stop write preserved the refusal evidence.
        assert len(calls) == 1  # The refused phase never repeated the destructive write.
        assert record["dispatch_failures"][0]["reason"] == reason  # The driver copy names the same loss.
        RunDispatchGate.forget(run_id)  # Leave no registry entry behind for another test.
