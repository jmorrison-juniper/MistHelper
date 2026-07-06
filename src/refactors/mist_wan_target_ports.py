"""MIST_WAN_TARGET_PORTS extracted from MistHelper (SC-032).

Owns the `MIST_WAN_TARGET_PORTS` list constant originally defined at
module scope in MistHelper.py, and re-lands it as a class-level
attribute on `MistWanTargetPorts` per FR-005 / FR-015 (assignment ->
class-body attribute). The sole MistHelper callsite -- the DI kwarg
`mist_wan_target_ports=MIST_WAN_TARGET_PORTS` in
`_gateway_export_dependency_kwargs` at line ~15568 -- is rewritten in
the same PR to reference the extracted class attribute; no wrapper
shim remains in MistHelper.py after this extraction.

The value is the operator-configured, comma-separated list of WAN port
names to target for gateway-override analysis. Source of truth remains
the `MIST_WAN_TARGET_PORTS` environment variable (no default -- an
unset env yields an empty list); the class-body evaluation preserves
the original CSV-parsing semantics.

FR-019 note: The local DI slots named `MIST_WAN_TARGET_PORTS` in
`src/gateway/gateway_export_utils.py:51` and
`src/gateway/overrides/_deps.py:17` are local module-level variables
that receive their value at runtime via the injected `deps` struct.
They are not references to the deleted MistHelper.py symbol and remain
unchanged by this extraction; the cross-file audit trail verifies the
sole external-file caller path continues to flow through the DI kwarg.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import os  # Read the environment override value


class MistWanTargetPorts:  # Class-body seam for the operator-configured WAN target ports
    """Class-body seam owning the operator-configured WAN target-ports list."""

    VALUE: list[str] = [  # Parsed CSV env into a clean list of port names
        p.strip()  # Trim whitespace around each entry
        for p in os.getenv("MIST_WAN_TARGET_PORTS", "").split(",")  # CSV env with empty default
        if p.strip()  # Drop empty entries
    ]
