"""Contract tests validating API endpoints match contracts/*.md schemas (T112).

These tests import Pydantic schemas used by API routes and verify they
serialize/deserialize correctly against the contract specifications.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from src.api.schemas.common import ErrorDetail, PaginationMeta, ResponseEnvelope

# Issue #1895: this module imported InventoryStatsResponse, and that name does not
# exist in src.api.schemas.sync. The dead import raised an ImportError and stopped
# pytest from collecting the whole contract module. No test used the name.
from src.api.schemas.sync import (
    SyncStatusResponse,
    SyncTriggerRequest,
)
from src.api.schemas.config import (
    DiffRequest,
    RevisionResponse,
    TimeTravelRequest,
)
from src.api.schemas.deploy import (
    DryRunRequest,
    JobCreate,
    JobSummary,
    RolloutCreate,
    WaveCreate,
)
from src.api.schemas.audit import (
    AuditRecordResponse,
    ExportRequest,
)


class TestCommonSchemas:
    """Verify common response envelope contracts."""

    def test_error_detail_serializes(self) -> None:
        err = ErrorDetail(code="NOT_FOUND", message="Item not found")
        data = err.model_dump()
        assert data["code"] == "NOT_FOUND"

    def test_pagination_meta(self) -> None:
        meta = PaginationMeta(page=1, per_page=50, total=200)
        data = meta.model_dump()
        assert data["page"] == 1
        assert data["total"] == 200

    def test_response_envelope_wraps_data(self) -> None:
        envelope = ResponseEnvelope[str](data="hello")
        data = envelope.model_dump()
        assert data["data"] == "hello"


class TestSyncContracts:
    """Verify sync endpoint request/response schemas."""

    def test_sync_trigger_request(self) -> None:
        req = SyncTriggerRequest(org_id=str(uuid.uuid4()))
        assert req.org_id is not None

    def test_sync_status_response_fields(self) -> None:
        resp = SyncStatusResponse(
            org_id=str(uuid.uuid4()),
            status="idle",
            last_sync_at=datetime.now(tz=UTC),
            next_sync_at=None,
        )
        data = resp.model_dump()
        assert "org_id" in data
        assert "status" in data


class TestConfigContracts:
    """Verify config endpoint schemas."""

    def test_revision_response_fields(self) -> None:
        resp = RevisionResponse(
            revision_id=str(uuid.uuid4()),
            entity_type="device",
            entity_id=str(uuid.uuid4()),
            org_id=str(uuid.uuid4()),
            config_blob={"radio": {"power": 10}},
            config_hash="abc123",
            captured_at=datetime.now(tz=UTC),
            source="sync",
        )
        data = resp.model_dump()
        assert "revision_id" in data
        assert "config_blob" in data

    def test_diff_request_requires_two_revisions(self) -> None:
        req = DiffRequest(
            revision_a=str(uuid.uuid4()),
            revision_b=str(uuid.uuid4()),
        )
        assert req.revision_a != req.revision_b

    def test_time_travel_request(self) -> None:
        req = TimeTravelRequest(
            org_id=str(uuid.uuid4()),
            entity_id=str(uuid.uuid4()),
            entity_type="device",
            timestamp=datetime.now(tz=UTC),
        )
        assert req.entity_type == "device"


class TestDeployContracts:
    """Verify deploy endpoint schemas."""

    def test_job_create_payload(self) -> None:
        job = JobCreate(
            org_id=str(uuid.uuid4()),
            change_payload={"radio": {"power": 12}},
            target_entities=[
                {"entity_type": "device", "entity_id": str(uuid.uuid4())},
            ],
        )
        data = job.model_dump()
        assert "change_payload" in data
        assert len(data["target_entities"]) == 1

    def test_dry_run_request(self) -> None:
        req = DryRunRequest(
            org_id=str(uuid.uuid4()),
            change_payload={"radio": {"power": 14}},
            target_entities=[
                {"entity_type": "device", "entity_id": str(uuid.uuid4())},
            ],
        )
        assert req.change_payload is not None

    def test_rollout_create_has_waves(self) -> None:
        wave = WaveCreate(
            name="Wave 1",
            device_ids=[str(uuid.uuid4())],
        )
        rollout = RolloutCreate(
            org_id=str(uuid.uuid4()),
            name="Firmware v1.2",
            waves=[wave],
        )
        assert len(rollout.waves) == 1


class TestAuditContracts:
    """Verify audit endpoint schemas."""

    def test_export_request(self) -> None:
        req = ExportRequest(
            org_id=str(uuid.uuid4()),
            format="csv",
        )
        assert req.format in ("csv", "json")

    def test_audit_record_response(self) -> None:
        resp = AuditRecordResponse(
            record_id=str(uuid.uuid4()),
            org_id=str(uuid.uuid4()),
            entity_type="device",
            entity_id=str(uuid.uuid4()),
            action="config_push",
            actor="system",
            timestamp=datetime.now(tz=UTC),
            details={},
        )
        data = resp.model_dump()
        assert "record_id" in data
        assert "action" in data
