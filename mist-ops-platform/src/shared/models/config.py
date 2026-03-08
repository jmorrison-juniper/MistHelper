"""Config models: ConfigRevision, DeviceStatusSnapshot, Baseline, DriftAlert, WebhookEnvelope.

Entities E-04, E-05, E-11, E-12, E-20 per data-model.md.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.models.base import Base


# ---------------------------------------------------------------------------
# E-04: ConfigRevision (hash-partitioned by org_id)
# ---------------------------------------------------------------------------
class ConfigRevision(Base):
    """Immutable configuration snapshot captured from Mist API."""

    __tablename__ = "config_revisions"
    __table_args__ = (
        UniqueConstraint("entity_id", "content_hash", "org_id", name="uq_revision_dedup"),
        {"postgresql_partition_by": "LIST (org_id)"},
    )

    revision_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        primary_key=True,
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False,
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    config_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    actor: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="sync",
    )


# ---------------------------------------------------------------------------
# E-05: DeviceStatusSnapshot (hash-partitioned by org_id)
# ---------------------------------------------------------------------------
class DeviceStatusSnapshot(Base):
    """Point-in-time device status for time-travel queries."""

    __tablename__ = "device_status_snapshots"
    __table_args__ = (
        {"postgresql_partition_by": "LIST (org_id)"},
    )

    snapshot_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        primary_key=True,
        nullable=False,
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.device_id"),
        nullable=False,
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    port_states: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    client_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    health_metrics: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
    )


# ---------------------------------------------------------------------------
# E-11: Baseline (intended-state definition)
# ---------------------------------------------------------------------------
class Baseline(Base):
    """Intended configuration baseline for drift detection."""

    __tablename__ = "baselines"
    __table_args__ = (
        UniqueConstraint(
            "org_id", "entity_type", "entity_scope",
            name="uq_baseline_scope",
        ),
    )

    baseline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_scope: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False,
    )
    config_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    updated_by: Mapped[str] = mapped_column(Text, nullable=False)


# ---------------------------------------------------------------------------
# E-12: DriftAlert
# ---------------------------------------------------------------------------
class DriftAlert(Base):
    """Alert raised when actual config diverges from baseline."""

    __tablename__ = "drift_alerts"

    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        nullable=False,
        index=True,
    )
    baseline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("baselines.baseline_id"),
        nullable=False,
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.device_id"),
        nullable=False,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    diff_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="open",
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    resolved_by: Mapped[str | None] = mapped_column(Text, nullable=True)


# ---------------------------------------------------------------------------
# E-20: WebhookEnvelope (deduplication store)
# ---------------------------------------------------------------------------
class WebhookEnvelope(Base):
    """Inbound Mist webhook payload with dedup tracking."""

    __tablename__ = "webhook_envelopes"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        nullable=False,
        index=True,
    )
    event_id: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending",
    )
