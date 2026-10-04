"""Unit tests for the CSV import model."""

from __future__ import annotations  # WHY: keep annotations lazy for the test runner.

import csv  # WHY: write realistic CSV files for parser tests.
from pathlib import Path  # WHY: build test paths with Windows-safe separators.

from src.mist.resources.inventory.csv_imports.model import (  # WHY: test pure validation and masking logic.
    MASK,
    CsvImportCatalog,
    CsvImportConfirmation,
    CsvImportReader,
    CsvImportResult,
    CsvImportSanitizer,
    CsvImportValidator,
)

RUNTIME_DIR = Path("tests") / "unit" / "inventory" / "csv_imports" / "_runtime_data"  # WHY: avoid temp dirs.


def _write_csv(name: str, rows: list[dict[str, str]], fieldnames: list[str]) -> Path:
    """Write a CSV file under the repository test data directory."""
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)  # WHY: keep all scratch files inside the worktree.
    path = RUNTIME_DIR / name  # WHY: each test uses a named file for clear failure messages.
    with path.open("w", newline="", encoding="utf-8") as csv_file:  # WHY: write the CSV parser input.
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)  # WHY: control header order in each test.
        writer.writeheader()  # WHY: CsvImportReader validates the header row.
        writer.writerows(rows)  # WHY: test data must include real rows.
    return path  # WHY: callers pass the path to CsvImportReader.


def test_csv_imports_model_names_missing_required_column() -> None:
    """A missing required column is reported before a request can run."""
    definition = CsvImportCatalog.by_key("org_psks")  # WHY: PSK imports require passphrase.
    path = _write_csv("missing_passphrase.csv", [{"name": "k1", "ssid": "ssid1"}], ["name", "ssid"])
    batch = CsvImportReader.read(definition, path)  # WHY: parse the same way the operation parses files.
    missing = CsvImportValidator.missing_columns(batch)  # WHY: collect blocking schema defects.
    assert missing == ("passphrase",)  # WHY: the operator must see the exact missing column.
    path.unlink()  # WHY: leave no scratch CSV after the test.


def test_csv_imports_model_masks_psk_passphrase() -> None:
    """PSK previews mask the passphrase value."""
    definition = CsvImportCatalog.by_key("site_psks")  # WHY: site PSKs share the secret column contract.
    row = {"name": "k1", "ssid": "ssid1", "passphrase": "secret-psk-value"}  # WHY: unique secret proves masking.
    sanitized = CsvImportSanitizer.sanitize_row(definition, row)  # WHY: preview must call the sanitizer.
    assert sanitized["passphrase"] == MASK  # WHY: the secret cannot reach logs or preview output.
    assert "secret-psk-value" not in str(sanitized)  # WHY: no representation may include the secret.


def test_csv_imports_model_preview_is_limited_to_ten_rows() -> None:
    """The preview returns only the first ten rows."""
    definition = CsvImportCatalog.by_key("org_assets")  # WHY: asset rows have no secret columns.
    rows = [
        {"name": f"asset{index}", "mac": f"0011223344{index:02d}"} for index in range(12)
    ]  # WHY: exceed preview limit.
    path = _write_csv("preview_limit.csv", rows, ["name", "mac"])  # WHY: create more than ten rows.
    batch = CsvImportReader.read(definition, path)  # WHY: preview uses parsed production batches.
    preview = CsvImportSanitizer.preview_rows(batch)  # WHY: call the preview helper under test.
    assert len(preview) == 10  # WHY: the operator preview must stop at ten rows.
    assert preview[-1]["name"] == "asset9"  # WHY: the preview must keep the original row order.
    path.unlink()  # WHY: leave no scratch CSV after the test.


def test_csv_imports_model_result_row_uses_safe_fields() -> None:
    """The audit result row contains only the safe result columns."""
    result = CsvImportResult("org_psks", 1, False, "sent", "request_sent_status_200")  # WHY: use a safe status.
    row = result.as_row()  # WHY: the operation writes this dictionary to CsvImportLog.csv.
    assert set(row) == set(CsvImportResult.column_names())  # WHY: no row data or secret column can appear.
    assert "passphrase" not in row  # WHY: the audit row must not reserve a secret column.


def test_csv_imports_model_accepts_exact_import_count() -> None:
    """The destructive phrase must match the reviewed row count."""
    assert CsvImportConfirmation.is_confirmed("IMPORT 3", 3) is True  # WHY: exact phrase permits the request.
    assert CsvImportConfirmation.is_confirmed("IMPORT 2", 3) is False  # WHY: wrong count blocks the request.
    assert CsvImportConfirmation.is_confirmed("import 3", 3) is False  # WHY: lower case must not pass.
