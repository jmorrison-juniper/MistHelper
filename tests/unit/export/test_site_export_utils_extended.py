"""Extended unit tests for SiteExportUtils covering module helpers + class methods."""

from __future__ import annotations

import logging  # WHY: verify log level branches via caplog.
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.export.site_export_utils import (
    SiteExportUtils,
    _api_supports_limit,
    _build_export_filename,
    _build_insight_rows,
    _channel_planning_rows_from_raw,
    _flatten_channel_planning_dict,
    _read_site_response_rows,
    _resolve_site_display_path,
    _sanitize_for_filename,
)

# ---------------------------------------------------------------------------
# Module-level pure helpers
# ---------------------------------------------------------------------------


def test_sanitize_for_filename_converts_spaces_and_dashes() -> None:
    """Spaces and dashes must collapse to underscores for filename tokens."""
    assert _sanitize_for_filename("My Site-1") == "My_Site_1"  # WHY: exact fragment expected.


def test_build_export_filename_preserves_legacy_camelcase() -> None:
    """Legacy CamelCase filename builder retains title-case + underscores."""
    assert _build_export_filename("system events", "Some Site") == "SiteSystemevents_Some_Site.csv"


def test_resolve_site_display_path_prefixes_data_when_bare_filename() -> None:
    """Bare filename gets prefixed with data subdir; nested paths pass through."""
    import os  # WHY: local os.path.join keeps assertion cross-platform.

    assert _resolve_site_display_path("f.csv") == os.path.join("data", "f.csv")
    assert _resolve_site_display_path("nested/f.csv") == "nested/f.csv"


def test_api_supports_limit_returns_true_when_signature_reveals_kwarg() -> None:
    """API-supports-limit probe returns True when the signature includes 'limit'."""

    def sample(session: Any, site_id: str, limit: int = 100) -> None:  # WHY: fake API accepts limit.
        return None

    assert _api_supports_limit(sample) is True


def test_api_supports_limit_returns_false_when_signature_omits_kwarg() -> None:
    """API-supports-limit probe returns False when signature has no 'limit'."""

    def sample(session: Any, site_id: str) -> None:  # WHY: fake API omits limit.
        return None

    assert _api_supports_limit(sample) is False


def test_api_supports_limit_defaults_to_true_on_signature_failure() -> None:
    """Signature inspection failures (TypeError/ValueError) fall back to True."""

    class Uninspectable:  # WHY: emulate callable rejecting signature inspection.
        def __call__(self) -> None:
            return None

    obj = Uninspectable()
    # Force inspect.signature to raise by monkey-patching in a probe wrapper.
    import inspect as _inspect  # WHY: import here to avoid module-attribute typing issues.

    original_signature = _inspect.signature  # WHY: preserve original for restoration.

    def _raise(*_args: Any, **_kwargs: Any) -> None:
        raise TypeError("cannot inspect")  # WHY: force fallback branch.

    _inspect.signature = _raise  # type: ignore[assignment]
    try:
        assert _api_supports_limit(obj) is True  # WHY: fallback path returns True.
    finally:
        _inspect.signature = original_signature  # WHY: restore for other tests.


def test_read_site_response_rows_handles_dict_list_and_fallback() -> None:
    """Dict payloads wrap; lists pass through; None/scalar collapse via `or {}` to [{}]."""
    assert _read_site_response_rows({"k": "v"}) == [{"k": "v"}]  # WHY: dict wraps to single-row list.
    assert _read_site_response_rows([{"a": 1}, {"a": 2}]) == [{"a": 1}, {"a": 2}]  # WHY: list identity.
    # WHY: falsy inputs are coerced to `{}` by `or {}` and then wrapped as single-row list.
    assert _read_site_response_rows(None) == [{}]
    # WHY: truthy non-dict, non-list scalars are treated as unknown shape -> empty list.
    assert _read_site_response_rows("junk") == []


def test_read_site_response_rows_extracts_data_attribute() -> None:
    """Dataclass-style responses with a .data attribute are unwrapped."""
    resp = SimpleNamespace(data=[{"x": 1}])  # WHY: emulate dataclass wrapper.
    assert _read_site_response_rows(resp) == [{"x": 1}]


