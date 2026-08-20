"""Contract tests that a read needs no site lock and no typed word.

Why:
    `contracts/site-lock.md` line 15 states that an operator may view a site, a
    capture, a comparison, or a history page with no lock and with no typed
    text. Line 128 repeats the rule for the two read pages by name. A read that
    started to ask for a lock would block a second operator from checking the
    work of the first, which is the exact review the portal exists to support.

    The rule is easy to break by accident, because the lock banner and the read
    pages share one layout. These tests therefore prove three separate things:
    a read answers with no lock at all, a read answers while a different
    operator holds the site, and a read answers while the lock store is down.

Scope:
    The comparison page, the comparison endpoint, the comparison download, and
    the history page. Each test counts every call into the lock store, so a
    read that started to consult the lock fails here even when it still answers
    200.

Fixtures:
    Every fixture lives in this file on purpose. `conftest.py` is shared with
    other test modules, and a counting lock store belongs to these tests alone.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

from collections.abc import Iterator  # The owner fixture yields and then clears the registry.
from datetime import UTC, datetime  # A seeded lock record needs two timestamps.
from typing import Any  # A stored capture is a free-form document.

import pytest  # The test framework of the project.
from flask import Flask  # The application type of the portal.
from flask.testing import FlaskClient  # The client type that drives every request.
from werkzeug.test import TestResponse  # The answer type that every assertion reads.

from src.upgrade_portal.runtime import identity, lock  # The real session guard and the real lock record.

LOCK_CLIENT_KEY = "LOCK_STORE_CLIENT"  # The lock store seam, named by `app/routes/select.py`.
CAPTURE_LOADER_KEY = "CAPTURE_LOADER"  # The capture reader seam, named by `app/routes/review.py`.
CAPTURE_LISTER_KEY = "CAPTURE_LISTER"  # The picker reader seam of the same module.

READER_EMAIL = "reader.operator@example.invalid"  # A reserved domain, so no real address appears.
HOLDER_EMAIL = "holder.operator@example.invalid"  # The operator that holds the site during a read.
ORG_ID = "00000000-0000-0000-0000-0000000000aa"  # Matches the shared organization of the other tests.
SITE_ID = "00000000-0000-0000-0000-0000000000bb"  # Matches the shared site of the other tests.

SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The organization pick inside the signed session.
SELECTED_SITE_SESSION_KEY = "selected_site_id"  # The site pick inside the same signed session.

COMPARE_PAGE_PATH = "/compare"  # `contracts/http-api.md:341` names this path.
COMPARISONS_API_PATH = "/api/comparisons"  # `contracts/http-api.md:296` names this path.
COMPARISONS_EXPORT_API_PATH = "/api/comparisons/export"  # `contracts/http-api.md:345` names this path.
HISTORY_PAGE_PATH = "/history"  # `contracts/http-api.md:364` names this path.
HISTORY_API_PATH = f"/api/sites/{SITE_ID}/history"  # `contracts/http-api.md:353` names this path.

BEFORE_CAPTURE_ID = "capture-before-0001"  # The pre-check capture of every comparison below.
AFTER_CAPTURE_ID = "capture-after-0001"  # The post-check capture of every comparison below.

OK_STATUS = 200  # Every read of this module must answer this status.

TAKEOVER_WORD = "CONFIRM"  # FR-079 asks for this word before a takeover, and never before a read.
RESUME_WORD = "continue"  # FR-080 asks for this word before a resume, and never before a read.

DEVICE_MAC = "aabbcc000001"  # One device that both captures hold.
CLIENT_MAC = "ddeeff000001"  # One client that both captures hold.

BEFORE_CAPTURE: dict[str, Any] = {
    "capture_id": BEFORE_CAPTURE_ID,
    "site_id": SITE_ID,
    "site_name": "Probe site",
    "org_name": "Probe organization",
    "role": "pre",
    "capture_status": "verified",
    "started_at": "2026-08-19T10:00:00+00:00",
    "finished_at": "2026-08-19T10:05:00+00:00",
    "device_index": {DEVICE_MAC: {"name": "core-switch", "status": "connected", "version": "0.14.29644"}},
    "clients": {"wireless": [{"mac": CLIENT_MAC, "hostname": "desk-one", "device_mac": DEVICE_MAC}]},
}

AFTER_CAPTURE: dict[str, Any] = {
    **BEFORE_CAPTURE,
    "capture_id": AFTER_CAPTURE_ID,
    "role": "post",
    "started_at": "2026-08-19T10:25:00+00:00",
    "finished_at": "2026-08-19T10:30:00+00:00",
    "device_index": {DEVICE_MAC: {"name": "core-switch", "status": "connected", "version": "0.16.30107"}},
}

CAPTURE_ROWS: list[dict[str, Any]] = [
    {"capture_id": BEFORE_CAPTURE_ID, "role": "pre", "started_at": BEFORE_CAPTURE["started_at"]},
    {"capture_id": AFTER_CAPTURE_ID, "role": "post", "started_at": AFTER_CAPTURE["started_at"]},
]


class CountingLockStore:
    """Answers no lock and counts every command it receives.

    Why:
        A read that answers 200 still breaks the contract when it consulted the
        lock on the way. Counting the calls turns that quiet fault into a plain
        failure, which a status assertion alone would never catch.

    Attributes:
        calls: The name of each command received, in order.
        values: The stored value of each locked site.
        fail: True when every command must raise.
    """

    def __init__(self) -> None:
        """Start with no lock, no calls, and every command working."""
        self.calls: list[str] = []  # Each command name, so a failure names the call that broke the rule.
        self.values: dict[str, str] = {}  # One stored JSON value for each locked site.
        self.fail = False  # A test sets this flag to make every command raise.

    def seed(self, key: str, value: str) -> None:
        """Write one lock without counting the write.

        Why:
            A test that seeds a holder must still assert that the read made no
            call. Seeding through `set` would count the write of the test itself
            and hide the fault the count exists to find.

        Args:
            key: The lock key.
            value: The JSON text of the record.
        """
        self.values[key] = value  # The store now reports a held site to any caller that asks.

    def _record(self, name: str) -> None:
        """Count one command and raise when the test asked the store to be down.

        Args:
            name: The command name.

        Raises:
            ConnectionError: When the test set the failure flag.
        """
        self.calls.append(name)  # Every command lands here first, so the count misses nothing.
        if self.fail:  # `contracts/site-lock.md:118` asks a read to answer anyway.
            raise ConnectionError("The stand-in lock store is down for this test.")

    def set(self, key: str, value: str, nx: bool = False, ex: int | None = None) -> bool | None:
        """Write one value, and refuse when `nx` is set and the key exists.

        Args:
            key: The lock key.
            value: The JSON text of the record.
            nx: True when the write must fail on an existing key.
            ex: The life of the key in seconds. The stand-in expires nothing.

        Returns:
            True when the write happened, or None when `nx` refused it.
        """
        self._record("set")  # No read of this module may reach this command.
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
        self._record("get")  # A read page that shows the lock state may reach this command.
        return self.values.get(key)  # An absent key reads as None, never a fault.

    def eval(self, script: str, numkeys: int, key: str, *arguments: Any) -> int:
        """Refuse every script, because no read of this module writes a lock.

        Args:
            script: The Lua source the caller sent.
            numkeys: The key count.
            key: The lock key.
            *arguments: The token and the fresh value.

        Returns:
            Always 0, because no read may change a lock.
        """
        self._record("eval")  # No read of this module may reach this command at all.
        del script, numkeys, key, arguments  # The stand-in performs no script for a read test.
        return 0  # A read never writes, so the answer never matters.


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def lock_store() -> CountingLockStore:
    """Return a fresh counting lock store.

    Returns:
        An empty store with no calls recorded.
    """
    return CountingLockStore()  # Each test starts with no lock and no call.


@pytest.fixture
def read_app(portal_app: Flask, lock_store: CountingLockStore) -> Flask:
    """Return the portal with the lock store and both capture readers injected.

    Why:
        The comparison routes fall back to `capture.store`, and that module
        imports a database driver. Injecting both readers keeps the test free of
        a database and leaves the lock rule as the only thing under test.

    Args:
        portal_app: The real application from the shared fixture.
        lock_store: The counting lock store.

    Returns:
        The application with all three seams in place.
    """
    portal_app.config[LOCK_CLIENT_KEY] = lock_store  # Every lock call now lands in the counter.
    portal_app.config[CAPTURE_LOADER_KEY] = read_capture  # A plain document, with no database.
    portal_app.config[CAPTURE_LISTER_KEY] = list_captures  # The two rows of the picker.
    portal_app.config["WTF_CSRF_ENABLED"] = False  # Every call below is a read, so no token applies.
    return portal_app  # Every test below drives this application.


@pytest.fixture
def reader_owner() -> Iterator[identity.SessionOwner]:
    """Register the operator that reads, and drop the record when the test ends.

    Yields:
        The identity pair of the reading operator.
    """
    yield from register_owner(READER_EMAIL)  # One helper serves both operators.


@pytest.fixture
def holder_owner() -> Iterator[identity.SessionOwner]:
    """Register the operator that holds the site during a read.

    Yields:
        The identity pair of the holding operator.
    """
    yield from register_owner(HOLDER_EMAIL)  # A different address and a different browser.


@pytest.fixture
def read_client(read_app: Flask, reader_owner: identity.SessionOwner) -> FlaskClient:
    """Return a signed-in client that holds no lock at all.

    Why:
        The client is not held open with a `with` block, because that block keeps
        the request context of the last call alive and two clients then pop the
        contexts out of order.

    Args:
        read_app: The application with the three seams injected.
        reader_owner: The identity pair of the reading operator.

    Returns:
        The Flask test client of the reading operator.
    """
    client = read_app.test_client()  # A fresh cookie jar for this operator.
    client.set_cookie(identity.BROWSER_ID_COOKIE, reader_owner.browser_id)  # Half of the guard.
    with client.session_transaction() as browser_session:  # The other half of the guard.
        browser_session[identity.SESSION_OWNER_KEY] = reader_owner.key  # Names the registered owner.
        browser_session[SELECTED_ORG_SESSION_KEY] = ORG_ID  # The picker writes this field.
        browser_session[SELECTED_SITE_SESSION_KEY] = SITE_ID  # The picker writes this field as well.
    return client  # Every test below drives this client.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def read_capture(capture_id: str) -> dict[str, Any] | None:
    """Return one stored capture, with no database behind it.

    Args:
        capture_id: The business key of the capture.

    Returns:
        The capture document, or None when the key is unknown.
    """
    known = {BEFORE_CAPTURE_ID: BEFORE_CAPTURE, AFTER_CAPTURE_ID: AFTER_CAPTURE}  # The two captures of this module.
    return known.get(capture_id)  # An unknown key reads as absent, exactly as the store answers.


def list_captures(site_id: str) -> list[dict[str, Any]]:
    """Return the rows that fill the two capture pickers.

    Args:
        site_id: The site to narrow to. The stand-in holds one site only.

    Returns:
        The two rows of this module.
    """
    del site_id  # Both rows belong to the one site of this module.
    return CAPTURE_ROWS  # The picker renders even with no rows, so the shape is the only thing that matters.


def register_owner(actor_email: str) -> Iterator[identity.SessionOwner]:
    """Register one operator and drop the record afterward.

    Why:
        Two fixtures need the same six lines. The registry outlives a test, so a
        leaked record would sign a later test in by accident.

    Args:
        actor_email: The work email address of the operator.

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


