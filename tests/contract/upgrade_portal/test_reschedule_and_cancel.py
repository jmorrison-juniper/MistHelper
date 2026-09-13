"""Contract tests for the reschedule and the cancel of a run that has not begun.

Why:
    Issue #2201 records the gap. An operator who takes over a site could start a
    run and stop a run. That operator could not move a run that had not begun,
    and could not end one that would never begin. A scheduled run therefore held
    its moment whatever the new operator needed.

    The two controls reach a run before the submission alone. A run that already
    sent firmware needs the stop control, which cancels the work that the cloud
    holds and names each device that is past the point of a cancel.

Fixtures:
    Every fixture lives in this file, which follows `test_upgrade_stop.py`.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.upgrade_portal.runtime import identity
from src.upgrade_portal.runtime.runs import RunState, RunStateMachine

# --------------------------------------------------------------------------
# The contract values.
# --------------------------------------------------------------------------

RUN_STORE_KEY = "RUN_STORE"  # The seam that holds the run record store.
LOCK_READER_KEY = "SITE_LOCK_READER"  # The seam that reads the site lock.

PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.
OTHER_EMAIL = "other.operator@example.invalid"  # The operator who holds the site in the refusal test.
ORG_ID = "00000000-0000-0000-0000-0000000000aa"
SITE_ID = "00000000-0000-0000-0000-0000000000bb"

SELECTED_ORG_SESSION_KEY = "selected_org_id"
SELECTED_SITE_SESSION_KEY = "selected_site_id"

RESCHEDULE_TEMPLATE = "/api/runs/{run_id}/reschedule"
CANCEL_TEMPLATE = "/api/runs/{run_id}/cancel"
UNKNOWN_RUN_ID = "run-00000000000000000000000000000000"

OK_STATUS = 200
BAD_REQUEST_STATUS = 400
NOT_AUTHENTICATED_STATUS = 401
NOT_FOUND_STATUS = 404
CONFLICT_STATUS = 409

RUN_NOT_FOUND_CODE = "run_not_found"
SITE_LOCKED_CODE = "site_locked"
ALREADY_STARTED_CODE = "run_already_started"
BAD_OPTION_CODE = "bad_option"

# Every state before the submission. Each one holds a plan and nothing that the
# cloud has seen, so both controls reach it.
OPEN_STATES = ("created", "pre_capture_running", "pre_capture_done", "awaiting_confirmation")

# Every state at or past the submission. Each one needs the stop control.
STARTED_STATES = ("upgrade_submitting", "upgrade_running", "settling_gateways", "complete", "failed")


class RecordingRunStore:
    """Holds every run record of one test in one dictionary."""

    def __init__(self) -> None:
        """Start with no run record and with writes allowed."""
        self.runs: dict[str, dict[str, Any]] = {}  # One entry for each run the test seeds.
        self.refuse_writes = False  # A test raises this flag to act out a dead store.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one run record, or None when no run holds the identifier.

        Args:
            run_id: The run key.

        Returns:
            A copy of the record, or None.
        """
        held = self.runs.get(run_id)
        return dict(held) if held is not None else None

    def write_run(self, run: dict[str, Any]) -> bool:
        """Write one run record and report the true result.

        Args:
            run: The whole record.

        Returns:
            True, or False while the test holds the refusal flag.
        """
        if self.refuse_writes:
            return False
        self.runs[str(run["run_id"])] = dict(run)
        return True


@pytest.fixture(name="run_store")
def fixture_run_store() -> RecordingRunStore:
    """Return a fresh run record store.

    Returns:
        An empty recording store.
    """
    return RecordingRunStore()


@pytest.fixture(name="upgrade_app")
def fixture_upgrade_app(portal_app: Flask, run_store: RecordingRunStore) -> Flask:
    """Return the portal application with the run store injected.

    Args:
        portal_app: The real application from the shared fixture.
        run_store: The stand-in run record store.

    Returns:
        The application with the seams in place.
    """
    portal_app.config[RUN_STORE_KEY] = run_store  # No ArangoDB server runs in a contract test.
    portal_app.config[LOCK_READER_KEY] = lambda org, sites: dict.fromkeys(sites)  # Every site reads free.
    portal_app.config["WTF_CSRF_ENABLED"] = False
    return portal_app


