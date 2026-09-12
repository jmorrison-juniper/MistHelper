"""Wave 9 P2 coverage tests for src.export.site_insights.site_metric_operation.

Targets the menu-74 orchestrator ``SiteMetricOperation``. Exercises every
branch of ``execute``: cancel, empty metrics, non-empty export, per-metric
API failure, empty payload short-circuit, and the finalize-error path.
"""

from __future__ import annotations  # WHY: PEP 604 unions module-wide

import logging  # WHY: emit before/after action logs per project contract
from unittest.mock import MagicMock  # WHY: build interchangeable injected collaborators

import pytest  # WHY: caplog fixture typing for logger capture assertions

from src.export.site_insights.site_metric_operation import (  # WHY: SUTs under test
    SiteMetricOperation,
    SiteRunContext,
)


def _make_deps() -> dict:
    """Return the seven injected constructor kwargs as fresh MagicMocks."""
    logging.info("Building baseline injected deps for SiteMetricOperation")  # WHY: pre-action trace
    apisession = MagicMock(name="apisession")  # WHY: opaque session passed through
    prompt_utils = MagicMock(name="PromptUtils")  # WHY: select_site stub bound per-test
    data_processing = MagicMock(name="DataProcessingUtils")  # WHY: flatten + escape helpers
    data_processing.flatten_nested_fields.side_effect = lambda x: x  # WHY: identity passthrough
    data_processing.escape_multiline.side_effect = lambda x: x  # WHY: identity passthrough
    data_exporter = MagicMock(name="DataExporter")  # WHY: write_with_format_selection observed
    enhanced_ssh = MagicMock(name="EnhancedSSHRunner")  # WHY: sanitize_filename returns deterministic token
    enhanced_ssh.sanitize_filename.side_effect = lambda s: s.replace(" ", "_")  # WHY: deterministic sanitizer
    insight_metrics = MagicMock(name="InsightMetricsUtils")  # WHY: get_by_scope + export_const_insight_metrics
    mistapi_mod = MagicMock(name="mistapi")  # WHY: API dispatcher mock; sub-attrs set per test
    logging.debug("Baseline deps built with %d keys", 7)  # WHY: post-action trace
    return {
        "apisession": apisession,
        "PromptUtils": prompt_utils,
        "DataProcessingUtils": data_processing,
        "DataExporter": data_exporter,
        "EnhancedSSHRunner": enhanced_ssh,
        "InsightMetricsUtils": insight_metrics,
        "mistapi": mistapi_mod,
    }


def _make_op(**overrides) -> SiteMetricOperation:
    """Build a SiteMetricOperation with default deps and optional overrides."""
    deps = _make_deps()  # WHY: baseline seven-key dict
    deps.update(overrides)  # WHY: allow per-test overrides for a single collaborator
    return SiteMetricOperation(**deps)  # WHY: keyword-only constructor


def _make_context(**overrides) -> SiteRunContext:
    """Return a fully-populated SiteRunContext for helpers that take one directly."""
    base = {"site_id": "site-xyz", "site_name": "HQ Site"}  # WHY: canonical bundle
    base.update(overrides)  # WHY: per-test override wins
    return SiteRunContext(**base)  # WHY: frozen dataclass; must build via kwargs


class TestExecuteCancelBranch:
    """Cover the cancel branch where the user does not select a site."""

    def test_no_site_selected_returns_without_running_export(self, caplog: pytest.LogCaptureFixture) -> None:
        # WHY: PromptUtils.select_site returning falsy must exit cleanly with no export attempt
        deps = _make_deps()  # WHY: fresh baseline
        deps["PromptUtils"].select_site.return_value = None  # WHY: simulate cancel
        op = SiteMetricOperation(**deps)  # WHY: build SUT
        with caplog.at_level(logging.INFO, logger="root"):  # WHY: SUT uses root logging.info
            op.execute()  # WHY: exercise cancel path
        assert not deps["InsightMetricsUtils"].export_const_insight_metrics.called  # WHY: never refreshed
        assert not deps["DataExporter"].write_with_format_selection.called  # WHY: never wrote file
        out = "\n".join(r.getMessage() for r in caplog.records)  # WHY: aggregate captured log records
        assert "Export Site Insight Metrics" in out  # WHY: banner still logged