def hold_the_site(store: CountingLockStore, owner: identity.SessionOwner) -> None:
    """Put one site under the lock of another operator.

    Why:
        The rule under test is that a held site still reads. Seeding the store
        is the only way to reach that state without a second signed-in client,
        and a second client would add calls that the counter must not see.

    Args:
        store: The counting lock store.
        owner: The operator that holds the site.
    """
    taken_at = datetime.now(UTC).isoformat()  # A fresh hold, so the cooldown of FR-078 has not started.
    record = lock.LockRecord(
        owner=owner,
        lock_token="held-by-another-operator",  # A read never reads this value, so any text serves.
        run_id="run-held",
        acquired_at=taken_at,
        refreshed_at=taken_at,
    )
    store.seed(lock.build_key(ORG_ID, SITE_ID), record.to_json())  # The site now reads as held.


def compare_query(path: str, extra: str = "") -> str:
    """Build one comparison path that names both captures.

    Args:
        path: The base path.
        extra: More query text, starting with an ampersand, or an empty string.

    Returns:
        The full path with the query.
    """
    return f"{path}?before={BEFORE_CAPTURE_ID}&after={AFTER_CAPTURE_ID}{extra}"  # Both routes take the same two values.


def read_every_comparison_surface(client: FlaskClient) -> list[TestResponse]:
    """Call every comparison surface once and return the four answers.

    Why:
        Three separate rules apply to all four surfaces at once: no lock, a held
        site, and a down store. Calling them from one helper keeps each test at
        one idea and keeps the surface list in one place.

    Args:
        client: The signed-in client.

    Returns:
        The answer of the picker, the page, the endpoint, and the download.
    """
    return [
        client.get(COMPARE_PAGE_PATH),  # The picker, reached from the navigation with no query.
        client.get(compare_query(COMPARE_PAGE_PATH)),  # The human view of one comparison.
        client.get(compare_query(COMPARISONS_API_PATH)),  # The machine view of the same comparison.
        client.get(compare_query(COMPARISONS_EXPORT_API_PATH, "&format=csv")),  # The download.
    ]


