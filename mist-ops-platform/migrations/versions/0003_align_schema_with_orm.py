"""Rebuild the schema so the database matches the ORM models.

Revision ID: 0003_align_schema_with_orm
Revises: 0002_add_device_uptime_last_seen
Create Date: 2026-08-24

Issue #1883 reports two schema owners that disagree. The migration `0001_initial`
built one schema. The ORM models in `src/shared/models/` declare another schema.
The disagreement broke the login route and every configuration route.

The ORM models win, because every route, worker, and API schema reads the ORM
column names. The migration `0002` already moved the migration toward the models
when it added `devices.uptime` and `devices.last_seen_at`.

This migration drops the tables of the old schema and builds the ORM schema. The
old tables hold no usable data, because no route could read or write them.

Warning: this migration drops every platform table. The drop is irreversible.
Take a database backup before you run `alembic upgrade head`.
"""

from __future__ import annotations

import logging

import sqlalchemy as sa
from alembic import op

revision: str = "0003_align_schema_with_orm"
down_revision: str = "0002_add_device_uptime_last_seen"
branch_labels: str | None = None
depends_on: str | None = None

logger = logging.getLogger(__name__)


# Every table of the old migration schema and of the ORM schema.
DROP_TABLES: tuple[str, ...] = (
    "audit_records",
    "baselines",
    "change_templates",
    "compliance_audit_packs",
    "config_revisions",
    "device_status_snapshots",
    "devices",
    "drift_alerts",
    "golden_images",
    "incident_change_correlations",
    "job_checkpoints",
    "msps",
    "network_policies",
    "notification_channels",
    "organizations",
    "orgs",
    "rollout_plans",
    "rollout_waves",
    "scheduled_jobs",
    "sites",
    "sync_ledger",
    "sync_ledger_entries",
    "webhook_envelopes",
)

