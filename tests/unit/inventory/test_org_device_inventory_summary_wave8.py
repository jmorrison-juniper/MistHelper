"""Wave 8 P2 coverage — OrgDeviceInventorySummary (extra branches/helpers)."""

from __future__ import annotations

import time as _stdlib_time  # WHY: patch time.time on the shared module (mypy-strict friendly)
from types import SimpleNamespace  # WHY: light stand-in for mistapi SDK modules and responses
from unittest.mock import MagicMock  # WHY: MagicMock(spec=Callable) is mandatory per project standard

import pytest  # WHY: capsys, monkeypatch fixtures drive banner assertions and env-var patching

from src.inventory.org_device_inventory_summary import (  # WHY: SUT plus DI seam
    OrgDeviceInventorySummaryCore,
    configure_org_device_inventory_summary_dependencies,
)


def _reset_dependencies(
    *,
    apisession: object | None = None,
    mistapi_module: object | None = None,
    exporter: MagicMock | None = None,
    org: str = "org-1",
) -> MagicMock:
    """Reset the module-level DI slots and return the exporter mock for assertions."""
    exporter = exporter or MagicMock(spec=lambda rows, filename, api_function_name=None: None)  # WHY: default stub
    api = (
        apisession if apisession is not None else SimpleNamespace(mist_get=MagicMock(return_value=None))
    )  # WHY: default
    mistapi_dep = (
        mistapi_module
        if mistapi_module is not None
        else SimpleNamespace(
            api=SimpleNamespace(
                v1=SimpleNamespace(
                    orgs=SimpleNamespace(
                        devices=SimpleNamespace(
                            searchOrgDevices=MagicMock(  # WHY: default page returns empty results w/ no next
                                return_value=SimpleNamespace(data={"results": [], "next": None})
                            )
                        ),
                        inventory=SimpleNamespace(getOrgInventory=MagicMock(return_value=SimpleNamespace(data=[]))),
                        orgs=SimpleNamespace(
                            getOrg=MagicMock(return_value=SimpleNamespace(data={"name": "Default Org"}))
                        ),
                    )
                )
            ),
            get_all=MagicMock(return_value=[]),
        )
    )  # WHY: keep default stub compact for tests that don't care about specific endpoints
    configure_org_device_inventory_summary_dependencies(  # WHY: hydrate module globals for the SUT
        apisession_dependency=api,
        mistapi_dependency=mistapi_dep,
        data_exporter=SimpleNamespace(write_with_format_selection=exporter),
        org_id_value=org,
    )
    return exporter  # WHY: caller asserts exporter usage


def test_execute_guard_prints_error_when_org_missing(capsys: pytest.CaptureFixture[str]) -> None:
    """execute() prints error + returns early when no org has been configured."""
    _reset_dependencies(org="")  # WHY: empty org triggers the guard clause
    OrgDeviceInventorySummaryCore.execute()  # WHY: exercise the guard branch
    assert "No organization selected" in capsys.readouterr().out  # WHY: user-visible error surfaced


def test_execute_delegates_to_run_for_org(monkeypatch: pytest.MonkeyPatch) -> None:
    """execute() delegates to run_for_org when the org id is populated."""
    _reset_dependencies(org="org-abc")  # WHY: populated org exercises delegation branch
    called_with: list[str] = []  # WHY: capture the org id passed through

    def _fake_run_for_org(target_org_id: str) -> tuple[list, list, list, str]:  # WHY: spy on delegate
        called_with.append(target_org_id)  # WHY: record for assertion
        return ([], [], [], "org-abc")  # WHY: shape-compatible with the real return

    monkeypatch.setattr(  # WHY: patch delegate to isolate execute() branch
        OrgDeviceInventorySummaryCore, "run_for_org", staticmethod(_fake_run_for_org)
    )
    OrgDeviceInventorySummaryCore.execute()  # WHY: run through the happy path
    assert called_with == ["org-abc"]  # WHY: delegate invoked with the configured org id


