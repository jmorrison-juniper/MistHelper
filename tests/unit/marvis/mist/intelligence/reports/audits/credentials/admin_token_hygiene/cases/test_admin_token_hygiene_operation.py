"""Unit tests for the admin token hygiene operation."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.mist.intelligence.reports.admin_token_hygiene.operation import AdminTokenHygieneReport


@dataclass
class FakeClient:
    """Fake client with deterministic admin, token, and setting rows."""

    apisession: Any
    org_id: str

    def list_admins(self) -> list[dict[str, Any]]:
        """Return one Super User admin."""
        return [{"email": "admin@example.net", "privileges": [{"role": "superuser", "scope": "org"}]}]

    def list_tokens(self) -> list[dict[str, Any]]:
        """Return one never-used token with a sentinel key."""
        return [{"id": "tok-1", "name": "robot", "created_time": 1_700_000_000, "key": "SECRET-SENTINEL"}]

    def get_settings(self) -> dict[str, Any]:
        """Return minimal organization settings."""
        return {"password_policy": {"enabled": True}}


class FakeConfigUtils:
    """Fake organization resolver."""

    @staticmethod
    def get_cached_or_prompted_org_id() -> str:
        """Return a fixed organization identifier."""
        return "org-1"


class FakeDataExporter:
    """Fake exporter that captures write calls."""

    calls: list[tuple[list[dict[str, Any]], str, str, list[str] | None]] = []

    @classmethod
    def write_with_format_selection(
        cls,
        rows: list[dict[str, Any]],
        filename: str,
        api_function_name: str,
        fieldnames: list[str] | None = None,
    ) -> bool:
        """Capture rows passed to the shared exporter."""
        cls.calls.append((rows, filename, api_function_name, fieldnames))
        path = Path("data") / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return True


class FakeResolver:
    """Fake resolver for operation tests."""

    apisession = object()
    ConfigUtils = FakeConfigUtils
    DataExporter = FakeDataExporter


class TestReport(AdminTokenHygieneReport):
    """Report class wired to fakes."""

    resolver = FakeResolver
    client_class = FakeClient


def test_operation_exports_both_reports_without_prompt(tmp_path: Path, monkeypatch: Any) -> None:
    """The operation must export both reports and avoid prompts."""
    monkeypatch.chdir(tmp_path)
    FakeDataExporter.calls = []
    TestReport.run()
    filenames = {call[1] for call in FakeDataExporter.calls}
    assert filenames == {"AdminHygiene.csv", "TokenHygiene.csv"}
    token_rows = [call[0] for call in FakeDataExporter.calls if call[1] == "TokenHygiene.csv"][0]
    token_file = (tmp_path / "data" / "TokenHygiene.csv").read_text(encoding="utf-8")
    assert "SECRET-SENTINEL" not in str(token_rows)
    assert "SECRET-SENTINEL" not in token_file


def test_operation_writes_empty_headers_when_sources_are_empty(tmp_path: Path, monkeypatch: Any) -> None:
    """Empty source data must still create both CSV files with headers."""

    class EmptyClient(FakeClient):
        """Fake client with no admins or tokens."""

        def list_admins(self) -> list[dict[str, Any]]:
            """Return no admins."""
            return []

        def list_tokens(self) -> list[dict[str, Any]]:
            """Return no tokens."""
            return []

    class EmptyReport(TestReport):
        """Report class with empty source data."""

        client_class = EmptyClient

    monkeypatch.chdir(tmp_path)
    FakeDataExporter.calls = []
    EmptyReport.run()
    admin_header = (tmp_path / "data" / "AdminHygiene.csv").read_text(encoding="utf-8").splitlines()[0]
    token_header = (tmp_path / "data" / "TokenHygiene.csv").read_text(encoding="utf-8").splitlines()[0]
    assert admin_header.startswith("admin_id,email,name")
    assert token_header.startswith("id,name,created_by")