class TestExecuteEmptyMetricsBranch:
    """Cover the empty-metric-list branch after site selection succeeds."""

    def test_empty_metrics_writes_empty_file(self, caplog: pytest.LogCaptureFixture) -> None:
        # WHY: when InsightMetricsUtils.get_by_scope returns [], the empty-file branch fires
        deps = _make_deps()  # WHY: baseline
        deps["PromptUtils"].select_site.return_value = "site-xyz"  # WHY: valid site
        deps["InsightMetricsUtils"].get_by_scope.return_value = []  # WHY: force empty branch
        deps["mistapi"].api.v1.sites.listSites.return_value = MagicMock()  # WHY: minimal API stub
        deps["mistapi"].get_all.return_value = [{"id": "site-xyz", "name": "HQ Site"}]  # WHY: name lookup
        op = SiteMetricOperation(**deps)  # WHY: build SUT
        with caplog.at_level(logging.INFO, logger="root"):  # WHY: SUT uses root logging.info
            op.execute()  # WHY: exercise empty-metrics branch
        # WHY: empty file must be written with [] payload
        deps["DataExporter"].write_with_format_selection.assert_called_once()
        args, _kwargs = deps["DataExporter"].write_with_format_selection.call_args  # WHY: inspect call
        assert args[0] == []  # WHY: first positional is the empty list
        assert "SiteInsightMetrics_HQ_Site.csv" in args[1]  # WHY: filename includes sanitized site name
        out = "\n".join(r.getMessage() for r in caplog.records)  # WHY: aggregate captured log records
        assert "No metrics found for site scope" in out  # WHY: user warning surfaced


class TestExecuteHappyPath:
    """Cover the non-empty-payload success branch end-to-end."""

    def test_success_writes_processed_rows(self, caplog: pytest.LogCaptureFixture) -> None:
        # WHY: get_by_scope returns metric list; API returns data; final export emits processed rows
        deps = _make_deps()  # WHY: baseline
        deps["PromptUtils"].select_site.return_value = "site-xyz"  # WHY: valid site
        deps["InsightMetricsUtils"].get_by_scope.return_value = ["metric-a", "metric-b"]  # WHY: two metrics
        deps["mistapi"].api.v1.sites.listSites.return_value = MagicMock()  # WHY: minimal API stub
        deps["mistapi"].get_all.return_value = [{"id": "site-xyz", "name": "HQ Site"}]  # WHY: name lookup

        # WHY: each per-metric call must return a *fresh* dict since _annotate_row mutates in place
        def _fresh_response(*_args, **_kwargs) -> MagicMock:
            resp = MagicMock()  # WHY: new response object per call
            resp.data = {"value": 42}  # WHY: new dict payload per call
            return resp  # WHY: caller gets a fresh object each invocation

        deps["mistapi"].api.v1.sites.insights.getSiteInsightMetrics.side_effect = _fresh_response
        op = SiteMetricOperation(**deps)  # WHY: build SUT
        with caplog.at_level(logging.INFO, logger="root"):  # WHY: SUT uses root logging.info
            op.execute()  # WHY: exercise full happy path
        # WHY: DataExporter must be called once with the annotated rows
        deps["DataExporter"].write_with_format_selection.assert_called_once()
        rows = deps["DataExporter"].write_with_format_selection.call_args.args[0]  # WHY: first positional
        assert len(rows) == 2  # WHY: two metrics -> two annotated rows
        # WHY: order is not guaranteed (may be concurrent) so use set comparison
        metric_types = {row["metric_type"] for row in rows}
        assert metric_types == {"metric-a", "metric-b"}  # WHY: both metrics annotated
        assert all(row["site_id"] == "site-xyz" for row in rows)  # WHY: annotate stamps site id
        assert all(row["site_name"] == "HQ Site" for row in rows)  # WHY: annotate stamps site name
        out = "\n".join(r.getMessage() for r in caplog.records)  # WHY: aggregate captured log records
        assert "2 site insight metrics exported" in out  # WHY: user summary surfaced


