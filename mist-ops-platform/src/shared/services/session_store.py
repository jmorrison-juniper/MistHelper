"""Server-side session records for the operator session cookie.

The ``mist_session`` cookie holds an opaque session identifier only. This
module keeps the Mist API token on the server, under that identifier. A reader
of the cookie therefore gains a handle to a revocable session record. The
reader does not gain the Mist credential.

The store writes to Redis when Redis answers. The store falls back to a
process-local map, so local work and the test suite run without Redis.
The fallback map expires each record after the session lifetime, so a
process that runs without Redis cannot grow without bound (issue #2051).

A deployment that runs more than one worker must hold its sessions in Redis.
A process-local map is invisible to the other workers, so the build refuses
to fall back when the worker count is greater than one (issue #2051).

The record also holds the last Mist ``/api/v1/self`` result. The auth
middleware reads that result inside the cache period, so a repeat request makes
no second call to the Mist cloud.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
import time
from dataclasses import dataclass, field
from typing import Any

from src.shared.config.settings import get_settings  # Shared access to the app settings.

logger = logging.getLogger(__name__)  # Records each session action, and never a token value.

SESSION_TTL_SECONDS = 8 * 3600  # Matches the 8 hour cookie lifetime that the login route sets.
PRIVILEGE_CACHE_TTL = 300  # A verification result stays valid for 5 minutes, per issue #1858.
SESSION_KEY_PREFIX = "ops_session"  # Separates a session record from every other Redis key.

_MEMORY_RECORDS: dict[str, str] = {}  # Holds the records when Redis is absent, for local work.
_MEMORY_CREATED_AT: dict[str, float] = {}  # Holds the write time, so the map can expire a record.


@dataclass(slots=True)
class SessionRecord:
    """Holds the server-side state of one operator session."""

    session_id: str
    token: str
    privileges: dict[str, Any] = field(default_factory=dict)
    verified_at: float = 0.0

    def privileges_are_fresh(self, now: float | None = None) -> bool:
        """Return True when the cached Mist result is still inside the cache period."""
        if not self.privileges:  # An empty result holds no identity, so it is never fresh.
            return False
        moment = time.time() if now is None else now  # A test supplies its own clock reading.
        return (moment - self.verified_at) < PRIVILEGE_CACHE_TTL  # Compare against the 5 minutes.


def session_key(session_id: str) -> str:
    """Return the storage key for *session_id*."""
    # WHY: the store holds a digest, so a Redis dump does not reveal a usable session identifier.
    digest = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
    return f"{SESSION_KEY_PREFIX}:{digest}"  # Prefix the digest, so the key space stays readable.


class SessionStore:
    """Create, read, and delete the server-side session records."""

    def __init__(self, redis_client: Any = None) -> None:
        self._redis = redis_client  # A None client selects the process-local fallback map.

    def create(self, token: str, privileges: dict[str, Any] | None = None) -> str:
        """Store *token* under a new opaque identifier and return that identifier."""
        logger.info("Session record creation starts.")  # Announce the write before the work.
        session_id = secrets.token_urlsafe(32)  # 32 random bytes resist a guess of the identifier.
        record = SessionRecord(
            session_id=session_id,
            token=token,
            privileges=privileges or {},  # An empty map forces the first request to ask Mist.
            verified_at=time.time() if privileges else 0.0,  # A fresh result starts the clock.
        )
        self._write(record)  # Persist the record, because the cookie carries the identifier only.
        logger.debug("Session record creation done. The key is %s.", session_key(session_id))
        return session_id

    def resolve(self, session_id: str) -> SessionRecord | None:
        """Return the record for *session_id*, or None when no record exists."""
        if not session_id:  # An empty cookie value cannot address a record.
            return None
        raw = self._read(session_key(session_id))  # Read the stored payload for this identifier.
        if not raw:  # A deleted or expired record makes the caller answer 401.
            logger.debug("Session record lookup found no record.")
            return None
        return self._decode(session_id, raw)  # Rebuild the record from the stored payload.

    def store_privileges(self, session_id: str, privileges: dict[str, Any]) -> None:
        """Attach a fresh Mist verification result to the record for *session_id*."""
        record = self.resolve(session_id)  # Read the record, because the token must stay the same.
        if record is None:  # A deleted record must not come back through a cache write.
            return
        record.privileges = privileges  # Keep the result, so the next request skips the Mist call.
        record.verified_at = time.time()  # Start the 5 minute cache period at this moment.
        self._write(record)  # Persist the updated record under the same identifier.
        logger.debug("Session privilege cache write done for key %s.", session_key(session_id))

    def renew(self, session_id: str) -> int | None:
        """Extend the lifetime of the record for *session_id* and return that lifetime.

        The method returns None when no record matches. A renewal must never
        create a record, because that would let an anonymous caller mint a
        session.
        """
        if not session_id:  # An empty cookie value addresses no record, so report no renewal.
            return None
        logger.info("Session record renewal starts.")  # Announce the write before the work.
        record = self.resolve(session_id)  # Read the record, so a renewal never creates one.
        if record is None:  # An unknown or expired identifier must not gain a new lifetime.
            logger.debug("Session record renewal found no record.")
            return None
        self._write(record)  # Re-write the record, so the store restarts the session lifetime.
        logger.debug("Session record renewal done. The key is %s.", session_key(session_id))
        return SESSION_TTL_SECONDS  # The caller reports this lifetime to the operator.

    def delete(self, session_id: str) -> bool:
        """Delete the record for *session_id* and report whether a record existed."""
        if not session_id:  # An empty cookie value addresses no record, so report no deletion.
            return False
        logger.info("Session record deletion starts.")  # Announce the logout before the work.
        key = session_key(session_id)  # Build the key once, because both branches need it.
        removed = self._delete_key(key)  # Remove the record, so the logout truly ends the session.
        logger.debug("Session record deletion done. A record existed: %s.", removed)
        return removed

    # -- storage helpers -------------------------------------------------

    def _write(self, record: SessionRecord) -> None:
        """Persist *record* under its key with the session lifetime."""
        key = session_key(record.session_id)  # Address the record by the digest of its identifier.
        payload = json.dumps(
            {
                "token": record.token,  # The server holds the credential, not the client.
                "privileges": record.privileges,  # The cached Mist result rides with the record.
                "verified_at": record.verified_at,  # The reader needs the age of that result.
            },
        )
        if self._redis is None:  # The fallback map keeps local work and the tests running.
            _sweep_memory_records()  # Drop expired records, so the map cannot grow without bound.
            _MEMORY_RECORDS[key] = payload  # Store the record under its digest key.
            _MEMORY_CREATED_AT[key] = time.time()  # Record the write time, so it can expire.
            return
        self._redis.setex(key, SESSION_TTL_SECONDS, payload)  # The TTL expires an idle session.

    def _read(self, key: str) -> str | None:
        """Return the stored payload for *key*, or None."""
        if self._redis is None:  # Read from the fallback map when Redis is absent.
            if _memory_record_is_expired(key):  # An expired record must act as a missing record.
                _remove_memory_record(key)  # Drop the record, so a stale session cannot resolve.
                return None
            return _MEMORY_RECORDS.get(key)
        raw = self._redis.get(key)  # Redis answers bytes or None for a missing key.
        if isinstance(raw, bytes):  # Decode the bytes, because json.loads wants text.
            return raw.decode("utf-8")
        if isinstance(raw, str):  # A text answer is the payload as stored.
            return raw
        return None  # A missing key or an unexpected type means no record.

    def _delete_key(self, key: str) -> bool:
        """Delete *key* and report whether the key existed."""
        if self._redis is None:  # Delete from the fallback map when Redis is absent.
            existed = _MEMORY_RECORDS.pop(key, None) is not None  # Report if it existed.
            _MEMORY_CREATED_AT.pop(key, None)  # Drop the write time, so the key leaves no trace.
            return existed
        return bool(self._redis.delete(key))  # Redis reports the count of the deleted keys.

    @staticmethod
    def _decode(session_id: str, raw: str) -> SessionRecord | None:
        """Rebuild a record from the stored payload *raw*."""
        try:
            data = json.loads(raw)  # Parse the payload that _write produced.
        except (TypeError, ValueError):
            # WHY: a corrupt payload must log the operator out, not crash the request.
            logger.warning("Session record payload is not valid JSON. The session ends.")
            return None
        return SessionRecord(
            session_id=session_id,  # Carry the identifier, so a cache write can find the record.
            token=data.get("token", ""),  # An absent token makes the caller answer 401.
            privileges=data.get("privileges", {}),  # An absent result forces a fresh Mist call.
            verified_at=float(data.get("verified_at", 0.0)),  # A zero age forces a fresh call.
        )


def _memory_record_is_expired(key: str) -> bool:
    """Report whether the fallback record for *key* is past its lifetime."""
    written_at = _MEMORY_CREATED_AT.get(key)  # A record without a write time cannot expire.
    if written_at is None:  # Keep a record that predates the timestamp map.
        return False
    return (time.time() - written_at) >= SESSION_TTL_SECONDS  # Compare age to the lifetime.


def _remove_memory_record(key: str) -> None:
    """Drop the fallback record and its write time for *key*."""
    _MEMORY_RECORDS.pop(key, None)  # Remove the payload, so a reader finds no record.
    _MEMORY_CREATED_AT.pop(key, None)  # Remove the write time, so the key leaves no trace.


def _sweep_memory_records() -> None:
    """Remove every expired fallback record from the process-local map."""
    expired = [key for key in _MEMORY_RECORDS if _memory_record_is_expired(key)]
    for key in expired:  # Drop each expired record, so the map cannot grow without bound.
        _remove_memory_record(key)
    if expired:  # A sweep that removed a record is worth a log line.
        logger.debug("Session store fallback sweep removed %d expired record(s).", len(expired))


def build_session_store() -> SessionStore:
    """Return a store that uses Redis when Redis answers.

    A multi-worker deployment must hold its sessions in Redis. A process-local
    map is invisible to the other workers, so the build refuses to fall back
    when more than one worker runs (issue #2051).
    """
    logger.info("Session store build starts.")  # Announce the connection attempt before the work.
    worker_count = _read_worker_count()  # The count decides whether the fallback is safe.
    client = _connect_redis()  # A None client selects the process-local fallback map.
    if client is None and worker_count > 1:  # A shared store is the only multi-worker store.
        # WHY: a per-process map loses a session on every request that lands on another worker.
        logger.error(
            "Session store build failed. Redis is required when WEB_WORKERS is %d.",
            worker_count,
        )
        raise RuntimeError(
            "Redis is required for the session store when more than one worker runs. "
            "Start Redis, or set WEB_WORKERS=1.",
        )
    if client is None:  # A single worker may keep its sessions in the process.
        logger.warning(
            "Session store fallback is active. Sessions live in this process only. "
            "A restart ends every session, and the fallback is unsafe with more than one worker.",
        )
    logger.debug("Session store build done. Redis is in use: %s.", client is not None)
    return SessionStore(redis_client=client)


def _read_worker_count() -> int:
    """Return the configured worker count, and refuse a count below one."""
    worker_count = get_settings().worker_count  # The deployment names its worker count here.
    if worker_count < 1:  # A count below one is a misconfiguration, not a valid setting.
        raise RuntimeError("WEB_WORKERS must be at least 1.")
    return worker_count


def _connect_redis() -> Any:
    """Return a live Redis client, or None when Redis does not answer."""
    try:
        import redis as redis_lib  # Import here, so a missing driver does not stop the import.

        from src.shared.redis_timeouts import redis_timeout_kwargs  # Shared socket limits.

        logger.info("Session store Redis connect starts.")  # Announce the connect attempt.
        # WHY: a client with no socket limit holds this worker forever on a silent Redis host.
        client = redis_lib.Redis.from_url(
            get_settings().redis_url,
            **redis_timeout_kwargs(),
        )  # Address the shared Redis.
        client.ping()  # Prove the connection now, because a later failure would end a session.
        logger.debug("Session store Redis connect done.")  # Confirm the live connection.
        return client
    except Exception as error:  # WHY: the Redis driver raises types this module cannot name.
        # WHY: the fallback map keeps local work alive. A single worker still serves its sessions.
        logger.warning("Redis is not available for the session store: %s.", error)
        return None
