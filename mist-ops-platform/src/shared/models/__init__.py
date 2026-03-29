"""All SQLAlchemy models — import here to ensure Alembic discovers them."""

from src.shared.models.base import Base, TimestampMixin, UUIDPKMixin
from src.shared.models.config import (
    Baseline,
    ConfigRevision,
    DeviceStatusSnapshot,
    DriftAlert,
    WebhookEnvelope,
)
from src.shared.models.governance import (
    ChangeTemplate,
    ComplianceAuditPack,
    GoldenImage,
    IncidentChangeCorrelation,
    NetworkPolicy,
)
from src.shared.models.inventory import (
    MSP,
    Device,
    Organization,
    Site,
    SyncLedgerEntry,
)
from src.shared.models.operations import (
    AuditRecord,
    JobCheckpoint,
    NotificationChannel,
    RolloutPlan,
    RolloutWave,
    ScheduledJob,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDPKMixin",
    # inventory (5)
    "MSP",
    "Organization",
    "Site",
    "Device",
    "SyncLedgerEntry",
    # config (5)
    "ConfigRevision",
    "DeviceStatusSnapshot",
    "Baseline",
    "DriftAlert",
    "WebhookEnvelope",
    # operations (6 — documented exception)
    "ScheduledJob",
    "JobCheckpoint",
    "AuditRecord",
    "RolloutPlan",
    "RolloutWave",
    "NotificationChannel",
    # governance (5)
    "ChangeTemplate",
    "GoldenImage",
    "ComplianceAuditPack",
    "NetworkPolicy",
    "IncidentChangeCorrelation",
]
