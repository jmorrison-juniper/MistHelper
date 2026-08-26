"""Unit tests for the Redis site lock.

Why:
    ``contracts/site-lock.md`` is the binding contract for this module, so
    every test names the behavior that the contract fixes: one atomic write
    decides the race, the pair of address and browser decides a resume, a quiet
    holder needs a typed word, and a read never needs the lock.

    Every failure test asserts on the contract error ``code`` and never on the
    operator message, as ``contracts/README.md`` requires.

    No test opens a socket. Each test injects an in-memory double that repeats
    the ``SET ... NX EX`` behavior of Redis and the three Lua scripts. The
    shared ``fake_lock_store`` fixture of ``conftest.py`` carries no ``eval``,
    so it cannot reach the refresh path or the release path. This module
    therefore builds a richer double of its own.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from src.upgrade_portal.runtime import lock as lock_module
from src.upgrade_portal.runtime.identity import SessionOwner
from src.upgrade_portal.runtime.lock import (
    _REFRESH_SCRIPT,
    _RELEASE_SCRIPT,
    _TAKEOVER_SCRIPT,
    COMMAND_TIMEOUT_SECONDS,
    CONNECT_TIMEOUT_SECONDS,
    COOLDOWN_SECONDS,
    HEARTBEAT_SECONDS,
    LOCK_TTL_SECONDS,
    RESUME_CONFIRMATION_TEXT,
    RETRY_AFTER_SECONDS,
    TAKEOVER_CONFIRMATION_TEXT,
    ConfirmationRequiredError,
    LockGrant,
    LockLostError,
    LockRecord,
    LockRequest,
    LockState,
    LockStoreUnreachableError,
    ReleaseOutcome,
    SiteLockedError,
    TakeoverAuditError,
    acquire_site_lock,
    build_key,
    connect_lock_store,
    read_lock,
    read_site_locks,
    refresh_site_lock,
    release_site_lock,
)

# The identifiers every test shares. The key literal repeats the contract row at
# contracts/site-lock.md line 21, so a change to the template fails here.
ORG_ID = "org-1234"
SITE_ID = "site-abcd"
OTHER_SITE_ID = "site-efgh"
RUN_ID = "run-ab12cd34"
SITE_KEY = "misthelper:lock:site:org-1234:site-abcd"

# The six field names that contracts/site-lock.md lines 26 to 33 fix.
CONTRACT_FIELDS = ("acquired_at", "actor_email", "browser_id", "lock_token", "refreshed_at", "run_id")

# The three identities. The browser values match the shape that identity.py
# accepts, which is 16 to 128 URL-safe characters.
FIRST_OWNER = SessionOwner(actor_email="first@example.com", browser_id="browser-first-000001")
SECOND_OWNER = SessionOwner(actor_email="second@example.com", browser_id="browser-second-00001")
FIRST_OWNER_SECOND_COMPUTER = SessionOwner(actor_email="first@example.com", browser_id="browser-first-000002")

# The message of a refused audit write. The value looks like a driver message,
# which names a host and an account, so a test can prove no log line repeats it.
AUDIT_FAULT_MESSAGE = "redis://portal:not-a-real-password@203.0.113.1:6379/0 refused the write"

# The token of every seeded record. A test compares this value to prove that a
# resume returns the stored token and that a takeover replaces it.
SEEDED_TOKEN = "seeded-lock-token"


class ScriptedLockStore:
    """An in-memory stand-in for the Redis client the lock module uses.

    Why:
        The lock needs one atomic ``SET key value NX EX <life>`` and three Lua
        scripts. A unit test must prove that a second operator loses each race
        without a Redis server and without a socket.

        The double compares the script text by identity with the constants of
        the module under test. A substring match would pick the wrong branch in
        silence if a script changed, and a silent wrong branch is worse than a
        loud failure.

        The double also drops a key that outlived its expiry. A store that keeps
        every key for ever answers with a state the real server cannot produce,
        and a test against an impossible state proves nothing.
    """

    def __init__(self) -> None:
        """Start with an empty store that answers every command."""
        self.values: dict[str, str] = {}  # The stored JSON of each key
        self.expiries: dict[str, int] = {}  # The last time to live each key received
        self.set_calls: list[tuple[str, bool, int | None]] = []  # Key, nx flag, and expiry of each write
        self.fail = False  # True makes every command raise, which models a dead server
        self.after_get: Callable[[], None] | None = None  # Runs after a read, to model a racing operator

    def _refuse_when_down(self) -> None:
        """Raise the error a dead server raises.

        Raises:
            ConnectionError: When the test set the `fail` flag.
        """
        if self.fail:
            raise ConnectionError("The test double models a lock store that does not answer.")

    def _drop_when_expired(self, key: str) -> None:
        """Delete one key when the real server would already have dropped it.

        Why:
            Real Redis deletes a key when the time to live runs out. Every write
            of the lock module sets `refreshed_at` and the expiry in the same
            operation, so the age past `refreshed_at` is the age of the key.

            A double that keeps a key for ever lets a test seed a lock that is
            both alive and quiet. The real server never holds that state when
            the expiry equals the cooldown, so a takeover test against that
            state would pass while the branch stays unreachable in production.

        Args:
            key: The lock key.
        """
        life = self.expiries.get(key)
        value = self.values.get(key)
        if life is None or value is None:  # A write with no expiry, or no key at all
            return
        held = LockRecord.from_json(value)
        if held is None:  # A value the lock module did not write carries no age
            return
        if held.age_seconds() >= life:  # The real server would already have dropped it
            self.values.pop(key, None)
            self.expiries.pop(key, None)

    def set(self, key: str, value: str, nx: bool = False, ex: int | None = None) -> bool | None:
        """Write one key, and honor the `nx` flag the way the real client does.

        Args:
            key: The lock key.
            value: The JSON text to store.
            nx: True writes only when the key is absent.
            ex: The life of the key in seconds.

        Returns:
            True after a write, or None when the `nx` flag blocked the write.
        """
        self._refuse_when_down()
        self.set_calls.append((key, nx, ex))
        self._drop_when_expired(key)  # An expired key never blocks a write
        if nx and key in self.values:  # The real client returns None when the key exists
            return None
        self.values[key] = value
        if ex is not None:
            self.expiries[key] = int(ex)
        return True

    def get(self, key: str) -> str | None:
        """Return the stored JSON of one key.

        Args:
            key: The lock key.

        Returns:
            The JSON text, or None when the key is absent or expired.
        """
        self._refuse_when_down()
        self._drop_when_expired(key)  # An expired key reads as absent
        value = self.values.get(key)
        if self.after_get is not None:  # A racing operator changes the store between the read and the write
            self.after_get()
        return value

    def eval(self, script: str, numkeys: int, key: str, *arguments: Any) -> int:
        """Run one of the three lock scripts.

        Args:
            script: The script text the module passed.
            numkeys: The count of keys. The lock always passes one.
            key: The lock key.
            *arguments: The token, and for two scripts the new value and the life.

        Returns:
            1 when the script wrote, 0 when the compare failed, and 2 when a
            release found no key at all.

        Raises:
            AssertionError: When the module ran a script this double does not know.
        """
        self._refuse_when_down()
        assert numkeys == 1  # Every lock script names exactly one key
        self._drop_when_expired(key)  # Each script starts with a GET, which never sees an expired key
        token = str(arguments[0])
        if script == _RELEASE_SCRIPT:
            return self._release(key, token)
        if script == _REFRESH_SCRIPT:
            return self._refresh(key, token, arguments)
        if script == _TAKEOVER_SCRIPT:
            return self._takeover(key, token, arguments)
        raise AssertionError("The lock module ran a script that this double does not know.")

    def _holds(self, key: str, token: str) -> bool:
        """Report whether the stored value carries one token.

        Args:
            key: The lock key.
            token: The token the caller claims.

        Returns:
            True when the key exists and holds that token.
        """
        current = self.values.get(key)
        if current is None:
            return False
        return bool(json.loads(current).get("lock_token") == token)

    def _release(self, key: str, token: str) -> int:
        """Delete one key when the caller still holds it.

        Why:
            The three answers of the script are not one answer. An absent key
            and a token that does not match both delete nothing, and the caller
            must tell them apart, so this double keeps them apart too.

        Args:
            key: The lock key.
            token: The token the caller claims.

        Returns:
            1 after a delete, 0 when another token holds the key, and 2 when
            the key is already gone.
        """
        if key not in self.values:
            return 2  # The key expired before the release ran
        if not self._holds(key, token):
            return 0  # A takeover moved the lock, so the delete must not run
        del self.values[key]
        return 1

    def _refresh(self, key: str, token: str, arguments: tuple[Any, ...]) -> int:
        """Extend one key when the caller still holds it.

        Args:
            key: The lock key.
            token: The token the caller claims.
            arguments: The token, the new JSON, and the life in seconds.

        Returns:
            1 after a write, and 0 when the key is absent or holds another token.
        """
        if not self._holds(key, token):  # An absent key returns 0, so a beat cannot revive a dead lock
            return 0
        self.values[key] = str(arguments[1])
        self.expiries[key] = int(arguments[2])
        return 1

    def _takeover(self, key: str, token: str, arguments: tuple[Any, ...]) -> int:
        """Write over one key when the value the caller read is still stored.

        Args:
            key: The lock key.
            token: The token the caller read.
            arguments: The token, the new JSON, and the life in seconds.

        Returns:
            1 after a write, and 0 when a third party changed the value first.
        """
        if key in self.values and not self._holds(key, token):
            return 0
        self.values[key] = str(arguments[1])
        self.expiries[key] = int(arguments[2])
        return 1


@pytest.fixture
def store() -> ScriptedLockStore:
    """Return one empty lock store double.

    Returns:
        A double that answers `set`, `get`, and `eval`.
    """
    return ScriptedLockStore()


@pytest.fixture(autouse=True)
def audit_trail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the takeover trail at a directory this test owns.

    Why:
        A takeover appends one line to the trail. Without this fixture the
        suite would write into the `data/` directory of the checkout, and one
        test run would leave a file behind for the next run to read.

    Args:
        tmp_path: The directory pytest gives this test.
        monkeypatch: Replaces the directory constant of the lock module.

    Returns:
        The path of the trail file this test owns.
    """
    monkeypatch.setattr(lock_module, "AUDIT_DIRECTORY", str(tmp_path))
    return tmp_path / lock_module.AUDIT_FILE_NAME


