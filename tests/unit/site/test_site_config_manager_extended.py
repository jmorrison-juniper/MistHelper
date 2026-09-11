"""Extended coverage for SiteConfigManager menus 171-174 destructive workflows."""

from __future__ import annotations  # WHY: enable PEP 604 union syntax across supported runtimes.

from types import SimpleNamespace  # WHY: build lightweight dependency containers per test.
from typing import Any  # WHY: dependencies are duck-typed via Any.
from unittest.mock import MagicMock  # WHY: mock spec'd API surfaces and callables.

import pytest  # WHY: monkeypatch + fixture wiring for isolated per-test state.

from src.site import site_config_manager as module  # WHY: touch module-level _DEPS state directly.
from src.site.site_config_manager import (  # WHY: import public surface + dataclasses.
    RfTemplateReport,
    SiteConfigDependencies,
    SiteConfigManager,
    configure_site_config_manager_dependencies,
)
from src.utils.rate_limiting import AdaptivePacer  # WHY: build an inert pacer for the write-loop helpers.


def _idle_pacer() -> AdaptivePacer:  # WHY: a disabled pacer keeps every unit test free of a real sleep.
    """Return a disabled pacer so a helper under test never waits."""
    return AdaptivePacer(apisession=None, api_usage_cache=None, enabled=False)  # WHY: no sleep, no PID call.


# --- Test fixtures & helpers -----------------------------------------------


def _make_response(*, status_code: int = 200, data: Any = None) -> SimpleNamespace:
    """Return a lightweight object mimicking a mistapi response."""
    return SimpleNamespace(status_code=status_code, data=data)  # WHY: mistapi shape used across helpers.


def _wire(
    *,
    safe_input_value: str = "CREATE",
    stop_signal: bool = False,
    mistapi_ns: SimpleNamespace | None = None,
    exporter_mock: MagicMock | None = None,
    org_id: str | None = "org-1",
    csv_path: str = "test.csv",
) -> SiteConfigDependencies:
    """Wire a fresh dependency graph and return it for further inspection."""
    exporter = exporter_mock or MagicMock()  # WHY: allow assertion on export calls when caller cares.
    deps = SiteConfigDependencies(
        apisession=object(),  # WHY: truthy sentinel simulates authenticated session.
        config_utils=SimpleNamespace(
            get_cached_or_prompted_org_id=MagicMock(return_value=org_id),  # WHY: control org gate.
            check_stop_signal=MagicMock(return_value=stop_signal),  # WHY: cancel path toggle.
        ),
        file_path_utils=SimpleNamespace(
            get_csv_path=MagicMock(return_value=csv_path),  # WHY: point loader at temp path.
        ),
        input_utils=SimpleNamespace(
            safe_input=MagicMock(return_value=safe_input_value),  # WHY: default matches CREATE gate.
        ),
        data_exporter=SimpleNamespace(
            write_with_format_selection=exporter,  # WHY: capture export invocation counts.
        ),
        mistapi=mistapi_ns or SimpleNamespace(),  # WHY: caller-provided SDK shape when needed.
        default_api_page_limit=1000,
    )
    configure_site_config_manager_dependencies(deps)  # WHY: install into module-level holder.
    return deps


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Neutralize time.sleep so tests run without artificial delays."""
    import time as _time  # WHY: reach the real time module without touching module attrs.

    monkeypatch.setattr(_time, "sleep", lambda _s: None)  # WHY: keep create-loop tests fast.


@pytest.fixture(autouse=True)
def _reset_deps() -> None:
    """Ensure each test starts with a clean SiteConfigDependencies holder."""
    module._DEPS = SiteConfigDependencies()  # WHY: prevent cross-test dependency bleed.


# --- Menu 171: create_test_sites_from_csv ----------------------------------


def test_create_test_sites_from_csv_declined() -> None:
    """Missing CREATE keyword aborts before any API work."""
    _wire(safe_input_value="no")  # WHY: any non-CREATE value declines.
    SiteConfigManager.create_test_sites_from_csv()  # WHY: exercise full entry point.
    # No exception + no export calls means the guard worked; nothing to assert further.


def test_create_test_sites_from_csv_missing_org_id(capsys: pytest.CaptureFixture[str]) -> None:
    """Empty org_id resolution prints error and exits early."""
    _wire(org_id="")  # WHY: forces the missing-org branch.
    SiteConfigManager.create_test_sites_from_csv()  # WHY: exercise early return.
    out = capsys.readouterr().out
    assert "No organization ID provided" in out  # WHY: verify operator-visible error message.


def test_load_test_sites_csv_missing_file(tmp_path: Any, capsys: pytest.CaptureFixture[str]) -> None:
    """Loader returns None and prints an error when CSV path does not exist."""
    _wire(csv_path=str(tmp_path / "nope.csv"))  # WHY: guarantee non-existent path.
    assert SiteConfigManager._load_test_sites_csv() is None  # WHY: missing file signals None.
    assert "CSV file not found" in capsys.readouterr().out  # WHY: operator message present.


def test_load_test_sites_csv_success(tmp_path: Any) -> None:
    """Loader parses a well-formed CSV into a list of row dicts."""
    csv_file = tmp_path / "sites.csv"  # WHY: real file makes csv.DictReader path exercised.
    csv_file.write_text("name,country_code\nAlpha,US\nBeta,CA\n", encoding="utf-8")
    _wire(csv_path=str(csv_file))
    rows = SiteConfigManager._load_test_sites_csv()
    assert rows is not None and len(rows) == 2  # WHY: verify count matches CSV.
    assert rows[0]["name"] == "Alpha"  # WHY: verify field parsing.


def test_load_test_sites_csv_oserror(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """OSError during read is caught and reported."""
    csv_file = tmp_path / "broken.csv"  # WHY: real file passes os.path.exists gate.
    csv_file.write_text("name\nAlpha\n", encoding="utf-8")
    _wire(csv_path=str(csv_file))

    def _boom(*_a: Any, **_kw: Any) -> Any:
        raise OSError("permission denied")  # WHY: simulate filesystem failure inside open().

    import builtins  # WHY: patch builtin open globally since module doesn't rebind it.

    monkeypatch.setattr(builtins, "open", _boom)  # WHY: intercept builtin open used by loader.
    assert SiteConfigManager._load_test_sites_csv() is None  # WHY: OSError branch returns None.
    assert "Failed to read CSV file" in capsys.readouterr().out


def test_copy_optional_fields_strips_and_skips_blanks() -> None:
    """Helper copies only non-empty optional values and strips whitespace."""
    payload: dict[str, Any] = {"name": "X"}  # WHY: seed with the mandatory name field.
    SiteConfigManager._copy_optional_fields(
        {"address": "  123 Main  ", "country_code": "", "timezone": "UTC", "notes": None},
        payload,
    )
    assert payload["address"] == "123 Main"  # WHY: stripped copy.
    assert payload["timezone"] == "UTC"  # WHY: kept as-is.
    assert "country_code" not in payload  # WHY: empty string not copied.
    assert "notes" not in payload  # WHY: None not copied.


def test_extract_latlng_returns_none_when_missing_one_coord() -> None:
    """Only one coord present is treated as absent."""
    assert SiteConfigManager._extract_latlng({"lat": "1.0", "lng": ""}) is None
    assert SiteConfigManager._extract_latlng({"lat": "", "lng": "1.0"}) is None


def test_extract_latlng_returns_none_on_parse_error() -> None:
    """Malformed coords are silently swallowed."""
    assert SiteConfigManager._extract_latlng({"lat": "abc", "lng": "1.0"}) is None


def test_extract_latlng_returns_pair_when_valid() -> None:
    """Both coords present and parseable produce a dict pair."""
    pair = SiteConfigManager._extract_latlng({"lat": " 40.7 ", "lng": " -74.0 "})
    assert pair == {"lat": 40.7, "lng": -74.0}


def test_build_site_payload_rejects_missing_name() -> None:
    """Nameless rows return None so caller can log invalid record."""
    assert SiteConfigManager._build_site_payload({"name": ""}) is None


def test_build_site_payload_includes_coords_when_valid() -> None:
    """Coords included in payload when both parse successfully."""
    payload = SiteConfigManager._build_site_payload({"name": "Alpha", "lat": "1.5", "lng": "2.5"})
    assert payload is not None
    assert payload["latlng"] == {"lat": 1.5, "lng": 2.5}


def test_create_single_site_success() -> None:
    """Successful API response returns (created_record, None)."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    sites=SimpleNamespace(createOrgSite=MagicMock(return_value=_make_response(data={"id": "s-1"})))
                )
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    created, failed = SiteConfigManager._create_single_site("org-1", {"name": "X"}, 1, 1)
    assert created is not None and created["id"] == "s-1"  # WHY: extracted id makes it into record.
    assert failed is None  # WHY: success path returns None for failed slot.


