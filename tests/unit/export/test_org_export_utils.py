"""Unit tests for ``src.export.org_export_utils``.

Why:
    #878 tranche 21 -- un-omit ``org_export_utils.py`` from the coverage
    configuration and pin behavior via a full test suite so future refactors
    of the generic org-level export helpers (SLE summary, insight metrics,
    parameterized metric expansion, NAC/BGP/audit-log exports, and service
    delegates like the E911 BSSID report) cannot silently regress. Covers
    every branch in the module including guard clauses, exception paths,
    empty-payload handling, and the three-way audit-log kwarg dispatch.
"""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def fake_mh(monkeypatch):
    """Install a stub ``MistHelper`` module in ``sys.modules``.

    Why:
        ``OrgExportUtils`` reaches out to many ``mh.*`` helpers through a
        lazy ``importlib.import_module("MistHelper")`` call: ``apisession``,
        ``APIDataFetcher``, ``ProgressContext``, ``PROGRESS_EMITTER``,
        ``InsightMetricsUtils``, ``ConfigUtils``, ``DataExporter``,
        ``DEFAULT_API_PAGE_LIMIT``, ``InputUtils``, and
        ``E911BSSIDReportGenerator``. The real MistHelper module has heavy
        side effects and network hooks, so tests replace it with a
        lightweight ``ModuleType`` populated with ``MagicMock`` stand-ins.

    Returns:
        The stubbed ``MistHelper`` module (also registered in ``sys.modules``).
    """
    mh = ModuleType("MistHelper")
    mh.apisession = MagicMock()
    mh.APIDataFetcher = MagicMock()
    mh.ProgressContext = MagicMock()
    mh.PROGRESS_EMITTER = MagicMock()
    mh.InsightMetricsUtils = MagicMock()
    mh.ConfigUtils = MagicMock()
    mh.DataExporter = MagicMock()
    mh.DEFAULT_API_PAGE_LIMIT = 1000
    mh.InputUtils = MagicMock()
    mh.E911BSSIDReportGenerator = MagicMock()
    monkeypatch.setitem(sys.modules, "MistHelper", mh)
    return mh


# ---------------------------------------------------------------------------
# export_data (generic builder)
# ---------------------------------------------------------------------------


class TestExportData:
    """Cover the two branches of ``export_data`` (with/without limit) plus extras."""

    def test_with_limit(self, fake_mh):
        """When limit is set it should be passed as an APIDataFetcher kwarg."""
        from src.export.org_export_utils import OrgExportUtils

        api_call = MagicMock()
        OrgExportUtils.export_data(api_call, "site stats", sort_key="name", limit=500, extra="x")
        fake_mh.APIDataFetcher.assert_called_once()
        kwargs = fake_mh.APIDataFetcher.call_args.kwargs
        assert kwargs["limit"] == 500
        assert kwargs["extra"] == "x"
        assert kwargs["filename"] == "OrgSitestats.csv"
        assert kwargs["sort_key"] == "name"

    def test_without_limit(self, fake_mh):
        """When limit is None the fetcher must not receive a limit kwarg."""
        from src.export.org_export_utils import OrgExportUtils

        api_call = MagicMock()
        OrgExportUtils.export_data(api_call, "e911 report", limit=None)
        kwargs = fake_mh.APIDataFetcher.call_args.kwargs
        assert "limit" not in kwargs
        assert kwargs["filename"] == "OrgE911Report.csv"


# ---------------------------------------------------------------------------
# SLE summary block
# ---------------------------------------------------------------------------


class TestCollectOneSleType:
    """Cover ``_collect_one_sle_type`` success + exception."""

    def test_success_tags_and_appends(self, fake_mh):
        """Successful fetch should tag each row with sle_type and append them."""
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        rows = [{"site": "a"}, {"site": "b"}]
        with (
            patch.object(mod.mistapi.api.v1.orgs.insights, "getOrgSitesSle", return_value="resp"),
            patch.object(mod.mistapi, "get_all", return_value=rows),
        ):
            accum: list = []
            OrgExportUtils._collect_one_sle_type("org1", "wifi", accum)
        assert accum == [{"site": "a", "sle_type": "wifi"}, {"site": "b", "sle_type": "wifi"}]

    def test_get_all_returns_none(self, fake_mh):
        """When get_all returns None the accumulator stays empty (no crash)."""
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        with (
            patch.object(mod.mistapi.api.v1.orgs.insights, "getOrgSitesSle", return_value="resp"),
            patch.object(mod.mistapi, "get_all", return_value=None),
        ):
            accum: list = []
            OrgExportUtils._collect_one_sle_type("org1", "wan", accum)
        assert accum == []

    def test_exception_is_swallowed(self, fake_mh, caplog):
        """Exceptions must be logged as a warning and NOT propagated."""
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        with patch.object(mod.mistapi.api.v1.orgs.insights, "getOrgSitesSle", side_effect=RuntimeError("boom")):
            accum: list = []
            OrgExportUtils._collect_one_sle_type("org1", "wired", accum)
        assert accum == []


