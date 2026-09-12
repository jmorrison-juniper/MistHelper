"""Unit tests for ``src.export.site_anomaly_exporter.SiteAnomalyExporter``.

Why: Exercises every line and branch of the 17 static methods so that
un-omitting the module in ``[tool.coverage.run].omit`` keeps overall coverage
above the 90% gate. The module resolves cross-class collaborators lazily via
``importlib.import_module("MistHelper")``; tests inject a fake ``MistHelper``
module via ``sys.modules`` monkeypatching to control those interactions.
``DataProcessingUtils`` is imported directly at module scope and is patched
against the module's own binding.
"""

from __future__ import annotations

import logging
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def fake_mh(monkeypatch):
    """Install a fake MistHelper module for lazy importlib resolution.

    Why: SiteAnomalyExporter methods call ``importlib.import_module("MistHelper")``
    to fetch PromptUtils, EnhancedSSHRunner, AnomalyMetricsDiscovery, mistapi,
    apisession, DataExporter, and PromptClientUtils. Replacing the module lets
    tests observe and control every collaborator without loading the monolith.
    """
    mh = ModuleType("MistHelper")
    mh.PromptUtils = MagicMock()
    mh.EnhancedSSHRunner = MagicMock()
    mh.AnomalyMetricsDiscovery = MagicMock()
    mh.mistapi = MagicMock()
    mh.apisession = MagicMock()
    mh.DataExporter = MagicMock()
    mh.PromptClientUtils = MagicMock()
    mh.EnhancedSSHRunner.sanitize_filename.side_effect = lambda s: s.replace(" ", "_")
    monkeypatch.setitem(sys.modules, "MistHelper", mh)
    return mh


class TestAnomalyEvents:
    """Cover SiteAnomalyExporter.anomaly_events (site-level public entry)."""

    def test_no_site_selected_returns_early(self, fake_mh, caplog):
        """Returns immediately when the site selection prompt yields nothing."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.PromptUtils.select_site.return_value = None

        caplog.set_level(logging.WARNING, logger="src.export.site_anomaly_exporter")
        SiteAnomalyExporter.anomaly_events()

        assert "No site selected" in caplog.text

    def test_no_metrics_discovered_returns_early(self, fake_mh):
        """Returns when discovery yields no metric names."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.PromptUtils.select_site.return_value = "site-1"
        fake_mh.AnomalyMetricsDiscovery.discover.return_value = []
        with patch.object(SiteAnomalyExporter, "_anomaly_resolve_site_name", return_value="Site"):
            SiteAnomalyExporter.anomaly_events()

    def test_happy_path_invokes_aggregate_and_export(self, fake_mh):
        """Aggregates metrics and writes CSV on the happy path."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.PromptUtils.select_site.return_value = "site-1"
        fake_mh.AnomalyMetricsDiscovery.discover.return_value = [{"metric_name": "m1", "description": "d"}]
        with (
            patch.object(SiteAnomalyExporter, "_anomaly_resolve_site_name", return_value="Site A"),
            patch.object(SiteAnomalyExporter, "_aggregate_site_anomaly_data", return_value=([{"a": 1}], 1)) as agg,
            patch.object(SiteAnomalyExporter, "_export_anomaly_data") as exp,
        ):
            SiteAnomalyExporter.anomaly_events()

        agg.assert_called_once_with("site-1", "Site A", ["m1"])
        exp.assert_called_once()

    def test_exception_during_aggregate_logged(self, fake_mh, caplog):
        """Prints and logs when aggregate/export raises."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.PromptUtils.select_site.return_value = "site-1"
        fake_mh.AnomalyMetricsDiscovery.discover.return_value = [{"metric_name": "m1", "description": "d"}]
        caplog.set_level(logging.ERROR, logger="src.export.site_anomaly_exporter")
        with (
            patch.object(SiteAnomalyExporter, "_anomaly_resolve_site_name", return_value="Site"),
            patch.object(SiteAnomalyExporter, "_aggregate_site_anomaly_data", side_effect=RuntimeError("boom")),
        ):
            SiteAnomalyExporter.anomaly_events()

        assert "Error exporting site anomaly events" in caplog.text