def test_create_single_site_empty_response() -> None:
    """Response without .data yields a No data failure tuple."""
    resp = SimpleNamespace(status_code=200)  # WHY: intentionally omit data attribute.
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(orgs=SimpleNamespace(sites=SimpleNamespace(createOrgSite=MagicMock(return_value=resp))))
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    created, failed = SiteConfigManager._create_single_site("org-1", {"name": "Y"}, 1, 1)
    assert created is None
    assert failed is not None and failed["error"] == "No data"


def test_create_single_site_exception_records_failure() -> None:
    """Exceptions from the SDK are converted to failure records."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    sites=SimpleNamespace(createOrgSite=MagicMock(side_effect=RuntimeError("500 err")))
                )
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    created, failed = SiteConfigManager._create_single_site("org-1", {"name": "Z"}, 1, 1)
    assert created is None
    assert failed is not None and "500 err" in failed["error"]


def test_execute_site_creation_mixed_rows() -> None:
    """Invalid rows are recorded as failures; valid rows go through the API."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    sites=SimpleNamespace(createOrgSite=MagicMock(return_value=_make_response(data={"id": "s-1"})))
                )
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    created, failed = SiteConfigManager._execute_site_creation("org-1", [{"name": ""}, {"name": "Alpha"}])
    assert len(created) == 1
    assert len(failed) == 1 and failed[0]["error"] == "No site name"


def test_report_site_creation_results_exports_both_when_present() -> None:
    """Reporter exports both successful and failed lists when non-empty."""
    exporter = MagicMock()
    _wire(exporter_mock=exporter)
    SiteConfigManager._report_site_creation_results(
        sites_data=[{"name": "A"}, {"name": "B"}],
        created=[{"name": "A"}],
        failed=[{"name": "B", "error": "x"}],
    )
    assert exporter.call_count == 2  # WHY: one call each for created + failed.


def test_report_site_creation_results_skips_export_when_empty() -> None:
    """Reporter does not export empty lists."""
    exporter = MagicMock()
    _wire(exporter_mock=exporter)
    SiteConfigManager._report_site_creation_results(sites_data=[], created=[], failed=[])
    exporter.assert_not_called()


# --- Menu 172: RF templates ------------------------------------------------


