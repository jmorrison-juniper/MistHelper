"""Unit tests for continuous monitoring + org-level upgrade jobs display.

Why:
    Monitoring is the operator's live-view into fleet firmware rollouts;
    any regression in the poll-print-sleep loop, the "active upgrade"
    classifier, or the org-jobs detail rendering surfaces immediately in
    an operator-visible way. Every branch of these helpers must be pinned
    against silent refactor drift so field-ops tooling and grep-based
    dashboards keep working.
"""

from __future__ import annotations

import logging
import sys
import types
from typing import Any
from unittest.mock import MagicMock

import pytest

import src.firmware.firmware_manager as fm_mod
from src.firmware.firmware_manager import FirmwareManager, FirmwareManagerConfig


def _make_manager(**overrides: Any) -> FirmwareManager:
    """Build a live ``FirmwareManager`` with the smallest valid config.

    Why:
        Monitoring/org-jobs helpers need a real instance to bind
        ``self.apisession`` and ``self.org_id`` for API calls, but they
        never touch the MSP privilege chain or the DI hooks. Keeping the
        constructor in one place lets each test focus on the branch it
        exercises.

    Args:
        **overrides: Any ``FirmwareManagerConfig`` field to override.

    Returns:
        A fully wired ``FirmwareManager`` ready to exercise helpers.
    """
    defaults: dict[str, Any] = {"apisession": object(), "org_id": "org-mon"}
    defaults.update(overrides)
    return FirmwareManager(FirmwareManagerConfig(**defaults))


_CHECK_CALL_CEILING = 40  # WHY: far above the retry limit. A regression trips this instead of hanging.


class _ScriptedCheck:
    """Return a scripted list of status-check results and refuse to run forever.

    Why:
        Before issue #1910 the monitoring loop retried a failed check
        forever. A plain endless fake would hang the whole test suite, so
        this helper raises after a hard call ceiling. A regression then
        fails fast with a readable message instead of blocking CI.
    """

    def __init__(self, results: list[int | None]) -> None:
        """Store the scripted results and reset the call counter.

        Args:
            results: One result per call. The last result repeats forever.
        """
        self.results = results  # WHY: drive one loop iteration per entry
        self.calls = 0  # WHY: the tests assert how many checks the loop ran

    def __call__(self, _site_filter: str | None) -> int | None:
        """Return the next scripted result and count the call."""
        self.calls += 1  # WHY: record this iteration before any early exit
        if self.calls > _CHECK_CALL_CEILING:  # WHY: the loop must stop long before this point
            raise AssertionError(f"the monitoring loop ran {self.calls} checks and did not stop")
        if self.calls <= len(self.results):  # WHY: still inside the scripted part
            return self.results[self.calls - 1]  # WHY: scripts are 0-indexed, calls start at 1
        return self.results[-1]  # WHY: hold the final state so a broken loop keeps failing


def _wire_monitoring_loop(mgr: FirmwareManager, monkeypatch: pytest.MonkeyPatch, check: _ScriptedCheck) -> list[int]:
    """Silence the screen work, inject the scripted check, and capture the sleeps.

    Args:
        mgr: The manager under test.
        monkeypatch: The pytest patching fixture.
        check: The scripted status check to inject.

    Returns:
        A list that collects every delay the loop passes to ``time.sleep``.
    """
    delays: list[int] = []  # WHY: the backoff assertions read the recorded delays
    monkeypatch.setattr(mgr, "_clear_monitoring_screen", lambda: None)  # WHY: no terminal reset in a test
    monkeypatch.setattr(mgr, "_present_monitoring_iteration_header", lambda _i: None)  # WHY: quiet banner
    monkeypatch.setattr(mgr, "_execute_monitoring_check", check)  # WHY: control every check result
    monkeypatch.setattr(fm_mod.time, "sleep", lambda seconds: delays.append(seconds))  # WHY: run fast
    return delays  # WHY: hand the recorder to the caller


