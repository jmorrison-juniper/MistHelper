"""Unit tests for the FR-037 guard that refuses a second upgrade at one site.

Why:
    FR-037 asks the portal to warn the operator before it sends a new upgrade to
    a site that already runs one. The site lock answers a different question. The
    operator who started the first run still holds that lock, so the same
    operator passes every lock check, opens a second tab, and starts a second
    upgrade over the first. That is the corruption the customer asked the portal
    to prevent, and no lock check catches it. These tests pin the repair.

    Every test drives the route through a bare application, so no factory, no
    database, and no Redis server takes part. Each store below is a stand-in that
    the test injects through the `RUN_STORE` seam the route already reads.

    Two parametrized tests read `RunStateMachine.TERMINAL` and the `RunState`
    model itself. No state name is written twice in this file, so a new state
    joins the correct group on the day the model gains it.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

from collections.abc import Callable, Iterator  # Types the lock reader and each fixture that yields.
from typing import Any  # A run record, an injected store, and a JSON body are all free-form.

import pytest  # The test framework.
from flask import Flask  # The smallest application that can hold the blueprint.
from flask.testing import FlaskClient  # Drives a route with no server and no browser.
from werkzeug.test import TestResponse  # The answer that the test client returns.

from src.upgrade_portal.app.routes import upgrade  # The module under test.
from src.upgrade_portal.app.routes.select import LOCK_READER_KEY, SELECTED_ORG_KEY, SELECTED_SITE_KEY  # Real names.
from src.upgrade_portal.runtime import identity  # The registry, the cookie name, and the session field names.
from src.upgrade_portal.runtime.runs import RunRecordBuilder, RunSpec, RunState, RunStateMachine  # The model.

# WHY: A reserved example domain, so no message can reach a real mailbox.
PROBE_EMAIL = "probe.operator@example.invalid"
OTHER_EMAIL = "other.operator@example.invalid"

# WHY: An obviously fake value. FR-009 forbids a real credential inside the suite.
FAKE_SECRET = "fake-flask-secret-key-for-tests-only"

# WHY: The identifier shape that the cloud uses. Two sites prove that the guard
# scopes its scan, because an operator upgrades one site while another settles.
ORG_ID = "00000000-0000-0000-0000-0000000000aa"
SITE_ID = "00000000-0000-0000-0000-0000000000bb"
OTHER_SITE_ID = "00000000-0000-0000-0000-0000000000cc"

# WHY: The two groups come from the model, never from a list typed here. A state
# added to `RunState` therefore reaches one of these tests with no edit.
TERMINAL_STATES = sorted(state.value for state in RunStateMachine.TERMINAL)
LIVE_STATES = sorted(state.value for state in RunState if state not in RunStateMachine.TERMINAL)


class SiteAwareStore:
    """A run record store that answers the reader, the writer, and the site scan.

    Why:
        The store that lands later reads a database. This stand-in holds the same
        three method names in memory, so a route test proves the decision of the
        route and never the behavior of a database.
    """

    def __init__(self) -> None:
        """Start with no record and with no scan recorded."""
        self.records: dict[str, dict[str, Any]] = {}  # One entry for each seeded or created run.
        self.scanned: list[str] = []  # One entry for each site scan, so a test proves the seam ran.
        self.rows: list[Any] | None = None  # A test sets this to answer a damaged row instead of a record.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one stored run record.

        Args:
            run_id: The key of the run to read.

        Returns:
            The record, or None when no run holds that key.
        """
        return self.records.get(run_id)  # An absent key answers None, as the real store does.

    def write_run(self, run: dict[str, Any]) -> bool:
        """Store one run record and report success.

        Args:
            run: The record to store.

        Returns:
            True, because a memory write never fails.
        """
        self.records[str(run["run_id"])] = dict(run)  # A copy, so a later edit cannot reach the store.
        return True  # The route reads this result and answers 201.

    def runs_for_site(self, site_id: str) -> list[Any]:
        """Return every stored record of one site, and record the scan.

        Args:
            site_id: The site that the new run wants to act on.

        Returns:
            The rows a test pinned, or one copy of each record of that site.
        """
        self.scanned.append(site_id)  # The proof that the route asked the store and guessed nothing.
        if self.rows is not None:  # The test pinned an answer, such as a damaged row.
            return list(self.rows)  # A copy, so the test list stays as the test wrote it.
        return [dict(item) for item in self.records.values() if item.get("site_id") == site_id]  # One site.


