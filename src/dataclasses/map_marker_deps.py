"""Dataclasses that pack device-orientation marker arguments.

Refs issue #433 phase C tranche 3 (STRUCT-PARAMS sweep on maps_manager.py).
Splitting the marker call signature into position + style keeps the
``_add_device_orientation_markers`` helper under the agents.md
5-parameter limit while the call site stays self-documenting.
"""

from __future__ import annotations  # PEP 604 unions on Python 3.10+ codebases.

from dataclasses import dataclass  # Standard library dataclass factory.


@dataclass(frozen=True, slots=True)
class MarkerPosition:
    """An (x, y) pixel coordinate on the Plotly map canvas."""

    x: float  # X pixel coordinate (origin top-left to match Mist convention).
    y: float  # Y pixel coordinate (origin top-left to match Mist convention).


@dataclass(frozen=True, slots=True)
class DeviceMarkerStyle:
    """Per-device orientation marker styling values."""

    angle: float  # Device orientation in Mist degrees (0 = up, clockwise positive).
    device_color: str  # Status-driven color used for the crosshair arms.
    type_cfg: dict  # Per-type config (legend name, default size, etc).