def read_audit_lines(trail: Path) -> list[dict[str, str]]:
    """Return every audit record the trail holds.

    Args:
        trail: The path of the append-only audit file.

    Returns:
        One dictionary for each line, in the order the module wrote them.
    """
    if not trail.exists():  # A test that expects no record reads an empty list
        return []
    lines = trail.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line]


def build_request(owner: SessionOwner, confirmation_text: str = "", site_id: str = SITE_ID) -> LockRequest:
    """Build one acquisition request.

    Args:
        owner: The operator and browser pair that would hold the lock.
        confirmation_text: The word the operator typed.
        site_id: The site the operator wants to drive.

    Returns:
        The request value.
    """
    return LockRequest(
        org_id=ORG_ID,
        site_id=site_id,
        owner=owner,
        run_id=RUN_ID,
        confirmation_text=confirmation_text,
    )


def seed_lock(store: ScriptedLockStore, owner: SessionOwner, age_seconds: float) -> LockRecord:
    """Put one lock of a chosen age into the store.

    Why:
        The cooldown depends on the stored heartbeat time and not on a clock
        patch, so a test controls the age by writing the time it wants. No test
        needs to wait.

        The seed also records the lease that a real acquire would have set. A
        seed without the lease would keep a key that the real server drops. A
        takeover test would then prove a state that production never reaches.

    Args:
        store: The lock store double.
        owner: The operator that holds the seeded lock.
        age_seconds: How long the holder has been quiet.

    Returns:
        The record the store now holds.
    """
    moment = (datetime.now(UTC) - timedelta(seconds=age_seconds)).isoformat()
    record = LockRecord(
        owner=owner,
        lock_token=SEEDED_TOKEN,
        run_id=RUN_ID,
        acquired_at=moment,
        refreshed_at=moment,
    )
    store.values[SITE_KEY] = record.to_json()
    store.expiries[SITE_KEY] = LOCK_TTL_SECONDS  # The lease a real acquire writes with the same operation
    return record


def stored_record(store: ScriptedLockStore) -> LockRecord:
    """Return the record the store holds for the shared site.

    Args:
        store: The lock store double.

    Returns:
        The stored record.
    """
    held = LockRecord.from_json(store.values[SITE_KEY])
    assert held is not None  # A test that reads the store expects a usable value
    return held


def test_the_key_repeats_the_contract_shape() -> None:
    """The key matches the row of contracts/site-lock.md line 21.

    Why:
        A worker that builds a different key locks a different name, and two
        operators would both win.
    """
    assert build_key(ORG_ID, SITE_ID) == SITE_KEY


