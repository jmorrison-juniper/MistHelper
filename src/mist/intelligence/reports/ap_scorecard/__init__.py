"""Organization access point scorecard report package."""

from src.mist.intelligence.reports.ap_scorecard.operation import (
    ApScorecard,
)  # WHY: expose the menu handler for deferred wiring.

__all__ = ["ApScorecard"]  # WHY: keep the public package surface explicit for menu wiring.
