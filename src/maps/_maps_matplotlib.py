"""Matplotlib viewer + standalone launcher cluster (extracted from MapsManager).

Split out of ``src/maps/maps_manager.py`` so the ~165 LOC matplotlib
fallback viewer + standalone-launch flow lives in its own module. The
extracted methods stay as methods of a small wrapper class
:class:`_MapsMatplotlib`; ``__getattr__`` delegates lookups that miss
on the wrapper to the wrapped MapsManager, so calls to
``self._collect_map_payload``, ``self._build_map_data_response``,
``self.apisession``, and other shared state resolve without rewrites.

MapsManager keeps a slim ``launch_viewer_standalone`` delegating method
because ``main()`` in the same file invokes it as
``maps_manager.launch_viewer_standalone()``.
"""

from __future__ import annotations  # Enable PEP 604 style unions on 3.10+ runtimes.

import logging  # Module-level structured logger for the viewer workflow.
from collections.abc import Callable  # Callable type from stdlib collections.abc (modern import).
from dataclasses import dataclass  # Frozen bundle helpers to satisfy the 5-item rule.
from math import cos, radians, sin  # Trigonometry for the orientation-arrow computation.
from typing import Any  # Loose typing for Mist API JSON payloads.

import matplotlib.pyplot as plt  # Plot backend used by the fallback matplotlib viewer.
import mistapi  # Mist API SDK used for listing site maps and related endpoints.

from src.maps._flask_viewer import FlaskViewerContext, launch_flask_viewer  # Viewer entry + context bundle.

logger = logging.getLogger(__name__)  # Module logger keyed to this file for filtering.

# Default map canvas dimensions used when the payload omits width/height.
_DEFAULT_MAP_WIDTH: int = 1000  # Fallback horizontal pixel extent when payload lacks width.
_DEFAULT_MAP_HEIGHT: int = 1000  # Fallback vertical pixel extent when payload lacks height.
_DEFAULT_MAP_NAME: str = "Unnamed"  # Fallback title fragment when payload lacks a name.

# Figure size and cosmetic constants for the matplotlib fallback viewer.
_FIGURE_SIZE: tuple[int, int] = (12, 10)  # Inches (w, h) for the matplotlib figure surface.
_MARKER_SIZE: int = 10  # Point size used for each device marker.
_LABEL_FONT_SIZE: int = 8  # Point size for device text labels above markers.
_LABEL_Y_OFFSET: int = 20  # Pixel offset so labels sit above markers, not overlapping them.
_ARROW_LENGTH: int = 30  # Length of the orientation arrow drawn from the marker origin.
_ARROW_HEAD: int = 10  # Head width/length shared for the orientation arrow rendering.
_ARROW_ALPHA: float = 0.7  # Alpha channel so arrows remain readable over background.
_GRID_ALPHA: float = 0.3  # Alpha for the axes grid to keep it subtle behind markers.

# Device-type -> marker color lookup, gray for anything unrecognized.
_DEVICE_COLORS: dict[str, str] = {
    "ap": "green",  # Access points render in green.
    "switch": "orange",  # Switches render in orange.
    "gateway": "purple",  # Gateways render in purple.
}
_FALLBACK_COLOR: str = "gray"  # Color used for unknown device types.
_UNKNOWN_TYPE: str = "unknown"  # Placeholder type when a device dict omits `type`.
_UNKNOWN_NAME: str = "Unknown"  # Placeholder label used when name and mac are absent.
_MARKER_SHAPE: str = "o"  # Matplotlib marker glyph for device dots.

# Default site name preferred at bootstrap when no explicit site is requested.
_PREFERRED_DEFAULT_SITE: str = "CAS0123G"  # Historically the first site staff want to open.

# HTTP status treated as a successful GET by the Mist client for entity fetches.
_OK_READ_STATUS: int = 200  # Only 200 counts as a successful read from the Mist API.

