"""Unit tests for OrgClientSecurityExporter — covers every static-method branch.

Why:
    The tranche-18 push of issue #878 removes ``src/export/org_client_security_exporter.py``
    from the coverage ``omit`` list. This suite drives every public entry
    (wireless_clients, wired_clients, security_events, rogue_clients, rogue_aps)
    plus every private helper (_check_csv_cache_fresh, _load_site_list,
    _fetch_rogues_for_one_site, _collect_rogues_across_sites, _export_rogues)
    so the module lands at 100% line + branch coverage without touching live
    Mist APIs or the real filesystem.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from src.export import org_client_security_exporter as ocse
from src.export.org_client_security_exporter import OrgClientSecurityExporter

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_mh(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Install a synthetic ``MistHelper`` module returned by every lazy import.

    Why:
        Every helper in ``org_client_security_exporter`` calls
        ``importlib.import_module("MistHelper")``.  Patching that lookup once
        keeps the tests deterministic and avoids pulling in real live globals.
    """
    mh = ModuleType("MistHelper")
    mh.OrgExportUtils = MagicMock()  # type: ignore[attr-defined]
    mh.CacheUtils = MagicMock()  # type: ignore[attr-defined]
    mh.OrgSiteExporter = MagicMock()  # type: ignore[attr-defined]
    mh.FilePathUtils = MagicMock()  # type: ignore[attr-defined]
    mh.CSV_FRESHNESS_MINUTES = 60  # type: ignore[attr-defined]
    mh.ConfigUtils = MagicMock()  # type: ignore[attr-defined]
    mh.ConfigUtils.check_stop_signal.return_value = False
    mh.DataExporter = MagicMock()  # type: ignore[attr-defined]
    mh.apisession = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "MistHelper", mh)
    return mh


# ---------------------------------------------------------------------------
# wireless_clients / wired_clients
# ---------------------------------------------------------------------------


class TestClientDelegation:
    def test_wireless_clients_delegates(self, fake_mh: ModuleType) -> None:
        OrgClientSecurityExporter.wireless_clients()
        fake_mh.OrgExportUtils.export_data.assert_called_once()  # type: ignore[attr-defined]
        kwargs = fake_mh.OrgExportUtils.export_data.call_args.kwargs  # type: ignore[attr-defined]
        assert kwargs["data_type"] == "wireless clients"
        assert kwargs["sort_key"] == "mac"

    def test_wired_clients_delegates(self, fake_mh: ModuleType) -> None:
        OrgClientSecurityExporter.wired_clients()
        fake_mh.OrgExportUtils.export_data.assert_called_once()  # type: ignore[attr-defined]
        kwargs = fake_mh.OrgExportUtils.export_data.call_args.kwargs  # type: ignore[attr-defined]
        assert kwargs["data_type"] == "wired clients"
        assert kwargs["sort_key"] == "mac"


# ---------------------------------------------------------------------------
# security_events
# ---------------------------------------------------------------------------


class TestSecurityEvents:
    def test_delegates_to_service(self, fake_mh: ModuleType) -> None:
        with patch("src.refactors.serial_cc.security_events.SecurityEventsService") as svc:
            OrgClientSecurityExporter.security_events(fast=True)
        svc.execute.assert_called_once_with(True)

    def test_default_fast_false(self, fake_mh: ModuleType) -> None:
        with patch("src.refactors.serial_cc.security_events.SecurityEventsService") as svc:
            OrgClientSecurityExporter.security_events()
        svc.execute.assert_called_once_with(False)


# ---------------------------------------------------------------------------
# _check_csv_cache_fresh — 5 branches
# ---------------------------------------------------------------------------