def test_create_country_rf_templates_missing_apisession(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing api session aborts before any work."""
    deps = _wire()
    deps.apisession = None  # WHY: explicitly clear session to hit unwired guard.
    SiteConfigManager.create_country_rf_templates_and_assign()
    assert "Mist API session not initialized" in capsys.readouterr().out


def test_create_country_rf_templates_missing_org_id() -> None:
    """Missing org id returns silently after the session check."""
    _wire(org_id="")  # WHY: empty org triggers early return.
    SiteConfigManager.create_country_rf_templates_and_assign()  # WHY: must not raise.


def test_fetch_org_sites_for_rf_error(capsys: pytest.CaptureFixture[str]) -> None:
    """API error path returns None and prints an error message."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(sites=SimpleNamespace(listOrgSites=MagicMock(side_effect=RuntimeError("boom"))))
            )
        ),
        get_all=MagicMock(return_value=[]),
    )
    _wire(mistapi_ns=mistapi_ns)
    assert SiteConfigManager._fetch_org_sites_for_rf("org-1") is None
    assert "Failed to fetch sites" in capsys.readouterr().out


def test_fetch_org_sites_for_rf_empty(capsys: pytest.CaptureFixture[str]) -> None:
    """Empty site list returns None with legacy message."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(orgs=SimpleNamespace(sites=SimpleNamespace(listOrgSites=MagicMock(return_value=None))))
        ),
        get_all=MagicMock(return_value=[]),
    )
    _wire(mistapi_ns=mistapi_ns)
    assert SiteConfigManager._fetch_org_sites_for_rf("org-1") is None
    assert "No sites found" in capsys.readouterr().out


def test_fetch_org_sites_for_rf_success() -> None:
    """Populated list is returned unchanged."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(orgs=SimpleNamespace(sites=SimpleNamespace(listOrgSites=MagicMock(return_value=None))))
        ),
        get_all=MagicMock(return_value=[{"id": "s-1", "name": "Alpha"}]),
    )
    _wire(mistapi_ns=mistapi_ns)
    sites = SiteConfigManager._fetch_org_sites_for_rf("org-1")
    assert sites is not None and sites[0]["name"] == "Alpha"


def test_group_sites_by_country_partitions_missing_country() -> None:
    """Sites without country_code go into the second bucket."""
    sites = [
        {"id": "s1", "name": "A", "country_code": "US"},
        {"id": "s2", "name": "B", "country_code": ""},
        {"id": "s3", "name": "C", "country_code": "us"},
    ]
    by_country, without = SiteConfigManager._group_sites_by_country(sites)
    assert set(by_country.keys()) == {"US"}  # WHY: normalized to uppercase.
    assert len(by_country["US"]) == 2
    assert len(without) == 1 and without[0]["id"] == "s2"


def test_fetch_existing_rf_templates_success_and_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Success returns {name: id}; error returns None."""
    ok_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(rftemplates=SimpleNamespace(listOrgRfTemplates=MagicMock(return_value=None)))
            )
        ),
        get_all=MagicMock(return_value=[{"name": "RF-US", "id": "t-1"}]),
    )
    _wire(mistapi_ns=ok_ns)
    assert SiteConfigManager._fetch_existing_rf_templates("org-1") == {"RF-US": "t-1"}
    _ = capsys.readouterr()  # WHY: discard captured output before next call.

    err_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    rftemplates=SimpleNamespace(listOrgRfTemplates=MagicMock(side_effect=OSError("net")))
                )
            )
        ),
        get_all=MagicMock(return_value=[]),
    )
    _wire(mistapi_ns=err_ns)
    assert SiteConfigManager._fetch_existing_rf_templates("org-1") is None


def test_analyze_sites_for_rf_templates_no_country() -> None:
    """Sites with no country codes cause early None return."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    sites=SimpleNamespace(listOrgSites=MagicMock(return_value=None)),
                    rftemplates=SimpleNamespace(listOrgRfTemplates=MagicMock(return_value=None)),
                )
            )
        ),
        get_all=MagicMock(
            side_effect=[[{"id": "s1", "name": "X", "country_code": ""}], []]
        ),  # WHY: sites list then rf list.
    )
    _wire(mistapi_ns=mistapi_ns)
    assert SiteConfigManager._analyze_sites_for_rf_templates("org-1") is None


def test_analyze_sites_for_rf_templates_full() -> None:
    """Happy path returns (sites_by_country, without_country, existing_templates)."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    sites=SimpleNamespace(listOrgSites=MagicMock(return_value=None)),
                    rftemplates=SimpleNamespace(listOrgRfTemplates=MagicMock(return_value=None)),
                )
            )
        ),
        get_all=MagicMock(
            side_effect=[
                [{"id": "s1", "name": "A", "country_code": "US"}],
                [{"name": "RF-US", "id": "t-1"}],
            ]
        ),
    )
    _wire(mistapi_ns=mistapi_ns)
    result = SiteConfigManager._analyze_sites_for_rf_templates("org-1")
    assert result is not None
    by_country, without, existing = result
    assert "US" in by_country and existing == {"RF-US": "t-1"}
    assert without == []


def test_split_templates_by_existence_partitions_correctly() -> None:
    """Templates split into create vs update based on existence."""
    to_create, to_update = SiteConfigManager._split_templates_by_existence(
        {"US": [{"id": "s1", "name": "A"}], "CA": [{"id": "s2", "name": "B"}]},
        {"RF-US": "t-1"},
    )
    names_create = [entry["country"] for entry in to_create]
    names_update = [entry["country"] for entry in to_update]
    assert names_create == ["CA"]
    assert names_update == ["US"]


def test_prompt_update_mode_choices(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prompt returns 'skip' for '1', 'update' for '2', reprompts on invalid."""
    responses = iter(["", "junk", "1"])  # WHY: exercise invalid loop before choosing 1.
    _wire()
    module._DEPS.input_utils = SimpleNamespace(safe_input=MagicMock(side_effect=lambda *_a, **_k: next(responses)))
    assert SiteConfigManager._prompt_update_mode([{"name": "RF-US"}]) == "skip"

    module._DEPS.input_utils = SimpleNamespace(safe_input=MagicMock(return_value="2"))
    assert SiteConfigManager._prompt_update_mode([{"name": "RF-US"}]) == "update"