def test_the_settings_repeat_the_contract_numbers() -> None:
    """The life, the cooldown, the beat, and the word match the contract.

    Why:
        The browser and the run driver both read these values. A quiet change
        to one of them would break the cooldown that guards a takeover.

        The life must stay above the cooldown. A life equal to the cooldown
        drops the key at the same second the holder turns quiet. The portal
        would then find no holder to name, and the typed word CONFIRM would
        reach no branch.
    """
    assert LOCK_TTL_SECONDS == 3600
    assert COOLDOWN_SECONDS == 300
    assert HEARTBEAT_SECONDS == 60
    assert TAKEOVER_CONFIRMATION_TEXT == "CONFIRM"
    assert LOCK_TTL_SECONDS > COOLDOWN_SECONDS  # A quiet holder must still hold a readable key


def test_a_free_site_grants_the_lock(store: ScriptedLockStore) -> None:
    """A free site answers with a fresh token and the state `acquired`.

    Why:
        contracts/site-lock.md line 56 answers 200 with the token when the
        atomic write wins.

    Args:
        store: The lock store double.
    """
    grant = acquire_site_lock(build_request(FIRST_OWNER), client=store)

    assert grant.state is LockState.ACQUIRED
    assert grant.record.lock_token != ""
    assert grant.expires_in == LOCK_TTL_SECONDS
    assert stored_record(store).owner == FIRST_OWNER


def test_the_acquisition_uses_one_atomic_write(store: ScriptedLockStore) -> None:
    """The acquisition writes with the `nx` flag and the contract life.

    Why:
        contracts/site-lock.md line 69 forbids a read followed by a write. The
        `nx` flag makes the store decide the race, so exactly one operator wins.

    Args:
        store: The lock store double.
    """
    acquire_site_lock(build_request(FIRST_OWNER), client=store)

    assert store.set_calls == [(SITE_KEY, True, LOCK_TTL_SECONDS)]
    assert store.expiries[SITE_KEY] == LOCK_TTL_SECONDS


def test_the_stored_value_holds_the_six_contract_fields(store: ScriptedLockStore) -> None:
    """The stored JSON holds the six fields the contract shows and no other.

    Why:
        contracts/site-lock.md lines 26 to 33 fix the value. A reader of a
        different release parses this text, so an extra field or a missing
        field breaks that reader.

    Args:
        store: The lock store double.
    """
    acquire_site_lock(build_request(FIRST_OWNER), client=store)

    assert tuple(sorted(json.loads(store.values[SITE_KEY]))) == CONTRACT_FIELDS


def test_a_held_site_refuses_a_second_operator(store: ScriptedLockStore) -> None:
    """An active holder blocks a different operator.

    Why:
        contracts/site-lock.md line 58 answers 409 `site_locked` while the
        holder is under the cooldown.

    Args:
        store: The lock store double.
    """
    acquire_site_lock(build_request(FIRST_OWNER), client=store)

    with pytest.raises(SiteLockedError) as refusal:
        acquire_site_lock(build_request(SECOND_OWNER), client=store)

    assert refusal.value.code == "site_locked"
    assert stored_record(store).owner == FIRST_OWNER


def test_a_different_operator_just_under_the_cooldown_still_waits(store: ScriptedLockStore) -> None:
    """A holder one second short of the cooldown keeps the site.

    Why:
        contracts/site-lock.md line 58 names the boundary as age under 300
        seconds, so the refusal must hold right up to the boundary.

    Args:
        store: The lock store double.
    """
    seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS - 1)

    with pytest.raises(SiteLockedError) as refusal:
        acquire_site_lock(build_request(SECOND_OWNER, TAKEOVER_CONFIRMATION_TEXT), client=store)

    assert refusal.value.code == "site_locked"


def test_the_same_operator_and_browser_resume_with_no_typed_word(store: ScriptedLockStore) -> None:
    """One operator returning in the same browser gets the stored token back.

    Why:
        contracts/site-lock.md line 57 answers 200 with the stored token and
        the state `resume`, and asks for no typed word.

    Args:
        store: The lock store double.
    """
    first = acquire_site_lock(build_request(FIRST_OWNER), client=store)

    second = acquire_site_lock(build_request(FIRST_OWNER), client=store)

    assert second.state is LockState.RESUMED
    assert second.record.lock_token == first.record.lock_token


def test_one_operator_holds_two_sites_at_once(store: ScriptedLockStore) -> None:
    """One operator may drive two sites in two tabs.

    Why:
        The lock covers one site. One person with several tabs is one holder
        on each site, so a second site must not refuse the same operator.

    Args:
        store: The lock store double.
    """
    first = acquire_site_lock(build_request(FIRST_OWNER), client=store)
    second = acquire_site_lock(build_request(FIRST_OWNER, site_id=OTHER_SITE_ID), client=store)

    assert first.state is LockState.ACQUIRED
    assert second.state is LockState.ACQUIRED


def test_a_second_computer_of_one_operator_is_a_different_holder(store: ScriptedLockStore) -> None:
    """The same address in a different browser cannot resume.

    Why:
        contracts/site-lock.md line 41 says the pair of address and browser
        decides a resume. Two computers hold two browser values, so the second
        computer is a different holder.

    Args:
        store: The lock store double.
    """
    acquire_site_lock(build_request(FIRST_OWNER), client=store)

    with pytest.raises(SiteLockedError) as refusal:
        acquire_site_lock(build_request(FIRST_OWNER_SECOND_COMPUTER), client=store)

    assert refusal.value.code == "site_locked"


def test_a_different_operator_after_the_cooldown_must_type_confirm(store: ScriptedLockStore) -> None:
    """A quiet holder yields only after the new operator types the word.

    Why:
        contracts/site-lock.md line 59 answers 400 `confirmation_required` once
        the holder passed the full 300 second cooldown.

    Args:
        store: The lock store double.
    """
    seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)

    with pytest.raises(ConfirmationRequiredError) as refusal:
        acquire_site_lock(build_request(SECOND_OWNER), client=store)

    assert refusal.value.code == "confirmation_required"
    assert refusal.value.needed_text == TAKEOVER_CONFIRMATION_TEXT
    assert stored_record(store).owner == FIRST_OWNER


