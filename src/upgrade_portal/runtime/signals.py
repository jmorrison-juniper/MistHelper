"""The stop request store for an upgrade run.

Why:
    An operator asks for a stop from a browser, and a different Gunicorn worker
    may serve the next request. A flag in process memory is invisible to that
    second worker. The file sentinel that the older code uses is worse. The
    writer at ``web_portal/services/operation.py:345`` and the reader at
    ``src/config/config_utils.py:159`` both name ``stop_loop.txt`` with no
    directory. The path therefore follows the process working directory, which
    no second worker and no container mount can trust. The stop request
    therefore lives inside the run record, which every worker reads from the
    shared store. This module writes no file of its own.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import logging  # Action logging per Constitution VII
from dataclasses import dataclass, replace  # Immutable request and outcome values
from datetime import UTC, datetime  # ISO 8601 timestamps in UTC
from typing import Any, ClassVar, Final, Protocol  # Record typing, error codes, and the store shape

from src.upgrade_portal.runtime.identity import email_digest  # The one address form a log record may hold

# WHAT: the exact text the operator types to confirm a stop.
# WHY: FR-038b accepts this text and this letter case only. A lower-case word or
#      a different word must leave the run untouched.
STOP_CONFIRMATION_TEXT: Final[str] = "STOP"

# WHAT: the scope value the first release writes.
# WHY: data-model.md section 4.3 fixes the field. A stop always covers the whole
#      run, never one device.
STOP_SCOPE_RUN: Final[str] = "run"

# WHAT: the run states that a stop can no longer change.
# WHY: the contract answers 409 run_not_stoppable when the run already finished.
TERMINAL_RUN_STATES: Final[frozenset[str]] = frozenset({"complete", "stopped", "failed"})


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
    """The two run record operations the stop store needs.

    Why:
        The stop store must not depend on one storage class. A narrow shape
        keeps the module testable with a plain double. It also lets the run
        record module own the ArangoDB write and the CSV fallback under
        ``data/``.
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
        run = self._load_run(run_id)  # Raises RunNotFoundError when the run is absent
        state = str(run.get("state", ""))  # The run state machine owns this field
        if state in TERMINAL_RUN_STATES:  # A finished run accepts no stop
            raise RunNotStoppableError(f"The run already reached the state {state}, so a stop changes nothing.")
        return run  # A stop may still change this run

    def _write_request(self, run: dict[str, Any], request: StopRequest) -> StopRequest:
        """Write one stop request into the run record.

        Why:
            The method changes `stop_request` and `updated_at` only. The run
            state machine owns the `state` field and moves the run to
            `stopping` in its own step.

        Args:
            run: The whole run record.
            request: The request to hold in the record.

        Returns:
            The request the store now holds.

        Raises:
            StopRequestError: When the store refuses the write.
        """
        run["stop_request"] = request.to_record()  # The request rides with the run, visible to every worker
        run["updated_at"] = datetime.now(UTC).isoformat()  # data-model.md asks for a fresh time on a change
        if not self._store.write_run(run):  # The store reports the true result
            raise StopRequestError("The portal could not write the stop request to the run record.")
        digest = email_digest(request.requested_by)  # An address never reaches a log record
        logging.debug("[STOP] Run %s holds a stop request from %s", run.get("run_id", ""), digest)
        return request  # The caller reports this value to the operator

    def request(self, run_id: str, actor_email: str, confirmation_text: str) -> StopRequest:
        """Record an operator request to stop one run.

        Args:
            run_id: The run key.
            actor_email: The signed-in operator who asks for the stop.
            confirmation_text: The text the operator typed.

        Returns:
            The stored request. A second call returns the first request.

        Raises:
            ConfirmationRequiredError: When the typed text is not `STOP`.
        """
        logging.info("[STOP] Operator %s asks to stop run %s", email_digest(actor_email), run_id)  # BEFORE
        if not StopRequestStore.confirmation_matches(confirmation_text):  # FR-038b guards the whole action
            raise ConfirmationRequiredError("The stop control needs the exact text STOP.")
        run = self._load_stoppable_run(run_id)  # Raises when the run is absent or already final
        held = StopRequestStore._read_from_run(run)  # A second click must not replace the first owner
        if held is not None:  # An earlier request already stands
            logging.info("* Run %s already holds a stop request from %s", run_id, email_digest(held.requested_by))
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
        logging.info("[STOP] Recording the stop outcome for run %s", run_id)  # BEFORE the change
        run = self._load_run(run_id)  # An outcome may arrive after the run reached a final state
        held = StopRequestStore._read_from_run(run)  # The outcome belongs to an existing request
        if held is None:  # A caller asked for an outcome before any operator asked for a stop
            raise StopRequestError(f"The run {run_id} holds no stop request, so it holds no outcome.")
        logging.info(  # FR-038e: name the counts, so the operator sees the split
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
        logging.debug("[STOP] Run %s stop pending: %s", run_id, pending)  # AFTER the read
        return pending  # The driver stops starting further devices
