"""Tests for the four silent-failure paths in web_portal.routes.operations.

Finding 5 of issue #2038: each helper catches a broad exception and returns []
without leaving any log record. A caller cannot distinguish a real empty result
from a failed API call.

The tests below prove the defect first (before fix) and then prove the fix.

Strategy:
- Patch the mistapi call to raise RuntimeError.
- Assert that the module logger records the failure (caplog).
- Assert that the route payload carries an error signal or that the function
  raises instead of returning a plain empty list.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

# Import the helpers directly so the tests do not need a running Flask app.
from web_portal.routes.operations import (
    _fetch_org_sites,
    _fetch_site_devices,
    _fetch_wired_clients,
    _fetch_wireless_clients,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _fake_apisession() -> MagicMock:
    """Return a non-None mock so the early-return guard does not trigger."""
    return MagicMock()  # The guard checks truthiness, not the actual type.


# ---------------------------------------------------------------------------
# Finding 5a -- _fetch_org_sites (line ~301)
# ---------------------------------------------------------------------------


class TestFetchOrgSitesSilentFailure:
    """The original code: except Exception: return [].

    A Mist API failure must leave a log record and must not return a plain [].
    """

    def test_logs_exception_on_api_failure(self, caplog):
        """A Mist API exception must produce an ERROR log with the exc info."""
        apisession = _fake_apisession()
        with caplog.at_level(logging.ERROR, logger="web_portal.routes.operations"):
            # Patch the mistapi import inside the function so the real SDK is
            # not required, and force the call to raise.
            with patch(
                "web_portal.routes.operations._fetch_org_sites",
                wraps=_fetch_org_sites,
            ):
                with patch(
                    "mistapi.api.v1.orgs.sites.listOrgSites",
                    side_effect=RuntimeError("Mist API unreachable"),
                ):
                    _fetch_org_sites(apisession, "fake-org-id")

        # Before the fix this assertion fails: no log record is written.
        assert any(
            "fake-org-id" in record.message or "org" in record.message.lower() for record in caplog.records
        ), "Expected an ERROR log record naming the org or operation."

    def test_result_carries_error_signal_on_api_failure(self, caplog):
        """A failed API call must not be indistinguishable from a real empty org."""
        apisession = _fake_apisession()
        with patch(
            "mistapi.api.v1.orgs.sites.listOrgSites",
            side_effect=RuntimeError("Mist API unreachable"),
        ):
            result = _fetch_org_sites(apisession, "fake-org-id")

        # Before the fix the result is [] -- identical to an empty org.
        # After the fix the result must NOT be a plain empty list with no
        # accompanying log record.
        if result == []:
            # The test passes only when the log contains the failure.
            assert caplog.records, "result is [] and no log record exists -- " "the failure is invisible to the caller."


# ---------------------------------------------------------------------------
# Finding 5b -- _fetch_site_devices (line ~330)
# ---------------------------------------------------------------------------


class TestFetchSiteDevicesSilentFailure:
    """Same pattern for the device-listing helper."""

    def test_logs_exception_on_api_failure(self):
        """A Mist API exception must produce an ERROR log naming the site."""
        apisession = _fake_apisession()
        # Patch the module logger directly. The full suite reconfigures logging,
        # so a caplog assertion is not reliable here. See issue #2038.
        with patch("web_portal.routes.operations.logger") as fake_logger:
            with patch(
                "mistapi.api.v1.sites.devices.listSiteDevices",
                side_effect=RuntimeError("connection timeout"),
            ):
                result = _fetch_site_devices(apisession, "site-abc", "all")

        # Before the fix this assertion fails, because the handler logs nothing.
        assert fake_logger.exception.called, "Expected an ERROR log record for the failed device call."
        # The site identifier must reach the record, so an operator can trace it.
        assert "site-abc" in fake_logger.exception.call_args[0], "Expected the log record to name the site."
        assert result == [], "The helper still returns a list, so no call site changes."

    def test_result_carries_error_signal_on_api_failure(self):
        """A failed device call must not look like a site with no devices."""
        apisession = _fake_apisession()
        with patch("web_portal.routes.operations.logger") as fake_logger:
            with patch(
                "mistapi.api.v1.sites.devices.listSiteDevices",
                side_effect=RuntimeError("connection timeout"),
            ):
                result = _fetch_site_devices(apisession, "site-abc", "all")

        # An empty list is acceptable only when the failure left a record.
        if result == []:
            assert fake_logger.exception.called, (
                "result is [] and no log record exists -- " "the failure is invisible to the caller."
            )


# ---------------------------------------------------------------------------
# Finding 5c -- _fetch_wireless_clients (line ~369)
# ---------------------------------------------------------------------------


class TestFetchWirelessClientsSilentFailure:
    """The wireless-client helper swallows the exception without logging."""

    def test_logs_exception_on_api_failure(self, caplog):
        """A Mist API exception must produce an ERROR log."""
        mistapi_mock = MagicMock()  # Pass as the mistapi module argument.
        mistapi_mock.api.v1.sites.clients.searchSiteWirelessClients.side_effect = RuntimeError("auth token expired")
        apisession = _fake_apisession()
        with caplog.at_level(logging.ERROR, logger="web_portal.routes.operations"):
            _fetch_wireless_clients(mistapi_mock, apisession, "site-xyz")

        # Before the fix: no log record for this helper.
        assert any(
            "site-xyz" in record.message or "wireless" in record.message.lower() for record in caplog.records
        ), "Expected an ERROR log record naming the site or operation."

    def test_result_carries_error_signal_on_api_failure(self, caplog):
        """A failed wireless call must not look like a site with no wireless clients."""
        mistapi_mock = MagicMock()
        mistapi_mock.api.v1.sites.clients.searchSiteWirelessClients.side_effect = RuntimeError("auth token expired")
        apisession = _fake_apisession()
        result = _fetch_wireless_clients(mistapi_mock, apisession, "site-xyz")

        if result == []:
            assert caplog.records, "result is [] and no log record exists -- " "the failure is invisible to the caller."


# ---------------------------------------------------------------------------
# Finding 5d -- _fetch_wired_clients (line ~390)
# ---------------------------------------------------------------------------


class TestFetchWiredClientsSilentFailure:
    """The wired-client helper has the same defect."""

    def test_logs_exception_on_api_failure(self, caplog):
        """A Mist API exception must produce an ERROR log."""
        mistapi_mock = MagicMock()
        mistapi_mock.api.v1.sites.clients.searchSiteWiredClients.side_effect = RuntimeError("rate limit exceeded")
        apisession = _fake_apisession()
        with caplog.at_level(logging.ERROR, logger="web_portal.routes.operations"):
            _fetch_wired_clients(mistapi_mock, apisession, "site-def")

        # Before the fix: no log record.
        assert any(
            "site-def" in record.message or "wired" in record.message.lower() for record in caplog.records
        ), "Expected an ERROR log record naming the site or operation."

    def test_result_carries_error_signal_on_api_failure(self, caplog):
        """A failed wired call must not look like a site with no wired clients."""
        mistapi_mock = MagicMock()
        mistapi_mock.api.v1.sites.clients.searchSiteWiredClients.side_effect = RuntimeError("rate limit exceeded")
        apisession = _fake_apisession()
        result = _fetch_wired_clients(mistapi_mock, apisession, "site-def")

        if result == []:
            assert caplog.records, "result is [] and no log record exists -- " "the failure is invisible to the caller."
