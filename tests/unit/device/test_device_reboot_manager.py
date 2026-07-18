"""Tests for :mod:`src.device.device_reboot_manager`.

Why:
    ``DeviceRebootManager`` executes destructive gateway reboots and is
    guarded by user confirmation, cache checks, CSV I/O, and Mist API
    calls. This suite exercises every branch of the module (missing
    files, empty CSVs, mismatched templates, HTTP responses of various
    shapes, and cancellation paths) so regressions in the safety flow
    surface immediately.
"""

from __future__ import annotations

import csv
import sys
import types
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.device.device_reboot_manager import DeviceRebootManager

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_mh() -> Any:
    """Install a synthetic ``MistHelper`` module for the duration of a test.

    Why:
        ``DeviceRebootManager`` reaches into ``MistHelper`` lazily via
        ``importlib.import_module``; providing a stub module keeps every
        lazy attribute access under test control without touching the
        real package.

    Yields:
        The synthetic module with mocks attached to every attribute the
        SUT reads.
    """

    saved = sys.modules.get("MistHelper")
    module = types.ModuleType("MistHelper")
    module.FilePathUtils = MagicMock()
    module.InputUtils = MagicMock()
    module.CacheUtils = MagicMock()
    module.OrgSiteExporter = MagicMock()
    module.GatewayExportUtils = MagicMock()
    module.mistapi = MagicMock()
    module.apisession = MagicMock()
    sys.modules["MistHelper"] = module
    try:
        yield module
    finally:
        if saved is not None:
            sys.modules["MistHelper"] = saved
        else:
            del sys.modules["MistHelper"]


