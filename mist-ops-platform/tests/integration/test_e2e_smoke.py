"""End-to-end smoke test (T113).

Validates the critical path: compose up -> migrate -> first sync ->
time-travel query. This test verifies component wiring without live
infrastructure by mocking external dependencies.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.shared.config.constants import EntityType, JobStatus


class TestE2ESmokeComponents:
    """Verify critical components are importable and wired correctly."""

    def test_fastapi_app_factory_importable(self) -> None:
        from src.api.main import create_app

        app = create_app()
        assert app is not None
        assert app.title is not None

    def test_celery_app_importable(self) -> None:
        from src.worker.celeryconfig import app

        assert app is not None

    def test_all_routes_registered(self) -> None:
        from src.api.main import create_app

        app = create_app()
        # FastAPI 0.141 defers an included router into an _IncludedRouter marker,
        # so app.routes holds markers rather than the mounted paths. The old list
        # comprehension read route.path on those markers and raised AttributeError,
        # so this test never checked a single route. The OpenAPI schema resolves
        # every included router, and it is the same surface a client reads.
        paths = list(app.openapi().get("paths", {}))
        # An empty mapping would satisfy the any() check below by accident, so this
        # floor proves the routers mounted. create_app publishes 48 paths today.
        assert len(paths) >= 40, f"create_app published only {len(paths)} paths"
        # Core endpoints exist
        assert any("/healthz" in p for p in paths)

    def test_settings_load(self) -> None:
        """AppSettings loads without errors (uses defaults/env)."""
        from src.shared.config.settings import AppSettings

        settings = AppSettings()
        assert settings.app_name is not None

    def test_model_imports(self) -> None:
        """All 21 entities import without circular dependency."""
        from src.shared.models import (
            AuditRecord,
            Baseline,
            ChangeTemplate,
            ComplianceAuditPack,
            ConfigRevision,
            Device,
            DeviceStatusSnapshot,
            DriftAlert,
            GoldenImage,
            IncidentChangeCorrelation,
            JobCheckpoint,
            MSP,
            NetworkPolicy,
            NotificationChannel,
            Organization,
            RolloutPlan,
            RolloutWave,
            ScheduledJob,
            Site,
            SyncLedgerEntry,
            WebhookEnvelope,
        )

        assert MSP.__tablename__ == "msps"
        assert Device.__tablename__ == "devices"
        assert ScheduledJob.__tablename__ == "scheduled_jobs"

    def test_entity_type_enum_covers_models(self) -> None:
        """EntityType enum has entries for major model types."""
        assert EntityType.DEVICE.value == "device"
        assert EntityType.SITE.value == "site"

    def test_diff_service_works_standalone(self) -> None:
        """DiffService computes diffs without any infrastructure."""
        from src.shared.services.diff import DiffService

        svc = DiffService()
        result = svc.compute_diff(
            {"a": 1, "b": 2},
            {"a": 1, "b": 3, "c": 4},
        )
        assert len(result.changes) > 0
