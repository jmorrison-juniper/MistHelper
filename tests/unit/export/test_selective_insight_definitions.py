"""Prove selective refresh through all four insight callers without live services."""

from __future__ import annotations

import builtins
import csv
import importlib
import io
import json
import logging
import os
import pkgutil
import statistics
import time
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
import requests

from src.analytics import insight_metrics_utils as insight_module
from src.analytics.insight_metrics_utils import InsightMetricsUtils
from src.dataclasses.endpoint_config import EndpointConfig
from src.export import const_definitions_exporter as const_module
from src.export import org_export_utils as org_module
from src.export.const_definitions_exporter import ConstDefinitionsExporter
from src.export.data_exporter import DataExporter
from src.export.org_export_utils import OrgExportUtils
from src.export.site_insights.device_metric_operation import DeviceMetricOperation
from src.export.site_insights.site_metric_operation import SiteMetricOperation
from src.refactors.serial_cc import site_client_insights as client_module
from src.refactors.serial_cc.site_client_insights import SiteClientInsightsService

CALLERS = ("site", "client", "device", "org")
CACHE_CLOCK = 1_800_000_000.0
INSIGHT_FILE = "ConstInsightMetrics.csv"
INSIGHT_URI = "/api/v1/const/insight_metrics"
CSV_FIELDS = ("description", "intervals", "metric_name", "report_intervals", "report_scopes", "scopes", "type", "unit")
BASELINE_DEFINITIONS = (
    "alarm_defs",
    "ap_channels",
    "ap_esl_versions",
    "ap_led_status",
    "app_categories",
    "app_subcategories",
    "applications",
    "client_events",
    "countries",
    "default_gateway_config",
    "device_events",
    "device_models",
    "fingerprint_types",
    "gateway_applications",
    "insight_metrics",
    "languages",
    "license_types",
    "marvisclient_events",
    "marvisclient_versions",
    "mxedge_events",
    "mxedge_models",
    "nac_events",
    "otherdevice_events",
    "otherdevice_models",
    "states",
    "system_events",
    "traffic_types",
    "webhook_topics",
)
INSIGHT_PAYLOAD = {
    "bytes": {
        "description": "Traffic\nvolume",
        "type": "counter",
        "unit": "bytes",
        "scopes": ["site", "client", "device", "org"],
        "report_scopes": ["site"],
        "intervals": {"1h": {"interval": 3600, "max_age": 86400}},
        "report_intervals": {"1d": {"interval": 86400}},
    },
    "rssi": {"description": "Signal \u00e9", "scopes": ["client", "device"]},
    "site-count": {"scopes": ["site", "org"]},
    "{metric}": {"scopes": ["site", "client", "device", "org"]},
    "": {"scopes": ["site"]},
    "unscoped": {},
}
EXPECTED_SCOPES = {
    "site": ["bytes", "site-count"],
    "client": ["bytes", "rssi"],
    "device": ["bytes", "rssi"],
    "org": ["bytes", "site-count"],
}
BEFORE_MEDIANS = {
    "site": 1.799229208,
    "client": 1.796314792,
    "device": 1.786930666,
    "org": 1.815521417,
}


@dataclass
class OfflineConstantSession:
    """Record SDK requests and return fixed definitions with optional real latency."""

    requests: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    latency: float = 0.0
    insight_response: Any = None

    def mist_get(self, uri: str, query: dict[str, Any] | None = None) -> SimpleNamespace:
        """Reject non-constant requests before they can reach an external service."""
        if not uri.startswith("/api/v1/const/"):
            raise AssertionError(f"Unscripted request: {uri}")
        self.requests.append((uri, dict(query or {})))
        if self.latency:
            time.sleep(self.latency)
        if uri == INSIGHT_URI and self.insight_response is not None:
            if isinstance(self.insight_response, Exception):
                raise self.insight_response
            return self.insight_response
        return SimpleNamespace(status_code=200, data=self._payload(uri), proxy_error=False)

    @staticmethod
    def _payload(uri: str) -> Any:
        """Provide one country and one gateway for the real full-export dispatch."""
        if uri == INSIGHT_URI:
            return deepcopy(INSIGHT_PAYLOAD)
        if uri == "/api/v1/const/countries":
            return {"US": {"name": "United States"}}
        if uri == "/api/v1/const/device_models":
            return [{"model": "SRX300", "type": "gateway"}]
        return {"sample": {"description": "Offline definition"}}


@dataclass
class OfflineConstantWriter:
    """Keep real CSV serialization while excluding every database backend."""

    directory: Path
    attempts: list[tuple[str, list[dict[str, Any]], str]] = field(default_factory=list)
    completed: list[str] = field(default_factory=list)
    failures: list[bool | Exception] = field(default_factory=list)

    def write_with_format_selection(self, data: list[dict[str, Any]], filename: str, api_function_name: str) -> bool:
        """Record the backend boundary and write only inside the temporary directory."""
        self.attempts.append((filename, deepcopy(data), api_function_name))
        outcome = self.failures.pop(0) if self.failures else True
        if isinstance(outcome, Exception):
            raise outcome
        if not outcome:
            return False
        result = DataExporter._write_csv_format(data, filename)
        destination = self.directory / filename
        if data and destination.exists():
            os.utime(destination, (CACHE_CLOCK, CACHE_CLOCK))  # Freeze cache time, not the elapsed-time clock.
        if result:
            self.completed.append(filename)
        return result


