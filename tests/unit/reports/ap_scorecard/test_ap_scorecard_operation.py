"""Tests for the AP scorecard operation handler."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from types import SimpleNamespace

from src.reports.ap_scorecard import operation


def test_ap_scorecard_operation_logs_console_summary(
    ap_stats_payload: list[dict[str, object]],
    caplog,
    monkeypatch,
) -> None:
    """The operation logs all required organization summary tile names."""
    exports: list[tuple[str, list[Mapping[str, object]], str]] = []
    _patch_operation(monkeypatch, ap_stats_payload, exports)
    caplog.set_level(logging.INFO)
    operation.ApScorecard.run()
    output = "\n".join(record.getMessage() for record in caplog.records)
    assert "Connection Status" in output
    assert "VLANs" in output
    assert "Version Compliance" in output
    assert "AP Switch Redundancy" in output
    assert "Potential Anomalies" in output


def test_ap_scorecard_operation_is_test_safe_and_writes_both_files(
    ap_stats_payload: list[dict[str, object]],
    monkeypatch,
) -> None:
    """The operation uses shared org resolution and writes both contract files."""
    exports: list[tuple[str, list[Mapping[str, object]], str]] = []
    monkeypatch.setattr("builtins.input", _raise_if_input_is_called)
    _patch_operation(monkeypatch, ap_stats_payload, exports)
    operation.ApScorecard.run()
    assert [export[0] for export in exports] == ["ApScorecard.csv", "ApScorecardBySite.csv"]
    assert [export[2] for export in exports] == ["ap_scorecard", "ap_scorecard_by_site"]
    assert all(row["org_id"] == "org-1" for row in exports[0][1])
    assert all(row["org_id"] == "org-1" for row in exports[1][1])


def test_ap_scorecard_operation_handles_no_ap_payload(caplog, monkeypatch) -> None:
    """The operation logs a clear message and skips exports when no AP rows exist."""
    exports: list[tuple[str, list[Mapping[str, object]], str]] = []
    _patch_operation(monkeypatch, [], exports)
    caplog.set_level(logging.INFO)
    operation.ApScorecard.run()
    assert exports == []
    assert "No access point statistics were found" in caplog.text
    assert "Connection Status" not in caplog.text


def _patch_operation(
    monkeypatch,
    payload: list[dict[str, object]],
    exports: list[tuple[str, list[Mapping[str, object]], str]],
) -> None:
    """Patch operation dependencies with no-prompt and no-network doubles."""
    monkeypatch.setattr(operation.ApScorecardClient, "list_ap_stats", lambda self: payload)

    def fake_write(
        rows: list[Mapping[str, object]],
        filename: str,
        *,
        api_function_name: str,
        fieldnames: list[str],
    ) -> bool:
        exports.append((filename, rows, api_function_name))
        assert fieldnames
        return True

    monkeypatch.setattr(
        operation,
        "SourceDependencyResolver",
        SimpleNamespace(
            ConfigUtils=SimpleNamespace(get_cached_or_prompted_org_id=lambda: "org-1"),
            apisession=object(),
            DataExporter=SimpleNamespace(write_with_format_selection=fake_write),
        ),
    )


def _raise_if_input_is_called(*args: object, **kwargs: object) -> str:
    """Fail if the operation calls a direct prompt."""
    raise AssertionError("ApScorecard.run must not call input directly.")
