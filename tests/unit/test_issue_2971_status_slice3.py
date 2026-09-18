"""Regression tests for issue #2971, third status-before-count slice."""

from __future__ import annotations  # WHY: keep annotations lazy for pytest imports.

import logging  # WHY: caplog assertions need severity checks.
from typing import Any  # WHY: response doubles use loose Mist SDK shapes.
from unittest.mock import MagicMock, patch  # WHY: replace cloud and writer boundaries with controlled doubles.

import pytest  # WHY: pytest fixtures drive the real product functions.

from src.api import api_data_fetcher as fetcher_module  # WHY: patch the shared fetcher resolver.
from src.api.api_data_fetcher import APIDataFetcher  # WHY: keep APIDataFetcher real in dispatch tests.
from src.device import prompt_utils as prompt_module  # WHY: patch module globals in the real prompt helper.
from src.device.prompt_utils import PromptNetworkDeviceUtils  # WHY: drive the real product class.
from src.export import org_site_exporter as site_module  # WHY: patch module globals in the real site exporter.
from src.export import site_device_exporter as site_device_module  # WHY: patch the real VC exporter.
from src.export import site_export_utils as site_utils_module  # WHY: patch the real site stats helper.
from src.export.org_site_exporter import OrgSiteExporter  # WHY: drive the real product class.
from src.export.site_device_exporter import SiteDeviceExporter  # WHY: drive the real product class.
from src.export.site_export_utils import SiteExportUtils  # WHY: drive the real product class.
from src.org import org_ticket_manager as ticket_module  # WHY: patch module globals in the real ticket manager.
from src.org.org_ticket_manager import OrgTicketManager  # WHY: drive the real product class.


class _FailedResponse:
    """Response object for a 503 with an empty payload."""

    status_code = 503  # WHY: simulate the exact failing cloud status from issue #2971.
    data: Any = []  # WHY: simulate the empty SDK payload that previously looked normal.


def _failed_api_call(_session: Any, _org_id: str, **_kwargs: Any) -> _FailedResponse:
    """Return a 503 response for APIDataFetcher-driven exporters."""
    return _FailedResponse()  # WHY: drive the real fetcher through the outage branch.


def _has_status_at_problem_level(caplog: pytest.LogCaptureFixture) -> bool:
    """Return true when a warning or error log names the HTTP 503 status."""
    return any(  # WHY: operators act on WARNING or ERROR for this failure.
        record.levelno >= logging.WARNING and "503" in record.getMessage()  # WHY: the exact code must be visible.
        for record in caplog.records  # WHY: inspect structured records instead of formatted text.
    )


def _writer_resolver(writer: MagicMock) -> MagicMock:
    """Build a resolver double that blocks live cloud and file writes."""
    resolver = MagicMock()  # WHY: isolate product functions from live application state.
    resolver.apisession = MagicMock()  # WHY: satisfy SDK call signatures without live credentials.
    resolver.APIDataFetcher = APIDataFetcher  # WHY: keep the shared fetcher under test real.
    resolver.DataExporter.write_with_format_selection = writer  # WHY: detect unsafe empty exports.
    resolver.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: fix the target org.
    resolver.RateLimitingUtils.get_rate_limited_delay.return_value = (None, 0)  # WHY: keep tests fast.
    resolver.OUTPUT_FORMAT = "csv"  # WHY: let site export success choose the CSV message.
    resolver.ProgressContext = MagicMock()  # WHY: satisfy progress completion construction.
    resolver.mistapi = MagicMock()  # WHY: support code that reads the SDK through the resolver.
    resolver.mistapi.get_all.return_value = []  # WHY: reproduce the empty SDK payload after a 503.
    return resolver  # WHY: callers patch each product module with this dependency set.


def _patch_fetcher_resolver(resolver: MagicMock) -> patch:
    """Patch APIDataFetcher dependencies for a controlled 503 response."""
    return patch.object(fetcher_module, "SourceDependencyResolver", resolver)  # WHY: avoid live org and rate state.


