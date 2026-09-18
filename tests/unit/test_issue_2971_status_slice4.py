"""Regression tests for issue #2971, fourth status-before-count slice."""

from __future__ import annotations  # WHY: keep annotations lazy for pytest imports.

import logging  # WHY: caplog assertions need severity checks.
from typing import Any  # WHY: response doubles use loose Mist SDK shapes.
from unittest.mock import MagicMock, patch  # WHY: replace cloud and writer boundaries with controlled doubles.

import pytest  # WHY: pytest fixtures drive the real product functions.

from src.export import site_export_utils as site_utils_module  # WHY: patch and drive the real site exporter.
from src.export.site_export_utils import SiteExportUtils  # WHY: construct the real site export class.
from src.firmware import firmware_manager as firmware_module  # WHY: patch module globals for firmware tests.
from src.firmware.firmware_manager import FirmwareUpgradeStatusChecker  # WHY: drive the real firmware checker.
from src.gateway import gateway_export_utils as gateway_module  # WHY: patch module globals for gateway tests.
from src.gateway import gateway_ha_exporter as gateway_ha_module  # WHY: patch module globals for HA tests.
from src.gateway.gateway_export_utils import GatewayExportUtils  # WHY: drive the real gateway template exporter.
from src.gateway.gateway_ha_exporter import GatewayHaExporter  # WHY: drive the real HA gateway helper.
from src.reports import e911_bssid as e911_module  # WHY: patch module dependencies for E911 tests.
from src.reports import offline_device_reporter as offline_module  # WHY: patch module dependencies for offline tests.
from src.reports.global_wired_client_report_generator import (  # WHY: drive the real wired client helper.
    GlobalWiredClientReportGenerator,
)
from src.reports.offline_device_reporter import OfflineDeviceReporter  # WHY: drive the real offline report helper.


class _FailedResponse:
    """Response object for a 503 with an empty payload."""

    status_code = 503  # WHY: simulate the exact failing cloud status from issue #2971.
    data: Any = []  # WHY: simulate the empty SDK payload that previously looked normal.


class _ClientErrorResponse:
    """Response object for a 404 with an empty payload."""

    status_code = 404  # WHY: simulate a client-side cloud status for the HTTP 4xx analyzer rule.
    data: Any = []  # WHY: simulate the empty SDK payload that must not look normal.


def _has_status_at_problem_level(caplog: pytest.LogCaptureFixture) -> bool:
    """Return true when a warning or error log names the HTTP 503 status."""
    return any(  # WHY: operators act on WARNING or ERROR for this failure.
        record.levelno >= logging.WARNING and "503" in record.getMessage()  # WHY: the exact code must be visible.
        for record in caplog.records  # WHY: inspect structured records instead of formatted text.
    )


def _resolver_with_writer(writer: MagicMock) -> MagicMock:
    """Build a resolver double that blocks live cloud and file writes."""
    resolver = MagicMock()  # WHY: isolate product functions from live application state.
    resolver.apisession = MagicMock()  # WHY: satisfy SDK call signatures without live credentials.
    resolver.DataExporter.write_with_format_selection = writer  # WHY: detect unsafe empty exports.
    resolver.APICoreFetchUtils.get_api_response_data.return_value = []  # WHY: reproduce an empty 503 payload.
    resolver.APICoreFetchUtils.all_sites_with_limit.return_value = [{"id": "site-1", "name": "Alpha"}]  # WHY: site.
    return resolver  # WHY: callers patch product modules with this dependency set.


def _site_utils(writer: MagicMock, api_name: str) -> SiteExportUtils:
    """Build a real SiteExportUtils instance with a single failing SDK function."""
    mistapi_double = MagicMock()  # WHY: provide a local SDK boundary to the real SiteExportUtils instance.
    getattr(mistapi_double.api.v1.sites.rrm, api_name).return_value = _FailedResponse()  # WHY: feed 503.
    stats = mistapi_double.api.v1.sites.stats  # WHY: keep the line count low for stats endpoint setup.
    stats.getSiteGatewayMetrics.return_value = _FailedResponse()  # WHY: feed 503 for gateway metric tests.
    stats.getSiteSwitchesMetrics.return_value = _FailedResponse()  # WHY: feed 503 for switch metric tests.
    stats.getSiteWxRulesUsage.return_value = _FailedResponse()  # WHY: feed 503 for WxRules usage tests.
    utils = SiteExportUtils(  # WHY: constructor injection lets tests drive the real product methods.
        apisession=MagicMock(),  # WHY: satisfy the API call signature without credentials.
        PromptUtils=MagicMock(select_site=MagicMock(return_value="site-1")),  # WHY: select one safe fake site.
        ConfigUtils=MagicMock(),  # WHY: satisfy constructor injection without live configuration.
        DataProcessingUtils=MagicMock(),  # WHY: keep row processing in a controlled double.
        DataExporter=MagicMock(write_with_format_selection=writer),  # WHY: observe file writes.
        TimeUtils=MagicMock(),  # WHY: satisfy constructor injection without time dependencies.
        EnhancedSSHRunner=MagicMock(),  # WHY: satisfy constructor injection without SSH.
        InsightMetricsUtils=MagicMock(),  # WHY: satisfy constructor injection without insight calls.
        PacketCaptureManager=MagicMock(),  # WHY: satisfy parent constructor dependencies.
        APICoreFetchUtils=MagicMock(),  # WHY: satisfy constructor injection without org fetches.
        check_fn=MagicMock(return_value=False),  # WHY: keep debug-mode behavior disabled.
        PrettyTable=MagicMock(),  # WHY: satisfy constructor injection without rendering.
        tqdm=MagicMock(side_effect=lambda rows, **_kwargs: rows),  # WHY: avoid a progress bar in tests.
        mistapi=mistapi_double,  # WHY: use the controlled SDK boundary.
    )
    utils.DataProcessingUtils.flatten_nested_fields.side_effect = lambda rows: rows  # WHY: keep row prep simple.
    return utils  # WHY: callers invoke one real export method on this object.


