"""Tests for the stage two endpoint family exporter."""

from __future__ import annotations

import importlib
import inspect
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

from src.foundation.support.refactors.endpoint_primary_key_strategies import ENDPOINT_PRIMARY_KEY_STRATEGIES
from src.operations.exporting.export.endpoint_family_exporter import (
    _MSP_DETAIL_OPS,
    _ORG_DETAIL_OPS,
    _OTHER_DETAIL_OPS,
    _SITE_DETAIL_OPS,
    _SITE_MAP_OPS,
    _SITE_SLE_OPS,
    ALL_STAGE_TWO_ENDPOINT_OPS,
    EndpointFamilyExporter,
    _EndpointFamilyOp,
)
from src.operations.exporting.export.endpoint_family_exporter import (
    _ORG_DETAIL_OPS as FAILURE_MODE_ORG_DETAIL_OPS,
)
from src.operations.exporting.export.endpoint_family_exporter import (
    EndpointFamilyExporter as FailureModeEndpointFamilyExporter,
)

EXPECTED_BUCKET_COUNTS = {
    "SITE_SLE": 15,
    "SITE_MAP": 7,
    "SITE_DETAIL": 33,
    "ORG_DETAIL": 61,
    "MSP_DETAIL": 10,
    "OTHER_DETAIL": 6,
}
GROUPS = {
    "SITE_SLE": _SITE_SLE_OPS,
    "SITE_MAP": _SITE_MAP_OPS,
    "SITE_DETAIL": _SITE_DETAIL_OPS,
    "ORG_DETAIL": _ORG_DETAIL_OPS,
    "MSP_DETAIL": _MSP_DETAIL_OPS,
    "OTHER_DETAIL": _OTHER_DETAIL_OPS,
}


def _fake_mist_helper() -> Any:
    """Build a MistHelper stand-in that records exporter calls."""
    module = MagicMock()
    module.apisession = MagicMock()
    module.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-one"
    module.SiteDeviceExporter._resolve_site_for_stats.return_value = ("site-one", "site name")
    return module


def _expected_value(param: str) -> str:
    """Return the synthetic value that the prompt test supplies."""
    if param == "org_id":
        return "org-one"
    if param == "site_id":
        return "site-one"
    if param == "msp_id":
        return "msp-one"
    return f"{param}-value"


def _safe_input(prompt: str, allow_empty: bool, context: str) -> str:
    """Return a value that encodes the final context token."""
    return f"{context.rsplit('.', 1)[-1]}-value"


def test_group_counts_match_discovery() -> None:
    """The shipped tables must match the measured stage-two groups."""
    assert {name: len(entries) for name, entries in GROUPS.items()} == EXPECTED_BUCKET_COUNTS
    assert len(ALL_STAGE_TWO_ENDPOINT_OPS) == 132


def test_operation_table_has_no_duplicate_operation() -> None:
    """Duplicate operation rows make the prompt ambiguous."""
    names = [entry.operation for entry in ALL_STAGE_TWO_ENDPOINT_OPS]
    assert len(names) == len(set(names))


def test_phantom_and_active_endpoint_entries_do_not_ship() -> None:
    """Known phantom and active endpoints must not ship in the read-only family."""
    names = {entry.operation for entry in ALL_STAGE_TWO_ENDPOINT_OPS}
    assert "searchOrgClientFingerprints" not in names
    assert "optimizeInstallerRrm" not in names


@pytest.mark.parametrize("entry", ALL_STAGE_TWO_ENDPOINT_OPS, ids=lambda entry: entry.operation)
def test_every_entry_resolves_to_a_callable(entry: _EndpointFamilyOp) -> None:
    """Each table row must name a real function in a real SDK module."""
    resolved = EndpointFamilyExporter._resolve(entry)
    assert inspect.isfunction(resolved)


@pytest.mark.parametrize("entry", ALL_STAGE_TWO_ENDPOINT_OPS, ids=lambda entry: entry.operation)
def test_required_identifier_order_matches_sdk_signature(entry: _EndpointFamilyOp) -> None:
    """Each table row must preserve the SDK required-identifier order."""
    target = getattr(importlib.import_module(entry.module), entry.operation)
    required = [
        param.name
        for param in list(inspect.signature(target).parameters.values())[1:]
        if param.default is inspect._empty
    ]
    assert tuple(required) == entry.required


