"""Client fingerprint census report package."""

from src.mist.intelligence.reports.client_fingerprint_census.operation import (
    ClientFingerprintCensus,
)  # WHY: expose the menu handler.

__all__ = ["ClientFingerprintCensus"]  # WHY: keep the public package surface small and explicit.
