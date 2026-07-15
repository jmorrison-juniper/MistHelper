"""Wave 8 P2 coverage — SecurityEventsService (branches not covered by legacy test)."""

from __future__ import annotations

from types import SimpleNamespace  # WHY: lightweight bundle for dependency injection into the resolver
from typing import Any  # WHY: heterogeneous API payload typing
from unittest.mock import MagicMock, patch  # WHY: MagicMock(spec=...) + resolver patch per project standard

import pytest  # WHY: capsys fixture for stdout assertions

from src.refactors.serial_cc import security_events as sut  # WHY: SUT module (helpers + service class)
from src.refactors.serial_cc.security_events import (  # WHY: named imports for direct helper coverage
    _ROGUE_KINDS,
    SecurityEventsService,
    _FlattenedExportSpec,
)


def _make_deps() -> SimpleNamespace:  # WHY: minimal dependency bundle with typed mocks
    """Return a fresh SimpleNamespace dependency bundle with MagicMock members."""
    return SimpleNamespace(  # WHY: matches shape produced by _resolve_runtime_dependencies
        ConfigUtils=MagicMock(
            spec=SimpleNamespace(get_cached_or_prompted_org_id=lambda: "", check_stop_signal=lambda: False)
        ),  # WHY: two attrs used by service
        PROGRESS_EMITTER=None,  # WHY: default None; tests override when exercising emitter branch
        TimeUtils=MagicMock(
            spec=SimpleNamespace(get_dynamic_lookback_hours=lambda p, t: 0, log_dynamic_lookback=lambda label, h: None)
        ),  # WHY: rogue export helpers
        CacheUtils=MagicMock(
            spec=SimpleNamespace(check_and_generate_csv=lambda name, cb: None)
        ),  # WHY: seeds site list cache
        OrgSiteExporter=SimpleNamespace(sites=MagicMock(spec=lambda: None)),  # WHY: attribute accessed as callable ref
        DataProcessingUtils=MagicMock(
            spec=SimpleNamespace(flatten_nested_fields=lambda r: r, escape_multiline=lambda r: r)
        ),  # WHY: pipeline helpers
        DataExporter=MagicMock(
            spec=SimpleNamespace(write_with_format_selection=lambda rows, filename: None)
        ),  # WHY: file writer
        FilePathUtils=MagicMock(spec=SimpleNamespace(get_csv_path=lambda name: name)),  # WHY: path resolver
        mistapi=MagicMock(),  # WHY: SDK entry point — attributes accessed dynamically
        apisession=MagicMock(),  # WHY: opaque session token passed through
        tqdm=lambda items, **_kwargs: items,  # WHY: pass-through iterator for deterministic loops
        csv_freshness_minutes=60,  # WHY: matches production default
    )


def test_all_outputs_fresh_returns_false_when_missing() -> None:
    """A missing file forces the freshness guard to False."""
    deps = _make_deps()  # WHY: default bundle
    deps.FilePathUtils.get_csv_path.side_effect = lambda name: name  # WHY: identity mapping for the probe
    with patch("src.refactors.serial_cc.security_events.os.path.exists", return_value=False):  # WHY: force miss
        assert SecurityEventsService._all_outputs_fresh(deps, ["nope.csv"]) is False  # WHY: missing file => False


def test_all_outputs_fresh_returns_false_when_stale() -> None:
    """Files older than the freshness window return False."""
    deps = _make_deps()  # WHY: default bundle
    deps.FilePathUtils.get_csv_path.side_effect = lambda name: name  # WHY: identity mapping
    with (
        patch("src.refactors.serial_cc.security_events.os.path.exists", return_value=True),  # WHY: file present
        patch("src.refactors.serial_cc.security_events.os.path.getmtime", return_value=0),  # WHY: mtime long ago
        patch("src.refactors.serial_cc.security_events.time.time", return_value=60 * 60 * 24 * 30),  # WHY: 30d
    ):
        assert SecurityEventsService._all_outputs_fresh(deps, ["stale.csv"]) is False  # WHY: age > 60 min


def test_all_outputs_fresh_returns_false_on_exception() -> None:
    """A filesystem error trips the broad-except guard and returns False."""
    deps = _make_deps()  # WHY: default bundle
    deps.FilePathUtils.get_csv_path.side_effect = OSError("nope")  # WHY: force the broad-except path
    assert SecurityEventsService._all_outputs_fresh(deps, ["boom.csv"]) is False  # WHY: exception => False


