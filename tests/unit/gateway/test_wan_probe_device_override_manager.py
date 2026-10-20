"""Unit tests for extracted WAN probe device override manager logic."""

from __future__ import annotations

import logging  # WHY: caplog assertions compare INFO and WARNING levels.
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.mist.resources.gateway.wan_probe_device_override_manager import (
    WANProbeDeviceOverrideDependencies,
    WANProbeDeviceOverrideManager,
    configure_wan_probe_device_override_dependencies,
)


def _configure_dependencies(*, site_exclude_prefix: str = "") -> None:
    """Configure minimal dependency graph for WAN probe override manager tests."""
    configure_wan_probe_device_override_dependencies(
        WANProbeDeviceOverrideDependencies(
            apisession=object(),
            config_utils=SimpleNamespace(
                get_cached_or_prompted_org_id=MagicMock(return_value="org-1"),
                check_stop_signal=MagicMock(return_value=False),
            ),
            cache_utils=SimpleNamespace(check_and_generate_csv=MagicMock()),
            org_site_exporter=SimpleNamespace(sites=MagicMock()),
            gateway_export_utils=SimpleNamespace(templates=MagicMock()),
            file_path_utils=SimpleNamespace(get_csv_path=MagicMock(return_value="test.csv")),
            input_utils=SimpleNamespace(safe_input=MagicMock(return_value="1")),
            data_exporter=SimpleNamespace(write_with_format_selection=MagicMock()),
            mistapi=SimpleNamespace(),
            site_exclude_prefix=site_exclude_prefix,
        )
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
    assert isinstance(manager.selected_template, dict)  # WHY: selection must store the template row.
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

    from src.mist.resources.gateway import wan_probe_device_override_manager as module

    module.InputUtils.safe_input = MagicMock(return_value="nope")
    assert manager._confirm_operation(3) is False

    module.InputUtils.safe_input = MagicMock(return_value="APPLY")
    assert manager._confirm_operation(3) is True


def test_generate_report_calls_exporter_with_expected_output_filename(caplog) -> None:
    """Report generation writes audit output through injected exporter dependency."""
    _configure_dependencies()
    manager = WANProbeDeviceOverrideManager()
    manager.selected_template = {"id": "tmpl-1", "name": "Template-A"}

    from src.mist.resources.gateway import wan_probe_device_override_manager as module

    exporter = MagicMock()
    module.DataExporter.write_with_format_selection = exporter

    with caplog.at_level(logging.INFO):  # WHY: capture the completion summary and its level.
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
    completion_records = [
        record for record in caplog.records if "Menu #167 DESTRUCTIVE operation complete" in record.getMessage()
    ]  # WHY: isolate the repaired success summary.
    assert [record.levelno for record in completion_records] == [logging.INFO]  # WHY: success is not a warning.


class TestDeviceUpdateHttpStatus:
    """Check the real update pipeline without sending a device configuration."""

    @staticmethod
    def _prepare_update(response, monkeypatch) -> SimpleNamespace:
        """Prepare the manager and controlled SDK calls for one HTTP response."""
        from mistapi.__api_response import APIResponse

        from src.mist.resources.gateway import wan_probe_device_override_manager as module

        sdk = MagicMock()
        sdk.api.v1.sites.devices.getSiteDevice.return_value = SimpleNamespace(data={"port_config": {"ge-0/0/0": {}}})
        sdk.api.v1.sites.devices.updateSiteDevice.return_value = APIResponse(response, "https://mist.invalid/device")
        session = object()
        monkeypatch.setattr(module, "mistapi", sdk)
        monkeypatch.setattr(module, "apisession", session)
        manager = WANProbeDeviceOverrideManager()
        manager.selected_template = {"id": "tmpl-1", "name": "Template-A"}
        device = {
            "device_name": "gw-1",
            "device_id": "dev-1",
            "site_name": "site-a",
            "site_id": "site-1",
            "overridden_wan_ports": [{"port_name": "ge-0/0/0"}],
        }
        return SimpleNamespace(device=device, endpoints=sdk.api.v1.sites.devices, session=session, manager=manager)

    def test_http_503_records_failed_update(self, monkeypatch, caplog) -> None:
        """A server refusal must retain its status and must not report success."""
        from requests import Response

        response = Response()
        response.status_code = 503
        response._content = b'{"id": "dev-1"}'
        with caplog.at_level(logging.DEBUG):
            update = self._prepare_update(response, monkeypatch)
            result = WANProbeDeviceOverrideManager._update_single_device(update.manager, update.device, dry_run=False)

        assert result == {
            "device_name": "gw-1",
            "device_id": "dev-1",
            "site_name": "site-a",
            "site_id": "site-1",
            "template_name": "Template-A",
            "ports_updated": ["ge-0/0/0"],
            "status": "FAILED",
            "error": "API returned status 503",
        }
        update.endpoints.getSiteDevice.assert_called_once_with(update.session, "site-1", "dev-1")
        update.endpoints.updateSiteDevice.assert_called_once_with(
            update.session,
            "site-1",
            "dev-1",
            body={
                "port_config": {
                    "ge-0/0/0": {
                        "wan_probe_override": {
                            "ips": update.manager.probe_ips,
                            "probe_profile": update.manager.probe_profile,
                        }
                    }
                }
            },
        )
        records = [
            record
            for record in caplog.records
            if record.name == "src.mist.resources.gateway.wan_probe_device_override_manager"
        ]
        assert [(record.levelno, record.getMessage()) for record in records if record.levelno >= logging.ERROR] == [
            (logging.ERROR, "Failed to update device gw-1: 503")
        ]
        assert not any("Successfully updated" in record.getMessage() for record in records)

    def test_http_200_preserves_success(self, monkeypatch, caplog) -> None:
        """A successful response remains distinct from a refused device update."""
        from requests import Response

        response = Response()
        response.status_code = 200
        response._content = b'{"id": "dev-1"}'
        with caplog.at_level(logging.DEBUG):
            update = self._prepare_update(response, monkeypatch)
            result = WANProbeDeviceOverrideManager._update_single_device(update.manager, update.device, dry_run=False)

        assert result["status"] == "SUCCESS"
        assert result["error"] == ""
        assert result["ports_updated"] == ["ge-0/0/0"]
        records = [
            record
            for record in caplog.records
            if record.name == "src.mist.resources.gateway.wan_probe_device_override_manager"
        ]
        assert (logging.INFO, "Successfully updated device gw-1") in [
            (record.levelno, record.getMessage()) for record in records
        ]
        assert not any(record.levelno >= logging.ERROR for record in records)
