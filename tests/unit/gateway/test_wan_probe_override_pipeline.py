"""Cover the full menu 167 pipeline of the WAN probe device override manager.

The manager writes probe configuration to gateway devices that carry a device
level port override. The existing tests cover the selection helpers. These
tests cover the remaining blocks. They cover the header, the initialization,
the data load, the site scan, the preview, the apply, and the report. Every
Mist API call is mocked, so no call reaches the network.
"""

from __future__ import annotations  # WHY: allow the PEP 604 union syntax in the annotations.

import csv  # WHY: the CSV fixture writes real files the reader must parse.
from types import SimpleNamespace  # WHY: the dependency doubles need named attributes.
from typing import Any  # WHY: the fixtures return loosely typed doubles.
from unittest.mock import MagicMock, patch  # WHY: MagicMock builds the doubles, patch swaps them.

import pytest  # WHY: the fixtures and the tmp_path helper come from pytest.

from src.gateway import wan_probe_device_override_manager as module  # WHY: patch the module globals.
from src.gateway.wan_probe_device_override_manager import (  # WHY: the module under test.
    WANProbeDeviceOverrideDependencies,
    WANProbeDeviceOverrideManager,
    configure_wan_probe_device_override_dependencies,
)


def _write_csv(path: Any, rows: list[dict[str, str]]) -> None:
    """Write a CSV file with a header row so the manager reader can parse it."""
    fieldnames = list(rows[0].keys()) if rows else ["id", "name"]  # WHY: an empty cache still needs a header.
    with open(path, "w", encoding="utf-8", newline="") as handle:  # WHY: the manager reads UTF-8.
        writer = csv.DictWriter(handle, fieldnames=fieldnames)  # WHY: one header row.
        writer.writeheader()  # WHY: DictReader needs the header names.
        writer.writerows(rows)  # WHY: one CSV row per template or site.


@pytest.fixture
def wired(tmp_path: Any) -> Any:
    """Wire the manager module to doubles and return the shared state bundle."""
    template_path = tmp_path / "OrgGatewayTemplates.csv"  # WHY: the manager reads this cache.
    site_path = tmp_path / "SiteList.csv"  # WHY: the manager reads this cache.
    _write_csv(
        template_path,
        [
            {"id": "tmpl-1", "name": "Alpha"},
            {"id": "tmpl-2", "name": "Beta"},
        ],
    )  # WHY: two rows give the menu a second entry to select.
    _write_csv(
        site_path,
        [
            {"id": "site-1", "name": "Alpha Site", "gatewaytemplate_id": "tmpl-1"},
            {"id": "site-2", "name": "Beta Site", "gatewaytemplate_id": "tmpl-2"},
        ],
    )  # WHY: each site binds to one template for the filter test.

    state = SimpleNamespace(
        site_path=site_path,  # WHY: a test may point the reader at the site CSV.
        org_id="org-1",  # WHY: the initialization gate echoes this value.
        stop_signal=False,  # WHY: the scan loop reads this flag per site.
        templates=MagicMock(),  # WHY: the cache generator receives this payload.
        sites=MagicMock(),  # WHY: the cache generator receives this payload.
        safe_input=MagicMock(side_effect=["1", "APPLY"]),  # WHY: template then confirm prompts.
        exporter=MagicMock(),  # WHY: the audit CSV write lands here.
        list_devices=MagicMock(),  # WHY: the site scan calls this endpoint.
        get_device=MagicMock(),  # WHY: the update pipeline calls this endpoint.
        update_device=MagicMock(),  # WHY: the live write calls this endpoint.
    )  # WHY: one bundle holds every double the tests assert on.

    config_utils = SimpleNamespace(
        get_cached_or_prompted_org_id=MagicMock(side_effect=lambda: state.org_id),  # WHY: org gate reads live state.
        check_stop_signal=MagicMock(side_effect=lambda: state.stop_signal),  # WHY: scan gate.
    )  # WHY: the manager reads both helpers by module global.
    cache_utils = SimpleNamespace(
        check_and_generate_csv=MagicMock(),  # WHY: the data load calls this twice.
    )  # WHY: the cache generator is a no-op double.
    org_site_exporter = SimpleNamespace(sites=state.sites)  # WHY: the site cache payload.
    gateway_export_utils = SimpleNamespace(templates=state.templates)  # WHY: the template payload.
    csv_paths = {  # WHY: the data load resolves each CSV name to a path.
        "OrgGatewayTemplates.csv": str(template_path),  # WHY: the template cache file.
        "SiteList.csv": str(site_path),  # WHY: the site cache file.
    }
    file_path_utils = SimpleNamespace(
        get_csv_path=MagicMock(side_effect=lambda name: csv_paths[name]),  # WHY: stable per name.
    )  # WHY: the data load resolves each CSV name to a path.
    input_utils = SimpleNamespace(safe_input=state.safe_input)  # WHY: the prompts read this.
    data_exporter = SimpleNamespace(write_with_format_selection=state.exporter)  # WHY: report sink.
    state.file_path_utils = file_path_utils  # WHY: a test may re-point the CSV path resolver.

    dependencies = WANProbeDeviceOverrideDependencies(
        apisession="session-1",  # WHY: the API calls receive this handle.
        config_utils=config_utils,  # WHY: org id and stop signal helpers.
        cache_utils=cache_utils,  # WHY: CSV cache generator.
        org_site_exporter=org_site_exporter,  # WHY: site cache payload holder.
        gateway_export_utils=gateway_export_utils,  # WHY: template cache payload holder.
        file_path_utils=file_path_utils,  # WHY: CSV path resolver.
        input_utils=input_utils,  # WHY: operator prompt helper.
        data_exporter=data_exporter,  # WHY: audit report writer.
        mistapi=MagicMock(),  # WHY: replaced below by the endpoint double.
        site_exclude_prefix="",  # WHY: no site exclusion in these tests.
    )  # WHY: the bundle wires every module slot.
    configure_wan_probe_device_override_dependencies(dependencies)  # WHY: install the doubles.

    def _device_response(devices: list[dict[str, Any]]) -> Any:
        """Build a listSiteDevices response double with a data attribute."""
        response = MagicMock()  # WHY: the reader only reads the data attribute.
        response.data = devices  # WHY: the scan loop iterates this list.
        return response  # WHY: the test assigns it to the endpoint double.

    state.list_devices = MagicMock(return_value=_device_response([]))  # WHY: default empty scan.
    state.get_device = MagicMock(return_value=_device_response({}))  # WHY: default empty config.
    update_response = MagicMock()  # WHY: the commit branch reads the status code.
    update_response.status_code = 200  # WHY: the success branch keys off 200.
    state.update_device = MagicMock(return_value=update_response)  # WHY: live write double.

    fake_api = MagicMock()  # WHY: one double covers the nested endpoint paths.
    fake_api.api.v1.sites.devices.listSiteDevices = state.list_devices  # WHY: scan endpoint.
    fake_api.api.v1.sites.devices.getSiteDevice = state.get_device  # WHY: fetch endpoint.
    fake_api.api.v1.sites.devices.updateSiteDevice = state.update_device  # WHY: write endpoint.
    with patch.object(module, "mistapi", fake_api):  # WHY: no call reaches the network.
        yield state  # WHY: the test body runs with the doubles in place.