def test_execute_fast_mode_falls_through_when_stale(monkeypatch: pytest.MonkeyPatch) -> None:
    """When fast=True but cache is stale, the full workflow runs."""
    deps = _make_deps()  # WHY: default bundle
    deps.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: needed for workflow
    deps.mistapi.get_all.return_value = []  # WHY: all fetches empty; short-circuits export paths
    monkeypatch.setattr(sut, "_resolve_runtime_dependencies", lambda: deps)  # WHY: inject deps bundle
    with (
        patch("src.refactors.serial_cc.security_events.os.path.exists", return_value=False),  # WHY: force stale
        patch(
            "src.refactors.serial_cc.security_events.open",
            MagicMock(spec=lambda p, encoding=None: None),
        ),  # WHY: any open() call succeeds
        patch("src.refactors.serial_cc.security_events.csv.DictReader", return_value=[]),  # WHY: empty site list
    ):
        SecurityEventsService.execute(fast=True)  # WHY: exercise fast=True + stale fall-through
    assert deps.DataExporter.write_with_format_selection.call_count >= 3  # WHY: all three files written


def test_run_export_workflow_emits_progress_bookends(monkeypatch: pytest.MonkeyPatch) -> None:
    """A populated PROGRESS_EMITTER receives start + complete emissions."""
    deps = _make_deps()  # WHY: default bundle
    emitter = MagicMock(  # WHY: emitter mock with the two methods invoked by the service
        spec=SimpleNamespace(
            emit_progress_start=lambda issue, stage, total: None,  # WHY: matches signature
            emit_progress_complete=lambda ctx, total, cancelled, duration: None,  # WHY: matches signature
        )
    )
    deps.PROGRESS_EMITTER = emitter  # WHY: exercise the emitter-populated branch
    deps.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: needed for workflow
    deps.mistapi.get_all.return_value = []  # WHY: empty datasets short-circuit downstream
    monkeypatch.setattr(sut, "_resolve_runtime_dependencies", lambda: deps)  # WHY: inject deps bundle
    with (
        patch(
            "src.refactors.serial_cc.security_events.open",
            MagicMock(spec=lambda p, encoding=None: None),
        ),  # WHY: any open() call succeeds
        patch("src.refactors.serial_cc.security_events.csv.DictReader", return_value=[]),  # WHY: empty site list
    ):
        SecurityEventsService.execute(fast=False)  # WHY: run the full workflow
    emitter.emit_progress_start.assert_called_once()  # WHY: start bookend emitted
    emitter.emit_progress_complete.assert_called_once()  # WHY: complete bookend emitted


def test_build_flattened_specs_returns_two_specs() -> None:
    """_build_flattened_specs returns the two expected export specs."""
    deps = _make_deps()  # WHY: default bundle for spec construction
    specs = SecurityEventsService._build_flattened_specs(deps, "org-1")  # WHY: exercise the helper
    assert len(specs) == 2  # WHY: policies + secintel profiles
    assert specs[0].output_file == "OrgSecurityPolicies.csv"  # WHY: policies target file
    assert specs[1].output_file == "OrgSecIntelProfiles.csv"  # WHY: secintel target file


def test_export_flattened_dataset_empty_writes_empty_file(capsys: pytest.CaptureFixture[str]) -> None:
    """An empty dataset writes an empty CSV and prints the empty summary."""
    deps = _make_deps()  # WHY: default bundle
    deps.mistapi.get_all.return_value = []  # WHY: force empty dataset
    spec = _FlattenedExportSpec(  # WHY: minimal spec for the empty branch
        output_file="OrgSecurityPolicies.csv",
        data_label="security policies",
        start_label="secpolicies",
        fetcher=lambda: None,  # WHY: response is unused when get_all returns []
        empty_message="No data",
        empty_suffix="(no policies found)",
    )
    SecurityEventsService._export_flattened_dataset(deps, spec)  # WHY: exercise the empty guard
    deps.DataExporter.write_with_format_selection.assert_called_once_with(
        [], "OrgSecurityPolicies.csv"
    )  # WHY: empty write
    assert "no policies found" in capsys.readouterr().out  # WHY: empty summary printed


