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
    """Patch both writer constructors so router doesn't need live DBs."""
    with (
        patch("src.db.router.ArangoDBWriter") as arango_cls,
        patch("src.db.router.RedisTimeSeriesWriter") as redis_cls,
    ):
        arango_writer = MagicMock()
        arango_cls.return_value = arango_writer
        redis_writer = MagicMock()
        redis_cls.return_value = redis_writer
        yield {
            "arango_cls": arango_cls,
            "arango_writer": arango_writer,
            "redis_cls": redis_cls,
            "redis_writer": redis_writer,
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
            success=True, backend="arangodb",
            records_written=3, records_failed=0,
        )
        data = [{"id": "site-1", "name": "HQ"}]
        result = router.write(data, "listOrgSites")

        mock_backends["arango_writer"].write.assert_called_once()
        assert result.backend == "arangodb"
        assert result.success is True

    def test_composite_pk_routes_to_redis(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["redis_writer"].write.return_value = WriteResult(
            success=True, backend="redis",
            records_written=5, records_failed=0,
        )
        data = [{"id": "ev-1", "device_id": "d1", "timestamp": 170000, "cpu": 42}]
        result = router.write(data, "searchOrgDeviceEvents")

        mock_backends["redis_writer"].write.assert_called_once()
        assert result.backend == "redis"

    def test_auto_increment_routes_to_arango(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].write.return_value = WriteResult(
            success=True, backend="arangodb",
            records_written=1, records_failed=0,
        )
        data = [{"license_type": "SUB-MAN", "quantity": 100}]
        result = router.write(data, "getOrgLicensesSummary")

        mock_backends["arango_writer"].write.assert_called_once()
        assert result.backend == "arangodb"

    def test_unknown_function_uses_default_arango(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].write.return_value = WriteResult(
            success=True, backend="arangodb",
            records_written=1, records_failed=0,
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

    def test_redis_unavailable_returns_csv_only(self, config, mock_backends, strategies):
        mock_backends["redis_cls"].side_effect = Exception("Connection refused")
        from src.db.router import DatabaseRouter

        router = DatabaseRouter(config, strategies=strategies)
        data = [{"id": "ev-1", "device_id": "d1", "timestamp": 170000, "cpu": 42}]
        result = router.write(data, "searchOrgDeviceEvents")

        assert result.backend == "csv_only"

    def test_backend_write_failure_returns_error(self, config, mock_backends, strategies):
        router = _make_router(config, mock_backends, strategies)
        mock_backends["arango_writer"].write.side_effect = Exception("Write failed")
        result = router.write([{"id": "1"}], "listOrgSites")

        assert result.success is False
        assert "Write failed" in result.error_message