def history_is_built(application: Flask) -> bool:
    """Report whether the history routes are registered yet.

    Why:
        `contracts/http-api.md` lines 353 and 364 name two history routes, and
        tasks T204, T205, and T209 build them in the US6 phase. This test lives
        in the US4 phase, so it must state the gap out loud instead of passing
        quietly. The check reads the URL map, so these tests start running on
        the day US6 lands and need no edit.

    Args:
        application: The portal application.

    Returns:
        True when both history routes exist.
    """
    rules = {str(rule.rule) for rule in application.url_map.iter_rules()}  # Every registered path.
    return HISTORY_PAGE_PATH in rules and "/api/sites/<site_id>/history" in rules


# ---------------------------------------------------------------------------
# A read with no lock at all. `contracts/site-lock.md:15`.
# ---------------------------------------------------------------------------


def test_the_comparison_picker_reads_with_no_lock(read_client: FlaskClient) -> None:
    """`GET /compare` renders the picker for an operator that holds nothing.

    Args:
        read_client: The signed-in client that holds no lock.
    """
    response = read_client.get(COMPARE_PAGE_PATH)  # No lock, and no query values either.

    assert response.status_code == OK_STATUS  # The page renders for any signed-in operator.


def test_the_comparison_page_reads_with_no_lock(read_client: FlaskClient) -> None:
    """`GET /compare?before=...&after=...` renders the comparison with no lock.

    Args:
        read_client: The signed-in client that holds no lock.
    """
    response = read_client.get(compare_query(COMPARE_PAGE_PATH))  # The full human view.

    assert response.status_code == OK_STATUS  # A comparison needs no lock.
    assert b"compare-device-table" in response.data  # `contracts/ui-testids.md:145` names this table.


