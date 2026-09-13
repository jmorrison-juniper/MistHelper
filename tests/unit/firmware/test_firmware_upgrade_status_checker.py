"""Unit tests for the co-located ``FirmwareUpgradeStatusChecker`` class.

Why:
    The status checker is a long procedural report generator that reads
    ``apisession`` at module scope and touches five separate mistapi
    endpoints. Each helper is small but the surface area is huge; without
    per-helper coverage a single silent regression (wrong status glyph,
    missing histogram bucket, swapped ``upgrade_id`` field) ships to
    operators unnoticed.
"""

from __future__ import annotations

import builtins
import json
import os
from typing import Any
from unittest.mock import MagicMock

import pytest

import src.firmware.firmware_manager as fm_mod
from src.firmware.firmware_manager import FirmwareUpgradeStatusChecker


class _FakeResponse:
    """Stand-in for a ``requests.Response`` used by mistapi helpers.

    Why:
        The status checker only inspects ``status_code`` and ``data`` on
        the responses it receives; the fake avoids constructing a real
        response object with headers, cookies, etc.
    """

    def __init__(self, status_code: int = 200, data: Any = None, has_data_attr: bool = True) -> None:
        """Store canned status + payload; drop ``data`` attribute if requested.

        Args:
            status_code: HTTP status code to expose.
            data: Payload to return via ``.data``.
            has_data_attr: If False, the ``data`` attribute is not set,
                simulating an API shape that lacks the field.
        """
        self.status_code = status_code
        if has_data_attr:
            self.data = data


def _install_mh_proxy(monkeypatch: pytest.MonkeyPatch, org_id: str = "org-test") -> MagicMock:
    """Replace ``fm_mod._MH`` with a MagicMock for the duration of the test.

    Why:
        The real ``_MH`` proxy forwards attribute lookups to the
        ``MistHelper`` module (which is a heavy import). Every checker
        helper touches it (``ConfigUtils``, ``DisplayUtils``, ``DataExporter``,
        ``APICoreFetchUtils``, ``PromptUtils``). A MagicMock with the org id
        wired in is enough to satisfy every call site.

    Args:
        monkeypatch: The active ``pytest.MonkeyPatch`` fixture.
        org_id: Org id to return from ``get_cached_or_prompted_org_id``.

    Returns:
        The MagicMock installed as ``fm_mod._MH`` (so tests can assert on it).
    """
    mh = MagicMock()
    mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = org_id
    mh.DisplayUtils.create_progress_bar.side_effect = lambda p, bar_length=20: f"[bar {p}]"
    monkeypatch.setattr(fm_mod, "_MH", mh)
    return mh


def _make_checker(
    monkeypatch: pytest.MonkeyPatch,
    scope_choice: str | None = None,
    site_filter: str | None = None,
    org_id: str = "org-test",
) -> FirmwareUpgradeStatusChecker:
    """Instantiate a checker with the _MH proxy stubbed.

    Args:
        monkeypatch: Test fixture used to install the mock proxy.
        scope_choice: Optional scope selector to forward.
        site_filter: Optional site id filter to forward.
        org_id: Org id the mocked ConfigUtils returns.

    Returns:
        Fresh ``FirmwareUpgradeStatusChecker`` ready for use.
    """
    _install_mh_proxy(monkeypatch, org_id=org_id)
    return FirmwareUpgradeStatusChecker(scope_choice=scope_choice, site_filter=site_filter)