def test_sites_503_returns_none_suppresses_success_and_writes_no_file(caplog: pytest.LogCaptureFixture) -> None:
    """A site-list 503 must not report a completed empty export."""
    writer = MagicMock()  # WHY: an outage must not create a valid empty export.
    resolver = _writer_resolver(writer)  # WHY: control dependencies for the exporter and fetcher.
    with patch.object(site_module, "SourceDependencyResolver", resolver):  # WHY: route exporter through doubles.
        with _patch_fetcher_resolver(resolver):  # WHY: route APIDataFetcher through doubles.
            with patch("src.export.org_site_exporter.mistapi.api.v1.orgs.sites.listOrgSites", _failed_api_call):
                with caplog.at_level(logging.INFO):  # WHY: capture success and failure logs from both modules.
                    result = OrgSiteExporter.sites()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Completed site list export and wrote results" not in caplog.text  # WHY: this success would be false.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.


def test_list_tickets_503_returns_none_suppresses_success_and_writes_no_file(caplog: pytest.LogCaptureFixture) -> None:
    """A support-ticket 503 must not report a completed empty export."""
    writer = MagicMock()  # WHY: an outage must not create a valid empty export.
    resolver = _writer_resolver(writer)  # WHY: control dependencies for the exporter and fetcher.
    resolver.mistapi.api.v1.orgs.tickets.listOrgTickets = _failed_api_call  # WHY: preserve __name__ for fetcher logs.
    with patch.object(  # WHY: route ticket manager through doubles.
        ticket_module, "SourceDependencyResolver", resolver
    ):
        with _patch_fetcher_resolver(resolver):  # WHY: route APIDataFetcher through doubles.
            with caplog.at_level(logging.INFO):  # WHY: capture success and failure logs from both modules.
                result = OrgTicketManager.list_tickets()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Completed org ticket list export" not in caplog.text  # WHY: this success would be false.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.


