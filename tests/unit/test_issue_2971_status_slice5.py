"""Regression tests for issue #2971, fifth status-before-count slice."""

from __future__ import annotations  # WHY: keep annotations lazy for pytest imports.

import logging  # WHY: caplog assertions need severity checks.
from typing import Any  # WHY: response doubles use loose Mist SDK shapes.
from unittest.mock import MagicMock, patch  # WHY: replace cloud and writer boundaries with controlled doubles.

import pytest  # WHY: pytest fixtures drive the real product functions.

from src.refactors import device_data_fetcher as fetcher_module  # WHY: patch the real device fetcher resolver.
from src.refactors.device_data_fetcher import DeviceDataFetcher  # WHY: drive the real device fetcher.
from src.reports import ssid_broadcast_gap_report as ssid_gap_module  # WHY: drive the real SSID report.
from src.reports import wired_client_manufacturer_report_generator as wired_report_module  # WHY: real report.
from src.ssid_consolidation import _ssid_template_phase1 as phase1_module  # WHY: drive the phase helper.
from src.ssid_consolidation import ssid_template_consolidation as ssid_template_module  # WHY: drive parent helper.
from src.ui import interactive_display_utils as display_module  # WHY: patch and drive real display functions.
from src.ui import prompt_utils as prompt_module  # WHY: patch and drive real prompt helpers.
from src.ui.interactive_display_utils import InteractiveDisplayUtils  # WHY: import the real product class.
from src.ui.prompt_utils import PromptUtils  # WHY: import the real prompt helper.


class _FailedResponse:
    """Response object for a 503 with an empty payload."""

    status_code = 503  # WHY: simulate the exact failing cloud status from issue #2971.
    data: Any = []  # WHY: simulate the empty SDK payload that previously looked normal.


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
    resolver.PromptUtils.select_site_id_from_csv.return_value = "site-1"  # WHY: select one safe fake site.
    resolver.PromptUtils.select_device_id_from_inventory.return_value = "dev-1"  # WHY: select one fake device.
    resolver.DeviceDataFetcher = DeviceDataFetcher  # WHY: keep the real fetcher in the display path.
    resolver.DisplayUtils.dict_list_as_pretty_table = MagicMock()  # WHY: prevent terminal rendering in tests.
    return resolver  # WHY: callers patch product modules with this dependency set.


def _failed_api_call(*_args: Any, **_kwargs: Any) -> _FailedResponse:
    """Return a 503 response for generic helper tests."""
    return _FailedResponse()  # WHY: drive the real functions through the outage branch.


def _run_display_with_failed_fetch(
    caplog: pytest.LogCaptureFixture,
    method_name: str,
    api_patch_path: str,
    success_message: str,
) -> None:
    """Drive one interactive display wrapper through a 503 response."""
    writer = MagicMock()  # WHY: an outage must not create a valid empty export.
    resolver = _resolver_with_writer(writer)  # WHY: control display and fetcher dependencies.
    with patch.object(display_module, "SourceDependencyResolver", resolver):  # WHY: route wrapper dependencies.
        with patch.object(fetcher_module, "_MH", resolver):  # WHY: route real DeviceDataFetcher dependencies.
            with patch(api_patch_path, _failed_api_call):  # WHY: replace the cloud request with a 503 response.
                with caplog.at_level(logging.INFO):  # WHY: capture logs from display and fetcher modules.
                    result = getattr(InteractiveDisplayUtils, method_name)()  # WHY: drive the real product function.
    assert result is None  # WHY: the existing failure contract for these display helpers is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert success_message not in caplog.text  # WHY: this success line would be false.
    writer.assert_not_called()  # WHY: an outage must not produce a valid empty export.


def test_ssid_gap_503_returns_empty_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """A derived-WLAN 503 must not report a site as missing an SSID."""
    sites = [{"id": "site-1", "name": "Alpha"}]  # WHY: one site makes the false conclusion visible.
    with patch.object(ssid_gap_module.mistapi.api.v1.sites.wlans, "listSiteWlansDerived", _failed_api_call):
        with caplog.at_level(logging.INFO, logger=ssid_gap_module.logger.name):  # WHY: capture module logs.
            result = ssid_gap_module.SSIDBroadcastGapReport._find_missing_sites(MagicMock(), sites, "Corp")
    assert result == []  # WHY: preserve list return while avoiding a false missing-site row.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "SSID gap report found" not in caplog.text  # WHY: this complete-report count would be false.


def test_wired_manufacturer_503_returns_empty_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """A wired-client 503 must not report a successful zero-client fetch."""
    resolver = _resolver_with_writer(MagicMock())  # WHY: control resolver dependencies.
    with patch.object(wired_report_module, "SourceDependencyResolver", resolver):  # WHY: avoid live app state.
        with patch.object(wired_report_module.mistapi, "get_all", return_value=[]):  # WHY: block pagination work.
            with patch.object(
                wired_report_module.mistapi.api.v1.orgs.wired_clients,  # WHY: patch the namespace used by code.
                "searchOrgWiredClients",  # WHY: replace the wired-client API function.
                _failed_api_call,  # WHY: feed a 503 response with an empty payload.
            ):
                with caplog.at_level(logging.INFO):  # WHY: capture echo and module logs.
                    result = wired_report_module.WiredClientManufacturerReportGenerator._fetch_all_clients("org-1")
    assert result == []  # WHY: the existing failure contract for this helper is an empty list.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Retrieved 0 wired client records" not in caplog.text  # WHY: this success would be false.


