"""Auth middleware for the bearer header and the session cookie (T020).

The middleware accepts an ``Authorization: Bearer`` header or a ``mist_session``
cookie. The cookie holds an opaque session identifier. The middleware reads the
Mist API token from the server-side session record, so no client ever sends the
Mist credential back to this service (issue #1859).

The middleware runs the Mist ``/api/v1/self`` lookup in a worker thread, so the
lookup never blocks the event loop. The middleware also caches the verification
result on the session record for 5 minutes, so a repeat request makes no second
call to the Mist cloud (issue #1858).

An unreachable Mist API returns 503. A token that Mist rejects returns 401.

Scope enforcement: query results are filtered to the user's MSP, org, and site
privileges (FR-025).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import anyio.to_thread
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.shared.services.session_store import (
    PRIVILEGE_CACHE_TTL,
    SessionRecord,
    SessionStore,
    build_session_store,
)

if TYPE_CHECKING:
    from src.shared.services.auth import MistPrivileges

logger = logging.getLogger(__name__)
_bearer_scheme = HTTPBearer(auto_error=False)

SESSION_COOKIE_NAME = "mist_session"  # Names the cookie that holds the opaque session identifier.

__all__ = [
    "PRIVILEGE_CACHE_TTL",
    "SESSION_COOKIE_NAME",
    "CallerIdentity",
    "CurrentUser",
    "get_current_user",
    "get_session_store",
    "privilege_cache_payload",
    "require_org_access",
]


@dataclass(slots=True)
class CurrentUser:
    """Represents the authenticated caller and their privilege scope."""

    token: str
    email: str = ""
    org_ids: list[str] = field(default_factory=list)
    site_ids: list[str] = field(default_factory=list)
    is_msp: bool = False
    privileges: dict = field(default_factory=dict)


@dataclass(slots=True)
class CallerIdentity:
    """Holds the Mist token that a request resolves to, and its session record."""

    token: str
    session_id: str = ""
    record: SessionRecord | None = None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser:
    """Extract and validate caller identity from the request."""
    logger.info("Request authentication starts for path %s.", request.url.path)
    identity = _extract_token(request, credentials)  # Read the token from the server side.
    if identity is None or not identity.token:  # No credential means the caller is anonymous.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
        )
    privs = await _resolve_privileges(request, identity)  # Read the cache, or ask Mist.
    if not privs.email and not privs.org_ids:  # Mist rejected the token, so the caller has no org.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    logger.debug("Request authentication done for operator %s.", privs.email or "unknown")
    return _build_current_user(identity.token, privs)  # Hand the route a scoped caller object.


def _build_current_user(token: str, privs: MistPrivileges) -> CurrentUser:
    """Return the caller object that the route handlers depend on."""
    return CurrentUser(
        token=token,  # The route uses this token for its own Mist calls.
        email=privs.email,  # The audit log records the operator by email address.
        org_ids=privs.org_ids,  # The scope check compares an org against this list.
        site_ids=privs.site_ids,  # The scope check compares a site against this list.
        is_msp=privs.is_msp,  # An MSP operator passes every org scope check.
    )


def _extract_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> CallerIdentity | None:
    """Return the caller identity from the bearer header or the session cookie."""
    if credentials and credentials.credentials:  # A direct API client sends its own token.
        return CallerIdentity(token=credentials.credentials)
    session_id = request.cookies.get(SESSION_COOKIE_NAME, "")  # The browser sends an opaque value.
    if not session_id:  # No cookie and no header means the caller sent no credential.
        return None
    record = get_session_store(request).resolve(session_id)  # Read the token from the server side.
    if record is None or not record.token:  # A deleted session must fail, so logout ends it.
        logger.debug("The session cookie resolves to no server-side record. The request fails.")
        return None
    return CallerIdentity(token=record.token, session_id=session_id, record=record)


async def _resolve_privileges(request: Request, identity: CallerIdentity) -> MistPrivileges:
    """Return the Mist privileges for *identity* without blocking the event loop."""
    from src.shared.services.auth import MistPrivileges

    record = identity.record  # A bearer client owns no record, so it always asks Mist.
    if record is not None and record.privileges_are_fresh():  # The 5 minute period still runs.
        logger.debug("The privilege cache answered. The request makes no call to the Mist cloud.")
        return MistPrivileges(**record.privileges)  # Rebuild the result that the last call stored.
    privs = await _verify_with_mist(identity.token)  # Ask Mist once, inside a worker thread.
    if identity.session_id:  # Only a cookie session owns a record that can hold the result.
        get_session_store(request).store_privileges(
            identity.session_id,
            privilege_cache_payload(privs),
        )
    return privs


async def _verify_with_mist(token: str) -> MistPrivileges:
    """Run the blocking Mist lookup in a worker thread."""
    from src.shared.services.auth import AuthService, MistApiUnavailableError

    logger.info("Mist token verification starts.")  # Announce the upstream call before the work.
    service = AuthService()  # The service holds no request state, so a new object costs little.
    try:
        # WHY: validate_token blocks on a network round trip. A worker thread frees the event loop.
        privs = await anyio.to_thread.run_sync(service.validate_token, token)
    except MistApiUnavailableError as error:
        # WHY: a transport fault is not a bad token. A 503 keeps the operator logged in.
        logger.warning("The Mist API is unreachable: %s.", error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The Mist API is unreachable. Try the request again.",
        ) from error
    logger.debug("Mist token verification done for operator %s.", privs.email or "unknown")
    return privs


def privilege_cache_payload(privs: MistPrivileges) -> dict:
    """Return the privilege fields that the session record stores."""
    return {
        "email": privs.email,  # The audit log needs the operator identity on the next request.
        "name": privs.name,  # The portal shows this name in its header.
        "is_msp": privs.is_msp,  # The scope check needs the MSP flag.
        "org_ids": privs.org_ids,  # The scope check needs the org list.
        "site_ids": privs.site_ids,  # The scope check needs the site list.
        "org_names": privs.org_names,  # The portal shows an org name beside each org.
    }


def get_session_store(request: Request) -> SessionStore:
    """Return the shared session store, and build it once for the application."""
    store = getattr(request.app.state, "session_store", None)  # Reuse the open connection.
    if store is None:  # The first request builds the store, so no start order matters.
        store = build_session_store()
        request.app.state.session_store = store  # Cache the store on the application state.
    return store


def require_org_access(org_id: str, user: CurrentUser) -> None:
    """Raise 403 if user lacks access to the specified org."""
    if user.is_msp:
        return
    if org_id not in user.org_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges for this organization",
        )
