"""Fast-mode sequential max-retries extracted from MistHelper (SC-030).

Owns the `FAST_MODE_SEQUENTIAL_MAX_RETRIES` constant originally defined
at module scope in MistHelper.py, and re-lands it as a class-level
attribute on `FastModeSequentialMaxRetries` per FR-005 / FR-015. Both
MistHelper callsites -- `_gw_retry_configs` at line ~6294 (which
previously called `os.getenv` inline) and the sequential-fallback
`fetch_synthetic_test_stats_with_retry` invocation at line ~15476 --
are rewritten in the same PR to reference the extracted class
attribute; no wrapper shim remains in MistHelper.py after this
extraction.

The value is the retry ceiling for the sequential fallback pass in
fast-mode workflows -- when the initial parallel pass fails and items
fall through to sequential processing, this limits how many times each
item is retried. Source of truth remains the
`FAST_MODE_SEQUENTIAL_MAX_RETRIES` environment variable (default 1);
the class-body evaluation preserves the original `os.getenv` semantics.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import os  # Read the environment override value


class FastModeSequentialMaxRetries:  # Class-body seam for the sequential-fallback retry ceiling
    """Class-body seam owning the fast-mode sequential-fallback retry ceiling."""

    VALUE: int = int(  # Retry ceiling for the sequential fallback pass
        os.getenv("FAST_MODE_SEQUENTIAL_MAX_RETRIES", "1")  # Env override with 1 default
    )
