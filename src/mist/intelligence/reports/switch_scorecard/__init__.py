"""Organization switch scorecard report package."""

from src.mist.intelligence.reports.switch_scorecard.operation import (
    SwitchScorecard,
)  # WHY: expose the menu handler class.

__all__ = ["SwitchScorecard"]  # WHY: make the public package surface explicit.