class TestPersistSitesSleSummary:
    """Cover both branches of ``_persist_sites_sle_summary``."""

    def test_with_data(self, fake_mh, capsys):
        """Data path should flatten, escape, and write."""
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        rows = [{"site": "a", "sle_type": "wifi"}]
        with (
            patch.object(mod.DataProcessingUtils, "flatten_nested_fields", return_value=rows),
            patch.object(mod.DataProcessingUtils, "escape_multiline", return_value=rows),
        ):
            OrgExportUtils._persist_sites_sle_summary(rows)
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(rows, "OrgSitesSLESummary.csv")
        assert "1 sites SLE summary exported" in capsys.readouterr().out

    def test_empty(self, fake_mh, capsys):
        """Empty path should still write an empty CSV and warn the user."""
        from src.export.org_export_utils import OrgExportUtils

        OrgExportUtils._persist_sites_sle_summary([])
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([], "OrgSitesSLESummary.csv")
        assert "0 sites SLE summary" in capsys.readouterr().out


class TestGatherAllSitesSle:
    """Cover ``_gather_all_sites_sle`` with and without an emitter."""

    def test_with_emitter_ticks_progress(self, fake_mh):
        """Progress emitter should be ticked once per SLE type."""
        from src.export.org_export_utils import OrgExportUtils

        emitter = MagicMock()
        with patch.object(OrgExportUtils, "_collect_one_sle_type") as coll:
            rows, done = OrgExportUtils._gather_all_sites_sle("org1", ["wifi", "wan"], emitter)
        assert done == 2
        assert coll.call_count == 2
        assert emitter.emit_progress_tick.call_count == 2

    def test_without_emitter(self, fake_mh):
        """Without an emitter no ticks are fired but items are still counted."""
        from src.export.org_export_utils import OrgExportUtils

        with patch.object(OrgExportUtils, "_collect_one_sle_type"):
            rows, done = OrgExportUtils._gather_all_sites_sle("org1", ["wifi"], None)
        assert done == 1


class TestSitesSleSummary:
    """Cover the ``sites_sle_summary`` orchestrator."""

    def test_with_emitter(self, fake_mh):
        """Emitter present: start + complete both invoked exactly once."""
        from src.export.org_export_utils import OrgExportUtils

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org1"
        with (
            patch.object(OrgExportUtils, "_gather_all_sites_sle", return_value=([{"x": 1}], 3)),
            patch.object(OrgExportUtils, "_persist_sites_sle_summary") as persist,
        ):
            OrgExportUtils.sites_sle_summary()
        fake_mh.PROGRESS_EMITTER.emit_progress_start.assert_called_once()
        fake_mh.PROGRESS_EMITTER.emit_progress_complete.assert_called_once()
        persist.assert_called_once_with([{"x": 1}])

    def test_without_emitter(self, fake_mh):
        """Emitter is None: neither start nor complete may be dereferenced."""
        from src.export.org_export_utils import OrgExportUtils

        fake_mh.PROGRESS_EMITTER = None
        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org1"
        with (
            patch.object(OrgExportUtils, "_gather_all_sites_sle", return_value=([], 0)),
            patch.object(OrgExportUtils, "_persist_sites_sle_summary"),
        ):
            OrgExportUtils.sites_sle_summary()


# ---------------------------------------------------------------------------
# Metric choice extraction
# ---------------------------------------------------------------------------


