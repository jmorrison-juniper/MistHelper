"""The Redis site lock that keeps two operators off one site.

Why:
    The older portal keeps its duplicate guard in process memory. The guard
    dies with a restart and never crosses a Gunicorn worker, so two operators
    can start an upgrade on one site at the same time. This module holds the
    guard in Redis, where every worker reads the same value.
    ``contracts/site-lock.md`` fixes the key, the value, and every command.

Failure policy:
    The policy differs by operation, and the difference is deliberate.

    A write fails closed. ``acquire_site_lock``, ``refresh_site_lock``, and
    ``release_site_lock`` raise ``LockStoreUnreachableError`` when the store
    does not answer, and the route reports 503. No path falls back to a lock in
    process memory. A memory fallback would let two workers each believe they
    hold the site, which is the exact failure this module prevents. The
    contract states this refusal at ``contracts/site-lock.md`` lines 116 and
    120.

    A read fails open. ``read_site_locks`` and ``read_lock`` never raise. An
    unreachable store answers with no holder, and the page still renders. An
    operator may view a site, a capture, a comparison, or a history page with
    no lock and with no typed word, so a dead lock store must not hide a page.
    The contract states this at ``contracts/site-lock.md`` line 118.

    Both halves need a bounded wait. A client with no limits waits on the
    operating system, and a page that reads the lock state then hangs behind a
    dead store. Every connection and every command therefore carries a limit,
    the client retries nothing, and a failed connection stops further attempts
    for ``RETRY_AFTER_SECONDS``.

Personal data:
    A log record here holds the value of ``email_digest`` and never a work
    email address, which repeats the rule of ``runtime/identity.py``. A log
    record never holds a ``lock_token`` either, which the contract states at
    line 37. The stored JSON does hold the address, because the site list
    shows the holder to the next operator.

    Every value class below replaces the generated ``__repr__``. The generated
    form prints each field, so one ``%s`` on a record, one ``logging.exception``
    call, or one traceback that shows a local value would publish the token and
    the address together. Naming each log line by hand keeps the rule only
    while every later author remembers it. Replacing the text form keeps the
    rule even when an author forgets, so the token cannot reach a log line by
    accident.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import json  # The lock value is a JSON string, per contracts/site-lock.md
import logging  # Action logging per Constitution VII
import os  # Reads the password value at connect time, and never holds it in a record
import secrets  # Builds the random lock token of each acquisition
from collections.abc import Callable  # The shape of one guarded store command
from dataclasses import dataclass, replace  # Immutable request, record, and grant values
from datetime import UTC, datetime  # ISO 8601 timestamps in UTC
from enum import StrEnum  # A page and a record hold the same state text
from pathlib import Path  # Locates the append-only takeover trail
from time import monotonic  # Times the window that follows a failed connection
from typing import Any, ClassVar, Final  # Store handles, error codes, and fixed settings

# The settings record lives in the app subpackage, which holds no HTTP import of
# its own. `app/routes/select.py` imports this module plainly, and the direction
# still stays one way, because this module reaches `app/config.py` alone and that
# module imports the standard library only.
from ..app.config import RedisSettings, load_redis_settings
from .identity import SessionOwner, email_digest  # The one identity notion, and the one safe form of an address

__all__ = [
    "ACQUIRE_ATTEMPTS",
    "AUDIT_DIRECTORY",
    "AUDIT_FILE_NAME",
    "COMMAND_TIMEOUT_SECONDS",
    "CONNECT_TIMEOUT_SECONDS",
    "COOLDOWN_SECONDS",
    "HEARTBEAT_SECONDS",
    "KEY_TEMPLATE",
    "LOCK_TTL_SECONDS",
    "RESUME_CONFIRMATION_TEXT",
    "RETRY_AFTER_SECONDS",
    "TAKEOVER_CONFIRMATION_TEXT",
    "ConfirmationRequiredError",
    "LockGrant",
    "LockLostError",
    "LockRecord",
    "LockRequest",
    "LockState",
    "LockStoreUnreachableError",
    "ReleaseOutcome",
    "SiteLockError",
    "SiteLockedError",
    "TakeoverAudit",
    "acquire_site_lock",
    "build_key",
    "connect_lock_store",
    "read_lock",
    "read_site_locks",
    "refresh_site_lock",
    "release_site_lock",
    "reset_connection",
]

_LOGGER: Final[logging.Logger] = logging.getLogger(__name__)  # One logger for the whole module

# WHAT: the Redis key of one site lock.
# WHY: contracts/site-lock.md line 21 fixes the shape. The organization and the
#      site live in the key, so the stored value holds neither.
KEY_TEMPLATE: Final[str] = "misthelper:lock:site:{org_id}:{site_id}"

# WHAT: how long a lock lives without a heartbeat.
# WHY: contracts/site-lock.md line 23 sets 300 seconds. A heartbeat every 60
#      seconds gives four missed beats before the lock expires.
LOCK_TTL_SECONDS: Final[int] = 300

# WHAT: how long a quiet holder keeps the site before another operator may take it.
# WHY: the contract calls this the full 300-second cooldown at line 105. The
#      value equals the lock life, so a lock that survives is never quiet.
COOLDOWN_SECONDS: Final[int] = 300

# WHAT: the gap between two heartbeats.
# WHY: contracts/site-lock.md line 84 sets 60 seconds for the browser and for
#      the run driver thread, so a closed browser does not drop a live upgrade.
HEARTBEAT_SECONDS: Final[int] = 60

# WHAT: the exact text that takes a quiet site from another operator.
# WHY: contracts/site-lock.md line 106 names this word and this letter case.
TAKEOVER_CONFIRMATION_TEXT: Final[str] = "CONFIRM"

# WHAT: the exact text that takes a quiet site back for its own operator.
# WHY: one operator who returns to an abandoned session of their own answers a
#      lighter prompt, because the takeover erases nobody else's decisions.
RESUME_CONFIRMATION_TEXT: Final[str] = "continue"

# WHAT: how many random bytes each lock token holds.
# WHY: 16 bytes give 22 URL-safe characters. The token proves which acquisition
#      holds the lock. It is not a credential, and it never reaches a log line.
LOCK_TOKEN_BYTES: Final[int] = 16

# WHAT: how many times an acquisition repeats the atomic write.
# WHY: a lock that expires between the write and the read is rare. One repeat
#      closes that gap, and a fixed count cannot spin.
ACQUIRE_ATTEMPTS: Final[int] = 2

# WHAT: how long a connection attempt and a command may take.
# WHY: contracts/site-lock.md line 118 says viewing must not need Redis. Without
#      these limits the client waits on the operating system, and a site list
#      that reads the lock state then hangs behind a dead store.
CONNECT_TIMEOUT_SECONDS: Final[float] = 1.0
COMMAND_TIMEOUT_SECONDS: Final[float] = 2.0

# WHAT: how long the module waits before it tries a failed store again.
# WHY: a host name that does not resolve costs seconds that no socket limit can
#      shorten. One request pays that cost. Every request inside the window then
#      answers at once, and the portal locks again as soon as Redis comes back.
RETRY_AFTER_SECONDS: Final[int] = 30

# WHAT: the value each Lua script returns when the caller still holds the lock.
# WHY: the contract tables at lines 79 and 92 read 1 as held and 0 as lost.
_SCRIPT_HELD: Final[int] = 1

# WHAT: the extra value the release script returns for a key that was already gone.
# WHY: the contract reads every value below 1 as lost, and an expired lock and a
#      stolen lock both answer 0. The two are not the same fault. An expired lock
#      left the site free. A stolen lock did not. The release names them apart, so
#      the caller can tell a real loss from a lock that simply ran out of life.
_SCRIPT_ABSENT: Final[int] = 2

# WHAT: the sentences the operator reads.
# WHY: the route reports the machine code, and the page shows one plain
#      sentence. No sentence holds an address, a token, or a host name.
LOCK_STORE_DOWN_MESSAGE: Final[str] = (
    "The lock store does not answer, so the portal cannot start an upgrade. Try again in a few minutes."
)
SITE_LOCKED_MESSAGE: Final[str] = "Another operator holds this site. Wait for that operator to finish."
TAKEOVER_MESSAGE: Final[str] = "The operator who holds this site went quiet. Type CONFIRM to take the site."
RESUME_MESSAGE: Final[str] = "Your earlier session on this site went quiet. Type continue to take it back."
LOCK_LOST_MESSAGE: Final[str] = "The portal no longer holds the lock on this site."
SITE_BUSY_MESSAGE: Final[str] = "The lock on this site changed hands during the request. Try again."

# WHAT: the compare and extend script of contracts/site-lock.md lines 69 to 77.
# WHY: the compare and the extend run as one step, so a heartbeat cannot extend
#      a lock that a different operator now holds. An absent key returns 0,
#      because a heartbeat must never bring a dead lock back.
_REFRESH_SCRIPT: Final[str] = """
local current = redis.call('GET', KEYS[1])
if not current then return 0 end
local held = cjson.decode(current)
if held['lock_token'] ~= ARGV[1] then return 0 end
redis.call('SET', KEYS[1], ARGV[2], 'EX', tonumber(ARGV[3]))
return 1
"""

# WHAT: the same compare, followed by a delete.
# WHY: contracts/site-lock.md line 90 asks for this pair. A plain delete would
#      drop a lock that a later operator acquired after a takeover. The compare
#      and the delete run as one step, so no second command can land between
#      them. The script answers 1 for a delete, 0 for a token that does not
#      match, and 2 for a key that was already gone.
_RELEASE_SCRIPT: Final[str] = """
local current = redis.call('GET', KEYS[1])
if not current then return 2 end
local held = cjson.decode(current)
if held['lock_token'] ~= ARGV[1] then return 0 end
redis.call('DEL', KEYS[1])
return 1
"""

# WHAT: the takeover write.
# WHY: the contract names the two takeover conditions at lines 105 and 106 but
#      gives no script. A read followed by a write would let two operators who
#      both type CONFIRM each believe they won. This script writes only while
#      the quiet record the caller read is still the stored one. An absent key
#      means the lock expired in the gap, so the caller takes the free site.
_TAKEOVER_SCRIPT: Final[str] = """
local current = redis.call('GET', KEYS[1])
if current then
  local held = cjson.decode(current)
  if held['lock_token'] ~= ARGV[1] then return 0 end
