"""Health, readiness, metrics, and notification channel endpoints (T025/T035).

Provides ``/healthz``, ``/readyz``, ``/metrics``, and CRUD for
notification channels (system-level concern per api-overview.md).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_authenticated_user, get_db_session, get_scoped_org_id
from src.api.middleware.auth import CurrentUser, require_org_access
from src.api.schemas.common import ResponseEnvelope
from src.shared.models.operations import NotificationChannel

if TYPE_CHECKING:
    from src.shared.services.auth import MistPrivileges

router = APIRouter(tags=["system"])
logger = logging.getLogger(__name__)  # Records the best-effort failures that this module allows.


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness probe — returns 200 if the process is alive."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request: Request) -> dict[str, str]:
    """Readiness probe — verifies database connectivity."""
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        # WHY: an operator cannot diagnose a probe failure without a cause.
        logger.warning("Readiness probe failed. The database engine is absent from app state.")
        return {"status": "unavailable"}
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        # WHY: log the exception so the traceback reaches the operator, not just the word.
        logger.warning(
            "Readiness probe failed. The database query raised an exception.",
            exc_info=True,
        )
        return {"status": "unavailable"}


@router.get("/metrics")
async def metrics() -> None:
    """Reject Prometheus scrapes until real metrics are exported.

    The route previously answered 200 with a fixed body. A Prometheus
    scrape then recorded a healthy target with no series, so no alert
    could fire. Answering 501 makes the gap visible to every scraper.
    """
    # WHY: warn on every call so the gap is visible in the application log.
    logger.warning(
        "The /metrics route is not implemented. Real Prometheus series are not exported yet."
        " Returning 501 so the scrape fails loudly."
    )
    # WHY: raise HTTPException so FastAPI returns 501 with a JSON detail body.
    from fastapi import HTTPException

    raise HTTPException(
        status_code=501,
        detail="Prometheus metrics export is not implemented. No series are available.",
    )


# -- Notification channel schemas ----------------------------------------


class ChannelCreate(BaseModel):
    """Request body for creating a notification channel."""

    org_id: UUID
    name: str
    channel_type: str
    endpoint: str
    alert_subscriptions: list[str] = []


class ChannelResponse(BaseModel):
    """Notification channel detail."""

    id: UUID
    org_id: UUID
    name: str
    channel_type: str
    endpoint: str
    alert_subscriptions: list[str] = []
    enabled: bool = True

    model_config = {"from_attributes": True}


# -- Notification channel CRUD ------------------------------------------


@router.get("/notifications/channels")
async def list_channels(
    org_id: UUID = Depends(get_scoped_org_id),
    db: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[ChannelResponse]]:
    """List notification channels for an org."""
    stmt = select(NotificationChannel).where(NotificationChannel.org_id == org_id)
    rows = (await db.execute(stmt)).scalars().all()
    items = [ChannelResponse.model_validate(r) for r in rows]
    return ResponseEnvelope(data=items)


@router.post("/notifications/channels", status_code=201)
async def create_channel(
    body: ChannelCreate,
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ChannelResponse:
    """Create a new notification channel.

    The channel holds an outbound endpoint, so an anonymous caller could point
    an organization's alerts at a host that the caller owns. The caller must
    hold a valid credential and must belong to the organization.
    """
    from uuid import uuid4

    logger.info("Notification channel creation starts for organization %s.", body.org_id)
    require_org_access(str(body.org_id), user)  # Raise 403 when the caller is outside the org

    channel = NotificationChannel(
        id=uuid4(),
        org_id=body.org_id,
        name=body.name,
        channel_type=body.channel_type,
        endpoint=body.endpoint,
        alert_subscriptions=body.alert_subscriptions,
    )
    db.add(channel)
    await db.flush()
    return ChannelResponse.model_validate(channel)


# ========================================================================
# Auth token / session endpoints (T114, FR-018)
# ========================================================================

auth_router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Body for POST /auth/login — accepts method + token."""

    method: str = "token"
    token: str


class OrgRefResponse(BaseModel):
    """Org reference in operator identity."""

    orgId: str
    name: str


class OperatorResponse(BaseModel):
    """Operator identity returned after login."""

    email: str
    name: str
    role: str
    orgs: list[OrgRefResponse]


