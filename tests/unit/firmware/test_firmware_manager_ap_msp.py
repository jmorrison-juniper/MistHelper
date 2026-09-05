"""AP mode dispatch + MSP multi-org upgrade unit tests.

Why:
    The MSP orchestrator is the largest branchy surface in the module and
    the only place where module-global ``msp_privileges``/``apisession``/
    ``org_id`` get mutated mid-flow. If the MSP guard regresses, single-org
    upgrade menus can silently offer an inaccessible "MSP" option; if
    selection parsing regresses, an operator's ``1,3,5-7`` picker string
    can silently drop indices. Every helper on the MSP path therefore has
    to stay pinned with an executable spec.
"""

from __future__ import annotations

import logging
import types
from typing import Any
from unittest.mock import MagicMock

import pytest

import src.firmware.firmware_manager as fm_mod
from src.firmware.firmware_manager import FirmwareManager, FirmwareManagerConfig

# ---------------------------------------------------------------------------
# Shared factory + snapshot helpers
# ---------------------------------------------------------------------------


def _make_manager(**overrides: Any) -> FirmwareManager:
    """Build a ``FirmwareManager`` with a valid minimum config.

    Why:
        Every test needs a live manager; centralising the factory removes
        boilerplate and lets each test body focus on the branch it drives.

    Args:
        **overrides: Any config field to override on the underlying
            ``FirmwareManagerConfig``.

    Returns:
        A live ``FirmwareManager`` bound to the current module state.
    """
    defaults: dict[str, Any] = {"apisession": object(), "org_id": "org-test"}
    defaults.update(overrides)
    return FirmwareManager(FirmwareManagerConfig(**defaults))


def _snapshot_msp() -> list[Any]:
    """Snapshot module-global ``msp_privileges`` for later restore.

    Why:
        MSP helpers read the module global directly; tests must not leak
        state across test functions or ``_is_msp_mode_available`` etc. will
        misbehave for the next test.

    Returns:
        Deep-enough copy of the current ``msp_privileges`` list.
    """
    return list(fm_mod.msp_privileges)


def _restore_msp(snap: list[Any]) -> None:
    """Restore module-global ``msp_privileges`` from a prior snapshot.

    Args:
        snap: Value returned by :func:`_snapshot_msp`.
    """
    fm_mod.msp_privileges = snap


def _snapshot_session() -> tuple[Any, str]:
    """Snapshot module-global ``apisession`` and ``org_id`` together.

    Why:
        MSP execution mutates the module ``org_id`` mid-flow; forgetting
        to restore leaks between tests and breaks other suites that read
        it later.

    Returns:
        Tuple of (apisession, org_id).
    """
    return fm_mod.apisession, fm_mod.org_id


def _restore_session(snap: tuple[Any, str]) -> None:
    """Restore module-global session/org state from a prior snapshot.

    Args:
        snap: Value returned by :func:`_snapshot_session`.
    """
    fm_mod.apisession, fm_mod.org_id = snap


# ---------------------------------------------------------------------------
# AP mode dispatch
# ---------------------------------------------------------------------------


class TestIsMspModeAvailable:
    """``_is_msp_mode_available`` reads module-global cache.

    Why:
        The AP mode menu conditionally renders option 3 based on this
        flag; a false negative silently hides the MSP branch from
        operators with valid privileges.
    """

    def test_empty_msp_list_returns_false(self) -> None:
        mgr = _make_manager()  # WHY: construct first — init rebinds globals
        snap = _snapshot_msp()
        try:
            fm_mod.msp_privileges = []
            assert mgr._is_msp_mode_available() is False
        finally:
            _restore_msp(snap)

    def test_populated_list_returns_true(self) -> None:
        mgr = _make_manager()  # WHY: construct first — init rebinds globals
        snap = _snapshot_msp()
        try:
            fm_mod.msp_privileges = [{"msp_id": "m1", "msp_name": "One"}]
            assert mgr._is_msp_mode_available() is True
        finally:
            _restore_msp(snap)


