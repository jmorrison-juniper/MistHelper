"""Wave 3 top-up tests for DeviceMetricOperation (initiative 1018).

Targets the 121 uncovered statements in
``src/export/site_insights/device_metric_operation.py``. Existing test
suite covers ``SiteInsightsExporter`` but never instantiates or
exercises ``DeviceMetricOperation``. This file drives every branch of
``execute()`` and its helpers via injected dependencies.

Constraints:
* Pure unit tests -- no live mistapi, no filesystem writes.
* All injected deps are ``MagicMock`` (no importable spec available for
  the mistapi module surface or the utility class collaborators).
* ``PacketCaptureManager`` mock provides ``validate_mac_address`` and
  ``normalize_mac_address`` so the real ``_normalize_device_mac_or_none``
  can be exercised via the sibling ``SiteInsightsExporter`` instance.
"""

from __future__ import annotations  # WHY: PEP 604 unions retained across whole module.

import logging  # WHY: assert error log paths were exercised for menu-76 cancel branches.
from unittest.mock import MagicMock  # WHY: build interchangeable stubs for injected collaborators.

import pytest

from src.export.site_insights.device_metric_operation import (  # WHY: SUTs under test.
    DeviceMetricOperation,
    DeviceRunContext,
)


# ---------------------------------------------------------------------------
# Shared fixture builders
# ---------------------------------------------------------------------------
def _make_deps() -> dict:
    """Return the eight injected constructor kwargs as a fresh dict of MagicMocks."""
    apisession = MagicMock(name="apisession")  # WHY: opaque session object; passed through unchanged.
    prompt_utils = MagicMock(
        name="PromptUtils"
    )  # WHY: select_site/select_device_id_from_inventory stubs bound per-test.
    data_processing = MagicMock(name="DataProcessingUtils")  # WHY: flatten/escape helpers.
    data_exporter = MagicMock(name="DataExporter")  # WHY: write_with_format_selection observed.
    enhanced_ssh = MagicMock(name="EnhancedSSHRunner")  # WHY: sanitize_filename returns predictable token.
    enhanced_ssh.sanitize_filename.side_effect = lambda s: s.replace(" ", "_")  # WHY: deterministic sanitizer.
    insight_metrics = MagicMock(name="InsightMetricsUtils")  # WHY: get_by_scope + export_const_insight_metrics.
    packet_capture = MagicMock(name="PacketCaptureManager")  # WHY: MAC validator / normalizer for exporter.
    packet_capture.validate_mac_address.return_value = True  # WHY: default: MAC passes validation.
    packet_capture.normalize_mac_address.side_effect = lambda mac: mac.replace(":", "").lower()  # WHY: canonical form.
    mistapi_mod = MagicMock(name="mistapi")  # WHY: API dispatcher mock; sub-attrs set per-test.
    return {
        "apisession": apisession,
        "PromptUtils": prompt_utils,
        "DataProcessingUtils": data_processing,
        "DataExporter": data_exporter,
        "EnhancedSSHRunner": enhanced_ssh,
        "InsightMetricsUtils": insight_metrics,
        "PacketCaptureManager": packet_capture,
        "mistapi": mistapi_mod,
    }


def _make_op(**overrides) -> DeviceMetricOperation:
    """Build a DeviceMetricOperation with default deps and optional per-test overrides."""
    deps = _make_deps()  # WHY: start with the eight-key baseline.
    deps.update(overrides)  # WHY: allow individual tests to swap out a specific collaborator.
    return DeviceMetricOperation(**deps)  # WHY: keyword-only constructor.


