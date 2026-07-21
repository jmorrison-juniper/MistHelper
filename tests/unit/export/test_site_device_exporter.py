"""Unit tests for ``src.export.site_device_exporter.SiteDeviceExporter``.

Why: Un-omitting this module in ``[tool.coverage.run].omit`` requires 100%
line + branch coverage on the 13 static methods that ship site-level device
inventory, stats, port stats, and virtual chassis exports. The module resolves
its cross-class collaborators lazily through
``importlib.import_module("MistHelper")``; tests inject a fake ``MistHelper``
module via ``sys.modules`` to observe and control those interactions without
importing the monolith.
"""

from __future__ import annotations

import logging
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

LOGGER_NAME = "src.export.site_device_exporter"


@pytest.fixture
def fake_mh(monkeypatch):
    """Install a fake MistHelper module for lazy importlib resolution.

    Why: SiteDeviceExporter reads apisession, DataExporter, PromptUtils,
    ConfigUtils, APICoreFetchUtils, TimeUtils, EnhancedSSHRunner,
    InsightMetricsUtils, PacketCaptureManager, IsDebugMode, PrettyTable,
    PROGRESS_EMITTER, ProgressContext, and mistapi at call time. Replacing the
    module lets tests observe those interactions cleanly.
    """
    mh = ModuleType("MistHelper")
    mh.apisession = MagicMock()
    mh.DataExporter = MagicMock()
    mh.PromptUtils = MagicMock()
    mh.ConfigUtils = MagicMock()
    mh.APICoreFetchUtils = MagicMock()
    mh.TimeUtils = MagicMock()
    mh.EnhancedSSHRunner = MagicMock()
    mh.InsightMetricsUtils = MagicMock()
    mh.PacketCaptureManager = MagicMock()
    mh.IsDebugMode = MagicMock()
    mh.PrettyTable = MagicMock()
    mh.PROGRESS_EMITTER = MagicMock()
    mh.ProgressContext = MagicMock()
    mh.mistapi = MagicMock()
    monkeypatch.setitem(sys.modules, "MistHelper", mh)
    return mh


class TestDeviceInventory:
    """Cover SiteDeviceExporter.device_inventory."""

    def test_no_devices_returns_early(self, fake_mh, caplog):
        """Empty rawdata → warns via logger, no write."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with (
            patch(
                "src.export.site_device_exporter.mistapi.api.v1.sites.devices.listSiteDevices",
                return_value=MagicMock(data=[]),
            ),
            caplog.at_level(logging.WARNING, logger=LOGGER_NAME),
        ):
            SiteDeviceExporter.device_inventory("s1")

        fake_mh.DataExporter.write_with_format_selection.assert_not_called()
        assert "No devices found" in caplog.text

    def test_type_filter_no_match_returns_early(self, fake_mh):
        """device_type filter returns None → aborts before write."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with (
            patch(
                "src.export.site_device_exporter.mistapi.api.v1.sites.devices.listSiteDevices",
                return_value=MagicMock(data=[{"type": "ap", "model": "AP41"}]),
            ),
            patch.object(SiteDeviceExporter, "_filter_devices_by_type", return_value=None),
        ):
            SiteDeviceExporter.device_inventory("s1", device_type="switch")

        fake_mh.DataExporter.write_with_format_selection.assert_not_called()

    def test_type_all_skips_filter_writes_csv(self, fake_mh):
        """type='all' → no filter call; flow through sort/flatten/write/display."""
        from src.export.site_device_exporter import SiteDeviceExporter

        rows = [{"type": "ap", "model": "AP41"}]
        with (
            patch(
                "src.export.site_device_exporter.mistapi.api.v1.sites.devices.listSiteDevices",
                return_value=MagicMock(data=rows),
            ),
            patch("src.export.site_device_exporter.DataProcessingUtils") as dpu,
            patch.object(SiteDeviceExporter, "_display_inventory_table"),
        ):
            dpu.flatten_nested_fields.return_value = rows
            dpu.escape_multiline.return_value = rows
            dpu.get_unique_keys.return_value = ["type", "model"]
            SiteDeviceExporter.device_inventory("s1", device_type="all")

        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(rows, "SiteInventory.csv")

    def test_type_filter_matches_writes_csv(self, fake_mh):
        """device_type='switch' → filter path returns rows and writes CSV."""
        from src.export.site_device_exporter import SiteDeviceExporter

        rows = [{"type": "switch", "model": "EX4400"}]
        with (
            patch(
                "src.export.site_device_exporter.mistapi.api.v1.sites.devices.listSiteDevices",
                return_value=MagicMock(data=rows),
            ),
            patch.object(SiteDeviceExporter, "_filter_devices_by_type", return_value=rows),
            patch("src.export.site_device_exporter.DataProcessingUtils") as dpu,
            patch.object(SiteDeviceExporter, "_display_inventory_table"),
        ):
            dpu.flatten_nested_fields.return_value = rows
            dpu.escape_multiline.return_value = rows
            dpu.get_unique_keys.return_value = ["type", "model"]
            SiteDeviceExporter.device_inventory("s1", device_type="switch", csv_filename="X.csv")

        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(rows, "X.csv")


