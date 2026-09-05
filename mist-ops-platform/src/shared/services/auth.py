"""Auth service for Mist token validation and the privilege cache (T031).

The service validates a Mist API token against the ``/api/v1/self`` endpoint.
The lookup blocks on a network round trip, so every caller must run
``validate_token`` in a worker thread. The auth middleware does that with
``anyio.to_thread.run_sync``.

The Redis privilege cache holds a result for 5 minutes. The cache key derives
from a SHA-256 digest of the token, so the key stays stable across every worker
and across a restart (issue #1858). The cache is active only when the caller
supplies a Redis client. The auth middleware caches on the session record
instead, so a cookie session needs no Redis client here.

``_fetch_self`` raises ``MistApiUnavailableError`` when the transport fails. It
returns an empty ``MistPrivileges`` when Mist answers and rejects the token. The
caller therefore reports 503 for a transport fault and 401 for a bad token.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Any

import mistapi

from src.shared.mist.endpoints import MistEndpointService
from src.shared.mist.session import MistSessionFactory, get_session_factory

logger = logging.getLogger(__name__)

PRIVILEGE_CACHE_TTL = 300  # A verification result stays valid for 5 minutes.


class MistApiUnavailableError(RuntimeError):
    """Raised when the Mist API does not answer the privilege lookup."""


@dataclass(slots=True)
class MistPrivileges:
    """Parsed Mist /api/v1/self privileges."""

    email: str = ""
    name: str = ""
    is_msp: bool = False
    org_ids: list[str] = field(default_factory=list)
    site_ids: list[str] = field(default_factory=list)
    org_names: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    def has_org_access(self, org_id: str) -> bool:
        """Return True when the operator may act on *org_id*."""
        if self.is_msp:  # An MSP operator holds every org below the MSP account.
            return True
        return org_id in self.org_ids  # A plain operator holds only the listed orgs.


def privilege_cache_key(token: str) -> str:
    """Return the Redis key that caches the privileges for *token*."""
    # WHY: hash() is randomized per process, so its key never matched across workers.
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"mist_priv:{digest}"  # The digest hides the token and stays stable across a restart.


class AuthService:
    """Validate Mist tokens and cache privilege data."""

    def __init__(
        self,
        session_factory: MistSessionFactory | None = None,
        redis_client: Any = None,
    ) -> None:
        # WHY: the factory opens Vault and Redis connections. Build it only when a caller needs it.
        self._factory = session_factory
        self._redis = redis_client  # A None client turns the Redis privilege cache off.

    @property
    def session_factory(self) -> MistSessionFactory:
        """Return the shared session factory, and build it on first use."""
        if self._factory is None:  # The singleton builder caches, so this cost happens once.
            self._factory = get_session_factory()
        return self._factory

    def validate_token(self, token: str) -> MistPrivileges:
        """Validate a Mist API token and return privileges.

        Warning: this call blocks on a network round trip. Run it in a worker
        thread when an event loop is running.
        """
        cached = self._read_cache(token)  # Read the cache first, to save a Mist API call.
        if cached:  # A cache hit needs no upstream call, so return it at once.
            logger.debug("The privilege cache answered the token validation.")
            return cached

        logger.info("Mist privilege lookup starts.")  # Announce the upstream call before the work.
        privileges = self._fetch_self(token)  # Ask Mist who owns this token.
        self._write_cache(token, privileges)  # Store the result for the next 5 minutes.
        logger.debug("Mist privilege lookup done for operator %s.", privileges.email or "unknown")
        return privileges

    def _fetch_self(self, token: str) -> MistPrivileges:
        """Call GET /api/v1/self to retrieve privileges."""
        try:
            session = mistapi.APISession(
                host="api.mist.com",
                apitoken=token,
            )
            mist_service = MistEndpointService(session)  # Wraps the SDK call in the registry.
            result = mist_service.list_all_entities(
                "self_identity",
                {},
            )
        except Exception as error:  # WHY: the SDK raises transport types this module cannot name.
            # WHY: a transport fault is not a bad token. The caller must answer 503, not 401.
            logger.warning("The Mist privilege lookup failed to reach the Mist API.")
            raise MistApiUnavailableError(str(error)) from error
        data = result.data[0] if result.data else {}  # An empty answer means Mist said no.
        return self._parse_privileges(data)

    @staticmethod
    def _parse_privileges(data: dict[str, Any]) -> MistPrivileges:
        """Extract structured privileges from raw /self response."""
        scopes = AuthService._collect_scopes(data.get("privileges", []))  # Read every scope row.
        first = data.get("first_name", "")  # The portal shows a display name for the operator.
        last = data.get("last_name", "")  # The last name completes that display name.
        name = f"{first} {last}".strip() or data.get("email", "")  # Fall back to the address.
        return MistPrivileges(
            email=data.get("email", ""),  # An empty address means Mist rejected the token.
            name=name,
            is_msp=scopes["is_msp"],
            org_ids=scopes["org_ids"],
            site_ids=scopes["site_ids"],
            org_names=scopes["org_names"],
            raw=data,  # Keep the raw answer, because a future check may need another field.
        )

    @staticmethod
    def _collect_scopes(privileges: list[dict[str, Any]]) -> dict[str, Any]:
        """Return the org scopes, the site scopes, and the MSP flag from *privileges*."""
        org_ids: list[str] = []
        site_ids: list[str] = []
        org_names: dict[str, str] = {}
        is_msp = False
        for priv in privileges:  # Each row grants one scope to the operator.
            is_msp = is_msp or priv.get("scope", "") == "msp"  # One MSP row grants every org.
            oid = priv.get("org_id")
            if oid:  # An org row adds the org to the scope list.
                org_ids.append(oid)
                if priv.get("name"):  # Keep the first name that Mist gives for this org.
                    org_names.setdefault(oid, priv["name"])
            if priv.get("site_id"):  # A site row narrows the operator to one site.
                site_ids.append(priv["site_id"])
        return {
            "org_ids": list(set(org_ids)),  # The set drops the duplicate rows that Mist returns.
            "site_ids": list(set(site_ids)),  # The set drops the duplicate site rows as well.
            "org_names": org_names,
            "is_msp": is_msp,
        }

    def _read_cache(self, token: str) -> MistPrivileges | None:
        """Read cached privileges from Redis."""
        if not self._redis:  # No client means the caller caches elsewhere, or not at all.
            return None
        raw = self._redis.get(privilege_cache_key(token))  # Address the entry by a stable digest.
        if not raw:  # A cache miss makes the caller ask Mist.
            return None
        return MistPrivileges(**json.loads(raw))  # Rebuild the result that _write_cache stored.

    def _write_cache(self, token: str, privs: MistPrivileges) -> None:
        """Cache privilege data in Redis with TTL."""
        if not self._redis:  # No client means the caller caches elsewhere, or not at all.
            return
        payload = {
            "email": privs.email,  # The audit log needs the operator identity.
            "name": privs.name,  # The portal shows this name in its header.
            "is_msp": privs.is_msp,  # The scope check needs the MSP flag.
            "org_ids": privs.org_ids,  # The scope check needs the org list.
            "site_ids": privs.site_ids,  # The scope check needs the site list.
            "org_names": privs.org_names,  # The portal shows an org name beside each org.
        }
        # WHY: the TTL bounds how long a revoked Mist privilege stays in effect here.
        self._redis.setex(privilege_cache_key(token), PRIVILEGE_CACHE_TTL, json.dumps(payload))