def _make_context(**overrides) -> DeviceRunContext:
    """Return a fully-populated DeviceRunContext for helpers that take one directly."""
    base = {
        "site_id": "site-xyz",  # WHY: canonical site UUID used in per-metric annotations.
        "site_name": "HQ Site",  # WHY: label with a space so sanitize_filename can act on it.
        "device_id": "dev-abc",  # WHY: canonical device UUID used in per-metric annotations.
        "device_name": "Edge Router",  # WHY: label with a space so sanitize_filename can act on it.
        "device_mac": "aabbccddeeff",  # WHY: normalized canonical MAC form.
        "device_model": "SRX345",  # WHY: gateway platform classification for filter tests.
    }
    base.update(overrides)  # WHY: per-test overrides win over the baseline.
    return DeviceRunContext(**base)  # WHY: frozen dataclass; must build via kwargs.


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------
class TestInit:
    """Constructor binds all eight injected deps and creates the sibling exporter."""

    def test_constructor_binds_all_injected_deps(self) -> None:
        """Each kwarg becomes an attribute of the instance; PacketCaptureManager builds the exporter."""
        deps = _make_deps()  # WHY: capture a stable reference to every mock for identity checks.
        op = DeviceMetricOperation(**deps)  # WHY: exercise the eight-kwarg keyword-only constructor.
        assert op.apisession is deps["apisession"]  # WHY: session is stored verbatim.
        assert op.PromptUtils is deps["PromptUtils"]  # WHY: prompt utility bound for select_* calls.
        assert op.DataProcessingUtils is deps["DataProcessingUtils"]  # WHY: flatten/escape helpers bound.
        assert op.DataExporter is deps["DataExporter"]  # WHY: writer bound for CSV/DB emit.
        assert op.EnhancedSSHRunner is deps["EnhancedSSHRunner"]  # WHY: filename sanitizer bound.
        assert op.InsightMetricsUtils is deps["InsightMetricsUtils"]  # WHY: insight metric helpers bound.
        assert op.mistapi is deps["mistapi"]  # WHY: mistapi module bound for dispatch.
        # WHY: The sibling SiteInsightsExporter is constructed with the injected PacketCaptureManager.
        assert op._insights_exporter.PacketCaptureManager is deps["PacketCaptureManager"]


# ---------------------------------------------------------------------------
# execute() -- top-level dispatcher
# ---------------------------------------------------------------------------
class TestExecute:
    """Cover the three exit paths of execute(): prompt-cancel, context-fail, full run."""

    def test_execute_returns_when_prompts_cancel(self, caplog) -> None:
        """When _prompt_site_and_device returns None, execute() must return without building context."""
        op = _make_op()  # WHY: fresh SUT.
        op.PromptUtils.select_site.return_value = ""  # WHY: falsy site_id triggers the cancel branch.
        with caplog.at_level(logging.INFO):  # WHY: capture starting log entry too.
            op.execute()  # WHY: exercise the top-level dispatcher.
        op.InsightMetricsUtils.export_const_insight_metrics.assert_called_once()  # WHY: refresh still ran.
        op.PromptUtils.select_device_id_from_inventory.assert_not_called()  # WHY: cancelled before device prompt.

    def test_execute_returns_when_context_fails(self, monkeypatch) -> None:
        """When _build_context returns None (bad MAC), execute() must skip _run_export."""
        op = _make_op()  # WHY: fresh SUT.
        op.PromptUtils.select_site.return_value = "site-xyz"  # WHY: happy prompt path.
        op.PromptUtils.select_device_id_from_inventory.return_value = "dev-abc"  # WHY: device prompt succeeds.
        # WHY: force _build_context to return None so _run_export must never fire.
        monkeypatch.setattr(op, "_build_context", lambda *_args, **_kw: None)
        run_export = MagicMock(name="_run_export")  # WHY: assert we never enter the export pipeline.
        monkeypatch.setattr(op, "_run_export", run_export)  # WHY: replace the pipeline entry point.
        op.execute()  # WHY: exercise the guard.
        run_export.assert_not_called()  # WHY: cancel-fail path bypasses run_export.

    def test_execute_full_success_path(self, monkeypatch) -> None:
        """When both helpers succeed, execute() must invoke _run_export with the built context."""
        op = _make_op()  # WHY: fresh SUT.
        op.PromptUtils.select_site.return_value = "site-xyz"  # WHY: happy prompt path.
        op.PromptUtils.select_device_id_from_inventory.return_value = "dev-abc"  # WHY: device prompt succeeds.
        context = _make_context()  # WHY: canned frozen context handed downstream.
        monkeypatch.setattr(op, "_build_context", lambda *_a, **_kw: context)  # WHY: stub the builder.
        run_export = MagicMock(name="_run_export")  # WHY: observe the orchestrator call site.
        monkeypatch.setattr(op, "_run_export", run_export)  # WHY: replace the pipeline entry point.
        op.execute()  # WHY: drive the happy path.
        run_export.assert_called_once_with(context)  # WHY: full path forwards context to _run_export.


# ---------------------------------------------------------------------------
# _refresh_const_metrics
# ---------------------------------------------------------------------------
class TestRefreshConstMetrics:
    """The single-call helper forwards to InsightMetricsUtils.export_const_insight_metrics."""

    def test_refresh_calls_injected_helper(self) -> None:
        """The refresh helper must invoke the injected refresh function exactly once."""
        op = _make_op()  # WHY: fresh SUT.
        op._refresh_const_metrics()  # WHY: exercise the isolated helper.
        op.InsightMetricsUtils.export_const_insight_metrics.assert_called_once_with()  # WHY: no args.


