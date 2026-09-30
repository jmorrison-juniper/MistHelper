"""Unit tests for the rogue PCI evidence client."""

from types import SimpleNamespace  # Build small fake dependency objects.
from unittest.mock import patch  # Patch the Mist SDK functions without network calls.

from src.reports.rogue_pci_evidence.client import RoguePciEvidenceClient  # Import the client under test.


class _FakeRateLimiter:
    """Record pacer calls and return a zero delay."""

    calls = 0  # Count pacer calls across one test.

    @classmethod
    def get_rate_limited_delay(cls, smoothed, apisession, cache):  # Match the shared pacer signature.
        """Return a zero delay while recording one pacing event."""
        cls.calls += 1  # Count the pacing call.
        return smoothed, 0.0  # Avoid sleeping during tests.


def test_site_settings_uses_one_pacer_call_per_site():
    """The settings pass paces one read per site."""
    _FakeRateLimiter.calls = 0  # Reset the class counter for this test.
    deps = SimpleNamespace(RateLimitingUtils=_FakeRateLimiter, _api_usage_cache={})  # Build fake deps.
    sites = [{"id": "site-1"}, {"id": "site-2"}]  # Provide two sites for the cost contract.
    client = RoguePciEvidenceClient(object(), "org-1", deps=deps)  # Build the client with fake deps.
    fake_response = SimpleNamespace(data={"rogue": {"enabled": True}})  # Return a minimal setting payload.
    with patch("src.reports.rogue_pci_evidence.client.time.sleep") as sleep_mock:  # Avoid real sleep calls.
        with patch(
            "src.reports.rogue_pci_evidence.client.mistapi.api.v1.sites.setting.getSiteSetting",
            return_value=fake_response,
        ) as api_mock:  # Patch Mist.
            result = client.list_site_settings(sites)  # Read settings through the client.
    assert _FakeRateLimiter.calls == 2  # Verify one pacer call for each site.
    assert api_mock.call_count == 2  # Verify one settings call for each site.
    assert sleep_mock.call_count == 2  # Verify the client obeyed the pacer delay.
    assert set(result) == {"site-1", "site-2"}  # Verify settings are keyed by site id.


def test_org_rogue_events_uses_available_org_event_search():
    """The client reads rogue event evidence from the available org event endpoint."""
    client = RoguePciEvidenceClient(object(), "org-1")  # Build the client with default dependencies.
    fake_response = SimpleNamespace(data={"results": [{"ssid": "CorpWiFi"}]})  # Return a minimal event page.
    with patch(
        "src.reports.rogue_pci_evidence.client.mistapi.get_all", return_value=[{"ssid": "CorpWiFi"}]
    ):  # Patch paging.
        with patch(
            "src.reports.rogue_pci_evidence.client.mistapi.api.v1.orgs.events.searchOrgEvents",
            return_value=fake_response,
        ) as api_mock:  # Patch Mist.
            rows = client.list_org_rogue_events()  # Read the available event rows.
    assert rows == [{"ssid": "CorpWiFi"}]  # Verify rows return from the pager.
    api_mock.assert_called_once()  # Verify the org event endpoint was called.


def test_org_rogue_events_returns_empty_rows_on_http_4xx():
    """The client returns no event rows when Mist returns an HTTP 4xx status."""
    client = RoguePciEvidenceClient(object(), "org-1")  # Build the client with default dependencies.
    fake_response = SimpleNamespace(status_code=404, data={"message": "not found"})  # Simulate a client error.
    with patch("src.reports.rogue_pci_evidence.client.mistapi.get_all") as pager_mock:  # Detect bad paging.
        with patch(
            "src.reports.rogue_pci_evidence.client.mistapi.api.v1.orgs.events.searchOrgEvents",
            return_value=fake_response,
        ):  # Patch Mist with a failed response.
            rows = client.list_org_rogue_events()  # Read the failed event response.
    assert rows == []  # Verify the client drops rows from a failed response.
    pager_mock.assert_not_called()  # Verify the failed response is not paged.


def test_site_settings_skips_failed_site_on_http_5xx():
    """The client skips one site setting when Mist returns an HTTP 5xx status."""
    _FakeRateLimiter.calls = 0  # Reset the pacer counter for this test.
    deps = SimpleNamespace(RateLimitingUtils=_FakeRateLimiter, _api_usage_cache={})  # Build fake deps.
    sites = [{"id": "site-1"}]  # Provide one site for the failed settings read.
    client = RoguePciEvidenceClient(object(), "org-1", deps=deps)  # Build the client with fake deps.
    fake_response = SimpleNamespace(status_code=503, data={"message": "unavailable"})  # Simulate a server error.
    with patch("src.reports.rogue_pci_evidence.client.time.sleep"):  # Avoid real pacer sleep.
        with patch(
            "src.reports.rogue_pci_evidence.client.mistapi.api.v1.sites.setting.getSiteSetting",
            return_value=fake_response,
        ):  # Patch Mist with a failed response.
            result = client.list_site_settings(sites)  # Read settings through the client.
    assert result == {}  # Verify failed settings are omitted for error-row mapping.
    assert _FakeRateLimiter.calls == 1  # Verify the pacer still runs before the failed read.