def test_the_typed_word_still_works_one_second_before_the_lease_ends(store: ScriptedLockStore) -> None:
    """A holder that stayed quiet for almost the whole lease still yields to the word.

    Why:
        The takeover needs a lock record that still exists and that already
        turned quiet. That window runs from the cooldown to the lease. An
        earlier release set the lease and the cooldown to the same 300 seconds,
        which closed the window to nothing and left the word CONFIRM
        unreachable in production.

        This test holds the far edge of the window. It fails if a later change
        lowers the lease toward the cooldown again.

    Args:
        store: The lock store double.
    """
    seed_lock(store, FIRST_OWNER, LOCK_TTL_SECONDS - 1)

    grant = acquire_site_lock(build_request(SECOND_OWNER, TAKEOVER_CONFIRMATION_TEXT), client=store)

    assert grant.state is LockState.TAKEN_OVER
    assert grant.audit is not None
    assert stored_record(store).owner == SECOND_OWNER


def test_a_holder_past_the_lease_leaves_no_record_and_needs_no_typed_word(store: ScriptedLockStore) -> None:
    """A lock that outlived the lease is gone, so the next operator just wins.

    Why:
        The real server deletes the key when the lease runs out. The next
        operator then meets a free site, and the atomic write grants the lock
        with no word to type and no audit record to write.

        The portal names no old holder here, because the store holds none. That
        is the reason the lease sits far above the cooldown. A short lease would
        make this the common path and would erase an abandoned session in
        silence.

    Args:
        store: The lock store double.
    """
    seed_lock(store, FIRST_OWNER, LOCK_TTL_SECONDS + 1)

    grant = acquire_site_lock(build_request(SECOND_OWNER), client=store)

    assert grant.state is LockState.ACQUIRED
    assert grant.audit is None
    assert grant.record.lock_token != SEEDED_TOKEN
    assert stored_record(store).owner == SECOND_OWNER


def test_the_store_double_drops_a_key_the_real_server_would_have_dropped(store: ScriptedLockStore) -> None:
    """The double answers a read of an expired key with nothing.

    Why:
        Every takeover test seeds a quiet lock and then reads it back. A double
        that keeps each key for ever would answer a state that the real server
        cannot reach, and each of those tests would prove nothing.

        This test guards the double itself. It holds both sides of the lease
        boundary, so a double that stops honoring the expiry fails here first
        and names the cause.

    Args:
        store: The lock store double.
    """
    seed_lock(store, FIRST_OWNER, LOCK_TTL_SECONDS - 1)
    assert store.get(SITE_KEY) is not None  # Inside the lease, so the real server keeps it

    seed_lock(store, FIRST_OWNER, LOCK_TTL_SECONDS + 1)
    assert store.get(SITE_KEY) is None  # Past the lease, so the real server dropped it


@pytest.mark.parametrize("typed", ["confirm", "Confirm", "CONFIRM ", " CONFIRM", "YES", ""])
def test_a_wrong_confirmation_word_leaves_the_holder_in_place(store: ScriptedLockStore, typed: str) -> None:
    """Only the exact word in the exact letter case moves the lock.

    Why:
        A takeover erases the decisions the earlier operator left in flight,
        so the module compares the word without a trim and without a case
        change, which repeats the stop word rule of `runtime/signals.py`.

    Args:
        store: The lock store double.
        typed: The text the operator typed.
    """
    seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)

    with pytest.raises(ConfirmationRequiredError) as refusal:
        acquire_site_lock(build_request(SECOND_OWNER, typed), client=store)

    assert refusal.value.code == "confirmation_required"
    assert stored_record(store).lock_token == SEEDED_TOKEN


def test_the_confirmed_takeover_moves_the_site_and_writes_an_audit(store: ScriptedLockStore) -> None:
    """The word CONFIRM moves the lock and reports the audit record.

    Why:
        contracts/site-lock.md line 120 asks for an audit record that holds the
        old address, the new address, and the time.

    Args:
        store: The lock store double.
    """
    seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)

    grant = acquire_site_lock(build_request(SECOND_OWNER, TAKEOVER_CONFIRMATION_TEXT), client=store)

    assert grant.state is LockState.TAKEN_OVER
    assert grant.record.lock_token != SEEDED_TOKEN
    assert stored_record(store).owner == SECOND_OWNER
    assert grant.audit is not None
    assert grant.audit.to_record()["previous_actor_email"] == FIRST_OWNER.actor_email


class AuditSinkFault(RuntimeError):
    """A stand-in for a sink fault whose message holds a connection string.

    Why:
        A real driver names the host and the account in the fault message, and
        sometimes the password. The takeover tests raise this class to prove
        that the module logs the class name alone.
    """


def raise_audit_fault(document: dict[str, str]) -> None:
    """Refuse one audit write.

    Args:
        document: The record the module tried to store.

    Raises:
        AuditSinkFault: Always. The message names a secret no log may repeat.
    """
    raise AuditSinkFault(AUDIT_FAULT_MESSAGE)


def test_the_confirmed_takeover_writes_one_record_to_the_audit_trail(
    store: ScriptedLockStore,
    audit_trail: Path,
) -> None:
    """A takeover adds exactly one record to the trail.

    Why:
        contracts/site-lock.md line 120 asks the portal to write an audit
        record for every takeover. The module built the record and dropped it,
        so a takeover left no trace at all.

    Args:
        store: The lock store double.
        audit_trail: The trail file this test owns.
    """
    seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)

    acquire_site_lock(build_request(SECOND_OWNER, TAKEOVER_CONFIRMATION_TEXT), client=store)

    assert len(read_audit_lines(audit_trail)) == 1


def test_the_stored_audit_names_both_addresses_and_the_time(
    store: ScriptedLockStore,
    audit_trail: Path,
) -> None:
    """The stored record holds the old address, the new address, and the time.

    Why:
        contracts/site-lock.md line 120 fixes these three fields. The record
        carries the organization and the site as well, because a reader cannot
        place a row that names no site.

    Args:
        store: The lock store double.
        audit_trail: The trail file this test owns.
    """
    seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)

    acquire_site_lock(build_request(SECOND_OWNER, TAKEOVER_CONFIRMATION_TEXT), client=store)

    record = read_audit_lines(audit_trail)[0]
    assert record["previous_actor_email"] == FIRST_OWNER.actor_email
    assert record["actor_email"] == SECOND_OWNER.actor_email
    assert record["org_id"] == ORG_ID
    assert record["site_id"] == SITE_ID
    written_at = datetime.fromisoformat(record["occurred_at"])
    assert written_at.utcoffset() == timedelta(0)  # One clock in UTC for every stored time
    assert abs(datetime.now(UTC) - written_at) < timedelta(minutes=1)