def test_phase1_fetch_and_log_503_returns_empty_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """A phase-one bulk 503 must not report a successful zero-row fetch."""
    with patch.object(phase1_module.mistapi, "get_all", return_value=[]):  # WHY: block pagination work.
        with caplog.at_level(logging.INFO, logger=phase1_module.logger.name):  # WHY: capture module logs.
            result = phase1_module._fetch_and_log("templates", _failed_api_call, MagicMock(), "org-1")
    assert result == []  # WHY: the existing failure contract for this helper is an empty list.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Templates fetched: 0" not in caplog.text  # WHY: this success count would be false.


def test_parent_fetch_and_log_503_returns_empty_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """A parent consolidation bulk 503 must not report a successful zero-row fetch."""
    with patch.object(ssid_template_module.mistapi, "get_all", return_value=[]):  # WHY: block pagination work.
        with caplog.at_level(logging.INFO, logger=ssid_template_module.logger.name):  # WHY: capture module logs.
            result = ssid_template_module._fetch_and_log("sites", _failed_api_call, MagicMock(), "org-1")
    assert result == []  # WHY: the existing failure contract for this helper is an empty list.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Sites fetched: 0" not in caplog.text  # WHY: this success count would be false.


def test_device_stats_503_returns_none_suppresses_success_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A device-stats 503 must not report completed interactive display."""
    _run_display_with_failed_fetch(
        caplog,
        "device_stats",
        "src.ui.interactive_display_utils.mistapi.api.v1.sites.stats.getSiteDeviceStats",
        "Completed device_stats execution.",
    )  # WHY: share the real display/fetcher assertion flow.


def test_device_tests_503_returns_none_suppresses_success_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A device-test 503 must not report completed interactive display."""
    _run_display_with_failed_fetch(
        caplog,
        "device_tests",
        "src.ui.interactive_display_utils.mistapi.api.v1.sites.devices.getSiteDeviceSyntheticTest",
        "Completed device_tests execution.",
    )  # WHY: share the real display/fetcher assertion flow.


def test_device_config_503_returns_none_suppresses_success_and_writes_no_file(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A device-config 503 must not report completed interactive display."""
    _run_display_with_failed_fetch(
        caplog,
        "device_config",
        "src.ui.interactive_display_utils.mistapi.api.v1.sites.devices.getSiteDevice",
        "Completed device_config execution.",
    )  # WHY: share the real display/fetcher assertion flow.


def test_site_wireless_clients_503_returns_empty_and_suppresses_success(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A site wireless-client 503 must not report a successful zero-client fetch."""
    resolver = _resolver_with_writer(MagicMock())  # WHY: control resolver dependencies.
    with patch.object(prompt_module, "SourceDependencyResolver", resolver):  # WHY: avoid live app state.
        with patch.object(prompt_module.mistapi, "get_all", return_value=[]):  # WHY: block pagination work.
            with patch.object(
                prompt_module.mistapi.api.v1.sites.clients,  # WHY: patch the namespace used by code.
                "searchSiteWirelessClients",  # WHY: replace the site wireless-client API function.
                _failed_api_call,  # WHY: feed a 503 response with an empty payload.
            ):
                with caplog.at_level(logging.INFO, logger=prompt_module.logger.name):  # WHY: capture module logs.
                    result = PromptUtils._fetch_site_wireless_clients("site-1")
    assert result == []  # WHY: the existing failure contract for this helper is an empty list.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Found 0 wireless clients in site" not in caplog.text  # WHY: this success would be false.


def test_wired_manufacturer_404_returns_empty_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """A wired-client 404 must not report a successful zero-client fetch."""

    class ClientErrorResponse:
        """Response object for a 404 with an empty payload."""

        status_code = 404  # WHY: simulate a missing organization resource response from the cloud.
        data: Any = []  # WHY: simulate the empty SDK payload that previously looked normal.

    resolver = _resolver_with_writer(MagicMock())  # WHY: control resolver dependencies.
    with patch.object(wired_report_module, "SourceDependencyResolver", resolver):  # WHY: avoid live app state.
        with patch.object(wired_report_module.mistapi, "get_all", return_value=[]):  # WHY: block pagination work.
            with patch.object(
                wired_report_module.mistapi.api.v1.orgs.wired_clients,  # WHY: patch the namespace used by code.
                "searchOrgWiredClients",  # WHY: replace the wired-client API function.
                return_value=ClientErrorResponse(),  # WHY: feed a 404 response with an empty payload.
            ):
                with caplog.at_level(logging.INFO):  # WHY: capture echo and module logs.
                    result = wired_report_module.WiredClientManufacturerReportGenerator._fetch_all_clients("org-1")
    assert result == []  # WHY: the existing failure contract for this helper is an empty list.
    assert any(  # WHY: require an operator-grade log for the exact status.
        record.levelno >= logging.WARNING and "404" in record.getMessage() for record in caplog.records
    )
    assert "Retrieved 0 wired client records" not in caplog.text  # WHY: this success would be false.
