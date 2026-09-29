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
