"""Verify that the portal exposes the read-only AP warning export."""

import csv
import logging
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from flask.testing import FlaskClient

import MistHelper
from src.operations.exporting.export.data_exporter import DataExporter
from web_portal.services.operation import OperationExecutor


def test_ap_warning_report_is_listed_in_a_named_group(client: FlaskClient) -> None:
    """The fallback portal must expose menu 307 without a cloud session."""
    response = client.get("/api/operations/list")
    assert response.status_code == 200
    groups = response.get_json()["categories"]
    reports = next(group for group in groups if group["name"] == "AP Warning Reports")
    assert [operation["menu_number"] for operation in reports["operations"]] == ["307"]
    assert reports["operations"][0]["description"] == "Export AP warning and error codes across all sites"


def test_ap_warning_report_needs_no_additional_controls(client: FlaskClient) -> None:
    """The report uses the selected organization and standard export controls."""
    response = client.get("/api/operations/parameters/307")
    assert response.status_code == 200
    assert response.get_json()["parameters"] == []


@pytest.mark.parametrize("case", ["missing_evidence", "cleared_code", "matched", "source_failure", "write_failure"])
def test_report_completion_through_portal(
    client: FlaskClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    case: str,
) -> None:
    """Keep a verified empty selection distinct from a source or output failure."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MISTHELPER_STANDALONE", "true")
    (tmp_path / "data").mkdir()
    caplog.set_level(logging.INFO)
    org_id = "00000000-0000-0000-0000-000000000001"
    runtime = SimpleNamespace(
        ConfigUtils=SimpleNamespace(get_cached_or_prompted_org_id=lambda: org_id),
        apisession=object(),
        DataExporter=Mock(),
    )
    runtime.DataExporter.write_with_format_selection.return_value = False
    if case == "matched":
        runtime.DataExporter = DataExporter
    observation = None if case == "missing_evidence" else {"code": "00" if case == "cleared_code" else "03"}
    sources = {
        "definitions": [
            {"code": "03", "key": "NO_IP_ADDRESS", "name": "No IP Address", "description": "No DHCP lease"}
        ],
        "sites": [],
        "inventory": [{"mac": "000000000001", "type": "ap"}],
        "stats": [{"mac": "000000000001", "last_trouble": observation}],
    }
    executor = OperationExecutor(MistHelper.menu_actions, runtime.apisession, org_id, None)
    monkeypatch.setitem(client.application.config, "OPERATION_EXECUTOR", executor)
    page = client.get("/operations").get_data(as_text=True)
    tokens = re.findall(r'<meta name="csrf-token" content="([^"]+)"', page)
    assert len(tokens) == 1
    try:
        with (
            patch("src.operations.exporting.ap_warning_report.operation.SourceDependencyResolver", runtime),
            patch(
                "src.operations.exporting.export.data_exporter.SourceDependencyResolver",
                SimpleNamespace(OUTPUT_FORMAT="csv"),
            ),
            patch(
                "src.operations.exporting.ap_warning_report.operation.ApWarningClient.read",
                return_value=sources,
                side_effect=RuntimeError("Controlled source read failure") if case == "source_failure" else None,
            ),
        ):
            started = client.post(
                "/api/operations/run", json={"menu_number": "307"}, headers={"X-CSRFToken": tokens[0]}
            )
            assert started.status_code == 202
            run_id = started.get_json()["run_id"]
            executor._runs[run_id]["_future"].result(timeout=10)
            status = client.get(f"/api/operations/status/{run_id}").get_json()
    finally:
        executor.shutdown()
    expected = "failed" if case in ("source_failure", "write_failure") else "completed"
    assert status["status"] == expected, status["error_message"]
    if case == "matched":
        assert len(status["output_files"]) == 1
        with (tmp_path / "data" / f"ApWarningReport_{org_id}.csv").open(encoding="utf-8", newline="") as output:
            rows = list(csv.DictReader(output))
        assert [(row["mac"], row["code"]) for row in rows] == [("000000000001", "03")]
        assert status["error_message"] is None
        return
    assert status["output_files"] == []
    if expected == "completed":
        assert "no output file" in status["completion_message"].lower()
        runtime.DataExporter.write_with_format_selection.assert_not_called()
    else:
        assert "AP warning report failed" in status["error_message"]
        assert status["completion_message"] is None
        assert runtime.DataExporter.write_with_format_selection.call_count == int(case == "write_failure")
    assert list((tmp_path / "data").iterdir()) == []
