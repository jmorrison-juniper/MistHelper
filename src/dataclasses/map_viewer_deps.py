"""Dataclasses that pack the Plotly/Dash map viewer arguments.

Refs issue #433 phase C tranche 3 (STRUCT-PARAMS sweep on maps_manager.py).
The viewer launcher and heatmap helper are kept under the agents.md
5-parameter limit by grouping scope, payload, and optional features into
focused dataclasses that document call-site intent.
"""

from __future__ import annotations  # PEP 604 unions on Python 3.10+ codebases.

from dataclasses import dataclass  # Standard library dataclass factory.
from typing import Any  # Wildcard inner type for the loosely-typed Mist payloads.


@dataclass(frozen=True, slots=True)
class MapViewerScope:
    """Identity triple naming which site and map the viewer is opening."""

    site_id: str  # Mist site UUID the viewer is scoped to.
    site_name: str  # Human-readable site name shown in the viewer title bar.
    map_id: str  # Mist map UUID being displayed.


@dataclass(frozen=True, slots=True)
class MapViewerData:
    """Required payload arrays the viewer draws on the canvas."""

    map_data: dict[str, Any]  # Full map record (dimensions, walls, BLE beacons, etc).
    devices: list[dict[str, Any]]  # AP/switch/gateway placement records currently on the map.
    zones: list[dict[str, Any]]  # Zone polygons displayed as overlays.
    clients: list[dict[str, Any]]  # Connected wireless client positions for the live overlay.


@dataclass(frozen=True, slots=True)
class MapViewerOptional:
    """Optional secondary inputs the viewer renders when present."""

    coverage_data: dict[str, Any] | None  # RF coverage payload (drives heatmap trace when not None).
    all_maps: list[dict[str, Any]] | None  # Other maps in the same site (powers the map-switcher dropdown).
    all_sites: list[dict[str, Any]] | None  # Other sites in the org (powers the site-switcher dropdown).


@dataclass(frozen=True, slots=True)
class HeatmapRenderCtx:
    """Render handles the heatmap helper needs before adding a trace."""

    fig: object  # Plotly figure the heatmap trace is appended to.
    heatmap_renderer: object  # Renderer that converts coverage data into a Plotly trace.
    coverage_data: dict[str, Any] | None  # Coverage payload (None means skip the heatmap entirely).