class TestFetchOneMetricBranches:
    """Cover the per-metric API loop's exception and empty-payload branches."""

    def test_api_exception_returns_none(self) -> None:
        # WHY: per-metric API failure logs debug and returns None (batch continues)
        deps = _make_deps()  # WHY: baseline
        # WHY: force API call to raise
        deps["mistapi"].api.v1.sites.insights.getSiteInsightMetrics.side_effect = RuntimeError("boom")
        op = SiteMetricOperation(**deps)  # WHY: build SUT
        ctx = _make_context()  # WHY: build a context bundle
        result = op._fetch_one_metric(ctx, "metric-x")  # WHY: exercise exception branch
        assert result is None  # WHY: caller receives None so it can skip this metric

    def test_empty_payload_returns_none(self) -> None:
        # WHY: when getattr(response, "data", ...) is falsy, _annotate_row returns None
        deps = _make_deps()  # WHY: baseline
        empty_response = MagicMock()  # WHY: response wrapper
        empty_response.data = {}  # WHY: empty payload
        deps["mistapi"].api.v1.sites.insights.getSiteInsightMetrics.return_value = empty_response  # WHY: empty
        op = SiteMetricOperation(**deps)  # WHY: build SUT
        ctx = _make_context()  # WHY: context bundle
        result = op._fetch_one_metric(ctx, "metric-x")  # WHY: exercise empty-payload branch
        assert result is None  # WHY: annotate short-circuited empty dict

    def test_response_without_data_attr_falls_back_to_response(self) -> None:
        # WHY: getattr(response, "data", response) uses the response itself when .data missing
        deps = _make_deps()  # WHY: baseline
        # WHY: use a plain dict (no .data attribute) so getattr returns the dict itself
        deps["mistapi"].api.v1.sites.insights.getSiteInsightMetrics.return_value = {"foo": "bar"}  # WHY: dict
        op = SiteMetricOperation(**deps)  # WHY: build SUT
        ctx = _make_context()  # WHY: context bundle
        result = op._fetch_one_metric(ctx, "metric-x")  # WHY: exercise fallback branch
        assert result is not None  # WHY: non-empty raw dict is annotated
        assert result["metric_type"] == "metric-x"  # WHY: annotate stamped metric name
        assert result["foo"] == "bar"  # WHY: original payload preserved


class TestResolveSiteName:
    """Cover the best-effort site-name lookup helper's fallback branch."""

    def test_list_sites_exception_falls_back_to_site_id(self) -> None:
        # WHY: any exception in listSites/get_all falls back to site_id
        deps = _make_deps()  # WHY: baseline
        deps["mistapi"].api.v1.sites.listSites.side_effect = RuntimeError("api down")  # WHY: force exception
        op = SiteMetricOperation(**deps)  # WHY: build SUT
        result = op._resolve_site_name("site-abc")  # WHY: exercise fallback branch
        assert result == "site-abc"  # WHY: fallback returns the input id

    def test_list_sites_no_match_falls_back_to_site_id(self) -> None:
        # WHY: when no site in the list matches, the generator expression yields the site_id fallback
        deps = _make_deps()  # WHY: baseline
        deps["mistapi"].api.v1.sites.listSites.return_value = MagicMock()  # WHY: minimal stub
        deps["mistapi"].get_all.return_value = [{"id": "other-site", "name": "Other"}]  # WHY: no match
        op = SiteMetricOperation(**deps)  # WHY: build SUT
        result = op._resolve_site_name("site-abc")  # WHY: exercise no-match branch
        assert result == "site-abc"  # WHY: fallback to the input id

    def test_list_sites_match_returns_name(self) -> None:
        # WHY: happy path returns the matched site name
        deps = _make_deps()  # WHY: baseline
        deps["mistapi"].api.v1.sites.listSites.return_value = MagicMock()  # WHY: minimal stub
        deps["mistapi"].get_all.return_value = [{"id": "site-abc", "name": "Alpha"}]  # WHY: match
        op = SiteMetricOperation(**deps)  # WHY: build SUT
        result = op._resolve_site_name("site-abc")  # WHY: exercise happy path
        assert result == "Alpha"  # WHY: matched name returned