# Device stats API keyword args used when hydrating the standalone viewer.
_DEVICE_STATS_KW: dict[str, Any] = {"type": "all", "limit": 1000}  # Hydrate every device up to page cap.

_BANNER_WIDTH: int = 70  # Column width for the standalone banner separators.


@dataclass(frozen=True, slots=True)  # Frozen slots keep canvas metadata immutable.
class _MapBounds:  # Bundle of canvas metadata plotted before device markers.
    """Bundle of canvas metadata plotted before device markers."""

    width: int  # Canvas width in pixels for xlim.
    height: int  # Canvas height in pixels for ylim.
    title: str  # Preformatted title string for the axes.


@dataclass(frozen=True, slots=True)  # Frozen slots keep marker style immutable.
class _DeviceMarker:  # Bundle of coordinates and style for a single device marker.
    """Bundle of coordinates and style for a single device marker."""

    x: float  # Horizontal position in canvas pixels.
    y: float  # Vertical position in canvas pixels.
    label: str  # Human-readable text drawn above the marker.
    color: str  # Matplotlib color string keyed to device type.
    device_type: str  # Original device type used for legend deduplication.
    orientation: float  # Bearing in degrees; 0 means no arrow gets drawn.


@dataclass(frozen=True, slots=True)  # Frozen slots keep entity snapshot immutable.
class _MapEntities:  # Bundle of hydrated entities for the initial map load.
    """Bundle of hydrated entities for the initial map load."""

    devices: list[dict[str, Any]]  # Device stats records filtered to the current map.
    zones: list[dict[str, Any]]  # Zone records filtered to the current map.
    clients: list[dict[str, Any]]  # Wireless client records filtered to the current map.


@dataclass(frozen=True, slots=True)  # Frozen slots keep target bundle immutable.
class _StandaloneTargets:  # Bundle of resolved site/map handles used to launch the Flask viewer.
    """Bundle of resolved site/map handles used to launch the Flask viewer."""

    site_id: str  # Site UUID selected as the viewer's initial focus.
    site_name: str  # Human-readable site name for status output.
    map_id: str | None  # Map UUID selected, or None when the site has no maps.
    all_maps: list[dict[str, Any]]  # Full map list belonging to the resolved site.


