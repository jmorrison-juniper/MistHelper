"""Tests for GatewayWan2VariableMigrator (Issue #220).

Uses identity-checked teardown to avoid cross-test sys.modules contamination.
"""

from __future__ import annotations

import sys
import threading
from unittest.mock import MagicMock

# --- Module-level mistapi mock (identity-checked teardown) ---
_had_mistapi = "mistapi" in sys.modules
_saved_mistapi = sys.modules.get("mistapi")
_our_mock = MagicMock()
sys.modules["mistapi"] = _our_mock

from src.gateway._wan2_variable_device import _Wan2VariableDevice
from src.gateway._wan2_variable_io import _Wan2VariableIO
from src.gateway._wan2_variable_reporting import _Wan2VariableReporting
from src.gateway.wan2_variable import GatewayWan2VariableMigrator, Wan2VariableDeps


def setup_module() -> None:
    """Re-assert our mock in sys.modules before tests run.

    During pytest collection, other test files may overwrite sys.modules["mistapi"]
    after our module-level setup but before our tests execute.
    """
    sys.modules["mistapi"] = _our_mock


def teardown_module() -> None:
    """Restore sys.modules only if our mock is still installed."""
    if sys.modules.get("mistapi") is not _our_mock:
        return
    if _had_mistapi:
        sys.modules["mistapi"] = _saved_mistapi
    else:
        sys.modules.pop("mistapi", None)


# --- Helpers ---


def _make_migrator(**overrides: object) -> GatewayWan2VariableMigrator:
    """Create a migrator with default mocked dependencies."""
    defaults = {
        "org_id": "org-123",
        "apisession": MagicMock(),
        "site_exclude_prefix": "",
        "check_and_generate_csv_fn": MagicMock(),
        "generate_templates_fn": MagicMock(),
        "generate_sites_fn": MagicMock(),
        "get_csv_path_fn": MagicMock(return_value="/tmp/test.csv"),
        "save_data_fn": MagicMock(),
        "input_fn": MagicMock(return_value="cancel"),
        "connection_pool_fn": MagicMock(return_value=([], [])),
    }
    defaults.update(overrides)
    deps = Wan2VariableDeps(**defaults)  # type: ignore[arg-type]
    return GatewayWan2VariableMigrator(deps)


# --- Constructor tests ---


class TestConstructor:
    """Test dependency injection in constructor."""

    def test_stores_org_id(self) -> None:
        migrator = _make_migrator(org_id="test-org")
        assert migrator._org_id == "test-org"

    def test_stores_site_exclude_prefix(self) -> None:
        migrator = _make_migrator(site_exclude_prefix="LAB_")
        assert migrator._site_exclude_prefix == "LAB_"

    def test_default_input_fn_is_builtin_input(self) -> None:
        deps = Wan2VariableDeps(
            org_id="org",
            apisession=MagicMock(),
            site_exclude_prefix="",
            check_and_generate_csv_fn=MagicMock(),
            generate_templates_fn=MagicMock(),
            generate_sites_fn=MagicMock(),
            get_csv_path_fn=MagicMock(),
            save_data_fn=MagicMock(),
            input_fn=None,
            connection_pool_fn=None,
        )
        migrator = GatewayWan2VariableMigrator(deps)
        assert migrator._input_fn is input

    def test_runtime_state_initialized(self) -> None:
        migrator = _make_migrator()
        assert migrator._search_pattern == ""
        assert migrator._replacement_value == ""
        assert migrator._operation_mode == ""
        assert migrator._dry_run is False


# --- Filter and count tests ---


class TestFilterExcludedSites:
    """Test site exclusion filtering."""

    def test_no_prefix_returns_all(self) -> None:
        migrator = _make_migrator(site_exclude_prefix="")
        sites = [{"name": "Site-A"}, {"name": "LAB_Test"}]
        result = migrator._filter_excluded_sites(sites)
        assert len(result) == 2

    def test_filters_matching_prefix(self) -> None:
        migrator = _make_migrator(site_exclude_prefix="LAB_")
        sites = [
            {"name": "Site-A"},
            {"name": "LAB_Test"},
            {"name": "LAB_Dev"},
            {"name": "Production"},
        ]
        result = migrator._filter_excluded_sites(sites)
        assert len(result) == 2
        names = [s["name"] for s in result]
        assert "Site-A" in names
        assert "Production" in names

    def test_empty_list(self) -> None:
        migrator = _make_migrator(site_exclude_prefix="LAB_")
        result = migrator._filter_excluded_sites([])
        assert result == []


class TestCountTemplateAssignments:
    """Test template assignment counting."""

    def test_counts_templates(self) -> None:
        sites = [
            {"gatewaytemplate_id": "tmpl-1"},
            {"gatewaytemplate_id": "tmpl-1"},
            {"gatewaytemplate_id": "tmpl-2"},
        ]
        counts = _Wan2VariableIO._count_template_assignments(sites)
        assert counts == {"tmpl-1": 2, "tmpl-2": 1}

    def test_ignores_empty_template_ids(self) -> None:
        sites = [
            {"gatewaytemplate_id": "tmpl-1"},
            {"gatewaytemplate_id": ""},
            {"gatewaytemplate_id": "  "},
        ]
        counts = _Wan2VariableIO._count_template_assignments(sites)
        assert counts == {"tmpl-1": 1}

    def test_empty_sites(self) -> None:
        counts = _Wan2VariableIO._count_template_assignments([])
        assert counts == {}


# --- Port matching tests ---