def test_flatten_channel_planning_dict_flattens_bands_and_scalars() -> None:
    """Dict flattener emits per-AP rows for both band-mapped and scalar assignments."""
    raw = {
        "ap-1": {"5": {"channel": 36}, "2.4": 6},  # WHY: mixed dict + scalar band values.
        "ap-2": "n/a",  # WHY: scalar-per-AP -> single row.
    }
    rows = _flatten_channel_planning_dict(raw, "site-a")
    assert {"ap": "ap-1", "band": "5", "site_id": "site-a", "channel": 36} in rows
    assert {"ap": "ap-1", "band": "2.4", "site_id": "site-a", "value": 6} in rows
    assert {"ap": "ap-2", "site_id": "site-a", "value": "n/a"} in rows


def test_channel_planning_rows_from_raw_dispatches_by_shape() -> None:
    """Shape dispatcher forwards dicts to flattener, wraps scalars, keeps lists."""
    assert _channel_planning_rows_from_raw({"ap-a": {"5": {"c": 1}}}, "site") == [
        {"ap": "ap-a", "band": "5", "site_id": "site", "c": 1}
    ]
    assert _channel_planning_rows_from_raw([{"x": 1}], "site") == [{"x": 1}]  # WHY: list stays.
    # WHY: scalar-input branch wraps into a single-element list; compare via list length.
    scalar_result: Any = _channel_planning_rows_from_raw("scalar", "site")
    assert scalar_result == ["scalar"]


def test_build_insight_rows_emits_one_row_per_unique_metric() -> None:
    """Insight-row builder unions enabled + supported metric name lists."""
    rows = _build_insight_rows("site-1", "Site 1", ["m1"], ["m1", "m2"])
    assert len(rows) == 2  # WHY: dedup m1.
    m1 = next(r for r in rows if r["metric_name"] == "m1")
    m2 = next(r for r in rows if r["metric_name"] == "m2")
    assert m1["enabled"] and m1["supported"]  # WHY: both flags true when in both lists.
    assert not m2["enabled"] and m2["supported"]  # WHY: only supported.


# ---------------------------------------------------------------------------
# Helpers for constructor injection wiring
# ---------------------------------------------------------------------------


class _RecordingApiCall:
    """Callable stand-in that records positional + keyword arguments per invocation."""

    __name__ = "recordingApiCall"

    def __init__(self, return_value: Any = None) -> None:
        self.return_value = return_value  # WHY: configurable return payload.
        self.calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []  # WHY: record inbound args.

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        self.calls.append((args, kwargs))  # WHY: capture for assertions.
        return self.return_value


class _NoLimitApi:
    """Callable emulating an API without limit kwarg."""

    __name__ = "noLimitApi"

    def __call__(self, apisession: Any, site_id: str, **kwargs: Any) -> Any:  # WHY: strict signature.
        return {"site_id": site_id, "kwargs": kwargs}


def _named_mock(name: str, return_value: Any) -> MagicMock:
    """Create a MagicMock with a real ``__name__`` attribute for helper-log lines."""
    mock = MagicMock(return_value=return_value)  # WHY: base callable.
    mock.__name__ = name  # WHY: SiteExportUtils helpers read api_call.__name__.
    return mock