def test_sanitize_name_replaces_bad_characters() -> None:
    """_sanitize_name replaces non-alphanumeric characters (except - and _) with underscores."""
    assert (
        OrgDeviceInventorySummaryCore._sanitize_name("Acme, Inc. / East")  # WHY: exercise punctuation + space branch
        == "Acme__Inc____East"
    )  # WHY: expected replacement pattern


def test_sanitize_name_preserves_hyphen_and_underscore() -> None:
    """_sanitize_name preserves hyphens and underscores verbatim."""
    assert (
        OrgDeviceInventorySummaryCore._sanitize_name("Org-One_Two") == "Org-One_Two"  # WHY: pure allowed-char branch
    )  # WHY: no substitutions performed


def test_lookup_org_name_from_api_returns_name() -> None:
    """_lookup_org_name_from_api returns the API-reported name on success."""
    mistapi_module = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    orgs=SimpleNamespace(getOrg=MagicMock(return_value=SimpleNamespace(data={"name": "AcmeCo"})))
                )
            )
        )
    )  # WHY: SDK returns a shape with a name key
    _reset_dependencies(mistapi_module=mistapi_module)  # WHY: replace default mistapi stub
    assert OrgDeviceInventorySummaryCore._lookup_org_name_from_api("org-1") == "AcmeCo"  # WHY: happy-path branch


def test_lookup_org_name_from_api_handles_exception() -> None:
    """_lookup_org_name_from_api returns None when the SDK raises."""
    mistapi_module = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    orgs=SimpleNamespace(
                        getOrg=MagicMock(side_effect=RuntimeError("boom"))  # WHY: force exception path
                    )
                )
            )
        )
    )
    _reset_dependencies(mistapi_module=mistapi_module)  # WHY: replace default mistapi stub
    assert OrgDeviceInventorySummaryCore._lookup_org_name_from_api("org-1") is None  # WHY: exception path returns None


def test_resolve_safe_org_name_prefers_api_name() -> None:
    """_resolve_safe_org_name uses the API name when the lookup returns a value."""
    mistapi_module = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    orgs=SimpleNamespace(getOrg=MagicMock(return_value=SimpleNamespace(data={"name": "Acme HQ"})))
                )
            )
        )
    )
    _reset_dependencies(mistapi_module=mistapi_module)  # WHY: API name available
    assert OrgDeviceInventorySummaryCore._resolve_safe_org_name("org-1") == "Acme_HQ"  # WHY: sanitized API name


def test_resolve_safe_org_name_falls_back_to_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """_resolve_safe_org_name falls back to END_CUSTOMER_NAME when the API returns no name."""
    mistapi_module = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    orgs=SimpleNamespace(
                        getOrg=MagicMock(return_value=SimpleNamespace(data={}))  # WHY: name missing => fall through
                    )
                )
            )
        )
    )
    _reset_dependencies(mistapi_module=mistapi_module)  # WHY: replace default mistapi stub
    monkeypatch.setenv("END_CUSTOMER_NAME", "FromEnv Co")  # WHY: env variable seeds the fallback branch
    assert OrgDeviceInventorySummaryCore._resolve_safe_org_name("org-1") == "FromEnv_Co"  # WHY: sanitized env value


def test_resolve_safe_org_name_falls_back_to_org_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """_resolve_safe_org_name falls back to the raw org id when both API + env are empty."""
    mistapi_module = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    orgs=SimpleNamespace(
                        getOrg=MagicMock(return_value=SimpleNamespace(data={}))  # WHY: name missing => fall through
                    )
                )
            )
        )
    )
    _reset_dependencies(mistapi_module=mistapi_module)  # WHY: replace default mistapi stub
    monkeypatch.delenv("END_CUSTOMER_NAME", raising=False)  # WHY: clear env so the id fallback fires
    assert (
        OrgDeviceInventorySummaryCore._resolve_safe_org_name("org-abc") == "org-abc"
    )  # WHY: id branch preserves hyphens