class TestFilterDevicesByType:
    """Cover SiteDeviceExporter._filter_devices_by_type."""

    def test_match_returns_filtered(self, fake_mh):
        """Rows with matching type are kept."""
        from src.export.site_device_exporter import SiteDeviceExporter

        rows = [{"type": "ap"}, {"type": "switch"}]
        result = SiteDeviceExporter._filter_devices_by_type(rows, "switch", "s1")
        assert result == [{"type": "switch"}]

    def test_no_match_returns_none(self, fake_mh, caplog):
        """No matches → warns via logger, returns None."""
        from src.export.site_device_exporter import SiteDeviceExporter

        rows = [{"type": "ap"}]
        with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
            result = SiteDeviceExporter._filter_devices_by_type(rows, "switch", "s1")
        assert result is None
        assert "No devices of type 'switch'" in caplog.text


class TestDisplayInventoryTable:
    """Cover SiteDeviceExporter._display_inventory_table."""

    def test_sorts_by_model_when_present(self, fake_mh):
        """Model in fields → sortby set to 'model'."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with patch("src.export.site_device_exporter.PrettyTable") as PT:
            table = MagicMock()
            PT.return_value = table
            SiteDeviceExporter._display_inventory_table([{"model": "AP41"}], ["model"])
        assert table.sortby == "model"

    def test_no_model_field_skips_sort(self, fake_mh):
        """No model column → sortby left untouched."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with patch("src.export.site_device_exporter.PrettyTable") as PT:
            table = MagicMock()
            PT.return_value = table
            SiteDeviceExporter._display_inventory_table([{"name": "x"}], ["name"])
        table.add_row.assert_called_once()

    def test_sort_exception_logged(self, fake_mh, caplog):
        """Exception on sortby assignment → warning logged, method continues."""
        from src.export.site_device_exporter import SiteDeviceExporter

        class BadTable:
            field_names: list[str] = []

            def __setattr__(self, name, value):
                if name == "sortby":
                    raise RuntimeError("bad sort")
                super().__setattr__(name, value)

            def add_row(self, _row):
                pass

            def get_string(self):
                return ""

        with patch("src.export.site_device_exporter.PrettyTable", return_value=BadTable()):
            SiteDeviceExporter._display_inventory_table([{"model": "AP41"}], ["model"])