def _gateway_with_override(port_name: str = "ge-0/0/0") -> dict[str, Any]:
    """Build a gateway record that carries one device level WAN port override."""
    return {
        "id": "gw-1",  # WHY: the update call needs the device UUID.
        "name": "Gateway-1",  # WHY: the report echoes the device name.
        "port_config": {
            port_name: {
                "usage": "wan",  # WHY: the extractor keeps WAN ports only.
                "wan_probe_override": {"ips": ["10.0.0.1"], "probe_profile": "lte"},  # WHY: prior state.
            }
        },
    }  # WHY: one port is enough for the pipeline under test.


def _override_entry(port_name: str = "ge-0/0/0") -> dict[str, Any]:
    """Build the manager entry shape for one device with one overridden port."""
    return {
        "device_id": "gw-1",  # WHY: the update call needs the device UUID.
        "device_name": "Gateway-1",  # WHY: the report echoes the device name.
        "site_id": "site-1",  # WHY: the API calls scope by site.
        "site_name": "Alpha Site",  # WHY: the report echoes the site name.
        "overridden_wan_ports": [
            {
                "port_name": port_name,  # WHY: the patch targets this port.
                "current_ips": ["10.0.0.1"],  # WHY: the preview shows the prior value.
                "current_profile": "lte",  # WHY: the preview shows the prior value.
                "port_settings": {"usage": "wan"},  # WHY: the extractor keeps the settings.
            }
        ],
    }  # WHY: the pipeline reads this shape at every step.


def _prepare_manager(wired: Any) -> WANProbeDeviceOverrideManager:
    """Run the manager through the prepare gate and return the ready instance."""
    manager = WANProbeDeviceOverrideManager()  # WHY: a fresh instance per test.
    assert manager._prepare_run() is True  # WHY: the prepare gate must succeed.
    return manager  # WHY: the test then drives the finalise phase.


def test_configure_runs_the_full_dry_run_pipeline(wired: Any) -> None:
    """A dry run scans, previews, applies without a write, and reports."""
    wired.list_devices.return_value.data = [_gateway_with_override()]  # WHY: one target device.
    wired.get_device.return_value.data = _gateway_with_override()  # WHY: the patch finds the port.
    wired.safe_input.side_effect = ["1"]  # WHY: dry run skips the confirm prompt.

    WANProbeDeviceOverrideManager.configure(dry_run=True)  # WHY: the classmethod entry point.

    wired.list_devices.assert_called_once()  # WHY: the scan ran once.
    wired.update_device.assert_not_called()  # WHY: a dry run must not write.
    wired.exporter.assert_called_once()  # WHY: the audit CSV still writes.
    report_data = wired.exporter.call_args.args[0]  # WHY: the first argument holds the rows.
    assert report_data[0]["status"] == "DRY-RUN"  # WHY: the dry run marks the row.
    assert report_data[0]["ports_updated"] == "ge-0/0/0"  # WHY: the row names the port.


