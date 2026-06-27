"""Unit tests for Menu 13 - Organization Device Stats Export.

Tests verify that OrgDeviceStatsExporter.device_stats() correctly wires
APIDataFetcher with the expected parameters, integrates with the
PROGRESS_EMITTER lifecycle, supports fast mode cache-hit behavior,
and uses dynamic lookback hours. All API calls are mocked.

Covers: FR-001, FR-005, FR-006, FR-007, US1, US4, US5, US6 from spec-025.
"""

import os
import time
from unittest.mock import MagicMock

import MistHelper


class TestDeviceStatsAPIDataFetcherWiring:
    """Verify OrgDeviceStatsExporter passes correct params to APIDataFetcher."""

    def test_creates_fetcher_with_correct_params(self, monkeypatch):
        """FR-001: APIDataFetcher receives api_call, filename, sort_key, type, duration, limit."""
        captured_kwargs: dict = {}

        class MockFetcher:
            def __init__(self, **kwargs):
                captured_kwargs.update(kwargs)

            def execute(self):
                pass

        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)
        monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", None)
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "get_dynamic_lookback_hours",
            staticmethod(lambda default, minimum: 24),
        )
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "log_dynamic_lookback",
            staticmethod(lambda label, hours: None),
        )

        MistHelper.OrgDeviceStatsExporter.device_stats()

        assert captured_kwargs["title"] == "Org Device Stats:"
        assert captured_kwargs["api_call"] is MistHelper.mistapi.api.v1.orgs.stats.listOrgDevicesStats
        assert captured_kwargs["filename"] == "OrgDeviceStats.csv"
        assert captured_kwargs["sort_key"] == "type"
        assert captured_kwargs["type"] == "all"
        assert captured_kwargs["duration"] == "24h"
        assert captured_kwargs["limit"] == 1000

    def test_calls_execute_exactly_once(self, monkeypatch):
        """US1: execute() is called exactly once per invocation."""
        mock_instance = MagicMock()

        class MockFetcher:
            def __init__(self, **kwargs):
                pass

            def execute(self):
                mock_instance.execute()

        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)
        monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", None)
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "get_dynamic_lookback_hours",
            staticmethod(lambda default, minimum: 24),
        )
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "log_dynamic_lookback",
            staticmethod(lambda label, hours: None),
        )

        MistHelper.OrgDeviceStatsExporter.device_stats()

        mock_instance.execute.assert_called_once()

    def test_handles_empty_api_response(self, monkeypatch):
        """US1 Scenario 3: Empty result does not crash."""
        execute_called = False

        class MockFetcher:
            def __init__(self, **kwargs):
                pass

            def execute(self):
                nonlocal execute_called
                execute_called = True

        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)
        monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", None)
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "get_dynamic_lookback_hours",
            staticmethod(lambda default, minimum: 24),
        )
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "log_dynamic_lookback",
            staticmethod(lambda label, hours: None),
        )

        MistHelper.OrgDeviceStatsExporter.device_stats()

        assert execute_called


class TestDeviceStatsProgressEmitter:
    """Verify PROGRESS_EMITTER lifecycle calls during Menu 13 export."""

    def test_emits_start_and_complete(self, monkeypatch):
        """US4 / FR-005: emit_progress_start and emit_progress_complete called."""
        mock_emitter = MagicMock()

        class MockFetcher:
            def __init__(self, **kwargs):
                pass

            def execute(self):
                pass

        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)
        monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", mock_emitter)
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "get_dynamic_lookback_hours",
            staticmethod(lambda default, minimum: 24),
        )
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "log_dynamic_lookback",
            staticmethod(lambda label, hours: None),
        )

        MistHelper.OrgDeviceStatsExporter.device_stats()

        mock_emitter.emit_progress_start.assert_called_once_with("13", "device_stats", 1)
        mock_emitter.emit_progress_complete.assert_called_once()
        call_args = mock_emitter.emit_progress_complete.call_args
        assert call_args[0][0].menu_option == "13"  # Issue #470: identity now bundled in ProgressContext.
        assert call_args[0][0].operation_name == "device_stats"  # ProgressContext.operation_name.
        assert call_args[0][0].total == 1  # ProgressContext.total.
        assert call_args[0][1] == 1  # processed count (now second positional arg).
        assert call_args[0][2] is False  # was_stopped flag (now third positional arg).
        assert isinstance(call_args[0][3], float)  # duration seconds (now fourth positional arg).

    def test_handles_no_emitter_gracefully(self, monkeypatch):
        """US4 Scenario 3: No exception when PROGRESS_EMITTER is None."""

        class MockFetcher:
            def __init__(self, **kwargs):
                pass

            def execute(self):
                pass

        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)
        monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", None)
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "get_dynamic_lookback_hours",
            staticmethod(lambda default, minimum: 24),
        )
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "log_dynamic_lookback",
            staticmethod(lambda label, hours: None),
        )

        MistHelper.OrgDeviceStatsExporter.device_stats()