def test_print_summary_banner_prints_label_and_table(capsys: pytest.CaptureFixture[str]) -> None:
    """_print_summary_banner prints the labelled banner then the table body."""
    from prettytable import PrettyTable  # WHY: local import to avoid touching the SUT's shared reference

    table = PrettyTable()  # WHY: real PrettyTable instance so the __str__ output matches production
    table.field_names = ["Device Type", "Model", "Count"]  # WHY: canonical columns
    table.add_row(["ap", "AP41", 3])  # WHY: at least one row so the printed table has content
    OrgDeviceInventorySummaryCore._print_summary_banner("model", table)  # WHY: exercise the banner helper
    out = capsys.readouterr().out  # WHY: capture stdout
    assert "Model Distribution Summary" in out  # WHY: capitalized label surfaced
    assert "AP41" in out  # WHY: table body rendered under the banner


def test_display_and_export_renders_and_persists(capsys: pytest.CaptureFixture[str]) -> None:
    """_display_and_export builds the export rows, renders the banner, and calls the exporter."""
    exporter = _reset_dependencies()  # WHY: capture the injected exporter mock
    rows = [
        {"device_type": "ap", "model": "AP41", "count": 4},  # WHY: mixed rows to exercise the loop
        {"device_type": "switch", "model": "EX2300", "count": 2},
    ]
    OrgDeviceInventorySummaryCore._display_and_export(  # WHY: exercise render + export
        rows, "model", "Acme_Models", "orgDeviceModelSummary"
    )
    out = capsys.readouterr().out  # WHY: banner + table go to stdout
    assert "Model Distribution Summary" in out  # WHY: banner label present
    exporter.assert_called_once()  # WHY: exporter called exactly once
    args, kwargs = exporter.call_args  # WHY: unpack invocation
    export_rows, filename = args  # WHY: positional args are (rows, filename)
    assert filename == "Acme_Models"  # WHY: filename propagated verbatim
    assert kwargs == {"api_function_name": "orgDeviceModelSummary"}  # WHY: api hint routed via kwargs
    assert export_rows[0] == {"Device Type": "ap", "Model": "AP41", "Count": 4}  # WHY: keys were remapped for export


def test_run_model_report_returns_rows_and_exports(monkeypatch: pytest.MonkeyPatch) -> None:
    """_run_model_report fetches all counts, renders/exports them, and returns the rows."""
    _reset_dependencies()  # WHY: hydrate module DI seams
    fake_rows = [{"device_type": "ap", "model": "AP41", "count": 2}]  # WHY: shape shared with production
    fetch_calls: list[tuple[str, str, list | None, list | None]] = []  # WHY: capture _fetch_all_counts args

    def _fake_fetch(target_org_id, distinct, unassigned_records=None, ap_records=None):  # WHY: spy on delegate
        fetch_calls.append((target_org_id, distinct, unassigned_records, ap_records))  # WHY: record
        return fake_rows  # WHY: constant, easy-to-assert payload

    display_mock = MagicMock(spec=lambda rows, distinct, filename, api_func: None)  # WHY: replace exporter side-effect
    monkeypatch.setattr(OrgDeviceInventorySummaryCore, "_fetch_all_counts", staticmethod(_fake_fetch))  # WHY: isolate
    monkeypatch.setattr(  # WHY: bypass the real display/export
        OrgDeviceInventorySummaryCore, "_display_and_export", staticmethod(display_mock)
    )
    unassigned = [{"type": "switch"}]  # WHY: sentinel list to verify propagation
    ap_records = [{"model": "AP41"}]  # WHY: sentinel list to verify propagation
    result = OrgDeviceInventorySummaryCore._run_model_report("org-1", "Acme", unassigned, ap_records)  # WHY: run
    assert result is fake_rows  # WHY: returned rows are the fetched rows verbatim
    assert fetch_calls == [("org-1", "model", unassigned, ap_records)]  # WHY: propagation confirmed
    display_mock.assert_called_once_with(  # WHY: exporter invoked with expected filename/api hint
        fake_rows, "model", "Acme_OrgDeviceModelCounts", "orgDeviceModelSummary"
    )