class TestPersistSiteDeviceStats:
    """Cover SiteDeviceExporter._persist_site_device_stats."""

    def test_empty_prints_and_returns(self, fake_mh, caplog):
        """Empty rawdata → warns via logger, no flatten/write."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
            SiteDeviceExporter._persist_site_device_stats([], "HQ")
        fake_mh.DataExporter.write_with_format_selection.assert_not_called()
        assert "No device statistics" in caplog.text

    def test_non_empty_flattens_and_writes(self, fake_mh, caplog):
        """Non-empty → flatten/escape/write with per-site filename."""
        from src.export.site_device_exporter import SiteDeviceExporter

        rows = [{"id": "d1"}]
        with (
            patch("src.export.site_device_exporter.DataProcessingUtils") as dpu,
            caplog.at_level(logging.INFO, logger=LOGGER_NAME),
        ):
            dpu.flatten_nested_fields.return_value = rows
            dpu.escape_multiline.return_value = rows
            SiteDeviceExporter._persist_site_device_stats(rows, "HQ Site")

        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(rows, "SiteDeviceStats_HQ_Site.csv")
        assert "1 device stats exported" in caplog.text


class TestResolveSiteForStats:
    """Cover SiteDeviceExporter._resolve_site_for_stats."""

    def test_no_site_returns_none(self, fake_mh):
        """PromptUtils.select_site None → returns None."""
        from src.export.site_device_exporter import SiteDeviceExporter

        fake_mh.PromptUtils.select_site.return_value = None
        assert SiteDeviceExporter._resolve_site_for_stats() is None

    def test_no_org_returns_none(self, fake_mh):
        """No org_id → returns None."""
        from src.export.site_device_exporter import SiteDeviceExporter

        fake_mh.PromptUtils.select_site.return_value = "s1"
        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = None
        assert SiteDeviceExporter._resolve_site_for_stats() is None

    def test_happy_path_resolves_name(self, fake_mh):
        """Site + org resolved → returns (site_id, site_name)."""
        from src.export.site_device_exporter import SiteDeviceExporter

        fake_mh.PromptUtils.select_site.return_value = "s1"
        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org1"
        fake_mh.APICoreFetchUtils.all_sites_with_limit.return_value = [{"id": "s1", "name": "HQ"}]
        assert SiteDeviceExporter._resolve_site_for_stats("data") == ("s1", "HQ")

    def test_no_matching_site_falls_back_to_id(self, fake_mh):
        """No matching site row → name falls back to id."""
        from src.export.site_device_exporter import SiteDeviceExporter

        fake_mh.PromptUtils.select_site.return_value = "s1"
        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org1"
        fake_mh.APICoreFetchUtils.all_sites_with_limit.return_value = [{"id": "other", "name": "X"}]
        assert SiteDeviceExporter._resolve_site_for_stats() == ("s1", "s1")


class TestDeviceStats:
    """Cover SiteDeviceExporter.device_stats."""

    def test_resolver_none_aborts(self, fake_mh):
        """Resolver returns None → early return, no fetch."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with patch.object(SiteDeviceExporter, "_resolve_site_for_stats", return_value=None):
            SiteDeviceExporter.device_stats()

    def test_happy_path_persists(self, fake_mh):
        """Resolver + fetch OK → _persist called with rows and site name."""
        from src.export.site_device_exporter import SiteDeviceExporter

        rows = [{"id": "d1"}]
        with (
            patch.object(SiteDeviceExporter, "_resolve_site_for_stats", return_value=("s1", "HQ")),
            patch(
                "src.export.site_device_exporter.mistapi.api.v1.sites.stats.listSiteDevicesStats",
                return_value=MagicMock(),
            ),
            patch("src.export.site_device_exporter.mistapi.get_all", return_value=rows),
            patch.object(SiteDeviceExporter, "_persist_site_device_stats") as persist,
        ):
            SiteDeviceExporter.device_stats()

        persist.assert_called_once_with(rows, "HQ")

    def test_fetch_exception_logged(self, fake_mh, caplog):
        """Fetch raises → error logged via logger, no crash."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with (
            patch.object(SiteDeviceExporter, "_resolve_site_for_stats", return_value=("s1", "HQ")),
            patch(
                "src.export.site_device_exporter.mistapi.api.v1.sites.stats.listSiteDevicesStats",
                side_effect=RuntimeError("boom"),
            ),
            caplog.at_level(logging.ERROR, logger=LOGGER_NAME),
        ):
            SiteDeviceExporter.device_stats()

        assert "Error fetching device statistics" in caplog.text


class TestPortStats:
    """Cover SiteDeviceExporter.port_stats."""

    def test_no_emitter_skips_progress(self, fake_mh):
        """PROGRESS_EMITTER None → skips emit_progress_start/complete."""
        from src.export.site_device_exporter import SiteDeviceExporter

        fake_mh.PROGRESS_EMITTER = None
        with patch("src.export.site_device_exporter.SiteExportUtils") as SEU:
            SiteDeviceExporter.port_stats()

        SEU.assert_called_once()
        SEU.return_value._export_data.assert_called_once()

    def test_with_emitter_emits_start_and_complete(self, fake_mh):
        """PROGRESS_EMITTER present → emit_progress_start + emit_progress_complete both called."""
        from src.export.site_device_exporter import SiteDeviceExporter

        emitter = MagicMock()
        fake_mh.PROGRESS_EMITTER = emitter
        with patch("src.export.site_device_exporter.SiteExportUtils") as SEU:
            SiteDeviceExporter.port_stats()

        emitter.emit_progress_start.assert_called_once()
        emitter.emit_progress_complete.assert_called_once()
        SEU.return_value._export_data.assert_called_once()


class TestDeviceVirtualChassis:
    """Cover SiteDeviceExporter.device_virtual_chassis."""

    def test_no_site_aborts(self, fake_mh):
        """No site → early return."""
        from src.export.site_device_exporter import SiteDeviceExporter

        fake_mh.PromptUtils.select_site.return_value = None
        with patch.object(SiteDeviceExporter, "_export_vc_for_device") as export:
            SiteDeviceExporter.device_virtual_chassis()
        export.assert_not_called()

    def test_no_device_aborts(self, fake_mh):
        """No device selected → early return."""
        from src.export.site_device_exporter import SiteDeviceExporter

        fake_mh.PromptUtils.select_site.return_value = "s1"
        fake_mh.PromptUtils.select_device_id_from_inventory.return_value = None
        with patch.object(SiteDeviceExporter, "_export_vc_for_device") as export:
            SiteDeviceExporter.device_virtual_chassis()
        export.assert_not_called()

    def test_happy_path_calls_export(self, fake_mh):
        """Site + device selected → resolve name + export VC."""
        from src.export.site_device_exporter import SiteDeviceExporter

        fake_mh.PromptUtils.select_site.return_value = "s1"
        fake_mh.PromptUtils.select_device_id_from_inventory.return_value = "d1"
        with (
            patch.object(SiteDeviceExporter, "_resolve_device_name", return_value="sw1"),
            patch.object(SiteDeviceExporter, "_export_vc_for_device") as export,
        ):
            SiteDeviceExporter.device_virtual_chassis()

        export.assert_called_once_with("s1", "d1", "sw1")


class TestResolveDeviceName:
    """Cover SiteDeviceExporter._resolve_device_name."""

    def test_match_returns_name(self, fake_mh):
        """Matching device → returns its name."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with (
            patch(
                "src.export.site_device_exporter.mistapi.api.v1.sites.devices.listSiteDevices",
                return_value=MagicMock(),
            ),
            patch(
                "src.export.site_device_exporter.mistapi.get_all",
                return_value=[{"id": "d1", "name": "sw1"}, {"id": "d2", "name": "sw2"}],
            ),
        ):
            assert SiteDeviceExporter._resolve_device_name("s1", "d2") == "sw2"

    def test_no_match_falls_back_to_id(self, fake_mh):
        """No matching device → returns device_id."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with (
            patch(
                "src.export.site_device_exporter.mistapi.api.v1.sites.devices.listSiteDevices",
                return_value=MagicMock(),
            ),
            patch("src.export.site_device_exporter.mistapi.get_all", return_value=[]),
        ):
            assert SiteDeviceExporter._resolve_device_name("s1", "d1") == "d1"


class TestExportVcForDevice:
    """Cover SiteDeviceExporter._export_vc_for_device."""

    def test_no_response_data_warns(self, fake_mh, caplog):
        """response.data empty → warns via logger + returns without write."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with (
            patch(
                "src.export.site_device_exporter.mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis",
                return_value=MagicMock(data=None),
            ),
            caplog.at_level(logging.WARNING, logger=LOGGER_NAME),
        ):
            SiteDeviceExporter._export_vc_for_device("s1", "d1", "sw1")

        fake_mh.DataExporter.write_with_format_selection.assert_not_called()
        assert "No virtual chassis data" in caplog.text

    def test_dict_response_normalized_to_list(self, fake_mh):
        """response.data as dict → wrapped into a list before flatten."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with (
            patch(
                "src.export.site_device_exporter.mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis",
                return_value=MagicMock(data={"members": ["m1"]}),
            ),
            patch("src.export.site_device_exporter.DataProcessingUtils") as dpu,
            patch.object(SiteDeviceExporter, "_print_vc_summary"),
        ):
            dpu.flatten_nested_fields.return_value = [{"members": ["m1"]}]
            dpu.escape_multiline.return_value = [{"members": ["m1"]}]
            SiteDeviceExporter._export_vc_for_device("s1", "d1", "sw1")

        dpu.flatten_nested_fields.assert_called_once_with([{"members": ["m1"]}])
        fake_mh.DataExporter.write_with_format_selection.assert_called_once()

    def test_list_response_used_directly(self, fake_mh):
        """response.data as list → used as-is."""
        from src.export.site_device_exporter import SiteDeviceExporter

        rows = [{"members": ["m1"]}, {"members": ["m2"]}]
        with (
            patch(
                "src.export.site_device_exporter.mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis",
                return_value=MagicMock(data=rows),
            ),
            patch("src.export.site_device_exporter.DataProcessingUtils") as dpu,
            patch.object(SiteDeviceExporter, "_print_vc_summary"),
        ):
            dpu.flatten_nested_fields.return_value = rows
            dpu.escape_multiline.return_value = rows
            SiteDeviceExporter._export_vc_for_device("s1", "d1", "sw1")

        dpu.flatten_nested_fields.assert_called_once_with(rows)

    def test_exception_prints_error(self, fake_mh, caplog):
        """Fetch raises → error logged via logger, user notified."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with (
            patch(
                "src.export.site_device_exporter.mistapi.api.v1.sites.devices.getSiteDeviceVirtualChassis",
                side_effect=RuntimeError("boom"),
            ),
            caplog.at_level(logging.ERROR, logger=LOGGER_NAME),
        ):
            SiteDeviceExporter._export_vc_for_device("s1", "d1", "sw1")

        assert "Failed to export virtual chassis" in caplog.text


