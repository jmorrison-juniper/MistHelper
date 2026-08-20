"""Integration tests for two operators who drive the portal at one time.

Why:
    The site lock is the one guard between two operators and one upgrade. Each
    rule of that guard already has a contract test, but no test drives two
    signed-in operators through the real application at the same moment. A
    portal that passes every single-operator test can still hand one site to two
    people, and the cost of that fault is a live network.

    These tests therefore build the real application through the factory, sign
    in two operators, and interleave their calls. Five rules are under test:

    1. Two operators hold two different sites at one time. Neither refuses.
    2. A second operator is refused on a site that a first operator holds.
    3. One operator in a second browser tab keeps the same site (FR-074).
    4. One address in a second browser is a second identity, and the portal
       refuses it exactly as it refuses a stranger.
    5. A read never needs the lock, so a held site still answers a reader.

Fixtures:
    Every fixture lives in this file on purpose. `tests/contract/upgrade_portal/`
    holds the shared portal fixtures, and pytest does not share a `conftest.py`
    across two test trees. This module therefore builds its own application.

Personal data:
    No assertion and no log record of this module holds a plain work address.
    Each identity check compares the one-way digest that `runtime/identity.py`
    builds, so a failure report prints a digest and never an address. Every
    address below sits in the reserved `example.invalid` domain, and no fixture
    reads the `.env` file or names a credential.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import json  # The stored lock value is JSON text, so the stand-in store decodes it the same way.
import logging  # The portal package logger must be reached by name, because it stops propagation.
from collections.abc import Callable, Iterator  # The reader seam is a callable, and the owners yield.
from typing import Any  # A stored value, a cloud record, and a request body are all free-form.

import pytest  # The test framework of the project.
from flask import Flask  # The application type of the portal.
from flask.testing import FlaskClient  # The client type that drives every request.
from werkzeug.test import TestResponse  # The answer type that every assertion reads.

from src.upgrade_portal.runtime import identity, lock  # The real session guard and the real lock rules.

LOCK_CLIENT_KEY = "LOCK_STORE_CLIENT"  # The lock store seam, named by `app/routes/select.py`.
LOCK_READER_KEY = "SITE_LOCK_READER"  # The holder reader seam of the same module.
MIST_READER_KEY = "MIST_READER"  # The cloud read seam of the same module.
CSRF_KEY = "WTF_CSRF_ENABLED"  # Every post below carries no token, and `test_capture_start.py` covers the check.

FIRST_EMAIL = "first.operator@example.invalid"  # A reserved domain, so no real address appears.
SECOND_EMAIL = "second.operator@example.invalid"  # The operator that meets a held site.
ORG_ID = "00000000-0000-0000-0000-0000000000aa"  # Matches the shared organization of the other portal tests.
SITE_A_ID = "00000000-0000-0000-0000-0000000000bb"  # The site that the first operator takes.
SITE_B_ID = "00000000-0000-0000-0000-0000000000cc"  # The second site, so two operators never meet.

SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The organization pick inside the signed session.
SELECTED_SITE_SESSION_KEY = "selected_site_id"  # The site pick inside the same signed session.

SITES_API_PATH = "/api/sites"  # `contracts/http-api.md:77` names this read, and a read needs no lock.
SITE_RECORDS: list[dict[str, Any]] = [
    {"id": SITE_A_ID, "name": "Probe site A", "org_id": ORG_ID},  # The site the first operator drives.
    {"id": SITE_B_ID, "name": "Probe site B", "org_id": ORG_ID},  # The site the second operator drives.
]

OK_STATUS = 200  # The take or the read succeeded.
CONFLICT_STATUS = 409  # `contracts/site-lock.md:58` fixes this status for a held site.
SITE_LOCKED_CODE = "site_locked"  # The machine code of that same refusal.

ACQUIRED_STATE = "acquired"  # `LockState.ACQUIRED`, answered when the site was free.
RESUME_STATE = "resume"  # `LockState.RESUMED`, answered when the same owner returns to a live session.

LOCK_STATE_FREE = "free"  # The site list answers this word for a site with no holder.
LOCK_STATE_LOCKED = "locked"  # The same list answers this word for a held site.

EXPECTED_LOCK_COUNT = 1  # One held site, used where a read must add no second lock.

# `app/factory.py` arms this one logger and then stops its propagation, so a plain
# `caplog` on the root logger captures no portal record at all. The name is read
# back from the lock module, so a move of the package keeps this value correct.
PACKAGE_LOGGER_NAME = lock.__name__.rsplit(".", maxsplit=2)[0]  # Reads `src.upgrade_portal`.


class FakeLockStore:
    """Answers the three store commands that the lock module sends.

    Why:
        The lock rules live in `runtime/lock.py`, and these tests must drive the
        real rules and never a stand-in of the rules. This class stands in for
        the store alone, so the atomic take, the compare-and-extend, and the
        compare-and-delete all run as they run against Redis, with no server.

        The class reads the script text instead of a private name, so a rename
        that changes no behavior leaves these tests alone.

    Attributes:
        values: The stored JSON text of each locked site.
        fail: True when every command must raise.
    """

    def __init__(self) -> None:
        """Start with no lock and with every command working."""
        self.values: dict[str, str] = {}  # One stored JSON value for each locked site.
        self.fail = False  # A test sets this flag to make every command raise.

    def _guard(self) -> None:
        """Raise when the test asked the store to be unreachable.

        Raises:
            ConnectionError: When the test set the failure flag.
        """
        if self.fail:  # `contracts/site-lock.md:128` asks a write to fail closed here.
            raise ConnectionError("The stand-in lock store is down for this test.")

    def set(self, key: str, value: str, nx: bool = False, ex: int | None = None) -> bool | None:
        """Write one value, and refuse when `nx` is set and the key exists.

        Why:
            The `NX` flag is the whole race rule. The store decides which of two
            operators wins, so this method must refuse the loser exactly as
            Redis refuses it.

        Args:
            key: The lock key.
            value: The JSON text of the record.
            nx: True when the write must fail on an existing key.
            ex: The life of the key in seconds. The stand-in expires nothing.

        Returns:
            True when the write happened, or None when `nx` refused it.
        """
        self._guard()  # A down store raises before it changes anything.
        del ex  # The stand-in holds no clock, so a test ages a record through its own timestamp.
        if nx and key in self.values:  # The `NX` flag makes the store decide the race.
            return None  # The real client answers None here, and the lock module reads that as a loss.
        self.values[key] = value  # The one place the stand-in keeps a lock.
        return True  # The caller took the lock.

    def get(self, key: str) -> str | None:
        """Read one stored value.

        Args:
            key: The lock key.

        Returns:
            The stored JSON text, or None when no lock exists.
        """
        self._guard()  # A read of a down store raises, and the caller then reports no holder.
        return self.values.get(key)  # An absent key reads as None, never a fault.

    def eval(self, script: str, numkeys: int, key: str, *arguments: Any) -> int:
        """Run one of the three Lua scripts of the contract.

        Why:
            The three scripts share one compare and differ in what follows it.
            The stand-in reads the text for the part that differs, so a rename of
            a private constant leaves these tests alone.

        Args:
            script: The Lua source the lock module sent.
            numkeys: The key count. The contract always sends one.
            key: The lock key.
            *arguments: The token, the fresh value, and the life.

        Returns:
            1 when the script wrote, or 0 when the compare refused.
        """
        self._guard()  # A down store raises, and the beat or the release then fails closed.
        del numkeys  # Every script of the contract names exactly one key.
        current = self.values.get(key)  # The value the compare reads.
        token = str(arguments[0])  # Every script compares this token first.
        if "DEL" in script:  # The release script.
            return self._compare_and_delete(key, current, token)
        if "if not current" in script:  # The refresh script, which never revives an absent key.
            return self._compare_and_write(key, current, token, arguments, revive=False)
        return self._compare_and_write(key, current, token, arguments, revive=True)  # The takeover script.

    def _compare_and_delete(self, key: str, current: str | None, token: str) -> int:
        """Delete the lock only while the caller token is the stored one.

        Args:
            key: The lock key.
            current: The stored JSON text, or None.
            token: The token the caller named.

        Returns:
            1 when the delete happened, or 0 when the compare refused.
        """
        if current is None or json.loads(current).get("lock_token") != token:  # A moved lock refuses.
            return 0  # The lock module raises `LockLostError` on this answer.
        del self.values[key]  # The site is free again.
        return 1  # The caller released its own lock.

    def _compare_and_write(self, key: str, current: str | None, token: str, arguments: Any, revive: bool) -> int:
        """Write a fresh value only while the caller token is the stored one.

        Args:
            key: The lock key.
            current: The stored JSON text, or None.
            token: The token the caller named.
            arguments: The script arguments, holding the fresh value in slot two.
            revive: True when an absent key still allows the write.

        Returns:
            1 when the write happened, or 0 when the compare refused.
        """
        if current is None:  # The lock expired between the read and the write.
            if not revive:  # A beat must never bring a dead lock back.
                return 0  # The lock module raises `LockLostError` on this answer.
        elif json.loads(current).get("lock_token") != token:  # A third party changed the lock first.
            return 0  # The lock module raises on this answer as well.
        self.values[key] = str(arguments[1])  # The fresh record of the caller.
        return 1  # The caller now holds the site.


# ---------------------------------------------------------------------------
# Seams
# ---------------------------------------------------------------------------


def read_cloud(name: str, **parameters: Any) -> list[dict[str, Any]]:
    """Answer one cloud read with the two sites of this module.

    Why:
        The site list reads the cloud twice. This stand-in answers the site
        records and answers nothing for the statistics, so the site list renders
        with no cloud account and every device count reads zero.

    Args:
        name: The name of the cloud read.
        **parameters: The call parameters. This stand-in holds one organization.

    Returns:
        The two site records, or an empty list for any other read.
    """
    del parameters  # One organization owns both sites, so no parameter changes the answer.
    return SITE_RECORDS if name == "listOrgSites" else []  # An unknown read answers empty, never a fault.


def bind_lock_reader(store: FakeLockStore) -> Callable[[str, list[str]], dict[str, str | None]]:
    """Bind the real holder reader of the lock module to the stand-in store.

    Why:
        A stand-in reader that always answers no holder is more permissive than
        the real reader, and it would hide the very fault these tests exist to
        catch. This binding runs `lock.read_site_locks` itself, so the site list
        names a holder whenever the write path stored one.

    Args:
        store: The stand-in lock store that the write path also uses.

    Returns:
        The two-argument reader that `app/routes/select.py` calls.
    """

    def read_holders(org_id: str, site_ids: list[str]) -> dict[str, str | None]:
        """Return the address of the operator that holds each named site.

        Args:
            org_id: The organization that owns the sites.
            site_ids: The sites the page lists.

        Returns:
            The holder of each site, or None for a free site.
        """
        return lock.read_site_locks(org_id, site_ids, client=store)  # The production reader, and no other rule.

    return read_holders  # The site list reaches the stand-in store through the real reader.


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def lock_store() -> FakeLockStore:
    """Return a fresh stand-in lock store.

    Returns:
        An empty store with every command working.
    """
    return FakeLockStore()  # Each test starts with no lock at all.


@pytest.fixture
def portal_app() -> Flask:
    """Return the capture portal application in test mode.

    Why:
        These tests drive the real routes, so they need the real application.
        The guarded import skips the module instead of failing collection, which
        keeps the whole suite collectable while the portal grows.

    Returns:
        The Flask application with the test settings applied.
    """
    factory = pytest.importorskip(  # The factory arrives at task T027.
        "src.upgrade_portal.app.factory",
        reason="The capture portal application factory is not built yet.",
    )
    application: Flask = factory.create_app()  # The real factory, with no argument.
    application.config.update(TESTING=True)  # Test mode reports the real exception instead of a 500 page.
    return application  # Every fixture below adds its seams to this application.


@pytest.fixture
def portal(portal_app: Flask, lock_store: FakeLockStore) -> Flask:
    """Return the portal with the store, the cloud reader, and the holder reader in place.

    Why:
        Three seams keep these tests free of Redis and free of a cloud account.
        All three point at the same stand-in store, so a lock that one operator
        takes through a write is the lock that a second operator reads.

    Args:
        portal_app: The real application.
        lock_store: The stand-in lock store.

    Returns:
        The application with every seam in place.
    """
    portal_app.config[LOCK_CLIENT_KEY] = lock_store  # Every lock write lands in the stand-in store.
    portal_app.config[MIST_READER_KEY] = read_cloud  # The site list then needs no cloud account.
    portal_app.config[LOCK_READER_KEY] = bind_lock_reader(lock_store)  # The reader names a real holder.
    portal_app.config[CSRF_KEY] = False  # Another module already covers the token check.
    return portal_app  # Every test below drives this application.


@pytest.fixture
def first_owner() -> Iterator[identity.SessionOwner]:
    """Register the operator that takes a site first.

    Yields:
        The identity pair of the first operator.
    """
    yield from register_owner(FIRST_EMAIL)  # One helper serves every operator of this module.


@pytest.fixture
def second_owner() -> Iterator[identity.SessionOwner]:
    """Register the operator that meets a held site.

    Yields:
        The identity pair of the second operator.
    """
    yield from register_owner(SECOND_EMAIL)  # A different address and a different browser.


@pytest.fixture
def second_browser_owner() -> Iterator[identity.SessionOwner]:
    """Register the first address again, on a second browser.

    Why:
        FR-073 pairs the address with the browser, so this fixture holds the
        same address as `first_owner` and a fresh browser identifier. The pair
        differs, which is what makes case four a separate identity.

    Yields:
        The identity pair of the first address on a second browser.
    """
    yield from register_owner(FIRST_EMAIL)  # `issue_browser_id` answers a fresh value on every call.


@pytest.fixture
def portal_log(portal: Flask, caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    """Capture the log records that the portal package writes.

    Why:
        `app/factory.py` stops the propagation of the package logger, because the
        root handler of the host process does not know the two extra fields of
        the portal format. The pytest capture handler binds to such a logger at
        the start of a test phase. The build runs in the fixture step, so the
        first phase of a session captures no portal record at all.

        This fixture binds the capture handler for the test body in every case.
        The check below also asserts on a digest that must be present. An empty
        capture therefore fails, and the check cannot pass without evidence.

    Args:
        portal: The application, which arms the package logger during the build.
        caplog: The capture fixture of the run.

    Yields:
        The capture fixture, now attached to the portal package logger.
    """
    del portal  # Named only for the order, because the build sets the level and stops propagation.
    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)  # The one logger that every portal module feeds.
    package_logger.addHandler(caplog.handler)  # A repeat call is safe, because `addHandler` skips a duplicate.
    try:  # The test body runs with the capture in place.
        yield caplog  # Every assertion reads the captured text.
    finally:  # A leaked handler would capture the records of every later test.
        package_logger.removeHandler(caplog.handler)  # The logger outlives the test, so clear it here.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def register_owner(actor_email: str) -> Iterator[identity.SessionOwner]:
    """Register one operator and drop the record afterward.

    Why:
        The guard admits a request only when the signed session and the browser
        cookie both name a registered owner. The registry is a process global,
        so a leaked record would sign a later test in by accident.

    Args:
        actor_email: The work address of the operator.

    Yields:
        The identity pair of the registered operator.
    """
    owner = identity.build_owner(actor_email, identity.issue_browser_id())  # The pair the guard checks.
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


def open_client(application: Flask, owner: identity.SessionOwner, site_id: str) -> FlaskClient:
    """Return one signed-in client that already picked the organization and a site.

    Why:
        The client is not held open with a `with` block on purpose. That block
        keeps the request context of the last call alive, and two clients that
        both hold one then pop the Flask contexts out of order. Every test below
        interleaves two clients, so the block would break them all.

    Args:
        application: The portal application with every seam in place.
        owner: The identity pair of the operator.
        site_id: The site this browser picked.

    Returns:
        The Flask test client of that operator.
    """
    client = application.test_client()  # A fresh cookie jar for this browser.
    client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # Half of the guard.
    with client.session_transaction() as browser_session:  # The other half of the guard.
        browser_session[identity.SESSION_OWNER_KEY] = owner.key  # Names the registered owner.
        browser_session[SELECTED_ORG_SESSION_KEY] = ORG_ID  # The organization picker writes this field.
        browser_session[SELECTED_SITE_SESSION_KEY] = site_id  # The site picker writes this field.
    return client  # The caller drives this client.


def take_lock(client: FlaskClient, site_id: str, confirm: str = "") -> TestResponse:
    """Ask for the lock on one site.

    Args:
        client: The signed-in client of one operator.
        site_id: The site to take.
        confirm: The word the operator typed. An empty value asks for a plain take.

    Returns:
        The answer of the lock endpoint.
    """
    return client.post(f"/api/sites/{site_id}/lock", json={"confirm": confirm})  # One path serves every way in.


def read_error_code(answer: TestResponse) -> str:
    """Return the machine code of one refusal.

    Args:
        answer: The refusal the portal sent.

    Returns:
        The code, or an empty string when the body carries none.
    """
    body: Any = answer.get_json() or {}  # A body of another shape reads as empty, never a fault.
    return str(body.get("error", {}).get("code", ""))  # `contracts/http-api.md` fixes this envelope.


def read_error_details(answer: TestResponse) -> dict[str, Any]:
    """Return the detail block of one refusal.

    Args:
        answer: The refusal the portal sent.

    Returns:
        The detail block, or an empty dictionary when the refusal carries none.
    """
    body: Any = answer.get_json() or {}  # A body of another shape reads as empty, never a fault.
    details: Any = body.get("error", {}).get("details") or {}  # Two refusals carry a block and the rest carry none.
    return dict(details)  # A copy stops a later edit of the parsed body.


def stored_token(store: FakeLockStore, site_id: str) -> str:
    """Return the lock token that the store holds for one site.

    Why:
        A refusal must leave the first lock untouched. Reading the token proves
        that, and it reads the store instead of the answer of the loser.

    Args:
        store: The stand-in lock store.
        site_id: The site to read.

    Returns:
        The stored token, or an empty string when the site is free.
    """
    value = store.values.get(lock.build_key(ORG_ID, site_id))  # None means the site holds no lock.
    return str(json.loads(value).get("lock_token", "")) if value else ""  # An absent lock reads as no token.


def site_row(answer: TestResponse, site_id: str) -> dict[str, Any]:
    """Return one row of the site list.

    Args:
        answer: The answer of the site list.
        site_id: The site to find.

    Returns:
        The row of that site.

    Raises:
        AssertionError: When the list holds no row for that site.
    """
    rows: list[dict[str, Any]] = (answer.get_json() or {}).get("sites", [])  # An empty body reads as no row.
    for row in rows:  # One pass, because the first match ends the search.
        if row.get("site_id") == site_id:  # The one site the caller named.
            return row
    raise AssertionError(f"The site list holds no row for the site {site_id}.")  # A missing row is a fault.


def digest_of(value: Any) -> str:
    """Return the one-way digest of one work address.

    Why:
        A failing assertion prints both compared values. Comparing digests keeps
        a plain address out of every failure report and out of every log record,
        which is the rule that `runtime/identity.py` states for personal data.

    Args:
        value: The address to reduce, in any type.

    Returns:
        The digest of that address.
    """
    return identity.email_digest(str(value))  # The same reduction the lock module writes to its log.


# ---------------------------------------------------------------------------
# Case 1. Two operators, two sites, one moment. FR-074.
# ---------------------------------------------------------------------------


def test_two_operators_take_two_sites_at_one_time(
    portal: Flask,
    first_owner: identity.SessionOwner,
    second_owner: identity.SessionOwner,
) -> None:
    """Two operators each take a different site, and neither refusal fires.

    Why:
        The lock is per site and never per portal. A guard that locked the whole
        portal would pass every single-operator test and would still stop a
        second team from working during a maintenance window.

    Args:
        portal: The application with every seam in place.
        first_owner: The operator that takes site A.
        second_owner: The operator that takes site B.
    """
    first = open_client(portal, first_owner, SITE_A_ID)  # One browser for each operator.
    second = open_client(portal, second_owner, SITE_B_ID)  # A separate cookie jar and a separate identity.

    answers = [take_lock(first, SITE_A_ID), take_lock(second, SITE_B_ID)]  # Interleaved, in one moment.

    assert [answer.status_code for answer in answers] == [OK_STATUS, OK_STATUS]  # No refusal at all.
    assert [answer.get_json()["state"] for answer in answers] == [ACQUIRED_STATE, ACQUIRED_STATE]  # Both were free.


def test_two_sites_keep_two_separate_lock_records(
    portal: Flask,
    lock_store: FakeLockStore,
    first_owner: identity.SessionOwner,
    second_owner: identity.SessionOwner,
) -> None:
    """Each site keeps its own key and its own token.

    Why:
        A shared key would let the second take overwrite the first, and the
        first operator would then beat a lock that no longer belongs to it.

    Args:
        portal: The application with every seam in place.
        lock_store: The stand-in lock store.
        first_owner: The operator that takes site A.
        second_owner: The operator that takes site B.
    """
    take_lock(open_client(portal, first_owner, SITE_A_ID), SITE_A_ID)  # The first operator takes site A.
    take_lock(open_client(portal, second_owner, SITE_B_ID), SITE_B_ID)  # The second operator takes site B.

    keys = set(lock_store.values)  # Every key the store now holds.

    assert keys == {lock.build_key(ORG_ID, SITE_A_ID), lock.build_key(ORG_ID, SITE_B_ID)}  # One key for each site.
    assert stored_token(lock_store, SITE_A_ID) != stored_token(lock_store, SITE_B_ID)  # Two separate tokens.


# ---------------------------------------------------------------------------
# Case 2. One site, two operators. `contracts/site-lock.md:58`.
# ---------------------------------------------------------------------------


def test_a_second_operator_is_refused_on_a_held_site(
    portal: Flask,
    first_owner: identity.SessionOwner,
    second_owner: identity.SessionOwner,
) -> None:
    """The second operator reads 409 and the code `site_locked`.

    Why:
        FR-077 blocks every write of an operator that does not hold the site.
        This is the one refusal that stops two people from upgrading one site
        together, so the status and the code are both part of the contract.

    Args:
        portal: The application with every seam in place.
        first_owner: The operator that holds the site.
        second_owner: The operator that arrives second.
    """
    holder = open_client(portal, first_owner, SITE_A_ID)  # The operator that wins the race.
    arrival = open_client(portal, second_owner, SITE_A_ID)  # The operator that meets the held site.
    take_lock(holder, SITE_A_ID)  # The site is now held and active.

    refused = take_lock(arrival, SITE_A_ID)  # The same site, from a second identity.

    assert refused.status_code == CONFLICT_STATUS  # `contracts/site-lock.md:58` fixes this status.
    assert read_error_code(refused) == SITE_LOCKED_CODE  # The same line fixes this machine code.


def test_the_refusal_names_the_holder_and_the_wait(
    portal: Flask,
    first_owner: identity.SessionOwner,
    second_owner: identity.SessionOwner,
) -> None:
    """The refusal carries the holder and the seconds left of the cooldown.

    Why:
        `contracts/http-api.md:103` asks for both values, so the waiting
        operator learns who holds the site and how long the wait lasts. The
        check compares digests, so no plain address enters a failure report.

    Args:
        portal: The application with every seam in place.
        first_owner: The operator that holds the site.
        second_owner: The operator that arrives second.
    """
    holder = open_client(portal, first_owner, SITE_A_ID)  # The operator that wins the race.
    arrival = open_client(portal, second_owner, SITE_A_ID)  # The operator that meets the held site.
    take_lock(holder, SITE_A_ID)  # The site is now held and active.

    details = read_error_details(take_lock(arrival, SITE_A_ID))  # The detail block of the refusal.

    assert digest_of(details["actor_email"]) == digest_of(FIRST_EMAIL)  # The block names the holder.
    assert details["cooldown_remaining"] > 0  # A fresh hold leaves the whole quiet window ahead.


def test_a_refusal_leaves_the_first_lock_in_place(
    portal: Flask,
    lock_store: FakeLockStore,
    first_owner: identity.SessionOwner,
    second_owner: identity.SessionOwner,
) -> None:
    """The refused operator changes no stored token.

    Why:
        A refusal that still wrote would hand the site to the loser of the race.
        Reading the token back from the store proves the first lock survived.

    Args:
        portal: The application with every seam in place.
        lock_store: The stand-in lock store.
        first_owner: The operator that holds the site.
        second_owner: The operator that arrives second.
    """
    holder = open_client(portal, first_owner, SITE_A_ID)  # The operator that wins the race.
    arrival = open_client(portal, second_owner, SITE_A_ID)  # The operator that meets the held site.
    granted = take_lock(holder, SITE_A_ID).get_json()["lock_token"]  # The token of the holder.

    take_lock(arrival, SITE_A_ID)  # The refused take, whose answer this test ignores.

    assert stored_token(lock_store, SITE_A_ID) == granted  # The store still holds the first token.


# ---------------------------------------------------------------------------
# Case 3. One operator, two browser tabs. FR-074.
# ---------------------------------------------------------------------------


def test_a_second_tab_of_one_operator_keeps_the_same_site(
    portal: Flask,
    first_owner: identity.SessionOwner,
) -> None:
    """A second tab of one browser resumes the site and asks for no typed word.

    Why:
        FR-074 states that one person in two tabs is one identity. A portal that
        refused the second tab would teach the operator to take the site over
        from themself, and a takeover erases the work that is in flight.

    Args:
        portal: The application with every seam in place.
        first_owner: The one operator, in both tabs.
    """
    first_tab = open_client(portal, first_owner, SITE_A_ID)  # One address and one browser identifier.
    second_tab = open_client(portal, first_owner, SITE_A_ID)  # The same pair, so the same identity.
    granted = take_lock(first_tab, SITE_A_ID).get_json()  # The first tab takes the site.

    resumed = take_lock(second_tab, SITE_A_ID)  # The second tab asks for the same site.

    assert resumed.status_code == OK_STATUS  # One person in two tabs is never refused.
    assert resumed.get_json()["state"] == RESUME_STATE  # `contracts/site-lock.md:57` names this state.
    assert resumed.get_json()["lock_token"] == granted["lock_token"]  # The same lock, and never a second one.


def test_one_operator_holds_two_sites_in_two_tabs(
    portal: Flask,
    first_owner: identity.SessionOwner,
) -> None:
    """One operator drives two sites at one time from two tabs.

    Why:
        FR-074 states this rule by name. An engineer often upgrades two sites in
        one maintenance window, so a per-operator lock would halve the work that
        one person can do in that window.

    Args:
        portal: The application with every seam in place.
        first_owner: The one operator, in both tabs.
    """
    first_tab = open_client(portal, first_owner, SITE_A_ID)  # The tab that drives site A.
    second_tab = open_client(portal, first_owner, SITE_B_ID)  # The tab that drives site B.

    answers = [take_lock(first_tab, SITE_A_ID), take_lock(second_tab, SITE_B_ID)]  # Interleaved, in one moment.

    assert [answer.status_code for answer in answers] == [OK_STATUS, OK_STATUS]  # No refusal at all.
    assert [answer.get_json()["state"] for answer in answers] == [ACQUIRED_STATE, ACQUIRED_STATE]  # Both were free.


# ---------------------------------------------------------------------------
# Case 4. One address, two browsers. FR-073.
# ---------------------------------------------------------------------------


def test_a_second_browser_of_one_address_is_a_second_identity(
    first_owner: identity.SessionOwner,
    second_browser_owner: identity.SessionOwner,
) -> None:
    """One address on two browsers builds two different identity pairs.

    Why:
        `runtime/identity.py` states that the same address on a second computer
        is a different identity. The frozen owner compares both halves, so this
        test pins the rule that decides every answer below.

    Args:
        first_owner: The address on its first browser.
        second_browser_owner: The same address on a second browser.
    """
    assert first_owner.email_digest == second_browser_owner.email_digest  # One person, so one digest.
    assert first_owner.browser_id != second_browser_owner.browser_id  # Two browsers, so two cookies.
    assert first_owner != second_browser_owner  # The pair differs, so the lock treats them apart.


def test_a_second_browser_of_one_address_is_refused_on_a_held_site(
    portal: Flask,
    first_owner: identity.SessionOwner,
    second_browser_owner: identity.SessionOwner,
) -> None:
    """One address in a second browser reads the same refusal as a stranger.

    Why:
        This is the behavior the code has today, and it is worth pinning because
        it surprises an operator. The refusal names the holder, and the holder is
        the same person who is reading the refusal.

    Args:
        portal: The application with every seam in place.
        first_owner: The address on its first browser.
        second_browser_owner: The same address on a second browser.
    """
    holder = open_client(portal, first_owner, SITE_A_ID)  # The browser that wins the race.
    other = open_client(portal, second_browser_owner, SITE_A_ID)  # The same address, a second browser.
    take_lock(holder, SITE_A_ID)  # The site is now held and active.

    refused = take_lock(other, SITE_A_ID)  # The same site, from the second browser.

    assert refused.status_code == CONFLICT_STATUS  # A second browser is refused, exactly like a stranger.
    assert read_error_code(refused) == SITE_LOCKED_CODE  # The same code that a second operator reads.


def test_a_second_browser_reads_its_own_address_as_the_holder(
    portal: Flask,
    first_owner: identity.SessionOwner,
    second_browser_owner: identity.SessionOwner,
) -> None:
    """The refusal of a second browser names the address of the reader.

    Why:
        The operator reads a refusal that names their own address. The page must
        therefore explain that a second browser starts a second session, because
        an operator who reads their own name will otherwise think the portal is
        broken and will type CONFIRM to take the site from themself.

    Args:
        portal: The application with every seam in place.
        first_owner: The address on its first browser.
        second_browser_owner: The same address on a second browser.
    """
    holder = open_client(portal, first_owner, SITE_A_ID)  # The browser that wins the race.
    other = open_client(portal, second_browser_owner, SITE_A_ID)  # The same address, a second browser.
    take_lock(holder, SITE_A_ID)  # The site is now held and active.

    details = read_error_details(take_lock(other, SITE_A_ID))  # The detail block of the refusal.

    assert digest_of(details["actor_email"]) == digest_of(FIRST_EMAIL)  # The reader reads their own address.


# ---------------------------------------------------------------------------
# Case 5. A read is never blocked. `contracts/site-lock.md:15`.
# ---------------------------------------------------------------------------


def test_the_site_list_answers_while_another_operator_holds_a_site(
    portal: Flask,
    first_owner: identity.SessionOwner,
    second_owner: identity.SessionOwner,
) -> None:
    """`GET /api/sites` answers 200 for an operator that holds no lock.

    Why:
        A second operator checks the work of the first while that work runs. A
        read that waited for the lock would make that check impossible during
        the exact window in which it matters.

    Args:
        portal: The application with every seam in place.
        first_owner: The operator that holds the site.
        second_owner: The operator that only reads.
    """
    holder = open_client(portal, first_owner, SITE_A_ID)  # The operator that takes the site.
    reader = open_client(portal, second_owner, SITE_B_ID)  # The operator that holds no lock on site A.
    take_lock(holder, SITE_A_ID)  # The site is now held and active.

    listed = reader.get(SITES_API_PATH)  # A plain read, with no lock and no typed word.

    assert listed.status_code == OK_STATUS  # A read needs no lock at all.


def test_the_site_list_names_the_holder_of_a_held_site(
    portal: Flask,
    first_owner: identity.SessionOwner,
    second_owner: identity.SessionOwner,
) -> None:
    """The row of a held site reads `locked` and names the holder.

    Why:
        The reader must see that the site is busy before opening it. A row that
        read free would send the second operator into a site that the first
        operator is upgrading.

    Args:
        portal: The application with every seam in place.
        first_owner: The operator that holds the site.
        second_owner: The operator that only reads.
    """
    holder = open_client(portal, first_owner, SITE_A_ID)  # The operator that takes the site.
    reader = open_client(portal, second_owner, SITE_B_ID)  # The operator that holds no lock on site A.
    take_lock(holder, SITE_A_ID)  # The site is now held and active.

    row = site_row(reader.get(SITES_API_PATH), SITE_A_ID)  # The row of the held site.

    assert row["lock_state"] == LOCK_STATE_LOCKED  # The page marks the site busy.
    assert digest_of(row["locked_by"]) == digest_of(FIRST_EMAIL)  # The row names the holder.


def test_the_site_list_shows_a_free_site_beside_a_held_one(
    portal: Flask,
    first_owner: identity.SessionOwner,
    second_owner: identity.SessionOwner,
) -> None:
    """The row of a free site still reads `free` while another site is held.

    Why:
        One held site must never mark the whole organization busy. The free row
        is what tells the second operator where the work may continue.

    Args:
        portal: The application with every seam in place.
        first_owner: The operator that holds site A.
        second_owner: The operator that only reads.
    """
    holder = open_client(portal, first_owner, SITE_A_ID)  # The operator that takes site A.
    reader = open_client(portal, second_owner, SITE_B_ID)  # The operator that holds no lock on site A.
    take_lock(holder, SITE_A_ID)  # Site A is now held and active.

    row = site_row(reader.get(SITES_API_PATH), SITE_B_ID)  # The row of the site that nobody holds.

    assert row["lock_state"] == LOCK_STATE_FREE  # Site B stays open for work.
    assert row["locked_by"] is None  # `contracts/http-api.md:79` fixes this value for a free site.


def test_a_read_takes_no_lock_of_its_own(
    portal: Flask,
    lock_store: FakeLockStore,
    first_owner: identity.SessionOwner,
    second_owner: identity.SessionOwner,
) -> None:
    """A read of the site list writes no lock at all.

    Why:
        A read that quietly took a lock would answer 200 and would still block
        the next operator. Counting the stored keys after the read proves that
        the reader took nothing, which a status check alone would never catch.

    Args:
        portal: The application with every seam in place.
        lock_store: The stand-in lock store.
        first_owner: The operator that holds site A.
        second_owner: The operator that only reads.
    """
    holder = open_client(portal, first_owner, SITE_A_ID)  # The operator that takes site A.
    reader = open_client(portal, second_owner, SITE_B_ID)  # The operator that holds no lock on site A.
    take_lock(holder, SITE_A_ID)  # One key now sits in the store.

    reader.get(SITES_API_PATH)  # The read under test, whose body this test ignores.

    assert len(lock_store.values) == EXPECTED_LOCK_COUNT  # The read added no second key.


def test_the_reader_may_still_take_the_free_site_it_read(
    portal: Flask,
    first_owner: identity.SessionOwner,
    second_owner: identity.SessionOwner,
) -> None:
    """A reader of a held site still takes the free site of the same list.

    Why:
        The read must leave the reader free to act. This test joins case 1 and
        case 5, because it proves that reading a busy site costs the reader
        nothing on the site where the work may continue.

    Args:
        portal: The application with every seam in place.
        first_owner: The operator that holds site A.
        second_owner: The operator that reads, then takes site B.
    """
    holder = open_client(portal, first_owner, SITE_A_ID)  # The operator that takes site A.
    reader = open_client(portal, second_owner, SITE_B_ID)  # The operator that reads the list first.
    take_lock(holder, SITE_A_ID)  # Site A is now held and active.
    reader.get(SITES_API_PATH)  # The read that must cost the reader nothing.

    taken = take_lock(reader, SITE_B_ID)  # The free site of the same list.

    assert taken.status_code == OK_STATUS  # The reader still works on the free site.


# ---------------------------------------------------------------------------
# Personal data. `runtime/identity.py` states the rule for a log record.
# ---------------------------------------------------------------------------


def test_no_lock_log_record_holds_a_plain_address(
    portal: Flask,
    first_owner: identity.SessionOwner,
    second_owner: identity.SessionOwner,
    portal_log: pytest.LogCaptureFixture,
) -> None:
    """The lock log names each operator by digest and never by address.

    Why:
        A portal log travels to a shared collector, so a work address in one log
        line becomes personal data in a system that nobody scoped for it. Two
        operators and one refusal exercise every log line of the acquire path.

        The digest check comes first on purpose. It fails on an empty capture,
        so this test can never pass because the records went somewhere else.

    Args:
        portal: The application with every seam in place.
        first_owner: The operator that holds the site.
        second_owner: The operator that meets the held site.
        portal_log: The capture attached to the portal package logger.
    """
    holder = open_client(portal, first_owner, SITE_A_ID)  # The operator that takes site A.
    arrival = open_client(portal, second_owner, SITE_A_ID)  # The operator that meets the held site.
    take_lock(holder, SITE_A_ID)  # One granted take, which the acquire path logs.
    take_lock(arrival, SITE_A_ID)  # One refused take.

    written = portal_log.text  # Every captured line of both calls.

    assert first_owner.email_digest in written  # Proves the capture works, so no empty text can pass.
    assert FIRST_EMAIL not in written  # No line holds the address of the holder.
    assert SECOND_EMAIL not in written  # No line holds the address of the second operator.