class TestPresentMonitoringHeader:
    """``_present_monitoring_header`` banner block.

    Why:
        Operators read the fixed banner to confirm they're in continuous
        mode and to see the 7-second cadence disclosure. Reformatting or
        dropping any line would silently mislead operators, so all six
        content lines and the two dividers are pinned.
    """

    def test_prints_all_expected_banner_lines(
        self, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO, logger="root")
        _make_manager()._present_monitoring_header()
        out = capsys.readouterr().out
        assert "Continuous Monitoring Mode" in out
        assert "Monitoring active firmware upgrades..." in out
        assert "Press Ctrl+C to exit at any time" in out
        assert "Auto-refreshing every 7 seconds" in out
        assert "NOTE: Each refresh scans ALL devices for active upgrades" in out
        assert out.count("=" * 70) == 2  # WHY: opening + closing dividers
        assert any("Starting continuous monitoring mode" in r.message for r in caplog.records)


class TestPresentMonitoringIterationHeader:
    """``_present_monitoring_iteration_header`` per-refresh banner."""

    def test_uses_iteration_number(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._present_monitoring_iteration_header(42)
        out = capsys.readouterr().out
        assert "Firmware Upgrade Monitoring - Live View" in out
        assert "Refresh #42 | Press Ctrl+C to exit" in out
        assert "Scanning all devices for active upgrades..." in out


class TestClearMonitoringScreen:
    """``_clear_monitoring_screen`` platform dispatch.

    Why:
        The wrong screen-clear command is silently ignored on the other
        platform, leaving stale text on screen. Both branches must be
        exercised with a mocked ``os.system`` so tests never fork a
        subprocess.
    """

    def test_windows_calls_cls(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import os
        import platform

        calls: list[str] = []
        monkeypatch.setattr(platform, "system", lambda: "Windows")
        monkeypatch.setattr(os, "system", lambda cmd: calls.append(cmd) or 0)
        _make_manager()._clear_monitoring_screen()
        assert calls == ["cls"]

    def test_posix_calls_clear(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import os
        import platform

        calls: list[str] = []
        monkeypatch.setattr(platform, "system", lambda: "Linux")
        monkeypatch.setattr(os, "system", lambda cmd: calls.append(cmd) or 0)
        _make_manager()._clear_monitoring_screen()
        assert calls == ["clear"]


class TestHandleMonitoringResult:
    """``_handle_monitoring_result`` three-way branch.

    Why:
        The return value drives loop exit: ``True`` means done, ``False``
        means "keep polling". Confusing these two returns silently wedges
        the monitoring loop or exits it early.
    """

    def test_none_result_prints_error_and_continues(
        self, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.WARNING, logger="root")
        assert _make_manager()._handle_monitoring_result(None, 3) is False
        out = capsys.readouterr().out
        assert "Error fetching upgrade status." in out
        assert any("Monitoring iteration 3 failed" in r.message for r in caplog.records)

    def test_zero_result_signals_completion(
        self, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.INFO, logger="root")
        assert _make_manager()._handle_monitoring_result(0, 5) is True
        out = capsys.readouterr().out
        assert "All upgrades completed!" in out
        assert "No active firmware upgrades detected." in out
        assert "Exiting monitoring mode." in out
        assert any("Monitoring mode exiting" in r.message for r in caplog.records)

    def test_positive_result_prints_progress_and_continues(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert _make_manager()._handle_monitoring_result(4, 2) is False
        out = capsys.readouterr().out
        assert "Found 4 device(s) actively upgrading" in out
        assert "Next refresh in 7 seconds..." in out


class TestRunMonitoringLoop:
    """``_run_monitoring_loop`` drive-through with mocked collaborators."""

    def test_exits_when_handler_returns_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_clear_monitoring_screen", lambda: None)
        monkeypatch.setattr(mgr, "_present_monitoring_iteration_header", lambda _i: None)
        monkeypatch.setattr(mgr, "_execute_monitoring_check", lambda _sf: 0)
        # If time.sleep were reached the test would hang; force the loop to exit first.
        monkeypatch.setattr(fm_mod.time, "sleep", lambda _s: (_ for _ in ()).throw(AssertionError("slept")))
        mgr._run_monitoring_loop("site-x")

    def test_loops_until_zero_upgrades(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        iterations = {"n": 0}

        def fake_check(_sf: str | None) -> int:
            iterations["n"] += 1
            return 2 if iterations["n"] < 3 else 0  # WHY: emulate two "still upgrading" then done

        monkeypatch.setattr(mgr, "_clear_monitoring_screen", lambda: None)
        monkeypatch.setattr(mgr, "_present_monitoring_iteration_header", lambda _i: None)
        monkeypatch.setattr(mgr, "_execute_monitoring_check", fake_check)
        monkeypatch.setattr(fm_mod.time, "sleep", lambda _s: None)  # WHY: no real sleep
        mgr._run_monitoring_loop(None)
        assert iterations["n"] == 3


class TestContinuousMonitoringMode:
    """``_continuous_monitoring_mode`` outer wrapper w/ KeyboardInterrupt."""

    def test_normal_exit_calls_run_loop(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        header = MagicMock()
        loop = MagicMock()
        monkeypatch.setattr(mgr, "_present_monitoring_header", header)
        monkeypatch.setattr(mgr, "_run_monitoring_loop", loop)
        mgr._continuous_monitoring_mode("site-a")
        header.assert_called_once_with()
        loop.assert_called_once_with("site-a")

    def test_keyboard_interrupt_prints_cancel_banner(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_present_monitoring_header", lambda: None)

        def raise_kb(_sf: str | None) -> None:
            raise KeyboardInterrupt

        monkeypatch.setattr(mgr, "_run_monitoring_loop", raise_kb)
        assert mgr._continuous_monitoring_mode(None) == fm_mod.MONITOR_EXIT_CANCELLED
        assert "Monitoring mode cancelled by user." in capsys.readouterr().out

    def test_returns_the_loop_exit_code(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_present_monitoring_header", lambda: None)
        monkeypatch.setattr(mgr, "_run_monitoring_loop", lambda _sf: fm_mod.MONITOR_EXIT_FAILED)
        assert mgr._continuous_monitoring_mode("site-a") == fm_mod.MONITOR_EXIT_FAILED


class TestMonitoringRetryPolicy:
    """``MonitoringRetryPolicy`` failure counting and backoff growth.

    Why:
        The policy is the only guard that stops an endless retry loop when
        the Mist API stays down (issue #1910). A wrong counter ends a
        healthy watch too early. A missing cap keeps a request going to an
        unhealthy API every few seconds.
    """

    def test_healthy_delay_matches_the_documented_cadence(self) -> None:
        policy = fm_mod.MonitoringRetryPolicy()
        assert policy.consecutive_failures == 0
        assert policy.next_delay_seconds() == fm_mod.MONITOR_REFRESH_SECONDS

    def test_delay_grows_and_stops_at_the_cap(self) -> None:
        policy = fm_mod.MonitoringRetryPolicy()
        delays: list[int] = []
        for _ in range(8):  # WHY: more failures than the cap needs, so the ceiling is visible
            policy.record_failure()
            delays.append(policy.next_delay_seconds())
        assert delays[0] == fm_mod.MONITOR_BACKOFF_BASE_SECONDS
        assert delays[1] == fm_mod.MONITOR_BACKOFF_BASE_SECONDS * fm_mod.MONITOR_BACKOFF_MULTIPLIER
        assert delays == sorted(delays)  # WHY: the wait never shrinks while the failures continue
        assert max(delays) == fm_mod.MONITOR_BACKOFF_MAX_SECONDS

    def test_success_clears_the_failure_streak(self) -> None:
        policy = fm_mod.MonitoringRetryPolicy()
        policy.record_failure()
        policy.record_failure()
        policy.record_success()
        assert policy.consecutive_failures == 0
        assert policy.exhausted is False
        assert policy.next_delay_seconds() == fm_mod.MONITOR_REFRESH_SECONDS

    def test_exhausted_reports_true_at_the_limit(self) -> None:
        policy = fm_mod.MonitoringRetryPolicy()
        for _ in range(fm_mod.MONITOR_MAX_CONSECUTIVE_FAILURES - 1):
            assert policy.record_failure() < fm_mod.MONITOR_MAX_CONSECUTIVE_FAILURES
            assert policy.exhausted is False
        assert policy.record_failure() == fm_mod.MONITOR_MAX_CONSECUTIVE_FAILURES
        assert policy.exhausted is True


class TestRunMonitoringLoopRetryBound:
    """``_run_monitoring_loop`` bounded retry behavior (issue #1910).

    Why:
        An expired token or a Mist cloud outage made every status check
        fail. The loop retried forever and the operator saw no final
        error. These tests pin the attempt limit, the backoff, the reset
        after one good check, and the non-zero result.
    """

    @pytest.mark.timeout(15)
    def test_stops_after_the_consecutive_failure_limit(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.ERROR, logger="root")
        mgr = _make_manager()
        check = _ScriptedCheck([None])  # WHY: every check fails, like a revoked token
        delays = _wire_monitoring_loop(mgr, monkeypatch, check)
        exit_code = mgr._run_monitoring_loop("site-down")
        assert exit_code == fm_mod.MONITOR_EXIT_FAILED
        assert check.calls == fm_mod.MONITOR_MAX_CONSECUTIVE_FAILURES
        assert len(delays) == fm_mod.MONITOR_MAX_CONSECUTIVE_FAILURES - 1  # WHY: no sleep after the last check
        assert delays == sorted(delays)  # WHY: the backoff grows between the failed attempts
        assert max(delays) <= fm_mod.MONITOR_BACKOFF_MAX_SECONDS
        out = capsys.readouterr().out
        assert "MONITORING STOPPED" in out
        assert "Mist API token" in out  # WHY: the operator needs the next action, not only the error
        assert any("consecutive failed status checks" in r.message for r in caplog.records)

    @pytest.mark.timeout(15)
    def test_one_failure_then_success_keeps_watching(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mgr = _make_manager()
        # Four failures, one good check, four more failures, then the upgrade completes.
        # Without a reset the ninth check would exceed the limit and end the watch.
        check = _ScriptedCheck([None, None, None, None, 2, None, None, None, None, 0])
        delays = _wire_monitoring_loop(mgr, monkeypatch, check)
        exit_code = mgr._run_monitoring_loop(None)
        assert exit_code == fm_mod.MONITOR_EXIT_COMPLETE
        assert check.calls == 10
        assert delays[4] == fm_mod.MONITOR_REFRESH_SECONDS  # WHY: the good check restores the cadence
        assert delays[5] == fm_mod.MONITOR_BACKOFF_BASE_SECONDS  # WHY: the backoff restarts at the base
        assert "MONITORING STOPPED" not in capsys.readouterr().out

    @pytest.mark.timeout(15)
    def test_healthy_loop_keeps_the_seven_second_cadence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        check = _ScriptedCheck([3, 2, 1, 0])  # WHY: a normal upgrade that drains to zero
        delays = _wire_monitoring_loop(mgr, monkeypatch, check)
        assert mgr._run_monitoring_loop(None) == fm_mod.MONITOR_EXIT_COMPLETE
        assert delays == [fm_mod.MONITOR_REFRESH_SECONDS] * 3


class TestRecordMonitoringAttempt:
    """``_record_monitoring_attempt`` counter updates and the stop signal."""

    def test_success_resets_the_counter_and_continues(self) -> None:
        mgr = _make_manager()
        policy = fm_mod.MonitoringRetryPolicy()
        policy.record_failure()
        assert mgr._record_monitoring_attempt(4, policy, 2) is False
        assert policy.consecutive_failures == 0

    def test_failure_below_the_limit_continues(
        self, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        caplog.set_level(logging.WARNING, logger="root")
        mgr = _make_manager()
        policy = fm_mod.MonitoringRetryPolicy()
        assert mgr._record_monitoring_attempt(None, policy, 1) is False
        assert policy.consecutive_failures == 1
        assert "Retry 1 of" in capsys.readouterr().out
        assert any("status check failed" in r.message for r in caplog.records)


class TestPrintUpgradeJobTimingInfo:
    """``_print_upgrade_job_timing_info`` epoch formatting + fallback."""

    def test_prints_formatted_times(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_upgrade_job_timing_info({"start_time": 1_700_000_000, "reboot_at": 1_700_003_600})
        out = capsys.readouterr().out
        assert "Start Time:" in out
        assert "Reboot Time:" in out

    def test_missing_fields_render_nothing(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_upgrade_job_timing_info({})
        assert capsys.readouterr().out == ""

    def test_bad_epoch_falls_back_to_raw(self, capsys: pytest.CaptureFixture[str]) -> None:
        # Very large epoch triggers OverflowError inside fromtimestamp on some platforms;
        # a string value forces the except branch cleanly.
        _make_manager()._print_upgrade_job_timing_info({"start_time": "bad", "reboot_at": "bad"})
        out = capsys.readouterr().out
        assert "Start Time: bad (epoch)" in out
        assert "Reboot Time: bad (epoch)" in out


class TestPrintUpgradeJobP2pConfig:
    """``_print_upgrade_job_p2p_config`` conditional block behavior."""

    def test_p2p_disabled_only_prints_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_upgrade_job_p2p_config({"enable_p2p": False})
        out = capsys.readouterr().out
        assert "P2P Enabled: False" in out
        assert "Cluster Size" not in out

    def test_p2p_enabled_prints_cluster_and_parallelism(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_upgrade_job_p2p_config({"enable_p2p": True, "p2p_cluster_size": 4, "p2p_parallelism": 2})
        out = capsys.readouterr().out
        assert "P2P Enabled: True" in out
        assert "P2P Cluster Size: 4" in out
        assert "P2P Parallelism: 2" in out

    def test_optional_fields_render_when_present(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_upgrade_job_p2p_config(
            {"canary_phases": [1, 2], "max_failure_percentage": 0, "current_phase": 0}
        )
        out = capsys.readouterr().out
        assert "Canary Phases: [1, 2]" in out
        assert "Max Failure %: 0" in out  # WHY: 0 is a legitimate value
        assert "Current Phase: 0" in out  # WHY: 0 is a legitimate value


class TestPrintUpgradeJobProgressSummary:
    """``_print_upgrade_job_progress_summary`` progress + sites lines."""

    def test_prints_progress_line(self, capsys: pytest.CaptureFixture[str]) -> None:
        details = {
            "targets": {
                "total": 10,
                "upgraded": ["d1", "d2"],
                "downloaded": ["d3"],
                "download_requested": ["d4", "d5", "d6"],
            }
        }
        _make_manager()._print_upgrade_job_progress_summary(details)
        out = capsys.readouterr().out
        assert "Progress: 2/10 upgraded, 1 downloaded, 3 downloading" in out

    def test_prints_sites_when_present(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_upgrade_job_progress_summary({"upgrades": [{"a": 1}, {"b": 2}]})
        assert "Sites: 2 site upgrade(s)" in capsys.readouterr().out

    def test_empty_details_prints_nothing(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_upgrade_job_progress_summary({})
        assert capsys.readouterr().out == ""


class TestPrintUpgradeJobDetailBlock:
    """``_print_upgrade_job_detail_block`` orchestrator + error path."""

    def test_prints_all_sections_on_success(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mgr = _make_manager()
        api = MagicMock()
        api.getOrgDeviceUpgrade.return_value = types.SimpleNamespace(
            data={"status": "inprogress", "target_version": "6.3.5", "strategy": "rolling"}
        )
        called: list[str] = []
        monkeypatch.setattr(mgr, "_print_upgrade_job_timing_info", lambda _d: called.append("timing"))
        monkeypatch.setattr(mgr, "_print_upgrade_job_p2p_config", lambda _d: called.append("p2p"))
        monkeypatch.setattr(mgr, "_print_upgrade_job_progress_summary", lambda _d: called.append("prog"))
        mgr._print_upgrade_job_detail_block(api, "job-1")
        out = capsys.readouterr().out
        assert "Status: inprogress" in out
        assert "Target Version: 6.3.5" in out
        assert "Strategy: rolling" in out
        assert called == ["timing", "p2p", "prog"]

    def test_missing_data_short_circuits(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mgr = _make_manager()
        api = MagicMock()
        api.getOrgDeviceUpgrade.return_value = None
        mgr._print_upgrade_job_detail_block(api, "job-2")
        # Nothing should be printed and no exception raised.
        assert capsys.readouterr().out == ""

    def test_non_dict_data_uses_empty_dict(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mgr = _make_manager()
        api = MagicMock()
        api.getOrgDeviceUpgrade.return_value = types.SimpleNamespace(data=["not-a-dict"])
        monkeypatch.setattr(mgr, "_print_upgrade_job_timing_info", lambda _d: None)
        monkeypatch.setattr(mgr, "_print_upgrade_job_p2p_config", lambda _d: None)
        monkeypatch.setattr(mgr, "_print_upgrade_job_progress_summary", lambda _d: None)
        mgr._print_upgrade_job_detail_block(api, "job-3")
        out = capsys.readouterr().out
        assert "Status: Unknown" in out

    def test_error_path_prints_and_logs(
        self, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        mgr = _make_manager()
        api = MagicMock()
        api.getOrgDeviceUpgrade.side_effect = RuntimeError("boom")
        caplog.set_level(logging.ERROR, logger="root")
        mgr._print_upgrade_job_detail_block(api, "job-err")
        assert "Error fetching details: boom" in capsys.readouterr().out
        assert any("Error fetching upgrade job job-err" in r.message for r in caplog.records)


class TestFetchOrgUpgradeJobs:
    """``_fetch_org_upgrade_jobs`` API-wrapper contract.

    Why:
        The lazy ``import mistapi.api.v1.orgs.devices as org_devices_api``
        resolves via attribute-walk from the ``mistapi`` package, so
        overriding ``sys.modules`` alone is not enough — we replace the
        function attribute on the real submodule so the import returns a
        module whose ``listOrgDeviceUpgrades`` is our fake.
    """

    def test_returns_normalized_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.orgs.devices as real_api

        monkeypatch.setattr(
            real_api,
            "listOrgDeviceUpgrades",
            lambda _s, _o: types.SimpleNamespace(data=[{"id": "j1"}, {"id": "j2"}]),
        )
        api, jobs = _make_manager()._fetch_org_upgrade_jobs()
        assert api is real_api
        assert jobs == [{"id": "j1"}, {"id": "j2"}]

    def test_missing_data_returns_empty_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.orgs.devices as real_api

        monkeypatch.setattr(real_api, "listOrgDeviceUpgrades", lambda _s, _o: None)
        api, jobs = _make_manager()._fetch_org_upgrade_jobs()
        assert api is real_api
        assert jobs == []

    def test_non_list_data_normalized_to_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.orgs.devices as real_api

        monkeypatch.setattr(
            real_api,
            "listOrgDeviceUpgrades",
            lambda _s, _o: types.SimpleNamespace(data={"not": "a list"}),
        )
        _api, jobs = _make_manager()._fetch_org_upgrade_jobs()
        assert jobs == []


class TestRenderOrgUpgradeJobs:
    """``_render_org_upgrade_jobs`` per-job iteration."""

    def test_calls_detail_block_for_each_job(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        seen: list[str] = []
        monkeypatch.setattr(mgr, "_print_upgrade_job_detail_block", lambda _api, jid: seen.append(jid))
        mgr._render_org_upgrade_jobs(MagicMock(), [{"id": "a"}, {"id": "b"}])
        assert seen == ["a", "b"]

    def test_skips_records_without_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        seen: list[str] = []
        monkeypatch.setattr(mgr, "_print_upgrade_job_detail_block", lambda _api, jid: seen.append(jid))
        mgr._render_org_upgrade_jobs(MagicMock(), [{"other": "x"}, {"id": None}, {"id": "keep"}])
        assert seen == ["keep"]

    def test_supports_object_style_jobs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        seen: list[str] = []
        monkeypatch.setattr(mgr, "_print_upgrade_job_detail_block", lambda _api, jid: seen.append(jid))
        obj = types.SimpleNamespace(id="objid")
        mgr._render_org_upgrade_jobs(MagicMock(), [obj])
        assert seen == ["objid"]


class TestShowOrgLevelUpgradeJobs:
    """``_show_org_level_upgrade_jobs`` end-to-end orchestrator."""

    def test_empty_list_prints_none_found(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_fetch_org_upgrade_jobs", lambda: (MagicMock(), []))
        render = MagicMock()
        monkeypatch.setattr(mgr, "_render_org_upgrade_jobs", render)
        mgr._show_org_level_upgrade_jobs()
        out = capsys.readouterr().out
        assert "No org-level upgrade jobs found." in out
        render.assert_not_called()

    def test_non_empty_list_renders_and_finalizes(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mgr = _make_manager()
        api = MagicMock()
        monkeypatch.setattr(mgr, "_fetch_org_upgrade_jobs", lambda: (api, [{"id": "j"}]))
        render = MagicMock()
        monkeypatch.setattr(mgr, "_render_org_upgrade_jobs", render)
        mgr._show_org_level_upgrade_jobs()
        out = capsys.readouterr().out
        assert "Found 1 org-level upgrade job(s)" in out
        assert "Org-level upgrade job details complete." in out
        render.assert_called_once_with(api, [{"id": "j"}])

    def test_exception_prints_error(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        mgr = _make_manager()

        def blow(*_a: Any, **_k: Any) -> None:
            raise RuntimeError("boom")

        monkeypatch.setattr(mgr, "_fetch_org_upgrade_jobs", blow)
        caplog.set_level(logging.ERROR, logger="root")
        mgr._show_org_level_upgrade_jobs()
        assert "Error fetching org-level upgrades: boom" in capsys.readouterr().out
        assert any("Error in _show_org_level_upgrade_jobs" in r.message for r in caplog.records)


class TestFetchDeviceStatsForMonitoring:
    """``_fetch_device_stats_for_monitoring`` branch selection."""

    def test_site_filter_uses_site_stats(self, monkeypatch: pytest.MonkeyPatch) -> None:
        seen: dict[str, Any] = {}

        def site_stats(_ses: Any, site_id: str, **kw: Any) -> str:
            seen["site"] = (site_id, kw)
            return "site-resp"

        fake_mistapi = types.SimpleNamespace(
            api=types.SimpleNamespace(
                v1=types.SimpleNamespace(
                    sites=types.SimpleNamespace(stats=types.SimpleNamespace(listSiteDevicesStats=site_stats)),
                    orgs=types.SimpleNamespace(stats=types.SimpleNamespace(listOrgDevicesStats=None)),
                )
            ),
            get_all=lambda response, mist_session: f"all-of-{response}",
        )
        monkeypatch.setattr(fm_mod, "mistapi", fake_mistapi)
        got = _make_manager()._fetch_device_stats_for_monitoring("site-1")
        assert got == "all-of-site-resp"
        assert seen["site"][0] == "site-1"
        assert seen["site"][1]["type"] == "all"
        assert seen["site"][1]["limit"] == 1000

    def test_no_site_filter_uses_org_stats(self, monkeypatch: pytest.MonkeyPatch) -> None:
        seen: dict[str, Any] = {}

        def org_stats(_ses: Any, org_id: str, **kw: Any) -> str:
            seen["org"] = (org_id, kw)
            return "org-resp"

        fake_mistapi = types.SimpleNamespace(
            api=types.SimpleNamespace(
                v1=types.SimpleNamespace(
                    sites=types.SimpleNamespace(stats=types.SimpleNamespace(listSiteDevicesStats=None)),
                    orgs=types.SimpleNamespace(stats=types.SimpleNamespace(listOrgDevicesStats=org_stats)),
                )
            ),
            get_all=lambda response, mist_session: f"all-of-{response}",
        )
        monkeypatch.setattr(fm_mod, "mistapi", fake_mistapi)
        got = _make_manager(org_id="ORG-Z")._fetch_device_stats_for_monitoring(None)
        assert got == "all-of-org-resp"
        assert seen["org"][0] == "ORG-Z"
        assert seen["org"][1]["fields"] == "*"


class TestIsActiveFwUpdate:
    """``_is_active_fw_update`` classifier + stale 100% guard."""

    def test_non_active_status_is_false(self) -> None:
        assert _make_manager()._is_active_fw_update({"status": "success", "progress": 100}) is False

    @pytest.mark.parametrize("verb", ["inprogress", "upgrading", "downloading"])
    def test_active_status_true(self, verb: str) -> None:
        assert _make_manager()._is_active_fw_update({"status": verb, "progress": 50}) is True

    def test_fresh_100_percent_is_active(self, monkeypatch: pytest.MonkeyPatch) -> None:
        now = 1_700_000_000
        monkeypatch.setattr(fm_mod.time, "time", lambda: now)
        rec = {"status": "inprogress", "progress": 100, "timestamp": now - 60}
        assert _make_manager()._is_active_fw_update(rec) is True

    def test_stale_100_percent_is_inactive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        now = 1_700_000_000
        monkeypatch.setattr(fm_mod.time, "time", lambda: now)
        # 2 hours old -> stale beyond 1-hour cutoff.
        rec = {"status": "inprogress", "progress": 100, "timestamp": now - 7200}
        assert _make_manager()._is_active_fw_update(rec) is False

    def test_bad_timestamp_leaves_active_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # A string epoch triggers TypeError in the subtraction -> except keeps active True.
        rec = {"status": "inprogress", "progress": 100, "timestamp": "bad"}
        assert _make_manager()._is_active_fw_update(rec) is True


class TestGetActiveUpgradesFromStats:
    """``_get_active_upgrades_from_stats`` filter + projection."""

    def test_filters_out_inactive_and_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        stats = [
            {"name": "a", "type": "ap", "model": "AP32", "fwupdate": {"status": "inprogress", "progress": 42}},
            {"name": "b", "type": "ap", "model": "AP32"},  # WHY: no fwupdate -> skip
            {
                "name": "c",
                "type": "switch",
                "model": "EX4400",
                "fwupdate": {"status": "success", "progress": 100},  # WHY: not active
            },
        ]
        result = mgr._get_active_upgrades_from_stats(stats)
        assert result == [{"name": "a", "type": "ap", "model": "AP32", "progress": 42, "status": "inprogress"}]

    def test_projection_defaults_when_fields_missing(self) -> None:
        stats = [{"fwupdate": {"status": "upgrading"}}]
        result = _make_manager()._get_active_upgrades_from_stats(stats)
        assert result == [
            {
                "name": "Unnamed",
                "type": "unknown",
                "model": "Unknown",
                "progress": 0,
                "status": "upgrading",
            }
        ]


class TestPrintActiveUpgradesTable:
    """``_print_active_upgrades_table`` header + DisplayUtils fallback."""

    def test_empty_list_returns_silently(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_active_upgrades_table([])
        assert capsys.readouterr().out == ""

    def test_no_main_module_uses_blank_progress(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Remove both main + MistHelper from sys.modules so _main_d is None.
        monkeypatch.delitem(sys.modules, "__main__", raising=False)
        monkeypatch.delitem(sys.modules, "MistHelper", raising=False)
        rec = [{"name": "sw1", "type": "switch", "model": "EX4400", "progress": 30, "status": "upgrading"}]
        _make_manager()._print_active_upgrades_table(rec)
        out = capsys.readouterr().out
        assert "Devices Currently Upgrading:" in out
        assert "Device Name" in out and "Progress" in out
        assert "sw1" in out and "switch" in out and "EX4400" in out and "upgrading" in out

    def test_with_display_utils_renders_progress_bar(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        fake_main = types.SimpleNamespace(
            DisplayUtils=types.SimpleNamespace(create_progress_bar=lambda pct, bar_length: f"[BAR-{pct}]")
        )
        monkeypatch.setitem(sys.modules, "__main__", fake_main)
        rec = [{"name": "ap1", "type": "ap", "model": "AP32", "progress": 55, "status": "upgrading"}]
        _make_manager()._print_active_upgrades_table(rec)
        out = capsys.readouterr().out
        assert "[BAR-55]" in out


class TestExecuteMonitoringCheck:
    """``_execute_monitoring_check`` orchestrator + error-safety."""

    def test_returns_active_count(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_fetch_device_stats_for_monitoring", lambda _sf: ["stat1", "stat2"])
        monkeypatch.setattr(mgr, "_get_active_upgrades_from_stats", lambda _s: [{"name": "a"}, {"name": "b"}])
        monkeypatch.setattr(mgr, "_print_active_upgrades_table", lambda _r: None)
        assert mgr._execute_monitoring_check("site-x") == 2

    def test_returns_none_on_exception(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        mgr = _make_manager()

        def blow(_sf: str | None) -> None:
            raise RuntimeError("fetch fail")

        monkeypatch.setattr(mgr, "_fetch_device_stats_for_monitoring", blow)
        caplog.set_level(logging.ERROR, logger="root")
        assert mgr._execute_monitoring_check(None) is None
        assert any("Error in monitoring check" in r.message for r in caplog.records)