def test_the_comparison_endpoint_reads_with_no_lock(read_client: FlaskClient) -> None:
    """`GET /api/comparisons` answers the comparison with no lock.

    Args:
        read_client: The signed-in client that holds no lock.
    """
    response = read_client.get(compare_query(COMPARISONS_API_PATH))  # The machine view.

    assert response.status_code == OK_STATUS  # The endpoint needs no lock either.
    assert response.get_json()["statistics"]  # The body carries the numbers the page shows.


def test_the_comparison_download_reads_with_no_lock(read_client: FlaskClient) -> None:
    """`GET /api/comparisons/export` answers a file with no lock.

    Args:
        read_client: The signed-in client that holds no lock.
    """
    response = read_client.get(compare_query(COMPARISONS_EXPORT_API_PATH, "&format=csv"))

    assert response.status_code == OK_STATUS  # A record keeper needs no lock to keep a record.


def test_no_read_touches_the_lock_store(read_client: FlaskClient, lock_store: CountingLockStore) -> None:
    """No comparison surface sends any command to the lock store.

    Why:
        A read that answered 200 after asking the lock store would still add a
        Redis call to every page view and would fail the moment Redis stops. The
        count proves the read never asks at all.

    Args:
        read_client: The signed-in client that holds no lock.
        lock_store: The counting lock store.
    """
    read_every_comparison_surface(read_client)  # Every read surface of this module, once each.

    assert lock_store.calls == []  # No get, no set, and no script.