def test_a_failed_audit_write_stops_the_takeover(
    store: ScriptedLockStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sink that refuses the record leaves the site with the current holder.

    Why:
        `contracts/site-lock.md` line 120 asks for a record of every takeover.
        A takeover with no record removes the one trail that names who took a
        site from whom, so the portal refuses the takeover instead.

    Args:
        store: The lock store double.
        monkeypatch: Replaces the sink with one that always raises.
    """
    seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)
    monkeypatch.setattr(lock_module, "_append_audit_line", raise_audit_fault)

    with pytest.raises(TakeoverAuditError):
        acquire_site_lock(build_request(SECOND_OWNER, TAKEOVER_CONFIRMATION_TEXT), client=store)

    assert stored_record(store).owner == FIRST_OWNER  # The lock never moved


def test_the_failed_audit_write_logs_the_class_and_never_the_message(
    store: ScriptedLockStore,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The warning names the fault class and repeats no message and no address.

    Why:
        A driver message can hold a connection string with an account and a
        password, and an audit record holds two work email addresses. Neither
        may reach a log line.

    Args:
        store: The lock store double.
        monkeypatch: Replaces the sink with one that always raises.
        caplog: Captures the log records the module writes.
    """
    seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)
    monkeypatch.setattr(lock_module, "_append_audit_line", raise_audit_fault)
    caplog.set_level(logging.WARNING)

    with pytest.raises(TakeoverAuditError):
        acquire_site_lock(build_request(SECOND_OWNER, TAKEOVER_CONFIRMATION_TEXT), client=store)

    written = caplog.text
    assert "AuditSinkFault" in written
    assert AUDIT_FAULT_MESSAGE not in written
    assert FIRST_OWNER.actor_email not in written
    assert SECOND_OWNER.actor_email not in written


def test_the_refused_takeover_names_no_address_in_its_sentence(
    store: ScriptedLockStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The sentence the operator reads holds no address and no path.

    Why:
        The page prints the sentence of the failure. A sink fault can name a
        directory of the host, and the audit record holds two work email
        addresses. Neither belongs on a page an operator reads.

    Args:
        store: The lock store double.
        monkeypatch: Replaces the sink with one that always raises.
    """
    seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)
    monkeypatch.setattr(lock_module, "_append_audit_line", raise_audit_fault)

    with pytest.raises(TakeoverAuditError) as caught:
        acquire_site_lock(build_request(SECOND_OWNER, TAKEOVER_CONFIRMATION_TEXT), client=store)

    sentence = str(caught.value)
    assert caught.value.code == "takeover_audit_failed"  # The route maps this code to 503
    assert AUDIT_FAULT_MESSAGE not in sentence
    assert FIRST_OWNER.actor_email not in sentence
    assert SECOND_OWNER.actor_email not in sentence


def test_a_relative_audit_directory_lands_beside_the_checkout(monkeypatch: pytest.MonkeyPatch) -> None:
    """A bare directory name anchors against the repository, not the shell.

    Why:
        A portal started by a service manager, by a container, or from another
        directory would otherwise leave the trail where no reader looks. Two
        starts from two directories would then split one site history across
        two files.

    Args:
        monkeypatch: Sets the directory to a bare name.
    """
    monkeypatch.setattr(lock_module, "AUDIT_DIRECTORY", "data")

    path = lock_module._audit_path()

    checkout = Path(__file__).resolve().parents[3]  # This file sits at the same depth as the module under test
    assert path == checkout / "data" / lock_module.AUDIT_FILE_NAME


def test_an_absolute_audit_directory_stands_as_written(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A directory a caller names in full reaches the sink unchanged.

    Why:
        A test points the trail at a directory it owns, and a deployment can
        name a volume outside the checkout. The portal re-anchors neither.

    Args:
        tmp_path: The directory this test owns.
        monkeypatch: Sets the directory to that absolute path.
    """
    monkeypatch.setattr(lock_module, "AUDIT_DIRECTORY", str(tmp_path))

    path = lock_module._audit_path()

    assert path == tmp_path / lock_module.AUDIT_FILE_NAME


def test_the_same_operator_after_the_cooldown_types_continue(store: ScriptedLockStore) -> None:
    """A quiet session of one operator asks that operator for `continue`.

    Why:
        The returning operator would erase decisions their own earlier session
        left in flight. The lighter word marks the act without the weight of a
        takeover, because no second person loses work.

    Args:
        store: The lock store double.
    """
    seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)

    with pytest.raises(ConfirmationRequiredError) as refusal:
        acquire_site_lock(build_request(FIRST_OWNER), client=store)

    assert refusal.value.code == "confirmation_required"
    assert refusal.value.needed_text == RESUME_CONFIRMATION_TEXT


def test_the_typed_continue_returns_the_quiet_session(store: ScriptedLockStore) -> None:
    """The word `continue` gives the site back to its own operator.

    Why:
        The state stays `resume`, because the same person holds the site
        before and after. Only the token changes, so an older tab cannot beat.

    Args:
        store: The lock store double.
    """
    seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)

    grant = acquire_site_lock(build_request(FIRST_OWNER, RESUME_CONFIRMATION_TEXT), client=store)

    assert grant.state is LockState.RESUMED
    assert grant.record.lock_token != SEEDED_TOKEN
    assert grant.audit is None
    assert stored_record(store).owner == FIRST_OWNER


def test_the_word_continue_still_works_one_second_before_the_lease_ends(store: ScriptedLockStore) -> None:
    """An operator who returns late in the lease still gets the lighter word.

    Why:
        The resume guard needs the same live and quiet record that a takeover
        needs. A lease equal to the cooldown broke both branches at once, so the
        far edge of the window needs a test on each side.

        An operator who steps away for an hour and returns must read the word
        `continue` and not lose their own in-flight decisions in silence.

    Args:
        store: The lock store double.
    """
    seed_lock(store, FIRST_OWNER, LOCK_TTL_SECONDS - 1)

    grant = acquire_site_lock(build_request(FIRST_OWNER, RESUME_CONFIRMATION_TEXT), client=store)

    assert grant.state is LockState.RESUMED
    assert grant.audit is None
    assert stored_record(store).owner == FIRST_OWNER


