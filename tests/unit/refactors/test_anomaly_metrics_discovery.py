"""Wave 4 P2 coverage for src/refactors/anomaly_metrics_discovery.py (initiative #1018).

Covers `AnomalyMetricsDiscovery.discover` end-to-end plus the `_MistHelperProxy`
`__getattr__` lazy-lookup path. `FilePathUtils.get_csv_path` on MistHelper is
monkeypatched so the discovery flow executes without touching real filesystem
paths. Tests exercise: missing-CSV fallback, IO/parse exception fallback, full
happy-path with site-scoped rows, priority sort ordering, and _process_csv_row
branch coverage (non-site rows, empty keys, blank names, priority keyword hits).
No source edits, no live I/O.
"""

from __future__ import annotations  # WHY: PEP 604 unions in type hints on Python 3.10+.

import logging  # WHY: verify structured error/warning/info logs at documented sites.
from pathlib import Path  # WHY: tmp_path fixture returns Path objects for CSV file creation.
from typing import Any  # WHY: return-type annotations for helpers/mocks.
from unittest.mock import MagicMock  # WHY: FR-008 mandates MagicMock(spec=...) for MistHelper doubles.

import pytest  # WHY: monkeypatch/tmp_path/caplog fixtures.

from src.refactors.anomaly_metrics_discovery import (  # WHY: SUT + proxy direct imports.
    _MH,
    AnomalyMetricsDiscovery,
    _MistHelperProxy,
)


def _install_file_path_utils(monkeypatch: pytest.MonkeyPatch, csv_path: str) -> MagicMock:
    """Publish a MagicMock FilePathUtils on MistHelper that returns csv_path."""
    file_path_utils_mock = MagicMock(name="FilePathUtils")  # WHY: proxy resolves via getattr on MistHelper.
    file_path_utils_mock.get_csv_path.return_value = csv_path  # WHY: SUT calls get_csv_path("ConstInsightMetrics.csv").
    monkeypatch.setattr(
        "MistHelper.FilePathUtils", file_path_utils_mock, raising=False
    )  # WHY: proxy lookup is call-time.
    return file_path_utils_mock  # WHY: expose to tests for call-arg assertions.


