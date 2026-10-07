"""The stop request store for an upgrade run.

Why:
    An operator asks for a stop from a browser, and a different Gunicorn worker
    may serve the next request. A flag in process memory is invisible to that
    second worker. The file sentinel that the older code uses is worse. The
    writer at ``web_portal/services/operation.py:345`` and the reader at
    ``src/foundation/runtime/config/config_utils.py:159`` both name ``stop_loop.txt`` with no
    directory. The path therefore follows the process working directory, which
    no second worker and no container mount can trust. The stop request
    therefore lives inside the run record, which every worker reads from the
    shared store. This module writes no file of its own.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import logging  # Action logging per Constitution VII
import threading  # The dispatch gate serializes one stop against one firmware call
from collections.abc import Iterator  # The gate publishes two context managers
from contextlib import contextmanager  # The gate releases its lock on every path
from dataclasses import dataclass, replace  # Immutable request and outcome values
from datetime import UTC, datetime  # ISO 8601 timestamps in UTC
from typing import Any, ClassVar, Final, Protocol  # Record typing, error codes, and the store shape

from src.interfaces.portals.upgrade_portal.runtime.identity import (
    email_digest,
)  # The one address form a log record may hold
from src.interfaces.portals.upgrade_portal.runtime.runs import (
    RunStateMachine,
    RunTransitionError,
)  # Use the canonical final states.

logger = logging.getLogger(__name__)  # Keep log records tied to this module.

# WHAT: the exact text the operator types to confirm a stop.
# WHY: FR-038b accepts this text and this letter case only. A lower-case word or
#      a different word must leave the run untouched.
STOP_CONFIRMATION_TEXT: Final[str] = "STOP"

# WHAT: the scope value the first release writes.
# WHY: data-model.md section 4.3 fixes the field. A stop always covers the whole
#      run, never one device.
STOP_SCOPE_RUN: Final[str] = "run"

# WHAT: the sentence a run carries when it lost the evidence of a firmware call.
# WHY: Issue #4020: an unproven refusal leaves the cloud state of the run
#      unknown, so the portal blocks every later family and names the cause.
DISPATCH_FENCED_REASON: Final[str] = (
    "The portal could not record one firmware call, so the run sends no more firmware until an operator checks it."
)


class StopRequestError(Exception):
    """Base error for every stop request failure.

    Why:
        The route layer maps an error to an HTTP status and to a machine code.
        A shared base lets one handler catch every failure of this module and
        read the code from the same attribute.
    """

    code: ClassVar[str] = "stop_request_failed"  # Default machine code the route reports


class ConfirmationRequiredError(StopRequestError):
    """The operator did not type the exact confirmation text.

    Why:
        FR-038b protects a running upgrade behind typed text. The contract
        answers 400 with this code.
    """

    code: ClassVar[str] = "confirmation_required"  # Matches contracts/http-api.md


class RunNotFoundError(StopRequestError):
    """The store holds no run with the asked identifier.

    Why:
        The contract answers 404 with this code.
    """

    code: ClassVar[str] = "run_not_found"  # Matches contracts/http-api.md


class RunNotStoppableError(StopRequestError):
    """The run already reached a state that a stop cannot change.

    Why:
        The contract answers 409 with this code.
    """

    code: ClassVar[str] = "run_not_stoppable"  # Matches contracts/http-api.md


@dataclass(frozen=True, slots=True)
class StopOutcome:
    """What the cancel calls achieved for each device of a run.

    Why:
        FR-038e asks the portal to name each cancelled device and each device
        that continues. The three lists carry those names, and the message
        carries one plain sentence for the operator.
    """

    cancelled: tuple[str, ...] = ()  # Devices that had not started, so the portal cancelled them
    already_writing: tuple[str, ...] = ()  # Devices in mid-flash. The portal never interrupts one
    no_cancel_available: tuple[str, ...] = ()  # Empty today. FR-038f reports a future gap here
    message: str = ""  # One plain sentence the interface shows without further work

    def to_record(self) -> dict[str, Any]:
        """Return the outcome in the shape the run record holds.

        Returns:
            A dictionary with three lists and one message.
        """
        return {
            "cancelled": list(self.cancelled),  # A list, because the store holds JSON
            "already_writing": list(self.already_writing),  # Same reason
            "no_cancel_available": list(self.no_cancel_available),  # Same reason
            "message": self.message,  # Plain text for the operator
        }

    @staticmethod
    def _text_tuple(value: Any) -> tuple[str, ...]:
        """Return a tuple of text values read from a stored list.

        Args:
            value: The stored field, which may hold anything.

        Returns:
            A tuple of text values, empty when the field holds no list.
        """
        if not isinstance(value, list):  # A missing or damaged field must not raise
            return ()  # An empty tuple keeps the caller simple
        return tuple(str(entry) for entry in value)  # Force text, because the store may hold other types

    @staticmethod
    def from_record(record: dict[str, Any]) -> StopOutcome:
        """Build an outcome from the dictionary held in a run record.

        Args:
            record: The `outcome` member of a stop request.

        Returns:
            The outcome value.
        """
        return StopOutcome(
            cancelled=StopOutcome._text_tuple(record.get("cancelled")),  # Devices the portal cancelled
            already_writing=StopOutcome._text_tuple(record.get("already_writing")),  # Devices that continue
            no_cancel_available=StopOutcome._text_tuple(record.get("no_cancel_available")),  # Future gaps
            message=str(record.get("message", "")),  # Plain sentence, empty when absent
        )


@dataclass(frozen=True, slots=True)
class StopRequest:
    """The operator request to stop one upgrade run.

    Why:
        FR-038h asks the portal to record every stop with an owner, a time, and
        a device list. The value holds all three, and the run record holds the
        value, so every worker reads the same request.
    """

    requested_by: str  # The operator email. Never a credential
    requested_at: str  # ISO 8601 in UTC
    confirmation_text: str = STOP_CONFIRMATION_TEXT  # The text the operator typed
    scope: str = STOP_SCOPE_RUN  # Always the whole run in the first release
    outcome: StopOutcome | None = None  # Null until the cancel calls report

    @staticmethod
    def for_operator(actor_email: str) -> StopRequest:
        """Build a fresh request for one operator, timed at the present moment.

        Args:
            actor_email: The signed-in operator who asks for the stop.

        Returns:
            A request with no outcome yet.
        """
        return StopRequest(requested_by=actor_email, requested_at=datetime.now(UTC).isoformat())  # Time it here

    def to_record(self) -> dict[str, Any]:
        """Return the request in the shape of data-model.md section 4.3.

        Returns:
            A dictionary the run record holds under `stop_request`.
        """
        return {
            "requested_by": self.requested_by,  # The owner of the stop
            "requested_at": self.requested_at,  # When the operator asked
            "confirmation_text": self.confirmation_text,  # Proof that the operator typed the word
            "scope": self.scope,  # Always the whole run today
            "outcome": self.outcome.to_record() if self.outcome else None,  # Null until the cancels report
        }

    @staticmethod
    def from_record(record: dict[str, Any]) -> StopRequest:
        """Build a request from the dictionary held in a run record.

        Args:
            record: The `stop_request` member of a run record.

        Returns:
            The request value, with the outcome when the record holds one.
        """
        outcome_record = record.get("outcome")  # Null until the cancel calls report
        outcome = StopOutcome.from_record(outcome_record) if isinstance(outcome_record, dict) else None
        return StopRequest(
            requested_by=str(record.get("requested_by", "")),  # The owner of the stop
            requested_at=str(record.get("requested_at", "")),  # When the operator asked
            confirmation_text=str(record.get("confirmation_text", STOP_CONFIRMATION_TEXT)),  # The typed word
            scope=str(record.get("scope", STOP_SCOPE_RUN)),  # Always the whole run today
            outcome=outcome,  # None until the cancel calls report
        )


class RunRecordStore(Protocol):
    """The run record operations that preserve stop and upgrade evidence.

    Why:
        The stop store must not depend on one storage class. A narrow shape
        keeps the module testable with a plain double. It also lets the run
        record module own the ArangoDB write and the CSV fallback under
        ``data/``. Accepted upgrade rows and stop requests each need one
        field-level mutation, because a stale whole-record write can erase the
        other one. The two mutations are the inverse of each other, and a store
        must make both of them atomic against the other.
    """

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one run record, or None when no run holds the identifier.

        Args:
            run_id: The run key.

        Returns:
            The record, or None.
        """
        ...  # A protocol declares the shape only

    def write_run(self, run: dict[str, Any]) -> bool:
        """Write one run record and report the true result.

        Args:
            run: The whole record, with the changed fields already in place.

        Returns:
            True when the store holds the record.
        """
        ...  # A protocol declares the shape only

    def append_accepted_upgrade(self, run_id: str, row: dict[str, Any]) -> bool:
        """Append one accepted upgrade row without replacing another field.

        Args:
            run_id: The run key.
            row: The accepted cloud response.

        Returns:
            True when the row is durable.
        """
        ...  # A protocol declares the shape only

    def append_dispatch_failure(self, run_id: str, failure: dict[str, Any]) -> bool:
        """Append one refused or faulted firmware dispatch without replacing another field.

        Why:
            Issue #4020: the submitter returned a refusal, released the dispatch
            gate, and left the driver to persist the refused phase afterwards. A
            stop that committed between those two steps sent the driver down the
            stopped path, and the refusal evidence of a destructive partial run
            disappeared. This mutation makes the refusal durable inside the gate.

        Args:
            run_id: The run key.
            failure: The refusal evidence of one dispatch.

        Returns:
            True when the refusal evidence is durable.
        """
        ...  # A protocol declares the shape only

    def apply_stop_request(self, run_id: str, stop_request: dict[str, Any], updated_at: str) -> bool:
        """Write only the stop fields of one run and preserve every other field.

        Args:
            run_id: The run key.
            stop_request: The stop request record.
            updated_at: The fresh change time in ISO 8601 UTC.

        Returns:
            True when the stop is durable.
        """
        ...  # A protocol declares the shape only

    def apply_state_transition(self, run_id: str, state: str, updated_at: str, expected_state: str) -> bool:
        """Write only the state fields of one run while the observed state still holds.

        Why:
            Issue #4020: the stop route read the whole record, moved it to
            ``stopping``, and wrote the whole record back. A driver update that
            committed inside that interval disappeared, so the operator could
            lose a phase result, post-check evidence, or a terminal state.

            The write also carried no condition, so a driver that reached a
            terminal state between the read and the write was moved backward.
            The caller now names the state it decided on, and the store refuses
            the move when the durable record left that state.

        Args:
            run_id: The run key.
            state: The new run state value.
            updated_at: The fresh change time in ISO 8601 UTC.
            expected_state: The state the caller read before it decided.

        Returns:
            True when the new state is durable.
        """
        ...  # A protocol declares the shape only