end
redis.call('SET', KEYS[1], ARGV[2], 'EX', tonumber(ARGV[3]))
return 1
"""

_REDIS_HANDLE: Any = None  # The shared client, opened once for each worker process
_LAST_FAILURE_AT: float | None = None  # When the last shared open failed, on the monotonic clock


class SiteLockError(Exception):
    """Base error for every site lock failure.

    Why:
        The route layer maps an error to an HTTP status and to a machine code.
        A shared base lets one handler catch every failure of this module and
        read the code from the same attribute.
    """

    code: ClassVar[str] = "site_lock_failed"  # Default machine code the route reports


class LockStoreUnreachableError(SiteLockError):
    """The lock store did not answer a write.

    Why:
        contracts/site-lock.md line 116 answers 503 and forbids a fallback to a
        lock in process memory.
    """

    code: ClassVar[str] = "lock_store_unreachable"  # Matches contracts/site-lock.md line 116


class SiteLockedError(SiteLockError):
    """A different operator holds the site and is still active.

    Why:
        contracts/site-lock.md line 58 answers 409 with this code.
    """

    code: ClassVar[str] = "site_locked"  # Matches contracts/site-lock.md line 58


class LockLostError(SiteLockError):
    """The caller no longer holds the lock it named.

    Why:
        contracts/site-lock.md lines 82 and 95 answer 409 with this code when a
        refresh or a release compares a token that the store no longer holds.

    Attributes:
        outcome: How one release lost the lock, or None when a refresh raised.
    """

    code: ClassVar[str] = "lock_lost"  # Matches contracts/site-lock.md lines 82 and 95

    def __init__(self, message: str, outcome: ReleaseOutcome | None = None) -> None:
        """Hold the plain sentence and how a release lost the lock.

        Why:
            The route answers the same code for both losses, so the difference
            travels on the error. A caller that must tell an expiry from a
            takeover reads this value instead of asking the store again.

        Args:
            message: One plain sentence for the operator.
            outcome: How one release lost the lock. None when a refresh raised.
        """
        super().__init__(message)
        self.outcome = outcome  # None keeps every earlier caller of one argument working


class ConfirmationRequiredError(SiteLockError):
    """The operator must type a word before the portal moves the lock.

    Why:
        contracts/site-lock.md line 59 answers 400 with this code. The module
        ``runtime/signals.py`` holds a class of the same name for the stop
        word, because the contract gives both refusals the same machine code.

    Attributes:
        needed_text: The exact word the operator must type.
    """

    code: ClassVar[str] = "confirmation_required"  # Matches contracts/site-lock.md line 59

    def __init__(self, message: str, needed_text: str) -> None:
        """Hold the plain sentence and the word the page must ask for.

        Args:
            message: One plain sentence for the operator.
            needed_text: The exact word the operator must type.
        """
        super().__init__(message)
        self.needed_text = needed_text  # The page prints this word, so the operator can copy it


class LockState(StrEnum):
    """How one caller came to hold the site lock.

    Why:
        The contract answers `resume` when the same operator returns, and the
        page shows a different sentence for each way in. A StrEnum keeps the
        page text and the stored text equal.
    """

    ACQUIRED = "acquired"  # The site was free and the atomic write won
    RESUMED = "resume"  # The same operator and the same browser came back
    TAKEN_OVER = "takeover"  # A new operator typed CONFIRM after the cooldown


class ReleaseOutcome(StrEnum):
    """What one compare-and-delete did to the site lock.

    Why:
        contracts/site-lock.md line 95 answers `lock_lost` for every release
        that deletes nothing, and two very different events share that answer.
        A lock that expired left the site free, and the run merely ended late.
        A lock that another operator holds means a takeover moved the site
        while the run wrote firmware. An operator reading the trail must tell
        the two apart, so the release names each one.
    """

    RELEASED = "released"  # The token matched, and the key is gone
    ALREADY_FREE = "already_free"  # The key had expired before the release ran
    HELD_BY_ANOTHER = "held_by_another"  # A takeover moved the site to a new token


def build_key(org_id: str, site_id: str) -> str:
    """Return the Redis key of one site lock.

    Args:
        org_id: The organization identifier.
        site_id: The site identifier.

    Returns:
        The key that contracts/site-lock.md line 21 fixes.
    """
    return KEY_TEMPLATE.format(org_id=org_id, site_id=site_id)


def _utc_now_text() -> str:
    """Return the present moment as ISO 8601 text in UTC.

    Why:
        Every stored time of this feature uses one clock and one format, so a
        record written by one worker compares with a record written by another.

    Returns:
        The timestamp text.
    """
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True, repr=False)
class TakeoverAudit:
    """The record of one takeover.

    Why:
        contracts/site-lock.md line 108 asks the portal to write an audit
        record for every takeover, holding the old address, the new address,
        and the time. This module builds the record, stores it, and hands it to
        the caller in the grant. The record holds the two plain addresses,
        because an audit trail names people. No log line ever repeats them.
    """

    previous_actor_email: str  # The operator who went quiet
    actor_email: str  # The operator who typed CONFIRM
    occurred_at: str  # ISO 8601 in UTC

    @staticmethod
    def build(previous_actor_email: str, actor_email: str) -> TakeoverAudit:
        """Build one audit record, timed at the present moment.

        Args:
            previous_actor_email: The operator who went quiet.
            actor_email: The operator who typed CONFIRM.

        Returns:
            The audit record.
        """
        return TakeoverAudit(
            previous_actor_email=previous_actor_email,
            actor_email=actor_email,
            occurred_at=_utc_now_text(),
        )

    def to_record(self) -> dict[str, str]:
        """Return the audit in the shape a store holds.

        Returns:
            A dictionary with the two addresses and the time.
        """
        return {
            "previous_actor_email": self.previous_actor_email,  # The operator who went quiet
            "actor_email": self.actor_email,  # The operator who took the site
            "occurred_at": self.occurred_at,  # When the takeover happened
        }

    def __repr__(self) -> str:  # Replaces the dataclass form, which would print two addresses
        """Return a text form that holds no work email address.

        Why:
            The audit holds two addresses on purpose, because the store keeps
            them. A traceback needs neither, so the text form shows the two
            digests instead and the pair still joins in an audit.

        Returns:
            The class name and the digest of each address.
        """
        previous = email_digest(self.previous_actor_email)  # The only form a log record may hold
        current = email_digest(self.actor_email)  # The same rule for the operator who took the site
        return f"TakeoverAudit(previous={previous!r}, actor={current!r})"  # No address in a traceback


# WHAT: the append-only file that holds every takeover.
# WHY: the three stored collections that data-model.md lines 13 to 15 fix hold
#      captures, runs, and the edge between them. Each write of that store
#      demands the key and the fields of one of those three kinds, so none of
#      them accepts a three-field audit row. A local append-only file keeps the
#      trail without a change to the stored data model, and it lets this module
#      keep the one-way import direction the header above describes.
AUDIT_DIRECTORY: Final[str] = "data"  # The directory every local artifact of this tool uses
AUDIT_FILE_NAME: Final[str] = "upgrade_takeover_audit.jsonl"  # One JSON object for each takeover


def _audit_path() -> Path:
    """Return the file that holds the takeover trail.

    Why:
        The function reads the two constants at call time, so a test points the
        trail at its own directory without a reload of this module.

    Returns:
        The path of the append-only audit file.
    """
    return Path(AUDIT_DIRECTORY) / AUDIT_FILE_NAME


def _append_audit_line(document: dict[str, str]) -> None:
    """Add one audit record to the end of the trail.

    Why:
        The trail appends, because a second takeover of one site must not
        replace the record of the first.

    Args:
        document: The fields the audit record holds.
    """
    path = _audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)  # The directory is absent on a fresh checkout
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(document, sort_keys=True) + "\n")  # One record on each line


def _write_takeover_audit(org_id: str, site_id: str, audit: TakeoverAudit) -> None:
    """Store the record of one takeover, and never raise.

    Why:
        The lock store already moved the site when this function runs, so a
        failure here must not cancel the takeover. The operator holds the site,
        and a lost audit line is the smaller fault.

    Args:
        org_id: The organization of the site.
        site_id: The site the operator took.
        audit: The record of the takeover.
    """
    document = audit.to_record()  # The two addresses and the time
    document["org_id"] = org_id  # Without this pair, no reader can place the row
    document["site_id"] = site_id
    try:
        _append_audit_line(document)
    except Exception as fault:  # A sink fault must never cancel a takeover the lock store already granted.
        _LOGGER.warning(
            "lock: the portal could not store the takeover audit of site %s (%s)",
            site_id,
            type(fault).__name__,  # The message may name a path or a connection string
        )


@dataclass(frozen=True, slots=True, repr=False)
class LockRecord:
    """The value that one lock key holds.

    Why:
        contracts/site-lock.md lines 25 to 34 fix six JSON fields. Two of them
        are the address and the browser identifier, which ``SessionOwner``
        already pairs and already checks. The record therefore holds the owner
        and not two loose strings, so no second identity notion appears.
    """

    owner: SessionOwner  # The address and the browser identifier, checked on construction
    lock_token: str  # A fresh random value for each acquisition. Never a log line
    run_id: str  # The run this lock protects
    acquired_at: str  # ISO 8601 in UTC, unchanged by a heartbeat
    refreshed_at: str  # ISO 8601 in UTC, moved forward by every heartbeat

    def to_record(self) -> dict[str, str]:
        """Return the six fields that contracts/site-lock.md fixes.

        Returns:
            A dictionary with the flat shape the contract shows.
        """
        return {
            "actor_email": self.owner.actor_email,  # The site list shows this to the next operator
            "browser_id": self.owner.browser_id,  # Separates one computer from another
            "lock_token": self.lock_token,  # Proves which acquisition holds the lock
            "run_id": self.run_id,  # The run this lock protects
            "acquired_at": self.acquired_at,  # When the operator first took the site
            "refreshed_at": self.refreshed_at,  # When the last heartbeat arrived
        }

    def to_json(self) -> str:
        """Return the record as the JSON text that Redis stores.

        Returns:
            Compact JSON with sorted keys, so two equal records compare equal.
        """
        return json.dumps(self.to_record(), sort_keys=True, separators=(",", ":"))

    @staticmethod
    def from_json(text: str) -> LockRecord | None:
        """Build a record from stored JSON, or report that the value is unusable.

        Why:
            A read must never raise. A value written by an older release, or a
            value damaged by hand, would otherwise hide a whole site list.

        Args:
            text: The JSON text the store holds.

        Returns:
            The record, or None when the text is not a usable lock value.
        """
        try:
            stored = json.loads(text)
        except (TypeError, ValueError):  # Damaged text must not raise out of a read
            return None
        if not isinstance(stored, dict):  # A list or a number is not a lock value
            return None
        return LockRecord._from_mapping(stored)

    @staticmethod
    def _from_mapping(stored: dict[str, Any]) -> LockRecord | None:
        """Build a record from a decoded mapping.

        Args:
            stored: The decoded JSON object.

        Returns:
            The record, or None when the owner pair fails its check.
        """
        try:
            owner = SessionOwner(
                actor_email=str(stored.get("actor_email", "")),  # Raises on an empty or malformed address
                browser_id=str(stored.get("browser_id", "")),  # Raises on a forged cookie shape
            )
        except ValueError:  # A damaged owner means the value cannot grant anything
            return None
        return LockRecord(
            owner=owner,
            lock_token=str(stored.get("lock_token", "")),  # An empty token matches no caller
            run_id=str(stored.get("run_id", "")),
            acquired_at=str(stored.get("acquired_at", "")),
            refreshed_at=str(stored.get("refreshed_at", "")),
        )

    def held_by(self, owner: SessionOwner) -> bool:
        """Report whether one operator and one browser already hold this lock.

        Why:
            contracts/site-lock.md line 41 says the pair decides whether a
            request may resume a run without typing anything. One person may
            therefore hold several sites in several tabs of one browser.

        Args:
            owner: The operator and browser pair of the asking request.

        Returns:
            True when both halves match.
        """
        return self.owner == owner  # A frozen dataclass compares both halves

    def age_seconds(self, now: datetime | None = None) -> float:
        """Return how long the holder has been quiet.

        Why:
            A damaged time counts as quiet. The other answer would hold a site
            until the key expires, and a takeover still needs the typed word,
            so counting a damaged time as quiet opens no door on its own.

        Args:
            now: The moment to measure from. The method reads the clock when
                the caller passes nothing.

        Returns:
            The seconds since the last heartbeat.
        """
        moment = now if now is not None else datetime.now(UTC)
        try:
            refreshed = datetime.fromisoformat(self.refreshed_at)
        except ValueError:  # An unreadable time counts as a full cooldown
            return float(COOLDOWN_SECONDS)
        if refreshed.tzinfo is None:  # A stored time without a zone counts as UTC
            refreshed = refreshed.replace(tzinfo=UTC)
        return (moment - refreshed).total_seconds()

    def is_quiet(self, now: datetime | None = None) -> bool:
        """Report whether the holder passed the full cooldown without a heartbeat.

        Args:
            now: The moment to measure from.

        Returns:
            True when the age reaches or passes the cooldown.
        """
        return self.age_seconds(now) >= COOLDOWN_SECONDS  # The contract says at or over

    def renewed(self) -> LockRecord:
        """Return the same record with a fresh heartbeat time.

        Why:
            A heartbeat moves `refreshed_at` and leaves `acquired_at` alone, so
            the page can still show when the operator first took the site.

        Returns:
            A new record. The value is frozen, so nothing changes in place.
        """
        return replace(self, refreshed_at=_utc_now_text())

    def __repr__(self) -> str:  # Replaces the dataclass form, which would print the token and the address
        """Return a text form that holds no token and no work email address.

        Why:
            contracts/site-lock.md line 37 says the token never reaches a log
            line. This form is the guard that holds even when a later author
            logs a whole record, so no reviewer has to catch that line.

        Returns:
            The class name, the email digest, and the run identifier.
        """
        return f"LockRecord(email_digest={self.owner.email_digest!r}, run_id={self.run_id!r})"  # No token


@dataclass(frozen=True, slots=True)
class LockRequest:
    """One operator asking to drive one site.

    Why:
        Grouping the five inputs keeps ``acquire_site_lock`` at two parameters
        and lets a route build the request once and pass it on.
    """

    org_id: str  # The organization identifier, part of the key
    site_id: str  # The site identifier, part of the key
    owner: SessionOwner  # The operator and browser pair that would hold the lock
    run_id: str  # The run the operator wants to start
    confirmation_text: str = ""  # Empty until the operator answers a prompt

    @property
    def key(self) -> str:
        """Return the Redis key this request works on.

        Returns:
            The key that contracts/site-lock.md line 21 fixes.
        """
        return build_key(self.org_id, self.site_id)


@dataclass(frozen=True, slots=True, repr=False)
class LockGrant:
    """The answer to an acquisition that succeeded.

    Why:
        The route needs the token for the heartbeat, the state for the page
        text, and the remaining life for the countdown. A takeover also carries
        the audit record, which the run store writes.
    """

    record: LockRecord  # The value the store now holds
    state: LockState  # How the caller came to hold the lock
    expires_in: int = LOCK_TTL_SECONDS  # Seconds left before the lock dies without a heartbeat
    audit: TakeoverAudit | None = None  # Set for a takeover only

    def __repr__(self) -> str:  # Replaces the dataclass form, which would print the record token
        """Return a text form that holds no token and no work email address.

        Why:
            A grant carries the record, so the generated form would print the
            token of that record. The state and the remaining life answer every
            question a log record asks about a grant.

        Returns:
            The class name, the state, and the seconds the lock has left.
        """
        return f"LockGrant(state={self.state.value!r}, expires_in={self.expires_in!r})"  # No token


def _open_client(settings: RedisSettings) -> Any:
    """Open one verified connection to the lock store.

    Why:
        A lazy handle hides a dead server until the first lock write. A
        verified handle fails here instead, so an acquisition refuses at once
        and a read-only page still renders.

        The client retries nothing. The contract puts the retry at the
        heartbeat, which owns a 60 second window. A retry inside the client
        would multiply every wait and would stall the page that reads the lock
        state.

    Args:
        settings: The host, the port, and the name of the password variable.

    Returns:
        The client, or None when the server does not answer.
    """
    try:
        import redis  # Imported here, so a missing package cannot break an import of this module
        from redis.backoff import NoBackoff
        from redis.retry import Retry

        client = redis.Redis(
            host=settings.host,
            port=settings.port,
            password=os.environ.get(settings.password_variable) or None,  # None makes the client skip AUTH
            decode_responses=True,  # The stored value is JSON text, not bytes
            socket_connect_timeout=CONNECT_TIMEOUT_SECONDS,
            socket_timeout=COMMAND_TIMEOUT_SECONDS,
            retry=Retry(NoBackoff(), 0),  # One attempt. The caller decides what a failure means
        )
        client.ping()  # Prove the server answers before any caller trusts the handle
        return client
    except Exception as error:  # A read-only page must render without the lock store.
        _LOGGER.warning("lock: the lock store at %s did not answer (%s)", settings.host, type(error).__name__)
        return None


def connect_lock_store(settings: RedisSettings | None = None) -> Any:
    """Return a client for the lock store, or None when it is out of reach.

    Why:
        A failed open costs a full connection wait. Repeating that wait for
        each request would hide every page behind a dead store, so the module
        remembers the failure for `RETRY_AFTER_SECONDS` and answers None at
        once inside that window. The portal locks again as soon as Redis comes
        back, because the window is short.

    Args:
        settings: Settings to use. The function reads the environment when the
            caller passes nothing, and it caches that shared client only.

    Returns:
        The client, or None.
    """
    global _REDIS_HANDLE, _LAST_FAILURE_AT
    if settings is not None:  # A caller with its own settings gets its own client
        return _open_client(settings)
    if _REDIS_HANDLE is not None:  # The shared client is already open
        return _REDIS_HANDLE
    if _LAST_FAILURE_AT is not None and monotonic() - _LAST_FAILURE_AT < RETRY_AFTER_SECONDS:
        return None  # A recent attempt failed. Answer at once instead of waiting again
    _REDIS_HANDLE = _open_client(load_redis_settings())
    _LAST_FAILURE_AT = None if _REDIS_HANDLE is not None else monotonic()
    return _REDIS_HANDLE


def reset_connection() -> None:
    """Drop the cached lock store client and the failure window.

    Why:
        A test installs its own client, and a long-lived worker needs a fresh
        connection after a Redis restart. Clearing the window as well lets an
        operator retry a repaired store without a wait.
    """
    global _REDIS_HANDLE, _LAST_FAILURE_AT
    _REDIS_HANDLE = None
    _LAST_FAILURE_AT = None


def _require_client(client: Any) -> Any:
    """Return a client for a write, or refuse the write.

    Why:
        Every write of this module fails closed. An in-memory fallback would
        let two workers each believe they hold the site.

    Args:
        client: The client the caller injects, or None.

    Returns:
        A usable client.

    Raises:
        LockStoreUnreachableError: When no client is available.
    """
    handle = client if client is not None else connect_lock_store()
    if handle is None:  # The contract forbids any fallback here
        raise LockStoreUnreachableError(LOCK_STORE_DOWN_MESSAGE)
    return handle


def _run_command(action: str, command: Callable[[], Any]) -> Any:
    """Run one store command and turn a store failure into a refusal.

    Args:
        action: The command name for the log record.
        command: The call to make.

    Returns:
        Whatever the store answered.

    Raises:
        LockStoreUnreachableError: When the store raised.
    """
    try:
        return command()
    except Exception as error:  # The client raises several classes, and each one refuses the write.
        _LOGGER.warning("lock: the lock store refused the %s command (%s)", action, type(error).__name__)
        raise LockStoreUnreachableError(LOCK_STORE_DOWN_MESSAGE) from error


def _read_record(handle: Any, key: str) -> LockRecord | None:
    """Return the record one key holds, without ever raising.

    Why:
        Every read path of this module fails open, so a dead store answers
        with no holder instead of hiding a page.

    Args:
        handle: The lock store client.
        key: The lock key.

    Returns:
        The record, or None when the key is free, damaged, or out of reach.
    """
    try:
        value = handle.get(key)
    except Exception as error:  # A read-only page must render without the lock store.
        _LOGGER.warning("lock: the lock store did not answer a read (%s)", type(error).__name__)
        return None
    if value is None:  # No lock exists on this site
        return None
    return LockRecord.from_json(str(value))


def _new_record(request: LockRequest) -> LockRecord:
    """Build the record one acquisition would store.

    Args:
        request: The operator, the site, and the run.

    Returns:
        A record with a fresh token and one time in both time fields.
    """
    now = _utc_now_text()  # One clock read, so both fields match on a new lock
    return LockRecord(
        owner=request.owner,
        lock_token=secrets.token_urlsafe(LOCK_TOKEN_BYTES),  # Fresh for each acquisition
        run_id=request.run_id,
        acquired_at=now,
        refreshed_at=now,
    )


def _write_new_lock(handle: Any, key: str, record: LockRecord) -> bool:
    """Try the one atomic command that takes a free lock.

    Why:
        contracts/site-lock.md line 61 forbids a read followed by a write. The
        `NX` flag makes the store decide the race, so exactly one operator wins.

    Args:
        handle: The lock store client.
        key: The lock key.
        record: The value to store.

    Returns:
        True when this caller took the lock.

    Raises:
        LockStoreUnreachableError: When the store raised.
    """
    written = _run_command("acquire", lambda: handle.set(key, record.to_json(), nx=True, ex=LOCK_TTL_SECONDS))
    return bool(written)  # The client answers None when the key already exists


def _replace_holder(request: LockRequest, held: LockRecord, handle: Any, state: LockState) -> LockGrant:
    """Write a fresh record over a quiet one.

    Why:
        Two operators can type the word at the same moment. The script writes
        only while the quiet record the caller read is still the stored one, so
        the second operator loses instead of overwriting the first.

    Args:
        request: The operator, the site, and the run.
        held: The quiet record this caller read.
        handle: The lock store client.
        state: How the caller came to hold the lock.

    Returns:
        The grant for the new holder.

    Raises:
        SiteLockedError: When a third party changed the lock first.
        LockStoreUnreachableError: When the store raised.
    """
    fresh = _new_record(request)
    won = _run_command(
        "takeover",
        lambda: handle.eval(_TAKEOVER_SCRIPT, 1, request.key, held.lock_token, fresh.to_json(), LOCK_TTL_SECONDS),
    )
    if int(won) != _SCRIPT_HELD:  # Another request took the site between the read and the write
        raise SiteLockedError(SITE_BUSY_MESSAGE)
    return LockGrant(record=fresh, state=state)


def _grant_to_same_owner(request: LockRequest, held: LockRecord, handle: Any) -> LockGrant:
    """Answer the operator and browser that already hold the site.

    Why:
        contracts/site-lock.md line 57 returns the stored token with the state
        `resume` and asks for no typed word. A session that passed the cooldown
        needs the word `continue`, because the portal would erase decisions
        that the earlier session left in flight.

    Args:
        request: The operator, the site, and the run.
        held: The record the store holds.
        handle: The lock store client.

    Returns:
        The grant, with the stored token for a live session.

    Raises:
        ConfirmationRequiredError: When the earlier session went quiet.
    """
    if not held.is_quiet():  # The same operator returns to a live session
        _LOGGER.info("lock: operator %s resumes site %s", request.owner.email_digest, request.site_id)
        return LockGrant(record=held, state=LockState.RESUMED)
    if request.confirmation_text != RESUME_CONFIRMATION_TEXT:  # Exact text and exact letter case
        raise ConfirmationRequiredError(RESUME_MESSAGE, RESUME_CONFIRMATION_TEXT)
    _LOGGER.info("lock: operator %s takes back a quiet session on site %s", request.owner.email_digest, request.site_id)
    return _replace_holder(request, held, handle, LockState.RESUMED)


def _grant_to_new_owner(request: LockRequest, held: LockRecord, handle: Any) -> LockGrant:
    """Answer an operator who is not the holder.

    Why:
        contracts/site-lock.md lines 58 and 59 refuse an active holder outright
        and ask for the word `CONFIRM` once the holder passed the cooldown.

    Args:
        request: The operator, the site, and the run.
        held: The record the store holds.
        handle: The lock store client.

    Returns:
        The grant, carrying the audit record of the takeover.

    Raises:
        SiteLockedError: When the holder is still active.
        ConfirmationRequiredError: When the operator typed the wrong word.
    """
    if not held.is_quiet():  # Another operator is driving this site right now
        raise SiteLockedError(SITE_LOCKED_MESSAGE)
    if request.confirmation_text != TAKEOVER_CONFIRMATION_TEXT:  # Exact text and exact letter case
        raise ConfirmationRequiredError(TAKEOVER_MESSAGE, TAKEOVER_CONFIRMATION_TEXT)
    grant = _replace_holder(request, held, handle, LockState.TAKEN_OVER)
    audit = TakeoverAudit.build(held.owner.actor_email, request.owner.actor_email)
    _write_takeover_audit(request.org_id, request.site_id, audit)  # Never raises, so the takeover stands
    _LOGGER.info(
        "lock: operator %s took site %s from operator %s",
        request.owner.email_digest,  # A log record holds the digest and never the address
        request.site_id,
        held.owner.email_digest,
    )
    return replace(grant, audit=audit)


def acquire_site_lock(request: LockRequest, client: Any = None) -> LockGrant:
    """Take the lock on one site for one operator.

    Why:
        This call is the only guard between two operators and one site. It
        fails closed, because a portal that starts an upgrade without the lock
        is worse than a portal that refuses to start one.

    Args:
        request: The operator, the site, the run, and any typed word.
        client: A lock store client for a test. The function opens the shared
            client when the caller passes nothing.

    Returns:
        The grant, holding the token, the state, and any audit record.

    Raises:
        SiteLockedError: When another operator is active on the site.
        ConfirmationRequiredError: When a quiet holder needs a typed word.
        LockStoreUnreachableError: When the lock store does not answer.
    """
    handle = _require_client(client)
    for _ in range(ACQUIRE_ATTEMPTS):
        fresh = _new_record(request)
        if _write_new_lock(handle, request.key, fresh):  # The store decided the race
            _LOGGER.info("lock: operator %s holds site %s", request.owner.email_digest, request.site_id)
            return LockGrant(record=fresh, state=LockState.ACQUIRED)
        held = _read_record(handle, request.key)
        if held is not None:  # A holder exists, so answer the operator about that holder
            return _resolve_conflict(request, held, handle)
    raise SiteLockedError(SITE_BUSY_MESSAGE)  # The lock expired twice between the write and the read


def _resolve_conflict(request: LockRequest, held: LockRecord, handle: Any) -> LockGrant:
    """Answer an acquisition that lost the atomic write.

    Args:
        request: The operator, the site, and the run.
        held: The record the store holds.
        handle: The lock store client.

    Returns:
        The grant when the request may hold the site.

    Raises:
        SiteLockedError: When another operator is active on the site.
        ConfirmationRequiredError: When a quiet holder needs a typed word.
    """
    if held.held_by(request.owner):  # Same address and same browser
        return _grant_to_same_owner(request, held, handle)
    return _grant_to_new_owner(request, held, handle)


def refresh_site_lock(key: str, record: LockRecord, client: Any = None) -> int:
    """Extend the life of a lock the caller still holds.

    Why:
        The browser and the run driver thread both beat every 60 seconds, so a
        closed browser does not drop a live upgrade. The compare and the extend
        run as one step, so a beat cannot extend a lock that changed hands.

    Args:
        key: The lock key, from `build_key`.
        record: The record this caller holds, carrying the token to compare.
        client: A lock store client for a test.

    Returns:
        The seconds the lock now has left.

    Raises:
        LockLostError: When the store holds a different token or no lock.
        LockStoreUnreachableError: When the lock store does not answer.
    """
    handle = _require_client(client)
    renewed = record.renewed()  # A beat moves refreshed_at and leaves acquired_at alone
    held = _run_command(
        "refresh",
        lambda: handle.eval(_REFRESH_SCRIPT, 1, key, record.lock_token, renewed.to_json(), LOCK_TTL_SECONDS),
    )
    if int(held) != _SCRIPT_HELD:  # The lock expired, or a takeover moved it
        raise LockLostError(LOCK_LOST_MESSAGE)
    return LOCK_TTL_SECONDS


def release_site_lock(key: str, record: LockRecord, client: Any = None) -> ReleaseOutcome:
    """Give up a lock the caller still holds.

    Why:
        contracts/site-lock.md line 97 releases the lock when a run reaches
        `complete`, `stopped`, or `failed`. A closed browser releases nothing,
        because the run continues. The compare and the delete run as one step,
        so a release cannot drop the lock of an operator who took the site
        after this caller stopped holding it.

    Args:
        key: The lock key, from `build_key`.
        record: The record this caller holds, carrying the token to compare.
        client: A lock store client for a test.

    Returns:
        ReleaseOutcome.RELEASED, the one answer that deleted a lock.

    Raises:
        LockLostError: When the store holds a different token or no lock. The
            `outcome` of the error tells the two apart.
        LockStoreUnreachableError: When the lock store does not answer.
    """
    handle = _require_client(client)
    freed = _run_command("release", lambda: handle.eval(_RELEASE_SCRIPT, 1, key, record.lock_token))
    if int(freed) != _SCRIPT_HELD:  # The lock expired, or a takeover moved it
        raise _release_loss(int(freed), record.run_id)
    _LOGGER.info("lock: the portal released the lock that run %s held", record.run_id)
    return ReleaseOutcome.RELEASED


def _release_loss(answer: int, run_id: str) -> LockLostError:
    """Return the refusal that names how one release lost the lock.

    Why:
        The route answers `lock_lost` for both losses, so the difference lives
        on the error. An expired lock is routine, because the run outlived the
        300-second life of the lock and left the site free. A moved lock means
        another operator now drives the site, which deserves a louder line.

    Args:
        answer: The value the release script returned.
        run_id: The run that asked for the release.

    Returns:
        The error the caller raises.
    """
    if answer == _SCRIPT_ABSENT:
        _LOGGER.info("lock: the lock of run %s had already expired, so the release deleted nothing", run_id)
        return LockLostError(LOCK_LOST_MESSAGE, ReleaseOutcome.ALREADY_FREE)
    _LOGGER.warning("lock: the lock of run %s now belongs to another operator, so the release stopped", run_id)
    return LockLostError(LOCK_LOST_MESSAGE, ReleaseOutcome.HELD_BY_ANOTHER)


def read_lock(org_id: str, site_id: str, client: Any = None) -> LockRecord | None:
    """Return the lock one site holds, or None.

    Why:
        Reading needs no lock and no typed word. The call never raises, so a
        dead lock store cannot hide a page.

    Args:
        org_id: The organization identifier.
        site_id: The site identifier.
        client: A lock store client for a test.

    Returns:
        The record, or None when the site is free or the store is out of reach.
    """
    handle = client if client is not None else connect_lock_store()
    if handle is None:  # A read fails open, so the page still renders
        return None
    return _read_record(handle, build_key(org_id, site_id))


def read_site_locks(org_id: str, site_ids: list[str], client: Any = None) -> dict[str, str | None]:
    """Return the holder of each named site.

    Why:
        This is the reader that ``app/routes/select.py`` loads through the
        ``SITE_LOCK_READER`` seam, and it calls with two positional arguments.
        The route puts each value straight into the `locked_by` field of a row,
        where None means no lock exists.

        The row shape carries no third value for an unknown state. An
        unreachable store therefore answers with an empty index, and every site
        shows no holder. The contract asks the page to mark the state unknown
        at line 118, so the page must label the state from the store health and
        not from this index.

    Args:
        org_id: The organization identifier.
        site_ids: The sites the page lists.
        client: A lock store client for a test.

    Returns:
        The work email address of each holder, or None for a free site. The
        index is empty when the lock store is out of reach.
    """
    handle = client if client is not None else connect_lock_store()
    if handle is None:  # A read fails open, and the site list still renders
        _LOGGER.warning("lock: the lock store is out of reach, so no site shows a holder")
        return {}
    return {site_id: _holder_email(handle, build_key(org_id, site_id)) for site_id in site_ids}


def _holder_email(handle: Any, key: str) -> str | None:
    """Return the address that holds one lock.

    Args:
        handle: The lock store client.
        key: The lock key.

    Returns:
        The work email address, or None when the site is free.
    """
    record = _read_record(handle, key)
    return record.owner.actor_email if record is not None else None
