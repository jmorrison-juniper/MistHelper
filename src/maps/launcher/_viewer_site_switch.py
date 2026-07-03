"""Site/scale/dropdown cluster extracted from ``viewer_callbacks.py``.

Owns the Wave-E2 public callbacks ``set_scale``, ``refresh_map_dropdown``,
``handle_site_from_url``, ``sync_dropdown_with_url`` and
``handle_site_switch_from_dropdown`` plus their 21 private helpers
(scale calibration, site payload construction, background image
injection, device trace rendering).  Follows the same wrapper-class +
``__getattr__`` template used by :mod:`src.capture._packet_capture_org`
so the parent
:class:`~src.maps.launcher.viewer_callbacks.MapViewerCallbacks` stays a
thin coordinator that hands each Dash callback off to the appropriate
cluster.
"""

from __future__ import annotations  # WHY: postponed evaluation consistent with parent module

import logging  # WHY: audit trail for site-switch diagnostics
from typing import TYPE_CHECKING, Any  # WHY: opaque manager + type-permissive Dash callback args

if TYPE_CHECKING:  # WHY: keep dash imports lazy at runtime
    from dash import Dash  # WHY: annotation reference for register(app)


class _ViewerSiteSwitch:  # WHY: wrapper class hosting the site-switch callback cluster
    """Cluster class holding the extracted site/scale/dropdown callbacks + helpers."""

    def __init__(self, manager: Any) -> None:  # WHY: bind parent so __getattr__ can proxy shared state
        """Store the parent MapViewerCallbacks for delegate lookups."""
        self._mm = manager  # WHY: enable __getattr__ delegation back to the parent class

    def __getattr__(self, name: str) -> Any:  # WHY: transparent proxy for shared state access
        """Delegate unknown attributes to the wrapped parent manager."""
        mm = self.__dict__.get("_mm")  # WHY: guard against half-initialized instances
        if mm is None:  # WHY: only trips during broken init; avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly
        return getattr(mm, name)  # WHY: forward all other attributes to parent

    # ------------------------------------------------------------------
    # Extracted callback bodies + helpers (wave E2 site-switch cluster)
    # ------------------------------------------------------------------

    def set_scale(
        self,
        n_clicks: int | None,
        actual_length_m: float | None,
        current_fig: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """Calculate and update PPM based on drawn line and known length."""
        logging.info("set_scale: n_clicks=%s, actual_length_m=%s", n_clicks, actual_length_m)  # Action log
        if not n_clicks or not actual_length_m or actual_length_m <= 0:  # Guard invalid input
            return "[!] Please enter a valid length in meters", current_fig  # User-visible error preserved
        shapes = current_fig.get("layout", {}).get("shapes", [])  # Read user-drawn shapes from figure
        last_line = self._find_last_line_shape(shapes)  # Locate most recent line shape
        if not last_line:  # Guard missing line
            return "[!] Please draw a line first using the ruler tool", current_fig  # User-visible error preserved
        new_ppm = self._compute_new_ppm(last_line, actual_length_m)  # Length px / known meters
        self._store_new_ppm(current_fig, new_ppm)  # Persist PPM in figure metadata
        self._reannotate_measurements(current_fig, shapes, new_ppm)  # Refresh every measurement annotation
        status_msg = (  # Mirror original status string format byte-for-byte
            f"[OK] Scale set! New PPM: {new_ppm:.2f} "
            f"({actual_length_m:.2f}m = {self._line_length_px(last_line):.1f}px)"
        )
        logging.info(
            "Map scale updated: PPM %s -> %.2f (user calibration: %sm)", self._state.ppm, new_ppm, actual_length_m
        )  # Match original log line
        return status_msg, current_fig

    @staticmethod
    def _find_last_line_shape(shapes: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Return the most recently drawn ``line`` shape (or None)."""
        for shape in reversed(shapes):  # Walk shapes newest first
            if shape.get("type") == "line":  # Match the ruler tool's line shape
                return shape
        return None

    @staticmethod
    def _line_length_px(line_shape: dict[str, Any]) -> float:
        """Return pixel length of a Plotly line shape via Euclidean distance."""
        x0, y0 = line_shape.get("x0", 0), line_shape.get("y0", 0)  # Line start
        x1, y1 = line_shape.get("x1", 0), line_shape.get("y1", 0)  # Line end
        return float(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5)  # WHY: coerce Any to float for strict typing

    @classmethod
    def _compute_new_ppm(cls, line_shape: dict[str, Any], actual_length_m: float) -> float:
        """Derive pixels-per-meter from a drawn line + its measured length."""
        return cls._line_length_px(line_shape) / actual_length_m  # px / meters = ppm

    @staticmethod
    def _store_new_ppm(current_fig: dict[str, Any], new_ppm: float) -> None:
        """Persist the new PPM into ``layout.meta.ppm`` (creating dict if needed)."""
        if "meta" not in current_fig["layout"]:  # Create meta dict if missing
            current_fig["layout"]["meta"] = {}
        current_fig["layout"]["meta"]["ppm"] = new_ppm  # Store for subsequent annotations

    def _reannotate_measurements(
        self,
        current_fig: dict[str, Any],
        shapes: list[dict[str, Any]],
        new_ppm: float,
    ) -> None:
        """Refresh every ``... px`` measurement annotation with the new PPM."""
        if "annotations" not in current_fig["layout"]:  # Nothing to update
            return
        for ann_idx, annotation in enumerate(current_fig["layout"]["annotations"]):  # Iterate annotations
            if "px" not in annotation.get("text", ""):  # Skip non-measurement annotations
                continue
            self._update_annotation_text(current_fig, ann_idx, shapes, new_ppm)  # Recalculate this one

    @staticmethod
    def _update_annotation_text(
        current_fig: dict[str, Any],
        ann_idx: int,
        shapes: list[dict[str, Any]],
        new_ppm: float,
    ) -> None:
        """Update one measurement annotation's text using the first line shape."""
        for shape in shapes:  # Find the shape paired with this annotation
            if shape.get("type") != "line":
                continue
            sx0, sy0 = shape.get("x0", 0), shape.get("y0", 0)  # Shape line start
            sx1, sy1 = shape.get("x1", 0), shape.get("y1", 0)  # Shape line end
            shape_px = ((sx1 - sx0) ** 2 + (sy1 - sy0) ** 2) ** 0.5  # Recompute length
            shape_m = shape_px / new_ppm  # Convert to meters at new PPM
            shape_ft = shape_m * 3.28084  # Convert to feet (preserve original format)
            current_fig["layout"]["annotations"][ann_idx][
                "text"
            ] = f"<b>{shape_px:.1f} px</b><br>{shape_ft:.2f} ft<br>{shape_m:.2f} m"  # Mirror original text format
            break  # Original code broke after first matching shape

    def refresh_map_dropdown(
        self,
        _cache_bust_data: Any,
        _manual_clicks: int | None,
        _url_search: str | None,
        config: dict[str, Any] | None,
    ) -> tuple[Any, Any]:
        """Fetch fresh map list from API after clone/delete, manual refresh, or page load."""
        import dash  # Local import: dash.callback_context only exists at request time
        from dash import no_update  # Sentinel used to skip output updates

        site_id_local = config.get("site_id") if config else None  # site_id is required for the API call
        if not site_id_local:  # Guard: cannot refresh without site context
            logging.warning("Cannot refresh map dropdown: site_id not available")  # Mirror original log
            return no_update, no_update
        try:
            ctx = dash.callback_context  # Per-request trigger context
            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else "initial_load"  # Trigger label
            logging.info("Refreshing map dropdown list (trigger: %s)", trigger_id)  # Mirror original log
            maps_response = self._state.mistapi_ref.api.v1.sites.maps.listSiteMaps(  # Fresh fetch
                self._state.api_session_ref, site_id=site_id_local
            )
            if maps_response.status_code != 200:  # API failed -> keep current options
                logging.warning("Failed to refresh map list: HTTP %s", maps_response.status_code)
                return no_update, no_update
            fresh_maps = maps_response.data if maps_response.data else []  # Default to empty list
            logging.info("Map dropdown refreshed: %d maps found", len(fresh_maps))  # Mirror original log
            new_options = self._state.serializer.build_dropdown_options(fresh_maps, default_name="Unnamed")
            new_store_data = self._state.serializer.build_named_items(fresh_maps, default_name="Unnamed")
            return new_options, new_store_data
        except Exception as refresh_error:  # Catch-all parity with original
            logging.exception("Error refreshing map dropdown: %s", refresh_error)  # Mirror log
            return no_update, no_update

    def handle_site_from_url(
        self,
        url_search: str | None,
        config: dict[str, Any] | None,
        available_sites: list[dict[str, Any]] | None,
    ) -> list[Any]:
        """Handle site selection when URL contains site_id parameter (for bookmarks/links)."""
        from dash import no_update  # Sentinel used to skip output updates

        if not url_search:  # Nothing to parse
            return [no_update]
        url_site_id = self._extract_url_param(url_search, "site_id")  # Pull site_id from URL
        if not url_site_id:  # Param absent
            return [no_update]
        current_site_id = config.get("site_id") if config else None  # Current selection
        if url_site_id == current_site_id:  # Already there
            return [no_update]
        valid_site_ids = [s.get("id") for s in available_sites] if available_sites else []  # Allow-list
        if url_site_id not in valid_site_ids:  # Reject unknown site
            logging.warning("URL site switch: Invalid site_id %s", url_site_id)  # Mirror log
            return [no_update]
        logging.info("URL site switch: Setting dropdown to site %s", url_site_id)  # Mirror log
        return [url_site_id]

    def sync_dropdown_with_url(
        self,
        url_search: str | None,
        available_maps: list[dict[str, Any]] | None,
        current_dropdown_value: str | None,
    ) -> Any:
        """Sync dropdown selection with URL parameter on page load."""
        from dash import no_update  # Sentinel used to skip output updates

        if not url_search:  # Nothing to parse
            return no_update
        url_map_id = self._extract_url_param(url_search, "map_id")  # Pull map_id from URL
        if not url_map_id:  # Param absent
            return no_update
        if url_map_id == current_dropdown_value:  # Already in sync
            return no_update
        valid_map_ids = [m.get("id") for m in available_maps] if available_maps else []  # Allow-list
        if url_map_id not in valid_map_ids:  # Reject unknown map
            logging.warning("URL dropdown sync: Invalid map_id %s", url_map_id)  # Mirror log
            return no_update
        logging.debug("URL dropdown sync: Setting dropdown to %s", url_map_id)  # Mirror log
        return url_map_id

    @staticmethod
    def _extract_url_param(url_search: str, name: str) -> str | None:
        """Parse a single query-string parameter from a ``?key=value&...`` string."""
        import urllib.parse  # Stdlib URL parsing

        params = urllib.parse.parse_qs(url_search.lstrip("?"))  # Strip leading ? then parse
        return params.get(name, [None])[0]  # Return first value or None

    def handle_site_switch_from_dropdown(
        self,
        selected_site_id: str | None,
        config: dict[str, Any] | None,
        available_sites: list[dict[str, Any]] | None,
        _current_fig: dict[str, Any],
    ) -> tuple[Any, Any, Any, Any, Any]:
        """Handle site switching from dropdown - rebuilds dropdown options, store, config, and figure."""
        from dash import no_update  # Sentinel used to skip output updates

        logging.info("[SITE-SWITCH] Callback triggered with site_id=%s", selected_site_id)  # Mirror log
        if not selected_site_id:  # Guard missing input
            logging.warning("[SITE-SWITCH] No selected_site_id provided")  # Mirror log
            return no_update, no_update, no_update, no_update, no_update
        current_site_id = config.get("site_id") if config else None  # Current site
        if selected_site_id == current_site_id:  # Same -> no-op
            logging.debug("[SITE-SWITCH] Same site selected (%s), no update needed", selected_site_id)
            return no_update, no_update, no_update, no_update, no_update
        site_name = self._resolve_site_name(selected_site_id, available_sites or [])  # Lookup display name
        logging.info("[SITE-SWITCH] Switching to site %s (%s)", site_name, selected_site_id)
        try:
            return self._perform_site_switch(selected_site_id, site_name, config)  # Heavy lifting
        except Exception as site_switch_error:  # Catch-all parity with original
            logging.exception("[SITE-SWITCH] Error: %s", site_switch_error)
            return no_update, no_update, no_update, no_update, no_update

    @staticmethod
    def _resolve_site_name(site_id: str, available_sites: list[dict[str, Any]]) -> str:
        """Look up display name for a site_id from the available-sites list."""
        return next((s.get("name", "Unknown") for s in available_sites if s.get("id") == site_id), "Unknown")

    def _perform_site_switch(
        self,
        selected_site_id: str,
        site_name: str,
        config: dict[str, Any] | None,
    ) -> tuple[Any, Any, Any, Any, Any]:
        """Fetch maps for new site, build dropdown + figure for the first map."""
        from dash import no_update  # Sentinel used to skip output updates

        new_maps = self._fetch_site_maps(selected_site_id)  # Returns None on API failure, [] on no maps
        if new_maps is None:  # API call failed
            return no_update, no_update, no_update, no_update, no_update
        if not new_maps:  # Site has no maps -> empty figure
            return self._build_empty_site_payload(selected_site_id, site_name, config)
        return self._build_first_map_payload(selected_site_id, site_name, new_maps, config)  # Pick first map

    def _fetch_site_maps(self, site_id: str) -> list[dict[str, Any]] | None:
        """Fetch site map list; return ``None`` on API failure, ``[]`` on empty."""
        maps_response = self._state.mistapi_ref.api.v1.sites.maps.listSiteMaps(  # Mist API call
            self._state.api_session_ref, site_id=site_id
        )
        if maps_response.status_code != 200:  # Mirror original HTTP gate
            logging.error(
                "[SITE-SWITCH] Failed to fetch maps for site %s - HTTP %s", site_id, maps_response.status_code
            )
            return None
        new_maps = maps_response.data if maps_response.data else []  # Normalize empty
        logging.info("[SITE-SWITCH] Found %d maps for site", len(new_maps))
        return new_maps

    def _build_empty_site_payload(
        self,
        selected_site_id: str,
        site_name: str,
        config: dict[str, Any] | None,
    ) -> tuple[list[Any], None, list[Any], dict[str, Any], Any]:
        """Return the 5-tuple shown when a site has no maps."""
        import plotly.graph_objects as go  # Local import - heavy module

        logging.warning("[SITE-SWITCH] No maps found for site %s", selected_site_id)
        empty_fig = go.Figure()  # Empty figure with site-level title
        empty_fig.update_layout(  # Match original empty-figure styling byte-for-byte
            title=f"No maps found for site: {site_name}",
            paper_bgcolor="#1e1e1e",
            plot_bgcolor="#1e1e1e",
            font=dict(color="#e0e0e0"),
        )
        updated_config = config.copy() if config else {}  # Preserve other config keys
        updated_config["site_id"] = selected_site_id  # Update site
        updated_config["site_name"] = site_name
        updated_config["map_id"] = None  # No active map
        updated_config["map_name"] = None
        return [], None, [], updated_config, empty_fig  # Empty options, no selection, empty store, config, fig

    def _build_first_map_payload(
        self,
        selected_site_id: str,
        site_name: str,
        new_maps: list[dict[str, Any]],
        config: dict[str, Any] | None,
    ) -> tuple[Any, Any, Any, dict[str, Any], Any]:
        """Build dropdown options, store, updated config, and figure for the first map."""
        new_map_options = self._state.serializer.build_dropdown_options(new_maps, default_name="Unnamed")  # Options
        new_maps_store = self._state.serializer.build_named_items(new_maps, default_name="Unnamed")  # Store data
        first_map = new_maps[0]  # Pick first map (matches original)
        selected_map_id: str = first_map.get("id", "")  # WHY: coerce to str for strict typing downstream
        map_name = first_map.get("name", "Unnamed")  # Map display name
        updated_config = self._merge_site_switch_config(config, selected_site_id, site_name, first_map)  # Config copy
        new_fig = self._build_site_switch_figure(selected_site_id, selected_map_id, first_map, site_name, map_name)
        logging.info("[SITE-SWITCH] Successfully loaded map %s", map_name)  # Mirror log
        return new_map_options, selected_map_id, new_maps_store, updated_config, new_fig

    @staticmethod
    def _merge_site_switch_config(
        config: dict[str, Any] | None,
        site_id: str,
        site_name: str,
        first_map: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge site + first-map info into a copy of the existing config dict."""
        updated_config = config.copy() if config else {}  # Preserve other keys
        updated_config["site_id"] = site_id  # New site
        updated_config["site_name"] = site_name
        updated_config["map_id"] = first_map.get("id")  # First map UUID
        updated_config["map_name"] = first_map.get("name", "Unnamed")
        updated_config["ppm"] = first_map.get("ppm", 1.0)  # PPM (default 1.0 matches original)
        updated_config["map_width"] = first_map.get("width", 1000)
        updated_config["map_height"] = first_map.get("height", 1000)
        return updated_config

    def _build_site_switch_figure(
        self,
        selected_site_id: str,
        selected_map_id: str,
        map_data: dict[str, Any],
        site_name: str,
        map_name: str,
    ) -> Any:
        """Construct a fresh Plotly figure for the first map on a newly-selected site."""
        import plotly.graph_objects as go  # Local import - heavy module

        new_fig = go.Figure()  # Start with an empty figure
        map_width = map_data.get("width", 1000)  # Canvas width
        map_height = map_data.get("height", 1000)  # Canvas height
        self._add_background_image(new_fig, map_data, map_width, map_height, anchor_top=False)  # Background
        devices = self._fetch_site_switch_devices(selected_site_id, selected_map_id)  # APs/switches/gateways on map
        self._add_simple_device_traces(new_fig, devices)  # Simple marker-per-device traces
        self._apply_site_switch_layout(new_fig, site_name, map_name, map_width, map_height)  # Layout/theme
        return new_fig

    @staticmethod
    def _add_background_image(
        fig: Any,
        map_data: dict[str, Any],
        map_width: int,
        map_height: int,
        anchor_top: bool,
    ) -> None:
        """Add the map background image; ``anchor_top`` selects y=map_height vs y=0."""
        if "url" not in map_data:  # No image to add
            return
        fig.add_layout_image(  # Plotly background-image API
            source=map_data["url"],
            xref="x",
            yref="y",
            x=0,
            y=map_height if anchor_top else 0,  # Original site-switch used map_height; URL-switch used 0
            sizex=map_width,
            sizey=map_height,
            sizing="stretch",
            opacity=1.0,
            layer="below",
        )

    def _fetch_site_switch_devices(self, site_id: str, map_id: str) -> list[dict[str, Any]]:
        """Fetch site devices and filter to the given map (returns [] on failure)."""
        try:
            devices_response = self._state.mistapi_ref.api.v1.sites.stats.listSiteDevicesStats(
                self._state.api_session_ref, site_id=site_id, limit=1000
            )
            if devices_response.status_code != 200:  # API failure -> no devices
                return []
            all_devices = devices_response.data or []  # Normalize empty
            return [d for d in all_devices if d.get("map_id") == map_id]  # Filter to this map
        except Exception:  # Mirror original bare-except behavior
            return []

    def _add_simple_device_traces(self, fig: Any, devices: list[dict[str, Any]]) -> None:
        """Add per-device markers to the figure using the original simple-style logic."""
        import plotly.graph_objects as go  # Local import - heavy module

        for device in devices:  # One trace per device (preserve original behavior)
            color = self._simple_device_color(device.get("status", "unknown"))  # Status-based color
            symbol = self._simple_device_symbol(device.get("type", "ap"))  # Type-based symbol
            self._add_single_device_trace(fig, device, color, symbol, go)  # Append one Scatter trace

    @staticmethod
    def _simple_device_color(status: str) -> str:
        """Map device status to marker color (mirrors original site-switch logic)."""
        if status == "connected":
            return "#00ff00"  # Bright green
        if status == "disconnected":
            return "#ff0000"  # Bright red
        return "#ffaa00"  # Amber for unknown/upgrading

    @staticmethod
    def _simple_device_symbol(device_type: str) -> str:
        """Map device type to marker symbol (mirrors original site-switch logic)."""
        if device_type == "switch":
            return "square"
        if device_type == "gateway":
            return "diamond"
        return "circle"  # Default (used for APs in original site-switch)

    @staticmethod
    def _add_single_device_trace(
        fig: Any,
        device: dict[str, Any],
        marker_color: str,
        marker_symbol: str,
        go: Any,
    ) -> None:
        """Add a single device's marker+label trace (mirrors original site-switch logic)."""
        device_name = device.get("name", "Unknown")  # Display name
        device_type = device.get("type", "ap")  # Device type
        device_status = device.get("status", "unknown")  # Connectivity status
        fig.add_trace(  # Single Scatter trace per device
            go.Scatter(
                x=[device.get("x", 0)],
                y=[device.get("y", 0)],
                mode="markers+text",
                marker=dict(size=12, color=marker_color, symbol=marker_symbol, line=dict(color="white", width=1)),
                text=[device_name],
                textposition="top center",
                textfont=dict(size=10, color="#e0e0e0"),
                name=device_name,
                showlegend=False,
                hovertemplate=(  # Preserve original hover format exactly
                    f"<b>{device_name}</b><br>Type: {device_type}<br>Status: {device_status}<extra></extra>"
                ),
            )
        )

    @staticmethod
    def _apply_site_switch_layout(
        fig: Any,
        site_name: str,
        map_name: str,
        map_width: int,
        map_height: int,
    ) -> None:
        """Apply the site-switch figure layout (title, axes, theme, drag mode)."""
        fig.update_layout(  # Preserve original layout dict byte-for-byte
            title=dict(text=f"{site_name} - {map_name}", font=dict(color="#e0e0e0", size=16), x=0.5),
            paper_bgcolor="#1e1e1e",
            plot_bgcolor="#1e1e1e",
            xaxis=dict(
                range=[0, map_width],
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                scaleanchor="y",
                scaleratio=1,
            ),
            yaxis=dict(range=[0, map_height], showgrid=False, zeroline=False, showticklabels=False),
            margin=dict(l=0, r=0, t=40, b=0),
            dragmode="pan",
        )

    # ------------------------------------------------------------------
    # Callback wiring
    # ------------------------------------------------------------------

    def register(self, app: Dash) -> None:  # WHY: hooks this wave's app.callback(...) blocks into Dash
        """Attach the 5 site-switch callbacks in this cluster to ``app``."""
        from dash import Input, Output, State  # WHY: local import keeps module import-light

        app.callback(  # WHY: set_scale - calibrate PPM from drawn line
            [Output("scale-status", "children"), Output("map-display", "figure", allow_duplicate=True)],
            Input("set-scale-button", "n_clicks"),  # WHY: triggered by Set Scale button
            [State("scale-length-input", "value"), State("map-display", "figure")],  # WHY: input + current figure
            prevent_initial_call=True,  # WHY: avoid initial render thrash
        )(self.set_scale)

        app.callback(  # WHY: refresh_map_dropdown - repopulate map selector
            [Output("map-selector-dropdown", "options"), Output("available-maps-store", "data")],
            [
                Input("cache-bust-store", "data"),  # WHY: cache-bust signal
                Input("manual-refresh-btn", "n_clicks"),  # WHY: manual refresh button
                Input("url-location", "search"),  # WHY: URL change trigger
            ],
            [State("map-config-store", "data")],  # WHY: site_id source
            prevent_initial_call=False,  # WHY: run on initial load to get fresh data
        )(self.refresh_map_dropdown)

        app.callback(  # WHY: handle_site_switch_from_dropdown - swap active site
            [
                Output("map-selector-dropdown", "options"),
                Output("map-selector-dropdown", "value", allow_duplicate=True),
                Output("available-maps-store", "data", allow_duplicate=True),
                Output("map-config-store", "data", allow_duplicate=True),
                Output("map-display", "figure", allow_duplicate=True),
            ],
            [Input("site-selector-dropdown", "value")],  # WHY: triggered by site selection
            [
                State("map-config-store", "data"),  # WHY: current config
                State("available-sites-store", "data"),  # WHY: sites store
                State("map-display", "figure"),  # WHY: current figure
            ],
            prevent_initial_call=True,  # WHY: avoid initial render thrash
        )(self.handle_site_switch_from_dropdown)

        app.callback(  # WHY: handle_site_from_url - sync dropdown to URL param
            [Output("site-selector-dropdown", "value")],
            [Input("url-location", "search")],  # WHY: URL change trigger
            [State("map-config-store", "data"), State("available-sites-store", "data")],
            prevent_initial_call="initial_duplicate",  # WHY: allow initial run on duplicate output
        )(self.handle_site_from_url)

        app.callback(  # WHY: sync_dropdown_with_url - map dropdown selection from URL
            Output("map-selector-dropdown", "value"),
            [Input("url-location", "search")],  # WHY: URL change trigger
            [State("available-maps-store", "data"), State("map-selector-dropdown", "value")],
            prevent_initial_call=False,  # WHY: must run on initial load
        )(self.sync_dropdown_with_url)
