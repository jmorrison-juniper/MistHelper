"""Template-based AP upgrade + AP mode-selection unit tests.

Why:
    The template flow reads two CSVs and joins them; a silent malformed
    row or missing DI hook must not crash the whole menu. AP mode
    selection is the operator's single gateway into every AP-upgrade
    branch (site / template / MSP), so its routing table has to be
    pinned against silent regressions.
"""

from __future__ import annotations

import csv
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

import src.firmware.firmware_manager as fm_mod
from src.firmware.firmware_manager import FirmwareManager, FirmwareManagerConfig


def _make_manager(**overrides: Any) -> FirmwareManager:
    """Build a ``FirmwareManager`` with a valid minimum config.

    Why:
        Every template/mode-selection test needs a live manager. Keeping
        construction in one helper lets each test focus on the branch it
        exercises rather than restating the required identity fields.

    Args:
        **overrides: Any config field to override.

    Returns:
        A live ``FirmwareManager`` ready to exercise helpers.
    """
    defaults: dict[str, Any] = {"apisession": object(), "org_id": "org-tpl"}
    defaults.update(overrides)
    return FirmwareManager(FirmwareManagerConfig(**defaults))


def _write_templates_csv(path: str, rows: list[dict[str, str]]) -> None:
    """Write an OrgGatewayTemplates.csv fixture.

    Why:
        Template-mapping tests need a real CSV file on disk because the
        loader opens the file directly rather than accepting a stream.

    Args:
        path: Absolute path to write the CSV to.
        rows: Row dicts with ``id`` and ``name`` columns.
    """
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_sites_csv(path: str, rows: list[dict[str, str]]) -> None:
    """Write a SiteList.csv fixture.

    Why:
        The template-to-site join reads the SiteList CSV from disk to
        associate ``gatewaytemplate_id`` back into template groupings.

    Args:
        path: Absolute path to write the CSV to.
        rows: Row dicts with ``id``, ``name``, ``gatewaytemplate_id``.
    """
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "gatewaytemplate_id"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


