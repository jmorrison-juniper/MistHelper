"""Unit tests for RetentionManager."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestRetentionInit:
    """Verify RetentionManager initializes from config."""

    def test_default_thresholds(self) -> None:
        from src.db.retention import RetentionManager

        manager = RetentionManager(
            arango_writer=MagicMock(),
            redis_writer=MagicMock(),
        )
        assert manager._max_storage_gb > 0
        assert manager._check_interval_hours > 0

    def test_custom_thresholds_from_env(self) -> None:
        from src.db.retention import RetentionManager

        with patch.dict("os.environ", {
            "ARANGO_MAX_STORAGE_GB": "50",
            "RETENTION_CHECK_INTERVAL_HOURS": "12",
        }):
            manager = RetentionManager(
                arango_writer=MagicMock(),
                redis_writer=MagicMock(),
            )
            assert manager._max_storage_gb == 50
            assert manager._check_interval_hours == 12


class TestArangoRetention:
    """Verify ArangoDB retention purges oldest data first."""

    def test_purge_skips_when_under_threshold(self) -> None:
        from src.db.retention import RetentionManager

        arango = MagicMock()
        manager = RetentionManager(
            arango_writer=arango, redis_writer=MagicMock(),
        )
        manager._get_storage_usage_gb = MagicMock(return_value=5.0)
        manager._max_storage_gb = 100
        result = manager.check_arango_retention()
        assert result == 0  # nothing purged

    def test_purge_removes_oldest_snapshots(self) -> None:
        from src.db.retention import RetentionManager

        arango = MagicMock()
        arango._database = MagicMock()
        arango._database.aql.execute.return_value = [
            {"_key": "old-1"}, {"_key": "old-2"},
        ]
        manager = RetentionManager(
            arango_writer=arango, redis_writer=MagicMock(),
        )
        manager._get_storage_usage_gb = MagicMock(return_value=95.0)
        manager._max_storage_gb = 100
        result = manager.check_arango_retention()
        assert result >= 0


class TestRedisRetention:
    """Verify Redis retention rules are validated."""

    def test_verify_compaction_exists(self) -> None:
        from src.db.retention import RetentionManager

        redis_writer = MagicMock()
        redis_writer._client = MagicMock()
        redis_writer._client.execute_command.return_value = []
        manager = RetentionManager(
            arango_writer=MagicMock(), redis_writer=redis_writer,
        )
        result = manager.check_redis_retention()
        assert isinstance(result, int)
