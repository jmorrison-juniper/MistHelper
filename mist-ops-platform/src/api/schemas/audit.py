"""Audit Pydantic schemas (T073).

Schemas for audit records, exports, correlations, and
compliance packs matching contracts/audit.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# -- Audit record schemas -----------------------------------------------


class AuditRecordResponse(BaseModel):
    """Single audit record with old/new field values."""

    model_config = ConfigDict(from_attributes=True)

    record_id: int
    timestamp: datetime
    actor: str
    entity_type: str
    entity_id: UUID
    change_type: str
    old_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None
    revision_id: int | None = None
    job_id: UUID | None = None


# -- Export schemas -----------------------------------------------------


class ExportFilters(BaseModel):
    """Filter criteria for audit export."""

    entity_type: str | None = None
    entity_id: UUID | None = None
    actor: str | None = None
    from_ts: datetime | None = Field(None, alias="from")
    to_ts: datetime | None = Field(None, alias="to")


class ExportRequest(BaseModel):
    """Request body for POST /audit/export."""

    org_id: UUID
    format: str = "csv"
    filters: ExportFilters = Field(default_factory=ExportFilters)


class ExportStatusResponse(BaseModel):
    """Status of an async audit export."""

    export_id: UUID
    status: str
    estimated_records: int = 0
    format: str = "csv"
    record_count: int | None = None
    download_url: str | None = None


# -- Correlation schemas ------------------------------------------------


class CorrelationResponse(BaseModel):
    """Incident-change correlation entry."""

    model_config = ConfigDict(from_attributes=True)

    correlation_id: UUID
    incident_type: str
    incident_id: str
    incident_at: datetime
    change_revision_id: int | None = None
    change_job_id: UUID | None = None
    confidence_score: float
    detection_method: str
    detected_at: datetime


# -- Compliance pack schemas --------------------------------------------


class CompliancePackRequest(BaseModel):
    """Request body for POST /audit/compliance-packs."""

    org_id: UUID
    framework: str
    date_range_start: datetime
    date_range_end: datetime
    export_format: str = "json"


class CompliancePackResponse(BaseModel):
    """Status of a compliance pack generation."""

    model_config = ConfigDict(from_attributes=True)

    pack_id: UUID
    status: str = "generating"
    framework: str
    record_count: int = 0
    estimated_records: int = 0
    download_url: str | None = None
    generated_at: datetime | None = None
