"""Operation tests for destructive CSV import behavior."""

from __future__ import annotations  # WHY: keep annotations lazy for pytest.

import csv  # WHY: create input files and inspect the audit log.
import logging  # WHY: caplog checks for passphrase leakage.
from pathlib import Path  # WHY: build repository-local test paths safely.
from typing import Any  # WHY: dependency and response doubles are dynamic.

from src.inventory.csv_imports.client import CsvImportClient  # WHY: satisfy dependency type annotations.
from src.inventory.csv_imports.operation import CsvImportDependencies, CsvImportOperation, CsvImportOptions

RUNTIME_DIR = Path("tests") / "unit" / "inventory" / "csv_imports" / "_runtime_data"  # WHY: avoid temp dirs.


class ResponseDouble:
    """Small SDK response double for operation tests."""

    status_code = 200  # WHY: operation result summary can read this safe status.


class RecordingClient(CsvImportClient):
    """Client double that records send calls without network access."""

    sent: list[tuple[str, str, Path]] = []  # WHY: tests assert when a request was or was not sent.

    def __init__(self, session: Any) -> None:
        """Create the client double."""
        self._session = session  # WHY: keep the same constructor shape as the real client.

    def send(self, definition: Any, scope_id: str, file_path: Path) -> ResponseDouble:
        """Record the request shape and return success."""
        self.sent.append((definition.key, scope_id, file_path))  # WHY: no network runs in unit tests.
        return ResponseDouble()  # WHY: operation expects an SDK-like response.


def _write_csv(name: str, rows: list[dict[str, str]], fieldnames: list[str]) -> Path:
    """Write a CSV input file under the repository test directory."""
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)  # WHY: all scratch files stay inside the worktree.
    path = RUNTIME_DIR / name  # WHY: dependency path resolver maps data file names here.
    with path.open("w", newline="", encoding="utf-8") as csv_file:  # WHY: create the exact input format.
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)  # WHY: tests choose valid or invalid headers.
        writer.writeheader()  # WHY: parser validates required columns from the header.
        writer.writerows(rows)  # WHY: row count drives the confirmation phrase.
    return path  # WHY: tests clean up this file after the run.


def _remove_runtime_files() -> None:
    """Remove files created by operation tests."""
    if not RUNTIME_DIR.exists():  # WHY: nothing to remove on first-run failures.
        return  # WHY: avoid raising while cleaning.
    for path in RUNTIME_DIR.glob("*.csv"):  # WHY: remove only CSV files created by these tests.
        path.unlink()  # WHY: leave the worktree clean after each test.


def _deps() -> CsvImportDependencies:
    """Return operation dependencies that stay in the test directory."""

    def get_csv_path(file_name: str) -> str:
        return str(RUNTIME_DIR / file_name)  # WHY: emulate data/ without writing outside the repo.

    return CsvImportDependencies(  # WHY: build a complete dependency bundle for the operation.
        session="session",
        get_csv_path=get_csv_path,
        safe_input=lambda prompt, context: "IMPORT 1",
        get_org_id=lambda: "org-id",
        client_factory=RecordingClient,
    )


def test_csv_imports_operation_dry_run_sends_no_request() -> None:
    """Dry run writes an audit row and skips the client."""
    _remove_runtime_files()  # WHY: start from a clean local scratch directory.
    RecordingClient.sent = []  # WHY: isolate this test from earlier calls.
    _write_csv("import_org_assets.csv", [{"name": "asset1", "mac": "001122334455"}], ["name", "mac"])
    options = CsvImportOptions(import_key="org_assets", dry_run=True, confirmation="IMPORT 1", scope_id="org-id")
    CsvImportOperation.run(options=options, deps=_deps())  # WHY: execute the dry-run path.
    assert RecordingClient.sent == []  # WHY: dry run must not send a Mist request.
    log_path = RUNTIME_DIR / "CsvImportLog.csv"  # WHY: operation writes the audit log through get_csv_path.
    assert "dry_run" in log_path.read_text(encoding="utf-8")  # WHY: audit log must show the safe mode.
    _remove_runtime_files()  # WHY: leave no scratch files.