@pytest.fixture(name="registered_owner")
def fixture_registered_owner() -> Iterator[identity.SessionOwner]:
    """Register one operator and drop the record when the test ends.

    Yields:
        The identity pair of the registered operator.
    """
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())
    record = identity.OperatorSession(
        owner=owner,
        cloud_session=object(),
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
    )
    identity.SESSION_REGISTRY.register(record)
    try:
        yield owner
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)


@pytest.fixture(name="client")
def fixture_client(upgrade_app: Flask, registered_owner: identity.SessionOwner) -> Iterator[FlaskClient]:
    """Return a signed-in client that already picked the organization and the site.

    Args:
        upgrade_app: The application with the seams injected.
        registered_owner: The identity pair of the registered operator.

    Yields:
        The Flask test client.
    """
    with upgrade_app.test_client() as test_client:
        test_client.set_cookie(identity.BROWSER_ID_COOKIE, registered_owner.browser_id)
        with test_client.session_transaction() as browser_session:
            browser_session[identity.SESSION_OWNER_KEY] = registered_owner.key
            browser_session[SELECTED_ORG_SESSION_KEY] = ORG_ID
            browser_session[SELECTED_SITE_SESSION_KEY] = SITE_ID
        yield test_client


def seed(store: RecordingRunStore, state: str, run_id: str = "run-abc") -> str:
    """Write one run record in a chosen state.

    Args:
        store: The recording store.
        state: The state the run holds.
        run_id: The run key.

    Returns:
        The run key.
    """
    store.runs[run_id] = {
        "run_id": run_id,
        "org_id": ORG_ID,
        "site_id": SITE_ID,
        "state": state,
        "options": {"strategy": "big_bang"},
    }
    return run_id


# ---------------------------------------------------------------------------
# The reschedule
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", OPEN_STATES)
def test_an_operator_reschedules_a_run_that_has_not_begun(
    client: FlaskClient, run_store: RecordingRunStore, state: str
) -> None:
    """Every state before the submission accepts a new start moment.

    Args:
        client: The signed-in client.
        run_store: The recording store.
        state: The run state under test.
    """
    run_id = seed(run_store, state)
    answer = client.post(RESCHEDULE_TEMPLATE.format(run_id=run_id), json={"start_time": "8h"})
    assert answer.status_code == OK_STATUS
    assert answer.get_json()["starts_in_seconds"] == 8 * 60 * 60


def test_the_new_duration_counts_from_the_moment_of_the_reschedule(
    client: FlaskClient, run_store: RecordingRunStore
) -> None:
    """A duration measured from a stale moment would fire at an hour nobody chose.

    Why:
        An operator who writes `8h` means eight hours from now. The original
        start may sit far in the past, and a duration added to it would name a
        moment that already passed.

    Args:
        client: The signed-in client.
        run_store: The recording store.
    """
    run_id = seed(run_store, "awaiting_confirmation")
    run_store.runs[run_id]["options"]["start_time"] = 1  # A stale moment at the start of the epoch.
    before = int(time.time())
    answer = client.post(RESCHEDULE_TEMPLATE.format(run_id=run_id), json={"start_time": "300s"})
    saved = int(answer.get_json()["start_time"])
    assert before + 300 <= saved <= int(time.time()) + 300  # The moment counts from now, not from the stale value.


def test_a_reschedule_keeps_every_other_option(client: FlaskClient, run_store: RecordingRunStore) -> None:
    """The run keeps its plan, because only the moment changed.

    Args:
        client: The signed-in client.
        run_store: The recording store.
    """
    run_id = seed(run_store, "awaiting_confirmation")
    client.post(RESCHEDULE_TEMPLATE.format(run_id=run_id), json={"start_time": "1h"})
    assert run_store.runs[run_id]["options"]["strategy"] == "big_bang"