@dataclass
class InsightRefreshScenario:
    """Bind real insight callers to isolated request, output, and filesystem seams."""

    deps: SimpleNamespace
    definitions: dict[str, EndpointConfig]
    exists: MagicMock
    mtime: MagicMock
    enumeration: MagicMock

    def seed(self, age: float = 86401.0, missing: bool = False) -> None:
        """Create equivalent cache fixtures outside the measured refresh interval."""
        directory = self.deps.DataExporter.directory
        directory.mkdir(exist_ok=True)
        for config in self.definitions.values():
            destination = directory / config.filename
            destination.write_text("cached,definition\nold,value\n", encoding="utf-8")
            os.utime(destination, (CACHE_CLOCK - age, CACHE_CLOCK - age))
        insight = directory / INSIGHT_FILE
        rows = ConstDefinitionsExporter(self.deps.apisession)._convert_insight_metrics(deepcopy(INSIGHT_PAYLOAD))
        DataExporter._write_csv_format(rows, INSIGHT_FILE)
        os.utime(insight, (CACHE_CLOCK - age, CACHE_CLOCK - age))
        if missing:
            insight.unlink()
        self.reset_records()

    def reset_records(self) -> None:
        """Exclude fixture creation and a prior trial from current-attempt counts."""
        self.deps.apisession.requests.clear()
        self.deps.DataExporter.attempts.clear()
        self.deps.DataExporter.completed.clear()
        self.deps.exporters.clear()
        for spy in (self.exists, self.mtime, self.enumeration, *getattr(self.deps, "open_spies", ())):
            spy.reset_mock()

    def invoke(self, caller: str) -> list[str] | None:
        """Invoke each actual refresh method without replacing its implementation."""
        if caller == "client":
            return SiteClientInsightsService._print_intro_and_refresh(self.deps)
        if caller == "org":
            return OrgExportUtils._insight_setup_or_empty()
        dependencies = {
            "apisession": self.deps.apisession,
            "InsightMetricsUtils": InsightMetricsUtils,
            "PromptUtils": MagicMock(),
            "DataProcessingUtils": MagicMock(),
            "DataExporter": self.deps.DataExporter,
            "EnhancedSSHRunner": MagicMock(),
            "mistapi": MagicMock(),
        }
        if caller == "site":
            return SiteMetricOperation(**dependencies)._refresh_const_metrics()
        if caller == "device":
            return DeviceMetricOperation(**dependencies, PacketCaptureManager=MagicMock())._refresh_const_metrics()
        raise AssertionError(f"Unknown insight caller: {caller}")

    def cache_accesses(self) -> set[str]:
        """Count only definition-file accesses inside the refresh interval."""
        return {
            Path(str(call.args[0])).name
            for spy in (self.exists, self.mtime, *getattr(self.deps, "open_spies", ()))
            for call in spy.call_args_list
            if Path(str(call.args[0])).name.startswith("Const")
        }


@dataclass(frozen=True)
class DefinitionCacheSnapshot:
    """Compare file contents and timestamps outside the measured refresh interval."""

    files: dict[str, tuple[bytes, float]]

    @classmethod
    def capture(cls, directory: Path, filenames: list[str]) -> DefinitionCacheSnapshot:
        """Read only the explicitly named temporary cache files."""
        files = {
            filename: ((directory / filename).read_bytes(), (directory / filename).stat().st_mtime)
            for filename in filenames
        }
        return cls(files)


@pytest.fixture
def offline_dependencies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Bind isolated request and CSV boundaries without replacing refresh behavior."""
    session = OfflineConstantSession()
    writer = OfflineConstantWriter(tmp_path / "data")
    exporters: list[ConstDefinitionsExporter] = []

    def recorded_exporter(api_session: OfflineConstantSession) -> ConstDefinitionsExporter:
        """Keep exporter instances available for real counter and failure assertions."""
        instance = ConstDefinitionsExporter(api_session)
        exporters.append(instance)
        return instance

    deps = SimpleNamespace(
        apisession=session,
        DataExporter=writer,
        InsightMetricsUtils=InsightMetricsUtils,
        ConstDefinitionsExporter=recorded_exporter,
        exporters=exporters,
    )
    for module in (insight_module, const_module, org_module):
        monkeypatch.setattr(module, "SourceDependencyResolver", deps)
    return deps


@pytest.fixture
def scenario(offline_dependencies: SimpleNamespace, monkeypatch: pytest.MonkeyPatch) -> InsightRefreshScenario:
    """Use the real installed SDK and control only cache time and filesystem measurement."""
    baseline = ConstDefinitionsExporter(offline_dependencies.apisession)
    baseline._discover_endpoints()
    exists, mtime, enumeration = (
        MagicMock(wraps=os.path.exists),
        MagicMock(wraps=os.path.getmtime),
        MagicMock(wraps=pkgutil.iter_modules),
    )
    monkeypatch.setattr(os.path, "exists", exists)
    monkeypatch.setattr(os.path, "getmtime", mtime)
    monkeypatch.setattr(pkgutil, "iter_modules", enumeration)
    monkeypatch.setattr(time, "time", lambda: CACHE_CLOCK)
    return InsightRefreshScenario(offline_dependencies, baseline.discovered_endpoints, exists, mtime, enumeration)


@pytest.fixture(autouse=True)
def guard_definition_reads(
    request: pytest.FixtureRequest, scenario: InsightRefreshScenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Guard functional file reads without changing the original timed benchmark harness."""
    if request.node.originalname == "test_controlled_refresh_benchmark":
        return
    opens = (MagicMock(wraps=builtins.open), MagicMock(wraps=io.open))
    scenario.deps.open_spies = opens
    monkeypatch.setattr(builtins, "open", opens[0])
    monkeypatch.setattr(io, "open", opens[1])