class DispatchEvidenceError(RuntimeError):
    """One firmware dispatch could not make its durable evidence.

    Why:
        Issue #4020: the submitter logged a failed refusal write and returned
        the ordinary refusal reason. The run then read as a plain refused phase
        while no durable record named the destructive call the cloud lost.
        This error makes that case fail the run where an operator can see it.
    """


class DispatchFencedError(RuntimeError):
    """A run may send no further firmware, because earlier evidence was lost.

    Why:
        Issue #4020: a run whose dispatch evidence never reached the store holds
        an unknown cloud state. No later family of that run may receive a
        destructive write until an operator recovers the run.
    """


class RunDispatchGate:
    """Serializes one durable stop against one in-flight firmware dispatch.

    Why:
        The submitter read the durable stop and then sent firmware as two
        separate actions. A stop that committed between them could not hold back
        the destructive call that had already passed the read, so the operator
        saw a committed stop while a firmware write was still in flight.

        This gate makes the stop check, the one cloud call, and the durable
        accepted row one action for each run. If a dispatch wins the gate, a
        concurrent stop waits until that dispatch finished and its accepted row
        or its refusal is durable. If a stop wins the gate, every later dispatch
        of the same run reads the durable stop before its cloud call and sends
        nothing.

    Warning:
        The lock is process local, and the portal serves the stop route and the
        run driver thread of one run in one worker process. A second worker that
        accepts a stop for a run it does not drive still cannot erase evidence,
        because every store mutation under this gate changes one field only.
        The invariant this gate adds is the ordering of the stop check and the
        cloud call inside the process that owns the dispatch. Do not hold a
        database transaction across the cloud call this gate covers.
    """

    _REGISTRY_GUARD: ClassVar[threading.Condition] = threading.Condition()  # Guards the two tables below.
    _LOCKS: ClassVar[dict[str, threading.RLock]] = {}  # One reentrant lock for each live run.
    _STOPS_WAITING: ClassVar[dict[str, int]] = {}  # The count of stops that wait for each run.
    _FENCED: ClassVar[set[str]] = set()  # Each run whose lost evidence blocks every later firmware call.

    @classmethod
    def _lock_for(cls, run_id: str) -> threading.RLock:
        """Return the one gate lock of one run.

        Why:
            A reentrant lock lets the stop route hold the gate and then call
            ``StopRequestStore.request``, which takes the same gate again.

        Args:
            run_id: The run key.

        Returns:
            The lock that both the stop path and the dispatch path take.
        """
        with cls._REGISTRY_GUARD:  # The guard is reentrant, so a holding caller may call this method.
            held = cls._LOCKS.get(run_id)  # A live run already owns one lock.
            if held is None:  # The first caller of this run creates the lock.
                held = threading.RLock()  # Reentrant, so one thread may nest the stop inside the gate.
                cls._LOCKS[run_id] = held  # Publish the lock for every later caller of this run.
            return held  # Both paths of this run now share one gate.

    @classmethod
    @contextmanager
    def dispatch(cls, run_id: str) -> Iterator[None]:
        """Hold the gate across one stop check, one cloud call, and its evidence.

        Why:
            A stop that already waits for this run takes the gate first. A plain
            lock gives no order, so a second firmware call could win the gate
            ahead of a stop that the operator sent during the first call.

        Args:
            run_id: The run key.

        Yields:
            None, while this dispatch owns the gate of the run.

        Raises:
            DispatchFencedError: The run lost earlier dispatch evidence.
        """
        logger.debug("[GATE] Run %s asks for the dispatch gate", run_id)  # Record the wait before the action.
        cls.raise_if_fenced(run_id)  # A run with lost evidence may never start another destructive call.
        gate = cls._claim_dispatch(run_id)  # Eligibility and acquisition form one linearizable claim.
        try:  # The claim must come back whatever the destructive caller does.
            cls.raise_if_fenced(run_id)  # A fence set during the wait still blocks this call, inside the gate.
            logger.info("[GATE] Run %s holds the dispatch gate", run_id)  # The firmware call may now start.
            yield  # The caller checks the stop, sends one call, and persists its result.
        finally:  # A fault in the cloud call must never leave the gate of this run held.
            gate.release()  # A waiting stop may now take the gate and commit.
        logger.debug("[GATE] Run %s released the dispatch gate", run_id)  # A waiting stop may now commit.

    @classmethod
    def _claim_dispatch(cls, run_id: str) -> threading.RLock:
        """Take the gate of one run only while no stop of that run waits.

        Why:
            Issue #4020: the first version read the waiting-stop count, dropped
            the table guard, and only then asked for the run lock. A stop that
            registered inside that gap still lost the race for the free lock, so
            a destructive call could start after the operator sent the stop.

            This loop rechecks the count after it holds the run lock. A stop
            that registered in the gap makes this dispatch give the lock back
            and wait again, so the stop always wins. The recheck never waits
            while it holds the run lock, so the stop path cannot deadlock
            against it.

        Args:
            run_id: The run key.

        Returns:
            The held run lock. The caller owns it and must release it.
        """
        while True:  # One pass for each stop that registers inside the acquisition gap.
            with cls._REGISTRY_GUARD:  # Read the waiting-stop count under the table guard.
                while cls._STOPS_WAITING.get(run_id, 0) > 0:  # An operator stop of this run comes first.
                    logger.info("[GATE] Run %s holds a firmware call, because a stop waits", run_id)
                    cls._REGISTRY_GUARD.wait()  # Release the guard until the stop finishes.
                gate = cls._lock_for(run_id)  # Read the lock of this run while no stop waits.
            gate.acquire()  # Block here only for a dispatch of the same run, never for the table guard.
            with cls._REGISTRY_GUARD:  # The recheck holds the run lock, so it must never wait here.
                if cls._STOPS_WAITING.get(run_id, 0) == 0:  # No stop registered inside the acquisition gap.
                    return gate  # The caller owns the gate, and every later stop waits for it.
            logger.info("[GATE] Run %s gives the dispatch gate back to a stop that registered", run_id)
            gate.release()  # A stop won the gap, so this dispatch waits for it and tries again.

    @classmethod
    @contextmanager
    def stop(cls, run_id: str) -> Iterator[None]:
        """Hold the gate across one durable stop write.

        Args:
            run_id: The run key.

        Yields:
            None, while this stop owns the gate of the run.
        """
        logger.debug("[GATE] Run %s asks for the stop gate", run_id)  # Record the wait before the action.
        with cls._REGISTRY_GUARD:  # Announce the stop before it waits for an in-flight dispatch.
            cls._STOPS_WAITING[run_id] = cls._STOPS_WAITING.get(run_id, 0) + 1  # No later call may start.
            gate = cls._lock_for(run_id)  # Claim the same lock that each dispatch of this run takes.
        try:  # The announcement must come back whatever the stop route does.
            with gate:  # A dispatch in flight finishes and records its evidence before this stop commits.
                logger.info("[GATE] Run %s holds the stop gate", run_id)  # No later cloud call may start.
                yield  # The caller writes the durable stop request.
        finally:  # A fault in the stop route must never block every later dispatch.
            with cls._REGISTRY_GUARD:  # Withdraw the announcement under the table guard.
                left = cls._STOPS_WAITING.get(run_id, 1) - 1  # This stop no longer waits for the run.
                if left > 0:  # A second operator click still waits for the same run.
                    cls._STOPS_WAITING[run_id] = left  # Keep the remaining announcement.
                else:  # No stop of this run waits now.
                    cls._STOPS_WAITING.pop(run_id, None)  # Drop the empty entry, so the table stays small.
                cls._REGISTRY_GUARD.notify_all()  # Wake every dispatch that waits for this run.
        logger.debug("[GATE] Run %s released the stop gate", run_id)  # A waiting dispatch now reads the stop.

    @classmethod
    def stops_waiting(cls, run_id: str) -> int:
        """Return the count of stops that wait for the gate of one run.

        Why:
            A deterministic test must know that a stop registered its claim
            before it releases an in-flight dispatch. The count is the only
            visible proof that no later firmware call may start.

        Args:
            run_id: The run key.

        Returns:
            The number of stops of this run that hold or await the gate.
        """
        with cls._REGISTRY_GUARD:  # The table is shared by every run of this process.
            return cls._STOPS_WAITING.get(run_id, 0)  # An absent run has no waiting stop.

    @classmethod
    def fence(cls, run_id: str) -> None:
        """Block every later firmware dispatch of one run.

        Why:
            Issue #4020: a refused dispatch whose evidence never reached the
            store leaves the cloud state of that run unknown. The portal must
            then send no further destructive write for the run until an
            operator recovers the run through the retry route.

            Caution: the fence lives in a table of this process alone. A restart
            drops it, so it is defense in depth beside the terminal state of the
            record, which already stops a new start of the same run.

        Args:
            run_id: The run key.
        """
        with cls._REGISTRY_GUARD:  # The table is shared by every run of this process.
            cls._FENCED.add(run_id)  # A later dispatch of this run now raises before it takes the gate.
        logger.error("[GATE] Run %s may send no further firmware, because its evidence was lost", run_id)

    @classmethod
    def is_fenced(cls, run_id: str) -> bool:
        """Report whether one run may still send firmware.

        Args:
            run_id: The run key.

        Returns:
            True when lost evidence blocks every later dispatch of the run.
        """
        with cls._REGISTRY_GUARD:  # The table is shared by every run of this process.
            return run_id in cls._FENCED  # An absent run carries no fence.

    @classmethod
    def raise_if_fenced(cls, run_id: str) -> None:
        """Stop one dispatch of a run that lost its earlier evidence.

        Args:
            run_id: The run key.

        Raises:
            DispatchFencedError: The run lost earlier dispatch evidence.
        """
        if cls.is_fenced(run_id):  # The fence outlives the dispatch that set it, for the life of the process.
            raise DispatchFencedError(DISPATCH_FENCED_REASON)  # The driver fails the run with this sentence.

    @classmethod
    def forget(cls, run_id: str) -> None:
        """Drop the gate lock and the fence of one recovered run.

        Why:
            Issue #4020: the fence lives in a table of this process alone, so it
            is defense in depth and not a durable record. The retry route is the
            one production caller, because it runs only after the operator
            confirms the recovery of a terminal unsuccessful run and the store
            holds the new record. The source run keeps its terminal state, and
            the start route refuses every state except the confirmation state,
            so the recovered key sends no further firmware.

        Args:
            run_id: The run key.
        """
        with cls._REGISTRY_GUARD:  # The table is shared by every run of this process.
            cls._LOCKS.pop(run_id, None)  # An absent run is no fault, because a run may never dispatch.
            cls._FENCED.discard(run_id)  # A recovered run needs no fence, and a new run may reuse the key.
        logger.info("[GATE] Run %s left the dispatch registry after an operator recovery", run_id)


