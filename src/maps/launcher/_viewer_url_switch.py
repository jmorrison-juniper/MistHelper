"""URL-map-switch cluster extracted from ``viewer_callbacks.py``.

Owns the single Wave-E3 public callback ``handle_url_map_switch`` plus its
30 private helpers (URL preflight, target-map fetch, device/zone/client
overlays, coverage heatmap rendering).  Follows the same wrapper-class +
``__getattr__`` template used by the other Wave-1..5 clusters so the
parent :class:`~src.maps.launcher.viewer_callbacks.MapViewerCallbacks`
stays a thin coordinator that hands each Dash callback off to the
appropriate cluster.
"""

from __future__ import annotations  # WHY: postponed evaluation consistent with parent module

import logging  # WHY: audit trail for URL-switch diagnostics
from typing import TYPE_CHECKING, Any  # WHY: opaque manager + type-permissive Dash callback args

if TYPE_CHECKING:  # WHY: keep dash imports lazy at runtime
    from dash import Dash  # WHY: annotation reference for register(app)


class _ViewerUrlSwitch:  # WHY: wrapper class hosting the URL-switch callback cluster
    """Cluster class holding the extracted handle_url_map_switch body + helpers."""

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
    # Extracted callback body + helpers (wave E3 URL-switch cluster)
    # ------------------------------------------------------------------

    def handle_url_map_switch(
        self,
        url_search: str | None,
        config: dict[str, Any] | None,
        _current_fig: dict[str, Any],
        available_maps: list[dict[str, Any]] | None,
        _dropdown_value: str | None,
    ) -> tuple[Any, Any]:
        """Handle map switching when URL contains map_id parameter."""
        from dash import no_update  # Sentinel used to skip output updates

        prep = self._prepare_url_map_switch(url_search, config, available_maps)  # Combined guard chain
        if prep is None:  # Any guard failed -> no update
            return no_update, no_update
        url_map_id, site_id_local, normalized_config = prep  # Unpack validated triple
        try:
            return self._perform_url_map_switch(url_map_id, site_id_local, normalized_config)  # Heavy lifting
        except Exception as e:  # Catch-all parity with original
            logging.exception("URL map switch: Error loading map - %s", e)
            return no_update, no_update

    def _prepare_url_map_switch(
        self,
        url_search: str | None,
        config: dict[str, Any] | None,
        available_maps: list[dict[str, Any]] | None,
    ) -> tuple[str, str, dict[str, Any]] | None:
        """Run all URL-switch preflight guards; return ``(url_map_id, site_id, config)`` or ``None``."""
        if not url_search:  # Nothing to parse
            return None
        url_map_id = self._site._extract_url_param(url_search, "map_id")  # WHY: reuse extracted site-cluster helper
        if not url_map_id:  # Param absent
            return None
        normalized_config = config or {}  # Defaults to empty dict
        if url_map_id == normalized_config.get("map_id"):  # Already on this map
            logging.debug("URL map switch: URL map_id %s matches config, no switch needed", url_map_id)
            return None
        site_id_local = normalized_config.get("site_id")  # site_id required for API calls
        if not site_id_local:  # Guard missing site context
            logging.warning("URL map switch: site_id not available in config")
            return None
        if not self._validate_url_map_id(url_map_id, site_id_local, available_maps or []):  # Allow-list
            return None
        logging.info("URL map switch: Loading map %s (current: %s)", url_map_id, normalized_config.get("map_id"))
        return url_map_id, site_id_local, normalized_config

    def _validate_url_map_id(
        self,
        url_map_id: str,
        site_id_local: str,
        available_maps: list[dict[str, Any]],
    ) -> bool:
        """Validate ``url_map_id`` against a fresh API fetch (falls back to store)."""
        valid_map_ids = self._fetch_valid_map_ids(site_id_local, available_maps)  # Fresh ID list
        if url_map_id not in valid_map_ids:  # Reject unknown map
            logging.warning("URL map switch: Invalid map_id %s", url_map_id)
            return False
        return True

    def _fetch_valid_map_ids(
        self,
        site_id_local: str,
        available_maps: list[dict[str, Any]],
    ) -> list[str | None]:
        """Fetch a fresh map ID list, falling back to the supplied store on errors."""
        try:
            fresh_response = self._state.mistapi_ref.api.v1.sites.maps.listSiteMaps(
                self._state.api_session_ref, site_id=site_id_local
            )
            if fresh_response.status_code == 200:  # Use fresh data
                fresh_maps = fresh_response.data if fresh_response.data else []
                return [m.get("id") for m in fresh_maps]
            logging.warning("URL map switch: Could not fetch fresh maps, using store")  # Mirror log
        except Exception as fetch_err:  # Mirror original except-block log
            logging.warning("URL map switch: Error fetching fresh maps: %s", fetch_err)
        return [m.get("id") for m in available_maps]  # Store fallback

    def _perform_url_map_switch(
        self,
        url_map_id: str,
        site_id_local: str,
        config: dict[str, Any],
    ) -> tuple[Any, Any]:
        """Fetch new map + entities and build a fresh figure + updated config."""
        from dash import no_update  # Sentinel used to skip output updates

        new_map_data = self._fetch_target_map(url_map_id, site_id_local)  # Map details
        if new_map_data is None:  # API failure
            return no_update, no_update
        new_devices = self._fetch_devices_for_map(url_map_id, site_id_local)  # Device list
        new_zones = self._fetch_zones_for_map(url_map_id, site_id_local)  # Zone list
        new_clients = self._fetch_clients_for_map(url_map_id, site_id_local)  # Client list
        new_fig = self._build_url_switch_figure(  # Compose figure from layers
            url_map_id, site_id_local, new_map_data, new_devices, new_zones, new_clients, config
        )
        new_config = self._merge_url_switch_config(config, url_map_id, new_map_data)  # Updated config
        logging.info("URL map switch: Successfully switched to map '%s'", new_map_data.get("name", "Unnamed"))
        return new_fig, new_config

    def _fetch_target_map(self, url_map_id: str, site_id_local: str) -> dict[str, Any] | None:
        """Fetch the target map's full data (returns None on HTTP failure)."""
        map_response = self._state.mistapi_ref.api.v1.sites.maps.getSiteMap(
            self._state.api_session_ref, site_id_local, url_map_id
        )
        if map_response.status_code != 200:  # Mirror original HTTP gate
            logging.error("URL map switch: Failed to fetch map - HTTP %s", map_response.status_code)
            return None
        new_map_data: dict[str, Any] = map_response.data  # WHY: explicit annotation coerces Any for strict typing
        logging.info(  # Mirror original info log
            "URL map switch: Loaded map '%s' (%sx%s, ppm=%s)",
            new_map_data.get("name", "Unnamed"),
            new_map_data.get("width", 1000),
            new_map_data.get("height", 1000),
            new_map_data.get("ppm") or 10,
        )
        return new_map_data

    def _fetch_devices_for_map(self, url_map_id: str, site_id_local: str) -> list[dict[str, Any]]:
        """Fetch site devices and filter to ``url_map_id``."""
        devices_response = self._state.mistapi_ref.api.v1.sites.stats.listSiteDevicesStats(
            self._state.api_session_ref, site_id=site_id_local, limit=1000
        )
        if devices_response.status_code != 200:  # Mirror original HTTP gate
            return []
        all_devices = self._state.mistapi_ref.get_all(  # Pagination helper exhausts result set
            response=devices_response, mist_session=self._state.api_session_ref
        )
        return [d for d in all_devices if d.get("map_id") == url_map_id]  # Filter to map

    def _fetch_zones_for_map(self, url_map_id: str, site_id_local: str) -> list[dict[str, Any]]:
        """Fetch site zones and filter to ``url_map_id``."""
        zones_response = self._state.mistapi_ref.api.v1.sites.zones.listSiteZones(
            self._state.api_session_ref, site_id=site_id_local
        )
        if zones_response.status_code != 200:  # Mirror original HTTP gate
            return []
        all_zones = self._state.mistapi_ref.get_all(response=zones_response, mist_session=self._state.api_session_ref)
        return [z for z in all_zones if z.get("map_id") == url_map_id]  # Filter to map

    def _fetch_clients_for_map(self, url_map_id: str, site_id_local: str) -> list[dict[str, Any]]:
        """Fetch wireless clients filtered to ``url_map_id`` (with coordinates)."""
        clients_response = self._state.mistapi_ref.api.v1.sites.stats.listSiteWirelessClientsStats(
            self._state.api_session_ref, site_id=site_id_local, limit=1000
        )
        if clients_response.status_code != 200:  # Mirror original HTTP gate
            return []
        all_clients = self._state.mistapi_ref.get_all(
            response=clients_response, mist_session=self._state.api_session_ref
        )
        return [  # Filter: same map + has x coordinate (matches original)
            c for c in all_clients if c.get("map_id") == url_map_id and c.get("x") is not None
        ]

    def _build_url_switch_figure(  # noqa: PLR0913 - mirrors original closure signature
        self,
        url_map_id: str,
        site_id_local: str,
        map_data: dict[str, Any],
        devices: list[dict[str, Any]],
        zones: list[dict[str, Any]],
        clients: list[dict[str, Any]],
        config: dict[str, Any],
    ) -> Any:
        """Compose a Plotly figure for a URL-driven map switch (background + layers + theme)."""
        import plotly.graph_objects as go  # Local import - heavy module

        map_width = map_data.get("width", 1000)
        map_height = map_data.get("height", 1000)
        ppm_local = map_data.get("ppm") or 10  # Mirror original default
        new_fig = go.Figure()  # Start empty
        self._site._add_background_image(
            new_fig, map_data, map_width, map_height, anchor_top=False
        )  # WHY: reuse extracted site-cluster helper
        self._state.figure_builder.add_walls(new_fig, map_data)  # Walls layer (reuse collaborator)
        self._state.figure_builder.add_wayfinding(new_fig, map_data)  # Wayfinding layer (reuse collaborator)
        self._state.figure_builder.add_zones(new_fig, zones)  # Zones layer (reuse collaborator)
        self._add_url_switch_devices(new_fig, devices)  # Device markers + labels + crosshairs
        self._add_url_switch_clients(new_fig, clients)  # Client markers + labels
        self._add_url_switch_origin(new_fig, map_data)  # Origin marker
        self._add_url_switch_heatmap(new_fig, url_map_id, site_id_local, ppm_local, config)  # RF coverage
        self._apply_url_switch_layout(new_fig, map_data.get("name", "Unnamed"), map_width, map_height)
        return new_fig

    def _add_url_switch_devices(self, fig: Any, devices: list[dict[str, Any]]) -> None:
        """Group devices by type and add full marker/label/crosshair traces (mirrors original)."""
        device_types = self._group_devices_by_type(devices)  # {type: [devices...]}
        for device_type, type_cfg in self._url_switch_device_config().items():  # Same config dict as original
            type_devices = device_types.get(device_type, [])
            if not type_devices:  # Skip empty types
                continue
            self._render_url_switch_device_type(fig, type_devices, type_cfg)  # Full per-type render

    @staticmethod
    def _group_devices_by_type(devices: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Group devices into ap/switch/gateway buckets (requires x and y coords)."""
        buckets: dict[str, list[dict[str, Any]]] = {"ap": [], "switch": [], "gateway": []}
        for device in devices:  # One pass
            device_type = device.get("type", "ap")
            if device.get("x") is None or device.get("y") is None:  # Skip un-placed devices
                continue
            if device_type in buckets:  # Only known types
                buckets[device_type].append(device)
        return buckets

    @staticmethod
    def _url_switch_device_config() -> dict[str, dict[str, Any]]:
        """Return the device-type symbol/color config (matches original byte-for-byte)."""
        return {
            "ap": {
                "symbol": "triangle-up",
                "name": "Access Points",
                "size": 20,
                "colors": {"connected": "#00ff00", "disconnected": "#ff0000", "upgrading": "#ff8800"},
            },
            "switch": {
                "symbol": "square",
                "name": "Switches",
                "size": 18,
                "colors": {"connected": "#00ccff", "disconnected": "#ff0000", "upgrading": "#ff8800"},
            },
            "gateway": {
                "symbol": "diamond",
                "name": "Gateways",
                "size": 20,
                "colors": {"connected": "#ff00ff", "disconnected": "#ff0000", "upgrading": "#ff8800"},
            },
        }

    def _render_url_switch_device_type(
        self,
        fig: Any,
        type_devices: list[dict[str, Any]],
        type_cfg: dict[str, Any],
    ) -> None:
        """Render the marker trace + labels + crosshairs for one device type."""
        x_coords = [d["x"] for d in type_devices]
        y_coords = [d["y"] for d in type_devices]
        names = [d.get("name", d.get("mac", "Unknown")) for d in type_devices]
        colors, hover_texts = self._build_device_colors_and_hovers(type_devices, type_cfg)  # Per-device computed
        self._add_url_switch_marker_trace(fig, x_coords, y_coords, type_cfg, colors, hover_texts)
        self._add_url_switch_device_labels(fig, x_coords, y_coords, names, colors, type_cfg)
        self._add_url_switch_orientation_crosshairs(fig, x_coords, y_coords, type_devices, colors, type_cfg)

    @staticmethod
    def _build_device_colors_and_hovers(
        type_devices: list[dict[str, Any]],
        type_cfg: dict[str, Any],
    ) -> tuple[list[str], list[str]]:
        """Compute per-device color + hover text from status (mirrors original)."""
        colors: list[str] = []
        hovers: list[str] = []
        for device in type_devices:  # Iterate once
            status = device.get("status", "disconnected")
            if device.get("upgrade_status") or device.get("fwupdate", {}).get("progress") is not None:
                device_status = "upgrading"
            elif status == "connected":
                device_status = "connected"
            else:
                device_status = "disconnected"
            colors.append(type_cfg["colors"][device_status])  # Color from type config
            text = f"<b>{device.get('name', 'Unnamed')}</b><br>"  # Mirror original hover format
            text += f"Type: {device.get('type', 'N/A')}<br>"
            text += f"Model: {device.get('model', 'N/A')}<br>"
            text += f"MAC: {device.get('mac', 'N/A')}<br>"
            text += f"Status: <b>{device_status.upper()}</b>"
            hovers.append(text)
        return colors, hovers

    @staticmethod
    def _add_url_switch_marker_trace(  # noqa: PLR0913 - mirrors original positional flow
        fig: Any,
        x_coords: list[float],
        y_coords: list[float],
        type_cfg: dict[str, Any],
        colors: list[str],
        hover_texts: list[str],
    ) -> None:
        """Add the per-type marker trace (preserves original styling)."""
        import plotly.graph_objects as go  # Local import - heavy module

        fig.add_trace(
            go.Scatter(
                x=x_coords,
                y=y_coords,
                mode="markers",
                name=type_cfg["name"],
                marker=dict(
                    symbol=type_cfg["symbol"],
                    size=type_cfg["size"],
                    color=colors,
                    line=dict(color="white", width=2),
                    opacity=0.9,
                ),
                hovertext=hover_texts,
                hoverinfo="text",
                visible=True,
                showlegend=True,
            )
        )

    @staticmethod
    def _add_url_switch_device_labels(  # noqa: PLR0913 - mirrors original loop signature
        fig: Any,
        x_coords: list[float],
        y_coords: list[float],
        names: list[str],
        colors: list[str],
        type_cfg: dict[str, Any],
    ) -> None:
        """Add per-device name annotations under each marker."""
        for x, y, name, device_color in zip(x_coords, y_coords, names, colors, strict=True):
            fig.add_annotation(
                x=x,
                y=y - 15,
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

    def _add_url_switch_orientation_crosshairs(  # noqa: PLR0913 - mirrors original loop signature
        self,
        fig: Any,
        x_coords: list[float],
        y_coords: list[float],
        type_devices: list[dict[str, Any]],
        colors: list[str],
        type_cfg: dict[str, Any],
    ) -> None:
        """Add horizontal+vertical lines + directional dot per device (mirrors original)."""
        import math  # Local import - lightweight

        import plotly.graph_objects as go  # Local import - heavy module

        for x, y, device, device_color in zip(x_coords, y_coords, type_devices, colors, strict=True):
            orientation = device.get("orientation", 0)
            self._add_crosshair_lines(fig, x, y, device_color, type_cfg, go)
            self._add_orientation_dot(fig, x, y, orientation, device_color, type_cfg, math, go)

    @staticmethod
    def _add_crosshair_lines(  # noqa: PLR0913 - mirrors original positional flow
        fig: Any,
        x: float,
        y: float,
        device_color: str,
        type_cfg: dict[str, Any],
        go: Any,
    ) -> None:
        """Add the horizontal + vertical crosshair lines for one device."""
        crosshair_size = 40  # Match original size
        fig.add_trace(  # Horizontal line
            go.Scatter(
                x=[x - crosshair_size, x + crosshair_size],
                y=[y, y],
                mode="lines",
                line=dict(color=device_color, width=3),
                name=f"{type_cfg['name']} Orientation",
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig.add_trace(  # Vertical line
            go.Scatter(
                x=[x, x],
                y=[y - crosshair_size, y + crosshair_size],
                mode="lines",
                line=dict(color=device_color, width=3),
                name=f"{type_cfg['name']} Orientation",
                showlegend=False,
                hoverinfo="skip",
            )
        )

    @staticmethod
    def _add_orientation_dot(  # noqa: PLR0913 - mirrors original positional flow
        fig: Any,
        x: float,
        y: float,
        orientation: float,
        device_color: str,
        type_cfg: dict[str, Any],
        math: Any,
        go: Any,
    ) -> None:
        """Add the directional dot showing each device's orientation angle."""
        dot_distance = 50  # Match original distance
        math_angle = 90 - orientation  # Mirror original angle conversion
        rad = math.radians(math_angle)
        dot_x = x + dot_distance * math.cos(rad)
        dot_y = y - dot_distance * math.sin(rad)
        fig.add_trace(
            go.Scatter(
                x=[dot_x],
                y=[dot_y],
                mode="markers",
                marker=dict(size=12, color=device_color, symbol="circle", line=dict(color="black", width=2)),
                name=f"{type_cfg['name']} Orientation",
                showlegend=False,
                hoverinfo="skip",
            )
        )

    def _add_url_switch_clients(self, fig: Any, clients: list[dict[str, Any]]) -> None:
        """Add client markers + per-client annotation labels (mirrors original)."""
        import plotly.graph_objects as go  # Local import - heavy module

        client_x, client_y, client_hover, client_names = self._collect_client_arrays(clients)
        if not client_x:  # Nothing to add
            return
        fig.add_trace(
            go.Scatter(
                x=client_x,
                y=client_y,
                mode="markers",
                name="Clients",
                marker=dict(symbol="circle", size=12, color="#00ff00", line=dict(color="white", width=2), opacity=0.9),
                hovertext=client_hover,
                hoverinfo="text",
                visible=True,
                showlegend=True,
            )
        )
        for x, y, name in zip(client_x, client_y, client_names, strict=True):  # Per-client annotations
            fig.add_annotation(
                x=x,
                y=y - 10,
                text=f"<b>{name}</b>",
                showarrow=False,
                font=dict(size=9, color="white", family="Arial"),
                bgcolor="rgba(0,128,0,0.9)",
                bordercolor="white",
                borderwidth=1,
                borderpad=2,
                xanchor="center",
                yanchor="bottom",
                name="Clients Label",
            )

    @staticmethod
    def _collect_client_arrays(
        clients: list[dict[str, Any]],
    ) -> tuple[list[float], list[float], list[str], list[str]]:
        """Walk clients once, returning parallel arrays of x/y/hover/name."""
        client_x: list[float] = []
        client_y: list[float] = []
        client_hover: list[str] = []
        client_names: list[str] = []
        for client in clients:  # Single pass through client list
            x = client.get("x")
            y = client.get("y")
            if x is None or y is None:  # Skip un-placed clients
                continue
            client_x.append(x)
            client_y.append(y)
            client_mac = client.get("mac", "unknown")
            hostname = client.get("hostname", "")
            label = hostname if hostname else client_mac[-8:]  # Mirror original label choice
            client_names.append(label)
            hover = "<b>Client</b><br>"  # Mirror original hover format
            hover += f"MAC: {client.get('mac', 'N/A')}<br>"
            hover += f"Hostname: {client.get('hostname', 'N/A')}<br>"
            hover += f"SSID: {client.get('ssid', 'N/A')}<br>"
            hover += f"AP: {client.get('ap_name', 'N/A')}<br>"
            hover += f"Band: {client.get('band', 'N/A')}<br>"
            hover += f"Signal: {client.get('rssi', 'N/A')} dBm<br>"
            hover += f"Position: ({x}, {y})"
            client_hover.append(hover)
        return client_x, client_y, client_hover, client_names

    @staticmethod
    def _add_url_switch_origin(fig: Any, map_data: dict[str, Any]) -> None:
        """Add the map-origin marker (hidden by default)."""
        import plotly.graph_objects as go  # Local import - heavy module

        origin = map_data.get("origin", {}) or {}
        origin_x = origin.get("x", 0)
        origin_y = origin.get("y", 0)
        fig.add_trace(
            go.Scatter(
                x=[origin_x],
                y=[origin_y],
                mode="markers+text",
                name="Map Origin",
                marker=dict(symbol="x", size=20, color="yellow", line=dict(width=3, color="black")),
                text=["Origin"],
                textposition="top center",
                textfont=dict(color="yellow", size=10),
                visible=False,
                showlegend=True,
            )
        )

    def _add_url_switch_heatmap(
        self,
        fig: Any,
        url_map_id: str,
        site_id_local: str,
        ppm_local: float,
        config: dict[str, Any],
    ) -> None:
        """Fetch RF coverage and add a heatmap trace; silently logs on failure."""
        site_id_for_coverage = config.get("site_id") or site_id_local  # Mirror original site_id source
        if not site_id_for_coverage:  # Mirror original guard
            logging.warning("URL map switch: Cannot fetch RF coverage - site_id is None")
            return
        try:
            coverage_data = self._fetch_url_switch_coverage(url_map_id, site_id_for_coverage)
            if coverage_data is None:  # Already logged inside helper
                return
            self._render_url_switch_heatmap(fig, coverage_data, ppm_local, url_map_id)
        except Exception as rf_error:  # Mirror original catch-all
            logging.warning("URL map switch: Could not load RF coverage - %s", rf_error, exc_info=True)

    def _fetch_url_switch_coverage(self, url_map_id: str, site_id_for_coverage: str) -> dict[str, Any] | None:
        """Hit the RF coverage endpoint; return parsed data or None on failure/error envelope."""
        coverage_url = f"/api/v1/sites/{site_id_for_coverage}/location/coverage"
        coverage_params = {  # Mirror original query parameters
            "resolution": "fine",
            "duration": "1d",
            "map_id": url_map_id,
            "type": "client",
            "from_apollo": "true",
        }
        logging.info("URL map switch: Fetching RF coverage for map %s", url_map_id)
        coverage_response = self._state.api_session_ref.mist_get(coverage_url, query=coverage_params)
        if coverage_response.status_code != 200:  # Mirror original HTTP gate
            logging.warning("URL map switch: RF coverage API returned HTTP %s", coverage_response.status_code)
            return None
        coverage_data: dict[str, Any] = coverage_response.data  # WHY: explicit annotation coerces Any for strict typing
        if isinstance(coverage_data, dict) and "exception" in coverage_data:  # Error envelope
            logging.warning(
                "URL map switch: RF Coverage backend error - %s",
                str(coverage_data.get("exception", ""))[:200],
            )
            return None
        return coverage_data

    def _render_url_switch_heatmap(
        self,
        fig: Any,
        coverage_data: dict[str, Any],
        ppm_local: float,
        url_map_id: str,
    ) -> None:
        """Build + add the heatmap trace from coverage payload (or log gracefully)."""
        results = coverage_data.get("results", [])
        result_def = coverage_data.get("result_def", [])
        logging.info("URL map switch: RF coverage API returned %d grid points", len(results))
        if not results or not result_def:  # Mirror original log
            logging.info("URL map switch: No RF coverage data available for this map (empty results)")
            return
        indices = self._resolve_url_switch_indices(result_def)  # (x, y, max_rssi) indices
        grid_data = self._build_url_switch_grid(results, indices, ppm_local)  # Filtered grid
        if not grid_data:  # Mirror original empty-grid log
            logging.warning("URL map switch: RF coverage - no valid grid data after processing %d points", len(results))
            return
        self._add_url_switch_heatmap_trace(fig, grid_data, url_map_id)

    @staticmethod
    def _resolve_url_switch_indices(result_def: list[str]) -> tuple[int, int, int]:
        """Find (x, y, max_rssi) column indices in ``result_def`` (falls back to 0,1,4)."""
        try:
            return result_def.index("x"), result_def.index("y"), result_def.index("max_rssi")
        except ValueError as idx_error:  # Mirror original log + fallback
            logging.warning("URL map switch: Coverage data missing expected fields in result_def: %s", idx_error)
            return 0, 1, 4

    @staticmethod
    def _build_url_switch_grid(
        results: list[list[Any]],
        indices: tuple[int, int, int],
        ppm_local: float,
    ) -> dict[tuple[float, float], float]:
        """Convert raw row-list results into a ``{(px_x, px_y): max_rssi}`` dict."""
        x_idx, y_idx, max_rssi_idx = indices  # Unpack
        max_idx = max(x_idx, y_idx, max_rssi_idx)
        grid_data: dict[tuple[float, float], float] = {}
        for item in results:  # One pass through rows
            if not isinstance(item, (list, tuple)) or len(item) <= max_idx:
                continue
            x_m = item[x_idx]
            y_m = item[y_idx]
            max_rssi = item[max_rssi_idx]
            if x_m is None or y_m is None or max_rssi is None:  # Skip incomplete rows
                continue
            grid_data[(x_m * ppm_local, y_m * ppm_local)] = max_rssi  # Convert meters -> pixels
        return grid_data

    @staticmethod
    def _add_url_switch_heatmap_trace(
        fig: Any,
        grid_data: dict[tuple[float, float], float],
        url_map_id: str,
    ) -> None:
        """Build z-matrix from sparse grid_data and add the Heatmap trace."""
        import plotly.graph_objects as go  # Local import - heavy module

        all_rssi = list(grid_data.values())
        min_rssi = min(all_rssi)
        max_rssi_val = max(all_rssi)
        unique_x = sorted({x for x, _y in grid_data})  # Distinct x bins
        unique_y = sorted({y for _x, y in grid_data})  # Distinct y bins
        z_matrix = [[grid_data.get((x_val, y_val)) for x_val in unique_x] for y_val in unique_y]  # Dense matrix
        colorscale = [  # Mirror original colorscale exactly
            [0.0, "rgb(0, 0, 255)"],
            [0.33, "rgb(0, 255, 0)"],
            [0.50, "rgb(255, 255, 0)"],
            [0.67, "rgb(255, 165, 0)"],
            [1.0, "rgb(255, 0, 0)"],
        ]
        fig.add_trace(
            go.Heatmap(
                x=unique_x,
                y=unique_y,
                z=z_matrix,
                colorscale=colorscale,
                zmin=min_rssi,
                zmax=max_rssi_val,
                opacity=0.5,
                name="RF Coverage",
                visible=False,
                showscale=True,
                colorbar=dict(
                    title=dict(text="RSSI (dBm)", side="right", font=dict(size=12, color="white")),
                    thickness=20,
                    len=0.5,
                    y=0.95,
                    yanchor="top",
                    tickfont=dict(size=10, color="white"),
                ),
                connectgaps=True,
                zsmooth="best",
            )
        )
        logging.info(
            "URL map switch: Added RF coverage heatmap with %d cells, RSSI range %s to %s dBm (map %s)",
            len(grid_data),
            min_rssi,
            max_rssi_val,
            url_map_id,
        )

    @staticmethod
    def _apply_url_switch_layout(
        fig: Any,
        new_map_name: str,
        new_map_width: int,
        new_map_height: int,
    ) -> None:
        """Apply the URL-switch figure layout (preserves original styling)."""
        fig.update_layout(
            title=dict(text=f"Map: {new_map_name}", font=dict(color="white")),
            xaxis=dict(
                range=[0, new_map_width],
                showgrid=False,
                zeroline=False,
                scaleanchor="y",
                scaleratio=1,
                constrain="domain",
            ),
            yaxis=dict(range=[new_map_height, 0], showgrid=False, zeroline=False, constrain="domain"),
            plot_bgcolor="#1a1a1a",
            paper_bgcolor="#1a1a1a",
            font=dict(color="#e0e0e0"),
            showlegend=True,
            legend=dict(bgcolor="rgba(0,0,0,0.7)", font=dict(color="white")),
            margin=dict(l=50, r=50, t=50, b=50),
        )

    @staticmethod
    def _merge_url_switch_config(
        config: dict[str, Any],
        url_map_id: str,
        new_map_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update ``config`` with the newly-switched map info (preserves site_id)."""
        new_config = config.copy()  # Don't mutate caller's dict
        new_config["map_id"] = url_map_id
        new_config["map_name"] = new_map_data.get("name", "Unnamed")
        new_config["ppm"] = new_map_data.get("ppm") or 10
        new_config["map_width"] = new_map_data.get("width", 1000)
        new_config["map_height"] = new_map_data.get("height", 1000)
        return new_config

    # ------------------------------------------------------------------
    # Callback wiring
    # ------------------------------------------------------------------

    def register(self, app: Dash) -> None:  # WHY: hooks this wave's app.callback(...) blocks into Dash
        """Attach the URL-switch callback in this cluster to ``app``."""
        from dash import Input, Output, State  # WHY: local import keeps module import-light

        app.callback(  # WHY: handle_url_map_switch - map switch triggered by URL change
            [
                Output("map-display", "figure", allow_duplicate=True),  # WHY: replaces the figure
                Output("map-config-store", "data", allow_duplicate=True),  # WHY: updates current-map config
            ],
            [Input("url-location", "search")],  # WHY: URL change trigger
            [
                State("map-config-store", "data"),  # WHY: current config
                State("map-display", "figure"),  # WHY: current figure
                State("available-maps-store", "data"),  # WHY: map allow-list
                State("map-selector-dropdown", "value"),  # WHY: current selection
            ],
            prevent_initial_call="initial_duplicate",  # WHY: allow initial run on duplicate output
        )(self.handle_url_map_switch)
