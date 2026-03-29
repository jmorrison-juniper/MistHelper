"""Operations models: ScheduledJob, JobCheckpoint, AuditRecord, RolloutPlan, RolloutWave, NotificationChannel.

Entities E-07, E-08, E-06, E-09, E-10, E-18 per data-model.md.
NOTE: 6 entities — documented Principle I exception (see plan.md Complexity Tracking).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.models.base import Base, TimestampMixin


# ---------------------------------------------------------------------------
# E-07: ScheduledJob
# ---------------------------------------------------------------------------
class ScheduledJob(Base, TimestampMixin):
    """Deployment job with lifecycle state machine."""

    __tablename__ = "scheduled_jobs"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        nullable=False,
        index=True,
    )
    target_entities: Mapped[dict] = mapped_column(JSONB, nullable=False)
    change_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="pending",
    )
    pre_check_defs: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
    )
    post_check_defs: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
    )
    pre_check_result: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
    )
    post_check_result: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
    )
    created_by: Mapped[str] = mapped_column(Text, nullable=False)
    approved_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    rollout_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rollout_plans.plan_id"),
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    checkpoints: Mapped[list[JobCheckpoint]] = relationship(
        back_populates="job", lazy="selectin",
    )


# ---------------------------------------------------------------------------
# E-08: JobCheckpoint
# ---------------------------------------------------------------------------
class JobCheckpoint(Base):
    """Progress checkpoint for safe resumption of interrupted jobs."""

    __tablename__ = "job_checkpoints"

    checkpoint_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scheduled_jobs.job_id"),
        primary_key=True,
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False,
    )
    step: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # relationships
    job: Mapped[ScheduledJob] = relationship(back_populates="checkpoints")


# ---------------------------------------------------------------------------
# E-06: AuditRecord (hash-partitioned by org_id)
# ---------------------------------------------------------------------------
class AuditRecord(Base):
    """Field-level change audit trail entry."""

    __tablename__ = "audit_records"
    __table_args__ = (
        {"postgresql_partition_by": "LIST (org_id)"},
    )

    record_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        primary_key=True,
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    actor: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False,
    )
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)
    old_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    revision_id: Mapped[int | None] = mapped_column(
        BigInteger, nullable=True,
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )


# ---------------------------------------------------------------------------
# E-09: RolloutPlan
# ---------------------------------------------------------------------------
class RolloutPlan(Base, TimestampMixin):
    """Multi-wave rollout plan with health-gate promotion."""

    __tablename__ = "rollout_plans"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    promotion_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="manual",
    )
    health_gate_criteria: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default="draft",
    )
    created_by: Mapped[str] = mapped_column(Text, nullable=False)

    # relationships
    waves: Mapped[list[RolloutWave]] = relationship(
        back_populates="plan", lazy="selectin",
    )


# ---------------------------------------------------------------------------
# E-10: RolloutWave
# ---------------------------------------------------------------------------
class RolloutWave(Base):
    """Single wave in a multi-wave rollout plan."""

    __tablename__ = "rollout_waves"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rollout_plans.plan_id"),
        primary_key=True,
        nullable=False,
    )
    wave_number: Mapped[int] = mapped_column(
        Integer, primary_key=True, nullable=False,
    )
    target_entities: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    health_check_result: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
    )

    # relationships
    plan: Mapped[RolloutPlan] = relationship(back_populates="waves")


# ---------------------------------------------------------------------------
# E-18: NotificationChannel
# ---------------------------------------------------------------------------
class NotificationChannel(Base, TimestampMixin):
    """Notification routing channel (email or webhook)."""

    __tablename__ = "notification_channels"

    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        nullable=False,
        index=True,
    )
    channel_type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    destination: Mapped[str] = mapped_column(Text, nullable=False)
    alert_subscriptions: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true",
    )
    auth_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