# ---------------------------------------------------------------------------
# _prompt_site_and_device
# ---------------------------------------------------------------------------
class TestPromptSiteAndDevice:
    """Cover the three branches of the two-prompt helper: no site, no device, success."""

    def test_returns_none_when_site_falsy(self, caplog) -> None:
        """A falsy site_id short-circuits and returns None without prompting for device."""
        op = _make_op()  # WHY: fresh SUT.
        op.PromptUtils.select_site.return_value = ""  # WHY: user cancelled at first prompt.
        with caplog.at_level(logging.ERROR):
            result = op._prompt_site_and_device()  # WHY: exercise cancel-at-site branch.
        assert result is None  # WHY: contract: None means cancel.
        op.PromptUtils.select_device_id_from_inventory.assert_not_called()  # WHY: never advance to device prompt.
        assert any("No site selected" in r.message for r in caplog.records)  # WHY: log preserved.

    def test_returns_none_when_device_falsy(self, caplog) -> None:
        """A falsy device_id after a good site_id also returns None."""
        op = _make_op()  # WHY: fresh SUT.
        op.PromptUtils.select_site.return_value = "site-xyz"  # WHY: first prompt succeeds.
        op.PromptUtils.select_device_id_from_inventory.return_value = None  # WHY: user cancels at second prompt.
        with caplog.at_level(logging.ERROR):
            result = op._prompt_site_and_device()  # WHY: exercise cancel-at-device branch.
        assert result is None  # WHY: contract: None means cancel.
        assert any("No device selected" in r.message for r in caplog.records)  # WHY: log preserved.

    def test_returns_pair_on_success(self) -> None:
        """When both prompts succeed, the helper returns (site_id, device_id)."""
        op = _make_op()  # WHY: fresh SUT.
        op.PromptUtils.select_site.return_value = "site-xyz"  # WHY: first prompt happy.
        op.PromptUtils.select_device_id_from_inventory.return_value = "dev-abc"  # WHY: second prompt happy.
        assert op._prompt_site_and_device() == ("site-xyz", "dev-abc")  # WHY: contract shape.


# ---------------------------------------------------------------------------
# _build_context
# ---------------------------------------------------------------------------
class TestBuildContext:
    """Cover the two branches: MAC validation fails vs succeeds."""

    def test_returns_none_when_mac_invalid(self, monkeypatch) -> None:
        """When _validate_mac returns None, _build_context returns None."""
        op = _make_op()  # WHY: fresh SUT.
        monkeypatch.setattr(op, "_resolve_site_name", lambda sid: "resolved-site")  # WHY: stub name lookup.
        monkeypatch.setattr(  # WHY: stub device lookup with shaped dict.
            op, "_resolve_device_info", lambda sid, did: {"name": "dev1", "mac": None, "model": ""}
        )
        result = op._build_context("site-xyz", "dev-abc")  # WHY: exercise the guard on MAC absence.
        assert result is None  # WHY: contract: bad MAC returns None.

    def test_returns_context_on_success(self, monkeypatch) -> None:
        """A successful validation yields a fully-populated DeviceRunContext."""
        op = _make_op()  # WHY: fresh SUT with default MAC validator returning True.
        monkeypatch.setattr(op, "_resolve_site_name", lambda sid: "resolved-site")  # WHY: canned site name.
        monkeypatch.setattr(  # WHY: canned device shape with a valid MAC to normalize.
            op,
            "_resolve_device_info",
            lambda sid, did: {"name": "dev1", "mac": "AA:BB:CC:DD:EE:FF", "model": "AP45"},
        )
        result = op._build_context("site-xyz", "dev-abc")  # WHY: exercise the happy path.
        assert isinstance(result, DeviceRunContext)  # WHY: contract: dataclass on success.
        assert result.site_id == "site-xyz"  # WHY: passed through.
        assert result.site_name == "resolved-site"  # WHY: resolver output surfaced.
        assert result.device_name == "dev1"  # WHY: device dict name surfaced.
        assert result.device_mac == "aabbccddeeff"  # WHY: normalizer stripped colons and lowercased.
        assert result.device_model == "AP45"  # WHY: model surfaced from lookup dict.


