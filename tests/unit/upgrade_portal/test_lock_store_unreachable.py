"""Unit tests that hold the write path of the portal closed when Redis is down.

Why:
    Issue #1827 reports a safety defect. The site lock read answered two states.
    A free site and a site the portal could not read both answered None, so a
    second operator read a held site as free and started a second upgrade on a
    live network. `contracts/site-lock.md:116` asks the portal to refuse the
    upgrade with 503 `lock_store_unreachable` and to add no fallback lock.

    Every test drives the route through a bare application. No factory, no
    database, and no Redis server takes part. Each test injects a lock reader
    through the `SITE_LOCK_READER` seam that the route already reads.

    A capture and a page keep the old rule. `capture.py` starts a capture when
    the state is unknown, because a capture writes no firmware. These tests
    cover the three routes that lead to a firmware write.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

from collections.abc import Callable, Iterator  # Types the lock reader and each fixture that yields.
from typing import Any  # A run record, an injected store, and a JSON body are all free-form.

import pytest  # The test framework.
from flask import Flask  # The smallest application that can hold the blueprint.
from flask.testing import FlaskClient  # Drives a route with no server and no browser.
from werkzeug.test import TestResponse  # The answer that the test client returns.

from src.upgrade_portal.app.routes import upgrade  # The module under test.
from src.upgrade_portal.app.routes.select import (  # The sibling module owns the three state words.
    LOCK_READER_KEY,
    LOCK_STATE_FREE,
    LOCK_STATE_LOCKED,
    LOCK_STATE_UNKNOWN,
    SELECTED_ORG_KEY,
    SELECTED_SITE_KEY,
)
from src.upgrade_portal.runtime import identity  # The registry, the cookie name, and the session field names.
from src.upgrade_portal.runtime.runs import RunRecordBuilder, RunSpec, RunState  # The record model.

# WHY: A reserved example domain, so no message can reach a real mailbox.
PROBE_EMAIL = "probe.operator@example.invalid"
OTHER_EMAIL = "other.operator@example.invalid"

# WHY: An obviously fake value. FR-009 forbids a real credential inside the suite.
FAKE_SECRET = "fake-flask-secret-key-for-tests-only"

# WHY: The identifier shape that the cloud uses.
ORG_ID = "00000000-0000-0000-0000-0000000000aa"
SITE_ID = "00000000-0000-0000-0000-0000000000bb"

UNREACHABLE_STATUS = 503  # `contracts/http-api.md:133` fixes this status for an unreadable lock store.

LockReader = Callable[[str, list[str]], dict[str, str | None]]  # The shape of the injected seam.


class SiteAwareStore:
    """A run record store that answers the reader, the writer, and the site scan.

    Why:
        The real store reads a database. This stand-in holds the same three
        method names in memory, so a route test proves the decision of the route
        and never the behavior of a database.
    """

    def __init__(self) -> None:
        """Start with no record."""
        self.records: dict[str, dict[str, Any]] = {}  # One entry for each seeded or created run.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one stored run record.

        Args:
            run_id: The key of the run to read.

        Returns:
            The record, or None when no run holds that key.
        """
        return self.records.get(run_id)  # An absent key answers None, as the real store does.

    def write_run(self, run: dict[str, Any]) -> bool:
        """Store one run record.

        Args:
            run: The record to store.

        Returns:
            True, because a memory write always succeeds.
        """
        self.records[str(run["run_id"])] = run  # The key comes from the record, never from the caller.
        return True  # A memory write never fails, so no route reads a false failure.

    def site_runs(self, site_id: str) -> list[dict[str, Any]]:
        """Return every record that this store holds for one site.

        Args:
            site_id: The site to scan.

        Returns:
            One record for each run of that site.
        """
        return [row for row in self.records.values() if row.get("site_id") == site_id]  # One site only.