def _build_exporter(  # noqa: PLR0913
    *,
    select_site_return: str | None = "site-1",
    org_sites: list[dict[str, Any]] | Exception | None = None,
    debug_mode: bool = False,
    sle_response: Any = None,
    get_all_side_effect: Any = None,
) -> tuple[SiteExportUtils, dict[str, MagicMock | Any]]:
    """Assemble a SiteExportUtils with fully-mocked dependencies. Returns (exporter, mocks)."""
    exporter_mock = MagicMock()
    check_fn = MagicMock(return_value=debug_mode)
    sites_default = org_sites or [{"id": "site-1", "name": "My Site"}]

    if get_all_side_effect is not None:
        get_all_mock = MagicMock(side_effect=get_all_side_effect)
    elif isinstance(org_sites, Exception):
        get_all_mock = MagicMock(side_effect=org_sites)
    else:
        get_all_mock = MagicMock(return_value=sites_default)

    prompt_utils = SimpleNamespace(select_site=MagicMock(return_value=select_site_return))
    config_utils = SimpleNamespace(
        get_cached_or_prompted_org_id=MagicMock(return_value="org-1"),
        check_stop_signal=MagicMock(return_value=False),
    )
    data_proc = SimpleNamespace(
        flatten_nested_fields=MagicMock(side_effect=lambda rows: rows),
        escape_multiline=MagicMock(side_effect=lambda rows: rows),
        get_unique_keys=MagicMock(return_value=["name"]),
    )
    data_exp = SimpleNamespace(write_with_format_selection=exporter_mock)
    time_utils = SimpleNamespace(
        get_dynamic_lookback_hours=MagicMock(return_value=24),
        log_dynamic_lookback=MagicMock(),
    )
    enhanced_ssh = SimpleNamespace(sanitize_filename=MagicMock(side_effect=lambda value: value.replace(" ", "_")))
    insight_metrics = SimpleNamespace(
        export_const_insight_metrics=MagicMock(),
        get_by_scope=MagicMock(return_value=[]),
    )
    packet_cap = SimpleNamespace(
        validate_mac_address=MagicMock(return_value=True),
        normalize_mac_address=MagicMock(return_value="aa:bb:cc:dd:ee:ff"),
    )
    api_core = SimpleNamespace(all_sites_with_limit=MagicMock(return_value=[]))
    tqdm_mock = MagicMock(side_effect=lambda rows, **kwargs: rows)

    class _PrettyTable:  # WHY: minimal PrettyTable stand-in supporting field_names/valign/add_row.
        instances: list[_PrettyTable] = []

        def __init__(self) -> None:
            self.field_names: list[str] = []
            self.valign: str = ""
            self.rows: list[list[Any]] = []
            _PrettyTable.instances.append(self)

        def add_row(self, row: list[Any]) -> None:
            self.rows.append(row)

        def __str__(self) -> str:
            return f"PrettyTable(rows={len(self.rows)})"

    stats_ns = SimpleNamespace(
        searchSiteOspfStats=_named_mock("searchSiteOspfStats", {"status": "ok"}),
        listSiteBeaconsStats=_named_mock("listSiteBeaconsStats", {"status": "ok"}),
        listSiteAssetsStats=_named_mock("listSiteAssetsStats", {"status": "ok"}),
        getSiteStats=_named_mock("getSiteStats", {"foo": "bar"}),
        getSiteGatewayMetrics=_named_mock("getSiteGatewayMetrics", {"foo": "gw"}),
        getSiteSwitchesMetrics=_named_mock("getSiteSwitchesMetrics", {"foo": "sw"}),
        getSiteWxRulesUsage=_named_mock("getSiteWxRulesUsage", {"foo": "wx"}),
    )
    events_ns = SimpleNamespace(
        searchSiteSystemEvents=_named_mock("searchSiteSystemEvents", {"status": "ok"}),
        searchSiteFastRoamEvents=_named_mock("searchSiteFastRoamEvents", {"status": "ok"}),
    )
    mxedges_ns = SimpleNamespace(listSiteMxEdgeUpgrades=_named_mock("listSiteMxEdgeUpgrades", {"status": "ok"}))
    auto_map_ns = SimpleNamespace(
        getSiteAutoMapAssignmentStatus=_named_mock("getSiteAutoMapAssignmentStatus", {"status": "ok"})
    )
    rrm_ns = SimpleNamespace(
        getSiteCurrentChannelPlanning=_named_mock("getSiteCurrentChannelPlanning", {"ap-a": {"5": {"c": 1}}})
    )
    sle_ns = SimpleNamespace(
        listSiteSlesMetrics=_named_mock(
            "listSiteSlesMetrics", sle_response or {"enabled": ["m1"], "supported": ["m1", "m2"]}
        )
    )

    sites_ns = SimpleNamespace(
        listOrgSites=MagicMock(return_value={"status": "ok"}),
        stats=stats_ns,
        events=events_ns,
        mxedges=mxedges_ns,
        auto_map_assignment=auto_map_ns,
        rrm=rrm_ns,
        sle=sle_ns,
    )
    mistapi_dependency = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(sites=SimpleNamespace(listOrgSites=MagicMock(return_value={"status": "ok"}))),
                sites=sites_ns,
            )
        ),
        get_all=get_all_mock,
    )

    exporter = SiteExportUtils(
        apisession=object(),
        PromptUtils=prompt_utils,
        ConfigUtils=config_utils,
        DataProcessingUtils=data_proc,
        DataExporter=data_exp,
        TimeUtils=time_utils,
        EnhancedSSHRunner=enhanced_ssh,
        InsightMetricsUtils=insight_metrics,
        PacketCaptureManager=packet_cap,
        APICoreFetchUtils=api_core,
        check_fn=check_fn,
        PrettyTable=_PrettyTable,
        tqdm=tqdm_mock,
        mistapi=mistapi_dependency,
    )
    mocks: dict[str, Any] = {
        "exporter_mock": exporter_mock,
        "check_fn": check_fn,
        "prompt_utils": prompt_utils,
        "config_utils": config_utils,
        "data_proc": data_proc,
        "time_utils": time_utils,
        "stats_ns": stats_ns,
        "events_ns": events_ns,
        "rrm_ns": rrm_ns,
        "sle_ns": sle_ns,
        "get_all": get_all_mock,
        "pretty_table": _PrettyTable,
    }
    return exporter, mocks