# ---------------------------------------------------------------------------
# _run_export
# ---------------------------------------------------------------------------
class TestRunExport:
    """Cover the two branches: empty filter (emit empty) vs non-empty (full pipeline)."""

    def test_empty_metrics_emits_empty_and_returns(self, monkeypatch) -> None:
        """When _filter_metrics returns [], _emit_empty_metric_list runs and we skip collection."""
        op = _make_op()  # WHY: fresh SUT.
        monkeypatch.setattr(op, "_build_filename", lambda ctx: "out.csv")  # WHY: canned filename.
        monkeypatch.setattr(op, "_filter_metrics", lambda model: [])  # WHY: force the empty branch.
        collect = MagicMock(name="_collect_metrics")  # WHY: must NOT be called.
        monkeypatch.setattr(op, "_collect_metrics", collect)  # WHY: assert absence.
        emit_empty = MagicMock(name="_emit_empty_metric_list")  # WHY: observe emit-empty invocation.
        monkeypatch.setattr(op, "_emit_empty_metric_list", emit_empty)  # WHY: replace emit-empty.
        op._run_export(_make_context())  # WHY: exercise the empty branch.
        emit_empty.assert_called_once_with("out.csv")  # WHY: correct filename passed through.
        collect.assert_not_called()  # WHY: skipped in empty branch.

    def test_nonempty_metrics_calls_full_pipeline(self, monkeypatch) -> None:
        """When metrics remain, _collect + _finalize must run with the correct args."""
        op = _make_op()  # WHY: fresh SUT.
        monkeypatch.setattr(op, "_build_filename", lambda ctx: "out.csv")  # WHY: canned filename.
        monkeypatch.setattr(op, "_filter_metrics", lambda model: ["m1", "m2"])  # WHY: non-empty list.
        collect = MagicMock(name="_collect_metrics", return_value=([{"x": 1}], 1))  # WHY: canned pair.
        monkeypatch.setattr(op, "_collect_metrics", collect)  # WHY: stub the loop helper.
        finalize = MagicMock(name="_finalize")  # WHY: observe orchestrator forwarding.
        monkeypatch.setattr(op, "_finalize", finalize)  # WHY: stub the final emit dispatcher.
        ctx = _make_context()  # WHY: fresh context matching the collect result.
        op._run_export(ctx)  # WHY: exercise the non-empty branch.
        collect.assert_called_once_with(ctx, ["m1", "m2"])  # WHY: two-arg contract preserved.
        finalize.assert_called_once_with([{"x": 1}], 1, "out.csv", ctx)  # WHY: four-arg forwarding.


# ---------------------------------------------------------------------------
# _emit_empty_metric_list
# ---------------------------------------------------------------------------
class TestEmitEmptyMetricList:
    """Empty-metric emit writes an empty file and logs the failure cause."""

    def test_writes_empty_file_and_logs(self, caplog) -> None:
        """The empty-metric helper must call the writer with [] and the given filename."""
        op = _make_op()  # WHY: fresh SUT.
        with caplog.at_level(logging.ERROR):
            op._emit_empty_metric_list("out.csv")  # WHY: exercise the emit path.
        op.DataExporter.write_with_format_selection.assert_called_once_with([], "out.csv")  # WHY: empty write.
        assert any("No device-scope metrics" in r.message for r in caplog.records)  # WHY: log preserved.


# ---------------------------------------------------------------------------
# _resolve_site_name
# ---------------------------------------------------------------------------
class TestResolveSiteName:
    """Cover the three branches: match found, no match falls back to id, exception falls back to id."""

    def test_match_returns_site_name(self) -> None:
        """When mistapi returns the site, its name is used."""
        op = _make_op()  # WHY: fresh SUT.
        op.mistapi.get_all.return_value = [  # WHY: canned paged sites result.
            {"id": "site-xyz", "name": "Corp HQ"},
            {"id": "other", "name": "Other Site"},
        ]
        assert op._resolve_site_name("site-xyz") == "Corp HQ"  # WHY: match extracts name.

    def test_no_match_returns_site_id(self) -> None:
        """When no sites match the id, the helper falls back to the site_id string."""
        op = _make_op()  # WHY: fresh SUT.
        op.mistapi.get_all.return_value = [{"id": "not-me", "name": "Other"}]  # WHY: no matching id.
        assert op._resolve_site_name("site-xyz") == "site-xyz"  # WHY: fallback to input id.

    def test_api_exception_returns_site_id(self) -> None:
        """A raising mistapi call falls back to the site_id string (silent legacy behaviour)."""
        op = _make_op()  # WHY: fresh SUT.
        op.mistapi.api.v1.sites.listSites.side_effect = RuntimeError("boom")  # WHY: force except path.
        assert op._resolve_site_name("site-xyz") == "site-xyz"  # WHY: silent fallback.


