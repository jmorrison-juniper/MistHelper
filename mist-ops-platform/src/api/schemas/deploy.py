"""Deploy Pydantic schemas (T062).

Schemas for scheduled deployment jobs, dry-run validation,
and job lifecycle matching contracts/deploy.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# -- Target entity schema -----------------------------------------------


class TargetEntity(BaseModel):
    """A single entity targeted by a deployment."""

    entity_type: str
    entity_id: UUID


# -- Check definition schemas -------------------------------------------


class CheckDefinition(BaseModel):
    """Pre/post check definition for a scheduled job."""

    type: str
    timeout_seconds: int = 30
    min_version: str | None = None
    min_threshold: int | None = None
    wait_seconds: int | None = None


# -- Job CRUD schemas ---------------------------------------------------


class JobCreate(BaseModel):
    """Request body for POST /deploy/jobs."""

    org_id: UUID
    target_entities: list[TargetEntity]
    change_payload: dict[str, Any]
    scheduled_at: datetime
    pre_check_defs: list[CheckDefinition] = Field(default_factory=list)
    post_check_defs: list[CheckDefinition] = Field(default_factory=list)
    auto_rollback_on_failure: bool = True


class JobSummary(BaseModel):
    """Abbreviated job info for list responses."""

    model_config = ConfigDict(from_attributes=True)

    job_id: UUID = Field(alias="job_id")
    status: str
    scheduled_at: datetime
    target_count: int = 0
    created_by: str | None = None
    approved_by: str | None = None
    rollout_plan_id: UUID | None = None
    created_at: datetime


class CheckpointDetail(BaseModel):
    """Status of a single checkpoint within a job."""

    entity_id: UUID
    step: str
    status: str
    detail: dict[str, Any] | None = None


class JobDetail(BaseModel):
    """Full job info for GET /deploy/jobs/{job_id}."""

    model_config = ConfigDict(from_attributes=True)

    job_id: UUID = Field(alias="job_id")
    status: str
    scheduled_at: datetime
    started_at: datetime | None = None
    target_entities: list[TargetEntity] = Field(default_factory=list)
    change_payload: dict[str, Any] = Field(default_factory=dict)
    pre_check_result: dict[str, Any] | None = None
    post_check_result: dict[str, Any] | None = None
    checkpoints: list[CheckpointDetail] = Field(default_factory=list)
    created_by: str | None = None
    approved_by: str | None = None


class JobUpdate(BaseModel):
    """Request body for PUT /deploy/jobs/{job_id}."""

    scheduled_at: datetime | None = None
    change_payload: dict[str, Any] | None = None
    pre_check_defs: list[CheckDefinition] | None = None
    post_check_defs: list[CheckDefinition] | None = None


class JobApproveRequest(BaseModel):
    """Request body for POST /deploy/jobs/{id}/approve."""

    confirm: bool = False
    comment: str = ""


class JobCancelledResponse(BaseModel):
    """Response after job cancellation."""

    job_id: UUID
    status: str = "cancelled"
    cancelled_at: datetime


# -- Dry-run schemas ----------------------------------------------------


class DryRunRequest(BaseModel):
    """Request body for POST /deploy/dry-run."""

    org_id: UUID
    target_entities: list[TargetEntity]
    change_payload: dict[str, Any]


class BlastRadius(BaseModel):
    """Estimated scope of change impact."""

    devices_affected: int = 0
    sites_affected: int = 0
    estimated_clients_affected: int = 0


class DryRunResponse(BaseModel):
    """Result of a dry-run validation."""

    valid: bool
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_level: str = "low"
    blast_radius: BlastRadius = Field(default_factory=BlastRadius)
    warnings: list[str] = Field(default_factory=list)
    policy_violations: list[str] = Field(default_factory=list)
    schema_errors: list[str] = Field(default_factory=list)


# -- Rollout schemas (T083) ---------------------------------------------


class WaveCreate(BaseModel):
    """Single wave definition in a rollout creation."""

    wave_number: int
    name: str = ""
    target_entities: list[TargetEntity]


class HealthGateCriteria(BaseModel):
    """Health gate criteria for automatic wave promotion."""

    min_client_count_pct: int = 90
    max_alarm_count: int = 0
    wait_minutes: int = 30


class RolloutCreate(BaseModel):
    """Request body for POST /deploy/rollouts."""

    org_id: UUID
    name: str
    promotion_mode: str = "manual"
    health_gate_criteria: HealthGateCriteria = Field(
        default_factory=HealthGateCriteria,
    )
    waves: list[WaveCreate]
    change_payload: dict[str, Any] = Field(default_factory=dict)


class WaveResponse(BaseModel):
    """Single wave status in a rollout."""

    model_config = ConfigDict(from_attributes=True)

    wave_number: int
    status: str
    target_entities: list[dict[str, Any]] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    health_check_result: dict[str, Any] | None = None


class RolloutSummary(BaseModel):
    """Rollout plan summary for list responses."""

    model_config = ConfigDict(from_attributes=True)

    plan_id: UUID
    name: str
    status: str
    promotion_mode: str
    wave_count: int = 0
    total_targets: int = 0
    created_at: datetime


class RolloutDetail(BaseModel):
    """Full rollout plan with waves."""

    model_config = ConfigDict(from_attributes=True)

    plan_id: UUID
    name: str
    status: str
    promotion_mode: str
    health_gate_criteria: dict[str, Any] = Field(default_factory=dict)
    waves: list[WaveResponse] = Field(default_factory=list)
    created_by: str
    created_at: datetime


# -- Golden image schemas -----------------------------------------------


class GoldenImageCreate(BaseModel):
    """Request body for POST /deploy/golden-images."""

    org_id: UUID
    image_type: str
    device_model: str
    version: str
    content_hash: str
    artifact_url: str | None = None


class GoldenImageResponse(BaseModel):
    """Golden image entry."""

    model_config = ConfigDict(from_attributes=True)

    image_id: UUID
    image_type: str
    device_model: str
    version: str
    lifecycle_state: str
    content_hash: str
    artifact_url: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_by: str
    created_at: datetime


# -- Change template schemas -------------------------------------------


class TemplateCreate(BaseModel):
    """Request body for POST /deploy/templates (FR-031)."""

    org_id: UUID
    name: str
    category: str
    target_entity_type: str
    parameter_schema: dict[str, Any] = Field(default_factory=dict)
    config_template: dict[str, Any] = Field(default_factory=dict)
    approval_required: bool = False


class TemplateResponse(BaseModel):
    """Change template response."""

    model_config = ConfigDict(from_attributes=True)

    template_id: UUID
    org_id: UUID
    name: str
    category: str
    target_entity_type: str
    parameter_schema: dict[str, Any] = Field(default_factory=dict)
    config_template: dict[str, Any] = Field(default_factory=dict)
    approval_required: bool
    author: str
    created_at: datetime


class TemplateInstantiateRequest(BaseModel):
    """Request body for POST /deploy/templates/{id}/instantiate."""

    org_id: UUID
    target_entity_id: UUID
    parameters: dict[str, Any] = Field(default_factory=dict)
    scheduled_at: datetime | None = None