def test_live_run_writes_the_probe_config_and_reports_success(wired: Any) -> None:
    """A confirmed live run patches the port and records a SUCCESS row."""
    wired.list_devices.return_value.data = [_gateway_with_override()]  # WHY: one target device.
    wired.get_device.return_value.data = _gateway_with_override()  # WHY: the patch finds the port.

    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    devices = manager._find_devices_with_overrides()  # WHY: the scan finds the override.
    manager._finalise_run(devices, dry_run=False)  # WHY: the confirm gate sees APPLY.

    wired.update_device.assert_called_once()  # WHY: the live write ran once.
    body = wired.update_device.call_args.kwargs["body"]  # WHY: the write carries the config.
    probe = body["port_config"]["ge-0/0/0"]["wan_probe_override"]  # WHY: the patched port.
    assert probe["ips"] == WANProbeDeviceOverrideManager.DEFAULT_PROBE_IPS  # WHY: new IPs.
    assert probe["probe_profile"] == WANProbeDeviceOverrideManager.DEFAULT_PROBE_PROFILE  # WHY: new profile.
    report_data = wired.exporter.call_args.args[0]  # WHY: the report rows.
    assert report_data[0]["status"] == "SUCCESS"  # WHY: the 200 status maps to success.


def test_live_run_records_a_failed_row_when_the_api_rejects_the_write(wired: Any) -> None:
    """A non-200 write response must record FAILED with the status code."""
    wired.list_devices.return_value.data = [_gateway_with_override()]  # WHY: one target device.
    wired.get_device.return_value.data = _gateway_with_override()  # WHY: the patch finds the port.
    wired.update_device.return_value.status_code = 403  # WHY: the failure branch keys off non-200.

    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    devices = manager._find_devices_with_overrides()  # WHY: the scan finds the override.
    manager._finalise_run(devices, dry_run=False)  # WHY: the confirm gate sees APPLY.

    report_data = wired.exporter.call_args.args[0]  # WHY: the report rows.
    assert report_data[0]["status"] == "FAILED"  # WHY: the non-200 status maps to failed.
    assert "403" in report_data[0]["error"]  # WHY: the row carries the status code.


def test_cancel_at_confirmation_stops_the_apply_phase(wired: Any) -> None:
    """A cancel at the confirm gate must skip the write and the report."""
    wired.list_devices.return_value.data = [_gateway_with_override()]  # WHY: one target device.
    wired.safe_input.side_effect = ["1", "no"]  # WHY: the confirm gate sees a cancel.

    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    devices = manager._find_devices_with_overrides()  # WHY: the scan finds the override.
    manager._finalise_run(devices, dry_run=False)  # WHY: the cancel gate stops the run.

    wired.update_device.assert_not_called()  # WHY: a cancel must not write.
    wired.exporter.assert_not_called()  # WHY: a cancel must not report.


def test_site_match_rejects_excluded_site() -> None:
    """Excluded sites never match a template, even with a matching id."""
    module.MIST_SITE_EXCLUDE_PREFIX = "EXCLUDED"  # WHY: activate the prefix filter.
    try:
        excluded = {"name": "EXCLUDED-1", "gatewaytemplate_id": "t-1"}
        assert WANProbeDeviceOverrideManager._site_matches_template(excluded, "t-1") is False
        plain = {"name": "Site-1", "gatewaytemplate_id": "t-1"}
        assert WANProbeDeviceOverrideManager._site_matches_template(plain, "t-1") is True
    finally:
        module.MIST_SITE_EXCLUDE_PREFIX = ""  # WHY: restore the default filter.


def test_scan_records_an_error_row_when_the_fetch_raises(wired: Any) -> None:
    """A fetch failure must record an ERROR row and not stop the run."""
    wired.list_devices.return_value.data = [_gateway_with_override()]  # WHY: one target device.
    wired.get_device.side_effect = RuntimeError("api down")  # WHY: the fetch branch fails.

    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    devices = manager._find_devices_with_overrides()  # WHY: the scan finds the override.
    manager._finalise_run(devices, dry_run=False)  # WHY: the run records the failure.

    report_data = wired.exporter.call_args.args[0]  # WHY: the report rows.
    assert report_data[0]["status"] == "ERROR"  # WHY: the exception maps to error.
    assert "api down" in report_data[0]["error"]  # WHY: the row carries the message.


