"""Fast-mode backoff multiplier extracted from MistHelper (SC-028).

Owns the `FAST_MODE_BACKOFF_MULTIPLIER` constant originally defined at
module scope in MistHelper.py, and re-lands it as a class-level
attribute on `FastModeBackoffMultiplier` per FR-005 / FR-015. Both
MistHelper callsites (`_handle_site_port_stats_retry` at line ~9899 and
the fast-retry helper at line ~15328) are rewritten in the same PR to
reference the extracted class attribute; no wrapper shim remains in
MistHelper.py after this extraction.

The value is the exponential-backoff growth factor applied to the
retry-delay curve in fast-mode workflows -- each successive attempt
multiplies the base delay by `VALUE**attempt`. Source of truth remains
the `FAST_MODE_BACKOFF_MULTIPLIER` environment variable (default 1.5);
the class-body evaluation preserves the original `os.getenv` semantics.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import os  # Read the environment override value


class FastModeBackoffMultiplier:  # Class-body seam for the fast-mode backoff growth factor
    """Class-body seam owning the fast-mode exponential-backoff growth factor."""

    VALUE: float = float(  # Exponential-backoff growth factor applied to retry-delay curve
        os.getenv("FAST_MODE_BACKOFF_MULTIPLIER", "1.5")  # Env override with 1.5 default
    )