class TestPrintApUpgradeBanner:
    """``_print_ap_upgrade_banner`` renders title + underline."""

    def test_prints_title_and_underline(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_ap_upgrade_banner()
        out = capsys.readouterr().out
        assert "Advanced AP Firmware Upgrade" in out
        assert "=" * 60 in out


class TestRenderApModeMenu:
    """``_render_ap_mode_menu`` returns choices tuple based on MSP flag."""

    def test_two_option_menu_no_msp(self, capsys: pytest.CaptureFixture[str]) -> None:
        choices, prompt = _make_manager()._render_ap_mode_menu(msp_mode_available=False)
        assert choices == ["1", "2"]
        assert "1-2" in prompt
        out = capsys.readouterr().out
        assert "By Site" in out
        assert "By Gateway Template" in out
        assert "MSP Multi-Org" not in out

    def test_three_option_menu_with_msp(self, capsys: pytest.CaptureFixture[str]) -> None:
        choices, prompt = _make_manager()._render_ap_mode_menu(msp_mode_available=True)
        assert choices == ["1", "2", "3"]
        assert "1-3" in prompt
        assert "MSP Multi-Org" in capsys.readouterr().out


class TestPromptApUpgradeMode:
    """``_prompt_ap_upgrade_mode`` retries invalid tokens; None on Ctrl-C."""

    def test_returns_valid_choice_first_try(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "2")
        assert mgr._prompt_ap_upgrade_mode("? ", ["1", "2"]) == "2"

    def test_retries_until_valid(self, capsys: pytest.CaptureFixture[str]) -> None:
        answers = iter(["9", "abc", "1"])

        def fake_input(*_a: Any, **_k: Any) -> str:
            return next(answers)

        mgr = _make_manager(safe_input_fn=fake_input)
        assert mgr._prompt_ap_upgrade_mode("? ", ["1", "2"]) == "1"
        out = capsys.readouterr().out
        assert out.count("Invalid selection") == 2

    def test_keyboard_interrupt_returns_none(self, capsys: pytest.CaptureFixture[str]) -> None:
        def raise_kbint(*_a: Any, **_k: Any) -> str:
            raise KeyboardInterrupt

        mgr = _make_manager(safe_input_fn=raise_kbint)
        assert mgr._prompt_ap_upgrade_mode("? ", ["1", "2"]) is None
        assert "cancelled by user" in capsys.readouterr().out


class TestDispatchApUpgradeMode:
    """``_dispatch_ap_upgrade_mode`` routes 1/2/3 to correct flows."""

    def test_mode_1_calls_bulk_upgrade(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        called = MagicMock()
        monkeypatch.setattr(mgr, "_bulk_upgrade_ap_firmware_by_site", called)
        assert mgr._dispatch_ap_upgrade_mode("1") is None
        called.assert_called_once_with()

    def test_mode_2_calls_template_flow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        called = MagicMock()
        monkeypatch.setattr(mgr, "_upgrade_ap_firmware_by_gateway_template", called)
        assert mgr._dispatch_ap_upgrade_mode("2") is None
        called.assert_called_once_with()

    def test_mode_3_calls_msp_orchestrator(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        expected = [{"org": "x"}]
        monkeypatch.setattr(mgr, "_execute_msp_multi_org_upgrade", lambda: expected)
        assert mgr._dispatch_ap_upgrade_mode("3") is expected


# ---------------------------------------------------------------------------
# Selection input parsing
# ---------------------------------------------------------------------------


class TestParseRangeBounds:
    """``_parse_range_bounds`` normalises range tokens to 0-based (start,end)."""

    def test_valid_ascending(self) -> None:
        assert _make_manager()._parse_range_bounds("1-5") == (0, 4)

    def test_valid_reversed(self) -> None:
        # Reversed bounds must swap to normalise order.
        assert _make_manager()._parse_range_bounds("5-1") == (0, 4)

    def test_whitespace_tolerated(self) -> None:
        assert _make_manager()._parse_range_bounds(" 2 - 4 ") == (1, 3)

    def test_too_many_parts_returns_none(self) -> None:
        assert _make_manager()._parse_range_bounds("1-2-3") is None

    def test_non_numeric_returns_none(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.WARNING, logger="root")
        assert _make_manager()._parse_range_bounds("a-b") is None
        assert any("Invalid range format" in r.message for r in caplog.records)


class TestAppendIndexIfValid:
    """``_append_index_if_valid`` bounds/dedupe gate."""

    def test_valid_index_appended(self) -> None:
        acc: list[int] = []
        _make_manager()._append_index_if_valid(3, 10, acc)
        assert acc == [3]

    def test_duplicate_not_appended(self) -> None:
        acc = [3]
        _make_manager()._append_index_if_valid(3, 10, acc)
        assert acc == [3]

    def test_negative_ignored_silently(self, capsys: pytest.CaptureFixture[str]) -> None:
        acc: list[int] = []
        _make_manager()._append_index_if_valid(-1, 10, acc)
        assert acc == []
        # Negative branch neither appends nor warns.
        assert capsys.readouterr().out == ""

    def test_overflow_prints_hint(self, capsys: pytest.CaptureFixture[str]) -> None:
        acc: list[int] = []
        _make_manager()._append_index_if_valid(11, 10, acc)
        assert acc == []
        assert "out of range" in capsys.readouterr().out


class TestParseRangeToken:
    """``_parse_range_token`` expands a range into indices."""

    def test_expands_inclusive_range(self) -> None:
        acc: list[int] = []
        _make_manager()._parse_range_token("2-4", 10, acc)
        assert acc == [1, 2, 3]

    def test_invalid_bounds_no_op(self) -> None:
        acc: list[int] = []
        _make_manager()._parse_range_token("x-y", 10, acc)
        assert acc == []


class TestParseSingleToken:
    """``_parse_single_token`` appends valid single index."""

    def test_valid_index(self) -> None:
        acc: list[int] = []
        _make_manager()._parse_single_token("3", 10, acc)
        assert acc == [2]

    def test_invalid_index_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.WARNING, logger="root")
        acc: list[int] = []
        _make_manager()._parse_single_token("abc", 10, acc)
        assert acc == []
        assert any("Invalid index" in r.message for r in caplog.records)


class TestParseSelectionInput:
    """Integration: ``_parse_selection_input`` handles combined tokens."""

    def test_single_index(self) -> None:
        assert _make_manager()._parse_selection_input("3", 10) == [2]

    def test_csv_indices(self) -> None:
        assert _make_manager()._parse_selection_input("1,3,5", 10) == [0, 2, 4]

    def test_dash_range(self) -> None:
        assert _make_manager()._parse_selection_input("2-4", 10) == [1, 2, 3]

    def test_through_range(self) -> None:
        assert _make_manager()._parse_selection_input("2 through 4", 10) == [1, 2, 3]

    def test_mixed_csv_and_range(self) -> None:
        assert _make_manager()._parse_selection_input("1,3-5,8", 10) == [0, 2, 3, 4, 7]

    def test_sorted_and_deduped(self) -> None:
        assert _make_manager()._parse_selection_input("5,1,3,1", 10) == [0, 2, 4]

    def test_out_of_range_dropped(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert _make_manager()._parse_selection_input("15", 10) == []
        assert "out of range" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# MSP selection prompt path
# ---------------------------------------------------------------------------


class TestAutoSelectSingleMsp:
    """``_auto_select_single_msp`` returns sole MSP and previews."""

    def test_returns_and_previews(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        snap = _snapshot_msp()
        try:
            fm_mod.msp_privileges = [{"msp_id": "m1", "msp_name": "Acme"}]
            result = mgr._auto_select_single_msp()
            assert result[0]["msp_id"] == "m1"
            assert "Single MSP available: Acme" in capsys.readouterr().out
        finally:
            _restore_msp(snap)


class TestDisplayMspsForSelection:
    """``_display_msps_for_selection`` renders numbered MSP list + help."""

    def test_lists_msps_and_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        snap = _snapshot_msp()
        try:
            fm_mod.msp_privileges = [
                {"msp_name": "One", "role": "admin"},
                {"msp_name": "Two", "role": "read"},
            ]
            mgr._display_msps_for_selection()
            out = capsys.readouterr().out
            assert "Available MSPs" in out
            assert "One (role: admin)" in out
            assert "Two (role: read)" in out
            assert "Selection options" in out
        finally:
            _restore_msp(snap)

    def test_missing_fields_use_defaults(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        snap = _snapshot_msp()
        try:
            fm_mod.msp_privileges = [{}]
            mgr._display_msps_for_selection()
            out = capsys.readouterr().out
            assert "Unknown (role: unknown)" in out
        finally:
            _restore_msp(snap)


class TestPromptMspSelectionInput:
    """``_prompt_msp_selection_input`` normalises operator tokens."""

    def test_returns_lowercased_stripped(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "  1,3  ")
        assert mgr._prompt_msp_selection_input() == "1,3"

    def test_q_returns_none(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "Q")
        assert mgr._prompt_msp_selection_input() is None

    def test_empty_returns_none(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "")
        assert mgr._prompt_msp_selection_input() is None

    def test_system_exit_returns_none(self) -> None:
        def raise_sysexit(*_a: Any, **_k: Any) -> str:
            raise SystemExit

        mgr = _make_manager(safe_input_fn=raise_sysexit)
        assert mgr._prompt_msp_selection_input() is None


class TestResolveMspSelection:
    """``_resolve_msp_selection`` maps tokens to MSP dicts."""

    def test_all_returns_full_list(self) -> None:
        mgr = _make_manager()
        snap = _snapshot_msp()
        try:
            fm_mod.msp_privileges = [{"msp_id": "a"}, {"msp_id": "b"}]
            result = mgr._resolve_msp_selection("all")
            assert result == [{"msp_id": "a"}, {"msp_id": "b"}]
        finally:
            _restore_msp(snap)

    def test_indices_return_picks(self) -> None:
        mgr = _make_manager()
        snap = _snapshot_msp()
        try:
            fm_mod.msp_privileges = [{"msp_id": "a"}, {"msp_id": "b"}, {"msp_id": "c"}]
            result = mgr._resolve_msp_selection("1,3")
            assert result == [{"msp_id": "a"}, {"msp_id": "c"}]
        finally:
            _restore_msp(snap)

    def test_invalid_returns_none(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        snap = _snapshot_msp()
        try:
            fm_mod.msp_privileges = [{"msp_id": "a"}]
            assert mgr._resolve_msp_selection("nope") is None
            assert "Invalid selection" in capsys.readouterr().out
        finally:
            _restore_msp(snap)


class TestSelectMspsForUpgrade:
    """``_select_msps_for_upgrade`` orchestrates the picker path."""

    def test_no_msps_returns_none(self) -> None:
        mgr = _make_manager()
        snap = _snapshot_msp()
        try:
            fm_mod.msp_privileges = []
            assert mgr._select_msps_for_upgrade() is None
        finally:
            _restore_msp(snap)

    def test_single_msp_auto_selected(self) -> None:
        mgr = _make_manager()
        snap = _snapshot_msp()
        try:
            fm_mod.msp_privileges = [{"msp_id": "one", "msp_name": "Only"}]
            result = mgr._select_msps_for_upgrade()
            assert result is not None
            assert result[0]["msp_id"] == "one"
        finally:
            _restore_msp(snap)

    def test_cancelled_prompt_returns_none(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "q")
        snap = _snapshot_msp()
        try:
            fm_mod.msp_privileges = [{"msp_id": "a"}, {"msp_id": "b"}]
            assert mgr._select_msps_for_upgrade() is None
        finally:
            _restore_msp(snap)

    def test_multi_select_returns_picks(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "2")
        snap = _snapshot_msp()
        try:
            fm_mod.msp_privileges = [{"msp_id": "a"}, {"msp_id": "b"}]
            result = mgr._select_msps_for_upgrade()
            assert result == [{"msp_id": "b"}]
        finally:
            _restore_msp(snap)


class TestSelectMspForUpgradeDeprecated:
    """Deprecated single-MSP shim ``_select_msp_for_upgrade``."""

    def test_returns_first_msp_dict_when_singleton(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_select_msps_for_upgrade", lambda: [{"msp_id": "only"}])
        assert mgr._select_msp_for_upgrade() == {"msp_id": "only"}

    def test_returns_none_when_multiple(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_select_msps_for_upgrade", lambda: [{"msp_id": "a"}, {"msp_id": "b"}])
        assert mgr._select_msp_for_upgrade() is None

    def test_returns_none_on_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_select_msps_for_upgrade", lambda: None)
        assert mgr._select_msp_for_upgrade() is None


# ---------------------------------------------------------------------------
# API response coercion + MSP org fetch
# ---------------------------------------------------------------------------


class TestExtractResponseList:
    """``_extract_response_list`` coerces API responses to list or None."""

    def test_none_response(self) -> None:
        assert _make_manager()._extract_response_list(None) is None

    def test_empty_data(self) -> None:
        resp = types.SimpleNamespace(data=[])
        assert _make_manager()._extract_response_list(resp) is None

    def test_missing_data_attr(self) -> None:
        assert _make_manager()._extract_response_list(object()) is None

    def test_list_data_passthrough(self) -> None:
        resp = types.SimpleNamespace(data=[{"a": 1}])
        assert _make_manager()._extract_response_list(resp) == [{"a": 1}]

    def test_single_dict_wrapped_in_list(self) -> None:
        resp = types.SimpleNamespace(data={"a": 1})
        assert _make_manager()._extract_response_list(resp) == [{"a": 1}]


class TestFetchMspOrgList:
    """``_fetch_msp_org_list`` sorts orgs case-insensitively; None on empty."""

    def test_returns_sorted_orgs(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.msps.orgs as real_api

        response = types.SimpleNamespace(data=[{"name": "Zeta"}, {"name": "alpha"}])
        monkeypatch.setattr(real_api, "listMspOrgs", lambda _s, _m: response)
        result = _make_manager()._fetch_msp_org_list("m1")
        assert result == [{"name": "alpha"}, {"name": "Zeta"}]

    def test_returns_none_when_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.msps.orgs as real_api

        response = types.SimpleNamespace(data=[])
        monkeypatch.setattr(real_api, "listMspOrgs", lambda _s, _m: response)
        assert _make_manager()._fetch_msp_org_list("m1") is None


class TestFetchOrgsForSelection:
    """``_fetch_orgs_for_selection`` wraps fetch with UX + error handling."""

    def test_no_session_returns_none(self) -> None:
        mgr = _make_manager()
        snap = _snapshot_session()
        try:
            fm_mod.apisession = None
            assert mgr._fetch_orgs_for_selection("m1", "MSP-One") is None
        finally:
            _restore_session(snap)

    def test_api_error_returns_none(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()

        def blow_up(_msp_id: str) -> list[dict[str, Any]] | None:
            raise RuntimeError("boom")

        monkeypatch.setattr(mgr, "_fetch_msp_org_list", blow_up)
        snap = _snapshot_session()
        try:
            fm_mod.apisession = object()
            assert mgr._fetch_orgs_for_selection("m1", "MSP-One") is None
            assert "Error fetching organizations" in capsys.readouterr().out
        finally:
            _restore_session(snap)

    def test_empty_returns_none(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_fetch_msp_org_list", lambda _m: None)
        snap = _snapshot_session()
        try:
            fm_mod.apisession = object()
            assert mgr._fetch_orgs_for_selection("m1", "MSP-One") is None
            assert "Failed to retrieve organizations" in capsys.readouterr().out
        finally:
            _restore_session(snap)

    def test_valid_returns_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        data = [{"id": "o1", "name": "Org1"}]
        monkeypatch.setattr(mgr, "_fetch_msp_org_list", lambda _m: data)
        snap = _snapshot_session()
        try:
            fm_mod.apisession = object()
            assert mgr._fetch_orgs_for_selection("m1", "MSP-One") == data
        finally:
            _restore_session(snap)


class TestDisplayOrgsForSelection:
    """``_display_orgs_for_selection`` renders numbered org table."""

    def test_renders_orgs_with_id_preview(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        mgr._display_orgs_for_selection([{"id": "abcdefgh1234", "name": "Org1"}])
        out = capsys.readouterr().out
        assert "Found 1 organization" in out
        assert "Org1 (abcdefgh...)" in out
        assert "Selection:" in out


class TestPromptOrgSelectionInput:
    """``_prompt_org_selection_input`` normalises input tokens."""

    def test_returns_normalized(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "  ALL  ")
        assert mgr._prompt_org_selection_input() == "all"

    def test_q_returns_none(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "q")
        assert mgr._prompt_org_selection_input() is None

    def test_empty_returns_none(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "")
        assert mgr._prompt_org_selection_input() is None

    def test_system_exit_returns_none(self) -> None:
        def raise_sysexit(*_a: Any, **_k: Any) -> str:
            raise SystemExit

        mgr = _make_manager(safe_input_fn=raise_sysexit)
        assert mgr._prompt_org_selection_input() is None


class TestResolveOrgSelection:
    """``_resolve_org_selection`` maps token to org list."""

    def test_all_returns_full(self) -> None:
        mgr = _make_manager()
        orgs = [{"id": "a"}, {"id": "b"}]
        assert mgr._resolve_org_selection("all", orgs) == orgs

    def test_indices(self) -> None:
        mgr = _make_manager()
        orgs = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        assert mgr._resolve_org_selection("1,3", orgs) == [{"id": "a"}, {"id": "c"}]

    def test_invalid_returns_none(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        assert mgr._resolve_org_selection("nope", [{"id": "a"}]) is None
        assert "Invalid selection" in capsys.readouterr().out


class TestSelectOrgsForUpgrade:
    """``_select_orgs_for_upgrade`` end-to-end MSP -> orgs picker."""

    def test_no_orgs_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_fetch_orgs_for_selection", lambda *_a, **_k: None)
        assert mgr._select_orgs_for_upgrade("m1", "MSP-One") is None

    def test_cancelled_prompt(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_fetch_orgs_for_selection", lambda *_a, **_k: [{"id": "a"}])
        monkeypatch.setattr(mgr, "_prompt_org_selection_input", lambda: None)
        assert mgr._select_orgs_for_upgrade("m1", "MSP-One") is None

    def test_valid_selection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        orgs = [{"id": "a"}, {"id": "b"}]
        monkeypatch.setattr(mgr, "_fetch_orgs_for_selection", lambda *_a, **_k: orgs)
        monkeypatch.setattr(mgr, "_prompt_org_selection_input", lambda: "all")
        assert mgr._select_orgs_for_upgrade("m1", "MSP-One") == orgs


# ---------------------------------------------------------------------------
# Site fetch + paginated site picker
# ---------------------------------------------------------------------------


class TestFetchAndValidateOrgSites:
    """``_fetch_and_validate_org_sites`` sorts sites and returns None on empty."""

    def test_returns_sorted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.orgs.sites as real_api

        response = types.SimpleNamespace(data=[{"name": "B"}, {"name": "a"}])
        monkeypatch.setattr(real_api, "listOrgSites", lambda _s, _o: response)
        assert _make_manager()._fetch_and_validate_org_sites("o1") == [{"name": "a"}, {"name": "B"}]

    def test_empty_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.orgs.sites as real_api

        response = types.SimpleNamespace(data=[])
        monkeypatch.setattr(real_api, "listOrgSites", lambda _s, _o: response)
        assert _make_manager()._fetch_and_validate_org_sites("o1") is None


class TestSafeFetchSitesForOrg:
    """``_safe_fetch_sites_for_org`` wraps fetch with error handling."""

    def test_exception_returns_none(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()

        def blow_up(_o: str) -> None:
            raise RuntimeError("net-fail")

        monkeypatch.setattr(mgr, "_fetch_and_validate_org_sites", blow_up)
        assert mgr._safe_fetch_sites_for_org("o1") is None
        assert "Error fetching sites" in capsys.readouterr().out

    def test_empty_returns_none(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_fetch_and_validate_org_sites", lambda _o: None)
        assert mgr._safe_fetch_sites_for_org("o1") is None
        assert "Failed to retrieve sites" in capsys.readouterr().out

    def test_valid_returns_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        data = [{"id": "s1"}]
        monkeypatch.setattr(mgr, "_fetch_and_validate_org_sites", lambda _o: data)
        assert mgr._safe_fetch_sites_for_org("o1") == data


class TestDisplaySitesPage:
    """``_display_sites_page`` prints one page and pagination footer."""

    def test_prints_indices(self, capsys: pytest.CaptureFixture[str]) -> None:
        sites = [{"name": f"s{i}"} for i in range(3)]
        _make_manager()._display_sites_page(sites, 0, 3, 0, 1)
        out = capsys.readouterr().out
        assert "s0" in out and "s1" in out and "s2" in out
        # Only one page -> no navigation footer.
        assert "Page 1/1" not in out

    def test_multi_page_prints_navigation(self, capsys: pytest.CaptureFixture[str]) -> None:
        sites = [{"name": f"s{i}"} for i in range(5)]
        _make_manager()._display_sites_page(sites, 0, 2, 0, 3)
        out = capsys.readouterr().out
        assert "Page 1/3" in out
        assert "[n]ext page" in out


class TestResolveSitePageNavigation:
    """``_resolve_site_page_navigation`` handles n/p only when in bounds."""

    def test_next_when_allowed(self) -> None:
        assert _make_manager()._resolve_site_page_navigation("n", 0, 2) == ("next", 1)

    def test_next_at_last_page_returns_none(self) -> None:
        assert _make_manager()._resolve_site_page_navigation("n", 1, 2) is None

    def test_prev_when_allowed(self) -> None:
        assert _make_manager()._resolve_site_page_navigation("p", 2, 3) == ("prev", 1)

    def test_prev_at_first_page_returns_none(self) -> None:
        assert _make_manager()._resolve_site_page_navigation("p", 0, 3) is None

    def test_non_nav_returns_none(self) -> None:
        assert _make_manager()._resolve_site_page_navigation("1,2", 0, 3) is None


class TestHandleSitePageInput:
    """``_handle_site_page_input`` classifies each token."""

    def test_q_is_quit(self) -> None:
        assert _make_manager()._handle_site_page_input("q", 0, 2) == ("quit", None)

    def test_empty_is_quit(self) -> None:
        assert _make_manager()._handle_site_page_input("", 0, 2) == ("quit", None)

    def test_all(self) -> None:
        assert _make_manager()._handle_site_page_input("all", 0, 2) == ("all", None)

    def test_next(self) -> None:
        assert _make_manager()._handle_site_page_input("n", 0, 2) == ("next", 1)

    def test_prev(self) -> None:
        assert _make_manager()._handle_site_page_input("p", 1, 2) == ("prev", 0)

    def test_select_default(self) -> None:
        assert _make_manager()._handle_site_page_input("1,3", 0, 2) == ("select", "1,3")


class TestHandleSimplePageAction:
    """``_handle_simple_page_action`` maps quit/all/nav to outcome tuple."""

    def test_quit(self) -> None:
        assert _make_manager()._handle_simple_page_action("quit", None, [{"id": "a"}]) == (
            "commit",
            None,
        )

    def test_all_returns_full(self) -> None:
        sites = [{"id": "a"}]
        assert _make_manager()._handle_simple_page_action("all", None, sites) == ("commit", sites)

    def test_next_navigate(self) -> None:
        assert _make_manager()._handle_simple_page_action("next", 2, [{"id": "a"}]) == ("navigate", 2)

    def test_select_returns_none(self) -> None:
        # 'select' actions aren't simple — should return None to signal fallback.
        assert _make_manager()._handle_simple_page_action("select", "1", [{"id": "a"}]) is None


class TestApplySiteSelectionAction:
    """``_apply_site_selection_action`` dispatches to commit or navigate."""

    def test_quit_commits_none(self) -> None:
        mgr = _make_manager()
        result = mgr._apply_site_selection_action("q", 0, 1, [{"id": "a"}])
        assert result == ("commit", None)

    def test_all_commits_full(self) -> None:
        mgr = _make_manager()
        sites = [{"id": "a"}]
        assert mgr._apply_site_selection_action("all", 0, 1, sites) == ("commit", sites)

    def test_valid_index_commits_pick(self) -> None:
        mgr = _make_manager()
        sites = [{"id": "a"}, {"id": "b"}]
        assert mgr._apply_site_selection_action("2", 0, 1, sites) == ("commit", [{"id": "b"}])

    def test_invalid_index_navigates_same_page(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        sites = [{"id": "a"}]
        assert mgr._apply_site_selection_action("99", 0, 1, sites) == ("navigate", 0)
        assert "Invalid selection" in capsys.readouterr().out


class TestPromptSitePageSelection:
    """``_prompt_site_page_selection`` renders + reads one token."""

    def test_returns_normalised_token(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "  ALL  ")
        sites = [{"name": f"s{i}"} for i in range(3)]
        assert mgr._prompt_site_page_selection(sites, 0, 25, 1) == "all"

    def test_system_exit_returns_none(self) -> None:
        def raise_sysexit(*_a: Any, **_k: Any) -> str:
            raise SystemExit

        mgr = _make_manager(safe_input_fn=raise_sysexit)
        assert mgr._prompt_site_page_selection([{"name": "s1"}], 0, 25, 1) is None


class TestRunSiteSelectionLoop:
    """``_run_site_selection_loop`` walks pagination and commits result."""

    def test_cancel_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_prompt_site_page_selection", lambda *_a, **_k: None)
        assert mgr._run_site_selection_loop([{"name": "s1"}]) is None

    def test_all_returns_full(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        sites = [{"name": "s1"}, {"name": "s2"}]
        monkeypatch.setattr(mgr, "_prompt_site_page_selection", lambda *_a, **_k: "all")
        assert mgr._run_site_selection_loop(sites) == sites

    def test_navigate_then_commit(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        sites = [{"name": f"s{i}"} for i in range(30)]  # WHY: two pages @ 25/page
        answers = iter(["n", "all"])
        monkeypatch.setattr(mgr, "_prompt_site_page_selection", lambda *_a, **_k: next(answers))
        assert mgr._run_site_selection_loop(sites) == sites


class TestSelectSitesForOrgUpgrade:
    """End-to-end ``_select_sites_for_org_upgrade``."""

    def test_no_session_returns_none(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        snap = _snapshot_session()
        try:
            fm_mod.apisession = None
            assert mgr._select_sites_for_org_upgrade("o1", "Org1") is None
            assert "API session not initialized" in capsys.readouterr().out
        finally:
            _restore_session(snap)

    def test_no_sites_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_safe_fetch_sites_for_org", lambda _o: None)
        snap = _snapshot_session()
        try:
            fm_mod.apisession = object()
            assert mgr._select_sites_for_org_upgrade("o1", "Org1") is None
        finally:
            _restore_session(snap)

    def test_sites_returned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        sites = [{"id": "s1", "name": "S1"}]
        monkeypatch.setattr(mgr, "_safe_fetch_sites_for_org", lambda _o: sites)
        monkeypatch.setattr(mgr, "_run_site_selection_loop", lambda _d: sites)
        snap = _snapshot_session()
        try:
            fm_mod.apisession = object()
            assert mgr._select_sites_for_org_upgrade("o1", "Org1") == sites
        finally:
            _restore_session(snap)


# ---------------------------------------------------------------------------
# Upgrade plan construction + display + confirmation
# ---------------------------------------------------------------------------


class TestAddOrgToUpgradePlan:
    """``_add_org_to_upgrade_plan`` appends non-empty selections."""

    def test_appends_when_sites_selected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_select_sites_for_org_upgrade", lambda *_a, **_k: [{"id": "s1"}])
        plan: list[dict[str, Any]] = []
        mgr._add_org_to_upgrade_plan(plan, "m1", "MSP1", {"id": "o1", "name": "Org1"})
        assert plan == [
            {"msp_id": "m1", "msp_name": "MSP1", "org_id": "o1", "org_name": "Org1", "sites": [{"id": "s1"}]}
        ]

    def test_skips_when_no_sites(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_select_sites_for_org_upgrade", lambda *_a, **_k: None)
        plan: list[dict[str, Any]] = []
        mgr._add_org_to_upgrade_plan(plan, "m1", "MSP1", {"id": "o1", "name": "Org1"})
        assert plan == []
        assert "no sites selected" in capsys.readouterr().out


class TestBuildMspUpgradePlan:
    """``_build_msp_upgrade_plan`` iterates MSPs and their orgs."""

    def test_skips_msp_with_no_orgs(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_select_orgs_for_upgrade", lambda *_a, **_k: None)
        result = mgr._build_msp_upgrade_plan([{"msp_id": "m1", "msp_name": "MSP1"}])
        assert result == []
        assert "no organizations selected" in capsys.readouterr().out

    def test_expands_orgs_into_plan_entries(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_select_orgs_for_upgrade", lambda *_a, **_k: [{"id": "o1", "name": "Org1"}])
        monkeypatch.setattr(mgr, "_select_sites_for_org_upgrade", lambda *_a, **_k: [{"id": "s1", "name": "S1"}])
        result = mgr._build_msp_upgrade_plan([{"msp_id": "m1", "msp_name": "MSP1"}])
        assert len(result) == 1
        assert result[0]["org_id"] == "o1"
        assert result[0]["sites"] == [{"id": "s1", "name": "S1"}]


class TestConfirmMspUpgrade:
    """``_confirm_msp_upgrade`` requires literal 'UPGRADE' token."""

    def _plan(self) -> list[dict[str, Any]]:
        return [{"org_id": "o1", "sites": [{"id": "s1"}, {"id": "s2"}]}]

    def test_confirms_on_exact_token(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "UPGRADE")
        assert mgr._confirm_msp_upgrade(self._plan()) is True

    def test_rejects_wrong_token(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "yes")
        assert mgr._confirm_msp_upgrade(self._plan()) is False
        assert "cancelled" in capsys.readouterr().out.lower()

    def test_lowercase_rejected(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "upgrade")
        assert mgr._confirm_msp_upgrade(self._plan()) is False

    def test_system_exit_returns_false(self) -> None:
        def raise_sysexit(*_a: Any, **_k: Any) -> str:
            raise SystemExit

        mgr = _make_manager(safe_input_fn=raise_sysexit)
        assert mgr._confirm_msp_upgrade(self._plan()) is False


class TestAwaitMspUpgradeConfirmation:
    """``_await_msp_upgrade_confirmation`` dry-run auto-confirms."""

    def test_dry_run_auto_confirms(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "no")
        assert mgr._await_msp_upgrade_confirmation([{"sites": []}], dry_run=True) is True
        assert "DRY-RUN" in capsys.readouterr().out

    def test_non_dry_delegates_to_confirm(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_confirm_msp_upgrade", lambda _p: True)
        assert mgr._await_msp_upgrade_confirmation([{"sites": []}], dry_run=False) is True


class TestPrintMspMultiOrgBanner:
    """``_print_msp_multi_org_banner`` prints banner + warning."""

    def test_no_dry_run(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_msp_multi_org_banner(dry_run=False)
        out = capsys.readouterr().out
        assert "MSP MULTI-ORGANIZATION FIRMWARE UPGRADE" in out
        assert "DRY-RUN" not in out
        assert "WARNING" in out

    def test_dry_run_banner(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_msp_multi_org_banner(dry_run=True)
        out = capsys.readouterr().out
        assert "DRY-RUN MODE ENABLED" in out


class TestDisplayUpgradePlanSummary:
    """``_display_upgrade_plan_summary`` renders plan + totals."""

    def test_renders_multiple_orgs(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        plan = [
            {
                "msp_id": "m1",
                "msp_name": "MSP1",
                "org_id": "o1",
                "org_name": "Org1",
                "sites": [{"name": f"s{i}"} for i in range(3)],
            },
            {
                "msp_id": "m1",
                "msp_name": "MSP1",
                "org_id": "o2",
                "org_name": "Org2",
                "sites": [{"name": f"t{i}"} for i in range(7)],  # WHY: >5 triggers elision
            },
        ]
        mgr._display_upgrade_plan_summary(plan, dry_run=False)
        out = capsys.readouterr().out
        assert "UPGRADE PLAN SUMMARY" in out
        assert "MSP1" in out
        assert "Org1" in out
        assert "and 2 more" in out
        assert "MSPs: 1" in out
        assert "Organizations: 2" in out
        assert "Sites: 10" in out

    def test_dry_run_title(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        mgr._display_upgrade_plan_summary(
            [{"msp_id": "m1", "msp_name": "M1", "org_id": "o1", "org_name": "Org", "sites": []}],
            dry_run=True,
        )
        assert "(DRY-RUN)" in capsys.readouterr().out


class TestPrintUpgradePlanEntry:
    """``_print_upgrade_plan_entry`` handles site elision correctly."""

    def test_small_list_no_elision(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        sites = [{"name": "s1"}, {"name": "s2"}]
        mgr._print_upgrade_plan_entry({"msp_name": "M", "org_name": "O"}, sites)
        out = capsys.readouterr().out
        assert "and" not in out or "more" not in out


class TestCollectMspUpgradePlan:
    """``_collect_msp_upgrade_plan`` drives MSP + org + site selection."""

    def test_no_msps_returns_none(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_select_msps_for_upgrade", lambda: None)
        assert mgr._collect_msp_upgrade_plan() is None
        assert "Cancelled" in capsys.readouterr().out

    def test_msps_expanded_to_plan(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_select_msps_for_upgrade", lambda: [{"msp_id": "m1"}])
        monkeypatch.setattr(
            mgr,
            "_build_msp_upgrade_plan",
            lambda _msps: [{"msp_id": "m1", "org_id": "o1", "sites": []}],
        )
        assert mgr._collect_msp_upgrade_plan() == [{"msp_id": "m1", "org_id": "o1", "sites": []}]


# ---------------------------------------------------------------------------
# Upgrade plan execution: loop + per-org + summary
# ---------------------------------------------------------------------------


class TestPresentMspPlanHeader:
    """``_present_msp_plan_header`` renders per-org banner."""

    def test_prints_org_and_msp_names(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._present_msp_plan_header(
            1, 3, {"org_name": "Org1", "msp_name": "MSP1", "org_id": "o1", "sites": [{"id": "s1"}]}
        )
        out = capsys.readouterr().out
        assert "[1/3]" in out
        assert "Org1" in out
        assert "MSP1" in out
        assert "Organization ID: o1" in out
        assert "Sites to upgrade: 1" in out


class TestMakeMspRecord:
    """``_make_msp_record`` builds status record dict."""

    def _plan(self) -> dict[str, Any]:
        return {"msp_name": "M1", "org_id": "o1", "org_name": "Org1", "sites": [{"id": "s1"}]}

    def test_completed_no_error(self) -> None:
        rec = _make_manager()._make_msp_record(self._plan(), "completed", dry_run=False)
        assert rec["status"] == "completed"
        assert rec["dry_run"] is False
        assert rec["sites_count"] == 1
        assert "error" not in rec

    def test_failed_with_error(self) -> None:
        rec = _make_manager()._make_msp_record(self._plan(), "failed", dry_run=True, error="boom")
        assert rec["error"] == "boom"
        assert rec["dry_run"] is True


class TestSplitResultsByStatus:
    """``_split_results_by_status`` fanout by status key."""

    def test_splits_all_three(self) -> None:
        results = [
            {"status": "completed", "org_name": "A"},
            {"status": "failed", "org_name": "B"},
            {"status": "interrupted", "org_name": "C"},
            {"status": "completed", "org_name": "D"},
        ]
        completed, failed, interrupted = _make_manager()._split_results_by_status(results)
        assert [c["org_name"] for c in completed] == ["A", "D"]
        assert [f["org_name"] for f in failed] == ["B"]
        assert [i["org_name"] for i in interrupted] == ["C"]

    def test_empty_returns_empty_buckets(self) -> None:
        completed, failed, interrupted = _make_manager()._split_results_by_status([])
        assert completed == [] and failed == [] and interrupted == []

    def test_unknown_status_bucket_created(self) -> None:
        # Unknown status buckets are created via setdefault but never
        # returned — verify unknown statuses don't crash the split.
        completed, failed, interrupted = _make_manager()._split_results_by_status([{"status": "weird"}])
        assert completed == [] and failed == [] and interrupted == []


class TestPrintOrgsDetail:
    """Print helpers for completed / failed / interrupted org details."""

    def test_completed_no_op_when_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_completed_orgs_detail([])
        assert capsys.readouterr().out == ""

    def test_completed_prefixes_dry_run(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_completed_orgs_detail([{"org_name": "A", "sites_count": 2, "dry_run": True}])
        out = capsys.readouterr().out
        assert "(DRY-RUN)" in out
        assert "A (2 sites)" in out

    def test_failed_prints_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_failed_orgs_detail([{"org_name": "X", "error": "bad"}])
        assert "X: bad" in capsys.readouterr().out

    def test_failed_default_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_failed_orgs_detail([{"org_name": "X"}])
        assert "Unknown error" in capsys.readouterr().out

    def test_interrupted(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_interrupted_orgs_detail([{"org_name": "Z"}])
        assert "Z" in capsys.readouterr().out


class TestPrintMspUpgradeSummary:
    """``_print_msp_upgrade_summary`` prints full summary block."""

    def test_summary_renders_totals_and_sections(self, capsys: pytest.CaptureFixture[str]) -> None:
        results = [
            {"status": "completed", "org_name": "A", "sites_count": 2, "dry_run": False},
            {"status": "failed", "org_name": "B", "sites_count": 1, "error": "boom"},
        ]
        _make_manager()._print_msp_upgrade_summary(results, dry_run=False)
        out = capsys.readouterr().out
        assert "MSP UPGRADE SUMMARY" in out
        assert "Completed: 1" in out
        assert "Failed: 1" in out
        assert "Interrupted: 0" in out

    def test_summary_dry_run_flag_appears(self, capsys: pytest.CaptureFixture[str]) -> None:
        _make_manager()._print_msp_upgrade_summary([], dry_run=True)
        assert "(DRY-RUN)" in capsys.readouterr().out

    def test_log_msp_summary_totals_emits_info(self, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.INFO, logger="root")
        _make_manager()._log_msp_summary_totals(
            dry_run=True, completed=[1], failed=[], interrupted=[]  # type: ignore[list-item]
        )
        assert any("DRY-RUN" in r.message for r in caplog.records)


class TestRunMspBulkUpgrader:
    """``_run_msp_bulk_upgrader`` normalises sites and dispatches."""

    def test_dispatches_normalised_sites(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        seen: dict[str, Any] = {}

        def fake_dispatch(oid: str, sites: list[dict[str, Any]], dry_run: bool) -> None:
            seen["oid"] = oid
            seen["sites"] = sites
            seen["dry_run"] = dry_run

        monkeypatch.setattr(mgr, "_dispatch_bulk_ap_upgrade", fake_dispatch)
        mgr._run_msp_bulk_upgrader("o1", [{"id": "s1", "name": "S1", "extra": "x"}], dry_run=True)
        assert seen["oid"] == "o1"
        assert seen["sites"] == [{"id": "s1", "name": "S1"}]  # extra field dropped
        assert seen["dry_run"] is True

    def test_missing_site_name_uses_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        seen: dict[str, list[dict[str, Any]]] = {}

        def fake_dispatch(_o: str, sites: list[dict[str, Any]], _d: bool) -> None:
            seen["sites"] = sites

        monkeypatch.setattr(mgr, "_dispatch_bulk_ap_upgrade", fake_dispatch)
        mgr._run_msp_bulk_upgrader("o1", [{"id": "s1"}], dry_run=False)
        assert seen["sites"] == [{"id": "s1", "name": "Unknown"}]


class TestHandleMspInterrupt:
    """``_handle_msp_interrupt`` handles Ctrl-C policy prompts."""

    def _plan(self) -> dict[str, Any]:
        return {"msp_name": "M", "org_id": "o1", "org_name": "Org1", "sites": [{"id": "s1"}]}

    def test_y_continues(self) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "y")
        out = mgr._handle_msp_interrupt(self._plan(), "Org1", dry_run=False)
        assert out["stop"] is False
        assert out["record"]["status"] == "interrupted"

    def test_n_stops(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager(safe_input_fn=lambda *_a, **_k: "n")
        out = mgr._handle_msp_interrupt(self._plan(), "Org1", dry_run=False)
        assert out["stop"] is True
        assert "Stopping" in capsys.readouterr().out

    def test_system_exit_stops(self) -> None:
        def raise_sysexit(*_a: Any, **_k: Any) -> str:
            raise SystemExit

        mgr = _make_manager(safe_input_fn=raise_sysexit)
        out = mgr._handle_msp_interrupt(self._plan(), "Org1", dry_run=False)
        assert out["stop"] is True


class TestHandleMspFailure:
    """``_handle_msp_failure`` converts exception to failure record."""

    def test_failure_record(self, capsys: pytest.CaptureFixture[str]) -> None:
        mgr = _make_manager()
        plan = {"msp_name": "M", "org_id": "o1", "org_name": "Org1", "sites": [{"id": "s1"}]}
        result = mgr._handle_msp_failure(plan, "Org1", RuntimeError("boom"), dry_run=False)
        assert result["stop"] is False
        assert result["record"]["status"] == "failed"
        assert result["record"]["error"] == "boom"
        assert "boom" in capsys.readouterr().out


class TestExecuteMspSingleOrg:
    """``_execute_msp_single_org`` classifies success/interrupt/failure."""

    def _plan(self) -> dict[str, Any]:
        return {"msp_name": "M", "org_id": "o1", "org_name": "Org1", "sites": [{"id": "s1"}]}

    def test_happy_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        snap = _snapshot_session()
        try:
            monkeypatch.setattr(mgr, "_run_msp_bulk_upgrader", lambda *_a, **_k: None)
            out = mgr._execute_msp_single_org(self._plan(), dry_run=False)
            assert out["stop"] is False
            assert out["record"]["status"] == "completed"
        finally:
            _restore_session(snap)

    def test_kbint_delegates_to_handler(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        snap = _snapshot_session()
        try:

            def raise_kbint(*_a: Any, **_k: Any) -> None:
                raise KeyboardInterrupt

            monkeypatch.setattr(mgr, "_run_msp_bulk_upgrader", raise_kbint)
            monkeypatch.setattr(mgr, "_handle_msp_interrupt", lambda *_a, **_k: {"record": {}, "stop": True})
            out = mgr._execute_msp_single_org(self._plan(), dry_run=False)
            assert out["stop"] is True
        finally:
            _restore_session(snap)

    def test_exception_delegates_to_handler(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        snap = _snapshot_session()
        try:

            def blow_up(*_a: Any, **_k: Any) -> None:
                raise RuntimeError("boom")

            monkeypatch.setattr(mgr, "_run_msp_bulk_upgrader", blow_up)
            monkeypatch.setattr(
                mgr,
                "_handle_msp_failure",
                lambda *_a, **_k: {"record": {"status": "failed"}, "stop": False},
            )
            out = mgr._execute_msp_single_org(self._plan(), dry_run=False)
            assert out["record"]["status"] == "failed"
        finally:
            _restore_session(snap)


class TestRunMspUpgradeLoop:
    """``_run_msp_upgrade_loop`` iterates plan and honours stop signal."""

    def test_normal_completion(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        outcomes = iter(
            [
                {"record": {"status": "completed"}, "stop": False},
                {"record": {"status": "completed"}, "stop": False},
            ]
        )
        monkeypatch.setattr(mgr, "_execute_msp_single_org", lambda *_a, **_k: next(outcomes))
        results: list[dict[str, Any]] = []
        stopped = mgr._run_msp_upgrade_loop(
            [
                {"msp_name": "M", "org_name": "A", "org_id": "o1", "sites": []},
                {"msp_name": "M", "org_name": "B", "org_id": "o2", "sites": []},
            ],
            False,
            results,
        )
        assert stopped is False
        assert len(results) == 2

    def test_stop_signal_short_circuits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(
            mgr,
            "_execute_msp_single_org",
            lambda *_a, **_k: {"record": {"status": "interrupted"}, "stop": True},
        )
        results: list[dict[str, Any]] = []
        stopped = mgr._run_msp_upgrade_loop(
            [
                {"msp_name": "M", "org_name": "A", "org_id": "o1", "sites": []},
                {"msp_name": "M", "org_name": "B", "org_id": "o2", "sites": []},
            ],
            False,
            results,
        )
        assert stopped is True
        assert len(results) == 1  # WHY: loop bailed after first entry


class TestExecuteMspUpgradePlan:
    """``_execute_msp_upgrade_plan`` restores org_id after loop."""

    def test_restores_org_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        snap = _snapshot_session()
        try:
            fm_mod.org_id = "before"
            monkeypatch.setattr(
                mgr,
                "_run_msp_upgrade_loop",
                lambda *_a, **_k: False,
            )
            result = mgr._execute_msp_upgrade_plan([], dry_run=False)
            assert fm_mod.org_id == "before"
            assert result == []
        finally:
            _restore_session(snap)


class TestFinalizeMspUpgrade:
    """``_finalize_msp_upgrade`` runs preview + confirm + execute + summary."""

    def test_confirmation_declined_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_display_upgrade_plan_summary", lambda *_a, **_k: None)
        monkeypatch.setattr(mgr, "_await_msp_upgrade_confirmation", lambda *_a, **_k: False)
        assert mgr._finalize_msp_upgrade([{"sites": []}], dry_run=False) is None

    def test_happy_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_display_upgrade_plan_summary", lambda *_a, **_k: None)
        monkeypatch.setattr(mgr, "_await_msp_upgrade_confirmation", lambda *_a, **_k: True)
        monkeypatch.setattr(
            mgr,
            "_execute_msp_upgrade_plan",
            lambda *_a, **_k: [{"status": "completed"}],
        )
        printed: dict[str, Any] = {}
        monkeypatch.setattr(
            mgr,
            "_print_msp_upgrade_summary",
            lambda results, dry_run: printed.setdefault("r", results),
        )
        out = mgr._finalize_msp_upgrade([{"sites": []}], dry_run=False)
        assert out == [{"status": "completed"}]
        assert printed["r"] == [{"status": "completed"}]


class TestExecuteMspMultiOrgUpgrade:
    """Top-level ``_execute_msp_multi_org_upgrade`` orchestration."""

    def test_cancel_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_collect_msp_upgrade_plan", lambda: None)
        assert mgr._execute_msp_multi_org_upgrade() is None

    def test_empty_plan_prints_and_returns_none(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_collect_msp_upgrade_plan", lambda: [])
        assert mgr._execute_msp_multi_org_upgrade() is None
        assert "No upgrade targets" in capsys.readouterr().out

    def test_happy_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        monkeypatch.setattr(mgr, "_collect_msp_upgrade_plan", lambda: [{"org_id": "o1"}])
        monkeypatch.setattr(mgr, "_finalize_msp_upgrade", lambda plan, dry_run: [{"status": "ok"}])
        assert mgr._execute_msp_multi_org_upgrade() == [{"status": "ok"}]

    def test_honours_dry_run_from_globals(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mgr = _make_manager()
        # Install a fake args namespace with dry_run=True in the module globals.
        fake_args = types.SimpleNamespace(dry_run=True)
        monkeypatch.setitem(fm_mod.__dict__, "args", fake_args)
        seen: dict[str, bool] = {}

        def fake_finalize(_plan: list[Any], dry_run: bool) -> list[dict[str, Any]] | None:
            seen["dry_run"] = dry_run
            return []

        monkeypatch.setattr(mgr, "_collect_msp_upgrade_plan", lambda: [{"org_id": "o1"}])
        monkeypatch.setattr(mgr, "_finalize_msp_upgrade", fake_finalize)
        mgr._execute_msp_multi_org_upgrade()
        assert seen["dry_run"] is True
