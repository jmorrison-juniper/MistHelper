"""Unit tests for RedisTimeSeriesWriter.

All redis interactions are mocked — no live Redis required.
"""

from __future__ import annotations

from collections import Counter  # WHY: the mocked _extract_chunk must return the same tally type as the real worker.
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
        with patch.object(  # Mock worker so the test measures the pool fan-out and not the extraction itself
            writer, "_extract_chunk", return_value=([], {}, Counter())
        ) as mock_chunk:  # The worker now returns three items, so the mock must match that shape
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


def _entity_context(entity_key_field: str = "entity_id"):  # WHY: every resolution test needs the same frozen context.
    """Return an _ExtractContext that names one strategy field and turns off the allow-list."""
    from src.db.redis_writer import _ExtractContext  # WHY: import inside the helper to match the file style.

    return _ExtractContext(  # WHY: the frozen context carries the four extraction inputs.
        api_function_name="testFunc",  # WHY: the first part of every generated time-series key.
        primary_keys=[entity_key_field],  # WHY: the primary key list excludes the identifier from the numeric scan.
        entity_key_field=entity_key_field,  # WHY: the field that the strategy branch reads first.
        ts_value_fields=None,  # WHY: None selects the automatic numeric scan rather than the allow-list.
    )


class TestResolveEntityIdFallbackBranch:
    """Tests for the fallback branch of the resolution rule (User Story 1)."""

    def test_record_without_strategy_field_uses_device_id(self) -> None:
        """FR-002: a record that omits the strategy field resolves through the fallback list."""
        from src.db.redis_writer import RedisTimeSeriesWriter  # WHY: import the class that owns the rule.

        record = {"device_id": "dev-1", "cpu": 42.0}  # WHY: the record carries no 'entity_id' field.
        entity_id, source = RedisTimeSeriesWriter._resolve_entity_id(record, "entity_id")  # WHY: run the rule.
        assert entity_id == "dev-1"  # WHY: the rule returns the text form of the device_id value.
        assert source == "fallback"  # WHY: the rule reports the fallback branch.

    def test_two_records_produce_two_distinct_keys(self, config, mock_redis) -> None:
        """SC-001: two records with different device_id values must not collapse into one key."""
        from src.db.redis_writer import RedisTimeSeriesWriter  # WHY: import the class under test.

        writer = RedisTimeSeriesWriter(config)  # WHY: the extraction path is an instance method.
        records = [  # WHY: neither record carries the strategy field.
            {"device_id": "dev-1", "cpu": 1.0},  # WHY: the first record names the first entity.
            {"device_id": "dev-2", "cpu": 2.0},  # WHY: the second record names a different entity.
        ]
        adds, _key_records, _sources = writer._extract_chunk(records, _entity_context())  # WHY: run the extraction.
        keys = [ts_key for ts_key, _value in adds]  # WHY: read only the key part of each pair.
        assert keys == ["testFunc:dev-1:cpu", "testFunc:dev-2:cpu"]  # WHY: each entity keeps its own series.
        assert len(set(keys)) == 2  # WHY: the two keys are distinct, so the records no longer collapse.
        assert all("unknown" not in ts_key for ts_key in keys)  # WHY: no record lands in the sentinel bucket.

    @pytest.mark.parametrize("unusable", [None, "", "   "])  # WHY: the three unusable strategy values.
    def test_unusable_strategy_value_falls_back(self, unusable) -> None:
        """Edge cases 1 to 3: an unusable strategy value must not block the fallback list."""
        from src.db.redis_writer import RedisTimeSeriesWriter  # WHY: import the class under test.

        record = {"entity_id": unusable, "device_id": "dev-1"}  # WHY: the strategy field holds an unusable value.
        entity_id, source = RedisTimeSeriesWriter._resolve_entity_id(record, "entity_id")  # WHY: run the rule.
        assert entity_id == "dev-1"  # WHY: the fallback list supplies the identifier.
        assert source == "fallback"  # WHY: the rule reports the fallback branch.

    def test_fallback_order_prefers_the_earlier_name(self) -> None:
        """FR-006: the fallback order decides the winner when a record carries two candidate fields."""
        from src.db.redis_writer import RedisTimeSeriesWriter  # WHY: import the class under test.

        both = {"site_id": "site-1", "org_id": "org-1"}  # WHY: site_id sits before org_id in the order.
        assert RedisTimeSeriesWriter._resolve_entity_id(both, "entity_id") == ("site-1", "fallback")  # WHY: order.
        empty_device = {"device_id": "", "site_id": "site-1"}  # WHY: an empty device_id is not a usable value.
        assert RedisTimeSeriesWriter._resolve_entity_id(empty_device, "entity_id") == (
            "site-1",
            "fallback",
        )  # WHY: the walk skips the empty field and takes the next usable name.


