"""Pydantic schemas for inventory and sync status (T032)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# -- Inventory response schemas ------------------------------------------

class SiteResponse(BaseModel):
    """Site detail returned by inventory endpoints."""

    id: UUID = Field(validation_alias="site_id")
    orgId: UUID = Field(validation_alias="org_id")
    name: str
    location: str | None = Field(default=None, validation_alias="address")
    deviceCount: int = 0

    model_config = {"from_attributes": True, "populate_by_name": True}


class DeviceResponse(BaseModel):
    """Device detail returned by inventory endpoints."""

    id: UUID = Field(validation_alias="device_id")
    orgId: UUID = Field(validation_alias="org_id")
    siteId: UUID = Field(validation_alias="site_id")
    name: str | None = None
    type: str = Field(default="unknown", validation_alias="device_type")
    model: str | None = None
    serial: str | None = None
    mac: str | None = Field(default=None, validation_alias="mac_address")
    firmwareVersion: str | None = Field(
        default=None, validation_alias="firmware_version",
    )
    connectionStatus: str = Field(default="disconnected", validation_alias="status")
    uptime: int | None = None
    lastSeenAt: str | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class OrganizationResponse(BaseModel):
    """Organization summary for dashboard display."""

    id: UUID
    name: str
    siteCount: int = 0
    deviceCount: int = 0

    model_config = {"from_attributes": True}


# -- Sync status schemas ------------------------------------------------

class EntitySyncCount(BaseModel):
    """Per-entity-type sync counts."""

    entityType: str
    total: int = 0
    synced: int = 0
    stale: int = 0
    error: int = 0


class SyncStatusResponse(BaseModel):
    """Aggregated sync status for a single org (matches frontend SyncStatus)."""

    orgId: UUID
    lastSyncAt: datetime | None = None
    nextPollAt: datetime | None = None
    state: str = "stale"
    entityCounts: list[EntitySyncCount] = []


class SyncTriggerRequest(BaseModel):
    """Request body for POST /sync/trigger."""

    org_id: UUID


# -- Drift alert schemas ------------------------------------------------


class DriftAlertSummary(BaseModel):
    """Drift alert list entry."""

    model_config = {"from_attributes": True}

    alert_id: UUID
    org_id: UUID
    baseline_id: UUID
    device_id: UUID
    status: str
    detected_at: datetime


class DriftAlertDetail(BaseModel):
    """Drift alert with full diff payload."""

    model_config = {"from_attributes": True}

    alert_id: UUID
    org_id: UUID
    baseline_id: UUID
    device_id: UUID
    diff_payload: dict
    status: str
    detected_at: datetime
    resolved_at: datetime | None = None
    resolved_by: str | None = None


class DriftAcknowledgeRequest(BaseModel):
    """Request to acknowledge a drift alert."""

    comment: str = ""


# -- Network policy schemas ---------------------------------------------


class PolicyCreate(BaseModel):
    """Request body for POST /policies."""

    org_id: UUID
    mist_entity_id: UUID
    policy_type: str
    name: str
    effective_from: datetime | None = None
    expires_at: datetime | None = None
    dependencies: dict | None = None


class PolicyResponse(BaseModel):
    """Network policy response."""

    model_config = {"from_attributes": True}

    policy_id: UUID
    org_id: UUID
    mist_entity_id: UUID
    policy_type: str
    name: str
    lifecycle_state: str
    version: int
    effective_from: datetime | None = None
    expires_at: datetime | None = None
    last_reviewed_at: datetime | None = None
    reviewed_by: str | None = None


class PolicyRecertifyRequest(BaseModel):
    """Request to recertify a policy."""

    confirm: bool = False
    comment: str = ""