class TestFindMatchingPorts:
    """Test port key pattern matching."""

    def test_exact_match(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"
        port_config = {"ge-0/0/1": {"usage": "wan"}, "ge-0/0/0": {"usage": "wan"}}
        result = migrator._find_matching_ports(port_config, "TestTemplate")
        assert result == [("ge-0/0/1", "{{wan2_interface}}")]

    def test_subinterface_match(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"
        port_config = {
            "ge-0/0/1": {"usage": "wan"},
            "ge-0/0/1.100": {"usage": "wan"},
        }
        result = migrator._find_matching_ports(port_config, "TestTemplate")
        assert ("ge-0/0/1", "{{wan2_interface}}") in result
        assert ("ge-0/0/1.100", "{{wan2_interface}}.100") in result

    def test_no_match(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"
        port_config = {"ge-0/0/0": {"usage": "wan"}}
        result = migrator._find_matching_ports(port_config, "TestTemplate")
        assert result == []

    def test_revert_direction(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "{{wan2_interface}}"
        migrator._replacement_value = "ge-0/0/1"
        port_config = {"{{wan2_interface}}": {"usage": "wan"}}
        result = migrator._find_matching_ports(port_config, "TestTemplate")
        assert result == [("{{wan2_interface}}", "ge-0/0/1")]


# --- Port key renaming tests ---


class TestRenamePortKeys:
    """Test in-place port_config key renaming."""

    def test_renames_exact_key(self) -> None:
        port_config = {"ge-0/0/1": {"ip": "1.2.3.4"}, "ge-0/0/0": {"ip": "5.6.7.8"}}
        result = _Wan2VariableDevice._rename_port_keys(port_config, "ge-0/0/1", "{{wan2_interface}}", "device1")
        assert "{{wan2_interface}}" in port_config
        assert "ge-0/0/1" not in port_config
        assert "ge-0/0/0" in port_config
        assert len(result) == 1
        assert "ge-0/0/1->{{wan2_interface}}" in result[0]

    def test_renames_subinterface(self) -> None:
        port_config = {
            "ge-0/0/1": {"ip": "1.2.3.4"},
            "ge-0/0/1.100": {"vlan": 100},
        }
        result = _Wan2VariableDevice._rename_port_keys(port_config, "ge-0/0/1", "{{wan2_interface}}", "device1")
        assert "{{wan2_interface}}" in port_config
        assert "{{wan2_interface}}.100" in port_config
        assert len(result) == 2

    def test_no_matching_keys(self) -> None:
        port_config = {"ge-0/0/0": {"ip": "1.2.3.4"}}
        result = _Wan2VariableDevice._rename_port_keys(port_config, "ge-0/0/1", "{{wan2_interface}}", "device1")
        assert result == []
        assert port_config == {"ge-0/0/0": {"ip": "1.2.3.4"}}


# --- Operation direction tests ---


class TestSelectOperationDirection:
    """Test operation direction selection."""

    def test_apply_direction(self) -> None:
        migrator = _make_migrator(input_fn=MagicMock(return_value="1"))
        result = migrator._select_operation_direction()
        assert result is not None
        mode, search, replace = result
        assert mode == "apply"
        assert search == "ge-0/0/1"
        assert replace == "{{wan2_interface}}"

    def test_revert_direction(self) -> None:
        migrator = _make_migrator(input_fn=MagicMock(return_value="2"))
        result = migrator._select_operation_direction()
        assert result is not None
        mode, search, replace = result
        assert mode == "revert"
        assert search == "{{wan2_interface}}"
        assert replace == "ge-0/0/1"

    def test_cancel(self) -> None:
        migrator = _make_migrator(input_fn=MagicMock(return_value="cancel"))
        result = migrator._select_operation_direction()
        assert result is None

    def test_invalid_input(self) -> None:
        migrator = _make_migrator(input_fn=MagicMock(return_value="xyz"))
        result = migrator._select_operation_direction()
        assert result is None


# --- Template selection tests ---


class TestPromptTemplateSelection:
    """Test template selection prompting."""

    def test_select_all(self) -> None:
        migrator = _make_migrator(input_fn=MagicMock(return_value="all"))
        templates = [
            {"id": "t1", "name": "Template1", "site_count": 3},
            {"id": "t2", "name": "Template2", "site_count": 5},
        ]
        result = migrator._prompt_template_selection(templates)
        assert result is not None
        assert len(result) == 2

    def test_select_specific(self) -> None:
        migrator = _make_migrator(input_fn=MagicMock(return_value="1,2"))
        templates = [
            {"id": "t1", "name": "Template1", "site_count": 3},
            {"id": "t2", "name": "Template2", "site_count": 5},
            {"id": "t3", "name": "Template3", "site_count": 1},
        ]
        result = migrator._prompt_template_selection(templates)
        assert result is not None
        assert len(result) == 2
        assert result[0]["id"] == "t1"
        assert result[1]["id"] == "t2"

    def test_cancel_selection(self) -> None:
        migrator = _make_migrator(input_fn=MagicMock(return_value="cancel"))
        templates = [{"id": "t1", "name": "Template1", "site_count": 3}]
        result = migrator._prompt_template_selection(templates)
        assert result is None

    def test_invalid_input(self) -> None:
        migrator = _make_migrator(input_fn=MagicMock(return_value="abc"))
        templates = [{"id": "t1", "name": "Template1", "site_count": 3}]
        result = migrator._prompt_template_selection(templates)
        assert result is None


# --- Preview and confirm tests ---


class TestPreviewAndConfirm:
    """Test preview and confirmation logic."""

    def test_dry_run_skips_confirmation(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = True
        migrator._operation_mode = "apply"
        templates = [{"name": "T1", "site_count": 3, "ports_to_replace": [("ge-0/0/1", "{{wan2_interface}}")]}]
        assert migrator._preview_and_confirm(templates) is True

    def test_live_mode_accepts_migrate(self) -> None:
        migrator = _make_migrator(input_fn=MagicMock(return_value="MIGRATE"))
        migrator._dry_run = False
        migrator._operation_mode = "apply"
        templates = [{"name": "T1", "site_count": 3, "ports_to_replace": [("ge-0/0/1", "{{wan2_interface}}")]}]
        assert migrator._preview_and_confirm(templates) is True

    def test_live_mode_rejects_wrong_confirmation(self) -> None:
        migrator = _make_migrator(input_fn=MagicMock(return_value="no"))
        migrator._dry_run = False
        migrator._operation_mode = "apply"
        templates = [{"name": "T1", "site_count": 3, "ports_to_replace": [("ge-0/0/1", "{{wan2_interface}}")]}]
        assert migrator._preview_and_confirm(templates) is False


# --- Device migration tests ---


class TestMigrateSingleDeviceOverride:
    """Test single device override migration."""

    def test_dry_run_returns_dry_run_status(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = True
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        mock_resp = MagicMock()
        mock_resp.data = {"port_config": {"ge-0/0/1": {"ip": "1.2.3.4"}}}
        _our_mock.api.v1.sites.devices.getSiteDevice.return_value = mock_resp

        device_info = {
            "site_id": "site-1",
            "device_id": "dev-1",
            "device_name": "GW-1",
            "template_id": "tmpl-1",
        }
        semaphore = threading.Semaphore(1)
        result = migrator._migrate_single_device_override(device_info, semaphore)
        assert result["status"] == "DRY-RUN"
        assert "ge-0/0/1" in result["ports_migrated"]

    def test_skips_device_without_matching_ports(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        mock_resp = MagicMock()
        mock_resp.data = {"port_config": {"ge-0/0/0": {"ip": "1.2.3.4"}}}
        _our_mock.api.v1.sites.devices.getSiteDevice.return_value = mock_resp

        device_info = {
            "site_id": "site-1",
            "device_id": "dev-1",
            "device_name": "GW-1",
            "template_id": "tmpl-1",
        }
        semaphore = threading.Semaphore(1)
        result = migrator._migrate_single_device_override(device_info, semaphore)
        assert result["status"] == "SKIPPED"

    def test_handles_api_error(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        _our_mock.api.v1.sites.devices.getSiteDevice.side_effect = RuntimeError("API down")

        device_info = {
            "site_id": "site-1",
            "device_id": "dev-1",
            "device_name": "GW-1",
            "template_id": "tmpl-1",
        }
        semaphore = threading.Semaphore(1)
        result = migrator._migrate_single_device_override(device_info, semaphore)
        assert result["status"] == "ERROR"
        assert "API down" in result["error"]

        # Reset side_effect for other tests
        _our_mock.api.v1.sites.devices.getSiteDevice.side_effect = None


# --- Apply single template tests ---


class TestApplySingleTemplate:
    """Test applying changes to a single template."""

    def test_dry_run_status(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = True
        tmpl = {
            "id": "t1",
            "name": "Template1",
            "site_count": 3,
            "config": {"port_config": {"ge-0/0/1": {"usage": "wan"}}},
            "ports_to_replace": [("ge-0/0/1", "{{wan2_interface}}")],
        }
        result = migrator._apply_single_template(tmpl, _our_mock)
        assert result["status"] == "DRY-RUN"
        assert "'ge-0/0/1' -> '{{wan2_interface}}'" in result["changes_made"]

    def test_live_success(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        _our_mock.api.v1.orgs.gatewaytemplates.updateOrgGatewayTemplate.return_value = mock_resp

        tmpl = {
            "id": "t1",
            "name": "Template1",
            "site_count": 3,
            "config": {"port_config": {"ge-0/0/1": {"usage": "wan"}}},
            "ports_to_replace": [("ge-0/0/1", "{{wan2_interface}}")],
        }
        result = migrator._apply_single_template(tmpl, _our_mock)
        assert result["status"] == "SUCCESS"

    def test_live_failure(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        _our_mock.api.v1.orgs.gatewaytemplates.updateOrgGatewayTemplate.return_value = mock_resp

        tmpl = {
            "id": "t1",
            "name": "Template1",
            "site_count": 3,
            "config": {"port_config": {"ge-0/0/1": {"usage": "wan"}}},
            "ports_to_replace": [("ge-0/0/1", "{{wan2_interface}}")],
        }
        result = migrator._apply_single_template(tmpl, _our_mock)
        assert result["status"] == "FAILED"
        assert "500" in result["error"]

    def test_skips_when_no_matching_ports(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        tmpl = {
            "id": "t1",
            "name": "Template1",
            "site_count": 3,
            "config": {"port_config": {}},
            "ports_to_replace": [("ge-0/0/1", "{{wan2_interface}}")],
        }
        result = migrator._apply_single_template(tmpl, _our_mock)
        assert result["status"] == "SKIPPED"


# --- Build affected site set tests ---


class TestBuildAffectedSiteSet:
    """Test building the set of affected site IDs."""

    def test_finds_affected_sites(self) -> None:
        migrator = _make_migrator()
        migrator._site_exclude_prefix = ""
        sites = [
            {"id": "s1", "name": "Site1", "gatewaytemplate_id": "t1"},
            {"id": "s2", "name": "Site2", "gatewaytemplate_id": "t2"},
            {"id": "s3", "name": "Site3", "gatewaytemplate_id": "t1"},
        ]
        affected, mapping = migrator._build_affected_site_set(sites, {"t1"})
        assert affected == {"s1", "s3"}
        assert mapping["s1"] == "t1"
        assert mapping["s2"] == "t2"

    def test_excludes_by_prefix(self) -> None:
        migrator = _make_migrator(site_exclude_prefix="LAB_")
        sites = [
            {"id": "s1", "name": "Site1", "gatewaytemplate_id": "t1"},
            {"id": "s2", "name": "LAB_Test", "gatewaytemplate_id": "t1"},
        ]
        affected, mapping = migrator._build_affected_site_set(sites, {"t1"})
        assert affected == {"s1"}
        assert "s2" not in mapping

    def test_empty_migrated_ids(self) -> None:
        migrator = _make_migrator()
        migrator._site_exclude_prefix = ""
        sites = [
            {"id": "s1", "name": "Site1", "gatewaytemplate_id": "t1"},
        ]
        affected, mapping = migrator._build_affected_site_set(sites, set())
        assert affected == set()
        assert mapping == {"s1": "t1"}


# --- Run device migrations tests ---


class TestRunDeviceMigrations:
    """Test device migration orchestration."""

    def test_empty_device_list(self) -> None:
        migrator = _make_migrator()
        result = migrator._run_device_migrations([], fast=False)
        assert result == []

    def test_sequential_mode(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = True
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        mock_resp = MagicMock()
        mock_resp.data = {"port_config": {"ge-0/0/1": {"ip": "1.2.3.4"}}}
        _our_mock.api.v1.sites.devices.getSiteDevice.return_value = mock_resp

        devices = [
            {
                "site_id": "s1",
                "device_id": "d1",
                "device_name": "GW-1",
                "template_id": "t1",
            },
        ]
        results = migrator._run_device_migrations(devices, fast=False)
        assert len(results) == 1
        assert results[0]["status"] == "DRY-RUN"


# --- Print header tests ---


class TestPrintHeader:
    """Test header output."""

    def test_dry_run_header(self, capsys: object) -> None:
        migrator = _make_migrator()
        migrator._dry_run = True
        migrator._print_header()

    def test_live_header(self, capsys: object) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        migrator._print_header()


# --- Execute workflow tests ---


class TestExecute:
    """Test the top-level execute() workflow."""

    def test_returns_early_when_no_csv_data(self) -> None:
        migrator = _make_migrator()
        migrator._load_csv_data = MagicMock(return_value=None)  # type: ignore[method-assign]
        migrator.execute(fast=False, dry_run=True)
        migrator._load_csv_data.assert_called_once()

    def test_returns_early_when_no_templates_selected(self) -> None:
        migrator = _make_migrator()
        migrator._load_csv_data = MagicMock(return_value=([], [], {}))  # type: ignore[method-assign]
        migrator._display_and_select_templates = MagicMock(return_value=None)  # type: ignore[method-assign]
        migrator.execute(fast=False, dry_run=False)

    def test_returns_early_when_direction_cancelled(self) -> None:
        migrator = _make_migrator()
        migrator._load_csv_data = MagicMock(return_value=([], [], {}))  # type: ignore[method-assign]
        migrator._display_and_select_templates = MagicMock(return_value=[{"id": "t1"}])  # type: ignore[method-assign]
        migrator._select_operation_direction = MagicMock(return_value=None)  # type: ignore[method-assign]
        migrator.execute(fast=False, dry_run=False)

    def test_returns_early_when_no_changes_found(self) -> None:
        migrator = _make_migrator()
        migrator._load_csv_data = MagicMock(return_value=([], [], {}))  # type: ignore[method-assign]
        migrator._display_and_select_templates = MagicMock(return_value=[{"id": "t1"}])  # type: ignore[method-assign]
        migrator._select_operation_direction = MagicMock(  # type: ignore[method-assign]
            return_value=("apply", "ge-0/0/1", "{{wan2_interface}}")
        )
        migrator._analyze_templates_parallel = MagicMock(return_value=[])  # type: ignore[method-assign]
        migrator.execute(fast=False, dry_run=False)

    def test_returns_early_when_confirm_rejected(self) -> None:
        migrator = _make_migrator()
        migrator._load_csv_data = MagicMock(return_value=([], [], {}))  # type: ignore[method-assign]
        migrator._display_and_select_templates = MagicMock(return_value=[{"id": "t1"}])  # type: ignore[method-assign]
        migrator._select_operation_direction = MagicMock(  # type: ignore[method-assign]
            return_value=("apply", "ge-0/0/1", "{{wan2_interface}}")
        )
        migrator._analyze_templates_parallel = MagicMock(return_value=[{"id": "t1"}])  # type: ignore[method-assign]
        migrator._preview_and_confirm = MagicMock(return_value=False)  # type: ignore[method-assign]
        migrator.execute(fast=False, dry_run=True)

    def test_full_workflow_completes(self) -> None:
        migrator = _make_migrator()
        migrator._load_csv_data = MagicMock(  # type: ignore[method-assign]
            return_value=([{"id": "t1"}], [{"id": "s1"}], {"t1": 1})
        )
        migrator._display_and_select_templates = MagicMock(return_value=[{"id": "t1"}])  # type: ignore[method-assign]
        migrator._select_operation_direction = MagicMock(  # type: ignore[method-assign]
            return_value=("apply", "ge-0/0/1", "{{wan2_interface}}")
        )
        changes = [{"id": "t1", "template_id": "t1", "status": "SUCCESS"}]
        migrator._analyze_templates_parallel = MagicMock(return_value=changes)  # type: ignore[method-assign]
        migrator._preview_and_confirm = MagicMock(return_value=True)  # type: ignore[method-assign]
        migrator._apply_template_changes = MagicMock(  # type: ignore[method-assign]
            return_value=[{"template_id": "t1", "status": "SUCCESS"}]
        )
        migrator._find_devices_needing_migration = MagicMock(return_value=[])  # type: ignore[method-assign]
        migrator._run_device_migrations = MagicMock(return_value=[])  # type: ignore[method-assign]
        migrator._generate_reports = MagicMock()  # type: ignore[method-assign]
        migrator.execute(fast=False, dry_run=False)
        migrator._generate_reports.assert_called_once()


# --- Load CSV data tests ---


class TestLoadCsvData:
    """Test CSV data loading."""

    def test_returns_none_when_no_templates(self, tmp_path: object) -> None:
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create empty templates CSV
            tmpl_path = os.path.join(tmpdir, "OrgGatewayTemplates.csv")
            sites_path = os.path.join(tmpdir, "SiteList.csv")
            with open(tmpl_path, "w", encoding="utf-8") as f:
                f.write("id,name\n")
            with open(sites_path, "w", encoding="utf-8") as f:
                f.write("id,name,gatewaytemplate_id\n")

            def get_path(name: str) -> str:
                return os.path.join(tmpdir, name)

            migrator = _make_migrator(get_csv_path_fn=get_path)
            result = migrator._load_csv_data()
            assert result is None

    def test_returns_data_when_templates_exist(self) -> None:
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpl_path = os.path.join(tmpdir, "OrgGatewayTemplates.csv")
            sites_path = os.path.join(tmpdir, "SiteList.csv")
            with open(tmpl_path, "w", encoding="utf-8") as f:
                f.write("id,name\ntmpl-1,Gateway1\n")
            with open(sites_path, "w", encoding="utf-8") as f:
                f.write("id,name,gatewaytemplate_id\ns1,Site1,tmpl-1\n")

            def get_path(name: str) -> str:
                return os.path.join(tmpdir, name)

            migrator = _make_migrator(
                get_csv_path_fn=get_path,
                site_exclude_prefix="",
            )
            result = migrator._load_csv_data()
            assert result is not None
            templates, sites, counts = result
            assert len(templates) == 1
            assert len(sites) == 1
            assert counts == {"tmpl-1": 1}


# --- Display and select templates tests ---


class TestDisplayAndSelectTemplates:
    """Test template display and selection."""

    def test_displays_sorted_templates(self) -> None:
        migrator = _make_migrator(input_fn=MagicMock(return_value="all"))
        template_rows = [
            {"id": "t2", "name": "Zebra Template"},
            {"id": "t1", "name": "Alpha Template"},
        ]
        site_counts = {"t1": 5, "t2": 3}
        result = migrator._display_and_select_templates(template_rows, site_counts)
        assert result is not None
        assert len(result) == 2
        assert result[0]["name"] == "Alpha Template"

    def test_returns_none_on_cancel(self) -> None:
        migrator = _make_migrator(input_fn=MagicMock(return_value="cancel"))
        result = migrator._display_and_select_templates(
            [{"id": "t1", "name": "T1"}],
            {"t1": 2},
        )
        assert result is None


# --- Fetch template config tests ---


class TestFetchTemplateConfig:
    """Test individual template fetching."""

    def test_successful_fetch_with_matching_ports(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        mock_resp = MagicMock()
        mock_resp.data = {"port_config": {"ge-0/0/1": {"usage": "wan"}}}
        _our_mock.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate.return_value = mock_resp

        result = migrator._fetch_template_config({"id": "t1", "name": "T1", "site_count": 3})
        assert result is not None
        assert result["id"] == "t1"
        assert len(result["ports_to_replace"]) == 1

    def test_returns_none_when_no_matching_ports(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        mock_resp = MagicMock()
        mock_resp.data = {"port_config": {"ge-0/0/0": {"usage": "wan"}}}
        _our_mock.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate.return_value = mock_resp

        result = migrator._fetch_template_config({"id": "t1", "name": "T1", "site_count": 3})
        assert result is None

    def test_returns_none_on_invalid_data(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        mock_resp = MagicMock()
        mock_resp.data = "not-a-dict"
        _our_mock.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate.return_value = mock_resp

        result = migrator._fetch_template_config({"id": "t1", "name": "T1", "site_count": 3})
        assert result is None

    def test_returns_none_on_no_port_config(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        mock_resp = MagicMock()
        mock_resp.data = {"port_config": "not-a-dict"}
        _our_mock.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate.return_value = mock_resp

        result = migrator._fetch_template_config({"id": "t1", "name": "T1", "site_count": 3})
        assert result is None

    def test_returns_none_on_api_error(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        _our_mock.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate.side_effect = RuntimeError("API error")

        result = migrator._fetch_template_config({"id": "t1", "name": "T1", "site_count": 3})
        assert result is None
        _our_mock.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate.side_effect = None


# --- Analyze templates parallel tests ---


class TestAnalyzeTemplatesParallel:
    """Test parallel template analysis."""

    def test_collects_results_from_threads(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        mock_resp = MagicMock()
        mock_resp.data = {"port_config": {"ge-0/0/1": {"usage": "wan"}}}
        _our_mock.api.v1.orgs.gatewaytemplates.getOrgGatewayTemplate.return_value = mock_resp

        templates = [
            {"id": "t1", "name": "T1", "site_count": 3},
            {"id": "t2", "name": "T2", "site_count": 5},
        ]
        results = migrator._analyze_templates_parallel(templates)
        assert len(results) == 2


# --- Apply template changes tests ---


class TestApplyTemplateChanges:
    """Test batch template change application."""

    def test_applies_all_templates(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = True
        templates = [
            {
                "id": "t1",
                "name": "T1",
                "site_count": 3,
                "config": {"port_config": {"ge-0/0/1": {"usage": "wan"}}},
                "ports_to_replace": [("ge-0/0/1", "{{wan2_interface}}")],
            },
        ]
        results = migrator._apply_template_changes(templates)
        assert len(results) == 1
        assert results[0]["status"] == "DRY-RUN"


# --- Apply single template error tests ---


class TestApplySingleTemplateError:
    """Test error handling in template application."""

    def test_exception_during_update(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        mock_mod = MagicMock()
        mock_mod.api.v1.orgs.gatewaytemplates.updateOrgGatewayTemplate.side_effect = RuntimeError("boom")
        tmpl = {
            "id": "t1",
            "name": "T1",
            "site_count": 3,
            "config": {"port_config": {"ge-0/0/1": {"usage": "wan"}}},
            "ports_to_replace": [("ge-0/0/1", "{{wan2_interface}}")],
        }
        result = migrator._apply_single_template(tmpl, mock_mod)
        assert result["status"] == "ERROR"
        assert "boom" in result["error"]


# --- Find devices needing migration tests ---


class TestFindDevicesNeedingMigration:
    """Test finding devices that need override migration."""

    def test_returns_empty_when_no_affected_sites(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"
        migrator._operation_mode = "apply"
        migrator._site_exclude_prefix = ""
        sites = [{"id": "s1", "name": "Site1", "gatewaytemplate_id": "t1"}]
        result = migrator._find_devices_needing_migration(sites, set())
        assert result == []

    def test_finds_devices_with_overrides(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"
        migrator._operation_mode = "apply"
        migrator._site_exclude_prefix = ""

        # Mock listSiteDevices
        list_resp = MagicMock()
        _our_mock.api.v1.sites.devices.listSiteDevices.return_value = list_resp
        _our_mock.get_all.return_value = [
            {"id": "d1", "name": "GW-1"},
        ]
        # Mock getSiteDevice
        get_resp = MagicMock()
        get_resp.data = {"port_config": {"ge-0/0/1": {"ip": "1.2.3.4"}}}
        _our_mock.api.v1.sites.devices.getSiteDevice.return_value = get_resp

        sites = [{"id": "s1", "name": "Site1", "gatewaytemplate_id": "t1"}]
        result = migrator._find_devices_needing_migration(sites, {"t1"})
        assert len(result) == 1
        assert result[0]["device_id"] == "d1"


# --- Scan site devices tests ---


class TestScanSiteDevices:
    """Test scanning site devices for port overrides."""

    def test_handles_api_error_gracefully(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        mock_mod = MagicMock()
        mock_mod.api.v1.sites.devices.listSiteDevices.side_effect = RuntimeError("fail")

        result = migrator._scan_site_devices({"s1"}, {"s1": "t1"}, mock_mod)
        assert result == []


# --- Check device override tests ---


class TestCheckDeviceOverride:
    """Test checking individual device for overrides."""

    def test_returns_match_when_override_present(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"

        mock_mod = MagicMock()
        resp = MagicMock()
        resp.data = {"port_config": {"ge-0/0/1": {"ip": "1.2.3.4"}}}
        mock_mod.api.v1.sites.devices.getSiteDevice.return_value = resp

        device = {"id": "d1", "name": "GW-1"}
        result = migrator._check_device_override(device, "s1", {"s1": "t1"}, mock_mod)
        assert result is not None
        assert result["device_id"] == "d1"

    def test_returns_none_when_no_override(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"

        mock_mod = MagicMock()
        resp = MagicMock()
        resp.data = {"port_config": {"ge-0/0/0": {"ip": "1.2.3.4"}}}
        mock_mod.api.v1.sites.devices.getSiteDevice.return_value = resp

        device = {"id": "d1", "name": "GW-1"}
        result = migrator._check_device_override(device, "s1", {"s1": "t1"}, mock_mod)
        assert result is None

    def test_returns_none_when_port_config_not_dict(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"

        mock_mod = MagicMock()
        resp = MagicMock()
        resp.data = {"port_config": "invalid"}
        mock_mod.api.v1.sites.devices.getSiteDevice.return_value = resp

        device = {"id": "d1", "name": "GW-1"}
        result = migrator._check_device_override(device, "s1", {"s1": "t1"}, mock_mod)
        assert result is None


# --- Device migration live success test ---


class TestMigrateSingleDeviceOverrideLive:
    """Test live device migration scenarios."""

    def test_live_success(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        get_resp = MagicMock()
        get_resp.data = {"port_config": {"ge-0/0/1": {"ip": "1.2.3.4"}}}
        _our_mock.api.v1.sites.devices.getSiteDevice.return_value = get_resp

        update_resp = MagicMock()
        update_resp.status_code = 200
        _our_mock.api.v1.sites.devices.updateSiteDevice.return_value = update_resp

        device_info = {
            "site_id": "s1",
            "device_id": "d1",
            "device_name": "GW-1",
            "template_id": "t1",
        }
        semaphore = threading.Semaphore(1)
        result = migrator._migrate_single_device_override(device_info, semaphore)
        assert result["status"] == "SUCCESS"

    def test_live_failure(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        get_resp = MagicMock()
        get_resp.data = {"port_config": {"ge-0/0/1": {"ip": "1.2.3.4"}}}
        _our_mock.api.v1.sites.devices.getSiteDevice.return_value = get_resp

        update_resp = MagicMock()
        update_resp.status_code = 500
        _our_mock.api.v1.sites.devices.updateSiteDevice.return_value = update_resp

        device_info = {
            "site_id": "s1",
            "device_id": "d1",
            "device_name": "GW-1",
            "template_id": "t1",
        }
        semaphore = threading.Semaphore(1)
        result = migrator._migrate_single_device_override(device_info, semaphore)
        assert result["status"] == "FAILED"

    def test_skips_invalid_config(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        get_resp = MagicMock()
        get_resp.data = "not-a-dict"
        _our_mock.api.v1.sites.devices.getSiteDevice.return_value = get_resp

        device_info = {
            "site_id": "s1",
            "device_id": "d1",
            "device_name": "GW-1",
            "template_id": "t1",
        }
        semaphore = threading.Semaphore(1)
        result = migrator._migrate_single_device_override(device_info, semaphore)
        assert result["status"] == "SKIPPED"

    def test_skips_no_port_config(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        get_resp = MagicMock()
        get_resp.data = {"port_config": "not-dict"}
        _our_mock.api.v1.sites.devices.getSiteDevice.return_value = get_resp

        device_info = {
            "site_id": "s1",
            "device_id": "d1",
            "device_name": "GW-1",
            "template_id": "t1",
        }
        semaphore = threading.Semaphore(1)
        result = migrator._migrate_single_device_override(device_info, semaphore)
        assert result["status"] == "SKIPPED"


# --- Fast mode migration tests ---


class TestMigrateDevicesFast:
    """Test fast mode device migration."""

    def test_calls_connection_pool(self) -> None:
        pool_fn = MagicMock(return_value=([{"status": "SUCCESS"}], []))
        migrator = _make_migrator(connection_pool_fn=pool_fn)
        devices = [
            {"site_id": "s1", "device_id": "d1", "device_name": "GW-1", "template_id": "t1"},
        ]
        result = migrator._migrate_devices_fast(devices)
        pool_fn.assert_called_once()
        assert len(result) == 1

    def test_logs_failed_items(self) -> None:
        pool_fn = MagicMock(return_value=([], [{"error": "fail"}]))
        migrator = _make_migrator(connection_pool_fn=pool_fn)
        devices = [
            {"site_id": "s1", "device_id": "d1", "device_name": "GW-1", "template_id": "t1"},
        ]
        result = migrator._migrate_devices_fast(devices)
        assert result == []


# --- Sequential migration tests ---


class TestMigrateDevicesSequential:
    """Test sequential device migration."""

    def test_fast_mode_small_batch(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = True
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        get_resp = MagicMock()
        get_resp.data = {"port_config": {"ge-0/0/1": {"ip": "1.2.3.4"}}}
        _our_mock.api.v1.sites.devices.getSiteDevice.return_value = get_resp

        devices = [
            {"site_id": "s1", "device_id": "d1", "device_name": "GW-1", "template_id": "t1"},
            {"site_id": "s1", "device_id": "d2", "device_name": "GW-2", "template_id": "t1"},
        ]
        results = migrator._migrate_devices_sequential(devices, fast=True)
        assert len(results) == 2

    def test_non_fast_mode(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = True
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"

        get_resp = MagicMock()
        get_resp.data = {"port_config": {"ge-0/0/1": {"ip": "1.2.3.4"}}}
        _our_mock.api.v1.sites.devices.getSiteDevice.return_value = get_resp

        devices = [
            {"site_id": "s1", "device_id": "d1", "device_name": "GW-1", "template_id": "t1"},
        ]
        results = migrator._migrate_devices_sequential(devices, fast=False)
        assert len(results) == 1


# --- Run device migrations extended tests ---


class TestRunDeviceMigrationsExtended:
    """Test device migration orchestration with fast mode."""

    def test_fast_mode_with_enough_devices(self) -> None:
        pool_fn = MagicMock(return_value=([{"status": "SUCCESS"}] * 6, []))
        migrator = _make_migrator(connection_pool_fn=pool_fn)
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"
        devices = [
            {"site_id": f"s{i}", "device_id": f"d{i}", "device_name": f"GW-{i}", "template_id": "t1"} for i in range(6)
        ]
        results = migrator._run_device_migrations(devices, fast=True)
        assert len(results) == 6
        pool_fn.assert_called_once()


# --- Reporting tests ---


class TestGenerateReports:
    """Test report generation."""

    def test_generates_all_sections(self) -> None:
        save_fn = MagicMock()
        migrator = _make_migrator(save_data_fn=save_fn)
        migrator._dry_run = True
        migrator._operation_mode = "apply"
        results = [{"status": "DRY-RUN", "template_id": "t1"}]
        device_results = [{"status": "DRY-RUN"}]
        devices = [{"device_id": "d1"}]
        migrator._generate_reports(results, device_results, devices)
        assert save_fn.call_count == 1


# --- Template summary tests ---


class TestPrintTemplateSummary:
    """Test template summary output."""

    def test_dry_run_summary(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = True
        results = [{"status": "DRY-RUN"}, {"status": "DRY-RUN"}, {"status": "SKIPPED"}]
        migrator._print_template_summary(results)

    def test_live_summary(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        results = [{"status": "SUCCESS"}, {"status": "FAILED"}]
        migrator._print_template_summary(results)


# --- Device summary tests ---


class TestPrintDeviceSummary:
    """Test device summary output."""

    def test_no_devices(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        migrator._print_device_summary([], [])

    def test_dry_run_with_devices(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = True
        device_results = [{"status": "DRY-RUN"}, {"status": "SKIPPED"}]
        migrator._print_device_summary(device_results, [{"id": "d1"}])

    def test_live_with_devices(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        device_results = [{"status": "SUCCESS"}, {"status": "FAILED"}]
        migrator._print_device_summary(device_results, [{"id": "d1"}])


# --- Report paths tests ---


class TestPrintReportPaths:
    """Test report path output."""

    def test_with_devices(self) -> None:
        _Wan2VariableReporting._print_report_paths("audit.csv", [{"id": "d1"}])

    def test_without_devices(self) -> None:
        _Wan2VariableReporting._print_report_paths("audit.csv", [])


# --- Final guidance tests ---


class TestPrintFinalGuidance:
    """Test final guidance output."""

    def test_dry_run_guidance(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = True
        migrator._operation_mode = "apply"
        results = [{"status": "DRY-RUN"}]
        device_results = [{"status": "DRY-RUN"}]
        devices = [{"id": "d1"}]
        migrator._print_final_guidance(results, device_results, devices)

    def test_live_guidance_with_success(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        migrator._operation_mode = "apply"
        results = [{"status": "SUCCESS"}, {"status": "FAILED"}]
        device_results = [{"status": "SUCCESS"}, {"status": "FAILED"}]
        devices = [{"id": "d1"}, {"id": "d2"}]
        migrator._print_final_guidance(results, device_results, devices)

    def test_live_guidance_no_devices(self) -> None:
        migrator = _make_migrator()
        migrator._dry_run = False
        migrator._operation_mode = "apply"
        results = [{"status": "SUCCESS"}]
        migrator._print_final_guidance(results, [], [])


# --- Dry run guidance tests ---


class TestPrintDryRunGuidance:
    """Test dry-run guidance output."""

    def test_with_devices(self) -> None:
        migrator = _make_migrator()
        results = [{"status": "DRY-RUN"}]
        device_results = [{"status": "DRY-RUN"}]
        devices = [{"id": "d1"}]
        migrator._print_dry_run_guidance(results, device_results, devices)

    def test_without_devices(self) -> None:
        migrator = _make_migrator()
        results = [{"status": "DRY-RUN"}]
        migrator._print_dry_run_guidance(results, [], [])

    def test_no_dry_run_results(self) -> None:
        migrator = _make_migrator()
        results = [{"status": "SKIPPED"}]
        migrator._print_dry_run_guidance(results, [], [])


# --- Live guidance tests ---


class TestPrintLiveGuidance:
    """Test live-mode guidance output."""

    def test_with_devices(self) -> None:
        device_results = [{"status": "SUCCESS"}]
        devices = [{"id": "d1"}]
        _Wan2VariableReporting._print_live_guidance(1, device_results, devices)

    def test_without_devices(self) -> None:
        _Wan2VariableReporting._print_live_guidance(1, [], [])

    def test_zero_success(self) -> None:
        _Wan2VariableReporting._print_live_guidance(0, [], [])


# --- Print device migration header tests ---


class TestPrintDeviceMigrationHeader:
    """Test device migration header output."""

    def test_apply_mode(self) -> None:
        migrator = _make_migrator()
        migrator._operation_mode = "apply"
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"
        migrator._print_device_migration_header()

    def test_revert_mode(self) -> None:
        migrator = _make_migrator()
        migrator._operation_mode = "revert"
        migrator._search_pattern = "{{wan2_interface}}"
        migrator._replacement_value = "ge-0/0/1"
        migrator._print_device_migration_header()


# --- Complex port pattern tests ---


class TestFindMatchingPortsComplex:
    """Test complex port pattern warning."""

    def test_warns_on_complex_pattern(self) -> None:
        migrator = _make_migrator()
        migrator._search_pattern = "ge-0/0/1"
        migrator._replacement_value = "{{wan2_interface}}"
        port_config = {"reth0-ge-0/0/1-backup": {"usage": "wan"}}
        result = migrator._find_matching_ports(port_config, "TestTemplate")
        assert result == []


# --- Prompt template selection edge cases ---


class TestPromptTemplateSelectionEdge:
    """Test edge cases in template selection."""

    def test_empty_selection_result(self) -> None:
        migrator = _make_migrator(input_fn=MagicMock(return_value="99"))
        templates = [{"id": "t1", "name": "T1", "site_count": 1}]
        result = migrator._prompt_template_selection(templates)
        assert result is None


# --- Device failure warning tests ---


class TestPrintDeviceFailureWarning:
    """Test device failure warning output."""

    def test_no_devices_needing_migration(self) -> None:
        migrator = _make_migrator()
        migrator._print_device_failure_warning([], [])

    def test_no_failures(self) -> None:
        migrator = _make_migrator()
        migrator._print_device_failure_warning([{"status": "SUCCESS"}], [{"id": "d1"}])

    def test_with_failures(self) -> None:
        migrator = _make_migrator()
        migrator._print_device_failure_warning([{"status": "FAILED"}], [{"id": "d1"}])


# --- Log operation summary tests ---


class TestLogOperationSummary:
    """Test operation summary logging."""

    def test_without_devices(self) -> None:
        migrator = _make_migrator()
        migrator._operation_mode = "apply"
        migrator._log_operation_summary(5, 1, [], [])

    def test_with_devices(self) -> None:
        migrator = _make_migrator()
        migrator._operation_mode = "apply"
        migrator._log_operation_summary(5, 1, [{"status": "SUCCESS"}], [{"id": "d1"}])