def test_plan_rf_template_operations_no_update_skips_prompt() -> None:
    """Zero existing templates produces skip mode without prompting."""
    _wire()
    result = SiteConfigManager._plan_rf_template_operations({"US": [{"id": "s1", "name": "A"}]}, {})
    assert result is not None  # WHY: narrow Optional[tuple] for mypy strict.
    to_create, to_update, mode = result
    assert to_update == [] and mode == "skip"
    assert to_create and to_create[0]["country"] == "US"


def test_confirm_rf_template_operation_accepts_create_only() -> None:
    """Only CREATE keyword returns True."""
    _wire(safe_input_value="CREATE")
    assert (
        SiteConfigManager._confirm_rf_template_operation(
            [{"country": "US"}], [{"country": "CA"}], {"US": [{}], "CA": [{}]}, "update"
        )
        is True
    )

    _wire(safe_input_value="nope")
    assert SiteConfigManager._confirm_rf_template_operation([], [], {}, "skip") is False


def test_build_rf_template_payload_shape() -> None:
    """Payload contains expected bands and country code."""
    payload = SiteConfigManager._build_rf_template_payload("US", "RF-US")
    assert payload["country_code"] == "US"
    assert payload["band_24"]["bandwidth"] == 20
    assert payload["band_24_usage"] == "auto"


def test_update_one_rf_template_success_populates_mapping() -> None:
    """A 200 response records mapping entry."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    rftemplates=SimpleNamespace(updateOrgRfTemplate=MagicMock(return_value=_make_response()))
                )
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    mapping: dict[str, dict[str, str]] = {}
    SiteConfigManager._update_one_rf_template(
        "org-1", {"country": "US", "id": "t-1", "name": "RF-US"}, mapping, _idle_pacer()
    )
    assert mapping["US"] == {"id": "t-1", "name": "RF-US"}


def test_update_one_rf_template_exception_skips_mapping() -> None:
    """Exception on update leaves mapping unchanged."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    rftemplates=SimpleNamespace(updateOrgRfTemplate=MagicMock(side_effect=ValueError("bad")))
                )
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    mapping: dict[str, dict[str, str]] = {}
    SiteConfigManager._update_one_rf_template(
        "org-1", {"country": "US", "id": "t-1", "name": "RF-US"}, mapping, _idle_pacer()
    )
    assert mapping == {}


def test_create_one_rf_template_success() -> None:
    """200 response records new id in mapping."""
    resp = _make_response(data={"id": "new-1"})
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(rftemplates=SimpleNamespace(createOrgRfTemplate=MagicMock(return_value=resp)))
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    mapping: dict[str, dict[str, str]] = {}
    SiteConfigManager._create_one_rf_template("org-1", {"country": "CA", "name": "RF-CA"}, mapping, _idle_pacer())
    assert mapping["CA"]["id"] == "new-1"


def test_apply_existing_templates_mapping_populates_map() -> None:
    """Skip-mode helper reuses ids without hitting the API."""
    mapping: dict[str, dict[str, str]] = {}
    SiteConfigManager._apply_existing_templates_mapping([{"country": "US", "id": "t-1", "name": "RF-US"}], mapping)
    assert mapping == {"US": {"id": "t-1", "name": "RF-US"}}


def test_execute_rf_template_operations_update_mode() -> None:
    """Update mode calls update endpoint for existing, create for new."""
    update_mock = MagicMock(return_value=_make_response())
    create_mock = MagicMock(return_value=_make_response(data={"id": "new-1"}))
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    rftemplates=SimpleNamespace(
                        updateOrgRfTemplate=update_mock,
                        createOrgRfTemplate=create_mock,
                    )
                )
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    mapping = SiteConfigManager._execute_rf_template_operations(
        "org-1",
        [{"country": "CA", "name": "RF-CA"}],
        [{"country": "US", "id": "t-1", "name": "RF-US"}],
        "update",
    )
    assert "US" in mapping and "CA" in mapping
    update_mock.assert_called_once()
    create_mock.assert_called_once()


def test_execute_rf_template_operations_skip_mode() -> None:
    """Skip mode does not call updateOrgRfTemplate."""
    update_mock = MagicMock()  # WHY: must not be invoked.
    create_mock = MagicMock(return_value=_make_response(data={"id": "new-1"}))
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    rftemplates=SimpleNamespace(
                        updateOrgRfTemplate=update_mock,
                        createOrgRfTemplate=create_mock,
                    )
                )
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    mapping = SiteConfigManager._execute_rf_template_operations(
        "org-1",
        [{"country": "CA", "name": "RF-CA"}],
        [{"country": "US", "id": "t-1", "name": "RF-US"}],
        "skip",
    )
    update_mock.assert_not_called()
    assert mapping["US"] == {"id": "t-1", "name": "RF-US"}


def test_assign_one_site_to_template_success() -> None:
    """200 records success entry with template name/country."""
    resp = _make_response()
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                sites=SimpleNamespace(sites=SimpleNamespace(updateSiteInfo=MagicMock(return_value=resp)))
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    success: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    SiteConfigManager._assign_one_site_to_template(
        {"id": "s1", "name": "Alpha"},
        {"id": "t-1", "name": "RF-US", "country": "US"},
        (success, failed),
        _idle_pacer(),
    )
    assert success[0]["country"] == "US"
    assert failed == []