def test_csv_imports_operation_wrong_confirmation_sends_no_request() -> None:
    """A row-count mismatch stops before the client."""
    _remove_runtime_files()  # WHY: start from a clean local scratch directory.
    RecordingClient.sent = []  # WHY: isolate this test from earlier calls.
    _write_csv("import_org_assets.csv", [{"name": "asset1", "mac": "001122334455"}], ["name", "mac"])
    options = CsvImportOptions(import_key="org_assets", dry_run=False, confirmation="IMPORT 2", scope_id="org-id")
    CsvImportOperation.run(options=options, deps=_deps())  # WHY: execute the confirmation gate.
    assert RecordingClient.sent == []  # WHY: mismatch must not send a Mist request.
    assert "confirmation_mismatch" in (RUNTIME_DIR / "CsvImportLog.csv").read_text(encoding="utf-8")
    _remove_runtime_files()  # WHY: leave no scratch files.


def test_csv_imports_operation_missing_required_column_stops_request() -> None:
    """A missing column stops before confirmation and request."""
    _remove_runtime_files()  # WHY: start from a clean local scratch directory.
    RecordingClient.sent = []  # WHY: isolate this test from earlier calls.
    _write_csv("import_org_psks.csv", [{"name": "psk1", "ssid": "ssid1"}], ["name", "ssid"])
    options = CsvImportOptions(import_key="org_psks", dry_run=False, confirmation="IMPORT 1", scope_id="org-id")
    CsvImportOperation.run(options=options, deps=_deps())  # WHY: execute validation before confirmation.
    assert RecordingClient.sent == []  # WHY: validation failure must not send a Mist request.
    assert "Missing required column: passphrase" in (RUNTIME_DIR / "CsvImportLog.csv").read_text(encoding="utf-8")
    _remove_runtime_files()  # WHY: leave no scratch files.


def test_csv_imports_operation_missing_file_stops_request() -> None:
    """A missing input file stops before any request."""
    _remove_runtime_files()  # WHY: start from a clean local scratch directory.
    RecordingClient.sent = []  # WHY: isolate this test from earlier calls.
    options = CsvImportOptions(
        import_key="site_assets", dry_run=False, confirmation="IMPORT 1", scope_id="site-id"
    )  # WHY: select a missing file.
    CsvImportOperation.run(options=options, deps=_deps())  # WHY: execute the missing-file guard.
    assert RecordingClient.sent == []  # WHY: no file means no Mist request can be valid.
    assert not (RUNTIME_DIR / "CsvImportLog.csv").exists()  # WHY: no parsed row count exists for the audit log.


def test_csv_imports_operation_does_not_log_psk_passphrase(caplog: Any) -> None:
    """PSK passphrases do not appear in log records."""
    _remove_runtime_files()  # WHY: start from a clean local scratch directory.
    RecordingClient.sent = []  # WHY: isolate this test from earlier calls.
    _write_csv(
        "import_site_psks.csv",
        [{"name": "psk1", "ssid": "ssid1", "passphrase": "secret-psk-value"}],
        ["name", "ssid", "passphrase"],
    )
    caplog.set_level(logging.DEBUG)  # WHY: inspect debug logs as well as info logs.
    options = CsvImportOptions(import_key="site_psks", dry_run=False, confirmation="IMPORT 1", scope_id="site-id")
    CsvImportOperation.run(options=options, deps=_deps())  # WHY: execute the live path through the client double.
    assert RecordingClient.sent == [("site_psks", "site-id", RUNTIME_DIR / "import_site_psks.csv")]
    assert "secret-psk-value" not in caplog.text  # WHY: no log line may contain a passphrase.
    assert "secret-psk-value" not in (RUNTIME_DIR / "CsvImportLog.csv").read_text(
        encoding="utf-8"
    )  # WHY: audit log is safe.
    _remove_runtime_files()  # WHY: leave no scratch files.