@pytest.mark.parametrize("caller", CALLERS)
def test_actual_stale_caller_refresh_is_selective(scenario: InsightRefreshScenario, caller: str) -> None:
    """All four real callers must avoid requests and cache accesses for other definitions."""
    scenario.seed()
    result = scenario.invoke(caller)
    requests = [uri for uri, _ in scenario.deps.apisession.requests]
    writes = [filename for filename, _, _ in scenario.deps.DataExporter.attempts]
    print(
        f"Checked caller={caller} requests={len(requests)} writes={len(writes)} caches={len(scenario.cache_accesses())}"
    )
    assert requests == [INSIGHT_URI], f"{caller} requested {len(requests)} definitions: {requests}"
    assert writes == [INSIGHT_FILE]
    assert scenario.cache_accesses() == {INSIGHT_FILE}
    assert scenario.enumeration.call_count == 0
    assert result == (EXPECTED_SCOPES["org"] if caller == "org" else None)


def test_export_endpoint_selection_reuses_real_helpers(
    scenario: InsightRefreshScenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The selected entry must use existing discovery and cache processing, not another implementation."""
    scenario.seed()
    exporter = ConstDefinitionsExporter(scenario.deps.apisession)
    inspect_module = MagicMock(wraps=exporter._inspect_module)
    process = MagicMock(wraps=exporter._process_single_endpoint)
    monkeypatch.setattr(exporter, "_inspect_module", inspect_module)
    monkeypatch.setattr(exporter, "_process_single_endpoint", process)
    result = exporter.export_endpoint("insight_metrics")
    assert result.outcome == "updated"
    assert dict(result.counts) == {"processed": 1, "skipped_fresh": 0, "updated": 1, "failed": 0}
    assert set(exporter.discovered_endpoints) == {"insight_metrics"}
    assert inspect_module.call_args.args == ("mistapi.api.v1.const.insight_metrics",)
    assert inspect_module.call_count == process.call_count == 1
    assert process.call_args.args[0] is exporter.discovered_endpoints["insight_metrics"]
    assert scenario.enumeration.call_count == 0


@pytest.mark.parametrize(
    "selection", [None, 42, "", "_private", "insight.metrics", "../countries", "insight/metrics", "\u00e9"]
)
def test_invalid_selection_is_failed_without_io(scenario: InsightRefreshScenario, selection: Any) -> None:
    """Invalid names must fail visibly without a full-export fallback."""
    scenario.seed()
    result = ConstDefinitionsExporter(scenario.deps.apisession).export_endpoint(selection)
    assert result.outcome == "failed"
    assert isinstance(result.first_error, ValueError)
    assert dict(result.counts) == {"processed": 0, "skipped_fresh": 0, "updated": 0, "failed": 1}
    assert scenario.deps.apisession.requests == []
    assert scenario.deps.DataExporter.attempts == []
    assert scenario.cache_accesses() == set()
    assert scenario.enumeration.call_count == 0


def test_import_failure_cannot_reuse_an_old_registration(
    scenario: InsightRefreshScenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed selected discovery must retain its first error and never use stale registration state."""
    scenario.seed()
    exporter = ConstDefinitionsExporter(scenario.deps.apisession)
    exporter.discovered_endpoints = dict(scenario.definitions)
    error = ImportError("Selected definition module is unavailable")
    importer = MagicMock(side_effect=error)
    monkeypatch.setattr(importlib, "import_module", importer)
    result = exporter.export_endpoint("insight_metrics")
    assert result.first_error is error
    assert result.outcome == "failed"
    assert result.http_status is None
    assert result.counts["failed"] == 1 and result.counts["processed"] == 0
    assert "insight_metrics" not in exporter.discovered_endpoints
    assert scenario.deps.apisession.requests == []
    assert scenario.deps.DataExporter.attempts == []
    assert importer.call_count == 1


def test_same_exporter_reports_independent_attempt_counts(scenario: InsightRefreshScenario) -> None:
    """A second cache hit must not inherit the first attempt's successful update count."""
    scenario.seed()
    exporter = ConstDefinitionsExporter(scenario.deps.apisession)
    first = exporter.export_endpoint("insight_metrics")
    second = exporter.export_endpoint("insight_metrics")
    assert first.outcome == "updated" and first.counts["updated"] == 1
    assert second.outcome == "fresh"
    assert dict(second.counts) == {"processed": 1, "skipped_fresh": 1, "updated": 0, "failed": 0}
    assert len(scenario.deps.apisession.requests) == len(scenario.deps.DataExporter.attempts) == 1
    with pytest.raises(TypeError):
        first.counts["updated"] = 99
    assert first.counts["updated"] == 1


@pytest.mark.parametrize("caller", CALLERS)
@pytest.mark.parametrize(
    "age,missing,requests_count", [(0, False, 0), (86399, False, 0), (86400, False, 1), (86401, False, 1), (0, True, 1)]
)
def test_each_caller_preserves_cache_boundary(
    scenario: InsightRefreshScenario, caller: str, age: float, missing: bool, requests_count: int
) -> None:
    """Fresh, exact-boundary, expired, and missing caches must retain the 24-hour decision."""
    scenario.seed(age, missing)
    directory = scenario.deps.DataExporter.directory
    unrelated_names = [config.filename for name, config in scenario.definitions.items() if name != "insight_metrics"]
    unrelated = DefinitionCacheSnapshot.capture(directory, unrelated_names)
    selected = directory / INSIGHT_FILE
    original = None if missing else (selected.read_bytes(), selected.stat().st_mtime)
    scenario.reset_records()  # Keep fixture snapshots outside the guarded refresh interval.
    result = scenario.invoke(caller)
    counts = (
        len(scenario.deps.apisession.requests),
        len(scenario.deps.DataExporter.attempts),
        scenario.enumeration.call_count,
    )
    assert counts == (requests_count, requests_count, 0)
    assert scenario.cache_accesses() == {INSIGHT_FILE}
    assert result == (EXPECTED_SCOPES["org"] if caller == "org" else None)
    if not requests_count:
        assert (selected.read_bytes(), selected.stat().st_mtime) == original
    assert DefinitionCacheSnapshot.capture(directory, unrelated_names) == unrelated


@pytest.mark.parametrize("caller", CALLERS)
def test_each_caller_reuses_the_second_refresh(scenario: InsightRefreshScenario, caller: str) -> None:
    """A successful refresh must produce an unchanged cache on the second call."""
    scenario.seed()
    scenario.invoke(caller)
    destination = scenario.deps.DataExporter.directory / INSIGHT_FILE
    original = (destination.read_bytes(), destination.stat().st_mtime)
    scenario.reset_records()
    scenario.invoke(caller)
    assert scenario.deps.apisession.requests == []
    assert scenario.deps.DataExporter.attempts == []
    assert scenario.deps.exporters[-1].endpoints_skipped_fresh == 1
    assert (destination.read_bytes(), destination.stat().st_mtime) == original


@pytest.mark.parametrize("caller", CALLERS)
@pytest.mark.parametrize("status_code", [404, 503])
@pytest.mark.parametrize("body", [{"detail": "Definition is unavailable"}, {}])
def test_each_caller_preserves_http_failure_status(
    scenario: InsightRefreshScenario,
    caller: str,
    status_code: int,
    body: dict[str, str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Failed HTTP responses must not become successful definitions or stale-file availability messages."""
    scenario.seed()
    scenario.deps.apisession.insight_response = SimpleNamespace(status_code=status_code, data=body)
    with caplog.at_level(logging.INFO):
        scenario.invoke(caller)
    exporter = scenario.deps.exporters[-1]
    assert exporter.endpoints_failed == 1 and exporter.endpoints_updated == 0
    assert scenario.deps.apisession.requests == [(INSIGHT_URI, {})]
    assert scenario.deps.DataExporter.attempts == [(INSIGHT_FILE, [], "listInsightMetrics")]
    assert f"HTTP {status_code}" in caplog.text
    assert "ConstInsightMetrics.csv is available" not in caplog.text
    assert (scenario.deps.DataExporter.directory / INSIGHT_FILE).is_file()


def test_first_http_error_survives_a_secondary_output_error(
    scenario: InsightRefreshScenario, caplog: pytest.LogCaptureFixture
) -> None:
    """The fallback must not replace the original HTTP response or count a second failure."""
    scenario.seed()
    response = SimpleNamespace(status_code=503, data={"detail": "Definition is unavailable"})
    scenario.deps.apisession.insight_response = response
    scenario.deps.DataExporter.failures = [OSError("Secondary output failure")]
    with caplog.at_level(logging.ERROR):
        result = ConstDefinitionsExporter(scenario.deps.apisession).export_endpoint("insight_metrics")
    assert result.outcome == "failed"
    assert isinstance(result.first_error, requests.HTTPError)
    assert result.first_error.response is response
    assert result.http_status == 503
    assert result.counts["failed"] == 1 and result.counts["updated"] == 0
    assert "HTTP 503" in caplog.text and "Secondary output failure" in caplog.text
    assert len(scenario.deps.DataExporter.attempts) == 1


def test_http_404_result_preserves_the_original_reason(scenario: InsightRefreshScenario) -> None:
    """An HTTP 404 must retain its original response and reason in the selected result."""
    scenario.seed()
    response = SimpleNamespace(status_code=404, data={"detail": "Definition is unavailable"})
    scenario.deps.apisession.insight_response = response
    result = ConstDefinitionsExporter(scenario.deps.apisession).export_endpoint("insight_metrics")
    assert result.outcome == "failed" and result.http_status == 404
    assert isinstance(result.first_error, requests.HTTPError)
    assert result.first_error.response is response
    assert "Definition is unavailable" in str(result.first_error)
    assert dict(result.counts) == {"processed": 1, "skipped_fresh": 0, "updated": 0, "failed": 1}
    assert scenario.deps.apisession.requests == [(INSIGHT_URI, {})]


@pytest.mark.parametrize("data,field_name", [(None, "raw_data"), ([], "text"), ({}, "raw_data"), ({}, "text")])
def test_unparsed_http_error_body_retains_its_first_reason(
    scenario: InsightRefreshScenario, data: Any, field_name: str
) -> None:
    """The SDK raw body and the requests text body must retain error evidence after JSON parsing fails."""
    scenario.seed()
    response = SimpleNamespace(status_code=503, data=data)
    setattr(response, field_name, "Original error before JSON parsing")
    scenario.deps.apisession.insight_response = response
    result = ConstDefinitionsExporter(scenario.deps.apisession).export_endpoint("insight_metrics")
    assert result.outcome == "failed" and result.http_status == 503
    assert isinstance(result.first_error, requests.HTTPError)
    assert result.first_error.response is response
    assert "Original error before JSON parsing" in str(result.first_error)
    assert result.counts["failed"] == 1 and result.counts["updated"] == 0


@pytest.mark.parametrize(
    "error", [requests.ConnectionError("Offline connection failure"), requests.Timeout("Offline timeout")]
)
def test_transport_failure_retains_the_original_error(
    scenario: InsightRefreshScenario, error: requests.RequestException
) -> None:
    """Expected transport faults must preserve error identity instead of returning empty success."""
    scenario.seed()
    scenario.deps.apisession.insight_response = error
    result = ConstDefinitionsExporter(scenario.deps.apisession).export_endpoint("insight_metrics")
    assert result.first_error is error
    assert result.outcome == "failed" and result.http_status is None
    assert result.counts["failed"] == 1 and result.counts["updated"] == 0
    assert scenario.deps.DataExporter.attempts == [(INSIGHT_FILE, [], "listInsightMetrics")]


def test_raised_http_error_preserves_a_false_boolean_response(scenario: InsightRefreshScenario) -> None:
    """A requests error response evaluates to False but still contains the original HTTP status."""
    scenario.seed()
    response = requests.Response()
    response.status_code = 503
    error = requests.HTTPError("Original HTTP 503 refusal", response=response)
    scenario.deps.apisession.insight_response = error
    result = ConstDefinitionsExporter(scenario.deps.apisession).export_endpoint("insight_metrics")
    assert result.first_error is error
    assert result.http_status == 503 and result.outcome == "failed"
    assert result.counts["failed"] == 1 and result.counts["updated"] == 0


@pytest.mark.parametrize("failure", [False, OSError("Primary output failure")])
def test_writer_failure_is_not_a_successful_update(scenario: InsightRefreshScenario, failure: bool | OSError) -> None:
    """A primary writer failure and failed fallback must remain one failed refresh."""
    scenario.seed()
    original = (scenario.deps.DataExporter.directory / INSIGHT_FILE).read_bytes()
    scenario.deps.DataExporter.failures = [failure, False]
    result = ConstDefinitionsExporter(scenario.deps.apisession).export_endpoint("insight_metrics")
    assert result.outcome == "failed"
    assert isinstance(result.first_error, OSError)
    if isinstance(failure, OSError):
        assert result.first_error is failure
    assert dict(result.counts) == {"processed": 1, "skipped_fresh": 0, "updated": 0, "failed": 1}
    assert len(scenario.deps.DataExporter.attempts) == 2
    assert scenario.deps.DataExporter.completed == []
    assert (scenario.deps.DataExporter.directory / INSIGHT_FILE).read_bytes() == original


def test_insight_csv_and_scope_contracts_are_unchanged(scenario: InsightRefreshScenario) -> None:
    """Real CSV serialization must preserve existing sorted fields, values, row order, and scope exclusions."""
    scenario.seed()
    destination = scenario.deps.DataExporter.directory / INSIGHT_FILE
    baseline_bytes = destination.read_bytes()
    scenario.invoke("site")
    assert destination.read_bytes() == baseline_bytes
    with destination.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == list(CSV_FIELDS)
        rows = list(reader)
    assert [row["metric_name"] for row in rows] == list(INSIGHT_PAYLOAD)
    assert rows[0]["scopes"] == "site, client, device, org"
    assert rows[0]["intervals"] == "1h(3600s, max_age:86400s)"
    assert rows[0]["report_intervals"] == "1d(86400s)"
    assert rows[1]["description"] == "Signal \u00e9"
    assert {scope: InsightMetricsUtils.get_by_scope(scope) for scope in CALLERS} == EXPECTED_SCOPES
    assert scenario.deps.DataExporter.attempts[0][2] == "listInsightMetrics"


@pytest.mark.parametrize("age,expected", [(0, (28, 0, 0, 0)), (86401, (0, 28, 31, 28))])
def test_export_all_keeps_complete_definition_coverage(
    scenario: InsightRefreshScenario, age: float, expected: tuple[int, int, int, int]
) -> None:
    """The separate full export must retain all 28 SDK definitions and every special-handling path."""
    scenario.seed(age)
    exporter = ConstDefinitionsExporter(scenario.deps.apisession)
    assert exporter.export_all() is None
    assert tuple(exporter.discovered_endpoints) == BASELINE_DEFINITIONS
    assert exporter.endpoints_processed == 28 and exporter.endpoints_failed == 0
    counts = (
        exporter.endpoints_skipped_fresh,
        exporter.endpoints_updated,
        len(scenario.deps.apisession.requests),
        len(scenario.deps.DataExporter.attempts),
    )
    assert counts == expected
    assert {config.special_handling for config in exporter.discovered_endpoints.values()} == {
        None,
        "all_models",
        "all_countries",
        "all_countries_channels",
    }
    if age:
        assert set(scenario.deps.DataExporter.completed) == {
            config.filename for config in scenario.definitions.values()
        }
        assert sum(uri == "/api/v1/const/countries" for uri, _ in scenario.deps.apisession.requests) == 3
        assert sum(uri == "/api/v1/const/device_models" for uri, _ in scenario.deps.apisession.requests) == 2


@pytest.mark.parametrize("caller", CALLERS)
def test_unreadable_timestamp_refreshes_only_insight(
    scenario: InsightRefreshScenario, caller: str, caplog: pytest.LogCaptureFixture
) -> None:
    """An unreadable cache timestamp must retain the existing refresh behavior."""
    scenario.seed(0)
    scenario.mtime.side_effect = OSError("Cache timestamp is unavailable")
    with caplog.at_level(logging.WARNING):
        scenario.invoke(caller)
    assert scenario.deps.apisession.requests == [(INSIGHT_URI, {})]
    assert [filename for filename, _, _ in scenario.deps.DataExporter.attempts] == [INSIGHT_FILE]
    assert scenario.deps.exporters[-1].endpoints_failed == 0
    assert "Cache timestamp is unavailable" in caplog.text


@pytest.mark.parametrize("caller", CALLERS)
def test_successful_empty_body_preserves_existing_output_contract(
    scenario: InsightRefreshScenario, caller: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Empty successful data must retain writer behavior and the organization's four empty-output attempts."""
    scenario.seed(missing=True)
    scenario.deps.apisession.insight_response = SimpleNamespace(status_code=200, data={})
    with caplog.at_level(logging.INFO):
        result = scenario.invoke(caller)
    assert result is None
    assert scenario.deps.exporters[-1].endpoints_updated == 1
    assert scenario.deps.exporters[-1].endpoints_failed == 0
    assert scenario.deps.DataExporter.attempts[0] == (INSIGHT_FILE, [], "listInsightMetrics")
    expected_outputs = {
        "OrgMetricsSummary.csv",
        "OrgMetricsTimeSeries.csv",
        "OrgMetricsResults.csv",
        "OrgSitesData.csv",
    }
    assert {filename for filename, _, _ in scenario.deps.DataExporter.attempts[1:]} == (
        expected_outputs if caller == "org" else set()
    )
    assert "was not created" in caplog.text
    assert not (scenario.deps.DataExporter.directory / INSIGHT_FILE).exists()


@pytest.mark.parametrize("proxy_error", [False, True])
def test_missing_http_response_is_failed(scenario: InsightRefreshScenario, proxy_error: bool) -> None:
    """An SDK response with no HTTP status must not become empty success."""
    scenario.seed()
    scenario.deps.apisession.insight_response = SimpleNamespace(status_code=None, data={}, proxy_error=proxy_error)
    result = ConstDefinitionsExporter(scenario.deps.apisession).export_endpoint("insight_metrics")
    assert result.outcome == "failed"
    assert isinstance(result.first_error, requests.RequestException)
    assert result.http_status is None
    assert result.counts["updated"] == 0 and result.counts["failed"] == 1


def test_malformed_json_definition_is_failed(scenario: InsightRefreshScenario) -> None:
    """Malformed definition rows must retain failure rather than report an updated cache."""
    scenario.seed()
    scenario.deps.apisession.insight_response = SimpleNamespace(status_code=200, data={"bytes": None})
    result = ConstDefinitionsExporter(scenario.deps.apisession).export_endpoint("insight_metrics")
    assert result.outcome == "failed"
    assert isinstance(result.first_error, AttributeError)
    assert result.counts["updated"] == 0 and result.counts["failed"] == 1
    assert scenario.deps.DataExporter.attempts == [(INSIGHT_FILE, [], "listInsightMetrics")]


def test_raw_definition_response_remains_supported(scenario: InsightRefreshScenario) -> None:
    """The selected fetch must retain the existing response double without an SDK status attribute."""
    scenario.seed()
    scenario.deps.apisession.insight_response = SimpleNamespace(data=deepcopy(INSIGHT_PAYLOAD))
    result = ConstDefinitionsExporter(scenario.deps.apisession).export_endpoint("insight_metrics")
    assert result.outcome == "updated"
    assert result.first_error is None and result.http_status is None
    assert result.counts["updated"] == 1 and result.counts["failed"] == 0


def test_unavailable_definition_reports_zero_io(scenario: InsightRefreshScenario) -> None:
    """An absent SDK module must not invoke another definition as a fallback."""
    scenario.seed()
    result = ConstDefinitionsExporter(scenario.deps.apisession).export_endpoint("unavailable_definition")
    assert result.outcome == "failed"
    assert isinstance(result.first_error, ImportError)
    assert result.counts["processed"] == 0 and result.counts["failed"] == 1
    assert scenario.deps.apisession.requests == [] and scenario.deps.DataExporter.attempts == []
    assert scenario.cache_accesses() == set()


def test_definition_without_a_usable_sdk_function_is_failed(
    scenario: InsightRefreshScenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Selected discovery must report missing functions without cache or request work."""
    scenario.seed()
    importer = MagicMock(return_value=SimpleNamespace(value=42))
    monkeypatch.setattr(importlib, "import_module", importer)
    result = ConstDefinitionsExporter(scenario.deps.apisession).export_endpoint("insight_metrics")
    assert result.outcome == "failed" and isinstance(result.first_error, ImportError)
    assert result.counts["processed"] == 0 and result.counts["failed"] == 1
    assert scenario.deps.apisession.requests == [] and scenario.deps.DataExporter.attempts == []
    assert importer.call_count == 1 and scenario.enumeration.call_count == 0


def test_unexpected_programming_fault_still_propagates(
    scenario: InsightRefreshScenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A programming fault must not become a normal failed or empty refresh result."""
    scenario.seed()
    exporter = ConstDefinitionsExporter(scenario.deps.apisession)
    monkeypatch.setattr(exporter, "_is_file_fresh", MagicMock(side_effect=TypeError("Incorrect cache state")))
    with pytest.raises(TypeError, match="Incorrect cache state"):
        exporter.export_endpoint("insight_metrics")
    assert exporter.endpoints_failed == 0
    assert scenario.deps.DataExporter.attempts == []


def test_client_resolver_removes_the_direct_exporter_dependency(
    scenario: InsightRefreshScenario, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The client dependency resolver must work without its obsolete comprehensive exporter field."""
    names = (
        "mistapi",
        "apisession",
        "InsightMetricsUtils",
        "PromptUtils",
        "InputUtils",
        "EnhancedSSHRunner",
        "DataProcessingUtils",
        "DataExporter",
        "SiteClientExporter",
    )
    host = SimpleNamespace(**{name: MagicMock(name=name) for name in names})
    resolver = SimpleNamespace(active_dependency_host=lambda: host)
    monkeypatch.setattr(client_module, "SourceDependencyResolver", resolver)
    dependencies = client_module._resolve_runtime_dependencies()
    assert vars(dependencies) == vars(host)
    assert "ConstDefinitionsExporter" not in vars(dependencies)
    assert scenario.deps.apisession.requests == []


@pytest.mark.parametrize("caller", CALLERS)
@pytest.mark.parametrize("insight_age", [-3600, 0, 86401])
def test_unrelated_cache_ages_cannot_change_the_insight_decision(
    scenario: InsightRefreshScenario, caller: str, insight_age: float
) -> None:
    """Fresh or future insight timestamps must ignore expired unrelated definition files."""
    scenario.seed(86401 if insight_age <= 0 else 0)
    selected = scenario.deps.DataExporter.directory / INSIGHT_FILE
    os.utime(selected, (CACHE_CLOCK - insight_age, CACHE_CLOCK - insight_age))
    scenario.reset_records()
    scenario.invoke(caller)
    expected_count = 0 if insight_age < 86400 else 1
    assert len(scenario.deps.apisession.requests) == expected_count
    assert len(scenario.deps.DataExporter.attempts) == expected_count
    assert scenario.cache_accesses() == {INSIGHT_FILE}
    assert scenario.enumeration.call_count == 0


def test_large_ordered_definition_payload_remains_one_request(scenario: InsightRefreshScenario) -> None:
    """A larger definition response must retain order without creating extra requests."""
    scenario.seed()
    payload = {f"metric-{number:04}": {"scopes": ["site"], "description": "Metric \u00e9"} for number in range(300)}
    scenario.deps.apisession.insight_response = SimpleNamespace(status_code=200, data=payload)
    scenario.invoke("site")
    assert InsightMetricsUtils.get_by_scope("site") == list(payload)
    assert scenario.deps.apisession.requests == [(INSIGHT_URI, {})]
    assert len(scenario.deps.DataExporter.attempts) == 1
    assert len(scenario.deps.DataExporter.attempts[0][1]) == 300


@pytest.mark.parametrize("caller", CALLERS)
def test_missing_insight_cache_ignores_mixed_unrelated_caches(scenario: InsightRefreshScenario, caller: str) -> None:
    """Unrelated fresh, boundary, and expired files must remain unchanged when insight definitions are missing."""
    scenario.seed(missing=True)
    previous = {}
    for index, (name, config) in enumerate(scenario.definitions.items()):
        if name == "insight_metrics":
            continue
        destination = scenario.deps.DataExporter.directory / config.filename
        timestamp = CACHE_CLOCK - (0, 86400, 86401)[index % 3]
        os.utime(destination, (timestamp, timestamp))
        previous[config.filename] = (destination.read_bytes(), destination.stat().st_mtime)
    scenario.reset_records()
    scenario.invoke(caller)
    assert scenario.deps.apisession.requests == [(INSIGHT_URI, {})]
    assert [filename for filename, _, _ in scenario.deps.DataExporter.attempts] == [INSIGHT_FILE]
    assert scenario.cache_accesses() == {INSIGHT_FILE}
    current = {
        name: (
            (scenario.deps.DataExporter.directory / name).read_bytes(),
            (scenario.deps.DataExporter.directory / name).stat().st_mtime,
        )
        for name in previous
    }
    assert current == previous


def test_full_export_continues_after_an_insight_http_failure(scenario: InsightRefreshScenario) -> None:
    """A failed definition must retain full discovery and processing of the remaining definitions."""
    scenario.seed()
    scenario.deps.apisession.insight_response = SimpleNamespace(status_code=503, data={})
    exporter = ConstDefinitionsExporter(scenario.deps.apisession)
    assert exporter.export_all() is None
    assert tuple(exporter.discovered_endpoints) == BASELINE_DEFINITIONS
    assert exporter.endpoints_processed == 28
    assert exporter.endpoints_failed == 1 and exporter.endpoints_updated == 27
    assert len(scenario.deps.apisession.requests) == 31
    assert len(scenario.deps.DataExporter.attempts) == 28
    assert scenario.deps.DataExporter.attempts[-1][0] == "ConstWebhookTopics.csv"


def test_current_attempt_does_not_inherit_an_earlier_failure(scenario: InsightRefreshScenario) -> None:
    """A successful retry must preserve the earlier result without inheriting its failed count."""
    scenario.seed()
    exporter = ConstDefinitionsExporter(scenario.deps.apisession)
    response = SimpleNamespace(status_code=503, data={})
    scenario.deps.apisession.insight_response = response
    first = exporter.export_endpoint("insight_metrics")
    scenario.deps.apisession.insight_response = None
    second = exporter.export_endpoint("insight_metrics")
    assert first.outcome == "failed" and first.http_status == 503
    assert first.first_error.response is response
    assert dict(first.counts) == {"processed": 1, "skipped_fresh": 0, "updated": 0, "failed": 1}
    assert second.outcome == "updated" and second.first_error is None
    assert dict(second.counts) == {"processed": 1, "skipped_fresh": 0, "updated": 1, "failed": 0}
    assert exporter.endpoints_failed == 1 and exporter.endpoints_updated == 1


def test_error_logs_exclude_synthetic_credentials(
    scenario: InsightRefreshScenario, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Failure reports must preserve status and error identity without printing response credentials."""
    scenario.seed()
    synthetic_value = "0123456789abcdef" * 4
    response = SimpleNamespace(
        status_code=503,
        data={"detail": "Definition is unavailable", "apitoken": synthetic_value},
        headers={"Authorization": f"Token {synthetic_value}"},
    )
    scenario.deps.apisession.insight_response = response
    with caplog.at_level(logging.DEBUG):
        result = ConstDefinitionsExporter(scenario.deps.apisession).export_endpoint("insight_metrics")
    assert result.http_status == 503 and result.first_error.response is response
    assert synthetic_value not in caplog.text
    assert synthetic_value not in capsys.readouterr().out
    assert "HTTP 503" in caplog.text
    assert all(record.getMessage().isascii() for record in caplog.records if record.name == const_module.logger.name)


def test_transport_traceback_excludes_synthetic_headers_and_urls(
    scenario: InsightRefreshScenario, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Formatted transport tracebacks must protect credentials without changing the first exception."""
    scenario.seed()
    synthetic_value = "0123456789abcdef" * 4
    message = (
        f"Original transport fault https://name:{synthetic_value}@example.invalid/path?api_token={synthetic_value}\n"
        f"Authorization: Token {synthetic_value}"
    )
    error = requests.ConnectionError(message)
    scenario.deps.apisession.insight_response = error
    with caplog.at_level(logging.DEBUG):
        result = ConstDefinitionsExporter(scenario.deps.apisession).export_endpoint("insight_metrics")
    assert result.first_error is error and result.outcome == "failed"
    assert synthetic_value in str(result.first_error)
    assert synthetic_value not in caplog.text
    assert synthetic_value not in capsys.readouterr().out
    assert "Original transport fault" in caplog.text
    assert "example.invalid" not in caplog.text
    assert result.counts["failed"] == 1 and result.counts["updated"] == 0


@dataclass
class ControlledRefreshBenchmark:
    """Measure actual caller time and verify the recorded controlled comparison."""

    scenario: InsightRefreshScenario
    caller: str

    def measure(self, phase: str, trial: int) -> dict[str, Any]:
        """Time only the original caller entry with the documented response and cache fixtures."""
        self.scenario.seed()
        started = time.perf_counter_ns()
        self.scenario.invoke(self.caller)
        elapsed = (time.perf_counter_ns() - started) / 1_000_000_000
        writer = self.scenario.deps.DataExporter
        return {
            "phase": phase,
            "caller": self.caller,
            "trial": trial,
            "elapsed_seconds": elapsed,
            "requests": len(self.scenario.deps.apisession.requests),
            "writes": len(writer.attempts),
            "completed": len(writer.completed),
            "definitions": self.scenario.deps.exporters[-1].endpoints_processed,
            "cache_files": len(self.scenario.cache_accesses()),
            "latency_seconds": 0.05,
            "fixture": "sdk-0.64.0-one-country-one-gateway",
            "cache_clock": CACHE_CLOCK,
            "cache_age_seconds": 86401,
        }

    def report(self, phase: str, records: list[dict[str, Any]], capsys: pytest.CaptureFixture[str]) -> float:
        """Print every measured trial before checking the required median reduction."""
        median = statistics.median(record["elapsed_seconds"] for record in records)
        capsys.readouterr()
        with capsys.disabled():
            for record in records:
                print("CONTROLLED_OFFLINE " + json.dumps(record, sort_keys=True))
            print(f"CONTROLLED_OFFLINE median caller={self.caller} phase={phase} seconds={median:.6f}")
            if phase == "after":
                reduction = 100 * (1 - median / BEFORE_MEDIANS[self.caller])
                print(
                    f"CONTROLLED_OFFLINE checked={len(records)} caller={self.caller} reduction_percent={reduction:.3f}"
                )
        return median

    def verify(self, phase: str, records: list[dict[str, Any]], median: float) -> None:
        """Check both actual I/O counts and real elapsed time, not a calculated request-count proxy."""
        expected = (31, 28, 28) if phase == "before" else (1, 1, 1)
        assert [(record["requests"], record["writes"], record["definitions"]) for record in records] == [expected] * 5
        assert [record["completed"] for record in records] == [expected[1]] * 5
        assert [record["cache_files"] for record in records] == [expected[2]] * 5
        if phase == "after":
            assert median <= BEFORE_MEDIANS[self.caller] * 0.1


@pytest.mark.parametrize("caller", CALLERS)
def test_controlled_refresh_benchmark(
    scenario: InsightRefreshScenario, caller: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """Measure real refresh elapsed time under identical stale-cache and request-delay conditions."""
    phase = os.environ.get("ISSUE_3300_BENCHMARK_PHASE")
    if phase is None:
        pytest.skip("Set ISSUE_3300_BENCHMARK_PHASE=before or after to run the controlled offline benchmark.")
    assert phase in ("before", "after"), f"Invalid benchmark phase: {phase}"
    scenario.deps.apisession.latency = 0.05
    scenario.seed()
    scenario.invoke(caller)  # Warm imports and filesystem paths outside the measured trials.
    benchmark = ControlledRefreshBenchmark(scenario, caller)
    records = [benchmark.measure(phase, trial) for trial in range(1, 6)]
    median = benchmark.report(phase, records, capsys)
    benchmark.verify(phase, records, median)
