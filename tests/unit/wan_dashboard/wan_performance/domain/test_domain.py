"""Verify WAN identity and measurement contracts."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from src.interfaces.wan_performance.domain.identity import (
    CircuitIdentity,
    GatewayIdentity,
    PeerPathIdentity,
    SiteIdentity,
)
from src.interfaces.wan_performance.domain.measurement import HourlyMeasurement, MetricMeasurement


class TestWanDomain:
    """Keep domain validation independently testable."""

    def test_identity_keys_keep_each_source_parent(self) -> None:
        """Preserve parent and source identifiers in natural keys."""
        site = SiteIdentity("org-one", "site-one")  # Keep the organization and site together.
        gateway = GatewayIdentity(site, "aabbccddeeff")  # Preserve the source gateway MAC.
        circuit = CircuitIdentity(gateway, "ge-0/0/0")  # Preserve the exact source port name.
        peer = PeerPathIdentity(gateway, "ge-0/0/0", "ge-0/0/1", "11:22:33:44:55:66", "tunnel-one")  # Keep full path.
        assert circuit.natural_key == ("org-one", "site-one", "aabbccddeeff", "ge-0/0/0")  # Verify source identity.
        assert peer.natural_key[-4:] == ("ge-0/0/0", "ge-0/0/1", "11:22:33:44:55:66", "tunnel-one")  # Keep peer scope.

    @pytest.mark.parametrize("value", ["", "../site", "bad/value", "x" * 129])  # Cover unsafe identifiers.
    def test_invalid_source_identifiers_are_rejected(self, value: str) -> None:
        """Reject unsafe or oversized values before route use."""
        with pytest.raises(ValueError):  # Require explicit validation failure.
            SiteIdentity("org-one", value)  # Reject the invalid site value.

    def test_hourly_measurement_serializes_utc_and_freezes_metrics(self) -> None:
        """Preserve UTC identity and prevent cross-consumer mutation."""
        hour = datetime(2024, 1, 1, 12, tzinfo=UTC)  # Use an exact UTC hour.
        metric = MetricMeasurement(0, "bit/s", sample_count=1)  # Preserve a measured zero.
        record = HourlyMeasurement(
            SiteIdentity("org-one", "site-one"), hour, hour, {"rx": metric}, "live"
        )  # Build record.
        assert record.to_dict()["hour_start_utc"] == hour.isoformat()  # Keep canonical UTC text.
        with pytest.raises(TypeError):  # Require immutable metric storage.
            record.metrics["tx"] = metric  # type: ignore[index]  # Reject mutation after construction.

    @pytest.mark.parametrize(
        "value", [datetime(2024, 1, 1, 12), datetime(2024, 1, 1, 12, tzinfo=timezone(timedelta(hours=2)))]
    )  # Cover naive and non-UTC.
    def test_non_utc_hour_is_rejected(self, value: datetime) -> None:
        """Reject local or offset hours as natural interval keys."""
        with pytest.raises(ValueError):  # Require an explicit UTC failure.
            HourlyMeasurement(
                SiteIdentity("org-one", "site-one"),
                value,
                datetime(2024, 1, 1, 13, tzinfo=UTC),
                {"rx": MetricMeasurement(1, "bit/s")},
                "live",
            )  # Keep UTC invariant.

    @pytest.mark.parametrize("value", [float("nan"), float("inf"), True])  # Cover non-finite and boolean values.
    def test_invalid_metric_values_are_rejected(self, value: float | bool) -> None:
        """Reject values that cannot represent a finite WAN measurement."""
        with pytest.raises(ValueError):  # Require domain validation.
            MetricMeasurement(value, "bit/s")  # Reject invalid source data.
