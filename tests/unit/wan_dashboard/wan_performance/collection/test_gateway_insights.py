"""Verify bounded gateway insight catalog and response validation."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from src.interfaces.wan_performance.collection import snapshot_client
from src.interfaces.wan_performance.collection.snapshot_client import GatewayInsights
from src.interfaces.wan_performance.domain.identity import GatewayIdentity, SiteIdentity


class FakeAdmission:
    """Count or refuse gateway insight requests."""

    def __init__(self, fail_on: int | None = None) -> None:
        """Set an optional request number to refuse."""
        self.fail_on = fail_on  # Keep the test outcome deterministic.
        self.checks = 0  # Count admission attempts.

    def check(self) -> None:
        """Refuse the selected request before transport."""
        self.checks += 1  # Record the current request.
        if self.fail_on == self.checks:  # Model a lost lease.
            raise ConnectionError("lease expired")  # Stop before API access.


class TestGatewayInsights:
    """Test catalog-backed collection with mocked Mist SDK calls."""

    def test_collect_uses_device_uuid_and_named_metric_arrays(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Use the returned device UUID and catalog units."""
        device_id = str(uuid4())  # Give the gateway a source UUID.
        target = GatewayIdentity(SiteIdentity("org-one", "site-one"), "gw-one")  # Select one gateway.
        monkeypatch.setattr(
            snapshot_client,
            "listOrgDevicesStats",
            lambda *args, **kwargs: SimpleNamespace(
                status_code=200, data=[{"id": device_id, "org_id": "org-one", "site_id": "site-one", "mac": "gw-one"}]
            ),
        )  # Mock source discovery.
        catalog = {
            name: {
                "scopes": ["gateway"],
                "type": "timeseries",
                "unit": "bit/s",
                "intervals": {"1h": {"interval": 3600, "max_age": 3600}},
            }
            for name in ("rx_bps", "tx_bps")
        }  # Define valid metrics.
        monkeypatch.setattr(
            snapshot_client, "listInsightMetrics", lambda session: SimpleNamespace(status_code=200, data=catalog)
        )  # Mock catalog.

        def insight(session: object, site_id: str, returned_id: str, metrics: str, **query: str) -> object:
            start = int(query["start"])  # Read the request start.
            timestamp = datetime.fromtimestamp(start, UTC).isoformat()  # Match one source sample.
            assert returned_id == device_id  # Verify the source UUID.
            return SimpleNamespace(
                status_code=200,
                data={
                    "start": start,
                    "end": int(query["end"]),
                    "interval": 3600,
                    "next": False,
                    "rt": [timestamp],
                    "rx_bps": [0],
                    "tx_bps": [8],
                },
            )  # Return aligned arrays.

        monkeypatch.setattr(snapshot_client, "getSiteInsightMetricsForGateway", insight)  # Mock the SDK insight call.
        result = GatewayInsights(object(), FakeAdmission()).collect("org-one", target)  # Collect one bounded hour.
        assert len(result["samples"]) == 2  # Keep both directional rates.
        assert result["samples"][0]["value"] == 0  # Preserve a measured zero.
        assert result["samples"][1]["value"] == 8  # Preserve the transmit rate.
        assert result["partial"] is False  # Mark the complete hourly sample.

    def test_discovery_errors_are_not_empty_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Reject missing or ambiguous gateway discovery."""
        target = GatewayIdentity(SiteIdentity("org-one", "site-one"), "gw-one")  # Select a gateway.
        monkeypatch.setattr(
            snapshot_client, "listOrgDevicesStats", lambda *args, **kwargs: SimpleNamespace(status_code=200, data=[])
        )  # Mock no device.
        with pytest.raises(ValueError, match="one matching"):  # Require explicit discovery failure.
            GatewayInsights(object(), FakeAdmission()).collect("org-one", target)  # Refuse missing device.

    def test_catalog_mismatch_is_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Reject a metric without the required gateway interval."""
        target = GatewayIdentity(SiteIdentity("org-one", "site-one"), "gw-one")  # Select a gateway.
        monkeypatch.setattr(
            snapshot_client,
            "listOrgDevicesStats",
            lambda *args, **kwargs: SimpleNamespace(
                status_code=200,
                data=[{"id": str(uuid4()), "org_id": "org-one", "site_id": "site-one", "mac": "gw-one"}],
            ),
        )  # Mock discovery.
        bad_catalog = {
            "rx_bps": {"scopes": ["gateway"], "type": "timeseries", "unit": "bit/s", "intervals": {}}
        }  # Omit the interval.
        monkeypatch.setattr(
            snapshot_client, "listInsightMetrics", lambda session: SimpleNamespace(status_code=200, data=bad_catalog)
        )  # Mock catalog.
        with pytest.raises(ValueError, match="one-hour window"):  # Require catalog contract validation.
            GatewayInsights(object(), FakeAdmission()).collect("org-one", target)  # Refuse unsupported metric.

    def test_admission_failure_prevents_discovery(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Stop before gateway discovery if request admission fails."""
        calls: list[bool] = []  # Record transport attempts.
        monkeypatch.setattr(
            snapshot_client, "listOrgDevicesStats", lambda *args, **kwargs: calls.append(True)
        )  # Track discovery.
        target = GatewayIdentity(SiteIdentity("org-one", "site-one"), "gw-one")  # Select a gateway.
        with pytest.raises(ConnectionError, match="lease"):  # Require fail-closed admission.
            GatewayInsights(object(), FakeAdmission(fail_on=1)).collect("org-one", target)  # Refuse the request.
        assert not calls  # Prove no Mist SDK method ran.