def test_assign_one_site_to_template_http_failure() -> None:
    """Non-200 status appended to failed bucket."""
    resp = _make_response(status_code=500)
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                sites=SimpleNamespace(sites=SimpleNamespace(updateSiteInfo=MagicMock(return_value=resp)))
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    success: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    SiteConfigManager._assign_one_site_to_template(
        {"id": "s1", "name": "Alpha"},
        {"id": "t-1", "name": "RF-US", "country": "US"},
        (success, failed),
        _idle_pacer(),
    )
    assert failed[0]["error"] == "HTTP 500"


def test_assign_one_site_to_template_exception() -> None:
    """Exception yields str(error) failure entry."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                sites=SimpleNamespace(sites=SimpleNamespace(updateSiteInfo=MagicMock(side_effect=RuntimeError("nope"))))
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    success: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    SiteConfigManager._assign_one_site_to_template(
        {"id": "s1", "name": "Alpha"},
        {"id": "t-1", "name": "RF-US", "country": "US"},
        (success, failed),
        _idle_pacer(),
    )
    assert "nope" in failed[0]["error"]


def test_assign_sites_to_rf_templates_stop_signal_early_exit() -> None:
    """A truthy stop_signal returns before making assignments."""
    call_counter = {"count": 0}

    def _upd(*_a: Any, **_kw: Any) -> Any:
        call_counter["count"] += 1  # WHY: any API call bumps counter.
        return _make_response()

    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(sites=SimpleNamespace(sites=SimpleNamespace(updateSiteInfo=MagicMock(side_effect=_upd))))
        )
    )
    _wire(mistapi_ns=mistapi_ns, stop_signal=True)  # WHY: force early exit branch.
    success, failed = SiteConfigManager._assign_sites_to_rf_templates(
        {"US": [{"id": "s1", "name": "Alpha"}]},
        {"US": {"id": "t-1", "name": "RF-US"}},
    )
    assert (success, failed) == ([], [])
    assert call_counter["count"] == 0  # WHY: verify no API calls when stop signalled.


def test_assign_sites_to_rf_templates_missing_country_skipped() -> None:
    """Countries missing from template_mapping are skipped."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                sites=SimpleNamespace(sites=SimpleNamespace(updateSiteInfo=MagicMock(return_value=_make_response())))
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    success, failed = SiteConfigManager._assign_sites_to_rf_templates(
        {"US": [{"id": "s1", "name": "Alpha"}], "CA": [{"id": "s2", "name": "Beta"}]},
        {"US": {"id": "t-1", "name": "RF-US"}},  # WHY: only US mapped; CA skipped.
    )
    assert len(success) == 1  # WHY: only US assignment attempted.
    assert failed == []


def test_report_rf_template_results_exports_present_lists() -> None:
    """Reporter exports success and failed lists when populated."""
    exporter = MagicMock()
    _wire(exporter_mock=exporter)
    report = RfTemplateReport(
        created=[{"country": "US"}],
        updated=[],
        update_mode="update",
        success=[{"site_name": "A"}],
        failed=[{"site_name": "B"}],
        skipped=[],
    )
    SiteConfigManager._report_rf_template_results(report)
    assert exporter.call_count == 2  # WHY: one call each for success + failed.


def test_audit_rf_template_completion_logs(caplog: pytest.LogCaptureFixture) -> None:
    """Audit helper logs at WARNING level with tallies."""
    caplog.set_level("WARNING", logger="root")
    SiteConfigManager._audit_rf_template_completion([{"country": "US"}], [{"site_name": "A"}], [])
    assert any("Menu #172 complete" in msg for msg in caplog.messages)


def test_run_rf_template_workflow_returns_early_when_analysis_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Workflow bails when analyze returns None."""
    _wire()
    monkeypatch.setattr(SiteConfigManager, "_analyze_sites_for_rf_templates", staticmethod(lambda _o: None))
    SiteConfigManager._run_rf_template_workflow("org-1")  # WHY: must not raise.


def test_run_rf_template_workflow_returns_when_plan_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Workflow bails when plan step returns None."""
    _wire()
    monkeypatch.setattr(
        SiteConfigManager,
        "_analyze_sites_for_rf_templates",
        staticmethod(lambda _o: ({"US": [{"id": "s1", "name": "A"}]}, [], {})),
    )
    monkeypatch.setattr(
        SiteConfigManager,
        "_plan_rf_template_operations",
        staticmethod(lambda *_a, **_k: None),
    )
    SiteConfigManager._run_rf_template_workflow("org-1")  # WHY: must not raise.