def test_run_version_report_returns_rows_and_exports(monkeypatch: pytest.MonkeyPatch) -> None:
    """_run_version_report fetches all counts, renders/exports them, and returns the rows."""
    _reset_dependencies()  # WHY: hydrate module DI seams
    fake_rows = [{"device_type": "ap", "version": "0.12", "count": 5}]  # WHY: shape shared with production
    fetch_mock = MagicMock(spec=lambda *args, **kwargs: fake_rows)  # WHY: strict spec keeps signatures honest
    fetch_mock.return_value = fake_rows  # WHY: return the fixed rows
    display_mock = MagicMock(spec=lambda rows, distinct, filename, api_func: None)  # WHY: replace exporter
    monkeypatch.setattr(OrgDeviceInventorySummaryCore, "_fetch_all_counts", staticmethod(fetch_mock))  # WHY: isolate
    monkeypatch.setattr(  # WHY: bypass real display/export
        OrgDeviceInventorySummaryCore, "_display_and_export", staticmethod(display_mock)
    )
    result = OrgDeviceInventorySummaryCore._run_version_report("org-1", "Acme", [], [])  # WHY: run
    assert result is fake_rows  # WHY: returned rows are the fetched rows verbatim
    display_mock.assert_called_once_with(  # WHY: exporter invoked with version filename/api hint
        fake_rows, "version", "Acme_OrgDeviceFirmwareSummary", "orgDeviceFirmwareSummary"
    )


def test_run_pivot_report_uses_lazy_imported_collaborators(monkeypatch: pytest.MonkeyPatch) -> None:
    """_run_pivot_report calls the lazy-imported VersionPerModelFetcher and PivotRenderer once each."""
    _reset_dependencies()  # WHY: hydrate module DI seams
    from src.inventory.inventory_summary import pivot_renderer as pivot_mod  # WHY: patch the real symbol
    from src.inventory.inventory_summary import version_per_model_fetcher as vpm_mod  # WHY: patch the real symbol

    vpm_rows = [{"device_type": "ap", "model": "AP41", "version": "0.12", "count": 1}]  # WHY: fixture
    fetch_mock = MagicMock(spec=lambda *args, **kwargs: vpm_rows)  # WHY: strict spec on VersionPerModelFetcher.fetch
    fetch_mock.return_value = vpm_rows  # WHY: return the fixture
    render_mock = MagicMock(spec=lambda rows, filename: None)  # WHY: strict spec on PivotRenderer.render
    monkeypatch.setattr(vpm_mod.VersionPerModelFetcher, "fetch", staticmethod(fetch_mock))  # WHY: swap in spy
    monkeypatch.setattr(pivot_mod.PivotRenderer, "render", staticmethod(render_mock))  # WHY: swap in spy
    model_rows = [{"device_type": "ap", "model": "AP41", "count": 2}]  # WHY: sentinel input rows
    result = OrgDeviceInventorySummaryCore._run_pivot_report(  # WHY: run the pivot report
        "org-1", "Acme", model_rows, [], []
    )
    assert result is vpm_rows  # WHY: returned rows are the fetched pivot rows verbatim
    fetch_mock.assert_called_once_with("org-1", model_rows, [], [])  # WHY: propagation confirmed
    render_mock.assert_called_once_with(vpm_rows, "Acme_OrgDeviceVersionPerModel")  # WHY: filename propagated


def test_fetch_switch_page_returns_dict_data() -> None:
    """_search_switch_page returns page dict when the SDK response carries dict-shaped .data."""
    mistapi_module = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    devices=SimpleNamespace(
                        searchOrgDevices=MagicMock(  # WHY: SDK returns SimpleNamespace(data={...})
                            return_value=SimpleNamespace(
                                data={"results": [{"model": "EX2300"}], "next": "https://api/next"}
                            )
                        )
                    )
                )
            )
        ),
        get_all=MagicMock(return_value=[]),
    )
    _reset_dependencies(mistapi_module=mistapi_module)  # WHY: replace default stub
    page = OrgDeviceInventorySummaryCore._search_switch_page("org-1", None)  # WHY: exercise primary-request branch
    assert page == {"results": [{"model": "EX2300"}], "next": "https://api/next"}  # WHY: dict returned verbatim


