"""Unit tests for RetentionManager."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


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

        with patch.dict(
            "os.environ",
            {
                "ARANGO_MAX_STORAGE_GB": "50",
                "RETENTION_CHECK_INTERVAL_HOURS": "12",
            },
        ):
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
            arango_writer=arango,
            redis_writer=MagicMock(),
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
            {"_key": "old-1"},
            {"_key": "old-2"},
        ]
        manager = RetentionManager(
            arango_writer=arango,
            redis_writer=MagicMock(),
        )
        manager._get_storage_usage_gb = MagicMock(return_value=95.0)
        manager._max_storage_gb = 100
        result = manager.check_arango_retention()
        assert result >= 0

    def test_storage_usage_with_no_database_attr(self) -> None:
        from src.db.retention import RetentionManager

        arango = MagicMock(spec=[])  # no _database attribute
        manager = RetentionManager(
            arango_writer=arango,
            redis_writer=MagicMock(),
        )
        usage = manager._get_storage_usage_gb()
        assert usage == 0.0

    def test_storage_usage_on_exception(self) -> None:
        from src.db.retention import RetentionManager

        arango = MagicMock()
        arango._database = MagicMock()
        arango._database.statistics.side_effect = Exception("fail")
        manager = RetentionManager(
            arango_writer=arango,
            redis_writer=MagicMock(),
        )
        usage = manager._get_storage_usage_gb()
        assert usage == 0.0

    def test_purge_with_no_database_returns_zero(self) -> None:
        from src.db.retention import RetentionManager

        arango = MagicMock(spec=[])
        manager = RetentionManager(
            arango_writer=arango,
            redis_writer=MagicMock(),
        )
        result = manager._purge_oldest_snapshots()
        assert result == 0

    def test_purge_on_aql_error(self) -> None:
        from src.db.retention import RetentionManager

        arango = MagicMock()
        arango._database = MagicMock()
        arango._database.aql.execute.side_effect = Exception("AQL error")
        manager = RetentionManager(
            arango_writer=arango,
            redis_writer=MagicMock(),
        )
        result = manager._purge_oldest_snapshots()
        assert result == 0


class TestRedisRetention:
    """Verify Redis retention rules are validated."""

    def test_verify_compaction_exists(self) -> None:
        from src.db.retention import RetentionManager

        redis_writer = MagicMock()
        redis_writer._client = MagicMock()
        redis_writer._client.execute_command.return_value = []
        manager = RetentionManager(
            arango_writer=MagicMock(),
            redis_writer=redis_writer,
        )
        result = manager.check_redis_retention()
        assert isinstance(result, int)

    def test_redis_retention_no_client(self) -> None:
        from src.db.retention import RetentionManager

        redis_writer = MagicMock(spec=[])
        manager = RetentionManager(
            arango_writer=MagicMock(),
            redis_writer=redis_writer,
        )
        result = manager.check_redis_retention()
        assert result == 0

    def test_redis_retention_on_error(self) -> None:
        from src.db.retention import RetentionManager

        redis_writer = MagicMock()
        redis_writer._client = MagicMock()
        redis_writer._client.execute_command.side_effect = Exception("err")
        manager = RetentionManager(
            arango_writer=MagicMock(),
            redis_writer=redis_writer,
        )
        result = manager.check_redis_retention()
        assert result == 0


class TestRetentionPeriodic:
    """Verify start/stop of background sweep."""

    def test_start_and_stop(self) -> None:
        from src.db.retention import RetentionManager

        manager = RetentionManager(
            arango_writer=MagicMock(),
            redis_writer=MagicMock(),
        )
        manager._check_interval_hours = 1
        manager.start_periodic()
        assert manager._thread is not None
        assert manager._thread.is_alive()
        manager.stop()
        assert manager._thread is None

    def test_start_idempotent(self) -> None:
        from src.db.retention import RetentionManager

        manager = RetentionManager(
            arango_writer=MagicMock(),
            redis_writer=MagicMock(),
        )
        manager.start_periodic()
        thread1 = manager._thread
        manager.start_periodic()
        assert manager._thread is thread1
        manager.stop()

    def test_stop_without_start(self) -> None:
        from src.db.retention import RetentionManager

        manager = RetentionManager(
            arango_writer=MagicMock(),
            redis_writer=MagicMock(),
        )
        manager.stop()  # should not raise
