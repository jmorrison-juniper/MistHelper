"""Config and time-travel Pydantic schemas (T045).

Schemas for configuration revisions, diffs, and time-travel queries
matching the contracts/config.md API contract.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# -- Revision schemas ---------------------------------------------------


class RevisionResponse(BaseModel):
    """Single config revision summary (without full payload)."""

    model_config = ConfigDict(from_attributes=True)

    revision_id: int = Field(alias="revision_number")
    entity_type: str
    entity_id: UUID
    captured_at: datetime
    content_hash: str
    actor: str | None = None
    source: str


class RevisionDetailResponse(BaseModel):
    """Full config revision including the JSON payload."""

    model_config = ConfigDict(from_attributes=True)

    revision_id: int = Field(alias="revision_number")
    entity_type: str
    entity_id: UUID
    captured_at: datetime
    content_hash: str
    actor: str | None = None
    config_payload: dict[str, Any] = Field(alias="config_blob")


# -- Diff schemas -------------------------------------------------------


class DiffChange(BaseModel):
    """A single field-level diff entry."""

    path: str
    old_value: Any = None
    new_value: Any = None
    change_type: str


class DiffSummary(BaseModel):
    """Aggregate count of changes in a diff."""

    fields_changed: int = 0
    fields_added: int = 0
    fields_removed: int = 0


class DiffRequest(BaseModel):
    """Request body for POST /config/diff."""

    org_id: UUID
    old_revision_id: int
    new_revision_id: int


class DiffResponse(BaseModel):
    """Result of computing a diff between two revisions."""

    old_revision_id: int
    new_revision_id: int
    entity_id: UUID
    changes: list[DiffChange]
    summary: DiffSummary


# -- Time-travel schemas ------------------------------------------------


class TimeTravelRequest(BaseModel):
    """Query parameters for GET /config/time-travel."""

    org_id: UUID
    entity_id: UUID
    entity_type: str
    timestamp: datetime
    include_status: bool = False
    include_health: bool = False


class TimeTravelStatusSnapshot(BaseModel):
    """Device status at a point in time."""

    operational_state: str = "unknown"
    client_count: int = 0
    uptime_seconds: int = 0
    cpu_pct: float = 0.0
    mem_pct: float = 0.0


class TimeTravelResponse(BaseModel):
    """Response for GET /config/time-travel."""

    entity_id: UUID
    entity_type: str
    queried_timestamp: datetime
    actual_timestamp: datetime | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    status: TimeTravelStatusSnapshot | None = None
    health: dict[str, Any] | None = None


# -- Install-from-revision schemas --------------------------------------


class InstallFromRevisionRequest(BaseModel):
    """Request body for POST /config/install-from-revision."""

    org_id: UUID
    revision_id: int
    target_entity_ids: list[UUID]
    confirm: bool = False
    reason: str = ""


class InstallJobResponse(BaseModel):
    """Response for queued install-from-revision jobs."""

    job_id: UUID
    status: str = "pending"
    target_count: int
    revision_id: int
    message: str = "Install-from-revision job queued"


# -- Baseline schemas ---------------------------------------------------


class BaselineCreate(BaseModel):
    """Request to create or update a baseline."""

    org_id: UUID
    entity_type: str
    entity_scope: UUID
    config_payload: dict[str, Any]


class BaselineResponse(BaseModel):
    """Baseline summary returned by list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    baseline_id: UUID
    org_id: UUID
    entity_type: str
    entity_scope: UUID
    updated_at: datetime
    updated_by: str


class AcceptDriftRequest(BaseModel):
    """Request to accept drift as new baseline."""

    alert_id: UUID
    confirm: bool = False
    reason: str = ""


class RemediateRequest(BaseModel):
    """Request to push baseline config back to drifted devices."""

    alert_ids: list[UUID]
    confirm: bool = False
    reason: str = ""