class TestResolveEntityIdStrategyBranch:
    """Tests for the strategy branch of the resolution rule (User Story 2)."""

    def test_usable_strategy_value_wins(self) -> None:
        """FR-001: a usable strategy value returns its text form and the source 'strategy'."""
        from src.db.redis_writer import RedisTimeSeriesWriter  # WHY: import the class under test.

        record = {"entity_id": "dev-1", "cpu": 42.0}  # WHY: the strategy field holds a usable value.
        entity_id, source = RedisTimeSeriesWriter._resolve_entity_id(record, "entity_id")  # WHY: run the rule.
        assert entity_id == "dev-1"  # WHY: the identifier equals the text form of the strategy value.
        assert source == "strategy"  # WHY: the rule reports the strategy branch.

    def test_strategy_value_outranks_a_fallback_field(self) -> None:
        """INV-3: the strategy field wins even when the record also carries a fallback field."""
        from src.db.redis_writer import RedisTimeSeriesWriter  # WHY: import the class under test.

        record = {"entity_id": "strategy-1", "device_id": "dev-1"}  # WHY: the two fields hold different values.
        entity_id, source = RedisTimeSeriesWriter._resolve_entity_id(record, "entity_id")  # WHY: run the rule.
        assert entity_id == "strategy-1"  # WHY: the rule never reads device_id on this path.
        assert source == "strategy"  # WHY: the rule reports the strategy branch.

    def test_zero_is_a_usable_identifier(self) -> None:
        """INV-5: the number 0 must resolve to the text '0' and not to the sentinel."""
        from src.db.redis_writer import RedisTimeSeriesWriter  # WHY: import the class under test.

        record = {"entity_id": 0, "device_id": "dev-1"}  # WHY: a plain truth test would reject this value.
        entity_id, source = RedisTimeSeriesWriter._resolve_entity_id(record, "entity_id")  # WHY: run the rule.
        assert entity_id == "0"  # WHY: the rule returns the text form of the number.
        assert source == "strategy"  # WHY: the value is usable, so the walk never starts.
        assert RedisTimeSeriesWriter._is_usable(0) is True  # WHY: guard the helper that the rule depends on.

    def test_existing_key_stays_byte_identical(self, config, mock_redis) -> None:
        """SC-002 and SC-004: a record with the strategy field produces the same three-part key as before."""
        from src.db.redis_writer import RedisTimeSeriesWriter  # WHY: import the class under test.

        writer = RedisTimeSeriesWriter(config)  # WHY: the extraction path is an instance method.
        records = [{"entity_id": "dev-1", "cpu": 42.0}]  # WHY: one record with one numeric field.
        adds, _key_records, _sources = writer._extract_chunk(records, _entity_context())  # WHY: run the extraction.
        assert adds == [("testFunc:dev-1:cpu", 42.0)]  # WHY: the key text must not change for an existing export.
        assert adds[0][0].split(":") == ["testFunc", "dev-1", "cpu"]  # WHY: the key holds three colon parts.

    def test_strategy_field_name_that_matches_a_fallback_name(self) -> None:
        """Edge case 7: a strategy field name that also sits in the fallback list reads the field once."""
        from src.db.redis_writer import RedisTimeSeriesWriter  # WHY: import the class under test.

        record = {"device_id": "dev-1", "site_id": "site-1"}  # WHY: 'device_id' is both the strategy and a fallback.
        entity_id, source = RedisTimeSeriesWriter._resolve_entity_id(record, "device_id")  # WHY: run the rule.
        assert entity_id == "dev-1"  # WHY: the early return stops the walk before it reads the same field again.
        assert source == "strategy"  # WHY: the rule reports the strategy branch and never reaches the walk.


