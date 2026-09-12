"""Dataclasses that pack MapsManager scaling helpers into the 5-Item Rule.

Refs issue #433 phase C tranche 3 (STRUCT-PARAMS sweep on maps_manager.py).
Each frozen, slots-enabled dataclass groups related arguments so the
intelligent-replacement wizard's scaling math stays within the agents.md
5-parameter-per-function limit while keeping intent obvious at call sites.
"""

from __future__ import annotations  # PEP 604 unions on Python 3.10+ codebases.

from dataclasses import dataclass  # Standard library dataclass factory.


@dataclass(frozen=True, slots=True)
class MapDimensions:
    """A map's pixel size plus its pixels-per-meter (PPM) ratio."""

    width_px: int  # Pixel width of the new image being placed on the map.
    height_px: int  # Pixel height of the new image being placed on the map.
    ppm: float  # Pixels-per-meter ratio so coordinates can be converted to meters.


@dataclass(frozen=True, slots=True)
class MapScalingFactors:
    """Mode + per-axis multipliers describing a wizard scaling choice."""

    mode: str  # One of: "none", "proportional", "preserve_physical", "manual_ppm".
    x_factor: float  # Multiplier applied to existing x coordinates.
    y_factor: float  # Multiplier applied to existing y coordinates.


@dataclass(frozen=True, slots=True)
class OriginalMapMetrics:
    """Pre-replacement metrics for a map being run through the scaling wizard."""

    width_px: int  # Original pixel width of the map before the new image is uploaded.
    height_px: int  # Original pixel height of the map before the new image is uploaded.
    ppm: float  # Original pixels-per-meter ratio (used as PPM fallback default).
    width_m: float  # Original real-world width in meters (used for physical-preserve mode).


@dataclass(frozen=True, slots=True)
class ScaleChoiceContext:
    """All inputs needed to translate a menu pick into concrete scale factors."""

    width_ratio: float  # new_width_px / original_width_px ratio.
    height_ratio: float  # new_height_px / original_height_px ratio.
    original_ppm: float  # Original pixels-per-meter as a sane default.
    original_width_m: float  # Original real-world width for the preserve-physical mode.
    new_width_px: int  # Pixel width of the new image (drives manual PPM calculations).