class TestPrintVcSummary:
    """Cover SiteDeviceExporter._print_vc_summary."""

    def test_empty_returns_early(self, fake_mh, caplog):
        """Empty sanitized → no log output."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            SiteDeviceExporter._print_vc_summary([], "sw1", "f.csv")
        assert caplog.text == ""

    def test_with_members_and_preprovisioned(self, fake_mh, caplog):
        """Both keys present → both logged."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            SiteDeviceExporter._print_vc_summary([{"members": ["m1"], "preprovisioned": True}], "sw1", "f.csv")
        out = caplog.text
        assert "VC members" in out
        assert "Preprovisioned" in out

    def test_without_optional_keys(self, fake_mh, caplog):
        """Neither key → still logs header/count/path."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with caplog.at_level(logging.INFO, logger=LOGGER_NAME):
            SiteDeviceExporter._print_vc_summary([{"id": "x"}], "sw1", "f.csv")
        out = caplog.text
        assert "Records exported: 1" in out
        assert "VC members" not in out
        assert "Preprovisioned" not in out


class TestPersistSiteDevices:
    """Cover SiteDeviceExporter._persist_site_devices."""

    def test_empty_prints_notice(self, fake_mh, caplog):
        """Empty rawdata → prints notice, no write."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with caplog.at_level(logging.WARNING, logger=LOGGER_NAME):
            SiteDeviceExporter._persist_site_devices([], "HQ")
        fake_mh.DataExporter.write_with_format_selection.assert_not_called()
        assert "No devices found" in caplog.text

    def test_non_empty_flattens_and_writes(self, fake_mh, caplog):
        """Non-empty → flatten/escape/write per-site filename."""
        from src.export.site_device_exporter import SiteDeviceExporter

        rows = [{"id": "d1"}]
        with (
            patch("src.export.site_device_exporter.DataProcessingUtils") as dpu,
            caplog.at_level(logging.INFO, logger=LOGGER_NAME),
        ):
            dpu.flatten_nested_fields.return_value = rows
            dpu.escape_multiline.return_value = rows
            SiteDeviceExporter._persist_site_devices(rows, "HQ Site")

        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(rows, "SiteDevices_HQ_Site.csv")
        assert "1 devices exported" in caplog.text