# The frozen DDL of every ORM table and index, in dependency order.
CREATE_STATEMENTS: tuple[str, ...] = (
    """CREATE TABLE msps (
    msp_id UUID NOT NULL,
    name TEXT NOT NULL,
    api_host TEXT NOT NULL,
    auth_method VARCHAR(20) NOT NULL,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_enabled BOOLEAN DEFAULT 'true' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (msp_id)
)""",
    """CREATE TABLE orgs (
    org_id UUID NOT NULL,
    msp_id UUID,
    name TEXT NOT NULL,
    api_host TEXT NOT NULL,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_enabled BOOLEAN DEFAULT 'true' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (org_id),
    FOREIGN KEY(msp_id) REFERENCES msps (msp_id)
)""",
    """CREATE TABLE audit_records (
    record_id BIGSERIAL NOT NULL,
    org_id UUID NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    actor TEXT NOT NULL,
    entity_type VARCHAR(30) NOT NULL,
    entity_id UUID NOT NULL,
    change_type VARCHAR(20) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    revision_id BIGINT,
    job_id UUID,
    PRIMARY KEY (record_id, org_id),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id)
)
 PARTITION BY LIST (org_id)""",
    """CREATE TABLE baselines (
    baseline_id UUID NOT NULL,
    org_id UUID NOT NULL,
    entity_type VARCHAR(30) NOT NULL,
    entity_scope UUID NOT NULL,
    config_payload JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_by TEXT NOT NULL,
    PRIMARY KEY (baseline_id),
    CONSTRAINT uq_baseline_scope UNIQUE (org_id, entity_type, entity_scope),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id)
)""",
    """CREATE INDEX ix_baselines_org_id ON baselines (org_id)""",
    """CREATE TABLE change_templates (
    template_id UUID NOT NULL,
    org_id UUID NOT NULL,
    name TEXT NOT NULL,
    category VARCHAR(30) NOT NULL,
    parameter_schema JSONB NOT NULL,
    config_template JSONB NOT NULL,
    target_entity_type VARCHAR(30) NOT NULL,
    approval_required BOOLEAN DEFAULT 'false' NOT NULL,
    author TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (template_id),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id)
)""",
    """CREATE INDEX ix_change_templates_org_id ON change_templates (org_id)""",
    """CREATE TABLE compliance_audit_packs (
    pack_id UUID NOT NULL,
    org_id UUID NOT NULL,
    framework VARCHAR(20) NOT NULL,
    date_range_start TIMESTAMP WITH TIME ZONE NOT NULL,
    date_range_end TIMESTAMP WITH TIME ZONE NOT NULL,
    included_records JSONB NOT NULL,
    artifact_url TEXT,
    export_format VARCHAR(10) DEFAULT 'json' NOT NULL,
    generated_by TEXT NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (pack_id),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id)
)""",
    """CREATE INDEX ix_compliance_audit_packs_org_id ON compliance_audit_packs (org_id)""",
    """CREATE TABLE config_revisions (
    revision_id BIGSERIAL NOT NULL,
    org_id UUID NOT NULL,
    entity_type VARCHAR(30) NOT NULL,
    entity_id UUID NOT NULL,
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    content_hash TEXT NOT NULL,
    config_payload JSONB NOT NULL,
    actor TEXT,
    source VARCHAR(20) DEFAULT 'sync' NOT NULL,
    PRIMARY KEY (revision_id, org_id),
    CONSTRAINT uq_revision_dedup UNIQUE (entity_id, content_hash, org_id),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id)
)
 PARTITION BY LIST (org_id)""",
    """CREATE TABLE golden_images (
    image_id UUID NOT NULL,
    org_id UUID NOT NULL,
    image_type VARCHAR(30) NOT NULL,
    device_model TEXT NOT NULL,
    version TEXT NOT NULL,
    lifecycle_state VARCHAR(20) DEFAULT 'draft' NOT NULL,
    content_hash TEXT NOT NULL,
    artifact_url TEXT,
    approved_by TEXT,
    approved_at TIMESTAMP WITH TIME ZONE,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (image_id),
    CONSTRAINT uq_golden_image UNIQUE (org_id, image_type, device_model, version),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id)
)""",
    """CREATE INDEX ix_golden_images_org_id ON golden_images (org_id)""",
    """CREATE TABLE incident_change_correlations (
    correlation_id UUID NOT NULL,
    org_id UUID NOT NULL,
    incident_type VARCHAR(30) NOT NULL,
    incident_id TEXT NOT NULL,
    incident_at TIMESTAMP WITH TIME ZONE NOT NULL,
    change_revision_id INTEGER,
    change_job_id UUID,
    confidence_score FLOAT NOT NULL,
    detection_method VARCHAR(20) NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (correlation_id),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id)
)""",
    """CREATE INDEX ix_incident_change_correlations_org_id
ON incident_change_correlations (org_id)""",
    """CREATE TABLE network_policies (
    policy_id UUID NOT NULL,
    org_id UUID NOT NULL,
    mist_entity_id UUID NOT NULL,
    policy_type VARCHAR(30) NOT NULL,
    name TEXT NOT NULL,
    lifecycle_state VARCHAR(20) DEFAULT 'active' NOT NULL,
    version INTEGER DEFAULT '1' NOT NULL,
    effective_from TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    dependencies JSONB,
    last_reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by TEXT,
    PRIMARY KEY (policy_id),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id)
)""",
    """CREATE INDEX ix_network_policies_org_id ON network_policies (org_id)""",
    """CREATE TABLE notification_channels (
    channel_id UUID NOT NULL,
    org_id UUID NOT NULL,
    channel_type VARCHAR(20) NOT NULL,
    name TEXT NOT NULL,
    destination TEXT NOT NULL,
    alert_subscriptions TEXT[] NOT NULL,
    enabled BOOLEAN DEFAULT 'true' NOT NULL,
    auth_config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (channel_id),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id)
)""",
    """CREATE INDEX ix_notification_channels_org_id ON notification_channels (org_id)""",
    """CREATE TABLE rollout_plans (
    plan_id UUID NOT NULL,
    org_id UUID NOT NULL,
    name TEXT NOT NULL,
    promotion_mode VARCHAR(20) DEFAULT 'manual' NOT NULL,
    health_gate_criteria JSONB NOT NULL,
    status VARCHAR(30) DEFAULT 'draft' NOT NULL,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (plan_id),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id)
)""",
    """CREATE INDEX ix_rollout_plans_org_id ON rollout_plans (org_id)""",
    """CREATE TABLE sites (
    site_id UUID NOT NULL,
    org_id UUID NOT NULL,
    name TEXT NOT NULL,
    address TEXT,
    location JSONB,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (site_id),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id)
)""",
    """CREATE INDEX ix_sites_org_id ON sites (org_id)""",
    """CREATE TABLE sync_ledger (
    id BIGSERIAL NOT NULL,
    org_id UUID NOT NULL,
    job_type VARCHAR(30) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'running' NOT NULL,
    rows_affected INTEGER,
    error_text TEXT,
    PRIMARY KEY (id),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id)
)""",
    """CREATE INDEX ix_sync_ledger_org_id ON sync_ledger (org_id)""",
    """CREATE TABLE webhook_envelopes (
    id BIGSERIAL NOT NULL,
    org_id UUID NOT NULL,
    event_id TEXT NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id),
    UNIQUE (event_id)
)""",
    """CREATE INDEX ix_webhook_envelopes_org_id ON webhook_envelopes (org_id)""",
    """CREATE TABLE devices (
    device_id UUID NOT NULL,
    org_id UUID NOT NULL,
    site_id UUID,
    name TEXT,
    serial TEXT NOT NULL,
    model TEXT NOT NULL,
    device_type VARCHAR(20) NOT NULL,
    firmware_version TEXT,
    status VARCHAR(20) DEFAULT 'unknown' NOT NULL,
    mac_address TEXT,
    ip_address TEXT,
    uptime INTEGER,
    last_seen_at TIMESTAMP WITH TIME ZONE,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (device_id),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id),
    FOREIGN KEY(site_id) REFERENCES sites (site_id),
    UNIQUE (serial)
)""",
    """CREATE INDEX ix_devices_org_id ON devices (org_id)""",
    """CREATE INDEX ix_devices_site_id ON devices (site_id)""",
    """CREATE TABLE rollout_waves (
    plan_id UUID NOT NULL,
    wave_number INTEGER NOT NULL,
    target_entities JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    health_check_result JSONB,
    PRIMARY KEY (plan_id, wave_number),
    FOREIGN KEY(plan_id) REFERENCES rollout_plans (plan_id)
)""",
    """CREATE TABLE scheduled_jobs (
    job_id UUID NOT NULL,
    org_id UUID NOT NULL,
    target_entities JSONB NOT NULL,
    change_payload JSONB NOT NULL,
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(30) DEFAULT 'pending' NOT NULL,
    pre_check_defs JSONB,
    post_check_defs JSONB,
    pre_check_result JSONB,
    post_check_result JSONB,
    created_by TEXT NOT NULL,
    approved_by TEXT,
    rollout_plan_id UUID,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (job_id),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id),
    FOREIGN KEY(rollout_plan_id) REFERENCES rollout_plans (plan_id)
)""",
    """CREATE INDEX ix_scheduled_jobs_org_id ON scheduled_jobs (org_id)""",
    """CREATE TABLE device_status_snapshots (
    snapshot_id BIGSERIAL NOT NULL,
    org_id UUID NOT NULL,
    device_id UUID NOT NULL,
    captured_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    status VARCHAR(20) NOT NULL,
    port_states JSONB,
    client_count INTEGER,
    health_metrics JSONB,
    PRIMARY KEY (snapshot_id, org_id),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id),
    FOREIGN KEY(device_id) REFERENCES devices (device_id)
)
 PARTITION BY LIST (org_id)""",
    """CREATE TABLE drift_alerts (
    alert_id UUID NOT NULL,
    org_id UUID NOT NULL,
    baseline_id UUID NOT NULL,
    device_id UUID NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    diff_payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'open' NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by TEXT,
    PRIMARY KEY (alert_id),
    FOREIGN KEY(org_id) REFERENCES orgs (org_id),
    FOREIGN KEY(baseline_id) REFERENCES baselines (baseline_id),
    FOREIGN KEY(device_id) REFERENCES devices (device_id)
)""",
    """CREATE INDEX ix_drift_alerts_org_id ON drift_alerts (org_id)""",
    """CREATE TABLE job_checkpoints (
    checkpoint_id BIGSERIAL NOT NULL,
    job_id UUID NOT NULL,
    entity_id UUID NOT NULL,
    step VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL,
    payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (checkpoint_id, job_id),
    FOREIGN KEY(job_id) REFERENCES scheduled_jobs (job_id)
)""",
)


def upgrade() -> None:
    """Drop the old schema and build the schema that the ORM models declare."""
    logger.info("Schema rebuild starts for %d tables.", len(CREATE_STATEMENTS))
    for table_name in DROP_TABLES:  # Clear both schemas, so no stale column survives.
        # WHY: CASCADE removes the hash partition children and the foreign keys too.
        op.execute(sa.text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
    for statement in CREATE_STATEMENTS:  # Build in dependency order, so each key resolves.
        op.execute(sa.text(statement))  # Send one frozen DDL statement to the database.
    logger.debug("Schema rebuild done for %d tables.", len(CREATE_STATEMENTS))


def downgrade() -> None:
    """Refuse the downgrade, because the old schema held no usable data."""
    logger.info("Downgrade request starts for revision %s.", revision)
    # WHY: a downgrade would restore a schema that no route can read. A clear stop
    # protects the operator better than a silent rebuild of a broken schema.
    raise NotImplementedError(
        "Revision 0003_align_schema_with_orm has no downgrade. "
        "The schema it replaced could not serve a request. "
        "Restore a database backup instead."
    )