class StopRequestStore:
    """Reads and writes the stop request that lives inside a run record.

    Why:
        Two Gunicorn workers serve the portal, and the run driver thread reads
        the request once for each phase. All three read the same run record, so
        the request needs no sentinel file and no shared memory.
    """

    def __init__(self, store: RunRecordStore) -> None:
        """Hold the run record store the stop store reads and writes.

        Args:
            store: Reads one run record and writes one run record.
        """
        self._store = store  # The only path to the shared record

    @staticmethod
    def confirmation_matches(text: str) -> bool:
        """Report whether the operator typed the exact stop text.

        Why:
            FR-038b names the letter case, so the check compares the text
            without a trim and without a case change.

        Args:
            text: The text the operator typed.

        Returns:
            True when the text equals `STOP` exactly.
        """
        return text == STOP_CONFIRMATION_TEXT  # Exact text and exact letter case

    @staticmethod
    def _read_from_run(run: dict[str, Any]) -> StopRequest | None:
        """Return the stop request held in one run record.

        Args:
            run: The whole run record.

        Returns:
            The request, or None when no operator asked for a stop.
        """
        record = run.get("stop_request")  # Null until an operator asks
        if not isinstance(record, dict):  # Null, absent, or damaged
            return None  # No operator asked for a stop
        return StopRequest.from_record(record)  # Rebuild the value from the record

    def _load_run(self, run_id: str) -> dict[str, Any]:
        """Read one run record.

        Args:
            run_id: The run key.

        Returns:
            The whole run record.

        Raises:
            RunNotFoundError: When the store holds no run with that key.
        """
        run = self._store.read_run(run_id)  # One read of the shared record
        if run is None:  # The identifier names no run
            raise RunNotFoundError(f"The portal holds no run with the identifier {run_id}.")
        return run  # The caller changes and writes this record

    def _load_stoppable_run(self, run_id: str) -> dict[str, Any]:
        """Read one run record that a stop can still change.

        Args:
            run_id: The run key.

        Returns:
            The whole run record.

        Raises:
            RunNotStoppableError: When the run already reached a final state.
        """
        logger.info("[STOP] Checking whether run %s is final", run_id)  # Record the stop guard before evaluation.
        run = self._load_run(run_id)  # Read the shared record before the canonical state decision.
        try:  # A malformed state cannot prove that a destructive stop is safe.
            state = RunStateMachine.read_state(run)  # Coerce the stored text through the canonical state model.
        except RunTransitionError as failure:  # Fail closed when the state does not belong to the model.
            raise RunNotStoppableError("The run state is invalid.") from failure  # Return one safe stop refusal.
        if state in RunStateMachine.TERMINAL:  # The canonical terminal set controls every stop refusal.
            raise RunNotStoppableError(f"The run is final: {state.value}.")  # Refuse every canonical final state.
        logger.debug("[STOP] Run %s remains stoppable in state %s", run_id, state.value)  # Record the safe result.
        return run  # A nonfinal run can continue through the stop request path.

    def _write_request(self, run: dict[str, Any], request: StopRequest) -> StopRequest:
        """Write one stop request into the run record.

        Why:
            The method changes `stop_request` and `updated_at` only. The run
            state machine owns the `state` field and moves the run to
            `stopping` in its own step.

            Issue #4020: the write is one narrow store mutation, never a whole
            record replacement. The old path read the record, merged the stop
            into that copy, and wrote the copy back, so an accepted firmware row
            that committed inside that interval disappeared. The operator then
            held a stop that could cancel nothing.

        Args:
            run: The whole run record, which names the run key.
            request: The request to hold in the record.

        Returns:
            The request the store now holds.

        Raises:
            StopRequestError: When the store refuses the write.
        """
        run_id = str(run.get("run_id", ""))  # The narrow mutation needs the durable run key only.
        changed_at = datetime.now(UTC).isoformat()  # data-model.md asks for a fresh time on a change
        record = request.to_record()  # The request rides with the run, visible to every worker
        if not self._store.apply_stop_request(run_id, record, changed_at):  # The store reports the true result
            raise StopRequestError("The portal could not write the stop request to the run record.")
        run["stop_request"] = record  # Keep the caller copy in step with the durable record.
        run["updated_at"] = changed_at  # The caller copy carries the same change time.
        digest = email_digest(request.requested_by)  # An address never reaches a log record
        logger.debug("[STOP] Run %s holds a stop request from %s", run_id, digest)
        return request  # The caller reports this value to the operator

    def request(self, run_id: str, actor_email: str, confirmation_text: str) -> StopRequest:
        """Record an operator request to stop one run.

        Why:
            Issue #4020: the read, the duplicate check, and the durable write
            run inside ``RunDispatchGate.stop``. A firmware dispatch of the same
            run therefore cannot start between the stop check of the submitter
            and its cloud call, and a dispatch already in flight completes and
            records its evidence before this stop commits.

        Args:
            run_id: The run key.
            actor_email: The signed-in operator who asks for the stop.
            confirmation_text: The text the operator typed.

        Returns:
            The stored request. A second call returns the first request.

        Raises:
            ConfirmationRequiredError: When the typed text is not `STOP`.
        """
        logger.info("[STOP] Operator %s asks to stop run %s", email_digest(actor_email), run_id)  # BEFORE
        if not StopRequestStore.confirmation_matches(confirmation_text):  # FR-038b guards the whole action
            raise ConfirmationRequiredError("The stop control needs the exact text STOP.")
        with RunDispatchGate.stop(run_id):  # No firmware call of this run may start inside this block.
            run = self._load_stoppable_run(run_id)  # Raises when the run is absent or already final
            held = StopRequestStore._read_from_run(run)  # A second click must not replace the first owner
            if held is not None:  # An earlier request already stands
                logger.info("* Run %s already holds a stop request from %s", run_id, email_digest(held.requested_by))
                return held  # Report the first request, so the record keeps one owner
            return self._write_request(run, StopRequest.for_operator(actor_email))  # Store the fresh request

    def record_outcome(self, run_id: str, outcome: StopOutcome) -> StopRequest:
        """Add the cancel results to the stop request the run already holds.

        Args:
            run_id: The run key.
            outcome: The devices cancelled, the devices that continue, and the message.

        Returns:
            The stored request, now with the outcome.

        Raises:
            StopRequestError: When the run holds no stop request.
        """
        logger.info("[STOP] Recording the stop outcome for run %s", run_id)  # BEFORE the change
        run = self._load_run(run_id)  # An outcome may arrive after the run reached a final state
        held = StopRequestStore._read_from_run(run)  # The outcome belongs to an existing request
        if held is None:  # A caller asked for an outcome before any operator asked for a stop
            raise StopRequestError(f"The run {run_id} holds no stop request, so it holds no outcome.")
        logger.info(  # FR-038e: name the counts, so the operator sees the split
            "* Run %s stop outcome: %s cancelled, %s already writing",
            run_id,
            len(outcome.cancelled),  # Devices the portal stopped before they started
            len(outcome.already_writing),  # Devices in mid-flash, which continue
        )
        return self._write_request(run, replace(held, outcome=outcome))  # Keep the owner, add the outcome

    def read(self, run_id: str) -> StopRequest | None:
        """Return the stop request for one run.

        Args:
            run_id: The run key.

        Returns:
            The request, or None when the run is absent or holds no request.
        """
        run = self._store.read_run(run_id)  # A status view may ask about a run that no longer exists
        if run is None:  # No record, so no request
            return None  # The caller shows no stop control state
        return StopRequestStore._read_from_run(run)  # The request, or None

    def is_stop_pending(self, run_id: str) -> bool:
        """Report whether an operator asked to stop one run.

        Why:
            The run driver calls this once for each phase, where the older code
            called ``ConfigUtils.check_stop_signal()``. The read hits the shared
            run record, so a request from a different worker still arrives.

        Args:
            run_id: The run key.

        Returns:
            True when the run record holds a stop request.
        """
        pending = self.read(run_id) is not None  # One read of the shared record
        logger.debug("[STOP] Run %s stop pending: %s", run_id, pending)  # AFTER the read
        return pending  # The driver stops starting further devices