def test_fetch_switch_page_follows_next_url() -> None:
    """_search_switch_page uses apisession.mist_get when a next URL is supplied."""
    api = SimpleNamespace(  # WHY: session stub records next-URL follows
        mist_get=MagicMock(return_value=SimpleNamespace(data={"results": [{"model": "EX4400"}], "next": None}))
    )
    _reset_dependencies(apisession=api)  # WHY: replace default apisession
    page = OrgDeviceInventorySummaryCore._search_switch_page("org-1", "https://api/next")  # WHY: exercise next branch
    api.mist_get.assert_called_once_with("https://api/next")  # WHY: cursor URL propagated verbatim
    assert page == {"results": [{"model": "EX4400"}], "next": None}  # WHY: dict returned verbatim


def test_fetch_switch_page_returns_none_on_exception() -> None:
    """_search_switch_page returns None when the SDK raises."""
    api = SimpleNamespace(mist_get=MagicMock(side_effect=RuntimeError("network")))  # WHY: force the except branch
    _reset_dependencies(apisession=api)  # WHY: replace default apisession
    assert OrgDeviceInventorySummaryCore._search_switch_page("org-1", "https://api/next") is None  # WHY: sentinel None


def test_fetch_switch_physical_inventory_walks_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    """_fetch_switch_physical_inventory accumulates results across pages until 'next' is missing."""
    _reset_dependencies()  # WHY: hydrate module DI seams (contents replaced by monkeypatch below)
    pages = [
        {"results": [{"model": "EX2300"}], "next": "url-2"},  # WHY: first page + continuation cursor
        {"results": [{"model": "EX4400"}], "next": None},  # WHY: final page (no continuation)
    ]
    iterator = iter(pages)  # WHY: pop one page per call

    def _fake_search(target_org_id, next_url):  # WHY: replaces _search_switch_page for the whole test
        return next(iterator, None)  # WHY: yield each page, then None to break the loop

    monkeypatch.setattr(  # WHY: swap _search_switch_page for the two-page walk
        OrgDeviceInventorySummaryCore, "_search_switch_page", staticmethod(_fake_search)
    )
    records = OrgDeviceInventorySummaryCore._fetch_switch_physical_inventory("org-1")  # WHY: exercise pagination
    assert records == [{"model": "EX2300"}, {"model": "EX4400"}]  # WHY: both pages accumulated


def test_fetch_switch_physical_inventory_stops_on_empty_page(monkeypatch: pytest.MonkeyPatch) -> None:
    """_fetch_switch_physical_inventory exits when a page returns no results."""
    _reset_dependencies()  # WHY: hydrate module DI seams

    def _fake_search(target_org_id, next_url):  # WHY: single empty page ends the walk
        return {"results": [], "next": "should-not-matter"}  # WHY: empty results triggers the break

    monkeypatch.setattr(  # WHY: swap in the empty-page stub
        OrgDeviceInventorySummaryCore, "_search_switch_page", staticmethod(_fake_search)
    )
    assert OrgDeviceInventorySummaryCore._fetch_switch_physical_inventory("org-1") == []  # WHY: nothing accumulated


def test_fetch_gateway_physical_inventory_returns_records() -> None:
    """_fetch_gateway_physical_inventory returns the auto-paginated get_all payload."""
    records = [{"model": "SRX345"}, {"model": "SRX345"}]  # WHY: fixture payload
    mistapi_module = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    inventory=SimpleNamespace(
                        getOrgInventory=MagicMock(return_value=SimpleNamespace(data=[]))  # WHY: get_all pulls real data
                    )
                )
            )
        ),
        get_all=MagicMock(return_value=records),  # WHY: paginator returns records
    )
    _reset_dependencies(mistapi_module=mistapi_module)  # WHY: replace default stub
    assert OrgDeviceInventorySummaryCore._fetch_gateway_physical_inventory("org-1") == records  # WHY: records returned


