"""Unit tests for inventory models (E-00 through E-03) and db.py (T105)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.shared.config.constants import DeviceType
from src.shared.models.inventory import (
    MSP,
    Device,
    Organization,
    Site,
    SyncLedgerEntry,
)


# ---------------------------------------------------------------------------
# E-00: MSP
# ---------------------------------------------------------------------------
class TestMSP:
    """Verify MSP entity attributes and tablename."""

    def test_tablename(self) -> None:
        assert MSP.__tablename__ == "msps"

    def test_primary_key_is_msp_id(self) -> None:
        cols = {c.name for c in MSP.__table__.primary_key.columns}
        assert cols == {"msp_id"}

    def test_required_columns(self) -> None:
        col_names = {c.name for c in MSP.__table__.columns}
        for expected in ("msp_id", "name", "api_host", "auth_method"):
            assert expected in col_names, f"Missing column: {expected}"


# ---------------------------------------------------------------------------
# E-01: Organization
# ---------------------------------------------------------------------------
class TestOrganization:
    """Verify Organization entity."""

    def test_tablename(self) -> None:
        # Issue #1883: this test asserted "organizations", which is the name that
        # migration 0001 used. Every route and worker reads the ORM name "orgs",
        # so the ORM name wins. Migration 0003 now builds "orgs".
        assert Organization.__tablename__ == "orgs"

    def test_primary_key(self) -> None:
        cols = {c.name for c in Organization.__table__.primary_key.columns}
        assert cols == {"org_id"}

    def test_has_msp_fk(self) -> None:
        fk_cols = {fk.parent.name for fk in Organization.__table__.foreign_keys}
        assert "msp_id" in fk_cols


# ---------------------------------------------------------------------------
# E-02: Site
# ---------------------------------------------------------------------------
class TestSite:
    """Verify Site entity."""

    def test_tablename(self) -> None:
        assert Site.__tablename__ == "sites"

    def test_primary_key(self) -> None:
        cols = {c.name for c in Site.__table__.primary_key.columns}
        assert cols == {"site_id"}


# ---------------------------------------------------------------------------
# E-03: Device
# ---------------------------------------------------------------------------
class TestDevice:
    """Verify Device entity."""

    def test_tablename(self) -> None:
        assert Device.__tablename__ == "devices"

    def test_primary_key(self) -> None:
        cols = {c.name for c in Device.__table__.primary_key.columns}
        assert cols == {"device_id"}

    def test_device_type_column_exists(self) -> None:
        col_names = {c.name for c in Device.__table__.columns}
        assert "device_type" in col_names


# ---------------------------------------------------------------------------
# E-19: SyncLedgerEntry
# ---------------------------------------------------------------------------
class TestSyncLedgerEntry:
    """Verify SyncLedgerEntry entity."""

    def test_tablename(self) -> None:
        # Issue #1883: this test asserted "sync_ledger_entries", which is the name
        # that migration 0001 used. The ORM names the table "sync_ledger", and the
        # ORM is the schema owner. Migration 0003 now builds "sync_ledger".
        assert SyncLedgerEntry.__tablename__ == "sync_ledger"

    def test_primary_key(self) -> None:
        cols = {c.name for c in SyncLedgerEntry.__table__.primary_key.columns}
        # This test asserted "ledger_id". No such column exists. The ORM names the
        # key "id", and migration 0001 creates sync_ledger_entries with a BigInteger
        # column named "id" as well. Both sides agree, so the expectation was wrong.
        assert cols == {"id"}


# ---------------------------------------------------------------------------
# db.py — engine factory
# ---------------------------------------------------------------------------
class TestDBFactory:
    """Verify async engine factory creates engine with expected URL."""

    @patch("src.shared.db.create_async_engine")
    def test_build_engine_uses_settings_url(
        self,
        mock_create: MagicMock,
    ) -> None:
        from src.shared.db import build_engine

        mock_settings = MagicMock()
        mock_settings.database_url = "postgresql+asyncpg://u:p@host/db"
        mock_create.return_value = MagicMock()

        engine = build_engine(mock_settings)

        mock_create.assert_called_once()
        call_url = mock_create.call_args[0][0]
        assert "postgresql" in call_url
        # WHY: the factory must hand back the engine that create_async_engine
        # built. Without this assertion the test passes even when the factory
        # returns None, so the caller would fail later with no cause.
        assert engine is mock_create.return_value
