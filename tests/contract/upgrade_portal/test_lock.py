"""Contract tests for the site lock endpoints of the portal.

Why:
    `contracts/http-api.md` section 3 fixes the path, the status, and the machine
    code of the three lock calls. `contracts/site-lock.md` fixes the four ways a
    caller reaches the lock: the plain take, the resume, the takeover, and the
    release. These tests read those two contracts and nothing else, so a later
    change of the route body cannot quietly change the answer that the browser
    and the operator depend on.

Scope:
    The acquire, the heartbeat, the release, the takeover, and the three refusal
    codes `site_locked`, `lock_lost`, and `confirmation_required`. Each test
    injects a stand-in lock store, so the real lock rules run and no test reaches
    a Redis server.

Fixtures:
    Every fixture lives in this file on purpose. `conftest.py` is shared with
    other test modules, and a lock store belongs to these tests alone.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import json  # The stored lock value is JSON text, so a seeded record is built the same way.
from collections.abc import Iterator  # The signed-in fixtures yield and then clean up.
from datetime import UTC, datetime, timedelta  # A quiet lock needs a timestamp in the past.
from typing import Any  # A stored value and a request body are both free-form.

import pytest  # The test framework of the project.
from flask import Flask  # The application type of the portal.
from flask.testing import FlaskClient  # The client type that drives every request.
from werkzeug.test import TestResponse  # The answer type that every assertion reads.

from src.upgrade_portal.runtime import identity, lock  # The real session guard and the real lock rules.

LOCK_CLIENT_KEY = "LOCK_STORE_CLIENT"  # The seam that holds the lock store, named by `select.py`.

PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.
OTHER_EMAIL = "second.operator@example.invalid"  # The operator that holds the lock in the refusal tests.
ORG_ID = "00000000-0000-0000-0000-0000000000aa"  # Matches the shared organization of the other tests.
SITE_ID = "00000000-0000-0000-0000-0000000000bb"  # Matches the shared site of the other tests.

SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The organization pick inside the signed session.
SELECTED_SITE_SESSION_KEY = "selected_site_id"  # The site pick inside the same signed session.

LOCK_PATH = f"/api/sites/{SITE_ID}/lock"  # `contracts/http-api.md:124` names this path for the take and the release.
BEAT_PATH = f"{LOCK_PATH}/heartbeat"  # `contracts/http-api.md:147` names this path for the beat.
SITE_KEY = f"misthelper:lock:site:{ORG_ID}:{SITE_ID}"  # The key `build_key` writes for this organization and site.

OK_STATUS = 200  # The take, the beat, or the release succeeded.
BAD_REQUEST_STATUS = 400  # The operator must type a word first.
CONFLICT_STATUS = 409  # The site is held, or this session lost the lock it named.
UNAVAILABLE_STATUS = 503  # The lock store did not answer a write, and no fallback is allowed.

LOCK_TTL_SECONDS = 3600  # `contracts/site-lock.md:23` fixes the life of one lock.
COOLDOWN_SECONDS = 300  # `contracts/site-lock.md:113` fixes the quiet window before a takeover.
QUIET_AGE_SECONDS = 400  # Past the cooldown, so the seeded holder counts as quiet.
ACTIVE_AGE_SECONDS = 10  # Well inside the cooldown, so the seeded holder counts as active.

TAKEOVER_WORD = "CONFIRM"  # `contracts/site-lock.md:114` fixes this word for a different operator.
RESUME_WORD = "continue"  # FR-080 fixes this word for the same operator returning to a quiet session.


class FakeLockStore:
    """Answers the three store commands that the lock module sends.

    Why:
        The lock rules live in `runtime/lock.py` and the routes must drive the
        real rules, not a stand-in of the rules. This class stands in for the
        store alone, so the compare-and-extend and the compare-and-delete both
        run exactly as they run against Redis, with no Redis server.

        The class reads the script text instead of comparing it with a private
        name. A test that reached a private name would break on a rename that
        changed no behavior at all.
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
        if self.fail:  # `contracts/site-lock.md:128` asks the portal to fail closed here.
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
        self._guard()  # A read of a down store raises, and the page then marks the state unknown.
        return self.values.get(key)  # An absent key reads as None, never a fault.

    def eval(self, script: str, numkeys: int, key: str, *arguments: Any) -> int:
        """Run one of the three Lua scripts of the contract.

        Why:
            The three scripts share one compare and differ in what follows it.
            The stand-in reads the text for the part that differs, so a rename of
            a private constant leaves this test alone.

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
def lock_app(portal_app: Flask, lock_store: FakeLockStore) -> Flask:
    """Return the portal application with the lock store seam injected.

    Why:
        The lock routes reach one store. The store sits behind a seam, so a
        contract test replaces it and runs the real lock rules with no server.

    Args:
        portal_app: The real application from the shared fixture.
        lock_store: The stand-in lock store.

    Returns:
        The application with the seam in place.
    """
    portal_app.config[LOCK_CLIENT_KEY] = lock_store  # No Redis server runs in a contract test.
    portal_app.config["WTF_CSRF_ENABLED"] = False  # `test_capture_start.py` already covers the token check.
    return portal_app  # Every test below drives this application.


@pytest.fixture
def probe_owner() -> Iterator[identity.SessionOwner]:
    """Register the first operator and drop the record when the test ends.

    Why:
        The guard admits a request only when the signed session and the browser
        cookie both name a registered owner. The registry is a process global,
        so the fixture clears it again.

    Yields:
        The identity pair of the registered operator.
    """
    yield from register_owner(PROBE_EMAIL)  # One helper serves both operators.


@pytest.fixture
def other_owner() -> Iterator[identity.SessionOwner]:
    """Register the second operator, who takes the site over.

    Yields:
        The identity pair of the second registered operator.
    """
    yield from register_owner(OTHER_EMAIL)  # A different address and a different browser.


@pytest.fixture
def lock_client(lock_app: Flask, probe_owner: identity.SessionOwner) -> FlaskClient:
    """Return a signed-in client that already picked the organization and the site.

    Args:
        lock_app: The application with the seam injected.
        probe_owner: The identity pair of the first operator.

    Returns:
        The Flask test client of the first operator.
    """
    return open_client(lock_app, probe_owner)  # One helper serves both operators.


@pytest.fixture
def other_client(lock_app: Flask, other_owner: identity.SessionOwner) -> FlaskClient:
    """Return a second signed-in client, for the takeover tests.

    Args:
        lock_app: The application with the seam injected.
        other_owner: The identity pair of the second operator.

    Returns:
        The Flask test client of the second operator.
    """
    return open_client(lock_app, other_owner)  # A separate browser cookie and a separate session.


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def open_client(application: Flask, owner: identity.SessionOwner) -> FlaskClient:
    """Open one signed-in client that already picked the organization and the site.

    Why:
        The client is not held open with a `with` block on purpose. That block
        keeps the request context of the last call alive, and two clients that
        both hold one then pop the contexts out of order. The client keeps its
        own cookie jar, so the signed session survives without the block.

    Args:
        application: The application with the lock seam injected.
        owner: The identity pair of the operator to sign in.

    Returns:
        The Flask test client, already signed in.
    """
    client = application.test_client()  # A fresh cookie jar for this operator.
    client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # Half of the guard.
    with client.session_transaction() as browser_session:  # The other half of the guard.
        browser_session[identity.SESSION_OWNER_KEY] = owner.key  # Names the registered owner.
        browser_session[SELECTED_ORG_SESSION_KEY] = ORG_ID  # The picker writes this field.
        browser_session[SELECTED_SITE_SESSION_KEY] = SITE_ID  # The picker writes this field as well.
    return client  # Every test below drives this client.


def seed_lock(store: FakeLockStore, owner: identity.SessionOwner, age_seconds: int, token: str = "seeded-token") -> str:
    """Write one lock straight into the stand-in store and return its token.

    Why:
        A takeover test needs a holder that already went quiet. No route can
        produce a quiet holder inside one test, because the cooldown is 300
        seconds. Writing the timestamp is the only way to reach that state.

    Args:
        store: The stand-in lock store.
        owner: The operator that holds the seeded lock.
        age_seconds: How long ago the holder last sent a beat.
        token: The token of the seeded lock.

    Returns:
        The token of the seeded lock.
    """
    stamp = (datetime.now(UTC) - timedelta(seconds=age_seconds)).isoformat()  # The lock module reads ISO 8601 text.
    record = lock.LockRecord(
        owner=owner,
        lock_token=token,
        run_id="run-seeded",
        acquired_at=stamp,
        refreshed_at=stamp,  # `is_quiet` reads this field, so the age of the beat decides the state.
    )
    store.values[SITE_KEY] = record.to_json()  # The route reads this value through the seam.
    return token  # Every path below names this token.


def read_error_code(response: TestResponse) -> str:
    """Return the `code` field of an error envelope.

    Why:
        `contracts/README.md` states that a test asserts on `code` and never on
        the message text, because the message may change with no contract change.

    Args:
        response: The answer of one refused request.

    Returns:
        The machine code, or an empty string when the body carries none.
    """
    body: Any = response.get_json()  # Every refusal of this portal answers JSON.
    return str(body.get("error", {}).get("code", "")) if isinstance(body, dict) else ""


def read_error_details(response: TestResponse) -> dict[str, Any]:
    """Return the `details` member of an error envelope.

    Args:
        response: The answer of one refused request.

    Returns:
        The details, or an empty dictionary when the body carries none.
    """
    body: Any = response.get_json()  # Every refusal of this portal answers JSON.
    details = body.get("error", {}).get("details", {}) if isinstance(body, dict) else {}
    return details if isinstance(details, dict) else {}  # A damaged body reads as no details at all.


def take_lock(client: FlaskClient, confirm: str = "") -> TestResponse:
    """Post one take request for the shared site.

    Args:
        client: The signed-in client.
        confirm: The word the operator typed, if any.

    Returns:
        The answer of the take.
    """
    return client.post(LOCK_PATH, json={"confirm": confirm})  # The one body field the contract names.


# ---------------------------------------------------------------------------
# The acquire. `contracts/http-api.md:124` and `contracts/site-lock.md:55`.
# ---------------------------------------------------------------------------


def test_take_a_free_site(lock_client: FlaskClient) -> None:
    """`POST /api/sites/<site_id>/lock` answers 200 with a token and the life of the lock.

    Args:
        lock_client: The signed-in client.
    """
    response = take_lock(lock_client)  # The site is free, so the store decides the race and this caller wins.

    assert response.status_code == OK_STATUS  # `contracts/http-api.md:129` fixes this status.
    body = response.get_json()
    assert body["lock_token"]  # The contract names this field and fixes no shape for the value.
    assert body["expires_in"] == LOCK_TTL_SECONDS  # `contracts/site-lock.md:23` fixes 3600 seconds.


def test_take_names_the_state_acquired(lock_client: FlaskClient) -> None:
    """A fresh take reports the state `acquired`.

    Args:
        lock_client: The signed-in client.
    """
    response = take_lock(lock_client)  # No lock exists, so this is a plain take.

    assert response.get_json()["state"] == "acquired"  # `contracts/site-lock.md:57` names the three states.


def test_the_same_browser_resumes_an_active_lock(lock_client: FlaskClient) -> None:
    """The same operator and browser get the stored token back with the state `resume`.

    Why:
        FR-074 lets one operator work in several tabs. A second tab must not be
        refused and must not receive a second token, because the beat of either
        tab then renews the one lock.

    Args:
        lock_client: The signed-in client.
    """
    first = take_lock(lock_client).get_json()  # The first tab takes the site.

    second = take_lock(lock_client)  # A second tab of the same browser asks again.

    assert second.status_code == OK_STATUS  # `contracts/site-lock.md:57` answers 200 here.
    assert second.get_json()["lock_token"] == first["lock_token"]  # The stored token, not a fresh one.
    assert second.get_json()["state"] == "resume"  # The contract fixes this word.


def test_another_operator_is_refused_while_the_holder_is_active(
    lock_client: FlaskClient,
    other_owner: identity.SessionOwner,
    lock_store: FakeLockStore,
) -> None:
    """An active holder refuses a different operator with `site_locked`.

    Args:
        lock_client: The signed-in client of the operator who wants the site.
        other_owner: The operator that already holds the site.
        lock_store: The stand-in lock store.
    """
    seed_lock(lock_store, other_owner, ACTIVE_AGE_SECONDS)  # A holder that beat 10 seconds ago is active.

    response = take_lock(lock_client)  # The second operator asks for the same site.

    assert response.status_code == CONFLICT_STATUS  # `contracts/http-api.md:132` fixes this status.
    assert read_error_code(response) == "site_locked"  # The contract fixes this code.


def test_the_refusal_names_the_holder_and_the_wait(
    lock_client: FlaskClient,
    other_owner: identity.SessionOwner,
    lock_store: FakeLockStore,
) -> None:
    """A `site_locked` refusal carries `actor_email` and `cooldown_remaining`.

    Why:
        `contracts/http-api.md:132` names both fields. The waiting operator reads
        who holds the site and how long the wait lasts, so the page needs no
        second call to answer either question.

    Args:
        lock_client: The signed-in client of the operator who wants the site.
        other_owner: The operator that already holds the site.
        lock_store: The stand-in lock store.
    """
    seed_lock(lock_store, other_owner, ACTIVE_AGE_SECONDS)  # An active holder, well inside the cooldown.

    details = read_error_details(take_lock(lock_client))  # The refusal body of the second operator.

    assert details["actor_email"] == OTHER_EMAIL  # The contract names the holder in the refusal.
    assert 0 < details["cooldown_remaining"] <= COOLDOWN_SECONDS  # The wait shrinks and never goes below zero.


def test_a_quiet_holder_asks_a_different_operator_for_a_word(
    lock_client: FlaskClient,
    other_owner: identity.SessionOwner,
    lock_store: FakeLockStore,
) -> None:
    """A quiet holder answers `confirmation_required` instead of `site_locked`.

    Args:
        lock_client: The signed-in client of the operator who wants the site.
        other_owner: The operator that went quiet.
        lock_store: The stand-in lock store.
    """
    seed_lock(lock_store, other_owner, QUIET_AGE_SECONDS)  # Past the 300-second cooldown.

    response = take_lock(lock_client)  # The second operator asks with no typed word.

    assert response.status_code == BAD_REQUEST_STATUS  # `contracts/http-api.md:131` fixes this status.
    assert read_error_code(response) == "confirmation_required"  # The contract fixes this code.


def test_the_word_for_a_different_operator_is_confirm(
    lock_client: FlaskClient,
    other_owner: identity.SessionOwner,
    lock_store: FakeLockStore,
) -> None:
    """The refusal names `CONFIRM` for an operator who is not the holder.

    Why:
        FR-079 asks a different operator for `CONFIRM` and FR-080 asks the same
        operator for `continue`. A page that showed one word for both cases would
        teach the returning operator to type the wrong text.

    Args:
        lock_client: The signed-in client of the operator who wants the site.
        other_owner: The operator that went quiet.
        lock_store: The stand-in lock store.
    """
    seed_lock(lock_store, other_owner, QUIET_AGE_SECONDS)  # A quiet holder, so a takeover is possible.

    details = read_error_details(take_lock(lock_client))  # The refusal body names the needed word.

    assert details["needed_text"] == TAKEOVER_WORD  # `contracts/site-lock.md:114` fixes this word.


def test_the_word_for_the_same_operator_is_continue(
    lock_client: FlaskClient,
    probe_owner: identity.SessionOwner,
    lock_store: FakeLockStore,
) -> None:
    """The refusal names `continue` for the same operator returning to a quiet session.

    Args:
        lock_client: The signed-in client of the operator that went quiet.
        probe_owner: The identity pair of that same operator.
        lock_store: The stand-in lock store.
    """
    seed_lock(lock_store, probe_owner, QUIET_AGE_SECONDS)  # The same address and the same browser.

    details = read_error_details(take_lock(lock_client))  # The refusal body names the needed word.

    assert details["needed_text"] == RESUME_WORD  # FR-080 fixes this word, and its letter case.


@pytest.mark.parametrize("typed", ["confirm", "Confirm", "CONFIRM ", " CONFIRM", "YES", ""])
def test_a_wrong_word_never_takes_the_site(
    lock_client: FlaskClient,
    other_owner: identity.SessionOwner,
    lock_store: FakeLockStore,
    typed: str,
) -> None:
    """Only the exact word takes a quiet site, and the letter case matters.

    Why:
        A takeover erases in-flight data. A near miss must therefore refuse, so
        no autocomplete and no trailing space can move the lock by accident.

    Args:
        lock_client: The signed-in client of the operator who wants the site.
        other_owner: The operator that went quiet.
        lock_store: The stand-in lock store.
        typed: The text the operator typed.
    """
    token = seed_lock(lock_store, other_owner, QUIET_AGE_SECONDS)  # A quiet holder, ready to be taken over.

    response = take_lock(lock_client, typed)  # The near miss.

    assert read_error_code(response) == "confirmation_required"  # The refusal, not a grant.
    assert json.loads(lock_store.values[SITE_KEY])["lock_token"] == token  # The stored lock never moved.


def test_the_exact_word_takes_a_quiet_site(
    lock_client: FlaskClient,
    other_owner: identity.SessionOwner,
    lock_store: FakeLockStore,
) -> None:
    """The word `CONFIRM` moves a quiet lock to the new operator.

    Args:
        lock_client: The signed-in client of the operator who wants the site.
        other_owner: The operator that went quiet.
        lock_store: The stand-in lock store.
    """
    token = seed_lock(lock_store, other_owner, QUIET_AGE_SECONDS)  # A quiet holder, ready to be taken over.

    response = take_lock(lock_client, TAKEOVER_WORD)  # The exact word, in capital letters.

    assert response.status_code == OK_STATUS  # The takeover succeeded.
    assert response.get_json()["state"] == "takeover"  # `contracts/site-lock.md:57` names this state.
    assert response.get_json()["lock_token"] != token  # A takeover always writes a fresh token.


def test_the_store_refuses_a_second_operator_that_arrives_together(
    lock_client: FlaskClient,
    other_client: FlaskClient,
) -> None:
    """Two operators who ask for a free site do not both win.

    Why:
        FR-076 gives the site to exactly one session owner. The store decides the
        race through the `NX` flag, so no read and no compare in the route can
        change the outcome.

    Args:
        lock_client: The first signed-in client.
        other_client: The second signed-in client.
    """
    first = take_lock(lock_client)  # One of the two wins.

    second = take_lock(other_client)  # The other asks for the same free site.

    assert first.status_code == OK_STATUS  # The winner holds the site.
    assert second.status_code == CONFLICT_STATUS  # The loser is refused, not granted a second token.
    assert read_error_code(second) == "site_locked"  # The contract fixes this code.


def test_a_down_store_refuses_the_take(lock_client: FlaskClient, lock_store: FakeLockStore) -> None:
    """A lock store that does not answer refuses the take with 503.

    Why:
        `contracts/site-lock.md:128` forbids an in-memory fallback. A fallback
        would let two workers each believe they hold the lock, which is the exact
        failure the lock prevents.

    Args:
        lock_client: The signed-in client.
        lock_store: The stand-in lock store.
    """
    lock_store.fail = True  # Every command of the store now raises.

    response = take_lock(lock_client)  # The take must fail closed.

    assert response.status_code == UNAVAILABLE_STATUS  # The contract fixes this status.
    assert read_error_code(response) == "lock_store_unreachable"  # The code names the cause plainly.


# ---------------------------------------------------------------------------
# The heartbeat. `contracts/http-api.md:147` and `contracts/site-lock.md:73`.
# ---------------------------------------------------------------------------


def test_a_beat_extends_the_lock(lock_client: FlaskClient) -> None:
    """`POST /api/sites/<site_id>/lock/heartbeat` answers 200 with the fresh life.

    Args:
        lock_client: The signed-in client.
    """
    token = take_lock(lock_client).get_json()["lock_token"]  # The browser holds this token.

    response = lock_client.post(BEAT_PATH, json={"lock_token": token})  # The beat the browser sends every 60 seconds.

    assert response.status_code == OK_STATUS  # `contracts/http-api.md:152` fixes this status.
    assert response.get_json()["expires_in"] == LOCK_TTL_SECONDS  # The lock lives another 3600 seconds.


def test_a_beat_with_a_wrong_token_is_refused(lock_client: FlaskClient) -> None:
    """A beat that names another token answers `lock_lost`.

    Args:
        lock_client: The signed-in client.
    """
    take_lock(lock_client)  # This browser holds a lock, but the beat below names another token.

    response = lock_client.post(BEAT_PATH, json={"lock_token": "not-the-stored-token"})

    assert response.status_code == CONFLICT_STATUS  # `contracts/http-api.md:153` fixes this status.
    assert read_error_code(response) == "lock_lost"  # The contract fixes this code.


def test_a_beat_without_a_lock_is_refused(lock_client: FlaskClient) -> None:
    """A beat from a browser that took no lock answers `lock_lost`.

    Args:
        lock_client: The signed-in client.
    """
    response = lock_client.post(BEAT_PATH, json={"lock_token": "never-granted"})  # No take ran before this beat.

    assert response.status_code == CONFLICT_STATUS  # The same refusal as a moved lock.
    assert read_error_code(response) == "lock_lost"  # One code covers every way a lock can be gone.


def test_a_beat_after_a_takeover_is_refused(
    lock_client: FlaskClient,
    other_client: FlaskClient,
    lock_store: FakeLockStore,
) -> None:
    """The operator that lost the site cannot renew the lock.

    Why:
        The compare and the extend run as one step inside the store. A beat that
        arrived after a takeover would otherwise pull the site back from the new
        operator without any typed word.

    Args:
        lock_client: The client of the operator that first held the site.
        other_client: The client of the operator that takes the site over.
        lock_store: The stand-in lock store.
    """
    token = take_lock(lock_client).get_json()["lock_token"]  # The first operator holds the site.
    age_the_lock(lock_store)  # The holder goes quiet, so a takeover becomes possible.
    take_lock(other_client, TAKEOVER_WORD)  # The second operator takes the site.

    response = lock_client.post(BEAT_PATH, json={"lock_token": token})  # The first operator beats anyway.

    assert response.status_code == CONFLICT_STATUS  # The store compared the token and refused.
    assert read_error_code(response) == "lock_lost"  # The page then tells the operator to take the site again.


def test_a_down_store_refuses_the_beat(lock_client: FlaskClient, lock_store: FakeLockStore) -> None:
    """A lock store that does not answer refuses the beat with 503.

    Args:
        lock_client: The signed-in client.
        lock_store: The stand-in lock store.
    """
    token = take_lock(lock_client).get_json()["lock_token"]  # The browser holds this token.
    lock_store.fail = True  # The store goes down between the take and the beat.

    response = lock_client.post(BEAT_PATH, json={"lock_token": token})

    assert response.status_code == UNAVAILABLE_STATUS  # A beat fails closed, the same as a take.
    assert read_error_code(response) == "lock_store_unreachable"  # The code names the cause plainly.


# ---------------------------------------------------------------------------
# The release. `contracts/http-api.md:155` and `contracts/site-lock.md:96`.
# ---------------------------------------------------------------------------


def test_a_release_frees_the_site(lock_client: FlaskClient, lock_store: FakeLockStore) -> None:
    """`DELETE /api/sites/<site_id>/lock` answers 200 and clears the stored lock.

    Args:
        lock_client: The signed-in client.
        lock_store: The stand-in lock store.
    """
    token = take_lock(lock_client).get_json()["lock_token"]  # The browser holds this token.

    response = lock_client.delete(LOCK_PATH, json={"lock_token": token})

    assert response.status_code == OK_STATUS  # `contracts/http-api.md:160` fixes this status.
    assert response.get_json()["released"] is True  # The contract fixes this field and this value.
    assert SITE_KEY not in lock_store.values  # The site is free, so the next operator waits no cooldown.


def test_a_release_with_a_wrong_token_is_refused(lock_client: FlaskClient, lock_store: FakeLockStore) -> None:
    """A release that names another token answers `lock_lost` and frees nothing.

    Args:
        lock_client: The signed-in client.
        lock_store: The stand-in lock store.
    """
    take_lock(lock_client)  # This browser holds a lock, but the release below names another token.

    response = lock_client.delete(LOCK_PATH, json={"lock_token": "not-the-stored-token"})

    assert response.status_code == CONFLICT_STATUS  # `contracts/http-api.md:161` fixes this status.
    assert read_error_code(response) == "lock_lost"  # The contract fixes this code.
    assert SITE_KEY in lock_store.values  # A wrong token never frees a lock that another caller holds.


def test_a_second_release_is_refused(lock_client: FlaskClient) -> None:
    """Releasing twice answers `lock_lost` on the second call.

    Args:
        lock_client: The signed-in client.
    """
    token = take_lock(lock_client).get_json()["lock_token"]  # The browser holds this token.
    lock_client.delete(LOCK_PATH, json={"lock_token": token})  # The first release frees the site.

    response = lock_client.delete(LOCK_PATH, json={"lock_token": token})  # The same call runs again.

    assert response.status_code == CONFLICT_STATUS  # There is nothing left to release.
    assert read_error_code(response) == "lock_lost"  # One code covers every way a lock can be gone.


def test_a_release_lets_the_next_operator_take_the_site(
    lock_client: FlaskClient,
    other_client: FlaskClient,
) -> None:
    """A released site needs no typed word from the next operator.

    Why:
        A release is the fast path out. FR-078 gives a 5 minute cooldown to an
        abandoned session alone, so an operator who releases on purpose must not
        make the next operator wait or type anything.

    Args:
        lock_client: The client of the operator that holds the site.
        other_client: The client of the next operator.
    """
    token = take_lock(lock_client).get_json()["lock_token"]  # The first operator holds the site.
    lock_client.delete(LOCK_PATH, json={"lock_token": token})  # That operator gives the site back.

    response = take_lock(other_client)  # The next operator asks with no typed word at all.

    assert response.status_code == OK_STATUS  # A free site needs no word.
    assert response.get_json()["state"] == "acquired"  # A plain take, never a takeover.


# ---------------------------------------------------------------------------
# The rule that no lock token reaches a log line. T180.
# ---------------------------------------------------------------------------


def test_no_log_line_holds_the_lock_token(
    lock_client: FlaskClient,
    other_client: FlaskClient,
    lock_store: FakeLockStore,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """No log line of a full lock life holds the token or a work email address.

    Why:
        `contracts/site-lock.md:37` states that the token never reaches a log
        line. The take, the takeover, the beat, and the release all log, so the
        whole life runs here and the whole captured text is read once.

    Args:
        lock_client: The client of the first operator.
        other_client: The client of the operator that takes the site over.
        lock_store: The stand-in lock store.
        caplog: The captured log records of this test.
    """
    with caplog.at_level("DEBUG"):  # The lowest level, so no record escapes the check.
        first = take_lock(lock_client).get_json()["lock_token"]  # The take logs.
        lock_client.post(BEAT_PATH, json={"lock_token": first})  # The beat logs.
        age_the_lock(lock_store)  # The holder goes quiet.
        second = take_lock(other_client, TAKEOVER_WORD).get_json()["lock_token"]  # The takeover logs.
        other_client.delete(LOCK_PATH, json={"lock_token": second})  # The release logs.

    written = caplog.text  # Every captured record, joined into one text.
    assert first not in written  # The first token never reached a log line.
    assert second not in written  # Neither did the token of the new holder.
    assert PROBE_EMAIL not in written  # FR-006 allows the digest of an address and never the address.
    assert OTHER_EMAIL not in written  # The same rule for the second operator.


def age_the_lock(store: FakeLockStore, age_seconds: int = QUIET_AGE_SECONDS) -> None:
    """Push the stored beat of the current lock into the past.

    Why:
        The cooldown is 300 seconds, so no test can wait it out. Rewriting the
        one timestamp the rule reads is the only way to reach a quiet holder
        after a real take ran through the route.

    Args:
        store: The stand-in lock store.
        age_seconds: How long ago the holder last sent a beat.
    """
    stored = json.loads(store.values[SITE_KEY])  # The record the take just wrote.
    stamp = (datetime.now(UTC) - timedelta(seconds=age_seconds)).isoformat()  # Past the cooldown.
    stored["refreshed_at"] = stamp  # `is_quiet` reads this field alone.
    store.values[SITE_KEY] = json.dumps(stored)  # The store now holds a quiet lock.