def reader_that_raises() -> LockReader:
    """Build a lock reader that fails as an unreachable Redis server does.

    Why:
        `runtime/lock.py` reaches Redis over a network. A stopped server raises
        inside that call, and `select.read_site_locks` catches the fault and
        answers an empty index. This stand-in reproduces that exact path.

    Returns:
        The reader callable that the seam accepts.
    """

    def read(org_id: str, site_ids: list[str]) -> dict[str, str | None]:
        """Fail as a stopped lock store does.

        Args:
            org_id: The organization that owns the sites.
            site_ids: The sites to ask about.

        Returns:
            Nothing, because this reader always raises.

        Raises:
            RuntimeError: Always, because the store cannot answer.
        """
        raise RuntimeError(f"the lock store cannot answer about {org_id} and {site_ids}")  # The dead store.

    return read  # The test writes this callable into the application configuration.


def reader_that_answers(holders: dict[str, str | None]) -> LockReader:
    """Build a lock reader that answers one fixed index.

    Args:
        holders: The holder of each site that the store knows about.

    Returns:
        The reader callable that the seam accepts.
    """

    def read(org_id: str, site_ids: list[str]) -> dict[str, str | None]:
        """Return the fixed index, unchanged.

        Args:
            org_id: The organization that owns the sites.
            site_ids: The sites to ask about.

        Returns:
            The index that the test built.
        """
        return dict(holders)  # The organization and the site list play no part in this stand-in.

    return read  # The test writes this callable into the application configuration.


@pytest.fixture
def run_store() -> SiteAwareStore:
    """Return a fresh stand-in run record store.

    Returns:
        A store with no record, so no record survives from an earlier test.
    """
    return SiteAwareStore()  # One store for each test keeps every test independent.


@pytest.fixture
def portal_app(run_store: SiteAwareStore) -> Flask:
    """Return a bare application that holds the upgrade blueprint alone.

    Args:
        run_store: The stand-in run record store.

    Returns:
        The application, ready for a test client.
    """
    app = Flask(__name__)  # The smallest application that can hold the blueprint.
    app.config.update(TESTING=True, SECRET_KEY=FAKE_SECRET, WTF_CSRF_ENABLED=False)  # Test settings alone.
    app.config[upgrade.RUN_STORE_KEY] = run_store  # The seam the route already reads.
    app.config[LOCK_READER_KEY] = reader_that_raises()  # Redis is down for every test unless a test says more.
    app.register_blueprint(upgrade.upgrade_bp)  # The routes under test.
    return app  # Each test drives this application through a client.


@pytest.fixture
def registered_owner() -> Iterator[identity.SessionOwner]:
    """Register one operator and drop the record when the test ends.

    Yields:
        The identity pair of the registered operator.
    """
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())  # The pair the guard checks.
    record = identity.OperatorSession(
        owner=owner,  # The pair that the browser cookie and the session field name.
        cloud_session=object(),  # A plain object states no scope, so every organization passes.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,  # No password takes part in these tests.
    )
    identity.SESSION_REGISTRY.register(record)  # The guard reads the registry on every request.
    try:  # The test body runs with the owner in place.
        yield owner  # Every signed-in test reads this pair.
    finally:  # A leaked record would sign in a later test by accident.
        identity.SESSION_REGISTRY.drop(owner.key)  # The registry outlives the test, so clear it here.


@pytest.fixture
def client(portal_app: Flask, registered_owner: identity.SessionOwner) -> Iterator[FlaskClient]:
    """Return a signed-in client that already picked the organization and the site.

    Args:
        portal_app: The application with both seams injected.
        registered_owner: The identity pair of the registered operator.

    Yields:
        The Flask test client, with the session held open.
    """
    with portal_app.test_client() as opened:  # The context manager holds the session across requests.
        opened.set_cookie(identity.BROWSER_ID_COOKIE, registered_owner.browser_id)  # Half of the guard.
        with opened.session_transaction() as browser_session:  # The other half of the guard.
            browser_session[identity.SESSION_OWNER_KEY] = registered_owner.key  # Names the registered owner.
            browser_session[SELECTED_ORG_KEY] = ORG_ID  # The picker writes this field.
            browser_session[SELECTED_SITE_KEY] = SITE_ID  # The picker writes this field as well.
        yield opened  # Every test below drives this client.