class TwoMethodStore:
    """A run record store of the two method shape that `runtime/signals` names.

    Why:
        `runtime.signals.RunRecordStore` asks for a reader and a writer only. A
        store of that shape must keep working, because FR-037 must add a check
        and must break no store that already satisfies the published shape.
    """

    def __init__(self) -> None:
        """Start with no record."""
        self.records: dict[str, dict[str, Any]] = {}  # The whole state of this store.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one stored run record.

        Args:
            run_id: The key of the run to read.

        Returns:
            The record, or None when no run holds that key.
        """
        return self.records.get(run_id)  # The first of the two published methods.

    def write_run(self, run: dict[str, Any]) -> bool:
        """Store one run record and report success.

        Args:
            run: The record to store.

        Returns:
            True, because a memory write never fails.
        """
        self.records[str(run["run_id"])] = dict(run)  # The second of the two published methods.
        return True  # The route reads this result and answers 201.


class BrokenScanStore(TwoMethodStore):
    """A store whose site scan fails, as an unreachable database does.

    Why:
        The scan reaches a network in the built portal. A create call must
        survive a store that does not answer, because a refusal built on a fault
        would stop honest work with no cause.
    """

    def runs_for_site(self, site_id: str) -> list[Any]:
        """Fail the scan, as an unreachable database does.

        Args:
            site_id: The site that the new run wants to act on.

        Returns:
            Nothing, because this method always raises.

        Raises:
            RuntimeError: Always, because the store cannot answer.
        """
        raise RuntimeError(f"the store cannot reach the database for {site_id}")  # The fault the route absorbs.


def lock_reader_that_names(holder: str) -> Callable[[str, list[str]], dict[str, str]]:
    """Build a site lock reader that names one holder for every site.

    Why:
        `upgrade.held_by_other` reads the lock through the `SITE_LOCK_READER`
        seam. A test that names the current operator as the holder reproduces the
        exact gap that FR-037 repairs.

    Args:
        holder: The address that the lock store reports for each site.

    Returns:
        The reader callable that the seam accepts.
    """

    def read(org_id: str, site_ids: list[str]) -> dict[str, str]:
        """Return the same holder for each site asked about.

        Args:
            org_id: The organization that owns the sites.
            site_ids: The sites to ask about.

        Returns:
            One entry for each site, all naming the same holder.
        """
        return dict.fromkeys(site_ids, holder)  # The organization plays no part in this stand-in.

    return read  # The test writes this callable into the application configuration.


@pytest.fixture
def run_store() -> SiteAwareStore:
    """Return the store that answers the reader, the writer, and the site scan.

    Returns:
        A fresh store, so no record survives from an earlier test.
    """
    return SiteAwareStore()  # One store for each test keeps every test independent.


@pytest.fixture
def portal_app(run_store: SiteAwareStore) -> Flask:
    """Return a bare application that holds the upgrade blueprint alone.

    Why:
        A bare application holds no other blueprint, so no sibling route and no
        cross-site request forgery guard can change an answer. The store arrives
        through the same configuration seam the built portal uses.

    Args:
        run_store: The stand-in run record store.

    Returns:
        The application, ready for a test client.
    """
    app = Flask(__name__)  # The smallest application that can hold the blueprint.
    app.config.update(TESTING=True, SECRET_KEY=FAKE_SECRET, WTF_CSRF_ENABLED=False)  # Test settings alone.
    app.config[upgrade.RUN_STORE_KEY] = run_store  # The seam the route already reads.
    app.config[LOCK_READER_KEY] = lambda org, sites: dict.fromkeys(sites)  # A reachable store, and no holder.
    app.register_blueprint(upgrade.upgrade_bp)  # The routes under test.
    return app  # Each test drives this application through a client.


@pytest.fixture
def registered_owner() -> Iterator[identity.SessionOwner]:
    """Register one operator and drop the record when the test ends.

    Why:
        The session guard reads the registry on every request. A leaked record
        would sign in a later test by accident, so the fixture clears it.

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
        portal_app: The application with the store injected.
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


@pytest.fixture
def empty_memory_store() -> Iterator[upgrade.MemoryRunStore]:
    """Return the memory store with its shared record table emptied.

    Why:
        The memory store keeps its records in one module level table. A test that
        left a record there could refuse a create call in a later test, so the
        fixture empties the table and puts the earlier content back.

    Yields:
        A memory store that starts with no record.
    """
    held = dict(upgrade._RUNS)  # noqa: SLF001  # WHY: the module owns this table and publishes no reader.
    upgrade._RUNS.clear()  # noqa: SLF001  # WHY: an earlier record would answer this scan and hide a defect.
    try:  # The test body runs against an empty table.
        yield upgrade.MemoryRunStore()  # Every instance reads the same shared table.
    finally:  # The table outlives the test, so put the earlier content back.
        upgrade._RUNS.clear()  # noqa: SLF001  # WHY: drop the records that this test wrote.
        upgrade._RUNS.update(held)  # noqa: SLF001  # WHY: restore the state that the test found.


