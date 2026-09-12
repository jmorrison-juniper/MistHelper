"""Contract tests for the pre-check adoption of the run create call.

Why:
    Issue 2098 asks the run create call to adopt the newest verified standalone
    pre-check of the site. The handler writes a ``capture_for_run`` edge from
    the new run to that capture with the role ``pre`` and sets the run pre-check
    field to that capture identifier. See Delta H3 of
    ``specs/1823-upgrade-capture-portal/contracts/remaining-defects-deltas.md``
    and FR-103.

    The adoption sits behind one seam, so a contract test injects a stand-in and
    reaches no ArangoDB server. The stand-in reads a fixed pre-check key and
    records every edge write, so a test proves both the field and the edge with
    no database.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.upgrade_portal.runtime import identity  # The real session guard, so the tests sign in for real.

logger = logging.getLogger(__name__)

RUN_STORE_KEY = "RUN_STORE"  # The seam that holds the run record store.
LOCK_READER_KEY = "SITE_LOCK_READER"  # The seam that reads the site lock, named by `select.py`.
ADOPTER_KEY = "PRECHECK_ADOPTER"  # The seam that reads and links a standalone pre-check.

PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.
ORG_ID = "00000000-0000-0000-0000-0000000000aa"  # Matches the shared organization of the other tests.
SITE_ID = "00000000-0000-0000-0000-0000000000bb"  # Matches the shared site of the other tests.

SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The organization pick inside the signed session.
SELECTED_SITE_SESSION_KEY = "selected_site_id"  # The site pick inside the same signed session.

CREATE_PATH = f"/api/sites/{SITE_ID}/runs"  # The path that `contracts/http-api.md` section 5 names.
CREATED_STATUS = 201  # The portal created one run record.

PRE_CAPTURE_FIELD = "pre_capture_id"  # The run record field that names the adopted pre-check.
PRE_ROLE = "pre"  # Delta H3 fixes this role for the adopted edge.
ADOPTED_CAPTURE_ID = "cap-adopted-01"  # The standalone pre-check the site holds for the first test.


class RecordingRunStore:
    """Holds every run record of one test in one dictionary.

    Why:
        The create route asks for a ``read_run`` and a ``write_run`` pair. This
        stand-in gives both and reaches no database server, so a contract test
        reads the saved run back with no ArangoDB server.
    """

    def __init__(self) -> None:
        """Start with no run record at all."""
        self.runs: dict[str, dict[str, Any]] = {}  # One entry for each run the route creates.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one run record, or None when no run holds the identifier.

        Args:
            run_id: The run key.

        Returns:
            A copy of the record, or None.
        """
        held = self.runs.get(run_id)  # An absent key reads as None, never a fault.
        return dict(held) if held is not None else None  # A copy stops a caller edit of the stored record.

    def write_run(self, run: dict[str, Any]) -> bool:
        """Write one run record and report the true result.

        Args:
            run: The whole record, with the adopted field already in place.

        Returns:
            True, because this stand-in never refuses a write.
        """
        self.runs[str(run["run_id"])] = dict(run)  # A copy stops a later edit of the caller dictionary.
        return True  # The route then answers the operator.


class RecordingAdopter:
    """Reads a fixed pre-check key and records every edge write.

    Why:
        The create route reads the newest standalone pre-check through this
        seam and then writes one edge through it. The stand-in answers a fixed
        key and records the edge, so a test proves both halves of Delta H3 with
        no database.
    """

    def __init__(self, capture_id: str) -> None:
        """Bind the stand-in to the key it answers.

        Args:
            capture_id: The pre-check key the reader returns, or an empty string.
        """
        self.capture_id = capture_id  # WHY: The reader answers this key for every site.
        self.edges: list[tuple[str, str, str]] = []  # WHY: One entry for each edge the route wrote.

    def newest_precheck(self, site_id: str) -> str:
        """Return the newest standalone pre-check key of one site.

        Args:
            site_id: The site the run belongs to.

        Returns:
            The fixed pre-check key, or an empty string for no adoption.
        """
        logger.info("test adopter reads the newest pre-check of site %s", site_id)  # ASCII, %s style, no secret.
        return self.capture_id  # The route adopts this key when it is not empty.

    def write_capture_edge(self, run_id: str, capture_id: str, role: str) -> None:
        """Record one edge from a run to its adopted pre-check.

        Args:
            run_id: The new run the edge starts at.
            capture_id: The adopted pre-check the edge points at.
            role: The role the edge carries, ``pre`` for an adoption.
        """
        self.edges.append((run_id, capture_id, role))  # The test reads this list to prove the write.