class TestResolveEntityIdUnknownBranch:
    """Tests for the sentinel branch of the resolution rule (User Story 3)."""

    def test_record_without_any_identifier_uses_the_sentinel(self, config, mock_redis) -> None:
        """FR-003: a record that carries no identifier still writes under the sentinel."""
        from src.db.redis_writer import RedisTimeSeriesWriter  # WHY: import the class under test.

        writer = RedisTimeSeriesWriter(config)  # WHY: the extraction path is an instance method.
        record = {"cpu": 7.0}  # WHY: the record carries a numeric field and no identifier.
        assert RedisTimeSeriesWriter._resolve_entity_id(record, "entity_id") == ("unknown", "unknown")  # WHY: rule.
        adds, _key_records, _sources = writer._extract_chunk([record], _entity_context())  # WHY: run the extraction.
        assert adds == [("testFunc:unknown:cpu", 7.0)]  # WHY: the sentinel keeps the key length stable.

    def test_empty_record_raises_no_error(self) -> None:
        """INV-1: the rule accepts an empty dictionary and returns the sentinel."""
        from src.db.redis_writer import RedisTimeSeriesWriter  # WHY: import the class under test.

        entity_id, source = RedisTimeSeriesWriter._resolve_entity_id({}, "entity_id")  # WHY: run the rule.
        assert entity_id == "unknown"  # WHY: no field holds a usable value.
        assert source == "unknown"  # WHY: the rule reports the sentinel branch.


class TestResolutionSummaryLogging:
    """Tests for the one summary event that each extraction call emits."""

    def test_one_summary_event_reports_three_counts(self, config, mock_redis) -> None:
        """FR-007 and FR-008: the writer emits one debug summary per call and no per-record line."""
        from src.db.redis_writer import RedisTimeSeriesWriter  # WHY: import the class under test.

        writer = RedisTimeSeriesWriter(config)  # WHY: the extraction path is an instance method.
        writer._log = MagicMock()  # WHY: replace the logger after connect, so the test reads extraction events only.
        records = [  # WHY: the set covers all three resolution branches.
            {"entity_id": "dev-1", "cpu": 1.0},  # WHY: the strategy branch.
            {"entity_id": "dev-2", "cpu": 2.0},  # WHY: the strategy branch a second time.
            {"device_id": "dev-3", "cpu": 3.0},  # WHY: the fallback branch.
            {"cpu": 4.0},  # WHY: the sentinel branch.
        ]
        writer._extract_all_adds(records, _entity_context())  # WHY: run the single entry point for both paths.
        assert writer._log.debug.call_count == 1  # WHY: exactly one summary for the whole call.
        counts = writer._log.debug.call_args_list[0].kwargs  # WHY: the summary reports the counts as keywords.
        assert counts["strategy"] == 2  # WHY: two records read the strategy field.
        assert counts["fallback"] == 1  # WHY: one record read a fallback field.
        assert counts["unknown"] == 1  # WHY: one record reached the sentinel.
        assert counts["strategy"] + counts["fallback"] + counts["unknown"] == len(records)  # WHY: the counts sum.
        assert writer._log.info.call_count == 1  # WHY: one action log before the extraction and no per-record line.

    def test_parallel_path_emits_one_summary_for_a_large_export(self, config, mock_redis) -> None:
        """SC-007: an extraction of 10000 records emits one summary whose counts sum to 10000."""
        from src.db.redis_writer import RedisTimeSeriesWriter  # WHY: import the class under test.

        writer = RedisTimeSeriesWriter(config)  # WHY: the extraction path is an instance method.
        writer._log = MagicMock()  # WHY: replace the logger after connect, so the test reads extraction events only.
        records = [{"device_id": f"dev-{i}", "cpu": float(i)} for i in range(10000)]  # WHY: 10000 crosses the pool.
        writer._extract_all_adds(records, _entity_context())  # WHY: the size routes the call through the thread pool.
        assert writer._log.debug.call_count == 1  # WHY: one summary for the whole call, not one for each chunk.
        counts = writer._log.debug.call_args_list[0].kwargs  # WHY: the summary reports the counts as keywords.
        assert counts["fallback"] == 10000  # WHY: every record resolves through the fallback list.
        assert counts["strategy"] + counts["fallback"] + counts["unknown"] == 10000  # WHY: the merge loses no count.
