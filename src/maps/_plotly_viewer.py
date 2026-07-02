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

from __future__ import annotations

import importlib.util
import logging
import os
import sys
import threading
import time
import webbrowser
from math import cos, pi, radians, sin
from typing import Any

from src.dataclasses.map_marker_deps import DeviceMarkerStyle, MarkerPosition
from src.dataclasses.map_scaling_deps import MapDimensions
from src.dataclasses.map_viewer_deps import (
    HeatmapRenderCtx,
    MapViewerData,
    MapViewerOptional,
    MapViewerScope,
)
from src.maps._container_detection import is_running_in_container
from src.maps.launcher import MapViewerCallbacks, MapViewerState
from src.maps.plotly_heatmap_renderer import PlotlyCoverageHeatmapRenderer
from src.maps.plotly_map_callback_manager import PlotlyMapCallbackManager
from src.maps.plotly_map_figure_builder import PlotlyMapFigureBuilder
from src.maps.plotly_map_serializer import PlotlyMapDataSerializer
from src.maps.plotly_map_templates import DashTemplateManager

logger = logging.getLogger(__name__)

# Optional visualization imports -- these mirror the checks in
# maps_manager.py so the extracted code sees the same runtime symbols
# and fallback paths. Kept module-scoped so callback closures can
# reference them without re-importing on every invocation.
PLOTLY_AVAILABLE = importlib.util.find_spec("plotly") is not None
DASH_AVAILABLE = importlib.util.find_spec("dash") is not None
PIL_AVAILABLE = importlib.util.find_spec("PIL") is not None

if PLOTLY_AVAILABLE:
    import plotly.graph_objects as go  # type: ignore[import-untyped]
else:
    go = None  # type: ignore[assignment]

# Dash symbols placeholders -- real modules imported lazily in the
# ``_try_import_dash_modules`` helper (matches original MapsManager
# behavior; keeps import cost off the hot path).
Dash = None
html = None
dcc = None

try:
    import mistapi  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - mistapi absent means viewer is unreachable anyway
    mistapi = None  # type: ignore[assignment]

try:
    from tqdm import tqdm  # type: ignore[import-untyped]
except ImportError:

    def tqdm(iterable, **_kwargs):
        """No-op fallback for tqdm progress bar."""
        return iterable