# ---------------------------------------------------------------------------
# _resolve_device_info
# ---------------------------------------------------------------------------
class TestResolveDeviceInfo:
    """Cover the three branches: match, no match, exception. All non-match paths return default shape."""

    def test_match_returns_shaped_dict(self) -> None:
        """A successful lookup returns the trio name/mac/model."""
        op = _make_op()  # WHY: fresh SUT.
        op.mistapi.get_all.return_value = [  # WHY: canned paged device list.
            {"id": "dev-abc", "name": "Edge-Router-1", "mac": "AA:BB:CC:DD:EE:FF", "model": "SRX345"},
        ]
        result = op._resolve_device_info("site-xyz", "dev-abc")  # WHY: exercise match branch.
        assert result == {"name": "Edge-Router-1", "mac": "AA:BB:CC:DD:EE:FF", "model": "SRX345"}

    def test_match_missing_model_defaults_empty(self) -> None:
        """Devices without a model key get the empty-string default from .get."""
        op = _make_op()  # WHY: fresh SUT.
        op.mistapi.get_all.return_value = [  # WHY: shape without a model field.
            {"id": "dev-abc", "name": "Edge-Router-1", "mac": "AA:BB:CC:DD:EE:FF"},
        ]
        result = op._resolve_device_info("site-xyz", "dev-abc")  # WHY: exercise .get default.
        assert result["model"] == ""  # WHY: default matches legacy fallback.

    def test_no_match_returns_default_shape(self) -> None:
        """When no device matches, the default fallback shape is returned."""
        op = _make_op()  # WHY: fresh SUT.
        op.mistapi.get_all.return_value = [{"id": "someone-else"}]  # WHY: no matching id.
        result = op._resolve_device_info("site-xyz", "dev-abc")  # WHY: exercise no-match branch.
        assert result == {"name": "dev-abc", "mac": None, "model": ""}  # WHY: default trio.

    def test_api_exception_returns_default_shape(self) -> None:
        """A raising mistapi call falls through to the default fallback shape."""
        op = _make_op()  # WHY: fresh SUT.
        op.mistapi.api.v1.sites.devices.listSiteDevices.side_effect = RuntimeError("boom")  # WHY: force except.
        result = op._resolve_device_info("site-xyz", "dev-abc")  # WHY: exercise except branch.
        assert result == {"name": "dev-abc", "mac": None, "model": ""}  # WHY: default trio.


# ---------------------------------------------------------------------------
# _validate_mac
# ---------------------------------------------------------------------------
class TestValidateMac:
    """Cover the three branches: missing MAC, invalid MAC, normalized success."""

    def test_missing_mac_returns_none(self, caplog) -> None:
        """A falsy MAC prints the missing-MAC prompt and returns None."""
        op = _make_op()  # WHY: fresh SUT.
        with caplog.at_level(logging.ERROR):
            result = op._validate_mac("dev-abc", "Edge-Router", None)  # WHY: exercise missing-MAC branch.
        assert result is None  # WHY: contract: missing -> None.
        assert any("Could not find MAC address" in r.message for r in caplog.records)  # WHY: log preserved.

    def test_invalid_mac_returns_none(self, caplog) -> None:
        """An invalid MAC (validator False) prints the invalid-MAC prompt and returns None."""
        op = _make_op()  # WHY: fresh SUT.
        # WHY: force validator False on the sibling exporter's injected PacketCaptureManager.
        op._insights_exporter.PacketCaptureManager.validate_mac_address.return_value = False
        with caplog.at_level(logging.ERROR):
            result = op._validate_mac("dev-abc", "Edge-Router", "not-a-mac")  # WHY: exercise invalid branch.
        assert result is None  # WHY: contract: invalid -> None.
        assert any("Invalid device MAC address" in r.message for r in caplog.records)  # WHY: log preserved.

    def test_valid_mac_returns_normalized(self) -> None:
        """A valid MAC returns the normalized canonical form from the exporter helper."""
        op = _make_op()  # WHY: fresh SUT. Default validator returns True and normalizer strips colons.
        assert op._validate_mac("dev-abc", "Edge-Router", "AA:BB:CC:DD:EE:FF") == "aabbccddeeff"


# ---------------------------------------------------------------------------
# _build_filename
# ---------------------------------------------------------------------------
class TestBuildFilename:
    """Filename builder mixes sanitized tokens with the fixed template."""

    def test_uses_site_and_device_names(self) -> None:
        """When both names are present, they drive the token substitution."""
        op = _make_op()  # WHY: fresh SUT with deterministic sanitizer.
        result = op._build_filename(_make_context())  # WHY: site='HQ Site' device='Edge Router'.
        assert result == "SiteDeviceInsights_HQ_Site_Edge_Router.csv"  # WHY: sanitizer replaces spaces.

    def test_falls_back_to_ids_when_names_missing(self) -> None:
        """Empty names must fall back to the ids per legacy behaviour."""
        op = _make_op()  # WHY: fresh SUT.
        ctx = _make_context(site_name="", device_name="")  # WHY: empty names activate fallback.
        result = op._build_filename(ctx)  # WHY: exercise the `or` fallbacks.
        assert result == "SiteDeviceInsights_site-xyz_dev-abc.csv"  # WHY: ids used verbatim.