class TestMetricChoiceList:
    """Cover the three guard branches of ``_metric_choice_list``."""

    def test_non_dict_definition(self):
        from src.export.org_export_utils import OrgExportUtils

        assert OrgExportUtils._metric_choice_list("not-a-dict") == []

    def test_non_dict_params(self):
        from src.export.org_export_utils import OrgExportUtils

        assert OrgExportUtils._metric_choice_list({"params": "bad"}) == []

    def test_non_dict_metric_param(self):
        from src.export.org_export_utils import OrgExportUtils

        assert OrgExportUtils._metric_choice_list({"params": {"metric": "bad"}}) == []

    def test_choices_not_list(self):
        from src.export.org_export_utils import OrgExportUtils

        assert OrgExportUtils._metric_choice_list({"params": {"metric": {"choices": "no"}}}) == []

    def test_happy_path(self):
        from src.export.org_export_utils import OrgExportUtils

        result = OrgExportUtils._metric_choice_list({"params": {"metric": {"choices": ["a", "b"]}}})
        assert result == ["a", "b"]


class TestOrgValidChoices:
    """Cover the org-scope-valid filter."""

    def test_filters_out_invalid_choices(self):
        from src.export.org_export_utils import OrgExportUtils

        result = OrgExportUtils._org_valid_choices(["bytes", "total_port_count", "rx_bytes"])
        assert result == ["bytes", "rx_bytes"]


class TestExtractMetricChoices:
    """Cover ``_extract_metric_choices`` guard and only-if-choices branches."""

    def test_non_dict_definitions_returns_empty(self):
        from src.export.org_export_utils import OrgExportUtils

        assert OrgExportUtils._extract_metric_choices("bad") == {}

    def test_only_metrics_with_choices_kept(self):
        from src.export.org_export_utils import OrgExportUtils

        defs = {
            "with_valid": {"params": {"metric": {"choices": ["bytes", "not-valid"]}}},
            "no_choices": {"params": {"metric": {"choices": []}}},
            "no_org_valid": {"params": {"metric": {"choices": ["total_port_count"]}}},
        }
        result = OrgExportUtils._extract_metric_choices(defs)
        assert result == {"with_valid": ["bytes"]}


class TestLoadParameterizedMetricChoices:
    """Cover the try/except around ``listInsightMetrics``."""

    def test_success(self, fake_mh):
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        response = SimpleNamespace(data={"m1": {"params": {"metric": {"choices": ["bytes"]}}}})
        with patch.object(mod.mistapi.api.v1.const.insight_metrics, "listInsightMetrics", return_value=response):
            result = OrgExportUtils._load_parameterized_metric_choices()
        assert result == {"m1": ["bytes"]}

    def test_exception_returns_empty(self, fake_mh):
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        with patch.object(
            mod.mistapi.api.v1.const.insight_metrics, "listInsightMetrics", side_effect=RuntimeError("boom")
        ):
            assert OrgExportUtils._load_parameterized_metric_choices() == {}


# ---------------------------------------------------------------------------
# Per-choice fetch
# ---------------------------------------------------------------------------