def test_fetch_gateway_physical_inventory_handles_exception() -> None:
    """_fetch_gateway_physical_inventory returns [] when the SDK raises."""
    mistapi_module = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    inventory=SimpleNamespace(
                        getOrgInventory=MagicMock(side_effect=RuntimeError("kaboom"))  # WHY: forced failure
                    )
                )
            )
        ),
        get_all=MagicMock(return_value=[]),
    )
    _reset_dependencies(mistapi_module=mistapi_module)  # WHY: replace default stub
    assert OrgDeviceInventorySummaryCore._fetch_gateway_physical_inventory("org-1") == []  # WHY: fallback list


def test_fetch_ap_inventory_handles_exception() -> None:
    """_fetch_ap_inventory returns [] when the SDK raises."""
    mistapi_module = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    inventory=SimpleNamespace(
                        getOrgInventory=MagicMock(side_effect=RuntimeError("kaboom"))  # WHY: forced failure
                    )
                )
            )
        ),
        get_all=MagicMock(return_value=[]),
    )
    _reset_dependencies(mistapi_module=mistapi_module)  # WHY: replace default stub
    assert OrgDeviceInventorySummaryCore._fetch_ap_inventory("org-1") == []  # WHY: fallback list


def test_fetch_unassigned_inventory_handles_exception() -> None:
    """_fetch_unassigned_inventory returns [] when the SDK raises."""
    mistapi_module = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    inventory=SimpleNamespace(
                        getOrgInventory=MagicMock(side_effect=RuntimeError("kaboom"))  # WHY: forced failure
                    )
                )
            )
        ),
        get_all=MagicMock(return_value=[]),
    )
    _reset_dependencies(mistapi_module=mistapi_module)  # WHY: replace default stub
    assert OrgDeviceInventorySummaryCore._fetch_unassigned_inventory("org-1") == []  # WHY: fallback list


def test_fetch_switch_type_rows_wraps_exceptions(monkeypatch: pytest.MonkeyPatch) -> None:
    """_fetch_switch_type_rows returns [] when the fetch helper raises."""
    _reset_dependencies()  # WHY: hydrate module DI seams

    def _boom(target_org_id: str) -> list[dict]:  # WHY: force the except branch
        raise RuntimeError("nope")  # WHY: exception path

    monkeypatch.setattr(  # WHY: swap in the raising helper
        OrgDeviceInventorySummaryCore, "_fetch_switch_physical_inventory", staticmethod(_boom)
    )
    assert OrgDeviceInventorySummaryCore._fetch_switch_type_rows("org-1", "model", None) == []  # WHY: [] on failure


def test_fetch_gateway_type_rows_wraps_exceptions(monkeypatch: pytest.MonkeyPatch) -> None:
    """_fetch_gateway_type_rows returns [] when the fetch helper raises."""
    _reset_dependencies()  # WHY: hydrate module DI seams

    def _boom(target_org_id: str) -> list[dict]:  # WHY: force the except branch
        raise RuntimeError("nope")  # WHY: exception path

    monkeypatch.setattr(  # WHY: swap in the raising helper
        OrgDeviceInventorySummaryCore, "_fetch_gateway_physical_inventory", staticmethod(_boom)
    )
    assert OrgDeviceInventorySummaryCore._fetch_gateway_type_rows("org-1", "model", None) == []  # WHY: [] on failure