def test_a_reschedule_refuses_a_duration_with_no_unit(client: FlaskClient, run_store: RecordingRunStore) -> None:
    """The duration reader owns the form, so the route repeats no rule.

    Args:
        client: The signed-in client.
        run_store: The recording store.
    """
    run_id = seed(run_store, "awaiting_confirmation")
    answer = client.post(RESCHEDULE_TEMPLATE.format(run_id=run_id), json={"start_time": "300"})
    assert answer.status_code == BAD_REQUEST_STATUS
    assert answer.get_json()["error"]["code"] == BAD_OPTION_CODE


@pytest.mark.parametrize("state", STARTED_STATES)
def test_a_reschedule_never_reaches_a_run_that_started(
    client: FlaskClient, run_store: RecordingRunStore, state: str
) -> None:
    """A run that sent firmware needs the stop control.

    Args:
        client: The signed-in client.
        run_store: The recording store.
        state: The run state under test.
    """
    run_id = seed(run_store, state)
    answer = client.post(RESCHEDULE_TEMPLATE.format(run_id=run_id), json={"start_time": "1h"})
    assert answer.status_code == CONFLICT_STATUS
    assert answer.get_json()["error"]["code"] == ALREADY_STARTED_CODE


def test_a_reschedule_names_the_operator(client: FlaskClient, run_store: RecordingRunStore) -> None:
    """The record names who moved the schedule, through the digest.

    Warning: no record may hold the address itself. The trail names people, and
    the portal stores a one-way digest for that reason.

    Args:
        client: The signed-in client.
        run_store: The recording store.
    """
    run_id = seed(run_store, "awaiting_confirmation")
    client.post(RESCHEDULE_TEMPLATE.format(run_id=run_id), json={"start_time": "1h"})
    digest = run_store.runs[run_id]["rescheduled_by"]
    assert digest  # The record names the operator.
    assert PROBE_EMAIL not in digest  # It never names the address.


# ---------------------------------------------------------------------------
# The cancel
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", OPEN_STATES)
def test_an_operator_cancels_a_run_that_has_not_begun(
    client: FlaskClient, run_store: RecordingRunStore, state: str
) -> None:
    """Every state before the submission accepts a cancel.

    Args:
        client: The signed-in client.
        run_store: The recording store.
        state: The run state under test.
    """
    run_id = seed(run_store, state)
    answer = client.post(CANCEL_TEMPLATE.format(run_id=run_id), json={})
    assert answer.status_code == OK_STATUS
    assert answer.get_json()["state"] == RunState.CANCELLED.value


@pytest.mark.parametrize("state", STARTED_STATES)
def test_a_cancel_never_reaches_a_run_that_started(
    client: FlaskClient, run_store: RecordingRunStore, state: str
) -> None:
    """A run that sent firmware needs the stop control, which reaches the cloud.

    Args:
        client: The signed-in client.
        run_store: The recording store.
        state: The run state under test.
    """
    run_id = seed(run_store, state)
    answer = client.post(CANCEL_TEMPLATE.format(run_id=run_id), json={})
    assert answer.status_code == CONFLICT_STATUS
    assert answer.get_json()["error"]["code"] == ALREADY_STARTED_CODE


def test_a_cancelled_run_reads_as_cancelled_and_never_as_stopped(
    client: FlaskClient, run_store: RecordingRunStore
) -> None:
    """A reader months later must tell a cancel from a stop.

    Why:
        A stop cancels firmware that the cloud already holds. A cancel ends a
        plan that no device ever saw. One of the two touched hardware.

    Args:
        client: The signed-in client.
        run_store: The recording store.
    """
    run_id = seed(run_store, "awaiting_confirmation")
    client.post(CANCEL_TEMPLATE.format(run_id=run_id), json={})
    assert run_store.runs[run_id]["state"] == "cancelled"


def test_a_cancel_names_the_operator(client: FlaskClient, run_store: RecordingRunStore) -> None:
    """The record names who ended the run, through the digest.

    Args:
        client: The signed-in client.
        run_store: The recording store.
    """
    run_id = seed(run_store, "created")
    client.post(CANCEL_TEMPLATE.format(run_id=run_id), json={})
    digest = run_store.runs[run_id]["cancelled_by"]
    assert digest
    assert PROBE_EMAIL not in digest


