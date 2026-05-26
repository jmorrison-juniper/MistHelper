"""Unit tests for extracted WAN probe device override manager logic."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.gateway.wan_probe_device_override_manager import WANProbeDeviceOverrideManager
from src.gateway.wan_probe_device_override_manager import configure_wan_probe_device_override_dependencies


def _configure_dependencies(*, site_exclude_prefix: str = "") -> None:
    """Configure minimal dependency graph for WAN probe override manager tests."""
    configure_wan_probe_device_override_dependencies(
        apisession_dependency=object(),
        config_utils=SimpleNamespace(
            get_cached_or_prompted_org_id=MagicMock(return_value="org-1"),
            check_stop_signal=MagicMock(return_value=False),
        ),
        cache_utils=SimpleNamespace(check_and_generate_csv=MagicMock()),
        org_site_exporter=SimpleNamespace(sites=MagicMock()),
        gateway_export_utils=SimpleNamespace(templates=MagicMock()),
        file_path_utils=SimpleNamespace(get_csv_path=MagicMock(return_value="test.csv")),
        input_utils=SimpleNamespace(safe_input=MagicMock(return_value="1")),
        data_exporter=SimpleNamespace(save_data_to_output=MagicMock()),
        mistapi_dependency=SimpleNamespace(),
        site_exclude_prefix=site_exclude_prefix,
    )


def test_select_template_accepts_valid_numeric_selection() -> None:
    """Template selection resolves chosen template index from prompt input."""
    _configure_dependencies()
    manager = WANProbeDeviceOverrideManager()
    manager.templates = [
        {"id": "tmpl-1", "name": "Template-A"},
        {"id": "tmpl-2", "name": "Template-B"},
    ]
    manager.sites = [{"gatewaytemplate_id": "tmpl-2", "name": "site-b"}]

    assert manager._select_template() is True
    assert manager.selected_template is not None
    assert manager.selected_template["id"] == "tmpl-1"


def test_find_template_sites_honors_exclusion_prefix() -> None:
    """Template site finder excludes sites with configured prefix from candidate set."""
    _configure_dependencies(site_exclude_prefix="LAB-")
    manager = WANProbeDeviceOverrideManager()
    manager.selected_template = {"id": "tmpl-1", "name": "Template-A", "site_count": 0}
    manager.sites = [
        {"id": "site-1", "name": "LAB-Test", "gatewaytemplate_id": "tmpl-1"},
        {"id": "site-2", "name": "Prod-West", "gatewaytemplate_id": "tmpl-1"},
    ]

    assert manager._find_template_sites() is True
    assert len(manager.template_sites) == 1
    assert manager.template_sites[0]["site_id"] == "site-2"


def test_confirm_operation_requires_apply_keyword() -> None:
    """Operation confirmation gate rejects non-APPLY values and accepts APPLY."""
    _configure_dependencies()
    manager = WANProbeDeviceOverrideManager()

    from src.gateway import wan_probe_device_override_manager as module

    module.InputUtils.safe_input = MagicMock(return_value="nope")
    assert manager._confirm_operation(3) is False

    module.InputUtils.safe_input = MagicMock(return_value="APPLY")
    assert manager._confirm_operation(3) is True


def test_generate_report_calls_exporter_with_expected_output_filename() -> None:
    """Report generation writes audit output through injected exporter dependency."""
    _configure_dependencies()
    manager = WANProbeDeviceOverrideManager()
    manager.selected_template = {"id": "tmpl-1", "name": "Template-A"}

    from src.gateway import wan_probe_device_override_manager as module

    exporter = MagicMock()
    module.DataExporter.save_data_to_output = exporter

    manager._generate_report(
        [
            {
                "device_name": "gw-1",
                "device_id": "dev-1",
                "site_name": "site-a",
                "site_id": "site-1",
                "template_name": "Template-A",
                "ports_updated": ["ge-0/0/0"],
                "status": "DRY-RUN",
                "error": "",
            }
        ],
        dry_run=True,
    )

    exporter.assert_called_once()
    _, output_filename = exporter.call_args.args
    assert output_filename == "GatewayDevice_WAN_Probe_Override_Audit.csv"