def seed_startable_run(store: SiteAwareStore, state: str = RunState.CREATED.value) -> str:
    """Write one run record that passes every start rule except the lock rule.

    Why:
        The start route reads the confirmation, the pre-check, the lock, and the
        plan in that order. A record that carries a pre-check and a plan proves
        that the lock rule alone stopped the call.

    Args:
        store: The stand-in run record store.
        state: The state that the seeded run holds.

    Returns:
        The key of the seeded run.
    """
    spec = RunSpec(ORG_ID, "Probe organization", SITE_ID, "Probe site", PROBE_EMAIL, "browser-probe")
    record = RunRecordBuilder().build(spec)  # The record layer owns every field and every default.
    record["state"] = state  # The test names the stage that the run already reached.
    record[upgrade.PRE_CAPTURE_FIELD] = "capture-probe"  # FR-035 needs a saved pre-check.
    record[upgrade.TARGETS_FIELD] = [{"mac": "aabbccddeeff", "version": "0.0.0"}]  # A plan with one device.
    store.records[str(record["run_id"])] = record  # The store answers the read with this record.
    return str(record["run_id"])  # Every start call and stop call below names this key.


def error_code(response: TestResponse) -> str:
    """Read the error code out of one answer.

    Args:
        response: The answer of the route.

    Returns:
        The code, or an empty string when the body carries none.
    """
    body: Any = response.get_json()  # The envelope of `contracts/README.md`.
    return str(body["error"]["code"]) if isinstance(body, dict) else ""  # A missing envelope reads as no code.


def test_the_create_call_refuses_an_unreachable_lock_store(client: FlaskClient) -> None:
    """A create call answers 503 when the portal cannot read the site lock.

    Why:
        Issue #1827 step 5 accepts the run today. An unreadable lock hides the
        holder, so the portal must refuse and must never report the site free.

    Args:
        client: The signed-in test client.
    """
    answer = client.post(f"/api/sites/{SITE_ID}/runs", json={"tier": 2})  # The path of the contract.
    assert answer.status_code == UNREACHABLE_STATUS  # A held site must not read as a free site.
    assert error_code(answer) == upgrade.LOCK_STORE_DOWN_CODE  # The code names the cause plainly.


def test_the_start_call_refuses_an_unreachable_lock_store(
    client: FlaskClient,
    run_store: SiteAwareStore,
) -> None:
    """A start call answers 503 when the portal cannot read the site lock.

    Why:
        Issue #1827 step 6 sends the firmware today. This route is the one that
        writes to a device, so this refusal is the whole point of the repair.

    Args:
        client: The signed-in test client.
        run_store: The stand-in run record store.
    """
    run_id = seed_startable_run(run_store)  # Every other start rule passes.
    answer = client.post(f"/api/runs/{run_id}/start", json={"confirm": upgrade.CONFIRM_TEXT})  # The real word.
    assert answer.status_code == UNREACHABLE_STATUS  # No firmware goes out while the lock is unreadable.
    assert error_code(answer) == upgrade.LOCK_STORE_DOWN_CODE  # The code names the cause plainly.


def test_the_stop_call_refuses_an_unreachable_lock_store(
    client: FlaskClient,
    run_store: SiteAwareStore,
) -> None:
    """A stop call answers 503 when the portal cannot read the site lock.

    Why:
        FR-038i binds the stop control to the operator that holds the site. An
        unreadable lock cannot prove that bond, so the stop must not run.

    Args:
        client: The signed-in test client.
        run_store: The stand-in run record store.
    """
    run_id = seed_startable_run(run_store, RunState.UPGRADE_RUNNING.value)  # A run that a stop could reach.
    answer = client.post(f"/api/runs/{run_id}/stop", json={"confirm": "STOP"})  # The word the route asks for.
    assert answer.status_code == UNREACHABLE_STATUS  # The stop of another operator must not run.
    assert error_code(answer) == upgrade.LOCK_STORE_DOWN_CODE  # The code names the cause plainly.