class TestDeviceAnomalyEvents:
    """Cover SiteAnomalyExporter.device_anomaly_events."""

    def test_no_site_selected(self, fake_mh, caplog):
        """Bails on empty site selection."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.PromptUtils.select_site.return_value = None

        caplog.set_level(logging.WARNING, logger="src.export.site_anomaly_exporter")
        SiteAnomalyExporter.device_anomaly_events()

        assert "No site selected" in caplog.text

    def test_no_device_selected(self, fake_mh, caplog):
        """Bails on empty device selection."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.PromptUtils.select_site.return_value = "site-1"
        fake_mh.PromptUtils.select_device_id_from_inventory.return_value = None
        caplog.set_level(logging.WARNING, logger="src.export.site_anomaly_exporter")
        with patch.object(SiteAnomalyExporter, "_anomaly_resolve_site_name", return_value="Site"):
            SiteAnomalyExporter.device_anomaly_events()

        assert "No device selected" in caplog.text

    def test_happy_path(self, fake_mh):
        """Fetches, aggregates, exports on happy path."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.PromptUtils.select_site.return_value = "site-1"
        fake_mh.PromptUtils.select_device_id_from_inventory.return_value = ("aa:bb", "AP1")
        with (
            patch.object(SiteAnomalyExporter, "_anomaly_resolve_site_name", return_value="Site"),
            patch.object(SiteAnomalyExporter, "_aggregate_device_anomaly_data", return_value=([{"x": 1}], 1)) as agg,
            patch.object(SiteAnomalyExporter, "_export_anomaly_data") as exp,
        ):
            SiteAnomalyExporter.device_anomaly_events()

        agg.assert_called_once()
        exp.assert_called_once()

    def test_exception_logs(self, fake_mh, caplog):
        """Prints and logs on aggregate exception."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.PromptUtils.select_site.return_value = "site-1"
        fake_mh.PromptUtils.select_device_id_from_inventory.return_value = ("aa:bb", "AP1")
        caplog.set_level(logging.ERROR, logger="src.export.site_anomaly_exporter")
        with (
            patch.object(SiteAnomalyExporter, "_anomaly_resolve_site_name", return_value="Site"),
            patch.object(SiteAnomalyExporter, "_aggregate_device_anomaly_data", side_effect=RuntimeError("boom")),
        ):
            SiteAnomalyExporter.device_anomaly_events()

        assert "Error exporting device anomaly events" in caplog.text


class TestBuildDeviceFilename:
    """Cover _build_device_filename."""

    def test_builds_sanitized_filename(self, fake_mh):
        """Sanitizes site and device parts before composing filename."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        result = SiteAnomalyExporter._build_device_filename("My Site", "My AP")

        assert result == "SiteDeviceAnomalyEvents_My_Site_My_AP.csv"


class TestDiscoverSiteAnomalyMetrics:
    """Cover _discover_site_anomaly_metrics."""

    def test_empty_metrics_warns(self, fake_mh, caplog):
        """Returns [] and warns when discovery is empty."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.AnomalyMetricsDiscovery.discover.return_value = []

        caplog.set_level(logging.WARNING, logger="src.export.site_anomaly_exporter")
        result = SiteAnomalyExporter._discover_site_anomaly_metrics()

        assert result == []
        assert "No potential anomaly metrics found" in caplog.text

    def test_returns_metric_names(self, fake_mh):
        """Returns list of metric names when discovery non-empty."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.AnomalyMetricsDiscovery.discover.return_value = [
            {"metric_name": "m1", "description": "desc" * 20},
            {"metric_name": "m2", "description": "short"},
        ]

        result = SiteAnomalyExporter._discover_site_anomaly_metrics()

        assert result == ["m1", "m2"]


class TestFetchOneAnomalyMetric:
    """Cover _fetch_one_anomaly_metric (site + device shared)."""

    def test_returns_tagged_data(self, fake_mh):
        """Tags the response data with metric, data_type, and caller tags."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        response = MagicMock()
        response.data = {"row": 1}
        fetch = MagicMock(return_value=response)

        result = SiteAnomalyExporter._fetch_one_anomaly_metric(
            fetch, "metric1", {"site_id": "s1"}, ("scope label", "typ")
        )

        assert result == {"row": 1, "metric_type": "metric1", "data_type": "typ", "site_id": "s1"}

    def test_returns_none_on_empty_data(self, fake_mh, caplog):
        """Returns None when response data is empty."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        response = MagicMock()
        response.data = {}
        fetch = MagicMock(return_value=response)

        caplog.set_level(logging.INFO, logger="src.export.site_anomaly_exporter")
        result = SiteAnomalyExporter._fetch_one_anomaly_metric(fetch, "metric1", {}, ("scope", "typ"))

        assert result is None
        assert "No metric1 scope available" in caplog.text

    def test_returns_none_on_exception(self, fake_mh, caplog):
        """Returns None and warns when fetch raises."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fetch = MagicMock(side_effect=RuntimeError("boom"))

        caplog.set_level(logging.WARNING, logger="src.export.site_anomaly_exporter")
        result = SiteAnomalyExporter._fetch_one_anomaly_metric(fetch, "metric1", {}, ("scope", "typ"))

        assert result is None
        assert "Error retrieving metric1 scope" in caplog.text


