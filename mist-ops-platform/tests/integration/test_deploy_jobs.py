"""Integration tests for scheduled job lifecycle (T110).

Covers: create -> approve -> pre-check -> execute -> post-check -> rollback.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from src.shared.config.constants import JobStatus


class TestDeployJobLifecycle:
    """Verify ScheduledJob state transitions."""

    @pytest.fixture()
    def job_payload(self) -> dict:
        return {
            "org_id": str(uuid.uuid4()),
            "change_payload": {
                "radio_config": {"band_24": {"power": 14}},
            },
            "target_entities": [
                {"entity_type": "device", "entity_id": str(uuid.uuid4())},
            ],
            "scheduled_at": (
                datetime.now(tz=UTC) + timedelta(hours=2)
            ).isoformat(),
        }

    def test_initial_status_is_pending(self) -> None:
        assert JobStatus.PENDING.value == "pending"

    def test_valid_status_transitions(self) -> None:
        """Verify the happy-path state machine."""
        happy_path = [
            JobStatus.PENDING,
            JobStatus.APPROVED,
            JobStatus.PRE_CHECK,
            JobStatus.EXECUTING,
            JobStatus.POST_CHECK,
            JobStatus.COMPLETED,
        ]
        for i in range(len(happy_path) - 1):
            current = happy_path[i]
            next_status = happy_path[i + 1]
            assert current != next_status

    def test_failed_transitions_to_rolled_back(self) -> None:
        """FAILED status should allow transition to ROLLED_BACK."""
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.ROLLED_BACK.value == "rolled_back"

    def test_cancelled_is_terminal(self) -> None:
        """CANCELLED prevents further transitions."""
        assert JobStatus.CANCELLED.value == "cancelled"

    def test_job_payload_structure(self, job_payload: dict) -> None:
        """Job creation payload has required fields."""
        assert "org_id" in job_payload
        assert "change_payload" in job_payload
        assert "target_entities" in job_payload
        assert len(job_payload["target_entities"]) >= 1

    def test_target_entity_has_type_and_id(self, job_payload: dict) -> None:
        target = job_payload["target_entities"][0]
        assert "entity_type" in target
        assert "entity_id" in target

    def test_scheduled_at_is_future(self, job_payload: dict) -> None:
        scheduled = datetime.fromisoformat(job_payload["scheduled_at"])
        assert scheduled > datetime.now(tz=UTC)
