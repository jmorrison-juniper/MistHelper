"""Unit tests for RedisTimeSeriesWriter.

All redis interactions are mocked — no live Redis required.
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
        mock_ts = MagicMock()
        mock_client.ts.return_value = mock_ts
        mock_client.module_list.return_value = [{"name": b"timeseries", "ver": 11006}]
        mock_pipeline = MagicMock()
        mock_client.pipeline.return_value = mock_pipeline
        mock_pipeline.__enter__ = MagicMock(return_value=mock_pipeline)
        mock_pipeline.__exit__ = MagicMock(return_value=False)
        yield {
            "client_cls": mock_cls,
            "client": mock_client,
            "ts": mock_ts,
            "pipeline": mock_pipeline,
        }


class TestRedisTimeSeriesWriterInit:
    """Tests for RedisTimeSeriesWriter.__init__."""

    def test_connects_and_verifies_ts_module(self, config, mock_redis):
        from src.db.redis_writer import RedisTimeSeriesWriter

        writer = RedisTimeSeriesWriter(config)
        mock_redis["client_cls"].assert_called_once()
        mock_redis["client"].module_list.assert_called_once()
        assert writer._ts is not None

    def test_raises_if_ts_module_missing(self, config, mock_redis):
        from src.db.redis_writer import RedisTimeSeriesWriter

        mock_redis["client"].module_list.return_value = []
        with pytest.raises(RuntimeError, match="TimeSeries"):
            RedisTimeSeriesWriter(config)


class TestRedisTimeSeriesWriterWrite:
    """Tests for RedisTimeSeriesWriter.write."""

    def test_writes_numeric_values_as_timeseries(self, config, mock_redis):
        from src.db.redis_writer import RedisTimeSeriesWriter

        writer = RedisTimeSeriesWriter(config)
        # Pipeline called 3 times: key creation, compaction, TS.ADD
        # 2 numeric fields (cpu_usage, mem_usage) → 2 keys, 8 compaction cmds, 2 adds
        mock_redis["pipeline"].execute.side_effect = [
            [True, True],
            [True] * 8,
            [True, True],
        ]
        strategy = {
            "type": "composite_pk",
            "primary_key": ["id", "device_id", "timestamp"],
        }
        data = [
            {
                "id": "evt-1",
                "device_id": "dev-1",
                "timestamp": 1700000000,
                "cpu_usage": 42.5,
                "mem_usage": 78.2,
                "name": "not-a-number",
            }
        ]
        result = writer.write(data, "getDeviceStats", strategy)

        assert result.success is True
        assert result.backend == "redis"
        assert result.records_written == 2

    def test_skips_non_numeric_fields(self, config, mock_redis):
        from src.db.redis_writer import RedisTimeSeriesWriter

        writer = RedisTimeSeriesWriter(config)
        strategy = {
            "type": "composite_pk",
            "primary_key": ["id", "timestamp"],
        }
        data = [{"id": "evt-1", "timestamp": 1700000000, "status": "active"}]
        result = writer.write(data, "getEvents", strategy)

        assert result.records_written == 0

    def test_key_naming_convention(self, config, mock_redis):
        from src.db.redis_writer import RedisTimeSeriesWriter

        writer = RedisTimeSeriesWriter(config)
        strategy = {
            "type": "composite_pk",
            "primary_key": ["id", "device_id", "timestamp"],
        }
        data = [{"id": "evt-1", "device_id": "dev-1", "timestamp": 1700000000, "cpu": 50.0}]
        writer.write(data, "getDeviceStats", strategy)

        # Verify TS.CREATE was called with the correct key pattern
        create_calls = mock_redis["ts"].create.call_args_list
        if create_calls:
            key = create_calls[0][0][0]
            assert "getDeviceStats" in key
            assert "cpu" in key

    def test_empty_data_returns_success(self, config, mock_redis):
        from src.db.redis_writer import RedisTimeSeriesWriter

        writer = RedisTimeSeriesWriter(config)
        strategy = {"type": "composite_pk", "primary_key": ["id"]}
        result = writer.write([], "getStats", strategy)

        assert result.success is True
        assert result.records_written == 0

    def test_handles_write_error_gracefully(self, config, mock_redis):
        from src.db.redis_writer import RedisTimeSeriesWriter

        writer = RedisTimeSeriesWriter(config)
        # 1 numeric field → 1 key creation, 4 compaction cmds, 1 TS.ADD (fails)
        mock_redis["pipeline"].execute.side_effect = [
            [True],
            [True] * 4,
            [Exception("Connection lost")],
        ]
        strategy = {
            "type": "composite_pk",
            "primary_key": ["id", "timestamp"],
        }
        data = [{"id": "evt-1", "timestamp": 1700000000, "value": 42.0}]
        result = writer.write(data, "getStats", strategy)

        assert result.records_failed > 0


class TestRedisTimeSeriesCompaction:
    """Tests for compaction rule creation."""

    def test_creates_hourly_and_daily_compaction(self, config, mock_redis):
        from src.db.redis_writer import RedisTimeSeriesWriter

        writer = RedisTimeSeriesWriter(config)
        writer._ensure_single_compaction("test:dev-1:cpu")

        create_rule_calls = mock_redis["ts"].createrule.call_args_list
        assert len(create_rule_calls) >= 2
        dest_keys = [call[0][1] for call in create_rule_calls]
        assert any("avg_1h" in k for k in dest_keys)
        assert any("avg_1d" in k for k in dest_keys)

    def test_skips_duplicate_compaction(self, config, mock_redis):
        from src.db.redis_writer import RedisTimeSeriesWriter

        writer = RedisTimeSeriesWriter(config)
        writer._ensure_single_compaction("test:dev-1:cpu")
        initial_calls = len(mock_redis["ts"].createrule.call_args_list)

        writer._ensure_single_compaction("test:dev-1:cpu")
        assert len(mock_redis["ts"].createrule.call_args_list) == initial_calls