def test_scan_records_a_skipped_row_when_the_config_lacks_the_port(wired: Any) -> None:
    """A config without the target port must record SKIPPED and not write."""
    wired.list_devices.return_value.data = [_gateway_with_override()]  # WHY: one target device.
    wired.get_device.return_value.data = {"port_config": {"ge-0/0/9": {"usage": "lan"}}}  # WHY: no match.

    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    devices = manager._find_devices_with_overrides()  # WHY: the scan finds the override.
    manager._finalise_run(devices, dry_run=False)  # WHY: the run records the skip.

    wired.update_device.assert_not_called()  # WHY: a skip must not write.
    report_data = wired.exporter.call_args.args[0]  # WHY: the report rows.
    assert report_data[0]["status"] == "SKIPPED"  # WHY: the missing port maps to skipped.


def test_scan_records_a_skipped_row_when_the_config_is_not_a_dict(wired: Any) -> None:
    """A non-dict config body must record SKIPPED with the structure reason."""
    wired.list_devices.return_value.data = [_gateway_with_override()]  # WHY: one target device.
    wired.get_device.return_value.data = ["not-a-dict"]  # WHY: the guard branch fires.

    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    devices = manager._find_devices_with_overrides()  # WHY: the scan finds the override.
    manager._finalise_run(devices, dry_run=False)  # WHY: the run records the skip.

    report_data = wired.exporter.call_args.args[0]  # WHY: the report rows.
    assert report_data[0]["status"] == "SKIPPED"  # WHY: the bad body maps to skipped.
    assert "Invalid" in report_data[0]["error"]  # WHY: the row names the structure fault.


def test_scan_records_a_skipped_row_when_the_config_lacks_port_config(wired: Any) -> None:
    """A config without a port_config block must record SKIPPED with the reason."""
    wired.list_devices.return_value.data = [_gateway_with_override()]  # WHY: one target device.
    # WHY: an empty port_config block yields no matching ports, so the row is SKIPPED.
    wired.get_device.return_value.data = {"name": "Gateway-1", "port_config": {}}

    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    devices = manager._find_devices_with_overrides()  # WHY: the scan finds the override.
    manager._finalise_run(devices, dry_run=False)  # WHY: the run records the skip.

    report_data = wired.exporter.call_args.args[0]  # WHY: the report rows.
    assert report_data[0]["status"] == "SKIPPED"  # WHY: no matching ports maps to skipped.
    assert "matching ports" in report_data[0]["error"]  # WHY: the row names the empty block.


def test_stop_signal_halts_the_site_scan(wired: Any) -> None:
    """A stop signal must break the site scan before the next site."""
    wired.stop_signal = True  # WHY: the scan loop reads this flag per site.
    wired.list_devices.return_value.data = [_gateway_with_override()]  # WHY: the scan would find it.

    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    devices = manager._find_devices_with_overrides()  # WHY: the scan must stop early.

    assert devices == []  # WHY: a stopped scan finds no devices.
    wired.list_devices.assert_not_called()  # WHY: the flag breaks before the first fetch.


def test_scan_skips_sites_that_raise_and_malformed_entries(wired: Any) -> None:
    """A site fetch error and a non-dict entry must both be skipped safely."""
    wired.list_devices.side_effect = [  # WHY: the first site raises, the second returns data.
        RuntimeError("site down"),  # WHY: the per-site guard must catch this.
        SimpleNamespace(data=[_gateway_with_override(), "junk"]),  # WHY: one good, one bad entry.
    ]  # WHY: two sites are bound to the selected template.

    manager = WANProbeDeviceOverrideManager()  # WHY: a fresh instance per test.
    manager.org_id = "org-1"  # WHY: the prepare gate reads this value.
    manager.templates = [{"id": "tmpl-1", "name": "Alpha"}]  # WHY: the selection gate reads this.
    manager.sites = [
        {"id": "site-1", "name": "Alpha Site", "gatewaytemplate_id": "tmpl-1"},
        {"id": "site-2", "name": "Alpha Two", "gatewaytemplate_id": "tmpl-1"},
    ]  # WHY: both sites bind to the selected template.
    manager.selected_template = {"id": "tmpl-1", "name": "Alpha"}  # WHY: the scan reads this.
    manager.template_sites = [
        {"site_id": "site-1", "site_name": "Alpha Site"},
        {"site_id": "site-2", "site_name": "Alpha Two"},
    ]  # WHY: the scan walks these two sites.

    devices = manager._find_devices_with_overrides()  # WHY: the scan must survive both faults.

    assert len(devices) == 1  # WHY: only the good entry survives.
    assert devices[0]["device_id"] == "gw-1"  # WHY: the good entry is the gateway.


