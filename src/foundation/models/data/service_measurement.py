"""Represent normalized service samples without a transport or storage dependency."""

import logging
from dataclasses import dataclass

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ServiceMeasurement:
    """Keep unavailable samples distinct from measured service quality."""

    total: int | None
    degraded: int | None

    def __post_init__(self) -> None:
        """Reject inconsistent counts before they can produce a score."""
        LOGGER.info("Validating service sample counts")
        if self.total is None and self.degraded is None:
            LOGGER.debug("Validated an unavailable service measurement")
            return
        if (
            not isinstance(self.total, int)
            or isinstance(self.total, bool)
            or not isinstance(self.degraded, int)
            or isinstance(self.degraded, bool)
        ):
            LOGGER.error("Sample counts must both be integers or both be absent")
            raise ValueError("Sample counts must both be integers or both be absent")
        if self.total < 0 or self.degraded < 0 or self.degraded > self.total:
            LOGGER.error("Sample counts require 0 <= degraded <= total")
            raise ValueError("Sample counts require 0 <= degraded <= total")
        LOGGER.debug("Validated a service measurement")

    @property
    def percentage(self) -> float | None:
        """Return nondegraded service percentage, or None without samples."""
        LOGGER.info("Calculating service percentage")
        if self.total is None or self.degraded is None or self.total == 0:
            LOGGER.debug("Service percentage is unavailable")
            return None
        # Divide integers first so large counts do not overflow a float conversion.
        percentage = (self.total - self.degraded) / self.total * 100
        LOGGER.debug("Calculated service percentage: %s", percentage)
        return percentage
