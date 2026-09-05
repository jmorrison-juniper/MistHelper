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

MSP scope: the Mist ``/self`` answer carries one privilege row for each grant.
An MSP row names the MSP account in its ``msp_id`` field. The middleware keeps
those identifiers, then reads the organizations that the MSP accounts own from
``Organization.msp_id``. An MSP operator therefore reaches only the
organizations of the MSP accounts that the operator administers. Every other
organization returns 403 (issue #2017).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

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
    "CallerPrivileges",
    "CurrentUser",
    "collect_msp_ids",
    "get_current_user",
    "get_session_store",
    "privilege_cache_payload",
    "require_org_access",
    "resolve_msp_org_ids",
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
    msp_ids: list[str] = field(default_factory=list)
    msp_org_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CallerPrivileges:
    """Holds the Mist privileges of one caller and the MSP accounts they hold.

    ``MistPrivileges`` carries one global ``is_msp`` flag and no MSP identifier.
    This object adds the identifiers, so the scope check can name which MSP the
    operator administers (issue #2017).
    """

    privileges: MistPrivileges
    msp_ids: list[str] = field(default_factory=list)


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
    if not privs.privileges.email and not privs.privileges.org_ids:  # Mist rejected the token.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    msp_org_ids = await _load_msp_org_ids(request, privs.msp_ids)  # Read the owned orgs.
    logger.debug(
        "Request authentication done for operator %s with %d MSP organization(s).",
        privs.privileges.email or "unknown",
        len(msp_org_ids),
    )
    return _build_current_user(identity.token, privs, msp_org_ids)  # Hand back a scoped caller.


def _build_current_user(
    token: str,
    caller: CallerPrivileges,
    msp_org_ids: list[str],
) -> CurrentUser:
    """Return the caller object that the route handlers depend on."""
    privs = caller.privileges  # Read the Mist answer once, so the mapping stays short.
    return CurrentUser(
        token=token,  # The route uses this token for its own Mist calls.
        email=privs.email,  # The audit log records the operator by email address.
        org_ids=privs.org_ids,  # The scope check compares an org against this list.
        site_ids=privs.site_ids,  # The scope check compares a site against this list.
        is_msp=privs.is_msp,  # The portal shows a different menu for an MSP operator.
        msp_ids=caller.msp_ids,  # Name the MSP accounts, so no other MSP is reachable.
        msp_org_ids=msp_org_ids,  # The scope check grants only the orgs that the MSP owns.
    )


def collect_msp_ids(privilege_rows: list[dict]) -> list[str]:
    """Return the MSP identifier of every MSP scoped row in *privilege_rows*.

    The Mist ``/self`` answer repeats a row, so the result drops a duplicate. A
    row with no ``msp_id`` names no MSP account, so the result drops that row
    as well. A dropped row grants nothing, which keeps the check closed.
    """
    found: list[str] = []  # Collect the identifiers in the order that Mist returned them.
    for row in privilege_rows:  # Each row grants one scope to the operator.
        if row.get("scope", "") != "msp":  # Only an MSP row can name an MSP account.
            continue
        msp_id = row.get("msp_id", "")  # Read the account that this row grants.
        if msp_id and msp_id not in found:  # Keep one entry for each distinct account.
            found.append(msp_id)
    return found


async def resolve_msp_org_ids(session: Any, msp_ids: list[str]) -> list[str]:
    """Return the organizations that the MSP accounts in *msp_ids* own.

    The answer comes from ``Organization.msp_id``. An organization whose
    ``msp_id`` is NULL belongs to no MSP, so it never appears here. That keeps
    the check closed for an organization with no MSP owner.
    """
    from sqlalchemy import select

    from src.shared.models.inventory import Organization

    wanted = _parse_uuids(msp_ids)  # Drop a value that the column can never match.
    if not wanted:  # A plain operator holds no MSP account, so the query has no work.
        return []
    logger.info("MSP organization lookup starts for %d MSP account(s).", len(wanted))
    statement = select(Organization.org_id).where(Organization.msp_id.in_(wanted))
    rows = (await session.execute(statement)).scalars().all()  # Read the owned org ids.
    org_ids = [str(row) for row in rows]  # The scope check compares strings, not UUIDs.
    logger.debug("MSP organization lookup done with %d organization(s).", len(org_ids))
    return org_ids


def _parse_uuids(values: list[str]) -> list[Any]:
    """Return the values in *values* that parse as a UUID."""
    from uuid import UUID  # Parse each value, because the column stores a UUID.

    parsed: list[Any] = []  # Collect only the values that the database can match.
    for value in values:  # Mist controls this data, so a bad value must not raise.
        try:
            parsed.append(UUID(str(value)))
        except (AttributeError, TypeError, ValueError):
            # WHY: a malformed identifier grants nothing. Skipping it keeps the check closed.
            logger.warning("An MSP identifier is not a UUID. The lookup skips it.")
    return parsed


async def _load_msp_org_ids(request: Request, msp_ids: list[str]) -> list[str]:
    """Return the MSP owned organizations, and fall closed on any failure.

    A plain operator holds no MSP account, so this call costs no query at all.
    """
    if not msp_ids:  # The common caller holds no MSP row, so add no database cost.
        return []
    engine = getattr(request.app.state, "engine", None)  # Reuse the application engine.
    if engine is None:  # No engine means no way to read the owner, so grant nothing.
        logger.warning("No database engine is present. The MSP caller reaches no organization.")
        return []
    try:
        return await _query_msp_org_ids(engine, msp_ids)
    except Exception as error:  # WHY: SQLAlchemy raises transport types this module cannot name.
        # WHY: a failed lookup must not widen the scope. An empty list refuses every org.
        logger.warning("The MSP organization lookup failed: %s. The caller reaches none.", error)
        return []


async def _query_msp_org_ids(engine: Any, msp_ids: list[str]) -> list[str]:
    """Open one session on *engine* and read the MSP owned organizations."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:  # The block closes the session on every path.
        return await resolve_msp_org_ids(session, msp_ids)


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


async def _resolve_privileges(request: Request, identity: CallerIdentity) -> CallerPrivileges:
    """Return the Mist privileges for *identity* without blocking the event loop."""
    record = identity.record  # A bearer client owns no record, so it always asks Mist.
    if record is not None and record.privileges_are_fresh():  # The 5 minute period still runs.
        logger.debug("The privilege cache answered. The request makes no call to the Mist cloud.")
        return _caller_from_cache(record.privileges)  # Rebuild the result the last call stored.
    privs = await _verify_with_mist(identity.token)  # Ask Mist once, inside a worker thread.
    msp_ids = collect_msp_ids(privs.raw.get("privileges", []))  # Name each MSP the caller holds.
    if identity.session_id:  # Only a cookie session owns a record that can hold the result.
        get_session_store(request).store_privileges(
            identity.session_id,
            privilege_cache_payload(privs),
        )
    return CallerPrivileges(privileges=privs, msp_ids=msp_ids)


def _caller_from_cache(payload: dict) -> CallerPrivileges:
    """Rebuild the caller privileges from a stored session payload."""
    from src.shared.services.auth import MistPrivileges

    fields = dict(payload)  # Copy first, so the pop never edits the stored record.
    msp_ids = fields.pop("msp_ids", [])  # This key is no MistPrivileges field, so remove it.
    return CallerPrivileges(privileges=MistPrivileges(**fields), msp_ids=list(msp_ids))


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
        # WHY: the cache must carry the MSP identifiers, or a cached MSP caller falls to no org.
        "msp_ids": collect_msp_ids(privs.raw.get("privileges", [])),
    }


def get_session_store(request: Request) -> SessionStore:
    """Return the shared session store, and build it once for the application."""
    store = getattr(request.app.state, "session_store", None)  # Reuse the open connection.
    if store is None:  # The first request builds the store, so no start order matters.
        store = build_session_store()
        request.app.state.session_store = store  # Cache the store on the application state.
    return store


def require_org_access(org_id: str, user: CurrentUser) -> None:
    """Raise 403 when *user* may not act on the organization *org_id*.

    A caller reaches an organization in two ways. A direct Mist grant lists the
    organization on the caller account. An MSP grant names an MSP account, and
    the platform reads the organizations that the MSP owns from
    ``Organization.msp_id``.

    The check falls closed. The ``is_msp`` flag alone grants nothing, because
    the flag never names which MSP the operator administers (issue #2017).
    """
    if org_id in user.org_ids:  # A direct Mist grant lists this organization.
        return
    if org_id in user.msp_org_ids:  # The MSP of the caller owns this organization.
        return
    logger.warning(  # Record the denial, because a denial is a security event.
        "Denied access to organization %s for operator %s. The caller holds %d org grant(s) "
        "and %d MSP organization(s).",
        org_id,
        user.email or "unknown caller",
        len(user.org_ids),
        len(user.msp_org_ids),
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient privileges for this organization",
    )