# ---------------------------------------------------------------------------
# _filter_metrics
# ---------------------------------------------------------------------------
class TestFilterMetrics:
    """Filter walks the device-scope metric list against the real classifier."""

    def test_ap_platform_keeps_ap_metrics(self) -> None:
        """An AP model keeps 'ap'/'wifi' metrics and drops obviously-switch ones."""
        op = _make_op()  # WHY: fresh SUT.
        op.InsightMetricsUtils.get_by_scope.return_value = [  # WHY: mix compatible and incompatible tokens.
            "ap-uptime",
            "wifi-clients",
            "switch-ports",  # WHY: should be dropped for AP platform.
        ]
        result = op._filter_metrics("AP45")  # WHY: AP prefix classifies as ap.
        assert "ap-uptime" in result  # WHY: AP token allowed.
        assert "wifi-clients" in result  # WHY: WIFI token allowed.
        assert "switch-ports" not in result  # WHY: switch metric excluded for AP platform.

    def test_unknown_metric_kept_for_any_platform(self) -> None:
        """A metric with no platform tokens is unrestricted; it survives the filter."""
        op = _make_op()  # WHY: fresh SUT.
        op.InsightMetricsUtils.get_by_scope.return_value = ["generic-metric"]  # WHY: no tokens.
        assert op._filter_metrics("SRX345") == ["generic-metric"]  # WHY: unrestricted metrics survive.


# ---------------------------------------------------------------------------
# _collect_metrics
# ---------------------------------------------------------------------------
class TestCollectMetrics:
    """Collect loop increments retrieved only on non-None fetch results."""

    def test_mixed_results_counted_correctly(self, monkeypatch) -> None:
        """Two successful fetches and one None fetch result in retrieved=2 and two rows."""
        op = _make_op()  # WHY: fresh SUT.
        ctx = _make_context()  # WHY: canned context.
        # WHY: canned per-metric fetch outcomes; None simulates empty payload / error.
        fetch_results = {"m1": {"m": 1}, "m2": None, "m3": {"m": 3}}
        monkeypatch.setattr(op, "_fetch_one_metric", lambda _ctx, metric: fetch_results[metric])
        rows, retrieved = op._collect_metrics(ctx, ["m1", "m2", "m3"])  # WHY: exercise the accumulator loop.
        assert rows == [{"m": 1}, {"m": 3}]  # WHY: only non-None rows accumulate.
        assert retrieved == 2  # WHY: retrieved counts only successful fetches.


# ---------------------------------------------------------------------------
# _fetch_one_metric
# ---------------------------------------------------------------------------
class TestFetchOneMetric:
    """Cover the three branches: response with .data, exception path, empty payload -> None."""

    def test_success_path_annotates_and_returns(self) -> None:
        """A response with .data set to a dict must be annotated with the seven scope fields."""
        op = _make_op()  # WHY: fresh SUT.
        response = MagicMock(name="response")  # WHY: mistapi wrapper.
        response.data = {"latency_ms": 3}  # WHY: non-empty payload triggers annotation.
        op.mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice.return_value = response
        result = op._fetch_one_metric(_make_context(), "latency")  # WHY: exercise the happy path.
        assert result is not None  # WHY: narrow Optional to dict for mypy strict indexing.
        assert result["metric_type"] == "latency"  # WHY: annotator adds metric name.
        assert result["site_id"] == "site-xyz"  # WHY: annotator adds site id.
        assert result["device_mac"] == "aabbccddeeff"  # WHY: annotator adds normalized mac.

    def test_exception_returns_none(self, caplog) -> None:
        """A raising API call must be caught and return None."""
        op = _make_op()  # WHY: fresh SUT.
        op.mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice.side_effect = RuntimeError("boom")
        with caplog.at_level(logging.DEBUG):
            result = op._fetch_one_metric(_make_context(), "latency")  # WHY: exercise except branch.
        assert result is None  # WHY: contract: exception -> None.
        assert any("Failed to get device insight" in r.message for r in caplog.records)  # WHY: debug log.

    def test_empty_payload_returns_none(self) -> None:
        """A response with .data == {} returns None (annotator short-circuits on falsy)."""
        op = _make_op()  # WHY: fresh SUT.
        response = MagicMock(name="response")  # WHY: mistapi wrapper.
        response.data = {}  # WHY: empty dict is falsy in the annotator.
        op.mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice.return_value = response
        assert op._fetch_one_metric(_make_context(), "latency") is None  # WHY: contract: empty -> None.

    def test_response_without_data_attr_uses_response(self) -> None:
        """When response has no .data, the fallback getattr default (response) is used as raw."""
        op = _make_op()  # WHY: fresh SUT.

        class Wrapper:  # WHY: bare object without .data attr; used verbatim as raw.
            """Response-like object with no .data attribute for the getattr default branch."""

            def __init__(self, payload) -> None:
                self.payload = payload  # WHY: bystander attr; only truthiness of the object matters.

            def __bool__(self) -> bool:
                return bool(self.payload)  # WHY: falsy iff payload empty.

        # WHY: for the getattr(response, 'data', response) branch when data is absent, `raw = response`
        # if truthy; and only truthy dict-like payloads survive the annotator's `raw["metric_type"] = ...`.
        # Use a real dict here since the annotator writes keys on it.
        op.mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice.return_value = {"latency_ms": 5}
        result = op._fetch_one_metric(_make_context(), "latency")  # WHY: exercise the getattr fallback.
        assert result is not None  # WHY: narrow Optional to dict for mypy strict indexing.
        assert result["metric_type"] == "latency"  # WHY: annotation ran.