class TestDeviceStatsFastMode:
    """Verify fast mode cache-hit and cache-miss behavior."""

    def test_fast_mode_cache_hit_skips_fetch(self, monkeypatch, tmp_path):
        """FR-006 / US5 Scenario 1: Fresh CSV skips API call."""
        csv_file = tmp_path / "OrgDeviceStats.csv"
        csv_file.write_text("header\nrow1\n")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(MistHelper, "CSV_FRESHNESS_MINUTES", 5)
        monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", None)

        fetcher_created = False

        class MockFetcher:
            def __init__(self, **kwargs):
                nonlocal fetcher_created
                fetcher_created = True

            def execute(self):
                pass

        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)

        MistHelper.OrgDeviceStatsExporter.device_stats(fast=True)

        assert not fetcher_created

    def test_fast_mode_cache_miss_stale_file(self, monkeypatch, tmp_path):
        """FR-006 / US5 Scenario 2: Stale CSV proceeds with API fetch."""
        csv_file = tmp_path / "OrgDeviceStats.csv"
        csv_file.write_text("header\nrow1\n")
        stale_time = time.time() - (10 * 60)
        os.utime(str(csv_file), (stale_time, stale_time))

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(MistHelper, "CSV_FRESHNESS_MINUTES", 5)
        monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", None)
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "get_dynamic_lookback_hours",
            staticmethod(lambda default, minimum: 24),
        )
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "log_dynamic_lookback",
            staticmethod(lambda label, hours: None),
        )

        fetcher_created = False

        class MockFetcher:
            def __init__(self, **kwargs):
                nonlocal fetcher_created
                fetcher_created = True

            def execute(self):
                pass

        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)

        MistHelper.OrgDeviceStatsExporter.device_stats(fast=True)

        assert fetcher_created

    def test_fast_mode_cache_miss_no_file(self, monkeypatch, tmp_path):
        """FR-006 / US5 Scenario 3: No CSV file proceeds with API fetch."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", None)
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "get_dynamic_lookback_hours",
            staticmethod(lambda default, minimum: 24),
        )
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "log_dynamic_lookback",
            staticmethod(lambda label, hours: None),
        )

        fetcher_created = False

        class MockFetcher:
            def __init__(self, **kwargs):
                nonlocal fetcher_created
                fetcher_created = True

            def execute(self):
                pass

        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)

        MistHelper.OrgDeviceStatsExporter.device_stats(fast=True)

        assert fetcher_created

    def test_fast_mode_disabled_by_default(self, monkeypatch, tmp_path):
        """US5 Scenario 4: Default call skips cache check entirely."""
        csv_file = tmp_path / "OrgDeviceStats.csv"
        csv_file.write_text("header\nrow1\n")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", None)
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "get_dynamic_lookback_hours",
            staticmethod(lambda default, minimum: 24),
        )
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "log_dynamic_lookback",
            staticmethod(lambda label, hours: None),
        )

        fetcher_created = False

        class MockFetcher:
            def __init__(self, **kwargs):
                nonlocal fetcher_created
                fetcher_created = True

            def execute(self):
                pass

        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)

        MistHelper.OrgDeviceStatsExporter.device_stats()

        assert fetcher_created


class TestDeviceStatsDynamicLookback:
    """Verify dynamic lookback hours integration."""

    def test_dynamic_lookback_value_passed_to_fetcher(self, monkeypatch):
        """FR-007 / US6: Lookback value from TimeUtils used in duration param."""
        captured_kwargs: dict = {}

        class MockFetcher:
            def __init__(self, **kwargs):
                captured_kwargs.update(kwargs)

            def execute(self):
                pass

        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)
        monkeypatch.setattr(MistHelper, "PROGRESS_EMITTER", None)
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "get_dynamic_lookback_hours",
            staticmethod(lambda default, minimum: 6),
        )
        monkeypatch.setattr(
            MistHelper.TimeUtils,
            "log_dynamic_lookback",
            staticmethod(lambda label, hours: None),
        )

        MistHelper.OrgDeviceStatsExporter.device_stats()

        assert captured_kwargs["duration"] == "6h"
