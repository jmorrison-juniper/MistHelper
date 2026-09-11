"""Unit tests for the stop request store of the upgrade capture portal.

Why:
    A stop ends a live firmware upgrade, so the confirmation gate and the audit
    owner must never drift. These tests hold the module to the record shape in
    ``specs/1823-upgrade-capture-portal/data-model.md`` section 4.3. Every
    failure test asserts on the contract error ``code`` and never on the
    operator message, as ``contracts/README.md`` requires. Every test runs
    against an in-memory double, so no test opens a database connection and no
    test writes a file.
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime
from typing import Any

import pytest

from src.upgrade_portal.runtime.signals import (
    STOP_CONFIRMATION_TEXT,
    STOP_SCOPE_RUN,
    TERMINAL_RUN_STATES,
    ConfirmationRequiredError,
    RunNotFoundError,
    RunNotStoppableError,
    StopOutcome,
    StopRequest,
    StopRequestStore,
)

# WHY: A run key in the shape of data-model.md section 4, so a reader sees a
# realistic identifier rather than a bare word.
RUN_ID = "run-0f3a9c2b7d1e4f5a8b6c0d2e4f6a8b0c"

# WHY: A key that no record holds. The absent run path needs one.
MISSING_RUN_ID = "run-00000000000000000000000000000000"

# WHY: Two operators, so a test can prove which email the record keeps.
FIRST_ACTOR = "first.operator@example.com"
SECOND_ACTOR = "second.operator@example.com"

# WHY: A live state from section 4.1. A stop can still change this run.
RUNNING_STATE = "upgrade_running"

# WHY: A time far in the past. A fresh timestamp must always compare later.
EARLIER_TIME = "2026-01-01T00:00:00+00:00"

# WHY: One outcome value the record_outcome tests share.
SAMPLE_OUTCOME = StopOutcome(
    cancelled=("aabbccddeeff",),
    already_writing=("001122334455",),
    message="The portal cancelled one device. One device continues.",
)


class FakeRunRecordStore:
    """An in-memory stand-in for the run record store.

    Why:
        The stop request store must reach a run record through the
        ``RunRecordStore`` protocol only. This double holds every record in one
        shared dictionary, so two separate instances read the same record. A
        read returns a copy and a write stores a copy, which models the round
        trip of a real database.
    """

    def __init__(self, records: dict[str, dict[str, Any]]) -> None:
        """Hold the shared record dictionary.

        Args:
            records: The run records, keyed by run identifier.
        """
        self.records = records  # Shared with every other double over the same dictionary

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return a copy of one run record.

        Args:
            run_id: The run key.

        Returns:
            A copy of the record, or None when no record holds the key.
        """
        record = self.records.get(run_id)  # None when the key is absent
        return deepcopy(record) if record is not None else None  # A copy, as a database read gives

    def write_run(self, run: dict[str, Any]) -> bool:
        """Store a copy of one run record.

        Args:
            run: The whole record, with the changed fields already in place.

        Returns:
            True, because this double always accepts a write.
        """
        self.records[str(run["run_id"])] = deepcopy(run)  # A copy, so a later edit cannot reach the store
        return True


def _run_record(state: str = RUNNING_STATE) -> dict[str, Any]:
    """Return one run record in the state a test needs.

    Why:
        Each test starts from a record that holds no stop request. The state
        field decides whether the store accepts a stop.

    Args:
        state: The run state the record holds.

    Returns:
        A run record with no stop request.
    """
    return {
        "_key": RUN_ID,
        "run_id": RUN_ID,
        "state": state,  # The run state machine owns this field
        "updated_at": EARLIER_TIME,  # A fresh write must replace this value
        "stop_request": None,  # Null until an operator asks for a stop
        "targets": [],  # Present so a test can prove the store leaves it alone
    }


def _records(state: str = RUNNING_STATE) -> dict[str, dict[str, Any]]:
    """Return the shared record dictionary that backs the fake store.

    Why:
        Two store instances share this dictionary in the cross-worker test, so
        the dictionary stands for the database itself.

    Args:
        state: The run state the single record holds.

    Returns:
        A dictionary that holds one run record.
    """
    return {RUN_ID: _run_record(state)}


def _new_store(records: dict[str, dict[str, Any]]) -> StopRequestStore:
    """Build one stop request store over the shared records.

    Why:
        Each call builds a fresh double and a fresh store, so a test can model
        a second worker process that shares only the database.

    Args:
        records: The shared record dictionary.

    Returns:
        A stop request store that reaches the records through the protocol.
    """
    return StopRequestStore(FakeRunRecordStore(records))


def _store_with_request(records: dict[str, dict[str, Any]]) -> StopRequestStore:
    """Build one store and record a stop request from the first operator.

    Args:
        records: The shared record dictionary.

    Returns:
        The store that recorded the request.
    """
    store = _new_store(records)
    store.request(RUN_ID, FIRST_ACTOR, STOP_CONFIRMATION_TEXT)
    return store


