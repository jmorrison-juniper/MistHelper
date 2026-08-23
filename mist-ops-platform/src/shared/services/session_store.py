"""Server-side session records for the operator session cookie.

The ``mist_session`` cookie holds an opaque session identifier only. This
module keeps the Mist API token on the server, under that identifier. A reader
of the cookie therefore gains a handle to a revocable session record. The
reader does not gain the Mist credential.

The store writes to Redis when Redis answers. The store falls back to a
process-local map, so local work and the test suite run without Redis.

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

logger = logging.getLogger(__name__)  # Records each session action, and never a token value.

SESSION_TTL_SECONDS = 8 * 3600  # Matches the 8 hour cookie lifetime that the login route sets.
PRIVILEGE_CACHE_TTL = 300  # A verification result stays valid for 5 minutes, per issue #1858.
SESSION_KEY_PREFIX = "ops_session"  # Separates a session record from every other Redis key.

_MEMORY_RECORDS: dict[str, str] = {}  # Holds the records when Redis is absent, for local work.


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
            _MEMORY_RECORDS[key] = payload
            return
        self._redis.setex(key, SESSION_TTL_SECONDS, payload)  # The TTL expires an idle session.

    def _read(self, key: str) -> str | None:
        """Return the stored payload for *key*, or None."""
        if self._redis is None:  # Read from the fallback map when Redis is absent.
            return _MEMORY_RECORDS.get(key)
        raw = self._redis.get(key)  # Redis answers bytes or None for a missing key.
        if isinstance(raw, bytes):  # Decode the bytes, because json.loads wants text.
            return raw.decode("utf-8")
        return raw

    def _delete_key(self, key: str) -> bool:
        """Delete *key* and report whether the key existed."""
        if self._redis is None:  # Delete from the fallback map when Redis is absent.
            return _MEMORY_RECORDS.pop(key, None) is not None
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


def build_session_store() -> SessionStore:
    """Return a store that uses Redis when Redis answers."""
    logger.info("Session store build starts.")  # Announce the connection attempt before the work.
    client = _connect_redis()  # A None client selects the process-local fallback map.
    logger.debug("Session store build done. Redis is in use: %s.", client is not None)
    return SessionStore(redis_client=client)


def _connect_redis() -> Any:
    """Return a live Redis client, or None when Redis does not answer."""
    try:
        import redis as redis_lib  # Import here, so a missing driver does not stop the import.

        from src.shared.config.settings import get_settings

        client = redis_lib.Redis.from_url(get_settings().redis_url)  # Address the shared Redis.
        client.ping()  # Prove the connection now, because a later failure would end a session.
        return client
    except Exception as error:  # WHY: the Redis driver raises types this module cannot name.
        # WHY: the fallback map keeps local work alive. A single worker still serves its sessions.
        logger.warning("Redis is not available for the session store: %s.", error)
        return None
