"""Negative fixture with an unauthorized RRM_DRY_RUN read."""

import os as operating_system  # WHY: an alias proves the guard detects equivalent read syntax.


def bypass_policy() -> str | None:
    """Read the protected value outside the policy resolver."""
    return operating_system.getenv("RRM_DRY_RUN")  # WHY: this aliased literal read must fail the guard.