def test_every_operation_has_a_primary_key_strategy() -> None:
    """Each exported endpoint must pass a known strategy to the data writer."""
    missing = [
        entry.operation
        for entry in ALL_STAGE_TWO_ENDPOINT_OPS
        if entry.operation not in ENDPOINT_PRIMARY_KEY_STRATEGIES
    ]
    assert missing == []


@pytest.mark.parametrize("entry", ALL_STAGE_TWO_ENDPOINT_OPS, ids=lambda entry: entry.operation)
def test_prompt_sequence_preserves_identifier_order(entry: _EndpointFamilyOp) -> None:
    """The collected values must match the identifier tuple order."""
    fake = _fake_mist_helper()
    fake.InputUtils.safe_input.side_effect = _safe_input
    with (
        patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake),
        patch(
            "src.operations.exporting.export.endpoint_family_exporter.InputUtils.prompt_msp_id", return_value="msp-one"
        ),
    ):
        result = EndpointFamilyExporter._collect_arguments(entry)
    assert result is not None and len(result.values) == len(entry.required)  # Require all collected identifiers.
    assert result.values == tuple(_expected_value(param) for param in entry.required)


def test_choose_rejects_a_non_numeric_answer() -> None:
    """A non-number answer must return to the menu safely."""
    fake = _fake_mist_helper()
    fake.InputUtils.safe_input.return_value = "abc"
    with patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake):
        assert EndpointFamilyExporter._choose(_ORG_DETAIL_OPS, "org detail") is None


def test_choose_rejects_an_out_of_range_answer() -> None:
    """An out-of-range answer must not index the table."""
    fake = _fake_mist_helper()
    fake.InputUtils.safe_input.return_value = str(len(_ORG_DETAIL_OPS) + 1)
    with patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake):
        assert EndpointFamilyExporter._choose(_ORG_DETAIL_OPS, "org detail") is None


def test_persist_skips_empty_rows() -> None:
    """An empty endpoint response must not create an export file."""
    fake = _fake_mist_helper()
    with patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake):
        EndpointFamilyExporter._persist([], "empty.csv", "getOrgSso")
    fake.DataExporter.write_with_format_selection.assert_not_called()
    assert fake.DataExporter.write_with_format_selection.call_count == 0  # WHY: empty rows must skip export.


def test_persist_wraps_single_object_response() -> None:
    """A single JSON object response must export as one row."""
    fake = _fake_mist_helper()
    with patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake):
        EndpointFamilyExporter._persist({"id": "one"}, "one.csv", "getOrgSso")
    args, kwargs = fake.DataExporter.write_with_format_selection.call_args
    assert args[0] == [{"id": "one"}]
    assert kwargs["api_function_name"] == "getOrgSso"


def test_persist_reports_failed_write_count(caplog: pytest.LogCaptureFixture) -> None:
    """A failed writer must report zero written rows."""
    fake = _fake_mist_helper()
    fake.DataExporter.write_with_format_selection.return_value = False
    with patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake):
        written_count = EndpointFamilyExporter._persist([{"id": "one"}], "one.csv", "getOrgSso")
    assert written_count == 0
    assert "write failed after receiving 1 records" in caplog.text


def test_recover_logs_a_discarded_non_object_payload(caplog: pytest.LogCaptureFixture) -> None:
    """A non-empty payload that the SDK cannot collect must produce a loud error."""
    response = MagicMock(data="unexpected")
    assert EndpointFamilyExporter._recover_unpaginated_object(response, [], "getOrgSso") == []
    assert "Discarded non-empty getOrgSso payload with shape str" in caplog.text


def test_resolve_returns_none_for_a_missing_module() -> None:
    """A bad SDK module path must not crash the menu."""
    bad = _EndpointFamilyOp("listNothing", "mistapi.api.v1.not_a_module", ("org_id", "item_id"), (1,))
    assert EndpointFamilyExporter._resolve(bad) is None


