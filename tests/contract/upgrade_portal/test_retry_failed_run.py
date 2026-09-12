"""Contract tests for the retry of one failed run.

Why:
    Issue #2202 records the gap. A failed run held every choice that the
    operator made, and the portal offered no way to use them again. The operator
    returned to the site, took the lock, and rebuilt every option by hand.

    A rebuild by hand drops a setting, and the retry then runs a plan that
    differs from the one that failed. The whole value of a retry is that it
    keeps the plan.

    The schedule is the part that must not be copied as it stands. A schedule of
    the failed run names a moment in the past, and a retry that kept that moment
    would write the firmware at once. The operator would read a delayed start
    that never happens.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.upgrade_portal.app.routes import upgrade
from src.upgrade_portal.runtime import identity

RUN_STORE_KEY = "RUN_STORE"
LOCK_READER_KEY = "SITE_LOCK_READER"

PROBE_EMAIL = "probe.operator@example.invalid"
OTHER_EMAIL = "other.operator@example.invalid"
ORG_ID = "00000000-0000-0000-0000-0000000000aa"
SITE_ID = "00000000-0000-0000-0000-0000000000bb"

SELECTED_ORG_SESSION_KEY = "selected_org_id"
SELECTED_SITE_SESSION_KEY = "selected_site_id"

RETRY_TEMPLATE = "/api/runs/{run_id}/retry"
UNKNOWN_RUN_ID = "run-00000000000000000000000000000000"

CREATED_STATUS = 201
NOT_AUTHENTICATED_STATUS = 401
NOT_FOUND_STATUS = 404
CONFLICT_STATUS = 409

RUN_NOT_FOUND_CODE = "run_not_found"
SITE_LOCKED_CODE = "site_locked"
NOT_RETRYABLE_CODE = "run_not_retryable"

# A stale moment of an earlier run. The retry must never reuse it.
STALE_MOMENT = 1_700_000_000

# Every option group that the failed run holds. The retry copies each one.
FAILED_OPTIONS: dict[str, Any] = {
    "strategy": "canary",
    "reboot": True,
    "force": False,
    "stable_version": True,
    "canary_phases": [1, 10, 50, 100],
    "max_failure_percentage": 5,
    "peer_to_peer": {"enable_p2p": True, "p2p_cluster_size": 10},
    "radio": {"rrm_node_order": "serial", "rrm_mesh_upgrade": "parallel"},
    "channel": "stable",
}

# The device list of the failed run, with the version that each device wanted.
FAILED_TARGETS: list[dict[str, Any]] = [
    {"mac": "5c5b350e0001", "device_type": "switch", "version_target": "24.2R1.17"},
    {"mac": "5c5b350e0002", "device_type": "ap", "version_target": "0.15.34994"},
]


class RecordingRunStore:
    """Holds every run record of one test in one dictionary."""

    def __init__(self) -> None:
        """Start with no run record and with writes allowed."""
        self.runs: dict[str, dict[str, Any]] = {}
        self.refuse_writes = False

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one run record, or None.

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


@pytest.fixture(name="retry_app")
def fixture_retry_app(portal_app: Flask, run_store: RecordingRunStore) -> Flask:
    """Return the portal application with the run store injected.

    Args:
        portal_app: The real application from the shared fixture.
        run_store: The stand-in run record store.

    Returns:
        The application with the seams in place.
    """
    portal_app.config[RUN_STORE_KEY] = run_store
    portal_app.config[LOCK_READER_KEY] = lambda org, sites: dict.fromkeys(sites)
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
def fixture_client(retry_app: Flask, registered_owner: identity.SessionOwner) -> Iterator[FlaskClient]:
    """Return a signed-in client that already picked the organization and the site.

    Args:
        retry_app: The application with the seams injected.
        registered_owner: The identity pair of the registered operator.

    Yields:
        The Flask test client.
    """
    with retry_app.test_client() as test_client:
        test_client.set_cookie(identity.BROWSER_ID_COOKIE, registered_owner.browser_id)
        with test_client.session_transaction() as browser_session:
            browser_session[identity.SESSION_OWNER_KEY] = registered_owner.key
            browser_session[SELECTED_ORG_SESSION_KEY] = ORG_ID
            browser_session[SELECTED_SITE_SESSION_KEY] = SITE_ID
        yield test_client


def seed_failed(store: RecordingRunStore, options: dict[str, Any] | None = None) -> str:
    """Write one failed run that holds a full plan.

    Args:
        store: The recording store.
        options: The option record, or None for the shared one.

    Returns:
        The run key.
    """
    run_id = "run-failed"
    store.runs[run_id] = {
        "run_id": run_id,
        "org_id": ORG_ID,
        "site_id": SITE_ID,
        "state": "failed",
        "options": dict(FAILED_OPTIONS if options is None else options),
        "targets": [dict(target) for target in FAILED_TARGETS],
        "pre_capture_id": "cap-before-the-failure",
    }
    return run_id


def new_record(store: RecordingRunStore, answer: Any) -> dict[str, Any]:
    """Return the record that the retry wrote.

    Args:
        store: The recording store.
        answer: The JSON body of the retry answer.

    Returns:
        The new run record.
    """
    return store.runs[str(answer["run_id"])]


# ---------------------------------------------------------------------------
# The rebase rule, which is the part a reader cannot check by eye
# ---------------------------------------------------------------------------


def test_a_stored_duration_survives_the_retry() -> None:
    """The record holds the duration beside the moment, so the retry keeps it.

    Why:
        The start route counts the duration again at the moment of the start, so
        `8h` still means eight hours from the retry.
    """
    kept, notes = upgrade.rebased_options(
        {"start_time": STALE_MOMENT, "schedule": {"start_time_after": 8 * 60 * 60}},
    )
    assert kept["start_time"] == STALE_MOMENT  # The start route rebases it from the duration.
    assert notes == []  # Nothing was dropped, so the page names nothing.


def test_a_moment_with_no_duration_is_dropped() -> None:
    """A moment alone cannot be rebased, so the retry drops it.

    Why:
        Warning: a retry that kept the moment would write the firmware at once,
        and the operator would read a delayed start that never happens.
    """
    kept, notes = upgrade.rebased_options({"start_time": STALE_MOMENT, "schedule": {}})
    assert "start_time" not in kept  # No stale moment reaches the new run.
    assert len(notes) == 1  # The page names the drop.


def test_the_drop_names_the_reason() -> None:
    """An operator who loses a schedule must learn why."""
    _, notes = upgrade.rebased_options({"reboot_at": STALE_MOMENT, "schedule": {}})
    assert "past" in notes[0]  # The sentence states the cause.


def test_both_schedules_rebase_on_their_own() -> None:
    """The start and the reboot each carry their own duration."""
    kept, notes = upgrade.rebased_options(
        {
            "start_time": STALE_MOMENT,
            "reboot_at": STALE_MOMENT,
            "schedule": {"start_time_after": 3600},
        },
    )
    assert kept["start_time"] == STALE_MOMENT  # The start holds a duration, so it stays.
    assert "reboot_at" not in kept  # The reboot holds a moment alone, so it goes.
    assert len(notes) == 1


def test_a_plan_with_no_schedule_needs_no_rebase() -> None:
    """A run that starts at once carries no schedule to move."""
    kept, notes = upgrade.rebased_options({"strategy": "big_bang"})
    assert kept == {"strategy": "big_bang"}
    assert notes == []


# ---------------------------------------------------------------------------
# The route
# ---------------------------------------------------------------------------


def test_the_retry_copies_every_option(client: FlaskClient, run_store: RecordingRunStore) -> None:
    """A rebuild by hand drops a setting, so the retry copies each one.

    Args:
        client: The signed-in client.
        run_store: The recording store.
    """
    run_id = seed_failed(run_store)
    answer = client.post(RETRY_TEMPLATE.format(run_id=run_id), json={})
    assert answer.status_code == CREATED_STATUS
    assert new_record(run_store, answer.get_json())["options"] == FAILED_OPTIONS


def test_the_retry_copies_the_device_list_and_each_version(client: FlaskClient, run_store: RecordingRunStore) -> None:
    """The retry acts on the same devices, and it wants the same versions.

    Args:
        client: The signed-in client.
        run_store: The recording store.
    """
    run_id = seed_failed(run_store)
    answer = client.post(RETRY_TEMPLATE.format(run_id=run_id), json={})
    assert new_record(run_store, answer.get_json())["targets"] == FAILED_TARGETS


def test_the_new_record_names_the_failed_run(client: FlaskClient, run_store: RecordingRunStore) -> None:
    """A reader must reach the run that this one came from.

    Args:
        client: The signed-in client.
        run_store: The recording store.
    """
    run_id = seed_failed(run_store)
    answer = client.post(RETRY_TEMPLATE.format(run_id=run_id), json={})
    assert new_record(run_store, answer.get_json())["retry_of_run_id"] == run_id


def test_the_retry_takes_no_pre_check_of_the_failed_run(client: FlaskClient, run_store: RecordingRunStore) -> None:
    """The site changed while the failed run wrote firmware to part of it.

    Why:
        The reading before the failure no longer describes the site. A retry
        that adopted it would compare the upgraded site against a stale reading,
        and the comparison would report a change that nobody made.

    Args:
        client: The signed-in client.
        run_store: The recording store.
    """
    run_id = seed_failed(run_store)
    answer = client.post(RETRY_TEMPLATE.format(run_id=run_id), json={})
    assert not new_record(run_store, answer.get_json()).get("pre_capture_id")


def test_the_retry_answers_the_dropped_schedule(client: FlaskClient, run_store: RecordingRunStore) -> None:
    """The page names every schedule that the retry dropped.

    Args:
        client: The signed-in client.
        run_store: The recording store.
    """
    run_id = seed_failed(run_store, {"start_time": STALE_MOMENT, "schedule": {}})
    answer = client.post(RETRY_TEMPLATE.format(run_id=run_id), json={})
    assert len(answer.get_json()["notes"]) == 1


def test_the_retry_starts_a_run_in_the_first_state(client: FlaskClient, run_store: RecordingRunStore) -> None:
    """The new run begins at the start of the chain, whatever the failed one held.

    Args:
        client: The signed-in client.
        run_store: The recording store.
    """
    run_id = seed_failed(run_store)
    answer = client.post(RETRY_TEMPLATE.format(run_id=run_id), json={})
    assert answer.get_json()["state"] == "created"


@pytest.mark.parametrize("state", ["created", "awaiting_confirmation", "upgrade_running", "complete", "cancelled"])
def test_a_run_that_did_not_fail_offers_no_retry(client: FlaskClient, run_store: RecordingRunStore, state: str) -> None:
    """A retry reads a failed run alone.

    Args:
        client: The signed-in client.
        run_store: The recording store.
        state: The state under test.
    """
    run_id = seed_failed(run_store)
    run_store.runs[run_id]["state"] = state
    answer = client.post(RETRY_TEMPLATE.format(run_id=run_id), json={})
    assert answer.status_code == CONFLICT_STATUS
    assert answer.get_json()["error"]["code"] == NOT_RETRYABLE_CODE


def test_an_absent_run_answers_run_not_found(client: FlaskClient) -> None:
    """One code serves every run path.

    Args:
        client: The signed-in client.
    """
    answer = client.post(RETRY_TEMPLATE.format(run_id=UNKNOWN_RUN_ID), json={})
    assert answer.status_code == NOT_FOUND_STATUS
    assert answer.get_json()["error"]["code"] == RUN_NOT_FOUND_CODE


def test_an_operator_without_the_lock_reaches_no_retry(
    retry_app: Flask, client: FlaskClient, run_store: RecordingRunStore
) -> None:
    """FR-038i binds every write of a run to the operator that holds the site.

    Args:
        retry_app: The application with the seams injected.
        client: The signed-in client.
        run_store: The recording store.
    """
    run_id = seed_failed(run_store)
    retry_app.config[LOCK_READER_KEY] = lambda org, sites: dict.fromkeys(sites, OTHER_EMAIL)
    answer = client.post(RETRY_TEMPLATE.format(run_id=run_id), json={})
    assert answer.status_code == CONFLICT_STATUS
    assert answer.get_json()["error"]["code"] == SITE_LOCKED_CODE


def test_a_signed_out_browser_reaches_no_retry(retry_app: Flask) -> None:
    """The retry needs a signed-in session.

    Args:
        retry_app: The application with the seams injected.
    """
    with retry_app.test_client() as anonymous:
        answer = anonymous.post(RETRY_TEMPLATE.format(run_id="run-failed"), json={})
    assert answer.status_code == NOT_AUTHENTICATED_STATUS


def test_the_failed_run_keeps_every_value(client: FlaskClient, run_store: RecordingRunStore) -> None:
    """The retry reads the failed run and never edits it.

    Why:
        The failed record is the evidence of what happened. A retry that changed
        it would destroy the one account of the failure.

    Args:
        client: The signed-in client.
        run_store: The recording store.
    """
    run_id = seed_failed(run_store)
    client.post(RETRY_TEMPLATE.format(run_id=run_id), json={})
    failed = run_store.runs[run_id]
    assert failed["state"] == "failed"
    assert failed["options"] == FAILED_OPTIONS
    assert failed["pre_capture_id"] == "cap-before-the-failure"
