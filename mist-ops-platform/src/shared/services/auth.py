"""Auth service — Mist session management and privilege cache (T031).

Provides helpers for validating Mist API tokens against the /api/v1/self
endpoint with Redis-backed privilege caching (R-07).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import mistapi

from src.shared.mist.endpoints import MistEndpointService
from src.shared.mist.session import MistSessionFactory, get_session_factory

logger = logging.getLogger(__name__)

PRIVILEGE_CACHE_TTL = 300  # 5 minutes


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


class AuthService:
    """Validate Mist tokens and cache privilege data."""

    def __init__(
        self,
        session_factory: MistSessionFactory | None = None,
        redis=None,  # noqa: ANN001
    ) -> None:
        self._factory = session_factory or get_session_factory()
        self._redis = redis

    def validate_token(self, token: str) -> MistPrivileges:
        """Validate a Mist API token and return privileges."""
        cached = self._read_cache(token)
        if cached:
            return cached

        privileges = self._fetch_self(token)
        self._write_cache(token, privileges)
        return privileges

    def _fetch_self(self, token: str) -> MistPrivileges:
        """Call GET /api/v1/self to retrieve privileges."""
        session = mistapi.APISession(
            host="api.mist.com",
            apitoken=token,
        )
        try:
            mist_service = MistEndpointService(session)
            result = mist_service.list_all_entities(
                "self_identity", {},
            )
            data = result.data[0] if result.data else {}
            return self._parse_privileges(data)
        except Exception:
            logger.exception("Failed to validate Mist token")
            return MistPrivileges()

    @staticmethod
    def _parse_privileges(data: dict[str, Any]) -> MistPrivileges:
        """Extract structured privileges from raw /self response."""
        privileges = data.get("privileges", [])
        org_ids: list[str] = []
        site_ids: list[str] = []
        org_names: dict[str, str] = {}
        is_msp = False
        for priv in privileges:
            scope = priv.get("scope", "")
            if scope == "msp":
                is_msp = True
            oid = priv.get("org_id")
            if oid:
                org_ids.append(oid)
                if oid not in org_names and priv.get("name"):
                    org_names[oid] = priv["name"]
            if priv.get("site_id"):
                site_ids.append(priv["site_id"])
        first = data.get("first_name", "")
        last = data.get("last_name", "")
        name = f"{first} {last}".strip() or data.get("email", "")
        return MistPrivileges(
            email=data.get("email", ""),
            name=name,
            is_msp=is_msp,
            org_ids=list(set(org_ids)),
            site_ids=list(set(site_ids)),
            org_names=org_names,
            raw=data,
        )

    def _read_cache(self, token: str) -> MistPrivileges | None:
        """Read cached privileges from Redis."""
        if not self._redis:
            return None
        import json

        key = f"mist_priv:{hash(token)}"
        raw = self._redis.get(key)
        if not raw:
            return None
        data = json.loads(raw)
        return MistPrivileges(**data)

    def _write_cache(self, token: str, privs: MistPrivileges) -> None:
        """Cache privilege data in Redis with TTL."""
        if not self._redis:
            return
        import json

        key = f"mist_priv:{hash(token)}"
        payload = {
            "email": privs.email,
            "is_msp": privs.is_msp,
            "org_ids": privs.org_ids,
            "site_ids": privs.site_ids,
        }
        self._redis.setex(key, PRIVILEGE_CACHE_TTL, json.dumps(payload))