class _PlotlyViewer:
    """Wrapper class holding the extracted Plotly/Dash viewer methods.

    Attribute lookups that miss on this class delegate to the wrapped
    MapsManager via :meth:`__getattr__`. That covers non-plotly helper
    methods (``_add_clients_to_figure``, ``_add_site_survey_paths``,
    ``_backup_map_geometry``, ``_validate_ppm``) and shared instance
    state (``apisession``, ``org_id``) without touching the extracted
    method bodies.
    """

    def __init__(self, maps_manager: Any) -> None:
        self._mm = maps_manager

    def __getattr__(self, name: str) -> Any:
        # Called only when normal lookup fails. Do not use self._mm
        # here directly (would recurse if _mm itself was missing);
        # go through __dict__ instead.
        mm = self.__dict__.get("_mm")
        if mm is None:  # pragma: no cover - only during broken init
            raise AttributeError(name)
        return getattr(mm, name)

    def _get_device_status(self, device: dict) -> str:
        """Determine display status string for a device based on its API fields."""
        if device.get("upgrade_status") or device.get("fwupdate", {}).get("progress") is not None:
            return "upgrading"  # Firmware update in progress takes priority over connected/disconnected
        status = device.get("status", "disconnected")  # API field: 'connected' or 'disconnected'
        if status == "connected":  # Device is reachable and connected
            return "connected"  # Standard connected state
        return "disconnected"  # Default to disconnected for any other status value

    def _build_device_hover_text(self, device: dict, device_status: str) -> str:
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

    def _add_mesh_links(self, fig, type_devices: list) -> None:
        """Add dashed mesh link lines between APs that have mesh uplink relationships."""
        mesh_links_added = 0  # Track how many links were drawn for logging
        for _, device in enumerate(type_devices):  # Check each AP for mesh uplink info
            mesh_uplink = device.get("mesh_uplink")  # MAC of the uplink AP in mesh topology
            if not mesh_uplink:  # This AP has no mesh uplink -- skip
                continue  # Not a mesh AP
            for uplink_device in type_devices:  # Find the uplink AP by MAC
                if uplink_device.get("mac") == mesh_uplink:  # Found the uplink device
                    fig.add_trace(
                        go.Scatter(
                            x=[device["x"], uplink_device["x"]],  # Line from this AP to its uplink
                            y=[device["y"], uplink_device["y"]],
                            mode="lines",
                            line=dict(color="rgba(255,0,255,0.4)", width=2, dash="dash"),  # Transparent magenta dashes
                            name="Mesh Link",
                            showlegend=(mesh_links_added == 0),  # Only show once in legend
                            hoverinfo="skip",  # No hover -- cosmetic line only
                        )
                    )  # Draw mesh link between AP pair
                    mesh_links_added += 1  # Increment drawn link count
                    break  # Found the uplink -- move to next device
        if mesh_links_added > 0:  # Only log if any links were drawn
            logging.info("Added %d mesh links between APs", mesh_links_added)  # Inform operator of topology

    def _add_device_orientation_markers(
        self,
        fig,
        position: MarkerPosition,
        style: DeviceMarkerStyle,
    ) -> None:
        """Add a Mist-style crosshair and directional dot to show device orientation on the map."""
        x = position.x  # Unpack device x pixel coord for the marker math below.
        y = position.y  # Unpack device y pixel coord for the marker math below.
        angle = style.angle  # Unpack Mist-degree orientation for math-angle conversion.
        device_color = style.device_color  # Unpack status-driven color for the crosshair arms.
        type_cfg = style.type_cfg  # Unpack per-type config (legend grouping, etc).
        crosshair_size = 40  # Crosshair arm length in pixels -- increased from 25 for visibility
        fig.add_trace(
            go.Scatter(
                x=[x - crosshair_size, x + crosshair_size],
                y=[y, y],
                mode="lines",
                line=dict(color=device_color, width=3),  # Status-based color for horizontal arm
                name=f"{type_cfg['name']} Orientation",  # Group name enables layer toggle
                showlegend=False,  # Don't clutter legend with individual crosshair lines
                hoverinfo="skip",  # No hover needed -- orientation marker only
            )
        )  # Horizontal crosshair arm
        fig.add_trace(
            go.Scatter(
                x=[x, x],
                y=[y - crosshair_size, y + crosshair_size],
                mode="lines",
                line=dict(color=device_color, width=3),  # Status-based color for vertical arm
                name=f"{type_cfg['name']} Orientation",  # Same group name for toggle
                showlegend=False,  # Keep legend clean
                hoverinfo="skip",  # Cosmetic only
            )
        )  # Vertical crosshair arm
        dot_distance = 50  # Distance from device center to orientation dot -- increased from 35
        math_angle = 90 - angle  # Convert Mist orientation (0=up) to math angle (0=right)
        dot_x = x + dot_distance * cos(radians(math_angle))  # X position of directional dot
        dot_y = y - dot_distance * sin(radians(math_angle))  # Y position -- subtract because Y increases downward
        fig.add_trace(
            go.Scatter(
                x=[dot_x],
                y=[dot_y],
                mode="markers",
                marker=dict(
                    size=16,  # Larger dot for visibility -- increased from 10
                    color=device_color,  # Status-based color matches device icon
                    line=dict(color="white", width=2),  # White outline for contrast
                ),
                name=f"{type_cfg['name']} Orientation",  # Same group name for toggle
                showlegend=False,  # Keep legend clean
                hovertext=f"Orientation: {angle} deg",  # Show orientation angle on hover
                hoverinfo="text",
            )
        )  # Directional dot indicating which way the device faces

    def _collect_vbeacon_markers(self, vbeacons: list) -> tuple[list, list, list, list]:
        """Return parallel arrays of (xs, ys, hovertexts, names) for placeable virtual beacons."""
        logging.debug("Collecting marker data for %d virtual beacons", len(vbeacons))  # Log collection start
        beacon_x: list = []  # Beacon x pixel coordinates
        beacon_y: list = []  # Beacon y pixel coordinates
        beacon_hover: list = []  # HTML hover tooltip strings
        beacon_names: list = []  # Display name labels
        for beacon in vbeacons:  # Iterate all virtual beacons
            x = beacon.get("x")  # Beacon x pixel coordinate
            y = beacon.get("y")  # Beacon y pixel coordinate
            if x is None or y is None:  # Skip beacons without position data
                continue  # Can't place beacon without coordinates
            beacon_x.append(x)  # Store valid x coordinate
            beacon_y.append(y)  # Store valid y coordinate
            name = beacon.get("name", "Unnamed Beacon")  # Beacon display name
            beacon_names.append(name)  # Store name for annotation
            hover = f"<b>Virtual Beacon: {name}</b><br>"  # Bold header for hover tooltip
            hover += f"UUID: {beacon.get('uuid', 'N/A')}<br>"  # Beacon UUID for iBeacon identification
            hover += f"Major: {beacon.get('major', 'N/A')}<br>"  # iBeacon major value
            hover += f"Minor: {beacon.get('minor', 'N/A')}<br>"  # iBeacon minor value
            hover += f"Power: {beacon.get('power', 'N/A')}<br>"  # Transmit power in dBm
            hover += f"Position: ({x}, {y})"  # Pixel coordinates on map
            beacon_hover.append(hover)  # Append completed hover text
        logging.debug("Collected %d placeable virtual beacons", len(beacon_x))  # Log result count
        return beacon_x, beacon_y, beacon_hover, beacon_names  # Return parallel arrays for plotting

    def _add_vbeacon_markers_trace(self, fig, beacon_x: list, beacon_y: list, beacon_hover: list) -> None:
        """Add a single Scatter trace containing all virtual beacon marker points."""
        logging.debug("Adding virtual beacon Scatter trace with %d points", len(beacon_x))  # Log trace add
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

    def _add_vbeacon_label_annotations(self, fig, beacon_x: list, beacon_y: list, beacon_names: list) -> None:
        """Add per-beacon text annotations below each marker."""
        logging.debug("Adding %d virtual beacon label annotations", len(beacon_x))  # Log annotation add
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

    def _add_vbeacon_coverage_circles(self, fig, vbeacons: list) -> None:
        """Add a translucent dashed coverage ring around each virtual beacon, sized by transmit power."""
        logging.debug("Adding coverage circles for %d virtual beacons", len(vbeacons))  # Log circle add
        for beacon in vbeacons:  # Add power-based coverage circles for each beacon
            x = beacon.get("x")  # Beacon center x
            y = beacon.get("y")  # Beacon center y
            power = beacon.get("power", 0)  # Transmit power in dBm (typical: -12 to +4)
            if x is None or y is None:  # Skip beacons without coordinates
                continue  # Can't draw circle without center point
            base_radius = 50  # Base coverage radius in pixels
            power_factor = (power + 12) / 16  # Normalize -12..+4 dBm range to 0..1
            radius = base_radius + (power_factor * 100)  # Scale coverage radius by power
            theta = [i * 2 * pi / 50 for i in range(51)]  # 50 points for smooth circle
            circle_x = [x + radius * cos(t) for t in theta]  # X coordinates of circle
            circle_y = [y + radius * sin(t) for t in theta]  # Y coordinates of circle
            fig.add_trace(
                go.Scatter(
                    x=circle_x,
                    y=circle_y,
                    mode="lines",
                    line=dict(color="rgba(0,255,0,0.3)", width=1, dash="dash"),  # Transparent green dashed ring
                    fill="toself",
                    fillcolor="rgba(0,255,0,0.05)",  # Very light fill for coverage area visualization
                    name="vBeacon Coverage",
                    showlegend=False,  # Don't add each circle to legend -- too many entries
                    hoverinfo="skip",  # No hover needed -- visual indicator only
                )
            )  # Draw power-proportional coverage circle

    def _add_vbeacons_to_figure(self, fig, map_data: dict) -> None:
        """Add virtual beacon markers, labels, and coverage circles to the Plotly figure."""
        if not map_data.get("vbeacons"):  # No virtual beacons on this map -- skip
            logging.info("No virtual beacons found on this map")  # Informational for operator
            return  # Nothing to add
        vbeacons = map_data["vbeacons"]  # List of virtual beacon objects from Mist API
        logging.info("Processing %d virtual beacons", len(vbeacons))  # Log beacon count
        # Build parallel arrays of valid beacon coordinates and hover text
        beacon_x, beacon_y, beacon_hover, beacon_names = self._collect_vbeacon_markers(vbeacons)
        if not beacon_x:  # No beacons had valid coordinates
            return  # Nothing to render
        self._add_vbeacon_markers_trace(fig, beacon_x, beacon_y, beacon_hover)  # Single Scatter trace for all markers
        self._add_vbeacon_label_annotations(fig, beacon_x, beacon_y, beacon_names)  # Per-beacon text labels
        self._add_vbeacon_coverage_circles(fig, vbeacons)  # Power-proportional coverage rings
        logging.info("Added %d virtual beacons to map", len(beacon_x))  # Log final count

    def _add_ble_beacons_to_figure(self, fig, map_data: dict) -> None:
        """Add BLE beacon markers and labels to the Plotly figure."""
        if not map_data.get("beacons"):  # No BLE beacons on this map -- skip
            logging.info("No BLE beacons found on this map")  # Informational for operator
            return  # Nothing to add
        ble_beacons = map_data["beacons"]  # List of BLE beacon objects from Mist API
        logging.info("Processing %d BLE beacons", len(ble_beacons))  # Log beacon count
        ble_x: list = []  # BLE beacon x pixel coordinates
        ble_y: list = []  # BLE beacon y pixel coordinates
        ble_hover: list = []  # HTML hover tooltip strings
        ble_names: list = []  # Display name labels
        for beacon in ble_beacons:  # Iterate all BLE beacons
            x = beacon.get("x")  # Beacon x pixel coordinate
            y = beacon.get("y")  # Beacon y pixel coordinate
            if x is None or y is None:  # Skip beacons without position data
                continue  # Can't place beacon without coordinates
            ble_x.append(x)  # Store valid x coordinate
            ble_y.append(y)  # Store valid y coordinate
            name = beacon.get("name", beacon.get("mac", "Unnamed"))  # Prefer name; fall back to MAC
            ble_names.append(name)  # Store name for annotation
            hover = f"<b>BLE Beacon: {name}</b><br>"  # Bold header for hover tooltip
            hover += f"MAC: {beacon.get('mac', 'N/A')}<br>"  # Hardware MAC address
            hover += f"Type: {beacon.get('type', 'N/A')}<br>"  # Beacon type (iBeacon, Eddystone, etc.)
            hover += f"Power: {beacon.get('power', 'N/A')}<br>"  # Transmit power in dBm
            hover += f"Position: ({x}, {y})"  # Pixel coordinates on map
            ble_hover.append(hover)  # Append completed hover text
        if not ble_x:  # No BLE beacons had valid coordinates
            return  # Nothing to render
        fig.add_trace(
            go.Scatter(
                x=ble_x,
                y=ble_y,
                mode="markers",
                name="BLE Beacons",
                marker=dict(
                    symbol="circle",
                    size=14,
                    color="#00bfff",  # Cyan for BLE beacons -- distinguishes from virtual beacons (green)
                    line=dict(color="white", width=2),
                    opacity=0.9,
                ),
                hovertext=ble_hover,
                hoverinfo="text",
                visible=True,
                showlegend=True,
            )
        )  # Add all BLE beacon markers as a single trace
        for _, (x, y, name) in enumerate(zip(ble_x, ble_y, ble_names, strict=True)):  # Add per-beacon labels
            fig.add_annotation(
                x=x,
                y=y - 12,
                text=f"<b>{name}</b>",
                showarrow=False,
                font=dict(size=9, color="white", family="Arial"),
                bgcolor="rgba(0,191,255,0.9)",
                bordercolor="white",
                borderwidth=1,
                borderpad=2,
                xanchor="center",
                yanchor="bottom",
                name="BLE Beacons Label",
            )  # Label positioned below marker for readability
        logging.info("Added %d BLE beacons to map", len(ble_x))  # Log final count

    def _launch_plotly_viewer(
        self,
        scope: MapViewerScope,
        data: MapViewerData,
        optional: MapViewerOptional,
    ):
        """Launch interactive Plotly/Dash map viewer with edit capabilities, client display, and RF coverage heatmap."""
        site_id = scope.site_id  # Unpack scope so the inner code paths stay readable.
        site_name = scope.site_name  # Unpack the human-readable site name for the viewer title.
        map_id = scope.map_id  # Unpack the map UUID needed by Dash callbacks downstream.
        map_data = data.map_data  # Unpack the full map record (dimensions, walls, beacons, etc).
        devices = data.devices  # Unpack the device list used to seed the placement layer.
        zones = data.zones  # Unpack the zone list used to seed the zone polygon layer.
        clients = data.clients  # Unpack the client list used to seed the connected-clients overlay.
        coverage_data = optional.coverage_data  # Unpack the coverage payload (None disables heatmap).
        all_maps = optional.all_maps  # Unpack the other-maps list (powers map-switcher dropdown).
        all_sites = optional.all_sites  # Unpack the other-sites list (powers site-switcher dropdown).
        coverage_count = self._resolve_coverage_count(coverage_data)  # Helper extracts the ternary
        all_maps, all_sites = self._normalize_optional_lists(all_maps, all_sites)  # Drops 2 BoolOps from parent CC
        logging.info(  # Issue #433 Phase C: split long log template across two lines for E501 compliance.
            "_launch_plotly_viewer called - site: %s (%s), map_id: %s, "
            "devices: %s, zones: %s, clients: %s, coverage: %s, "
            "available_maps: %s, available_sites: %s",
            site_name,
            site_id,
            map_id,
            len(devices),
            len(zones),
            len(clients),
            coverage_count,
            len(all_maps),
            len(all_sites),
        )
        import os  # Used by getenv for DASH_PORT lookup

        import plotly.graph_objects as go

        # Wave E2: dash import + ImportError fallback extracted to helper to drop CC.
        dash_modules = self._try_import_dash_modules(map_data, devices)
        if dash_modules is None:  # Helper already invoked the static-fallback path
            return
        dash, Dash, Input, Output, State, dcc, html, no_update = dash_modules
        # Wave E2: viewer banner extracted to helper (purely print statements, no CC).
        self._print_viewer_intro_banner()

        # Create Dash app with dark theme
        # update_title="" prevents "Updating..." flash in browser tab during callbacks
        # suppress_callback_exceptions=True is required for allow_duplicate=True on callback outputs
        logging.debug("Creating Dash application instance")

        # Initialize template manager for CSS/HTML/metadata
        callback_manager = PlotlyMapCallbackManager()
        # Wave A+B+C MapViewerState construction is deferred to after
        # ppm is finalized via _validate_ppm() below (ppm is a state
        # field consumed by update_shape_labels in wave C).
        template_mgr = DashTemplateManager(org_id=self.org_id)
        figure_builder = PlotlyMapFigureBuilder(logger=logging.getLogger(__name__))
        heatmap_renderer = PlotlyCoverageHeatmapRenderer(logger=logging.getLogger(__name__))
        serializer = PlotlyMapDataSerializer()
        app_meta = template_mgr.get_app_meta()

        app = Dash(
            __name__,
            update_title=app_meta["update_title"],
            title=app_meta["title"],
            suppress_callback_exceptions=app_meta["suppress_callback_exceptions"],
        )

        # Set app template and CSS from template manager
        app.index_string = template_mgr.get_html_template()

        # Build figure
        logging.debug("Building Plotly figure")
        fig = go.Figure()

        # Set map dimensions and get PPM for unit conversions
        map_width = map_data.get("width", 1000)
        map_height = map_data.get("height", 1000)
        ppm = map_data.get("ppm", 10)  # pixels per meter, default to 10 if not set
        logging.debug("Map canvas dimensions: %sx%s, PPM from map: %s", map_width, map_height, ppm)

        # Validate PPM using client coordinates to detect calibration mismatches
        ppm = self._validate_ppm(clients, ppm)  # Returns corrected PPM if mismatch > 10%

        # Waves A+B+C: now that ppm is finalized, build the shared
        # MapViewerState and the MapViewerCallbacks handler that
        # register_with(app) will wire below.
        viewer_state = MapViewerState(  # Shared state container
            callback_manager=callback_manager,  # Wave A: layer/click delegation
            zones=zones,  # Wave B/C: zone toggle + zone-action callbacks
            map_id=map_id,  # Wave B/C: logging + fallback for delete/utilities
            site_id=site_id,  # Wave C: site_id for delete/zone API calls
            api_session_ref=self.apisession,  # Wave C: live mistapi session
            ppm=ppm,  # Wave C: pixels-per-meter fallback in update_shape_labels
            mistapi_ref=mistapi,  # Wave C: module reference for deleteSiteMap/Zone
            maps_manager_ref=self._mm,  # Wave C: enables _backup_map_geometry callback (wrapper -> real MapsManager)
            serializer=serializer,  # Wave E2: dropdown option/store builder
            all_sites=all_sites,  # Wave E2: URL/site-switch site list
            all_maps=all_maps,  # Wave E2: URL/site-switch map list
            available_sites=all_sites,  # Wave E2: same data as all_sites for parity
            figure_builder=figure_builder,  # Wave E2: shared walls/wayfinding/zones builder
            heatmap_renderer=heatmap_renderer,  # Wave E2: RF coverage heatmap renderer
        )
        viewer_callbacks = MapViewerCallbacks(state=viewer_state)  # Extracted callback handlers

        # Wave E2: background image add extracted to helper (gates the URL check internally).
        self._add_background_image_to_figure(fig, map_data, map_width, map_height)

        figure_builder.add_walls(fig, map_data)
        figure_builder.add_wayfinding(fig, map_data)
        figure_builder.add_zones(fig, zones)

        # Add validation paths (site survey paths) if present
        self._add_site_survey_paths(fig, map_data)  # Draw any site survey paths on the map

        # Add connected clients if present
        self._add_clients_to_figure(fig, clients, map_id)  # Draw connected client dots on the map

        # Add devices by type with LARGER, more visible markers
        # Wave E2: device categorization extracted to helper to drop parent CC (for + if + 2 BoolOp).
        device_types = self._categorize_devices_by_type(devices)

        # Enhanced colors and symbols for device types - with status-based coloring
        # Status colors: connected (green), disconnected (red), upgrading (orange/amber)
        type_config = {
            "ap": {
                "symbol": "triangle-up",
                "name": "Access Points",
                "size": 20,
                "colors": {
                    "connected": "#00ff00",  # Bright green
                    "disconnected": "#ff0000",  # Bright red
                    "upgrading": "#ff8800",  # Orange/amber
                },
            },
            "switch": {
                "symbol": "square",
                "name": "Switches",
                "size": 18,
                "colors": {
                    "connected": "#00ccff",  # Cyan
                    "disconnected": "#ff0000",  # Bright red
                    "upgrading": "#ff8800",  # Orange/amber
                },
            },
            "gateway": {
                "symbol": "diamond",
                "name": "Gateways",
                "size": 20,
                "colors": {
                    "connected": "#ff00ff",  # Magenta
                    "disconnected": "#ff0000",  # Bright red
                    "upgrading": "#ff8800",  # Orange/amber
                },
            },
        }

        # Wave E2: keep parent CC <= 10 by handling per-type rendering in a helper.
        for device_type, type_cfg in type_config.items():  # One iteration per device type
            self._render_device_type_on_figure(fig, device_types[device_type], type_cfg, device_type)

        # Add virtual beacons (vBeacons) if present in map data
        self._add_vbeacons_to_figure(fig, map_data)  # Draw virtual beacon markers and power circles

        # Add BLE beacons if present in map data
        self._add_ble_beacons_to_figure(fig, map_data)  # Draw BLE beacon markers on the map

        # Wave E2: heatmap conditional moved inside helper to drop parent if-check.
        self._maybe_add_heatmap_trace(
            HeatmapRenderCtx(fig=fig, heatmap_renderer=heatmap_renderer, coverage_data=coverage_data),
            MapDimensions(width_px=map_width, height_px=map_height, ppm=ppm),
        )

        # Wave E2: origin marker extracted to helper (drops 1 BoolOp + add_trace).
        self._add_origin_marker_trace(fig, map_data, go)

        # Update layout with dark theme and responsive sizing
        fig.update_layout(
            title={"text": f"Map: {map_data.get('name', 'Unnamed')}", "font": {"size": 20, "color": "#e0e0e0"}},
            xaxis=dict(
                range=[-50, map_width + 50],  # Add margins to show full map
                visible=True,
                title="X (pixels)",
                gridcolor="#444",
                zerolinecolor="#666",
                color="#b0b0b0",
                constrain="domain",  # Keep zoom within bounds
            ),
            yaxis=dict(
                range=[map_height + 50, -50],  # Inverted range with margins: Mist uses top-left origin
                visible=True,
                title="Y (pixels)",
                scaleanchor="x",
                scaleratio=1,
                gridcolor="#444",
                zerolinecolor="#666",
                color="#b0b0b0",
                constrain="domain",  # Keep zoom within bounds
            ),
            autosize=True,
            hovermode="closest",
            showlegend=True,
            uirevision="constant",  # Prevent auto-ranging to data - maintain user's view
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor="rgba(45,45,45,0.9)",
                bordercolor="#667eea",
                borderwidth=2,
                font=dict(color="#e0e0e0", size=12),
            ),
            plot_bgcolor="#1a1a1a",
            paper_bgcolor="#1a1a1a",
            margin=dict(l=50, r=50, t=80, b=50),
            dragmode="zoom",  # Default to zoom, users can select drawing tools
            newshape=dict(line=dict(color="cyan", width=3), fillcolor="rgba(0,255,255,0.2)", opacity=0.8),
            # Store PPM for unit conversions in annotations
            meta={"ppm": ppm, "origin_x": map_data.get("origin_x", 0), "origin_y": map_data.get("origin_y", 0)},
        )

        # Wave E2: origin crosshair extracted to helper (3 fig.add_trace calls, 0 decisions but keeps method short).
        self._add_origin_crosshair(fig, map_data)

        # Wave E2: dropdown option building extracted to helper to drop comprehensions + lambda from parent CC.
        map_dropdown_options, site_dropdown_options = self._build_selector_options(all_maps, all_sites)

        # Create responsive Dash layout with dark theme
        app.layout = html.Div(
            [
                # Header with title and utilities buttons
                html.Div(
                    [
                        # Site selector dropdown
                        html.Div(
                            [
                                html.Span("Site: ", style={"fontSize": "14px", "color": "#888", "marginRight": "5px"}),
                                dcc.Dropdown(
                                    id="site-selector-dropdown",
                                    options=site_dropdown_options,
                                    value=site_id,
                                    clearable=False,
                                    searchable=True,
                                    style={"width": "250px", "display": "inline-block", "verticalAlign": "middle"},
                                    className="dark-dropdown",
                                ),
                            ],
                            style={"display": "inline-block", "marginRight": "20px", "verticalAlign": "middle"},
                        ),
                        # Map selector dropdown
                        html.Div(
                            [
                                html.Span("Map: ", style={"fontSize": "14px", "color": "#888", "marginRight": "5px"}),
                                dcc.Dropdown(
                                    id="map-selector-dropdown",
                                    options=map_dropdown_options,
                                    value=map_id,
                                    clearable=False,
                                    searchable=False,
                                    style={"width": "200px", "display": "inline-block", "verticalAlign": "middle"},
                                    className="dark-dropdown",
                                ),
                            ],
                            style={"display": "inline-block", "marginRight": "30px", "verticalAlign": "middle"},
                        ),
                        html.Div(
                            [
                                # Live Data Refresh Controls - moved to header
                                html.Div(
                                    [
                                        dcc.Checklist(
                                            id="auto-refresh-toggle",
                                            options=[{"label": " Auto-Refresh", "value": "enabled"}],
                                            value=["enabled"],  # Enabled by default
                                            labelStyle={
                                                "display": "inline-block",
                                                "fontSize": "12px",
                                                "color": "#e0e0e0",
                                            },
                                            style={"display": "inline-block", "marginRight": "10px"},
                                        ),
                                        html.Button(
                                            "Refresh",
                                            id="manual-refresh-btn",
                                            n_clicks=0,
                                            style={
                                                "marginRight": "15px",
                                                "padding": "6px 12px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#00ff00",
                                                "border": "1px solid #00ff00",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontSize": "12px",
                                                "verticalAlign": "middle",
                                            },
                                        ),
                                        html.Span(
                                            id="countdown-display",
                                            children="Clients: 30s | RF: 5m",
                                            style={
                                                "fontSize": "11px",
                                                "color": "#667eea",
                                                "marginRight": "15px",
                                                "verticalAlign": "middle",
                                            },
                                        ),
                                    ],
                                    style={
                                        "display": "inline-block",
                                        "marginRight": "20px",
                                        "padding": "5px 10px",
                                        "backgroundColor": "#1a1a1a",
                                        "borderRadius": "4px",
                                        "border": "1px solid #444",
                                    },
                                ),
                                html.Button(
                                    "[AUTO] Auto-Zone",
                                    id="auto-zone-btn",
                                    n_clicks=0,
                                    style={
                                        "marginRight": "10px",
                                        "padding": "8px 15px",
                                        "backgroundColor": "#667eea",
                                        "color": "white",
                                        "border": "none",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                        "fontWeight": "bold",
                                    },
                                ),
                                html.Button(
                                    "[PIN] Add vBeacon",
                                    id="add-vbeacon-btn",
                                    n_clicks=0,
                                    style={
                                        "marginRight": "10px",
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#00ff00",
                                        "border": "1px solid #00ff00",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Button(
                                    "[ANT] Add Beacon",
                                    id="add-beacon-btn",
                                    n_clicks=0,
                                    style={
                                        "marginRight": "10px",
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#00bfff",
                                        "border": "1px solid #00bfff",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Button(
                                    "[IMG] Change Image",
                                    id="change-image-btn",
                                    n_clicks=0,
                                    style={
                                        "marginRight": "10px",
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#e0e0e0",
                                        "border": "1px solid #667eea",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Button(
                                    "[DEL] Remove Image",
                                    id="remove-image-btn",
                                    n_clicks=0,
                                    style={
                                        "marginRight": "10px",
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#e0e0e0",
                                        "border": "1px solid #667eea",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Button(
                                    "[EDIT] Rename",
                                    id="rename-btn",
                                    n_clicks=0,
                                    style={
                                        "marginRight": "10px",
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#e0e0e0",
                                        "border": "1px solid #667eea",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Button(
                                    "[X] Delete",
                                    id="delete-btn",
                                    n_clicks=0,
                                    style={
                                        "marginRight": "10px",
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#ff4444",
                                        "border": "1px solid #ff4444",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Button(
                                    "[+] Clone",
                                    id="clone-btn",
                                    n_clicks=0,
                                    style={
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#00ff88",
                                        "border": "1px solid #00ff88",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                        "fontWeight": "bold",
                                    },
                                ),
                                html.Div(
                                    id="utilities-status",
                                    style={
                                        "display": "inline-block",
                                        "marginLeft": "20px",
                                        "color": "#a0a0ff",
                                        "fontSize": "13px",
                                    },
                                ),
                            ],
                            style={"display": "inline-block", "float": "right"},
                        ),
                    ],
                    style={"padding": "15px 20px", "borderBottom": "2px solid #667eea", "backgroundColor": "#2a2a2a"},
                ),
                # Clone map input panel (hidden by default)
                html.Div(
                    id="clone-panel",
                    children=[
                        html.Div(
                            [
                                html.Span(
                                    "[+] Clone Map: ",
                                    style={"color": "#00ff88", "fontWeight": "bold", "marginRight": "10px"},
                                ),
                                dcc.Input(
                                    id="clone-name-input",
                                    type="text",
                                    placeholder=f"{map_data.get('name', 'Map')} (Copy)",
                                    value=f"{map_data.get('name', 'Map')} (Copy)",
                                    style={
                                        "width": "300px",
                                        "padding": "8px 12px",
                                        "backgroundColor": "#2a2a2a",
                                        "color": "#e0e0e0",
                                        "border": "1px solid #00ff88",
                                        "borderRadius": "4px",
                                        "marginRight": "10px",
                                    },
                                ),
                                html.Button(
                                    "Execute Clone",
                                    id="execute-clone-btn",
                                    n_clicks=0,
                                    style={
                                        "padding": "8px 15px",
                                        "backgroundColor": "#00ff88",
                                        "color": "#1a1a1a",
                                        "border": "none",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                        "fontWeight": "bold",
                                        "marginRight": "10px",
                                    },
                                ),
                                html.Button(
                                    "Cancel",
                                    id="cancel-clone-btn",
                                    n_clicks=0,
                                    style={
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#ff4444",
                                        "border": "1px solid #ff4444",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Span(
                                    id="clone-status",
                                    style={"marginLeft": "15px", "color": "#e0e0e0", "fontSize": "13px"},
                                ),
                            ],
                            style={"display": "flex", "alignItems": "center", "justifyContent": "center"},
                        )
                    ],
                    style={
                        "display": "none",
                        "padding": "12px 20px",
                        "backgroundColor": "#1a1a1a",
                        "borderBottom": "1px solid #00ff88",
                    },
                ),
                # Delete map confirmation panel (hidden by default)
                html.Div(
                    id="delete-panel",
                    children=[
                        html.Div(
                            [
                                html.Span(
                                    "X DESTRUCTIVE: Delete this floorplan? ",
                                    style={"color": "#ff4444", "fontWeight": "bold", "marginRight": "10px"},
                                ),
                                html.Span(
                                    id="delete-map-name-display",
                                    children=f"Map: {map_data.get('name', 'Unknown')}",
                                    style={"color": "#ffaa00", "marginRight": "20px"},
                                ),
                                html.Button(
                                    "YES - DELETE MAP",
                                    id="confirm-delete-btn",
                                    n_clicks=0,
                                    style={
                                        "padding": "8px 15px",
                                        "backgroundColor": "#ff4444",
                                        "color": "white",
                                        "border": "none",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                        "fontWeight": "bold",
                                        "marginRight": "10px",
                                    },
                                ),
                                html.Button(
                                    "Cancel",
                                    id="cancel-delete-btn",
                                    n_clicks=0,
                                    style={
                                        "padding": "8px 15px",
                                        "backgroundColor": "#3d3d3d",
                                        "color": "#00ff88",
                                        "border": "1px solid #00ff88",
                                        "borderRadius": "4px",
                                        "cursor": "pointer",
                                    },
                                ),
                                html.Span(
                                    id="delete-status",
                                    style={"marginLeft": "15px", "color": "#e0e0e0", "fontSize": "13px"},
                                ),
                            ],
                            style={"display": "flex", "alignItems": "center", "justifyContent": "center"},
                        )
                    ],
                    style={
                        "display": "none",
                        "padding": "12px 20px",
                        "backgroundColor": "#330000",
                        "borderBottom": "2px solid #ff4444",
                    },
                ),
                html.Div(
                    [
                        # Map container - responsive
                        html.Div(
                            [
                                dcc.Graph(
                                    id="map-display",
                                    figure=fig,
                                    config={
                                        "displayModeBar": True,
                                        "displaylogo": False,
                                        "modeBarButtonsToAdd": [
                                            "drawline",
                                            "drawopenpath",
                                            "drawclosedpath",
                                            "drawcircle",
                                            "drawrect",
                                            "eraseshape",
                                        ],
                                        "scrollZoom": True,
                                        "editable": True,
                                        "edits": {"shapePosition": True, "annotationPosition": True},
                                        "toImageButtonOptions": {
                                            "format": "png",
                                            "filename": f"map_{map_data.get('name', 'export')}",
                                            "height": 1080,
                                            "width": 1920,
                                            "scale": 2,
                                        },
                                    },
                                    style={"height": "100%", "width": "100%"},
                                )
                            ],
                            className="map-container",
                        ),
                        # Sidebar
                        html.Div(
                            [
                                html.H3("Layer Controls"),
                                html.H4(
                                    "Infrastructure",
                                    style={
                                        "fontSize": "13px",
                                        "color": "#667eea",
                                        "marginTop": "10px",
                                        "marginBottom": "5px",
                                    },
                                ),
                                dcc.Checklist(
                                    id="layer-toggle",
                                    options=[
                                        {"label": " [W] Walls", "value": "walls"},
                                        {"label": " [M] Wayfinding", "value": "wayfinding"},
                                        {"label": " [Z] Location Zones", "value": "zones"},
                                        {"label": " [P] Proximity Zones", "value": "proximity_zones"},
                                        {"label": " [V] Validation Paths", "value": "validation"},
                                        {"label": " [R] RF Diagnostics Heatmap", "value": "rf_heatmap"},
                                        {"label": " [O] Map Origin", "value": "origin"},
                                    ],
                                    value=["walls", "wayfinding", "zones", "validation"],
                                    labelStyle={"display": "block", "margin": "8px 0", "fontSize": "13px"},
                                    style={"marginBottom": "10px"},
                                ),
                                html.H4(
                                    "Beacons & Positioning",
                                    style={"fontSize": "13px", "color": "#667eea", "marginBottom": "5px"},
                                ),
                                dcc.Checklist(
                                    id="beacon-toggle",
                                    options=[
                                        {"label": " [vB] Virtual Beacons", "value": "vbeacons"},
                                        {"label": " [C] vBeacon Coverage", "value": "vbeacon_coverage"},
                                        {"label": " [3P] 3rd Party Beacons", "value": "ble_beacons"},
                                    ],
                                    value=["vbeacons", "ble_beacons"],
                                    labelStyle={"display": "block", "margin": "8px 0", "fontSize": "13px"},
                                    style={"marginBottom": "10px"},
                                ),
                                html.H4(
                                    "Clients", style={"fontSize": "13px", "color": "#667eea", "marginBottom": "5px"}
                                ),
                                dcc.Checklist(
                                    id="client-toggle",
                                    options=[
                                        {"label": " [Wi] WiFi Clients", "value": "wifi_clients"},
                                        {"label": " [Wr] Wired Clients", "value": "wired_clients"},
                                        {"label": " [Ex] Excluded Clients", "value": "excluded_clients"},
                                        {"label": " [AP] Show Associated AP", "value": "show_client_ap"},
                                    ],
                                    value=["wifi_clients", "wired_clients", "show_client_ap"],
                                    labelStyle={"display": "block", "margin": "8px 0", "fontSize": "13px"},
                                    style={"marginBottom": "10px"},
                                ),
                                html.H4(
                                    "Devices", style={"fontSize": "13px", "color": "#667eea", "marginBottom": "5px"}
                                ),
                                dcc.Checklist(
                                    id="device-toggle",
                                    options=[
                                        {"label": " [AP] Access Points", "value": "aps"},
                                        {"label": " [SW] Switches", "value": "switches"},
                                        {"label": " [GW] Gateways", "value": "gateways"},
                                        {"label": " [MS] Mesh Associations", "value": "mesh_links"},
                                    ],
                                    value=["aps", "switches", "gateways"],
                                    labelStyle={"display": "block", "margin": "8px 0", "fontSize": "13px"},
                                    style={"marginBottom": "10px"},
                                ),
                                html.H4(
                                    "Filters", style={"fontSize": "13px", "color": "#667eea", "marginBottom": "5px"}
                                ),
                                dcc.Checklist(
                                    id="filter-toggle",
                                    options=[
                                        {"label": " [HI] Hide Inactive Items", "value": "hide_inactive"},
                                    ],
                                    value=[],
                                    labelStyle={"display": "block", "margin": "8px 0", "fontSize": "13px"},
                                    style={"marginBottom": "10px"},
                                ),
                                html.Hr(),
                                html.H3("Drawing Tools"),
                                html.Details(
                                    [
                                        html.Summary(
                                            "How to use",
                                            style={
                                                "fontSize": "12px",
                                                "color": "#00bfff",
                                                "cursor": "pointer",
                                                "marginBottom": "8px",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.P(
                                                    "1. Select a Drawing Mode below",
                                                    style={
                                                        "fontSize": "11px",
                                                        "color": "#aaa",
                                                        "margin": "4px 0 4px 10px",
                                                    },
                                                ),
                                                html.P(
                                                    "2. Use toolbar above map to draw shape",
                                                    style={
                                                        "fontSize": "11px",
                                                        "color": "#aaa",
                                                        "margin": "4px 0 4px 10px",
                                                    },
                                                ),
                                                html.P(
                                                    "3. Click 'Save Last Shape to Mist'",
                                                    style={
                                                        "fontSize": "11px",
                                                        "color": "#aaa",
                                                        "margin": "4px 0 4px 10px",
                                                    },
                                                ),
                                                html.P(
                                                    "Zones: Draw rectangle for coverage areas",
                                                    style={
                                                        "fontSize": "11px",
                                                        "color": "#00bfff",
                                                        "margin": "4px 0 4px 10px",
                                                    },
                                                ),
                                                html.P(
                                                    "Walls: Draw line for RF attenuation",
                                                    style={
                                                        "fontSize": "11px",
                                                        "color": "#ffa500",
                                                        "margin": "4px 0 4px 10px",
                                                    },
                                                ),
                                                html.P(
                                                    "Paths: Draw line for validation routes",
                                                    style={
                                                        "fontSize": "11px",
                                                        "color": "#ff00ff",
                                                        "margin": "4px 0 8px 10px",
                                                    },
                                                ),
                                            ],
                                            style={
                                                "backgroundColor": "#2a2a2a",
                                                "padding": "8px",
                                                "borderRadius": "4px",
                                                "marginBottom": "10px",
                                            },
                                        ),
                                    ],
                                    open=False,
                                ),
                                # Drawing mode selector
                                html.Div(
                                    [
                                        html.Label(
                                            "Drawing Mode:",
                                            style={"fontSize": "12px", "color": "#888", "marginBottom": "4px"},
                                        ),
                                        dcc.Dropdown(
                                            id="drawing-mode-dropdown",
                                            options=[
                                                {"label": "Validation Path (magenta)", "value": "path"},
                                                {"label": "Zone Rectangle (cyan)", "value": "zone"},
                                                {"label": "Wall Segment (orange)", "value": "wall"},
                                                {"label": "Measurement Only", "value": "measure"},
                                            ],
                                            value="measure",
                                            clearable=False,
                                            style={"marginBottom": "10px", "color": "#e0e0e0"},
                                            className="dark-dropdown",
                                        ),
                                    ],
                                    style={"marginBottom": "10px"},
                                ),
                                # Zone name input (shown when zone mode selected)
                                html.Div(
                                    [
                                        dcc.Input(
                                            id="zone-name-input",
                                            type="text",
                                            placeholder="Zone name (required)",
                                            style={
                                                "width": "100%",
                                                "padding": "8px",
                                                "marginBottom": "8px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#e0e0e0",
                                                "border": "1px solid #00bfff",
                                                "borderRadius": "4px",
                                            },
                                        ),
                                    ],
                                    id="zone-name-container",
                                    style={"display": "none"},
                                ),
                                # Action buttons
                                html.Div(
                                    [
                                        html.Button(
                                            "[SAVE] Save Last Shape to Mist",
                                            id="save-shape-btn",
                                            n_clicks=0,
                                            style={
                                                "width": "100%",
                                                "marginBottom": "8px",
                                                "padding": "10px",
                                                "backgroundColor": "#28a745",
                                                "color": "white",
                                                "border": "none",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontSize": "13px",
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        html.Button(
                                            "[CLR] Clear All Drawings",
                                            id="clear-drawings-btn",
                                            n_clicks=0,
                                            style={
                                                "width": "100%",
                                                "marginBottom": "8px",
                                                "padding": "8px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#ffc107",
                                                "border": "1px solid #ffc107",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontSize": "13px",
                                            },
                                        ),
                                    ]
                                ),
                                html.Hr(style={"margin": "10px 0"}),
                                # Delete from Mist section
                                html.P(
                                    "Delete from Mist API:",
                                    style={"fontSize": "12px", "color": "#ff6666", "marginBottom": "8px"},
                                ),
                                html.Div(
                                    [
                                        html.Button(
                                            "Delete Validation Paths",
                                            id="delete-paths-btn",
                                            n_clicks=0,
                                            style={
                                                "width": "100%",
                                                "marginBottom": "6px",
                                                "padding": "6px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#ff4444",
                                                "border": "1px solid #ff4444",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontSize": "11px",
                                            },
                                        ),
                                        html.Button(
                                            "Delete Wayfinding Paths",
                                            id="delete-wayfinding-btn",
                                            n_clicks=0,
                                            style={
                                                "width": "100%",
                                                "marginBottom": "6px",
                                                "padding": "6px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#ff8844",
                                                "border": "1px solid #ff8844",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontSize": "11px",
                                            },
                                        ),
                                        html.Button(
                                            "Delete All Walls",
                                            id="delete-walls-btn",
                                            n_clicks=0,
                                            style={
                                                "width": "100%",
                                                "marginBottom": "6px",
                                                "padding": "6px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#ff4444",
                                                "border": "1px solid #ff4444",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontSize": "11px",
                                            },
                                        ),
                                        html.Button(
                                            "Delete All Zones",
                                            id="delete-zones-btn",
                                            n_clicks=0,
                                            style={
                                                "width": "100%",
                                                "marginBottom": "6px",
                                                "padding": "6px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#ff66ff",
                                                "border": "1px solid #ff66ff",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontSize": "11px",
                                            },
                                        ),
                                    ]
                                ),
                                html.Div(
                                    id="drawing-tool-status",
                                    style={
                                        "fontSize": "11px",
                                        "color": "#a0a0ff",
                                        "marginTop": "8px",
                                        "minHeight": "40px",
                                    },
                                ),
                                html.Hr(),
                                html.H3("Measurement Tools"),
                                html.P("Use the toolbar above the map:", style={"fontSize": "12px", "color": "#888"}),
                                html.P(
                                    "- Draw Line - Measure distances",
                                    style={"fontSize": "11px", "marginLeft": "10px", "color": "#999"},
                                ),
                                html.P(
                                    "- Draw Path - Create routes",
                                    style={"fontSize": "11px", "marginLeft": "10px", "color": "#999"},
                                ),
                                html.P(
                                    "- Draw Circle - Mark areas",
                                    style={"fontSize": "11px", "marginLeft": "10px", "color": "#999"},
                                ),
                                html.P(
                                    "- Erase - Remove drawings",
                                    style={"fontSize": "11px", "marginLeft": "10px", "color": "#999"},
                                ),
                                html.Hr(),
                                html.H3("Set Scale"),
                                html.P("1. Draw a line of known length", style={"fontSize": "11px", "color": "#888"}),
                                html.P("2. Enter actual length below", style={"fontSize": "11px", "color": "#888"}),
                                html.Div(
                                    [
                                        dcc.Input(
                                            id="scale-length-input",
                                            type="number",
                                            placeholder="Length in meters",
                                            style={
                                                "width": "100%",
                                                "padding": "8px",
                                                "marginBottom": "8px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "#e0e0e0",
                                                "border": "1px solid #667eea",
                                                "borderRadius": "4px",
                                            },
                                        ),
                                        html.Button(
                                            "Set Scale from Last Line",
                                            id="set-scale-button",
                                            style={
                                                "width": "100%",
                                                "padding": "8px",
                                                "backgroundColor": "#667eea",
                                                "color": "white",
                                                "border": "none",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        html.Div(
                                            id="scale-status",
                                            style={"marginTop": "8px", "fontSize": "11px", "color": "#a0a0ff"},
                                        ),
                                    ]
                                ),
                                html.Hr(),
                                html.H3("Set Origin"),
                                html.P(
                                    "Click map to set coordinate origin", style={"fontSize": "11px", "color": "#888"}
                                ),
                                html.Div(
                                    [
                                        html.Button(
                                            "Enable Origin Setting Mode",
                                            id="origin-mode-button",
                                            n_clicks=0,
                                            style={
                                                "width": "100%",
                                                "padding": "8px",
                                                "marginBottom": "8px",
                                                "backgroundColor": "#3d3d3d",
                                                "color": "white",
                                                "border": "1px solid #667eea",
                                                "borderRadius": "4px",
                                                "cursor": "pointer",
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        html.Div(
                                            id="origin-status",
                                            children=[
                                                html.P(
                                                    f"Current: ({map_data.get('origin_x', 0)}, "
                                                    f"{map_data.get('origin_y', 0)})",
                                                    style={"fontSize": "11px", "color": "#888", "margin": "4px 0"},
                                                )
                                            ],
                                        ),
                                    ]
                                ),
                                html.Hr(),
                                html.H3("Location Zones"),
                                html.Div(
                                    [
                                        self._build_zone_toggle_widget(zones, dcc, html),
                                        html.Div(
                                            id="selected-zone-info",
                                            children=[
                                                html.P(
                                                    "Click a zone for details",
                                                    style={"fontSize": "11px", "color": "#888", "fontStyle": "italic"},
                                                )
                                            ],
                                            style={
                                                "padding": "10px",
                                                "backgroundColor": "#3d3d3d",
                                                "borderRadius": "4px",
                                                "marginTop": "10px",
                                            },
                                        ),
                                        (
                                            html.Div(
                                                [
                                                    html.Button(
                                                        "[EDIT] Edit Zone",
                                                        id="edit-zone-btn",
                                                        n_clicks=0,
                                                        style={
                                                            "width": "48%",
                                                            "marginRight": "4%",
                                                            "padding": "6px",
                                                            "backgroundColor": "#667eea",
                                                            "color": "white",
                                                            "border": "none",
                                                            "borderRadius": "4px",
                                                            "cursor": "pointer",
                                                            "fontSize": "12px",
                                                        },
                                                    ),
                                                    html.Button(
                                                        "[DEL] Remove Zone",
                                                        id="remove-zone-btn",
                                                        n_clicks=0,
                                                        style={
                                                            "width": "48%",
                                                            "padding": "6px",
                                                            "backgroundColor": "#ff4444",
                                                            "color": "white",
                                                            "border": "none",
                                                            "borderRadius": "4px",
                                                            "cursor": "pointer",
                                                            "fontSize": "12px",
                                                        },
                                                    ),
                                                ],
                                                style={"marginTop": "10px", "display": "flex"},
                                            )
                                            if zones
                                            else None
                                        ),
                                    ]
                                ),
                                html.Hr(),
                                html.H3("Map Info"),
                                html.Div(
                                    id="map-info",
                                    children=[
                                        html.P(
                                            [
                                                html.Span("Dimensions: ", className="info-badge"),
                                                f"{map_width} x {map_height} px",
                                            ]
                                        ),
                                        html.P(
                                            [
                                                html.Span("PPM: ", className="info-badge"),
                                                f"{map_data.get('ppm', 'N/A')}",
                                            ]
                                        ),
                                        html.P(
                                            [
                                                html.Span("Orientation: ", className="info-badge"),
                                                f"{map_data.get('orientation', 0)} deg",
                                            ]
                                        ),
                                        html.P([html.Span("Devices: ", className="info-badge"), f"{len(devices)}"]),
                                        html.P([html.Span("Clients: ", className="info-badge"), f"{len(clients)}"]),
                                        html.P([html.Span("Zones: ", className="info-badge"), f"{len(zones)}"]),
                                        html.P(
                                            [
                                                html.Span("vBeacons: ", className="info-badge"),
                                                f"{len(map_data.get('vbeacons', []))}",
                                            ]
                                        ),
                                        html.P(
                                            [
                                                html.Span("BLE Beacons: ", className="info-badge"),
                                                f"{len(map_data.get('beacons', []))}",
                                            ]
                                        ),
                                        html.P(
                                            [
                                                html.Span("Validation Paths: ", className="info-badge"),
                                                f"{len(map_data.get('sitesurvey_path', []))}",
                                            ]
                                        ),
                                    ],
                                ),
                                html.Hr(),
                                html.Div(
                                    id="click-data",
                                    children=[
                                        html.H3("Device Info"),
                                        html.P(
                                            "Click a device for details", style={"color": "#888", "fontStyle": "italic"}
                                        ),
                                    ],
                                ),
                            ],
                            className="sidebar",
                        ),
                    ],
                    className="main-container",
                ),
                # Hidden stores for state management
                dcc.Store(
                    id="map-config-store",
                    data=serializer.build_map_config(
                        site_id=site_id,
                        site_name=site_name,
                        map_id=map_id,
                        map_name=map_data.get("name", "Unknown"),
                        ppm=ppm,
                        map_width=map_width,
                        map_height=map_height,
                    ),
                ),
                # Store for available maps list (for dropdown)
                dcc.Store(
                    id="available-maps-store",
                    data=serializer.build_named_items(all_maps, default_name="Unnamed"),
                ),
                # Store for available sites list (for dropdown)
                dcc.Store(
                    id="available-sites-store",
                    data=serializer.build_named_items(all_sites, default_name="Unnamed Site"),
                ),
                # Store for tracking selected zone ID
                dcc.Store(id="selected-zone-store", data=serializer.build_selected_zone_store()),
                # Store for tracking last refresh times
                dcc.Store(id="refresh-times-store", data=serializer.build_refresh_times_store()),
                # Store to trigger map list refresh (cache bust) after clone/delete operations
                dcc.Store(id="cache-bust-store", data=serializer.build_cache_bust_store()),
                # Interval components for live refresh (enabled by default since auto-refresh is on)
                dcc.Interval(
                    id="client-refresh-interval",
                    interval=30 * 1000,  # 30 seconds in milliseconds
                    n_intervals=0,
                    disabled=False,  # Enabled by default with auto-refresh
                ),
                dcc.Interval(
                    id="coverage-refresh-interval",
                    interval=5 * 60 * 1000,  # 5 minutes in milliseconds
                    n_intervals=0,
                    disabled=False,  # Enabled by default with auto-refresh
                ),
                # Fast interval for countdown display (1 second)
                dcc.Interval(
                    id="countdown-tick-interval",
                    interval=1000,  # 1 second
                    n_intervals=0,
                    disabled=False,  # Enabled by default with auto-refresh
                ),
                # Location component for URL-based map switching
                dcc.Location(id="url-location", refresh=True),
                # Hidden div for map switch trigger
                html.Div(id="map-switch-trigger", style={"display": "none"}),
            ],
            style={"height": "100vh", "display": "flex", "flexDirection": "column"},
        )

        # Clientside callback for map switching - triggers page reload with new map_id in URL
        app.clientside_callback(
            """
            function(selected_map_id, config) {
                var current_map_id = config ? config.map_id : null;
                if (!selected_map_id || selected_map_id === current_map_id) {
                    return window.dash_clientside.no_update;
                }

                // Check if URL already has this map_id - if so, don't redirect (prevents loop)
                var urlParams = new URLSearchParams(window.location.search);
                var url_map_id = urlParams.get('map_id');
                if (url_map_id === selected_map_id) {
                    console.log('Map switch: URL already has map_id=' + selected_map_id + ', skipping redirect');
                    return window.dash_clientside.no_update;
                }

                // Redirect to URL with map_id parameter (preserve site_id if present)
                var site_id = urlParams.get('site_id') || (config ? config.site_id : null);
                var new_url = '/?map_id=' + selected_map_id;
                if (site_id) {
                    new_url += '&site_id=' + site_id;
                }
                console.log('Map switch: redirecting to map_id=' + selected_map_id);
                window.location.href = new_url;
                return '';
            }
            """,
            Output("map-switch-trigger", "children"),
            [Input("map-selector-dropdown", "value")],
            [State("map-config-store", "data")],
            prevent_initial_call=True,
        )

        # Clientside callback to reload page after clone/delete to get fresh map data
        app.clientside_callback(
            """
            function(cache_bust_data) {
                if (!cache_bust_data || !cache_bust_data.trigger) {
                    return window.dash_clientside.no_update;
                }
                // Check if this trigger was already processed (stored in sessionStorage)
                var lastTrigger = parseInt(sessionStorage.getItem('lastCacheBustTrigger') || '0');
                var currentTrigger = cache_bust_data.trigger;

                // Only reload if trigger is NEW (greater than last processed)
                if (currentTrigger > lastTrigger) {
                    console.log('Cache bust: Reloading page to refresh map data '
                        + '(trigger=' + currentTrigger + ', last=' + lastTrigger + ')');
                    // Store this trigger as processed before reloading
                    sessionStorage.setItem('lastCacheBustTrigger', currentTrigger.toString());
                    // Small delay to allow status message to display briefly
                    setTimeout(function() {
                        window.location.reload();
                    }, 1500);
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output("map-switch-trigger", "children", allow_duplicate=True),
            [Input("cache-bust-store", "data")],
            prevent_initial_call=True,
        )

        # Wave E2: handle_site_switch_from_dropdown, handle_site_from_url, sync_dropdown_with_url,
        # and handle_url_map_switch now live in MapViewerCallbacks (registered below via
        # viewer_callbacks.register_with(app)).
        # Wave-A: register the 5 trivial UI-toggle callbacks via the
        # extracted MapViewerCallbacks. This replaces the nested defs
        # for apply_layer_toggles and display_click_data (and three more below).
        # Waves B+C extend MapViewerCallbacks with 8 more callbacks
        # (zone/panel toggles, origin click, delete map, label updates,
        # zone actions). register_with(app) wires all 13 at once.
        viewer_callbacks.register_with(app)  # Wires 13 callbacks (waves A+B+C)

        # Wave C: update_shape_labels now lives in MapViewerCallbacks
        # (registered above via viewer_callbacks.register_with(app)).

        # Wave E2: set_scale now lives in MapViewerCallbacks (registered below via
        # viewer_callbacks.register_with(app)).
        # Wave E2: api_session_ref closure removed; refresh callback now uses self._state.api_session_ref.

        # Wave E1: execute_clone_operation now lives in MapViewerCallbacks
        # (registered above via viewer_callbacks.register_with(app)).

        # Wave E2: refresh_map_dropdown now lives in MapViewerCallbacks (registered below via
        # viewer_callbacks.register_with(app)).
        # Wave D: refresh_client_positions (now update_clients_traces) and refresh_rf_coverage
        # (now update_coverage_heatmap) live in MapViewerCallbacks and are registered above
        # via viewer_callbacks.register_with(app).

        # Wave E2: dash binding + server boot extracted into helpers to drop parent CC.
        dash_host, dash_port = self._resolve_dash_binding(os)  # Network binding + port
        self._print_dash_startup_banner(dash_host, dash_port)  # User-facing banner
        self._schedule_browser_open(dash_port)  # Background browser open (no-op in containers)
        self._run_dash_server(app, dash_host, dash_port)  # Runs server + handles KeyboardInterrupt/Exception

    @staticmethod
    def _open_browser_after_delay(dash_port: int) -> None:
        """Wait for the Dash server to start, then open the system browser to the viewer URL."""
        import time  # Local import keeps top-of-file imports minimal
        import webbrowser  # Stdlib browser launcher

        logging.info("Browser auto-open: scheduling open to http://127.0.0.1:%s", dash_port)  # Trace start
        time.sleep(1.5)  # Wait for Dash server to initialize (matches original delay)
        webbrowser.open(f"http://127.0.0.1:{dash_port}")  # Launch system browser
        logging.debug("Browser opened to http://127.0.0.1:%s", dash_port)  # Mirror original log

    # ------------------------------------------------------------------
    # Wave E2 helpers extracted from _launch_plotly_viewer to drive CC <= 10
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_coverage_count(coverage_data: dict | None) -> int:
        """Return the number of grid results in ``coverage_data`` (0 if missing)."""
        if not coverage_data:  # Original used a ternary; explicit guard preserves behavior
            return 0
        return len(coverage_data.get("results", []))

    @staticmethod
    def _normalize_optional_lists(all_maps: list | None, all_sites: list | None) -> tuple[list, list]:
        """Coalesce optional list args to empty lists (drops two BoolOps from parent CC)."""
        return all_maps if all_maps else [], all_sites if all_sites else []

    def _try_import_dash_modules(self, map_data: dict, devices: list) -> tuple | None:
        """Import dash + companions; on ImportError run the static fallback and return ``None``."""
        logging.info("_try_import_dash_modules: attempting to import dash")  # Trace start
        try:
            logging.debug("Importing Dash modules for interactive viewer")  # Mirror original log
            import dash  # Heavy module; local import keeps top-of-file imports minimal
            from dash import Dash, Input, Output, State, dcc, html, no_update  # Names used in layout/callbacks

            logging.info("Dash version: %s", dash.__version__)  # Mirror original log
            return dash, Dash, Input, Output, State, dcc, html, no_update
        except ImportError as e:  # Fallback path (mirrors original except block)
            logging.exception("Failed to import Dash, falling back to static view: %s", e)
            print("\n! Dash not available - using static Plotly view only")
            print("! Install with: pip install dash")
            self._create_static_plotly_map(map_data, devices)  # Render static figure instead
            return None

    @staticmethod
    def _print_viewer_intro_banner() -> None:
        """Print the user-facing 'LAUNCHING INTERACTIVE MAP VIEWER' banner (no decisions)."""
        print("\n" + "-" * 80)
        print("LAUNCHING INTERACTIVE MAP VIEWER")
        print("-" * 80)
        print("! Opening web browser with interactive map...")
        print("! Features:")
        print("!   - Toggle layers (walls, zones, wayfinding, devices, clients)")
        print("!   - Live data refresh (clients update every 30s, RF every 5min)")
        print("!   - Ruler tool - Draw lines to measure distances")
        print("!   - Connected client visualization (green dots)")
        print("!   - Click devices/clients to see details")
        print("!   - Drag devices to new positions (future: save to cloud)")
        print("!   - Pan and zoom")
        print("! Press Ctrl+C in terminal to stop server")
        print("-" * 80)

    @staticmethod
    def _add_background_image_to_figure(fig: object, map_data: dict, map_width: int, map_height: int) -> None:
        """Add the map background image to the figure (gates the URL check internally)."""
        if "url" not in map_data:  # Mirror original else-branch behavior
            logging.warning("Map has no background image URL")
            return
        logging.debug("Adding map background image: %s...", str(map_data.get("url"))[:100])  # Mirror log
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
            logging.debug("Device '%s': orientation=%s", device_name, device_orientation)

    @staticmethod
    def _add_device_marker_trace(
        fig: object,
        coords: dict[str, list],
        type_cfg: dict,
        colors: list[str],
        hover_text: list[str],
    ) -> None:
        """Add the per-type marker Scatter trace (preserves original styling exactly)."""
        import plotly.graph_objects as go  # Local import keeps top-level light

        fig.add_trace(
            go.Scatter(
                x=coords["x_coords"],
                y=coords["y_coords"],
                mode="markers",
                name=type_cfg["name"],
                marker=dict(
                    symbol=type_cfg["symbol"],
                    size=type_cfg["size"],
                    color=colors,
                    line=dict(color="white", width=2),
                    opacity=0.9,
                ),
                hovertext=hover_text,
                hoverinfo="text",
                visible=True,
                showlegend=True,
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
    def _add_origin_crosshair(fig: object, map_data: dict) -> None:
        """Add a blue crosshair (horizontal line + vertical line + center dot) at the origin point."""
        import plotly.graph_objects as go  # Local import keeps top-level light

        origin_x = map_data.get("origin_x", 0)  # Pixel-space origin x
        origin_y = map_data.get("origin_y", 0)  # Pixel-space origin y
        crosshair_size = 40  # Match original size
        fig.add_trace(  # Horizontal line
            go.Scatter(
                x=[origin_x - crosshair_size, origin_x + crosshair_size],
                y=[origin_y, origin_y],
                mode="lines",
                line=dict(color="#00bfff", width=3),
                name="Origin",
                showlegend=True,
                hovertext=f"Origin: ({origin_x}, {origin_y})",
                hoverinfo="text",
            )
        )
        fig.add_trace(  # Vertical line
            go.Scatter(
                x=[origin_x, origin_x],
                y=[origin_y - crosshair_size, origin_y + crosshair_size],
                mode="lines",
                line=dict(color="#00bfff", width=3),
                showlegend=False,
                hovertext=f"Origin: ({origin_x}, {origin_y})",
                hoverinfo="text",
            )
        )
        fig.add_trace(  # Center dot
            go.Scatter(
                x=[origin_x],
                y=[origin_y],
                mode="markers",
                marker=dict(size=12, color="#00bfff", line=dict(color="white", width=2)),
                name="Origin Point",
                showlegend=False,
                hovertext=f"Origin: ({origin_x}, {origin_y})",
                hoverinfo="text",
            )
        )

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
        print("\nStarting Dash server...")
        if is_running_in_container():  # Container-specific lines
            print(f"! Map viewer available at http://<container-ip>:{dash_port}")
            print(f"! Access from host: http://localhost:{dash_port} (if port is mapped)")
        else:
            print("! Map viewer will open in your default browser")
        print("! Press Ctrl+C to stop the server\n")
        logging.info("Starting Dash server on http://%s:%s", dash_host, dash_port)  # Mirror original log

    def _schedule_browser_open(self, dash_port: int) -> None:
        """Start a daemon thread that opens the browser shortly after server boots (skip in container)."""
        if is_running_in_container():  # No display in container; skip browser
            return
        import threading  # Local import keeps top-of-file lean

        threading.Thread(  # Background thread -> _open_browser_after_delay
            target=self._open_browser_after_delay, args=(dash_port,), daemon=True
        ).start()

    @staticmethod
    def _run_dash_server(app: object, dash_host: str, dash_port: int) -> None:
        """Run the Dash server with the project's standard kwargs, handling Ctrl+C + errors."""
        try:
            debug_mode = getattr(globals().get("args"), "debug", False)  # CLI --debug flag if present
            logging.info("Starting Dash server with debug_mode=%s", debug_mode)  # Mirror original log
            app.run(  # Dash 3.x uses app.run() instead of app.run_server()
                host=dash_host,
                port=dash_port,
                debug=debug_mode,
                use_reloader=False,  # Disable reloader to prevent double-execution
                threaded=True,
            )
        except KeyboardInterrupt:  # Mirror original user-cancel path
            print("\n\nMap viewer stopped by user")
            logging.info("Interactive map viewer stopped by user (Ctrl+C)")
        except Exception as e:  # Mirror original catch-all
            logging.exception("Error running Dash server: %s", e)
            print(f"\n! Error running map viewer: {e}")

    def _create_static_plotly_map(self, map_data, devices):
        """Create static Plotly HTML map when Dash is not available."""
        import os
        import tempfile
        import webbrowser

        import plotly.graph_objects as go

        print("\n! Creating static HTML map...")

        # Similar to _launch_plotly_viewer but save to HTML file
        fig = go.Figure()

        map_width = map_data.get("width", 1000)
        map_height = map_data.get("height", 1000)

        if "url" in map_data:
            fig.add_layout_image(
                source=map_data["url"],
                x=0,
                y=map_height,
                sizex=map_width,
                sizey=map_height,
                xref="x",
                yref="y",
                sizing="stretch",
                layer="below",
            )

        # Add devices (simplified version)
        if devices:
            x_coords = [d.get("x", 0) for d in devices if "x" in d]
            y_coords = [map_height - d.get("y", 0) for d in devices if "y" in d]
            names = [d.get("name", d.get("mac", "Unknown")) for d in devices if "x" in d]

            fig.add_trace(
                go.Scatter(
                    x=x_coords,
                    y=y_coords,
                    mode="markers+text",
                    name="Devices",
                    marker=dict(size=10, color="green"),
                    text=names,
                    textposition="top center",
                )
            )

        fig.update_layout(
            title=f"Map: {map_data.get('name', 'Unnamed')}",
            xaxis=dict(range=[0, map_width]),
            yaxis=dict(range=[0, map_height], scaleanchor="x", scaleratio=1),
            height=800,
        )

        # Save to temp HTML file
        temp_html = os.path.join(tempfile.gettempdir(), f"mist_map_{map_data.get('id', 'unknown')[:8]}.html")
        logging.debug("Saving static map to: %s", temp_html)
        fig.write_html(temp_html)

        print(f"\n! Map saved to: {temp_html}")
        print("! Opening in browser...")
        logging.info("Static HTML map created: %s", temp_html)
        webbrowser.open(f"file://{temp_html}")
        logging.debug("Browser launched with static map")


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
    return _PlotlyViewer(maps_manager)._launch_plotly_viewer(scope, data, optional)