class _MapsMatplotlib:  # Wrapper class holding the extracted matplotlib/launch methods.
    """Wrapper class holding the extracted matplotlib/launch methods."""

    def __init__(self, maps_manager: Any) -> None:  # Store wrapped manager for delegation.
        self._mm = maps_manager  # Retain manager for delegation via __getattr__.

    def __getattr__(self, name: str) -> Any:  # Forward unknown attrs to the wrapped MapsManager.
        mm = self.__dict__.get("_mm")  # Access instance dict directly to avoid recursion.
        if mm is None:  # Broken-init guard: _mm was never assigned.
            raise AttributeError(name)  # Only reachable if __init__ never assigned _mm.
        return getattr(mm, name)  # Delegate all missing lookups to the wrapped manager.

    def _launch_matplotlib_viewer(
        self, map_data: dict[str, Any], devices: list[dict[str, Any]]
    ) -> None:  # Fallback viewer entry.
        """Fallback matplotlib viewer (view-only)."""
        logging.info("_launch_matplotlib_viewer called - basic fallback mode")  # Trace entry.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.warning("\n! Using matplotlib viewer (view-only, no interactivity)")
        logging.debug("Creating matplotlib figure for basic visualization")  # Debug breadcrumb.
        bounds = _extract_bounds(map_data)  # Read canvas dims/title with safe defaults.
        _fig, ax = plt.subplots(figsize=_FIGURE_SIZE)  # Create the plotting surface.
        _configure_axes(ax, bounds)  # Apply canvas limits, aspect, title, labels.
        _plot_devices(ax, devices)  # Draw every valid device marker.
        ax.legend()  # Show legend keyed by device-type entries added during plotting.
        ax.grid(True, alpha=_GRID_ALPHA)  # Light grid for spatial orientation.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\n! Displaying map... Close window to return to menu")
        logging.info("Displaying matplotlib figure (blocking until window closed)")  # Trace.
        plt.show()  # Blocking call until user closes the window.
        logging.info("Matplotlib map viewer closed by user")  # Trace after return.

    def _resolve_initial_site(
        self, sites_sorted: list[dict[str, Any]], requested_site_id: str | None
    ) -> tuple[str, str]:  # Site pick.
        """Resolve the initial site for standalone viewer from requested or default."""
        if requested_site_id:  # Honor explicit request first when caller supplied one.
            match = _find_by_id(sites_sorted, requested_site_id)  # Lookup by id in the sorted list.
            if match is not None:  # Requested site is present in the org.
                return _site_tuple(match)  # Return the requested site handle.
        default_site = _find_named_default(sites_sorted)  # Try the preferred default site by name.
        chosen = default_site or sites_sorted[0]  # Fallback to first site alphabetically.
        return _site_tuple(chosen)  # Return the resolved fallback handle.

    def _resolve_initial_map(
        self, all_maps: list[dict[str, Any]], requested_map_id: str | None
    ) -> tuple[str, dict[str, Any]]:  # Map pick.
        """Resolve the initial map from requested or first available."""
        if requested_map_id:  # Only build the id lookup when a request was made.
            match = _find_by_id(all_maps, requested_map_id)  # Reuse shared id-lookup helper.
            if match is not None:  # Requested map exists on this site.
                return requested_map_id, match  # Return the requested map tuple.
        first = all_maps[0]  # Fallback to first map when nothing else matched.
        return str(first.get("id", "")), first  # Cast id to str for mypy strict return type.

    def _fetch_entities_on_map(
        self, api_fn: Callable[..., Any], site_id: str, map_id: str, **kwargs: Any
    ) -> list[dict[str, Any]]:  # Fetch + filter helper.
        """Call api_fn for site_id, return entities filtered to map_id."""
        resp = _safe_api_call(api_fn, self.apisession, site_id, kwargs)  # Swallow API errors as None.
        return _filter_response_by_map(resp, map_id)  # Handle status/data checks + filter downstream.

    def _fetch_site_maps(self, site_id: str) -> list[dict[str, Any]]:
        """Fetch maps for a site. Return empty list on failure."""
        try:
            resp = mistapi.api.v1.sites.maps.listSiteMaps(self.apisession, site_id=site_id)  # Mist API call.
        except Exception as error:
            logging.error("Error fetching maps for site %s: %s", site_id, error)  # Log and fall through.
            return []
        if resp.status_code != _OK_READ_STATUS or not resp.data:
            return []  # Non-200 or empty body both yield an empty list.
        data: list[dict[str, Any]] = resp.data  # Local var narrows Any -> list[dict] for mypy strict.
        return data  # Hand data back to caller unchanged.

    def launch_viewer_standalone(
        self, requested_site_id: str | None = None, requested_map_id: str | None = None
    ) -> None:
        """Launch the standalone Flask viewer. Site/map picked in-browser."""
        _print_banner()  # Announce mode to the operator.
        sites_sorted = self._bootstrap_sites()  # Fetch and sort or return None on empty.
        if sites_sorted is None:
            return  # Nothing to launch when the org has zero sites.
        targets = self._resolve_targets(sites_sorted, requested_site_id, requested_map_id)  # Site+map handles.
        entities = self._hydrate_initial_entities(targets)  # Fetch devices/zones/clients.
        _print_entity_counts(entities, targets)  # Give operator quick feedback.
        self._open_flask_view(sites_sorted, targets)  # Delegate to the Flask viewer helper.

    def _open_flask_view(self, sites_sorted: list[dict[str, Any]], targets: _StandaloneTargets) -> None:
        """Log the launch, then invoke the Flask viewer with wrapped session + callbacks."""
        logging.info(  # Audit line captured before the blocking Flask process starts.
            "Launching Flask viewer for site=%s map=%s (sites loaded=%d)",
            targets.site_id,
            targets.map_id,
            len(sites_sorted),
        )
        launch_flask_viewer(
            FlaskViewerContext(
                api_session=self.apisession,  # Authenticated Mist API session passed through.
                initial_site_id=targets.site_id,  # Site selected for the initial render.
                initial_map_id=targets.map_id,  # Map selected for the initial render.
                all_sites=sites_sorted,  # Sorted site list for the site picker dropdown.
                all_maps=targets.all_maps,  # Map list for the initial site.
                collect_payload_fn=self._collect_map_payload,  # Callback that hydrates payload entities.
                build_response_fn=self._build_map_data_response,  # Callback that shapes the JSON reply.
            )
        )  # Delegate to the Flask-based interactive viewer.

    def _bootstrap_sites(self) -> list[dict[str, Any]] | None:
        """Fetch and sort all org sites. Return None when the org has none."""
        logging.info("launch_viewer_standalone: Starting web-first viewer mode")  # Trace entry.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\n  Loading sites...")
        all_sites = self._fetch_sites()  # Delegated to MapsManager via __getattr__.
        if not all_sites:
            # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
            logger.warning("\n  [!] No sites found in organization")
            return None  # Signal the caller to abort the launch.
        sites_sorted = sorted(all_sites, key=_site_sort_key)  # Alphabetic case-insensitive sort by name.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("  Found %s sites", len(sites_sorted))
        return sites_sorted  # Ready-to-use, ordered site list.

    def _resolve_targets(
        self,
        sites_sorted: list[dict[str, Any]],
        requested_site_id: str | None,
        requested_map_id: str | None,
    ) -> _StandaloneTargets:
        """Resolve site + map targets that the Flask viewer will bootstrap with."""
        site_id, site_name = self._resolve_initial_site(sites_sorted, requested_site_id)  # Reuse core helper.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("  Loading maps for site: %s...", site_name)
        all_maps = self._fetch_site_maps(site_id)  # May be empty on API/no-map failures.
        if not all_maps:
            _print_no_maps_notice(site_name)  # Tell the user we are deferring selection to the browser.
            return _StandaloneTargets(site_id, site_name, None, all_maps)  # Return with map_id=None sentinel.
        map_id, target_map = self._resolve_initial_map(all_maps, requested_map_id)  # Pick initial map handle.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("  Loading map: %s...", target_map.get("name", _DEFAULT_MAP_NAME))
        return _StandaloneTargets(site_id, site_name, map_id, all_maps)  # Return fully-resolved bundle.

    def _hydrate_initial_entities(self, targets: _StandaloneTargets) -> _MapEntities:
        """Fetch devices/zones/clients for the initial map (empty when unknown)."""
        if targets.map_id is None:
            return _MapEntities([], [], [])  # Skip API calls when there is no map focus yet.
        devices = self._fetch_entities_on_map(
            mistapi.api.v1.sites.stats.listSiteDevicesStats,
            targets.site_id,
            targets.map_id,
            **_DEVICE_STATS_KW,
        )  # Full page of device stats scoped to the initial map.
        zones = self._fetch_entities_on_map(
            mistapi.api.v1.sites.zones.listSiteZones, targets.site_id, targets.map_id
        )  # Zone records scoped to the initial map.
        clients = self._fetch_entities_on_map(
            mistapi.api.v1.sites.stats.listSiteWirelessClientsStats, targets.site_id, targets.map_id
        )  # Wireless client stats scoped to the initial map.
        return _MapEntities(devices, zones, clients)  # Bundle every hydrated collection.