class SessionResponse(BaseModel):
    """Returned after successful authentication."""

    sessionId: str
    operator: OperatorResponse
    expiresAt: str


class TokenRefreshResponse(BaseModel):
    """Returned from POST /auth/token (refresh)."""

    session_id: str
    expires_in: int


@auth_router.post("/login")
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[SessionResponse]:
    """Authenticate with a Mist API token, upsert orgs, return session."""
    from datetime import UTC, datetime, timedelta

    from fastapi import HTTPException

    logger.info("Operator login starts.")  # Announce the login before the upstream call.
    privs = await _verify_login_token(body.token)  # Ask Mist once, inside a worker thread.
    if not privs.email and not privs.org_ids:
        raise HTTPException(status_code=401, detail="Invalid API token")

    await _upsert_orgs(db, request.app.state.engine, privs)  # Record every org the operator holds.
    _cache_worker_token(privs.org_ids, body.token)  # Let the Celery worker reuse the credential.
    _dispatch_inventory_sync(privs.org_ids)  # Start the first inventory sync for each org.

    session_id = _create_session(request, body.token, privs)  # Keep the token on the server side.
    expires = datetime.now(UTC) + timedelta(hours=8)
    envelope = _build_login_envelope(session_id, privs, expires.isoformat())
    logger.debug("Operator login done for operator %s.", privs.email or "unknown")
    return _login_response(envelope, session_id)  # The cookie holds the identifier, not the token.


async def _verify_login_token(token: str) -> MistPrivileges:
    """Verify *token* with the Mist API without blocking the event loop."""
    import anyio.to_thread
    from fastapi import HTTPException

    from src.shared.services.auth import AuthService, MistApiUnavailableError

    svc = AuthService()  # The Redis privilege cache is not needed, because the record holds it.
    try:
        # WHY: validate_token blocks on a network round trip. A worker thread frees the event loop.
        return await anyio.to_thread.run_sync(svc.validate_token, token)
    except MistApiUnavailableError as error:
        # WHY: a transport fault is not a bad token. A 503 tells the operator to try again.
        logger.warning("The Mist API is unreachable during the login: %s.", error)
        raise HTTPException(
            status_code=503,
            detail="The Mist API is unreachable. Try the login again.",
        ) from error


async def _upsert_orgs(db: AsyncSession, engine: object, privs: MistPrivileges) -> None:
    """Record every org that the operator may reach, and build its partitions."""
    import uuid as uuid_mod

    from src.shared.db import ensure_org_partitions
    from src.shared.models.inventory import Organization

    logger.info("Organization upsert starts for %d orgs.", len(privs.org_ids))
    for oid in privs.org_ids:  # One row per org keeps the inventory scoped to that org.
        org_uuid = uuid_mod.UUID(oid)  # The table keys an org by its Mist UUID.
        org_name = privs.org_names.get(oid, oid)  # Use the identifier when no name exists.
        org = await db.get(Organization, org_uuid)  # Read the row, because this is an upsert.
        if org is None:  # A first login for this org inserts the row.
            db.add(Organization(org_id=org_uuid, name=org_name, api_host="api.mist.com"))
        else:  # A later login refreshes the name, because an operator can rename an org.
            org.name = org_name
        await ensure_org_partitions(engine, oid)  # A time-series table needs a partition per org.
    await db.flush()  # Write the rows now, so the session record and the orgs agree.
    logger.debug("Organization upsert done for %d orgs.", len(privs.org_ids))


def _cache_worker_token(org_ids: list[str], token: str) -> None:
    """Cache the Mist token in Redis, so a Celery worker can call the Mist API."""
    import redis as redis_lib

    from src.shared.config.settings import get_settings
    from src.shared.redis_timeouts import redis_timeout_kwargs

    try:
        logger.info("Worker token cache write starts for %d orgs.", len(org_ids))  # Announce it.
        # WHY: a client with no socket limit holds this uvicorn worker on a silent Redis host.
        client = redis_lib.Redis.from_url(
            get_settings().redis_url,
            **redis_timeout_kwargs(),
        )  # Address the shared Redis.
        for oid in org_ids:  # Each org key lets a worker find the token for that org.
            client.setex(f"mist_token:{oid}", 8 * 3600, token)
        client.close()  # Release the socket, because this route holds no long-lived client.
        logger.debug("Worker token cache write done for %d orgs.", len(org_ids))  # Confirm it.
    except (redis_lib.RedisError, OSError, ValueError) as error:  # Redis, socket, and URL faults.
        # WHY: the worker falls back to the environment token. A cache miss must not fail login.
        logger.debug("Redis token cache unavailable: %s", error)  # Make the cache miss visible.