def test_a_racing_takeover_loses_to_the_operator_that_wrote_first(store: ScriptedLockStore) -> None:
    """Two operators who both type the word do not both win.

    Why:
        The compare and the write run as one step. This test changes the store
        between the read and the write, which models the other operator
        winning the race, and the loser must be refused.

    Args:
        store: The lock store double.
    """
    seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)
    winner = LockRecord(
        owner=FIRST_OWNER_SECOND_COMPUTER,
        lock_token="a-different-token",
        run_id=RUN_ID,
        acquired_at=datetime.now(UTC).isoformat(),
        refreshed_at=datetime.now(UTC).isoformat(),
    )
    store.after_get = lambda: store.values.__setitem__(SITE_KEY, winner.to_json())

    with pytest.raises(SiteLockedError) as refusal:
        acquire_site_lock(build_request(SECOND_OWNER, TAKEOVER_CONFIRMATION_TEXT), client=store)

    assert refusal.value.code == "site_locked"
    assert stored_record(store).lock_token == "a-different-token"


def test_a_heartbeat_extends_the_lock_the_caller_holds(store: ScriptedLockStore) -> None:
    """A beat moves the heartbeat time and leaves the first time alone.

    Why:
        contracts/site-lock.md line 89 answers 200 with the remaining life. The
        page still shows when the operator first took the site, so the beat
        must not move `acquired_at`.

    Args:
        store: The lock store double.
    """
    grant = acquire_site_lock(build_request(FIRST_OWNER), client=store)

    remaining = refresh_site_lock(SITE_KEY, grant.record, client=store)

    held = stored_record(store)
    assert remaining == LOCK_TTL_SECONDS
    assert held.acquired_at == grant.record.acquired_at
    assert held.refreshed_at >= grant.record.refreshed_at


def test_a_heartbeat_after_a_takeover_reports_the_lock_lost(store: ScriptedLockStore) -> None:
    """A beat cannot extend a lock that changed hands.

    Why:
        contracts/site-lock.md line 90 answers 409 `lock_lost`. The compare and
        the extend run as one step for exactly this case.

    Args:
        store: The lock store double.
    """
    stale = seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)
    acquire_site_lock(build_request(SECOND_OWNER, TAKEOVER_CONFIRMATION_TEXT), client=store)

    with pytest.raises(LockLostError) as refusal:
        refresh_site_lock(SITE_KEY, stale, client=store)

    assert refusal.value.code == "lock_lost"
    assert stored_record(store).owner == SECOND_OWNER


def test_a_heartbeat_on_a_free_site_reports_the_lock_lost(store: ScriptedLockStore) -> None:
    """A beat never brings an expired lock back.

    Why:
        The refresh script returns 0 for an absent key. A beat that wrote the
        key again would hold a site that the store already freed.

    Args:
        store: The lock store double.
    """
    record = seed_lock(store, FIRST_OWNER, 0)
    store.values.clear()

    with pytest.raises(LockLostError) as refusal:
        refresh_site_lock(SITE_KEY, record, client=store)

    assert refusal.value.code == "lock_lost"
    assert store.values == {}


def test_a_release_frees_the_site(store: ScriptedLockStore) -> None:
    """A release deletes the key the caller holds.

    Why:
        contracts/site-lock.md line 105 releases the lock when a run reaches
        `complete`, `stopped`, or `failed`.

    Args:
        store: The lock store double.
    """
    grant = acquire_site_lock(build_request(FIRST_OWNER), client=store)

    outcome = release_site_lock(SITE_KEY, grant.record, client=store)

    assert outcome is ReleaseOutcome.RELEASED
    assert SITE_KEY not in store.values


def test_a_release_with_an_old_token_reports_the_lock_lost(store: ScriptedLockStore) -> None:
    """A release never deletes a lock that a later operator holds.

    Why:
        contracts/site-lock.md line 103 answers 409 `lock_lost`. A plain delete
        would drop the lock of the operator who took the site.

    Args:
        store: The lock store double.
    """
    stale = seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)
    acquire_site_lock(build_request(SECOND_OWNER, TAKEOVER_CONFIRMATION_TEXT), client=store)

    with pytest.raises(LockLostError) as refusal:
        release_site_lock(SITE_KEY, stale, client=store)

    assert refusal.value.code == "lock_lost"
    assert refusal.value.outcome is ReleaseOutcome.HELD_BY_ANOTHER
    assert stored_record(store).owner == SECOND_OWNER


def test_a_release_of_an_expired_lock_reads_apart_from_a_stolen_lock(store: ScriptedLockStore) -> None:
    """The two ways to delete nothing carry two different outcomes.

    Why:
        A lock that expired left the site free, and the run merely ended late.
        A lock that another operator holds means a takeover moved the site
        while the run wrote firmware. Both answer `lock_lost` to the browser,
        so only the outcome tells an operator which event happened.

    Args:
        store: The lock store double.
    """
    grant = acquire_site_lock(build_request(FIRST_OWNER), client=store)
    store.values.pop(SITE_KEY)  # The lock ran out of its 300-second life

    with pytest.raises(LockLostError) as refusal:
        release_site_lock(SITE_KEY, grant.record, client=store)

    assert refusal.value.outcome is ReleaseOutcome.ALREADY_FREE
    assert refusal.value.outcome is not ReleaseOutcome.HELD_BY_ANOTHER


def test_the_release_script_keeps_its_three_answers_apart(store: ScriptedLockStore) -> None:
    """The shipped Lua compares, deletes, and answers three ways.

    Why:
        No unit test runs Lua, so every other test reads the script through a
        double. This test reads the shipped text, and it fails when an edit
        drops the compare, the delete, or one of the three answers.

    Args:
        store: The lock store double.
    """
    assert "if held['lock_token'] ~= ARGV[1] then return 0 end" in _RELEASE_SCRIPT
    assert "if not current then return 2 end" in _RELEASE_SCRIPT
    assert "redis.call('DEL', KEYS[1])" in _RELEASE_SCRIPT
    assert _RELEASE_SCRIPT.rstrip().endswith("return 1")
    assert store.values == {}  # The script text needs no store, and this test opens none


def test_an_unreachable_store_refuses_an_acquisition(store: ScriptedLockStore) -> None:
    """A dead lock store refuses the upgrade start and writes nothing.

    Why:
        contracts/site-lock.md line 136 answers 503 and line 140 forbids a
        fallback to a lock in process memory. A fallback would let two workers
        each believe they hold the site.

    Args:
        store: The lock store double.
    """
    store.fail = True

    with pytest.raises(LockStoreUnreachableError) as refusal:
        acquire_site_lock(build_request(FIRST_OWNER), client=store)

    assert refusal.value.code == "lock_store_unreachable"
    assert store.values == {}