def test_fetch_ap_type_rows_pulls_shared_records_when_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """_fetch_ap_type_rows fetches AP inventory when ap_records is None, then aggregates."""
    _reset_dependencies()  # WHY: hydrate module DI seams
    fetched: list[str] = []  # WHY: capture target_org_id when the helper is invoked

    def _fake_fetch(target_org_id: str) -> list[dict]:  # WHY: replace the shared AP fetch
        fetched.append(target_org_id)  # WHY: record invocation
        return [{"type": "ap", "model": "AP41", "site_id": "s1", "version": "0.1"}]  # WHY: minimal fixture

    monkeypatch.setattr(  # WHY: swap in the counting stub
        OrgDeviceInventorySummaryCore, "_fetch_ap_inventory", staticmethod(_fake_fetch)
    )
    rows = OrgDeviceInventorySummaryCore._fetch_ap_type_rows("org-1", "model", None)  # WHY: None triggers the fetch
    assert fetched == ["org-1"]  # WHY: shared fetch invoked exactly once
    assert rows == [{"device_type": "ap", "model": "AP41", "count": 1}]  # WHY: aggregation ran once


def test_fetch_ap_type_rows_uses_provided_records(monkeypatch: pytest.MonkeyPatch) -> None:
    """_fetch_ap_type_rows skips the shared fetch when ap_records is provided."""
    _reset_dependencies()  # WHY: hydrate module DI seams
    fetched: list[str] = []  # WHY: capture whether the shared fetch is called

    def _fake_fetch(target_org_id: str) -> list[dict]:  # WHY: should not be invoked when ap_records is provided
        fetched.append(target_org_id)  # WHY: record any call so the test can assert absence
        return []

    monkeypatch.setattr(  # WHY: swap in the counter
        OrgDeviceInventorySummaryCore, "_fetch_ap_inventory", staticmethod(_fake_fetch)
    )
    supplied = [{"type": "ap", "model": "AP41"}]  # WHY: caller-supplied records path
    rows = OrgDeviceInventorySummaryCore._fetch_ap_type_rows(
        "org-1", "model", supplied
    )  # WHY: exercise provided branch
    assert fetched == []  # WHY: shared fetch not invoked
    assert rows == [{"device_type": "ap", "model": "AP41", "count": 1}]  # WHY: aggregation ran on supplied records


def test_fetch_ap_type_rows_wraps_exceptions(monkeypatch: pytest.MonkeyPatch) -> None:
    """_fetch_ap_type_rows returns [] when aggregation raises."""
    _reset_dependencies()  # WHY: hydrate module DI seams

    def _boom(records: list[dict], distinct: str) -> list[dict]:  # WHY: force the except branch
        raise RuntimeError("nope")  # WHY: exception path

    monkeypatch.setattr(  # WHY: swap in the raising aggregator
        OrgDeviceInventorySummaryCore, "_aggregate_ap_counts", staticmethod(_boom)
    )
    assert (
        OrgDeviceInventorySummaryCore._fetch_ap_type_rows("org-1", "model", [{"type": "ap"}]) == []
    )  # WHY: [] on failure


def test_fetch_all_counts_dispatches_and_sorts(monkeypatch: pytest.MonkeyPatch) -> None:
    """_fetch_all_counts routes through _TYPE_HANDLERS then folds in the unassigned counts."""
    _reset_dependencies()  # WHY: hydrate module DI seams

    def _switch(target, distinct, ap):  # WHY: fake handler for the "switch" slot
        return [{"device_type": "switch", "model": "EX", "count": 4}]  # WHY: fixture rows

    def _gateway(target, distinct, ap):  # WHY: fake handler for the "gateway" slot
        return [{"device_type": "gateway", "model": "SRX", "count": 2}]  # WHY: fixture rows

    def _ap(target, distinct, ap):  # WHY: fake handler for the "ap" slot
        return [{"device_type": "ap", "model": "AP41", "count": 6}]  # WHY: fixture rows

    monkeypatch.setitem(OrgDeviceInventorySummaryCore._TYPE_HANDLERS, "switch", _switch)  # WHY: swap switch handler
    monkeypatch.setitem(OrgDeviceInventorySummaryCore._TYPE_HANDLERS, "gateway", _gateway)  # WHY: swap gateway
    monkeypatch.setitem(OrgDeviceInventorySummaryCore._TYPE_HANDLERS, "ap", _ap)  # WHY: swap ap
    rows = OrgDeviceInventorySummaryCore._fetch_all_counts(  # WHY: exercise dispatch
        "org-1", "model", unassigned_records=[], ap_records=[]
    )
    device_types = [row["device_type"] for row in rows]  # WHY: extract the sorted order
    assert device_types == ["ap", "gateway", "switch"]  # WHY: alphabetical primary sort key