def _extract_bounds(map_data: dict[str, Any]) -> _MapBounds:
    """Read canvas metadata from a Mist map payload with safe fallbacks."""
    return _MapBounds(
        width=map_data.get("width", _DEFAULT_MAP_WIDTH),  # Fallback width when absent.
        height=map_data.get("height", _DEFAULT_MAP_HEIGHT),  # Fallback height when absent.
        title=f"Map: {map_data.get('name', _DEFAULT_MAP_NAME)}",  # Preformatted title string.
    )


def _configure_axes(ax: Any, bounds: _MapBounds) -> None:
    """Apply canvas limits, aspect, title and labels to a matplotlib Axes."""
    ax.set_xlim(0, bounds.width)  # Left/right pixel extents from bundle.
    ax.set_ylim(0, bounds.height)  # Bottom/top pixel extents from bundle.
    ax.set_aspect("equal")  # Preserve real-world proportions.
    ax.set_title(bounds.title)  # Human-readable map name in the title.
    ax.set_xlabel("X (pixels)")  # Label for horizontal axis units.
    ax.set_ylabel("Y (pixels)")  # Label for vertical axis units.


def _plot_devices(ax: Any, devices: list[dict[str, Any]]) -> None:
    """Draw every valid device on the axes. Skip records without coordinates."""
    for device in devices:  # Iterate through hydrated device list once.
        marker = _device_to_marker(device)  # Build marker bundle or None sentinel.
        if marker is None:
            continue  # Skip records missing x/y coordinates.
        _draw_marker(ax, marker)  # Draw the marker dot and its text label.
        _draw_orientation_arrow(ax, marker)  # Optional arrow when orientation is nonzero.