def test_export_flattened_dataset_populates(capsys: pytest.CaptureFixture[str]) -> None:
    """A populated dataset is flattened, escaped, and exported with a count summary."""
    deps = _make_deps()  # WHY: default bundle
    deps.mistapi.get_all.return_value = [{"id": "one"}, {"id": "two"}]  # WHY: two rows
    deps.DataProcessingUtils.flatten_nested_fields.side_effect = lambda rows: rows  # WHY: identity pipeline
    deps.DataProcessingUtils.escape_multiline.side_effect = lambda rows: rows  # WHY: identity pipeline
    spec = _FlattenedExportSpec(  # WHY: minimal spec for the populated branch
        output_file="OrgSecurityPolicies.csv",
        data_label="security policies",
        start_label="secpolicies",
        fetcher=lambda: MagicMock(),  # WHY: response object passed to get_all
        empty_message="No data",
        empty_suffix="(no policies found)",
    )
    SecurityEventsService._export_flattened_dataset(deps, spec)  # WHY: exercise the populated branch
    assert deps.DataExporter.write_with_format_selection.call_count == 1  # WHY: one write for populated
    assert "2 security policies exported" in capsys.readouterr().out  # WHY: count summary printed


def test_fetch_dataset_returns_empty_on_exception() -> None:
    """A fetcher exception is swallowed and returns []."""
    deps = _make_deps()  # WHY: default bundle

    def _boom() -> None:  # WHY: fetcher raises to force the exception branch
        raise RuntimeError("kaboom")  # WHY: any exception exercises the broad-except

    spec = _FlattenedExportSpec(  # WHY: minimal spec pointing at the raising fetcher
        output_file="OrgSecurityPolicies.csv",
        data_label="security policies",
        start_label="secpolicies",
        fetcher=_boom,
        empty_message="No data",
        empty_suffix="(no policies found)",
    )
    result = SecurityEventsService._fetch_dataset(deps, spec)  # WHY: exercise exception path
    assert result == []  # WHY: contract: empty list on failure


def test_fetch_dataset_returns_dataset_on_success() -> None:
    """A successful fetcher returns the paged dataset."""
    deps = _make_deps()  # WHY: default bundle
    deps.mistapi.get_all.return_value = [{"id": "one"}]  # WHY: one row from the pager
    spec = _FlattenedExportSpec(  # WHY: minimal spec
        output_file="OrgSecurityPolicies.csv",
        data_label="security policies",
        start_label="secpolicies",
        fetcher=lambda: MagicMock(),  # WHY: response passed through to get_all
        empty_message="No data",
        empty_suffix="(no policies found)",
    )
    assert SecurityEventsService._fetch_dataset(deps, spec) == [{"id": "one"}]  # WHY: pass-through


def test_fetch_tagged_rogue_tags_records() -> None:
    """Every rogue record is annotated with site_id/site_name/rogue_type."""
    deps = _make_deps()  # WHY: default bundle
    records = [{"mac": "aa"}, {"mac": "bb"}]  # WHY: two rogue records to tag
    fetcher = MagicMock(spec=lambda session, sid, duration, limit: None)  # WHY: dynamic endpoint mock
    fetcher.return_value = MagicMock()  # WHY: response object
    deps.mistapi.api.v1.sites.insights.listSiteRogueAPs = fetcher  # WHY: match _ROGUE_KINDS[0].endpoint
    deps.mistapi.get_all.return_value = records  # WHY: pager yields our list

    result = SecurityEventsService._fetch_tagged_rogue(
        deps, "site-1", "SiteOne", "168h", _ROGUE_KINDS[0]
    )  # WHY: exercise the tagging loop
    assert all(r["site_id"] == "site-1" for r in result)  # WHY: site_id tag applied
    assert all(r["site_name"] == "SiteOne" for r in result)  # WHY: site_name tag applied
    assert all(r["rogue_type"] == "AP" for r in result)  # WHY: kind label applied


