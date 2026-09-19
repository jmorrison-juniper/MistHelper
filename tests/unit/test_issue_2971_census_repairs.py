"""Regression tests for issue #2971 census findings."""

from __future__ import annotations  # WHY: keep annotations lazy for pytest imports.

import logging  # WHY: caplog assertions need severity checks.
from typing import Any  # WHY: response doubles use loose Mist SDK shapes.
from unittest.mock import MagicMock, patch  # WHY: replace cloud and writer boundaries with controlled doubles.

import pytest  # WHY: pytest fixtures drive the real product functions.

from src.export import site_guest_authorization_exporter as guest_module  # WHY: patch the real guest exporter.
from src.export import site_mist_edge_events_exporter as mist_edge_module  # WHY: patch the real Mist Edge exporter.
from src.export import site_nac_client_events_exporter as nac_module  # WHY: patch the real NAC exporter.
from src.export import site_wan_usage_exporter as wan_module  # WHY: patch the real WAN exporter.
from src.export import site_webhook_deliveries_exporter as webhook_module  # WHY: patch the real webhook exporter.
from src.export.site_guest_authorization_exporter import SiteGuestAuthorizationExporter  # WHY: real product class.
from src.export.site_mist_edge_events_exporter import SiteMistEdgeEventsExporter  # WHY: real product class.
from src.export.site_nac_client_events_exporter import SiteNacClientEventsExporter  # WHY: real product class.
from src.export.site_wan_usage_exporter import SiteWanUsageExporter  # WHY: real product class.
from src.export.site_webhook_deliveries_exporter import SiteWebhookDeliveriesExporter  # WHY: real product class.


class _FailedResponse:
    """Response object for a 503 with an empty payload."""

    status_code = 503  # WHY: simulate the exact failing cloud status from issue #2971.
    data: list[Any] = []  # WHY: simulate the empty SDK payload that previously looked normal.


def _has_status_at_problem_level(caplog: pytest.LogCaptureFixture) -> bool:
    """Return true when a warning or error log names the HTTP 503 status."""
    return any(  # WHY: operators act on WARNING or ERROR for this failure.
        record.levelno >= logging.WARNING and "503" in record.getMessage()  # WHY: the exact code must be visible.
        for record in caplog.records  # WHY: inspect structured records instead of formatted text.
    )


def _resolver(writer: MagicMock) -> MagicMock:
    """Build a resolver double that prevents live cloud and file access."""
    resolver = MagicMock()  # WHY: isolate product functions from live application state.
    resolver.apisession = MagicMock()  # WHY: satisfy SDK call signatures without live credentials.
    resolver.SiteDeviceExporter._resolve_site_for_stats.return_value = ("site-1", "Alpha")  # WHY: select site.
    resolver.DataExporter.write_with_format_selection = writer  # WHY: detect unsafe empty exports.
    return resolver  # WHY: callers patch each product module with this dependency set.


def _run_site_export(
    caplog: pytest.LogCaptureFixture,
    module: Any,
    exporter: Any,
    method_name: str,
    api_namespace: Any,
    api_name: str,
    success_message: str,
) -> None:
    """Drive one site exporter through a 503 empty payload."""
    writer = MagicMock()  # WHY: an outage must not create a valid empty export.
    with patch.object(module, "SourceDependencyResolver", _resolver(writer)):  # WHY: avoid live app state.
        with patch.object(module.mistapi, "get_all", return_value=[]):  # WHY: reproduce empty 503 payload.
            with patch.object(api_namespace, api_name, return_value=_FailedResponse()):  # WHY: feed 503.
                with caplog.at_level(logging.INFO, logger=module.logger.name):  # WHY: capture module logs.
                    result = getattr(exporter, method_name)()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for these exporters is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert success_message not in caplog.text  # WHY: this success or no-data line would be false.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.


def test_guest_authorizations_503_suppresses_no_data_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A guest authorization 503 must not report a normal empty site result."""
    _run_site_export(
        caplog,
        guest_module,
        SiteGuestAuthorizationExporter,
        "guest_authorizations",
        guest_module.mistapi.api.v1.sites.guests,
        "searchSiteGuestAuthorization",
        "! No guest authorization data found for this site",
    )  # WHY: share the real exporter assertion flow.


def test_mist_edge_events_503_suppresses_no_data_and_writes_no_file(caplog: pytest.LogCaptureFixture) -> None:
    """A Mist Edge event 503 must not report a normal empty site result."""
    _run_site_export(
        caplog,
        mist_edge_module,
        SiteMistEdgeEventsExporter,
        "mist_edge_events",
        mist_edge_module.mistapi.api.v1.sites.mxedges,
        "searchSiteMistEdgeEvents",
        "! No Mist Edge event data found for this site",
    )  # WHY: share the real exporter assertion flow.


def test_nac_client_events_503_suppresses_no_data_and_writes_no_file(caplog: pytest.LogCaptureFixture) -> None:
    """A NAC client event 503 must not report a normal empty site result."""
    _run_site_export(
        caplog,
        nac_module,
        SiteNacClientEventsExporter,
        "nac_client_events",
        nac_module.mistapi.api.v1.sites.nac_clients,
        "searchSiteNacClientEvents",
        "! No NAC client event data found for this site",
    )  # WHY: share the real exporter assertion flow.


def test_wan_usages_503_suppresses_no_data_and_writes_no_file(caplog: pytest.LogCaptureFixture) -> None:
    """A WAN usage 503 must not report a normal empty site result."""
    _run_site_export(
        caplog,
        wan_module,
        SiteWanUsageExporter,
        "wan_usages",
        wan_module.mistapi.api.v1.sites.wan_usages,
        "searchSiteWanUsage",
        "! No WAN usage data found for this site",
    )  # WHY: share the real exporter assertion flow.


def test_webhook_deliveries_503_suppresses_no_data_and_writes_no_file(caplog: pytest.LogCaptureFixture) -> None:
    """A webhook delivery 503 must not report a normal empty webhook result."""
    writer = MagicMock()  # WHY: an outage must not create a valid empty export.
    with patch.object(webhook_module, "SourceDependencyResolver", _resolver(writer)):  # WHY: avoid live app state.
        with patch.object(webhook_module.mistapi, "get_all", return_value=[]):  # WHY: reproduce empty 503 payload.
            with patch.object(SiteWebhookDeliveriesExporter, "_select_webhook_id", return_value=("hook-1", "Hook")):
                with patch.object(
                    webhook_module.mistapi.api.v1.sites.webhooks,  # WHY: patch the SDK namespace used by code.
                    "searchSiteWebhooksDeliveries",  # WHY: replace the webhook delivery API function.
                    return_value=_FailedResponse(),  # WHY: feed a 503 response with an empty payload.
                ):
                    with caplog.at_level(logging.INFO, logger=webhook_module.logger.name):  # WHY: capture logs.
                        result = SiteWebhookDeliveriesExporter.deliveries()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for this exporter is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "! No webhook delivery data found" not in caplog.text  # WHY: this empty-result line would be false.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.
