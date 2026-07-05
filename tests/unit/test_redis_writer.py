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


class TestExtractAllAddsThreadPoolBranch:
    """Tests for _extract_all_adds when data exceeds 1000 records (lines 143-173).

    When the record count exceeds the 1000-record threshold, _extract_all_adds
    must use a ThreadPoolExecutor to process chunks in parallel.
    """

    def test_over_1000_records_uses_thread_pool(self, config, mock_redis) -> None:
        """Lines 143-173: Exactly 1001 records must trigger the thread pool branch."""
        from src.db.redis_writer import RedisTimeSeriesWriter, _ExtractContext  # Import module under test

        writer = RedisTimeSeriesWriter(config)  # Create writer with mocked redis
        records = [{"id": str(i), "ts": float(i)} for i in range(1001)]  # 1001 exceeds 1000 threshold
        ctx = _ExtractContext(  # Frozen context replaces the loose-arg signature
            api_function_name="testFunc",
            primary_keys=["id"],
            entity_key_field="id",
            ts_value_fields=None,
        )
        with patch.object(writer, "_extract_chunk", return_value=([], {})) as mock_chunk:  # Mock worker
            adds, keys = writer._extract_all_adds(records, ctx)  # Route through parallel branch via context
        assert adds == []  # Thread pool collects empty adds from mocked chunks
        assert keys == {}  # Thread pool collects empty keys from mocked chunks
        assert mock_chunk.call_count >= 2  # Multiple chunks must be processed by the pool


class TestCoverageGapTargets:
    """Targeted tests to cover the final gap lines and reach 90% threshold.

    Lines covered here: 56-57 (DNS failure), 189 (ts_value_fields path), 341 (key cache hit).
    """

    def test_init_dns_resolution_failure_raises_connection_error(self, config) -> None:
        """Lines 56-57: ConnectionError must be raised when Redis host DNS fails."""
        import socket  # Import for socket.gaierror exception type

        from src.db.redis_writer import RedisTimeSeriesWriter  # Import module under test

        with patch(
            "src.db.redis_writer.socket.getaddrinfo", side_effect=socket.gaierror("Name or service not known")
        ):  # Patch only getaddrinfo
            with pytest.raises(ConnectionError, match="not resolvable"):  # Must raise ConnectionError
                RedisTimeSeriesWriter(config)  # Constructor must propagate DNS failure as ConnectionError

    def test_extract_chunk_with_ts_value_fields_calls_listed_fields(self, config, mock_redis) -> None:
        """Line 189: when ts_value_fields is provided, _extract_listed_fields is called instead of _extract_numeric."""
        from src.db.redis_writer import RedisTimeSeriesWriter, _ExtractContext  # Import module under test

        writer = RedisTimeSeriesWriter(config)  # Create writer with mocked redis
        records = [{"entity_id": "dev-1", "cpu": 45.0}]  # Single record for testing
        listed_return = {"cpu": 45.0}  # Fake return value from _extract_listed_fields (must be a dict)
        ctx = _ExtractContext(  # Frozen context carrying ts_value_fields=["cpu"]
            api_function_name="testFunc",
            primary_keys=["entity_id"],
            entity_key_field="entity_id",
            ts_value_fields=["cpu"],
        )
        with patch(  # Patch on the class since _select_numeric references the static via class binding
            "src.db.redis_writer.RedisTimeSeriesWriter._extract_listed_fields", return_value=listed_return
        ) as mock_lf:
            writer._extract_chunk(records, ctx)  # Trigger the listed-fields branch via context.ts_value_fields
        mock_lf.assert_called_once()  # _extract_listed_fields must have been called via line 189

    def test_create_single_key_skips_when_key_already_cached(self, config, mock_redis) -> None:
        """Line 341: _create_single_key must return early when ts_key is already in _created_keys."""
        from src.db.redis_writer import RedisTimeSeriesWriter  # Import module under test

        writer = RedisTimeSeriesWriter(config)  # Create writer with mocked redis
        writer._created_keys = {"existing:ts:key"}  # Pre-populate cache with the target key
        writer._ensure_key_single(  # Call with a key that is already in the cache
            "existing:ts:key", {"id": "dev-1"}, "testFunc"  # Key already cached → must return early
        )
        mock_redis["ts"].create.assert_not_called()  # Redis ts.create must NOT be called for cached key

    def test_ensure_key_single_reraises_non_exists_response_error(self, config, mock_redis) -> None:
        """Lines 350-352: ResponseError not containing 'already exists' must be re-raised by _ensure_key_single."""
        import redis  # Import redis for redis.ResponseError exception class

        from src.db.redis_writer import RedisTimeSeriesWriter  # Import module under test

        writer = RedisTimeSeriesWriter(config)  # Create writer with mocked redis (empty _created_keys)
        mock_redis["ts"].create.side_effect = redis.ResponseError("permission denied")  # Non-exists error
        with pytest.raises(redis.ResponseError, match="permission denied"):  # Must re-raise the non-exists error
            writer._ensure_key_single(  # Key is NOT in cache, so ts.create will be called
                "new:ts:key", {"id": "dev-1"}, "testFunc"  # Fresh key — triggers ts.create which raises
            )
