"""Tests for the client fingerprint census operation."""

from __future__ import annotations  # WHY: keep annotations consistent.

from pathlib import Path  # WHY: inspect wiring files without hard-coded separators.
from typing import Any  # WHY: fakes capture exporter values of multiple types.

import pytest  # WHY: use monkeypatch and log capture fixtures.
from pytest import LogCaptureFixture, MonkeyPatch  # WHY: type pytest fixtures used here.

from src.reports.client_fingerprint_census import operation as operation_module
from src.reports.client_fingerprint_census.model import EMPTY_CENSUS_MESSAGE, FingerprintCensusRow
from src.reports.client_fingerprint_census.operation import ClientFingerprintCensus


class _FakeClient:
    """Fake API client used by operation tests."""

    rows: list[dict[str, object]] = []  # WHY: each test controls the API response rows.
    calls: list[tuple[str, str]] = []  # WHY: tests assert that the API call happened once.

    def __init__(self, session: object) -> None:
        """Store the fake session for completeness."""
        self.session = session  # WHY: mirror the real client constructor.

    def count(self, site_id: str, distinct: str) -> list[dict[str, object]]:
        """Return the configured fake API rows."""
        self.calls.append((site_id, distinct))  # WHY: record the call contract.
        return self.rows  # WHY: operation passes these rows to the model.


def test_run_prompts_calls_exports_and_prints_top_20(monkeypatch: MonkeyPatch, caplog: LogCaptureFixture) -> None:
    """Assert that a populated run prompts, calls, exports, and prints top rows."""
    exported: dict[str, Any] = {}  # WHY: capture exporter arguments.
    _FakeClient.rows = [{"property": f"value-{index}", "count": index} for index in range(25)]  # WHY: 25 rows.
    _FakeClient.calls = []  # WHY: start each test with no call history.

    def fake_export(rows: list[dict[str, str | int]], filename: str, **kwargs: Any) -> bool:
        exported["rows"] = rows  # WHY: assert CSV payload.
        exported["filename"] = filename  # WHY: assert stable report name.
        exported["kwargs"] = kwargs  # WHY: assert endpoint and field names.
        return True  # WHY: simulate a successful write.

    monkeypatch.setattr(ClientFingerprintCensus, "_resolve_site", staticmethod(lambda: ("site-1", "HQ")))  # WHY.
    monkeypatch.setattr(ClientFingerprintCensus, "_prompt_distinct", staticmethod(lambda: "family"))  # WHY.
    monkeypatch.setattr(operation_module, "ClientFingerprintCensusClient", _FakeClient)  # WHY: no network.
    monkeypatch.setattr(operation_module.SourceDependencyResolver, "apisession", object())  # WHY: fake session.
    monkeypatch.setattr(  # WHY: replace the shared exporter with a capture fake.
        operation_module.SourceDependencyResolver.DataExporter,
        "write_with_format_selection",
        fake_export,
    )
    caplog.set_level("INFO")  # WHY: capture console table rows written through logging.

    ClientFingerprintCensus.run()  # WHY: exercise the full operation path.

    assert _FakeClient.calls == [("site-1", "family")]  # WHY: one API call with selected values.
    assert exported["filename"] == "ClientFingerprintCensus.csv"  # WHY: acceptance names this file.
    assert exported["kwargs"]["api_function_name"] == "countOrgClientFingerprints"  # WHY: OpenAPI operation ID.
    assert exported["kwargs"]["fieldnames"] == FingerprintCensusRow.column_names()  # WHY: headers are explicit.
    assert len(exported["rows"]) == 25  # WHY: export writes all rows, not only the display rows.
    assert "value-24" in caplog.text  # WHY: highest count appears in the table.
    assert "value-4" not in caplog.text  # WHY: only the top 20 rows are printed.


def test_run_empty_response_writes_header_only_and_message(
    monkeypatch: MonkeyPatch,
    caplog: LogCaptureFixture,
) -> None:
    """Assert that an empty response writes headers and reports the empty census."""
    exported: dict[str, Any] = {}  # WHY: capture exporter arguments.
    _FakeClient.rows = []  # WHY: simulate an empty Mist response.
    _FakeClient.calls = []  # WHY: reset call history.

    def fake_export(rows: list[dict[str, str | int]], filename: str, **kwargs: Any) -> bool:
        exported["rows"] = rows  # WHY: verify header-only payload has no rows.
        exported["filename"] = filename  # WHY: verify stable report name.
        exported["kwargs"] = kwargs  # WHY: verify explicit field names.
        return True  # WHY: simulate a successful write.

    monkeypatch.setattr(ClientFingerprintCensus, "_resolve_site", staticmethod(lambda: ("site-1", "HQ")))  # WHY.
    monkeypatch.setattr(ClientFingerprintCensus, "_prompt_distinct", staticmethod(lambda: "os_type"))  # WHY.
    monkeypatch.setattr(operation_module, "ClientFingerprintCensusClient", _FakeClient)  # WHY: no network.
    monkeypatch.setattr(operation_module.SourceDependencyResolver, "apisession", object())  # WHY: fake session.
    monkeypatch.setattr(  # WHY: replace the shared exporter with a capture fake.
        operation_module.SourceDependencyResolver.DataExporter,
        "write_with_format_selection",
        fake_export,
    )
    caplog.set_level("INFO")  # WHY: capture empty-state operator message.

    ClientFingerprintCensus.run()  # WHY: exercise the empty path.

    assert exported["rows"] == []  # WHY: a header-only file passes no data rows.
    assert exported["kwargs"]["fieldnames"] == FingerprintCensusRow.column_names()  # WHY: headers still write.
    assert EMPTY_CENSUS_MESSAGE in caplog.text  # WHY: acceptance requires this clear message.


def test_wiring_manifest_defers_shared_file_registration() -> None:
    """Assert that the wiring manifest contains the required integration data."""
    repo_root = Path(__file__).resolve().parents[4]  # WHY: pytest can run from a changed current directory.
    wiring_path = repo_root / "specs" / "3569-client-fingerprint-census" / "wiring.md"  # WHY: contract path.
    if not wiring_path.exists():  # WHY: fail clearly until the task creates the manifest.
        pytest.fail("wiring.md is missing")  # WHY: acceptance requires the wiring manifest.
    wiring_text = wiring_path.read_text(encoding="utf-8")  # WHY: inspect the integration contract.
    assert "| 289 |" in wiring_text  # WHY: menu number is pre-assigned.
    assert "interactive_safe" in wiring_text  # WHY: category must match the site prompt behavior.
    assert "site prompt" in wiring_text  # WHY: skip reason must name the site prompt.
    assert "countOrgClientFingerprints" in wiring_text  # WHY: primary key strategy uses the OpenAPI operation ID.
    assert '"type": "composite_pk"' in wiring_text  # WHY: integration must use a natural business key.
    assert '"primary_key": ["site_id", "distinct", "value"]' in wiring_text  # WHY: avoid artificial IDs.
    assert "README update" in wiring_text  # WHY: integration owns the shared README menu table.
    assert "ClientFingerprintCensus.run" in wiring_text  # WHY: integration needs the handler attribute.
