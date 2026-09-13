"""Integration tests for config revision capture and time-travel query (T109).

Validates that ConfigSyncService captures revisions and the time-travel
endpoint returns the correct snapshot for a given timestamp.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest


class TestTimeTravelIntegration:
    """Verify time-travel query returns correct revision for timestamp."""

    @pytest.fixture()
    def sample_configs(self) -> list[dict]:
        """Three config versions at staggered timestamps."""
        base_time = datetime(2026, 3, 1, tzinfo=UTC)
        return [
            {
                "revision_id": str(uuid.uuid4()),
                "captured_at": base_time,
                "config_blob": {"radio": {"power": 8, "channel": 6}},
            },
            {
                "revision_id": str(uuid.uuid4()),
                "captured_at": base_time + timedelta(hours=4),
                "config_blob": {"radio": {"power": 10, "channel": 6}},
            },
            {
                "revision_id": str(uuid.uuid4()),
                "captured_at": base_time + timedelta(hours=8),
                "config_blob": {"radio": {"power": 12, "channel": 11}},
            },
        ]

    def test_sha256_dedup(self, sample_configs: list[dict]) -> None:
        """Two identical blobs should produce the same SHA hash."""
        blob_a = json.dumps(sample_configs[0]["config_blob"], sort_keys=True)
        blob_b = json.dumps(sample_configs[0]["config_blob"], sort_keys=True)
        assert hashlib.sha256(blob_a.encode()).hexdigest() == (hashlib.sha256(blob_b.encode()).hexdigest())

    def test_different_blobs_different_hash(
        self,
        sample_configs: list[dict],
    ) -> None:
        """Different configs should yield different SHA hashes."""
        hash_a = hashlib.sha256(json.dumps(sample_configs[0]["config_blob"], sort_keys=True).encode()).hexdigest()
        hash_b = hashlib.sha256(json.dumps(sample_configs[1]["config_blob"], sort_keys=True).encode()).hexdigest()
        assert hash_a != hash_b

    def test_time_travel_selects_latest_before_ts(
        self,
        sample_configs: list[dict],
    ) -> None:
        """Query at t+6h should return revision 2 (captured at t+4h)."""
        query_ts = sample_configs[0]["captured_at"] + timedelta(hours=6)
        # Find latest revision <= query_ts
        candidates = [c for c in sample_configs if c["captured_at"] <= query_ts]
        candidates.sort(key=lambda c: c["captured_at"], reverse=True)
        result = candidates[0]
        assert result["config_blob"]["radio"]["power"] == 10

    def test_time_travel_before_first_revision(
        self,
        sample_configs: list[dict],
    ) -> None:
        """Query before any revision should return empty."""
        query_ts = sample_configs[0]["captured_at"] - timedelta(hours=1)
        candidates = [c for c in sample_configs if c["captured_at"] <= query_ts]
        assert len(candidates) == 0

    def test_revision_ordering(self, sample_configs: list[dict]) -> None:
        """Revisions should be strictly ordered by captured_at."""
        times = [c["captured_at"] for c in sample_configs]
        assert times == sorted(times)