class TestPrepareTemplateCache:
    """``_prepare_template_cache`` warms both CSVs when a cache fn is wired."""

    def test_no_cache_fn_is_noop(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager(check_cache_fn=None)
        mgr._prepare_template_cache()
        assert "Preparing template and site data" in capsys.readouterr().out

    def test_invokes_cache_fn_for_both_csvs(self) -> None:
        calls: list[tuple[str, Any]] = []

        def cache(name: str, fn: Any) -> None:
            calls.append((name, fn))

        gw_fn = lambda *_a, **_k: None  # noqa: E731
        sites_fn = lambda *_a, **_k: None  # noqa: E731
        mgr = _make_manager(check_cache_fn=cache, gateway_templates_fn=gw_fn, sites_fn=sites_fn)
        mgr._prepare_template_cache()
        assert ("OrgGatewayTemplates.csv", gw_fn) in calls
        assert ("SiteList.csv", sites_fn) in calls


class TestEnsureTemplateCsvFreshness:
    """``_ensure_template_csv_freshness`` duplicate wrapper of prepare_cache."""

    def test_no_cache_fn_is_noop(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager(check_cache_fn=None)._ensure_template_csv_freshness()
        assert "Preparing template and site data" in capsys.readouterr().out

    def test_invokes_cache_fn_when_set(self) -> None:
        calls: list[str] = []
        mgr = _make_manager(check_cache_fn=lambda name, _fn: calls.append(name))
        mgr._ensure_template_csv_freshness()
        assert "OrgGatewayTemplates.csv" in calls
        assert "SiteList.csv" in calls


class TestReadGatewayTemplatesCsv:
    """CSV parsing for OrgGatewayTemplates.csv."""

    def test_no_path_fn_returns_empty(self, caplog: pytest.LogCaptureFixture) -> None:
        mgr = _make_manager(get_csv_path_fn=None)
        caplog.set_level(logging.WARNING, logger="root")
        name_to_id, sites_map = mgr._read_gateway_templates_csv()
        assert name_to_id == {}
        assert sites_map == {}
        assert any("get_csv_path_fn not configured" in r.message for r in caplog.records)

    def test_reads_populated_csv(self, tmp_path: Any) -> None:
        csv_path = tmp_path / "OrgGatewayTemplates.csv"
        _write_templates_csv(
            str(csv_path),
            [{"id": "t1", "name": "Alpha"}, {"id": "t2", "name": "Beta"}],
        )
        mgr = _make_manager(get_csv_path_fn=lambda _n: str(csv_path))
        name_to_id, sites_map = mgr._read_gateway_templates_csv()
        assert name_to_id == {"Alpha": "t1", "Beta": "t2"}
        assert sites_map == {"t1": [], "t2": []}

    def test_skips_rows_missing_name_or_id(self, tmp_path: Any) -> None:
        csv_path = tmp_path / "OrgGatewayTemplates.csv"
        _write_templates_csv(
            str(csv_path),
            [
                {"id": "", "name": "NoID"},
                {"id": "t1", "name": ""},
                {"id": "t2", "name": "Good"},
            ],
        )
        mgr = _make_manager(get_csv_path_fn=lambda _n: str(csv_path))
        name_to_id, sites_map = mgr._read_gateway_templates_csv()
        assert name_to_id == {"Good": "t2"}
        assert sites_map == {"t2": []}


class TestMapSitesToTemplate:
    """``_map_sites_to_template`` joins sites into the template mapping."""

    def test_joins_matching_sites(self, tmp_path: Any) -> None:
        site_path = tmp_path / "SiteList.csv"
        _write_sites_csv(
            str(site_path),
            [
                {"id": "s1", "name": "S1", "gatewaytemplate_id": "t1"},
                {"id": "s2", "name": "S2", "gatewaytemplate_id": "t2"},
                {"id": "s3", "name": "S3", "gatewaytemplate_id": "t1"},
            ],
        )
        mapping: dict[str, list[dict[str, Any]]] = {"t1": [], "t2": []}
        _make_manager()._map_sites_to_template(mapping, str(site_path))
        assert len(mapping["t1"]) == 2
        assert len(mapping["t2"]) == 1

    def test_skips_missing_fields(self, tmp_path: Any) -> None:
        site_path = tmp_path / "SiteList.csv"
        _write_sites_csv(
            str(site_path),
            [
                {"id": "", "name": "S1", "gatewaytemplate_id": "t1"},
                {"id": "s2", "name": "", "gatewaytemplate_id": "t1"},
                {"id": "s3", "name": "S3", "gatewaytemplate_id": "unknown"},
            ],
        )
        mapping: dict[str, list[dict[str, Any]]] = {"t1": []}
        _make_manager()._map_sites_to_template(mapping, str(site_path))
        assert mapping["t1"] == []


class TestLoadTemplateSitesMapping:
    """``_load_template_sites_mapping`` composes read + join + stats."""

    def test_no_path_fn_returns_empty_pair(self) -> None:
        assert _make_manager(get_csv_path_fn=None)._load_template_sites_mapping() == ({}, {})

    def test_happy_path_loads_both(self, tmp_path: Any) -> None:
        tpl_path = tmp_path / "OrgGatewayTemplates.csv"
        site_path = tmp_path / "SiteList.csv"
        _write_templates_csv(str(tpl_path), [{"id": "t1", "name": "Alpha"}])
        _write_sites_csv(str(site_path), [{"id": "s1", "name": "S1", "gatewaytemplate_id": "t1"}])

        def path_fn(name: str) -> str:
            return str(tpl_path if "Gateway" in name else site_path)

        mgr = _make_manager(get_csv_path_fn=path_fn)
        name_to_id, sites_map = mgr._load_template_sites_mapping()
        assert name_to_id == {"Alpha": "t1"}
        assert sites_map["t1"][0]["id"] == "s1"

    def test_exception_returns_empty(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mgr = _make_manager(get_csv_path_fn=lambda _n: "/does/not/exist.csv")
        caplog.set_level(logging.ERROR, logger="root")
        # _read_gateway_templates_csv will raise FileNotFoundError.
        assert mgr._load_template_sites_mapping() == ({}, {})
        out = capsys.readouterr().out
        assert "Failed to load template and site data" in out
        assert any("Failed to load template-sites mapping" in r.message for r in caplog.records)


class TestRenderTemplateSelectionMenu:
    """``_render_template_selection_menu`` prints table + returns index map."""

    def test_returns_index_map(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        idx_map = mgr._render_template_selection_menu(
            [("Alpha", "t1"), ("Beta", "t2")], {"t1": [{"id": "s1", "name": "S1"}], "t2": []}
        )
        assert idx_map == {"1": ("t1", "Alpha"), "2": ("t2", "Beta")}
        out = capsys.readouterr().out
        assert "Available Gateway Templates" in out
        assert "Alpha" in out
        assert "Beta" in out


class TestResolveTemplateSelection:
    """Index-then-name resolution."""

    def test_by_index(self) -> None:
        mgr = _make_manager()
        result = mgr._resolve_template_selection("1", {"1": ("t1", "Alpha")}, {"Alpha": "t1"})
        assert result == ("t1", "Alpha")

    def test_by_exact_name(self) -> None:
        mgr = _make_manager()
        result = mgr._resolve_template_selection("Alpha", {"1": ("t1", "Alpha")}, {"Alpha": "t1"})
        assert result == ("t1", "Alpha")

    def test_no_match(self) -> None:
        assert _make_manager()._resolve_template_selection("zzz", {"1": ("t1", "A")}, {"A": "t1"}) is None


class TestLoopTemplateSelectionInput:
    """Loop reads until index/name match or cancel."""

    def test_keyboard_interrupt_cancels(self, capsys: pytest.CaptureFixture[str]) -> None:
        def raise_kb(*_a: Any, **_k: Any) -> str:
            raise KeyboardInterrupt

        mgr = _make_manager(safe_input_fn=raise_kb)
        result = mgr._loop_template_selection_input({"1": ("t1", "A")}, {"A": "t1"}, 1)
        assert result == (None, None)
        assert "cancelled" in capsys.readouterr().out.lower()

    def test_blank_cancels(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "")
        assert mgr._loop_template_selection_input({"1": ("t1", "A")}, {"A": "t1"}, 1) == (None, None)

    def test_invalid_then_valid(self, capsys: pytest.CaptureFixture[str]) -> None:
        answers = iter(["zzz", "1"])
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: next(answers))
        assert mgr._loop_template_selection_input({"1": ("t1", "A")}, {"A": "t1"}, 1) == ("t1", "A")
        assert "Invalid selection" in capsys.readouterr().out


class TestPromptTemplateSelection:
    """End-to-end prompt: menu render + input loop."""

    def test_returns_selection(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "1")
        result = mgr._prompt_template_selection({"Alpha": "t1"}, {"t1": []})
        assert result == ("t1", "Alpha")


class TestSelectTemplateForUpgrade:
    """``_select_template_for_upgrade`` composes load + prompt."""

    def test_no_templates_returns_none_pair(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_load_template_sites_mapping", lambda: ({}, {}))
        assert mgr._select_template_for_upgrade() == (None, None)
        assert "No gateway templates found" in capsys.readouterr().out

    def test_cancel_returns_none_pair(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_load_template_sites_mapping", lambda: ({"A": "t1"}, {"t1": []}))
        monkeypatch.setattr(mgr, "_prompt_template_selection", lambda *_a, **_k: (None, None))
        assert mgr._select_template_for_upgrade() == (None, None)
        assert "No template selected" in capsys.readouterr().out

    def test_happy_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_load_template_sites_mapping", lambda: ({"A": "t1"}, {"t1": []}))
        monkeypatch.setattr(mgr, "_prompt_template_selection", lambda *_a, **_k: ("t1", "A"))
        assert mgr._select_template_for_upgrade() == ("t1", "A")


class TestResolveTemplateSites:
    """``_resolve_template_sites`` warns + returns [] when empty."""

    def test_empty_warns(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_load_template_sites_mapping", lambda: ({}, {"t1": []}))
        assert mgr._resolve_template_sites("t1", "TplA") == []
        assert "No sites found using template" in capsys.readouterr().out

    def test_returns_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        sites = [{"id": "s1", "name": "S1"}]
        monkeypatch.setattr(mgr, "_load_template_sites_mapping", lambda: ({}, {"t1": sites}))
        assert mgr._resolve_template_sites("t1", "TplA") == sites


class TestPresentTemplateSummary:
    """Summary printer + per-site debug log."""

    def test_prints_summary(self, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.DEBUG, logger="root")
        mgr = _make_manager()
        mgr._present_template_summary("t1", "Alpha", [{"id": "s1", "name": "S1"}])
        out = capsys.readouterr().out
        assert "Selected Template: Alpha" in out
        assert "Template ID: t1" in out
        assert "Sites in Template: 1" in out
        assert any("Site: S1" in r.message for r in caplog.records)


class TestPrintTemplateUpgradeBanner:
    """Banner + table for template-based upgrades."""

    def test_prints_all_rows(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        mgr._print_template_upgrade_banner("Alpha", [{"id": "s1", "name": "S1"}, {"id": "s2", "name": "S2"}])
        out = capsys.readouterr().out
        assert "Template-Based Upgrade Execution" in out
        assert "Template: Alpha" in out
        assert "Sites to process: 2" in out
        assert "S1" in out
        assert "S2" in out


class TestExecuteTemplateBasedUpgrade:
    """Delegates to ``_bulk_upgrade_ap_firmware_by_site`` with override list."""

    def test_delegates_with_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        called = MagicMock()
        monkeypatch.setattr(mgr, "_bulk_upgrade_ap_firmware_by_site", called)
        sites = [{"id": "s1", "name": "S1"}]
        mgr._execute_template_based_upgrade(sites, "Alpha")
        called.assert_called_once_with(sites_to_upgrade_override=sites)


class TestUpgradeApFirmwareByGatewayTemplate:
    """End-to-end orchestrator: cancel + empty-site + happy paths."""

    def test_cancelled_at_template_selection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_prepare_template_cache", lambda: None)
        monkeypatch.setattr(mgr, "_select_template_for_upgrade", lambda: (None, None))
        exec_hook = MagicMock()
        monkeypatch.setattr(mgr, "_execute_template_based_upgrade", exec_hook)
        assert mgr._upgrade_ap_firmware_by_gateway_template() is None
        exec_hook.assert_not_called()

    def test_empty_sites_returns_early(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_prepare_template_cache", lambda: None)
        monkeypatch.setattr(mgr, "_select_template_for_upgrade", lambda: ("t1", "A"))
        monkeypatch.setattr(mgr, "_resolve_template_sites", lambda _tid, _tn: [])
        exec_hook = MagicMock()
        monkeypatch.setattr(mgr, "_execute_template_based_upgrade", exec_hook)
        assert mgr._upgrade_ap_firmware_by_gateway_template() is None
        exec_hook.assert_not_called()

    def test_happy_path_dispatches(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_prepare_template_cache", lambda: None)
        monkeypatch.setattr(mgr, "_select_template_for_upgrade", lambda: ("t1", "Alpha"))
        sites = [{"id": "s1", "name": "S1"}]
        monkeypatch.setattr(mgr, "_resolve_template_sites", lambda _tid, _tn: sites)
        monkeypatch.setattr(mgr, "_present_template_summary", lambda *_a, **_k: None)
        exec_hook = MagicMock()
        monkeypatch.setattr(mgr, "_execute_template_based_upgrade", exec_hook)
        mgr._upgrade_ap_firmware_by_gateway_template()
        exec_hook.assert_called_once_with(sites, "Alpha")


class TestEmitApUpgradeProgressStart:
    """Progress-emitter fires only when the module-global is set."""

    def test_no_emitter_is_noop(self) -> None:
        mgr = _make_manager()  # WHY: construct first — init rebinds globals
        original = fm_mod.PROGRESS_EMITTER
        try:
            fm_mod.PROGRESS_EMITTER = None
            mgr._emit_ap_upgrade_progress_start()  # should not raise
        finally:
            fm_mod.PROGRESS_EMITTER = original

    def test_emitter_fires_progress_start(self) -> None:
        mgr = _make_manager()  # WHY: construct first — init rebinds globals
        original = fm_mod.PROGRESS_EMITTER
        try:
            emitter = MagicMock()
            fm_mod.PROGRESS_EMITTER = emitter
            mgr._emit_ap_upgrade_progress_start()
            emitter.emit_progress_start.assert_called_once_with("90", "firmware_upgrade", 1)
        finally:
            fm_mod.PROGRESS_EMITTER = original


class TestIsMspModeAvailable:
    """Module-global MSP privileges gate."""

    def test_empty_list_returns_false(self) -> None:
        mgr = _make_manager()  # WHY: construct first — init rebinds globals
        original = list(fm_mod.msp_privileges)
        try:
            fm_mod.msp_privileges = []
            assert mgr._is_msp_mode_available() is False
        finally:
            fm_mod.msp_privileges = original

    def test_populated_list_returns_true(self) -> None:
        mgr = _make_manager()  # WHY: construct first — init rebinds globals
        original = list(fm_mod.msp_privileges)
        try:
            fm_mod.msp_privileges = [{"msp_id": "m1", "msp_name": "MSP1"}]
            assert mgr._is_msp_mode_available() is True
        finally:
            fm_mod.msp_privileges = original


class TestRenderApModeMenu:
    """Menu prints + returns choice/prompt tuple."""

    def test_without_msp(self, capsys: pytest.CaptureFixture[str]) -> None:
        choices, prompt = _make_manager()._render_ap_mode_menu(False)
        assert choices == ["1", "2"]
        assert "1-2" in prompt
        out = capsys.readouterr().out
        assert "Select upgrade mode" in out
        assert "MSP Multi-Org" not in out

    def test_with_msp(self, capsys: pytest.CaptureFixture[str]) -> None:
        choices, prompt = _make_manager()._render_ap_mode_menu(True)
        assert choices == ["1", "2", "3"]
        assert "1-3" in prompt
        assert "MSP Multi-Org" in capsys.readouterr().out


class TestPromptApUpgradeMode:
    """Retries invalid input; KeyboardInterrupt cancels."""

    def test_valid_returns_choice(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "2")
        assert mgr._prompt_ap_upgrade_mode("> ", ["1", "2"]) == "2"

    def test_invalid_then_valid(self, capsys: pytest.CaptureFixture[str]) -> None:
        answers = iter(["9", "1"])
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: next(answers))
        assert mgr._prompt_ap_upgrade_mode("> ", ["1", "2"]) == "1"
        assert "Invalid selection" in capsys.readouterr().out

    def test_keyboard_interrupt_returns_none(self, capsys: pytest.CaptureFixture[str]) -> None:
        def raise_kb(*_a: Any, **_k: Any) -> str:
            raise KeyboardInterrupt

        mgr = _make_manager(safe_input_fn=raise_kb)
        assert mgr._prompt_ap_upgrade_mode("> ", ["1", "2"]) is None
        assert "cancelled" in capsys.readouterr().out.lower()


class TestDispatchApUpgradeMode:
    """Routing table: 1 -> site, 2 -> template, 3 -> MSP orchestrator."""

    def test_mode_1_calls_bulk(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        called = MagicMock()
        monkeypatch.setattr(mgr, "_bulk_upgrade_ap_firmware_by_site", called)
        assert mgr._dispatch_ap_upgrade_mode("1") is None
        called.assert_called_once_with()

    def test_mode_2_calls_template(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        called = MagicMock()
        monkeypatch.setattr(mgr, "_upgrade_ap_firmware_by_gateway_template", called)
        assert mgr._dispatch_ap_upgrade_mode("2") is None
        called.assert_called_once_with()

    def test_mode_3_calls_msp(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        msp_result = [{"org_id": "o1", "status": "completed"}]
        monkeypatch.setattr(mgr, "_execute_msp_multi_org_upgrade", lambda: msp_result)
        assert mgr._dispatch_ap_upgrade_mode("3") == msp_result


class TestExecuteFirmwareUpgradeWithModeSelection:
    """End-to-end AP-upgrade entry point."""

    def test_cancelled_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_emit_ap_upgrade_progress_start", lambda: None)
        monkeypatch.setattr(mgr, "_is_msp_mode_available", lambda: False)
        monkeypatch.setattr(mgr, "_print_ap_upgrade_banner", lambda: None)
        monkeypatch.setattr(mgr, "_render_ap_mode_menu", lambda _msp: (["1", "2"], "> "))
        monkeypatch.setattr(mgr, "_prompt_ap_upgrade_mode", lambda _p, _c: None)
        dispatch = MagicMock()
        monkeypatch.setattr(mgr, "_dispatch_ap_upgrade_mode", dispatch)
        assert mgr.execute_firmware_upgrade_with_mode_selection() is None
        dispatch.assert_not_called()

    def test_happy_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_emit_ap_upgrade_progress_start", lambda: None)
        monkeypatch.setattr(mgr, "_is_msp_mode_available", lambda: True)
        monkeypatch.setattr(mgr, "_print_ap_upgrade_banner", lambda: None)
        monkeypatch.setattr(mgr, "_render_ap_mode_menu", lambda _msp: (["1", "2", "3"], "> "))
        monkeypatch.setattr(mgr, "_prompt_ap_upgrade_mode", lambda _p, _c: "1")
        dispatch = MagicMock(return_value=None)
        monkeypatch.setattr(mgr, "_dispatch_ap_upgrade_mode", dispatch)
        assert mgr.execute_firmware_upgrade_with_mode_selection() is None
        dispatch.assert_called_once_with("1")


class TestBulkUpgradeApFirmwareBySite:
    """``_bulk_upgrade_ap_firmware_by_site`` save/restore of module apisession.

    Why:
        Legacy helpers read the bare ``apisession`` module global.
        Missing the save/restore step would silently leak the previous
        caller's session into the next flow.
    """

    def test_wraps_execute_and_restores_module_apisession(self, monkeypatch: pytest.MonkeyPatch) -> None:
        instance_session = object()
        mgr = _make_manager(apisession=instance_session)
        # Set the sentinel AFTER __init__ rebinds the module global; the
        # save/restore under test only holds if we trap the *current* value
        # of ``fm_mod.apisession`` at call time.
        sentinel_prev = object()
        monkeypatch.setattr(fm_mod, "apisession", sentinel_prev)
        seen: dict[str, Any] = {}

        def fake_execute(override: Any) -> None:
            seen["override"] = override
            seen["during"] = fm_mod.apisession

        monkeypatch.setattr(mgr, "_execute_bulk_upgrade", fake_execute)
        mgr._bulk_upgrade_ap_firmware_by_site([{"id": "s"}])
        # apisession swapped in during the call, restored after.
        assert seen["during"] is instance_session
        assert seen["override"] == [{"id": "s"}]
        assert fm_mod.apisession is sentinel_prev

    def test_restores_apisession_even_on_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager(apisession=object())
        # Set sentinel after __init__ rebound the module global.
        sentinel_prev = object()
        monkeypatch.setattr(fm_mod, "apisession", sentinel_prev)

        def boom(_o: Any) -> None:
            raise RuntimeError("boom")

        monkeypatch.setattr(mgr, "_execute_bulk_upgrade", boom)
        with pytest.raises(RuntimeError):
            mgr._bulk_upgrade_ap_firmware_by_site(None)
        assert fm_mod.apisession is sentinel_prev


class TestExecuteBulkUpgrade:
    """``_execute_bulk_upgrade`` reads dry_run and delegates."""

    def test_dispatches_with_dry_run_from_mh_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import types

        mgr = _make_manager()
        # _MH is a proxy; give it an args namespace with dry_run flipped on.
        fake_mh = types.SimpleNamespace(args=types.SimpleNamespace(dry_run=True))
        monkeypatch.setattr(fm_mod, "_MH", fake_mh)
        seen: dict[str, Any] = {}

        def fake_dispatch(oid: str, override: Any, dry_run: bool) -> None:
            seen["oid"] = oid
            seen["override"] = override
            seen["dry_run"] = dry_run

        monkeypatch.setattr(mgr, "_dispatch_bulk_ap_upgrade", fake_dispatch)
        mgr._execute_bulk_upgrade([{"id": "s"}])
        assert seen["oid"] == "org-tpl"
        assert seen["override"] == [{"id": "s"}]
        assert seen["dry_run"] is True

    def test_defaults_dry_run_false_when_args_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import types

        mgr = _make_manager()
        # _MH proxy without args attribute -> getattr default None; getattr
        # dry_run default False.
        monkeypatch.setattr(fm_mod, "_MH", types.SimpleNamespace())
        seen: dict[str, bool] = {}

        def fake_dispatch(_o: str, _s: Any, dry_run: bool) -> None:
            seen["dry_run"] = dry_run

        monkeypatch.setattr(mgr, "_dispatch_bulk_ap_upgrade", fake_dispatch)
        mgr._execute_bulk_upgrade(None)
        assert seen["dry_run"] is False


class TestBuildBulkAPConfig:
    """``_build_bulk_ap_config`` lazily builds an immutable upgrader config."""

    def test_returns_config_with_wired_fields(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import types

        # Stub the _MH proxy with the attributes the builder reads.
        fake_mh = types.SimpleNamespace(
            apisession="AMBIENT",
            InputUtils=types.SimpleNamespace(safe_input=lambda *_a, **_k: ""),
            ConfigUtils=types.SimpleNamespace(
                check_stop_signal=lambda *_a, **_k: False,
                get_cached_or_prompted_org_id=lambda: "org-tpl",
            ),
            APICoreFetchUtils=types.SimpleNamespace(all_sites_with_limit=lambda *_a, **_k: []),
            FilePathUtils=types.SimpleNamespace(get_csv_path=lambda _n: "/tmp/x.csv"),
            _build_firmware_manager=lambda _s, _o: types.SimpleNamespace(check_firmware_upgrade_status=lambda: None),
        )
        monkeypatch.setattr(fm_mod, "_MH", fake_mh)
        mgr = _make_manager()
        cfg = mgr._build_bulk_ap_config("org-tpl", [{"id": "s"}], dry_run=True)
        # Sanity: config is the frozen BulkAPUpgraderConfig with our fields.
        assert cfg.org_id == "org-tpl"
        assert cfg.apisession == "AMBIENT"
        assert cfg.sites_override == [{"id": "s"}]
        assert cfg.dry_run is True
        assert callable(cfg.safe_input_fn)
        # Lazy status factory returns a live-looking object with the method wired.
        assert cfg.check_firmware_status_fn() is None


class TestDispatchBulkAPUpgrade:
    """``_dispatch_bulk_ap_upgrade`` builds config + drives the upgrader."""

    def test_builds_config_and_calls_execute(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.firmware.bulk_ap_upgrader as bau

        mgr = _make_manager()
        built_cfg = object()
        monkeypatch.setattr(mgr, "_build_bulk_ap_config", lambda *_a, **_k: built_cfg)

        seen: dict[str, Any] = {}

        class _FakeUpgrader:
            def __init__(self, cfg: Any) -> None:
                seen["cfg"] = cfg

            def execute(self) -> None:
                seen["executed"] = True

        monkeypatch.setattr(bau, "BulkAPFirmwareUpgrader", _FakeUpgrader)
        mgr._dispatch_bulk_ap_upgrade("org-tpl", [{"id": "s"}], dry_run=False)
        assert seen["cfg"] is built_cfg
        assert seen["executed"] is True