def test_an_unreachable_store_refuses_a_heartbeat_and_a_release(store: ScriptedLockStore) -> None:
    """Every write of the lock fails closed, and never in silence.

    Why:
        A beat that answered success without reaching Redis would let the run
        drive on with no lock behind it.

    Args:
        store: The lock store double.
    """
    grant = acquire_site_lock(build_request(FIRST_OWNER), client=store)
    store.fail = True

    with pytest.raises(LockStoreUnreachableError):
        refresh_site_lock(SITE_KEY, grant.record, client=store)
    with pytest.raises(LockStoreUnreachableError):
        release_site_lock(SITE_KEY, grant.record, client=store)


def test_an_unreachable_store_still_answers_the_site_list(store: ScriptedLockStore) -> None:
    """A read never raises, even when every command fails.

    Why:
        contracts/site-lock.md line 138 says viewing must not need Redis. A
        page that refused to render would punish a reader for a lock fault.

    Args:
        store: The lock store double.
    """
    store.fail = True

    assert read_site_locks(ORG_ID, [SITE_ID], store) == {SITE_ID: None}
    assert read_lock(ORG_ID, SITE_ID, store) is None


def test_no_client_answers_an_empty_index_and_refuses_a_write(monkeypatch: pytest.MonkeyPatch) -> None:
    """A store that never opens still lets a page render, and blocks a start.

    Why:
        This is the split at the center of the module. The read fails open and
        the write fails closed, so a fault hides no page and starts no upgrade.

    Args:
        monkeypatch: Replaces the connection helper with one that opens nothing.
    """
    monkeypatch.setattr(lock_module, "connect_lock_store", lambda settings=None: None)

    assert read_site_locks(ORG_ID, [SITE_ID]) == {}
    assert read_lock(ORG_ID, SITE_ID) is None
    with pytest.raises(LockStoreUnreachableError) as refusal:
        acquire_site_lock(build_request(FIRST_OWNER))

    assert refusal.value.code == "lock_store_unreachable"


def test_the_reader_answers_the_shape_the_site_list_expects(store: ScriptedLockStore) -> None:
    """The reader answers a holder address for a held site and None for a free one.

    Why:
        `app/routes/select.py` loads this reader through the `SITE_LOCK_READER`
        seam, calls it with two positional arguments, and puts each value
        straight into the `locked_by` field of a row.

    Args:
        store: The lock store double.
    """
    acquire_site_lock(build_request(FIRST_OWNER), client=store)

    holders = read_site_locks(ORG_ID, [SITE_ID, OTHER_SITE_ID], store)

    assert holders == {SITE_ID: FIRST_OWNER.actor_email, OTHER_SITE_ID: None}


def test_a_damaged_value_reads_as_no_holder(store: ScriptedLockStore) -> None:
    """A value that is not a lock record never breaks a page.

    Why:
        A value written by an older release, or damaged by hand, would
        otherwise hide the whole site list behind one bad key.

    Args:
        store: The lock store double.
    """
    store.values[SITE_KEY] = "{ this is not json"

    assert read_site_locks(ORG_ID, [SITE_ID], store) == {SITE_ID: None}
    assert read_lock(ORG_ID, SITE_ID, store) is None


def test_a_damaged_value_holds_the_site_until_the_key_expires(store: ScriptedLockStore) -> None:
    """A damaged value refuses an acquisition instead of overwriting the key.

    Why:
        The module cannot name the holder of a damaged value, so it cannot
        prove that the cooldown passed. The key carries a 300 second life, so
        the site frees itself without a hand repair.

    Args:
        store: The lock store double.
    """
    store.values[SITE_KEY] = "{ this is not json"

    with pytest.raises(SiteLockedError) as refusal:
        acquire_site_lock(build_request(FIRST_OWNER), client=store)

    assert refusal.value.code == "site_locked"


def test_no_log_record_holds_an_address_or_a_token(store: ScriptedLockStore, caplog: pytest.LogCaptureFixture) -> None:
    """The log holds the email digest, and never the address or the token.

    Why:
        `runtime/identity.py` keeps every address out of a log record, and
        contracts/site-lock.md line 37 keeps every lock token out of one.

    Args:
        store: The lock store double.
        caplog: Captures the log records the module writes.
    """
    caplog.set_level(logging.INFO)
    seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)

    grant = acquire_site_lock(build_request(SECOND_OWNER, TAKEOVER_CONFIRMATION_TEXT), client=store)

    written = caplog.text
    assert FIRST_OWNER.actor_email not in written
    assert SECOND_OWNER.actor_email not in written
    assert grant.record.lock_token not in written
    assert SECOND_OWNER.email_digest in written


def test_a_grant_carries_no_audit_for_a_plain_acquisition(store: ScriptedLockStore) -> None:
    """Only a takeover carries an audit record.

    Why:
        The run store writes the audit record it receives. An audit on every
        acquisition would fill the history with events that never happened.

    Args:
        store: The lock store double.
    """
    grant: LockGrant = acquire_site_lock(build_request(FIRST_OWNER), client=store)

    assert grant.audit is None


def test_one_failed_connection_stops_the_next_attempt(monkeypatch: pytest.MonkeyPatch) -> None:
    """A store that did not answer is not asked again inside the window.

    Why:
        A host name that does not resolve costs seconds that no socket limit
        can shorten. One request pays that cost. Without this window every page
        that reads the lock state would pay it again, and viewing would need
        Redis after all.

    Args:
        monkeypatch: Counts the connection attempts the module makes.
    """
    attempts: list[int] = []
    monkeypatch.setattr(lock_module, "_open_client", lambda settings: attempts.append(1))
    lock_module.reset_connection()

    assert connect_lock_store() is None
    assert connect_lock_store() is None
    assert len(attempts) == 1


def test_a_reset_lets_the_module_try_the_store_again(monkeypatch: pytest.MonkeyPatch) -> None:
    """A reset clears the window, so a repaired store connects at once.

    Why:
        An operator who starts Redis must not wait out the window, and a test
        must be able to put the module back to a known state.

    Args:
        monkeypatch: Counts the connection attempts the module makes.
    """
    attempts: list[int] = []
    monkeypatch.setattr(lock_module, "_open_client", lambda settings: attempts.append(1))
    lock_module.reset_connection()

    connect_lock_store()
    lock_module.reset_connection()
    connect_lock_store()

    assert len(attempts) == 2