# ---------------------------------------------------------------------------
# _annotate_row (staticmethod)
# ---------------------------------------------------------------------------
class TestAnnotateRow:
    """Cover the empty-vs-populated branches of the annotator."""

    def test_empty_row_returns_none(self, caplog) -> None:
        """A falsy raw dict must return None and log a debug entry."""
        with caplog.at_level(logging.DEBUG):
            assert DeviceMetricOperation._annotate_row({}, "latency", _make_context()) is None  # WHY: empty -> None.
        assert any("No data available" in r.message for r in caplog.records)  # WHY: debug log preserved.

    def test_populated_row_adds_six_scope_fields(self) -> None:
        """A non-empty row must gain metric_type, site_id, site_name, device_id, device_name, device_mac."""
        raw = {"latency_ms": 3}  # WHY: minimal payload; will be annotated in place and returned.
        result = DeviceMetricOperation._annotate_row(raw, "latency", _make_context())  # WHY: exercise happy path.
        assert result is raw  # WHY: annotator mutates and returns the same dict.
        assert result["metric_type"] == "latency"  # WHY: added.
        assert result["site_id"] == "site-xyz"  # WHY: added.
        assert result["site_name"] == "HQ Site"  # WHY: added.
        assert result["device_id"] == "dev-abc"  # WHY: added.
        assert result["device_name"] == "Edge Router"  # WHY: added.
        assert result["device_mac"] == "aabbccddeeff"  # WHY: added.


# ---------------------------------------------------------------------------
# _finalize -- dispatcher
# ---------------------------------------------------------------------------
class TestFinalize:
    """Cover the three branches: with-data, empty, exception."""

    def test_with_data_calls_export_with_data(self, monkeypatch) -> None:
        """When all_device_data is non-empty, _export_with_data must be called."""
        op = _make_op()  # WHY: fresh SUT.
        with_data = MagicMock(name="_export_with_data")  # WHY: observe success path.
        empty = MagicMock(name="_export_empty")  # WHY: must NOT be called.
        error = MagicMock(name="_export_error")  # WHY: must NOT be called.
        monkeypatch.setattr(op, "_export_with_data", with_data)  # WHY: stub the success emitter.
        monkeypatch.setattr(op, "_export_empty", empty)  # WHY: stub the empty emitter.
        monkeypatch.setattr(op, "_export_error", error)  # WHY: stub the error emitter.
        ctx = _make_context()  # WHY: canned context.
        op._finalize([{"x": 1}], 1, "out.csv", ctx)  # WHY: exercise the success path.
        with_data.assert_called_once_with([{"x": 1}], 1, "out.csv", ctx)  # WHY: contract preserved.
        empty.assert_not_called()  # WHY: only one branch fires.
        error.assert_not_called()  # WHY: no exception raised.

    def test_empty_data_calls_export_empty(self, monkeypatch) -> None:
        """When all_device_data is [], _export_empty must be called."""
        op = _make_op()  # WHY: fresh SUT.
        with_data = MagicMock(name="_export_with_data")  # WHY: must NOT be called.
        empty = MagicMock(name="_export_empty")  # WHY: observe empty path.
        error = MagicMock(name="_export_error")  # WHY: must NOT be called.
        monkeypatch.setattr(op, "_export_with_data", with_data)  # WHY: stub the success emitter.
        monkeypatch.setattr(op, "_export_empty", empty)  # WHY: stub the empty emitter.
        monkeypatch.setattr(op, "_export_error", error)  # WHY: stub the error emitter.
        ctx = _make_context()  # WHY: canned context.
        op._finalize([], 0, "out.csv", ctx)  # WHY: exercise the empty path.
        empty.assert_called_once_with("out.csv", ctx)  # WHY: contract preserved.
        with_data.assert_not_called()  # WHY: not the success branch.

    def test_exception_calls_export_error(self, monkeypatch) -> None:
        """When _export_with_data raises, _export_error must handle the failure."""
        op = _make_op()  # WHY: fresh SUT.
        boom = RuntimeError("boom")  # WHY: canned failure to route to the error emitter.

        def raising(*_args, **_kw):
            """Stand-in _export_with_data that raises to trigger the except branch."""
            raise boom  # WHY: force the try-except to fall through.

        monkeypatch.setattr(op, "_export_with_data", raising)  # WHY: replace with raising stub.
        error = MagicMock(name="_export_error")  # WHY: observe the error emit.
        monkeypatch.setattr(op, "_export_error", error)  # WHY: stub the error emitter.
        ctx = _make_context()  # WHY: canned context.
        op._finalize([{"x": 1}], 1, "out.csv", ctx)  # WHY: exercise the except branch.
        error.assert_called_once_with(boom, "out.csv", ctx)  # WHY: exception routed with same instance.