def _dispatch_inventory_sync(org_ids: list[str]) -> None:
    """Ask the Celery worker to sync the inventory of each org now."""
    try:
        from src.worker.tasks.sync_tasks import sync_org_inventory

        for oid in org_ids:  # One task per org keeps a slow org from blocking the others.
            sync_org_inventory.delay(oid)
    except Exception as error:  # WHY: the Celery broker raises types this app cannot name.
        # WHY: beat retries the sync later, so a dispatch failure must not fail the login.
        logger.debug("Inventory sync dispatch unavailable: %s", error)  # Make the miss visible.


def _create_session(request: Request, token: str, privs: MistPrivileges) -> str:
    """Store *token* in the server-side session record and return its identifier."""
    from src.api.middleware.auth import get_session_store, privilege_cache_payload

    store = get_session_store(request)  # Reuse the store that the auth middleware also reads.
    # WHY: the login already verified the token, so the first request needs no second Mist call.
    return store.create(token, privilege_cache_payload(privs))


def _build_login_envelope(
    session_id: str,
    privs: MistPrivileges,
    expires_at: str,
) -> ResponseEnvelope[SessionResponse]:
    """Build the JSON body that the login returns to the portal."""
    role = "msp" if privs.is_msp else "org_admin"  # The portal shows a different menu per role.
    orgs = [OrgRefResponse(orgId=oid, name=privs.org_names.get(oid, oid)) for oid in privs.org_ids]
    operator = OperatorResponse(
        email=privs.email,  # The portal shows the signed-in operator.
        name=privs.name,  # The portal shows a display name beside the email address.
        role=role,  # The portal hides the MSP views from an org administrator.
        orgs=orgs,  # The portal lists every org that the operator may select.
    )
    return ResponseEnvelope(
        data=SessionResponse(
            sessionId=session_id,  # The body repeats the identifier that the cookie carries.
            operator=operator,
            expiresAt=expires_at,
        ),
    )


def _login_response(
    envelope: ResponseEnvelope[SessionResponse],
    session_id: str,
) -> JSONResponse:
    """Return the login response with the opaque session cookie attached."""
    from src.shared.config.settings import get_settings

    secure = get_settings().session_cookie_secure  # A false value serves local plain HTTP work.
    response = JSONResponse(content=envelope.model_dump(mode="json"))
    response.set_cookie(
        key="mist_session",
        value=session_id,  # WHY: an opaque identifier gives a cookie reader no Mist credential.
        httponly=True,  # Script in the page cannot read the cookie.
        secure=secure,  # The browser sends the cookie over HTTPS only, unless a setting stops it.
        samesite="lax",  # A cross-site form post cannot carry the session.
        max_age=8 * 3600,  # The cookie and the server-side record expire together.
        path="/",
    )
    logger.debug("The login cookie carries an opaque session identifier. Secure is %s.", secure)
    return response


@auth_router.post("/token")
async def refresh_token() -> ResponseEnvelope[TokenRefreshResponse]:
    """Refresh an existing session token (placeholder)."""
    import secrets

    return ResponseEnvelope(
        data=TokenRefreshResponse(
            session_id=secrets.token_urlsafe(32),
            expires_in=3600,
        ),
    )


@auth_router.delete("/session")
async def logout(request: Request) -> JSONResponse:
    """Invalidate current session and clear cookie."""
    from src.api.middleware.auth import SESSION_COOKIE_NAME, get_session_store

    logger.info("Operator logout starts.")  # Announce the logout before the delete.
    session_id = request.cookies.get(SESSION_COOKIE_NAME, "")  # Address the record to delete.
    # WHY: the record holds the Mist token. The delete is what truly ends the session.
    removed = get_session_store(request).delete(session_id)
    response = JSONResponse(content={"status": "logged_out"})
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")  # Clear the browser copy as well.
    logger.debug("Operator logout done. A server-side record existed: %s.", removed)
    return response