class TestAnnotateRow:
    """Cover the ``_annotate_row`` static helper directly."""

    def test_non_empty_row_gets_annotations(self) -> None:
        # WHY: non-empty raw dict is annotated with metric_type/site_id/site_name
        ctx = _make_context(site_id="s1", site_name="S One")  # WHY: canonical context bundle
        result = SiteMetricOperation._annotate_row({"k": "v"}, "m1", ctx)  # WHY: exercise annotate
        assert result is not None  # WHY: non-empty payload survives
        assert result["k"] == "v"  # WHY: original key preserved
        assert result["metric_type"] == "m1"  # WHY: metric stamp applied
        assert result["site_id"] == "s1"  # WHY: site id stamp applied
        assert result["site_name"] == "S One"  # WHY: site name stamp applied

    def test_empty_row_returns_none(self) -> None:
        # WHY: empty dict is treated as no-data and returns None
        ctx = _make_context()  # WHY: canonical context bundle
        result = SiteMetricOperation._annotate_row({}, "m1", ctx)  # WHY: exercise empty-row branch
        assert result is None  # WHY: no-data short-circuits before annotation


class TestFinalizeErrorBranch:
    """Cover the ``_finalize`` exception branch that emits an empty file on failure."""

    def test_flatten_exception_emits_empty_file(self, caplog: pytest.LogCaptureFixture) -> None:
        # WHY: exception from flatten_nested_fields must be caught by _finalize and route to _export_error
        deps = _make_deps()  # WHY: baseline
        deps["DataProcessingUtils"].flatten_nested_fields.side_effect = RuntimeError("flatten failed")  # WHY: force
        op = SiteMetricOperation(**deps)  # WHY: build SUT
        ctx = _make_context()  # WHY: context bundle
        with caplog.at_level(logging.INFO, logger="root"):  # WHY: SUT uses root logging.info
            op._finalize([{"row": 1}], 1, "out.csv", ctx)  # WHY: exercise error branch directly
        # WHY: _export_error always writes an empty file so downstream consumers still get output
        deps["DataExporter"].write_with_format_selection.assert_called_once()
        args, _kwargs = deps["DataExporter"].write_with_format_selection.call_args  # WHY: inspect call
        assert args[0] == []  # WHY: empty payload on error path
        out = "\n".join(r.getMessage() for r in caplog.records)  # WHY: aggregate captured log records
        assert "Error exporting site insight metrics" in out  # WHY: user warning surfaced

    def test_empty_data_emits_zero_data_summary(self, caplog: pytest.LogCaptureFixture) -> None:
        # WHY: zero-data path emits the "no data available" summary and an empty file
        deps = _make_deps()  # WHY: baseline
        op = SiteMetricOperation(**deps)  # WHY: build SUT
        ctx = _make_context()  # WHY: context bundle
        with caplog.at_level(logging.INFO, logger="root"):  # WHY: SUT uses root logging.info
            op._finalize([], 0, "out.csv", ctx)  # WHY: exercise zero-data branch
        # WHY: empty-data path still writes empty file for consistency
        deps["DataExporter"].write_with_format_selection.assert_called_once_with([], "out.csv")
        out = "\n".join(r.getMessage() for r in caplog.records)  # WHY: aggregate captured log records
        assert "0 insight metrics exported" in out  # WHY: user summary surfaced


class TestBuildFilename:
    """Cover the ``_build_filename`` helper's sanitisation path."""

    def test_filename_uses_sanitized_site_name(self) -> None:
        # WHY: site_name with a space must be sanitised before formatting
        deps = _make_deps()  # WHY: baseline
        op = SiteMetricOperation(**deps)  # WHY: build SUT
        ctx = _make_context(site_name="HQ Site")  # WHY: name with a space
        filename = op._build_filename(ctx)  # WHY: exercise sanitiser
        assert filename == "SiteInsightMetrics_HQ_Site.csv"  # WHY: space replaced by underscore

    def test_filename_falls_back_to_site_id_when_name_empty(self) -> None:
        # WHY: empty site_name triggers the "context.site_name or context.site_id" fallback
        deps = _make_deps()  # WHY: baseline
        op = SiteMetricOperation(**deps)  # WHY: build SUT
        ctx = _make_context(site_name="")  # WHY: empty name forces fallback
        filename = op._build_filename(ctx)  # WHY: exercise fallback branch
        assert "site-xyz" in filename  # WHY: falls back to site_id