def test_preview_prints_the_sample_and_the_overflow_hint(wired: Any) -> None:
    """The preview must cap the sample and hint at the remaining devices."""
    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    manager.selected_template = {"id": "tmpl-1", "name": "Alpha"}  # WHY: the preview reads this.
    devices = [_override_entry(f"ge-0/0/{index}") for index in range(7)]  # WHY: seven devices.

    manager._show_preview(devices, dry_run=False)  # WHY: the preview caps at five.

    assert devices[0]["device_name"] == "Gateway-1"  # WHY: the entry shape is intact.


def test_preview_prints_the_empty_probe_state(wired: Any) -> None:
    """The preview must render a placeholder when the port has no prior probe."""
    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    manager.selected_template = {"id": "tmpl-1", "name": "Alpha"}  # WHY: the preview reads this.
    entry = _override_entry()  # WHY: one device with one port.
    entry["overridden_wan_ports"][0]["current_ips"] = []  # WHY: the empty list branch.
    entry["overridden_wan_ports"][0]["current_profile"] = ""  # WHY: the empty string branch.

    manager._print_preview_device(entry)  # WHY: the renderer must handle the empty state.

    assert entry["overridden_wan_ports"][0]["current_ips"] == []  # WHY: the state is intact.


def test_apply_replaces_a_non_dict_port_settings_entry(wired: Any) -> None:
    """A non-dict port entry must be replaced before the probe patch lands."""
    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    port_config = {"ge-0/0/0": "scalar"}  # WHY: the guard branch replaces this.
    entry = _override_entry()  # WHY: one device with one port.

    modified = manager._apply_probe_to_ports(port_config, entry["overridden_wan_ports"], "Gateway-1")

    assert modified == ["ge-0/0/0"]  # WHY: the port counts as modified.
    assert port_config["ge-0/0/0"]["wan_probe_override"]["ips"] == manager.probe_ips  # WHY: patch landed.


def test_apply_skips_a_port_that_is_absent_from_the_config(wired: Any) -> None:
    """A port that vanished from the config must be skipped without a patch."""
    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    port_config = {"ge-0/0/9": {"usage": "lan"}}  # WHY: the target port is absent.
    entry = _override_entry()  # WHY: one device with one port.

    modified = manager._apply_probe_to_ports(port_config, entry["overridden_wan_ports"], "Gateway-1")

    assert modified == []  # WHY: no port was modified.
    assert "wan_probe_override" not in port_config["ge-0/0/9"]  # WHY: no patch landed.


def test_extract_keeps_only_wan_ports_with_a_dict_settings_block(wired: Any) -> None:
    """The extractor must drop LAN ports and non-dict settings blocks."""
    port_config = {
        "ge-0/0/0": {"usage": "wan", "wan_probe_override": {"ips": ["1.1.1.1"]}},
        "ge-0/0/1": {"usage": "lan"},  # WHY: the usage filter drops this port.
        "ge-0/0/2": "scalar",  # WHY: the type guard drops this port.
    }  # WHY: three ports with three different shapes.

    ports = WANProbeDeviceOverrideManager._extract_overridden_wan_ports(port_config)

    assert len(ports) == 1  # WHY: only the WAN port survives.
    assert ports[0]["port_name"] == "ge-0/0/0"  # WHY: the survivor is the WAN port.
    assert ports[0]["current_ips"] == ["1.1.1.1"]  # WHY: the prior probe state is kept.


def test_extract_replaces_a_malformed_probe_block(wired: Any) -> None:
    """A non-dict probe block must be treated as an empty probe state."""
    port_config = {"ge-0/0/0": {"usage": "wan", "wan_probe_override": "junk"}}  # WHY: guard branch.

    ports = WANProbeDeviceOverrideManager._extract_overridden_wan_ports(port_config)

    assert ports[0]["current_ips"] == []  # WHY: the malformed block reads as empty.
    assert ports[0]["current_profile"] == ""  # WHY: the malformed block reads as empty.


def test_extract_entry_rejects_a_device_without_port_config(wired: Any) -> None:
    """A device without a port_config block must be rejected by the entry builder."""
    gateway_info = {
        "device": {"id": "gw-1", "name": "Gateway-1"},  # WHY: no port_config key.
        "site_id": "site-1",  # WHY: the entry shape needs the site.
        "site_name": "Alpha Site",  # WHY: the entry shape needs the site name.
    }  # WHY: the entry builder must reject this record.

    assert WANProbeDeviceOverrideManager._extract_device_override_entry(gateway_info) is None


def test_extract_entry_rejects_a_non_dict_port_config(wired: Any) -> None:
    """A non-dict port_config block must be rejected by the entry builder."""
    gateway_info = {
        "device": {"id": "gw-1", "name": "Gateway-1", "port_config": "junk"},  # WHY: guard branch.
        "site_id": "site-1",  # WHY: the entry shape needs the site.
        "site_name": "Alpha Site",  # WHY: the entry shape needs the site name.
    }  # WHY: the entry builder must reject this record.

    assert WANProbeDeviceOverrideManager._extract_device_override_entry(gateway_info) is None


