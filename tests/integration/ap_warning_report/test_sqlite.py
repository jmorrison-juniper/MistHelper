"""Verify natural-key replacement through the actual report and SQLite writer."""

import sqlite3
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from src.foundation.models.data.data_processing_utils import DataProcessingUtils
from src.foundation.persistence.db.database_schema_utils import DatabaseSchemaUtils
from src.operations.exporting.ap_warning_report.operation import ApWarningReport
from src.operations.exporting.export.data_exporter import DataExporter

ORG_ID = "00000000-0000-0000-0000-000000000001"


def test_repeated_export_updates_ap_without_duplicates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Two reads of one AP replace its evidence while preserving another AP."""
    monkeypatch.chdir(tmp_path)
    database = tmp_path / "report.db"
    dependencies = SimpleNamespace(
        DatabaseSchemaUtils=DatabaseSchemaUtils,
        DataProcessingUtils=DataProcessingUtils,
        misthelper_module=SimpleNamespace(DATABASE_PATH=str(database)),
    )
    runtime = SimpleNamespace(
        ConfigUtils=SimpleNamespace(get_cached_or_prompted_org_id=lambda: ORG_ID),
        apisession=Mock(),
        DataExporter=DataExporter,
    )
    sources = {
        "definitions": [{"code": "03", "key": "DHCP", "name": "DHCP error", "description": "No DHCP response"}],
        "sites": [],
        "inventory": [{"mac": "000000000001"}, {"mac": "000000000002"}],
        "stats": [
            {"mac": "000000000001", "last_trouble": {"code": "03"}},
            {"mac": "000000000002", "last_trouble": {"code": "03"}},
        ],
    }
    with (
        patch("src.operations.exporting.ap_warning_report.operation.SourceDependencyResolver", runtime),
        patch("src.operations.exporting.ap_warning_report.operation.ApWarningClient") as client,
        patch(
            "src.operations.exporting.export.data_exporter.SourceDependencyResolver",
            SimpleNamespace(OUTPUT_FORMAT="sqlite"),
        ),
        patch(
            "src.foundation.support.refactors.sqlite_database_writer._resolve_runtime_dependencies",
            return_value=dependencies,
        ),
        patch.object(DataExporter, "_route_to_polyglot", return_value=SimpleNamespace(written=True)),
    ):
        client.return_value.read.return_value = sources
        assert ApWarningReport.run() == 2
        sources["stats"][0]["last_trouble"] = {"code": "99"}
        assert ApWarningReport.run() == 2
    with closing(sqlite3.connect(database)) as connection:
        rows = connection.execute(
            "SELECT org_id, mac, code FROM ApWarningReport_00000000_0000_0000_0000_000000000001 ORDER BY mac"
        ).fetchall()
    assert rows == [(ORG_ID, "000000000001", "99"), (ORG_ID, "000000000002", "03")]


@pytest.mark.parametrize(
    "response",
    [
        SimpleNamespace(status_code=200, data=None, raw_data="", next=None),
        SimpleNamespace(status_code=200, data={}, raw_data="bad json", next=None),
    ],
    ids=["empty_body", "malformed_json"],
)
def test_empty_body_and_malformed_json_block_sqlite_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, response: SimpleNamespace
) -> None:
    """Broken SDK bodies must fail before the real SQLite export boundary."""
    monkeypatch.chdir(tmp_path)
    runtime = SimpleNamespace(
        ConfigUtils=SimpleNamespace(get_cached_or_prompted_org_id=lambda: ORG_ID),
        apisession=Mock(),
        DataExporter=DataExporter,
    )
    with (
        patch("src.operations.exporting.ap_warning_report.operation.SourceDependencyResolver", runtime),
        patch(
            "src.operations.exporting.export.data_exporter.SourceDependencyResolver",
            SimpleNamespace(OUTPUT_FORMAT="sqlite"),
        ),
        patch("mistapi.api.v1.const.ap_led_status.listApLedDefinition", return_value=response),
        patch.object(
            DataExporter, "write_with_format_selection", wraps=DataExporter.write_with_format_selection
        ) as writer,
        pytest.raises(RuntimeError, match="AP warning report failed"),
    ):
        ApWarningReport.run()
    writer.assert_not_called()
    assert not (tmp_path / "data").exists()