def test_run_uses_identifiers_in_order() -> None:
    """Endpoint calls must receive identifiers in table order."""
    fake = _fake_mist_helper()
    callable_obj = MagicMock(return_value=MagicMock())
    entry = _SITE_MAP_OPS[0]
    with (
        patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake),
        patch.object(EndpointFamilyExporter, "_resolve", return_value=callable_obj),
        patch.object(
            EndpointFamilyExporter,
            "_collect_arguments",
            return_value=MagicMock(values=("site-one", "map-one"), label="target"),
        ),
        patch("src.operations.exporting.export.endpoint_family_exporter.mistapi.get_all", return_value=[]),
    ):
        EndpointFamilyExporter._run(entry)
    callable_obj.assert_called_once_with(fake.apisession, "site-one", "map-one")


def test_run_reports_sdk_errors_without_raising() -> None:
    """The menu must survive an SDK exception."""
    fake = _fake_mist_helper()
    callable_obj = MagicMock(side_effect=RuntimeError("boom"))
    with (
        patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake),
        patch.object(EndpointFamilyExporter, "_resolve", return_value=callable_obj),
        patch.object(
            EndpointFamilyExporter,
            "_collect_arguments",
            return_value=MagicMock(values=("org-one", "sso-one"), label="target"),
        ),
    ):
        EndpointFamilyExporter._run(_ORG_DETAIL_OPS[0])
    callable_obj.assert_called_once_with(fake.apisession, "org-one", "sso-one")


@pytest.mark.parametrize("status_code", [404, 503])
def test_run_logs_http_status_sdk_errors_without_raising(caplog: pytest.LogCaptureFixture, status_code: int) -> None:
    """An HTTP 404 or HTTP 503 SDK failure must be logged and contained."""
    fake = _fake_mist_helper()  # Build the MistHelper double used by the exporter.
    error = RuntimeError(f"HTTP {status_code}")  # Preserve the cloud status in the SDK error.
    callable_obj = MagicMock(side_effect=error)  # Force the selected SDK call to fail.
    with (
        patch.object(EndpointFamilyExporter, "_mist_helper", return_value=fake),
        patch.object(EndpointFamilyExporter, "_resolve", return_value=callable_obj),
        patch.object(
            EndpointFamilyExporter,
            "_collect_arguments",
            return_value=MagicMock(values=("org-one", "sso-one"), label="target"),
        ),
        caplog.at_level("ERROR"),
    ):
        FailureModeEndpointFamilyExporter._run(FAILURE_MODE_ORG_DETAIL_OPS[0])  # Call the real src path.
    assert f"HTTP {status_code}" in caplog.text  # Prove the operator can see the status.
    assert "Error running" in caplog.text  # Prove the product logged the failure.
    callable_obj.assert_called_once_with(fake.apisession, "org-one", "sso-one")  # Prove the API path ran.


# Keep the existing line-based quality fingerprints stable and reuse one guard decision.
if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from mistapi import APISession
    from requests import Response

    from src.operations.exporting.export.simple_endpoint_exporter import _SimpleEndpointOp
    from tests.guardrails.test_endpoint_catalog import GuardDecision, RegistrationInput, RegistrationKind

_catalog_guards = importlib.import_module("tests.guardrails.test_endpoint_catalog")
_CatalogCoverage = _catalog_guards.TestCatalogCoverage
deprecated_source = _catalog_guards.deprecated_source
deprecated_injection = _catalog_guards.deprecated_injection
deprecated_copy = _catalog_guards.deprecated_copy
deprecated_registration_case = _catalog_guards.deprecated_registration_case
_mistapi = importlib.import_module("mistapi")

