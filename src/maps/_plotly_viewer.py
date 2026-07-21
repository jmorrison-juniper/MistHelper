"""Plotly/Dash interactive map viewer (extracted from MapsManager).

Split out of ``src/maps/maps_manager.py`` so the ~2000 LOC plotly/dash
viewer cluster lives in a dedicated module. The extracted code stays
as methods on a small wrapper class :class:`_PlotlyViewer`; a magic
``__getattr__`` fallback delegates any attribute the plotly cluster
does not define directly (``apisession``, ``org_id``, non-plotly helper
methods) to the wrapped MapsManager, so the extraction diff stays tiny.

Callers use the module-level :func:`launch_plotly_viewer` factory:

    launch_plotly_viewer(maps_manager, scope, data, optional)

which is what MapsManager itself now calls instead of the old
``self._launch_plotly_viewer(...)`` method.
"""

from __future__ import annotations  # WHY: Enable PEP 563 lazy annotation resolution for typing-only imports.

import importlib.util  # WHY: Runtime check for optional deps (plotly/dash/PIL) without hard import cost.
import logging  # WHY: Emit viewer lifecycle + validation diagnostics to project logger.
import os  # WHY: Read DASH_PORT env var and check container flags for host binding.
import threading  # WHY: Run browser-open timer off the main event loop.
import time  # WHY: Sleep briefly before opening browser so Dash server is ready.
import webbrowser  # WHY: Auto-open the viewer URL in the operator's default browser.
from math import cos, pi, radians, sin  # WHY: Compute crosshair angles + coverage-circle points.
from typing import Any  # WHY: Type MapsManager wrapper attr without importing the concrete class.

from src.dataclasses.map_marker_deps import (
    DeviceMarkerStyle,
    MarkerPosition,
)  # WHY: Bundle marker inputs into typed dataclass params.
from src.dataclasses.map_scaling_deps import MapDimensions  # WHY: Typed bundle for static-map figure sizing.
from src.dataclasses.map_viewer_deps import (  # WHY: Grouped scope/data/optional bundles keep public API compact.
    HeatmapRenderCtx,  # WHY: Bundle heatmap render inputs (coverage, ppm, dims).
    MapViewerData,  # WHY: Map/devices/zones/clients payload bundle.
    MapViewerOptional,  # WHY: Optional overlays (coverage_data, all_maps, all_sites).
    MapViewerScope,  # WHY: Site/map identity bundle for the viewer session.
)
from src.maps._container_detection import (
    is_running_in_container,
)  # WHY: Bind Dash to 0.0.0.0 when containerized so host can reach it.

logger = logging.getLogger(__name__)  # WHY: Module-scoped logger for lifecycle + validation traces.

# Optional visualization imports -- these mirror the checks in
# maps_manager.py so the extracted code sees the same runtime symbols
# and fallback paths. Kept module-scoped so callback closures can
# reference them without re-importing on every invocation.
PLOTLY_AVAILABLE = (
    importlib.util.find_spec("plotly") is not None
)  # WHY: Enables graceful degrade when plotly is absent.
DASH_AVAILABLE = importlib.util.find_spec("dash") is not None  # WHY: Toggles Dash launch vs static HTML fallback path.
PIL_AVAILABLE = importlib.util.find_spec("PIL") is not None  # WHY: Guards optional Pillow-based image ops.

if PLOTLY_AVAILABLE:  # WHY: Only import go when plotly is installed.
    import plotly.graph_objects as go  # type: ignore[import-untyped]
else:
    go = None  # type: ignore[assignment]

# Dash symbols placeholders -- real modules imported lazily in the
# ``_try_import_dash_modules`` helper (matches original MapsManager
# behavior; keeps import cost off the hot path).
Dash = None  # WHY: Lazy Dash sentinel replaced after successful runtime import.
html = None  # WHY: Lazy dash.html sentinel replaced during runtime import.
dcc = None  # WHY: Lazy dash.dcc sentinel replaced during runtime import.

try:
    import mistapi  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - mistapi absent means viewer is unreachable anyway
    mistapi = None  # type: ignore[assignment]

try:
    from tqdm import tqdm  # type: ignore[import-untyped]
except ImportError:  # WHY: Provide silent progress fallback when tqdm is not installed.

    def tqdm(iterable, **_kwargs):  # WHY: Iterable pass-through keeps caller code identical.
        """No-op fallback for tqdm progress bar."""
        return iterable  # WHY: Yield the input unchanged; caller relies on iterator semantics.