def test_with_unassigned_falls_back_on_aggregate_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """_with_unassigned degrades to base rows when unassigned aggregation raises."""
    _reset_dependencies()  # WHY: hydrate module DI seams
    base = [{"device_type": "ap", "model": "AP41", "count": 2}]  # WHY: original assigned rows

    def _boom(records: list[dict], distinct: str) -> list[dict]:  # WHY: force the except branch
        raise RuntimeError("aggregate failure")  # WHY: aggregation must not break the report

    monkeypatch.setattr(  # WHY: swap in the raising aggregator
        OrgDeviceInventorySummaryCore, "_aggregate_unassigned_counts", staticmethod(_boom)
    )
    result = OrgDeviceInventorySummaryCore._with_unassigned(  # WHY: exercise the fallback branch
        base, "org-1", "model", unassigned_records=[{"type": "ap", "model": "AP41"}]
    )
    assert result == base  # WHY: fell back to base rows verbatim


def test_run_for_org_returns_expected_tuple(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """run_for_org runs each report once and returns the tuple in the documented order."""
    _reset_dependencies()  # WHY: hydrate module DI seams

    monkeypatch.setattr(  # WHY: pin org name so the printed summary is deterministic
        OrgDeviceInventorySummaryCore,
        "_resolve_safe_org_name",
        staticmethod(lambda target_org_id: "SafeOrg"),
    )
    monkeypatch.setattr(  # WHY: bypass network for unassigned inventory
        OrgDeviceInventorySummaryCore,
        "_fetch_unassigned_inventory",
        staticmethod(lambda target_org_id: [{"type": "switch", "model": "EX2300"}]),
    )
    monkeypatch.setattr(  # WHY: bypass network for AP inventory
        OrgDeviceInventorySummaryCore,
        "_fetch_ap_inventory",
        staticmethod(lambda target_org_id: [{"type": "ap", "model": "AP41", "site_id": "s1"}]),
    )
    model_rows = [{"device_type": "ap", "model": "AP41", "count": 1}]  # WHY: fixture rows
    version_rows = [{"device_type": "ap", "version": "0.1", "count": 1}]  # WHY: fixture rows
    pivot_rows = [{"device_type": "ap", "model": "AP41", "version": "0.1", "count": 1}]  # WHY: fixture rows
    monkeypatch.setattr(  # WHY: swap model report for direct return
        OrgDeviceInventorySummaryCore,
        "_run_model_report",
        staticmethod(lambda org, safe, un, ap: model_rows),
    )
    monkeypatch.setattr(  # WHY: swap version report for direct return
        OrgDeviceInventorySummaryCore,
        "_run_version_report",
        staticmethod(lambda org, safe, un, ap: version_rows),
    )
    monkeypatch.setattr(  # WHY: swap pivot report for direct return
        OrgDeviceInventorySummaryCore,
        "_run_pivot_report",
        staticmethod(lambda org, safe, mr, un, ap: pivot_rows),
    )
    monkeypatch.setattr(_stdlib_time, "time", lambda: 0.0)  # WHY: pin elapsed to 0 for deterministic output
    result = OrgDeviceInventorySummaryCore.run_for_org("org-1")  # WHY: exercise the entry point
    assert result == (model_rows, version_rows, pivot_rows, "SafeOrg")  # WHY: tuple order documented
    assert "Summary for SafeOrg completed" in capsys.readouterr().out  # WHY: user-visible summary printed