# ---------------------------------------------------------------------------
# A read while a different operator holds the site. `contracts/site-lock.md:128`.
# ---------------------------------------------------------------------------


def test_a_held_site_still_reads(
    read_client: FlaskClient,
    holder_owner: identity.SessionOwner,
    lock_store: CountingLockStore,
) -> None:
    """Every comparison surface answers while another operator holds the site.

    Why:
        A second operator checks the work of the first while that work runs. A
        read that waited for the lock would make that check impossible during
        the exact window in which it matters.

    Args:
        read_client: The signed-in client that holds no lock.
        holder_owner: The operator that holds the site.
        lock_store: The counting lock store.
    """
    hold_the_site(lock_store, holder_owner)  # A different operator now holds this site.

    answers = read_every_comparison_surface(read_client)  # Every read surface, once each.

    assert [answer.status_code for answer in answers] == [OK_STATUS] * len(answers)  # No refusal at all.


def test_a_held_site_asks_for_no_typed_word(
    read_client: FlaskClient,
    holder_owner: identity.SessionOwner,
    lock_store: CountingLockStore,
) -> None:
    """A read page names neither takeover word while another operator holds the site.

    Why:
        `contracts/site-lock.md:15` states that a read needs no typed text. A
        page that showed the takeover box would teach the operator to type
        CONFIRM to read, and a takeover erases the in-flight data of the holder.

    Args:
        read_client: The signed-in client that holds no lock.
        holder_owner: The operator that holds the site.
        lock_store: The counting lock store.
    """
    hold_the_site(lock_store, holder_owner)  # A different operator now holds this site.

    page = read_client.get(compare_query(COMPARE_PAGE_PATH)).data  # The human view of the comparison.

    assert TAKEOVER_WORD.encode() not in page  # No page of a read asks for the takeover word.
    assert RESUME_WORD.encode() not in page  # It asks for the resume word no more than the takeover word.


def test_a_held_site_names_no_lock_control_on_a_read_page(
    read_client: FlaskClient,
    holder_owner: identity.SessionOwner,
    lock_store: CountingLockStore,
) -> None:
    """A read page carries no lock control at all.

    Args:
        read_client: The signed-in client that holds no lock.
        holder_owner: The operator that holds the site.
        lock_store: The counting lock store.
    """
    hold_the_site(lock_store, holder_owner)  # A different operator now holds this site.

    page = read_client.get(compare_query(COMPARE_PAGE_PATH)).data  # The human view of the comparison.

    assert b"lock-take-button" not in page  # `contracts/ui-testids.md:77` names the take control.
    assert b"lock-confirm-submit" not in page  # The takeover control belongs to a write page alone.