def test_initialize_fails_when_the_org_id_is_empty(wired: Any) -> None:
    """An empty org id must stop the prepare gate before the data load."""
    wired.org_id = ""  # WHY: the initialization gate sees an empty value.
    manager = WANProbeDeviceOverrideManager()  # WHY: a fresh instance per test.

    assert manager._initialize() is False  # WHY: the empty org id must fail the gate.
    assert manager.org_id == ""  # WHY: the instance keeps the empty value.


def test_load_data_fails_when_no_templates_exist(wired: Any, tmp_path: Any) -> None:
    """An empty template cache must stop the prepare gate before the selection."""
    empty_template_path = tmp_path / "empty_templates.csv"  # WHY: a header-only template cache.
    _write_csv(empty_template_path, [])  # WHY: zero template rows must fail the gate.
    csv_paths = {  # WHY: the data load resolves each CSV name to a path.
        "OrgGatewayTemplates.csv": str(empty_template_path),  # WHY: the empty template cache.
        "SiteList.csv": str(wired.site_path),  # WHY: the site cache file.
    }
    wired.file_path_utils.get_csv_path = MagicMock(side_effect=lambda name: csv_paths[name])  # WHY: stable per name.
    manager = WANProbeDeviceOverrideManager()  # WHY: a fresh instance per test.
    manager.org_id = "org-1"  # WHY: the initialization gate already passed.

    assert manager._load_data() is False  # WHY: the empty template set must fail.
    assert manager.templates == []  # WHY: the instance keeps the empty list.


def test_select_template_rejects_a_non_numeric_selection(wired: Any) -> None:
    """A non-numeric selection must fail the resolve gate with a message."""
    manager = WANProbeDeviceOverrideManager()  # WHY: a fresh instance per test.
    manager.templates = [{"id": "tmpl-1", "name": "Alpha"}]  # WHY: the menu needs one row.
    manager.sites = []  # WHY: the count map stays empty.

    assert manager._resolve_template_selection("abc", manager._build_template_display_list()) is False


def test_select_template_rejects_an_out_of_range_selection(wired: Any) -> None:
    """An out-of-range selection must fail the resolve gate before the commit."""
    manager = WANProbeDeviceOverrideManager()  # WHY: a fresh instance per test.
    manager.templates = [{"id": "tmpl-1", "name": "Alpha"}]  # WHY: the menu holds one row.
    manager.sites = []  # WHY: the count map stays empty.

    assert manager._resolve_template_selection("9", manager._build_template_display_list()) is False


def test_select_template_cancel_stops_the_run(wired: Any) -> None:
    """A cancel keyword at the template prompt must stop the prepare gate."""
    wired.safe_input.side_effect = ["cancel"]  # WHY: the prompt gate sees a cancel.
    manager = WANProbeDeviceOverrideManager()  # WHY: a fresh instance per test.
    manager.org_id = "org-1"  # WHY: the initialization gate already passed.
    manager.templates = [{"id": "tmpl-1", "name": "Alpha"}]  # WHY: the menu holds one row.
    manager.sites = []  # WHY: the count map stays empty.

    assert manager._select_template() is False  # WHY: the cancel must stop the run.


def test_find_template_sites_fails_when_no_site_matches(wired: Any) -> None:
    """A template with no bound site must stop the prepare gate."""
    manager = WANProbeDeviceOverrideManager()  # WHY: a fresh instance per test.
    manager.selected_template = {"id": "tmpl-9", "name": "Orphan"}  # WHY: no site binds here.
    manager.sites = [{"id": "site-1", "name": "Alpha Site", "gatewaytemplate_id": "tmpl-1"}]

    assert manager._find_template_sites() is False  # WHY: the empty site set must fail.
    assert manager.template_sites == []  # WHY: the instance keeps the empty list.


def test_find_devices_reports_when_no_gateways_exist(wired: Any) -> None:
    """An empty gateway scan must return an empty list without a write."""
    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    wired.list_devices.return_value.data = []  # WHY: the scan finds no gateways.

    devices = manager._find_devices_with_overrides()  # WHY: the scan must report empty.

    assert devices == []  # WHY: no gateway means no device.
    wired.update_device.assert_not_called()  # WHY: an empty scan must not write.


def test_find_devices_reports_when_no_overrides_exist(wired: Any) -> None:
    """A gateway with no WAN override must return an empty device list."""
    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    wired.list_devices.return_value.data = [
        {"id": "gw-1", "name": "Gateway-1", "port_config": {"ge-0/0/0": {"usage": "lan"}}}
    ]  # WHY: the gateway has no WAN port.

    devices = manager._find_devices_with_overrides()  # WHY: the filter must drop it.

    assert devices == []  # WHY: no override means no device.