RETAINED_FAMILY_DIGESTS = {
    "259": "a1b130efc7fc2605136e8ced260d7a5aeb79a98e0eb9e0daf360ab61e7a9761d",
    "260": "3c27ae201bab31537d2acb7557342b618fac200f9f3547ac3820febd7c3f948e",
    "261": "b02389a933165409e9222ef638b4130db38ff0e280bc6649864fb23afaa44719",
    "262": "0844ab9840694c88c8f8a1e654dbbb7a7d19fd8fb18c21dd58aba057f2502d60",
    "263": "3973a4a0594e0c0a8cb307329a58bcf010da2155b37b4cf7571abe6c1fc514f4",
    "264": "a5777f2fa6075431cbd4fedd08b4c076a1c72f0c99efde3b551314bfd8b9d7d0",
    "265": "18f6a4cb356dbcec3409a0fcb065ab438d581ea9e2b62a10fc4b04e64029549c",
    "266": "dfd2267bb67cfa939cb8470d8b51501db556bac79a7a2d70a8bdb0f7aa9285db",
    "267": "5ffbc2173183f78936aa421091c6a5df75c293dab567e11a59c6503845051e58",
    "268": "e418a0eea52f1b8d2f1f3e7488ba3fb5715907efd504c338d80e22f6dd58d4d8",
}
TREND_DEFINITIONS = (
    (
        "getSiteSleSummaryTrend",
        ("site_id", "scope", "scope_id", "metric"),
        1217,
        "Get site SLE summary trend (needs scope, scope ID, metric)",
    ),
    (
        "getSiteSleClassifierSummaryTrend",
        ("site_id", "scope", "scope_id", "metric", "classifier"),
        1213,
        "Get site SLE classifier summary trend (needs scope, scope ID, metric)",
    ),
)


@pytest.mark.parametrize("identifier", _catalog_guards.RETIRED_IDENTIFIERS)
@pytest.mark.parametrize("scenario", _catalog_guards.DEPRECATED_SCENARIOS)
def test_deprecated_registrations(
    identifier: str,
    scenario: str,
    deprecated_source: tuple[RegistrationKind, RegistrationInput],
    deprecated_registration_case: tuple[RegistrationInput, GuardDecision],
) -> None:
    """The exporter matrix uses the same guard on the same raw sources."""
    kind, _raw_source = deprecated_source
    source, expected = deprecated_registration_case
    decision = _CatalogCoverage._deprecated_decision(kind, source)
    message = f"{kind} {scenario} inspected {decision[1]} records: {decision[2]}"
    if scenario == "live":
        assert identifier not in decision[2], f"{kind} contains {identifier}. {message}"
    assert decision == expected, message