# ---------------------------------------------------------------------------
# Class method tests
# ---------------------------------------------------------------------------


def test_fetch_site_data_bypasses_limit_kwarg_when_unsupported() -> None:
    """_fetch_site_data omits limit kwarg when the API does not accept it."""
    exporter, mocks = _build_exporter()
    api = _NoLimitApi()
    exporter._fetch_site_data(api, "site-1", {"extra": True})
    mocks["get_all"].assert_called_once()  # WHY: pagination path executed.


def test_emit_debug_table_renders_prettytable_and_progress() -> None:
    """_emit_debug_table configures PrettyTable columns and iterates rows via tqdm."""
    exporter, mocks = _build_exporter()
    exporter._emit_debug_table([{"name": "a"}, {"name": "b"}])
    table = mocks["pretty_table"].instances[-1]
    assert table.field_names == ["name"]
    assert table.valign == "t"
    assert len(table.rows) == 2


def test_write_site_report_returns_row_count_and_persists_rows() -> None:
    """_write_site_report normalises response, flattens rows, and returns count."""
    exporter, mocks = _build_exporter()
    api = _RecordingApiCall(return_value={"row": 1})
    count = exporter._write_site_report(api, "site-1", "OUT.csv", "getSiteFoo")
    assert count == 1  # WHY: single-row response wraps to length-1 list.
    mocks["exporter_mock"].assert_called_once()


def test_prompt_site_or_abort_returns_none_when_operator_declines(caplog: pytest.LogCaptureFixture) -> None:
    """_prompt_site_or_abort logs and returns None when the operator declines the site prompt."""
    exporter, _ = _build_exporter(select_site_return=None)
    with caplog.at_level(logging.ERROR):
        result = exporter._prompt_site_or_abort("abort msg")
    assert result is None
    assert "abort msg" in caplog.text


def test_run_dynamic_event_export_reuses_export_data_pipeline() -> None:
    """_run_dynamic_event_export calls TimeUtils.log_dynamic_lookback + _export_data."""
    exporter, mocks = _build_exporter()
    api = _RecordingApiCall(return_value=[{"row": 1}])
    exporter._run_dynamic_event_export(api, "events", "describe events")
    mocks["time_utils"].log_dynamic_lookback.assert_called_once_with("describe events", 24)
    # verify export writer invoked
    mocks["exporter_mock"].assert_called_once()


def test_fetch_site_sle_metrics_payload_returns_empty_when_non_dict() -> None:
    """SLE metrics fetch returns empty dict when API payload is not a dict."""
    exporter, mocks = _build_exporter()
    mocks["sle_ns"].listSiteSlesMetrics.return_value = "not-a-dict"
    assert exporter._fetch_site_sle_metrics_payload("site-1") == {}


def test_fetch_site_sle_metrics_payload_returns_dict_when_data_attribute_present() -> None:
    """SLE metrics fetch unwraps .data attribute when present."""
    exporter, mocks = _build_exporter()
    mocks["sle_ns"].listSiteSlesMetrics.return_value = SimpleNamespace(data={"enabled": ["m1"]})
    assert exporter._fetch_site_sle_metrics_payload("site-1") == {"enabled": ["m1"]}