class TestRunAnomalyMetricLoop:
    """Cover _run_anomaly_metric_loop."""

    def test_collects_rows_and_restores_loggers(self, fake_mh):
        """Appends only non-None rows; restore is called via finally."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        with (
            patch.object(SiteAnomalyExporter, "_anomaly_suppress_mistapi_loggers", return_value={"lg": 20}),
            patch.object(SiteAnomalyExporter, "_anomaly_restore_loggers") as restore,
            patch.object(SiteAnomalyExporter, "_fetch_one_anomaly_metric", side_effect=[{"a": 1}, None]),
        ):
            builder = lambda m: MagicMock()  # noqa: E731
            rows, count = SiteAnomalyExporter._run_anomaly_metric_loop(["m1", "m2"], builder, {}, ("s", "t"))

        assert rows == [{"a": 1}]
        assert count == 1
        restore.assert_called_once_with({"lg": 20})


class TestAggregateSiteAnomalyData:
    """Cover _aggregate_site_anomaly_data."""

    def test_delegates_to_loop(self, fake_mh):
        """Builds site tags/scope and delegates to _run_anomaly_metric_loop."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        with patch.object(
            SiteAnomalyExporter,
            "_run_anomaly_metric_loop",
            return_value=([{"r": 1}], 1),
        ) as loop:
            rows, count = SiteAnomalyExporter._aggregate_site_anomaly_data("s1", "Site", ["m1"])

        assert rows == [{"r": 1}]
        assert count == 1
        args = loop.call_args[0]
        assert args[0] == ["m1"]
        assert args[2] == {"site_id": "s1", "site_name": "Site"}
        assert args[3] == ("anomaly events", "site_anomaly_events")


class TestAggregateDeviceAnomalyData:
    """Cover _aggregate_device_anomaly_data."""

    def test_delegates_to_loop(self, fake_mh):
        """Builds device tags/scope and delegates to _run_anomaly_metric_loop."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        with patch.object(
            SiteAnomalyExporter,
            "_run_anomaly_metric_loop",
            return_value=([{"r": 1}], 1),
        ) as loop:
            rows, count = SiteAnomalyExporter._aggregate_device_anomaly_data("s1", "Site", "aa:bb", "AP1", ["m1"])

        assert rows == [{"r": 1}]
        assert count == 1
        tags = loop.call_args[0][2]
        assert tags["device_mac"] == "aa:bb"
        assert tags["device_name"] == "AP1"
        assert loop.call_args[0][3] == ("device anomaly data", "device_anomaly_events")


class TestExportAnomalyData:
    """Cover _export_anomaly_data (site + device shared)."""

    def test_writes_flattened_data(self, fake_mh):
        """Flattens + escapes + writes when data present."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        with patch("src.export.site_anomaly_exporter.DataProcessingUtils") as dpu:
            dpu.flatten_nested_fields.return_value = [{"flat": 1}]
            dpu.escape_multiline.return_value = [{"escaped": 1}]
            SiteAnomalyExporter._export_anomaly_data([{"raw": 1}], "out.csv", "site anomaly event", 1, "Site")

        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([{"escaped": 1}], "out.csv")

    def test_writes_empty_csv_when_no_data(self, fake_mh, caplog):
        """Writes empty CSV when no data collected."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        caplog.set_level(logging.WARNING, logger="src.export.site_anomaly_exporter")
        SiteAnomalyExporter._export_anomaly_data([], "out.csv", "site anomaly event", 0, "Site")

        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([], "out.csv")
        assert "no data available" in caplog.text


class TestAnomalyResolveSiteName:
    """Cover _anomaly_resolve_site_name."""

    def test_returns_name_on_match(self, fake_mh):
        """Returns the site name when the site is in the list."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.mistapi.get_all.return_value = [{"id": "s1", "name": "MySite"}]

        result = SiteAnomalyExporter._anomaly_resolve_site_name("s1")

        assert result == "MySite"

    def test_returns_id_when_no_match(self, fake_mh):
        """Falls back to id when the site is not found."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.mistapi.get_all.return_value = [{"id": "other", "name": "X"}]

        result = SiteAnomalyExporter._anomaly_resolve_site_name("s1")

        assert result == "s1"

    def test_returns_id_on_exception(self, fake_mh):
        """Falls back to id when the lookup raises."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.mistapi.api.v1.sites.listSites.side_effect = RuntimeError("boom")

        result = SiteAnomalyExporter._anomaly_resolve_site_name("s1")

        assert result == "s1"


