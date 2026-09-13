"""Add uptime and last_seen_at columns to devices table.

Revision ID: 0002_add_device_uptime_last_seen
Revises: 0001_initial
Create Date: 2025-07-19

Adds uptime (integer) and last_seen_at (timestamptz) so the
DeviceDetailPage can display live values instead of 'Unknown'/'Never'.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_device_uptime_last_seen"
down_revision: str = "0001_initial"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.add_column(
        "devices",
        sa.Column("uptime", sa.Integer(), nullable=True),
    )
    op.add_column(
        "devices",
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("devices", "last_seen_at")
    op.drop_column("devices", "uptime")
