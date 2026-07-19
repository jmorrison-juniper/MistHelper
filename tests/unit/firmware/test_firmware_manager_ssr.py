"""Switch-mode + full SSR firmware upgrade flow unit tests.

Why:
    The SSR upgrade path is the most destructive operation in the whole
    tool — it reboots WAN routers and can drop branch offices offline.
    Every branch of the input validation, verdict classification, error
    interpretation and dispatch orchestration must be pinned or a
    silent regression could turn a controlled maintenance window into
    an outage. The switch mode-selection helpers share the same
    ``_safe_input_fn`` retry contract so they are covered here too.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

import src.firmware.firmware_manager as fm_mod
from src.firmware.firmware_manager import FirmwareManager, FirmwareManagerConfig


def _make_manager(**overrides: Any) -> FirmwareManager:
    """Build a ``FirmwareManager`` with a valid minimum config.

    Why:
        Every helper under test needs a live manager but only reads
        ``self.apisession`` / ``self.org_id`` (or one of the DI hooks).
        Centralising construction keeps each test focused on the
        branch it exercises.

    Args:
        **overrides: Any config field to override.

    Returns:
        A live ``FirmwareManager`` ready for helper invocation.
    """
    defaults: dict[str, Any] = {"apisession": object(), "org_id": "org-test"}
    defaults.update(overrides)
    return FirmwareManager(FirmwareManagerConfig(**defaults))


def _snapshot_session() -> tuple[Any, str]:
    """Snapshot ``(apisession, org_id)`` module globals.

    Why:
        ``FirmwareManager.__init__`` rebinds these; tests that depend
        on the pre-existing values must restore them to avoid leaking
        state into the next test.

    Returns:
        A pair of ``(apisession, org_id)`` values.
    """
    return fm_mod.apisession, fm_mod.org_id


def _restore_session(snap: tuple[Any, str]) -> None:
    """Restore the module-scope session captured by ``_snapshot_session``.

    Args:
        snap: The pair captured by ``_snapshot_session``.
    """
    fm_mod.apisession, fm_mod.org_id = snap


class _FakeResponse:
    """Minimal mistapi response stand-in.

    Why:
        Every SSR helper reads ``status_code`` + ``data`` off the
        response object; some also fall through to ``text``/``content``.
        A hand-rolled stand-in avoids importing ``requests`` just to
        wire up a test.
    """

    def __init__(
        self,
        status_code: int = 200,
        data: Any = None,
        text: str | None = None,
        content: bytes | None = None,
    ) -> None:
        """Store the pieces the SSR helpers read.

        Args:
            status_code: Response status.
            data: Parsed JSON payload.
            text: Optional textual body.
            content: Optional raw bytes body.
        """
        self.status_code = status_code
        self.data = data
        if text is not None:
            self.text = text
        if content is not None:
            self.content = content


# ==============================================================================
# SWITCH MODE SELECTION HELPERS
# ==============================================================================


class TestPrintSwitchUpgradeBanner:
    """``_print_switch_upgrade_banner`` operator hazard header."""

    def test_prints_expected_banner_lines(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_switch_upgrade_banner()
        out = capsys.readouterr().out
        assert "Advanced Switch Firmware Upgrade" in out
        assert "DESTRUCTIVE OPERATION WARNING" in out
        assert "Reboot switches during upgrade process" in out
        assert "Require recovery snapshots for Junos devices" in out


class TestPrintSwitchModeMenu:
    """``_print_switch_mode_menu`` shows the 1/2 menu."""

    def test_menu_lines_emitted(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_switch_mode_menu()
        out = capsys.readouterr().out
        assert "Select upgrade mode" in out
        assert "[1] By Site" in out
        assert "[2] By Gateway Template" in out


class TestPromptSwitchUpgradeMode:
    """Loop until 1|2; EOF/interrupt returns None."""

    @pytest.mark.parametrize("choice", ["1", "2"])
    def test_returns_valid_choice(self, choice: str) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: choice)
        assert mgr._prompt_switch_upgrade_mode() == choice

    def test_retries_on_invalid(self, capsys: pytest.CaptureFixture[str]) -> None:
        answers = iter(["x", "0", "1"])
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: next(answers))
        assert mgr._prompt_switch_upgrade_mode() == "1"
        assert "Invalid selection. Please choose 1 or 2." in capsys.readouterr().out

    @pytest.mark.parametrize("exc", [EOFError, KeyboardInterrupt])
    def test_returns_none_on_interrupt(self, capsys: pytest.CaptureFixture[str], exc: type[BaseException]) -> None:
        def raise_exc(*_a: Any, **_k: Any) -> str:
            raise exc()

        mgr = _make_manager(safe_input_fn=raise_exc)
        assert mgr._prompt_switch_upgrade_mode() is None
        assert "Operation cancelled by user" in capsys.readouterr().out


class TestDispatchSwitchUpgradeMode:
    """Route validated 1|2 to site or template flow."""

    def test_mode_1_calls_site_flow(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        called = MagicMock()
        monkeypatch.setattr(mgr, "_bulk_upgrade_switch_firmware_by_site", called)
        mgr._dispatch_switch_upgrade_mode("1")
        called.assert_called_once_with()
        assert "Site-based switch upgrade mode selected" in capsys.readouterr().out

    def test_mode_2_calls_template_flow(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mgr = _make_manager()
        called = MagicMock()
        monkeypatch.setattr(mgr, "_upgrade_switch_firmware_by_gateway_template", called)
        mgr._dispatch_switch_upgrade_mode("2")
        called.assert_called_once_with()
        assert "Template-based switch upgrade mode selected" in capsys.readouterr().out


class TestExecuteSwitchFirmwareUpgradeWithModeSelection:
    """Full switch upgrade orchestrator wiring."""

    def test_early_return_on_none_mode(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_print_switch_upgrade_banner", lambda: None)
        monkeypatch.setattr(mgr, "_print_switch_mode_menu", lambda: None)
        monkeypatch.setattr(mgr, "_prompt_switch_upgrade_mode", lambda: None)
        dispatch = MagicMock()
        monkeypatch.setattr(mgr, "_dispatch_switch_upgrade_mode", dispatch)
        assert mgr.execute_switch_firmware_upgrade_with_mode_selection() is None
        dispatch.assert_not_called()

    def test_happy_path_dispatches(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_print_switch_upgrade_banner", lambda: None)
        monkeypatch.setattr(mgr, "_print_switch_mode_menu", lambda: None)
        monkeypatch.setattr(mgr, "_prompt_switch_upgrade_mode", lambda: "1")
        dispatch = MagicMock()
        monkeypatch.setattr(mgr, "_dispatch_switch_upgrade_mode", dispatch)
        mgr.execute_switch_firmware_upgrade_with_mode_selection()
        dispatch.assert_called_once_with("1")


class TestBulkUpgradeSwitchFirmwareBySite:
    """Lazy import + delegate to ``BulkSwitchFirmwareUpgrader``."""

    def test_delegates_to_bulk_switch_upgrader(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        import src.firmware.bulk_switch_upgrader as bsu

        captured: dict[str, Any] = {}

        class FakeImpl:
            def __init__(self, **kwargs: Any) -> None:
                captured.update(kwargs)

            def execute(self) -> None:
                captured["executed"] = True

        monkeypatch.setattr(bsu, "BulkSwitchFirmwareUpgrader", FakeImpl)
        mgr._bulk_upgrade_switch_firmware_by_site(sites_to_upgrade_override=[{"id": "s1"}])
        assert captured["org_id"] == "org-test"
        assert captured["executed"] is True
        assert captured["sites_override"] == [{"id": "s1"}]


class TestUpgradeSwitchFirmwareByGatewayTemplate:
    """Template flow: banner + prepare + select + execute."""

    def test_returns_none_when_prepare_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_print_switch_template_banner", lambda: None)
        monkeypatch.setattr(mgr, "_prepare_template_upgrade", lambda _k: None)
        exec_mock = MagicMock()
        monkeypatch.setattr(mgr, "_execute_template_based_switch_upgrade", exec_mock)
        assert mgr._upgrade_switch_firmware_by_gateway_template() is None
        exec_mock.assert_not_called()

    def test_returns_none_when_selection_declined(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_print_switch_template_banner", lambda: None)
        monkeypatch.setattr(mgr, "_prepare_template_upgrade", lambda _k: ({}, {}))
        monkeypatch.setattr(mgr, "_select_template_and_sites", lambda *_a: None)
        exec_mock = MagicMock()
        monkeypatch.setattr(mgr, "_execute_template_based_switch_upgrade", exec_mock)
        assert mgr._upgrade_switch_firmware_by_gateway_template() is None
        exec_mock.assert_not_called()

    def test_happy_path_dispatches(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_print_switch_template_banner", lambda: None)
        monkeypatch.setattr(mgr, "_prepare_template_upgrade", lambda _k: ({"t": "1"}, {"1": [{"id": "s1"}]}))
        monkeypatch.setattr(mgr, "_select_template_and_sites", lambda *_a: ("tpl", [{"id": "s1"}]))
        exec_mock = MagicMock()
        monkeypatch.setattr(mgr, "_execute_template_based_switch_upgrade", exec_mock)
        mgr._upgrade_switch_firmware_by_gateway_template()
        exec_mock.assert_called_once_with([{"id": "s1"}], "tpl")


class TestPrintSwitchTemplateBanner:
    """``_print_switch_template_banner`` operator title."""

    def test_prints_banner(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_switch_template_banner()
        out = capsys.readouterr().out
        assert "Advanced Switch Firmware Upgrade by Gateway Template" in out
        assert "=" * 70 in out


class TestExecuteTemplateBasedSwitchUpgrade:
    """Template-driven switch upgrade prints headers + delegates."""

    def test_calls_bulk_switch_with_override(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mgr = _make_manager()
        called = MagicMock()
        monkeypatch.setattr(mgr, "_bulk_upgrade_switch_firmware_by_site", called)
        sites = [{"id": "s1"}, {"id": "s2"}]
        mgr._execute_template_based_switch_upgrade(sites, "TMPL")
        called.assert_called_once_with(sites)
        out = capsys.readouterr().out
        assert "template: TMPL" in out
        assert "Target sites: 2" in out


# ==============================================================================
# SSR MODE ENTRY + WARNING HELPERS
# ==============================================================================


class TestPrintSSRHazardsBlock:
    """SSR hazards banner content."""

    def test_prints_hazards(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_ssr_hazards_block()
        out = capsys.readouterr().out
        assert "Advanced SSR Firmware Upgrade" in out
        assert "CRITICAL ROUTING INFRASTRUCTURE WARNING" in out
        assert "Reboot Session Smart Routers" in out
        assert "Impact tunnel establishment and failover" in out


class TestPrintSSRPrecautionsBlock:
    """SSR precautions + mode-selector banner."""

    def test_prints_precautions_and_menu(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_ssr_precautions_block()
        out = capsys.readouterr().out
        assert "RECOMMENDED PRECAUTIONS" in out
        assert "Schedule maintenance windows" in out
        assert "Select upgrade mode" in out
        assert "[1] By Site" in out
        assert "[2] By Gateway Template" in out


class TestPresentSSRUpgradeWarning:
    """Combined banner + precautions dispatch."""

    def test_calls_both_blocks(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        h = MagicMock()
        p = MagicMock()
        monkeypatch.setattr(mgr, "_print_ssr_hazards_block", h)
        monkeypatch.setattr(mgr, "_print_ssr_precautions_block", p)
        mgr._present_ssr_upgrade_warning()
        h.assert_called_once_with()
        p.assert_called_once_with()


class TestPromptSSRModeSelection:
    """Mode prompt loop and cancel semantics."""

    @pytest.mark.parametrize("choice", ["1", "2"])
    def test_returns_valid_choice(self, choice: str) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: choice)
        assert mgr._prompt_ssr_mode_selection() == choice

    def test_retries_on_invalid(self, capsys: pytest.CaptureFixture[str]) -> None:
        answers = iter(["", "x", "2"])
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: next(answers))
        assert mgr._prompt_ssr_mode_selection() == "2"
        assert "Invalid selection" in capsys.readouterr().out

    @pytest.mark.parametrize("exc", [EOFError, KeyboardInterrupt])
    def test_returns_none_on_interrupt(self, capsys: pytest.CaptureFixture[str], exc: type[BaseException]) -> None:
        def raise_exc(*_a: Any, **_k: Any) -> str:
            raise exc()

        mgr = _make_manager(safe_input_fn=raise_exc)
        assert mgr._prompt_ssr_mode_selection() is None
        assert "Operation cancelled by user" in capsys.readouterr().out


class TestDispatchSSRUpgradeMode:
    """Route validated mode to site or template flow."""

    def test_mode_1_returns_site_result(
        self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_bulk_upgrade_ssr_firmware_by_site", lambda: {"upgraded": 3})
        result = mgr._dispatch_ssr_upgrade_mode("1")
        assert result == {"upgraded": 3}
        assert "Site-based SSR upgrade mode selected" in capsys.readouterr().out

    def test_mode_2_returns_none(self, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        called = MagicMock()
        monkeypatch.setattr(mgr, "_upgrade_ssr_firmware_by_gateway_template", called)
        assert mgr._dispatch_ssr_upgrade_mode("2") is None
        called.assert_called_once_with()
        assert "Template-based SSR upgrade mode selected" in capsys.readouterr().out


class TestExecuteSSRFirmwareUpgradeWithModeSelection:
    """Orchestrator: warning + prompt + dispatch."""

    def test_returns_none_on_prompt_cancel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_present_ssr_upgrade_warning", lambda: None)
        monkeypatch.setattr(mgr, "_prompt_ssr_mode_selection", lambda: None)
        dispatch = MagicMock()
        monkeypatch.setattr(mgr, "_dispatch_ssr_upgrade_mode", dispatch)
        assert mgr.execute_ssr_firmware_upgrade_with_mode_selection() is None
        dispatch.assert_not_called()

    def test_returns_dispatch_result(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_present_ssr_upgrade_warning", lambda: None)
        monkeypatch.setattr(mgr, "_prompt_ssr_mode_selection", lambda: "1")
        monkeypatch.setattr(mgr, "_dispatch_ssr_upgrade_mode", lambda _c: {"x": 1})
        assert mgr.execute_ssr_firmware_upgrade_with_mode_selection() == {"x": 1}


# ==============================================================================
# ORG VALIDATION
# ==============================================================================


class TestValidateOrgForSSRUpgrade:
    """``_validate_org_for_ssr_upgrade`` handles success/error/exception."""

    def test_success_returns_org_name(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        import mistapi.api.v1.orgs.orgs as real_orgs

        monkeypatch.setattr(
            real_orgs,
            "getOrg",
            lambda _s, _o: _FakeResponse(200, {"name": "MyOrg"}),
        )
        mgr = _make_manager()
        name, err = mgr._validate_org_for_ssr_upgrade()
        assert name == "MyOrg"
        assert err is None
        assert "MyOrg" in capsys.readouterr().out

    def test_non_200_returns_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.orgs.orgs as real_orgs

        monkeypatch.setattr(real_orgs, "getOrg", lambda _s, _o: _FakeResponse(500, {}))
        mgr = _make_manager()
        name, err = mgr._validate_org_for_ssr_upgrade()
        assert name == ""
        assert err == {"error": "Organization access failed"}

    def test_exception_returns_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.orgs.orgs as real_orgs

        def raise_exc(*_a: Any, **_k: Any) -> Any:
            raise RuntimeError("boom")

        monkeypatch.setattr(real_orgs, "getOrg", raise_exc)
        mgr = _make_manager()
        name, err = mgr._validate_org_for_ssr_upgrade()
        assert name == ""
        assert err is not None and "Organization validation error" in err["error"]


# ==============================================================================
# SITE SELECTION HELPERS
# ==============================================================================


class TestPromptSSRSiteSelection:
    """A/S/C site selection menu."""

    def test_choice_a_returns_all(self, capsys: pytest.CaptureFixture[str]) -> None:
        sites = [{"id": "s1", "name": "S1"}, {"id": "s2", "name": "S2"}]
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "A")
        selected, err = mgr._prompt_ssr_site_selection(sites)
        assert selected == sites
        assert err is None
        assert "Selected all 2 sites" in capsys.readouterr().out

    def test_choice_a_case_insensitive(self) -> None:
        sites = [{"id": "s1"}]
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "a")
        selected, err = mgr._prompt_ssr_site_selection(sites)
        assert selected == sites and err is None

    def test_choice_c_cancels(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "C")
        selected, err = mgr._prompt_ssr_site_selection([{"id": "s1"}])
        assert selected == []
        assert err == {"cancelled": True}
        assert "Operation cancelled by user" in capsys.readouterr().out

    def test_choice_s_delegates_to_parser(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "S")
        sites = [{"id": "s1"}]
        monkeypatch.setattr(mgr, "_parse_ssr_site_selection", lambda s: (s, None))
        selected, err = mgr._prompt_ssr_site_selection(sites)
        assert selected == sites and err is None

    def test_invalid_choice_returns_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "Q")
        selected, err = mgr._prompt_ssr_site_selection([{"id": "s1"}])
        assert selected == []
        assert err == {"error": "Invalid selection"}
        assert "Invalid selection" in capsys.readouterr().out


class TestParseSSRSiteSelection:
    """Site index/range parser: valid tokens vs exception path."""

    def test_valid_range_selection(self, capsys: pytest.CaptureFixture[str]) -> None:
        sites = [{"id": f"s{i}"} for i in range(5)]
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "1-3")
        selected, err = mgr._parse_ssr_site_selection(sites)
        assert len(selected) == 3
        assert err is None
        assert "Selected 3 sites" in capsys.readouterr().out

    def test_invalid_input_returns_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "abc")
        selected, err = mgr._parse_ssr_site_selection([{"id": "s1"}])
        assert selected == []
        assert err == {"error": "Invalid site selection"}
        assert "Invalid site selection" in capsys.readouterr().out


class TestResolveSSRSiteTokens:
    """Comma-separated site token resolver."""

    def test_single_index(self) -> None:
        sites = [{"id": f"s{i}"} for i in range(5)]
        result = _make_manager()._resolve_ssr_site_tokens("2", sites)
        assert result == [{"id": "s1"}]

    def test_range(self) -> None:
        sites = [{"id": f"s{i}"} for i in range(5)]
        result = _make_manager()._resolve_ssr_site_tokens("1-3", sites)
        assert result == [{"id": "s0"}, {"id": "s1"}, {"id": "s2"}]

    def test_mixed_tokens_and_blanks(self) -> None:
        sites = [{"id": f"s{i}"} for i in range(5)]
        result = _make_manager()._resolve_ssr_site_tokens("1, ,3", sites)
        assert result == [{"id": "s0"}, {"id": "s2"}]

    def test_out_of_range_ignored(self) -> None:
        sites = [{"id": f"s{i}"} for i in range(3)]
        result = _make_manager()._resolve_ssr_site_tokens("99", sites)
        assert result == []


class TestExtendSitesFromToken:
    """``_extend_sites_from_token`` per-token appender."""

    def test_single_valid(self) -> None:
        sites = [{"id": f"s{i}"} for i in range(5)]
        buffer: list[dict[str, Any]] = []
        _make_manager()._extend_sites_from_token("3", sites, buffer)
        assert buffer == [{"id": "s2"}]

    def test_single_out_of_range(self) -> None:
        sites = [{"id": "s0"}]
        buffer: list[dict[str, Any]] = []
        _make_manager()._extend_sites_from_token("99", sites, buffer)
        assert buffer == []

    def test_range_inclusive(self) -> None:
        sites = [{"id": f"s{i}"} for i in range(5)]
        buffer: list[dict[str, Any]] = []
        _make_manager()._extend_sites_from_token("2-4", sites, buffer)
        assert buffer == [{"id": "s1"}, {"id": "s2"}, {"id": "s3"}]


class TestSelectSSRSitesForUpgrade:
    """Site selection driver: override / discover / error."""

    def test_override_short_circuits(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        override = [{"id": "s1"}, {"id": "s2"}]
        selected, err = mgr._select_ssr_sites_for_upgrade(override)
        assert selected == override and err is None
        assert "Using provided site list: 2 sites" in capsys.readouterr().out

    def test_discovery_success_delegates_to_prompt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        real_sites = fm_mod.mistapi.api.v1.orgs.sites

        monkeypatch.setattr(
            real_sites,
            "listOrgSites",
            lambda _s, _o: _FakeResponse(200, [{"id": "s1", "name": "S1"}]),
        )
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_prompt_ssr_site_selection", lambda sites: (sites, None))
        selected, err = mgr._select_ssr_sites_for_upgrade(None)
        assert selected == [{"id": "s1", "name": "S1"}] and err is None

    def test_discovery_non_200_returns_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        real_sites = fm_mod.mistapi.api.v1.orgs.sites

        monkeypatch.setattr(real_sites, "listOrgSites", lambda _s, _o: _FakeResponse(500, []))
        mgr = _make_manager()
        selected, err = mgr._select_ssr_sites_for_upgrade(None)
        assert selected == []
        assert err == {"error": "Failed to retrieve sites"}

    def test_exception_returns_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        real_sites = fm_mod.mistapi.api.v1.orgs.sites

        def boom(*_a: Any, **_k: Any) -> Any:
            raise RuntimeError("net-down")

        monkeypatch.setattr(real_sites, "listOrgSites", boom)
        mgr = _make_manager()
        selected, err = mgr._select_ssr_sites_for_upgrade(None)
        assert selected == []
        assert err is not None and "Site discovery error" in err["error"]


# ==============================================================================
# UPGRADE PARAMETER SELECTION
# ==============================================================================


class TestSelectSSRUpgradeStrategy:
    """Serial vs big-bang strategy prompt."""

    def test_serial(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "1")
        assert mgr._select_ssr_upgrade_strategy() == "serial"

    def test_big_bang(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "2")
        assert mgr._select_ssr_upgrade_strategy() == "big_bang"
        assert "Big bang" in capsys.readouterr().out

    def test_retries_on_bad_input(self) -> None:
        answers = iter(["9", "", "1"])
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: next(answers))
        assert mgr._select_ssr_upgrade_strategy() == "serial"


class TestSelectSSRRebootTiming:
    """Auto vs manual reboot flag."""

    def test_auto(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "1")
        assert mgr._select_ssr_reboot_timing() is True

    def test_manual(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "2")
        assert mgr._select_ssr_reboot_timing() is False
        assert "manual reboot" in capsys.readouterr().out.lower()

    def test_retries_on_bad_input(self) -> None:
        answers = iter(["x", "1"])
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: next(answers))
        assert mgr._select_ssr_reboot_timing() is True


class TestSelectSSRFirmwareChannel:
    """Stable/beta/alpha channel selection."""

    @pytest.mark.parametrize("choice,expected", [("1", "stable"), ("2", "beta"), ("3", "alpha")])
    def test_channel_choices(self, choice: str, expected: str) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: choice)
        assert mgr._select_ssr_firmware_channel() == expected

    def test_alpha_warning_printed(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "3")
        mgr._select_ssr_firmware_channel()
        assert "alpha channel contains development" in capsys.readouterr().out

    def test_retries_on_bad_input(self) -> None:
        answers = iter(["", "4", "2"])
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: next(answers))
        assert mgr._select_ssr_firmware_channel() == "beta"


class TestSetupSSRUpgradeParams:
    """Assemble strategy + reboot + channel into a bundle."""

    def test_returns_bundle(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_select_ssr_upgrade_strategy", lambda: "serial")
        monkeypatch.setattr(mgr, "_select_ssr_reboot_timing", lambda: True)
        monkeypatch.setattr(mgr, "_select_ssr_firmware_channel", lambda: "stable")
        params = mgr._setup_ssr_upgrade_params()
        assert params == {"strategy": "serial", "auto_reboot": True, "channel": "stable"}

    def test_returns_none_when_strategy_cancelled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Cancel path: strategy prompt returns None -> reboot/channel are
        # never called and the caller receives None so it can abort cleanly
        # instead of firing a partial-config upgrade.
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_select_ssr_upgrade_strategy", lambda: None)
        reboot_calls: list[int] = []
        channel_calls: list[int] = []
        monkeypatch.setattr(mgr, "_select_ssr_reboot_timing", lambda: reboot_calls.append(1) or True)
        monkeypatch.setattr(mgr, "_select_ssr_firmware_channel", lambda: channel_calls.append(1) or "stable")
        assert mgr._setup_ssr_upgrade_params() is None
        assert reboot_calls == []
        assert channel_calls == []


# ==============================================================================
# VERSION FETCH / NORMALIZE / SUMMARY
# ==============================================================================


class TestFetchSSRVersionRows:
    """Raw version rows: success / non-200 / empty data."""

    def test_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.orgs.ssr as real_ssr

        monkeypatch.setattr(
            real_ssr,
            "listOrgAvailableSsrVersions",
            lambda _s, _o, channel=None: _FakeResponse(200, [{"version": "6.3.5"}]),
        )
        mgr = _make_manager()
        rows = mgr._fetch_ssr_version_rows("stable")
        assert rows == [{"version": "6.3.5"}]

    def test_non_200_returns_none(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        import mistapi.api.v1.orgs.ssr as real_ssr

        monkeypatch.setattr(
            real_ssr,
            "listOrgAvailableSsrVersions",
            lambda _s, _o, channel=None: _FakeResponse(503, None),
        )
        mgr = _make_manager()
        assert mgr._fetch_ssr_version_rows("stable") is None
        assert "Error retrieving SSR firmware versions" in capsys.readouterr().out

    def test_none_data_becomes_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.orgs.ssr as real_ssr

        monkeypatch.setattr(
            real_ssr,
            "listOrgAvailableSsrVersions",
            lambda _s, _o, channel=None: _FakeResponse(200, None),
        )
        mgr = _make_manager()
        assert mgr._fetch_ssr_version_rows("stable") == []


class TestParseSingleSSRVersionRow:
    """Dict / string / other row shapes."""

    def test_dict_with_all_fields(self) -> None:
        row = {"version": "6.3.5", "package": "pkgX", "default": True}
        assert _make_manager()._parse_single_ssr_version_row(row) == row

    def test_dict_missing_fields_defaults(self) -> None:
        result = _make_manager()._parse_single_ssr_version_row({"version": "6.3"})
        assert result == {"version": "6.3", "package": "SSR", "default": False}

    def test_dict_missing_version_returns_none(self) -> None:
        # empty/missing "version" is falsy so returns None
        assert _make_manager()._parse_single_ssr_version_row({}) is None

    def test_string_row_minimal_shape(self) -> None:
        assert _make_manager()._parse_single_ssr_version_row("6.3.5") == {
            "version": "6.3.5",
            "package": "SSR",
            "default": False,
        }

    def test_unrecognized_returns_none(self) -> None:
        assert _make_manager()._parse_single_ssr_version_row(42) is None


class TestNormalizeSSRVersionRows:
    """Normalize raw list into a uniform list of dicts."""

    def test_mixed_rows_filter_bad(self) -> None:
        rows: list[Any] = [
            {"version": "6.3.5"},
            "6.3.4",
            None,
            42,
            {"missing": "version"},
        ]
        result = _make_manager()._normalize_ssr_version_rows(rows)
        assert result == [
            {"version": "6.3.5", "package": "SSR", "default": False},
            {"version": "6.3.4", "package": "SSR", "default": False},
        ]


class TestPrintSSRVersionSummary:
    """Version summary shows count or empty warning."""

    def test_empty_warns(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_ssr_version_summary([], "stable")
        assert "No SSR firmware versions" in capsys.readouterr().out

    def test_count_summary(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_ssr_version_summary([{"version": "1"}, {"version": "2"}], "stable")
        out = capsys.readouterr().out
        assert "Found 2" in out and "stable" in out


class TestGetSSRAvailableVersions:
    """End-to-end version discovery orchestrator."""

    def test_returns_empty_on_fetch_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_fetch_ssr_version_rows", lambda _c: None)
        assert mgr._get_ssr_available_versions("stable") == []

    def test_returns_normalized_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_fetch_ssr_version_rows", lambda _c: [{"version": "6.3.5"}])
        result = mgr._get_ssr_available_versions("stable")
        assert result == [{"version": "6.3.5", "package": "SSR", "default": False}]


# ==============================================================================
# INVENTORY COLLECTION
# ==============================================================================


class TestIsSSRInventoryRow:
    """Predicate: type/model based SSR detection."""

    def test_type_ssr_matches(self) -> None:
        assert _make_manager()._is_ssr_inventory_row({"type": "ssr"}) is True

    def test_model_ssr_matches(self) -> None:
        assert _make_manager()._is_ssr_inventory_row({"model": "SSR-100"}) is True

    def test_model_128t_matches(self) -> None:
        assert _make_manager()._is_ssr_inventory_row({"model": "128T-Router"}) is True

    def test_nothing_matches(self) -> None:
        assert _make_manager()._is_ssr_inventory_row({"type": "ap"}) is False


class TestCollectSSRRowMetadata:
    """Populate model/version sets from a row."""

    def test_populates_both_sets(self) -> None:
        models: set[str] = set()
        versions: set[str] = set()
        _make_manager()._collect_ssr_row_metadata({"model": "SSR-100", "version": "6.3.5"}, models, versions)
        assert models == {"SSR-100"}
        assert versions == {"6.3.5"}

    def test_empty_fields_skipped(self) -> None:
        models: set[str] = set()
        versions: set[str] = set()
        _make_manager()._collect_ssr_row_metadata({}, models, versions)
        assert not models and not versions


class TestCollectSSRInventoryData:
    """Aggregate count/models/versions across rows."""

    def test_mixed_rows(self) -> None:
        gws = [
            {"type": "ssr", "model": "SSR-100", "version": "6.3.5"},
            {"type": "gateway", "model": "SSR-200", "version": "6.3.4"},
            {"type": "ap", "model": "AP41"},
            {"type": "gateway", "model": "SRX", "version": "20"},
        ]
        count, models, versions = _make_manager()._collect_ssr_inventory_data(gws)
        assert count == 2
        assert models == {"SSR-100", "SSR-200"}
        assert versions == {"6.3.5", "6.3.4"}


class TestDisplaySSRInventoryStats:
    """Stats printer skips empty counts."""

    def test_zero_count_skipped(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._display_ssr_inventory_stats(0, set(), set())
        assert capsys.readouterr().out == ""

    def test_positive_count_prints(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._display_ssr_inventory_stats(2, {"M"}, {"1", "2"})
        out = capsys.readouterr().out
        assert "Found 2 SSR" in out
        assert "Models: M" in out
        assert "Current versions: 1, 2" in out


class TestDisplaySSRInventoryInfo:
    """Wrapper around ``getOrgInventory`` — silently swallows all errors."""

    def test_success_calls_stats(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.orgs.inventory as real_inv

        monkeypatch.setattr(
            real_inv,
            "getOrgInventory",
            lambda _s, _o, type=None: _FakeResponse(200, [{"type": "ssr", "model": "M"}]),
        )
        mgr = _make_manager()
        stats = MagicMock()
        monkeypatch.setattr(mgr, "_display_ssr_inventory_stats", stats)
        mgr._display_ssr_inventory_info()
        stats.assert_called_once()

    def test_non_200_no_stats(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.orgs.inventory as real_inv

        monkeypatch.setattr(real_inv, "getOrgInventory", lambda _s, _o, type=None: _FakeResponse(500))
        mgr = _make_manager()
        stats = MagicMock()
        monkeypatch.setattr(mgr, "_display_ssr_inventory_stats", stats)
        mgr._display_ssr_inventory_info()
        stats.assert_not_called()

    def test_exception_swallowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.orgs.inventory as real_inv

        def boom(*_a: Any, **_k: Any) -> Any:
            raise RuntimeError("net-down")

        monkeypatch.setattr(real_inv, "getOrgInventory", boom)
        # Should not raise; wrapper swallows.
        _make_manager()._display_ssr_inventory_info()


# ==============================================================================
# VERSION SELECTION UI
# ==============================================================================


class TestRenderSSRVersionMenu:
    """Numbered menu with default marker."""

    def test_marks_default(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._render_ssr_version_menu(
            [
                {"version": "6.3.5", "package": "SSR", "default": True},
                {"version": "6.3.4", "package": "SSR", "default": False},
            ]
        )
        out = capsys.readouterr().out
        assert "6.3.5" in out and "(default)" in out
        assert "6.3.4" in out


class TestResolveSSRVersionChoice:
    """Choice → version string, or None to retry."""

    def test_empty_returns_none(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert _make_manager()._resolve_ssr_version_choice("", [{"version": "1"}]) is None
        assert "Please enter a selection" in capsys.readouterr().out

    def test_non_numeric_returns_none(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert _make_manager()._resolve_ssr_version_choice("abc", [{"version": "1"}]) is None
        assert "valid number" in capsys.readouterr().out

    def test_out_of_range_returns_none(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert _make_manager()._resolve_ssr_version_choice("99", [{"version": "1"}]) is None
        assert "between 1 and 1" in capsys.readouterr().out

    def test_valid_returns_version(self) -> None:
        result = _make_manager()._resolve_ssr_version_choice("2", [{"version": "6.3.4"}, {"version": "6.3.5"}])
        assert result == "6.3.5"


class TestLoopSSRVersionInput:
    """Loop until a valid selection returns."""

    def test_retries_then_accepts(self, capsys: pytest.CaptureFixture[str]) -> None:
        answers = iter(["", "abc", "1"])
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: next(answers))
        assert mgr._loop_ssr_version_input([{"version": "6.3.5"}]) == "6.3.5"
        assert "Selected firmware version: 6.3.5" in capsys.readouterr().out


class TestSelectSSRVersionFromList:
    """End-to-end version selection UI."""

    def test_returns_selected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_render_ssr_version_menu", lambda _v: None)
        monkeypatch.setattr(mgr, "_loop_ssr_version_input", lambda _v: "6.3.5")
        assert mgr._select_ssr_version_from_list([{"version": "6.3.5"}]) == "6.3.5"


class TestFetchAndSelectSSRVersion:
    """Fetch → display inventory → select version."""

    def test_empty_versions_returns_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_get_ssr_available_versions", lambda _c: [])
        version, err = mgr._fetch_and_select_ssr_version("stable")
        assert version == ""
        assert err is not None and "No SSR firmware versions" in err["error"]

    def test_happy_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_get_ssr_available_versions", lambda _c: [{"version": "6.3.5"}])
        monkeypatch.setattr(mgr, "_display_ssr_inventory_info", lambda: None)
        monkeypatch.setattr(mgr, "_select_ssr_version_from_list", lambda _v: "6.3.5")
        version, err = mgr._fetch_and_select_ssr_version("stable")
        assert version == "6.3.5" and err is None

    def test_exception_returns_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()

        def boom(*_a: Any, **_k: Any) -> Any:
            raise RuntimeError("api-down")

        monkeypatch.setattr(mgr, "_get_ssr_available_versions", boom)
        version, err = mgr._fetch_and_select_ssr_version("stable")
        assert version == ""
        assert err is not None and "SSR firmware discovery error" in err["error"]


# ==============================================================================
# CONFIRMATION FLOW
# ==============================================================================


class TestPrintSSRUpgradeSummary:
    """Print upgrade summary block."""

    def test_prints_all_fields(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager(org_id="ORGX")
        mgr._print_ssr_upgrade_summary(
            "OrgName",
            [{"id": "s1"}, {"id": "s2"}],
            "6.3.5",
            {"channel": "stable", "strategy": "serial", "auto_reboot": True},
        )
        out = capsys.readouterr().out
        assert "ORGX" in out
        assert "OrgName" in out
        assert "Sites to upgrade: 2" in out
        assert "Target firmware: 6.3.5" in out
        assert "channel: stable" in out.lower()
        assert "Auto reboot: Yes" in out

    def test_auto_reboot_no(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_ssr_upgrade_summary(
            "O", [], "v", {"channel": "c", "strategy": "s", "auto_reboot": False}
        )
        assert "Auto reboot: No" in capsys.readouterr().out


class TestPrintSSRUpgradeWarning:
    """Print critical routing warning."""

    def test_prints_warning(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_ssr_upgrade_warning()
        out = capsys.readouterr().out
        assert "CRITICAL ROUTING INFRASTRUCTURE" in out
        assert "type: UPGRADE" in out


class TestReadSSRUpgradeConfirmation:
    """UPGRADE token strict match; SystemExit -> False."""

    def test_correct_token_true(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "UPGRADE")
        assert mgr._read_ssr_upgrade_confirmation() is True

    def test_wrong_token_false(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "no")
        assert mgr._read_ssr_upgrade_confirmation() is False
        assert "incorrect confirmation" in capsys.readouterr().out

    def test_systemexit_returns_false(self, capsys: pytest.CaptureFixture[str]) -> None:
        def raise_exit(*_a: Any, **_k: Any) -> str:
            raise SystemExit(1)

        mgr = _make_manager(safe_input_fn=raise_exit)
        assert mgr._read_ssr_upgrade_confirmation() is False
        assert "Operation cancelled" in capsys.readouterr().out


class TestConfirmSSRUpgrade:
    """Combined summary + warning + read."""

    def test_delegates_to_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_print_ssr_upgrade_summary", lambda *_a: None)
        monkeypatch.setattr(mgr, "_print_ssr_upgrade_warning", lambda: None)
        monkeypatch.setattr(mgr, "_read_ssr_upgrade_confirmation", lambda: True)
        assert mgr._confirm_ssr_upgrade("Org", [], "v", {}) is True


# ==============================================================================
# RESULTS ENVELOPE
# ==============================================================================


class TestBuildSSRUpgradeResults:
    """Initialize the upgrade results dict shape."""

    def test_shape(self) -> None:
        result = _make_manager()._build_ssr_upgrade_results(
            "6.3.5",
            {"strategy": "serial", "channel": "stable", "auto_reboot": True},
        )
        assert result["target_version"] == "6.3.5"
        assert result["strategy"] == "serial"
        assert result["channel"] == "stable"
        assert result["reboot"] is True
        assert result["sites_processed"] == 0
        assert result["ssrs_upgraded"] == 0
        assert result["errors"] == []
        assert result["site_results"] == []
        assert "start_time" in result
        assert result["operation_id"].startswith("ssr_upgrade_")


# ==============================================================================
# ORG INVENTORY LOADING
# ==============================================================================


class TestIsSSRGatewayRow:
    """Type/model discriminator for SSR gateway."""

    def test_type_ssr_true(self) -> None:
        assert _make_manager()._is_ssr_gateway_row("ssr", "") is True

    def test_model_ssr_true(self) -> None:
        assert _make_manager()._is_ssr_gateway_row("gateway", "SSR-100") is True

    def test_model_128t_true(self) -> None:
        assert _make_manager()._is_ssr_gateway_row("gateway", "128T") is True

    def test_neither_false(self) -> None:
        assert _make_manager()._is_ssr_gateway_row("ap", "AP41") is False


class TestSSREntryFromGateway:
    """Return (id, info) tuple for SSR row or None."""

    def test_ssr_gateway_returns_tuple(self) -> None:
        gw = {"type": "ssr", "model": "SSR-100", "id": "id-1", "version": "6.3.5", "site_id": "s"}
        result = _make_manager()._ssr_entry_from_gateway(gw)
        assert result is not None
        gid, info = result
        assert gid == "id-1"
        assert info == {"model": "SSR-100", "type": "ssr", "version": "6.3.5", "site_id": "s"}

    def test_non_ssr_returns_none(self) -> None:
        assert _make_manager()._ssr_entry_from_gateway({"type": "ap", "id": "x"}) is None

    def test_missing_id_returns_none(self) -> None:
        assert _make_manager()._ssr_entry_from_gateway({"type": "ssr"}) is None

    def test_non_string_id_returns_none(self) -> None:
        assert _make_manager()._ssr_entry_from_gateway({"type": "ssr", "id": 42}) is None


class TestExtractSSRDevicesFromGateways:
    """Filter gateway list down to SSR-keyed dict."""

    def test_mixed_list(self) -> None:
        gws = [
            {"type": "ssr", "id": "s1", "model": "SSR-100"},
            {"type": "ap", "id": "a1"},
            {"type": "gateway", "model": "SRX", "id": "g1"},
            {"type": "gateway", "model": "128T", "id": "g2"},
        ]
        result = _make_manager()._extract_ssr_devices_from_gateways(gws)
        assert set(result.keys()) == {"s1", "g2"}


class TestFetchOrgGatewayInventory:
    """Fetch gateway inventory: success/error/exception."""

    def test_success_returns_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.orgs.inventory as real_inv

        monkeypatch.setattr(
            real_inv,
            "getOrgInventory",
            lambda _s, _o, type=None: _FakeResponse(200, [{"id": "g1"}]),
        )
        assert _make_manager()._fetch_org_gateway_inventory() == [{"id": "g1"}]

    def test_exception_returns_none(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        import mistapi.api.v1.orgs.inventory as real_inv

        def boom(*_a: Any, **_k: Any) -> Any:
            raise RuntimeError("bad")

        monkeypatch.setattr(real_inv, "getOrgInventory", boom)
        assert _make_manager()._fetch_org_gateway_inventory() is None
        assert "Error validating SSR inventory" in capsys.readouterr().out

    def test_non_200_returns_none(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        import mistapi.api.v1.orgs.inventory as real_inv

        monkeypatch.setattr(
            real_inv,
            "getOrgInventory",
            lambda _s, _o, type=None: _FakeResponse(500),
        )
        assert _make_manager()._fetch_org_gateway_inventory() is None
        assert "Failed to validate SSR inventory" in capsys.readouterr().out

    def test_none_data_becomes_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.orgs.inventory as real_inv

        monkeypatch.setattr(
            real_inv,
            "getOrgInventory",
            lambda _s, _o, type=None: _FakeResponse(200, None),
        )
        assert _make_manager()._fetch_org_gateway_inventory() == []


class TestLoadOrgSSRInventory:
    """Load full org SSR inventory map."""

    def test_returns_empty_on_fetch_failure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_fetch_org_gateway_inventory", lambda: None)
        assert mgr._load_org_ssr_inventory() == {}

    def test_success_returns_filtered_map(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(
            mgr,
            "_fetch_org_gateway_inventory",
            lambda: [{"type": "ssr", "id": "s1", "model": "SSR-100"}],
        )
        result = mgr._load_org_ssr_inventory()
        assert list(result.keys()) == ["s1"]


# ==============================================================================
# SITE SSR DISCOVERY
# ==============================================================================


class TestIsSSRGateway:
    """Gateway-type + model pattern check."""

    def test_non_gateway_type_false(self) -> None:
        assert _make_manager()._is_ssr_gateway({"type": "ap", "model": "SSR-100"}, []) is False

    def test_ssr_in_model_true(self) -> None:
        assert _make_manager()._is_ssr_gateway({"type": "gateway", "model": "SSR-100"}, []) is True

    def test_pattern_match_true(self) -> None:
        assert _make_manager()._is_ssr_gateway({"type": "gateway", "model": "128T-x"}, ["128T"]) is True

    def test_no_match_false(self) -> None:
        assert _make_manager()._is_ssr_gateway({"type": "gateway", "model": "SRX"}, ["SSR", "128T"]) is False


class TestFetchSiteGatewayDevices:
    """Per-site device fetch."""

    def test_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.sites.devices as real_devs

        monkeypatch.setattr(
            real_devs,
            "listSiteDevices",
            lambda _s, _sid, type=None: _FakeResponse(200, [{"id": "d1"}]),
        )
        result = _make_manager()._fetch_site_gateway_devices("s1", "S1")
        assert result == [{"id": "d1"}]

    def test_non_200_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.sites.devices as real_devs

        monkeypatch.setattr(
            real_devs,
            "listSiteDevices",
            lambda _s, _sid, type=None: _FakeResponse(500),
        )
        assert _make_manager()._fetch_site_gateway_devices("s1", "S1") is None

    def test_none_data_becomes_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.sites.devices as real_devs

        monkeypatch.setattr(
            real_devs,
            "listSiteDevices",
            lambda _s, _sid, type=None: _FakeResponse(200, None),
        )
        assert _make_manager()._fetch_site_gateway_devices("s1", "S1") == []


class TestFilterDevicesBySSRModel:
    """Filter devices to SSR matches."""

    def test_mixed_list(self, capsys: pytest.CaptureFixture[str]) -> None:
        devices = [
            {"type": "gateway", "model": "SSR-100", "id": "d1"},
            {"type": "ap", "model": "SSR-x", "id": "d2"},
            {"type": "gateway", "model": "SRX", "id": "d3"},
        ]
        result = _make_manager()._filter_devices_by_ssr_model(devices, ["SSR"])
        assert [d["id"] for d in result] == ["d1"]
        assert "Identified SSR" in capsys.readouterr().out


class TestDiscoverSiteSSRDevices:
    """Site SSR discovery driver."""

    def test_fetch_none_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_fetch_site_gateway_devices", lambda _sid, _sn: None)
        assert mgr._discover_site_ssr_devices({"id": "s1", "name": "S1"}, ["SSR"]) == []

    def test_delegates_to_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(
            mgr,
            "_fetch_site_gateway_devices",
            lambda _sid, _sn: [{"id": "d1", "type": "gateway", "model": "SSR-100"}],
        )
        result = mgr._discover_site_ssr_devices({"id": "s1", "name": "S1"}, ["SSR"])
        assert [d["id"] for d in result] == ["d1"]


# ==============================================================================
# VALIDATE + CLASSIFY DEVICE
# ==============================================================================


class TestClassifySSRDeviceForUpgrade:
    """Four verdicts: missing / current / downgrade / upgrade."""

    def test_missing_verdict(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        result = mgr._classify_ssr_device_for_upgrade("missing-id", {}, "6.3.5")
        assert result == "missing"
        assert "not in SSR inventory" in capsys.readouterr().out

    def test_current_verdict(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        inv = {"d1": {"model": "SSR-100", "version": "6.3.5"}}
        result = mgr._classify_ssr_device_for_upgrade("d1", inv, "6.3.5")
        assert result == "current"
        assert "already at version" in capsys.readouterr().out

    def test_downgrade_verdict(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        inv = {"d1": {"model": "SSR-100", "version": "6.3.5"}}
        result = mgr._classify_ssr_device_for_upgrade("d1", inv, "6.3.4")
        assert result == "downgrade"
        assert "Downgrade detected" in capsys.readouterr().out

    def test_upgrade_verdict(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        inv = {"d1": {"model": "SSR-100", "version": "6.3.4"}}
        result = mgr._classify_ssr_device_for_upgrade("d1", inv, "6.3.5")
        assert result == "upgrade"
        assert "Upgrade needed" in capsys.readouterr().out


class TestValidateSSRDevicesForVersion:
    """Split ids into validated vs skipped lists."""

    def test_splits_by_verdict(self) -> None:
        mgr = _make_manager()
        inv = {
            "u": {"model": "M", "version": "6.3.4"},  # upgrade
            "c": {"model": "M", "version": "6.3.5"},  # current
        }
        validated, skipped = mgr._validate_ssr_devices_for_version(["u", "c", "missing"], inv, "6.3.5")
        assert validated == ["u"]
        assert set(skipped) == {"c", "missing"}


# ==============================================================================
# ERROR RESPONSE HANDLING
# ==============================================================================


class TestExtractSSRErrorText:
    """Priority: data > text > content > status code."""

    def test_data_wins(self) -> None:
        r = _FakeResponse(500, data={"detail": "bad"})
        assert _make_manager()._extract_ssr_error_text(r) == "{'detail': 'bad'}"

    def test_text_wins_when_no_data(self) -> None:
        r = _FakeResponse(500, data=None, text="oops")
        assert _make_manager()._extract_ssr_error_text(r) == "oops"

    def test_content_decoded_when_no_data_or_text(self) -> None:
        r = _FakeResponse(500, data=None, text="", content=b"payload")
        assert _make_manager()._extract_ssr_error_text(r) == "payload"

    def test_status_fallback(self) -> None:
        r = _FakeResponse(503)
        assert _make_manager()._extract_ssr_error_text(r) == "Status: 503"


class TestClassifySSRErrorText:
    """Route error text into skip_reason or error."""

    def test_already_at_version(self, capsys: pytest.CaptureFixture[str]) -> None:
        result: dict[str, Any] = {}
        _make_manager()._classify_ssr_error_text(
            "SSRs already at the requested fw version", "site-1", _FakeResponse(400), result
        )
        assert result == {"skip_reason": "already_at_version"}
        assert "already at target version" in capsys.readouterr().out

    def test_downgrade_not_allowed(self, capsys: pytest.CaptureFixture[str]) -> None:
        result: dict[str, Any] = {}
        _make_manager()._classify_ssr_error_text(
            "Downgrade fw version not allowed", "site-1", _FakeResponse(400), result
        )
        assert result == {"skip_reason": "downgrade_not_allowed"}
        assert "downgrade not allowed" in capsys.readouterr().out.lower()

    def test_case_insensitive_match(self) -> None:
        result: dict[str, Any] = {}
        _make_manager()._classify_ssr_error_text("ALREADY AT THE REQUESTED FW VERSION", "s", _FakeResponse(400), result)
        assert result.get("skip_reason") == "already_at_version"

    def test_generic_error_records_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        result: dict[str, Any] = {}
        _make_manager()._classify_ssr_error_text("some other error", "site-1", _FakeResponse(500), result)
        assert result["error"] == "Upgrade initiation failed for site-1: 500"
        assert "some other error" in capsys.readouterr().out


class TestHandleSSRUpgradeErrorResponse:
    """Wraps extract + classify."""

    def test_delegates_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_extract_ssr_error_text", lambda _r: "text")

        def stub_classify(text: str, site: str, response: Any, result: dict[str, Any]) -> None:
            result["skip_reason"] = "already_at_version"

        monkeypatch.setattr(mgr, "_classify_ssr_error_text", stub_classify)
        site_result: dict[str, Any] = {}
        result = mgr._handle_ssr_upgrade_error_response("site-1", _FakeResponse(400), site_result)
        assert result["skip_reason"] == "already_at_version"

    def test_extract_exception_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()

        def boom(_r: Any) -> str:
            raise RuntimeError("decode-fail")

        monkeypatch.setattr(mgr, "_extract_ssr_error_text", boom)
        site_result: dict[str, Any] = {}
        result = mgr._handle_ssr_upgrade_error_response("site-1", _FakeResponse(500), site_result)
        assert "Upgrade initiation failed for site-1: 500" in result["error"]


# ==============================================================================
# CALL API + BUILD BODY
# ==============================================================================


class TestBuildSSRUpgradeBody:
    """Body includes reboot_at=-1 only when not auto_reboot."""

    def test_auto_reboot_omits_reboot_at(self) -> None:
        body = _make_manager()._build_ssr_upgrade_body(
            ["d1", "d2"],
            "6.3.5",
            {"channel": "stable", "strategy": "serial", "auto_reboot": True},
        )
        assert body == {
            "device_ids": ["d1", "d2"],
            "channel": "stable",
            "version": "6.3.5",
            "strategy": "serial",
        }

    def test_manual_reboot_adds_sentinel(self) -> None:
        body = _make_manager()._build_ssr_upgrade_body(
            ["d1"],
            "6.3.5",
            {"channel": "stable", "strategy": "serial", "auto_reboot": False},
        )
        assert body["reboot_at"] == -1


class TestLogSSRUpgradeRequest:
    """Log + operator visible print of body summary."""

    def test_prints_summary(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._log_ssr_upgrade_request(
            {"device_ids": ["d1"], "channel": "stable", "version": "v", "strategy": "serial"},
            ["d1"],
            "v",
            {"channel": "stable", "strategy": "serial"},
        )
        out = capsys.readouterr().out
        assert "channel='stable'" in out
        assert "version='v'" in out
        assert "strategy='serial'" in out
        assert "['d1']" in out


class TestInterpretSSRUpgradeResponse:
    """Success codes vs delegated error."""

    @pytest.mark.parametrize("code", [200, 202])
    def test_success_codes(self, code: int) -> None:
        mgr = _make_manager()
        result = mgr._interpret_ssr_upgrade_response(
            _FakeResponse(code), "site-1", ["d1"], {"upgrade_initiated": False}
        )
        assert result["upgrade_initiated"] is True

    def test_failure_delegates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        handler = MagicMock(return_value={"error": "e"})
        monkeypatch.setattr(mgr, "_handle_ssr_upgrade_error_response", handler)
        r = _FakeResponse(500)
        site_result: dict[str, Any] = {"upgrade_initiated": False}
        result = mgr._interpret_ssr_upgrade_response(r, "site-1", ["d1"], site_result)
        handler.assert_called_once_with("site-1", r, site_result)
        assert result == {"error": "e"}


class TestCallSSRUpgradeAPI:
    """Full upgrade API call: builds body, logs, interprets."""

    def test_success_flow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.orgs.ssr as real_ssr

        monkeypatch.setattr(real_ssr, "upgradeOrgSsrs", lambda _s, _o, body=None: _FakeResponse(200))
        mgr = _make_manager()
        result = mgr._call_ssr_upgrade_api(
            "site-1",
            ["d1"],
            "6.3.5",
            {"channel": "stable", "strategy": "serial", "auto_reboot": True},
        )
        assert result["upgrade_initiated"] is True


# ==============================================================================
# SITE PROCESSING ORCHESTRATION
# ==============================================================================


class TestInitSSRSiteResult:
    """Zeroed per-site result shape."""

    def test_shape(self) -> None:
        result = _make_manager()._init_ssr_site_result({"id": "s1", "name": "S1"})
        assert result == {
            "site_id": "s1",
            "site_name": "S1",
            "ssrs_found": 0,
            "upgrade_initiated": False,
            "error": None,
        }

    def test_defaults_name_to_unknown(self) -> None:
        result = _make_manager()._init_ssr_site_result({})
        assert result["site_name"] == "Unknown"


class TestTallySSRSiteUpgradeResult:
    """Fold per-site outcome into global counters."""

    def test_upgrade_initiated_bumps_count(self) -> None:
        results = {"ssrs_upgraded": 0, "errors": []}
        _make_manager()._tally_ssr_site_upgrade_result({"upgrade_initiated": True}, ["d1", "d2"], results)
        assert results["ssrs_upgraded"] == 2
        assert results["errors"] == []

    def test_error_appended(self) -> None:
        results: dict[str, Any] = {"ssrs_upgraded": 0, "errors": []}
        _make_manager()._tally_ssr_site_upgrade_result({"upgrade_initiated": False, "error": "boom"}, [], results)
        assert results["errors"] == ["boom"]


class TestRunSSRSiteUpgradeFlow:
    """Discover + validate + call API + tally."""

    def test_no_ssrs_returns_early(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_discover_site_ssr_devices", lambda *_a: [])
        site_result: dict[str, Any] = {"upgrade_initiated": False}
        results: dict[str, Any] = {"errors": [], "ssrs_upgraded": 0}
        mgr._run_ssr_site_upgrade_flow(
            {"id": "s1", "name": "S1"},
            site_result,
            {"inventory": {}, "version": "v"},
            results,
        )
        assert site_result["ssrs_found"] == 0

    def test_no_validated_returns_early(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(
            mgr,
            "_discover_site_ssr_devices",
            lambda *_a: [{"id": "d1"}],
        )
        monkeypatch.setattr(
            mgr,
            "_validate_ssr_devices_for_version",
            lambda *_a: ([], ["d1"]),
        )
        api_mock = MagicMock()
        monkeypatch.setattr(mgr, "_call_ssr_upgrade_api", api_mock)
        site_result: dict[str, Any] = {"upgrade_initiated": False, "site_name": "S1"}
        mgr._run_ssr_site_upgrade_flow(
            {"id": "s1", "name": "S1"},
            site_result,
            {"inventory": {}, "version": "v"},
            {"errors": [], "ssrs_upgraded": 0},
        )
        api_mock.assert_not_called()

    def test_happy_path_calls_api_and_tallies(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_discover_site_ssr_devices", lambda *_a: [{"id": "d1"}])
        monkeypatch.setattr(mgr, "_validate_ssr_devices_for_version", lambda *_a: (["d1"], []))
        monkeypatch.setattr(
            mgr,
            "_call_ssr_upgrade_api",
            lambda *_a: {"upgrade_initiated": True},
        )
        site_result: dict[str, Any] = {"upgrade_initiated": False, "site_name": "S1"}
        results: dict[str, Any] = {"errors": [], "ssrs_upgraded": 0}
        mgr._run_ssr_site_upgrade_flow(
            {"id": "s1", "name": "S1"},
            site_result,
            {"inventory": {}, "version": "v"},
            results,
        )
        assert results["ssrs_upgraded"] == 1
        assert site_result["upgrade_initiated"] is True


class TestRecordSSRSiteError:
    """Uniform error recording."""

    def test_records_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        site_result: dict[str, Any] = {}
        results: dict[str, Any] = {"errors": []}
        _make_manager()._record_ssr_site_error("S1", RuntimeError("boom"), site_result, results)
        assert "Error processing site S1" in site_result["error"]
        assert len(results["errors"]) == 1
        assert "boom" in capsys.readouterr().out


class TestProcessSSRSiteUpgrade:
    """Full per-site orchestrator: init, run, tally, record."""

    def test_happy_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()

        def fake_run(_site: Any, site_result: dict[str, Any], *_a: Any) -> None:
            site_result["upgrade_initiated"] = True

        monkeypatch.setattr(mgr, "_run_ssr_site_upgrade_flow", fake_run)
        results: dict[str, Any] = {"sites_processed": 0, "site_results": [], "errors": []}
        mgr._process_ssr_site_upgrade({"id": "s1", "name": "S1"}, 1, 3, {}, results)
        assert results["sites_processed"] == 1
        assert len(results["site_results"]) == 1

    def test_exception_recorded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()

        def blow(*_a: Any) -> None:
            raise RuntimeError("boom")

        monkeypatch.setattr(mgr, "_run_ssr_site_upgrade_flow", blow)
        results: dict[str, Any] = {"sites_processed": 0, "site_results": [], "errors": []}
        mgr._process_ssr_site_upgrade({"id": "s1", "name": "S1"}, 1, 3, {}, results)
        assert results["sites_processed"] == 1
        assert "Error processing site S1" in results["errors"][0]


class TestPrintSSRUpgradeCompletion:
    """Completion banner + error list."""

    def test_no_errors(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_ssr_upgrade_completion(
            {
                "operation_id": "op-1",
                "sites_processed": 3,
                "ssrs_upgraded": 5,
                "errors": [],
            }
        )
        out = capsys.readouterr().out
        assert "OPERATION COMPLETED" in out
        assert "op-1" in out
        assert "Sites processed: 3" in out
        assert "SSRs upgraded: 5" in out

    def test_with_errors(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_ssr_upgrade_completion(
            {
                "operation_id": "op-1",
                "sites_processed": 3,
                "ssrs_upgraded": 5,
                "errors": ["err1", "err2"],
            }
        )
        out = capsys.readouterr().out
        assert "Errors encountered: 2" in out
        assert "err1" in out and "err2" in out


class TestIterateSSRSiteUpgrades:
    """Iterate selected sites for per-site processing."""

    def test_calls_process_for_each(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        calls: list[tuple[Any, int, int]] = []

        def fake_process(site: Any, idx: int, total: int, _cfg: Any, _res: Any) -> None:
            calls.append((site["id"], idx, total))

        monkeypatch.setattr(mgr, "_process_ssr_site_upgrade", fake_process)
        mgr._iterate_ssr_site_upgrades([{"id": "s1"}, {"id": "s2"}, {"id": "s3"}], {}, {})
        assert calls == [("s1", 1, 3), ("s2", 2, 3), ("s3", 3, 3)]


class TestRunSSRSiteUpgrades:
    """End-to-end upgrade runner."""

    def test_happy_path_populates_end_time(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_load_org_ssr_inventory", lambda: {})
        monkeypatch.setattr(mgr, "_iterate_ssr_site_upgrades", lambda *_a: None)
        monkeypatch.setattr(mgr, "_print_ssr_upgrade_completion", lambda _r: None)
        result = mgr._run_ssr_site_upgrades(
            [{"id": "s1"}],
            "6.3.5",
            {"strategy": "serial", "channel": "stable", "auto_reboot": True},
        )
        assert "end_time" in result
        assert result["target_version"] == "6.3.5"

    def test_exception_recorded(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_load_org_ssr_inventory", lambda: {})

        def blow(*_a: Any) -> None:
            raise RuntimeError("critical")

        monkeypatch.setattr(mgr, "_iterate_ssr_site_upgrades", blow)
        result = mgr._run_ssr_site_upgrades(
            [{"id": "s1"}],
            "6.3.5",
            {"strategy": "serial", "channel": "stable", "auto_reboot": True},
        )
        assert result["error"] == "critical"
        assert "Critical error in SSR firmware upgrade" in capsys.readouterr().out


# ==============================================================================
# BULK ENTRYPOINT + PREPARATION HELPERS
# ==============================================================================


class TestResolveSSRSitesOrError:
    """Wrap select_ssr_sites into standardised error/empty guard."""

    def test_error_propagates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_select_ssr_sites_for_upgrade", lambda _o: ([], {"error": "boom"}))
        sites, err = mgr._resolve_ssr_sites_or_error(None)
        assert sites is None
        assert err == {"error": "boom"}

    def test_empty_selection_becomes_error(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_select_ssr_sites_for_upgrade", lambda _o: ([], None))
        sites, err = mgr._resolve_ssr_sites_or_error(None)
        assert sites is None
        assert err == {"error": "No sites selected"}
        assert "No sites selected" in capsys.readouterr().out

    def test_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        picked = [{"id": "s1"}]
        monkeypatch.setattr(mgr, "_select_ssr_sites_for_upgrade", lambda _o: (picked, None))
        sites, err = mgr._resolve_ssr_sites_or_error(None)
        assert sites == picked
        assert err is None


class TestResolveSSROrgAndSites:
    """Chain org validate + site select."""

    def test_org_error_propagates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_validate_org_for_ssr_upgrade", lambda: ("", {"error": "org"}))
        result, err = mgr._resolve_ssr_org_and_sites(None)
        assert result is None and err == {"error": "org"}

    def test_sites_error_propagates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_validate_org_for_ssr_upgrade", lambda: ("Org", None))
        monkeypatch.setattr(mgr, "_resolve_ssr_sites_or_error", lambda _o: (None, {"error": "sites"}))
        result, err = mgr._resolve_ssr_org_and_sites(None)
        assert result is None and err == {"error": "sites"}

    def test_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_validate_org_for_ssr_upgrade", lambda: ("Org", None))
        monkeypatch.setattr(mgr, "_resolve_ssr_sites_or_error", lambda _o: ([{"id": "s1"}], None))
        result, err = mgr._resolve_ssr_org_and_sites(None)
        assert result == ("Org", [{"id": "s1"}])
        assert err is None


class TestResolveSSRConfigAndVersion:
    """Chain param setup + version selection."""

    def test_setup_cancel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_setup_ssr_upgrade_params", lambda: None)
        result, err = mgr._resolve_ssr_config_and_version()
        assert result is None
        assert err == {"cancelled": True}

    def test_version_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(
            mgr,
            "_setup_ssr_upgrade_params",
            lambda: {"channel": "stable", "strategy": "serial", "auto_reboot": True},
        )
        monkeypatch.setattr(mgr, "_fetch_and_select_ssr_version", lambda _c: ("", {"error": "vfail"}))
        result, err = mgr._resolve_ssr_config_and_version()
        assert result is None and err == {"error": "vfail"}

    def test_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        cfg = {"channel": "stable", "strategy": "serial", "auto_reboot": True}
        monkeypatch.setattr(mgr, "_setup_ssr_upgrade_params", lambda: cfg)
        monkeypatch.setattr(mgr, "_fetch_and_select_ssr_version", lambda _c: ("6.3.5", None))
        result, err = mgr._resolve_ssr_config_and_version()
        assert result == (cfg, "6.3.5")
        assert err is None


class TestPrepareSSRBulkUpgrade:
    """Bulk prep: org error / cfg error / success."""

    def test_org_error_propagates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_resolve_ssr_org_and_sites", lambda _o: (None, {"error": "e"}))
        result, err = mgr._prepare_ssr_bulk_upgrade(None)
        assert result is None and err == {"error": "e"}

    def test_config_error_propagates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_resolve_ssr_org_and_sites", lambda _o: (("Org", [{"id": "s1"}]), None))
        monkeypatch.setattr(mgr, "_resolve_ssr_config_and_version", lambda: (None, {"cancelled": True}))
        result, err = mgr._prepare_ssr_bulk_upgrade(None)
        assert result is None and err == {"cancelled": True}

    def test_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        cfg = {"channel": "stable", "strategy": "serial", "auto_reboot": True}
        monkeypatch.setattr(mgr, "_resolve_ssr_org_and_sites", lambda _o: (("Org", [{"id": "s1"}]), None))
        monkeypatch.setattr(mgr, "_resolve_ssr_config_and_version", lambda: ((cfg, "6.3.5"), None))
        result, err = mgr._prepare_ssr_bulk_upgrade(None)
        assert result == ("Org", [{"id": "s1"}], cfg, "6.3.5")
        assert err is None


class TestBulkUpgradeSSRFirmwareBySite:
    """SSR bulk entrypoint: prep error / confirm decline / happy path."""

    def test_prep_error_returns_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_prepare_ssr_bulk_upgrade", lambda _o: (None, {"error": "e"}))
        assert mgr._bulk_upgrade_ssr_firmware_by_site() == {"error": "e"}

    def test_confirm_decline_returns_cancel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        cfg = {"channel": "stable", "strategy": "serial", "auto_reboot": True}
        monkeypatch.setattr(
            mgr,
            "_prepare_ssr_bulk_upgrade",
            lambda _o: (("Org", [{"id": "s1"}], cfg, "6.3.5"), None),
        )
        monkeypatch.setattr(mgr, "_confirm_ssr_upgrade", lambda *_a: False)
        assert mgr._bulk_upgrade_ssr_firmware_by_site() == {"cancelled": True}

    def test_happy_path_runs_upgrades(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        cfg = {"channel": "stable", "strategy": "serial", "auto_reboot": True}
        monkeypatch.setattr(
            mgr,
            "_prepare_ssr_bulk_upgrade",
            lambda _o: (("Org", [{"id": "s1"}], cfg, "6.3.5"), None),
        )
        monkeypatch.setattr(mgr, "_confirm_ssr_upgrade", lambda *_a: True)
        monkeypatch.setattr(mgr, "_run_ssr_site_upgrades", lambda *_a: {"ssrs_upgraded": 2})
        assert mgr._bulk_upgrade_ssr_firmware_by_site() == {"ssrs_upgraded": 2}


# ==============================================================================
# SSR TEMPLATE FLOW
# ==============================================================================


class TestPrintSSRTemplateBanner:
    """Template banner content."""

    def test_prints_banner(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_ssr_template_banner()
        out = capsys.readouterr().out
        assert "Advanced SSR Firmware Upgrade by Gateway Template" in out


class TestExecuteTemplateBasedSSRUpgrade:
    """Template-driven SSR upgrade delegates to site bulk."""

    def test_delegates(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_bulk_upgrade_ssr_firmware_by_site", lambda sites: {"handled": len(sites)})
        result = mgr._execute_template_based_ssr_upgrade([{"id": "s1"}, {"id": "s2"}], "TMPL")
        assert result == {"handled": 2}
        out = capsys.readouterr().out
        assert "template: TMPL" in out
        assert "Target sites: 2" in out


class TestUpgradeSSRFirmwareByGatewayTemplate:
    """SSR template flow orchestrator."""

    def test_prep_none_returns_early(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_print_ssr_template_banner", lambda: None)
        monkeypatch.setattr(mgr, "_prepare_template_upgrade", lambda _k: None)
        exec_mock = MagicMock()
        monkeypatch.setattr(mgr, "_execute_template_based_ssr_upgrade", exec_mock)
        assert mgr._upgrade_ssr_firmware_by_gateway_template() is None
        exec_mock.assert_not_called()

    def test_selection_none_returns_early(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_print_ssr_template_banner", lambda: None)
        monkeypatch.setattr(mgr, "_prepare_template_upgrade", lambda _k: ({}, {}))
        monkeypatch.setattr(mgr, "_select_template_and_sites", lambda *_a: None)
        exec_mock = MagicMock()
        monkeypatch.setattr(mgr, "_execute_template_based_ssr_upgrade", exec_mock)
        assert mgr._upgrade_ssr_firmware_by_gateway_template() is None
        exec_mock.assert_not_called()

    def test_happy_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_print_ssr_template_banner", lambda: None)
        monkeypatch.setattr(mgr, "_prepare_template_upgrade", lambda _k: ({"t": "1"}, {"1": [{"id": "s1"}]}))
        monkeypatch.setattr(mgr, "_select_template_and_sites", lambda *_a: ("TPL", [{"id": "s1"}]))
        exec_mock = MagicMock()
        monkeypatch.setattr(mgr, "_execute_template_based_ssr_upgrade", exec_mock)
        mgr._upgrade_ssr_firmware_by_gateway_template()
        exec_mock.assert_called_once_with([{"id": "s1"}], "TPL")


class TestPrepareTemplateUpgrade:
    """``_prepare_template_upgrade`` freshens CSV then loads the mapping.

    Why:
        The helper is the join between the CSV cache-refresh step and the
        template->sites mapping load. Both halves are audit-logged and
        the early return on an empty mapping is what stops the SSR
        (destructive!) flow when there are no assigned sites.
    """

    def test_returns_none_when_mapping_empty(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        mgr = _make_manager()
        fresh_calls: list[int] = []
        monkeypatch.setattr(mgr, "_ensure_template_csv_freshness", lambda: fresh_calls.append(1))
        # Empty mapping -> operator diagnostic + audit warning + None return.
        monkeypatch.setattr(mgr, "_load_template_sites_mapping", lambda: ({}, {}))
        caplog.set_level(logging.WARNING, logger="root")
        assert mgr._prepare_template_upgrade("SSR") is None
        assert fresh_calls == [1]
        out = capsys.readouterr().out
        assert "No Gateway Templates with assigned sites found." in out
        assert "Make sure sites are assigned to Gateway Templates" in out
        assert any("No Gateway Templates with site assignments found" in r.message for r in caplog.records)

    def test_returns_tuple_on_success(self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_ensure_template_csv_freshness", lambda: None)
        name_to_id = {"tpl-a": "id-a"}
        sites_mapping = {"id-a": [{"id": "site-1"}, {"id": "site-2"}]}
        monkeypatch.setattr(mgr, "_load_template_sites_mapping", lambda: (name_to_id, sites_mapping))
        caplog.set_level(logging.DEBUG, logger="root")
        result = mgr._prepare_template_upgrade("SSR")
        assert result == (name_to_id, sites_mapping)
        # Both audit lines fired: entry (info) + exit (debug).
        messages = [r.message for r in caplog.records]
        assert any("Preparing SSR template upgrade" in m for m in messages)
        assert any("Template mapping loaded" in m for m in messages)


class TestSelectTemplateAndSites:
    """``_select_template_and_sites`` picks a template and returns its sites.

    Why:
        The picker is the last human gate before a bulk SSR upgrade
        fires. Both the decline path (must return None cleanly) and the
        happy path (must forward the exact site list from the mapping)
        need to be pinned.
    """

    def test_returns_none_when_operator_declines(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_prompt_template_selection", lambda *_a: ("", None))
        assert mgr._select_template_and_sites({"t": "id-1"}, {"id-1": [{"id": "s"}]}) is None
        assert "No template selected. Exiting." in capsys.readouterr().out

    def test_returns_none_when_id_is_empty_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Guard both halves of the "declined" predicate: empty id string.
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_prompt_template_selection", lambda *_a: ("", "some-name"))
        assert mgr._select_template_and_sites({}, {}) is None

    def test_returns_name_and_sites_on_success(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_prompt_template_selection", lambda *_a: ("id-x", "TPL-X"))
        sites_mapping = {"id-x": [{"id": "s1"}, {"id": "s2"}]}
        result = mgr._select_template_and_sites({"TPL-X": "id-x"}, sites_mapping)
        assert result == ("TPL-X", [{"id": "s1"}, {"id": "s2"}])
        out = capsys.readouterr().out
        assert "Template 'TPL-X' includes 2 sites" in out

    def test_returns_empty_sites_when_id_not_in_mapping(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Defensive branch: picker returned an id that is somehow absent
        # from the mapping -> resolves to [] via dict.get default.
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_prompt_template_selection", lambda *_a: ("orphan-id", "orphan"))
        result = mgr._select_template_and_sites({"orphan": "orphan-id"}, {})
        assert result == ("orphan", [])
