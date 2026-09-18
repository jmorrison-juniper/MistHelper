"""Regression tests for issue #2971, first status-before-count slice."""

from __future__ import annotations  # WHY: keep annotations lazy for the pytest process.

import logging  # WHY: caplog assertions need numeric severity levels.
from typing import Any  # WHY: fake response data carries loose Mist payload types.
from unittest.mock import MagicMock, patch  # WHY: patch Mist SDK calls without live cloud access.

import pytest  # WHY: SystemExit and caplog fixtures drive the real functions.

from src.api.api_fetch_utils import APIFetchUtils  # WHY: import the real API helper under test.
from src.api.tenant_fetch import APITenantFetchUtils  # WHY: import the real tenant helper under test.
from src.capture import client_pcap_downloader as pcap_module  # WHY: patch module globals in the real code.
from src.capture.client_pcap_downloader import ClientPacketCaptureDownloader  # WHY: drive the real downloader.
from src.config.config_utils import ConfigUtils  # WHY: import the real configuration helper under test.
from src.device.device_utils import DeviceUtils  # WHY: import the real device helper under test.


class _FailedResponse:
    """Response object for a 503 with an empty payload."""

    status_code = 503  # WHY: simulate the exact failing cloud status from issue #2971.
    data: list[Any] = []  # WHY: simulate the empty SDK payload that looked normal before the fix.

    def __bool__(self) -> bool:
        """Return false so legacy list checks follow their documented failure path."""
        return False  # WHY: ConfigUtils must use its existing empty-selection exit path.


def _has_status_at_problem_level(caplog: pytest.LogCaptureFixture) -> bool:
    """Return true when a warning or error log names the HTTP 503 status."""
    return any(  # WHY: the operator only acts on WARNING or ERROR for this failure.
        record.levelno >= logging.WARNING and "503" in record.getMessage()  # WHY: the exact code must be visible.
        for record in caplog.records  # WHY: inspect the captured log records directly.
    )


