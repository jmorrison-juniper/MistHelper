"""Unit tests for DatabaseRouter write / degraded-mode logic.

All database backends are mocked — no live services required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.db import DatabaseConfig, WriteResult


@pytest.fixture
def config() -> DatabaseConfig:
    return DatabaseConfig(
        arango_host="http://localhost:8529",
        redis_host="localhost",
    )


@pytest.fixture
def standalone_config() -> DatabaseConfig:
    return DatabaseConfig(standalone_mode=True)


@pytest.fixture
def strategies() -> dict:
    """Minimal ENDPOINT_PRIMARY_KEY_STRATEGIES for testing."""
    return {
        "listOrgSites": {
            "type": "natural_pk",
            "primary_key": ["id"],
        },
        "searchOrgDeviceEvents": {
            "type": "composite_pk",
            "primary_key": ["id", "device_id", "timestamp"],
        },
        "getOrgLicensesSummary": {
            "type": "auto_increment_with_unique",
            "primary_key": ["misthelper_internal_id"],
        },
        "default": {
            "type": "auto_increment_with_unique",
            "primary_key": ["misthelper_internal_id"],
        },
    }


@pytest.fixture
def mock_backends():
    """Patch all writer constructors so router doesn't need live DBs."""
    with (
        patch("src.db.router.ArangoDBWriter") as arango_cls,
        patch("src.db.router.RedisTimeSeriesWriter") as redis_cls,
        patch("src.db.router.RedisJSONWriter") as redis_json_cls,
    ):
        arango_writer = MagicMock()
        arango_cls.return_value = arango_writer
        redis_writer = MagicMock()
        redis_cls.return_value = redis_writer
        redis_json_writer = MagicMock()
        redis_json_cls.return_value = redis_json_writer
        yield {
            "arango_cls": arango_cls,
            "arango_writer": arango_writer,
            "redis_cls": redis_cls,
            "redis_writer": redis_writer,
            "redis_json_cls": redis_json_cls,
            "redis_json_writer": redis_json_writer,
        }


# Import must happen after patch is active for the constructor path
def _make_router(config, mock_backends, strategies):
    from src.db.router import DatabaseRouter

    return DatabaseRouter(config, strategies=strategies)


