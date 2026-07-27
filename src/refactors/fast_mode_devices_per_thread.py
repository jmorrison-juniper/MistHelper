"""Fast-mode devices-per-thread extracted from MistHelper (SC-029).

Owns the `FAST_MODE_DEVICES_PER_THREAD` constant originally defined at
module scope in MistHelper.py, and re-lands it as a class-level
attribute on `FastModeDevicesPerThread` per FR-005 / FR-015. The sole
MistHelper callsite (batch-size sizing in `_pool_configure` at line
~7392) is rewritten in the same PR to reference the extracted class
attribute. No wrapper shim remains in MistHelper.py after this
extraction.

The value is the number of devices each worker thread handles in
fast-mode workflows -- multiplied by `max_threads` to yield the effective
batch size. Source of truth remains the `FAST_MODE_DEVICES_PER_THREAD`
environment variable (default 10). The class-body evaluation preserves
the original `os.getenv` semantics.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import os  # Read the environment override value


class FastModeDevicesPerThread:  # Class-body seam for the fast-mode devices-per-thread setting
    """Class-body seam owning the fast-mode devices-per-thread setting."""

    VALUE: int = int(  # Number of devices each worker thread handles in fast-mode
        os.getenv("FAST_MODE_DEVICES_PER_THREAD", "10")  # Env override with 10 default
    )