def _double_request(records: dict[str, dict[str, Any]]) -> tuple[StopRequest, StopRequest]:
    """Ask for a stop twice, with a different operator on each call.

    Why:
        A double click sends the request twice. Both calls share one store
        instance, exactly as one worker process serves two fast clicks.

    Args:
        records: The shared record dictionary.

    Returns:
        The request from the first call and the request from the second call.
    """
    store = _new_store(records)
    first = store.request(RUN_ID, FIRST_ACTOR, STOP_CONFIRMATION_TEXT)
    second = store.request(RUN_ID, SECOND_ACTOR, STOP_CONFIRMATION_TEXT)
    return first, second


def _stored_stop_request(records: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Return the stop request the shared record holds.

    Args:
        records: The shared record dictionary.

    Returns:
        The ``stop_request`` member of the run record.
    """
    stored = records[RUN_ID]["stop_request"]
    assert isinstance(stored, dict), "The run record must hold a stop request."
    return stored


def test_confirmation_accepts_the_exact_text() -> None:
    """The gate accepts the exact text the module publishes.

    Why:
        The route layer and the browser both read STOP_CONFIRMATION_TEXT. The
        gate must accept that value, or no operator can ever stop a run.
    """
    assert STOP_CONFIRMATION_TEXT == "STOP"
    assert StopRequestStore.confirmation_matches(STOP_CONFIRMATION_TEXT) is True


@pytest.mark.parametrize("typed", ["stop", "Stop", "sTOP"])
def test_confirmation_is_case_sensitive(typed: str) -> None:
    """The gate rejects the word in any other letter case.

    Why:
        FR-038b names the letter case. A lower-case word must leave the run
        untouched, because a stop ends a live upgrade.

    Args:
        typed: The text the operator typed.
    """
    assert StopRequestStore.confirmation_matches(typed) is False


@pytest.mark.parametrize("typed", [" STOP", "STOP ", " STOP ", "\tSTOP"])
def test_confirmation_does_not_trim_blank_space(typed: str) -> None:
    """The gate rejects the word with blank space around it.

    Why:
        The module compares the text without a trim. An operator who pastes a
        trailing space therefore keeps the run running, which is the safe
        result for a destructive action.

    Args:
        typed: The text the operator typed.
    """
    assert StopRequestStore.confirmation_matches(typed) is False


@pytest.mark.parametrize("typed", ["", "CONFIRM", "STOPP"])
def test_confirmation_rejects_other_text(typed: str) -> None:
    """The gate rejects the empty string and every other word.

    Why:
        The empty string is the value a browser sends for an untouched field.
        CONFIRM belongs to the lock takeover gate and must not stop a run.

    Args:
        typed: The text the operator typed.
    """
    assert StopRequestStore.confirmation_matches(typed) is False


def test_confirmation_rejects_none() -> None:
    """The gate rejects a missing value and raises nothing.

    Why:
        A browser may omit the field, so the value arrives as None. The gate
        must report False rather than raise, because the route layer answers
        400 from the return value.
    """
    absent: Any = None  # The annotation states that the value arrives untyped from a request body
    assert StopRequestStore.confirmation_matches(absent) is False


def test_request_rejects_a_wrong_confirmation_text() -> None:
    """A wrong word raises the confirmation error and writes nothing.

    Why:
        The contract answers 400 with the code confirmation_required. The test
        asserts on the code, never on the message.
    """
    records = _records()
    with pytest.raises(ConfirmationRequiredError) as error:
        _new_store(records).request(RUN_ID, FIRST_ACTOR, "stop")
    assert error.value.code == "confirmation_required"
    assert records[RUN_ID]["stop_request"] is None


def test_request_writes_the_data_model_shape() -> None:
    """The stored request holds every field of data-model.md section 4.3.

    Why:
        The status view and the audit trail both read this dictionary. One
        missing field breaks both readers, so the test compares the whole
        dictionary rather than single members.
    """
    records = _records()
    request = _new_store(records).request(RUN_ID, FIRST_ACTOR, STOP_CONFIRMATION_TEXT)
    assert _stored_stop_request(records) == {
        "requested_by": FIRST_ACTOR,
        "requested_at": request.requested_at,
        "confirmation_text": STOP_CONFIRMATION_TEXT,
        "scope": STOP_SCOPE_RUN,
        "outcome": None,
    }


def test_request_writes_a_fresh_updated_at() -> None:
    """The request replaces updated_at with a later ISO 8601 time.

    Why:
        data-model.md asks for a fresh time on every change. The status poll
        reads this field to decide whether the run moved.
    """
    records = _records()
    _store_with_request(records)
    written = str(records[RUN_ID]["updated_at"])
    assert datetime.fromisoformat(written) > datetime.fromisoformat(EARLIER_TIME)


def test_request_changes_only_the_stop_request_and_the_time() -> None:
    """The request leaves every other field of the run record alone.

    Why:
        The run state machine owns the move to the stopping state. The stop
        store must not race it, so the store writes two fields only.
    """
    records = _records()
    before = deepcopy(records[RUN_ID])
    _store_with_request(records)
    after = records[RUN_ID]
    assert {key for key in after if after[key] != before.get(key)} == {"stop_request", "updated_at"}


def test_request_does_not_add_a_state_field() -> None:
    """The request adds no state field to a record that holds none.

    Why:
        This proves the boundary by absence. Only the run state machine writes
        the state field, and it moves the run to stopping in its own step.
    """
    records = _records()
    del records[RUN_ID]["state"]  # The record now holds no state field at all
    _store_with_request(records)
    assert "state" not in records[RUN_ID]


def test_second_request_returns_the_first_request() -> None:
    """A second request returns the request the record already holds.

    Why:
        A double click must read as one stop. The second call therefore
        reports the first request instead of raising or writing again.
    """
    first, second = _double_request(_records())
    assert second == first


def test_second_request_keeps_the_first_owner() -> None:
    """The record keeps the first operator email after a second request.

    Why:
        FR-038h makes the request an audit record. A second click from a
        different operator must never rewrite the owner of that record.
    """
    records = _records()
    _double_request(records)
    stored = _stored_stop_request(records)
    assert stored["requested_by"] == FIRST_ACTOR
    assert SECOND_ACTOR not in json.dumps(records[RUN_ID])


def test_request_raises_when_the_run_is_absent() -> None:
    """An unknown run identifier raises the run not found error.

    Why:
        The contract answers 404 with the code run_not_found. The test asserts
        on the code, never on the message.
    """
    store = _new_store(_records())
    with pytest.raises(RunNotFoundError) as error:
        store.request(MISSING_RUN_ID, FIRST_ACTOR, STOP_CONFIRMATION_TEXT)
    assert error.value.code == "run_not_found"


@pytest.mark.parametrize("state", sorted(TERMINAL_RUN_STATES))
def test_request_raises_for_every_terminal_state(state: str) -> None:
    """A run in a final state raises the run not stoppable error.

    Why:
        The contract answers 409 with the code run_not_stoppable. Every state
        in TERMINAL_RUN_STATES must give the same answer.

    Args:
        state: One final run state from TERMINAL_RUN_STATES.
    """
    store = _new_store(_records(state))
    with pytest.raises(RunNotStoppableError) as error:
        store.request(RUN_ID, FIRST_ACTOR, STOP_CONFIRMATION_TEXT)
    assert error.value.code == "run_not_stoppable"


def test_is_stop_pending_is_false_before_a_request() -> None:
    """A run with no stop request reports no pending stop.

    Why:
        The run driver calls this once for each phase. A false positive would
        end an upgrade that no operator asked to stop.
    """
    assert _new_store(_records()).is_stop_pending(RUN_ID) is False


def test_is_stop_pending_is_true_after_a_request() -> None:
    """A run with a stop request reports a pending stop.

    Why:
        The run driver reads this flag to decide whether to start the next
        device. A false negative would ignore the operator.
    """
    records = _records()
    store = _store_with_request(records)
    assert store.is_stop_pending(RUN_ID) is True


def test_read_returns_the_stored_request() -> None:
    """The read returns the request the record holds.

    Why:
        The status view shows the owner and the time of the stop, so the read
        must rebuild the value from the stored dictionary.
    """
    records = _records()
    stored = _store_with_request(records).read(RUN_ID)
    assert stored is not None
    assert stored.requested_by == FIRST_ACTOR
    assert stored.scope == STOP_SCOPE_RUN


def test_a_second_store_instance_sees_the_request() -> None:
    """A second, separately built store over the same records sees the request.

    Why:
        This models two Gunicorn workers, and it is the property that replaces
        the old stop_loop.txt sentinel file. The store keeps no process-local
        state, so it reaches the record through the RunRecordStore protocol
        only. A request from one worker must arrive at the other worker.
    """
    records = _records()
    _store_with_request(records)  # The first worker records the request
    second_worker = _new_store(records)  # A separate store over the same records
    assert second_worker.is_stop_pending(RUN_ID) is True


def test_record_outcome_writes_the_outcome() -> None:
    """The outcome joins the request the record already holds.

    Why:
        FR-038e asks the portal to name each cancelled device and each device
        that continues. The outcome must reach the record without replacing
        the owner of the request.
    """
    records = _records()
    updated = _store_with_request(records).record_outcome(RUN_ID, SAMPLE_OUTCOME)
    assert updated.outcome == SAMPLE_OUTCOME
    assert updated.requested_by == FIRST_ACTOR
    assert _stored_stop_request(records)["outcome"] == SAMPLE_OUTCOME.to_record()