def test_fetch_site_rogue_returns_both_kinds() -> None:
    """Success path returns tuple of (aps, clients) after tagging both kinds."""
    deps = _make_deps()  # WHY: default bundle
    ap_fetcher = MagicMock(spec=lambda s, sid, duration, limit: None)  # WHY: rogue AP endpoint mock
    ap_fetcher.return_value = MagicMock()  # WHY: response object
    client_fetcher = MagicMock(spec=lambda s, sid, duration, limit: None)  # WHY: rogue client endpoint mock
    client_fetcher.return_value = MagicMock()  # WHY: response object
    deps.mistapi.api.v1.sites.insights.listSiteRogueAPs = ap_fetcher  # WHY: attach AP endpoint
    deps.mistapi.api.v1.sites.insights.listSiteRogueClients = client_fetcher  # WHY: attach client endpoint
    deps.mistapi.get_all.side_effect = [[{"mac": "aa"}], [{"mac": "bb"}]]  # WHY: two pages, one per kind

    aps, clients = SecurityEventsService._fetch_site_rogue(deps, "site-1", "SiteOne", "168h")  # WHY: run helper
    assert aps[0]["rogue_type"] == "AP"  # WHY: AP tagged
    assert clients[0]["rogue_type"] == "Client"  # WHY: Client tagged


def test_fetch_site_rogue_returns_empties_on_exception() -> None:
    """Any exception during per-site fetch yields ([],[]) so the outer loop keeps going."""
    deps = _make_deps()  # WHY: default bundle
    fetcher = MagicMock(spec=lambda s, sid, duration, limit: None)  # WHY: raises on call
    fetcher.side_effect = RuntimeError("boom")  # WHY: force per-site failure branch
    deps.mistapi.api.v1.sites.insights.listSiteRogueAPs = fetcher  # WHY: AP fetch raises first
    aps, clients = SecurityEventsService._fetch_site_rogue(deps, "site-1", "SiteOne", "168h")  # WHY: run helper
    assert aps == []  # WHY: empty on exception
    assert clients == []  # WHY: empty on exception


def test_iterate_site_rogue_honors_stop_signal(monkeypatch: pytest.MonkeyPatch) -> None:
    """When the stop signal fires, iteration breaks before the next fetch."""
    deps = _make_deps()  # WHY: default bundle
    deps.ConfigUtils.check_stop_signal.side_effect = [True]  # WHY: first call trips the guard
    site_rows = [{"id": "site-1", "name": "SiteOne"}]  # WHY: single row so break is observable
    with (
        patch(
            "src.refactors.serial_cc.security_events.open",
            MagicMock(spec=lambda p, encoding=None: None),
        ),  # WHY: open() opaque
        patch(
            "src.refactors.serial_cc.security_events.csv.DictReader",
            return_value=site_rows,
        ),  # WHY: DictReader yields our stub rows
    ):
        result = list(SecurityEventsService._iterate_site_rogue(deps, "168h"))  # WHY: consume iterator
    assert result == []  # WHY: break before yielding


def test_iterate_site_rogue_skips_missing_site_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rows without an id are skipped defensively."""
    deps = _make_deps()  # WHY: default bundle
    deps.ConfigUtils.check_stop_signal.return_value = False  # WHY: never break out
    site_rows: list[dict[str, Any]] = [{"name": "NoIdSite"}]  # WHY: no 'id' key exercises the guard
    with (
        patch(
            "src.refactors.serial_cc.security_events.open",
            MagicMock(spec=lambda p, encoding=None: None),
        ),  # WHY: open() opaque
        patch(
            "src.refactors.serial_cc.security_events.csv.DictReader",
            return_value=site_rows,
        ),  # WHY: rows without id
    ):
        result = list(SecurityEventsService._iterate_site_rogue(deps, "168h"))  # WHY: consume iterator
    assert result == []  # WHY: only row was skipped


def test_iterate_site_rogue_yields_valid_site(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valid rows yield the per-site fetch tuple."""
    deps = _make_deps()  # WHY: default bundle
    deps.ConfigUtils.check_stop_signal.return_value = False  # WHY: never break out
    ap_fetcher = MagicMock(spec=lambda s, sid, duration, limit: None)  # WHY: rogue AP endpoint mock
    ap_fetcher.return_value = MagicMock()  # WHY: response object
    client_fetcher = MagicMock(spec=lambda s, sid, duration, limit: None)  # WHY: rogue client endpoint mock
    client_fetcher.return_value = MagicMock()  # WHY: response object
    deps.mistapi.api.v1.sites.insights.listSiteRogueAPs = ap_fetcher  # WHY: attach AP endpoint
    deps.mistapi.api.v1.sites.insights.listSiteRogueClients = client_fetcher  # WHY: attach client endpoint
    deps.mistapi.get_all.side_effect = [[{"mac": "aa"}], [{"mac": "bb"}]]  # WHY: two pages
    site_rows = [{"id": "site-1", "name": "SiteOne"}]  # WHY: one valid row
    with (
        patch(
            "src.refactors.serial_cc.security_events.open",
            MagicMock(spec=lambda p, encoding=None: None),
        ),  # WHY: open() opaque
        patch(
            "src.refactors.serial_cc.security_events.csv.DictReader",
            return_value=site_rows,
        ),  # WHY: our stub row
    ):
        result = list(SecurityEventsService._iterate_site_rogue(deps, "168h"))  # WHY: consume iterator
    assert len(result) == 1  # WHY: one valid row yields once
    aps, clients = result[0]  # WHY: unpack the yielded tuple
    assert aps[0]["rogue_type"] == "AP"  # WHY: AP tag applied
    assert clients[0]["rogue_type"] == "Client"  # WHY: Client tag applied


