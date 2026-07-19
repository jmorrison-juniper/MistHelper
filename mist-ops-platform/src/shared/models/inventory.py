"""Inventory models: MSP, Org, Site, Device, SyncLedgerEntry (E-00 to E-03, E-19)."""

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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.models.base import Base, TimestampMixin


# ---------------------------------------------------------------------------
# E-00: MSP (Managed Service Provider)
# ---------------------------------------------------------------------------
class MSP(Base, TimestampMixin):
    """Top-level MSP tenant discovered from Mist API self endpoint."""

    __tablename__ = "msps"

    msp_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    api_host: Mapped[str] = mapped_column(Text, nullable=False)
    auth_method: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="session",
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sync_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    # relationships
    organizations: Mapped[list[Organization]] = relationship(
        back_populates="msp",
        lazy="selectin",
    )


# ---------------------------------------------------------------------------
# E-01: Organization
# ---------------------------------------------------------------------------
class Organization(Base, TimestampMixin):
    """Mist organization — primary tenant boundary."""

    __tablename__ = "orgs"

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )
    msp_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("msps.msp_id"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    api_host: Mapped[str] = mapped_column(Text, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sync_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
    )

    # relationships
    msp: Mapped[MSP | None] = relationship(back_populates="organizations")
    sites: Mapped[list[Site]] = relationship(
        back_populates="organization",
        lazy="selectin",
    )


# ---------------------------------------------------------------------------
# E-02: Site
# ---------------------------------------------------------------------------
class Site(Base, TimestampMixin):
    """Mist site — logical grouping of devices at a location."""

    __tablename__ = "sites"

    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # relationships
    organization: Mapped[Organization] = relationship(
        back_populates="sites",
    )
    devices: Mapped[list[Device]] = relationship(
        back_populates="site",
        lazy="selectin",
    )


# ---------------------------------------------------------------------------
# E-03: Device
# ---------------------------------------------------------------------------
class Device(Base, TimestampMixin):
    """Mist device — AP, switch, or gateway."""

    __tablename__ = "devices"

    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        nullable=False,
        index=True,
    )
    site_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sites.site_id"),
        nullable=True,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    serial: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )
    model: Mapped[str] = mapped_column(Text, nullable=False)
    device_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    firmware_version: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="unknown",
    )
    mac_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    uptime: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # relationships
    site: Mapped[Site | None] = relationship(back_populates="devices")


# ---------------------------------------------------------------------------
# E-19: SyncLedgerEntry
# ---------------------------------------------------------------------------
class SyncLedgerEntry(Base):
    """Internal bookkeeping for sync job runs."""

    __tablename__ = "sync_ledger"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orgs.org_id"),
        nullable=False,
        index=True,
    )
    job_type: Mapped[str] = mapped_column(String(30), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="running",
    )
    rows_affected: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    error_text: Mapped[str | None] = mapped_column(Text, nullable=True)