class TestCheckCsvCacheFresh:
    def test_returns_false_when_not_fast(self, fake_mh: ModuleType) -> None:
        assert OrgClientSecurityExporter._check_csv_cache_fresh("Foo.csv", fast=False) is False

    def test_returns_false_when_file_missing(self, fake_mh: ModuleType) -> None:
        fake_mh.FilePathUtils.get_csv_path.return_value = "/tmp/missing.csv"  # type: ignore[attr-defined]
        with patch.object(ocse.os.path, "exists", return_value=False):
            assert OrgClientSecurityExporter._check_csv_cache_fresh("Foo.csv", fast=True) is False

    def test_returns_false_when_stale(self, fake_mh: ModuleType) -> None:
        fake_mh.FilePathUtils.get_csv_path.return_value = "/tmp/stale.csv"  # type: ignore[attr-defined]
        with (
            patch.object(ocse.os.path, "exists", return_value=True),
            patch.object(ocse.os.path, "getmtime", return_value=0),
            patch.object(ocse.time, "time", return_value=60 * 60 * 24),
        ):
            assert OrgClientSecurityExporter._check_csv_cache_fresh("Foo.csv", fast=True) is False

    def test_returns_true_when_fresh(self, fake_mh: ModuleType, capsys: pytest.CaptureFixture) -> None:
        fake_mh.FilePathUtils.get_csv_path.return_value = "/tmp/fresh.csv"  # type: ignore[attr-defined]
        with (
            patch.object(ocse.os.path, "exists", return_value=True),
            patch.object(ocse.os.path, "getmtime", return_value=1000),
            patch.object(ocse.time, "time", return_value=1000 + 30),
        ):
            assert OrgClientSecurityExporter._check_csv_cache_fresh("Foo.csv", fast=True) is True
        assert "Fast mode" in capsys.readouterr().out

    def test_returns_false_on_exception(self, fake_mh: ModuleType) -> None:
        fake_mh.FilePathUtils.get_csv_path.side_effect = RuntimeError("boom")  # type: ignore[attr-defined]
        assert OrgClientSecurityExporter._check_csv_cache_fresh("Foo.csv", fast=True) is False


# ---------------------------------------------------------------------------
# _load_site_list
# ---------------------------------------------------------------------------


class TestLoadSiteList:
    def test_success(self, fake_mh: ModuleType, tmp_path) -> None:
        csv_file = tmp_path / "SiteList.csv"
        csv_file.write_text("id,name\ns1,Site One\ns2,Site Two\n", encoding="utf-8")
        fake_mh.FilePathUtils.get_csv_path.return_value = str(csv_file)  # type: ignore[attr-defined]
        rows = OrgClientSecurityExporter._load_site_list()
        assert rows is not None
        assert len(rows) == 2
        assert rows[0]["id"] == "s1"
        assert rows[1]["name"] == "Site Two"

    def test_returns_none_on_exception(self, fake_mh: ModuleType) -> None:
        fake_mh.FilePathUtils.get_csv_path.return_value = "/nonexistent/path/SiteList.csv"  # type: ignore[attr-defined]
        assert OrgClientSecurityExporter._load_site_list() is None


# ---------------------------------------------------------------------------
# _fetch_rogues_for_one_site
# ---------------------------------------------------------------------------


class TestFetchRoguesForOneSite:
    def test_success_tags_rogues(self, fake_mh: ModuleType) -> None:
        fetch_callable = MagicMock(return_value=MagicMock())
        rogues = [{"bssid": "aa:bb"}, {"bssid": "cc:dd"}]
        with patch.object(ocse.mistapi, "get_all", return_value=rogues):
            result = OrgClientSecurityExporter._fetch_rogues_for_one_site(
                fetch_callable, "site-1", "Alpha", "24h", "rogue APs"
            )
        assert len(result) == 2
        assert all(r["site_id"] == "site-1" for r in result)
        assert all(r["site_name"] == "Alpha" for r in result)

    def test_exception_returns_empty(self, fake_mh: ModuleType) -> None:
        fetch_callable = MagicMock(side_effect=RuntimeError("boom"))
        result = OrgClientSecurityExporter._fetch_rogues_for_one_site(
            fetch_callable, "site-1", "Alpha", "24h", "rogue APs"
        )
        assert result == []