def test_a_cancelled_run_moves_nowhere(client: FlaskClient, run_store: RecordingRunStore) -> None:
    """The cancelled state is final, so a second cancel changes nothing.

    Args:
        client: The signed-in client.
        run_store: The recording store.
    """
    run_id = seed(run_store, "created")
    client.post(CANCEL_TEMPLATE.format(run_id=run_id), json={})
    second = client.post(CANCEL_TEMPLATE.format(run_id=run_id), json={})
    assert second.status_code == CONFLICT_STATUS  # The run already ended.


# ---------------------------------------------------------------------------
# The guards that both controls share
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("template", [RESCHEDULE_TEMPLATE, CANCEL_TEMPLATE])
def test_an_absent_run_answers_run_not_found(client: FlaskClient, template: str) -> None:
    """One code serves every run path.

    Args:
        client: The signed-in client.
        template: The path under test.
    """
    answer = client.post(template.format(run_id=UNKNOWN_RUN_ID), json={"start_time": "1h"})
    assert answer.status_code == NOT_FOUND_STATUS
    assert answer.get_json()["error"]["code"] == RUN_NOT_FOUND_CODE


@pytest.mark.parametrize("template", [RESCHEDULE_TEMPLATE, CANCEL_TEMPLATE])
def test_a_signed_out_browser_reaches_neither_control(upgrade_app: Flask, template: str) -> None:
    """Both controls need a signed-in session.

    Args:
        upgrade_app: The application with the seams injected.
        template: The path under test.
    """
    with upgrade_app.test_client() as anonymous:
        answer = anonymous.post(template.format(run_id="run-abc"), json={})
    assert answer.status_code == NOT_AUTHENTICATED_STATUS


@pytest.mark.parametrize("template", [RESCHEDULE_TEMPLATE, CANCEL_TEMPLATE])
def test_an_operator_without_the_lock_reaches_neither_control(
    upgrade_app: Flask, client: FlaskClient, run_store: RecordingRunStore, template: str
) -> None:
    """FR-038i binds every write of a run to the operator that holds the site.

    Args:
        upgrade_app: The application with the seams injected.
        client: The signed-in client.
        run_store: The recording store.
        template: The path under test.
    """
    run_id = seed(run_store, "awaiting_confirmation")
    # Another operator holds the site now. The index maps a site to the address
    # of its holder, which is a plain string.
    upgrade_app.config[LOCK_READER_KEY] = lambda org, sites: dict.fromkeys(sites, OTHER_EMAIL)
    answer = client.post(template.format(run_id=run_id), json={"start_time": "1h"})
    assert answer.status_code == CONFLICT_STATUS
    assert answer.get_json()["error"]["code"] == SITE_LOCKED_CODE


@pytest.mark.parametrize("template", [RESCHEDULE_TEMPLATE, CANCEL_TEMPLATE])
def test_a_store_that_refuses_the_write_answers_a_fault(
    client: FlaskClient, run_store: RecordingRunStore, template: str
) -> None:
    """The operator must learn that the portal kept nothing.

    Args:
        client: The signed-in client.
        run_store: The recording store.
        template: The path under test.
    """
    run_id = seed(run_store, "awaiting_confirmation")
    run_store.refuse_writes = True
    answer = client.post(template.format(run_id=run_id), json={"start_time": "1h"})
    assert answer.status_code >= 500  # A lost write never reads as a success.


# ---------------------------------------------------------------------------
# The state machine
# ---------------------------------------------------------------------------


def test_the_model_forbids_a_cancel_of_a_running_upgrade() -> None:
    """The model is the last guard, whatever a route does.

    Why:
        A cancel of a running upgrade would end the record while the cloud still
        writes firmware. The run would then read as ended while devices reboot.
    """
    assert RunState.CANCELLED not in RunStateMachine.allowed_next(RunState.UPGRADE_RUNNING)


def test_the_cancelled_state_is_final() -> None:
    """A cancelled run moves nowhere, which every terminal state promises."""
    assert RunStateMachine.allowed_next(RunState.CANCELLED) == frozenset()
    assert RunState.CANCELLED in RunStateMachine.TERMINAL
