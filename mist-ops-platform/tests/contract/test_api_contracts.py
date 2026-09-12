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
        # This test sent org_id, status, last_sync_at, and next_sync_at. The schema
        # names its fields orgId, state, lastSyncAt, and nextPollAt, and it sets no
        # alias, so every one of those four names was wrong.
        resp = SyncStatusResponse(
            orgId=uuid.uuid4(),
            state="idle",
            lastSyncAt=datetime.now(tz=UTC),
            nextPollAt=None,
        )
        data = resp.model_dump()
        assert "orgId" in data
        assert "state" in data


class TestConfigContracts:
    """Verify config endpoint schemas."""

    def test_revision_response_fields(self) -> None:
        # This test sent org_id, config_blob, and config_hash. The schema carries
        # none of those three names. It requires content_hash, and it exposes
        # revision_id under the alias revision_number. The schema sets no
        # populate_by_name, so a caller must use the alias.
        resp = RevisionResponse(
            revision_number=1,
            entity_type="device",
            entity_id=uuid.uuid4(),
            content_hash="abc123",
            captured_at=datetime.now(tz=UTC),
            source="sync",
        )
        data = resp.model_dump()
        assert "revision_id" in data
        assert "content_hash" in data

    def test_diff_request_requires_two_revisions(self) -> None:
        # This test sent revision_a and revision_b. The schema requires org_id,
        # old_revision_id, and new_revision_id, and the revision keys are integers
        # rather than UUID strings.
        req = DiffRequest(
            org_id=uuid.uuid4(),
            old_revision_id=1,
            new_revision_id=2,
        )
        assert req.old_revision_id != req.new_revision_id

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
        # This test omitted scheduled_at. JobCreate requires it, because the deploy
        # route writes it straight to ScheduledJob.scheduled_at. JobUpdate is the
        # schema that makes the field optional, so the requirement is deliberate.
        job = JobCreate(
            org_id=uuid.uuid4(),
            change_payload={"radio": {"power": 12}},
            scheduled_at=datetime.now(tz=UTC),
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
        # This test sent name and device_ids to WaveCreate. The schema requires
        # wave_number and target_entities. device_ids does not exist, and a wave
        # targets an entity pair rather than a bare device identifier.
        wave = WaveCreate(
            wave_number=1,
            name="Wave 1",
            target_entities=[
                {"entity_type": "device", "entity_id": str(uuid.uuid4())},
            ],
        )
        rollout = RolloutCreate(
            org_id=uuid.uuid4(),
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
        # This test sent record_id as a UUID string and added org_id, action, and
        # details. record_id is an integer, because the audit_records table uses an
        # autoincrement key. The schema names the verb change_type, not action, and
        # it carries no org_id or details field.
        resp = AuditRecordResponse(
            record_id=1,
            entity_type="device",
            entity_id=uuid.uuid4(),
            change_type="config_push",
            actor="system",
            timestamp=datetime.now(tz=UTC),
        )
        data = resp.model_dump()
        assert "record_id" in data
        assert "change_type" in data