# ---------------------------------------------------------------------------
# _collect_rogues_across_sites
# ---------------------------------------------------------------------------


class TestCollectRoguesAcrossSites:
    def test_returns_none_when_sites_none(self, fake_mh: ModuleType) -> None:
        with patch.object(OrgClientSecurityExporter, "_load_site_list", return_value=None):
            result = OrgClientSecurityExporter._collect_rogues_across_sites(MagicMock(), "24h", "rogue APs")
        assert result is None

    def test_normal_path_aggregates(self, fake_mh: ModuleType) -> None:
        sites = [{"id": "s1", "name": "A"}, {"id": "s2", "name": "B"}]
        with (
            patch.object(OrgClientSecurityExporter, "_load_site_list", return_value=sites),
            patch.object(
                OrgClientSecurityExporter,
                "_fetch_rogues_for_one_site",
                side_effect=[[{"a": 1}], [{"b": 2}]],
            ),
        ):
            result = OrgClientSecurityExporter._collect_rogues_across_sites(MagicMock(), "24h", "rogue APs")
        assert result == [{"a": 1}, {"b": 2}]

    def test_stop_signal_breaks_early(self, fake_mh: ModuleType) -> None:
        sites = [{"id": "s1", "name": "A"}, {"id": "s2", "name": "B"}]
        fake_mh.ConfigUtils.check_stop_signal.return_value = True  # type: ignore[attr-defined]
        with (
            patch.object(OrgClientSecurityExporter, "_load_site_list", return_value=sites),
            patch.object(OrgClientSecurityExporter, "_fetch_rogues_for_one_site") as fetch_mock,
        ):
            result = OrgClientSecurityExporter._collect_rogues_across_sites(MagicMock(), "24h", "rogue APs")
        assert result == []
        fetch_mock.assert_not_called()

    def test_missing_site_id_skipped(self, fake_mh: ModuleType) -> None:
        sites = [{"name": "no-id"}, {"id": "s1", "name": "A"}]
        with (
            patch.object(OrgClientSecurityExporter, "_load_site_list", return_value=sites),
            patch.object(
                OrgClientSecurityExporter,
                "_fetch_rogues_for_one_site",
                return_value=[{"x": 1}],
            ) as fetch_mock,
        ):
            result = OrgClientSecurityExporter._collect_rogues_across_sites(MagicMock(), "24h", "rogue APs")
        assert result == [{"x": 1}]
        assert fetch_mock.call_count == 1


# ---------------------------------------------------------------------------
# _export_rogues
# ---------------------------------------------------------------------------


class TestExportRogues:
    def test_writes_when_rogues_present(self, fake_mh: ModuleType, capsys: pytest.CaptureFixture) -> None:
        rogues = [{"bssid": "aa"}, {"bssid": "bb"}]
        with (
            patch.object(ocse.DataProcessingUtils, "flatten_nested_fields", return_value=rogues) as flat,
            patch.object(ocse.DataProcessingUtils, "escape_multiline", return_value=rogues) as esc,
        ):
            OrgClientSecurityExporter._export_rogues(rogues, "OrgRogueAPs", "rogue APs")
        flat.assert_called_once_with(rogues)
        esc.assert_called_once_with(rogues)
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(rogues, "OrgRogueAPs")  # type: ignore[attr-defined]
        assert "2 rogue APs exported" in capsys.readouterr().out

    def test_empty_rogues_logs_only(self, fake_mh: ModuleType, capsys: pytest.CaptureFixture) -> None:
        OrgClientSecurityExporter._export_rogues([], "OrgRogueAPs", "rogue APs")
        fake_mh.DataExporter.write_with_format_selection.assert_not_called()  # type: ignore[attr-defined]
        assert "No rogue APs detected" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# rogue_clients / rogue_aps
# ---------------------------------------------------------------------------