def test_run_rf_template_workflow_bails_when_unconfirmed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Workflow does not execute writes when user declines final gate."""
    _wire()
    monkeypatch.setattr(
        SiteConfigManager,
        "_analyze_sites_for_rf_templates",
        staticmethod(lambda _o: ({"US": [{"id": "s1", "name": "A"}]}, [], {})),
    )
    monkeypatch.setattr(
        SiteConfigManager,
        "_plan_rf_template_operations",
        staticmethod(lambda *_a, **_k: ([{"country": "US"}], [], "skip")),
    )
    monkeypatch.setattr(
        SiteConfigManager,
        "_confirm_rf_template_operation",
        staticmethod(lambda *_a, **_k: False),
    )
    exec_spy = MagicMock()
    monkeypatch.setattr(SiteConfigManager, "_run_rf_template_execution", exec_spy)
    SiteConfigManager._run_rf_template_workflow("org-1")
    exec_spy.assert_not_called()


# --- Menu 173: create_ap_model_device_profiles -----------------------------


def test_fetch_org_ap_inventory_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Inventory error path returns None."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(inventory=SimpleNamespace(getOrgInventory=MagicMock(side_effect=OSError("net"))))
            )
        ),
        get_all=MagicMock(return_value=[]),
    )
    _wire(mistapi_ns=mistapi_ns)
    assert SiteConfigManager._fetch_org_ap_inventory("org-1") is None
    assert "Failed to fetch inventory" in capsys.readouterr().out


def test_fetch_org_ap_inventory_empty(capsys: pytest.CaptureFixture[str]) -> None:
    """Empty inventory returns None with legacy message."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(inventory=SimpleNamespace(getOrgInventory=MagicMock(return_value=None)))
            )
        ),
        get_all=MagicMock(return_value=[]),
    )
    _wire(mistapi_ns=mistapi_ns)
    assert SiteConfigManager._fetch_org_ap_inventory("org-1") is None
    assert "No AP devices found" in capsys.readouterr().out


def test_fetch_org_ap_inventory_success() -> None:
    """Successful inventory is returned as-is."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(inventory=SimpleNamespace(getOrgInventory=MagicMock(return_value=None)))
            )
        ),
        get_all=MagicMock(return_value=[{"mac": "a", "model": "AP32"}]),
    )
    _wire(mistapi_ns=mistapi_ns)
    result = SiteConfigManager._fetch_org_ap_inventory("org-1")
    assert result is not None and result[0]["model"] == "AP32"


def test_tally_ap_models_bins_correctly() -> None:
    """Devices without model captured in second bucket by name/mac fallback."""
    models, missing = SiteConfigManager._tally_ap_models(
        [
            {"mac": "a", "model": "AP32"},
            {"mac": "b", "model": "AP43"},
            {"mac": "c"},
            {"name": "silent", "mac": "d"},
        ]
    )
    assert models == {"AP32", "AP43"}
    assert set(missing) == {"c", "silent"}  # WHY: verify both fallback paths.


def test_analyze_ap_models_full(capsys: pytest.CaptureFixture[str]) -> None:
    """Analyzer orchestrates fetch + tally and prints summary."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(inventory=SimpleNamespace(getOrgInventory=MagicMock(return_value=None)))
            )
        ),
        get_all=MagicMock(return_value=[{"mac": "a", "model": "AP32"}]),
    )
    _wire(mistapi_ns=mistapi_ns)
    models, missing = SiteConfigManager._analyze_ap_models("org-1")
    assert models == {"AP32"} and missing == []
    assert "Found 1 unique AP models" in capsys.readouterr().out


def test_analyze_ap_models_empty_inventory() -> None:
    """Empty inventory returns empty pair without raising."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(inventory=SimpleNamespace(getOrgInventory=MagicMock(return_value=None)))
            )
        ),
        get_all=MagicMock(return_value=[]),
    )
    _wire(mistapi_ns=mistapi_ns)
    models, missing = SiteConfigManager._analyze_ap_models("org-1")
    assert models == set() and missing == []


def test_get_existing_device_profiles_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Error branch returns None."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    deviceprofiles=SimpleNamespace(listOrgDeviceProfiles=MagicMock(side_effect=KeyError("k")))
                )
            )
        ),
        get_all=MagicMock(return_value=[]),
    )
    _wire(mistapi_ns=mistapi_ns)
    assert SiteConfigManager._get_existing_device_profiles("org-1") is None
    assert "Failed to fetch device profiles" in capsys.readouterr().out


def test_plan_profile_creation_mixed() -> None:
    """Planner categorizes model set against existing profile map."""
    to_create, to_skip = SiteConfigManager._plan_profile_creation({"AP32", "AP43"}, {"AP-AP32": "id-32"})
    creates = {entry["model"] for entry in to_create}
    skips = {entry["model"] for entry in to_skip}
    assert creates == {"AP43"} and skips == {"AP32"}


def test_confirm_profile_creation_gate() -> None:
    """CREATE returns True, otherwise False."""
    _wire(safe_input_value="CREATE")
    assert SiteConfigManager._confirm_profile_creation([{"name": "AP-AP32"}], []) is True
    _wire(safe_input_value="no")
    assert SiteConfigManager._confirm_profile_creation([{"name": "AP-AP32"}], []) is False


def test_record_profile_create_response_success() -> None:
    """200 status appends to created bucket."""
    created: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    SiteConfigManager._record_profile_create_response(
        _make_response(data={"id": "p-1"}),
        {"model": "AP32", "name": "AP-AP32"},
        created,
        failed,
    )
    assert created[0]["id"] == "p-1"
    assert failed == []


def test_record_profile_create_response_failure() -> None:
    """Non-200 goes to failed."""
    created: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    SiteConfigManager._record_profile_create_response(
        _make_response(status_code=500),
        {"model": "AP32", "name": "AP-AP32"},
        created,
        failed,
    )
    assert failed[0]["error"] == "HTTP 500"


def test_create_one_device_profile_exception_path() -> None:
    """Exception path adds record to failed bucket."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    deviceprofiles=SimpleNamespace(createOrgDeviceProfile=MagicMock(side_effect=RuntimeError("boom")))
                )
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    created: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    SiteConfigManager._create_one_device_profile(
        "org-1", {"model": "AP32", "name": "AP-AP32"}, created, failed, _idle_pacer()
    )
    assert failed[0]["model"] == "AP32"