def test_export_rogue_combined_empty_writes_empty(capsys: pytest.CaptureFixture[str]) -> None:
    """Empty rogue list writes an empty file and prints the zero-count summary."""
    deps = _make_deps()  # WHY: default bundle
    SecurityEventsService._export_rogue_combined(deps, [])  # WHY: exercise empty guard
    deps.DataExporter.write_with_format_selection.assert_called_once_with([], "OrgRogueData.csv")  # WHY: empty write
    assert "0 rogue devices" in capsys.readouterr().out  # WHY: zero summary printed


def test_export_rogue_combined_populated_flattens_and_exports(capsys: pytest.CaptureFixture[str]) -> None:
    """Populated rogue list is flattened, escaped, and exported with a count summary."""
    deps = _make_deps()  # WHY: default bundle
    deps.DataProcessingUtils.flatten_nested_fields.side_effect = lambda rows: rows  # WHY: identity pipeline
    deps.DataProcessingUtils.escape_multiline.side_effect = lambda rows: rows  # WHY: identity pipeline
    rogue = [{"mac": "aa", "rogue_type": "AP"}, {"mac": "bb", "rogue_type": "Client"}]  # WHY: two records
    SecurityEventsService._export_rogue_combined(deps, rogue)  # WHY: exercise populated branch
    deps.DataExporter.write_with_format_selection.assert_called_once_with(rogue, "OrgRogueData.csv")  # WHY: write
    assert "2 rogue devices exported" in capsys.readouterr().out  # WHY: count summary printed


def test_export_rogue_data_iterate_exception_aborts(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An exception during iteration aborts the rogue export leg silently."""
    deps = _make_deps()  # WHY: default bundle
    deps.TimeUtils.get_dynamic_lookback_hours.return_value = 168  # WHY: prod lookback value
    monkeypatch.setattr(  # WHY: force the iterator generator to raise mid-consumption
        SecurityEventsService,
        "_iterate_site_rogue",
        lambda deps_arg, duration: (_ for _ in ()).throw(RuntimeError("iter-boom")),  # WHY: raising generator
    )
    SecurityEventsService._export_rogue_data(deps)  # WHY: exercise the try/except that guards iteration
    deps.DataExporter.write_with_format_selection.assert_not_called()  # WHY: aborted before combined write


def test_export_rogue_data_happy_path_writes_combined(monkeypatch: pytest.MonkeyPatch) -> None:
    """Happy path aggregates rogue tuples and calls combined export."""
    deps = _make_deps()  # WHY: default bundle
    deps.TimeUtils.get_dynamic_lookback_hours.return_value = 168  # WHY: prod lookback value
    monkeypatch.setattr(  # WHY: stub iterator to a single per-site tuple
        SecurityEventsService,
        "_iterate_site_rogue",
        lambda deps_arg, duration: iter(
            [([{"mac": "aa", "rogue_type": "AP"}], [{"mac": "bb", "rogue_type": "Client"}])]
        ),
    )
    combined = MagicMock(spec=lambda deps_arg, rogue: None)  # WHY: capture combined call
    monkeypatch.setattr(SecurityEventsService, "_export_rogue_combined", combined)  # WHY: swap combined helper
    SecurityEventsService._export_rogue_data(deps)  # WHY: run the rogue export
    args, _kwargs = combined.call_args  # WHY: inspect the aggregated list argument
    assert len(args[1]) == 2  # WHY: aps + clients concatenated
