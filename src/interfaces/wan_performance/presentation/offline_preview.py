"""Build a labeled WAN preview without Mist, storage, or worker clients."""

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from types import MappingProxyType

from src.interfaces.wan_performance.domain.identity import (
    CircuitIdentity,
    GatewayIdentity,
    PeerPathIdentity,
    SiteIdentity,
)
from src.interfaces.wan_performance.domain.measurement import HourlyMeasurement, MetricMeasurement

logger = logging.getLogger(__name__)  # Keep offline preview records on the feature logger.


@dataclass(frozen=True, slots=True)
class OfflineDashboard:
    """Group synthetic route identities and measurements for portal preview pages."""

    @dataclass(frozen=True, slots=True)
    class Metric:
        """Keep one synthetic dashboard value and its display unit."""

        label: str
        value: str
        unit: str = ""
        scale_max: float = 100

    @dataclass(frozen=True, slots=True)
    class Table:
        """Keep one synthetic detail table and its visible empty state."""

        title: str
        columns: tuple[str, ...]
        rows: tuple[tuple[str, ...], ...]
        empty_message: str = "No synthetic records are available."

    @dataclass(frozen=True, slots=True)
    class Series:
        """Keep synthetic chart samples separate from hourly history."""

        label: str
        unit: str
        values: tuple[float, ...]
        color: str

    @dataclass(frozen=True, slots=True)
    class Chart:
        """Keep chart labels and scale with synthetic samples."""

        title: str
        subtitle: str
        labels: tuple[str, ...]
        series: tuple["OfflineDashboard.Series", ...]
        scale: tuple[float, float]
        kind: str = "line"
        bar_colors: tuple[str, ...] = ()
        reference_lines: tuple[tuple[str, float, str], ...] = ()
        empty_message: str = ""

    @dataclass(frozen=True, slots=True)
    class Page:
        """Group KPI cards, gauges, tables, and charts for one route."""

        kpis: tuple["OfflineDashboard.Metric", ...]
        gauges: tuple["OfflineDashboard.Metric", ...]
        tables: tuple["OfflineDashboard.Table", ...]
        charts: tuple["OfflineDashboard.Chart", ...]

    circuit: CircuitIdentity
    peer_path: PeerPathIdentity
    measurements: tuple[HourlyMeasurement, ...]
    site_name: str
    remote_site_name: str
    pages: Mapping[str, Page]

    def __post_init__(self) -> None:
        """Prevent a caller from changing a synthetic page after construction."""
        object.__setattr__(self, "pages", MappingProxyType(dict(self.pages)))

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
        dashboard = OfflineDashboard(
            circuit,
            peer_path,
            measurements,
            "Store 100 (synthetic)",
            "Remote Store (synthetic)",
            cls._build_pages(),
        )  # Group sample records and screenshot-shaped pages for the preview.
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
            peer_port_id="ge-0/0/2",
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
                value=12.5,
                unit="percent",
                sample_count=1,
                coverage_fraction=None,
            ),
            "receive_bandwidth": MetricMeasurement(value=125.0, unit="megabits_per_second"),
            "transmit_bandwidth": MetricMeasurement(value=50.0, unit="megabits_per_second"),
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
            "packet_loss": MetricMeasurement(value=0.25, unit="percent", sample_count=1),
            "latency": MetricMeasurement(value=33.3, unit="milliseconds", sample_count=1),
            "jitter": MetricMeasurement(value=4.5, unit="milliseconds", sample_count=1),
        }
        return HourlyMeasurement(peer_path, hour_start, collected_at, metrics, "synthetic")  # Mark every sample.

    @classmethod
    def _build_pages(cls) -> Mapping[str, OfflineDashboard.Page]:
        """Build the four source-shaped views from synthetic dashboard values."""
        logger.info("Building four synthetic WAN dashboard page models.")
        pages = {
            "overview": cls._overview_page(),
            "gateway": cls._gateway_page(),
            "port": cls._port_page(),
            "peer": cls._peer_page(),
        }
        logger.debug("Built %d synthetic WAN page models.", len(pages))
        return pages

    @classmethod
    def _overview_page(cls) -> OfflineDashboard.Page:
        """Build overview cards, tables, and chart panels."""
        return OfflineDashboard.Page(
            cls._overview_metrics(),
            (),
            cls._overview_tables(),
            cls._overview_charts(),
        )

    @classmethod
    def _overview_metrics(cls) -> tuple[OfflineDashboard.Metric, ...]:
        """Create the screenshot-aligned overview values as synthetic data."""
        rows = (
            ("Total Sites", "1", ""),
            ("Healthy", "1", ""),
            ("High Util", "0", ""),
            ("Critical", "0", ""),
            ("Failovers", "0", ""),
            ("Alerts", "0", ""),
            ("Gateways Online", "1", ""),
            ("Gateways Offline", "0", ""),
            ("Circuits Up", "1", ""),
            ("Down", "0", ""),
            ("Disabled", "0", ""),
            ("Above 80%", "0", ""),
            ("Avg Util", "12.5", "%"),
            ("Max Util", "12.5", "%"),
            ("Total BW", "1.0", "Gbps"),
            ("SLE Gateway", "-", ""),
            ("SLE WAN Link", "-", ""),
            ("SLE App", "-", ""),
            ("SLE Degraded", "0", ""),
            ("Alarms", "0", ""),
            ("Critical", "0", ""),
            ("VPN Peers", "0", ""),
            ("Paths Up", "0", ""),
            ("Paths Down", "0", ""),
            ("VPN Health", "-", "%"),
        )
        return tuple(OfflineDashboard.Metric(*row) for row in rows)

    @staticmethod
    def _overview_tables() -> tuple[OfflineDashboard.Table, ...]:
        """Create synthetic overview rankings and explicit empty result panels."""
        table = OfflineDashboard.Table
        return (
            table(
                "Top 10 Congested Circuits",
                ("Rank", "Site", "Port", "Speed (Mbps)", "Utilization %", "Status"),
                (("1", "Store 100 (synthetic)", "WAN 1", "1,000", "12.5", "Up"),),
            ),
            table("Active Alerts", ("Time (UTC)", "Severity", "Site", "Description"), ()),
            table(
                "SLE Degraded Sites (< 90%)",
                ("Site Name", "Gateway %", "WAN Link %", "App Health %"),
                (),
                "No synthetic degraded sites are available.",
            ),
        )

    @classmethod
    def _overview_charts(cls) -> tuple[OfflineDashboard.Chart, ...]:
        """Combine overview summaries with time trends and empty site plots."""
        return cls._overview_summary_charts() + cls._overview_time_charts()

    @staticmethod
    def _overview_summary_charts() -> tuple[OfflineDashboard.Chart, ...]:
        """Create synthetic region and utilization distribution panels."""
        chart = OfflineDashboard.Chart
        series = OfflineDashboard.Series
        return (
            chart(
                "Region Summary",
                "Mean circuit utilization by region.",
                ("Demo",),
                (series("Avg utilization", "%", (12.5,), "#20a44b"),),
                (0, 20),
                kind="bar",
            ),
            chart(
                "Utilization Distribution",
                "Synthetic circuit count by range.",
                ("0-1%", "1-5%", "5-10%", "10-25%", "25-50%", "50-70%", "70-90%", "90-100%"),
                (series("Circuits", "count", (0, 0, 0, 1, 0, 0, 0, 0), "#20a44b"),),
                (0, 2),
                kind="bar",
                bar_colors=("#20a44b", "#20a44b", "#20a44b", "#72797e", "#72797e", "#f2c230", "#ff8c00", "#f04454"),
            ),
        )

    @staticmethod
    def _overview_time_charts() -> tuple[OfflineDashboard.Chart, ...]:
        """Create synthetic time trends and clearly empty site-specific panels."""
        chart = OfflineDashboard.Chart
        return (
            chart(
                "Real-Time Utilization Trends (24h)",
                "Instantaneous synthetic utilization samples.",
                ("22:00",),
                (),
                (0, 100),
                reference_lines=(
                    ("70%", 70, "#f2c230"),
                    ("80%", 80, "#ff8c00"),
                    ("90%", 90, "#f04454"),
                ),
            ),
            chart(
                "Aggregate Throughput (24h)",
                "Total Mbps across all circuits.",
                ("0", "1", "2", "3", "4", "5", "6"),
                (),
                (0, 4),
                empty_message="Collecting data... Throughput history will appear after multiple refresh cycles.",
            ),
            chart(
                "Gateway Port Bandwidth Time-Series",
                "Select a site to view gateway bandwidth.",
                ("0", "1", "2", "3", "4", "5", "6"),
                (),
                (0, 4),
                empty_message="Select a site to view gateway bandwidth time-series.",
            ),
            chart(
                "VPN Peer Quality Time-Series",
                "Loss, latency, and jitter for the selected site.",
                ("0", "1", "2", "3", "4", "5", "6"),
                (),
                (0, 4),
                empty_message="Select a site to view VPN peer quality time-series.",
            ),
        )

    @staticmethod
    def _gateway_page() -> OfflineDashboard.Page:
        """Build gateway health cards, child tables, and trends."""
        metric = OfflineDashboard.Metric
        table = OfflineDashboard.Table
        series = OfflineDashboard.Series
        labels = ("22:20", "22:30", "22:40", "22:50", "23:00", "23:10")
        kpis = tuple(
            metric(*row)
            for row in (
                ("Ports Up", "1", ""),
                ("Ports Down", "0", ""),
                ("VPN Peers", "1", ""),
                ("CPU", "22.5", "%"),
                ("Memory", "44.0", "%"),
                ("Uptime", "12", "days"),
            )
        )
        tables = (
            table(
                "WAN Ports",
                ("Port", "Status", "Speed (Mbps)", "RX (Mbps)", "TX (Mbps)", "Util %"),
                (("WAN 1", "Unknown", "-", "125.0", "50.0", "12.5"),),
            ),
            table(
                "VPN Peer Paths",
                ("Peer", "Status", "Loss %", "Latency", "Jitter", "MOS"),
                (("Remote Peer", "Up", "0.25", "33.3", "4.5", "4.20"),),
            ),
        )
        charts = (
            OfflineDashboard.Chart(
                "Gateway Bandwidth (24h)",
                "RX and TX rates in Mbps.",
                labels,
                (
                    series("RX", "Mbps", (100, 104, 108, 112, 116, 120), "#21b7c8"),
                    series("TX", "Mbps", (39, 40, 41, 42, 43, 44), "#ff0080"),
                ),
                (0, 140),
            ),
            OfflineDashboard.Chart(
                "Device Metrics (24h)",
                "CPU and memory utilization.",
                labels,
                (
                    series("CPU", "%", (20, 21, 22, 23, 24, 25), "#f2c230"),
                    series("Memory", "%", (40, 41, 42, 43, 44, 45), "#21b7c8"),
                ),
                (0, 50),
            ),
        )
        return OfflineDashboard.Page(kpis, (), tables, charts)

    @staticmethod
    def _port_page() -> OfflineDashboard.Page:
        """Build port KPI cards, gauges, configuration, and counters."""
        metric = OfflineDashboard.Metric
        table = OfflineDashboard.Table
        series = OfflineDashboard.Series
        labels = ("22:20", "22:30", "22:40", "22:50", "23:00", "23:10")
        kpis = tuple(
            metric(*row)
            for row in (
                ("Speed", "1,000", "Mbps"),
                ("RX", "125.0", "Mbps"),
                ("TX", "50.0", "Mbps"),
                ("Utilization", "12.5", "%"),
                ("RX Errors", "1", ""),
                ("TX Errors", "2", ""),
            )
        )
        gauges = (metric("Current Utilization", "12.5", "%", 100),)
        tables = (
            table(
                "Current Statistics",
                ("Metric", "Value"),
                (
                    ("RX Bytes", "1.50 MB"),
                    ("TX Bytes", "2.50 MB"),
                    ("RX Packets", "1,000"),
                    ("TX Packets", "2,000"),
                    ("MTU", "1,500"),
                ),
            ),
            table(
                "Configuration",
                ("Setting", "Value"),
                (
                    ("Type", "ethernet"),
                    ("Role", "wan"),
                    ("Provider", "ISP"),
                    ("IP Address", "192.0.2.10"),
                    ("MAC", "aa:bb:cc:dd:ee:ff"),
                ),
            ),
            table(
                "Packet Statistics",
                ("Metric", "RX", "TX"),
                (("Unicast", "10", "20"), ("Multicast", "30", "40"), ("Broadcast", "50", "60")),
            ),
            table(
                "Error Counters",
                ("Error Type", "RX", "TX"),
                (("Errors", "1", "2"), ("Drops", "3", "4"), ("CRC Errors", "5", "6")),
            ),
        )
        charts = (
            OfflineDashboard.Chart(
                "Bandwidth Time-Series",
                "RX and TX rates in Mbps.",
                labels,
                (
                    series("RX", "Mbps", (100, 104, 108, 112, 116, 120), "#21b7c8"),
                    series("TX", "Mbps", (39, 40, 41, 42, 43, 44), "#ff0080"),
                ),
                (0, 140),
            ),
        )
        return OfflineDashboard.Page(kpis, gauges, tables, charts)

    @staticmethod
    def _peer_page() -> OfflineDashboard.Page:
        """Build peer quality cards, gauges, time series, and path details."""
        metric = OfflineDashboard.Metric
        table = OfflineDashboard.Table
        series = OfflineDashboard.Series
        labels = ("22:20", "22:30", "22:40", "22:50", "23:00", "23:10")
        kpis = tuple(
            metric(*row)
            for row in (
                ("Path Status", "Up", "", 1),
                ("Loss", "0.25", "%", 1),
                ("Latency", "33.3", "ms", 200),
                ("Jitter", "4.5", "ms", 100),
                ("MOS Score", "4.20", "", 5),
                ("Path MTU", "1,400", "", 1),
            )
        )
        gauges = tuple(
            metric(*row)
            for row in (
                ("Packet Loss", "0.25", "%", 10),
                ("Latency", "33.3", "ms", 200),
                ("Jitter", "4.5", "ms", 100),
                ("MOS Score", "4.20", "", 5),
            )
        )
        tables = (
            table(
                "Path Details",
                ("Setting", "Value"),
                (
                    ("Peer MAC", "11:22:33:44:55:66"),
                    ("Peer IP", "198.51.100.10"),
                    ("Local IP", "192.0.2.1"),
                    ("Path Type", "wan"),
                    ("Tunnel", "corp-vpn"),
                    ("Tunnel identity", "synthetic-tunnel-4200"),
                ),
            ),
            table(
                "Path Statistics",
                ("Metric", "Value"),
                (
                    ("Uptime", "3 days"),
                    ("TX Bytes", "1.00 KB"),
                    ("RX Bytes", "2.00 KB"),
                    ("TX Packets", "10"),
                    ("RX Packets", "20"),
                ),
            ),
        )
        charts = (
            OfflineDashboard.Chart(
                "Quality Metrics Time-Series",
                "Loss, latency, and jitter samples.",
                labels,
                (
                    series("Loss", "%", (0.10, 0.12, 0.14, 0.16, 0.18, 0.20), "#ff4050"),
                    series("Latency", "ms", (33, 33.4, 33.8, 34.2, 34.6, 35), "#f2c230"),
                    series("Jitter", "ms", (4.0, 4.1, 4.2, 4.3, 4.4, 4.5), "#21b7c8"),
                ),
                (0, 40),
            ),
        )
        return OfflineDashboard.Page(kpis, gauges, tables, charts)
