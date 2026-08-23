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

from __future__ import annotations  # Defer annotation evaluation; cheap forward refs

from dataclasses import dataclass  # For query-param grouping (replaces 6/7-arg signatures)
from datetime import UTC, datetime  # Timezone-aware timestamps for ack/recertify
from typing import TYPE_CHECKING  # For type-only imports below
from uuid import UUID  # Used in route signatures and DB filters

from fastapi import APIRouter, Depends, HTTPException, Query  # FastAPI route plumbing
from sqlalchemy import select  # Build typed SQLAlchemy SELECTs

from src.api.deps import (  # DI for auth, DB session, and the org scope check
    get_authenticated_user,
    get_db_session,
    get_scoped_org_id,
)
from src.api.middleware.auth import require_org_access  # Org membership check
from src.api.schemas.common import ResponseEnvelope  # Uniform response wrapper
from src.api.schemas.sync import (  # Public response/request models
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
from src.shared.models.config import DriftAlert  # ORM model for drift alerts
from src.shared.models.governance import NetworkPolicy  # ORM model for policies
from src.shared.models.inventory import (  # ORM inventory models
    Device,
    Organization,
    Site,
    SyncLedgerEntry,
)

if TYPE_CHECKING:  # Type-only imports -- runtime cost zero
    from sqlalchemy.ext.asyncio import AsyncSession  # Async DB session type
    from src.api.middleware.auth import CurrentUser  # Current-user identity object

router = APIRouter(prefix="/sync", tags=["sync"])  # /sync/* endpoints
inv_router = APIRouter(prefix="/inventory", tags=["inventory"])  # /inventory/* endpoints


def _resolve_org_ids(
    explicit: UUID | None,
    user: CurrentUser,
) -> list[UUID]:
    """Return org_ids to query — explicit param or user's orgs.

    An explicit organization must pass the membership check. Without the
    check, any caller reads the data of any organization.
    """
    if explicit:  # Caller supplied a specific org filter
        require_org_access(str(explicit), user)  # Raise 403 when the caller is outside that org
        return [explicit]
    return [UUID(oid) for oid in user.org_ids] if user.org_ids else []  # User's accessible orgs


def _latest_ledger_by_type(
    ledger: list[SyncLedgerEntry],
) -> tuple[datetime | None, dict[str, SyncLedgerEntry]]:
    """Return ``(last_sync, latest_by_type)`` -- newest ``ended_at`` + first entry per job type."""
    last_sync: datetime | None = None  # Newest completed sync timestamp
    latest_by_type: dict[str, SyncLedgerEntry] = {}  # First entry per job type (desc-sorted)
    for entry in ledger:  # Walk newest-first ledger
        if entry.ended_at and (last_sync is None or entry.ended_at > last_sync):
            last_sync = entry.ended_at  # Track newest end timestamp
        job = entry.job_type or "unknown"  # Unknown job_type bucketed together
        if job not in latest_by_type:  # First (newest) entry wins per job type
            latest_by_type[job] = entry
    return last_sync, latest_by_type


def _entity_count_for_entry(entry: SyncLedgerEntry) -> EntitySyncCount:
    """Project a single ledger entry into the response's per-entity count row."""
    total = entry.rows_affected or 0  # Defensive: None -> 0
    synced = total if entry.status == "completed" else 0  # Only completed runs are "synced"
    error = total if entry.status == "failed" else 0  # Only failed runs are "error"
    return EntitySyncCount(
        entityType=entry.job_type or "unknown",
        total=total,
        synced=synced,
        error=error,
    )


def _aggregate_state(latest_by_type: dict[str, SyncLedgerEntry]) -> str:
    """Reduce the per-type ledger map to a single state string (stale/error/synced)."""
    if not latest_by_type:  # No ledger entries -> data is stale
        return "stale"
    has_error = any(entry.status == "failed" for entry in latest_by_type.values())  # Any failed?
    return "error" if has_error else "synced"  # Error if any failed; else synced


def _build_sync_status(
    org: Organization,
    ledger: list[SyncLedgerEntry],
) -> SyncStatusResponse:
    """Aggregate ledger entries into a single SyncStatusResponse."""
    last_sync, latest_by_type = _latest_ledger_by_type(ledger)  # Decompose ledger
    counts = [_entity_count_for_entry(entry) for entry in latest_by_type.values()]  # Per-type counts
    return SyncStatusResponse(
        orgId=org.org_id,
        lastSyncAt=last_sync or org.last_sync_at,  # Prefer newest ledger ts; fallback to org cache
        nextPollAt=None,
        state=_aggregate_state(latest_by_type),  # Single derived state
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
    org_ids = _resolve_org_ids(org_id, user)  # Compute org scope from request + identity
    stmt = select(Organization).where(Organization.org_id.in_(org_ids))  # Fetch matching orgs
    orgs = (await db.execute(stmt)).scalars().all()  # Materialize org rows
    items: list[SyncStatusResponse] = []  # Collected per-org responses
    for org in orgs:  # Walk each org in scope
        ledger = await _recent_ledger_for_org(db, org.org_id)  # Recent ledger entries
        items.append(_build_sync_status(org, ledger))  # Reduce to status response
    return ResponseEnvelope(data=items)


async def _recent_ledger_for_org(db: AsyncSession, org_id: UUID) -> list[SyncLedgerEntry]:
    """Fetch the 20 most recent ledger entries for one org (newest first)."""
    ledger_stmt = (
        select(SyncLedgerEntry)
        .where(SyncLedgerEntry.org_id == org_id)
        .order_by(SyncLedgerEntry.started_at.desc())
        .limit(20)
    )  # Bounded query -- caller drives full aggregation
    return list((await db.execute(ledger_stmt)).scalars().all())  # Materialize result list


@router.post("/trigger")
async def trigger_sync(body: SyncTriggerRequest) -> dict[str, str]:
    """Enqueue an on-demand inventory sync for an org."""
    from src.worker.tasks.sync_tasks import sync_org_inventory  # Lazy import; avoid worker cycle

    sync_org_inventory.delay(str(body.org_id))  # Hand off to Celery worker
    return {"status": "queued", "org_id": str(body.org_id)}  # Caller polls status separately


# -- Inventory queries ---------------------------------------------------


def _org_to_response(org: Organization) -> OrganizationResponse:
    """Project an Organization ORM row into the public response shape."""
    return OrganizationResponse(
        id=org.org_id,
        name=org.name,
        siteCount=len(org.sites) if org.sites else 0,  # Optional pre-loaded relationship
        deviceCount=(sum(len(s.devices) for s in org.sites) if org.sites else 0),  # Sum device counts across sites
    )


@inv_router.get("/orgs")
async def list_orgs(
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[list[OrganizationResponse]]:
    """List organizations the current user has access to."""
    stmt = _orgs_query_for_user(user)  # Build SQL scoped to user's orgs
    rows = (await db.execute(stmt)).scalars().all()  # Materialize org rows
    items = [_org_to_response(org) for org in rows]  # Project rows to response shape
    return ResponseEnvelope(data=items)


def _orgs_query_for_user(user: CurrentUser):
    """Return the SELECT statement scoped to a user's accessible orgs."""
    if user.org_ids:  # User restricted to specific orgs
        return select(Organization).where(Organization.org_id.in_([UUID(oid) for oid in user.org_ids]))
    return select(Organization)  # No restriction -> all orgs (admin)


@inv_router.get("/sites")
async def list_sites(
    org_id: UUID = Depends(get_scoped_org_id),
    db: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[list[SiteResponse]]:
    """List sites for an organization."""
    stmt = select(Site).where(Site.org_id == org_id)  # Filter sites by org
    rows = (await db.execute(stmt)).scalars().all()  # Materialize sites
    items = [
        SiteResponse(
            id=s.site_id,
            orgId=s.org_id,
            name=s.name,
            location=s.address,
            deviceCount=len(s.devices) if s.devices else 0,  # Pre-loaded relationship count
        )
        for s in rows
    ]
    return ResponseEnvelope(data=items)


def _device_to_response(d: Device) -> DeviceResponse:
    """Project a Device ORM row into the public response shape."""
    return DeviceResponse(
        id=d.device_id,
        orgId=d.org_id,
        siteId=d.site_id,
        name=d.name,
        type=d.device_type,
        model=d.model,
        serial=d.serial,
        mac=d.mac_address,
        firmwareVersion=d.firmware_version,
        connectionStatus=d.status or "disconnected",  # Fallback for null status
        uptime=d.uptime,
        lastSeenAt=d.last_seen_at.isoformat() if d.last_seen_at else None,  # ISO string or None
    )


def _device_search_query(org_id: UUID | None, site_id: UUID | None, search: str | None):
    """Compose the Device SELECT with optional org/site/search filters."""
    stmt = select(Device)  # Base select
    if org_id:  # Apply org filter
        stmt = stmt.where(Device.org_id == org_id)
    if site_id:  # Apply site filter
        stmt = stmt.where(Device.site_id == site_id)
    if search:  # Apply name/MAC search
        pattern = f"%{search}%"  # SQL LIKE pattern
        stmt = stmt.where(Device.name.ilike(pattern) | Device.mac_address.ilike(pattern))
    return stmt


@inv_router.get("/devices")
async def list_devices(
    org_id: UUID | None = Query(None),
    site_id: UUID | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[list[DeviceResponse]]:
    """List devices (filtered by org, site, and/or name/MAC search)."""
    org_ids = _resolve_org_ids(org_id, user)  # Check membership and compute the org scope
    stmt = _device_search_query(org_id, site_id, search)  # Build SELECT with filters
    stmt = stmt.where(Device.org_id.in_(org_ids))  # Never return a device outside the caller scope
    rows = (await db.execute(stmt)).scalars().all()  # Materialize device rows
    items = [_device_to_response(d) for d in rows]  # Project rows to response shape
    return ResponseEnvelope(data=items)


@inv_router.get("/devices/{device_id}")
async def get_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db_session),
) -> ResponseEnvelope[DeviceResponse]:
    """Get a single device by ID."""
    stmt = select(Device).where(Device.device_id == device_id)  # Single-row lookup
    row = (await db.execute(stmt)).scalar_one_or_none()  # 0 or 1 result
    if not row:  # 404 path
        raise HTTPException(status_code=404, detail="Device not found")
    return ResponseEnvelope(data=_device_to_response(row))  # 200 path


# ===================================================================
# Drift alert endpoints (T094)
# ===================================================================

drift_router = APIRouter(prefix="/drift", tags=["drift"])  # /drift/* endpoints


@dataclass(slots=True)
class DriftAlertFilters:
    """Grouped query filters for /drift/alerts (replaces 6+ separate params)."""

    org_id: UUID | None  # Optional org scope
    acknowledged: bool | None  # None = no ack filter; True/False filter on status
    status: str | None  # Optional explicit status filter (overridden by acknowledged)
    page: int  # 1-based page number
    per_page: int  # Page size 1-200


def _drift_alert_filters(
    org_id: UUID | None = Query(None),
    acknowledged: bool | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    user: CurrentUser = Depends(get_authenticated_user),
) -> DriftAlertFilters:
    """FastAPI dependency that groups drift-alert filter query params into one object."""
    if org_id is not None:  # Only an explicit organization needs the membership check
        require_org_access(str(org_id), user)  # Raise 403 when the caller is outside that org
    return DriftAlertFilters(
        org_id=org_id,
        acknowledged=acknowledged,
        status=status,
        page=page,
        per_page=per_page,
    )


def _drift_alert_query(filters: DriftAlertFilters, org_ids: list[UUID]):
    """Build the drift-alert SELECT with org scope + status filters + pagination."""
    stmt = (
        select(DriftAlert).where(DriftAlert.org_id.in_(org_ids)).order_by(DriftAlert.detected_at.desc())
    )  # Newest first
    if filters.acknowledged is not None:  # ack flag explicitly set
        ack_status = "acknowledged" if filters.acknowledged else "open"
        stmt = stmt.where(DriftAlert.status == ack_status)
    elif filters.status:  # Fall back to explicit status string
        stmt = stmt.where(DriftAlert.status == filters.status)
    return stmt.offset((filters.page - 1) * filters.per_page).limit(filters.per_page)


@drift_router.get("/alerts")
async def list_drift_alerts(
    filters: DriftAlertFilters = Depends(_drift_alert_filters),
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[list[DriftAlertSummary]]:
    """List drift alerts for user's organizations (FR-011)."""
    org_ids = _resolve_org_ids(filters.org_id, user)  # Scope alerts to user's orgs
    stmt = _drift_alert_query(filters, org_ids)  # Build paginated SELECT
    rows = (await db.execute(stmt)).scalars().all()  # Materialize alert rows
    items = [DriftAlertSummary.model_validate(r) for r in rows]  # Pydantic-validate each row
    return ResponseEnvelope(data=items)


@drift_router.get("/alerts/{alert_id}")
async def get_drift_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[DriftAlertDetail]:
    """Get drift alert detail with full diff payload."""
    stmt = select(DriftAlert).where(DriftAlert.alert_id == alert_id)  # Single-row lookup
    alert = (await db.execute(stmt)).scalar_one_or_none()  # 0 or 1
    if alert is None:  # 404 path
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
    stmt = select(DriftAlert).where(DriftAlert.alert_id == alert_id)  # Look up alert
    alert = (await db.execute(stmt)).scalar_one_or_none()  # 0 or 1
    if alert is None:  # 404 path
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "acknowledged"  # Flip state to acknowledged
    alert.resolved_by = user.email  # Track who acknowledged
    alert.resolved_at = datetime.now(UTC)  # Track when (UTC)
    await db.flush()  # Push changes to DB without committing the transaction
    return ResponseEnvelope(data=DriftAlertDetail.model_validate(alert))


# ===================================================================
# Network policy endpoints (T095)
# ===================================================================

policy_router = APIRouter(prefix="/policies", tags=["policies"])  # /policies/* endpoints


@dataclass(slots=True)
class PolicyListFilters:
    """Grouped query filters for /policies (replaces 5+ separate params)."""

    org_id: UUID  # Org scope (required)
    lifecycle_state: str | None  # Optional lifecycle filter
    page: int  # 1-based page number
    per_page: int  # Page size 1-200


def _policy_list_filters(
    org_id: UUID = Depends(get_scoped_org_id),
    lifecycle_state: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
) -> PolicyListFilters:
    """FastAPI dependency that groups policy-list filter query params into one object."""
    return PolicyListFilters(
        org_id=org_id,
        lifecycle_state=lifecycle_state,
        page=page,
        per_page=per_page,
    )


def _policy_list_query(filters: PolicyListFilters):
    """Build the policy SELECT with org scope + lifecycle filter + pagination."""
    stmt = (
        select(NetworkPolicy).where(NetworkPolicy.org_id == filters.org_id).order_by(NetworkPolicy.name)
    )  # Base SELECT, alpha-sorted
    if filters.lifecycle_state:  # Apply optional lifecycle filter
        stmt = stmt.where(NetworkPolicy.lifecycle_state == filters.lifecycle_state)
    return stmt.offset((filters.page - 1) * filters.per_page).limit(filters.per_page)


@policy_router.get("")
async def list_policies(
    filters: PolicyListFilters = Depends(_policy_list_filters),
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[list[PolicyResponse]]:
    """List network policies (FR-024)."""
    stmt = _policy_list_query(filters)  # Build paginated SELECT
    rows = (await db.execute(stmt)).scalars().all()  # Materialize policy rows
    items = [PolicyResponse.model_validate(r) for r in rows]  # Validate each row
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
    )  # Hydrate ORM object from request body
    db.add(policy)  # Stage insert
    await db.flush()  # Push to DB to populate generated columns
    return ResponseEnvelope(data=PolicyResponse.model_validate(policy))


@policy_router.post("/{policy_id}/recertify")
async def recertify_policy(
    policy_id: UUID,
    body: PolicyRecertifyRequest,
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[PolicyResponse]:
    """Recertify a policy before expiration."""
    if not body.confirm:  # Reject unconfirmed recertify
        raise HTTPException(status_code=400, detail="confirm required")
    stmt = select(NetworkPolicy).where(NetworkPolicy.policy_id == policy_id)  # Look up policy
    policy = (await db.execute(stmt)).scalar_one_or_none()  # 0 or 1
    if policy is None:  # 404 path
        raise HTTPException(status_code=404, detail="Policy not found")
    policy.last_reviewed_at = datetime.now(UTC)  # Stamp review time
    policy.reviewed_by = user.email  # Track who reviewed
    policy.version = policy.version + 1  # Bump version
    await db.flush()  # Push update
    return ResponseEnvelope(data=PolicyResponse.model_validate(policy))