class TestRouterRouting:
    """Test that write() dispatches to the correct backend."""

    def test_natural_pk_routes_to_arango(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].write.return_value = WriteResult(
            success=True,
            backend="arangodb",
            records_written=3,
            records_failed=0,
        )
        data = [{"id": "site-1", "name": "HQ"}]
        result = router.write(data, "listOrgSites")

        mock_backends["arango_writer"].write.assert_called_once()
        assert result.backend == "arangodb"
        assert result.success is True

    def test_composite_pk_routes_to_dual(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["redis_json_writer"].write.return_value = WriteResult(
            success=True,
            backend="redis_json",
            records_written=1,
            records_failed=0,
        )
        mock_backends["arango_writer"].write.return_value = WriteResult(
            success=True,
            backend="arangodb",
            records_written=1,
            records_failed=0,
        )
        data = [{"id": "ev-1", "device_id": "d1", "timestamp": 170000, "cpu": 42}]
        result = router.write(data, "searchOrgDeviceEvents")

        mock_backends["redis_json_writer"].write.assert_called_once()
        mock_backends["arango_writer"].write.assert_called_once()
        assert result.backend == "dual"

    def test_auto_increment_routes_to_arango(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].write.return_value = WriteResult(
            success=True,
            backend="arangodb",
            records_written=1,
            records_failed=0,
        )
        data = [{"license_type": "SUB-MAN", "quantity": 100}]
        result = router.write(data, "getOrgLicensesSummary")

        mock_backends["arango_writer"].write.assert_called_once()
        assert result.backend == "arangodb"

    def test_unknown_function_uses_default_arango(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].write.return_value = WriteResult(
            success=True,
            backend="arangodb",
            records_written=1,
            records_failed=0,
        )
        result = router.write([{"x": 1}], "unknownEndpoint")
        assert result.backend == "arangodb"


class TestRouterDegradedMode:
    """Test graceful degradation when backends are unavailable."""

    def test_standalone_mode_returns_csv_only(self, standalone_config):
        from src.db.router import DatabaseRouter

        router = DatabaseRouter(standalone_config)
        result = router.write([{"id": "1"}], "listOrgSites")

        assert result.backend == "csv_only"
        assert result.success is True

    def test_arango_unavailable_returns_csv_only(self, config, mock_backends, strategies):
        mock_backends["arango_cls"].side_effect = Exception("Connection refused")
        from src.db.router import DatabaseRouter

        router = DatabaseRouter(config, strategies=strategies)
        result = router.write([{"id": "1", "name": "HQ"}], "listOrgSites")

        assert result.backend == "csv_only"

    def test_redis_unavailable_degrades_to_arango_only(self, config, mock_backends, strategies):
        mock_backends["redis_cls"].side_effect = Exception("Connection refused")
        mock_backends["redis_json_cls"].side_effect = Exception("Connection refused")
        from src.db.router import DatabaseRouter

        router = DatabaseRouter(config, strategies=strategies)
        mock_backends["arango_writer"].write.return_value = WriteResult(
            success=True,
            backend="arangodb",
            records_written=1,
            records_failed=0,
        )
        data = [{"id": "ev-1", "device_id": "d1", "timestamp": 170000, "cpu": 42}]
        result = router.write(data, "searchOrgDeviceEvents")

        # Dual write: redis_json falls back, arango still writes
        assert result.backend == "dual"
        mock_backends["arango_writer"].write.assert_called_once()

    def test_backend_write_failure_returns_error(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].write.side_effect = Exception("Write failed")
        result = router.write([{"id": "1"}], "listOrgSites")

        assert result.success is False
        assert "Write failed" in result.error_message


class TestRouterHealthCheck:
    """Test health_check returns correct status."""

    def test_all_backends_available(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        health = router.health_check()
        assert health["arangodb"] is True
        assert health["redis"] is True
        assert health["redis_json"] is True
        assert health["standalone"] is False

    def test_standalone_health(self, standalone_config):
        from src.db.router import DatabaseRouter

        router = DatabaseRouter(standalone_config)
        health = router.health_check()
        assert health["standalone"] is True


class TestRouterSnapshot:
    """Test config snapshot logic."""

    def test_snapshot_called_for_config_api(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].write.return_value = WriteResult(
            success=True,
            backend="arangodb",
            records_written=1,
            records_failed=0,
        )
        mock_backends["arango_writer"].snapshot.return_value = True
        data = [{"id": "site-1", "name": "HQ"}]
        router.write(data, "listOrgSites")
        mock_backends["arango_writer"].snapshot.assert_called_once()

    def test_snapshot_error_does_not_fail_write(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].write.return_value = WriteResult(
            success=True,
            backend="arangodb",
            records_written=1,
            records_failed=0,
        )
        mock_backends["arango_writer"].snapshot.side_effect = Exception("snap err")
        data = [{"id": "site-1", "name": "HQ"}]
        result = router.write(data, "listOrgSites")
        assert result.success is True


class TestRouterWebhook:
    """Test webhook audit handler."""

    def test_handle_webhook_audit(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].snapshot.return_value = True
        payload = {
            "object_type": "site",
            "object_id": "site-1",
            "after": {"name": "Updated Site"},
        }
        router.handle_webhook_audit(payload)
        mock_backends["arango_writer"].snapshot.assert_called_once()

    def test_webhook_with_no_arango(self, standalone_config):
        from src.db.router import DatabaseRouter

        router = DatabaseRouter(standalone_config)
        router.handle_webhook_audit({"object_type": "site", "object_id": "s1"})
        # Should not raise

    def test_webhook_missing_object_id(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        router.handle_webhook_audit({"object_type": "site"})
        mock_backends["arango_writer"].snapshot.assert_not_called()

    def test_webhook_snapshot_error_handled(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].snapshot.side_effect = Exception("err")
        payload = {"object_type": "site", "object_id": "s1", "after": {}}
        router.handle_webhook_audit(payload)  # should not raise


class TestRouterTimeseries:
    """Test timeseries_pk routing."""

    def test_timeseries_routes_to_redis(self, config, mock_backends):
        strategies = {
            "getDeviceStats": {
                "type": "timeseries_pk",
                "primary_key": ["mac", "timestamp"],
            },
        }
        router = _make_router(config, mock_backends, strategies)
        mock_backends["redis_writer"].write.return_value = WriteResult(
            success=True,
            backend="redis",
            records_written=2,
            records_failed=0,
        )
        data = [{"mac": "aa:bb", "timestamp": 170000, "cpu": 42}]
        result = router.write(data, "getDeviceStats")

        assert result.backend == "redis"
        mock_backends["redis_writer"].write.assert_called_once()

    def test_timeseries_redis_unavailable(self, config, mock_backends):
        strategies = {
            "getDeviceStats": {
                "type": "timeseries_pk",
                "primary_key": ["mac", "timestamp"],
            },
        }
        mock_backends["redis_cls"].side_effect = Exception("down")
        from src.db.router import DatabaseRouter

        router = DatabaseRouter(config, strategies=strategies)
        data = [{"mac": "aa:bb", "timestamp": 170000, "cpu": 42}]
        result = router.write(data, "getDeviceStats")

        assert result.backend == "csv_only"


class TestRouterIngestStatsBatch:
    """Test ingest_stats_batch for periodic stats."""

    def test_ingests_with_redis_available(self, config, mock_backends):
        strategies = {
            "getDeviceStats": {
                "type": "timeseries_pk",
                "primary_key": ["mac", "timestamp"],
            },
        }
        router = _make_router(config, mock_backends, strategies)
        mock_backends["redis_writer"].write.return_value = WriteResult(
            success=True,
            backend="redis",
            records_written=3,
            records_failed=0,
        )
        data = [{"mac": "aa:bb", "timestamp": 170000, "cpu": 42}]
        result = router.ingest_stats_batch(data, "getDeviceStats")

        assert result.backend == "redis"

    def test_degrades_when_redis_unavailable(self, config, mock_backends):
        mock_backends["redis_cls"].side_effect = Exception("down")
        from src.db.router import DatabaseRouter

        router = DatabaseRouter(config, strategies={})
        result = router.ingest_stats_batch([], "getDeviceStats")

        assert result.backend == "csv_only"


class TestRouterPullConfigHistory:
    """Test pull_config_history for device config snapshots."""

    def test_stores_config_snapshots(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].snapshot.return_value = True
        configs = [
            {"device_id": "dev-1", "config": {"ntp": "1.2.3.4"}},
            {"device_id": "dev-2", "config": {"ntp": "5.6.7.8"}},
        ]
        count = router.pull_config_history(configs)

        assert count == 2
        assert mock_backends["arango_writer"].snapshot.call_count == 2

    def test_skips_empty_entity_id(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        configs = [{"config": {"ntp": "1.2.3.4"}}]  # no device_id or mac
        count = router.pull_config_history(configs)

        assert count == 0
        mock_backends["arango_writer"].snapshot.assert_not_called()

    def test_handles_snapshot_error(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].snapshot.side_effect = Exception("err")
        configs = [{"device_id": "dev-1"}]
        count = router.pull_config_history(configs)

        assert count == 0

    def test_returns_zero_without_arango(self, standalone_config):
        from src.db.router import DatabaseRouter

        router = DatabaseRouter(standalone_config)
        count = router.pull_config_history([{"device_id": "d1"}])

        assert count == 0

    def test_mac_fallback(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].snapshot.return_value = True
        configs = [{"mac": "aa:bb:cc:dd:ee:ff"}]
        count = router.pull_config_history(configs)

        assert count == 1


class TestRouterClose:
    """Test close() cleanup."""

    def test_close_all_backends(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        router.close()

        mock_backends["arango_writer"].close.assert_called_once()
        mock_backends["redis_writer"].close.assert_called_once()

    def test_close_handles_errors(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].close.side_effect = Exception("err")
        mock_backends["redis_writer"].close.side_effect = Exception("err")
        router.close()  # should not raise

    def test_close_standalone(self, standalone_config):
        from src.db.router import DatabaseRouter

        router = DatabaseRouter(standalone_config)
        router.close()  # should not raise


class TestRouterRedisJsonError:
    """Test _write_redis_json exception handling."""

    def test_redis_json_write_exception(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["redis_json_writer"].write.side_effect = Exception("JSON err")
        mock_backends["arango_writer"].write.return_value = WriteResult(
            success=True,
            backend="arangodb",
            records_written=1,
            records_failed=0,
        )
        data = [{"id": "ev-1", "device_id": "d1", "timestamp": 170000}]
        result = router.write(data, "searchOrgDeviceEvents")

        # Dual write: redis_json fails but arango succeeds
        assert result.backend == "dual"


class TestRouterSnapshotEdgeCases:
    """Test _snapshot_if_config edge cases."""

    def test_snapshot_skips_non_config_api(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].write.return_value = WriteResult(
            success=True,
            backend="arangodb",
            records_written=1,
            records_failed=0,
        )
        data = [{"id": "lic-1"}]
        router.write(data, "getOrgLicensesSummary")
        mock_backends["arango_writer"].snapshot.assert_not_called()

    def test_snapshot_skips_empty_pk(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].write.return_value = WriteResult(
            success=True,
            backend="arangodb",
            records_written=1,
            records_failed=0,
        )
        data = [{"id": "", "name": "Empty ID"}]
        router.write(data, "listOrgSites")
        mock_backends["arango_writer"].snapshot.assert_not_called()

    def test_snapshot_skips_when_arango_none(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)

        def clear_writer(*_args, **_kwargs):
            router._arango_writer = None
            return WriteResult(success=True, backend="arangodb", records_written=1, records_failed=0)

        mock_backends["arango_writer"].write.side_effect = clear_writer
        data = [{"id": "site-1", "name": "HQ"}]
        result = router.write(data, "listOrgSites")
        assert result.success is True
        mock_backends["arango_writer"].snapshot.assert_not_called()


class TestRouterRedisWriteError:
    """Test _write_redis exception handling."""

    def test_redis_write_exception_returns_csv(self, config, mock_backends):
        strategies = {
            "getDeviceStats": {
                "type": "timeseries_pk",
                "primary_key": ["mac", "timestamp"],
            },
        }
        router = _make_router(config, mock_backends, strategies)
        mock_backends["redis_writer"].write.side_effect = Exception("TS write err")
        data = [{"mac": "aa:bb", "timestamp": 170000, "cpu": 42}]
        result = router.write(data, "getDeviceStats")

        assert result.success is False
        assert result.backend == "csv_only"
        assert "TS write err" in result.error_message