class TestFetchSingleMetricChoice:
    """Cover session-None guard, empty payload, and dict/non-dict normalization."""

    def test_no_session_returns_none(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        fake_mh.apisession = None
        result = OrgExportUtils._fetch_single_metric_choice("o", "m", "bytes", "7d")
        assert result is None

    def test_success_dict_payload(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        response = SimpleNamespace(data={"foo": "bar"})
        fake_mh.apisession.mist_get = MagicMock(return_value=response)
        result = OrgExportUtils._fetch_single_metric_choice("o", "m", "bytes", "7d")
        assert result == {
            "foo": "bar",
            "metric_type": "m:bytes",
            "org_id": "o",
            "metric_param": "bytes",
        }

    def test_success_non_dict_payload(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        response = SimpleNamespace(data=[1, 2, 3])
        fake_mh.apisession.mist_get = MagicMock(return_value=response)
        result = OrgExportUtils._fetch_single_metric_choice("o", "m", "bytes", "7d")
        assert result["results"] == [1, 2, 3]
        assert result["metric_type"] == "m:bytes"

    def test_empty_payload_returns_none(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        response = SimpleNamespace(data=None)
        fake_mh.apisession.mist_get = MagicMock(return_value=response)
        assert OrgExportUtils._fetch_single_metric_choice("o", "m", "bytes", "7d") is None

    def test_exception_returns_none(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        fake_mh.apisession.mist_get = MagicMock(side_effect=RuntimeError("boom"))
        assert OrgExportUtils._fetch_single_metric_choice("o", "m", "bytes", "7d") is None


class TestFetchParameterizedOrgMetric:
    """Cover both success and failure counting branches."""

    def test_mixed_results(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        with patch.object(
            OrgExportUtils,
            "_fetch_single_metric_choice",
            side_effect=[{"ok": True}, None, {"ok": True}],
        ):
            records, ok, fail = OrgExportUtils._fetch_parameterized_org_metric("o", "m", ["a", "b", "c"], "7d")
        assert len(records) == 2
        assert ok == 2
        assert fail == 1


# ---------------------------------------------------------------------------
# Insight metric dispatch
# ---------------------------------------------------------------------------


class TestInsightIsWorstSitesMetric:
    """Cover the three ways a metric is a worst-sites metric."""

    def test_worst_sites_substring(self):
        from src.export.org_export_utils import OrgExportUtils

        assert OrgExportUtils._insight_is_worst_sites_metric("worst-sites-by-sle")

    def test_sites_sle(self):
        from src.export.org_export_utils import OrgExportUtils

        assert OrgExportUtils._insight_is_worst_sites_metric("sites-sle")

    def test_sites_sle_filtered(self):
        from src.export.org_export_utils import OrgExportUtils

        assert OrgExportUtils._insight_is_worst_sites_metric("sites-sle-filtered")

    def test_default_metric(self):
        from src.export.org_export_utils import OrgExportUtils

        assert OrgExportUtils._insight_is_worst_sites_metric("client-metrics") is False


class TestInsightBuildSitesResult:
    """Trivial builder — pin the shape."""

    def test_shape(self):
        from src.export.org_export_utils import OrgExportUtils

        result = OrgExportUtils._insight_build_sites_result("o", "m", "wifi", [{"s": 1}])
        assert result["metric_type"] == "m_wifi"
        assert result["org_id"] == "o"
        assert result["sle_category"] == "wifi"
        assert result["data_source"] == "sites_sle_analysis"
        assert result["total_sites"] == 1
        assert result["sites_data"] == [{"s": 1}]
        assert result["original_metric"] == "m"


class TestInsightFetchOneSleCategory:
    """Cover success/empty/exception branches."""

    def test_success(self, fake_mh):
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        with (
            patch.object(mod.mistapi.api.v1.orgs.insights, "getOrgSitesSle", return_value="resp"),
            patch.object(mod.mistapi, "get_all", return_value=[{"s": 1}]),
        ):
            result = OrgExportUtils._insight_fetch_one_sle_category("o", "m", "wifi")
        assert result is not None
        assert result["total_sites"] == 1

    def test_empty_returns_none(self, fake_mh):
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        with (
            patch.object(mod.mistapi.api.v1.orgs.insights, "getOrgSitesSle", return_value="resp"),
            patch.object(mod.mistapi, "get_all", return_value=[]),
        ):
            assert OrgExportUtils._insight_fetch_one_sle_category("o", "m", "wifi") is None

    def test_exception_returns_none(self, fake_mh):
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        with patch.object(mod.mistapi.api.v1.orgs.insights, "getOrgSitesSle", side_effect=RuntimeError("boom")):
            assert OrgExportUtils._insight_fetch_one_sle_category("o", "m", "wifi") is None


class TestInsightFetchWorstSitesSle:
    """Cover mixed hits/misses across three SLE categories."""

    def test_mixed_categories(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        with patch.object(
            OrgExportUtils,
            "_insight_fetch_one_sle_category",
            side_effect=[{"a": 1}, None, {"b": 2}],
        ):
            records, retrieved, failed = OrgExportUtils._insight_fetch_worst_sites_sle("o", "m")
        assert len(records) == 2
        assert retrieved == 2
        assert failed == 0


class TestInsightFetchDefaultMetric:
    """Cover data + empty branches of the default fetcher."""

    def test_success(self, fake_mh):
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        response = SimpleNamespace(data={"payload": True})
        with patch.object(mod.mistapi.api.v1.orgs.insights, "getOrgSle", return_value=response):
            records, ok, fail = OrgExportUtils._insight_fetch_default_metric("o", "m")
        assert len(records) == 1
        assert records[0]["metric_type"] == "m"
        assert records[0]["org_id"] == "o"
        assert ok == 1
        assert fail == 0

    def test_empty_counts_as_failure(self, fake_mh):
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        response = SimpleNamespace(data=None)
        with patch.object(mod.mistapi.api.v1.orgs.insights, "getOrgSle", return_value=response):
            records, ok, fail = OrgExportUtils._insight_fetch_default_metric("o", "m")
        assert records == []
        assert ok == 0
        assert fail == 1


class TestInsightFetchOneMetric:
    """Cover the 3-way dispatch plus the outer exception handler."""

    def test_parameterized_branch(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        with patch.object(
            OrgExportUtils,
            "_fetch_parameterized_org_metric",
            return_value=([{"r": 1}], 1, 0),
        ):
            records, ok, fail = OrgExportUtils._insight_fetch_one_metric("o", "m1", {"m1": ["bytes"]})
        assert records == [{"r": 1}]
        assert (ok, fail) == (1, 0)

    def test_worst_sites_branch(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        with patch.object(OrgExportUtils, "_insight_fetch_worst_sites_sle", return_value=([{"r": 2}], 3, 0)):
            records, ok, fail = OrgExportUtils._insight_fetch_one_metric("o", "worst-sites-x", {})
        assert (ok, fail) == (3, 0)

    def test_default_branch(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        with patch.object(OrgExportUtils, "_insight_fetch_default_metric", return_value=([{"r": 3}], 1, 0)):
            records, ok, fail = OrgExportUtils._insight_fetch_one_metric("o", "client-x", {})
        assert (ok, fail) == (1, 0)

    def test_exception_returns_failure(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        with patch.object(OrgExportUtils, "_insight_fetch_default_metric", side_effect=RuntimeError("boom")):
            records, ok, fail = OrgExportUtils._insight_fetch_one_metric("o", "client-x", {})
        assert records == []
        assert (ok, fail) == (0, 1)


class TestInsightFetchSitesSleSummary:
    """Cover data + empty + exception branches of the summary fetcher."""

    def test_success(self, fake_mh):
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        with (
            patch.object(mod.mistapi.api.v1.orgs.insights, "getOrgSitesSle", return_value="resp"),
            patch.object(mod.mistapi, "get_all", return_value=[{"s": 1}, {"s": 2}]),
        ):
            records, ok, fail = OrgExportUtils._insight_fetch_sites_sle_summary("o")
        assert len(records) == 2
        assert all(r["metric_type"] == "org_sites_sle_summary" for r in records)
        assert ok == 1
        assert fail == 0

    def test_empty(self, fake_mh):
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        with (
            patch.object(mod.mistapi.api.v1.orgs.insights, "getOrgSitesSle", return_value="resp"),
            patch.object(mod.mistapi, "get_all", return_value=[]),
        ):
            records, ok, fail = OrgExportUtils._insight_fetch_sites_sle_summary("o")
        assert records == []
        assert (ok, fail) == (0, 0)

    def test_exception(self, fake_mh):
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        with patch.object(mod.mistapi.api.v1.orgs.insights, "getOrgSitesSle", side_effect=RuntimeError("boom")):
            records, ok, fail = OrgExportUtils._insight_fetch_sites_sle_summary("o")
        assert records == []
        assert (ok, fail) == (0, 1)


class TestInsightCollectAllMetrics:
    """Aggregate across metrics + summary."""

    def test_aggregation(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        with (
            patch.object(
                OrgExportUtils,
                "_insight_fetch_one_metric",
                side_effect=[([{"a": 1}], 1, 0), ([], 0, 1)],
            ),
            patch.object(
                OrgExportUtils,
                "_insight_fetch_sites_sle_summary",
                return_value=([{"b": 1}], 1, 0),
            ),
        ):
            records, ok, fail = OrgExportUtils._insight_collect_all_metrics("o", ["m1", "m2"], {})
        assert len(records) == 2
        assert ok == 2
        assert fail == 1


class TestInsightNormalizeRecords:
    """Fold four buckets."""

    def test_bucket_folding(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        fake_mh.InsightMetricsUtils.parse_to_normalized_data.return_value = {
            "summary": [{"s": 1}],
            "time_series": [{"t": 1}],
            "results": [{"r": 1}],
            "sites_data": [{"sd": 1}],
        }
        result = OrgExportUtils._insight_normalize_records([{"m": 1}, {"m": 2}], "o")
        assert len(result["summary"]) == 2
        assert len(result["time_series"]) == 2
        assert len(result["results"]) == 2
        assert len(result["sites_data"]) == 2


class TestInsightExportNormalized:
    """Writes 4 CSVs plus the legacy combined file."""

    def test_writes_four_plus_legacy(self, fake_mh):
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        buckets = {
            "summary": [{"s": 1}],
            "time_series": [{"t": 1}],
            "results": [{"r": 1}],
            "sites_data": [{"sd": 1}],
        }
        with (
            patch.object(OrgExportUtils, "_insight_normalize_records", return_value=buckets),
            patch.object(mod.DataProcessingUtils, "escape_multiline", side_effect=lambda x: x),
            patch.object(mod.DataProcessingUtils, "flatten_nested_fields", side_effect=lambda x: x),
            patch.object(OrgExportUtils, "_insight_write_combined") as combined,
        ):
            OrgExportUtils._insight_export_normalized([{"a": 1}], "o", 3)
        # 4 normalized writes fired via DataExporter
        assert fake_mh.DataExporter.write_with_format_selection.call_count == 4
        combined.assert_called_once_with([{"a": 1}])


class TestInsightWriteCombined:
    """Legacy combined write."""

    def test_writes_legacy(self, fake_mh):
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        with (
            patch.object(mod.DataProcessingUtils, "flatten_nested_fields", side_effect=lambda x: x),
            patch.object(mod.DataProcessingUtils, "escape_multiline", side_effect=lambda x: x),
        ):
            OrgExportUtils._insight_write_combined([{"a": 1}])
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(
            [{"a": 1}], "OrgInsightMetrics_Legacy.csv"
        )


class TestInsightWriteEmptyOutputs:
    """Both branches: with and without legacy file."""

    def test_with_legacy(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        OrgExportUtils._insight_write_empty_outputs(include_legacy=True)
        assert fake_mh.DataExporter.write_with_format_selection.call_count == 5

    def test_without_legacy(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        OrgExportUtils._insight_write_empty_outputs(include_legacy=False)
        assert fake_mh.DataExporter.write_with_format_selection.call_count == 4


class TestInsightSetupOrEmpty:
    """Cover the "no metrics" abort path plus the happy path."""

    def test_no_org_metrics_returns_none(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        fake_mh.InsightMetricsUtils.get_by_scope.return_value = []
        with patch.object(OrgExportUtils, "_insight_write_empty_outputs") as empty:
            result = OrgExportUtils._insight_setup_or_empty()
        assert result is None
        empty.assert_called_once_with(include_legacy=False)

    def test_happy_path(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        fake_mh.InsightMetricsUtils.get_by_scope.return_value = ["m1", "m2"]
        result = OrgExportUtils._insight_setup_or_empty()
        assert result == ["m1", "m2"]


class TestInsightReportTotals:
    """Trivial reporter."""

    def test_prints_and_logs(self, fake_mh, capsys):
        from src.export.org_export_utils import OrgExportUtils

        OrgExportUtils._insight_report_totals(3, 1)
        assert "3 successful" in capsys.readouterr().out


class TestInsightMetrics:
    """Cover the three outcomes of the top-level orchestrator."""

    def test_setup_returns_none_aborts(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        with patch.object(OrgExportUtils, "_insight_setup_or_empty", return_value=None):
            OrgExportUtils.insight_metrics()
        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.assert_not_called()

    def test_success_with_data_writes_normalized(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "o"
        with (
            patch.object(OrgExportUtils, "_insight_setup_or_empty", return_value=["m1"]),
            patch.object(OrgExportUtils, "_load_parameterized_metric_choices", return_value={}),
            patch.object(
                OrgExportUtils,
                "_insight_collect_all_metrics",
                return_value=([{"r": 1}], 1, 0),
            ),
            patch.object(OrgExportUtils, "_insight_report_totals"),
            patch.object(OrgExportUtils, "_insight_export_normalized") as export,
        ):
            OrgExportUtils.insight_metrics()
        export.assert_called_once()

    def test_success_no_data_writes_empties(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "o"
        with (
            patch.object(OrgExportUtils, "_insight_setup_or_empty", return_value=["m1"]),
            patch.object(OrgExportUtils, "_load_parameterized_metric_choices", return_value={}),
            patch.object(OrgExportUtils, "_insight_collect_all_metrics", return_value=([], 0, 1)),
            patch.object(OrgExportUtils, "_insight_report_totals"),
            patch.object(OrgExportUtils, "_insight_write_empty_outputs") as empty,
        ):
            OrgExportUtils.insight_metrics()
        empty.assert_called_once_with(include_legacy=True)

    def test_exception_writes_empties(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "o"
        with (
            patch.object(OrgExportUtils, "_insight_setup_or_empty", return_value=["m1"]),
            patch.object(OrgExportUtils, "_load_parameterized_metric_choices", return_value={}),
            patch.object(OrgExportUtils, "_insight_collect_all_metrics", side_effect=RuntimeError("boom")),
            patch.object(OrgExportUtils, "_insight_write_empty_outputs") as empty,
        ):
            OrgExportUtils.insight_metrics()
        empty.assert_called_once_with(include_legacy=True)


# ---------------------------------------------------------------------------
# Simple delegates
# ---------------------------------------------------------------------------


class TestSimpleDelegates:
    """Cover each thin delegate by asserting the export_data kwargs."""

    def _assert_calls(self, fake_mh, method, expected_data_type, expected_sort_key, extra_kwargs=None):
        """Invoke the delegate with export_data patched; assert kwargs match."""
        from src.export.org_export_utils import OrgExportUtils

        with patch.object(OrgExportUtils, "export_data") as export:
            getattr(OrgExportUtils, method)()
        assert export.call_args.kwargs["data_type"] == expected_data_type
        assert export.call_args.kwargs["sort_key"] == expected_sort_key
        if extra_kwargs:
            for key, val in extra_kwargs.items():
                assert export.call_args.kwargs[key] == val

    def test_nac_clients(self, fake_mh):
        self._assert_calls(fake_mh, "_nac_clients", "nac clients", "mac")

    def test_nac_tags(self, fake_mh):
        self._assert_calls(fake_mh, "_nac_tags", "nac tags", "name")

    def test_nac_portals(self, fake_mh):
        self._assert_calls(fake_mh, "_nac_portals", "nac portals", "name")

    def test_nac_rules(self, fake_mh):
        self._assert_calls(fake_mh, "_nac_rules", "nac rules", "name")

    def test_nac_events(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        with (
            patch("src.export.org_export_utils.TimeUtils.get_dynamic_lookback_hours", return_value=12),
            patch("src.export.org_export_utils.TimeUtils.log_dynamic_lookback"),
            patch.object(OrgExportUtils, "export_data") as export,
        ):
            OrgExportUtils._nac_events()
        assert export.call_args.kwargs["data_type"] == "nac events"
        assert export.call_args.kwargs["sort_key"] == "timestamp"
        assert export.call_args.kwargs["duration"] == "12h"

    def test_assets(self, fake_mh):
        self._assert_calls(fake_mh, "_assets", "assets", "name")

    def test_bgp_peers(self, fake_mh):
        self._assert_calls(fake_mh, "_bgp_peers", "bgp peers", "peer_ip")

    def test_tunnel_stats(self, fake_mh):
        self._assert_calls(fake_mh, "_tunnel_stats", "tunnel stats", "name")

    def test_site_stats(self, fake_mh):
        self._assert_calls(fake_mh, "_site_stats", "site stats", "name")

    def test_mxedge_stats(self, fake_mh):
        self._assert_calls(fake_mh, "_mxedge_stats", "mx edge stats", "name")

    def test_e911_report(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        with patch.object(OrgExportUtils, "export_data") as export:
            OrgExportUtils.e911_report()
        assert export.call_args.kwargs["data_type"] == "e911 report"
        assert export.call_args.kwargs["limit"] is None

    def test_jsi_pbn(self, fake_mh):
        self._assert_calls(fake_mh, "jsi_pbn", "jsi pbn", "id")

    def test_jsi_sirt(self, fake_mh):
        self._assert_calls(fake_mh, "jsi_sirt", "jsi sirt", "id")

    def test_ospf_stats(self, fake_mh):
        self._assert_calls(fake_mh, "ospf_stats", "ospf stats", "mac")

    def test_security_intel_profiles(self, fake_mh):
        self._assert_calls(fake_mh, "_security_intel_profiles", "security intel profiles", "name")

    def test_invites(self, fake_mh):
        """listOrgInvites is not exposed by the current mistapi SDK; patch it in."""
        from src.export.org_export_utils import OrgExportUtils

        with (
            patch(
                "mistapi.api.v1.orgs.invites.listOrgInvites",
                new=MagicMock(),
                create=True,
            ),
            patch.object(OrgExportUtils, "export_data") as export,
        ):
            OrgExportUtils._invites()
        assert export.call_args.kwargs["data_type"] == "invites"
        assert export.call_args.kwargs["sort_key"] == "email"


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------


class TestBuildAuditLogKwargs:
    """Cover the three branches of ``_build_audit_log_kwargs``."""

    def test_duration_branch(self):
        from src.export.org_export_utils import OrgExportUtils

        result = OrgExportUtils._build_audit_log_kwargs(False, "3h")
        assert result == {"limit": 1000, "duration": "3h"}

    def test_recent_branch(self):
        from src.export.org_export_utils import OrgExportUtils

        with (
            patch("src.export.org_export_utils.TimeUtils.get_dynamic_lookback_hours", return_value=24),
            patch("src.export.org_export_utils.TimeUtils.log_dynamic_lookback"),
        ):
            result = OrgExportUtils._build_audit_log_kwargs(False, None)
        assert result == {"limit": 1000, "duration": "24h"}

    def test_full_history_branch(self):
        from src.export.org_export_utils import OrgExportUtils

        result = OrgExportUtils._build_audit_log_kwargs(True, None)
        assert result == {"limit": 1000, "start": 0}


class TestAuditLogs:
    """Cover audit_logs success, no-data, and exception re-raise."""

    def test_success(self, fake_mh, capsys):
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "o"
        with (
            patch.object(mod.mistapi.api.v1.orgs.logs, "listOrgAuditLogs", return_value="resp"),
            patch.object(mod.mistapi, "get_all", return_value=[{"a": 1}]),
            patch.object(mod.DataProcessingUtils, "flatten_nested_fields", side_effect=lambda x: x),
            patch.object(mod.DataProcessingUtils, "escape_multiline", side_effect=lambda x: x),
        ):
            OrgExportUtils.audit_logs(full_history=False, duration="1h")
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([{"a": 1}], "OrgAuditLogs.csv")
        assert "1 audit logs exported" in capsys.readouterr().out

    def test_no_data_early_return(self, fake_mh):
        from src.export import org_export_utils as mod
        from src.export.org_export_utils import OrgExportUtils

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "o"
        with (
            patch.object(mod.mistapi.api.v1.orgs.logs, "listOrgAuditLogs", return_value="resp"),
            patch.object(mod.mistapi, "get_all", return_value=[]),
        ):
            OrgExportUtils.audit_logs(full_history=False, duration="1h")
        fake_mh.DataExporter.write_with_format_selection.assert_not_called()

    def test_exception_reraises(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.side_effect = RuntimeError("boom")
        with pytest.raises(RuntimeError, match="boom"):
            OrgExportUtils.audit_logs()


# ---------------------------------------------------------------------------
# Service delegates
# ---------------------------------------------------------------------------


class TestSleMetrics:
    """Cover the SLE metrics delegate.

    Why:
        Tranche 19 lesson: ``import package.submodule.name as alias`` inside a
        function body is NOT intercepted by ``sys.modules`` monkeypatching --
        the callable must be patched directly at its resolved import path.
    """

    def test_delegates_to_service(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        with patch("src.refactors.serial_cc.sle_metrics.SLEMetricsService.execute") as execute:
            OrgExportUtils.sle_metrics(fast=True)
        execute.assert_called_once_with(True)


class TestSsidTemplateConsolidation:
    """Cover the SSID template consolidation delegate."""

    def test_delegates(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        with patch(
            "src.ssid_consolidation.ssid_template_consolidation.SSIDTemplateConsolidationManager.execute"
        ) as execute:
            OrgExportUtils.ssid_template_consolidation()
        execute.assert_called_once()
        kwargs = execute.call_args.kwargs
        assert kwargs["apisession"] is fake_mh.apisession
        assert kwargs["page_limit"] == fake_mh.DEFAULT_API_PAGE_LIMIT


class TestE911BssidComplianceReport:
    """Cover the no-org early return and happy path."""

    def test_no_org_early_return(self, fake_mh, capsys):
        from src.export.org_export_utils import OrgExportUtils

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = None
        OrgExportUtils.e911_bssid_compliance_report()
        fake_mh.E911BSSIDReportGenerator.execute.assert_not_called()
        assert "No organization selected" in capsys.readouterr().out

    def test_happy_path(self, fake_mh):
        from src.export.org_export_utils import OrgExportUtils

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "o"
        OrgExportUtils.e911_bssid_compliance_report()
        fake_mh.E911BSSIDReportGenerator.execute.assert_called_once()
        kwargs = fake_mh.E911BSSIDReportGenerator.execute.call_args.kwargs
        assert kwargs["org_id"] == "o"


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------


class TestModuleImport:
    """Guard against future import-time regressions."""

    def test_module_importable(self):
        """The module must import without side effects."""
        from src.export import org_export_utils

        assert hasattr(org_export_utils, "OrgExportUtils")