@pytest.fixture
def run_store() -> RecordingRunStore:
    """Return a fresh run record store.

    Returns:
        An empty recording store.
    """
    return RecordingRunStore()  # Each test starts with no run at all.


@pytest.fixture
def adopter() -> RecordingAdopter:
    """Return a stand-in adopter that holds one pre-check.

    Returns:
        A recorder that answers the adopted key and records each edge.
    """
    return RecordingAdopter(ADOPTED_CAPTURE_ID)  # Each test starts with the site holding one pre-check.


@pytest.fixture
def upgrade_app(portal_app: Flask, run_store: RecordingRunStore, adopter: RecordingAdopter) -> Flask:
    """Return the portal application with the store and the adopter injected.

    Why:
        The create call writes a run record and adopts a pre-check. Both sit
        behind a seam, so a contract test replaces each and reaches no database
        server. The lock reader answers a reachable store that holds no lock, so
        the create call passes the lock refusal.

    Args:
        portal_app: The real application from the shared fixture.
        run_store: The stand-in run record store.
        adopter: The stand-in pre-check adopter.

    Returns:
        The application with the seams in place.
    """
    portal_app.config[RUN_STORE_KEY] = run_store  # No ArangoDB server runs in a contract test.
    portal_app.config[ADOPTER_KEY] = adopter  # The create route reads the newest pre-check through this seam.
    # A reachable lock store that holds no lock. An empty index would read as an
    # unreachable store and every write below would answer 503.
    portal_app.config[LOCK_READER_KEY] = lambda org_id, site_ids: dict.fromkeys(site_ids)
    portal_app.config["WTF_CSRF_ENABLED"] = False  # A contract test drives the route without a token round trip.
    return portal_app  # Every test below drives this application.


@pytest.fixture
def registered_owner() -> Iterator[identity.SessionOwner]:
    """Register one operator and drop the record when the test ends.

    Why:
        The guard admits a request only when the signed session and the browser
        cookie both name a registered owner. The registry is a process global,
        so the fixture clears it again.

    Yields:
        The identity pair of the registered operator.
    """
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())  # The pair the guard checks.
    record = identity.OperatorSession(
        owner=owner,
        cloud_session=object(),  # A plain object states no scope, so every organization passes.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
    )
    identity.SESSION_REGISTRY.register(record)  # The guard reads the registry on every request.
    try:  # The test body runs with the owner in place.
        yield owner  # Every signed-in test reads this pair.
    finally:  # A leaked record would sign in a later test by accident.
        identity.SESSION_REGISTRY.drop(owner.key)  # The registry outlives the test, so clear it here.


@pytest.fixture
def upgrade_client(upgrade_app: Flask, registered_owner: identity.SessionOwner) -> Iterator[FlaskClient]:
    """Return a signed-in client that already picked the organization and the site.

    Args:
        upgrade_app: The application with the seams injected.
        registered_owner: The identity pair of the registered operator.

    Yields:
        The Flask test client, with the session held open.
    """
    with upgrade_app.test_client() as client:  # The context manager holds the session across requests.
        client.set_cookie(identity.BROWSER_ID_COOKIE, registered_owner.browser_id)  # Half of the guard.
        with client.session_transaction() as browser_session:  # The other half of the guard.
            browser_session[identity.SESSION_OWNER_KEY] = registered_owner.key  # Names the registered owner.
            browser_session[SELECTED_ORG_SESSION_KEY] = ORG_ID  # The scope of every later read.
            browser_session[SELECTED_SITE_SESSION_KEY] = SITE_ID  # The site the run belongs to.
        yield client  # Every test below drives this client.


