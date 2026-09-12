"""Version comparison + scope prompt/dispatch unit tests.

Why:
    Version comparison is safety-critical: mis-classifying an upgrade as
    a downgrade would silently block operators from rolling firmware
    forward. Scope prompt and dispatch route the whole ``check_firmware_
    upgrade_status`` entry point, so every branch of the router has to
    stay pinned.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.firmware.firmware_manager import FirmwareManager, FirmwareManagerConfig


def _make_manager(**overrides: Any) -> FirmwareManager:
    """Build a ``FirmwareManager`` with a valid minimum config.

    Why:
        Version helpers and scope prompt only need a live manager
        instance — no real API session, no MSP privileges, no template
        cache. Keeping construction in one place avoids re-stating the
        identity fields in every test.

    Args:
        **overrides: Any config field to override.

    Returns:
        A live ``FirmwareManager`` ready to exercise helpers.
    """
    defaults: dict[str, Any] = {"apisession": object(), "org_id": "org-test"}
    defaults.update(overrides)
    return FirmwareManager(FirmwareManagerConfig(**defaults))


class TestNormalizeVersionParts:
    """``_normalize_version_parts`` pads and splits version strings.

    Why:
        The zero-pad step is what makes ``6.3`` and ``6.3.5`` comparable
        instead of triggering a spurious IndexError downstream.
    """

    def test_equal_length_versions_unpadded(self) -> None:
        mgr = _make_manager()
        left, right = mgr._normalize_version_parts("1.2.3", "1.2.4")
        assert left == ["1", "2", "3"]
        assert right == ["1", "2", "4"]

    def test_shorter_current_is_zero_padded(self) -> None:
        mgr = _make_manager()
        left, right = mgr._normalize_version_parts("1.2", "1.2.3.4")
        assert left == ["1", "2", "0", "0"]
        assert right == ["1", "2", "3", "4"]

    def test_shorter_target_is_zero_padded(self) -> None:
        mgr = _make_manager()
        left, right = mgr._normalize_version_parts("1.2.3.4", "1.2")
        assert left == ["1", "2", "3", "4"]
        assert right == ["1", "2", "0", "0"]

    def test_suffix_after_dash_is_dropped(self) -> None:
        mgr = _make_manager()
        left, right = mgr._normalize_version_parts("6.3.4-7.r2", "6.3.5-37.sts")
        assert left == ["6", "3", "4"]
        assert right == ["6", "3", "5"]


class TestCompareScalarPair:
    """``_compare_scalar_pair`` three-way comparison."""

    def test_target_less_is_downgrade(self) -> None:
        assert _make_manager()._compare_scalar_pair(1, 2) is True

    def test_target_greater_is_upgrade(self) -> None:
        assert _make_manager()._compare_scalar_pair(3, 2) is False

    def test_target_equal_returns_none(self) -> None:
        assert _make_manager()._compare_scalar_pair(2, 2) is None

    def test_string_comparison_supported(self) -> None:
        # Lexical fallback path — used when int cast fails.
        assert _make_manager()._compare_scalar_pair("a", "b") is True
        assert _make_manager()._compare_scalar_pair("b", "a") is False


class TestCompareSingleVersionPair:
    """``_compare_single_version_pair`` numeric-with-lexical-fallback."""

    def test_numeric_downgrade(self) -> None:
        assert _make_manager()._compare_single_version_pair("5", "3") is True

    def test_numeric_upgrade(self) -> None:
        assert _make_manager()._compare_single_version_pair("3", "5") is False

    def test_numeric_equal(self) -> None:
        assert _make_manager()._compare_single_version_pair("3", "3") is None

    def test_lexical_fallback_when_non_numeric(self) -> None:
        # "abc" and "abd" trigger the ValueError fallback.
        mgr = _make_manager()
        assert mgr._compare_single_version_pair("abd", "abc") is True
        assert mgr._compare_single_version_pair("abc", "abd") is False


class TestCompareVersionParts:
    """``_compare_version_parts`` iterates until a verdict is reached."""

    def test_all_equal_returns_false(self) -> None:
        assert _make_manager()._compare_version_parts(["1", "2", "3"], ["1", "2", "3"]) is False

    def test_stops_at_first_definitive(self) -> None:
        # Middle segment decides: 2 < 3 -> current has greater middle -> downgrade.
        assert _make_manager()._compare_version_parts(["1", "3", "5"], ["1", "2", "9"]) is True

    def test_upgrade_verdict(self) -> None:
        assert _make_manager()._compare_version_parts(["1", "2", "3"], ["1", "3", "0"]) is False


class TestIsFirmwareDowngrade:
    """Public downgrade classifier — wires normalise+compare together."""

    def test_empty_current_returns_false(self) -> None:
        assert _make_manager()._is_firmware_downgrade("", "1.0") is False

    def test_empty_target_returns_false(self) -> None:
        assert _make_manager()._is_firmware_downgrade("1.0", "") is False

    def test_true_downgrade(self) -> None:
        assert _make_manager()._is_firmware_downgrade("6.3.5", "6.3.4") is True

    def test_upgrade_returns_false(self) -> None:
        assert _make_manager()._is_firmware_downgrade("6.3.5", "6.3.6") is False

    def test_equal_versions_return_false(self) -> None:
        assert _make_manager()._is_firmware_downgrade("6.3.5", "6.3.5") is False

    def test_ssr_style_suffix_ignored(self) -> None:
        # 6.3.5 vs 6.3.4 (with -N.sts suffixes) — downgrade.
        assert _make_manager()._is_firmware_downgrade("6.3.5-37.sts", "6.3.4-7.r2") is True

    def test_exception_path_returns_false_and_logs(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        mgr = _make_manager()

        def blow_up(*_a: Any, **_k: Any) -> tuple[list[str], list[str]]:
            raise RuntimeError("boom")

        monkeypatch.setattr(mgr, "_normalize_version_parts", blow_up)
        caplog.set_level(logging.WARNING, logger="root")
        assert mgr._is_firmware_downgrade("1.0", "2.0") is False
        assert any("Could not compare versions" in r.message for r in caplog.records)


class TestPromptScopeSelection:
    """Scope prompt loop: valid range, retry, KeyboardInterrupt cancel."""

    @pytest.mark.parametrize("choice", ["1", "2", "3", "4", "5", "6"])
    def test_returns_valid_choice(self, capsys: pytest.CaptureFixture[str], choice: str) -> None:
        prompts: list[str] = []

        def fake_input(prompt: str, context: str = "") -> str:
            prompts.append(prompt)
            return choice

        mgr = _make_manager(safe_input_fn=fake_input)
        assert mgr._prompt_scope_selection() == choice
        out = capsys.readouterr().out
        assert "Select status check scope" in out
        assert prompts and "Select scope" in prompts[0]

    def test_retries_on_invalid_then_accepts(self, capsys: pytest.CaptureFixture[str]) -> None:
        answers = iter(["7", "0", "3"])

        def fake_input(_prompt: str, context: str = "") -> str:
            return next(answers)

        mgr = _make_manager(safe_input_fn=fake_input)
        assert mgr._prompt_scope_selection() == "3"
        out = capsys.readouterr().out
        assert out.count("Invalid selection. Please choose 1-6.") == 2

    def test_keyboard_interrupt_returns_none(self, capsys: pytest.CaptureFixture[str]) -> None:
        def fake_input(*_a: Any, **_k: Any) -> str:
            raise KeyboardInterrupt

        mgr = _make_manager(safe_input_fn=fake_input)
        assert mgr._prompt_scope_selection() is None
        assert "Operation cancelled by user" in capsys.readouterr().out


class TestResolveScopeChoice:
    """``_resolve_scope_choice`` passthrough vs prompt."""

    def test_passthrough_when_provided(self) -> None:
        mgr = _make_manager()
        assert mgr._resolve_scope_choice("1") == "1"

    def test_prompts_when_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_prompt_scope_selection", lambda: "4")
        assert mgr._resolve_scope_choice(None) == "4"


class TestResolveSiteFilterForStatus:
    """``_resolve_site_filter_for_status`` prompts only when scope=2."""

    def test_non_scope_2_passthrough(self) -> None:
        mgr = _make_manager()
        assert mgr._resolve_site_filter_for_status("1", None) is None
        assert mgr._resolve_site_filter_for_status("3", "sf") == "sf"

    def test_scope_2_with_existing_filter_passthrough(self) -> None:
        mgr = _make_manager()
        assert mgr._resolve_site_filter_for_status("2", "already-set") == "already-set"

    def test_scope_2_no_hook_returns_none_and_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        mgr = _make_manager(select_site_fn=None)
        caplog.set_level(logging.ERROR, logger="root")
        assert mgr._resolve_site_filter_for_status("2", None) is None
        assert any("select_site_fn not configured" in r.message for r in caplog.records)

    def test_scope_2_empty_selection_returns_none(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager(select_site_fn=lambda: None)
        assert mgr._resolve_site_filter_for_status("2", None) is None
        assert "No site selected" in capsys.readouterr().out

    def test_scope_2_valid_selection_returned(self) -> None:
        mgr = _make_manager(select_site_fn=lambda: "site-abc")
        assert mgr._resolve_site_filter_for_status("2", None) == "site-abc"


class TestDispatchStatusScope:
    """Route from scope choice to correct handler."""

    def test_scope_5_calls_monitoring_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        called = MagicMock()
        monkeypatch.setattr(mgr, "_continuous_monitoring_mode", called)
        mgr._dispatch_status_scope("5", "site-x")
        called.assert_called_once_with("site-x")

    def test_scope_6_calls_show_org_jobs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        called = MagicMock()
        monkeypatch.setattr(mgr, "_show_org_level_upgrade_jobs", called)
        mgr._dispatch_status_scope("6", None)
        called.assert_called_once_with()

    def test_default_calls_execute_status_check(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        called = MagicMock()
        monkeypatch.setattr(mgr, "_execute_status_check", called)
        mgr._dispatch_status_scope("1", "sf")
        called.assert_called_once_with("1", "sf")


class TestCheckFirmwareUpgradeStatus:
    """End-to-end orchestrator with fully mocked collaborators."""

    def test_cancelled_scope_returns_early(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_resolve_scope_choice", lambda _s: None)
        dispatch = MagicMock()
        monkeypatch.setattr(mgr, "_dispatch_status_scope", dispatch)
        assert mgr.check_firmware_upgrade_status() is None
        dispatch.assert_not_called()

    def test_scope_2_cancelled_returns_early(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_resolve_scope_choice", lambda _s: "2")
        monkeypatch.setattr(mgr, "_resolve_site_filter_for_status", lambda _s, _f: None)
        dispatch = MagicMock()
        monkeypatch.setattr(mgr, "_dispatch_status_scope", dispatch)
        assert mgr.check_firmware_upgrade_status() is None
        dispatch.assert_not_called()

    def test_happy_path_dispatches(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_resolve_scope_choice", lambda _s: "1")
        monkeypatch.setattr(mgr, "_resolve_site_filter_for_status", lambda _s, _f: None)
        dispatch = MagicMock()
        monkeypatch.setattr(mgr, "_dispatch_status_scope", dispatch)
        mgr.check_firmware_upgrade_status()
        dispatch.assert_called_once_with("1", None)


class TestExecuteStatusCheck:
    """``_execute_status_check`` save/restore module apisession + runs checker.

    Why:
        The co-located FirmwareUpgradeStatusChecker reads the bare
        ``apisession`` module global. Missing the save/restore around it
        would leak the previous caller's session and (worse) skew audit
        logs. The try/finally block is safety-critical.
    """

    def test_runs_checker_with_bound_session_and_restores(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.firmware.firmware_manager as fm_mod

        instance_session = object()
        mgr = _make_manager(apisession=instance_session)
        # Set the sentinel AFTER construction — __init__ rebinds the module
        # global to the instance session, so we must override it here to
        # verify the save/restore contract of _execute_status_check itself.
        sentinel_prev = object()
        monkeypatch.setattr(fm_mod, "apisession", sentinel_prev)

        observed: dict[str, Any] = {}

        class _FakeChecker:
            def __init__(self, scope: str, site: str | None) -> None:
                observed["scope"] = scope
                observed["site"] = site
                observed["session_during_init"] = fm_mod.apisession

            def check(self) -> None:
                observed["ran"] = True

        monkeypatch.setattr(fm_mod, "FirmwareUpgradeStatusChecker", _FakeChecker)
        mgr._execute_status_check("3", "sf")
        assert observed == {
            "scope": "3",
            "site": "sf",
            "session_during_init": instance_session,
            "ran": True,
        }
        assert fm_mod.apisession is sentinel_prev

    def test_restores_apisession_even_on_checker_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.firmware.firmware_manager as fm_mod

        mgr = _make_manager(apisession=object())
        # Reset the module global AFTER __init__ rebound it.
        sentinel_prev = object()
        monkeypatch.setattr(fm_mod, "apisession", sentinel_prev)

        class _BadChecker:
            def __init__(self, _s: str, _f: str | None) -> None:
                pass

            def check(self) -> None:
                raise RuntimeError("boom")

        monkeypatch.setattr(fm_mod, "FirmwareUpgradeStatusChecker", _BadChecker)
        with pytest.raises(RuntimeError):
            mgr._execute_status_check("1", None)
        assert fm_mod.apisession is sentinel_prev

    def test_emits_audit_logs(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        import src.firmware.firmware_manager as fm_mod

        mgr = _make_manager()

        class _NoopChecker:
            def __init__(self, *_a: Any, **_k: Any) -> None:
                pass

            def check(self) -> None:
                pass

        monkeypatch.setattr(fm_mod, "FirmwareUpgradeStatusChecker", _NoopChecker)
        caplog.set_level(logging.DEBUG, logger="root")
        mgr._execute_status_check("2", "site-x")
        messages = [r.message for r in caplog.records]
        assert any("Dispatching status check (scope=2, site_filter=site-x)" in m for m in messages)
        assert any("Status check dispatch complete" in m for m in messages)
