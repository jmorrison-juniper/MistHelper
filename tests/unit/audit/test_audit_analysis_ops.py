"""Wave 5 P2 coverage for src/audit/audit_analysis_ops.py (initiative #1018).

Covers all static methods of ``AuditAnalysisOps``:
- ``_prompt_audit_time_range_input`` in test-mode + interactive-mode branches.
- ``_fetch_filtered_audit_entries`` success + API-failure branches.
- ``_render_audit_analysis_reports`` renderer delegation with print assertions.
- ``audit_log_analysis`` full orchestration branches: cache-hit, no org_id,
  invalid time range, API failure, and full happy-path.

MagicMock(spec=...) is mandatory on all mocks. No live network, no source edits.
"""

from __future__ import annotations  # WHY: PEP 604 unions in test type hints.

import logging  # WHY: caplog verification of structured log lines.
import os  # WHY: verify os.path.join-produced paths in printed report locations.
import sys  # WHY: mint a fake MistHelper module into sys.modules for lazy-import to resolve.
import types  # WHY: build the fake MistHelper module cheaply.
from typing import Any  # WHY: dict[str, Any] annotations in fixtures.
from unittest.mock import MagicMock, patch  # WHY: mandatory spec= mocks + patch decorators.

import pytest  # WHY: monkeypatch + caplog + capsys fixtures.

from src.audit.audit_analysis_ops import AuditAnalysisOps  # WHY: SUT direct import.
from src.audit.time_parser import ParsedTimeRange  # WHY: build real time-range value objects.


def _install_fake_mist_helper(monkeypatch: pytest.MonkeyPatch, mh_module: Any) -> None:
    """Replace the module resolved by ``importlib.import_module('MistHelper')`` with our fake."""
    monkeypatch.setitem(sys.modules, "MistHelper", mh_module)  # WHY: lazy-import inside SUT returns this stub.


def _make_mh(test_mode: bool = True) -> Any:
    """Build a minimal MistHelper stand-in with the attributes touched by the SUT."""
    mh: Any = types.ModuleType("MistHelper")  # WHY: Any typing satisfies both mypy strict + ruff B010 on dynamic attrs.
    mh.IS_TEST_MODE = test_mode  # WHY: SUT reads this flag to skip interactive prompts under tests.
    mh.apisession = MagicMock(spec=object)  # WHY: opaque placeholder API session; SUT pass-through only.
    mh.InputUtils = MagicMock(spec=object)  # WHY: overwritten per-test where interactive-prompt path is needed.
    mh.CacheUtils = MagicMock(spec=object)  # WHY: overwritten per-test to control cache-hit branch.
    mh.ConfigUtils = MagicMock(spec=object)  # WHY: overwritten per-test to control org_id branch.
    return mh  # Caller wires up per-test behaviors.


class TestPromptAuditTimeRangeInput:
    """``_prompt_audit_time_range_input`` returns fixed default in test-mode; else prompts InputUtils."""

    def test_test_mode_returns_seven_days_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When IS_TEST_MODE is True the method skips interaction and returns "7d"."""
        mh = _make_mh(test_mode=True)  # WHY: test-mode branch.
        _install_fake_mist_helper(monkeypatch, mh)  # WHY: SUT's lazy import lands on our stub.

        result = AuditAnalysisOps._prompt_audit_time_range_input()  # WHY: exercise test-mode branch.

        assert result == "7d"  # WHY: contract-mandated default in test-mode.

    def test_interactive_mode_uses_input_utils_and_strips(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Interactive mode prints examples banner and returns stripped safe_input result."""
        mh = _make_mh(test_mode=False)  # WHY: interactive branch.
        mh.InputUtils.safe_input = MagicMock(return_value="  4w  ")  # WHY: stripped result asserted.
        _install_fake_mist_helper(monkeypatch, mh)

        result = AuditAnalysisOps._prompt_audit_time_range_input()  # WHY: exercise interactive branch.

        assert result == "4w"  # WHY: whitespace trimmed per SUT.
        mh.InputUtils.safe_input.assert_called_once_with(  # WHY: prompt string is user-visible contract.
            "Enter time range [7d]: ", context="audit_analysis"
        )
        assert "Time range examples" in capsys.readouterr().out  # WHY: banner is user-visible contract.


