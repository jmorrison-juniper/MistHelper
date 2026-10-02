"""Real selected CSV bytes and SQLite records for native trend documents."""

from __future__ import annotations

import csv
import io
import logging
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any
from unittest.mock import call, patch

import pytest

from src.config import runtime_settings
from src.config.source_dependency_resolver import SourceDependencyResolver
from src.export.endpoint_family_exporter import EndpointFamilyExporter
from src.refactors.main_entrypoint import MainEntrypoint
from tests.unit.export.trend_object_export.conftest import (
    local_trend_context as local_trend_context,
)
from tests.unit.export.trend_object_export.conftest import (
    local_trend_environment as local_trend_environment,
)
from tests.unit.export.trend_object_export.conftest import (
    local_trend_session as local_trend_session,
)
from tests.unit.export.trend_object_export.conftest import (
    native_failure as native_failure,
)
from tests.unit.export.trend_object_export.conftest import (
    native_trend_run as native_trend_run,
)
from tests.unit.export.trend_object_export.conftest import (
    trend_document as trend_document,
)
from tests.unit.export.trend_object_export.conftest import (
    trend_sdk_logging as trend_sdk_logging,
)
from tests.unit.export.trend_object_export.documents import RICH_DOCUMENTS, TrendDocument
from tests.unit.export.trend_object_export.native_transport import (
    NativeBoundaries,
    NativeResponseFactory,
    NativeTrendTransport,
    WireScenario,
)


class SQLiteOutputInspection:
    """Own isolated SQLite configuration and real record inspection."""

    @staticmethod
    def configure(path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Require the exact owned database path before a selected write can begin."""
        monkeypatch.setattr(runtime_settings, "DATABASE_PATH", str(path))
        monkeypatch.setattr(SourceDependencyResolver.root_module(), "DATABASE_PATH", str(path), raising=False)
        monkeypatch.setattr(MainEntrypoint.context, "output_format", "sqlite")
        assert Path(SourceDependencyResolver.DATABASE_PATH).resolve() == path

    @staticmethod
    def records(path: Path, document: TrendDocument) -> list[dict[str, Any]]:
        """Read actual table values without changing its schema or key metadata."""
        table = re.sub(r"[^a-zA-Z0-9_]", "_", document.target.filename.removesuffix(".csv"))
        with closing(sqlite3.connect(path)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(f'SELECT * FROM "{table}" ORDER BY misthelper_internal_id').fetchall()
        return [dict(row) for row in rows]

    @classmethod
    def require_snapshot(cls, path: Path, document: TrendDocument) -> None:
        """Verify the actual second snapshot and its unchanged auto-increment key."""
        rows = cls.records(path, document)
        expected = {key: str(value) for key, value in document.expected.items()}
        assert [{key: row[key] for key in document.expected} for row in rows] == [expected]
        assert [row["misthelper_internal_id"] for row in rows] == [2]
        assert path.stat().st_size >= 4096
        print(
            f"Checked 2 {document.target.operation} SQLite writes, 1 retained record, "
            f"and {path.stat().st_size} output bytes."
        )


class TestSelectedOutput:
    """Measure actual bytes, rows, keys, and repeated-write behavior."""

    @staticmethod
    def _expected_csv(document: TrendDocument) -> bytes:
        """Construct the independent golden bytes with the standard CSV rules."""
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=sorted(document.expected))
        writer.writeheader()
        writer.writerow(document.expected)
        return buffer.getvalue().encode("utf-8")

    @pytest.mark.parametrize("shape", ("canonical", "rich"))
    def test_selected_csv_has_exact_bytes(self, native_trend_run: NativeBoundaries, shape: str) -> None:
        """Each actual selected CSV must contain exactly the expected header and one record."""
        document = native_trend_run.document
        if shape == "rich":
            document = next(case for case in RICH_DOCUMENTS if case.target == document.target)
            native_trend_run.transport.responses[document.target.uri] = NativeResponseFactory.make(
                document.target.uri, WireScenario(200, document.payload)
            )
        EndpointFamilyExporter.site_sle_endpoints()
        expected = self._expected_csv(document)
        path = Path("data") / document.target.filename
        assert path.read_bytes() == expected
        assert path.stat().st_size == len(expected)
        assert native_trend_run.writer.call_args_list == [
            call([document.expected], document.target.filename, api_function_name=document.target.operation)
        ]
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)
        print(f"Checked 1 {document.target.operation} CSV record and {len(expected)} output bytes.")

    @pytest.mark.parametrize("shape", ("canonical", "rich"))
    def test_selected_sqlite_keeps_existing_autoincrement_behavior(
        self, native_trend_run: NativeBoundaries, shape: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Real repeated writes keep the existing snapshot replacement without synthetic context or keys."""
        document = native_trend_run.document
        if shape == "rich":
            document = next(case for case in RICH_DOCUMENTS if case.target == document.target)
            native_trend_run.transport.responses[document.target.uri] = NativeResponseFactory.make(
                document.target.uri, WireScenario(200, document.payload)
            )
        path = Path("data").resolve() / "issue3699.sqlite"
        SQLiteOutputInspection.configure(path, monkeypatch)
        for _repeat in range(2):
            with patch("builtins.input", side_effect=document.target.answers):
                EndpointFamilyExporter.site_sle_endpoints()
        SQLiteOutputInspection.require_snapshot(path, document)
        assert (
            native_trend_run.writer.call_args_list
            == [call([document.expected], document.target.filename, api_function_name=document.target.operation)] * 2
        )
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document) * 2
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    def test_failure_modes_preserve_actual_previous_csv_bytes(
        self, native_trend_run: NativeBoundaries, native_failure: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A real failure cannot call the selected writer or replace prior bytes."""
        document = native_trend_run.document
        path = Path("data") / document.target.filename
        previous = self._expected_csv(document)
        path.write_bytes(previous)
        EndpointFamilyExporter.site_sle_endpoints()
        assert path.read_bytes() == previous
        assert path.stat().st_size == len(previous)
        assert native_trend_run.writer.call_args_list == []
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert "Error running" in caplog.text and document.target.operation in caplog.text
        assert "source-body-marker-3699" not in caplog.text and "credential-marker-3699" not in caplog.text
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)

    @pytest.mark.parametrize("status", (403, 503))
    def test_http_status_failures_preserve_actual_previous_csv_bytes(
        self, native_trend_run: NativeBoundaries, status: int, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Concrete client and server refusals preserve the exact prior output bytes."""
        document = native_trend_run.document
        path = Path("data") / document.target.filename
        previous = self._expected_csv(document)
        path.write_bytes(previous)
        native_trend_run.transport.responses[document.target.uri] = NativeResponseFactory.make(
            document.target.uri, WireScenario(status=status, body={"error": "source-body-marker-3699"})
        )
        with caplog.at_level(logging.DEBUG, logger="src.export.endpoint_family_response.reader"):
            EndpointFamilyExporter.site_sle_endpoints()
        assert native_trend_run.transport.decoded[-1].status_code == status
        assert path.read_bytes() == previous
        assert native_trend_run.writer.call_args_list == []
        assert native_trend_run.transport.calls == NativeTrendTransport.expected_calls(document)
        assert f"HTTP {status}" in caplog.text and "source-body-marker-3699" not in caplog.text
        assert (native_trend_run.network.call_count, native_trend_run.router.call_count) == (0, 0)