def _device_to_marker(device: dict[str, Any]) -> _DeviceMarker | None:
    """Convert a raw device dict into a marker bundle, or None when unusable."""
    if "x" not in device or "y" not in device:
        return None  # Guard clause for coordinateless devices.
    device_type = device.get("type", _UNKNOWN_TYPE)  # Default type keeps color/legend logic total.
    return _DeviceMarker(
        x=device["x"],  # Known-present x coordinate.
        y=device["y"],  # Known-present y coordinate.
        label=device.get("name", device.get("mac", _UNKNOWN_NAME)),  # Prefer name, then mac, then Unknown.
        color=_DEVICE_COLORS.get(device_type, _FALLBACK_COLOR),  # Table-driven color dispatch.
        device_type=device_type,  # Retain for legend dedup below.
        orientation=device.get("orientation", 0),  # Zero means no arrow later.
    )


def _draw_marker(ax: Any, marker: _DeviceMarker) -> None:
    """Plot the marker point and label. Register legend entry once per type."""
    legend_label = _legend_label_for(ax, marker.device_type)  # Dedup legend entries by type.
    ax.plot(
        marker.x,
        marker.y,
        marker=_MARKER_SHAPE,
        markersize=_MARKER_SIZE,
        color=marker.color,
        label=legend_label,
    )  # Render the point with type-keyed style.
    ax.text(
        marker.x,
        marker.y + _LABEL_Y_OFFSET,
        marker.label,
        fontsize=_LABEL_FONT_SIZE,
        ha="center",
    )  # Draw the text label above the marker.


def _legend_label_for(ax: Any, device_type: str) -> str:
    """Return an empty label when this device type already has a legend entry."""
    existing = ax.get_legend_handles_labels()[1]  # Names already registered in legend.
    return device_type if device_type not in existing else ""  # Blank suppresses duplicate legend rows.


def _draw_orientation_arrow(ax: Any, marker: _DeviceMarker) -> None:
    """Draw the orientation arrow when the device carries a non-zero heading."""
    if marker.orientation == 0:
        return  # Skip drawing when no heading is set.
    dx = _ARROW_LENGTH * cos(radians(marker.orientation))  # X delta from bearing.
    dy = _ARROW_LENGTH * sin(radians(marker.orientation))  # Y delta from bearing.
    ax.arrow(
        marker.x,
        marker.y,
        dx,
        dy,
        head_width=_ARROW_HEAD,
        head_length=_ARROW_HEAD,
        fc=marker.color,
        ec=marker.color,
        alpha=_ARROW_ALPHA,
    )  # Render orientation arrow with type-keyed color.


