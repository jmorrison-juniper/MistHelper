"""Audit trail, correlation, and compliance endpoints (T074, T075).

Covers:
  - GET    /audit/records           — query audit trail
  - GET    /audit/records/{id}      — single record detail
  - POST   /audit/export            — async export
  - GET    /audit/correlations      — query correlations
  - POST   /audit/compliance-packs  — generate compliance pack
  - GET    /audit/compliance-packs/{id} — poll pack status
"""

from __future__ import annotations

import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import (
    get_authenticated_user,
    get_db_session,
    get_scoped_org_id,
)
from src.api.middleware.auth import CurrentUser
from src.api.schemas.audit import (
    AuditRecordResponse,
    CompliancePackRequest,
    CompliancePackResponse,
    CorrelationResponse,
    ExportRequest,
    ExportStatusResponse,
)
from src.api.schemas.common import PaginationMeta, ResponseEnvelope
from src.shared.models.governance import (
    ComplianceAuditPack,
    IncidentChangeCorrelation,
)
from src.shared.models.operations import AuditRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["audit"])


# -- Audit records ---


@router.get("/records")
async def list_audit_records(
    org_id: UUID = Depends(get_scoped_org_id),
    entity_type: str | None = Query(None),
    entity_id: UUID | None = Query(None),
    actor: str | None = Query(None),
    change_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[list[AuditRecordResponse]]:
    """Query the change audit trail (SC-006 <5s for 12 months)."""
    stmt = _build_record_query(
        org_id,
        entity_type,
        entity_id,
        actor,
        change_type,
    )
    total = await _count_records(db, stmt)
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(stmt)).scalars().all()

    items = [AuditRecordResponse.model_validate(r) for r in rows]
    meta = PaginationMeta(
        total=total,
        page=page,
        page_size=per_page,
        has_next=(page * per_page < total),
    )
    return ResponseEnvelope(data=items, meta=meta)


@router.get("/records/{record_id}")
async def get_audit_record(
    record_id: int,
    org_id: UUID = Depends(get_scoped_org_id),
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[AuditRecordResponse]:
    """Get single audit record with full old/new values."""
    stmt = select(AuditRecord).where(
        AuditRecord.record_id == record_id,
        AuditRecord.org_id == org_id,
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return ResponseEnvelope(
        data=AuditRecordResponse.model_validate(row),
    )


# -- Export ---


@router.post("/export", status_code=202)
async def export_records(
    body: ExportRequest,
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[ExportStatusResponse]:
    """Trigger async audit record export (SC-012 <30s)."""
    from src.worker.tasks.audit_tasks import export_audit_records

    filters = body.filters.model_dump(by_alias=True)
    export_audit_records.delay(
        str(body.org_id),
        body.format,
        filters,
    )
    import uuid as _uuid

    export_id = _uuid.uuid4()
    total = await _estimate_records(db, body.org_id)
    return ResponseEnvelope(
        data=ExportStatusResponse(
            export_id=export_id,
            status="generating",
            estimated_records=total,
            format=body.format,
        ),
    )


# -- Correlations ---


@router.get("/correlations")
async def list_correlations(
    org_id: UUID = Depends(get_scoped_org_id),
    incident_type: str | None = Query(None),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[list[CorrelationResponse]]:
    """Query incident-change correlations."""
    stmt = select(IncidentChangeCorrelation).where(IncidentChangeCorrelation.org_id == org_id)
    if incident_type:
        stmt = stmt.where(
            IncidentChangeCorrelation.incident_type == incident_type,
        )
    stmt = stmt.where(
        IncidentChangeCorrelation.confidence_score >= min_confidence,
    )
    stmt = stmt.order_by(IncidentChangeCorrelation.detected_at.desc()).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(stmt)).scalars().all()
    items = [CorrelationResponse.model_validate(r) for r in rows]
    return ResponseEnvelope(data=items)


# -- Compliance packs ---


@router.post("/compliance-packs", status_code=202)
async def create_compliance_pack(
    body: CompliancePackRequest,
    db: AsyncSession = Depends(get_db_session),
    user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[CompliancePackResponse]:
    """Generate a compliance audit evidence package."""
    from src.worker.tasks.audit_tasks import generate_compliance_pack

    generate_compliance_pack.delay(
        str(body.org_id),
        body.framework,
        body.date_range_start.isoformat(),
        body.date_range_end.isoformat(),
        body.export_format,
        user.email,
    )
    import uuid as _uuid

    return ResponseEnvelope(
        data=CompliancePackResponse(
            pack_id=_uuid.uuid4(),
            status="generating",
            framework=body.framework,
        ),
    )


@router.get("/compliance-packs/{pack_id}")
async def get_compliance_pack(
    pack_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    _user: CurrentUser = Depends(get_authenticated_user),
) -> ResponseEnvelope[CompliancePackResponse]:
    """Poll compliance pack generation status."""
    stmt = select(ComplianceAuditPack).where(
        ComplianceAuditPack.pack_id == pack_id,
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Pack not found")

    included = row.included_records or {}
    return ResponseEnvelope(
        data=CompliancePackResponse(
            pack_id=row.pack_id,
            status="completed",
            framework=row.framework,
            record_count=included.get("total_records", 0),
            generated_at=row.generated_at,
        ),
    )


# -- Private helpers ---


def _build_record_query(
    org_id: UUID,
    entity_type: str | None,
    entity_id: UUID | None,
    actor: str | None,
    change_type: str | None,
):
    """Build filtered AuditRecord select statement."""
    stmt = select(AuditRecord).where(AuditRecord.org_id == org_id).order_by(AuditRecord.timestamp.desc())
    if entity_type:
        stmt = stmt.where(AuditRecord.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditRecord.entity_id == entity_id)
    if actor:
        stmt = stmt.where(AuditRecord.actor == actor)
    if change_type:
        stmt = stmt.where(AuditRecord.change_type == change_type)
    return stmt


async def _count_records(db: AsyncSession, base_stmt) -> int:
    """Count total matching records for pagination."""
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    result = await db.execute(count_stmt)
    return result.scalar_one()


async def _estimate_records(db: AsyncSession, org_id: UUID) -> int:
    """Estimate total records for an org (for export status)."""
    stmt = select(func.count()).select_from(AuditRecord).where(AuditRecord.org_id == org_id)
    result = await db.execute(stmt)
    return result.scalar_one()