def test_report_counts_the_success_rows(wired: Any) -> None:
    """The report helpers must count ports and successes from the result rows."""
    results = [
        {"ports_updated": ["ge-0/0/0", "ge-0/0/1"], "status": "SUCCESS"},
        {"ports_updated": [], "status": "FAILED"},
    ]  # WHY: two rows with different outcomes.

    total = WANProbeDeviceOverrideManager._total_ports_from_results(results)
    assert total == 2  # WHY: the port count sums both rows.
    assert WANProbeDeviceOverrideManager._count_success(results) == 1  # WHY: one success row.


def test_report_rows_carry_the_configuration_applied(wired: Any) -> None:
    """The report rows must carry the probe configuration that was applied."""
    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    manager.selected_template = {"id": "tmpl-1", "name": "Alpha"}  # WHY: the row reads this.
    results = [
        {
            "device_name": "Gateway-1",  # WHY: the row echoes the device.
            "device_id": "gw-1",  # WHY: the row carries the UUID.
            "site_name": "Alpha Site",  # WHY: the row echoes the site.
            "site_id": "site-1",  # WHY: the row carries the site UUID.
            "template_name": "Alpha",  # WHY: the row carries the template.
            "ports_updated": [],  # WHY: the empty branch renders an empty string.
            "status": "SKIPPED",  # WHY: the row carries the outcome.
            "error": "No matching ports found in current config",  # WHY: the row carries the reason.
        }
    ]  # WHY: one row exercises the empty ports branch.

    rows = manager._build_report_rows(results)

    assert rows[0]["ports_updated"] == ""  # WHY: the empty list renders empty.
    assert rows[0]["port_count"] == 0  # WHY: the count matches the list.
    assert rows[0]["new_probe_ips"] == ", ".join(manager.probe_ips)  # WHY: the config is carried.


def test_summary_prints_the_failure_hint(wired: Any) -> None:
    """The apply summary must point the operator at the audit report on failure."""
    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    results = [
        {"ports_updated": [], "status": "FAILED"},  # WHY: the failure branch fires.
    ]  # WHY: one failed row.

    manager._print_apply_summary(results, "Alpha", 0)  # WHY: the summary must hint at the CSV.

    assert results[0]["status"] == "FAILED"  # WHY: the row is intact.


def test_summary_prints_the_configuration_block_on_success(wired: Any) -> None:
    """The apply summary must echo the applied configuration on success."""
    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    results = [
        {"ports_updated": ["ge-0/0/0"], "status": "SUCCESS"},  # WHY: the success branch fires.
    ]  # WHY: one success row.

    manager._print_apply_summary(results, "Alpha", 1)  # WHY: the summary must echo the config.

    assert results[0]["status"] == "SUCCESS"  # WHY: the row is intact.


def test_dry_run_summary_prints_the_planned_count(wired: Any) -> None:
    """The dry run summary must count the planned updates from the rows."""
    results = [
        {"ports_updated": ["ge-0/0/0"], "status": "DRY-RUN"},  # WHY: the planned row.
        {"ports_updated": [], "status": "SKIPPED"},  # WHY: the skipped row.
    ]  # WHY: two rows with different outcomes.

    WANProbeDeviceOverrideManager._print_dry_run_summary(results, "Alpha", 1)  # WHY: the banner.

    assert sum(1 for row in results if row["status"] == "DRY-RUN") == 1  # WHY: one planned row.


def test_display_header_prints_the_dry_run_and_live_wording(wired: Any) -> None:
    """The header must print the mode specific wording for both branches."""
    manager = WANProbeDeviceOverrideManager()  # WHY: a fresh instance per test.

    manager._display_header(True)  # WHY: the dry run branch wording.
    manager._display_header(False)  # WHY: the live branch wording.

    assert manager.probe_ips == WANProbeDeviceOverrideManager.DEFAULT_PROBE_IPS  # WHY: defaults intact.


def test_scan_wraps_the_gateway_entries_with_site_metadata(wired: Any) -> None:
    """The single site scan must wrap each gateway with the site metadata."""
    wired.list_devices.return_value.data = [_gateway_with_override(), "junk"]  # WHY: one good entry.
    site_info = {"site_id": "site-1", "site_name": "Alpha Site"}  # WHY: the scan reads this.

    entries = WANProbeDeviceOverrideManager._scan_single_site(site_info)

    assert len(entries) == 1  # WHY: the junk entry is dropped.
    assert entries[0]["site_id"] == "site-1"  # WHY: the site UUID is carried.
    assert entries[0]["device"]["id"] == "gw-1"  # WHY: the device is carried.


def test_execute_stops_when_the_prepare_gate_fails(wired: Any) -> None:
    """A failed prepare gate must stop the run before the device scan."""
    wired.org_id = ""  # WHY: the initialization gate fails on an empty org id.

    WANProbeDeviceOverrideManager().configure(dry_run=True)  # WHY: the entry point must bail.

    wired.list_devices.assert_not_called()  # WHY: a failed gate must not scan.
    wired.exporter.assert_not_called()  # WHY: a failed gate must not report.


