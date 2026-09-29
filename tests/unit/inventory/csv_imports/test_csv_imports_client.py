"""Client contract tests for the CSV import file-upload calls."""

from __future__ import annotations  # WHY: keep annotations lazy for pytest startup.

from pathlib import Path  # WHY: pass a path object through the client seam.
from typing import Any  # WHY: response and session doubles are dynamic.

from src.inventory.csv_imports.client import CsvImportClient  # WHY: test the request dispatch layer.
from src.inventory.csv_imports.model import CsvImportCatalog  # WHY: use production import definitions.


class ResponseDouble:
    """Small SDK response double with a status code."""

    status_code = 200  # WHY: response summary can read this safe status value.


def test_csv_imports_client_sends_each_multipart_shape() -> None:
    """Each supported import type calls the matching SDK file function shape."""
    calls_seen: list[tuple[str, Any, str, str]] = []  # WHY: collect operation, session, scope, and file path.

    def make_call(operation_id: str) -> Any:
        """Return one SDK call double for an operation."""

        def _call(session: Any, scope_id: str, file: str) -> ResponseDouble:
            calls_seen.append((operation_id, session, scope_id, file))  # WHY: record the request shape.
            return ResponseDouble()  # WHY: caller expects an SDK-like response object.

        return _call  # WHY: each operation ID gets its own recorder.

    call_map = {
        definition.operation_id: make_call(definition.operation_id) for definition in CsvImportCatalog.DEFINITIONS
    }
    client = CsvImportClient(session="session", calls=call_map)  # WHY: inject all SDK call doubles.
    file_path = Path("data") / "import.csv"  # WHY: path conversion is part of the contract.
    for definition in CsvImportCatalog.DEFINITIONS:  # WHY: one contract check for each import type.
        response = client.send(definition, "scope-id", file_path)  # WHY: send through production dispatch.
        assert response.status_code == 200  # WHY: response double returned through the client.
    assert len(calls_seen) == len(CsvImportCatalog.DEFINITIONS)  # WHY: every import type must send once.
    assert {call[0] for call in calls_seen} == {item.operation_id for item in CsvImportCatalog.DEFINITIONS}
    assert {call[2] for call in calls_seen} == {"scope-id"}  # WHY: scope id passes through unchanged.
    assert {call[3] for call in calls_seen} == {str(file_path)}  # WHY: SDK receives a string file path.
