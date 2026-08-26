"""Unit tests for the upgrade run record, the run key, and the run states.

Why:
    One upgrade run record must hold every field of the data model from the
    first write, because this feature deletes no record. A missing field or an
    illegal state move leaves a record that no operator can read months later.

    These tests hold their own copy of the twenty field names and of the state
    chain. Both copies come from ``specs/1823-upgrade-capture-portal/
    data-model.md`` section 4. A test that only repeated the module constants
    would still pass after a wrong edit of those constants, so the second copy
    is deliberate.

    Every test here runs offline. The module under test opens no socket and
    writes to no database.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Final

import pytest

from src.upgrade_portal.runtime.runs import (
    PHASE_ORDER,
    RUN_KEY_PREFIX,
    SCHEMA_VERSION,
    PhaseState,
    RunRecordBuilder,
    RunSpec,
    RunState,
    RunStateMachine,
    RunTransitionError,
)

# WHY: The twenty required fields of data-model.md section 4, lines 219 to 236.
# The test carries its own copy, so a field dropped from the module fails here.
DATA_MODEL_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "_key",
        "run_id",
        "schema_version",
        "org_id",
        "org_name",
        "site_id",
        "site_name",
        "actor_email",
        "browser_id",
        "created_at",
        "updated_at",
        "state",
        "tier",
        "targets",
        "options",
        "phases",
        "stop_request",
        "pre_capture_id",
        "post_capture_id",
        "error",
    },
)

# WHY: The one linear path of data-model.md section 4.1. Thirteen states give
# twelve forward moves.
DATA_MODEL_CHAIN: Final[tuple[str, ...]] = (
    "created",
    "pre_capture_running",
    "pre_capture_done",
    "awaiting_confirmation",
    "upgrade_submitting",
    "upgrade_running",
    "settling_gateways",
    "settling_switches",
    "settling_aps",
    "settling_clients",
    "post_capture_running",
    "post_capture_done",
    "complete",
)

# WHY: The data model says any live state may reach either of these two.
STOP_ROUTES: Final[tuple[str, str]] = ("stopping", "failed")

# WHY: The three states that sit off the linear chain.
OFF_CHAIN_STATES: Final[tuple[str, ...]] = ("stopping", "stopped", "failed")

# WHY: A finished run moves nowhere. The stop route reads this refusal.
TERMINAL_NAMES: Final[tuple[str, ...]] = ("complete", "stopped", "failed")

# WHY: The four states before firmware submission. A run in one of these has
# touched no device, so a fresh pre-check still describes the site before the
# upgrade. The test carries its own copy, so a slice that moves in the module
# fails here.
PRE_CHECK_OPEN_NAMES: Final[tuple[str, ...]] = (
    "created",
    "pre_capture_running",
    "pre_capture_done",
    "awaiting_confirmation",
)

# WHY: Every other state. A capture taken in one of these reads devices that the
# upgrade already touched, and a stopped or failed run must keep the reading it
# holds. No state here may replace a pre-check.
PRE_CHECK_CLOSED_NAMES: Final[tuple[str, ...]] = (
    "upgrade_submitting",
    "upgrade_running",
    "settling_gateways",
    "settling_switches",
    "settling_aps",
    "settling_clients",
    "post_capture_running",
    "post_capture_done",
    "complete",
    "stopping",
    "stopped",
    "failed",
)

# WHY: The two moves out of stopping.
STOPPING_MOVES: Final[tuple[tuple[str, str], ...]] = (
    ("stopping", "stopped"),
    ("stopping", "failed"),
)

# WHY: Twelve forward moves, twenty-four stop or fail moves, two moves out of
# stopping. The model must offer these and no others.
EXPECTED_MOVE_TOTAL: Final[int] = 38

# WHY: A move that the model forbids. Each pair skips a step, reverses a step,
# repeats a state, or leaves the stop route.
ILLEGAL_MOVES: Final[tuple[tuple[str, str], ...]] = (
    ("created", "complete"),
    ("created", "created"),
    ("created", "upgrade_running"),
    ("pre_capture_running", "created"),
    ("settling_gateways", "settling_aps"),
    ("post_capture_done", "post_capture_running"),
    ("stopping", "stopping"),
    ("stopping", "upgrade_running"),
)

# WHY: One target row of the operator input. The builder copies it unchanged.
SAMPLE_TARGET: Final[dict[str, Any]] = {
    "mac": "5c5b350e0001",
    "name": "switch-one",
    "device_type": "switch",
    "version_before": "21.4R3-S5",
    "version_target": "23.4R2-S3",
}

# WHY: The upgrade options of the operator. The builder copies them unchanged.
SAMPLE_OPTIONS: Final[dict[str, Any]] = {"reboot": True, "start_time": None}

# WHY: The seven values the operator supplies, and the value each field holds.
OPERATOR_VALUES: Final[tuple[tuple[str, Any], ...]] = (
    ("org_id", "org-0001"),
    ("org_name", "Example Organization"),
    ("site_id", "site-0001"),
    ("site_name", "Example Site"),
    ("actor_email", "operator@example.com"),
    ("browser_id", "browser-0001"),
    ("tier", 2),
)

# WHY: Each of these fields starts as null rather than absent.
NULL_FIELDS: Final[tuple[str, ...]] = (
    "stop_request",
    "pre_capture_id",
    "post_capture_id",
    "error",
)

# WHY: An obviously old time. A test writes it, then proves a move replaced it.
OLD_TIME: Final[str] = "2020-01-01T00:00:00+00:00"

# WHY: The key reads the four character prefix and a uuid4 hexadecimal value.
KEY_BODY_LENGTH: Final[int] = 32
KEY_LENGTH: Final[int] = 36


def _forward_moves() -> list[tuple[str, str]]:
    """Return the twelve one-step moves along the linear chain.

    Why:
        The chain is the spine of the run. Each member may move only to the
        member that follows it.

    Returns:
        Twelve pairs of a start state and a target state.
    """
    return list(zip(DATA_MODEL_CHAIN[:-1], DATA_MODEL_CHAIN[1:], strict=True))


def _escape_moves() -> list[tuple[str, str]]:
    """Return every move from a live chain state to stopping or to failed.

    Why:
        The data model allows a stop and a failure from any live state. The
        twelve live chain states give twenty-four moves.

    Returns:
        Twenty-four pairs of a start state and a target state.
    """
    live_states = DATA_MODEL_CHAIN[:-1]
    return [(start, target) for start in live_states for target in STOP_ROUTES]


# WHY: Every move the data model allows. The count must read thirty-eight.
LEGAL_MOVES: Final[tuple[tuple[str, str], ...]] = tuple(
    _forward_moves() + _escape_moves() + list(STOPPING_MOVES),
)

# WHY: A readable test name for each of the thirty-eight moves.
MOVE_IDS: Final[list[str]] = [f"{start}_to_{target}" for start, target in LEGAL_MOVES]


def _spec(tier: int = 2) -> RunSpec:
    """Return one operator specification for a test run.

    Why:
        Every test that needs a record needs the same nine operator values.
        One helper keeps those values in one place.

    Args:
        tier: The capture tier for both captures.

    Returns:
        A specification that holds fixed sample values.
    """
    return RunSpec(
        org_id="org-0001",
        org_name="Example Organization",
        site_id="site-0001",
        site_name="Example Site",
        actor_email="operator@example.com",
        browser_id="browser-0001",
        tier=tier,
        targets=(SAMPLE_TARGET,),
        options=SAMPLE_OPTIONS,
    )


def _record(spec: RunSpec | None = None) -> dict[str, Any]:
    """Return one freshly built run record.

    Why:
        Most tests need a valid record and do not care about the operator
        values. One helper keeps the build call in one place.

    Args:
        spec: The operator choices. The helper builds a default one when the
            caller passes none.

    Returns:
        A new run record in the created state.
    """
    return RunRecordBuilder().build(spec or _spec())


def _record_in(state: str) -> dict[str, Any]:
    """Return one run record that already holds the named state.

    Why:
        The state machine refuses an illegal move, so a test cannot walk the
        chain to reach a terminal start state. This helper writes the state
        straight into the record, which is the shape the store reads back.

    Args:
        state: The state name the record must hold.

    Returns:
        A run record in that state.
    """
    record = _record()
    record["state"] = state
    return record


def _parsed_time(value: str) -> datetime:
    """Return one stored time as a datetime.

    Why:
        Several tests read a stored time. One helper keeps the parse in one
        place and fails with a clear error on malformed text.

    Args:
        value: The stored time as ISO 8601 text.

    Returns:
        The parsed time, with the time zone the text carried.
    """
    return datetime.fromisoformat(value)


def test_build_writes_every_data_model_field() -> None:
    """The new record holds the twenty data model fields, and no other field.

    Why:
        A field written at a later stage would leave every older record
        without it. This test names the exact defect the record must not hold.
    """
    record = _record()
    assert set(record) == DATA_MODEL_FIELDS
    assert len(record) == 20


def test_the_required_field_list_matches_the_data_model() -> None:
    """The module field list agrees with the data model field list.

    Why:
        The builder validates against its own list. A wrong list would accept
        a record that the data model rejects.
    """
    assert set(RunRecordBuilder.REQUIRED_FIELDS) == DATA_MODEL_FIELDS
    assert len(RunRecordBuilder.REQUIRED_FIELDS) == len(DATA_MODEL_FIELDS)


def test_schema_version_is_the_integer_one() -> None:
    """The record holds the integer 1, never the text and never a boolean.

    Why:
        Python treats True as equal to 1, so a plain equality check passes for
        a boolean. A reader of a stored record needs the integer.
    """
    version = _record()["schema_version"]
    assert type(version) is int
    assert version == 1
    assert version == SCHEMA_VERSION


def test_run_id_repeats_the_key() -> None:
    """The record holds the same value in run_id and in _key.

    Why:
        run_id is the natural business key. A reader that holds one value can
        find the record by either name.
    """
    record = _record()
    assert record["run_id"] == record["_key"]


def test_the_times_are_iso_8601_in_utc() -> None:
    """The creation time and the update time read as ISO 8601 in UTC.

    Why:
        A local time reads wrong in another time zone. A naive value gives no
        clue which zone the writer used.
    """
    record = _record()
    assert record["created_at"] == record["updated_at"]
    for value in (record["created_at"], record["updated_at"]):
        parsed = _parsed_time(str(value))
        assert parsed.tzinfo is not None
        assert parsed.utcoffset() == timedelta(0)


@pytest.mark.parametrize(("field_name", "expected"), OPERATOR_VALUES)
def test_build_copies_the_operator_values(field_name: str, expected: Any) -> None:
    """The record repeats each value the operator supplied.

    Why:
        An operator reads the organization and the site months after the work.
        A wrong copy would name the wrong site.

    Args:
        field_name: The record field under test.
        expected: The value the specification carried.
    """
    assert _record()[field_name] == expected


@pytest.mark.parametrize("field_name", NULL_FIELDS)
def test_build_starts_the_progress_fields_as_null(field_name: str) -> None:
    """Each progress field starts as null rather than absent.

    Why:
        A reader never has to tell a missing key from an empty value.

    Args:
        field_name: The progress field under test.
    """
    assert _record()[field_name] is None


def test_build_opens_the_record_in_the_created_state() -> None:
    """A new record holds the first state of the chain.

    Why:
        The run starts before the pre-check capture. Any other first state
        would let the run skip a step.
    """
    assert _record()["state"] == RunState.CREATED.value
    assert _record()["state"] == DATA_MODEL_CHAIN[0]


def test_build_copies_each_target_entry() -> None:
    """The record holds a copy of each target, never the caller dictionary.

    Why:
        A later edit of the operator input must never reach a stored record.
    """
    record = _record()
    assert record["targets"] == [SAMPLE_TARGET]
    assert record["targets"][0] is not SAMPLE_TARGET


def test_build_copies_the_options() -> None:
    """The record holds a copy of the upgrade options.

    Why:
        A later edit of the operator input must never reach a stored record.
    """
    record = _record()
    assert record["options"] == SAMPLE_OPTIONS
    assert record["options"] is not SAMPLE_OPTIONS


def test_build_accepts_the_tier_three_capture() -> None:
    """The record carries the tier the operator chose.

    Why:
        The tier decides how much the two captures read. A wrong tier would
        make the comparison read the wrong data.
    """
    assert _record(_spec(tier=3))["tier"] == 3


def test_two_records_hold_different_keys() -> None:
    """Two builds never mint the same key.

    Why:
        A repeated key would overwrite an earlier run, and this feature
        deletes no record.
    """
    builder = RunRecordBuilder()
    assert builder.build(_spec())["_key"] != builder.build(_spec())["_key"]


def test_initial_phases_follow_the_cascade_order() -> None:
    """The four phases read in the fixed cascade order.

    Why:
        The physical dependency of a site fixes this order. Everything sits
        downstream of the gateways.
    """
    names = [entry["name"] for entry in RunRecordBuilder.initial_phases()]
    assert names == list(PHASE_ORDER)
    assert names == ["gateways", "switches", "aps", "clients"]


def test_each_initial_phase_is_pending_with_empty_counts() -> None:
    """Every phase starts pending, with no settled device and no total.

    Why:
        The record holds the four phases from the first moment, so the status
        body never has to invent one.
    """
    for entry in RunRecordBuilder.initial_phases():
        assert entry["state"] == PhaseState.PENDING.value
        assert entry["settled"] == 0
        assert entry["total"] == 0
        assert entry["settled_at"] is None
        assert entry["note"] == ""  # Empty text, never null. The page prints this value.


def test_each_initial_phase_holds_the_six_contract_keys() -> None:
    """Every phase entry carries the same six keys.

    Why:
        The page reads one shape only. A missing key would break the render.
    """
    expected = {"name", "state", "settled", "total", "settled_at", "note"}
    for entry in RunRecordBuilder.initial_phases():
        assert set(entry) == expected


def test_the_record_holds_the_initial_phases() -> None:
    """The new record carries the four pending phases.

    Why:
        The builder writes the phases at creation, so no stage meets a
        missing phase list.
    """
    assert _record()["phases"] == RunRecordBuilder.initial_phases()


@pytest.mark.parametrize("field_name", sorted(DATA_MODEL_FIELDS))
def test_validate_rejects_a_record_that_misses_a_field(field_name: str) -> None:
    """A record without one required field never reaches the store.

    Why:
        A record that reaches the store with a missing field stays wrong
        forever, because this feature deletes no record.

    Args:
        field_name: The required field the test removes.
    """
    record = _record()
    del record[field_name]
    with pytest.raises(ValueError, match="misses these fields"):
        RunRecordBuilder.validate(record)


def test_validate_accepts_a_fresh_record() -> None:
    """A record straight from the builder passes its own validation.

    Why:
        The builder validates before it returns. This test proves the two
        agree, so a valid build never raises.
    """
    RunRecordBuilder.validate(_record())


@pytest.mark.parametrize("version", [0, 2, "1"])
def test_validate_rejects_a_wrong_schema_version(version: object) -> None:
    """A record with another schema version never reaches the store.

    Why:
        A reader that finds a higher number refuses to render and says so.

    Args:
        version: The wrong schema version the test writes.
    """
    record = _record()
    record["schema_version"] = version
    with pytest.raises(ValueError, match="schema_version"):
        RunRecordBuilder.validate(record)


@pytest.mark.parametrize("tier", [0, 1, 4, "2"])
def test_validate_rejects_a_tier_outside_the_model(tier: object) -> None:
    """A record with another tier never reaches the store.

    Why:
        The portal reads a tier 2 capture or a tier 3 capture. No other tier
        has a reader.

    Args:
        tier: The wrong tier the test writes.
    """
    record = _record()
    record["tier"] = tier
    with pytest.raises(ValueError, match="tier"):
        RunRecordBuilder.validate(record)


def test_validate_rejects_a_run_id_that_differs_from_the_key() -> None:
    """A record with two different identifiers never reaches the store.

    Why:
        A reader that searches by run_id must find the same record that the
        key names.
    """
    record = _record()
    record["run_id"] = RunRecordBuilder.new_key()
    with pytest.raises(ValueError, match="run_id must match"):
        RunRecordBuilder.validate(record)


@pytest.mark.parametrize(
    "key",
    ["run-abc", "cap-" + "0" * 32, "run-" + "g" * 32, "run-" + "0" * 33, "0" * 32],
)
def test_validate_rejects_a_key_outside_the_pattern(key: str) -> None:
    """A key of another shape never reaches the store.

    Why:
        A key of any other shape breaks the read-back check of the store.

    Args:
        key: The wrong key the test writes.
    """
    record = _record()
    record["_key"] = key
    record["run_id"] = key
    with pytest.raises(ValueError, match="hexadecimal"):
        RunRecordBuilder.validate(record)


def test_new_key_matches_the_key_pattern() -> None:
    """A fresh key matches the pattern the store expects.

    Why:
        The store reads the key back to prove the write. A key of another
        shape breaks that check.
    """
    key = RunRecordBuilder.new_key()
    assert RunRecordBuilder.KEY_PATTERN.fullmatch(key) is not None
    assert key.startswith(RUN_KEY_PREFIX)


def test_new_key_is_thirty_six_characters() -> None:
    """A fresh key reads the prefix and thirty-two hexadecimal characters.

    Why:
        A shorter body would raise the chance of a repeated key.
    """
    key = RunRecordBuilder.new_key()
    assert len(key) == KEY_LENGTH
    assert len(key) == len(RUN_KEY_PREFIX) + KEY_BODY_LENGTH


def test_new_key_holds_no_hyphen_after_the_prefix() -> None:
    """The body of the key carries no separator.

    Why:
        The key comes from the hexadecimal form of a uuid4 value, which
        carries no separator. A separator would break the key pattern.
    """
    body = RunRecordBuilder.new_key()[len(RUN_KEY_PREFIX) :]
    assert "-" not in body
    assert len(body) == KEY_BODY_LENGTH
    assert body == body.lower()


def test_new_key_returns_a_fresh_value_every_call() -> None:
    """One hundred calls return one hundred different keys.

    Why:
        A random value needs no counter and no round trip to the database, so
        two workers never mint the same key.
    """
    keys = {RunRecordBuilder.new_key() for _ in range(100)}
    assert len(keys) == 100


def test_the_state_list_matches_the_data_model() -> None:
    """The model holds the sixteen states of the data model, and no other.

    Why:
        A closed set of names keeps a stored record readable years after the
        work.
    """
    names = {state.value for state in RunState}
    assert names == set(DATA_MODEL_CHAIN) | set(OFF_CHAIN_STATES)
    assert len(RunState) == 16


def test_the_module_chain_matches_the_data_model() -> None:
    """The module chain repeats the linear path of the data model.

    Why:
        A reordered chain would let a run settle the access points before the
        switches, which the physical dependency of a site forbids.
    """
    module_chain = tuple(state.value for state in RunStateMachine.CHAIN)
    assert module_chain == DATA_MODEL_CHAIN
    assert len(module_chain) == 13


def test_the_terminal_states_match_the_data_model() -> None:
    """The three final states are complete, stopped, and failed.

    Why:
        The stop route answers run_not_stoppable for each of these three
        states.
    """
    assert {state.value for state in RunStateMachine.TERMINAL} == set(TERMINAL_NAMES)


def test_the_forward_chain_reaches_complete() -> None:
    """A run walks the twelve forward steps from created to complete.

    Why:
        A run that could not reach the end would strand the operator. This
        test walks the whole spine of the model in one pass.
    """
    machine = RunStateMachine()
    record = _record()
    visited = [str(record["state"])]
    for target in DATA_MODEL_CHAIN[1:]:
        machine.advance(record, target)
        visited.append(str(record["state"]))
    assert visited == list(DATA_MODEL_CHAIN)
    assert len(visited) - 1 == 12


@pytest.mark.parametrize(("start", "target"), LEGAL_MOVES, ids=MOVE_IDS)
def test_every_legal_move_is_allowed(start: str, target: str) -> None:
    """The state machine performs each of the thirty-eight legal moves.

    Why:
        A dropped edge leaves a run stuck with no way forward. This test runs
        every move the data model allows, so a dropped edge fails loudly.

    Args:
        start: The state the record holds before the move.
        target: The state the record holds after the move.
    """
    record = _record_in(start)
    RunStateMachine().advance(record, target)
    assert record["state"] == target


def test_the_model_allows_exactly_thirty_eight_moves() -> None:
    """The whole model offers thirty-eight moves, and no more.

    Why:
        The parametrized move test catches a dropped edge. This test catches
        an added edge, because it counts every edge the model offers.
    """
    total = sum(len(RunStateMachine.allowed_next(state)) for state in RunState)
    assert total == EXPECTED_MOVE_TOTAL
    assert len(LEGAL_MOVES) == EXPECTED_MOVE_TOTAL
    assert len(set(LEGAL_MOVES)) == EXPECTED_MOVE_TOTAL


@pytest.mark.parametrize("state", list(RunState))
def test_allowed_next_matches_the_legal_move_list(state: RunState) -> None:
    """Each state offers exactly the targets the data model allows.

    Why:
        A count alone would hide a move that landed on the wrong target. This
        test compares the target names for every one of the sixteen states.

    Args:
        state: The state under test.
    """
    expected = {target for start, target in LEGAL_MOVES if start == state.value}
    actual = {member.value for member in RunStateMachine.allowed_next(state)}
    assert actual == expected


@pytest.mark.parametrize("state_name", TERMINAL_NAMES)
def test_a_terminal_state_allows_no_move(state_name: str) -> None:
    """A finished run moves nowhere, so every move out of it raises.

    Why:
        The stop route reads this refusal to answer run_not_stoppable. A
        finished run that still moved would corrupt a stored record.

    Args:
        state_name: The final state the record holds.
    """
    record = _record_in(state_name)
    assert RunStateMachine.allowed_next(RunState(state_name)) == frozenset()
    with pytest.raises(RunTransitionError, match="cannot move"):
        RunStateMachine().advance(record, RunState.STOPPING)
    assert record["state"] == state_name


@pytest.mark.parametrize(("start", "target"), ILLEGAL_MOVES)
def test_an_illegal_move_raises(start: str, target: str) -> None:
    """A move that skips, reverses, or repeats a state raises.

    Why:
        A silent illegal move leaves a stored record that no reader can
        explain months later.

    Args:
        start: The state the record holds.
        target: The state the caller asked for.
    """
    record = _record_in(start)
    with pytest.raises(RunTransitionError, match="cannot move"):
        RunStateMachine().advance(record, target)
    assert record["state"] == start


def test_advance_updates_the_update_time() -> None:
    """Every move writes a fresh update time in UTC.

    Why:
        An operator reads the update time to see when the run last moved. A
        stale value would hide a stuck run.
    """
    record = _record()
    record["updated_at"] = OLD_TIME
    RunStateMachine().advance(record, RunState.PRE_CAPTURE_RUNNING)
    assert record["updated_at"] != OLD_TIME
    assert _parsed_time(str(record["updated_at"])).utcoffset() == timedelta(0)


def test_advance_keeps_the_creation_time() -> None:
    """A move never rewrites the creation time.

    Why:
        The creation time reports when the operator started the work. Only
        the update time follows the moves.
    """
    record = _record()
    created = record["created_at"]
    RunStateMachine().advance(record, RunState.PRE_CAPTURE_RUNNING)
    assert record["created_at"] == created


def test_advance_accepts_a_plain_state_name() -> None:
    """A caller may name the target state as plain text.

    Why:
        The routes and the driver pass plain text from a request body.
    """
    record = _record()
    returned = RunStateMachine().advance(record, "pre_capture_running")
    assert record["state"] == RunState.PRE_CAPTURE_RUNNING.value
    assert returned is record


def test_advance_rejects_a_name_outside_the_model() -> None:
    """A target name that no state carries raises at the edge.

    Why:
        A name outside the model must fail here and must never reach the
        store.
    """
    record = _record()
    with pytest.raises(RunTransitionError, match="not a run state"):
        RunStateMachine().advance(record, "settling_printers")
    assert record["state"] == RunState.CREATED.value


def test_coerce_accepts_a_member_and_a_name() -> None:
    """The helper returns the same member for a member and for its name.

    Why:
        The driver holds members and the routes hold text. Both callers need
        one answer.
    """
    assert RunStateMachine.coerce("complete") is RunState.COMPLETE
    assert RunStateMachine.coerce(RunState.COMPLETE) is RunState.COMPLETE


def test_coerce_rejects_a_name_outside_the_model() -> None:
    """A name that no state carries raises a run transition error.

    Why:
        The caller catches one error class for every refusal of this module.
    """
    with pytest.raises(RunTransitionError, match="not a run state"):
        RunStateMachine.coerce("settling_printers")


def test_read_state_returns_the_stored_state() -> None:
    """The helper reads the state a record holds.

    Why:
        Every move starts from the stored state, so a wrong read would allow
        a wrong move.
    """
    assert RunStateMachine.read_state(_record()) is RunState.CREATED


def test_read_state_rejects_a_record_with_no_state() -> None:
    """A record without a state raises rather than guesses.

    Why:
        A guessed state would let the run move from a place it never held.
    """
    with pytest.raises(RunTransitionError, match="not a run state"):
        RunStateMachine.read_state({})


def test_the_open_set_holds_only_the_states_before_submission() -> None:
    """The open set names the four states that precede firmware submission.

    Why:
        The module derives this set by slicing the chain. A slice that moved by
        one would let a capture taken after submission replace the pre-check,
        and the comparison would then measure the upgraded site against itself.
    """
    names = {state.value for state in RunStateMachine.PRE_CHECK_OPEN}
    assert names == set(PRE_CHECK_OPEN_NAMES)


def test_the_two_name_groups_cover_every_state() -> None:
    """Every state of the model sits in exactly one of the two test groups.

    Why:
        A state added to the model without a place here would go untested, and
        the untested answer is the one that destroys the pre-check.
    """
    open_names = set(PRE_CHECK_OPEN_NAMES)
    closed_names = set(PRE_CHECK_CLOSED_NAMES)
    assert open_names & closed_names == set()
    assert open_names | closed_names == {state.value for state in RunState}


@pytest.mark.parametrize("state_name", PRE_CHECK_OPEN_NAMES)
def test_pre_check_replaceable_allows_a_run_before_submission(state_name: str) -> None:
    """A run that sent no firmware may still name a different pre-check.

    Why:
        An operator who reviews a capture and wants the extra tier may take the
        pre-check again. The newer reading is the better one, because no device
        has changed.

    Args:
        state_name: The state the run record holds.
    """
    assert RunStateMachine.pre_check_replaceable(_record_in(state_name)) is True


@pytest.mark.parametrize("state_name", PRE_CHECK_CLOSED_NAMES)
def test_pre_check_replaceable_refuses_a_run_from_submission_onward(state_name: str) -> None:
    """A run that reached firmware submission keeps the pre-check it named.

    Why:
        A capture read after submission reads upgraded devices. It would replace
        the only reading of the site before the upgrade, and the comparison
        would then report no change at all.

    Args:
        state_name: The state the run record holds.
    """
    assert RunStateMachine.pre_check_replaceable(_record_in(state_name)) is False


def test_pre_check_replaceable_refuses_a_record_with_no_state() -> None:
    """A record that names no state answers False rather than raising.

    Why:
        The caller runs inside a capture worker thread. An unreadable stage
        cannot prove a replacement is safe, so the stored pre-check stays.
    """
    assert RunStateMachine.pre_check_replaceable({}) is False


def test_pre_check_replaceable_refuses_a_state_outside_the_model() -> None:
    """A state name the model never held answers False.

    Why:
        A record written by a newer version of the portal may name a stage this
        one cannot read. The safe answer keeps the reading that exists.
    """
    assert RunStateMachine.pre_check_replaceable({"state": "settling_printers"}) is False


def test_fail_writes_the_error_object() -> None:
    """A failed run holds the stage, the message, and the time of the failure.

    Why:
        A failed run with no reason gives the operator nothing to act on. The
        error time repeats the update time, so the two agree.
    """
    record = _record()
    RunStateMachine().fail(record, "post_capture", "The cloud refused the read.")
    assert record["state"] == RunState.FAILED.value
    assert record["error"] == {
        "stage": "post_capture",
        "message": "The cloud refused the read.",
        "at": record["updated_at"],
    }


def test_fail_refuses_a_finished_run() -> None:
    """A run that already finished cannot fail again.

    Why:
        A second write would replace the record of the first outcome.
    """
    record = _record_in("complete")
    with pytest.raises(RunTransitionError, match="cannot move"):
        RunStateMachine().fail(record, "post_capture", "Too late.")
    assert record["state"] == "complete"
    assert record["error"] is None


def test_a_skipped_phase_keeps_the_settling_state_in_the_chain() -> None:
    """A site with no gateway still passes through the gateway settle state.

    Why:
        FR-058 asks the portal to skip a settle gate when the site holds no
        device of that family. The module answers with the phase state
        skipped and keeps the chain literal. This test pins that reading.
    """
    machine = RunStateMachine()
    record = _record_in("upgrade_running")
    record["phases"][0]["state"] = PhaseState.SKIPPED.value
    machine.advance(record, RunState.SETTLING_GATEWAYS)
    assert record["state"] == RunState.SETTLING_GATEWAYS.value
    assert record["phases"][0]["state"] == PhaseState.SKIPPED.value
    with pytest.raises(RunTransitionError, match="cannot move"):
        machine.advance(record, RunState.SETTLING_APS)


def test_the_specification_holds_the_model_defaults() -> None:
    """A specification without options starts at tier 2 with no target.

    Why:
        The operator picks the versions later, so the run starts with an
        empty target list.
    """
    spec = RunSpec(
        org_id="org-0001",
        org_name="Example Organization",
        site_id="site-0001",
        site_name="Example Site",
        actor_email="operator@example.com",
        browser_id="browser-0001",
    )
    assert spec.tier == 2
    assert spec.targets == ()
    assert spec.options == {}


def test_the_specification_refuses_an_edit() -> None:
    """The specification is frozen and carries slots.

    Why:
        No stage may change the operator input after the run starts. The
        slots also stop a typing mistake that would add an unread attribute.
    """
    spec = _spec()
    attribute = "tier"
    with pytest.raises(AttributeError):
        setattr(spec, attribute, 3)
    assert not hasattr(spec, "__dict__")