class TestAnomalyLookupClientHostname:
    """Cover _anomaly_lookup_client_hostname."""

    def test_returns_hostname(self, fake_mh):
        """Reads hostname field on match."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        response = MagicMock()
        response.data = [{"mac": "aa", "hostname": "H1"}]
        fake_mh.mistapi.api.v1.sites.stats.listSiteWirelessClientsStats.return_value = response

        result = SiteAnomalyExporter._anomaly_lookup_client_hostname("s1", "aa")

        assert result == "H1"

    def test_falls_back_to_name(self, fake_mh):
        """Uses name field when hostname missing."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        response = MagicMock()
        response.data = [{"mac": "aa", "name": "NamedClient"}]
        fake_mh.mistapi.api.v1.sites.stats.listSiteWirelessClientsStats.return_value = response

        result = SiteAnomalyExporter._anomaly_lookup_client_hostname("s1", "aa")

        assert result == "NamedClient"

    def test_returns_unknown_when_no_fields(self, fake_mh):
        """Returns 'Unknown' when neither hostname nor name is present."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        response = MagicMock()
        response.data = [{"mac": "aa"}]
        fake_mh.mistapi.api.v1.sites.stats.listSiteWirelessClientsStats.return_value = response

        result = SiteAnomalyExporter._anomaly_lookup_client_hostname("s1", "aa")

        assert result == "Unknown"

    def test_returns_unknown_when_no_match(self, fake_mh):
        """Returns 'Unknown' when client MAC is absent from stats."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        response = MagicMock()
        response.data = [{"mac": "other"}]
        fake_mh.mistapi.api.v1.sites.stats.listSiteWirelessClientsStats.return_value = response

        result = SiteAnomalyExporter._anomaly_lookup_client_hostname("s1", "aa")

        assert result == "Unknown"

    def test_returns_mac_on_exception(self, fake_mh):
        """Falls back to MAC when the lookup raises."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.mistapi.api.v1.sites.stats.listSiteWirelessClientsStats.side_effect = RuntimeError("boom")

        result = SiteAnomalyExporter._anomaly_lookup_client_hostname("s1", "aa:bb")

        assert result == "aa:bb"


class TestSuppressAndRestoreLoggers:
    """Cover _anomaly_suppress_mistapi_loggers and _anomaly_restore_loggers."""

    def test_suppress_captures_and_sets_critical(self, fake_mh):
        """Captures original level and raises to CRITICAL for known mistapi loggers."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        logging.getLogger("apirequest").setLevel(logging.INFO)
        try:
            original = SiteAnomalyExporter._anomaly_suppress_mistapi_loggers()
            assert original["apirequest"] == logging.INFO
            assert logging.getLogger("apirequest").level == logging.CRITICAL
        finally:
            logging.getLogger("apirequest").setLevel(logging.NOTSET)

    def test_restore_sets_levels_back(self, fake_mh):
        """Restore reinstates the saved logger levels."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        logging.getLogger("apirequest").setLevel(logging.CRITICAL)
        SiteAnomalyExporter._anomaly_restore_loggers({"apirequest": logging.INFO})
        try:
            assert logging.getLogger("apirequest").level == logging.INFO
        finally:
            logging.getLogger("apirequest").setLevel(logging.NOTSET)


class TestAnomalyFetchOneMetric:
    """Cover _anomaly_fetch_one_metric (client-level)."""

    def test_tags_data(self, fake_mh):
        """Tags the returned client anomaly record with site/client metadata."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        response = MagicMock()
        response.data = {"payload": 1}
        fake_mh.mistapi.api.v1.sites.anomaly.getSiteAnomalyEventsForClient.return_value = response

        result = SiteAnomalyExporter._anomaly_fetch_one_metric("s1", "aa", "Site", "Host", "m1")

        assert result["metric_type"] == "m1"
        assert result["site_id"] == "s1"
        assert result["client_mac"] == "aa"
        assert result["client_hostname"] == "Host"
        assert result["data_type"] == "client_anomaly_events"

    def test_returns_none_on_empty(self, fake_mh):
        """Returns None when the response is empty."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        response = MagicMock()
        response.data = {}
        fake_mh.mistapi.api.v1.sites.anomaly.getSiteAnomalyEventsForClient.return_value = response

        result = SiteAnomalyExporter._anomaly_fetch_one_metric("s1", "aa", "Site", "Host", "m1")

        assert result is None


class TestAnomalyHandleMetricResult:
    """Cover _anomaly_handle_metric_result."""

    def test_appends_and_returns_one(self, fake_mh, caplog):
        """Appends record when non-None; returns 1."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        acc: list = []
        result = SiteAnomalyExporter._anomaly_handle_metric_result({"row": 1}, "m1", "aa", acc)

        assert result == 1
        assert acc == [{"row": 1}]

    def test_returns_zero_when_none(self, fake_mh, caplog):
        """Returns 0 without appending when record is None."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        caplog.set_level(logging.INFO, logger="src.export.site_anomaly_exporter")
        acc: list = []
        result = SiteAnomalyExporter._anomaly_handle_metric_result(None, "m1", "aa", acc)

        assert result == 0
        assert acc == []
        assert "No m1 client anomaly data available" in caplog.text


class TestAnomalyCollectMetrics:
    """Cover _anomaly_collect_metrics."""

    def test_iterates_all_client_metrics(self, fake_mh):
        """Loops the three client anomaly metrics and delegates fetch+handle."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        with (
            patch.object(
                SiteAnomalyExporter,
                "_anomaly_fetch_one_metric",
                side_effect=[{"a": 1}, None, {"c": 3}],
            ),
            patch.object(
                SiteAnomalyExporter,
                "_anomaly_handle_metric_result",
                side_effect=[1, 0, 1],
            ),
        ):
            rows, count = SiteAnomalyExporter._anomaly_collect_metrics("s1", "aa", "Site", "Host")

        assert count == 2

    def test_exception_in_metric_isolated(self, fake_mh, caplog):
        """Prints and warns on per-metric failure without aborting the loop."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        caplog.set_level(logging.WARNING, logger="src.export.site_anomaly_exporter")
        with patch.object(
            SiteAnomalyExporter,
            "_anomaly_fetch_one_metric",
            side_effect=RuntimeError("boom"),
        ):
            rows, count = SiteAnomalyExporter._anomaly_collect_metrics("s1", "aa", "Site", "Host")

        assert count == 0
        assert "Error retrieving" in caplog.text


class TestAnomalyExport:
    """Cover _anomaly_export (client-level)."""

    def test_writes_flattened_data(self, fake_mh):
        """Flattens and writes when data present."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        with patch("src.export.site_anomaly_exporter.DataProcessingUtils") as dpu:
            dpu.flatten_nested_fields.return_value = [{"flat": 1}]
            dpu.escape_multiline.return_value = [{"escaped": 1}]
            SiteAnomalyExporter._anomaly_export([{"raw": 1}], 1, "aa", "out.csv")

        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([{"escaped": 1}], "out.csv")

    def test_writes_empty_when_no_data(self, fake_mh, caplog):
        """Writes an empty CSV when no data was collected."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        caplog.set_level(logging.WARNING, logger="src.export.site_anomaly_exporter")
        SiteAnomalyExporter._anomaly_export([], 0, "aa", "out.csv")

        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([], "out.csv")
        assert "no data available" in caplog.text


class TestAnomalyPrepare:
    """Cover _anomaly_prepare."""

    def test_happy_path_returns_context(self, fake_mh):
        """Returns tuple of resolved context on happy path."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.PromptUtils.select_site.return_value = "s1"
        fake_mh.PromptClientUtils.select_client.return_value = ("aa:bb:cc", None, None)
        with (
            patch.object(SiteAnomalyExporter, "_anomaly_resolve_site_name", return_value="Site A"),
            patch.object(SiteAnomalyExporter, "_anomaly_lookup_client_hostname", return_value="Host"),
        ):
            result = SiteAnomalyExporter._anomaly_prepare()

        assert result is not None
        site_id, site_name, client_mac, client_hostname, filename = result
        assert site_id == "s1"
        assert site_name == "Site A"
        assert client_mac == "aa:bb:cc"
        assert client_hostname == "Host"
        assert filename == "SiteClientAnomalyEvents_Site_A_aabbcc.csv"

    def test_returns_none_when_no_site(self, fake_mh, caplog):
        """Returns None when the operator cancels site selection."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.PromptUtils.select_site.return_value = None

        caplog.set_level(logging.WARNING, logger="src.export.site_anomaly_exporter")
        result = SiteAnomalyExporter._anomaly_prepare()

        assert result is None
        assert "No site selected" in caplog.text

    def test_returns_none_when_no_client(self, fake_mh, caplog):
        """Returns None when the operator cancels client selection."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        fake_mh.PromptUtils.select_site.return_value = "s1"
        fake_mh.PromptClientUtils.select_client.return_value = (None, None, None)
        caplog.set_level(logging.WARNING, logger="src.export.site_anomaly_exporter")
        with patch.object(SiteAnomalyExporter, "_anomaly_resolve_site_name", return_value="Site"):
            result = SiteAnomalyExporter._anomaly_prepare()

        assert result is None
        assert "No client selected" in caplog.text