def test_the_shared_client_opens_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """A working store opens one shared client for the whole process.

    Why:
        Each open costs a round trip for the `PING` that proves the server
        answers. One handle for each worker keeps that cost off every request.

    Args:
        monkeypatch: Replaces the open with a counter that answers a stand-in.
    """
    attempts: list[int] = []
    opened = ScriptedLockStore()

    def count_and_answer(settings: Any) -> ScriptedLockStore:
        """Count one open and answer the same stand-in every time.

        Why:
            A list append states no value, so a lambda cannot both count the
            open and answer the handle.

        Args:
            settings: The Redis settings the module passes.

        Returns:
            The one stand-in client of this test.
        """
        del settings  # The stand-in opens no socket, so the settings never apply
        attempts.append(1)  # One entry for each open the module performs
        return opened  # Every call answers the same handle, which is what the test proves

    monkeypatch.setattr(lock_module, "_open_client", count_and_answer)
    lock_module.reset_connection()

    first = connect_lock_store()
    second = connect_lock_store()
    lock_module.reset_connection()

    assert first is opened
    assert second is opened
    assert len(attempts) == 1


def test_the_connection_limits_are_short() -> None:
    """The client carries a connection limit, a command limit, and no retry.

    Why:
        A client with no limits waits on the operating system. The site list
        reads the lock state on every render, so an unbounded wait would hold
        the page until the operator gave up.
    """
    assert CONNECT_TIMEOUT_SECONDS <= 2.0
    assert COMMAND_TIMEOUT_SECONDS <= 5.0
    assert RETRY_AFTER_SECONDS >= 10


def test_a_heartbeat_keeps_the_same_token(store: ScriptedLockStore) -> None:
    """A beat extends the life and leaves the token alone.

    Why:
        The browser holds the token for the whole session and beats with it
        every 60 seconds. A beat that changed the token would make the next
        beat of the same browser fail, and the run would lose its own lock.

    Args:
        store: The lock store double.
    """
    grant = acquire_site_lock(build_request(FIRST_OWNER), client=store)

    refresh_site_lock(SITE_KEY, grant.record, client=store)

    assert stored_record(store).lock_token == grant.record.lock_token
    assert store.expiries[SITE_KEY] == LOCK_TTL_SECONDS


def test_a_second_release_reports_the_lock_lost(store: ScriptedLockStore) -> None:
    """A release of an already free site refuses instead of answering success.

    Why:
        The release script returns 2 for an absent key. A second release that
        answered success would tell the browser it still held something.

    Args:
        store: The lock store double.
    """
    grant = acquire_site_lock(build_request(FIRST_OWNER), client=store)
    release_site_lock(SITE_KEY, grant.record, client=store)

    with pytest.raises(LockLostError) as refusal:
        release_site_lock(SITE_KEY, grant.record, client=store)

    assert refusal.value.code == "lock_lost"
    assert refusal.value.outcome is ReleaseOutcome.ALREADY_FREE


def test_a_released_site_needs_no_typed_word_from_the_next_operator(store: ScriptedLockStore) -> None:
    """A release clears the cooldown, so the next operator types nothing.

    Why:
        FR-078 gives the cooldown to an abandoned session alone. An operator
        who gave the site back on purpose left no in-flight work to erase, so
        asking the next operator for CONFIRM would teach the word for nothing.

    Args:
        store: The lock store double.
    """
    grant = acquire_site_lock(build_request(FIRST_OWNER), client=store)
    release_site_lock(SITE_KEY, grant.record, client=store)

    second = acquire_site_lock(build_request(SECOND_OWNER), client=store)

    assert second.state is LockState.ACQUIRED
    assert stored_record(store).owner == SECOND_OWNER


def test_the_record_text_form_holds_no_token_and_no_address(store: ScriptedLockStore) -> None:
    """The text form of a record shows the digest, and never the token.

    Why:
        The generated dataclass form prints every field, so one `%s` of a whole
        record would put the token and the work email address in a log file.
        The hand-written form is the guard, and this test is what holds it.

    Args:
        store: The lock store double.
    """
    grant = acquire_site_lock(build_request(FIRST_OWNER), client=store)

    written = repr(grant.record)

    assert grant.record.lock_token not in written
    assert FIRST_OWNER.actor_email not in written
    assert FIRST_OWNER.email_digest in written
    assert RUN_ID in written  # The run identifier stays, because a log line needs it


def test_the_grant_text_form_holds_no_token(store: ScriptedLockStore) -> None:
    """The text form of a grant shows the state and the life, and no token.

    Why:
        A grant carries the record, so the generated form would print the token
        of that record through the record field.

    Args:
        store: The lock store double.
    """
    grant = acquire_site_lock(build_request(FIRST_OWNER), client=store)

    written = repr(grant)

    assert grant.record.lock_token not in written
    assert FIRST_OWNER.actor_email not in written
    assert "acquired" in written


def test_the_audit_text_form_holds_neither_address(store: ScriptedLockStore) -> None:
    """The text form of an audit record shows two digests and no address.

    Why:
        The audit holds two addresses on purpose, because the store keeps them.
        A traceback needs neither, and a traceback reaches a log file.

    Args:
        store: The lock store double.
    """
    seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)
    grant = acquire_site_lock(build_request(SECOND_OWNER, TAKEOVER_CONFIRMATION_TEXT), client=store)
    assert grant.audit is not None  # A takeover always reports the audit record

    written = repr(grant.audit)

    assert FIRST_OWNER.actor_email not in written
    assert SECOND_OWNER.actor_email not in written
    assert FIRST_OWNER.email_digest in written
    assert SECOND_OWNER.email_digest in written


def test_the_audit_record_still_holds_both_addresses(store: ScriptedLockStore) -> None:
    """The stored shape of an audit keeps the two addresses whole.

    Why:
        The text form hides the addresses, and a careless edit could hide them
        from the audit itself. contracts/site-lock.md line 120 asks the store to
        keep both, so a reviewer can name who took the site from whom.

    Args:
        store: The lock store double.
    """
    seed_lock(store, FIRST_OWNER, COOLDOWN_SECONDS + 1)
    grant = acquire_site_lock(build_request(SECOND_OWNER, TAKEOVER_CONFIRMATION_TEXT), client=store)
    assert grant.audit is not None  # A takeover always reports the audit record

    kept = grant.audit.to_record()

    assert kept["previous_actor_email"] == FIRST_OWNER.actor_email
    assert kept["actor_email"] == SECOND_OWNER.actor_email
    assert kept["occurred_at"] != ""
