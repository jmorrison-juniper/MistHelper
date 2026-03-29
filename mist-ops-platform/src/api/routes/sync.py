"""Sync routes — inventory queries, sync status, drift alerts, and policies.

Provides:
- GET  /sync/status         — latest sync ledger entries
- POST /sync/trigger        — on-demand inventory sync
- GET  /inventory/orgs      — list organizations
- GET  /inventory/sites     — list sites (scoped by org)
- GET  /inventory/devices   — list devices (scoped by org or site)
- GET  /drift/alerts        — list drift alerts (T094)
- GET  /drift/alerts/{id}   — drift alert detail
- POST /drift/alerts/{id}/acknowledge — acknowledge a drift alert
- GET  /policies            — list network policies (T095)
- POST /policies            — create network policy
- POST /policies/{id}/recertify — recertify a policy
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_authenticated_user, get_db_session
from src.api.middleware.auth import CurrentUser
from src.api.schemas.common import ResponseEnvelope
from src.api.schemas.sync import (
    DeviceResponse,
    DriftAcknowledgeRequest,
    DriftAlertDetail,
    DriftAlertSummary,
    EntitySyncCount,
    OrganizationResponse,
    PolicyCreate,
    PolicyRecertifyRequest,
    PolicyResponse,
    SiteResponse,
    SyncStatusResponse,
    SyncTriggerRequest,
)
from src.shared.models.config import DriftAlert
from src.shared.models.governance import NetworkPolicy
from src.shared.models.inventory import (
    Device,
    Organization,
    Site,
    SyncLedgerEntry,
)

router = APIRouter(prefix="/sync", tags=["sync"])
inv_router = APIRouter(prefix="/inventory", tags=["inventory"])


def _resolve_org_ids(
    explicit: UUID | None, user: CurrentUser,
) -> list[UUID]:
    """Return org_ids to query — explicit param or user's orgs."""
    if explicit:
        return [explicit]
    return [UUID(oid) for oid in user.org_ids] if user.org_ids else []


def _build_sync_status(
    org: Organization, ledger: list[SyncLedgerEntry],
) -> SyncStatusResponse:
    """Aggregate ledger entries into a single SyncStatusResponse."""
    last_sync = None
    latest_by_type: dict[str, SyncLedgerEntry] = {}

    for entry in ledger:
        if entry.ended_at and (last_sync is None or entry.ended_at > last_sync):
            last_sync = entry.ended_at
        job = entry.job_type or "unknown"
        if job not in latest_by_type:
            latest_by_type[job] = entry

    state = "stale"
    counts = []
    has_error = False
    for job, entry in latest_by_type.items():
        total = entry.rows_affected or 0
        synced = total if entry.status == "completed" else 0
        error = total if entry.status == "failed" else 0
        if entry.status == "failed":
            has_error = True
        counts.append(EntitySyncCount(
            entityType=job, total=total, synced=synced, error=error,
        ))

    if latest_by_type:
        state = "error" if has_error else "synced"

    return SyncStatusResponse(
        orgId=org.org_id,
        lastSyncAt=last_sync or org.last_sync_at,
        nextPollAt=None,
        state=state,
        entityCounts=counts,
    )


# -- Sync status ---------------------------------------------------------