def test_execute_stops_when_the_scan_finds_no_devices(wired: Any) -> None:
    """An empty device scan must stop the run before the finalise phase."""
    wired.list_devices.return_value.data = []  # WHY: the scan finds no gateway.

    WANProbeDeviceOverrideManager().configure(dry_run=True)  # WHY: the entry point must bail.

    wired.update_device.assert_not_called()  # WHY: an empty scan must not write.
    wired.exporter.assert_not_called()  # WHY: an empty scan must not report.


def test_prepare_run_stops_when_the_data_load_fails(wired: Any, tmp_path: Any) -> None:
    """A failed data load must stop the prepare gate before the selection."""
    empty_template_path = tmp_path / "empty_templates.csv"  # WHY: a header-only template cache.
    _write_csv(empty_template_path, [])  # WHY: zero template rows must fail the load.
    csv_paths = {  # WHY: the data load resolves each CSV name to a path.
        "OrgGatewayTemplates.csv": str(empty_template_path),  # WHY: the empty template cache.
        "SiteList.csv": str(wired.site_path),  # WHY: the site cache file.
    }
    wired.file_path_utils.get_csv_path = MagicMock(side_effect=lambda name: csv_paths[name])  # WHY: stable per name.

    manager = WANProbeDeviceOverrideManager()  # WHY: a fresh instance per test.
    manager.org_id = "org-1"  # WHY: the initialization gate already passed.

    assert manager._prepare_run() is False  # WHY: the failed load must stop the gate.


def test_prepare_run_stops_when_the_template_selection_fails(wired: Any) -> None:
    """A cancel at the template prompt must stop the prepare gate."""
    wired.safe_input.side_effect = ["cancel"]  # WHY: the prompt gate sees a cancel.

    manager = WANProbeDeviceOverrideManager()  # WHY: a fresh instance per test.

    assert manager._prepare_run() is False  # WHY: the cancel must stop the gate.


def test_prepare_run_stops_when_no_site_matches_the_template(wired: Any) -> None:
    """A template with no bound site must stop the prepare gate."""
    manager = _prepare_manager(wired)  # WHY: the gate succeeds with the bound site.
    manager.selected_template = {"id": "tmpl-9", "name": "Orphan"}  # WHY: no site binds here.

    assert manager._find_template_sites() is False  # WHY: the empty site set must fail.


def test_site_counts_skip_sites_that_match_the_exclude_prefix(wired: Any) -> None:
    """A site name that matches the exclude prefix must leave the count map."""
    with patch.object(module, "MIST_SITE_EXCLUDE_PREFIX", "Alpha"):  # WHY: the filter reads this global.
        manager = WANProbeDeviceOverrideManager()  # WHY: a fresh instance per test.
        manager.sites = [
            {"id": "site-1", "name": "Alpha Site", "gatewaytemplate_id": "tmpl-1"},  # WHY: excluded by prefix.
            {"id": "site-2", "name": "Beta Site", "gatewaytemplate_id": "tmpl-2"},  # WHY: kept by the filter.
        ]

        counts = manager._compute_template_site_counts()

    assert counts == {"tmpl-2": 1}  # WHY: the excluded site leaves the map.


def test_apply_stops_when_the_stop_signal_fires(wired: Any) -> None:
    """A stop signal must break the apply loop before the first write."""
    wired.stop_signal = False  # WHY: the scan must run before the apply gate.
    wired.list_devices.return_value.data = [_gateway_with_override()]  # WHY: one target device.
    wired.get_device.return_value.data = _gateway_with_override()  # WHY: the patch would find it.

    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    devices = manager._find_devices_with_overrides()  # WHY: the scan finds the override.
    wired.stop_signal = True  # WHY: the apply loop reads this flag per device.
    results = manager._apply_changes(devices, dry_run=True)  # WHY: the loop must break early.

    assert results == []  # WHY: a stopped loop records no row.
    wired.update_device.assert_not_called()  # WHY: a stopped loop must not write.


def test_fetch_skips_a_config_with_a_non_dict_port_config(wired: Any) -> None:
    """A non-dict port_config block must record SKIPPED with the reason."""
    wired.list_devices.return_value.data = [_gateway_with_override()]  # WHY: one target device.
    wired.get_device.return_value.data = {"name": "Gateway-1", "port_config": ["junk"]}  # WHY: guard branch.

    manager = _prepare_manager(wired)  # WHY: the prepare gate loads templates and sites.
    devices = manager._find_devices_with_overrides()  # WHY: the scan finds the override.
    manager._finalise_run(devices, dry_run=False)  # WHY: the run records the skip.

    wired.update_device.assert_not_called()  # WHY: a skip must not write.
    report_data = wired.exporter.call_args.args[0]  # WHY: the report rows.
    assert report_data[0]["status"] == "SKIPPED"  # WHY: the bad block maps to skipped.
    assert "No port_config found" in report_data[0]["error"]  # WHY: the row names the fault.