def test_fetch_wireless_clients_503_returns_empty_and_suppresses_success(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A wireless-client 503 must not report a successful zero-client fetch."""
    downloader = ClientPacketCaptureDownloader(MagicMock(), org_id="org-1")  # WHY: avoid a live org prompt.
    fake_sdk = MagicMock()  # WHY: replace the Mist SDK boundary with a controlled object.
    fake_sdk.get_all.return_value = []  # WHY: reproduce the empty payload returned after a 5xx.
    fake_sdk.api.v1.sites.clients.searchSiteWirelessClients.return_value = _FailedResponse()  # WHY: feed 503.
    with caplog.at_level(logging.INFO, logger=pcap_module.logger.name):  # WHY: capture success and failure logs.
        with patch.object(pcap_module, "mistapi", fake_sdk), patch.object(pcap_module, "MISTAPI_AVAILABLE", True):
            result = downloader._fetch_wireless_clients("site-1")  # WHY: drive the real product function.
    assert result == []  # WHY: the existing failure contract for this helper is an empty list.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Fetched 0 wireless clients for site site-1" not in caplog.text  # WHY: this success line was false.


def test_fetch_captures_503_returns_empty_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """A packet-capture 503 must not report a successful zero-PCAP fetch."""
    downloader = ClientPacketCaptureDownloader(MagicMock(), org_id="org-1")  # WHY: avoid a live org prompt.
    fake_sdk = MagicMock()  # WHY: replace the Mist SDK boundary with a controlled object.
    fake_sdk.get_all.return_value = []  # WHY: reproduce the empty payload returned after a 5xx.
    fake_sdk.api.v1.sites.pcaps.listSitePacketCaptures.return_value = _FailedResponse()  # WHY: feed 503.
    with caplog.at_level(logging.INFO, logger=pcap_module.logger.name):  # WHY: capture success and failure logs.
        with patch.object(pcap_module, "mistapi", fake_sdk), patch.object(pcap_module, "MISTAPI_AVAILABLE", True):
            result = downloader._fetch_captures("site-1", "aa:bb:cc:dd:ee:ff")  # WHY: drive the real function.
    assert result == []  # WHY: the existing failure contract for this helper is an empty list.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Fetched 0 PCAPs for aa:bb:cc:dd:ee:ff" not in caplog.text  # WHY: this success line was false.


def test_organization_services_503_returns_empty_and_suppresses_success(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An organization-service 503 must not report a successful zero-service fetch."""
    fake_resolver = MagicMock()  # WHY: isolate the helper from the live application state.
    fake_resolver.apisession = MagicMock()  # WHY: satisfy the SDK call signature without live auth.
    fake_resolver.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"  # WHY: fix the target org.
    with caplog.at_level(logging.INFO, logger="src.api.api_fetch_utils"):  # WHY: capture success and failure logs.
        with patch("src.api.api_fetch_utils.SourceDependencyResolver", fake_resolver):
            with patch("src.api.api_fetch_utils.mistapi.api.v1.orgs.services.listOrgServices") as sdk_call:
                sdk_call.return_value = _FailedResponse()  # WHY: feed a 503 response with an empty payload.
                result = APIFetchUtils.organization_services()  # WHY: drive the real product function.
    assert result == []  # WHY: the existing failure contract for this helper is an empty list.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Successfully retrieved 0 organization services" not in caplog.text  # WHY: success would be false.


def test_fetch_single_site_setting_503_returns_none_and_suppresses_success(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A site-setting 503 must not report a successful configuration fetch."""
    site = {"id": "site-1", "name": "Alpha"}  # WHY: real function reads both fields from a site row.
    with caplog.at_level(logging.INFO, logger="src.api.api_fetch_utils"):  # WHY: capture success and failure logs.
        with patch("src.api.api_fetch_utils.mistapi.api.v1.sites.setting.getSiteSetting") as sdk_call:
            sdk_call.return_value = _FailedResponse()  # WHY: feed a 503 response with an empty payload.
            result = APIFetchUtils._fetch_single_site_setting(MagicMock(), site)  # WHY: drive the real helper.
    assert result is None  # WHY: the existing failure contract for this helper is None.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "! Fetched config for site: Alpha (ID: site-1)" not in caplog.text  # WHY: this success line was false.


def test_organization_tenants_503_returns_empty_and_suppresses_success(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An organization-network 503 must not report a successful zero-tenant fetch."""
    tenant_fetch = APITenantFetchUtils(MagicMock(), lambda: "org-1")  # WHY: use the real class with fixed inputs.
    with caplog.at_level(logging.INFO, logger="src.api.tenant_fetch"):  # WHY: capture success and failure logs.
        with patch("src.api.tenant_fetch.mistapi.api.v1.orgs.networks.listOrgNetworks") as sdk_call:
            sdk_call.return_value = _FailedResponse()  # WHY: feed a 503 response with an empty payload.
            result = tenant_fetch.organization_tenants()  # WHY: drive the real product method.
    assert result == []  # WHY: the existing failure contract for this helper is an empty list.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Found 0 unique org-network tenants" not in caplog.text  # WHY: this success line would be false.


def test_site_tenants_503_returns_empty_and_suppresses_success(caplog: pytest.LogCaptureFixture) -> None:
    """A site-network 503 must not report a successful zero-tenant fetch."""
    tenant_fetch = APITenantFetchUtils(MagicMock(), lambda: "org-1")  # WHY: use the real class with fixed inputs.
    with caplog.at_level(logging.INFO, logger="src.api.tenant_fetch"):  # WHY: capture success and failure logs.
        with patch("src.api.tenant_fetch.mistapi.api.v1.sites.networks.listSiteNetworksDerived") as sdk_call:
            sdk_call.return_value = _FailedResponse()  # WHY: feed a 503 response with an empty payload.
            result = tenant_fetch.site_tenants("site-1")  # WHY: drive the real product method.
    assert result == []  # WHY: the existing failure contract for this helper is an empty list.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Found 0 unique site-network tenants" not in caplog.text  # WHY: this success line would be false.


def test_get_all_ap_macs_from_site_503_returns_empty_and_suppresses_success(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """An AP-list 503 must not report a successful zero-AP fetch."""
    with caplog.at_level(logging.INFO, logger="src.device.device_utils"):  # WHY: capture success and failure logs.
        with patch("src.device.device_utils.mistapi.api.v1.sites.devices.listSiteDevices") as sdk_call:
            sdk_call.return_value = _FailedResponse()  # WHY: feed a 503 response with an empty payload.
            result = DeviceUtils.get_all_ap_macs_from_site("site-1")  # WHY: drive the real product function.
    assert result == []  # WHY: the existing failure contract for this helper is an empty list.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Found 0 AP MACs at site" not in caplog.text  # WHY: this success line would be false.


def test_resolve_org_id_via_prompt_503_exits_and_suppresses_success(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An organization-selection 503 must not continue as if the list is valid."""
    monkeypatch.setattr(ConfigUtils, "_apisession", MagicMock())  # WHY: reach the interactive SDK call safely.
    monkeypatch.setattr("sys.argv", ["MistHelper.py"])  # WHY: avoid the non-interactive preflight exit path.
    with caplog.at_level(logging.INFO, logger="src.config.config_utils"):  # WHY: capture prompt and failure logs.
        with patch("src.config.config_utils.mistapi.cli.select_org", return_value=_FailedResponse()):
            with pytest.raises(SystemExit) as exit_info:  # WHY: existing empty-org failure path exits.
                ConfigUtils._resolve_org_id_via_prompt()  # WHY: drive the real product function.
    assert exit_info.value.code == 1  # WHY: the existing failure contract uses exit code 1.
    assert _has_status_at_problem_level(caplog)  # WHY: the operator must see the exact 503 status.
    assert "Use the first selected org" not in caplog.text  # WHY: the helper must not proceed after the 503.
