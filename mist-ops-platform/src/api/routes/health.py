"""Health, readiness, metrics, and notification channel endpoints (T025/T035).

Provides ``/healthz``, ``/readyz``, ``/metrics``, and CRUD for
notification channels (system-level concern per api-overview.md).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db_session
from src.api.schemas.common import ResponseEnvelope
from src.shared.models.operations import NotificationChannel

router = APIRouter(tags=["system"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness probe — returns 200 if the process is alive."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(request) -> dict[str, str]:  # noqa: ANN001
    """Readiness probe — verifies database connectivity."""
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        return {"status": "unavailable"}
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "unavailable"}


@router.get("/metrics")
async def metrics() -> dict[str, str]:
    """Placeholder for Prometheus metrics export."""
    return {"status": "metrics_placeholder"}


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
    org_id: UUID = Query(...),
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
) -> ChannelResponse:
    """Create a new notification channel."""
    from uuid import uuid4

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
    import secrets
    import uuid as uuid_mod
    from datetime import datetime, timedelta, timezone

    from fastapi import HTTPException

    from src.shared.db import ensure_org_partitions
    from src.shared.models.inventory import Organization
    from src.shared.services.auth import AuthService

    svc = AuthService(redis=None)
    privs = svc.validate_token(body.token)

    if not privs.email and not privs.org_ids:
        raise HTTPException(status_code=401, detail="Invalid API token")

    engine = request.app.state.engine
    for oid in privs.org_ids:
        org_uuid = uuid_mod.UUID(oid)
        org_name = privs.org_names.get(oid, oid)
        org = await db.get(Organization, org_uuid)
        if org is None:
            org = Organization(
                org_id=org_uuid,
                name=org_name,
                api_host="api.mist.com",
            )
            db.add(org)
        else:
            org.name = org_name
        await ensure_org_partitions(engine, oid)
    await db.flush()

    # Cache token in Redis so Celery workers can use it for API calls
    import redis as redis_lib
    from src.shared.config.settings import get_settings

    _settings = get_settings()
    try:
        _redis = redis_lib.Redis.from_url(_settings.redis_url)
        for oid in privs.org_ids:
            _redis.setex(f"mist_token:{oid}", 8 * 3600, body.token)
        _redis.close()
    except Exception:
        pass  # Redis unavailable — worker falls back to env token

    # Trigger immediate inventory sync for each org
    try:
        from src.worker.tasks.sync_tasks import sync_org_inventory

        for oid in privs.org_ids:
            sync_org_inventory.delay(oid)
    except Exception:
        pass  # Worker unavailable — beat will catch up

    session_id = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=8)
    role = "msp" if privs.is_msp else "org_admin"
    orgs = [OrgRefResponse(orgId=oid, name=privs.org_names.get(oid, oid)) for oid in privs.org_ids]
    operator = OperatorResponse(
        email=privs.email,
        name=privs.name,
        role=role,
        orgs=orgs,
    )
    envelope = ResponseEnvelope(
        data=SessionResponse(
            sessionId=session_id,
            operator=operator,
            expiresAt=expires.isoformat(),
        ),
    )
    from fastapi.responses import JSONResponse

    response = JSONResponse(content=envelope.model_dump(mode="json"))
    response.set_cookie(
        key="mist_session",
        value=body.token,
        httponly=True,
        samesite="lax",
        max_age=8 * 3600,
        path="/",
    )
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
async def logout() -> JSONResponse:
    """Invalidate current session and clear cookie."""
    from fastapi.responses import JSONResponse

    response = JSONResponse(content={"status": "logged_out"})
    response.delete_cookie(key="mist_session", path="/")
    return response