def test_write_insight_rows_writes_and_logs_when_rows_present(
    caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """_write_insight_rows writes CSV and prints success line for non-empty rows."""
    exporter, mocks = _build_exporter()
    with caplog.at_level(logging.INFO):
        exporter._write_insight_rows([{"metric_name": "m1"}], "f.csv", "site")
    mocks["exporter_mock"].assert_called_once_with([{"metric_name": "m1"}], "f.csv")
    assert "1 records exported" in capsys.readouterr().out


def test_write_insight_rows_writes_empty_file_when_rows_missing(
    caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """_write_insight_rows writes empty file + prints empty message when no rows."""
    exporter, mocks = _build_exporter()
    with caplog.at_level(logging.WARNING):
        exporter._write_insight_rows([], "f.csv", "site")
    mocks["exporter_mock"].assert_called_once_with([], "f.csv")
    assert "no metrics available" in capsys.readouterr().out
    assert "No site SLE metric insight data available" in caplog.text


def test_resolve_insights_site_name_falls_back_to_id_on_error(caplog: pytest.LogCaptureFixture) -> None:
    """_resolve_insights_site_name catches API errors and returns site_id."""
    exporter, _ = _build_exporter(org_sites=RuntimeError("boom"))
    with caplog.at_level(logging.ERROR):
        assert exporter._resolve_insights_site_name("site-1") == "site-1"


def test_resolve_site_name_success_returns_org_site_name() -> None:
    """_resolve_site_name returns human-readable name from org listing."""
    exporter, _ = _build_exporter()
    assert exporter._resolve_site_name("site-1") == "My Site"


def test_resolve_site_name_falls_back_to_id_on_error() -> None:
    """_resolve_site_name catches API errors and returns site_id."""
    exporter, _ = _build_exporter(org_sites=RuntimeError("boom"))
    assert exporter._resolve_site_name("site-1") == "site-1"


def test_display_or_log_results_debug_mode_calls_debug_table() -> None:
    """When check_fn returns True the debug table path executes and skips summary log."""
    exporter, mocks = _build_exporter(debug_mode=True)
    exporter._display_or_log_results([{"name": "row"}], "data type", "out.csv")
    # PrettyTable stand-in captured invocation with expected column
    assert mocks["pretty_table"].instances, "expected PrettyTable to be constructed"


def test_display_or_log_results_non_debug_logs_summary(caplog: pytest.LogCaptureFixture) -> None:
    """Non-debug branch logs summary line via logging.info."""
    exporter, _ = _build_exporter(debug_mode=False)
    with caplog.at_level(logging.INFO):
        exporter._display_or_log_results([{"name": "row"}], "data type", "out.csv")
    assert "export completed" in caplog.text


def test_export_data_returns_when_rawdata_is_none(caplog: pytest.LogCaptureFixture) -> None:
    """_export_data logs warning and returns early when API returns None rawdata."""
    exporter, mocks = _build_exporter()
    # Configure two get_all calls (site name resolve, then site data)
    mocks["get_all"].side_effect = [
        [{"id": "site-1", "name": "My Site"}],  # WHY: name resolution.
        None,  # WHY: force rawdata None branch.
    ]
    api = _RecordingApiCall(return_value={"row": 1})
    with caplog.at_level(logging.WARNING):
        exporter._export_data(api_call=api, data_type="test data")
    assert "No data returned from API" in caplog.text


def test_export_data_raises_and_logs_on_api_failure(caplog: pytest.LogCaptureFixture) -> None:
    """_export_data logs and re-raises when downstream API raises."""
    exporter, mocks = _build_exporter()

    def boom(*_a: Any, **_k: Any) -> Any:  # WHY: emulate API raise.
        raise RuntimeError("api down")

    # Configure get_all so the first call (site name) succeeds, then never reaches second.
    mocks["get_all"].side_effect = [[{"id": "site-1", "name": "My Site"}], RuntimeError("api down")]
    api = _RecordingApiCall(return_value={"row": 1})
    api.__call__ = boom  # type: ignore[method-assign]

    with pytest.raises(RuntimeError):
        with caplog.at_level(logging.ERROR):
            exporter._export_data(api_call=api, data_type="test data")


def test_insights_happy_path_writes_rows(caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]) -> None:
    """insights() resolves site, fetches SLE payload and writes rows."""
    exporter, mocks = _build_exporter()
    with caplog.at_level(logging.INFO):
        exporter.insights()
    # write_with_format_selection called once for the rows.
    mocks["exporter_mock"].assert_called_once()
    args, _kwargs = mocks["exporter_mock"].call_args
    written_rows, filename = args
    assert filename.startswith("SiteSleMetricsInsights_")
    assert len(written_rows) == 2  # WHY: enabled+supported union produces 2 rows.


def test_insights_returns_when_no_site_selected() -> None:
    """insights() bails out when the operator declines the site prompt."""
    exporter, mocks = _build_exporter(select_site_return=None)
    exporter.insights()
    mocks["exporter_mock"].assert_not_called()


def test_insights_handles_api_error_by_writing_empty_file(capsys: pytest.CaptureFixture[str]) -> None:
    """insights() error branch writes empty file and prints operator message."""
    exporter, mocks = _build_exporter()
    mocks["sle_ns"].listSiteSlesMetrics.side_effect = RuntimeError("boom")
    exporter.insights()
    # writer should still be called once with empty rows.
    mocks["exporter_mock"].assert_called_once()
    args, _kwargs = mocks["exporter_mock"].call_args
    assert args[0] == []  # WHY: empty file for pipeline continuity.
    assert "Error exporting site SLE metric insights" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Public export wrappers (dynamic-event, single-endpoint, and generic)
# ---------------------------------------------------------------------------


def test_system_events_delegates_via_run_dynamic_event_export() -> None:
    """_system_events wraps searchSiteSystemEvents via dynamic-lookback helper."""
    exporter, mocks = _build_exporter()
    exporter._system_events()
    mocks["exporter_mock"].assert_called_once()


def test_fast_roam_events_delegates_via_run_dynamic_event_export() -> None:
    """_fast_roam_events wraps searchSiteFastRoamEvents via dynamic-lookback helper."""
    exporter, mocks = _build_exporter()
    exporter._fast_roam_events()
    mocks["exporter_mock"].assert_called_once()


def test_ospf_stats_invokes_generic_exporter() -> None:
    """ospf_stats invokes shared _export_data pipeline."""
    exporter, mocks = _build_exporter()
    exporter.ospf_stats()
    mocks["exporter_mock"].assert_called_once()


def test_mxedge_upgrade_status_invokes_generic_exporter() -> None:
    """mxedge_upgrade_status invokes shared _export_data pipeline."""
    exporter, mocks = _build_exporter()
    exporter.mxedge_upgrade_status()
    mocks["exporter_mock"].assert_called_once()


def test_auto_map_assignment_status_invokes_generic_exporter() -> None:
    """auto_map_assignment_status invokes shared _export_data pipeline."""
    exporter, mocks = _build_exporter()
    exporter.auto_map_assignment_status()
    mocks["exporter_mock"].assert_called_once()


def test_beacons_stats_invokes_generic_exporter() -> None:
    """beacons_stats invokes shared _export_data pipeline."""
    exporter, mocks = _build_exporter()
    exporter.beacons_stats()
    mocks["exporter_mock"].assert_called_once()


def test_assets_stats_invokes_generic_exporter() -> None:
    """assets_stats invokes shared _export_data pipeline."""
    exporter, mocks = _build_exporter()
    exporter.assets_stats()
    mocks["exporter_mock"].assert_called_once()


def test_site_stats_writes_report(caplog: pytest.LogCaptureFixture) -> None:
    """site_stats delegates to _write_site_report and logs record count."""
    exporter, mocks = _build_exporter()
    with caplog.at_level(logging.INFO):
        exporter.site_stats()
    mocks["exporter_mock"].assert_called_once()
    assert "site stats records" in caplog.text


def test_site_stats_handles_exception(caplog: pytest.LogCaptureFixture) -> None:
    """site_stats logs when the underlying API call raises."""
    exporter, mocks = _build_exporter()
    mocks["stats_ns"].getSiteStats.side_effect = RuntimeError("api down")
    with caplog.at_level(logging.ERROR):
        exporter.site_stats()
    assert "Failed to export site stats" in caplog.text


def test_site_stats_returns_when_no_site_selected() -> None:
    """site_stats returns immediately when operator declines the prompt."""
    exporter, mocks = _build_exporter(select_site_return=None)
    exporter.site_stats()
    mocks["exporter_mock"].assert_not_called()


def test_gateway_metrics_writes_report_and_handles_exception(caplog: pytest.LogCaptureFixture) -> None:
    """gateway_metrics happy path writes report; error path logs."""
    exporter, mocks = _build_exporter()
    exporter.gateway_metrics()
    mocks["exporter_mock"].assert_called_once()
    mocks["stats_ns"].getSiteGatewayMetrics.side_effect = RuntimeError("api down")
    with caplog.at_level(logging.ERROR):
        exporter.gateway_metrics()
    assert "Failed to export gateway metrics" in caplog.text


def test_gateway_metrics_returns_when_no_site_selected() -> None:
    """gateway_metrics aborts early when operator declines prompt."""
    exporter, mocks = _build_exporter(select_site_return=None)
    exporter.gateway_metrics()
    mocks["exporter_mock"].assert_not_called()


def test_switches_metrics_writes_report_and_handles_exception(caplog: pytest.LogCaptureFixture) -> None:
    """switches_metrics happy + error paths."""
    exporter, mocks = _build_exporter()
    exporter.switches_metrics()
    mocks["exporter_mock"].assert_called_once()
    mocks["stats_ns"].getSiteSwitchesMetrics.side_effect = RuntimeError("api down")
    with caplog.at_level(logging.ERROR):
        exporter.switches_metrics()
    assert "Failed to export switches metrics" in caplog.text


def test_switches_metrics_returns_when_no_site_selected() -> None:
    """switches_metrics aborts early when no site is selected."""
    exporter, mocks = _build_exporter(select_site_return=None)
    exporter.switches_metrics()
    mocks["exporter_mock"].assert_not_called()


def test_wxrules_usage_writes_report_and_handles_exception(caplog: pytest.LogCaptureFixture) -> None:
    """wxrules_usage happy + error paths."""
    exporter, mocks = _build_exporter()
    exporter.wxrules_usage()
    mocks["exporter_mock"].assert_called_once()
    mocks["stats_ns"].getSiteWxRulesUsage.side_effect = RuntimeError("api down")
    with caplog.at_level(logging.ERROR):
        exporter.wxrules_usage()
    assert "Failed to export WxRules usage" in caplog.text


def test_wxrules_usage_returns_when_no_site_selected() -> None:
    """wxrules_usage aborts early when no site is selected."""
    exporter, mocks = _build_exporter(select_site_return=None)
    exporter.wxrules_usage()
    mocks["exporter_mock"].assert_not_called()


def test_current_channel_planning_writes_rows(caplog: pytest.LogCaptureFixture) -> None:
    """current_channel_planning flattens and writes RRM plan rows."""
    exporter, mocks = _build_exporter()
    with caplog.at_level(logging.INFO):
        exporter.current_channel_planning()
    mocks["exporter_mock"].assert_called_once()
    assert "channel planning records" in caplog.text


def test_current_channel_planning_returns_when_no_site_selected() -> None:
    """current_channel_planning aborts early when operator declines."""
    exporter, mocks = _build_exporter(select_site_return=None)
    exporter.current_channel_planning()
    mocks["exporter_mock"].assert_not_called()


def test_current_channel_planning_handles_exception(caplog: pytest.LogCaptureFixture) -> None:
    """current_channel_planning logs when RRM API raises."""
    exporter, mocks = _build_exporter()
    mocks["rrm_ns"].getSiteCurrentChannelPlanning.side_effect = RuntimeError("api down")
    with caplog.at_level(logging.ERROR):
        exporter.current_channel_planning()
    assert "Failed to export channel planning" in caplog.text


def test_zone_config_analysis_delegates_to_zone_analyzer(monkeypatch: pytest.MonkeyPatch) -> None:
    """zone_config_analysis routes to ZoneConfigurationAnalyzer.analyze with wired deps."""
    exporter, _ = _build_exporter()
    from src.analytics import zone_analyzer as za_module  # WHY: patch analyzer under test.

    analyze_mock = MagicMock()
    monkeypatch.setattr(za_module.ZoneConfigurationAnalyzer, "analyze", analyze_mock)
    exporter.zone_config_analysis()
    analyze_mock.assert_called_once()
    kwargs = analyze_mock.call_args.kwargs
    assert set(kwargs) == {"apisession", "get_org_id_fn", "check_stop_fn", "all_sites_fn", "save_data_fn"}