def _firmware_checker(site_filter: str | None) -> FirmwareUpgradeStatusChecker:
    """Build a firmware checker without running its prompt-heavy initializer."""
    checker = FirmwareUpgradeStatusChecker.__new__(FirmwareUpgradeStatusChecker)  # WHY: bypass live org lookup.
    checker.site_filter = site_filter  # WHY: set the branch-specific target scope.
    checker.org_id = "org-1"  # WHY: fix the organization for deterministic assertions.
    checker.all_device_stats = []  # WHY: start with no accumulated device rows.
    return checker  # WHY: callers drive the real helper methods directly.


def test_current_channel_planning_503_suppresses_success_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A channel-planning 503 must not write an empty planning export."""
    writer = MagicMock()  # WHY: an outage must not create a valid empty export.
    utils = _site_utils(writer, "getSiteCurrentChannelPlanning")  # WHY: build the real product object.
    with caplog.at_level(logging.INFO, logger=site_utils_module.logger.name):  # WHY: capture module logs.
        result = utils.current_channel_planning()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Exported 0 channel planning records" not in caplog.text  # WHY: this success would be false.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.


def test_current_channel_planning_404_suppresses_success_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A channel-planning 404 must not write an empty planning export."""
    writer = MagicMock()  # WHY: a client error must not create a valid empty export.
    utils = _site_utils(writer, "getSiteCurrentChannelPlanning")  # WHY: build the real product object.
    utils.mistapi.api.v1.sites.rrm.getSiteCurrentChannelPlanning.return_value = _ClientErrorResponse()  # 404.
    with caplog.at_level(logging.INFO, logger=site_utils_module.logger.name):  # WHY: capture module logs.
        result = utils.current_channel_planning()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert any(  # WHY: the operator must see the exact client-error status.
        record.levelno >= logging.WARNING and "404" in record.getMessage() for record in caplog.records
    )
    assert "Exported 0 channel planning records" not in caplog.text  # WHY: this success would be false.
    writer.assert_not_called()  # WHY: a client error must not produce a valid empty export.


def test_fetch_site_stats_503_returns_false_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """A firmware site-stat 503 must not report a retrieved zero-device result."""
    checker = _firmware_checker("site-1")  # WHY: drive the site-specific branch.
    with patch.object(firmware_module, "apisession", MagicMock()):  # WHY: satisfy the SDK call signature.
        with patch.object(firmware_module.mistapi, "get_all", return_value=[]):  # WHY: block pagination work.
            with patch.object(
                firmware_module.mistapi.api.v1.sites.stats,  # WHY: patch the exact SDK namespace used by code.
                "listSiteDevicesStats",  # WHY: replace the site stats API function.
                return_value=_FailedResponse(),  # WHY: feed a 503 response with an empty payload.
            ):
                with caplog.at_level(logging.INFO, logger=firmware_module.logger.name):  # WHY: capture module logs.
                    result = checker._fetch_site_stats()  # WHY: drive the real product helper.
    assert result is False  # WHY: the existing failure contract for this helper is False.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Retrieved stats for 0 devices at site site-1" not in caplog.text  # WHY: false success.


def test_fetch_org_stats_503_returns_false_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """A firmware org-stat 503 must not report a retrieved zero-device result."""
    checker = _firmware_checker(None)  # WHY: drive the organization-wide branch.
    with patch.object(firmware_module, "apisession", MagicMock()):  # WHY: satisfy the SDK call signature.
        with patch.object(firmware_module.mistapi, "get_all", return_value=[]):  # WHY: block pagination work.
            with patch.object(
                firmware_module.mistapi.api.v1.orgs.stats,  # WHY: patch the exact SDK namespace used by code.
                "listOrgDevicesStats",  # WHY: replace the org stats API function.
                return_value=_FailedResponse(),  # WHY: feed a 503 response with an empty payload.
            ):
                with caplog.at_level(logging.INFO, logger=firmware_module.logger.name):  # WHY: capture module logs.
                    result = checker._fetch_org_stats()  # WHY: drive the real product helper.
    assert result is False  # WHY: the existing failure contract for this helper is False.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Retrieved stats for 0 devices organization-wide" not in caplog.text  # WHY: false success.