def _target(**overrides: Any) -> dict:
    """Build a default reboot-target row for grouping/display tests."""

    base = {
        "device_id": "dev-1",
        "device_name": "gw-1",
        "site_id": "site-1",
        "site_name": "Site One",
        "template_id": "tpl-1",
        "template_name": "TemplateOne",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# by_gateway_template_list orchestrator
# ---------------------------------------------------------------------------


class TestByGatewayTemplateList:
    """Exercise the top-level ``by_gateway_template_list`` orchestration."""

    def test_aborts_when_no_targets(self, fake_mh: Any) -> None:
        """Abort silently when the loader yields no targets."""

        with (
            patch.object(DeviceRebootManager, "_load_and_validate_reboot_targets", return_value=None),
            patch.object(DeviceRebootManager, "_confirm_reboot_operation") as confirm,
        ):
            DeviceRebootManager.by_gateway_template_list()
        confirm.assert_not_called()

    def test_aborts_when_user_declines(self, fake_mh: Any) -> None:
        """Skip execution when the user declines confirmation."""

        with (
            patch.object(
                DeviceRebootManager,
                "_load_and_validate_reboot_targets",
                return_value=[_target()],
            ),
            patch.object(DeviceRebootManager, "_confirm_reboot_operation", return_value=False),
            patch.object(DeviceRebootManager, "_execute_reboots") as execute,
        ):
            DeviceRebootManager.by_gateway_template_list()
        execute.assert_not_called()

    def test_runs_end_to_end_on_confirm(self, fake_mh: Any) -> None:
        """Execute reboots and export results when confirmed."""

        with (
            patch.object(
                DeviceRebootManager,
                "_load_and_validate_reboot_targets",
                return_value=[_target()],
            ),
            patch.object(DeviceRebootManager, "_confirm_reboot_operation", return_value=True),
            patch.object(
                DeviceRebootManager,
                "_execute_reboots",
                return_value=[{"Status": "SUCCESS"}],
            ) as execute,
            patch.object(DeviceRebootManager, "_export_reboot_results") as export,
        ):
            DeviceRebootManager.by_gateway_template_list()
        execute.assert_called_once()
        export.assert_called_once_with([{"Status": "SUCCESS"}])


# ---------------------------------------------------------------------------
# _load_and_validate_reboot_targets branches
# ---------------------------------------------------------------------------


class TestLoadAndValidateRebootTargets:
    """Cover every early-abort branch inside the validator."""

    def test_missing_file(self, fake_mh: Any, tmp_path: Any) -> None:
        """Return ``None`` when the reboot-list CSV is missing."""

        fake_mh.FilePathUtils.get_csv_path.return_value = str(tmp_path / "missing.csv")
        with patch.object(DeviceRebootManager, "_handle_missing_reboot_file") as handler:
            result = DeviceRebootManager._load_and_validate_reboot_targets()
        assert result is None
        handler.assert_called_once()

    def test_no_template_mappings(self, fake_mh: Any, tmp_path: Any) -> None:
        """Abort when the templates CSV yields an empty mapping."""

        path = tmp_path / "reboot.csv"
        path.write_text("row\n", encoding="utf-8")
        fake_mh.FilePathUtils.get_csv_path.return_value = str(path)
        with (
            patch.object(DeviceRebootManager, "_ensure_fresh_csv_cache"),
            patch.object(DeviceRebootManager, "_load_template_mappings", return_value=None),
        ):
            assert DeviceRebootManager._load_and_validate_reboot_targets() is None

    def test_no_reboot_names(self, fake_mh: Any, tmp_path: Any) -> None:
        """Abort when the reboot list has no template names."""

        path = tmp_path / "reboot.csv"
        path.write_text("row\n", encoding="utf-8")
        fake_mh.FilePathUtils.get_csv_path.return_value = str(path)
        with (
            patch.object(DeviceRebootManager, "_ensure_fresh_csv_cache"),
            patch.object(DeviceRebootManager, "_load_template_mappings", return_value={"a": "1"}),
            patch.object(DeviceRebootManager, "_load_reboot_template_names", return_value=None),
        ):
            assert DeviceRebootManager._load_and_validate_reboot_targets() is None

    def test_no_matching_ids(self, fake_mh: Any, tmp_path: Any) -> None:
        """Abort when no template names map to known IDs."""

        path = tmp_path / "reboot.csv"
        path.write_text("row\n", encoding="utf-8")
        fake_mh.FilePathUtils.get_csv_path.return_value = str(path)
        with (
            patch.object(DeviceRebootManager, "_ensure_fresh_csv_cache"),
            patch.object(DeviceRebootManager, "_load_template_mappings", return_value={"a": "1"}),
            patch.object(DeviceRebootManager, "_load_reboot_template_names", return_value={"b"}),
            patch.object(DeviceRebootManager, "_map_template_names_to_ids", return_value=None),
        ):
            assert DeviceRebootManager._load_and_validate_reboot_targets() is None

    def test_returns_targets(self, fake_mh: Any, tmp_path: Any) -> None:
        """Return targets when every prerequisite succeeds."""

        path = tmp_path / "reboot.csv"
        path.write_text("row\n", encoding="utf-8")
        fake_mh.FilePathUtils.get_csv_path.return_value = str(path)
        with (
            patch.object(DeviceRebootManager, "_ensure_fresh_csv_cache"),
            patch.object(DeviceRebootManager, "_load_template_mappings", return_value={"a": "1"}),
            patch.object(DeviceRebootManager, "_load_reboot_template_names", return_value={"a"}),
            patch.object(DeviceRebootManager, "_map_template_names_to_ids", return_value={"1"}),
            patch.object(
                DeviceRebootManager,
                "_find_reboot_target_devices",
                return_value=[_target()],
            ),
        ):
            result = DeviceRebootManager._load_and_validate_reboot_targets()
        assert result == [_target()]


# ---------------------------------------------------------------------------
# _handle_missing_reboot_file
# ---------------------------------------------------------------------------


class TestHandleMissingRebootFile:
    """Cover template-file creation prompt branches."""

    def test_user_declines_creation(self, fake_mh: Any, capsys: Any) -> None:
        """Skip template creation when the user answers 'n'."""

        fake_mh.InputUtils.safe_input.return_value = "n"
        DeviceRebootManager._handle_missing_reboot_file("/tmp/missing.csv")
        fake_mh.FilePathUtils.create_csv_template.assert_not_called()

    def test_user_accepts_creation(self, fake_mh: Any) -> None:
        """Delegate to ``create_csv_template`` when the user answers 'y'."""

        fake_mh.InputUtils.safe_input.return_value = "Y"
        fake_mh.FilePathUtils.create_csv_template.return_value = "/tmp/new.csv"
        DeviceRebootManager._handle_missing_reboot_file("/tmp/missing.csv")
        fake_mh.FilePathUtils.create_csv_template.assert_called_once_with("GatewayTemplateRebootList.CSV")

    def test_creation_failure_is_handled(self, fake_mh: Any, capsys: Any) -> None:
        """Report but swallow ``create_csv_template`` errors."""

        fake_mh.InputUtils.safe_input.return_value = "yes"
        fake_mh.FilePathUtils.create_csv_template.side_effect = OSError("boom")
        DeviceRebootManager._handle_missing_reboot_file("/tmp/missing.csv")
        assert "Failed to create file" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _ensure_fresh_csv_cache
# ---------------------------------------------------------------------------


class TestEnsureFreshCsvCache:
    """Ensure every CSV cache refresh is invoked."""

    def test_refreshes_all_four_caches(self, fake_mh: Any) -> None:
        """Call ``check_and_generate_csv`` for each dependent artifact."""

        DeviceRebootManager._ensure_fresh_csv_cache()
        names = [c.args[0] for c in fake_mh.CacheUtils.check_and_generate_csv.call_args_list]
        assert names == [
            "OrgDevices.csv",
            "SiteList.csv",
            "OrgGatewayTemplates.csv",
            "AllSiteGatewayConfigs.csv",
        ]

    def test_gateway_configs_lambda_uses_fast(self, fake_mh: Any) -> None:
        """The fourth registration passes a lambda that requests fast mode."""

        DeviceRebootManager._ensure_fresh_csv_cache()
        lambda_arg = fake_mh.CacheUtils.check_and_generate_csv.call_args_list[3].args[1]
        lambda_arg()
        fake_mh.GatewayExportUtils.device_configs.assert_called_once_with(fast=True)


# ---------------------------------------------------------------------------
# _load_template_mappings
# ---------------------------------------------------------------------------


class TestLoadTemplateMappings:
    """Cover success, exception, and empty branches."""

    def test_returns_map_from_csv(self, fake_mh: Any, tmp_path: Any) -> None:
        """Return the name->id map when the CSV has valid rows."""

        path = tmp_path / "templates.csv"
        path.write_text("name,id\nAlpha,111\nBeta,222\n", encoding="utf-8")
        fake_mh.FilePathUtils.get_csv_path.return_value = str(path)
        assert DeviceRebootManager._load_template_mappings() == {"Alpha": "111", "Beta": "222"}

    def test_empty_map_returns_none(self, fake_mh: Any, tmp_path: Any) -> None:
        """Return ``None`` when the CSV only contains headers."""

        path = tmp_path / "templates.csv"
        path.write_text("name,id\n", encoding="utf-8")
        fake_mh.FilePathUtils.get_csv_path.return_value = str(path)
        assert DeviceRebootManager._load_template_mappings() is None

    def test_exception_returns_none(self, fake_mh: Any) -> None:
        """Swallow read errors and return ``None``."""

        fake_mh.FilePathUtils.get_csv_path.side_effect = RuntimeError("nope")
        assert DeviceRebootManager._load_template_mappings() is None


class TestReadTemplateNameIdCsv:
    """Verify the low-level template CSV parser."""

    def test_skips_rows_missing_fields(self, tmp_path: Any) -> None:
        """Drop rows missing either name or id."""

        path = tmp_path / "templates.csv"
        path.write_text(
            "name,id\nGood,1\n,2\nBad,\n\n",
            encoding="utf-8",
        )
        assert DeviceRebootManager._read_template_name_id_csv(str(path)) == {"Good": "1"}


# ---------------------------------------------------------------------------
# _load_reboot_template_names
# ---------------------------------------------------------------------------


class TestLoadRebootTemplateNames:
    """Cover the reboot-list name loader."""

    def test_returns_names(self, fake_mh: Any, tmp_path: Any) -> None:
        """Return the parsed name set."""

        path = tmp_path / "reboot.csv"
        path.write_text("Alpha\nBeta\n\n", encoding="utf-8")
        fake_mh.FilePathUtils.get_csv_path.return_value = str(path)
        assert DeviceRebootManager._load_reboot_template_names() == {"Alpha", "Beta"}

    def test_empty_returns_none(self, fake_mh: Any, tmp_path: Any) -> None:
        """Return ``None`` when the file is empty."""

        path = tmp_path / "reboot.csv"
        path.write_text("\n\n", encoding="utf-8")
        fake_mh.FilePathUtils.get_csv_path.return_value = str(path)
        assert DeviceRebootManager._load_reboot_template_names() is None

    def test_exception_returns_none(self, fake_mh: Any) -> None:
        """Swallow read errors and return ``None``."""

        fake_mh.FilePathUtils.get_csv_path.side_effect = OSError("read fail")
        assert DeviceRebootManager._load_reboot_template_names() is None


class TestReadRebootNamesCsv:
    """Verify the low-level reboot names parser."""

    def test_reads_first_column(self, tmp_path: Any) -> None:
        """Read only the first CSV column."""

        path = tmp_path / "reboot.csv"
        path.write_text("Alpha,x\nBeta\n\n,skipme\n", encoding="utf-8")
        assert DeviceRebootManager._read_reboot_names_csv(str(path)) == {"Alpha", "Beta"}


# ---------------------------------------------------------------------------
# _map_template_names_to_ids
# ---------------------------------------------------------------------------


class TestMapTemplateNamesToIds:
    """Cover match, mismatch, and empty-result branches."""

    def test_maps_matches_and_logs_misses(self, capsys: Any) -> None:
        """Return matching IDs and warn about missing names."""

        mapping = {"Alpha": "1", "Beta": "2"}
        result = DeviceRebootManager._map_template_names_to_ids({"Alpha", "Ghost"}, mapping)
        assert result == {"1"}
        assert "Ghost" in capsys.readouterr().out

    def test_none_when_no_matches(self, capsys: Any) -> None:
        """Return ``None`` and list available templates when nothing matches."""

        mapping = {"Alpha": "1"}
        assert DeviceRebootManager._map_template_names_to_ids({"Ghost"}, mapping) is None
        out = capsys.readouterr().out
        assert "Available templates" in out
        assert "Alpha" in out


# ---------------------------------------------------------------------------
# _build_gateway_reboot_target
# ---------------------------------------------------------------------------


class TestBuildGatewayRebootTarget:
    """Verify tuple unpacking and dict shape."""

    def test_builds_full_row(self) -> None:
        """Return a dict populated from the CSV row and the resolved tuple."""

        row = {"id": "dev1", "name": "gw", "site_id": "s1"}
        resolved = ("tpl-1", "Alpha", "Site1")
        assert DeviceRebootManager._build_gateway_reboot_target(row, resolved) == {
            "device_id": "dev1",
            "device_name": "gw",
            "site_id": "s1",
            "site_name": "Site1",
            "template_id": "tpl-1",
            "template_name": "Alpha",
        }


# ---------------------------------------------------------------------------
# _scan_csv_for_gateway_targets
# ---------------------------------------------------------------------------


class TestScanCsvForGatewayTargets:
    """Cover match, skip, and exception branches of the scanner."""

    def test_collects_matching_gateways(self, fake_mh: Any, tmp_path: Any) -> None:
        """Return matching gateway rows, skipping non-gateway or unlisted sites."""

        path = tmp_path / "configs.csv"
        path.write_text(
            "id,name,site_id,type\n" "d1,gw,s1,gateway\n" "d2,ap,s1,ap\n" "d3,other-gw,s2,gateway\n",
            encoding="utf-8",
        )
        fake_mh.FilePathUtils.get_csv_path.return_value = str(path)
        site_map = {"s1": ("tpl-1", "Alpha", "Site1")}
        result = DeviceRebootManager._scan_csv_for_gateway_targets(site_map)
        assert result == [
            {
                "device_id": "d1",
                "device_name": "gw",
                "site_id": "s1",
                "site_name": "Site1",
                "template_id": "tpl-1",
                "template_name": "Alpha",
            }
        ]

    def test_returns_none_on_exception(self, fake_mh: Any) -> None:
        """Return ``None`` when the CSV cannot be opened."""

        fake_mh.FilePathUtils.get_csv_path.side_effect = OSError("bad path")
        assert DeviceRebootManager._scan_csv_for_gateway_targets({"s1": ("tpl", "Alpha", "Site1")}) is None

    def test_empty_result_returned(self, fake_mh: Any, tmp_path: Any) -> None:
        """Return an empty list when no rows match."""

        path = tmp_path / "configs.csv"
        path.write_text("id,name,site_id,type\n", encoding="utf-8")
        fake_mh.FilePathUtils.get_csv_path.return_value = str(path)
        assert DeviceRebootManager._scan_csv_for_gateway_targets({}) == []


# ---------------------------------------------------------------------------
# _find_reboot_target_devices
# ---------------------------------------------------------------------------


class TestFindRebootTargetDevices:
    """Cover the site-lookup + scanner glue."""

    def test_no_matching_sites(self) -> None:
        """Return ``None`` when no sites use the templates."""

        with patch.object(DeviceRebootManager, "_find_sites_using_templates", return_value={}):
            assert DeviceRebootManager._find_reboot_target_devices({"1"}, {"Alpha": "1"}) is None

    def test_scanner_returns_none(self) -> None:
        """Propagate a scanner failure by returning ``None``."""

        with (
            patch.object(
                DeviceRebootManager,
                "_find_sites_using_templates",
                return_value={"s1": ("1", "Alpha", "Site1")},
            ),
            patch.object(DeviceRebootManager, "_scan_csv_for_gateway_targets", return_value=None),
        ):
            assert DeviceRebootManager._find_reboot_target_devices({"1"}, {"Alpha": "1"}) is None

    def test_scanner_returns_empty(self) -> None:
        """Return ``None`` when the scanner finds no matching devices."""

        with (
            patch.object(
                DeviceRebootManager,
                "_find_sites_using_templates",
                return_value={"s1": ("1", "Alpha", "Site1")},
            ),
            patch.object(DeviceRebootManager, "_scan_csv_for_gateway_targets", return_value=[]),
        ):
            assert DeviceRebootManager._find_reboot_target_devices({"1"}, {"Alpha": "1"}) is None

    def test_scanner_returns_targets(self) -> None:
        """Return the discovered targets."""

        targets = [_target()]
        with (
            patch.object(
                DeviceRebootManager,
                "_find_sites_using_templates",
                return_value={"s1": ("1", "Alpha", "Site1")},
            ),
            patch.object(DeviceRebootManager, "_scan_csv_for_gateway_targets", return_value=targets),
        ):
            assert DeviceRebootManager._find_reboot_target_devices({"1"}, {"Alpha": "1"}) == targets


# ---------------------------------------------------------------------------
# _find_sites_using_templates
# ---------------------------------------------------------------------------


class TestFindSitesUsingTemplates:
    """Cover success and exception paths of the site lookup."""

    def test_returns_matching_sites(self, fake_mh: Any, tmp_path: Any) -> None:
        """Return a site_id -> (template_id, template_name, site_name) map."""

        path = tmp_path / "sites.csv"
        path.write_text(
            "id,name,gatewaytemplate_id\n" "s1,Site1,tpl-1\n" "s2,Site2,tpl-2\n" "s3,Site3,\n",
            encoding="utf-8",
        )
        fake_mh.FilePathUtils.get_csv_path.return_value = str(path)
        result = DeviceRebootManager._find_sites_using_templates({"tpl-1"}, {"tpl-1": "Alpha"})
        assert result == {"s1": ("tpl-1", "Alpha", "Site1")}

    def test_unknown_template_name(self, fake_mh: Any, tmp_path: Any) -> None:
        """Fall back to 'Unknown' when the id-to-name map is missing an entry."""

        path = tmp_path / "sites.csv"
        path.write_text(
            "id,name,gatewaytemplate_id\ns1,Site1,tpl-1\n",
            encoding="utf-8",
        )
        fake_mh.FilePathUtils.get_csv_path.return_value = str(path)
        result = DeviceRebootManager._find_sites_using_templates({"tpl-1"}, {})
        assert result == {"s1": ("tpl-1", "Unknown", "Site1")}

    def test_exception_returns_empty(self, fake_mh: Any) -> None:
        """Return an empty dict when the CSV cannot be opened."""

        fake_mh.FilePathUtils.get_csv_path.side_effect = OSError("cannot open")
        assert DeviceRebootManager._find_sites_using_templates({"tpl"}, {}) == {}


# ---------------------------------------------------------------------------
# grouping + display helpers
# ---------------------------------------------------------------------------


class TestGroupTargetsByTemplate:
    """Verify the target grouping helper."""

    def test_groups_by_template_name(self) -> None:
        """Group targets into lists keyed by template name."""

        t1 = _target(template_name="Alpha", device_id="d1")
        t2 = _target(template_name="Alpha", device_id="d2")
        t3 = _target(template_name="Beta", device_id="d3")
        grouped = DeviceRebootManager._group_targets_by_template([t1, t2, t3])
        assert grouped == {"Alpha": [t1, t2], "Beta": [t3]}


class TestPrintRebootTargetSummary:
    """Verify the summary printer."""

    def test_prints_summary_and_warnings(self, capsys: Any) -> None:
        """Print per-template devices plus totals."""

        targets = [_target()]
        grouped = {"Alpha": targets}
        DeviceRebootManager._print_reboot_target_summary(targets, grouped)
        out = capsys.readouterr().out
        assert "Template: Alpha" in out
        assert "Total devices to reboot: 1" in out
        assert "Templates involved: 1" in out
        assert "Sites affected: 1" in out


class TestDisplayRebootWarnings:
    """Verify the critical-warning banner."""

    def test_contains_liability_statement(self, capsys: Any) -> None:
        """Print the liability warning banner."""

        DeviceRebootManager._display_reboot_warnings()
        out = capsys.readouterr().out
        assert "NO LIABILITY" in out


# ---------------------------------------------------------------------------
# _prompt_reboot_confirmation
# ---------------------------------------------------------------------------


class TestPromptRebootConfirmation:
    """Cover accept, cancel, and interrupt branches."""

    def test_accepts_reboot(self, fake_mh: Any) -> None:
        """Return ``True`` when the user types REBOOT."""

        fake_mh.InputUtils.safe_input.return_value = "REBOOT"
        assert DeviceRebootManager._prompt_reboot_confirmation(3) is True

    def test_rejects_other_input(self, fake_mh: Any) -> None:
        """Return ``False`` on any other input."""

        fake_mh.InputUtils.safe_input.return_value = "no"
        assert DeviceRebootManager._prompt_reboot_confirmation(3) is False

    def test_keyboard_interrupt(self, fake_mh: Any) -> None:
        """Return ``False`` on ``KeyboardInterrupt``."""

        fake_mh.InputUtils.safe_input.side_effect = KeyboardInterrupt
        assert DeviceRebootManager._prompt_reboot_confirmation(1) is False

    def test_eof_error(self, fake_mh: Any) -> None:
        """Return ``False`` on ``EOFError``."""

        fake_mh.InputUtils.safe_input.side_effect = EOFError
        assert DeviceRebootManager._prompt_reboot_confirmation(1) is False


# ---------------------------------------------------------------------------
# _confirm_reboot_operation
# ---------------------------------------------------------------------------


class TestConfirmRebootOperation:
    """Verify the confirmation orchestrator."""

    def test_delegates_to_prompt(self, fake_mh: Any) -> None:
        """Return the value produced by ``_prompt_reboot_confirmation``."""

        with patch.object(DeviceRebootManager, "_prompt_reboot_confirmation", return_value=True) as prompt:
            result = DeviceRebootManager._confirm_reboot_operation([_target()])
        assert result is True
        prompt.assert_called_once_with(1)


# ---------------------------------------------------------------------------
# _reboot_one_device
# ---------------------------------------------------------------------------


class TestRebootOneDevice:
    """Cover success + failure branches of the per-device reboot."""

    def test_success_returns_status(self, fake_mh: Any) -> None:
        """Return the parsed status when the API call succeeds."""

        response = MagicMock()
        response.data = {"status": "OK"}
        fake_mh.mistapi.api.v1.sites.devices.restartSiteDevice.return_value = response
        status = DeviceRebootManager._reboot_one_device(_target())
        assert status == "OK"

    def test_failure_returns_error_string(self, fake_mh: Any) -> None:
        """Return an ``ERROR:`` string when the API call raises."""

        fake_mh.mistapi.api.v1.sites.devices.restartSiteDevice.side_effect = RuntimeError("boom")
        status = DeviceRebootManager._reboot_one_device(_target())
        assert status.startswith("ERROR: ")


# ---------------------------------------------------------------------------
# _build_reboot_result_row
# ---------------------------------------------------------------------------


class TestBuildRebootResultRow:
    """Verify the result-row dict shape."""

    def test_builds_full_row(self) -> None:
        """Return the seven-field result dict for CSV export."""

        row = DeviceRebootManager._build_reboot_result_row(_target(), "SUCCESS")
        assert row == {
            "Template ID": "tpl-1",
            "Template Name": "TemplateOne",
            "Device ID": "dev-1",
            "Device Name": "gw-1",
            "Site ID": "site-1",
            "Site Name": "Site One",
            "Status": "SUCCESS",
        }


# ---------------------------------------------------------------------------
# _execute_reboots
# ---------------------------------------------------------------------------


class TestExecuteReboots:
    """Verify the per-target reboot loop."""

    def test_collects_result_row_per_target(self, fake_mh: Any) -> None:
        """Reboot each device and append a result row."""

        targets = [_target(device_id="d1"), _target(device_id="d2")]
        with patch.object(DeviceRebootManager, "_reboot_one_device", side_effect=["OK", "ERROR: x"]):
            results = DeviceRebootManager._execute_reboots(targets)
        assert [r["Device ID"] for r in results] == ["d1", "d2"]
        assert [r["Status"] for r in results] == ["OK", "ERROR: x"]


# ---------------------------------------------------------------------------
# _parse_reboot_response
# ---------------------------------------------------------------------------


class TestParseRebootResponse:
    """Cover every response-shape branch."""

    def test_dict_with_status_field(self) -> None:
        """Return the ``status`` value when present."""

        response = MagicMock()
        response.data = {"status": "OK"}
        assert DeviceRebootManager._parse_reboot_response(response) == "OK"

    def test_dict_without_status_field(self) -> None:
        """Fall back to a formatted SUCCESS string when status is missing."""

        response = MagicMock()
        response.data = {"other": "value"}
        result = DeviceRebootManager._parse_reboot_response(response)
        assert result.startswith("SUCCESS - ")

    def test_non_dict_data_returns_success(self) -> None:
        """Handle non-dict ``data`` payloads."""

        response = MagicMock()
        response.data = "raw text"
        assert DeviceRebootManager._parse_reboot_response(response) == "SUCCESS - raw text"

    def test_status_code_fallback(self) -> None:
        """Fall back to ``status_code`` when ``data`` is falsy."""

        class Response:
            data = None
            status_code = 200

        assert DeviceRebootManager._parse_reboot_response(Response()) == "SUCCESS - HTTP 200"

    def test_str_fallback(self) -> None:
        """Fall back to ``str(response)`` when neither field is usable."""

        result = DeviceRebootManager._parse_reboot_response("just-a-string")
        assert result == "SUCCESS - just-a-string"


# ---------------------------------------------------------------------------
# _export_reboot_results
# ---------------------------------------------------------------------------


class TestExportRebootResults:
    """Cover successful export + exception path."""

    def test_writes_csv(self, fake_mh: Any, tmp_path: Any) -> None:
        """Write one row per result with the canonical fieldnames."""

        path = tmp_path / "results.csv"
        fake_mh.FilePathUtils.get_csv_path.return_value = str(path)
        results = [
            DeviceRebootManager._build_reboot_result_row(_target(), "OK"),
            DeviceRebootManager._build_reboot_result_row(_target(device_id="d2"), "ERROR: x"),
        ]
        DeviceRebootManager._export_reboot_results(results)
        with open(path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2
        assert rows[0]["Status"] == "OK"
        assert rows[1]["Device ID"] == "d2"

    def test_handles_write_error(self, fake_mh: Any, capsys: Any) -> None:
        """Log and print when the CSV write raises."""

        fake_mh.FilePathUtils.get_csv_path.side_effect = OSError("write fail")
        DeviceRebootManager._export_reboot_results([])
        assert "Failed to write results" in capsys.readouterr().out