@pytest.mark.parametrize("menu,rows", _catalog_guards.ALL_TABLES)
def test_every_retained_family_row_keeps_its_fields(
    menu: str, rows: tuple[_EndpointFamilyOp | _SimpleEndpointOp, ...]
) -> None:
    """Pre-edit snapshots cover order, membership, and every row field."""
    import hashlib
    import json
    from dataclasses import asdict

    retained = [asdict(row) for row in rows if row.operation not in _catalog_guards.RETIRED_IDENTIFIERS]
    payload = json.dumps(retained, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(payload).hexdigest() == RETAINED_FAMILY_DIGESTS[menu]


@pytest.mark.parametrize("operation,required,issue,description", TREND_DEFINITIONS)
def test_retained_trend_rows_and_keys_are_exact(
    operation: str, required: tuple[str, ...], issue: int, description: str
) -> None:
    """Both supported rows retain their original SDK routing and keys."""
    from src.operations.exporting.export.endpoint_catalog import ENDPOINT_CATALOG, INTERACTIVE_SAFE, EndpointInfo

    row = next(entry for entry in _SITE_SLE_OPS if entry.operation == operation)
    assert row == _EndpointFamilyOp(operation, "mistapi.api.v1.sites.sle", required, (issue,))
    assert ENDPOINT_CATALOG[operation] == EndpointInfo(description, INTERACTIVE_SAFE)
    assert ENDPOINT_PRIMARY_KEY_STRATEGIES[operation] == {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": list(required),
        "unique_constraints": [],
        "description": "Endpoint family export for " + operation,
    }


LOCAL_TREND_HOST = "https://api.issue3335.test"
LOCAL_SITE_URL = LOCAL_TREND_HOST + "/api/v1/orgs/org-3335/sites?limit=1000"
LOCAL_TREND_ENV_KEYS = (
    "MIST_HOST",
    "MIST_APITOKEN",
    "MIST_API_TOKEN",
    "MIST_USER",
    "MIST_PASSWORD",
    "MIST_VAULT_URL",
    "MIST_VAULT_TOKEN",
    "MIST_VAULT_PATH",
    "MIST_VAULT_MOUNT_POINT",
    "MIST_KEYRING_SERVICE",
    "CONSOLE_LOG_LEVEL",
    "LOGGING_LOG_LEVEL",
    "HTTPS_PROXY",
)
TREND_ROUTES = (
    (
        "getSiteSleSummaryTrend",
        "/api/v1/sites/site-3335/sle/site/scope-3335/metric/coverage/summary-trend",
    ),
    (
        "getSiteSleClassifierSummaryTrend",
        "/api/v1/sites/site-3335/sle/site/scope-3335/metric/coverage/classifier/low-rssi/summary-trend",
    ),
)


def _trend_response(url: str, body: object, headers: dict[str, str] | None = None) -> Response:
    """Build a complete local HTTP response for real SDK decoding."""
    import json

    from requests import Request, Response

    response = Response()
    response.status_code = 200
    response.url = url
    response.encoding = "utf-8"
    response._content = json.dumps(body).encode("utf-8")
    response.request = Request("GET", url, headers={"Accept": "application/json"}).prepare()
    response.headers.update({"Content-Type": "application/json", **(headers or {})})
    return response


@pytest.fixture
def local_trend_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Use an empty local environment and fresh site data without credentials."""
    for name in LOCAL_TREND_ENV_KEYS:
        monkeypatch.delenv(name, raising=False)
    environment = tmp_path / "empty.env"
    environment.write_text("", encoding="utf-8")
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "data" / "SiteList.csv").write_text("id,name\nsite-3335,Local Site\n", encoding="utf-8")
    return environment


@pytest.fixture
def trend_sdk_logging(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Restore shared SDK log settings without filtering errors."""
    import logging

    from mistapi.__api_session import CONSOLE

    monkeypatch.setattr(CONSOLE, "level", CONSOLE.level)
    sdk_logger = logging.getLogger("mistapi")
    original_level = sdk_logger.level
    try:
        yield
    finally:
        sdk_logger.setLevel(original_level)


@pytest.fixture
def no_trend_sdk_errors(caplog: pytest.LogCaptureFixture) -> Iterator[None]:
    """Reject SDK error logs from setup, the real call, or teardown."""
    yield
    records = [record for phase in ("setup", "call", "teardown") for record in caplog.get_records(phase)]
    errors = [record.getMessage() for record in records if record.name.startswith("mistapi") and record.levelno >= 40]
    assert errors == []


@pytest.fixture
def local_trend_session(
    local_trend_environment: Path, trend_sdk_logging: None, no_trend_sdk_errors: None
) -> Iterator[APISession]:
    """Keep a real SDK session on an isolated host and close its transport."""
    session = _mistapi.APISession(env_file=str(local_trend_environment), show_cli_notif=False)
    session._cloud_uri = "api.issue3335.test"  # The SDK constructor accepts production clouds only.
    assert len(session._apitoken) == 0
    try:
        yield session
    finally:
        session._session.close()


@pytest.fixture
def local_trend_context(local_trend_session: APISession, monkeypatch: pytest.MonkeyPatch) -> None:
    """Seed real context and selectors through the existing local setters."""
    from src.foundation.runtime.config import runtime_settings
    from src.foundation.runtime.config.config_utils import ConfigUtils
    from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver
    from src.foundation.support.refactors.main_entrypoint import AppContext, MainEntrypoint

    session = local_trend_session
    monkeypatch.setattr(MainEntrypoint, "context", AppContext(mistapi=_mistapi, apisession=session, org_id="org-3335"))
    ConfigUtils.set_apisession(session)
    ConfigUtils.set_cached_org_id("org-3335")
    monkeypatch.setattr(runtime_settings, "LAST_SELECTED_SITE_ID", runtime_settings.LAST_SELECTED_SITE_ID)
    assert SourceDependencyResolver.apisession is session


@pytest.fixture(params=(False, True), ids=("sdk-present", "sdk-absent"))
def trend_sdk_absence(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> bool:
    """Remove both actual obsolete SDK attributes without replacing a trend."""
    from mistapi.api.v1.sites import sle

    if request.param:
        for identifier in _catalog_guards.RETIRED_IDENTIFIERS:
            monkeypatch.delattr(sle, identifier)
        assert [name for name in _catalog_guards.RETIRED_IDENTIFIERS if hasattr(sle, name)] == []
    return bool(request.param)


@pytest.fixture
def local_trend_boundaries(
    local_trend_session: APISession, local_trend_context: None, trend_sdk_absence: bool
) -> Iterator[tuple[APISession, MagicMock, MagicMock]]:
    """Only local HTTP transport and final output can use stand-ins."""
    from src.operations.exporting.export.data_exporter import DataExporter

    with (
        patch.object(
            local_trend_session._session, "get", side_effect=AssertionError("Unexpected local HTTP request")
        ) as transport,
        patch.object(DataExporter, "write_with_format_selection", autospec=True) as writer,
    ):
        yield local_trend_session, transport, writer


@pytest.fixture
def trend_case(request: pytest.FixtureRequest) -> tuple[str, str, str]:
    """Keep the expected route and filename independent of production code."""
    operation, uri = request.param
    suffix = "_classifier_low-rssi" if operation == "getSiteSleClassifierSummaryTrend" else ""
    filename = operation + "_Local_Site_scope_site_scope_id_scope-3335_metric_coverage" + suffix + ".csv"
    return operation, uri, filename


@pytest.fixture
def trend_answers(trend_case: tuple[str, str, str]) -> list[str]:
    """Supply console answers to the real one-based chooser and site selector."""
    operation, _uri, _filename = trend_case
    selection = next(index for index, row in enumerate(_SITE_SLE_OPS, 1) if row.operation == operation)
    answers = [str(selection), "0", "site", "scope-3335", "coverage"]
    return answers + (["low-rssi"] if operation == "getSiteSleClassifierSummaryTrend" else [])


@pytest.fixture
def trend_payloads(
    trend_case: tuple[str, str, str], shape: str
) -> tuple[dict[str, Response], list[dict[str, object]], list[str]]:
    """Cover list/results decoding and both real next-page mechanisms."""
    _operation, uri, _filename = trend_case
    url = LOCAL_TREND_HOST + uri
    first: dict[str, object] = {"summary": {"value": 42}, "note": "first\nsecond\r\nthird"}
    second: dict[str, object] = {"summary": {"value": 43}, "note": "next\rpage"}
    body: list[dict[str, object]] | dict[str, object] = {"results": [first]} if "results" in shape else [first]
    headers = {"X-Page-Total": "2", "X-Page-Limit": "1", "X-Page-Page": "1"} if shape == "paged-list" else {}
    if shape == "paged-results":
        assert isinstance(body, dict)
        body["next"] = uri + "?page=2"
    responses = {
        LOCAL_SITE_URL: _trend_response(LOCAL_SITE_URL, [{"id": "site-3335", "name": "Local Site"}]),
        url: _trend_response(url, body, headers),
    }
    expected: list[dict[str, object]] = [{"summary_value": 42, "note": "first\\nsecond\\nthird"}]
    urls = [LOCAL_SITE_URL, url]
    if shape.startswith("paged"):
        next_url = url + "?page=2"
        responses[next_url] = _trend_response(next_url, {"results": [second]} if "results" in shape else [second])
        expected.append({"summary_value": 43, "note": "nextpage"})
        urls.append(next_url)
    return responses, expected, urls


@pytest.mark.parametrize("trend_case", TREND_ROUTES, indirect=True, ids=[row[0] for row in TREND_ROUTES])
@pytest.mark.parametrize("shape", ("list", "results", "paged-list", "paged-results"))
def test_real_trend_generic_payloads_repeat_exact_dispatch(
    trend_case: tuple[str, str, str],
    trend_answers: list[str],
    trend_payloads: tuple[dict[str, Response], list[dict[str, object]], list[str]],
    local_trend_boundaries: tuple[APISession, MagicMock, MagicMock],
) -> None:
    """Generic list and results fixtures retain the existing SDK dispatch."""
    from unittest.mock import call

    from mistapi.api.v1.sites import sle

    operation, _uri, filename = trend_case
    _session, transport, writer = local_trend_boundaries
    responses, expected, urls = trend_payloads
    entry = next(row for row in _SITE_SLE_OPS if row.operation == operation)
    assert EndpointFamilyExporter._resolve(entry) is getattr(sle, operation)
    transport.side_effect = responses.__getitem__
    for _repeat in range(2):
        with patch("builtins.input", side_effect=trend_answers):
            EndpointFamilyExporter.site_sle_endpoints()
    assert transport.call_args_list == [call(url) for url in urls] * 2
    assert writer.call_args_list == [call(expected, filename, api_function_name=operation)] * 2


@pytest.fixture
def documented_trend_body(trend_case: tuple[str, str, str]) -> dict[str, object]:
    """Return the documented object shape for the selected trend operation."""
    operation, _uri, _filename = trend_case
    if operation == "getSiteSleSummaryTrend":
        return {
            "start": 1_728_144_000,
            "end": 1_728_147_600,
            "sle": {
                "interval": 300,
                "name": "coverage",
                "x_label": "time",
                "y_label": "value",
                "samples": {"degraded": [0], "total": [1], "value": [42]},
            },
            "classifiers": [],
        }
    return {
        "start": 1_728_144_000,
        "end": 1_728_147_600,
        "metric": "coverage",
        "classifier": {
            "interval": 300,
            "name": "low-rssi",
            "x_label": "time",
            "y_label": "duration",
            "samples": {"degraded": [0], "duration": [42], "total": [1]},
        },
    }


@pytest.mark.parametrize("trend_case", TREND_ROUTES, indirect=True, ids=[row[0] for row in TREND_ROUTES])
def test_real_trend_documented_object_exports_one_record(
    trend_case: tuple[str, str, str],
    trend_answers: list[str],
    documented_trend_body: dict[str, object],
    local_trend_boundaries: tuple[APISession, MagicMock, MagicMock],
) -> None:
    """Documented non-empty trend objects must reach the existing writer."""
    from unittest.mock import call

    _operation, uri, filename = trend_case
    _session, transport, writer = local_trend_boundaries
    url = LOCAL_TREND_HOST + uri
    transport.side_effect = {
        LOCAL_SITE_URL: _trend_response(LOCAL_SITE_URL, [{"id": "site-3335", "name": "Local Site"}]),
        url: _trend_response(url, documented_trend_body),
    }.__getitem__
    with patch("builtins.input", side_effect=trend_answers):
        EndpointFamilyExporter.site_sle_endpoints()
    assert transport.call_args_list == [call(LOCAL_SITE_URL), call(url)]
    assert writer.call_count == 1
    assert writer.call_args.kwargs["api_function_name"] == _operation
    assert writer.call_args.args[1] == filename
    row = writer.call_args.args[0][0]
    assert row["start"] == documented_trend_body["start"]
    assert row["end"] == documented_trend_body["end"]
    if _operation == "getSiteSleSummaryTrend":
        assert row["sle_samples_value"] == "42"
    else:
        assert row["metric"] == "coverage"
        assert row["classifier_samples_duration"] == "42"


@pytest.mark.parametrize("trend_case", TREND_ROUTES, indirect=True, ids=[row[0] for row in TREND_ROUTES])
@pytest.mark.parametrize(
    "query,query_suffix",
    (({}, ""), ({"start": "-1d", "end": "now", "duration": "10m"}, "?start=-1d&end=now&duration=10m")),
)
def test_real_trend_optional_queries(
    trend_case: tuple[str, str, str],
    query: dict[str, str],
    query_suffix: str,
    local_trend_boundaries: tuple[APISession, MagicMock, MagicMock],
) -> None:
    """Real SDK functions construct the optional query without new prompts."""
    from unittest.mock import call

    from mistapi.api.v1.sites import sle

    operation, uri, _filename = trend_case
    session, transport, writer = local_trend_boundaries
    target = getattr(sle, operation)
    defaults = [inspect.signature(target).parameters[name].default for name in ("start", "end", "duration")]
    assert defaults == [None, None, None]
    url = LOCAL_TREND_HOST + uri + query_suffix
    transport.return_value, transport.side_effect = _trend_response(url, [{"summary": {"value": 42}}]), None
    identifiers: tuple[str, ...] = ("site-3335", "site", "scope-3335", "coverage")
    identifiers += ("low-rssi",) if operation == "getSiteSleClassifierSummaryTrend" else ()
    response = target(session, *identifiers, **query)
    actual = (response.status_code, response.url, response.data, response.next)
    assert actual == (200, url, [{"summary": {"value": 42}}], None)
    assert transport.call_args_list == [call(url)]
    assert writer.call_args_list == []


@pytest.fixture
def trend_empty_payload(trend_case: tuple[str, str, str], empty_body: object) -> tuple[dict[str, Response], list[str]]:
    """Preserve empty SDK results without treating documented objects as empty."""
    _operation, uri, _filename = trend_case
    url = LOCAL_TREND_HOST + uri
    return {
        LOCAL_SITE_URL: _trend_response(LOCAL_SITE_URL, [{"id": "site-3335", "name": "Local Site"}]),
        url: _trend_response(url, empty_body),
    }, [LOCAL_SITE_URL, url]


@pytest.mark.parametrize("trend_case", TREND_ROUTES, indirect=True, ids=[row[0] for row in TREND_ROUTES])
@pytest.mark.parametrize("empty_body", ([], {"results": []}))
def test_real_trend_empty_results_skip_output(
    trend_answers: list[str],
    trend_empty_payload: tuple[dict[str, Response], list[str]],
    local_trend_boundaries: tuple[APISession, MagicMock, MagicMock],
) -> None:
    """True empty results must not create an export file."""
    from unittest.mock import call

    _session, transport, writer = local_trend_boundaries
    responses, urls = trend_empty_payload
    transport.side_effect = responses.__getitem__
    with patch("builtins.input", side_effect=trend_answers):
        EndpointFamilyExporter.site_sle_endpoints()
    assert transport.call_args_list == [call(url) for url in urls]
    assert writer.call_args_list == []


@pytest.fixture
def cancel_answers(
    request: pytest.FixtureRequest, trend_answers: list[str]
) -> tuple[list[str | EOFError | KeyboardInterrupt], list[str]]:
    """Supply failures at each actual required input boundary."""
    position: int
    failure: str
    position, failure = request.param
    failures: dict[str, str | EOFError | KeyboardInterrupt] = {
        "blank": " ",
        "eof": EOFError(),
        "interrupt": KeyboardInterrupt(),
    }
    answer = failures[failure] if failure in failures else failure
    answers = trend_answers[:position] + [answer]
    return answers, [LOCAL_SITE_URL] if position >= 2 else []


@pytest.mark.parametrize(
    "trend_case,cancel_answers",
    [
        (route, (position, failure))
        for route, definition in zip(TREND_ROUTES, TREND_DEFINITIONS, strict=True)
        for position in range(len(definition[1]) + 1)
        for failure in ("blank", "eof", "interrupt")
    ],
    indirect=True,
)
def test_real_trend_required_answer_cancellation(
    cancel_answers: tuple[list[str | EOFError | KeyboardInterrupt], list[str]],
    local_trend_boundaries: tuple[APISession, MagicMock, MagicMock],
) -> None:
    """The existing handlers cancel every blank, EOF, or interrupted answer."""
    from unittest.mock import call

    _session, transport, writer = local_trend_boundaries
    answers, urls = cancel_answers
    site_response = _trend_response(LOCAL_SITE_URL, [{"id": "site-3335", "name": "Local Site"}])
    transport.side_effect = {LOCAL_SITE_URL: site_response}.__getitem__
    with patch("builtins.input", side_effect=answers) as console:
        EndpointFamilyExporter.site_sle_endpoints()
    assert console.call_count == len(answers)
    assert transport.call_args_list == [call(url) for url in urls]
    assert writer.call_args_list == []


@pytest.mark.parametrize(
    "trend_case,cancel_answers",
    [
        (route, (position, answer))
        for route in TREND_ROUTES
        for position in (0, 1)
        for answer in ("invalid-choice", "999")
    ],
    indirect=True,
)
def test_real_trend_invalid_choices_cancel(
    cancel_answers: tuple[list[str | EOFError | KeyboardInterrupt], list[str]],
    local_trend_boundaries: tuple[APISession, MagicMock, MagicMock],
) -> None:
    """Invalid menu and site choices cannot become a trend request."""
    from unittest.mock import call

    _session, transport, writer = local_trend_boundaries
    answers, urls = cancel_answers
    with patch("builtins.input", side_effect=answers) as console:
        EndpointFamilyExporter.site_sle_endpoints()
    assert console.call_count == len(answers)
    assert transport.call_args_list == [call(url) for url in urls] == []
    assert writer.call_args_list == []