def _find_by_id(records: list[dict[str, Any]], target_id: str) -> dict[str, Any] | None:
    """Return the first record whose id matches target_id, or None."""
    return next((r for r in records if r.get("id") == target_id), None)  # Linear scan. Lists are small.


def _find_named_default(sites_sorted: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the site named `_PREFERRED_DEFAULT_SITE`, or None if absent."""
    return next((s for s in sites_sorted if s.get("name", "") == _PREFERRED_DEFAULT_SITE), None)  # Name match.


def _site_tuple(site: dict[str, Any]) -> tuple[str, str]:
    """Extract (id, name) tuple with a safe name default for logging."""
    site_id = str(site.get("id", ""))  # Cast Any->str. Missing id becomes empty string.
    site_name = str(site.get("name", _UNKNOWN_NAME))  # Cast Any->str. Fallback preserves prior behavior.
    return site_id, site_name  # Consistent (str, str) tuple for mypy strict.


def _site_sort_key(site: dict[str, Any]) -> str:
    """Return the lowercase site name for case-insensitive alpha sorting."""
    return str(site.get("name", "")).lower()  # Cast Any->str before .lower() for mypy strict.


def _safe_api_call(api_fn: Callable[..., Any], apisession: Any, site_id: str, kwargs: dict[str, Any]) -> Any:
    """Invoke api_fn. Return None on any raised exception (caller treats as empty)."""
    try:
        return api_fn(apisession, site_id=site_id, **kwargs)  # Delegate the actual API call.
    except Exception:
        return None  # Silent failure. Caller returns empty list downstream.


def _filter_response_by_map(resp: Any, map_id: str) -> list[dict[str, Any]]:
    """Return entries whose `map_id` matches. Empty list on any failure."""
    if not _is_ok_response(resp):
        return []  # Non-OK responses collapse into the empty-list result.
    return _entries_for_map(resp.data, map_id)  # Delegate matching to comprehension helper.


def _is_ok_response(resp: Any) -> bool:
    """True when resp exists and reports HTTP 200 status."""
    if resp is None:
        return False  # Exception-swallowed API call returned None.
    return bool(resp.status_code == _OK_READ_STATUS)  # bool() cast keeps mypy strict happy.


def _entries_for_map(data: Any, map_id: str) -> list[dict[str, Any]]:
    """Filter Mist entities matching map_id, tolerating None payloads."""
    return [entity for entity in (data or []) if entity.get("map_id") == map_id]  # Same-map only.


def _print_banner() -> None:
    """Print the standalone-viewer banner block."""
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.info("\n%s", "=" * _BANNER_WIDTH)  # Top rule.
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.info("  MAPS MANAGER - Standalone Web Viewer")  # Title line.
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.info("  Select a site and map from the browser interface")  # Subtitle line.
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.info("%s", "=" * _BANNER_WIDTH)  # Bottom rule.


def _print_no_maps_notice(site_name: str) -> None:
    """Notify the user that the target site has no maps yet."""
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.warning("\n  [!] No maps found for site %s", site_name)  # Explicit empty-site notice.
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.info("  Launching viewer anyway - select a different site in browser")  # Guidance to switch.


def _print_entity_counts(entities: _MapEntities, targets: _StandaloneTargets) -> None:
    """Print the hydrated entity counts unless the initial map is undecided."""
    if targets.map_id is None:
        return  # Nothing meaningful to report without a chosen map.
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.info(
        "  Found %s devices, %s zones, %s clients",
        len(entities.devices),
        len(entities.zones),
        len(entities.clients),
    )


def launch_viewer_standalone(maps_manager: Any) -> None:
    """Entry point mirroring MapsManager.launch_viewer_standalone.

    Kept as a module-level factory so callers can invoke the standalone
    viewer without instantiating :class:`_MapsMatplotlib` directly.
    """
    _MapsMatplotlib(maps_manager).launch_viewer_standalone()  # Instantiate wrapper and invoke method.
