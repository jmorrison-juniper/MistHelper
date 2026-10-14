"""Normalize the bundled vpn_peer_stat schema without inferring hourly coverage."""

import logging
from collections.abc import Mapping
from types import MappingProxyType

from src.interfaces.portals.wan_performance.domain.measurement import MetricMeasurement

logger = logging.getLogger(__name__)


class PeerSnapshotMetrics:
    """Read documented VPN fields while keeping missing values distinct from zero."""

    FIELDS: Mapping[str, tuple[str, int | None]] = MappingProxyType(
        {"latency": ("ms", None), "jitter": ("ms", None), "loss": ("%", 100), "mos": ("score", 5)}
    )

    @classmethod
    def parse(cls, row: Mapping[str, object]) -> Mapping[str, MetricMeasurement]:
        """Return immutable snapshot metrics without adding time-series semantics."""
        logger.info("Validate VPN snapshot metrics.")
        metrics = {name: cls._metric(name, row.get(name)) for name in cls.FIELDS}
        logger.debug("Validated %d VPN snapshot metrics.", len(metrics))
        return MappingProxyType(metrics)

    @classmethod
    def _metric(cls, name: str, value: object) -> MetricMeasurement:
        """Validate the documented unit and bounds before constructing a metric."""
        unit, maximum = cls.FIELDS[name]
        try:
            if value is None:
                return MetricMeasurement(None, unit, missing_reason="The API snapshot has no value.")
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("The value must be a number.")
            metric = MetricMeasurement(value, unit)
            if value < 0 or (maximum is not None and value > maximum):
                raise ValueError("The value is outside the documented bounds.")
            return metric
        except ValueError as error:
            logger.error("Invalid VPN snapshot metric %s: %s", name, error)
            raise ValueError(f"Invalid {name} in VPN snapshot: {error}") from error