def test_fetch_switch_gateway_port_stats_503_returns_empty_and_suppresses_success(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A switch-port-stat 503 must not report a retrieved zero-port result."""
    helper = PromptNetworkDeviceUtils(MagicMock(), MagicMock(), MagicMock())  # WHY: use the real product class.
    failed = _FailedResponse()  # WHY: reuse the standard failed response double.
    failed.data = {"results": []}  # WHY: match the endpoint shape that the product reads.
    with patch.object(prompt_module.mistapi.api.v1.sites.stats, "searchSiteSwOrGwPorts", return_value=failed):
        with caplog.at_level(logging.INFO, logger=prompt_module.logger.name):  # WHY: capture module logs.
            result = helper._fetch_switch_gateway_port_stats("site-1", "dev-1", "aa:bb")  # WHY: drive real code.
    assert result == {}  # WHY: the existing failure contract for this helper is an empty dict.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Retrieved 0 port stat entries from searchSiteSwOrGwPorts" not in caplog.text  # WHY: false success.


def test_fetch_ap_port_stats_503_returns_empty_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """An AP port-stat 503 must not report a missing port_stat field as normal."""
    helper = PromptNetworkDeviceUtils(MagicMock(), MagicMock(), MagicMock())  # WHY: use the real product class.
    failed = _FailedResponse()  # WHY: reuse the standard failed response double.
    failed.data = {"port_stat": {}}  # WHY: match the endpoint shape that the product reads.
    with patch.object(prompt_module.mistapi.api.v1.sites.stats, "getSiteDeviceStats", return_value=failed):
        with caplog.at_level(logging.INFO, logger=prompt_module.logger.name):  # WHY: capture module logs.
            result = helper._fetch_ap_port_stats("site-1", "dev-1")  # WHY: drive the real product helper.
    assert result == {}  # WHY: the existing failure contract for this helper is an empty dict.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "No port_stat found in AP stats for device dev-1" not in caplog.text  # WHY: outage is not empty data.


def test_current_guests_503_returns_none_suppresses_success_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A current-guest 503 must not write an empty guest export."""
    writer = MagicMock()  # WHY: an outage must not create a valid empty export.
    resolver = _writer_resolver(writer)  # WHY: control dependencies for the exporter.
    with patch.object(site_module, "SourceDependencyResolver", resolver):  # WHY: avoid live org resolution.
        with patch.object(site_module.mistapi, "get_all", return_value=[]):  # WHY: reproduce empty 503 payload.
            with patch.object(  # WHY: replace the cloud request with a controlled failed response.
                site_module.mistapi.api.v1.orgs.guests,  # WHY: patch the exact SDK namespace used by product code.
                "searchOrgGuestAuthorization",  # WHY: replace the current-guest API function.
                return_value=_FailedResponse(),  # WHY: feed a 503 response with an empty payload.
            ):
                with caplog.at_level(logging.INFO, logger=site_module.logger.name):  # WHY: capture module logs.
                    result = OrgSiteExporter.current_guests()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Fetched 0 current guest users from API." not in caplog.text  # WHY: this success would be false.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.


def test_historical_guests_503_returns_none_suppresses_success_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A historical-guest 503 must not write an empty guest export."""
    writer = MagicMock()  # WHY: an outage must not create a valid empty export.
    resolver = _writer_resolver(writer)  # WHY: control dependencies for the exporter.
    with patch.object(site_module, "SourceDependencyResolver", resolver):  # WHY: avoid live org resolution.
        with patch.object(site_module.mistapi, "get_all", return_value=[]):  # WHY: reproduce empty 503 payload.
            with patch.object(  # WHY: replace the cloud request with a controlled failed response.
                site_module.mistapi.api.v1.orgs.guests,  # WHY: patch the exact SDK namespace used by product code.
                "searchOrgGuestAuthorization",  # WHY: replace the historical-guest API function.
                return_value=_FailedResponse(),  # WHY: feed a 503 response with an empty payload.
            ):
                with caplog.at_level(logging.INFO, logger=site_module.logger.name):  # WHY: capture module logs.
                    result = OrgSiteExporter.historical_guests()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Fetched 0 historical guest users from API." not in caplog.text  # WHY: this success would be false.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.


def test_export_vc_for_device_503_returns_none_suppresses_empty_message_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A virtual-chassis 503 must not report that the device has no virtual chassis."""
    writer = MagicMock()  # WHY: an outage must not create a valid empty export.
    resolver = _writer_resolver(writer)  # WHY: control dependencies for the exporter.
    with patch.object(site_device_module, "SourceDependencyResolver", resolver):  # WHY: avoid live state.
        with patch.object(  # WHY: replace the cloud request with a controlled failed response.
            site_device_module.mistapi.api.v1.sites.devices,  # WHY: patch the SDK namespace used by product code.
            "getSiteDeviceVirtualChassis",  # WHY: replace the VC API function.
            return_value=_FailedResponse(),  # WHY: feed a 503 response with an empty payload.
        ):
            with caplog.at_level(logging.INFO, logger=site_device_module.logger.name):  # WHY: capture module logs.
                result = SiteDeviceExporter._export_vc_for_device("site-1", "dev-1", "Switch 1")  # WHY: real helper.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "! No virtual chassis data returned for device Switch 1" not in caplog.text  # WHY: false empty result.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.


def test_site_stats_503_returns_none_suppresses_success_and_writes_no_file(caplog: pytest.LogCaptureFixture) -> None:
    """A site-stats 503 must not write an empty site-stats export."""
    writer = MagicMock()  # WHY: an outage must not create a valid empty export.
    mistapi_double = MagicMock()  # WHY: provide a local SDK boundary to the real SiteExportUtils instance.
    mistapi_double.api.v1.sites.stats.getSiteStats.return_value = _FailedResponse()  # WHY: feed a 503 response.
    utils = SiteExportUtils(  # WHY: constructor injection lets this test drive the real product method.
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
    with caplog.at_level(logging.INFO, logger=site_utils_module.logger.name):  # WHY: capture module logs.
        result = utils.site_stats()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Exported 0 site stats records to SiteSiteStats.csv" not in caplog.text  # WHY: false success.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.