def test_the_refusal_names_no_operator(client: FlaskClient) -> None:
    """The 503 answer names no holder, because the portal knows of none.

    Why:
        A named address would tell the operator that a lock exists. The portal
        read nothing, so any address in this body would be a guess.

    Args:
        client: The signed-in test client.
    """
    answer = client.post(f"/api/sites/{SITE_ID}/runs", json={"tier": 2})  # The create path.
    body: Any = answer.get_json()  # The envelope of `contracts/README.md`.
    assert "actor_email" not in body["error"].get("details", {})  # No guess reaches the operator.


def test_a_reachable_store_that_reports_free_still_creates_a_run(
    portal_app: Flask,
    client: FlaskClient,
) -> None:
    """A store that answers `no lock` keeps the create call working.

    Why:
        The repair must refuse an unreadable store alone. A store that answers
        and names no holder leaves the site free, so the run must continue.

    Args:
        portal_app: The application that holds the lock reader seam.
        client: The signed-in test client.
    """
    portal_app.config[LOCK_READER_KEY] = reader_that_answers({SITE_ID: None})  # The store answered `no lock`.
    answer = client.post(f"/api/sites/{SITE_ID}/runs", json={"tier": 2})  # The create path.
    assert answer.status_code == upgrade.CREATED_STATUS  # A free site still accepts a new run.


def test_a_held_site_still_answers_the_lock_code(portal_app: Flask, client: FlaskClient) -> None:
    """A store that names another operator keeps the 409 answer.

    Why:
        The new 503 must not replace the 409. The two answers name two different
        causes, and the operator needs the address that only the 409 carries.

    Args:
        portal_app: The application that holds the lock reader seam.
        client: The signed-in test client.
    """
    portal_app.config[LOCK_READER_KEY] = reader_that_answers({SITE_ID: OTHER_EMAIL})  # A second operator holds it.
    answer = client.post(f"/api/sites/{SITE_ID}/runs", json={"tier": 2})  # The create path.
    assert answer.status_code == upgrade.CONFLICT_STATUS  # The held site keeps the documented status.
    assert error_code(answer) == upgrade.SITE_LOCKED_CODE  # The refusal still names the holder.


def test_the_lock_read_reports_the_unknown_state(portal_app: Flask) -> None:
    """The lock read names `unknown` when the store answers about no site.

    Why:
        `select.py` already tests membership for the site list. The write path
        must test membership as well, because `.get()` maps an absent entry and
        a free site to one answer.

    Args:
        portal_app: The application that holds the lock reader seam.
    """
    portal_app.config[LOCK_READER_KEY] = reader_that_answers({})  # An empty index names no site at all.
    with portal_app.test_request_context():  # The read looks at the application configuration.
        assert upgrade.lock_holder(ORG_ID, SITE_ID).state == LOCK_STATE_UNKNOWN  # Never `free`.


def test_the_lock_read_reports_the_free_state(portal_app: Flask) -> None:
    """The lock read names `free` when the store answers None for the site.

    Args:
        portal_app: The application that holds the lock reader seam.
    """
    portal_app.config[LOCK_READER_KEY] = reader_that_answers({SITE_ID: None})  # The store answered `no lock`.
    with portal_app.test_request_context():  # The read looks at the application configuration.
        assert upgrade.lock_holder(ORG_ID, SITE_ID).state == LOCK_STATE_FREE  # An answer of None means free.


def test_the_lock_read_reports_the_locked_state(portal_app: Flask) -> None:
    """The lock read names `locked` and carries the address of the holder.

    Args:
        portal_app: The application that holds the lock reader seam.
    """
    portal_app.config[LOCK_READER_KEY] = reader_that_answers({SITE_ID: OTHER_EMAIL})  # A named holder.
    with portal_app.test_request_context():  # The read looks at the application configuration.
        found = upgrade.lock_holder(ORG_ID, SITE_ID)  # One read, two assertions.
    assert found.state == LOCK_STATE_LOCKED  # An address names a holder.
    assert found.holder == OTHER_EMAIL  # The refusal needs this address.