def test_execute_profile_creation_orchestration() -> None:
    """Orchestrator runs per-item helper for each profile."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    deviceprofiles=SimpleNamespace(
                        createOrgDeviceProfile=MagicMock(return_value=_make_response(data={"id": "p-1"}))
                    )
                )
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    created, failed = SiteConfigManager._execute_profile_creation("org-1", [{"model": "AP32", "name": "AP-AP32"}])
    assert len(created) == 1 and failed == []


def test_report_profile_creation_results_exports() -> None:
    """Reporter exports both created and failed when non-empty."""
    exporter = MagicMock()
    _wire(exporter_mock=exporter)
    SiteConfigManager._report_profile_creation_results(
        [{"model": "AP32", "name": "AP-AP32"}],
        [{"model": "AP43", "name": "AP-AP43", "error": "x"}],
        [{"model": "AP44"}],
    )
    assert exporter.call_count == 2  # WHY: created + failed each exported.


# --- Menu 174: assign_aps_to_matching_device_profiles ----------------------


def test_build_profile_map_filters_missing_fields() -> None:
    """Rows missing name or id are dropped from the map."""
    result = SiteConfigManager._build_profile_map(
        [
            {"name": "A", "id": "1"},
            {"name": "", "id": "2"},
            {"name": "C"},
            {"id": "4"},
        ]
    )
    assert result == {"A": "1"}


def test_fetch_profile_map_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Error branch returns None and prints error."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    deviceprofiles=SimpleNamespace(listOrgDeviceProfiles=MagicMock(side_effect=ValueError("bad")))
                )
            )
        ),
        get_all=MagicMock(return_value=[]),
    )
    _wire(mistapi_ns=mistapi_ns)
    assert SiteConfigManager._fetch_profile_map("org-1") is None
    assert "Failed to fetch Device Profiles" in capsys.readouterr().out


def test_fetch_profile_map_empty(capsys: pytest.CaptureFixture[str]) -> None:
    """Empty map returns None with legacy message."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(deviceprofiles=SimpleNamespace(listOrgDeviceProfiles=MagicMock(return_value=None)))
            )
        ),
        get_all=MagicMock(return_value=[]),
    )
    _wire(mistapi_ns=mistapi_ns)
    assert SiteConfigManager._fetch_profile_map("org-1") is None
    assert "No Device Profiles" in capsys.readouterr().out


def test_fetch_ap_inventory_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Error branch on inventory fetch returns None."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(inventory=SimpleNamespace(getOrgInventory=MagicMock(side_effect=OSError("net"))))
            )
        ),
        get_all=MagicMock(return_value=[]),
    )
    _wire(mistapi_ns=mistapi_ns)
    assert SiteConfigManager._fetch_ap_inventory("org-1") is None
    assert "Failed to fetch AP inventory" in capsys.readouterr().out


def test_fetch_ap_inventory_empty(capsys: pytest.CaptureFixture[str]) -> None:
    """Empty inventory returns None."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(inventory=SimpleNamespace(getOrgInventory=MagicMock(return_value=None)))
            )
        ),
        get_all=MagicMock(return_value=[]),
    )
    _wire(mistapi_ns=mistapi_ns)
    assert SiteConfigManager._fetch_ap_inventory("org-1") is None
    assert "No APs found" in capsys.readouterr().out


def test_classify_one_ap_all_branches() -> None:
    """Classifier picks matched/unmatched/no_model based on model presence."""
    matched_key, matched_rec = SiteConfigManager._classify_one_ap(
        {"mac": "aa", "name": "n", "model": "AP32"}, {"AP-AP32": "p-1"}
    )
    assert matched_key == "matched" and matched_rec["profile_id"] == "p-1"

    unmatched_key, unmatched_rec = SiteConfigManager._classify_one_ap(
        {"mac": "bb", "model": "AP99"}, {"AP-AP32": "p-1"}
    )
    assert unmatched_key == "unmatched" and unmatched_rec["expected_profile"] == "AP-AP99"

    no_model_key, no_model_rec = SiteConfigManager._classify_one_ap({"mac": "cc"}, {"AP-AP32": "p-1"})
    assert no_model_key == "no_model" and no_model_rec["mac"] == "cc"


def test_record_ap_assign_response_success_and_failure() -> None:
    """Response branches route to success vs failed buckets."""
    success: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    SiteConfigManager._record_ap_assign_response(
        _make_response(),
        {
            "mac": "aa",
            "name": "n",
            "model": "AP32",
            "profile_name": "AP-AP32",
            "profile_id": "p-1",
        },
        success,
        failed,
    )
    assert success and success[0]["mac"] == "aa"

    SiteConfigManager._record_ap_assign_response(
        _make_response(status_code=418),
        {
            "mac": "bb",
            "name": "n2",
            "model": "AP43",
            "profile_name": "AP-AP43",
            "profile_id": "p-2",
        },
        success,
        failed,
    )
    assert failed and failed[0]["error"] == "HTTP 418"


def test_assign_one_ap_to_profile_exception() -> None:
    """SDK exception recorded on failed bucket."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    deviceprofiles=SimpleNamespace(assignOrgDeviceProfile=MagicMock(side_effect=RuntimeError("no")))
                )
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    success: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    SiteConfigManager._assign_one_ap_to_profile(
        "org-1",
        {
            "mac": "aa",
            "name": "n",
            "model": "AP32",
            "profile_name": "AP-AP32",
            "profile_id": "p-1",
        },
        success,
        failed,
        _idle_pacer(),
    )
    assert failed[0]["mac"] == "aa"


