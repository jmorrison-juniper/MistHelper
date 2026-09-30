"""Client contract tests for the CSV import file-upload calls."""

from __future__ import annotations  # WHY: keep annotations lazy for pytest startup.

from pathlib import Path  # WHY: pass a path object through the client seam.
from typing import Any  # WHY: response and session doubles are dynamic.

import pytest  # WHY: parameterize one contract test per supported import type.

from src.inventory.csv_imports.client import (  # WHY: test the request dispatch layer and status summaries.
    CsvImportClient,
    CsvImportResponseSummary,
)
from src.inventory.csv_imports.model import CsvImportCatalog  # WHY: use production import definitions.


class ResponseDouble:
    """Small SDK response double with a status code."""

    status_code = 200  # WHY: response summary can read this safe status value.


class StatusResponseDouble:
    """Small SDK response double with a configurable status code."""

    def __init__(self, status_code: int) -> None:
        """Store the HTTP status code for summary tests."""
        self.status_code = status_code  # WHY: tests need explicit 4xx and 5xx statuses.


@pytest.mark.parametrize("definition", CsvImportCatalog.DEFINITIONS)  # WHY: report one contract per import type.
def test_csv_imports_client_sends_multipart_shape_per_type(definition: Any) -> None:
    """Each supported import type calls the matching SDK file function shape."""
    calls_seen: list[tuple[str, Any, str, str]] = []  # WHY: collect operation, session, scope, and file path.

    def make_call(operation_id: str) -> Any:
        """Return one SDK call double for an operation."""

        def _call(session: Any, scope_id: str, file: str) -> ResponseDouble:
            calls_seen.append((operation_id, session, scope_id, file))  # WHY: record the request shape.
            return ResponseDouble()  # WHY: caller expects an SDK-like response object.

        return _call  # WHY: each operation ID gets its own recorder.

    call_map = {item.operation_id: make_call(item.operation_id) for item in CsvImportCatalog.DEFINITIONS}
    client = CsvImportClient(session="session", calls=call_map)  # WHY: inject all SDK call doubles.
    file_path = Path("data") / "import.csv"  # WHY: path conversion is part of the contract.
    response = client.send(definition, "scope-id", file_path)  # WHY: send through production dispatch.
    assert response.status_code == 200  # WHY: response double returned through the client.
    assert len(calls_seen) == 1  # WHY: this parameter case must send one request.
    assert calls_seen[0][0] == definition.operation_id  # WHY: dispatch must match the selected operation.
    assert {call[2] for call in calls_seen} == {"scope-id"}  # WHY: scope id passes through unchanged.
    assert {call[3] for call in calls_seen} == {str(file_path)}  # WHY: SDK receives a string file path.


def test_csv_imports_client_summarizes_4xx_response_status() -> None:
    """A client-side HTTP failure is preserved as a safe status summary."""
    response = StatusResponseDouble(400)  # WHY: use a 4xx response without a live API call.
    summary = CsvImportResponseSummary.summarize(response)  # WHY: operation logs this sanitized summary.
    assert summary == "request_sent_status_400"  # WHY: preserve the 4xx status without response row data.


def test_csv_imports_client_summarizes_5xx_response_status() -> None:
    """A server-side HTTP failure is preserved as a safe status summary."""
    response = StatusResponseDouble(500)  # WHY: use a 5xx response without a live API call.
    summary = CsvImportResponseSummary.summarize(response)  # WHY: operation logs this sanitized summary.
    assert summary == "request_sent_status_500"  # WHY: preserve the 5xx status without response row data.