@router.get("/status")
async def get_sync_status(
    org_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[list[SyncStatusResponse]]:
    """Return aggregated sync status per org."""
    org_ids = _resolve_org_ids(org_id, user)
    stmt = select(Organization).where(Organization.org_id.in_(org_ids))
    orgs = (await db.execute(stmt)).scalars().all()

    items: list[SyncStatusResponse] = []
    for org in orgs:
        ledger_stmt = (
            select(SyncLedgerEntry)
            .where(SyncLedgerEntry.org_id == org.org_id)
            .order_by(SyncLedgerEntry.started_at.desc())
            .limit(20)
        )
        ledger = (await db.execute(ledger_stmt)).scalars().all()
        items.append(_build_sync_status(org, ledger))
    return ResponseEnvelope(data=items)


@router.post("/trigger")
async def trigger_sync(body: SyncTriggerRequest) -> dict[str, str]:
    """Enqueue an on-demand inventory sync for an org."""
    from src.worker.tasks.sync_tasks import sync_org_inventory

    sync_org_inventory.delay(str(body.org_id))
    return {"status": "queued", "org_id": str(body.org_id)}


# -- Inventory queries ---------------------------------------------------

@inv_router.get("/orgs")
async def list_orgs(
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[list[OrganizationResponse]]:
    """List organizations the current user has access to."""
    if user.org_ids:
        stmt = select(Organization).where(
            Organization.org_id.in_(
                [UUID(oid) for oid in user.org_ids]
            )
        )
    else:
        stmt = select(Organization)
    rows = (await db.execute(stmt)).scalars().all()
    items = [
        OrganizationResponse(
            id=org.org_id,
            name=org.name,
            siteCount=len(org.sites) if org.sites else 0,
            deviceCount=sum(
                len(s.devices) for s in org.sites
            ) if org.sites else 0,
        )
        for org in rows
    ]
    return ResponseEnvelope(data=items)


@inv_router.get("/sites")
async def list_sites(
    org_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[SiteResponse]]:
    """List sites for an organization."""
    stmt = select(Site).where(Site.org_id == org_id)
    rows = (await db.execute(stmt)).scalars().all()
    items = [
        SiteResponse(
            id=s.site_id,
            orgId=s.org_id,
            name=s.name,
            location=s.address,
            deviceCount=len(s.devices) if s.devices else 0,
        )
        for s in rows
    ]
    return ResponseEnvelope(data=items)


@inv_router.get("/devices")
async def list_devices(
    org_id: UUID | None = Query(None),
    site_id: UUID | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[DeviceResponse]]:
    """List devices (filtered by org, site, and/or name/MAC search)."""
    stmt = select(Device)
    if org_id:
        stmt = stmt.where(Device.org_id == org_id)
    if site_id:
        stmt = stmt.where(Device.site_id == site_id)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(Device.name.ilike(pattern) | Device.mac_address.ilike(pattern))
    rows = (await db.execute(stmt)).scalars().all()
    items = [
        DeviceResponse(
            id=d.device_id,
            orgId=d.org_id,
            siteId=d.site_id,
            name=d.name,
            type=d.device_type,
            model=d.model,
            serial=d.serial,
            mac=d.mac_address,
            firmwareVersion=d.firmware_version,
            connectionStatus=d.status or "disconnected",
            uptime=d.uptime,
            lastSeenAt=d.last_seen_at.isoformat() if d.last_seen_at else None,
        )
        for d in rows
    ]
    return ResponseEnvelope(data=items)


@inv_router.get("/devices/{device_id}")
async def get_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[DeviceResponse]:
    """Get a single device by ID."""
    row = (await db.execute(
        select(Device).where(Device.device_id == device_id)
    )).scalar_one_or_none()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Device not found")
    item = DeviceResponse(
        id=row.device_id,
        orgId=row.org_id,
        siteId=row.site_id,
        name=row.name,
        type=row.device_type,
        model=row.model,
        serial=row.serial,
        mac=row.mac_address,
        firmwareVersion=row.firmware_version,
        connectionStatus=row.status or "disconnected",
        uptime=row.uptime,
        lastSeenAt=row.last_seen_at.isoformat() if row.last_seen_at else None,
    )
    return ResponseEnvelope(data=item)


# ===================================================================
# Drift alert endpoints (T094)
# ===================================================================

drift_router = APIRouter(prefix="/drift", tags=["drift"])


@drift_router.get("/alerts")
async def list_drift_alerts(
    org_id: UUID | None = Query(None),
    acknowledged: bool | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[list[DriftAlertSummary]]:
    """List drift alerts for user's organizations (FR-011)."""
    org_ids = _resolve_org_ids(org_id, user)
    stmt = (
        select(DriftAlert)
        .where(DriftAlert.org_id.in_(org_ids))
        .order_by(DriftAlert.detected_at.desc())
    )
    if acknowledged is not None:
        ack_status = "acknowledged" if acknowledged else "open"
        stmt = stmt.where(DriftAlert.status == ack_status)
    elif status:
        stmt = stmt.where(DriftAlert.status == status)
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)

    rows = (await db.execute(stmt)).scalars().all()
    items = [DriftAlertSummary.model_validate(r) for r in rows]
    return ResponseEnvelope(data=items)


@drift_router.get("/alerts/{alert_id}")
async def get_drift_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[DriftAlertDetail]:
    """Get drift alert detail with full diff payload."""
    stmt = select(DriftAlert).where(DriftAlert.alert_id == alert_id)
    alert = (await db.execute(stmt)).scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return ResponseEnvelope(data=DriftAlertDetail.model_validate(alert))


@drift_router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_drift_alert(
    alert_id: UUID,
    body: DriftAcknowledgeRequest,
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[DriftAlertDetail]:
    """Acknowledge a drift alert."""
    stmt = select(DriftAlert).where(DriftAlert.alert_id == alert_id)
    alert = (await db.execute(stmt)).scalar_one_or_none()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "acknowledged"
    alert.resolved_by = user.email
    alert.resolved_at = datetime.now(UTC)
    await db.flush()
    return ResponseEnvelope(data=DriftAlertDetail.model_validate(alert))


# ===================================================================
# Network policy endpoints (T095)
# ===================================================================

policy_router = APIRouter(prefix="/policies", tags=["policies"])


@policy_router.get("")
async def list_policies(
    org_id: UUID = Query(...),
    lifecycle_state: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[list[PolicyResponse]]:
    """List network policies (FR-024)."""
    stmt = (
        select(NetworkPolicy)
        .where(NetworkPolicy.org_id == org_id)
        .order_by(NetworkPolicy.name)
    )
    if lifecycle_state:
        stmt = stmt.where(
            NetworkPolicy.lifecycle_state == lifecycle_state,
        )
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)

    rows = (await db.execute(stmt)).scalars().all()
    items = [PolicyResponse.model_validate(r) for r in rows]
    return ResponseEnvelope(data=items)


@policy_router.post("", status_code=201)
async def create_policy(
    body: PolicyCreate,
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[PolicyResponse]:
    """Create a network policy."""
    policy = NetworkPolicy(
        org_id=body.org_id,
        mist_entity_id=body.mist_entity_id,
        policy_type=body.policy_type,
        name=body.name,
        lifecycle_state="active",
        effective_from=body.effective_from,
        expires_at=body.expires_at,
        dependencies=body.dependencies,
    )
    db.add(policy)
    await db.flush()
    return ResponseEnvelope(data=PolicyResponse.model_validate(policy))


@policy_router.post("/{policy_id}/recertify")
async def recertify_policy(
    policy_id: UUID,
    body: PolicyRecertifyRequest,
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[PolicyResponse]:
    """Recertify a policy before expiration."""
    if not body.confirm:
        raise HTTPException(status_code=400, detail="confirm required")

    stmt = select(NetworkPolicy).where(
        NetworkPolicy.policy_id == policy_id,
    )
    policy = (await db.execute(stmt)).scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    policy.last_reviewed_at = datetime.now(UTC)
    policy.reviewed_by = user.email
    policy.version = policy.version + 1
    await db.flush()
    return ResponseEnvelope(data=PolicyResponse.model_validate(policy))
