"""Governance models: ChangeTemplate, GoldenImage, ComplianceAuditPack, NetworkPolicy, IncidentChangeCorrelation.

Entities E-13, E-14, E-15, E-16, E-17 per data-model.md.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
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

from src.shared.models.base import Base, TimestampMixin


# ---------------------------------------------------------------------------
# E-13: ChangeTemplate
# ---------------------------------------------------------------------------
class ChangeTemplate(Base, TimestampMixin):
    """Reusable template for common configuration changes."""

    __tablename__ = "change_templates"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    parameter_schema: Mapped[dict] = mapped_column(JSONB, nullable=False)
    config_template: Mapped[dict] = mapped_column(JSONB, nullable=False)
    target_entity_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
    )
    approval_required: Mapped[bool] = mapped_column(
        default=False, server_default="false",
    )
    author: Mapped[str] = mapped_column(Text, nullable=False)


# ---------------------------------------------------------------------------
# E-14: GoldenImage
# ---------------------------------------------------------------------------
class GoldenImage(Base, TimestampMixin):
    """Approved firmware or config artifact for controlled deployments."""

    __tablename__ = "golden_images"
    __table_args__ = (
        UniqueConstraint(
            "org_id", "image_type", "device_model", "version",
            name="uq_golden_image",
        ),
    )

    image_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        nullable=False,
        index=True,
    )
    image_type: Mapped[str] = mapped_column(String(30), nullable=False)
    device_model: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft",
    )
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_by: Mapped[str] = mapped_column(Text, nullable=False)


# ---------------------------------------------------------------------------
# E-15: ComplianceAuditPack
# ---------------------------------------------------------------------------
class ComplianceAuditPack(Base):
    """Bundled compliance evidence export (SOX, PCI-DSS, SOC2)."""

    __tablename__ = "compliance_audit_packs"

    pack_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        nullable=False,
        index=True,
    )
    framework: Mapped[str] = mapped_column(String(20), nullable=False)
    date_range_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    date_range_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    included_records: Mapped[dict] = mapped_column(JSONB, nullable=False)
    artifact_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    export_format: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default="json",
    )
    generated_by: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


# ---------------------------------------------------------------------------
# E-16: NetworkPolicy
# ---------------------------------------------------------------------------
class NetworkPolicy(Base):
    """Mist network policy lifecycle tracking."""

    __tablename__ = "network_policies"

    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        nullable=False,
        index=True,
    )
    mist_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False,
    )
    policy_type: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="active",
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1",
    )
    effective_from: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    dependencies: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    reviewed_by: Mapped[str | None] = mapped_column(Text, nullable=True)


# ---------------------------------------------------------------------------
# E-17: IncidentChangeCorrelation
# ---------------------------------------------------------------------------
class IncidentChangeCorrelation(Base):
    """Temporal/scope correlation between incidents and config changes."""

    __tablename__ = "incident_change_correlations"

    correlation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        nullable=False,
        index=True,
    )
    incident_type: Mapped[str] = mapped_column(String(30), nullable=False)
    incident_id: Mapped[str] = mapped_column(Text, nullable=False)
    incident_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    change_revision_id: Mapped[int | None] = mapped_column(
        nullable=True,
    )
    change_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    confidence_score: Mapped[float] = mapped_column(
        Float, nullable=False,
    )
    detection_method: Mapped[str] = mapped_column(
        String(20), nullable=False,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