class _PlotlyViewer:  # WHY: Class boundary for extracted Plotly/Dash viewer methods.
    """Wrapper class holding the extracted Plotly/Dash viewer methods.

    Attribute lookups that miss on this class delegate to the wrapped
    MapsManager via :meth:`__getattr__`. That covers non-plotly helper
    methods (``_add_clients_to_figure``, ``_add_site_survey_paths``,
    ``_backup_map_geometry``, ``_validate_ppm``) and shared instance
    state (``apisession``, ``org_id``) without touching the extracted
    method bodies.
    """

    def __init__(self, maps_manager: Any) -> None:  # WHY: Bind wrapped MapsManager instance.
        self._mm = maps_manager  # WHY: Store reference for __getattr__ delegation lookups.

    def __getattr__(self, name: str) -> Any:  # WHY: Called only when normal lookup fails.
        # Called only when normal lookup fails. Do not use self._mm
        # here directly (would recurse if _mm itself was missing);
        # go through __dict__ instead.
        mm = self.__dict__.get("_mm")  # WHY: Avoid recursion if _mm itself missing.
        if mm is None:  # pragma: no cover - only during broken init  # WHY: Guard broken init.
            raise AttributeError(name)  # WHY: Preserve normal missing-attr semantics.
        return getattr(mm, name)  # WHY: Forward attribute access to wrapped manager.

    def _get_device_status(self, device: dict) -> str:  # WHY: Return display status label.
        """Determine display status string for a device based on its API fields."""
        if (
            device.get("upgrade_status") or device.get("fwupdate", {}).get("progress") is not None
        ):  # WHY: Firmware upgrade takes precedence over status.
            return "upgrading"  # Firmware update in progress takes priority over connected/disconnected
        status = device.get("status", "disconnected")  # API field: 'connected' or 'disconnected'
        if status == "connected":  # Device is reachable and connected
            return "connected"  # Standard connected state
        return "disconnected"  # Default to disconnected for any other status value

    def _build_device_hover_text(self, device: dict, device_status: str) -> str:  # WHY: Rich HTML tooltip builder.
        """Build rich HTML hover tooltip text for a device marker."""
        text = f"<b>{device.get('name', 'Unnamed')}</b><br>"  # Device name as bold header
        text += f"Type: {device.get('type', 'N/A')}<br>"  # Device type (ap/switch/gateway)
        text += f"Model: {device.get('model', 'N/A')}<br>"  # Hardware model number
        text += f"MAC: {device.get('mac', 'N/A')}<br>"  # MAC address for identification
        text += f"Status: <b>{device_status.upper()}</b><br>"  # Status in bold uppercase for visibility
        if device_status == "upgrading":  # Only show progress for upgrading devices
            progress = device.get("fwupdate", {}).get("progress", "N/A")  # Firmware update progress
            text += f"Upgrade Progress: {progress}%<br>" if progress != "N/A" else ""  # Percentage if available
        text += f"Position: ({device.get('x', 'N/A')}, {device.get('y', 'N/A')})<br>"  # Pixel coordinates
        text += f"Orientation: {device.get('orientation', 0)}deg"  # Device orientation in degrees
        return text  # Return completed hover tooltip HTML string

    @staticmethod
    def _find_mesh_uplink(type_devices: list, uplink_mac: str) -> dict | None:  # WHY: Locate mesh uplink AP object.
        """Return the AP whose MAC matches ``uplink_mac`` or ``None``."""
        for uplink_device in type_devices:  # WHY: Linear scan -- typical AP list is small.
            if uplink_device.get("mac") == uplink_mac:  # WHY: MAC is unique per device.
                return uplink_device  # WHY: Found the mesh uplink target.
        return None  # WHY: Uplink AP not on this map -- skip.

    def _add_mesh_links(self, fig, type_devices: list) -> None:  # WHY: Draw mesh uplink lines onto figure.
        """Add dashed mesh link lines between APs that have mesh uplink relationships."""
        mesh_links_added = 0  # WHY: Track how many links were drawn for legend + logging.
        for device in type_devices:  # WHY: Check each AP for mesh uplink info.
            uplink_mac = device.get("mesh_uplink")  # WHY: MAC of the uplink AP in mesh topology.
            if not uplink_mac:  # WHY: This AP has no mesh uplink -- skip.
                continue  # WHY: Not a mesh AP.
            uplink_device = self._find_mesh_uplink(type_devices, uplink_mac)  # WHY: Resolve MAC to AP object.
            if uplink_device is None:  # WHY: Uplink AP not present on this map.
                continue  # WHY: Cannot draw link without endpoint.
            fig.add_trace(  # WHY: Draw magenta dashed line between AP pair.
                go.Scatter(
                    x=[device["x"], uplink_device["x"]],  # WHY: Line endpoints (this AP + uplink AP).
                    y=[device["y"], uplink_device["y"]],  # WHY: Y coords matching x endpoints.
                    mode="lines",  # WHY: Line-only trace (no markers).
                    line=dict(color="rgba(255,0,255,0.4)", width=2, dash="dash"),  # WHY: Transparent magenta dashes.
                    name="Mesh Link",  # WHY: Legend/toggle name.
                    showlegend=(mesh_links_added == 0),  # WHY: Only show once in legend.
                    hoverinfo="skip",  # WHY: No hover -- cosmetic line only.
                )
            )
            mesh_links_added += 1  # WHY: Increment drawn link count for legend gating.
        if mesh_links_added > 0:  # WHY: Only log if any links were drawn.
            logger.info("Added %d mesh links between APs", mesh_links_added)  # WHY: Inform operator of topology.

    @staticmethod
    def _add_orientation_horizontal_arm(
        fig, position: MarkerPosition, size: int, color: str, group_name: str
    ) -> None:  # WHY: Draw horizontal crosshair arm.
        """Draw the horizontal arm of the orientation crosshair."""
        fig.add_trace(
            go.Scatter(
                x=[position.x - size, position.x + size],  # WHY: Left/right endpoints of horizontal arm.
                y=[position.y, position.y],  # WHY: Same y -- horizontal line.
                mode="lines",  # WHY: Line-only trace.
                line=dict(color=color, width=3),  # WHY: Status-based color for horizontal arm.
                name=f"{group_name} Orientation",  # WHY: Group name enables layer toggle.
                showlegend=False,  # WHY: Don't clutter legend with individual crosshair lines.
                hoverinfo="skip",  # WHY: No hover needed -- orientation marker only.
            )
        )

    @staticmethod
    def _add_orientation_vertical_arm(
        fig, position: MarkerPosition, size: int, color: str, group_name: str
    ) -> None:  # WHY: Draw vertical crosshair arm.
        """Draw the vertical arm of the orientation crosshair."""
        fig.add_trace(
            go.Scatter(
                x=[position.x, position.x],  # WHY: Same x -- vertical line.
                y=[position.y - size, position.y + size],  # WHY: Top/bottom endpoints of vertical arm.
                mode="lines",  # WHY: Line-only trace.
                line=dict(color=color, width=3),  # WHY: Status-based color for vertical arm.
                name=f"{group_name} Orientation",  # WHY: Same group name for toggle parity.
                showlegend=False,  # WHY: Keep legend clean.
                hoverinfo="skip",  # WHY: Cosmetic only.
            )
        )

    @staticmethod
    def _add_orientation_direction_dot(
        fig, position: MarkerPosition, angle: float, color: str, group_name: str
    ) -> None:  # WHY: Draw directional dot indicating device facing.
        """Draw the directional dot indicating device facing."""
        dot_distance = 50  # WHY: Distance from device center to orientation dot (px).
        math_angle = 90 - angle  # WHY: Convert Mist orientation (0=up) to math angle (0=right).
        dot_x = position.x + dot_distance * cos(radians(math_angle))  # WHY: X position of directional dot.
        dot_y = position.y - dot_distance * sin(radians(math_angle))  # WHY: Y position -- subtract, Y grows downward.
        fig.add_trace(
            go.Scatter(
                x=[dot_x],
                y=[dot_y],
                mode="markers",  # WHY: Single-point marker.
                marker=dict(
                    size=16,  # WHY: Larger dot for visibility.
                    color=color,  # WHY: Status-based color matches device icon.
                    line=dict(color="white", width=2),  # WHY: White outline for contrast.
                ),
                name=f"{group_name} Orientation",  # WHY: Same group name for toggle parity.
                showlegend=False,  # WHY: Keep legend clean.
                hovertext=f"Orientation: {angle} deg",  # WHY: Show orientation angle on hover.
                hoverinfo="text",  # WHY: Enable text hover for orientation debugging.
            )
        )

    def _add_device_orientation_markers(
        self,
        fig,
        position: MarkerPosition,
        style: DeviceMarkerStyle,
    ) -> None:  # WHY: Draw crosshair + dot for device orientation.
        """Add a Mist-style crosshair and directional dot to show device orientation on the map."""
        angle = style.angle  # WHY: Unpack Mist-degree orientation for math-angle conversion.
        color = style.device_color  # WHY: Unpack status-driven color for the crosshair arms.
        group_name = style.type_cfg["name"]  # WHY: Group name enables layer toggle parity.
        crosshair_size = 40  # WHY: Crosshair arm length in pixels for visibility.
        self._add_orientation_horizontal_arm(
            fig, position, crosshair_size, color, group_name
        )  # WHY: Draw horizontal arm.
        self._add_orientation_vertical_arm(fig, position, crosshair_size, color, group_name)  # WHY: Draw vertical arm.
        self._add_orientation_direction_dot(fig, position, angle, color, group_name)  # WHY: Draw directional dot.

    @staticmethod
    def _build_vbeacon_hover(beacon: dict, name: str, x, y) -> str:  # WHY: Isolate hover HTML build.
        """Return the HTML hover tooltip string for a single virtual beacon marker."""
        return (  # WHY: Concatenate multi-line hover HTML in one expression.
            f"<b>Virtual Beacon: {name}</b><br>"
            f"UUID: {beacon.get('uuid', 'N/A')}<br>"
            f"Major: {beacon.get('major', 'N/A')}<br>"
            f"Minor: {beacon.get('minor', 'N/A')}<br>"
            f"Power: {beacon.get('power', 'N/A')}<br>"
            f"Position: ({x}, {y})"
        )

    def _collect_vbeacon_markers(
        self, vbeacons: list
    ) -> tuple[list, list, list, list]:  # WHY: Return parallel arrays for vbeacon markers.
        """Return parallel arrays of (xs, ys, hovertexts, names) for placeable virtual beacons."""
        logger.debug("Collecting marker data for %d virtual beacons", len(vbeacons))  # WHY: Trace collection start.
        beacon_x: list = []  # WHY: Beacon x pixel coordinates.
        beacon_y: list = []  # WHY: Beacon y pixel coordinates.
        beacon_hover: list = []  # WHY: HTML hover tooltip strings.
        beacon_names: list = []  # WHY: Display name labels.
        for beacon in vbeacons:  # WHY: Iterate all virtual beacons.
            x, y = beacon.get("x"), beacon.get("y")  # WHY: Pixel coordinates on map.
            if x is None or y is None:  # WHY: Skip beacons without position data.
                continue  # WHY: Can't place beacon without coordinates.
            beacon_x.append(x)  # WHY: Store valid x coordinate.
            beacon_y.append(y)  # WHY: Store valid y coordinate.
            name = beacon.get("name", "Unnamed Beacon")  # WHY: Beacon display name fallback.
            beacon_names.append(name)  # WHY: Store name for annotation.
            beacon_hover.append(self._build_vbeacon_hover(beacon, name, x, y))  # WHY: Append hover HTML.
        logger.debug("Collected %d placeable virtual beacons", len(beacon_x))  # WHY: Log result count.
        return beacon_x, beacon_y, beacon_hover, beacon_names  # WHY: Return parallel arrays.

    def _add_vbeacon_markers_trace(
        self, fig, beacon_x: list, beacon_y: list, beacon_hover: list
    ) -> None:  # WHY: Add vbeacon Scatter trace.
        """Add a single Scatter trace containing all virtual beacon marker points."""
        logger.debug("Adding virtual beacon Scatter trace with %d points", len(beacon_x))  # Log trace add
        fig.add_trace(
            go.Scatter(
                x=beacon_x,
                y=beacon_y,
                mode="markers",
                name="Virtual Beacons",
                marker=dict(
                    symbol="circle",
                    size=14,
                    color="#00ff00",  # Green for virtual beacons -- distinguishes from BLE (cyan)
                    line=dict(color="white", width=2),
                    opacity=0.9,
                ),
                hovertext=beacon_hover,
                hoverinfo="text",
                visible=True,
                showlegend=True,
            )
        )  # Add all virtual beacon markers as a single trace

    def _add_vbeacon_label_annotations(
        self, fig, beacon_x: list, beacon_y: list, beacon_names: list
    ) -> None:  # WHY: Per-beacon text annotations.
        """Add per-beacon text annotations below each marker."""
        logger.debug("Adding %d virtual beacon label annotations", len(beacon_x))  # Log annotation add
        for _, (x, y, name) in enumerate(zip(beacon_x, beacon_y, beacon_names, strict=True)):  # Add per-beacon labels
            fig.add_annotation(
                x=x,
                y=y - 12,
                text=f"<b>{name}</b>",
                showarrow=False,
                font=dict(size=9, color="white", family="Arial"),
                bgcolor="rgba(0,200,0,0.9)",
                bordercolor="white",
                borderwidth=1,
                borderpad=2,
                xanchor="center",
                yanchor="bottom",
                name="Virtual Beacons Label",
            )  # Label positioned below marker

    @staticmethod
    def _draw_vbeacon_coverage_ring(
        fig, x: float, y: float, power: float
    ) -> None:  # WHY: Draw power-scaled coverage ring.
        """Draw a single power-scaled coverage ring for one virtual beacon."""
        base_radius = 50  # WHY: Base coverage radius in pixels.
        power_factor = (power + 12) / 16  # WHY: Normalize -12..+4 dBm range to 0..1.
        radius = base_radius + (power_factor * 100)  # WHY: Scale coverage radius by power.
        theta = [i * 2 * pi / 50 for i in range(51)]  # WHY: 50 points for smooth circle.
        circle_x = [x + radius * cos(t) for t in theta]  # WHY: X coordinates of circle.
        circle_y = [y + radius * sin(t) for t in theta]  # WHY: Y coordinates of circle.
        fig.add_trace(
            go.Scatter(
                x=circle_x,
                y=circle_y,
                mode="lines",  # WHY: Line-only trace for ring outline.
                line=dict(color="rgba(0,255,0,0.3)", width=1, dash="dash"),  # WHY: Transparent green dashed ring.
                fill="toself",  # WHY: Close and fill the ring shape.
                fillcolor="rgba(0,255,0,0.05)",  # WHY: Very light fill for coverage area visualization.
                name="vBeacon Coverage",
                showlegend=False,  # WHY: Don't add each circle to legend -- too many entries.
                hoverinfo="skip",  # WHY: No hover needed -- visual indicator only.
            )
        )

    def _add_vbeacon_coverage_circles(self, fig, vbeacons: list) -> None:  # WHY: Add coverage rings per vbeacon.
        """Add a translucent dashed coverage ring around each virtual beacon, sized by transmit power."""
        logger.debug(
            "Adding coverage circles for %d virtual beacons", len(vbeacons)
        )  # WHY: Log circle add for tracing.
        for beacon in vbeacons:  # WHY: Add power-based coverage circles for each beacon.
            x = beacon.get("x")  # WHY: Beacon center x pixel coordinate.
            y = beacon.get("y")  # WHY: Beacon center y pixel coordinate.
            if x is None or y is None:  # WHY: Skip beacons without coordinates.
                continue  # WHY: Can't draw circle without center point.
            power = beacon.get("power", 0)  # WHY: Transmit power in dBm (typical: -12 to +4).
            self._draw_vbeacon_coverage_ring(fig, x, y, power)  # WHY: Delegate ring drawing to keep CC low.

    def _add_vbeacons_to_figure(self, fig, map_data: dict) -> None:  # WHY: Compose vbeacon markers + labels + rings.
        """Add virtual beacon markers, labels, and coverage circles to the Plotly figure."""
        if not map_data.get("vbeacons"):  # No virtual beacons on this map -- skip
            logger.info("No virtual beacons found on this map")  # Informational for operator
            return  # Nothing to add
        vbeacons = map_data["vbeacons"]  # List of virtual beacon objects from Mist API
        logger.info("Processing %d virtual beacons", len(vbeacons))  # Log beacon count
        # Build parallel arrays of valid beacon coordinates and hover text
        beacon_x, beacon_y, beacon_hover, beacon_names = self._collect_vbeacon_markers(
            vbeacons
        )  # WHY: Extract parallel marker arrays.
        if not beacon_x:  # No beacons had valid coordinates
            return  # Nothing to render
        self._add_vbeacon_markers_trace(fig, beacon_x, beacon_y, beacon_hover)  # Single Scatter trace for all markers
        self._add_vbeacon_label_annotations(fig, beacon_x, beacon_y, beacon_names)  # Per-beacon text labels
        self._add_vbeacon_coverage_circles(fig, vbeacons)  # Power-proportional coverage rings
        logger.info("Added %d virtual beacons to map", len(beacon_x))  # Log final count

    @staticmethod
    def _collect_ble_beacon_markers(
        ble_beacons: list,
    ) -> tuple[list, list, list, list]:  # WHY: Parallel arrays for BLE beacons.
        """Return parallel arrays of (xs, ys, hovertexts, names) for placeable BLE beacons."""
        ble_x: list = []  # WHY: BLE beacon x pixel coordinates.
        ble_y: list = []  # WHY: BLE beacon y pixel coordinates.
        ble_hover: list = []  # WHY: HTML hover tooltip strings.
        ble_names: list = []  # WHY: Display name labels for annotations.
        for beacon in ble_beacons:  # WHY: Iterate all BLE beacons.
            x = beacon.get("x")  # WHY: Beacon x pixel coordinate.
            y = beacon.get("y")  # WHY: Beacon y pixel coordinate.
            if x is None or y is None:  # WHY: Skip beacons without position data.
                continue  # WHY: Can't place beacon without coordinates.
            ble_x.append(x)  # WHY: Store valid x coordinate.
            ble_y.append(y)  # WHY: Store valid y coordinate.
            name = beacon.get("name", beacon.get("mac", "Unnamed"))  # WHY: Prefer name; fall back to MAC.
            ble_names.append(name)  # WHY: Store name for annotation.
            hover = f"<b>BLE Beacon: {name}</b><br>"  # WHY: Bold header for hover tooltip.
            hover += f"MAC: {beacon.get('mac', 'N/A')}<br>"  # WHY: Hardware MAC address.
            hover += f"Type: {beacon.get('type', 'N/A')}<br>"  # WHY: Beacon type (iBeacon, Eddystone, etc.).
            hover += f"Power: {beacon.get('power', 'N/A')}<br>"  # WHY: Transmit power in dBm.
            hover += f"Position: ({x}, {y})"  # WHY: Pixel coordinates on map.
            ble_hover.append(hover)  # WHY: Append completed hover text.
        return ble_x, ble_y, ble_hover, ble_names  # WHY: Return parallel arrays for plotting.

    @staticmethod
    def _add_ble_markers_trace(fig, ble_x: list, ble_y: list, ble_hover: list) -> None:  # WHY: Add BLE Scatter trace.
        """Add a single Scatter trace containing all BLE beacon marker points."""
        fig.add_trace(
            go.Scatter(
                x=ble_x,
                y=ble_y,
                mode="markers",
                name="BLE Beacons",
                marker=dict(
                    symbol="circle",
                    size=14,
                    color="#00bfff",  # WHY: Cyan for BLE beacons -- distinguishes from virtual beacons (green).
                    line=dict(color="white", width=2),
                    opacity=0.9,
                ),
                hovertext=ble_hover,
                hoverinfo="text",
                visible=True,
                showlegend=True,
            )
        )

    @staticmethod
    def _add_ble_label_annotations(
        fig, ble_x: list, ble_y: list, ble_names: list
    ) -> None:  # WHY: Per-BLE text annotations.
        """Add per-BLE-beacon text annotations below each marker."""
        for x, y, name in zip(ble_x, ble_y, ble_names, strict=True):  # WHY: Add per-beacon labels.
            fig.add_annotation(
                x=x,
                y=y - 12,  # WHY: Offset below marker for readability.
                text=f"<b>{name}</b>",
                showarrow=False,
                font=dict(size=9, color="white", family="Arial"),
                bgcolor="rgba(0,191,255,0.9)",  # WHY: Cyan background matches marker color.
                bordercolor="white",
                borderwidth=1,
                borderpad=2,
                xanchor="center",
                yanchor="bottom",
                name="BLE Beacons Label",
            )

    def _add_ble_beacons_to_figure(self, fig, map_data: dict) -> None:  # WHY: Compose BLE markers + labels.
        """Add BLE beacon markers and labels to the Plotly figure."""
        if not map_data.get("beacons"):  # WHY: No BLE beacons on this map -- skip.
            logger.info("No BLE beacons found on this map")  # WHY: Informational for operator.
            return  # WHY: Nothing to add.
        ble_beacons = map_data["beacons"]  # WHY: List of BLE beacon objects from Mist API.
        logger.info("Processing %d BLE beacons", len(ble_beacons))  # WHY: Log beacon count.
        ble_x, ble_y, ble_hover, ble_names = self._collect_ble_beacon_markers(
            ble_beacons
        )  # WHY: Build parallel arrays.
        if not ble_x:  # WHY: No BLE beacons had valid coordinates.
            return  # WHY: Nothing to render.
        self._add_ble_markers_trace(fig, ble_x, ble_y, ble_hover)  # WHY: Single Scatter trace for all markers.
        self._add_ble_label_annotations(fig, ble_x, ble_y, ble_names)  # WHY: Per-beacon text labels.
        logger.info("Added %d BLE beacons to map", len(ble_x))  # WHY: Log final count.

    def _launch_plotly_viewer(  # WHY: Public entry point; delegates to extracted ViewerLauncher.
        self,
        scope: MapViewerScope,  # WHY: Site/map identity bundle for the viewer session.
        data: MapViewerData,  # WHY: Map/devices/zones/clients payload for the figure.
        optional: MapViewerOptional,  # WHY: Optional overlays (coverage, all_maps, all_sites).
    ) -> None:
        """Launch interactive Plotly/Dash map viewer via the extracted ViewerLauncher module."""
        from src.maps._viewer_launch import _ViewerLauncher  # WHY: Lazy import breaks Dash-optional import cycle.

        launcher = _ViewerLauncher(self)  # WHY: Bind wrapped viewer so helper methods stay reachable.
        launcher.run(scope, data, optional)  # WHY: Execute the full Dash viewer workflow.

    def _open_browser_after_delay(dash_port: int) -> None:  # WHY: Delayed browser auto-open.
        """Wait for the Dash server to start, then open the system browser to the viewer URL."""
        logger.info("Browser auto-open: scheduling open to http://127.0.0.1:%s", dash_port)  # Trace start
        time.sleep(1.5)  # Wait for Dash server to initialize (matches original delay)
        webbrowser.open(f"http://127.0.0.1:{dash_port}")  # Launch system browser
        logger.debug("Browser opened to http://127.0.0.1:%s", dash_port)  # Mirror original log

    # ------------------------------------------------------------------
    # Wave E2 helpers extracted from _launch_plotly_viewer to drive CC <= 10
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_coverage_count(coverage_data: dict | None) -> int:  # WHY: Safe grid-result count.
        """Return the number of grid results in ``coverage_data`` (0 if missing)."""
        if not coverage_data:  # Original used a ternary; explicit guard preserves behavior
            return 0  # WHY: No coverage payload means zero grid results.
        return len(coverage_data.get("results", []))  # WHY: Count of grid samples.

    @staticmethod
    def _normalize_optional_lists(
        all_maps: list | None, all_sites: list | None
    ) -> tuple[list, list]:  # WHY: Coalesce optional lists.
        """Coalesce optional list args to empty lists (drops two BoolOps from parent CC)."""
        return (
            all_maps if all_maps else [],
            all_sites if all_sites else [],
        )  # WHY: None-safe defaults.

    def _try_import_dash_modules(self, map_data: dict, devices: list) -> tuple | None:  # WHY: Import Dash or fall back.
        """Import dash + companions; on ImportError run the static fallback and return ``None``."""
        logger.info("_try_import_dash_modules: attempting to import dash")  # Trace start
        try:
            logger.debug("Importing Dash modules for interactive viewer")  # WHY: Mirror original log.
            import dash  # WHY: Heavy module; local import keeps top-of-file imports minimal.
            from dash import Dash, Input, Output, State, dcc, html, no_update  # WHY: Names used in layout/callbacks.

            logger.info("Dash version: %s", dash.__version__)  # WHY: Record actual Dash version at launch.
            return dash, Dash, Input, Output, State, dcc, html, no_update  # WHY: Return full Dash symbol tuple.
        except ImportError as e:  # WHY: Fallback path (mirrors original except block).
            logger.exception("Failed to import Dash, falling back to static view: %s", e)  # WHY: Surface import fail.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! Dash not available - using static Plotly view only")
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.warning("! Install with: pip install dash")
            self._create_static_plotly_map(map_data, devices)  # WHY: Render static figure instead.
            return None  # WHY: Signal to caller that Dash is unavailable.

    @staticmethod
    def _print_viewer_intro_banner() -> None:  # WHY: Print operator-facing launch banner.
        """Print the user-facing 'LAUNCHING INTERACTIVE MAP VIEWER' banner (no decisions)."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("-" * 80)
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("LAUNCHING INTERACTIVE MAP VIEWER")
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("-" * 80)
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("! Opening web browser with interactive map...")
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("! Features:")
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("!   - Toggle layers (walls, zones, wayfinding, devices, clients)")
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("!   - Live data refresh (clients update every 30s, RF every 5min)")
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("!   - Ruler tool - Draw lines to measure distances")
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("!   - Connected client visualization (green dots)")
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("!   - Click devices/clients to see details")
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("!   - Drag devices to new positions (future: save to cloud)")
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("!   - Pan and zoom")
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("! Press Ctrl+C in terminal to stop server")
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("-" * 80)

    @staticmethod
    def _add_background_image_to_figure(fig: object, map_data: dict, map_width: int, map_height: int) -> None:
        """Add the map background image to the figure (gates the URL check internally)."""
        if "url" not in map_data:  # Mirror original else-branch behavior
            logger.warning("Map has no background image URL")
            return
        logger.debug("Adding map background image: %s...", str(map_data.get("url"))[:100])  # Mirror log
        fig.add_layout_image(  # Plotly background-image API
            source=map_data["url"],
            x=0,
            y=0,
            sizex=map_width,
            sizey=map_height,
            xref="x",
            yref="y",
            sizing="stretch",
            layer="below",
        )

    @staticmethod
    def _categorize_devices_by_type(devices: list[dict]) -> dict[str, list[dict]]:
        """Bucket devices by type filtered to those with both x and y coordinates."""
        buckets: dict[str, list[dict]] = {"ap": [], "switch": [], "gateway": []}  # Mirror original keys
        for device in devices:  # One pass; ignores devices without coords or unknown type
            device_type = device.get("type", "unknown")
            if device_type not in buckets:  # Skip unknown device types
                continue
            if "x" not in device or "y" not in device:  # Skip un-placed devices
                continue
            buckets[device_type].append(device)
        return buckets

    def _render_device_type_on_figure(
        self,
        fig: object,
        type_devices: list[dict],
        type_cfg: dict,
        device_type: str,
    ) -> None:
        """Render markers + labels + mesh links + orientation markers for one device type."""
        if not type_devices:  # Nothing to render for this type
            return
        coords = self._extract_device_coords(type_devices)  # x/y/names/orientations arrays
        colors, hover_text = self._compute_device_visuals(type_devices, type_cfg)  # Per-device color + hover
        self._log_device_orientations(type_devices)  # Debug log (mirror original)
        self._add_device_marker_trace(fig, coords, type_cfg, colors, hover_text)  # Trace
        self._add_device_name_labels(fig, coords, type_cfg, colors)  # Per-device label annotations
        if device_type == "ap":  # Mirror original "ap" mesh-links branch
            self._add_mesh_links(fig, type_devices)
        self._add_orientation_markers_for_devices(fig, coords, colors, type_cfg)  # Crosshair + dot

    @staticmethod
    def _extract_device_coords(type_devices: list[dict]) -> dict[str, list]:
        """Pull parallel x/y/names/orientations arrays from a list of device dicts."""
        return {
            "x_coords": [d["x"] for d in type_devices],
            "y_coords": [d["y"] for d in type_devices],
            "names": [d.get("name", d.get("mac", "Unknown")) for d in type_devices],
            "orientations": [d.get("orientation", 0) for d in type_devices],
        }

    def _compute_device_visuals(self, type_devices: list[dict], type_cfg: dict) -> tuple[list[str], list[str]]:
        """Compute per-device color array + per-device hover-text array."""
        statuses = [self._get_device_status(device) for device in type_devices]  # Per-device status
        colors = [type_cfg["colors"][status] for status in statuses]  # Status -> color
        hover_text = [
            self._build_device_hover_text(device, status) for device, status in zip(type_devices, statuses, strict=True)
        ]
        return colors, hover_text

    @staticmethod
    def _log_device_orientations(type_devices: list[dict]) -> None:
        """Debug-log each device's orientation (mirrors original loop verbatim)."""
        for device in type_devices:  # One log line per device
            device_name = device.get("name", "Unnamed")
            device_orientation = device.get("orientation", 0)
            logger.debug("Device '%s': orientation=%s", device_name, device_orientation)

    @staticmethod
    def _build_device_marker_style(type_cfg: dict, colors: list[str]) -> dict:  # WHY: Isolate marker style dict.
        """Return the inline marker style dict for a device Scatter trace."""
        return {  # WHY: Consolidated marker styling for device points.
            "symbol": type_cfg["symbol"],  # WHY: Per-type shape (triangle/square/diamond).
            "size": type_cfg["size"],  # WHY: Per-type marker size.
            "color": colors,  # WHY: Status-driven per-device color list.
            "line": dict(color="white", width=2),  # WHY: White outline for contrast.
            "opacity": 0.9,  # WHY: Slight transparency for overlap visibility.
        }

    @staticmethod
    def _add_device_marker_trace(
        fig: object,
        coords: dict[str, list],
        type_cfg: dict,
        colors: list[str],
        hover_text: list[str],
    ) -> None:  # WHY: Add per-type device markers as one Scatter trace.
        """Add the per-type marker Scatter trace (preserves original styling exactly)."""
        import plotly.graph_objects as go  # WHY: Local import keeps top-level light.

        marker_style = _PlotlyViewer._build_device_marker_style(type_cfg, colors)  # WHY: Extracted style dict.
        fig.add_trace(
            go.Scatter(
                x=coords["x_coords"],  # WHY: Per-device pixel x list.
                y=coords["y_coords"],  # WHY: Per-device pixel y list.
                mode="markers",  # WHY: Marker-only trace.
                name=type_cfg["name"],  # WHY: Legend + toggle group name.
                marker=marker_style,  # WHY: Style dict (see _build_device_marker_style).
                hovertext=hover_text,  # WHY: Rich per-device hover HTML.
                hoverinfo="text",  # WHY: Use only hovertext (not defaults).
                visible=True,  # WHY: Default to visible.
                showlegend=True,  # WHY: Group appears in legend.
            )
        )

    @staticmethod
    def _add_device_name_labels(
        fig: object,
        coords: dict[str, list],
        type_cfg: dict,
        colors: list[str],
    ) -> None:
        """Add per-device name labels as annotations (preserves original styling)."""
        for _, (x, y, name, device_color) in enumerate(
            zip(coords["x_coords"], coords["y_coords"], coords["names"], colors, strict=True)
        ):
            fig.add_annotation(
                x=x,
                y=y - 15,  # Position above marker
                text=f"<b>{name}</b>",
                showarrow=False,
                font=dict(size=11, color="white", family="Arial Black"),
                bgcolor="rgba(0,0,0,0.85)",
                bordercolor=device_color,
                borderwidth=2,
                borderpad=3,
                xanchor="center",
                yanchor="bottom",
                name=f"{type_cfg['name']} Label",
            )

    def _add_orientation_markers_for_devices(
        self,
        fig: object,
        coords: dict[str, list],
        colors: list[str],
        type_cfg: dict,
    ) -> None:
        """Add Mist-style orientation crosshair + directional dot for each device."""
        for x, y, angle, device_color in zip(
            coords["x_coords"], coords["y_coords"], coords["orientations"], colors, strict=True
        ):
            self._add_device_orientation_markers(
                fig,
                MarkerPosition(x=x, y=y),
                DeviceMarkerStyle(angle=angle, device_color=device_color, type_cfg=type_cfg),
            )

    @staticmethod
    def _maybe_add_heatmap_trace(
        ctx: HeatmapRenderCtx,
        dims: MapDimensions,
    ) -> None:
        """Build the RF coverage heatmap trace and add it to ``fig`` when non-None."""
        fig = ctx.fig  # Unpack Plotly figure handle the heatmap trace appends to.
        heatmap_renderer = ctx.heatmap_renderer  # Unpack renderer that converts coverage data to a trace.
        coverage_data = ctx.coverage_data  # Unpack coverage payload (None skips the heatmap entirely).
        ppm = dims.ppm  # Unpack pixels-per-meter ratio so the renderer scales the heatmap correctly.
        map_width = dims.width_px  # Unpack map pixel width for the renderer bounds.
        map_height = dims.height_px  # Unpack map pixel height for the renderer bounds.
        heatmap_trace = heatmap_renderer.build_heatmap_trace(
            coverage_data=coverage_data, ppm=ppm, map_width=map_width, map_height=map_height
        )
        if heatmap_trace is None:  # Mirror original guard
            return
        fig.add_trace(heatmap_trace)

    @staticmethod
    def _add_origin_marker_trace(fig: object, map_data: dict, go: object) -> None:
        """Add the map-origin marker trace (hidden by default; mirrors original)."""
        origin = map_data.get("origin") or {}  # Drop ``or {}`` BoolOp from parent
        origin_x = origin.get("x", 0)
        origin_y = origin.get("y", 0)
        fig.add_trace(
            go.Scatter(
                x=[origin_x],
                y=[origin_y],
                mode="markers+text",
                name="Map Origin",
                marker=dict(symbol="x", size=20, color="yellow", line=dict(width=3, color="black")),
                text=["Origin (0,0)"],
                textposition="top center",
                textfont=dict(size=12, color="yellow"),
                visible=False,
                showlegend=True,
            )
        )

    @staticmethod
    def _add_origin_horizontal_line(fig: object, origin_x: float, origin_y: float, size: int) -> None:
        """Add horizontal blue line of origin crosshair."""
        import plotly.graph_objects as go  # WHY: Local import keeps module top light.

        hover = f"Origin: ({origin_x}, {origin_y})"  # WHY: Reuse hover text across all three traces.
        fig.add_trace(
            go.Scatter(
                x=[origin_x - size, origin_x + size],  # WHY: Left/right endpoints.
                y=[origin_y, origin_y],  # WHY: Same y -- horizontal.
                mode="lines",
                line=dict(color="#00bfff", width=3),  # WHY: Cyan for origin distinction.
                name="Origin",
                showlegend=True,  # WHY: Show in legend so operator can toggle.
                hovertext=hover,
                hoverinfo="text",
            )
        )

    @staticmethod
    def _add_origin_vertical_line(fig: object, origin_x: float, origin_y: float, size: int) -> None:
        """Add vertical blue line of origin crosshair."""
        import plotly.graph_objects as go  # WHY: Local import keeps module top light.

        hover = f"Origin: ({origin_x}, {origin_y})"  # WHY: Match horizontal hover for consistency.
        fig.add_trace(
            go.Scatter(
                x=[origin_x, origin_x],  # WHY: Same x -- vertical.
                y=[origin_y - size, origin_y + size],  # WHY: Top/bottom endpoints.
                mode="lines",
                line=dict(color="#00bfff", width=3),  # WHY: Cyan matches horizontal.
                showlegend=False,  # WHY: Already in legend via horizontal trace.
                hovertext=hover,
                hoverinfo="text",
            )
        )

    @staticmethod
    def _add_origin_center_dot(fig: object, origin_x: float, origin_y: float) -> None:
        """Add central dot of origin crosshair."""
        import plotly.graph_objects as go  # WHY: Local import keeps module top light.

        hover = f"Origin: ({origin_x}, {origin_y})"  # WHY: Consistent hover across origin traces.
        fig.add_trace(
            go.Scatter(
                x=[origin_x],
                y=[origin_y],
                mode="markers",
                marker=dict(
                    size=12, color="#00bfff", line=dict(color="white", width=2)
                ),  # WHY: White outline for contrast.
                name="Origin Point",
                showlegend=False,  # WHY: Origin already in legend via horizontal trace.
                hovertext=hover,
                hoverinfo="text",
            )
        )

    @staticmethod
    def _add_origin_crosshair(fig: object, map_data: dict) -> None:
        """Add a blue crosshair (horizontal line + vertical line + center dot) at the origin point."""
        origin_x = map_data.get("origin_x", 0)  # WHY: Pixel-space origin x from map metadata.
        origin_y = map_data.get("origin_y", 0)  # WHY: Pixel-space origin y from map metadata.
        crosshair_size = 40  # WHY: Arm length matches device orientation crosshair.
        _PlotlyViewer._add_origin_horizontal_line(fig, origin_x, origin_y, crosshair_size)  # WHY: Draw horizontal arm.
        _PlotlyViewer._add_origin_vertical_line(fig, origin_x, origin_y, crosshair_size)  # WHY: Draw vertical arm.
        _PlotlyViewer._add_origin_center_dot(fig, origin_x, origin_y)  # WHY: Draw center dot.

    @staticmethod
    def _build_selector_options(all_maps: list[dict], all_sites: list[dict]) -> tuple[list[dict], list[dict]]:
        """Build (map_dropdown_options, site_dropdown_options) for the selectors."""
        map_options = [{"label": m.get("name", "Unnamed"), "value": m.get("id")} for m in all_maps]
        sites_sorted = sorted(all_sites, key=lambda x: x.get("name", "").lower())  # Sort by name
        site_options = [{"label": s.get("name", "Unnamed Site"), "value": s.get("id")} for s in sites_sorted]
        return map_options, site_options

    @staticmethod
    def _build_zone_toggle_widget(zones: list[dict], dcc: object, html: object) -> object:
        """Build either a zone-toggle Checklist or a 'no zones' placeholder paragraph."""
        if not zones:  # Mirror original else-branch
            return html.P(
                "No zones on this map",
                style={"color": "#888", "fontSize": "12px", "fontStyle": "italic"},
            )
        return dcc.Checklist(  # Mirror original Checklist construction byte-for-byte
            id="zone-toggle",
            options=[
                {
                    "label": f" {zone.get('name', f'Zone {i + 1}')}",
                    "value": zone.get("id", f"zone_{i}"),
                }
                for i, zone in enumerate(zones)
            ],
            value=[zone.get("id", f"zone_{i}") for i, zone in enumerate(zones)],
            labelStyle={
                "display": "block",
                "margin": "8px 0",
                "fontSize": "13px",
                "color": "#e0e0e0",
            },
            style={"marginBottom": "15px"},
        )

    @staticmethod
    def _resolve_dash_binding(os_mod: object) -> tuple[str, int]:
        """Resolve Dash server bind host + port (container-aware, ``DASH_PORT`` override)."""
        dash_host = "127.0.0.1"  # Default to loopback for safety
        if is_running_in_container():  # In container -> bind all interfaces
            dash_host = "0.0.0.0"  # nosec B104 — container must bind all interfaces
        dash_port = int(os_mod.getenv("DASH_PORT", "8050"))  # Use port 8050 by default
        return dash_host, dash_port

    @staticmethod
    def _print_dash_startup_banner(dash_host: str, dash_port: int) -> None:
        """Print the user-facing 'Starting Dash server...' banner."""
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("\nStarting Dash server...")
        if is_running_in_container():  # Container-specific lines
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("! Map viewer available at http://<container-ip>:%s", dash_port)
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("! Access from host: http://localhost:%s (if port is mapped)", dash_port)
        else:
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("! Map viewer will open in your default browser")
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("! Press Ctrl+C to stop the server\n")
        logger.info("Starting Dash server on http://%s:%s", dash_host, dash_port)  # Mirror original log

    def _schedule_browser_open(self, dash_port: int) -> None:
        """Start a daemon thread that opens the browser shortly after server boots (skip in container)."""
        if is_running_in_container():  # No display in container; skip browser
            return

        threading.Thread(  # Background thread -> _open_browser_after_delay
            target=self._open_browser_after_delay, args=(dash_port,), daemon=True
        ).start()

    @staticmethod
    def _run_dash_server(app: object, dash_host: str, dash_port: int) -> None:
        """Run the Dash server with the project's standard kwargs, handling Ctrl+C + errors."""
        try:
            debug_mode = getattr(globals().get("args"), "debug", False)  # CLI --debug flag if present
            logger.info("Starting Dash server with debug_mode=%s", debug_mode)  # Mirror original log
            app.run(  # Dash 3.x uses app.run() instead of app.run_server()
                host=dash_host,
                port=dash_port,
                debug=debug_mode,
                use_reloader=False,  # Disable reloader to prevent double-execution
                threaded=True,
            )
        except KeyboardInterrupt:  # Mirror original user-cancel path
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.info("\n\nMap viewer stopped by user")
            logger.info("Interactive map viewer stopped by user (Ctrl+C)")
        except Exception as e:  # Mirror original catch-all
            logger.exception("Error running Dash server: %s", e)
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            logger.error("\n! Error running map viewer: %s", e)

    @staticmethod
    def _add_static_map_background(fig: object, map_data: dict, map_width: int, map_height: int) -> None:
        """Attach the map image as a background layer on ``fig`` when URL is present."""
        if "url" not in map_data:  # WHY: Skip when the map has no image URL to render.
            return
        fig.add_layout_image(
            source=map_data["url"],  # WHY: Direct S3 URL for the floorplan image.
            x=0,  # WHY: Left edge anchored at x=0.
            y=map_height,  # WHY: Top edge -- Plotly y grows upward.
            sizex=map_width,  # WHY: Image width in pixels.
            sizey=map_height,  # WHY: Image height in pixels.
            xref="x",  # WHY: Coordinate reference frame -- x axis.
            yref="y",  # WHY: Coordinate reference frame -- y axis.
            sizing="stretch",  # WHY: Stretch to fill the plot area.
            layer="below",  # WHY: Render below all traces.
        )

    @staticmethod
    def _collect_static_device_coords(placed: list[dict], map_height: int) -> tuple[list, list, list]:
        """Return parallel (x, y, name) lists for a pre-filtered device list."""
        x_coords: list = []  # WHY: Pixel x per placed device.
        y_coords: list = []  # WHY: Flipped pixel y per placed device.
        names: list = []  # WHY: Display name (MAC fallback) per device.
        for device in placed:  # WHY: Iterate pre-filtered devices only.
            x_coords.append(device.get("x", 0))  # WHY: Default 0 keeps parallel arrays aligned.
            y_coords.append(map_height - device.get("y", 0))  # WHY: Flip y so origin is top-left.
            names.append(device.get("name", device.get("mac", "Unknown")))  # WHY: Fallback name = MAC.
        return x_coords, y_coords, names

    @staticmethod
    def _add_static_map_devices(fig: object, devices: list[dict], map_height: int) -> None:
        """Add a green Scatter trace for every device with pixel coords."""
        if not devices:  # WHY: Skip when no devices supplied.
            return
        placed = [d for d in devices if "x" in d]  # WHY: Only devices with x coord render.
        if not placed:  # WHY: Nothing to plot -- avoid empty trace.
            return
        import plotly.graph_objects as go  # WHY: Local import keeps top-level light.

        x_coords, y_coords, names = _PlotlyViewer._collect_static_device_coords(
            placed, map_height
        )  # WHY: Aligned arrays.
        fig.add_trace(
            go.Scatter(
                x=x_coords,
                y=y_coords,
                mode="markers+text",  # WHY: Marker + label above it.
                name="Devices",  # WHY: Legend entry.
                marker=dict(size=10, color="green"),  # WHY: Uniform green markers for static export.
                text=names,  # WHY: Device names rendered above markers.
                textposition="top center",  # WHY: Center label above marker for legibility.
            )
        )

    @staticmethod
    def _configure_static_map_layout(fig: object, map_data: dict, map_width: int, map_height: int) -> None:
        """Apply the static-map layout: title, axes ranges, aspect lock, height."""
        fig.update_layout(
            title=f"Map: {map_data.get('name', 'Unnamed')}",  # WHY: Show map name in title.
            xaxis=dict(range=[0, map_width]),  # WHY: Lock x range to map pixel width.
            yaxis=dict(range=[0, map_height], scaleanchor="x", scaleratio=1),  # WHY: Square pixel aspect ratio.
            height=800,  # WHY: Default plot height in pixels.
        )

    @staticmethod
    def _save_and_open_static_map(fig: object, map_data: dict) -> None:
        """Write ``fig`` to a temp HTML file and open it in the default browser."""
        import tempfile  # WHY: Locate the OS temp directory.

        map_id = str(map_data.get("id", "unknown"))[:8]  # WHY: Short id fragment for stable temp name.
        temp_html = os.path.join(tempfile.gettempdir(), f"mist_map_{map_id}.html")  # WHY: OS-appropriate temp path.
        logger.debug("Saving static map to: %s", temp_html)  # WHY: Debug the resolved path.
        fig.write_html(temp_html)  # WHY: Serialise the figure to a self-contained HTML file.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("\n! Map saved to: %s", temp_html)
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("! Opening in browser...")
        logger.info("Static HTML map created: %s", temp_html)  # WHY: Record for audit.
        webbrowser.open(f"file://{temp_html}")  # WHY: Trigger the OS browser handler.
        logger.debug("Browser launched with static map")  # WHY: Post-launch trace.

    def _create_static_plotly_map(self, map_data, devices):
        """Create static Plotly HTML map when Dash is not available."""
        import plotly.graph_objects as go  # WHY: Only import when this path is taken.

        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("\n! Creating static HTML map...")
        fig = go.Figure()  # WHY: Fresh figure receives all traces + layout.
        map_width = map_data.get("width", 1000)  # WHY: Fallback width in pixels.
        map_height = map_data.get("height", 1000)  # WHY: Fallback height in pixels.
        self._add_static_map_background(fig, map_data, map_width, map_height)  # WHY: Attach floorplan image.
        self._add_static_map_devices(fig, devices, map_height)  # WHY: Plot device markers on top of image.
        self._configure_static_map_layout(fig, map_data, map_width, map_height)  # WHY: Set axes/aspect/title.
        self._save_and_open_static_map(fig, map_data)  # WHY: Persist to disk and hand off to browser.


def launch_plotly_viewer(
    maps_manager: Any,
    scope: MapViewerScope,
    data: MapViewerData,
    optional: MapViewerOptional,
):
    """Entry point: construct the viewer wrapper and launch it.

    Kept as a thin factory so MapsManager (and tests) can invoke the
    plotly viewer without instantiating :class:`_PlotlyViewer` directly.
    """
    logger.debug(
        "launch_plotly_viewer invoked for scope=%s", getattr(scope, "site_name", "?")
    )  # WHY: Trace entry point.
    viewer = _PlotlyViewer(maps_manager)  # WHY: Wrap MapsManager so viewer helpers can call back safely.
    return viewer._launch_plotly_viewer(scope, data, optional)  # WHY: Delegate to the class method that owns the flow.