class TestRogueClients:
    def test_cache_hit_short_circuits(self, fake_mh: ModuleType) -> None:
        with (
            patch.object(OrgClientSecurityExporter, "_check_csv_cache_fresh", return_value=True),
            patch.object(OrgClientSecurityExporter, "_collect_rogues_across_sites") as collect,
        ):
            OrgClientSecurityExporter.rogue_clients(fast=True)
        collect.assert_not_called()

    def test_collect_returns_none_aborts(self, fake_mh: ModuleType) -> None:
        with (
            patch.object(OrgClientSecurityExporter, "_check_csv_cache_fresh", return_value=False),
            patch.object(ocse.TimeUtils, "get_dynamic_lookback_hours", return_value=168),
            patch.object(ocse.TimeUtils, "log_dynamic_lookback"),
            patch.object(OrgClientSecurityExporter, "_collect_rogues_across_sites", return_value=None),
            patch.object(OrgClientSecurityExporter, "_export_rogues") as export_mock,
        ):
            OrgClientSecurityExporter.rogue_clients()
        export_mock.assert_not_called()

    def test_normal_flow_exports(self, fake_mh: ModuleType) -> None:
        rogues = [{"a": 1}]
        with (
            patch.object(OrgClientSecurityExporter, "_check_csv_cache_fresh", return_value=False),
            patch.object(ocse.TimeUtils, "get_dynamic_lookback_hours", return_value=168),
            patch.object(ocse.TimeUtils, "log_dynamic_lookback"),
            patch.object(OrgClientSecurityExporter, "_collect_rogues_across_sites", return_value=rogues),
            patch.object(OrgClientSecurityExporter, "_export_rogues") as export_mock,
        ):
            OrgClientSecurityExporter.rogue_clients()
        export_mock.assert_called_once_with(rogues, "OrgRogueClients", "rogue clients")


class TestRogueAps:
    def test_cache_hit_short_circuits(self, fake_mh: ModuleType) -> None:
        with (
            patch.object(OrgClientSecurityExporter, "_check_csv_cache_fresh", return_value=True),
            patch.object(OrgClientSecurityExporter, "_collect_rogues_across_sites") as collect,
        ):
            OrgClientSecurityExporter.rogue_aps(fast=True)
        collect.assert_not_called()

    def test_collect_returns_none_aborts(self, fake_mh: ModuleType) -> None:
        with (
            patch.object(OrgClientSecurityExporter, "_check_csv_cache_fresh", return_value=False),
            patch.object(ocse.TimeUtils, "get_dynamic_lookback_hours", return_value=168),
            patch.object(ocse.TimeUtils, "log_dynamic_lookback"),
            patch.object(OrgClientSecurityExporter, "_collect_rogues_across_sites", return_value=None),
            patch.object(OrgClientSecurityExporter, "_export_rogues") as export_mock,
        ):
            OrgClientSecurityExporter.rogue_aps()
        export_mock.assert_not_called()

    def test_normal_flow_exports(self, fake_mh: ModuleType) -> None:
        rogues = [{"a": 1}]
        with (
            patch.object(OrgClientSecurityExporter, "_check_csv_cache_fresh", return_value=False),
            patch.object(ocse.TimeUtils, "get_dynamic_lookback_hours", return_value=168),
            patch.object(ocse.TimeUtils, "log_dynamic_lookback"),
            patch.object(OrgClientSecurityExporter, "_collect_rogues_across_sites", return_value=rogues),
            patch.object(OrgClientSecurityExporter, "_export_rogues") as export_mock,
        ):
            OrgClientSecurityExporter.rogue_aps()
        export_mock.assert_called_once_with(rogues, "OrgRogueAPs", "rogue APs")


def test_smoke_module_symbols() -> None:
    """Sanity check module exports match documented public API."""
    assert isinstance(OrgClientSecurityExporter.__doc__, str)
    for name in ("wireless_clients", "wired_clients", "security_events", "rogue_clients", "rogue_aps"):
        assert callable(getattr(OrgClientSecurityExporter, name))
