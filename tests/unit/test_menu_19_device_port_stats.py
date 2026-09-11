"""Unit tests for Menu 19 organization device port stats refactor."""

from unittest.mock import MagicMock

import MistHelper


class TestDevicePortStatsHelpers:
    """Verify helper behavior for in-place device_port_stats refactor."""

    def test_flatten_site_port_results_ignores_non_lists(self):
        """Only list-shaped worker results contribute rows."""
        results = [[{"mac": "1"}], {"bad": True}, [{"mac": "2"}]]

        flattened = MistHelper.OrgDeviceStatsExporter._flatten_site_port_results(results)

        assert flattened == [{"mac": "1"}, {"mac": "2"}]

    def test_port_stats_cache_hit_returns_false_when_not_fast(self):
        """Cache helper does nothing outside fast mode."""
        assert MistHelper.OrgDeviceStatsExporter._port_stats_cache_hit("does-not-matter.csv", False) is False


class TestDevicePortStatsOrchestration:
    """Verify top-level method chooses the correct execution path."""

    def test_fast_mode_calls_fast_helper(self, monkeypatch):
        """Fast mode routes through decomposed fast helper and skips APIDataFetcher."""
        helper_called = {"count": 0}
        monkeypatch.setattr(MistHelper.OrgDeviceStatsExporter, "_port_stats_cache_hit", lambda output_file, fast: False)
        monkeypatch.setattr(
            MistHelper.OrgDeviceStatsExporter,
            "_run_fast_device_port_stats",
            lambda output_file: helper_called.__setitem__("count", helper_called["count"] + 1),
        )
        monkeypatch.setattr(MistHelper.TimeUtils, "get_dynamic_lookback_hours", lambda default_hours, test_hours: 1)
        monkeypatch.setattr(MistHelper.TimeUtils, "log_dynamic_lookback", lambda context, hours: None)
        api_fetcher = MagicMock()
        monkeypatch.setattr(MistHelper, "APIDataFetcher", api_fetcher)

        MistHelper.OrgDeviceStatsExporter.device_port_stats(fast=True)

        assert helper_called["count"] == 1
        api_fetcher.assert_not_called()

    def test_non_fast_mode_uses_api_data_fetcher(self, monkeypatch):
        """Non-fast path preserves org-level APIDataFetcher behavior."""
        executed = {"count": 0}

        class MockFetcher:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

            def execute(self):
                executed["count"] += 1

        monkeypatch.setattr(MistHelper.OrgDeviceStatsExporter, "_port_stats_cache_hit", lambda output_file, fast: False)
        monkeypatch.setattr(MistHelper.TimeUtils, "get_dynamic_lookback_hours", lambda default_hours, test_hours: 24)
        monkeypatch.setattr(MistHelper.TimeUtils, "log_dynamic_lookback", lambda context, hours: None)
        monkeypatch.setattr(MistHelper, "APIDataFetcher", MockFetcher)

        MistHelper.OrgDeviceStatsExporter.device_port_stats(fast=False)

        assert executed["count"] == 1