def seed_run(store: SiteAwareStore, state: str, site_id: str = SITE_ID) -> str:
    """Write one run record straight into the store and return its key.

    Why:
        A test of the second create call needs a first run that already reached a
        named state. Driving the earlier routes would test those routes twice and
        would hide the rule under test.

    Args:
        store: The stand-in run record store.
        state: The state that the seeded run holds.
        site_id: The site that the seeded run acts on.

    Returns:
        The key of the seeded run.
    """
    spec = RunSpec(ORG_ID, "Probe organization", site_id, "Probe site", PROBE_EMAIL, "browser-probe")
    record = RunRecordBuilder().build(spec)  # The record layer owns every field and every default.
    record["state"] = state  # The test names the stage that the first run already reached.
    store.records[str(record["run_id"])] = record  # The store answers the scan with this record.
    return str(record["run_id"])  # The refusal must name this key.


def create_run(client: FlaskClient, site_id: str = SITE_ID) -> TestResponse:
    """Send one create-run call for one site.

    Args:
        client: The signed-in test client.
        site_id: The site named in the path.

    Returns:
        The answer of the route.
    """
    return client.post(f"/api/sites/{site_id}/runs", json={"tier": 2})  # The path of the contract.


def error_code(response: TestResponse) -> str:
    """Read the error code out of one answer.

    Args:
        response: The answer of the route.

    Returns:
        The code, or an empty string when the body carries none.
    """
    body: Any = response.get_json()  # The envelope of `contracts/README.md`.
    return str(body["error"]["code"]) if isinstance(body, dict) else ""  # A missing envelope reads as no code.


def error_details(response: TestResponse) -> dict[str, Any]:
    """Read the optional details object out of one answer.

    Args:
        response: The answer of the route.

    Returns:
        The details object, or an empty dictionary when the body carries none.
    """
    body: Any = response.get_json()  # The same envelope as the code above.
    return dict(body["error"].get("details", {})) if isinstance(body, dict) else {}  # An absent key reads as empty.


def test_a_live_run_refuses_the_second_create(client: FlaskClient, run_store: SiteAwareStore) -> None:
    """A site that already runs an upgrade refuses a new run with 409.

    Args:
        client: The signed-in test client.
        run_store: The stand-in run record store.
    """
    seed_run(run_store, RunState.UPGRADE_RUNNING.value)  # One upgrade of this site is under way.
    answer = create_run(client)  # The operator opens a second tab and starts again.
    assert answer.status_code == upgrade.CONFLICT_STATUS  # The contract fixes 409 for a refused create.
    assert error_code(answer) == upgrade.UPGRADE_RUNNING_CODE  # The FR-037 code, and no other.


def test_the_refusal_names_the_running_run(client: FlaskClient, run_store: SiteAwareStore) -> None:
    """The refusal carries the key of the run that already acts on the site.

    Why:
        The operator must open the first run instead of guessing which run holds
        the site. A refusal that names no run leaves that operator stuck.

    Args:
        client: The signed-in test client.
        run_store: The stand-in run record store.
    """
    first = seed_run(run_store, RunState.SETTLING_SWITCHES.value)  # The run that already holds the site.
    answer = create_run(client)  # The second create call.
    assert error_details(answer).get("run_id") == first  # The operator reads this key and opens that run.


def test_the_refusal_code_differs_from_the_lock_code(client: FlaskClient, run_store: SiteAwareStore) -> None:
    """The FR-037 refusal never reuses the site lock code.

    Why:
        `site_locked` states that a second operator holds the site. A live run is
        a different fact, and one code for both facts is the exact confusion that
        FR-037 exists to repair.

    Args:
        client: The signed-in test client.
        run_store: The stand-in run record store.
    """
    seed_run(run_store, RunState.POST_CAPTURE_RUNNING.value)  # One run of this site has not finished.
    answer = create_run(client)  # No lock exists, so only the FR-037 check can refuse.
    assert error_code(answer) != upgrade.SITE_LOCKED_CODE  # Two facts, two codes.