# ---------------------------------------------------------------------------
# _export_with_data / _export_empty / _export_error
# ---------------------------------------------------------------------------
class TestExportPaths:
    """Cover the three emit helpers directly."""

    def test_export_with_data_flattens_escapes_writes(self, caplog) -> None:
        """Success path: flatten -> escape -> write -> summary log."""
        op = _make_op()  # WHY: fresh SUT.
        op.DataProcessingUtils.flatten_nested_fields.return_value = [{"flat": 1}]  # WHY: canned flatten.
        op.DataProcessingUtils.escape_multiline.return_value = [{"escaped": 1}]  # WHY: canned escape.
        ctx = _make_context()  # WHY: canned context.
        with caplog.at_level(logging.INFO):
            op._export_with_data([{"raw": 1}], 4, "out.csv", ctx)  # WHY: exercise the success emitter.
        op.DataProcessingUtils.flatten_nested_fields.assert_called_once_with([{"raw": 1}])  # WHY: pipeline step 1.
        op.DataProcessingUtils.escape_multiline.assert_called_once_with([{"flat": 1}])  # WHY: pipeline step 2.
        op.DataExporter.write_with_format_selection.assert_called_once_with([{"escaped": 1}], "out.csv")
        assert any("Exported 4 device insight" in r.message for r in caplog.records)  # WHY: summary log.

    def test_export_empty_writes_empty_and_logs_warning(self, caplog) -> None:
        """Empty path: write [] + warn log."""
        op = _make_op()  # WHY: fresh SUT.
        ctx = _make_context()  # WHY: canned context.
        with caplog.at_level(logging.WARNING):
            op._export_empty("out.csv", ctx)  # WHY: exercise the empty emitter.
        op.DataExporter.write_with_format_selection.assert_called_once_with([], "out.csv")  # WHY: empty write.
        assert any("No device insight data available" in r.message for r in caplog.records)  # WHY: warn log.

    def test_export_error_writes_empty_and_logs_error(self, caplog) -> None:
        """Error path: log the failure and still emit an empty file."""
        op = _make_op()  # WHY: fresh SUT.
        ctx = _make_context()  # WHY: canned context.
        with caplog.at_level(logging.ERROR):
            op._export_error(RuntimeError("boom"), "out.csv", ctx)  # WHY: exercise the error emitter.
        op.DataExporter.write_with_format_selection.assert_called_once_with([], "out.csv")  # WHY: empty write.
        assert any("Failed to export device insights" in r.message for r in caplog.records)  # WHY: error log.


# ---------------------------------------------------------------------------
# DeviceRunContext (frozen dataclass) sanity checks
# ---------------------------------------------------------------------------
class TestDeviceRunContextFrozen:
    """Cheap sanity checks that DeviceRunContext is frozen and slotted as declared."""

    def test_is_frozen(self) -> None:
        """Mutation must raise FrozenInstanceError (the dataclasses standard)."""
        from dataclasses import FrozenInstanceError  # WHY: exact stdlib exception for frozen mutation.

        ctx = _make_context()  # WHY: canned instance.
        with pytest.raises(FrozenInstanceError):  # WHY: precise exception avoids ruff B017 blind-exception rule.
            ctx.site_id = "different"  # type: ignore[misc]  # WHY: intentional mutation attempt.