class TestMistHelperProxy:
    """`_MistHelperProxy.__getattr__` resolves names against the live MistHelper module."""

    def test_getattr_returns_module_attribute(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A published attribute on MistHelper is returned by the proxy's __getattr__."""
        sentinel = MagicMock(name="sentinel")  # WHY: unique object we can identity-compare.
        monkeypatch.setattr("MistHelper._anomaly_sentinel_attr", sentinel, raising=False)  # WHY: publish attr.
        proxy = _MistHelperProxy()  # WHY: fresh proxy to exercise __getattr__ in isolation.
        assert proxy._anomaly_sentinel_attr is sentinel  # WHY: identity check confirms zero-copy passthrough.

    def test_module_level_singleton_is_proxy(self) -> None:
        """`_MH` module-level singleton is an instance of `_MistHelperProxy`."""
        assert isinstance(_MH, _MistHelperProxy)  # WHY: guard against accidental replacement.


class TestDiscover:
    """`AnomalyMetricsDiscovery.discover` orchestrates CSV read, parse, and fallback."""

    def test_missing_csv_returns_fallback_and_logs_warning(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """When ConstInsightMetrics.csv does not exist, discover() returns a fallback copy and logs a warning."""
        missing_path = str(tmp_path / "does_not_exist.csv")  # WHY: guaranteed missing path under tmp_path.
        _install_file_path_utils(monkeypatch, missing_path)  # WHY: point SUT at the missing file.
        with caplog.at_level(logging.WARNING):  # WHY: _handle_missing_csv logs at WARNING.
            result = AnomalyMetricsDiscovery.discover()  # WHY: exercise the missing-file branch.
        assert result == AnomalyMetricsDiscovery.FALLBACK_METRICS  # WHY: contents match fallback verbatim.
        assert result is not AnomalyMetricsDiscovery.FALLBACK_METRICS  # WHY: must be a copy, not the same list.
        assert "ConstInsightMetrics.csv not found" in caplog.text  # WHY: operator guidance in the warning.

    def test_exception_returns_fallback_and_logs_error(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """When get_csv_path raises, discover() logs ERROR and returns a fallback copy."""
        broken_utils = MagicMock(name="FilePathUtils")  # WHY: MagicMock stand-in for MistHelper.FilePathUtils.
        broken_utils.get_csv_path.side_effect = RuntimeError("boom")  # WHY: trigger the outer except path.
        monkeypatch.setattr("MistHelper.FilePathUtils", broken_utils, raising=False)  # WHY: publish for proxy.
        with caplog.at_level(logging.ERROR):  # WHY: except branch logs at ERROR.
            result = AnomalyMetricsDiscovery.discover()  # WHY: exercise the exception branch.
        assert result == AnomalyMetricsDiscovery.FALLBACK_METRICS  # WHY: verbatim match of the fallback set.
        assert result is not AnomalyMetricsDiscovery.FALLBACK_METRICS  # WHY: must be a defensive copy.
        assert "Error reading ConstInsightMetrics.csv" in caplog.text  # WHY: error log message format.

    def test_parses_site_scoped_rows_only(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Non-site scope rows and empty keys are filtered out; site rows survive."""
        csv_file = tmp_path / "ConstInsightMetrics.csv"  # WHY: real CSV path under tmp_path.
        csv_file.write_text(  # WHY: minimal CSV exercising every _process_csv_row branch.
            "key,name,scope\n"
            "client-roam-band5,Roaming 5GHz,site\n"  # WHY: site-scoped priority row (keyword match).
            "device-uptime,Device Uptime,org\n"  # WHY: non-site row, skipped.
            ",Blank Key,site\n"  # WHY: empty key row, skipped.
            "custom-metric,Custom Metric,site\n"  # WHY: site row, no priority keyword.
            "capacity-index,,site\n"  # WHY: blank name triggers fallback description branch.
        )
        _install_file_path_utils(monkeypatch, str(csv_file))  # WHY: point SUT at our fixture CSV.

        result = AnomalyMetricsDiscovery.discover()  # WHY: run the happy-path parse+sort.

        assert len(result) == 3  # WHY: two skipped rows leave three eligible metrics.
        # First two are priority=True (keywords 'roam' and 'capacity'); last is non-priority 'custom-metric'.
        assert [m["metric_name"] for m in result] == [
            "capacity-index",
            "client-roam-band5",
            "custom-metric",
        ]  # WHY: priority-first then alpha; capacity-index precedes client-roam-band5.
        assert result[0]["priority"] is True  # WHY: 'capacity' keyword match sets priority.
        assert result[0]["description"] == "Anomaly events for capacity-index"  # WHY: blank name fallback.
        assert result[1]["priority"] is True  # WHY: 'roam' keyword match sets priority.
        assert result[1]["description"] == "Roaming 5GHz"  # WHY: non-blank name preserved.
        assert result[2]["priority"] is False  # WHY: 'custom-metric' matches no priority keyword.

    def test_empty_csv_returns_empty_list(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """CSV with only header and no data rows returns an empty list."""
        csv_file = tmp_path / "empty.csv"  # WHY: header-only CSV exercises reader with zero rows.
        csv_file.write_text("key,name,scope\n")  # WHY: valid schema, no rows.
        _install_file_path_utils(monkeypatch, str(csv_file))  # WHY: point SUT at the empty CSV.

        result = AnomalyMetricsDiscovery.discover()  # WHY: exercise zero-row parse path.

        assert result == []  # WHY: no eligible metrics returns empty list (post-sort).


class TestProcessCsvRow:
    """`_process_csv_row` filters non-site rows and populates the metric dict."""

    def test_non_site_scope_returns_none(self) -> None:
        """A row with scope != 'site' is rejected."""
        row = {"key": "device-metric", "name": "Device Metric", "scope": "org"}  # WHY: org-scope row.
        assert AnomalyMetricsDiscovery._process_csv_row(row) is None  # WHY: non-site rejected.

    def test_empty_key_returns_none(self) -> None:
        """A row with an empty key is rejected even when scope is 'site'."""
        row = {"key": "  ", "name": "Whitespace Key", "scope": "site"}  # WHY: whitespace-only key strips to empty.
        assert AnomalyMetricsDiscovery._process_csv_row(row) is None  # WHY: empty key rejected.

    def test_priority_keyword_hit_sets_priority_true(self) -> None:
        """A key containing any PRIORITY_KEYWORDS entry sets priority=True."""
        row = {"key": "ap-availability", "name": "AP Avail", "scope": "site"}  # WHY: 'availability' keyword.
        metric = AnomalyMetricsDiscovery._process_csv_row(row)  # WHY: exercise priority-true branch.
        assert metric is not None  # WHY: eligible row returns a dict.
        assert metric["priority"] is True  # WHY: 'availability' keyword hit.
        assert metric["metric_name"] == "ap-availability"  # WHY: lowercased key becomes metric_name.
        assert metric["description"] == "AP Avail"  # WHY: non-blank name preserved as description.

    def test_no_priority_keyword_sets_priority_false(self) -> None:
        """A key matching none of PRIORITY_KEYWORDS sets priority=False."""
        row = {"key": "obscure-metric", "name": "Obscure", "scope": "site"}  # WHY: no priority keyword match.
        metric = AnomalyMetricsDiscovery._process_csv_row(row)  # WHY: exercise priority-false branch.
        assert metric is not None  # WHY: eligible row.
        assert metric["priority"] is False  # WHY: no keyword hit.

    def test_missing_fields_default_to_empty_strings(self) -> None:
        """Missing keys in the input dict default to empty string via row.get(..., '')."""
        row: dict[str, str] = {}  # WHY: no keys at all; get(..., "") should apply.
        assert AnomalyMetricsDiscovery._process_csv_row(row) is None  # WHY: empty scope != 'site' rejects row.


class TestSortByPriority:
    """`_sort_by_priority` places priority items first, then alphabetical."""

    def test_priority_first_then_alpha(self, caplog: pytest.LogCaptureFixture) -> None:
        """Priority-True items come before priority-False, each alpha within its group."""
        metrics: list[dict[str, Any]] = [
            {"metric_name": "z-nonpri", "description": "z", "priority": False},  # WHY: non-priority, alpha last.
            {"metric_name": "b-pri", "description": "b", "priority": True},  # WHY: priority, alpha 2nd.
            {"metric_name": "a-pri", "description": "a", "priority": True},  # WHY: priority, alpha 1st.
            {"metric_name": "a-nonpri", "description": "an", "priority": False},  # WHY: non-priority, alpha 1st.
        ]
        with caplog.at_level(logging.INFO):  # WHY: _sort_by_priority logs INFO with the count.
            result = AnomalyMetricsDiscovery._sort_by_priority(metrics)  # WHY: exercise the sort path.
        assert [m["metric_name"] for m in result] == [
            "a-pri",
            "b-pri",
            "a-nonpri",
            "z-nonpri",
        ]  # WHY: priority group first (alpha), then non-priority (alpha).
        assert "Found 4 potential anomaly metrics" in caplog.text  # WHY: log format assertion.

    def test_missing_priority_key_treated_as_false(self) -> None:
        """A metric dict without a 'priority' key defaults to False (via .get('priority', False))."""
        metrics: list[dict[str, Any]] = [
            {"metric_name": "no-pri-key"},  # WHY: no 'priority' key.
            {"metric_name": "explicit-pri", "priority": True},  # WHY: explicit priority.
        ]
        result = AnomalyMetricsDiscovery._sort_by_priority(metrics)  # WHY: exercise default-false branch.
        assert result[0]["metric_name"] == "explicit-pri"  # WHY: explicit priority wins.
        assert result[1]["metric_name"] == "no-pri-key"  # WHY: missing key treated as non-priority.