def test_the_operator_who_holds_the_lock_is_still_refused(
    portal_app: Flask,
    client: FlaskClient,
    run_store: SiteAwareStore,
    registered_owner: identity.SessionOwner,
) -> None:
    """The lock holder who starts a second run is refused, which is the defect.

    Why:
        `held_by_other` lets the current operator pass, and that rule is correct
        for the lock. Before FR-037 the create call had no second check, so the
        operator who started the first run could start a second one over it from
        a second tab. This test is the whole reason the guard exists.

    Args:
        portal_app: The application that holds the lock reader seam.
        client: The signed-in test client.
        run_store: The stand-in run record store.
        registered_owner: The identity pair of the registered operator.
    """
    portal_app.config[LOCK_READER_KEY] = lock_reader_that_names(registered_owner.actor_email)  # Same operator.
    first = seed_run(run_store, RunState.UPGRADE_RUNNING.value)  # The run that this operator already started.
    answer = create_run(client)  # The lock check passes, because the holder is this operator.
    assert answer.status_code == upgrade.CONFLICT_STATUS  # The FR-037 check stops the call instead.
    assert error_code(answer) == upgrade.UPGRADE_RUNNING_CODE  # The lock never reports this fact.
    assert error_details(answer).get("run_id") == first  # The refusal points at the first run.


def test_a_second_operator_still_reads_the_lock_code(
    portal_app: Flask,
    client: FlaskClient,
    run_store: SiteAwareStore,
) -> None:
    """A held site answers the lock code, so FR-037 hides no earlier refusal.

    Why:
        The lock check runs first and names the operator to ask. A live run of the
        same site must not replace that address with a run key, because the second
        operator needs the address and cannot open a run of another operator.

    Args:
        portal_app: The application that holds the lock reader seam.
        client: The signed-in test client.
        run_store: The stand-in run record store.
    """
    portal_app.config[LOCK_READER_KEY] = lock_reader_that_names(OTHER_EMAIL)  # A different operator holds it.
    seed_run(run_store, RunState.UPGRADE_RUNNING.value)  # Both checks would refuse this call.
    answer = create_run(client)  # The lock check runs first.
    assert error_code(answer) == upgrade.SITE_LOCKED_CODE  # The address, never the run key.


@pytest.mark.parametrize("state", TERMINAL_STATES)
def test_a_finished_run_leaves_the_site_free(client: FlaskClient, run_store: SiteAwareStore, state: str) -> None:
    """A run in a final state blocks no new run at the same site.

    Why:
        An operator upgrades the switches today and the access points tomorrow.
        That is normal work, so a finished run must never hold a site.

    Args:
        client: The signed-in test client.
        run_store: The stand-in run record store.
        state: One final state, read from `RunStateMachine.TERMINAL`.
    """
    seed_run(run_store, state)  # Yesterday's run of the same site.
    answer = create_run(client)  # Today's work.
    assert answer.status_code == upgrade.CREATED_STATUS  # The portal created the new run.


@pytest.mark.parametrize("state", LIVE_STATES)
def test_an_unfinished_run_holds_the_site(client: FlaskClient, run_store: SiteAwareStore, state: str) -> None:
    """A run in any state outside the final group refuses a new run.

    Why:
        The guard reads `RunStateMachine.TERMINAL` and never a list typed by hand.
        This test walks every other member of `RunState`, so a state added to the
        model reaches this check with no edit here.

    Args:
        client: The signed-in test client.
        run_store: The stand-in run record store.
        state: One state of `RunState` that the final group leaves out.
    """
    seed_run(run_store, state)  # The first run still holds the site.
    answer = create_run(client)  # The second create call.
    assert error_code(answer) == upgrade.UPGRADE_RUNNING_CODE  # Every unfinished state refuses.


def test_a_run_at_another_site_blocks_nothing(client: FlaskClient, run_store: SiteAwareStore) -> None:
    """A live run at one site leaves every other site free.

    Args:
        client: The signed-in test client.
        run_store: The stand-in run record store.
    """
    seed_run(run_store, RunState.UPGRADE_RUNNING.value, site_id=OTHER_SITE_ID)  # A run of a different site.
    answer = create_run(client)  # The chosen site holds no run at all.
    assert answer.status_code == upgrade.CREATED_STATUS  # The portal created the new run.


def test_the_route_asks_the_store_for_the_chosen_site(client: FlaskClient, run_store: SiteAwareStore) -> None:
    """The guard reads the store through the run store seam and names the site.

    Why:
        A guard that read a second seam would answer from a store that no other
        route writes. The recorded scan proves the route used the one store that
        every worker of the portal shares.

    Args:
        client: The signed-in test client.
        run_store: The stand-in run record store.
    """
    create_run(client)  # No run exists yet, so the call must still perform the scan.
    assert run_store.scanned == [SITE_ID]  # One scan, of the site the path named.