class TestFetchFilteredAuditEntries:
    """``_fetch_filtered_audit_entries`` returns entries on success and None on API errors."""

    def test_success_returns_paginated_entries(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Successful API call + get_all pagination returns the merged entries list."""
        mh = _make_mh()
        _install_fake_mist_helper(monkeypatch, mh)
        time_range = ParsedTimeRange(  # WHY: real value object; SUT calls .description.
            duration="7d",  # WHY: TimeRangeParser.to_api_kwargs forwards duration when set.
            description="7 days",  # WHY: appears in the info log line asserted below.
        )
        fake_response = MagicMock(spec=object)  # WHY: opaque; passed through to get_all.
        fake_entries: list[dict[str, Any]] = [{"id": "1"}, {"id": "2"}]  # WHY: representative payload.

        with patch(  # WHY: patch mistapi call chain used inside the SUT.
            "src.audit.audit_analysis_ops.mistapi"
        ) as fake_mistapi:
            fake_mistapi.api.v1.orgs.logs.listOrgAuditLogs.return_value = fake_response
            fake_mistapi.get_all.return_value = fake_entries  # WHY: pagination collates all pages.
            with caplog.at_level(logging.DEBUG):
                result = AuditAnalysisOps._fetch_filtered_audit_entries("org-1", time_range)

        assert result == fake_entries  # WHY: successful returns raw entries.
        fake_mistapi.api.v1.orgs.logs.listOrgAuditLogs.assert_called_once()  # WHY: API contract call.
        fake_mistapi.get_all.assert_called_once_with(response=fake_response, mist_session=mh.apisession)
        assert "Fetching audit logs for org org-1" in caplog.text  # WHY: pre-action info log.
        assert "Retrieved 2 raw audit log entries" in caplog.text  # WHY: post-action debug log.

    def test_get_all_returns_none_falls_back_to_empty_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When ``mistapi.get_all`` returns None the SUT substitutes an empty list (falsy branch)."""
        mh = _make_mh()
        _install_fake_mist_helper(monkeypatch, mh)
        time_range = ParsedTimeRange(duration="1d", description="tiny")

        with patch("src.audit.audit_analysis_ops.mistapi") as fake_mistapi:
            fake_mistapi.api.v1.orgs.logs.listOrgAuditLogs.return_value = MagicMock(spec=object)
            fake_mistapi.get_all.return_value = None  # WHY: covers `... or []` fallback.
            result = AuditAnalysisOps._fetch_filtered_audit_entries("org-1", time_range)

        assert result == []  # WHY: SUT normalises None to empty list.

    def test_api_exception_returns_none_and_logs_error(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Exception in the API layer is swallowed and returns None with an error log line."""
        mh = _make_mh()
        _install_fake_mist_helper(monkeypatch, mh)
        time_range = ParsedTimeRange(duration="4w", description="4 weeks")

        with patch("src.audit.audit_analysis_ops.mistapi") as fake_mistapi:
            fake_mistapi.api.v1.orgs.logs.listOrgAuditLogs.side_effect = RuntimeError("boom")
            with caplog.at_level(logging.ERROR):
                result = AuditAnalysisOps._fetch_filtered_audit_entries("org-1", time_range)

        assert result is None  # WHY: legacy contract: API failure returns None (not raise).
        assert "API call failed: boom" in caplog.text  # WHY: exception message must appear in log.


class TestRenderAuditAnalysisReports:
    """``_render_audit_analysis_reports`` writes both mermaid + html reports and prints paths."""

    def test_delegates_to_renderer_and_prints_both_paths(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Both render methods are invoked with the analysis + report paths, and paths are printed."""
        analysis = MagicMock(spec=object)  # WHY: opaque analysis object passed through unmodified.
        with patch("src.audit.audit_analysis_ops.AuditReportRenderer") as fake_renderer_cls:
            fake_renderer = MagicMock(spec=object)
            fake_renderer.render_mermaid = MagicMock()
            fake_renderer.render_html = MagicMock()
            fake_renderer_cls.return_value = fake_renderer

            AuditAnalysisOps._render_audit_analysis_reports(analysis)

        expected_md = os.path.join("data", "OrgAuditAnalysis.md")  # WHY: mirror SUT's os.path.join contract.
        expected_html = os.path.join("data", "OrgAuditAnalysis.html")  # WHY: mirror SUT's os.path.join contract.
        fake_renderer.render_mermaid.assert_called_once_with(analysis, expected_md)  # WHY: mermaid delegation.
        fake_renderer.render_html.assert_called_once_with(analysis, expected_html)  # WHY: html delegation.
        output = capsys.readouterr().out  # WHY: user-visible paths in stdout.
        assert f"Mermaid report: {expected_md}" in output
        assert f"HTML report: {expected_html}" in output


class TestAuditLogAnalysisOrchestration:
    """``audit_log_analysis`` top-level branches: cache-hit, no org, invalid range, API fail, happy path."""

    def _prime_helpers(
        self,
        monkeypatch: pytest.MonkeyPatch,
        *,
        cache_hit: bool,
        org_id: str | None,
        test_mode: bool = True,
    ) -> Any:
        """Wire the MistHelper stub with CacheUtils / ConfigUtils / InputUtils per branch under test."""
        mh = _make_mh(test_mode=test_mode)
        mh.CacheUtils.fast_cache_hit = MagicMock(return_value=cache_hit)  # WHY: control the early-return cache branch.
        mh.ConfigUtils.get_cached_or_prompted_org_id = MagicMock(return_value=org_id)  # WHY: control org branch.
        _install_fake_mist_helper(monkeypatch, mh)
        return mh

    def test_cache_hit_short_circuits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Cache-hit branch returns immediately without calling ConfigUtils."""
        mh = self._prime_helpers(monkeypatch, cache_hit=True, org_id="ignored")
        AuditAnalysisOps.audit_log_analysis()  # WHY: cache-hit path.
        mh.ConfigUtils.get_cached_or_prompted_org_id.assert_not_called()  # WHY: proves early return.

    def test_missing_org_id_short_circuits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Missing org_id returns before invoking time-range prompt or API."""
        mh = self._prime_helpers(monkeypatch, cache_hit=False, org_id=None)
        with patch.object(AuditAnalysisOps, "_prompt_audit_time_range_input") as fake_prompt:
            AuditAnalysisOps.audit_log_analysis()
        fake_prompt.assert_not_called()  # WHY: no org means no prompt.
        mh.CacheUtils.fast_cache_hit.assert_called_once()  # WHY: entered top of function.

    def test_invalid_time_range_logs_and_returns(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """When the parser raises ValueError, the SUT logs an error and returns without API call."""
        self._prime_helpers(monkeypatch, cache_hit=False, org_id="org-x")
        with (
            patch.object(AuditAnalysisOps, "_prompt_audit_time_range_input", return_value="bogus"),
            patch("src.audit.audit_analysis_ops.TimeRangeParser") as fake_parser_cls,
            patch.object(AuditAnalysisOps, "_fetch_filtered_audit_entries") as fake_fetch,
        ):
            fake_parser_cls.return_value.parse.side_effect = ValueError("bad range")
            with caplog.at_level(logging.ERROR):
                AuditAnalysisOps.audit_log_analysis()

        fake_fetch.assert_not_called()  # WHY: aborted before fetching entries.
        assert "Invalid time range: bad range" in caplog.text  # WHY: error log line contract.

    def test_api_failure_returns_before_analyzing(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When _fetch_filtered_audit_entries returns None the SUT stops before AuditLogFilter runs."""
        self._prime_helpers(monkeypatch, cache_hit=False, org_id="org-x")
        time_range = ParsedTimeRange(duration="7d", description="7d desc")

        with (
            patch.object(AuditAnalysisOps, "_prompt_audit_time_range_input", return_value="7d"),
            patch("src.audit.audit_analysis_ops.TimeRangeParser") as fake_parser_cls,
            patch.object(AuditAnalysisOps, "_fetch_filtered_audit_entries", return_value=None),
            patch("src.audit.audit_analysis_ops.AuditLogFilter") as fake_filter_cls,
        ):
            fake_parser_cls.return_value.parse.return_value = time_range
            AuditAnalysisOps.audit_log_analysis()

        fake_filter_cls.assert_not_called()  # WHY: API-failure aborts before filter+analyze.
        assert "Fetching audit logs for: 7d desc" in capsys.readouterr().out  # WHY: pre-fetch banner still printed.

    def test_happy_path_orchestrates_full_pipeline(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """End-to-end: parse -> fetch -> filter -> analyze -> render, with all summary prints."""
        self._prime_helpers(monkeypatch, cache_hit=False, org_id="org-42")
        time_range = ParsedTimeRange(duration="7d", description="7 days")
        fake_entries = [{"id": "a"}, {"id": "b"}, {"id": "c"}]  # WHY: 3 raw entries for print-count assertion.
        filter_stats = {"kept_count": 2, "removed_count": 1}  # WHY: exact numbers appear in printed summary.
        fake_filtered = [{"id": "a"}, {"id": "b"}]  # WHY: represents post-noise-filter entries.

        with (
            patch.object(AuditAnalysisOps, "_prompt_audit_time_range_input", return_value="7d"),
            patch("src.audit.audit_analysis_ops.TimeRangeParser") as fake_parser_cls,
            patch.object(AuditAnalysisOps, "_fetch_filtered_audit_entries", return_value=fake_entries),
            patch("src.audit.audit_analysis_ops.AuditLogFilter") as fake_filter_cls,
            patch("src.audit.audit_analysis_ops.AuditLogAnalyzer") as fake_analyzer_cls,
            patch.object(AuditAnalysisOps, "_render_audit_analysis_reports") as fake_render,
        ):
            fake_parser_cls.return_value.parse.return_value = time_range
            fake_filter = MagicMock(spec=object)
            fake_filter.filter_with_stats = MagicMock(return_value=(fake_filtered, filter_stats))
            fake_filter_cls.return_value = fake_filter
            fake_analyzer = MagicMock(spec=object)
            fake_analysis = MagicMock(spec=object)
            fake_analyzer.analyze = MagicMock(return_value=fake_analysis)
            fake_analyzer_cls.return_value = fake_analyzer

            AuditAnalysisOps.audit_log_analysis()

        fake_analyzer.analyze.assert_called_once_with(
            fake_filtered, "7 days"
        )  # WHY: analyzer called with filtered+desc.
        fake_render.assert_called_once_with(fake_analysis)  # WHY: rendering delegated to helper method.
        out = capsys.readouterr().out
        assert "Retrieved 3 raw entries" in out  # WHY: raw entry count printed.
        assert "Filtered: 2 kept, 1 noise removed" in out  # WHY: filter summary printed.
