"""Tests for the switch scorecard operation."""

from __future__ import annotations  # WHY: keep annotations consistent with the source package.

from typing import Any  # WHY: fake exporter call storage is dynamic.

from src.reports.switch_scorecard import operation  # WHY: monkeypatch operation-level dependencies.


class _Client:
    def list_switch_stats(self):  # Return one switch without a network call.
        return [  # WHY: operation tests need one complete healthy switch.
            {
                "site_id": "site-1",
                "site_name": "Main",
                "name": "sw-1",
                "mac": "aa",
                "model": "EX4400",
                "version": "22.4R3",
                "config_status": "success",
                "ap_redundancy": {"num_aps": 3, "num_aps_with_switch_redundancy": 2},
                "module_stat": [],
                "uptime": 3600,
                "last_trouble": "",
            }
        ]


class _Exporter:
    calls: list[dict[str, Any]] = []  # WHY: tests inspect both export calls.

    @staticmethod
    def write_with_format_selection(rows, filename, api_function_name=None, fieldnames=None):
        _Exporter.calls.append(  # WHY: capture enough data to prove the operation contract.
            {
                "rows": rows,
                "filename": filename,
                "api_function_name": api_function_name,
                "fieldnames": fieldnames,
            }
        )
        return True  # WHY: the operation logs a successful export path.


class _Resolver:
    DataExporter = _Exporter  # WHY: mimic SourceDependencyResolver for the operation.


def test_operation_writes_both_scorecard_files(monkeypatch):  # Verify FR-007 and output contract.
    _Exporter.calls.clear()  # WHY: isolate this test from previous calls.
    monkeypatch.setattr(operation, "SwitchScorecardClient", _Client)  # WHY: avoid the real Mist API.
    monkeypatch.setattr(operation, "SourceDependencyResolver", _Resolver)  # WHY: avoid the real exporter.
    monkeypatch.delenv("SWITCH_AP_AFFINITY_LIMIT", raising=False)  # WHY: prove no prompt or env setup is required.

    operation.SwitchScorecard.run()  # WHY: execute the menu handler exactly as wiring will call it.

    filenames = [call["filename"] for call in _Exporter.calls]  # WHY: both required files must be written.
    assert filenames == ["SwitchScorecard.csv", "SwitchScorecardBySite.csv"]
    assert _Exporter.calls[0]["rows"][0]["switch_name"] == "sw-1"  # WHY: detail output has one switch row.
    assert _Exporter.calls[1]["rows"][0]["switch_count"] == 1  # WHY: site output has one site summary row.
