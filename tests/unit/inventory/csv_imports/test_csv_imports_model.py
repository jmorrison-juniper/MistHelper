"""Unit tests for the CSV import model."""

from __future__ import annotations  # WHY: keep annotations lazy for the test runner.

import csv  # WHY: write realistic CSV files for parser tests.
from pathlib import Path  # WHY: build test paths with Windows-safe separators.

from src.inventory.csv_imports.model import (  # WHY: test pure validation and masking logic.
    MASK,
    CsvImportCatalog,
    CsvImportConfirmation,
    CsvImportReader,
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


def test_csv_imports_model_accepts_exact_import_count() -> None:
    """The destructive phrase must match the reviewed row count."""
    assert CsvImportConfirmation.is_confirmed("IMPORT 3", 3) is True  # WHY: exact phrase permits the request.
    assert CsvImportConfirmation.is_confirmed("IMPORT 2", 3) is False  # WHY: wrong count blocks the request.
    assert CsvImportConfirmation.is_confirmed("import 3", 3) is False  # WHY: lower case must not pass.
