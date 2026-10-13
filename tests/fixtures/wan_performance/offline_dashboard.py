"""Build historical synthetic dashboard records without service clients."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.interfaces.portals.wan_performance.domain.identity import (
    CircuitIdentity,
    GatewayIdentity,
    PeerPathIdentity,
    SiteIdentity,
)
from src.interfaces.portals.wan_performance.domain.measurement import HourlyMeasurement, MetricMeasurement


@dataclass(frozen=True, slots=True)
class OfflineDashboard:
    """Group synthetic route identities and measurements for page previews."""

    circuit: CircuitIdentity
    peer_path: PeerPathIdentity
    measurements: tuple[HourlyMeasurement, ...]

    @property
    def site(self) -> SiteIdentity:
        """Expose the site identity through the circuit parent chain."""
        return self.circuit.gateway.site

    @property
    def provenance(self) -> str:
        """Keep the fixture origin explicit at the dashboard boundary."""
        return "synthetic"


class OfflineDashboardFactory:
    """Create fixed historical records without starting runtime clients."""

    @classmethod
    def build(cls) -> OfflineDashboard:
        """Build route identities and synthetic measurements for preview tests."""
        circuit, peer_path = cls._build_identities()
        hour_start = datetime(2024, 1, 1, 12, tzinfo=UTC)
        collected_at = hour_start + timedelta(hours=1)
        measurements = (
            cls._build_circuit_measurement(circuit, hour_start, collected_at),
            cls._build_peer_measurement(peer_path, hour_start, collected_at),
        )
        return OfflineDashboard(circuit, peer_path, measurements)

    @staticmethod
    def _build_identities() -> tuple[CircuitIdentity, PeerPathIdentity]:
        """Build documented synthetic route identities in their parent context."""
        site = SiteIdentity(org_id="synthetic-org-4200", site_id="11111111-1111-1111-1111-111111111111")
        gateway = GatewayIdentity(site=site, gateway_id="aabbccddeeff")
        circuit = CircuitIdentity(gateway=gateway, port_name="ge-0/0/1")
        peer_path = PeerPathIdentity(
            gateway=gateway,
            port_name=circuit.port_name,
            peer_mac="11:22:33:44:55:66",
            tunnel_identity="synthetic-tunnel-4200",
        )
        return circuit, peer_path

    @staticmethod
    def _build_circuit_measurement(
        circuit: CircuitIdentity,
        hour_start: datetime,
        collected_at: datetime,
    ) -> HourlyMeasurement:
        """Build one synthetic circuit record with explicit units."""
        metrics = {
            "utilization": MetricMeasurement(
                value=42.5,
                unit="percent",
                sample_count=4,
                coverage_fraction=1.0,
            ),
            "receive_bandwidth": MetricMeasurement(value=80.0, unit="megabits_per_second"),
            "transmit_bandwidth": MetricMeasurement(value=35.0, unit="megabits_per_second"),
        }
        return HourlyMeasurement(circuit, hour_start, collected_at, metrics, "synthetic")

    @staticmethod
    def _build_peer_measurement(
        peer_path: PeerPathIdentity,
        hour_start: datetime,
        collected_at: datetime,
    ) -> HourlyMeasurement:
        """Build one synthetic peer record with explicit quality units."""
        metrics = {
            "packet_loss": MetricMeasurement(value=0.2, unit="percent", sample_count=4),
            "latency": MetricMeasurement(value=24.0, unit="milliseconds", sample_count=4),
            "jitter": MetricMeasurement(value=3.5, unit="milliseconds", sample_count=4),
        }
        return HourlyMeasurement(peer_path, hour_start, collected_at, metrics, "synthetic")
