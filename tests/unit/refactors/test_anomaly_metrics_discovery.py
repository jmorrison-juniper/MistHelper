"""Wave 4 P2 coverage for src/foundation/support/refactors/anomaly_metrics_discovery.py (initiative #1018).

Covers `AnomalyMetricsDiscovery.discover` end-to-end plus the `_MistHelperProxy`
`__getattr__` lazy-lookup path. `FilePathUtils.get_csv_path` on MistHelper is
monkeypatched so the discovery flow executes without touching real filesystem
paths. Tests exercise: missing-CSV fallback, IO/parse exception fallback, full
happy-path with site-scoped rows, priority sort ordering, and _process_csv_row
branch coverage (non-site rows, empty keys, blank names, priority keyword hits).
Uses synthetic CSV files and errors. Makes no live API requests.
"""

from __future__ import annotations  # WHY: PEP 604 unions in type hints on Python 3.10+.

import csv  # Generate a parser failure with the active CSV field limit.
import logging  # WHY: verify structured error/warning/info logs at documented sites.
from pathlib import Path  # WHY: tmp_path fixture returns Path objects for CSV file creation.
from typing import Any  # WHY: return-type annotations for helpers/mocks.
from unittest.mock import MagicMock  # WHY: FR-008 mandates MagicMock(spec=...) for MistHelper doubles.