def test_execute_profile_assignment_orchestration() -> None:
    """Orchestrator invokes per-AP helper and aggregates buckets."""
    mistapi_ns = SimpleNamespace(
        api=SimpleNamespace(
            v1=SimpleNamespace(
                orgs=SimpleNamespace(
                    deviceprofiles=SimpleNamespace(assignOrgDeviceProfile=MagicMock(return_value=_make_response()))
                )
            )
        )
    )
    _wire(mistapi_ns=mistapi_ns)
    success, failed = SiteConfigManager._execute_profile_assignment(
        "org-1",
        [
            {
                "mac": "aa",
                "name": "n",
                "model": "AP32",
                "profile_name": "AP-AP32",
                "profile_id": "p-1",
            }
        ],
    )
    assert len(success) == 1 and failed == []


def test_report_profile_assignment_results_exports_when_present() -> None:
    """Reporter exports every non-empty bucket."""
    exporter = MagicMock()
    _wire(exporter_mock=exporter)
    SiteConfigManager._report_profile_assignment_results(
        [{"mac": "aa"}],
        [{"mac": "bb", "error": "x"}],
        [{"mac": "cc"}],
        [{"mac": "dd"}],
    )
    assert exporter.call_count == 3  # WHY: success + failed + without_profile exported.


def test_run_profile_assignment_workflow_no_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty inventory returns early."""
    _wire()
    monkeypatch.setattr(SiteConfigManager, "_fetch_ap_inventory", staticmethod(lambda _o: None))
    SiteConfigManager._run_profile_assignment_workflow("org-1")  # WHY: must not raise.


def test_run_profile_assignment_workflow_no_profile_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing profile map returns early after inventory fetch."""
    _wire()
    monkeypatch.setattr(
        SiteConfigManager,
        "_fetch_ap_inventory",
        staticmethod(lambda _o: [{"mac": "aa", "model": "AP32"}]),
    )
    monkeypatch.setattr(SiteConfigManager, "_fetch_profile_map", staticmethod(lambda _o: None))
    SiteConfigManager._run_profile_assignment_workflow("org-1")  # WHY: must not raise.


def test_run_profile_assignment_workflow_no_matched(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """No matched APs prints legacy message and bails."""
    _wire()
    monkeypatch.setattr(
        SiteConfigManager,
        "_fetch_ap_inventory",
        staticmethod(lambda _o: [{"mac": "aa"}]),
    )
    monkeypatch.setattr(
        SiteConfigManager,
        "_fetch_profile_map",
        staticmethod(lambda _o: {"AP-AP32": "p-1"}),
    )
    monkeypatch.setattr(
        SiteConfigManager,
        "_analyze_ap_profile_matching",
        staticmethod(lambda *_a, **_k: ([], [], [])),
    )
    SiteConfigManager._run_profile_assignment_workflow("org-1")
    assert "No APs have matching" in capsys.readouterr().out


def test_run_profile_assignment_workflow_declined(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Confirmation decline prevents execution."""
    _wire()
    monkeypatch.setattr(
        SiteConfigManager,
        "_fetch_ap_inventory",
        staticmethod(lambda _o: [{"mac": "aa", "model": "AP32"}]),
    )
    monkeypatch.setattr(
        SiteConfigManager,
        "_fetch_profile_map",
        staticmethod(lambda _o: {"AP-AP32": "p-1"}),
    )
    monkeypatch.setattr(
        SiteConfigManager,
        "_analyze_ap_profile_matching",
        staticmethod(lambda *_a, **_k: ([{"mac": "aa"}], [], [])),
    )
    monkeypatch.setattr(
        SiteConfigManager,
        "_confirm_profile_assignment",
        staticmethod(lambda *_a, **_k: False),
    )
    exec_spy = MagicMock()
    monkeypatch.setattr(SiteConfigManager, "_execute_profile_assignment", exec_spy)
    SiteConfigManager._run_profile_assignment_workflow("org-1")
    exec_spy.assert_not_called()


# --- Menu 173 top-level entry ----------------------------------------------


def test_create_ap_model_device_profiles_no_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty ap_models returns before existing-profile fetch."""
    _wire()
    monkeypatch.setattr(
        SiteConfigManager,
        "_analyze_ap_models",
        staticmethod(lambda _o: (set(), [])),
    )
    fetch_spy = MagicMock()
    monkeypatch.setattr(SiteConfigManager, "_get_existing_device_profiles", fetch_spy)
    SiteConfigManager.create_ap_model_device_profiles()
    fetch_spy.assert_not_called()


def test_create_ap_model_device_profiles_all_exist(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """All models already have profiles prints message and returns."""
    _wire()
    monkeypatch.setattr(
        SiteConfigManager,
        "_analyze_ap_models",
        staticmethod(lambda _o: ({"AP32"}, [])),
    )
    monkeypatch.setattr(
        SiteConfigManager,
        "_get_existing_device_profiles",
        staticmethod(lambda _o: {"AP-AP32": "p-1"}),
    )
    SiteConfigManager.create_ap_model_device_profiles()
    assert "already exist" in capsys.readouterr().out


def test_create_ap_model_device_profiles_declined(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Declined confirmation stops before execution."""
    _wire()
    monkeypatch.setattr(
        SiteConfigManager,
        "_analyze_ap_models",
        staticmethod(lambda _o: ({"AP99"}, [])),
    )
    monkeypatch.setattr(
        SiteConfigManager,
        "_get_existing_device_profiles",
        staticmethod(lambda _o: {}),
    )
    monkeypatch.setattr(
        SiteConfigManager,
        "_confirm_profile_creation",
        staticmethod(lambda *_a, **_k: False),
    )
    exec_spy = MagicMock()
    monkeypatch.setattr(SiteConfigManager, "_execute_profile_creation", exec_spy)
    SiteConfigManager.create_ap_model_device_profiles()
    exec_spy.assert_not_called()