# ---------------------------------------------------------------------------
# A read while the lock store is down. `contracts/site-lock.md:118`.
# ---------------------------------------------------------------------------


def test_a_down_lock_store_still_lets_a_read_answer(
    read_client: FlaskClient,
    lock_store: CountingLockStore,
) -> None:
    """Every comparison surface answers while the lock store is unreachable.

    Why:
        `contracts/site-lock.md:118` asks a read-only page to show the page and
        mark the lock state unknown. A write fails closed and a read fails open,
        so an outage of Redis must never hide a finished comparison.

    Args:
        read_client: The signed-in client that holds no lock.
        lock_store: The counting lock store.
    """
    lock_store.fail = True  # Every command of the store now raises.

    answers = read_every_comparison_surface(read_client)  # Every read surface, once each.

    assert [answer.status_code for answer in answers] == [OK_STATUS] * len(answers)  # No read failed closed.


def test_a_down_lock_store_leaves_the_comparison_numbers_whole(
    read_client: FlaskClient,
    lock_store: CountingLockStore,
) -> None:
    """A down lock store changes no number of a comparison.

    Args:
        read_client: The signed-in client that holds no lock.
        lock_store: The counting lock store.
    """
    healthy = read_client.get(compare_query(COMPARISONS_API_PATH)).get_json()  # The numbers with a live store.
    lock_store.fail = True  # The store goes down between the two reads.

    broken = read_client.get(compare_query(COMPARISONS_API_PATH)).get_json()  # The same read again.

    assert broken["statistics"] == healthy["statistics"]  # The lock state changes no count.


# ---------------------------------------------------------------------------
# The history page. `contracts/http-api.md:353` and `contracts/http-api.md:364`.
# ---------------------------------------------------------------------------


def test_the_history_page_reads_with_no_lock(read_app: Flask, read_client: FlaskClient) -> None:
    """`GET /history` renders for an operator that holds no lock.

    Args:
        read_app: The portal application.
        read_client: The signed-in client that holds no lock.
    """
    if not history_is_built(read_app):  # The US6 tasks T204, T205, and T209 build these routes.
        pytest.skip("The history routes of contracts/http-api.md lines 353 and 364 are not registered yet.")

    response = read_client.get(HISTORY_PAGE_PATH)  # The human view of the stored captures.

    assert response.status_code == OK_STATUS  # A history page needs no lock.


def test_the_history_endpoint_reads_with_no_lock(read_app: Flask, read_client: FlaskClient) -> None:
    """`GET /api/sites/<site_id>/history` answers for an operator that holds no lock.

    Args:
        read_app: The portal application.
        read_client: The signed-in client that holds no lock.
    """
    if not history_is_built(read_app):  # The US6 tasks T204, T205, and T209 build these routes.
        pytest.skip("The history routes of contracts/http-api.md lines 353 and 364 are not registered yet.")

    response = read_client.get(HISTORY_API_PATH)  # The machine view of the same list.

    assert response.status_code == OK_STATUS  # A history read needs no lock.


def test_the_history_page_reads_while_another_operator_holds_the_site(
    read_app: Flask,
    read_client: FlaskClient,
    holder_owner: identity.SessionOwner,
    lock_store: CountingLockStore,
) -> None:
    """`GET /history` renders while a different operator holds the site.

    Args:
        read_app: The portal application.
        read_client: The signed-in client that holds no lock.
        holder_owner: The operator that holds the site.
        lock_store: The counting lock store.
    """
    if not history_is_built(read_app):  # The US6 tasks T204, T205, and T209 build these routes.
        pytest.skip("The history routes of contracts/http-api.md lines 353 and 364 are not registered yet.")
    hold_the_site(lock_store, holder_owner)  # A different operator now holds this site.

    response = read_client.get(HISTORY_PAGE_PATH)  # The human view of the stored captures.

    assert response.status_code == OK_STATUS  # `contracts/site-lock.md:128` names this page by hand.
