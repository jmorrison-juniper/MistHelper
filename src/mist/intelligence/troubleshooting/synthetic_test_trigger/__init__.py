"""On-demand synthetic test trigger package for menu 283."""

from __future__ import annotations  # WHY: keep annotations stable across runtime imports.

from src.mist.intelligence.troubleshooting.synthetic_test_trigger.operation import (
    SyntheticTestTrigger,
)  # WHY: expose menu handler.

__all__ = ["SyntheticTestTrigger"]  # WHY: declare the menu entry point as the public package API.
