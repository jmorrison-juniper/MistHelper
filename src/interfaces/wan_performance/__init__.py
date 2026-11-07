"""Expose the WAN collection package as one stable import boundary."""

from src.interfaces.wan_performance.collection.snapshot_client import SnapshotClient
from src.interfaces.wan_performance.domain.identity import (
    CircuitIdentity,
    GatewayIdentity,
    PeerPathIdentity,
    SiteIdentity,
)
from src.interfaces.wan_performance.domain.measurement import HourlyMeasurement, MetricMeasurement

__all__ = [
    "CircuitIdentity",
    "GatewayIdentity",
    "HourlyMeasurement",
    "MetricMeasurement",
    "PeerPathIdentity",
    "SiteIdentity",
    "SnapshotClient",
]