class TestClientAnomalyEvents:
    """Cover SiteAnomalyExporter.client_anomaly_events."""

    def test_cancelled_returns_early(self, fake_mh):
        """Bails when _anomaly_prepare returns None."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        with (
            patch.object(SiteAnomalyExporter, "_anomaly_prepare", return_value=None),
            patch.object(SiteAnomalyExporter, "_anomaly_suppress_mistapi_loggers") as suppress,
        ):
            SiteAnomalyExporter.client_anomaly_events()

        suppress.assert_not_called()

    def test_happy_path_restores_loggers(self, fake_mh):
        """Collects, exports, and always restores loggers via finally."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        with (
            patch.object(
                SiteAnomalyExporter,
                "_anomaly_prepare",
                return_value=("s1", "Site", "aa", "Host", "out.csv"),
            ),
            patch.object(SiteAnomalyExporter, "_anomaly_suppress_mistapi_loggers", return_value={"lg": 20}),
            patch.object(SiteAnomalyExporter, "_anomaly_restore_loggers") as restore,
            patch.object(SiteAnomalyExporter, "_anomaly_collect_metrics", return_value=([{"row": 1}], 1)),
            patch.object(SiteAnomalyExporter, "_anomaly_export") as exp,
        ):
            SiteAnomalyExporter.client_anomaly_events()

        exp.assert_called_once()
        restore.assert_called_once_with({"lg": 20})

    def test_exception_still_restores_loggers(self, fake_mh, caplog):
        """Prints, logs, and still restores loggers when collect/export raises."""
        from src.export.site_anomaly_exporter import SiteAnomalyExporter

        caplog.set_level(logging.ERROR, logger="src.export.site_anomaly_exporter")
        with (
            patch.object(
                SiteAnomalyExporter,
                "_anomaly_prepare",
                return_value=("s1", "Site", "aa", "Host", "out.csv"),
            ),
            patch.object(SiteAnomalyExporter, "_anomaly_suppress_mistapi_loggers", return_value={}),
            patch.object(SiteAnomalyExporter, "_anomaly_restore_loggers") as restore,
            patch.object(SiteAnomalyExporter, "_anomaly_collect_metrics", side_effect=RuntimeError("boom")),
        ):
            SiteAnomalyExporter.client_anomaly_events()

        assert "Error exporting client anomaly events" in caplog.text
        restore.assert_called_once()