def test_create_adopts_the_newest_precheck_and_sets_the_field(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The created run names the adopted pre-check in its pre-check field.

    Why:
        Delta H3 asks the handler to set the run pre-check field to the newest
        verified standalone pre-check of the site. A later start refuses a run
        with no saved pre-check, so this field lets the adopted run begin.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    answer = upgrade_client.post(CREATE_PATH, json={})  # The browser sends no body of its own.
    assert answer.status_code == CREATED_STATUS  # The create call still answers 201.
    run_id = str(answer.get_json()["run_id"])  # The key the record store now holds.
    assert run_store.runs[run_id][PRE_CAPTURE_FIELD] == ADOPTED_CAPTURE_ID  # The field names the pre-check.


def test_create_writes_the_pre_edge_to_the_new_run(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
    adopter: RecordingAdopter,
) -> None:
    """The created run gains one ``pre`` edge to the adopted pre-check.

    Why:
        Delta H3 asks the handler to write a ``capture_for_run`` edge from the
        new run to the adopted capture with the role ``pre``. The history view
        walks that edge, so a lost edge hides the pre-check.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
        adopter: The stand-in pre-check adopter.
    """
    answer = upgrade_client.post(CREATE_PATH, json={})  # The create call adopts the site pre-check.
    run_id = str(answer.get_json()["run_id"])  # The run the edge must start at.
    assert adopter.edges == [(run_id, ADOPTED_CAPTURE_ID, PRE_ROLE)]  # One edge, run to pre-check, role pre.


def test_create_without_a_precheck_adopts_nothing(
    portal_app: Flask,
    run_store: RecordingRunStore,
    registered_owner: identity.SessionOwner,
) -> None:
    """A site with no standalone pre-check creates a run with no adoption.

    Why:
        Delta H3 states that a site with no standalone pre-check creates the run
        with no adopted pre-check and an unchanged answer. The handler then
        writes no edge and leaves the pre-check field empty.

    Args:
        portal_app: The real application from the shared fixture.
        run_store: The stand-in run record store.
        registered_owner: The identity pair of the registered operator.
    """
    empty_adopter = RecordingAdopter("")  # WHY: The site holds no standalone pre-check at all.
    portal_app.config[RUN_STORE_KEY] = run_store  # No ArangoDB server runs in a contract test.
    portal_app.config[ADOPTER_KEY] = empty_adopter  # The reader answers an empty key for this site.
    portal_app.config[LOCK_READER_KEY] = lambda org_id, site_ids: dict.fromkeys(site_ids)  # No lock is held.
    portal_app.config["WTF_CSRF_ENABLED"] = False  # A contract test drives the route without a token.
    with portal_app.test_client() as client:  # The context manager holds the session across requests.
        client.set_cookie(identity.BROWSER_ID_COOKIE, registered_owner.browser_id)  # Half of the guard.
        with client.session_transaction() as browser_session:  # The other half of the guard.
            browser_session[identity.SESSION_OWNER_KEY] = registered_owner.key  # Names the registered owner.
            browser_session[SELECTED_ORG_SESSION_KEY] = ORG_ID  # The scope of the read.
            browser_session[SELECTED_SITE_SESSION_KEY] = SITE_ID  # The site the run belongs to.
        answer = client.post(CREATE_PATH, json={})  # The create call finds no pre-check to adopt.
    assert answer.status_code == CREATED_STATUS  # The answer is unchanged for a site with no pre-check.
    run_id = str(answer.get_json()["run_id"])  # The key the record store now holds.
    assert not run_store.runs[run_id].get(PRE_CAPTURE_FIELD)  # No adoption leaves the field at its empty default.
    assert empty_adopter.edges == []  # No pre-check means no edge.
