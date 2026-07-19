"""Initial schema with hash-partitioned tables.

Revision ID: 0001_initial
Revises: None
Create Date: 2025-07-10

Creates all 21 entity tables. Three tables use HASH partitioning
by org_id (16 partitions each): config_revisions, device_status_snapshots,
and audit_records.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None

PARTITION_COUNT = 16


# ---------------------------------------------------------------------------
# Helper: create hash partitions for a parent table
# ---------------------------------------------------------------------------
def _create_hash_partitions(table_name: str) -> None:
    """Create 16 hash partitions for *table_name*."""
    for idx in range(PARTITION_COUNT):
        partition = f"{table_name}_p{idx}"
        op.execute(
            sa.text(
                f"CREATE TABLE {partition} PARTITION OF {table_name} "
                f"FOR VALUES WITH (MODULUS {PARTITION_COUNT}, REMAINDER {idx})"
            )
        )


def _drop_hash_partitions(table_name: str) -> None:
    """Drop 16 hash partitions for *table_name*."""
    for idx in range(PARTITION_COUNT):
        op.execute(sa.text(f"DROP TABLE IF EXISTS {table_name}_p{idx}"))


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------
def upgrade() -> None:
    # -- E-00 MSPs --------------------------------------------------------
    op.create_table(
        "msps",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("mist_msp_id", sa.String(36), nullable=False, unique=True),
        sa.Column("metadata_", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # -- E-01 Organizations -----------------------------------------------
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("mist_org_id", sa.String(36), nullable=False, unique=True),
        sa.Column(
            "msp_id",
            sa.Uuid(),
            sa.ForeignKey("msps.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("metadata_", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_organizations_msp_id", "organizations", ["msp_id"])

    # -- E-02 Sites -------------------------------------------------------
    op.create_table(
        "sites",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("mist_site_id", sa.String(36), nullable=False, unique=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("country_code", sa.String(2), nullable=True),
        sa.Column("timezone", sa.String(64), nullable=True),
        sa.Column("metadata_", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_sites_org_id", "sites", ["org_id"])

    # -- E-03 Devices -----------------------------------------------------
    op.create_table(
        "devices",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("mist_device_id", sa.String(36), nullable=False, unique=True),
        sa.Column(
            "site_id",
            sa.Uuid(),
            sa.ForeignKey("sites.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("device_type", sa.String(20), nullable=False),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("serial", sa.String(64), nullable=True),
        sa.Column("mac_address", sa.String(17), nullable=True),
        sa.Column("firmware_version", sa.String(64), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            server_default="unknown",
            nullable=False,
        ),
        sa.Column("metadata_", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_devices_site_id", "devices", ["site_id"])
    op.create_index("ix_devices_org_id", "devices", ["org_id"])
    op.create_index("ix_devices_device_type", "devices", ["device_type"])

    # -- E-04 ConfigRevisions (HASH partitioned) --------------------------
    op.execute(
        sa.text(
            """
            CREATE TABLE config_revisions (
                id          UUID NOT NULL,
                org_id      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                entity_type VARCHAR(30) NOT NULL,
                entity_id   UUID NOT NULL,
                revision    INTEGER NOT NULL DEFAULT 1,
                content     JSONB NOT NULL DEFAULT '{}',
                content_hash VARCHAR(64) NOT NULL,
                diff        JSONB DEFAULT '{}',
                fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
                created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
                PRIMARY KEY (id, org_id),
                UNIQUE (entity_id, content_hash, org_id)
            ) PARTITION BY HASH (org_id)
            """
        )
    )
    _create_hash_partitions("config_revisions")
    op.execute(sa.text("CREATE INDEX ix_config_revisions_entity " "ON config_revisions (entity_type, entity_id)"))

    # -- E-05 DeviceStatusSnapshots (HASH partitioned) --------------------
    op.execute(
        sa.text(
            """
            CREATE TABLE device_status_snapshots (
                id          UUID NOT NULL,
                device_id   UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
                org_id      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                status      VARCHAR(20) NOT NULL DEFAULT 'unknown',
                uptime_seconds BIGINT DEFAULT 0,
                cpu_pct     REAL DEFAULT 0.0,
                mem_pct     REAL DEFAULT 0.0,
                raw_payload JSONB DEFAULT '{}',
                captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
                PRIMARY KEY (id, org_id)
            ) PARTITION BY HASH (org_id)
            """
        )
    )
    _create_hash_partitions("device_status_snapshots")
    op.execute(sa.text("CREATE INDEX ix_dss_device ON device_status_snapshots (device_id)"))

    # -- E-06 AuditRecords (HASH partitioned) -----------------------------
    op.execute(
        sa.text(
            """
            CREATE TABLE audit_records (
                id          UUID NOT NULL,
                org_id      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                actor       VARCHAR(255) NOT NULL,
                action      VARCHAR(50) NOT NULL,
                entity_type VARCHAR(30) NOT NULL,
                entity_id   UUID NOT NULL,
                before_snapshot JSONB DEFAULT '{}',
                after_snapshot  JSONB DEFAULT '{}',
                source      VARCHAR(20) NOT NULL DEFAULT 'platform',
                created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
                PRIMARY KEY (id, org_id)
            ) PARTITION BY HASH (org_id)
            """
        )
    )
    _create_hash_partitions("audit_records")
    op.execute(sa.text("CREATE INDEX ix_audit_entity " "ON audit_records (entity_type, entity_id)"))

    # -- E-07 ScheduledJobs -----------------------------------------------
    op.create_table(
        "scheduled_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("cron_expr", sa.String(100), nullable=True),
        sa.Column("payload", postgresql.JSONB(), server_default="{}"),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_scheduled_jobs_org_id", "scheduled_jobs", ["org_id"])
    op.create_index("ix_scheduled_jobs_status", "scheduled_jobs", ["status"])

    # -- E-08 JobCheckpoints ---------------------------------------------
    op.create_table(
        "job_checkpoints",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "job_id",
            sa.Uuid(),
            sa.ForeignKey("scheduled_jobs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_name", sa.String(100), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            sa.String(20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("detail", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_job_checkpoints_job_id", "job_checkpoints", ["job_id"])

    # -- E-09 RolloutPlans ------------------------------------------------
    op.create_table(
        "rollout_plans",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            server_default="draft",
            nullable=False,
        ),
        sa.Column(
            "golden_image_id",
            sa.Uuid(),
            nullable=True,
        ),
        sa.Column("target_filter", postgresql.JSONB(), server_default="{}"),
        sa.Column("failure_threshold_pct", sa.Integer(), server_default="20"),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_rollout_plans_org_id", "rollout_plans", ["org_id"])

    # -- E-10 RolloutWaves ------------------------------------------------
    op.create_table(
        "rollout_waves",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "plan_id",
            sa.Uuid(),
            sa.ForeignKey("rollout_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("wave_index", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("device_ids", postgresql.ARRAY(sa.Text()), server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_rollout_waves_plan_id", "rollout_waves", ["plan_id"])

    # -- E-11 Baselines ---------------------------------------------------
    op.create_table(
        "baselines",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("entity_scope", sa.String(255), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("locked_by", sa.String(255), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("org_id", "entity_type", "entity_scope", name="uq_baseline_scope"),
    )

    # -- E-12 DriftAlerts -------------------------------------------------
    op.create_table(
        "drift_alerts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "baseline_id",
            sa.Uuid(),
            sa.ForeignKey("baselines.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "config_revision_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.String(20),
            server_default="warning",
            nullable=False,
        ),
        sa.Column("diff_summary", postgresql.JSONB(), server_default="{}"),
        sa.Column("acknowledged", sa.Boolean(), server_default="false"),
        sa.Column("acknowledged_by", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_drift_alerts_baseline_id", "drift_alerts", ["baseline_id"])

    # -- E-13 ChangeTemplates ---------------------------------------------
    op.create_table(
        "change_templates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column("template_body", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_change_templates_org_id", "change_templates", ["org_id"])

    # -- E-14 GoldenImages ------------------------------------------------
    op.create_table(
        "golden_images",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("image_type", sa.String(30), nullable=False),
        sa.Column("device_model", sa.String(64), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            server_default="draft",
            nullable=False,
        ),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("release_notes_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "org_id",
            "image_type",
            "device_model",
            "version",
            name="uq_golden_image_version",
        ),
    )

    # -- E-15 ComplianceAuditPacks ----------------------------------------
    op.create_table(
        "compliance_audit_packs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("rules", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("schedule_cron", sa.String(100), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_result", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_compliance_audit_packs_org_id",
        "compliance_audit_packs",
        ["org_id"],
    )

    # -- E-16 NetworkPolicies ---------------------------------------------
    op.create_table(
        "network_policies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "policy_type",
            sa.String(30),
            nullable=False,
        ),
        sa.Column("definition", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "status",
            sa.String(20),
            server_default="draft",
            nullable=False,
        ),
        sa.Column("enforcement_level", sa.String(20), server_default="audit"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_network_policies_org_id", "network_policies", ["org_id"])

    # -- E-17 IncidentChangeCorrelations ----------------------------------
    op.create_table(
        "incident_change_correlations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("incident_id", sa.String(255), nullable=False),
        sa.Column("config_revision_id", sa.Uuid(), nullable=False),
        sa.Column("correlation_score", sa.Float(), server_default="0.0"),
        sa.Column("analysis", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_icc_org_id",
        "incident_change_correlations",
        ["org_id"],
    )

    # -- E-18 NotificationChannels ----------------------------------------
    op.create_table(
        "notification_channels",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("channel_type", sa.String(20), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("alert_subscriptions", postgresql.ARRAY(sa.Text()), server_default="{}"),
        sa.Column("enabled", sa.Boolean(), server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_notification_channels_org_id",
        "notification_channels",
        ["org_id"],
    )

    # -- E-19 SyncLedgerEntries -------------------------------------------
    op.create_table(
        "sync_ledger_entries",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "org_id",
            sa.Uuid(),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_type", sa.String(30), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("items_fetched", sa.Integer(), server_default="0"),
        sa.Column("items_changed", sa.Integer(), server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_sync_ledger_org_id", "sync_ledger_entries", ["org_id"])

    # -- E-20 WebhookEnvelopes -------------------------------------------
    op.create_table(
        "webhook_envelopes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("event_id", sa.String(255), nullable=False, unique=True),
        sa.Column("topic", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("processed", sa.Boolean(), server_default="false"),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_webhook_envelopes_topic", "webhook_envelopes", ["topic"])


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------
def downgrade() -> None:
    # Reverse order of creation
    op.drop_table("webhook_envelopes")
    op.drop_table("sync_ledger_entries")
    op.drop_table("notification_channels")
    op.drop_table("incident_change_correlations")
    op.drop_table("network_policies")
    op.drop_table("compliance_audit_packs")
    op.drop_table("golden_images")
    op.drop_table("change_templates")
    op.drop_table("drift_alerts")
    op.drop_table("baselines")
    op.drop_table("rollout_waves")
    op.drop_table("rollout_plans")
    op.drop_table("job_checkpoints")
    op.drop_table("scheduled_jobs")

    # Partitioned tables — drop partitions first
    _drop_hash_partitions("audit_records")
    op.drop_table("audit_records")

    _drop_hash_partitions("device_status_snapshots")
    op.drop_table("device_status_snapshots")

    _drop_hash_partitions("config_revisions")
    op.drop_table("config_revisions")

    op.drop_table("devices")
    op.drop_table("sites")
    op.drop_table("organizations")
    op.drop_table("msps")
