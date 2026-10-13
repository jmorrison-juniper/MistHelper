"""Build a labeled WAN preview without Mist, storage, or worker clients."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.interfaces.portals.wan_performance.domain.identity import (
    CircuitIdentity,
    GatewayIdentity,
    PeerPathIdentity,
    SiteIdentity,
)
from src.interfaces.portals.wan_performance.domain.measurement import HourlyMeasurement, MetricMeasurement

logger = logging.getLogger(__name__)  # Keep offline preview records on the feature logger.


@dataclass(frozen=True, slots=True)
class OfflineDashboard:
    """Group synthetic route identities and measurements for portal preview pages."""

    circuit: CircuitIdentity
    peer_path: PeerPathIdentity
    measurements: tuple[HourlyMeasurement, ...]

    @property
    def site(self) -> SiteIdentity:
        """Expose the site identity through its circuit parent."""
        return self.circuit.gateway.site  # Keep route identity access direct and immutable.

    @property
    def provenance(self) -> str:
        """Keep the fixture origin explicit at the dashboard boundary."""
        return "synthetic"  # Prevent the preview from appearing to hold live data.


class OfflinePreviewFactory:
    """Create fixed synthetic records without starting runtime clients."""

    @classmethod
    def build(cls) -> OfflineDashboard:
        """Build route identities and records for the offline preview."""
        logger.info("Building the labeled synthetic WAN preview")  # Log before the data transform.
        circuit, peer_path = cls._build_identities()  # Build isolated identities for route links.
        hour_start = datetime(2024, 1, 1, 12, tzinfo=UTC)  # Use a fixed historical UTC hour.
        collected_at = hour_start + timedelta(hours=1)  # End the synthetic record at the next hour boundary.
        measurements = (  # Keep the preview limited to independently authored sample metrics.
            cls._build_circuit_measurement(circuit, hour_start, collected_at),
            cls._build_peer_measurement(peer_path, hour_start, collected_at),
        )
        dashboard = OfflineDashboard(circuit, peer_path, measurements)  # Group sample records for all four pages.
        logger.debug("Built %d synthetic WAN preview records", len(measurements))  # Summarize the sample result.
        return dashboard  # Return only synthetic records with explicit identities.

    @staticmethod
    def _build_identities() -> tuple[CircuitIdentity, PeerPathIdentity]:
        """Build synthetic route identities in their site and gateway context."""
        site = SiteIdentity(  # Mark sample identifiers with an unmistakable organization value.
            org_id="synthetic-org-4200",
            site_id="11111111-1111-1111-1111-111111111111",
        )
        gateway = GatewayIdentity(site=site, gateway_id="aabbccddeeff")  # Scope the sample gateway to its site.
        circuit = CircuitIdentity(gateway=gateway, port_name="ge-0/0/1")  # Preserve a slash-bearing port identity.
        peer_path = PeerPathIdentity(  # Give the sample VPN path a distinct peer and tunnel identity.
            gateway=gateway,
            port_name=circuit.port_name,
            peer_mac="11:22:33:44:55:66",
            tunnel_identity="synthetic-tunnel-4200",
        )
        return circuit, peer_path  # Return the exact identities used by the detail routes.

    @staticmethod
    def _build_circuit_measurement(
        circuit: CircuitIdentity,
        hour_start: datetime,
        collected_at: datetime,
    ) -> HourlyMeasurement:
        """Build one synthetic circuit record with explicit metric units."""
        metrics = {  # Keep sample values separate from unverified live formulas.
            "utilization": MetricMeasurement(
                value=42.5,
                unit="percent",
                sample_count=4,
                coverage_fraction=1.0,
            ),
            "receive_bandwidth": MetricMeasurement(value=80.0, unit="megabits_per_second"),
            "transmit_bandwidth": MetricMeasurement(value=35.0, unit="megabits_per_second"),
        }
        return HourlyMeasurement(circuit, hour_start, collected_at, metrics, "synthetic")  # Mark every sample.

    @staticmethod
    def _build_peer_measurement(
        peer_path: PeerPathIdentity,
        hour_start: datetime,
        collected_at: datetime,
    ) -> HourlyMeasurement:
        """Build one synthetic peer record with explicit quality units."""
        metrics = {  # Keep sample quality values separate from live measurements.
            "packet_loss": MetricMeasurement(value=0.2, unit="percent", sample_count=4),
            "latency": MetricMeasurement(value=24.0, unit="milliseconds", sample_count=4),
            "jitter": MetricMeasurement(value=3.5, unit="milliseconds", sample_count=4),
        }
        return HourlyMeasurement(peer_path, hour_start, collected_at, metrics, "synthetic")  # Mark every sample.
