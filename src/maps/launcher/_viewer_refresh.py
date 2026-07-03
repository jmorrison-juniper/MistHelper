"""Live-refresh cluster extracted from ``viewer_callbacks.py``.

Owns the three Wave-D public callbacks (countdown display, client
positions refresh, RF coverage heatmap refresh) plus their 14 private
helpers (fetch/partition clients, aggregate coverage grid cells, mutate
Plotly traces in place).  Follows the same wrapper-class +
``__getattr__`` template used by :mod:`src.capture._packet_capture_org`
so the parent
:class:`~src.maps.launcher.viewer_callbacks.MapViewerCallbacks` stays a
thin coordinator that hands each Dash callback off to the appropriate
cluster.
"""

from __future__ import annotations  # WHY: postponed evaluation consistent with parent module

import logging  # WHY: audit trail for live-refresh diagnostics
from datetime import datetime  # WHY: human-readable audit timestamps on refresh completion
from typing import TYPE_CHECKING, Any  # WHY: opaque manager + type-permissive Dash callback args

if TYPE_CHECKING:  # WHY: keep dash imports lazy at runtime
    from dash import Dash  # WHY: annotation reference for register(app)


class _ViewerRefresh:  # WHY: wrapper class hosting the live-refresh callback cluster
    """Cluster class holding the extracted countdown/clients/coverage refresh bodies."""

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
    # Extracted callback bodies (wave D of the refresh cluster)
    # ------------------------------------------------------------------

    def update_countdown_display(
        self,
        _n_intervals: int,
        refresh_times: dict[str, float] | None,
        toggle_value: list[str] | None,
    ) -> str:
        """Render the per-second countdown until the next client/RF refresh."""
        import time  # Local import keeps module import-light (matches original closure)

        if not refresh_times or "enabled" not in (toggle_value or []):  # Refresh disabled or never seeded
            return "Auto-refresh: Off"  # User-facing label (byte-identical to original)

        current_time = time.time()  # Epoch seconds anchors all deltas below

        # Seconds elapsed since last client refresh (used to compute 30s cadence remaining)
        client_elapsed = current_time - refresh_times.get("client_last_refresh", current_time)
        client_remaining = max(0, 30 - int(client_elapsed) % 30)  # 30s cadence -> seconds until next tick

        # Seconds elapsed since last coverage refresh (used to compute 5 min cadence remaining)
        coverage_elapsed = current_time - refresh_times.get("coverage_last_refresh", current_time)
        coverage_remaining = max(0, 300 - int(coverage_elapsed) % 300)  # 5 min cadence -> remaining
        coverage_mins = coverage_remaining // 60  # Whole minutes of remaining wait
        coverage_secs = coverage_remaining % 60  # Residual seconds after the minute split

        return f"Clients: {client_remaining}s | RF: {coverage_mins}:{coverage_secs:02d}"  # User-facing label

    def update_clients_traces(
        self,
        _n_intervals: int,
        _manual_clicks: int | None,
        config: dict[str, Any] | None,
        current_fig: dict[str, Any],
        _client_layers: Any,
        refresh_times: dict[str, float] | None,
    ) -> tuple[Any, Any]:
        """Refresh wireless and wired client traces from the Mist API."""
        import time  # Stdlib for refresh-time stamp

        import dash  # Local import: dash.callback_context only exists at request time
        from dash import no_update  # Sentinel used to skip output updates

        ctx = dash.callback_context  # Trigger info exposed by Dash on every callback
        if not ctx.triggered:  # No trigger => skip both outputs
            return no_update, no_update

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]  # Component id that fired the callback
        if trigger_id == "manual-refresh-btn":  # User clicked the manual refresh button
            logging.info("Live data refresh: Manual refresh requested")  # Preserve original audit log

        current_time = time.time()  # Snapshot for the refresh-time store
        updated_refresh_times = refresh_times.copy() if refresh_times else {}  # Copy avoids mutating shared store
        updated_refresh_times["client_last_refresh"] = current_time  # Persist refresh anchor for countdown

        site_id_local = config.get("site_id") if config else None  # Required by every API call below
        map_id_local = config.get("map_id") if config else None  # Filter for clients/zones/walls on this map

        if not site_id_local:  # Missing site_id is a misconfiguration; skip refresh
            logging.warning("Live data refresh: site_id is None, skipping refresh. Config: %s", config)  # Audit
            return no_update, updated_refresh_times
        if not map_id_local:  # Missing map_id is a misconfiguration; skip refresh
            logging.warning("Live data refresh: map_id is None, skipping refresh")  # Audit
            return no_update, updated_refresh_times

        try:
            fresh_clients = self._fetch_fresh_clients(site_id_local, map_id_local)  # Pull + filter clients
            if fresh_clients is None:  # API failure already logged inside helper
                return no_update, updated_refresh_times
            wifi_data, wired_data = self._partition_clients_by_link(fresh_clients)  # Split for trace updates
            self._apply_client_traces(current_fig, wifi_data, wired_data)  # Mutate Plotly traces in place
            self._apply_client_annotations(current_fig, wifi_data)  # Refresh WiFi client label widgets
            self._refresh_zones_silent(site_id_local, map_id_local)  # Side-effect log of zone count
            self._refresh_walls_silent(site_id_local, map_id_local, current_fig)  # Side-effect log of wall count
            timestamp = datetime.now().strftime("%H:%M:%S")  # Human-readable timestamp for audit log
            logging.info(  # Preserve original completion audit message
                "Live data refresh: Client positions updated at %s - WiFi: %s, Wired: %s",
                timestamp,
                len(wifi_data["x"]),
                len(wired_data["x"]),
            )
            return current_fig, updated_refresh_times
        except Exception as refresh_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.exception("Live data refresh: Error refreshing clients: %s", refresh_error)  # Audit
            return no_update, updated_refresh_times

    def _fetch_fresh_clients(self, site_id: str, map_id: str) -> list[dict[str, Any]] | None:
        """Fetch site wireless clients and filter for this map (returns None on API error)."""
        logging.info(  # Preserve original "fetching" audit log
            "Live data refresh: Fetching client positions for map %s (site: %s)", map_id, site_id
        )
        clients_response = self._state.mistapi_ref.api.v1.sites.stats.listSiteWirelessClientsStats(  # Mist API call
            self._state.api_session_ref, site_id=site_id, limit=1000
        )
        if clients_response.status_code != 200:  # API error => caller short-circuits
            logging.warning(  # Audit failure with HTTP status
                "Live data refresh: Failed to fetch clients - HTTP %s", clients_response.status_code
            )
            return None
        all_clients = self._state.mistapi_ref.get_all(  # Pagination helper exhausts the result set
            response=clients_response, mist_session=self._state.api_session_ref
        )
        fresh_clients = [  # Keep only positioned clients on this specific map
            c for c in all_clients if c.get("map_id") == map_id and c.get("x") is not None and c.get("y") is not None
        ]
        logging.info(  # Preserve original "found" audit log
            "Live data refresh: Found %s clients on map (total: %s)", len(fresh_clients), len(all_clients)
        )
        logging.debug("Live data refresh: client fetch complete count=%d", len(fresh_clients))  # Detail trace
        return fresh_clients

    @staticmethod
    def _partition_clients_by_link(
        fresh_clients: list[dict[str, Any]],
    ) -> tuple[dict[str, list[Any]], dict[str, list[Any]]]:
        """Split clients into WiFi vs Wired bundles for trace updates."""
        wifi: dict[str, list[Any]] = {"x": [], "y": [], "hover": [], "names": []}  # WiFi trace buckets
        wired: dict[str, list[Any]] = {"x": [], "y": [], "hover": [], "names": []}  # Wired trace buckets
        for client in fresh_clients:  # Walk every positioned client
            client_x_px = client.get("x")  # API already returns pixels (no PPM multiplication)
            client_y_px = client.get("y")  # API already returns pixels (no PPM multiplication)
            if client_x_px is None or client_y_px is None:  # Defensive guard for partial records
                continue
            hostname = client.get("hostname", "")  # Friendlier than MAC for the label
            client_mac = client.get("mac", "Unknown")  # Fallback identifier
            client_name = hostname if hostname else client_mac[-8:]  # Last 4 hex pairs of MAC as fallback
            hover_text = (  # Multi-line hover identical to original implementation
                f"<b>Client</b><br>MAC: {client_mac}<br>"
                f"Hostname: {hostname or 'N/A'}<br>IP: {client.get('ip', 'N/A')}<br>"
                f"SSID: {client.get('ssid', 'N/A')}<br>RSSI: {client.get('rssi', 'N/A')} dBm<br>"
                f"Position: ({client_x_px}, {client_y_px})"
            )
            bucket = wired if client.get("wired", False) else wifi  # Route to the correct trace bucket
            bucket["x"].append(client_x_px)  # X pixel coordinate
            bucket["y"].append(client_y_px)  # Y pixel coordinate
            bucket["hover"].append(hover_text)  # Pre-rendered hover HTML
            bucket["names"].append(client_name)  # Short label for annotations
        return wifi, wired

    @staticmethod
    def _apply_client_traces(
        current_fig: dict[str, Any],
        wifi: dict[str, list[Any]],
        wired: dict[str, list[Any]],
    ) -> None:
        """Mutate the WiFi/Wired client traces in the figure in place."""
        trace_updated = False  # Track whether we found a matching trace at all
        for trace in current_fig["data"]:  # Plotly traces array
            trace_name = trace.get("name", "").lower()  # Case-insensitive matching
            if trace_name == "clients" or ("wifi client" in trace_name and "link" not in trace_name):
                trace["x"] = wifi["x"]  # Replace X coords
                trace["y"] = wifi["y"]  # Replace Y coords
                trace["hovertext"] = wifi["hover"]  # Replace hover HTML
                trace_updated = True  # At least the WiFi trace was updated
                logging.info(  # Preserve original audit log
                    "Live data refresh: Updated WiFi clients trace with %s clients, coords sample: %s",
                    len(wifi["x"]),
                    wifi["x"][:3] if wifi["x"] else "empty",
                )
            elif "wired client" in trace_name and "link" not in trace_name:  # Wired client trace
                trace["x"] = wired["x"]  # Replace X coords
                trace["y"] = wired["y"]  # Replace Y coords
                trace["hovertext"] = wired["hover"]  # Replace hover HTML
                logging.info(  # Preserve original audit log
                    "Live data refresh: Updated Wired clients trace with %s clients", len(wired["x"])
                )
        if not trace_updated:  # Warn when neither trace was found
            logging.warning(  # Preserve original warning identifying the available trace names
                "Live data refresh: Could not find 'Clients' trace to update. Available traces: %s",
                [t.get("name", "unnamed") for t in current_fig["data"]],
            )

    @staticmethod
    def _apply_client_annotations(current_fig: dict[str, Any], wifi: dict[str, list[Any]]) -> None:
        """Replace the WiFi 'Clients Label' annotations with fresh positions."""
        if "layout" not in current_fig or "annotations" not in current_fig["layout"]:  # No annotations array
            return  # Nothing to mutate
        new_annotations = [  # Drop the prior "Clients Label" entries
            ann for ann in current_fig["layout"]["annotations"] if ann.get("name") != "Clients Label"
        ]
        for x, y, name in zip(wifi["x"], wifi["y"], wifi["names"], strict=True):  # Add new labels
            new_annotations.append(
                {
                    "x": x,  # Anchor X to the client marker
                    "y": y - 10,  # Position 10 px below the marker
                    "text": f"<b>{name}</b>",  # Bold short label
                    "showarrow": False,
                    "font": {"size": 9, "color": "white", "family": "Arial"},
                    "bgcolor": "rgba(0,128,0,0.9)",
                    "bordercolor": "white",
                    "borderwidth": 1,
                    "borderpad": 2,
                    "xanchor": "center",
                    "yanchor": "bottom",
                    "name": "Clients Label",  # Tag for the next refresh to remove
                }
            )
        current_fig["layout"]["annotations"] = new_annotations  # Commit the replacement
        logging.info("Live data refresh: Updated %s client label annotations", len(wifi["names"]))  # Audit

    def _refresh_zones_silent(self, site_id: str, map_id: str) -> None:
        """Fetch zones for logging visibility only; swallow errors per original behavior."""
        try:
            zones_response = self._state.mistapi_ref.api.v1.sites.zones.listSiteZones(  # Mist API call
                self._state.api_session_ref, site_id=site_id
            )
            if zones_response.status_code == 200:  # Only log when fetch succeeded
                all_zones = self._state.mistapi_ref.get_all(  # Pagination helper exhausts the result set
                    response=zones_response, mist_session=self._state.api_session_ref
                )
                zones_on_map = [z for z in all_zones if z.get("map_id") == map_id]  # Filter to this map
                logging.info("Live data refresh: Found %s zones on map", len(zones_on_map))  # Audit
        except Exception as zone_refresh_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.warning("Live data refresh: Error refreshing zones: %s", zone_refresh_error)  # Audit warning

    def _refresh_walls_silent(self, site_id: str, map_id: str, current_fig: dict[str, Any]) -> None:
        """Fetch map walls for logging visibility only; swallow errors per original behavior."""
        try:
            map_response = self._state.mistapi_ref.api.v1.sites.maps.getSiteMap(  # Mist API call
                self._state.api_session_ref, site_id=site_id, map_id=map_id
            )
            if map_response.status_code == 200:  # Only walk walls when fetch succeeded
                map_data_fresh = map_response.data  # Raw map payload
                wall_path = map_data_fresh.get("wall_path", {})  # Walls live under wall_path
                wall_nodes = wall_path.get("nodes", [])  # Node list (may be empty)
                logging.info("Live data refresh: Map has %s wall nodes", len(wall_nodes))  # Audit
                if wall_nodes:  # Preserve the original 'walls' trace touch (no mutation, parity only)
                    for trace in current_fig["data"]:  # Walk every trace
                        if trace.get("name", "").lower() == "walls":  # Find the walls trace
                            break  # Original code intentionally does no work here
        except Exception as wall_refresh_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.warning("Live data refresh: Error refreshing walls: %s", wall_refresh_error)  # Audit warning

    def update_coverage_heatmap(
        self,
        n_intervals: int,
        config: dict[str, Any] | None,
        current_fig: dict[str, Any],
        layer_values: list[str] | None,
        refresh_times: dict[str, float] | None,
    ) -> tuple[Any, Any]:
        """Refresh the RF coverage heatmap trace from the Mist coverage API."""
        import time  # Stdlib for refresh-time stamp

        from dash import no_update  # Sentinel used to skip output updates

        if n_intervals == 0:  # Initial tick is ignored by the original implementation
            return no_update, no_update

        current_time = time.time()  # Snapshot for the refresh-time store
        updated_refresh_times = refresh_times.copy() if refresh_times else {}  # Copy avoids mutating shared store
        updated_refresh_times["coverage_last_refresh"] = current_time  # Persist anchor for countdown

        resolved = self._resolve_coverage_config(config)  # Validate site_id/map_id presence
        if resolved is None:  # Already logged inside helper
            return no_update, updated_refresh_times
        site_id_local, map_id_local, ppm_local = resolved

        try:
            coverage_results = self._fetch_coverage_results(site_id_local, map_id_local)  # Fetch payload
            if coverage_results is None:  # Error or empty already logged inside helper
                return no_update, updated_refresh_times
            results, result_def = coverage_results  # Tuple unpack
            grid_info = self._build_coverage_grid(results, result_def, ppm_local)  # Build heatmap data
            if grid_info is None:  # Missing fields or empty grid already logged inside helper
                return no_update, updated_refresh_times
            self._apply_coverage_trace(current_fig, grid_info, layer_values)  # Mutate Plotly trace in place
            timestamp = datetime.now().strftime("%H:%M:%S")  # Human-readable timestamp for audit
            logging.info(  # Preserve original completion audit log
                "Live data refresh: RF coverage updated at %s - %s points", timestamp, len(results)
            )
            return current_fig, updated_refresh_times
        except Exception as refresh_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.exception(  # Capture stack trace
                "Live data refresh: Error refreshing RF coverage: %s", refresh_error
            )
            return no_update, updated_refresh_times

    def _fetch_coverage_results(self, site_id: str, map_id: str) -> tuple[list[Any], list[str]] | None:
        """Call the coverage endpoint and validate the payload; return (results, result_def) or None."""
        logging.info(  # Preserve original audit log
            "Live data refresh: Fetching RF coverage data for map %s (site: %s)", map_id, site_id
        )
        coverage_url = f"/api/v1/sites/{site_id}/location/coverage"  # Mist coverage endpoint path
        coverage_params = {  # Query parameters mirroring the original request
            "resolution": "fine",
            "duration": "1d",
            "map_id": map_id,
            "type": "client",
            "from_apollo": "true",
        }
        coverage_response = self._state.api_session_ref.mist_get(coverage_url, query=coverage_params)  # API call
        if coverage_response.status_code != 200:  # Network or auth failure
            logging.warning(  # Preserve original warning text
                "Live data refresh: Failed to fetch RF coverage - HTTP %s", coverage_response.status_code
            )
            return None
        coverage_data = coverage_response.data  # Parsed JSON payload
        if isinstance(coverage_data, dict) and "exception" in coverage_data:  # API-level error response
            logging.warning("Live data refresh: Coverage API returned error")  # Audit
            return None
        result_def = coverage_data.get("result_def", [])  # Field name array
        results = coverage_data.get("results", [])  # Per-cell measurement array
        if not results or not result_def:  # Empty payload => nothing to render
            logging.info("Live data refresh: No coverage data available")  # Audit
            return None
        logging.info("Live data refresh: Processing %s coverage grid points", len(results))  # Audit
        return results, result_def

    @staticmethod
    def _resolve_coverage_config(
        config: dict[str, Any] | None,
    ) -> tuple[str, str, float] | None:
        """Validate the config store and return (site_id, map_id, ppm) or None on failure."""
        site_id_local = config.get("site_id") if config else None  # Required for the coverage URL
        map_id_local = config.get("map_id") if config else None  # Required filter for this map
        ppm_local = config.get("ppm", 10) if config else 10  # Pixel/meter conversion for the grid
        if not site_id_local:  # Missing site_id is a misconfiguration; skip refresh
            logging.warning(  # Preserve original audit warning text
                "Live data refresh: RF coverage - site_id is None, skipping. Config: %s", config
            )
            return None
        if not map_id_local:  # Missing map_id is a misconfiguration; skip refresh
            logging.warning("Live data refresh: RF coverage - map_id is None, skipping")  # Audit
            return None
        return site_id_local, map_id_local, ppm_local

    @staticmethod
    def _extract_coverage_indices(result_def: list[str]) -> tuple[int, int, int] | None:
        """Return (x_idx, y_idx, rssi_idx) or None when result_def lacks required columns."""
        try:
            x_idx = result_def.index("x")  # Column index for X (meters)
            y_idx = result_def.index("y")  # Column index for Y (meters)
        except ValueError as index_error:  # result_def missing required column
            logging.warning(  # Preserve original warning text
                "Live data refresh: Missing expected fields in result_def: %s", index_error
            )
            return None
        if "max_rssi" in result_def:  # Prefer max_rssi when available
            rssi_idx = result_def.index("max_rssi")
        elif "avg_rssi" in result_def:  # Fall back to avg_rssi
            rssi_idx = result_def.index("avg_rssi")
        else:  # No usable RSSI column; default sentinel handled downstream
            rssi_idx = -1
        return x_idx, y_idx, rssi_idx

    @staticmethod
    def _aggregate_grid_cells(
        results: list[Any], x_idx: int, y_idx: int, rssi_idx: int
    ) -> dict[tuple[float, float], float]:
        """Aggregate raw coverage rows into a (x_m, y_m) -> rssi mapping."""
        grid_data: dict[tuple[float, float], float] = {}  # Aggregated cells
        for point in results:  # Walk every grid sample
            x_meters = point[x_idx] if x_idx < len(point) else 0  # Defensive bound check
            y_meters = point[y_idx] if y_idx < len(point) else 0  # Defensive bound check
            rssi_val = point[rssi_idx] if 0 <= rssi_idx < len(point) else -100  # Default floor when missing
            grid_data[(x_meters, y_meters)] = rssi_val
        return grid_data

    @staticmethod
    def _build_z_matrix(grid_data: dict[tuple[float, float], float], ppm_local: float) -> dict[str, Any]:
        """Project the aggregated grid into pixel-space bins + 2D z-matrix for Plotly."""
        unique_x_m = sorted({k[0] for k in grid_data.keys()})  # Unique X bins in meters
        unique_y_m = sorted({k[1] for k in grid_data.keys()})  # Unique Y bins in meters
        unique_x = [x_m * ppm_local for x_m in unique_x_m]  # Convert to pixel coordinates
        unique_y = [y_m * ppm_local for y_m in unique_y_m]  # Convert to pixel coordinates
        z_matrix = [  # 2D matrix expected by Plotly Heatmap (rows are Y bins)
            [grid_data.get((x_m, y_m), None) for x_m in unique_x_m] for y_m in unique_y_m  # Cols are X bins
        ]
        min_rssi, max_rssi = _ViewerRefresh._compute_rssi_bounds(grid_data)  # WHY: color scale bounds
        return {
            "unique_x": unique_x,  # Pixel-space X bins
            "unique_y": unique_y,  # Pixel-space Y bins
            "z_matrix": z_matrix,  # 2D RSSI grid
            "min_rssi": min_rssi,  # Color scale lower bound
            "max_rssi": max_rssi,  # Color scale upper bound
            "cell_count": len(grid_data),  # For audit logging
        }

    @staticmethod
    def _compute_rssi_bounds(grid_data: dict[tuple[float, float], float]) -> tuple[float, float]:
        """Compute (min, max) RSSI for the heatmap color scale; defaults preserve original behavior."""
        all_rssi = [v for v in grid_data.values() if v is not None]  # Non-null samples only
        if not all_rssi:  # Empty grid => use the original defaults
            return -100, -30
        return min(all_rssi), max(all_rssi)

    @classmethod
    def _build_coverage_grid(cls, results: list[Any], result_def: list[str], ppm_local: float) -> dict[str, Any] | None:
        """Translate the coverage results into a heatmap-ready grid dict; return None when unusable."""
        indices = cls._extract_coverage_indices(result_def)  # Resolve column indices
        if indices is None:  # Missing required columns; already logged
            return None
        x_idx, y_idx, rssi_idx = indices
        grid_data = cls._aggregate_grid_cells(results, x_idx, y_idx, rssi_idx)  # Reduce rows -> cells
        if not grid_data:  # Coverage payload was non-empty but yielded no cells
            logging.info("Live data refresh: No coverage grid data to visualize")  # Audit
            return None
        return cls._build_z_matrix(grid_data, ppm_local)  # Project into Plotly heatmap shape

    @staticmethod
    def _apply_coverage_trace(
        current_fig: dict[str, Any],
        grid_info: dict[str, Any],
        layer_values: list[str] | None,
    ) -> None:
        """Mutate the RF coverage heatmap trace in place."""
        for trace in current_fig["data"]:  # Walk every trace
            if "rf coverage" in trace.get("name", "").lower():  # Match the heatmap trace
                trace["x"] = grid_info["unique_x"]  # Pixel-space X bins
                trace["y"] = grid_info["unique_y"]  # Pixel-space Y bins
                trace["z"] = grid_info["z_matrix"]  # 2D RSSI grid
                trace["zmin"] = grid_info["min_rssi"]  # Color scale lower bound
                trace["zmax"] = grid_info["max_rssi"]  # Color scale upper bound
                trace["visible"] = "rf_heatmap" in (layer_values or [])  # Visibility follows toggle
                logging.debug(  # Preserve original debug audit
                    "Live data refresh: Updated RF coverage heatmap with %s cells", grid_info["cell_count"]
                )
                break  # Only one coverage trace expected

    # ------------------------------------------------------------------
    # Callback wiring
    # ------------------------------------------------------------------

    def register(self, app: Dash) -> None:  # WHY: hooks this wave's app.callback(...) blocks into Dash
        """Attach the live-refresh callbacks in this cluster to ``app``."""
        from dash import Input, Output, State  # WHY: local import keeps module import-light

        app.callback(  # WHY: update_countdown_display - per-second countdown label
            Output("countdown-display", "children", allow_duplicate=True),  # WHY: countdown text output
            [Input("countdown-tick-interval", "n_intervals")],  # WHY: 1s tick trigger
            [State("refresh-times-store", "data"), State("auto-refresh-toggle", "value")],  # WHY: anchors+toggle
            prevent_initial_call=True,  # WHY: avoid initial render thrash
        )(self.update_countdown_display)

        app.callback(  # WHY: update_clients_traces - 30s live client positions refresh
            [
                Output("map-display", "figure", allow_duplicate=True),  # WHY: mutated figure (duplicate output)
                Output("refresh-times-store", "data", allow_duplicate=True),  # WHY: updated refresh anchor
            ],
            [
                Input("client-refresh-interval", "n_intervals"),  # WHY: 30s timer trigger
                Input("manual-refresh-btn", "n_clicks"),  # WHY: manual refresh button
            ],
            [
                State("map-config-store", "data"),  # WHY: site_id/map_id source
                State("map-display", "figure"),  # WHY: current figure for in-place mutation
                State("client-toggle", "value"),  # WHY: reserved for parity with original signature
                State("refresh-times-store", "data"),  # WHY: existing refresh anchors
            ],
            prevent_initial_call=True,  # WHY: avoid initial render thrash
        )(self.update_clients_traces)

        app.callback(  # WHY: update_coverage_heatmap - 5-minute RF coverage refresh
            [
                Output("map-display", "figure", allow_duplicate=True),  # WHY: mutated figure (duplicate output)
                Output("refresh-times-store", "data", allow_duplicate=True),  # WHY: updated refresh anchor
            ],
            [Input("coverage-refresh-interval", "n_intervals")],  # WHY: 5-minute timer trigger
            [
                State("map-config-store", "data"),  # WHY: site_id/map_id/ppm source
                State("map-display", "figure"),  # WHY: current figure for in-place mutation
                State("layer-toggle", "value"),  # WHY: drives heatmap visibility flag
                State("refresh-times-store", "data"),  # WHY: existing refresh anchors
            ],
            prevent_initial_call=True,  # WHY: avoid initial render thrash
        )(self.update_coverage_heatmap)