class TestDevices:
    """Cover SiteDeviceExporter.devices."""

    def test_resolver_none_aborts(self, fake_mh):
        """Resolver returns None → early return."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with patch.object(SiteDeviceExporter, "_resolve_site_for_stats", return_value=None):
            SiteDeviceExporter.devices()

    def test_happy_path_persists(self, fake_mh):
        """Fetch OK → persist called with data."""
        from src.export.site_device_exporter import SiteDeviceExporter

        rows = [{"id": "d1"}]
        with (
            patch.object(SiteDeviceExporter, "_resolve_site_for_stats", return_value=("s1", "HQ")),
            patch(
                "src.export.site_device_exporter.mistapi.api.v1.sites.devices.listSiteDevices",
                return_value=MagicMock(data=rows),
            ),
            patch.object(SiteDeviceExporter, "_persist_site_devices") as persist,
        ):
            SiteDeviceExporter.devices()

        persist.assert_called_once_with(rows, "HQ")

    def test_fetch_exception_logged(self, fake_mh, caplog):
        """Fetch raises → user notified."""
        from src.export.site_device_exporter import SiteDeviceExporter

        with (
            patch.object(SiteDeviceExporter, "_resolve_site_for_stats", return_value=("s1", "HQ")),
            patch(
                "src.export.site_device_exporter.mistapi.api.v1.sites.devices.listSiteDevices",
                side_effect=RuntimeError("boom"),
            ),
            caplog.at_level(logging.ERROR, logger=LOGGER_NAME),
        ):
            SiteDeviceExporter.devices()

        assert "Error fetching device data" in caplog.text
