"""Unit tests for RedisJSONWriter.

All redis interactions are mocked -- no live Redis required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.db import DatabaseConfig


@pytest.fixture
def config() -> DatabaseConfig:
    return DatabaseConfig(
        redis_host="localhost",
        redis_port=6379,
        redis_password="test",
    )


@pytest.fixture
def mock_redis():
    """Patch redis.Redis and return mock objects."""
    with patch("src.db.redis_writer.redis.Redis") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.module_list.return_value = [{"name": b"ReJSON", "ver": 20600}]
        mock_pipeline = MagicMock()
        mock_client.pipeline.return_value = mock_pipeline
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        yield {
            "client_cls": mock_cls,
            "client": mock_client,
            "pipeline": mock_pipeline,
        }


class TestRedisJSONWriterInit:
    """Tests for RedisJSONWriter.__init__."""

    def test_connects_and_verifies_json_module(self, config, mock_redis):
        from src.db.redis_writer import RedisJSONWriter

        writer = RedisJSONWriter(config)
        mock_redis["client_cls"].assert_called_once()
        mock_redis["client"].module_list.assert_called_once()
        assert writer is not None

    def test_raises_if_json_module_missing(self, config, mock_redis):
        from src.db.redis_writer import RedisJSONWriter

        mock_redis["client"].module_list.return_value = []
        with pytest.raises(RuntimeError, match="JSON"):
            RedisJSONWriter(config)


class TestRedisJSONWriterWrite:
    """Tests for RedisJSONWriter.write."""

    def test_writes_documents_with_ttl(self, config, mock_redis):
        from src.db.redis_writer import RedisJSONWriter

        writer = RedisJSONWriter(config)
        # json().set() + expire() per record, pipeline.execute returns pairs
        mock_redis["pipeline"].execute.return_value = [True, True]
        strategy = {
            "type": "composite_pk",
            "primary_key": ["id", "device_id"],
        }
        data = [{"id": "ev-1", "device_id": "d1", "cpu": 42}]
        result = writer.write(data, "searchOrgDeviceEvents", strategy)

        assert result.success is True
        assert result.backend == "redis_json"
        assert result.records_written == 1

    def test_empty_data_returns_success(self, config, mock_redis):
        from src.db.redis_writer import RedisJSONWriter

        writer = RedisJSONWriter(config)
        strategy = {"type": "composite_pk", "primary_key": ["id"]}
        result = writer.write([], "getStats", strategy)

        assert result.success is True
        assert result.records_written == 0

    def test_handles_write_error(self, config, mock_redis):
        from src.db.redis_writer import RedisJSONWriter

        writer = RedisJSONWriter(config)
        mock_redis["pipeline"].execute.return_value = [
            Exception("Connection lost"),
            True,
        ]
        strategy = {"type": "composite_pk", "primary_key": ["id"]}
        data = [{"id": "ev-1", "value": 42}]
        result = writer.write(data, "getStats", strategy)

        assert result.records_failed == 1

    def test_close(self, config, mock_redis):
        from src.db.redis_writer import RedisJSONWriter

        writer = RedisJSONWriter(config)
        writer.close()
        mock_redis["client"].close.assert_called_once()


class TestRedisTimeSeriesClose:
    """Test close method for RedisTimeSeriesWriter."""

    def test_close(self, config):
        with patch("src.db.redis_writer.redis.Redis") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.module_list.return_value = [{"name": b"timeseries", "ver": 11006}]
            from src.db.redis_writer import RedisTimeSeriesWriter

            writer = RedisTimeSeriesWriter(config)
            writer.close()
            mock_client.close.assert_called_once()


class TestRedisTimeSeriesWebhookIngestion:
    """Tests for ingest_webhook method."""

    def test_ingests_numeric_fields(self, config):
        with patch("src.db.redis_writer.redis.Redis") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.module_list.return_value = [{"name": b"timeseries", "ver": 11006}]
            mock_pipeline = MagicMock()
            mock_client.pipeline.return_value = mock_pipeline
            from src.db.redis_writer import RedisTimeSeriesWriter

            writer = RedisTimeSeriesWriter(config)
            events = [{"mac": "aa:bb:cc:dd:ee:ff", "rssi": -65, "snr": 30}]
            result = writer.ingest_webhook(events, "client-sessions")
            assert result == 2  # rssi and snr
            mock_pipeline.execute.assert_called_once()

    def test_no_numeric_fields_skips_execute(self, config):
        with patch("src.db.redis_writer.redis.Redis") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.module_list.return_value = [{"name": b"timeseries", "ver": 11006}]
            mock_pipeline = MagicMock()
            mock_client.pipeline.return_value = mock_pipeline
            from src.db.redis_writer import RedisTimeSeriesWriter

            writer = RedisTimeSeriesWriter(config)
            events = [{"mac": "aa:bb:cc:dd:ee:ff", "status": "connected"}]
            result = writer.ingest_webhook(events, "client-sessions")
            assert result == 0
            mock_pipeline.execute.assert_not_called()


class TestBuildLabels:
    """Tests for _build_labels static method."""

    def test_includes_api_function_and_metric(self):
        from src.db.redis_writer import RedisTimeSeriesWriter

        labels = RedisTimeSeriesWriter._build_labels(
            {"org_id": "org-1", "site_id": "site-1"},
            "getDeviceStats",
            "getDeviceStats:dev-1:cpu",
        )
        assert labels["api_function"] == "getDeviceStats"
        assert labels["metric_name"] == "cpu"
        assert labels["org_id"] == "org-1"

    def test_custom_label_fields(self):
        from src.db.redis_writer import RedisTimeSeriesWriter

        labels = RedisTimeSeriesWriter._build_labels(
            {"custom_field": "val"},
            "getStats",
            "getStats:dev-1:mem",
            ts_label_fields=["custom_field"],
        )
        assert labels["custom_field"] == "val"
        assert "org_id" not in labels


class TestExtractListedFields:
    """Tests for _extract_listed_fields static method."""

    def test_extracts_only_named_numeric(self):
        from src.db.redis_writer import RedisTimeSeriesWriter

        result = RedisTimeSeriesWriter._extract_listed_fields(
            {"cpu": 42.0, "mem": 78, "name": "test", "disk": 90.0},
            ["cpu", "mem", "name"],
        )
        assert result == {"cpu": 42.0, "mem": 78.0}
        assert "name" not in result
        assert "disk" not in result