def test_a_store_with_no_site_scan_still_creates_a_run(portal_app: Flask, client: FlaskClient) -> None:
    """A store of the published two method shape refuses no create call.

    Why:
        `runtime.signals.RunRecordStore` asks for a reader and a writer only. A
        store of that shape can answer no site scan, and a guess would stop honest
        work, so the guard continues and the lock check still guards a second
        operator.

    Args:
        portal_app: The application that holds the run store seam.
        client: The signed-in test client.
    """
    portal_app.config[upgrade.RUN_STORE_KEY] = TwoMethodStore()  # No `runs_for_site` at all.
    answer = create_run(client)  # The guard finds no scan and continues.
    assert answer.status_code == upgrade.CREATED_STATUS  # The portal created the new run.


def test_a_failed_site_scan_still_creates_a_run(portal_app: Flask, client: FlaskClient) -> None:
    """A store that cannot answer the scan refuses no create call.

    Why:
        The scan reaches a database in the built portal. A refusal built on an
        unreachable database would stop every upgrade with no cause, so the guard
        records the gap and continues.

    Args:
        portal_app: The application that holds the run store seam.
        client: The signed-in test client.
    """
    portal_app.config[upgrade.RUN_STORE_KEY] = BrokenScanStore()  # The scan raises on every call.
    answer = create_run(client)  # The guard absorbs the fault.
    assert answer.status_code == upgrade.CREATED_STATUS  # The portal created the new run.


def test_a_damaged_row_blocks_no_new_run(client: FlaskClient, run_store: SiteAwareStore) -> None:
    """A row that is not a record reads as no record.

    Why:
        A store may answer a row that no reader can use. The guard must not treat
        that row as a live run, because the operator could then never start a run
        at that site again.

    Args:
        client: The signed-in test client.
        run_store: The stand-in run record store.
    """
    run_store.rows = ["not-a-record", None, 7]  # Three rows that hold no state and no key.
    answer = create_run(client)  # The guard drops every row it cannot read.
    assert answer.status_code == upgrade.CREATED_STATUS  # The portal created the new run.


def test_a_record_with_no_state_blocks_no_new_run(client: FlaskClient, run_store: SiteAwareStore) -> None:
    """A record that names no state reads as a run that finished.

    Why:
        `run_is_live` refuses to guess a state, and a guess that blocked the site
        would need an operator to repair a record before any new upgrade.

    Args:
        client: The signed-in test client.
        run_store: The stand-in run record store.
    """
    run_store.rows = [{"run_id": "run-damaged", "site_id": SITE_ID}]  # A record with no state field.
    answer = create_run(client)  # The guard reads no state and blocks nothing.
    assert answer.status_code == upgrade.CREATED_STATUS  # The portal created the new run.


def test_the_memory_store_answers_one_site_only(empty_memory_store: upgrade.MemoryRunStore) -> None:
    """The memory store scans by site and returns a copy of each record.

    Why:
        The portal runs on the memory store until the database store lands. The
        scan must therefore work there too, or FR-037 would guard nothing today.

    Args:
        empty_memory_store: The memory store with its shared table emptied.
    """
    empty_memory_store.write_run({"run_id": "run-here", "site_id": SITE_ID, "state": RunState.CREATED.value})
    empty_memory_store.write_run({"run_id": "run-there", "site_id": OTHER_SITE_ID, "state": RunState.CREATED.value})
    found = empty_memory_store.runs_for_site(SITE_ID)  # The scan of one site.
    assert [item["run_id"] for item in found] == ["run-here"]  # The other site never appears.


def test_the_memory_store_answers_a_copy(empty_memory_store: upgrade.MemoryRunStore) -> None:
    """An edit of a scanned record never reaches the stored record.

    Why:
        A caller that edited a stored record would change a run that a driver
        thread is writing, and the two writes would then race.

    Args:
        empty_memory_store: The memory store with its shared table emptied.
    """
    empty_memory_store.write_run({"run_id": "run-here", "site_id": SITE_ID, "state": RunState.CREATED.value})
    found = empty_memory_store.runs_for_site(SITE_ID)  # One copy of the stored record.
    found[0]["state"] = RunState.FAILED.value  # An edit of the copy alone.
    assert empty_memory_store.runs_for_site(SITE_ID)[0]["state"] == RunState.CREATED.value  # Unchanged.


def test_the_state_groups_cover_the_whole_model() -> None:
    """The two parametrized groups together hold every state of the model.

    Why:
        A group built from a hand-typed list would drift from `RunState` on the
        day the model gains a state, and a whole branch of FR-037 would then run
        untested with nobody noticing.
    """
    assert sorted(TERMINAL_STATES + LIVE_STATES) == sorted(state.value for state in RunState)