def test_gateway_templates_503_suppresses_success_and_writes_no_file(caplog: pytest.LogCaptureFixture) -> None:
    """A gateway-template 503 must not report no templates or write an empty export."""
    writer = MagicMock()  # WHY: an outage must not create a valid empty export.
    mistapi_double = MagicMock()  # WHY: provide a controlled gateway-template SDK boundary.
    mistapi_double.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates.return_value = _FailedResponse()  # WHY: 503.
    config_utils = MagicMock()  # WHY: avoid live organization selection.
    config_utils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: fix the target org.
    with patch.object(gateway_module, "apisession", MagicMock()):  # WHY: satisfy the SDK call signature.
        with patch.object(gateway_module, "mistapi", mistapi_double):  # WHY: route SDK calls to the double.
            with patch.object(gateway_module, "ConfigUtils", config_utils):  # WHY: avoid live config state.
                with patch.object(gateway_module, "DataExporter", MagicMock(write_with_format_selection=writer)):
                    with caplog.at_level(logging.INFO, logger=gateway_module.logger.name):  # WHY: capture logs.
                        result = GatewayExportUtils.templates()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Gateway templates exported to OrgGatewayTemplates.csv" not in caplog.text  # WHY: false success.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.


def test_collect_ha_gateways_503_returns_none_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """An HA gateway 503 must not report a normal zero-HA result."""
    resolver = _resolver_with_writer(MagicMock())  # WHY: control resolver dependencies.
    with patch.object(gateway_ha_module, "SourceDependencyResolver", resolver):  # WHY: avoid live app state.
        with patch.object(gateway_ha_module.mistapi.api.v1.sites.stats, "listSiteDevicesStats") as sdk_call:
            sdk_call.return_value = _FailedResponse()  # WHY: feed a 503 response with an empty payload.
            with caplog.at_level(logging.INFO, logger=gateway_ha_module.logger.name):  # WHY: capture module logs.
                result = GatewayHaExporter._collect_ha_gateways("site-1")  # WHY: drive the real product helper.
    assert result is None  # WHY: the existing failure contract for this helper is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Found 0 HA gateways in site site-1" not in caplog.text  # WHY: false success.


def test_fetch_radio_bulk_503_returns_empty_bundle_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """An AP-radio 503 must not report a successful zero-radio fetch."""
    with patch("mistapi.get_all", return_value=[]):  # WHY: block pagination after the failed first page.
        with patch("mistapi.api.v1.orgs.devices.listOrgApsMacs", return_value=_FailedResponse()):
            with caplog.at_level(logging.INFO, logger=e911_module.logger.name):  # WHY: capture module logs.
                result = e911_module.E911BSSIDReportGenerator._fetch_radio_bulk(MagicMock(), "org-1", 1000)
    assert result == {"radio_macs": [], "radio_bands": {}}  # WHY: preserve the existing empty bundle shape.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Radio MAC records fetched: 0" not in caplog.text  # WHY: this success would be false.


def test_fetch_clients_503_returns_empty_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """A wired-client 503 must not report a successful zero-client fetch."""
    resolver = _resolver_with_writer(MagicMock())  # WHY: control resolver dependencies.
    with patch("src.reports.global_wired_client_report_generator.SourceDependencyResolver", resolver):
        with patch("src.reports.global_wired_client_report_generator.mistapi.get_all", return_value=[]):
            with patch(
                "src.reports.global_wired_client_report_generator.mistapi.api.v1.orgs.wired_clients.searchOrgWiredClients",
                return_value=_FailedResponse(),
            ):
                with caplog.at_level(logging.INFO):  # WHY: capture echo and module logs.
                    result = GlobalWiredClientReportGenerator._fetch_clients("org-1", None)
    assert result == ([], False)  # WHY: preserve the existing exception failure contract.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Retrieved 0 wired client records" not in caplog.text  # WHY: this success would be false.


def test_fetch_data_503_returns_empty_devices_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """An offline-device 503 must not report a successful zero-device fetch."""
    resolver = _resolver_with_writer(MagicMock())  # WHY: control resolver dependencies.
    resolver.mistapi.api.v1.orgs.stats.listOrgDevicesStats.return_value = _FailedResponse()  # WHY: feed 503.
    with patch.object(offline_module, "SourceDependencyResolver", resolver):  # WHY: avoid live app state.
        with caplog.at_level(logging.INFO, logger=offline_module.logger.name):  # WHY: capture module logs.
            result = OfflineDeviceReporter._fetch_data("org-1")  # WHY: drive the real product helper.
    assert result == ({"site-1": "Alpha"}, [])  # WHY: preserve the tuple shape and known site lookup.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Retrieved stats for 0 devices" not in caplog.text  # WHY: this success would be false.