import pytest  # WHY: monkeypatch/tmp_path/caplog fixtures.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,
)  # WHY: assert the source dependency seam.
from src.foundation.support.refactors.anomaly_metrics_discovery import (  # WHY: SUT + proxy direct imports.
    _MH,
    AnomalyMetricsDiscovery,
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
        proxy = _MH  # WHY: fresh proxy to exercise __getattr__ in isolation.
        assert proxy._anomaly_sentinel_attr is sentinel  # WHY: identity check confirms zero-copy passthrough.

    def test_module_level_singleton_is_proxy(self) -> None:
        """`_MH` module-level singleton is an instance of `_MistHelperProxy`."""
        assert _MH is SourceDependencyResolver  # WHY: guard against accidental replacement.


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

    @pytest.mark.parametrize(
        "failure",
        [
            (stage, error_type)
            for stage in ("get_csv_path", "_parse_metrics_csv")
            for error_type in (RuntimeError, OSError, UnicodeError, csv.Error)
        ],
    )
    def test_supported_failure_returns_fallback_and_logs_safe_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
        failure: tuple[str, type[Exception]],
    ) -> None:
        """Supported failures retain the fallback without disclosing exception text."""
        stage, error_type = failure  # Cover each supported failure at both guarded calls.
        csv_file = tmp_path / "metrics.csv"  # Use an isolated input for both failure stages.
        csv_file.write_text("key,name,scope\n", encoding="utf-8")  # Permit the parser stage to run.
        file_utils = _install_file_path_utils(monkeypatch, str(csv_file))  # Resolve only the synthetic file.
        target = file_utils if stage == "get_csv_path" else AnomalyMetricsDiscovery  # Cover both guarded calls.
        monkeypatch.setattr(
            target, stage, MagicMock(side_effect=error_type("synthetic-sensitive-detail"))
        )  # Inject safely.
        with caplog.at_level(logging.DEBUG):  # Include every log level in the disclosure check.
            result = AnomalyMetricsDiscovery.discover()  # Exercise the supported failure boundary.
        assert result == AnomalyMetricsDiscovery.FALLBACK_METRICS  # WHY: verbatim match of the fallback set.
        assert result is not AnomalyMetricsDiscovery.FALLBACK_METRICS  # WHY: must be a defensive copy.
        assert f"Error reading ConstInsightMetrics.csv ({error_type.__name__})" in caplog.text  # Name the safe cause.
        assert "Using fallback metrics." in caplog.text  # Make degraded discovery explicit.
        assert "synthetic-sensitive-detail" not in caplog.text  # Never log raw exception text.
        assert not any(record.exc_info for record in caplog.records)  # Tracebacks can disclose exception text.

    @pytest.mark.parametrize("stage", ["get_csv_path", "_parse_metrics_csv"])
    @pytest.mark.parametrize("error_type", [TypeError, AttributeError, NameError, KeyError, ValueError, AssertionError])
    def test_unexpected_failure_propagates(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        stage: str,
        error_type: type[Exception],
    ) -> None:
        """Programming defects propagate from path resolution and CSV processing."""
        csv_file = tmp_path / "metrics.csv"  # Use an isolated input for both failure stages.
        csv_file.write_text("key,name,scope\n", encoding="utf-8")  # Permit the parser stage to run.
        file_utils = _install_file_path_utils(monkeypatch, str(csv_file))  # Resolve only the synthetic file.
        target = file_utils if stage == "get_csv_path" else AnomalyMetricsDiscovery  # Cover both guarded calls.
        error = error_type("synthetic-programming-defect")  # Identify the exact propagated exception.
        monkeypatch.setattr(
            target, stage, MagicMock(side_effect=error)
        )  # Inject a defect rather than an input failure.
        with pytest.raises(error_type) as caught:  # A fallback must not hide this defect.
            AnomalyMetricsDiscovery.discover()  # Exercise the narrowed exception boundary.
        assert caught.value is error  # Preserve the original exception for the caller.

    @pytest.mark.parametrize(
        "contents",
        [
            "key,name,scope\nvalid,Valid,site\nshort,Short\n",
            "scope,key,name\nsite,valid,Valid\nsite,short\n",
            "scope,name,key\nsite,Valid,valid\nsite,Short\n",
        ],
    )
    def test_short_csv_row_returns_fallback(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
        contents: str,
    ) -> None:
        """A missing cell triggers CSV recovery instead of an attribute error or partial result."""
        csv_file = tmp_path / "short.csv"  # Keep malformed input isolated from product files.
        csv_file.write_text(contents, encoding="utf-8")  # Omit each required cell in turn.
        _install_file_path_utils(monkeypatch, str(csv_file))  # Read only this synthetic CSV.
        with caplog.at_level(logging.ERROR):  # Verify the malformed input has an explicit report.
            result = AnomalyMetricsDiscovery.discover()  # Exercise real DictReader padding.
        assert result == AnomalyMetricsDiscovery.FALLBACK_METRICS  # Discard partial discovery on malformed rows.
        assert result is not AnomalyMetricsDiscovery.FALLBACK_METRICS  # Preserve the fallback copy contract.
        assert "Error reading ConstInsightMetrics.csv (Error)" in caplog.text  # Report the CSV error category.

    @pytest.mark.parametrize("failure", ["encoding", "field-limit", "permission", "directory"])
    def test_unreadable_csv_returns_fallback(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
        failure: str,
    ) -> None:
        """Unreadable input returns defaults and a safe error report."""
        csv_file = tmp_path / "unreadable.csv"  # Confine file access to the test directory.
        contents = (
            b"key,name,scope\n\xff,Private,site\n"
            if failure == "encoding"
            else ("key,name,scope\n" + "x" * (csv.field_size_limit() + 1) + ",Private,site\n").encode("utf-8")
        )  # Exercise real decoding and CSV parser failures.
        csv_file.write_bytes(contents)  # Create synthetic input without production credentials.
        _install_file_path_utils(
            monkeypatch, str(tmp_path if failure == "directory" else csv_file)
        )  # Include directory IO.
        if failure == "permission":  # File permissions differ across supported platforms.
            monkeypatch.setattr(
                "src.foundation.support.refactors.anomaly_metrics_discovery.open",
                MagicMock(side_effect=PermissionError("synthetic-sensitive-detail")),
                raising=False,
            )  # Simulate denial only at this module's file-read boundary.
        with caplog.at_level(logging.DEBUG):  # Check all emitted records for data disclosure.
            result = AnomalyMetricsDiscovery.discover()  # Exercise real reading except for simulated permission denial.
        assert result == AnomalyMetricsDiscovery.FALLBACK_METRICS  # Preserve the existing recovery result.
        assert result is not AnomalyMetricsDiscovery.FALLBACK_METRICS  # Return a distinct list.
        assert "Error reading ConstInsightMetrics.csv" in caplog.text  # Report failure instead of silent success.
        assert "Using fallback metrics." in caplog.text  # Tell the operator that defaults replaced discovery.
        assert "synthetic-sensitive-detail" not in caplog.text  # Exclude simulated private exception text.
        assert "Private" not in caplog.text  # Exclude CSV content from diagnostic messages.
        assert str(tmp_path) not in caplog.text  # Exclude private filesystem paths.

    @pytest.mark.parametrize(
        ("contents", "expected"),
        [
            ("", []),
            (
                "key,scope\n CUSTOM , SITE \n",
                [{"metric_name": "custom", "description": "Anomaly events for custom", "priority": False}],
            ),
            ("key,name\ncustom,Custom\n", []),
            (
                'key,name,scope,extra\ncustom,"Custom, metric",site,ignored\n',
                [{"metric_name": "custom", "description": "Custom, metric", "priority": False}],
            ),
        ],
    )
    def test_supported_csv_shapes_remain_unchanged(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        contents: str,
        expected: list[dict[str, Any]],
    ) -> None:
        """Empty files, absent headers, quoted cells, and extra columns retain their behavior."""
        csv_file = tmp_path / "supported.csv"  # Keep compatibility cases independent of exported files.
        csv_file.write_text(contents, encoding="utf-8")  # Use the export encoding.
        _install_file_path_utils(monkeypatch, str(csv_file))  # Resolve this supported input.
        assert AnomalyMetricsDiscovery.discover() == expected  # Preserve exact filtering and output shapes.

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
        assert isinstance(metric, dict)  # WHY: an eligible row returns a metric dict.
        assert metric["priority"] is True  # WHY: 'availability' keyword hit.
        assert metric["metric_name"] == "ap-availability"  # WHY: lowercased key becomes metric_name.
        assert metric["description"] == "AP Avail"  # WHY: non-blank name preserved as description.

    def test_no_priority_keyword_sets_priority_false(self) -> None:
        """A key matching none of PRIORITY_KEYWORDS sets priority=False."""
        row = {"key": "obscure-metric", "name": "Obscure", "scope": "site"}  # WHY: no priority keyword match.
        metric = AnomalyMetricsDiscovery._process_csv_row(row)  # WHY: exercise priority-false branch.
        assert isinstance(metric, dict)  # WHY: an eligible row returns a metric dict.
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