class TestInit:
    """Init wiring + summary shape.

    Why:
        Every other helper reads ``self.summary`` and ``self.org_id``, so
        a regression in the constructor's default state cascades into all
        downstream displays.
    """

    def test_stores_scope_and_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch, scope_choice="2", site_filter="site-x")
        assert chk.scope_choice == "2"
        assert chk.site_filter == "site-x"
        assert chk.org_id == "org-test"

    def test_org_id_pulled_from_configutils(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mh = _install_mh_proxy(monkeypatch, org_id="ORG-42")
        chk = FirmwareUpgradeStatusChecker()
        assert chk.org_id == "ORG-42"
        mh.ConfigUtils.get_cached_or_prompted_org_id.assert_called_once()

    def test_summary_keys_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        expected_keys = {
            "total_devices",
            "devices_with_fwupdate",
            "upgrade_in_progress",
            "upgrade_failed",
            "upgrade_completed",
            "upgrade_unknown",
            "devices_by_status",
            "devices_by_version",
            "devices_by_model",
            "devices_by_type",
            "progress_total",
            "progress_count",
            "devices_upgrading",
        }
        assert expected_keys.issubset(chk.summary.keys())
        assert chk.summary["total_devices"] == 0
        assert chk.summary["devices_upgrading"] == []

    def test_empty_collections_initialized(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        assert chk.all_device_stats == []
        assert chk.upgrade_results == []
        assert chk.active_upgrades == []
        assert chk.site_lookup == {}


class TestResolveSiteFilter:
    """``_resolve_site_filter`` prompt/passthrough gate."""

    def test_scope_not_2_returns_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch, scope_choice="3")
        assert chk._resolve_site_filter() is True

    def test_scope_2_with_existing_filter_returns_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch, scope_choice="2", site_filter="pre-set")
        assert chk._resolve_site_filter() is True

    def test_scope_2_selects_via_promptutils(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mh = _install_mh_proxy(monkeypatch)
        mh.PromptUtils.select_site.return_value = "chosen-site"
        chk = FirmwareUpgradeStatusChecker(scope_choice="2")
        assert chk._resolve_site_filter() is True
        assert chk.site_filter == "chosen-site"

    def test_scope_2_no_selection_returns_false(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mh = _install_mh_proxy(monkeypatch)
        mh.PromptUtils.select_site.return_value = None
        chk = FirmwareUpgradeStatusChecker(scope_choice="2")
        assert chk._resolve_site_filter() is False
        assert "No site selected" in capsys.readouterr().out


class TestFetchDeviceStats:
    """``_fetch_device_stats`` dispatch + exception guard."""

    def test_delegates_to_site_when_filter_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch, scope_choice="2", site_filter="site-a")
        monkeypatch.setattr(chk, "_fetch_site_stats", lambda: True)
        monkeypatch.setattr(chk, "_fetch_org_stats", lambda: pytest.fail("wrong branch"))
        assert chk._fetch_device_stats() is True

    def test_delegates_to_org_when_no_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(chk, "_fetch_site_stats", lambda: pytest.fail("wrong branch"))
        monkeypatch.setattr(chk, "_fetch_org_stats", lambda: True)
        assert chk._fetch_device_stats() is True

    def test_exception_returns_false(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)

        def blow_up() -> bool:
            raise RuntimeError("api-down")

        monkeypatch.setattr(chk, "_fetch_org_stats", blow_up)
        assert chk._fetch_device_stats() is False
        assert "Failed to fetch device statistics" in capsys.readouterr().out


class TestFetchSiteAndOrgStats:
    """Site + org fetch helpers hit mistapi + accumulate results."""

    def _install_pagination(
        self,
        monkeypatch: pytest.MonkeyPatch,
        page1: list[dict[str, Any]],
        endpoint_path: tuple[str, ...],
    ) -> None:
        """Wire ``mistapi.get_all`` + a specific endpoint to canned data.

        Why:
            Patch through ``fm_mod.mistapi`` (the same module reference
            firmware_manager already resolved) so a sibling test that
            replaces ``sys.modules['mistapi']`` cannot desync our shim.
        """
        mistapi = fm_mod.mistapi

        monkeypatch.setattr(mistapi, "get_all", lambda response, mist_session: response.data)
        module = mistapi
        for part in endpoint_path[:-1]:
            module = getattr(module, part)
        monkeypatch.setattr(module, endpoint_path[-1], lambda *_a, **_k: _FakeResponse(200, page1))

    def test_site_stats_accumulates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch, site_filter="site-x")
        self._install_pagination(
            monkeypatch,
            [{"id": "d1"}, {"id": "d2"}],
            ("api", "v1", "sites", "stats", "listSiteDevicesStats"),
        )
        assert chk._fetch_site_stats() is True
        assert len(chk.all_device_stats) == 2

    def test_site_stats_empty_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch, site_filter="site-x")
        self._install_pagination(monkeypatch, [], ("api", "v1", "sites", "stats", "listSiteDevicesStats"))
        assert chk._fetch_site_stats() is False

    def test_org_stats_accumulates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        self._install_pagination(
            monkeypatch,
            [{"id": "d1"}],
            ("api", "v1", "orgs", "stats", "listOrgDevicesStats"),
        )
        assert chk._fetch_org_stats() is True
        assert chk.all_device_stats == [{"id": "d1"}]

    def test_org_stats_empty_returns_false(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        self._install_pagination(monkeypatch, [], ("api", "v1", "orgs", "stats", "listOrgDevicesStats"))
        assert chk._fetch_org_stats() is False
        assert "No device statistics found" in capsys.readouterr().out


class TestFetchSiteLookup:
    """``_fetch_site_lookup`` builds site_id -> site_name map, tolerates errors."""

    def test_populates_lookup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mh = _install_mh_proxy(monkeypatch)
        mh.APICoreFetchUtils.all_sites_with_limit.return_value = [
            {"id": "s1", "name": "Site 1"},
            {"id": "s2", "name": "Site 2"},
            {"id": None, "name": "Skip"},
        ]
        chk = FirmwareUpgradeStatusChecker()
        chk._fetch_site_lookup()
        assert chk.site_lookup == {"s1": "Site 1", "s2": "Site 2"}

    def test_exception_clears_lookup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mh = _install_mh_proxy(monkeypatch)
        mh.APICoreFetchUtils.all_sites_with_limit.side_effect = RuntimeError("boom")
        chk = FirmwareUpgradeStatusChecker()
        chk.site_lookup["stale"] = "must-clear"
        chk._fetch_site_lookup()
        assert chk.site_lookup == {}


class TestExtractDeviceInfo:
    """``_extract_device_info`` normalises the raw stats row."""

    def test_fields_pulled_and_defaulted(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        chk.site_lookup["s1"] = "Site 1"
        row = chk._extract_device_info(
            {
                "id": "d1",
                "name": "n1",
                "mac": "aabbcc",
                "model": "m1",
                "type": "ap",
                "version": "6.3.5",
                "site_id": "s1",
                "last_seen": 100,
            }
        )
        assert row["device_id"] == "d1"
        assert row["device_name"] == "n1"
        assert row["device_mac"] == "aabbcc"
        assert row["site_name"] == "Site 1"

    def test_unknown_site_yields_fallback_label(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        row = chk._extract_device_info({"site_id": "unknown-site"})
        assert row["site_name"] == "Unknown Site"
        assert row["device_id"] == "Unknown"


class TestProcessFwupdateAndSubHelpers:
    """``_process_fwupdate`` + ``_parse_fwupdate_data`` + ``_categorize_status``."""

    def _base_info(self, last_seen: int = 0) -> dict[str, Any]:
        return {
            "device_id": "d1",
            "device_name": "n1",
            "device_mac": "aabbcc",
            "device_model": "m1",
            "device_type": "ap",
            "device_version": "6.3.5",
            "site_id": "s1",
            "site_name": "Site 1",
            "last_seen": last_seen,
        }

    def test_empty_fwupdate_returns_no_upgrade_info(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        fw = chk._process_fwupdate({}, self._base_info())
        assert fw["fw_status"] == "no_upgrade_info"
        assert chk.summary["devices_with_fwupdate"] == 0

    def test_populated_fwupdate_increments_counter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        fw = chk._process_fwupdate(
            {"fwupdate": {"status": "upgraded", "progress": 100}},
            self._base_info(),
        )
        assert fw["fw_status"] == "upgraded"
        assert chk.summary["devices_with_fwupdate"] == 1

    @pytest.mark.parametrize(
        "status,progress,expected_key",
        [
            ("failed", 0, "upgrade_failed"),
            ("upgraded", 100, "upgrade_completed"),
            ("success", 100, "upgrade_completed"),
            ("mystery", 0, "upgrade_unknown"),
        ],
    )
    def test_categorize_terminal_states(
        self,
        monkeypatch: pytest.MonkeyPatch,
        status: str,
        progress: int,
        expected_key: str,
    ) -> None:
        chk = _make_checker(monkeypatch)
        chk._categorize_status(status, progress, 0, self._base_info())
        assert chk.summary[expected_key] == 1

    def test_categorize_active_upgrade_tracks(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        chk._categorize_status("inprogress", 50, 0, self._base_info())
        assert chk.summary["upgrade_in_progress"] == 1
        assert chk.summary["devices_upgrading"][0]["progress"] == 50

    def test_categorize_active_stale_marks_complete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(chk, "_is_stale_upgrade", lambda _p, _t: True)
        chk._categorize_status("upgrading", 100, 12345, self._base_info())
        assert chk.summary["upgrade_completed"] == 1


class TestStaleUpgrade:
    """``_is_stale_upgrade`` + ``_is_valid_upgrade_timestamp``."""

    def test_non_100_progress_not_stale(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        assert chk._is_stale_upgrade(50, 12345) is False

    def test_invalid_timestamp_not_stale(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        assert chk._is_stale_upgrade(100, 0) is False
        assert chk._is_stale_upgrade(100, "abc") is False

    def test_old_upgrade_is_stale(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        # 2 hours ago, threshold 1
        monkeypatch.setattr(fm_mod.time, "time", lambda: 3600 * 5)
        assert chk._is_stale_upgrade(100, 3600 * 2) is True

    def test_fresh_upgrade_not_stale(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        # 1 minute ago
        monkeypatch.setattr(fm_mod.time, "time", lambda: 3660)
        assert chk._is_stale_upgrade(100, 3600) is False

    def test_math_exception_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)

        def bad_time() -> float:
            raise ValueError("nope")

        monkeypatch.setattr(fm_mod.time, "time", bad_time)
        assert chk._is_stale_upgrade(100, 1) is False

    @pytest.mark.parametrize("value,expected", [(1, True), (1.5, True), (0, False), (-5, False), ("x", False)])
    def test_valid_timestamp(self, value: Any, expected: bool) -> None:
        assert FirmwareUpgradeStatusChecker._is_valid_upgrade_timestamp(value) is expected


class TestTrackActiveUpgrade:
    """``_track_active_upgrade`` progress accounting."""

    def test_numeric_progress_updates_average(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        info = {
            "device_name": "n1",
            "device_mac": "aabbcc",
            "device_type": "ap",
            "device_model": "m1",
            "site_name": "Site 1",
            "device_version": "6.3.5",
        }
        chk._track_active_upgrade(30, 1000, info)
        assert chk.summary["progress_total"] == 30
        assert chk.summary["progress_count"] == 1
        assert chk.summary["devices_upgrading"][0]["progress"] == 30

    def test_none_progress_records_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        info = {
            "device_name": "n1",
            "device_mac": "aabbcc",
            "device_type": "ap",
            "device_model": "m1",
            "site_name": "Site 1",
            "device_version": "6.3.5",
        }
        chk._track_active_upgrade(None, 1000, info)
        assert chk.summary["progress_count"] == 0
        assert chk.summary["devices_upgrading"][0]["progress"] == 0


class TestFormatTimestamp:
    """``_format_timestamp`` fallbacks + happy path."""

    def test_valid_timestamp(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        out = chk._format_timestamp(1700000000)
        assert len(out) == 19  # YYYY-MM-DD HH:MM:SS

    @pytest.mark.parametrize("bad", [0, -1, None, "abc"])
    def test_invalid_returns_unknown(self, monkeypatch: pytest.MonkeyPatch, bad: Any) -> None:
        chk = _make_checker(monkeypatch)
        assert chk._format_timestamp(bad) == "Unknown"

    def test_exception_returns_invalid_marker(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)

        class _Dt:
            @staticmethod
            def fromtimestamp(_ts: float) -> Any:
                raise ValueError("bad epoch")

        monkeypatch.setattr(fm_mod, "datetime", _Dt)
        assert chk._format_timestamp(123).startswith("Invalid:")


class TestUpdateSummaryCounters:
    """``_update_summary_counters`` histogram maintenance."""

    def test_all_three_histograms_increment(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        info = {"device_version": "6.3.5", "device_model": "AP41", "device_type": "ap"}
        chk._update_summary_counters(info, {})
        chk._update_summary_counters(info, {})
        assert chk.summary["devices_by_version"]["6.3.5"] == 2
        assert chk.summary["devices_by_model"]["AP41"] == 2
        assert chk.summary["devices_by_type"]["ap"] == 2
        assert chk.summary["total_devices"] == 2


class TestBuildUpgradeResultRow:
    """``_build_upgrade_result_row`` CSV row shape."""

    def test_all_columns_present(self) -> None:
        row = FirmwareUpgradeStatusChecker._build_upgrade_result_row(
            {
                "site_id": "s1",
                "site_name": "Site 1",
                "device_id": "d1",
                "device_name": "n1",
                "device_mac": "aabbcc",
                "device_model": "m1",
                "device_type": "ap",
                "device_version": "6.3.5",
            },
            {
                "last_seen_str": "2024-01-01 00:00:00",
                "fw_status": "upgraded",
                "fw_progress": 100,
                "fw_status_id": 5,
                "fw_will_retry": False,
                "fw_time_str": "2024-01-01 00:01:00",
            },
            "[bar 100]",
        )
        assert row["Site ID"] == "s1"
        assert row["FW Progress Display"] == "[bar 100]"
        assert "Timestamp" in row


class TestMaybeAddToResults:
    """``_maybe_add_to_results`` scope gate + row append."""

    def test_scope_3_active_appends(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch, scope_choice="3")
        chk._maybe_add_to_results(
            {
                "site_id": "s1",
                "site_name": "Site 1",
                "device_id": "d1",
                "device_name": "n1",
                "device_mac": "aabbcc",
                "device_model": "m1",
                "device_type": "ap",
                "device_version": "6.3.5",
            },
            {
                "fw_status": "inprogress",
                "fw_progress": 50,
                "fw_timestamp": 0,
                "fw_status_id": 0,
                "fw_will_retry": False,
                "fw_time_str": "-",
                "last_seen_str": "-",
            },
        )
        assert len(chk.upgrade_results) == 1

    def test_out_of_scope_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch, scope_choice="4")
        chk._maybe_add_to_results(
            {
                "site_id": "s1",
                "site_name": "Site 1",
                "device_id": "d1",
                "device_name": "n1",
                "device_mac": "aabbcc",
                "device_model": "m1",
                "device_type": "ap",
                "device_version": "6.3.5",
            },
            {
                "fw_status": "upgraded",
                "fw_progress": 100,
                "fw_timestamp": 0,
                "fw_status_id": 0,
                "fw_will_retry": False,
                "fw_time_str": "-",
                "last_seen_str": "-",
            },
        )
        assert chk.upgrade_results == []


class TestShouldIncludeDevice:
    """``_should_include_device`` scope gate branches."""

    @pytest.mark.parametrize("status", ["inprogress", "upgrading", "downloading"])
    def test_scope_3_active_included(self, monkeypatch: pytest.MonkeyPatch, status: str) -> None:
        chk = _make_checker(monkeypatch, scope_choice="3")
        assert chk._should_include_device({"fw_status": status, "fw_progress": 50, "fw_timestamp": 0}) is True

    def test_scope_3_stale_excluded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch, scope_choice="3")
        monkeypatch.setattr(chk, "_is_stale_upgrade", lambda _p, _t: True)
        assert chk._should_include_device({"fw_status": "inprogress", "fw_progress": 100, "fw_timestamp": 1}) is False

    def test_scope_3_non_active_excluded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch, scope_choice="3")
        assert chk._should_include_device({"fw_status": "upgraded", "fw_progress": 100, "fw_timestamp": 0}) is False

    def test_scope_4_failed_included(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch, scope_choice="4")
        assert chk._should_include_device({"fw_status": "failed", "fw_progress": 0, "fw_timestamp": 0}) is True

    def test_scope_4_non_failed_excluded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch, scope_choice="4")
        assert chk._should_include_device({"fw_status": "upgraded", "fw_progress": 100, "fw_timestamp": 0}) is False

    def test_default_includes_all(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch, scope_choice=None)
        assert chk._should_include_device({"fw_status": "whatever", "fw_progress": 0, "fw_timestamp": 0}) is True


class TestRenderActiveProgress:
    """``_render_active_progress`` branch coverage."""

    def test_stale_marker(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(chk, "_is_stale_upgrade", lambda _p, _t: True)
        assert "Stale" in chk._render_active_progress(100, 0)

    def test_progress_renders_bar(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(chk, "_is_stale_upgrade", lambda _p, _t: False)
        assert chk._render_active_progress(50, 0) == "[bar 50]"

    def test_no_progress_falls_back(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(chk, "_is_stale_upgrade", lambda _p, _t: False)
        assert chk._render_active_progress(None, 0) == "N/A"


class TestCreateProgressDisplay:
    """``_create_progress_display`` per-status rendering."""

    @pytest.mark.parametrize("status", ["inprogress", "upgrading", "downloading"])
    def test_active_delegates_to_render(self, monkeypatch: pytest.MonkeyPatch, status: str) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(chk, "_render_active_progress", lambda _p, _t: "RENDERED")
        assert chk._create_progress_display({"fw_status": status, "fw_progress": 40, "fw_timestamp": 0}) == "RENDERED"

    @pytest.mark.parametrize("status", ["upgraded", "success"])
    def test_completed_display(self, monkeypatch: pytest.MonkeyPatch, status: str) -> None:
        chk = _make_checker(monkeypatch)
        assert "Complete" in chk._create_progress_display({"fw_status": status, "fw_progress": 100, "fw_timestamp": 0})

    def test_failed_display(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        assert "FAILED" in chk._create_progress_display({"fw_status": "failed", "fw_progress": 0, "fw_timestamp": 0})

    def test_unknown_display(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        assert chk._create_progress_display({"fw_status": "mystery", "fw_progress": 0, "fw_timestamp": 0}) == "N/A"


class TestDisplaySummary:
    """``_display_summary`` + distribution helpers."""

    def test_summary_prints_totals(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)
        chk.summary["total_devices"] = 3
        chk._display_summary()
        out = capsys.readouterr().out
        assert "Firmware Status Summary" in out
        assert "Total devices analyzed: 3" in out

    def test_display_average_progress_when_zero_count(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        chk._display_average_progress()
        assert "Average" not in capsys.readouterr().out

    def test_display_average_progress_prints(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        chk.summary["progress_total"] = 100
        chk.summary["progress_count"] = 2
        chk._display_average_progress()
        assert "Average upgrade progress" in capsys.readouterr().out

    def test_status_distribution_empty(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        chk._display_status_distribution()
        assert "Status Distribution" not in capsys.readouterr().out

    def test_status_distribution_populated(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        chk.summary["devices_by_status"] = {"upgraded": 3, "failed": 1}
        chk._display_status_distribution()
        out = capsys.readouterr().out
        assert "upgraded: 3" in out
        assert "failed: 1" in out

    def test_type_distribution_empty_shows_message(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        chk._display_type_distribution()
        assert "No device type information" in capsys.readouterr().out

    def test_type_distribution_uses_friendly_names(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        chk.summary["devices_by_type"] = {"ap": 2, "switch": 1, "custom": 4}
        chk._display_type_distribution()
        out = capsys.readouterr().out
        assert "Access Points" in out
        assert "Switches" in out
        assert "CUSTOM" in out

    def test_version_distribution(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)
        chk.summary["devices_by_version"] = {"6.3.5": 2, "6.3.4": 1}
        chk._display_version_distribution()
        assert "6.3.5: 2" in capsys.readouterr().out

    def test_model_distribution(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)
        chk.summary["devices_by_model"] = {"AP41": 5}
        chk._display_model_distribution()
        assert "AP41: 5" in capsys.readouterr().out


class TestDisplayUpgradingDevices:
    """``_display_upgrading_devices`` + progress distribution."""

    def test_empty_short_circuits(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)
        chk._display_upgrading_devices()
        assert capsys.readouterr().out == ""

    def test_populated_renders_table(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)
        chk.summary["devices_upgrading"] = [
            {
                "device_name": "n1",
                "device_type": "ap",
                "device_mac": "aabbcc",
                "device_model": "m1",
                "site_name": "Site 1",
                "current_version": "6.3.5",
                "progress": 60,
                "fw_timestamp": 0,
            }
        ]
        chk._display_upgrading_devices()
        out = capsys.readouterr().out
        assert "Currently Upgrading" in out
        assert "n1" in out

    def test_print_upgrading_device_defaults(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        chk._print_upgrading_device(
            {
                "device_name": "",
                "device_type": "",
                "device_mac": "",
                "device_model": "",
                "site_name": "",
                "current_version": "",
                "progress": 25,
                "fw_timestamp": 0,
            }
        )
        out = capsys.readouterr().out
        assert "Unnamed" in out
        assert "Unknown" in out

    @pytest.mark.parametrize(
        "progress,bucket",
        [
            (0, "0-25%"),
            (25, "0-25%"),
            (26, "26-50%"),
            (50, "26-50%"),
            (51, "51-75%"),
            (75, "51-75%"),
            (76, "76-99%"),
            (99, "76-99%"),
            (100, "100%"),
        ],
    )
    def test_classify_progress_bucket(self, progress: int, bucket: str) -> None:
        assert FirmwareUpgradeStatusChecker._classify_progress_bucket(progress) == bucket

    def test_display_progress_distribution(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        chk._display_progress_distribution(
            [
                {"progress": 10},
                {"progress": 60},
                {"progress": 100},
            ]
        )
        out = capsys.readouterr().out
        assert "0-25%" in out
        assert "51-75%" in out
        assert "100%" in out


class TestFetchSsrUpgradesPayload:
    """``_fetch_ssr_upgrades_payload`` HTTP-shape guard."""

    def test_non_200_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        import mistapi.api.v1.orgs.ssr as real_ssr

        monkeypatch.setattr(real_ssr, "listOrgSsrUpgrades", lambda *_a, **_k: _FakeResponse(500, None))
        assert chk._fetch_ssr_upgrades_payload() is None

    def test_missing_data_attr_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        import mistapi.api.v1.orgs.ssr as real_ssr

        monkeypatch.setattr(
            real_ssr,
            "listOrgSsrUpgrades",
            lambda *_a, **_k: _FakeResponse(200, None, has_data_attr=False),
        )
        assert chk._fetch_ssr_upgrades_payload() is None

    def test_empty_data_returns_empty_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        import mistapi.api.v1.orgs.ssr as real_ssr

        monkeypatch.setattr(real_ssr, "listOrgSsrUpgrades", lambda *_a, **_k: _FakeResponse(200, None))
        assert chk._fetch_ssr_upgrades_payload() == []

    def test_populated_returns_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        import mistapi.api.v1.orgs.ssr as real_ssr

        monkeypatch.setattr(
            real_ssr,
            "listOrgSsrUpgrades",
            lambda *_a, **_k: _FakeResponse(200, [{"id": "u1"}]),
        )
        assert chk._fetch_ssr_upgrades_payload() == [{"id": "u1"}]


class TestCheckSsrUpgrades:
    """``_check_ssr_upgrades`` full-flow branches."""

    def test_none_payload_short_circuits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(chk, "_fetch_ssr_upgrades_payload", lambda: None)
        chk._check_ssr_upgrades()
        assert chk.active_upgrades == []

    def test_empty_payload_prints_message(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(chk, "_fetch_ssr_upgrades_payload", lambda: [])
        chk._check_ssr_upgrades()
        assert "No active SSR upgrade" in capsys.readouterr().out

    def test_populated_processes_each(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(chk, "_fetch_ssr_upgrades_payload", lambda: [{"id": "u1"}, {"id": "u2"}])
        called = []
        monkeypatch.setattr(chk, "_process_ssr_upgrade", lambda u: called.append(u))
        chk._check_ssr_upgrades()
        assert len(called) == 2

    def test_exception_prints_warning(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(
            chk,
            "_fetch_ssr_upgrades_payload",
            lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        chk._check_ssr_upgrades()
        assert "Error checking SSR upgrade" in capsys.readouterr().out


class TestProcessSsrUpgrade:
    """``_process_ssr_upgrade`` + helpers."""

    def test_appends_record(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        chk._process_ssr_upgrade(
            {
                "id": "abcdefgh-longer",
                "status": "upgrading",
                "strategy": "big_bang",
                "counts": {"upgrading": 2, "success": 1, "failed": 0, "queued": 3},
                "versions": {"router-a": "6.3.5"},
                "channel": "stable",
            }
        )
        assert len(chk.active_upgrades) == 1
        rec = chk.active_upgrades[0]
        assert rec["upgrade_id"] == "abcdefgh-longer"
        assert rec["total_devices"] == 6
        assert rec["site_id"] == "N/A (Org-level)"

    def test_build_ssr_status_parts_all_buckets(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        parts = chk._build_ssr_status_parts({"upgrading": 1, "success": 2, "failed": 3, "queued": 4})
        assert parts == ["1 upgrading", "2 completed", "3 failed", "4 queued"]

    def test_build_ssr_status_parts_all_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        assert chk._build_ssr_status_parts({"upgrading": 0}) == []

    def test_build_version_info_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        assert chk._build_version_info({}) == "Multiple versions"

    def test_build_version_info_single(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        assert chk._build_version_info({"a": "6.3.5"}) == "-> 6.3.5"

    def test_build_version_info_multiple(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        assert "Multiple versions" in chk._build_version_info({"a": "6.3.5", "b": "6.3.6"})


class TestLoadOrgUpgradesFromFile:
    """``_load_org_upgrades_from_file`` json + filter."""

    def test_read_error_returns_none(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(builtins, "open", MagicMock(side_effect=OSError("nope")))
        assert chk._load_org_upgrades_from_file("missing.json") is None
        assert "Failed to read" in capsys.readouterr().out

    def test_filters_by_org_id(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
        chk = _make_checker(monkeypatch, org_id="me")
        file = tmp_path / "upgrades.json"
        file.write_text(json.dumps([{"org_id": "me"}, {"org_id": "other"}]))
        assert chk._load_org_upgrades_from_file(str(file)) == [{"org_id": "me"}]


class TestCheckStoredUpgrades:
    """``_check_stored_upgrades`` decision tree."""

    def test_no_file(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(os.path, "exists", lambda _p: False)
        chk._check_stored_upgrades()
        assert "No site-level upgrade tracking file" in capsys.readouterr().out

    def test_load_error_returns(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(os.path, "exists", lambda _p: True)
        monkeypatch.setattr(chk, "_load_org_upgrades_from_file", lambda _p: None)
        chk._check_stored_upgrades()

    def test_empty_after_filter(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(os.path, "exists", lambda _p: True)
        monkeypatch.setattr(chk, "_load_org_upgrades_from_file", lambda _p: [])
        chk._check_stored_upgrades()
        assert "No stored upgrades match" in capsys.readouterr().out

    def test_delegates_per_record(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(os.path, "exists", lambda _p: True)
        monkeypatch.setattr(chk, "_load_org_upgrades_from_file", lambda _p: [{"a": 1}, {"a": 2}])
        called: list[dict[str, Any]] = []
        monkeypatch.setattr(chk, "_check_stored_upgrade", lambda rec: called.append(rec))
        chk._check_stored_upgrades()
        assert len(called) == 2


class TestSafeGetSiteUpgradeData:
    """``_safe_get_site_upgrade_data`` API-call error tolerance."""

    def test_exception_returns_none(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        import mistapi.api.v1.sites.devices as real_dev

        def blow(*_a: Any, **_k: Any) -> None:
            raise RuntimeError("boom")

        monkeypatch.setattr(real_dev, "getSiteDeviceUpgrade", blow)
        assert FirmwareUpgradeStatusChecker._safe_get_site_upgrade_data("u1", "s1", "Site 1") is None
        assert "Failed to check upgrade" in capsys.readouterr().out

    def test_empty_data_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.sites.devices as real_dev

        monkeypatch.setattr(real_dev, "getSiteDeviceUpgrade", lambda *_a, **_k: _FakeResponse(200, None))
        assert FirmwareUpgradeStatusChecker._safe_get_site_upgrade_data("u1", "s1", "Site 1") is None

    def test_populated_returns_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mistapi.api.v1.sites.devices as real_dev

        monkeypatch.setattr(
            real_dev,
            "getSiteDeviceUpgrade",
            lambda *_a, **_k: _FakeResponse(200, {"status": "upgrading"}),
        )
        assert FirmwareUpgradeStatusChecker._safe_get_site_upgrade_data("u1", "s1", "Site 1") == {"status": "upgrading"}


class TestCheckStoredUpgrade:
    """``_check_stored_upgrade`` single-record probe."""

    def test_missing_fields_skipped(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        chk._check_stored_upgrade({"upgrade_id": None, "site_id": "s1"})
        assert chk.active_upgrades == []

    def test_present_data_records(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(
            type(chk),
            "_safe_get_site_upgrade_data",
            staticmethod(lambda *a, **kw: {"status": "up"}),
        )
        chk._check_stored_upgrade({"upgrade_id": "u12345678", "site_id": "s1", "site_name": "n"})
        assert len(chk.active_upgrades) == 1
        assert chk.active_upgrades[0]["upgrade_id"] == "u12345678"

    def test_empty_data_prints_no_longer_active(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(
            type(chk),
            "_safe_get_site_upgrade_data",
            staticmethod(lambda *a, **kw: None),
        )
        chk._check_stored_upgrade({"upgrade_id": "u12345678", "site_id": "s1", "site_name": "n"})
        assert "No longer active" in capsys.readouterr().out


class TestAuditLogs:
    """``_fetch_audit_logs_24h`` + ``_check_audit_logs`` + helpers."""

    def test_is_upgrade_event_matches_keywords(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        assert chk._is_upgrade_event({"message": "Firmware upgrade started"}) is True
        assert chk._is_upgrade_event({"message": "regular login"}) is False

    def test_filter_upgrade_events(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        events = chk._filter_upgrade_events([{"message": "upgrade"}, {"message": "hello"}])
        assert len(events) == 1

    def test_check_audit_logs_no_logs(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(chk, "_fetch_audit_logs_24h", lambda: [])
        chk._check_audit_logs()
        assert "No audit logs available" in capsys.readouterr().out

    def test_check_audit_logs_no_upgrade_events(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(chk, "_fetch_audit_logs_24h", lambda: [{"message": "login"}])
        chk._check_audit_logs()
        assert "No upgrade-related events" in capsys.readouterr().out

    def test_check_audit_logs_ok(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(
            chk,
            "_fetch_audit_logs_24h",
            lambda: [{"message": "firmware upgrade", "timestamp": 1700000000, "admin_name": "op", "site_name": "s"}],
        )
        chk._check_audit_logs()
        assert "1 upgrade-related audit event" in capsys.readouterr().out

    def test_check_audit_logs_exception(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)

        def blow() -> list[dict[str, Any]]:
            raise RuntimeError("api")

        monkeypatch.setattr(chk, "_fetch_audit_logs_24h", blow)
        chk._check_audit_logs()
        assert "Error checking audit logs" in capsys.readouterr().out

    def test_fetch_audit_logs_calls_api(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        mistapi = fm_mod.mistapi
        real_logs = mistapi.api.v1.orgs.logs

        monkeypatch.setattr(
            real_logs,
            "listOrgAuditLogs",
            lambda *_a, **_k: _FakeResponse(200, [{"message": "upgrade"}]),
        )
        monkeypatch.setattr(mistapi, "get_all", lambda response, mist_session: response.data)
        assert chk._fetch_audit_logs_24h() == [{"message": "upgrade"}]

    def test_display_audit_events(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)
        chk._display_audit_events(
            [
                {"timestamp": 1700000001, "admin_name": "op1", "message": "m1", "site_name": "s1"},
                {"timestamp": 1700000000, "admin_name": "op2", "message": "m2", "site_name": "s2"},
            ]
        )
        out = capsys.readouterr().out
        assert "op1" in out and "op2" in out


class TestDeviceEvents:
    """``_check_device_events`` + display helper."""

    def test_no_events(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(chk, "_fetch_device_upgrade_events_24h", lambda: [])
        chk._check_device_events()
        assert "No device upgrade events" in capsys.readouterr().out

    def test_populated(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(
            chk,
            "_fetch_device_upgrade_events_24h",
            lambda: [
                {"type": "SYSTEM_UPGRADE_STARTED"},
                {"type": "SYSTEM_UPGRADE_STARTED"},
                {"type": "SYSTEM_UPGRADE_FAILED"},
            ],
        )
        chk._check_device_events()
        out = capsys.readouterr().out
        assert "Started: 2" in out
        assert "Failed: 1" in out

    def test_exception(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)

        def blow() -> list[dict[str, Any]]:
            raise RuntimeError("api")

        monkeypatch.setattr(chk, "_fetch_device_upgrade_events_24h", blow)
        chk._check_device_events()
        assert "Error checking device events" in capsys.readouterr().out

    def test_fetch_device_events_calls_api(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        mistapi = fm_mod.mistapi
        real_dev = mistapi.api.v1.orgs.devices

        monkeypatch.setattr(
            real_dev,
            "searchOrgDeviceEvents",
            lambda *_a, **_k: _FakeResponse(200, [{"type": "SYSTEM_UPGRADE_STARTED"}]),
        )
        monkeypatch.setattr(mistapi, "get_all", lambda response, mist_session: response.data)
        assert chk._fetch_device_upgrade_events_24h() == [{"type": "SYSTEM_UPGRADE_STARTED"}]


class TestSiteUpgrades:
    """``_check_site_upgrades`` + single-site probe + reporting."""

    def test_report_sites_without_upgrades_skips_when_filter(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch, site_filter="site-x")
        chk._report_sites_without_upgrades(3, 1)
        assert capsys.readouterr().out == ""

    def test_report_sites_without_upgrades_prints_diff(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        chk._report_sites_without_upgrades(3, 1)
        assert "2 site(s) have no active" in capsys.readouterr().out

    def test_report_sites_without_upgrades_zero_diff_silent(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        chk._report_sites_without_upgrades(3, 3)
        assert capsys.readouterr().out == ""

    def test_check_site_upgrades_with_filter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch, site_filter="site-x")
        monkeypatch.setattr(chk, "_check_single_site_upgrades", lambda _s: True)
        chk._check_site_upgrades()

    def test_check_site_upgrades_no_filter_uses_first_5(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        chk.site_lookup = {f"s{i}": f"Name {i}" for i in range(10)}
        called: list[str] = []
        monkeypatch.setattr(chk, "_check_single_site_upgrades", lambda s: (called.append(s), False)[1])
        chk._check_site_upgrades()
        assert len(called) == 5

    def test_check_single_site_no_upgrades(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        mistapi = fm_mod.mistapi
        real_dev = mistapi.api.v1.sites.devices

        monkeypatch.setattr(real_dev, "listSiteDeviceUpgrades", lambda *_a, **_k: _FakeResponse(200, []))
        monkeypatch.setattr(mistapi, "get_all", lambda response, mist_session: response.data)
        assert chk._check_single_site_upgrades("s1") is False

    def test_check_single_site_populated(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        mistapi = fm_mod.mistapi
        real_dev = mistapi.api.v1.sites.devices

        monkeypatch.setattr(
            real_dev,
            "listSiteDeviceUpgrades",
            lambda *_a, **_k: _FakeResponse(200, [{"id": "u1"}]),
        )
        monkeypatch.setattr(mistapi, "get_all", lambda response, mist_session: response.data)
        called: list[dict[str, Any]] = []
        monkeypatch.setattr(chk, "_process_site_upgrade", lambda u, s, n: called.append(u))
        assert chk._check_single_site_upgrades("s1") is True
        assert len(called) == 1

    def test_check_single_site_exception(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        import mistapi.api.v1.sites.devices as real_dev

        def blow(*_a: Any, **_k: Any) -> None:
            raise RuntimeError("api")

        monkeypatch.setattr(real_dev, "listSiteDeviceUpgrades", blow)
        assert chk._check_single_site_upgrades("s1") is False
        assert "Error checking upgrades" in capsys.readouterr().out


class TestProcessSiteUpgrade:
    """``_process_site_upgrade`` + progress helper."""

    def test_appends_full_record(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        chk._process_site_upgrade(
            {
                "id": "u12345678xxxx",
                "status": "created",
                "strategy": "big_bang",
                "target_version": "6.3.5",
                "counts": {"total": 3, "downloaded": 2, "rebooted": 1, "failed": 0},
                "start_time": 1700000000,
            },
            "site-a",
            "Site A",
        )
        assert len(chk.active_upgrades) == 1
        row = chk.active_upgrades[0]
        assert row["target_version"] == "6.3.5"
        assert row["site_id"] == "site-a"
        assert row["total"] == 3

    def test_build_site_upgrade_progress_all(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        parts = chk._build_site_upgrade_progress({"total": 5, "downloaded": 3, "rebooted": 2, "failed": 1})
        assert "3/5 downloaded" in parts
        assert "2/5 rebooted" in parts
        assert "1 failed" in parts

    def test_build_site_upgrade_progress_no_total(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        assert chk._build_site_upgrade_progress({"total": 0}) == []


class TestExports:
    """CSV export helpers."""

    def test_export_device_status_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        chk._export_device_status("ts")  # no-op, no exceptions
        assert True

    def test_export_device_status_calls_writer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mh = _install_mh_proxy(monkeypatch)
        chk = FirmwareUpgradeStatusChecker()
        chk.upgrade_results = [{"row": 1}]
        chk._export_device_status("ts")
        mh.DataExporter.write_with_format_selection.assert_called_once()

    def test_export_device_status_write_error(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mh = _install_mh_proxy(monkeypatch)
        mh.DataExporter.write_with_format_selection.side_effect = RuntimeError("io")
        chk = FirmwareUpgradeStatusChecker()
        chk.upgrade_results = [{"row": 1}]
        chk._export_device_status("ts")
        assert "Failed to export device status" in capsys.readouterr().out

    def test_export_active_operations_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        chk._export_active_operations("ts")

    def test_export_active_operations_writes_csv(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
        chk = _make_checker(monkeypatch)
        chk.active_upgrades = [
            {
                "site_id": "s1",
                "site_name": "Site 1",
                "upgrade_id": "u1",
                "status": "ok",
                "strategy": "big_bang",
                "target_version": "6.3.5",
                "source": "site_lookup",
                "details": {"counts": {"total": 3}},
            }
        ]
        monkeypatch.chdir(tmp_path)
        (tmp_path / "data").mkdir()
        chk._export_active_operations("ts-42")
        csv_files = list((tmp_path / "data").glob("ActiveUpgradeOperations_*.csv"))
        assert len(csv_files) == 1

    def test_export_active_operations_write_error(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chk = _make_checker(monkeypatch)
        chk.active_upgrades = [{"source": "x"}]
        monkeypatch.setattr(builtins, "open", MagicMock(side_effect=OSError("io")))
        chk._export_active_operations("ts")
        assert "Failed to export upgrade operations" in capsys.readouterr().out

    def test_export_results_calls_both(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        called: list[str] = []
        monkeypatch.setattr(chk, "_export_device_status", lambda ts: called.append(f"dev-{ts}"))
        monkeypatch.setattr(chk, "_export_active_operations", lambda ts: called.append(f"act-{ts}"))
        chk._export_results()
        assert len(called) == 2


class TestMapUpgradeForExport:
    """``_map_upgrade_for_export`` + resolve helpers."""

    def test_maps_all_fields(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        mapped = chk._map_upgrade_for_export(
            {
                "site_id": "s1",
                "site_name": "n1",
                "upgrade_id": "u1",
                "status": "ok",
                "strategy": "big_bang",
                "target_version": "6.3.5",
                "start_time": 1700000000,
                "enable_p2p": True,
                "total_devices": 3,
                "source": "x",
                "timestamp": "2024-01-01T00:00:00+00:00",
                "details": {"counts": {"total": 3, "downloaded": 2}},
            }
        )
        assert mapped["site_id"] == "s1"
        assert mapped["total_devices"] == 3
        assert mapped["downloaded"] == 2
        assert "start_time" in mapped

    def test_falls_back_to_details(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        mapped = chk._map_upgrade_for_export(
            {"source": "x", "details": {"counts": {"downloaded": 5}, "enable_p2p": False}}
        )
        assert mapped["downloaded"] == 5

    def test_resolve_start_time_formats_epoch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        out = chk._resolve_upgrade_start_time({"start_time": 1700000000}, {})
        assert len(out) == 19

    def test_resolve_start_time_passthrough_when_not_epoch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        assert chk._resolve_upgrade_start_time({"start_time": "text"}, {}) == "text"

    def test_resolve_counts_prefers_top_level(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        counts = chk._resolve_upgrade_counts({"total_devices": 7}, {"total": 3})
        assert counts["total_devices"] == 7


class TestDisplayRecommendations:
    """``_display_recommendations`` branch coverage."""

    def test_no_activity(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)
        chk._display_recommendations()
        out = capsys.readouterr().out
        assert "No active upgrade operations" in out
        assert "Status check complete" in out

    def test_all_branches(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)
        chk.summary["upgrade_failed"] = 2
        chk.summary["upgrade_in_progress"] = 3
        chk.summary["devices_by_version"] = {"a": 1, "b": 1, "c": 1, "d": 1}
        chk.active_upgrades = [{"a": 1}]
        chk._display_recommendations()
        out = capsys.readouterr().out
        assert "2 devices have failed upgrades" in out
        assert "3 devices currently upgrading" in out
        assert "Multiple firmware versions detected" in out
        assert "1 active upgrade operations" in out


class TestCheckOrchestrator:
    """``check`` end-to-end orchestration + ``_check_active_operations`` fanout."""

    def test_early_exit_on_no_site(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(chk, "_resolve_site_filter", lambda: False)
        chk.check()  # no exception

    def test_early_exit_on_no_stats(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(chk, "_resolve_site_filter", lambda: True)
        monkeypatch.setattr(chk, "_fetch_device_stats", lambda: False)
        chk.check()

    def test_happy_path_calls_all_stages(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        monkeypatch.setattr(chk, "_resolve_site_filter", lambda: True)
        monkeypatch.setattr(chk, "_fetch_device_stats", lambda: True)
        stages: list[str] = []
        for name in [
            "_fetch_site_lookup",
            "_process_all_devices",
            "_display_summary",
            "_display_upgrading_devices",
            "_check_active_operations",
            "_export_results",
            "_display_recommendations",
        ]:
            monkeypatch.setattr(chk, name, lambda n=name: stages.append(n))
        chk.check()
        assert len(stages) == 7

    def test_check_active_operations_fanout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        called: list[str] = []
        for name in [
            "_check_ssr_upgrades",
            "_check_stored_upgrades",
            "_check_audit_logs",
            "_check_device_events",
            "_check_site_upgrades",
        ]:
            monkeypatch.setattr(chk, name, lambda n=name: called.append(n))
        chk._check_active_operations()
        assert len(called) == 5


class TestProcessAllDevices:
    """``_process_all_devices`` iteration wiring."""

    def test_iterates_and_delegates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        chk.all_device_stats = [{"id": "d1"}, {"id": "d2"}]
        seen: list[Any] = []
        monkeypatch.setattr(chk, "_extract_device_info", lambda d: {"device_id": d["id"]})
        monkeypatch.setattr(
            chk,
            "_process_fwupdate",
            lambda d, i: seen.append(("fw", i)) or {"fw_status": "no_upgrade_info"},
        )
        monkeypatch.setattr(chk, "_update_summary_counters", lambda i, f: seen.append(("counter", i)))
        monkeypatch.setattr(chk, "_maybe_add_to_results", lambda i, f: seen.append(("results", i)))
        chk._process_all_devices()
        assert len([entry for entry in seen if entry[0] == "fw"]) == 2
        assert len([entry for entry in seen if entry[0] == "counter"]) == 2


class TestRecordHelpers:
    """Small ``_record_*`` helpers append correctly shaped rows."""

    def test_record_ssr_upgrade(self, monkeypatch: pytest.MonkeyPatch) -> None:
        chk = _make_checker(monkeypatch)
        chk._record_ssr_upgrade("u1", "queued", "big_bang", 5, {"raw": True})
        assert chk.active_upgrades[0]["source"] == "ssr_api"
        assert chk.active_upgrades[0]["total_devices"] == 5

    def test_record_stored_upgrade(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        chk = _make_checker(monkeypatch)
        chk._record_stored_upgrade("u12345678", "s1", "Site 1", {"status": "up"})
        assert chk.active_upgrades[0]["source"] == "stored_tracking"
        assert "Site 1" in capsys.readouterr().out
