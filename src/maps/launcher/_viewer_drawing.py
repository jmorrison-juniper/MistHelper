"""Drawing-tools cluster extracted from ``viewer_callbacks.py``.

Owns the single Wave-E1 public callback ``handle_drawing_tools`` plus
its 11 private helpers (dispatcher + save/delete branches for shapes,
zones, wayfinding, walls, validation paths).  Follows the same
wrapper-class + ``__getattr__`` template used by
:mod:`src.capture._packet_capture_org` so the parent
:class:`~src.maps.launcher.viewer_callbacks.MapViewerCallbacks` stays a
thin coordinator that hands each Dash callback off to the appropriate
cluster.
"""

from __future__ import annotations  # WHY: postponed evaluation consistent with parent module

import logging  # WHY: audit trail for drawing-tool diagnostics
from typing import TYPE_CHECKING, Any  # WHY: opaque manager + type-permissive Dash callback args

if TYPE_CHECKING:  # WHY: keep dash imports lazy at runtime
    from dash import Dash  # WHY: annotation reference for register(app)


class _ViewerDrawing:  # WHY: wrapper class hosting the drawing-tools callback cluster
    """Cluster class holding the extracted handle_drawing_tools body + helpers."""

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
    # Extracted callback body + helpers (wave E1 drawing-tools cluster)
    # ------------------------------------------------------------------

    def handle_drawing_tools(  # noqa: PLR0913 - signature mirrors original Dash callback
        self,
        _save_clicks: int,
        _clear_clicks: int,
        del_path_clicks: int,
        _del_wayfinding_clicks: int,
        del_wall_clicks: int,
        _del_zone_clicks: int,
        drawing_mode: str | None,
        zone_name: str | None,
        current_fig: dict[str, Any] | None,
        config: dict[str, Any] | None,
        cache_bust_data: dict[str, Any] | None,
    ) -> tuple[Any, Any]:
        """Handle drawing tool actions - save shapes to Mist or delete from Mist."""
        import dash  # Local import: dash.callback_context only exists at request time
        from dash import no_update  # Local import keeps module import-light

        ctx = dash.callback_context  # Dash provides trigger info via callback_context
        if not ctx.triggered:  # No trigger => no-op
            return "", no_update
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]  # Component id that fired
        logging.info(  # Audit which button fired and the click counts
            "Drawing tools callback triggered: button_id=%s, del_path_clicks=%s, del_wall_clicks=%s",
            button_id,
            del_path_clicks,
            del_wall_clicks,
        )
        cfg_site_id = (config or {}).get("site_id") or self._state.site_id  # Prefer config-store value
        cfg_map_id = (config or {}).get("map_id") or self._state.map_id  # Prefer config-store value
        cfg_ppm = (config or {}).get("ppm", self._state.ppm) if config else self._state.ppm  # PPM fallback
        current_trigger = cache_bust_data.get("trigger", 0) if cache_bust_data else 0  # Cache-bust counter
        return self._dispatch_drawing_button(
            button_id, drawing_mode, zone_name, current_fig or {}, cfg_site_id, cfg_map_id, cfg_ppm, current_trigger
        )

    def _dispatch_drawing_button(  # noqa: PLR0913 - dispatcher mirrors per-button branches
        self,
        button_id: str,
        drawing_mode: str | None,
        zone_name: str | None,
        current_fig: dict[str, Any],
        site_id: str | None,
        map_id: str | None,
        ppm: float,
        current_trigger: int,
    ) -> tuple[Any, Any]:
        """Route a drawing-tool button click to its specific handler."""
        from dash import html, no_update  # Local import keeps module import-light

        if button_id == "clear-drawings-btn":  # Local-only clear (no Mist call)
            msg = "Use the eraser tool in the toolbar to clear drawings from the map"
            logging.info("Drawing tool: Clear local drawings requested")  # Audit
            return html.Span(msg, style={"color": "#ffc107"}), no_update
        if button_id == "save-shape-btn":  # Save-shape branch
            return self._handle_save_shape(drawing_mode, zone_name, current_fig, site_id, map_id, ppm, current_trigger)
        if button_id == "delete-paths-btn":  # Wipe sitesurvey_path
            return self._delete_validation_paths(site_id, map_id, current_trigger)
        if button_id == "delete-wayfinding-btn":  # Wipe wayfinding_path
            return self._delete_wayfinding_paths(site_id, map_id, current_trigger)
        if button_id == "delete-walls-btn":  # Wipe wall_path
            return self._delete_walls(site_id, map_id, current_trigger)
        if button_id == "delete-zones-btn":  # Delete every zone on this map
            return self._delete_all_zones(site_id, map_id, current_trigger)
        return "", no_update  # Unknown button => silent no-op

    def _handle_save_shape(  # noqa: PLR0913 - mirror of original save branch
        self,
        drawing_mode: str | None,
        zone_name: str | None,
        current_fig: dict[str, Any],
        site_id: str | None,
        map_id: str | None,
        ppm: float,
        current_trigger: int,
    ) -> tuple[Any, Any]:
        """Persist the last drawn shape according to the active drawing mode."""
        from dash import html, no_update  # Local import keeps module import-light

        shapes = current_fig.get("layout", {}).get("shapes", [])  # Plotly shapes list
        if not shapes:  # Nothing drawn yet
            return (
                html.Span("No shapes drawn. Use toolbar to draw first.", style={"color": "#ff6666"}),
                no_update,
            )
        last_shape = shapes[-1]  # Most-recently drawn shape
        shape_type = last_shape.get("type", "unknown")  # rect / line / path / etc.
        try:
            if drawing_mode == "zone":  # Persist as a Mist zone
                return self._save_zone_shape(last_shape, shape_type, zone_name, site_id, map_id, ppm, current_trigger)
            if drawing_mode == "wall":  # Append to wall_path
                return self._save_wall_shape(last_shape, shape_type, site_id, map_id, current_trigger)
            if drawing_mode == "path":  # Append to sitesurvey_path
                return self._save_validation_path_shape(last_shape, shape_type, site_id, map_id, ppm, current_trigger)
            return (  # Measurement mode is not persisted
                html.Span("Measurement mode - shapes not saved to Mist", style={"color": "#888"}),
                no_update,
            )
        except Exception as save_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.exception("Drawing tool: Error saving shape - %s", save_error)  # Audit failure
            return html.Span(f"Error: {str(save_error)[:50]}", style={"color": "#ff4444"}), no_update

    def _save_zone_shape(  # noqa: PLR0913 - mirror of original save-zone branch
        self,
        last_shape: dict[str, Any],
        shape_type: str,
        zone_name: str | None,
        site_id: str | None,
        map_id: str | None,
        ppm: float,
        current_trigger: int,
    ) -> tuple[Any, Any]:
        """Persist a rectangle shape as a Mist zone."""
        from dash import html, no_update  # Local import keeps module import-light

        if not zone_name:  # Required field
            return html.Span("Please enter a zone name first", style={"color": "#ff6666"}), no_update
        if shape_type != "rect":  # Mist zones must be rectangles via this UI
            return (
                html.Span(
                    "Zones require rectangle shapes. Use Draw Rectangle tool.",
                    style={"color": "#ff6666"},
                ),
                no_update,
            )
        # Convert pixel coordinates to meters using the active PPM
        x0 = last_shape.get("x0", 0) / ppm  # Top-left X (m)
        y0 = last_shape.get("y0", 0) / ppm  # Top-left Y (m)
        x1 = last_shape.get("x1", 0) / ppm  # Bottom-right X (m)
        y1 = last_shape.get("y1", 0) / ppm  # Bottom-right Y (m)
        vertices = [{"x": x0, "y": y0}, {"x": x1, "y": y0}, {"x": x1, "y": y1}, {"x": x0, "y": y1}]  # 4 corners
        zone_data = {"name": zone_name, "map_id": map_id, "vertices": vertices}  # Mist zone payload
        logging.info("Drawing tool: Creating zone '%s' at site %s", zone_name, site_id)  # Audit start
        response = self._state.mistapi_ref.api.v1.sites.zones.createSiteZone(  # Mist API write
            self._state.api_session_ref, site_id, zone_data
        )
        return self._render_save_result(
            response,
            success_msg=f"Zone '{zone_name}' saved to Mist!",
            failure_prefix="Failed to save zone",
            audit_success=f"Drawing tool: Zone '{zone_name}' created successfully",
            audit_failure="Drawing tool: Failed to create zone",
            current_trigger=current_trigger,
            success_codes=(200, 201),
        )

    def _save_wall_shape(  # noqa: PLR0913 - mirror of original save-wall branch
        self,
        last_shape: dict[str, Any],
        shape_type: str,
        site_id: str | None,
        map_id: str | None,
        current_trigger: int,
    ) -> tuple[Any, Any]:
        """Append a wall segment (line) to the map's wall_path."""
        from dash import html, no_update  # Local import keeps module import-light

        if shape_type != "line":  # Walls must be lines
            return (
                html.Span("Walls require line shapes. Use Draw Line tool.", style={"color": "#ff6666"}),
                no_update,
            )
        # Wall coordinates are stored in pixels matching the image, NOT in meters
        x0 = last_shape.get("x0", 0)  # Pixel x of segment start
        y0 = last_shape.get("y0", 0)  # Pixel y of segment start
        x1 = last_shape.get("x1", 0)  # Pixel x of segment end
        y1 = last_shape.get("y1", 0)  # Pixel y of segment end
        logging.info(  # Audit segment coords
            "Drawing tool: Saving wall segment from (%.1f, %.1f) to (%.1f, %.1f) pixels", x0, y0, x1, y1
        )
        map_response = self._state.mistapi_ref.api.v1.sites.maps.getSiteMap(  # Fetch current wall_path
            self._state.api_session_ref, site_id, map_id
        )
        existing_wall_path: dict[str, Any] = {}  # Default empty wall_path container
        if hasattr(map_response, "data"):
            existing_wall_path = map_response.data.get("wall_path", {}) or {}
        existing_nodes = existing_wall_path.get("nodes", [])  # Append to current node list
        node_count = len(existing_nodes)  # Used for unique W<n> names
        new_nodes = [  # Two-node wall segment with adjacency edge
            {
                "name": f"W{node_count}",
                "position": {"x": x0, "y": y0},
                "edges": {f"W{node_count + 1}": "wall"},
            },
            {"name": f"W{node_count + 1}", "position": {"x": x1, "y": y1}, "edges": {}},
        ]
        existing_nodes.extend(new_nodes)
        wall_path_data = {
            "coordinate": existing_wall_path.get("coordinate", "actual"),
            "nodes": existing_nodes,
        }
        update_data = {"wall_path": wall_path_data}  # updateSiteMap payload
        response = self._state.mistapi_ref.api.v1.sites.maps.updateSiteMap(  # Mist API write
            self._state.api_session_ref, site_id, map_id, update_data
        )
        return self._render_save_result(
            response,
            success_msg="Wall segment saved to Mist!",
            failure_prefix="Failed to save wall",
            audit_success="Drawing tool: Wall segment added successfully",
            audit_failure="Drawing tool: Failed to save wall",
            current_trigger=current_trigger,
            success_codes=(200,),
        )

    def _save_validation_path_shape(  # noqa: PLR0913 - mirror of original save-path branch
        self,
        last_shape: dict[str, Any],
        shape_type: str,
        site_id: str | None,
        map_id: str | None,
        ppm: float,
        current_trigger: int,
    ) -> tuple[Any, Any]:
        """Append a validation path (line) to the map's sitesurvey_path list."""
        import uuid  # Local import keeps module import-light

        from dash import html, no_update  # Local import keeps module import-light

        if shape_type == "path":  # SVG paths not supported in this UI yet
            return (
                html.Span(
                    "Path saving requires SVG parsing. Use Mist Portal for complex paths.",
                    style={"color": "#ff8800"},
                ),
                no_update,
            )
        if shape_type != "line":  # Anything else is unsupported
            return (
                html.Span("Paths require line shapes. Use Draw Line tool.", style={"color": "#ff6666"}),
                no_update,
            )
        x0 = last_shape.get("x0", 0) / ppm  # Pixel -> meter for segment start
        y0 = last_shape.get("y0", 0) / ppm
        x1 = last_shape.get("x1", 0) / ppm  # Pixel -> meter for segment end
        y1 = last_shape.get("y1", 0) / ppm
        logging.info("Drawing tool: Fetching existing sitesurvey_path before append")  # Audit start
        map_response = self._state.mistapi_ref.api.v1.sites.maps.getSiteMap(  # Fetch current paths
            self._state.api_session_ref, site_id, map_id
        )
        existing_paths: list[dict[str, Any]] = []  # Default empty paths list
        if hasattr(map_response, "data"):
            existing_paths = map_response.data.get("sitesurvey_path", []) or []
        new_path = {  # Single two-node validation path
            "id": str(uuid.uuid4()),
            "name": f"Path_{len(existing_paths) + 1}",
            "coordinate": "actual",
            "nodes": [
                {"name": "P0", "position": {"x": x0, "y": y0}, "edges": {"P1": "path"}},
                {"name": "P1", "position": {"x": x1, "y": y1}, "edges": {}},
            ],
        }
        existing_paths.append(new_path)
        update_data = {"sitesurvey_path": existing_paths}  # updateSiteMap payload
        response = self._state.mistapi_ref.api.v1.sites.maps.updateSiteMap(  # Mist API write
            self._state.api_session_ref, site_id, map_id, update_data
        )
        return self._render_save_result(
            response,
            success_msg="Validation path saved to Mist!",
            failure_prefix="Failed to save path",
            audit_success="Drawing tool: Validation path added successfully",
            audit_failure="Drawing tool: Failed to save path",
            current_trigger=current_trigger,
            success_codes=(200,),
        )

    @staticmethod
    def _render_save_result(  # noqa: PLR0913 - mirrors original inline result blocks
        response: Any,
        *,
        success_msg: str,
        failure_prefix: str,
        audit_success: str,
        audit_failure: str,
        current_trigger: int,
        success_codes: tuple[int, ...],
    ) -> tuple[Any, Any]:
        """Render the Dash output based on a save-shape Mist response."""
        from dash import html, no_update  # Local import keeps module import-light

        if hasattr(response, "status_code") and response.status_code in success_codes:  # Success path
            logging.info(audit_success)  # Audit success
            return (
                html.Span(success_msg, style={"color": "#28a745", "fontWeight": "bold"}),
                {"trigger": current_trigger + 1},
            )
        error_msg = getattr(response, "text", str(response))  # Error body or repr
        logging.error("%s - %s", audit_failure, error_msg)  # Audit failure
        return (
            html.Span(f"{failure_prefix}: {error_msg[:50]}", style={"color": "#ff4444"}),
            no_update,
        )

    def _delete_validation_paths(
        self, site_id: str | None, map_id: str | None, current_trigger: int
    ) -> tuple[Any, Any]:
        """Clear all sitesurvey_path entries via updateSiteMap."""
        from dash import html, no_update  # Local import keeps module import-light

        logging.info(  # Audit trigger
            "Drawing tool: Delete paths button clicked - site_id=%s, map_id=%s", site_id, map_id
        )
        try:
            update_data: dict[str, Any] = {"sitesurvey_path": []}  # Empty list clears all paths
            logging.info("Drawing tool: Calling updateSiteMap with %s", update_data)  # Audit body
            response = self._state.mistapi_ref.api.v1.sites.maps.updateSiteMap(  # Mist API write
                self._state.api_session_ref, site_id, map_id, update_data
            )
            logging.info(  # Audit response
                "Drawing tool: updateSiteMap response status_code=%s", getattr(response, "status_code", "N/A")
            )
            if hasattr(response, "status_code") and response.status_code == 200:
                logging.info("Drawing tool: All validation paths deleted from map %s", map_id)
                return (
                    html.Span("All validation paths deleted - click Refresh to reload map", style={"color": "#28a745"}),
                    {"trigger": current_trigger + 1},
                )
            error_msg = getattr(response, "text", str(response))  # Error body or repr
            logging.error("Drawing tool: Delete paths failed - %s", error_msg)
            return html.Span(f"Failed: {error_msg[:50]}", style={"color": "#ff4444"}), no_update
        except Exception as del_error:  # noqa: BLE001 - preserve broad-except behavior
            logging.exception("Drawing tool: Error deleting paths - %s", del_error)
            return html.Span(f"Error: {str(del_error)[:50]}", style={"color": "#ff4444"}), no_update

    def _delete_wayfinding_paths(
        self, site_id: str | None, map_id: str | None, current_trigger: int
    ) -> tuple[Any, Any]:
        """Clear all wayfinding_path entries via updateSiteMap."""
        from dash import html, no_update  # Local import keeps module import-light

        logging.info(  # Audit trigger
            "Drawing tool: Delete wayfinding button clicked - site_id=%s, map_id=%s", site_id, map_id
        )
        try:
            update_data = {"wayfinding_path": {"coordinate": "actual", "nodes": []}}  # Reset wayfinding
            logging.info("Drawing tool: Calling updateSiteMap with %s", update_data)  # Audit body
            response = self._state.mistapi_ref.api.v1.sites.maps.updateSiteMap(  # Mist API write
                self._state.api_session_ref, site_id, map_id, update_data
            )
            logging.info(  # Audit response
                "Drawing tool: updateSiteMap response status_code=%s", getattr(response, "status_code", "N/A")
            )
            if hasattr(response, "status_code") and response.status_code == 200:
                logging.info("Drawing tool: All wayfinding paths deleted from map %s", map_id)
                return (
                    html.Span("All wayfinding paths deleted - click Refresh to reload map", style={"color": "#28a745"}),
                    {"trigger": current_trigger + 1},
                )
            error_msg = getattr(response, "text", str(response))  # Error body or repr
            logging.error("Drawing tool: Delete wayfinding failed - %s", error_msg)
            return html.Span(f"Failed: {error_msg[:50]}", style={"color": "#ff4444"}), no_update
        except Exception as del_error:  # noqa: BLE001 - preserve broad-except behavior
            logging.exception("Drawing tool: Error deleting wayfinding - %s", del_error)
            return html.Span(f"Error: {str(del_error)[:50]}", style={"color": "#ff4444"}), no_update

    def _delete_walls(self, site_id: str | None, map_id: str | None, current_trigger: int) -> tuple[Any, Any]:
        """Clear wall_path entries via updateSiteMap."""
        from dash import html, no_update  # Local import keeps module import-light

        try:
            update_data: dict[str, Any] = {"wall_path": {"coordinate": "actual", "nodes": []}}  # Reset wall_path
            response = self._state.mistapi_ref.api.v1.sites.maps.updateSiteMap(  # Mist API write
                self._state.api_session_ref, site_id, map_id, update_data
            )
            if hasattr(response, "status_code") and response.status_code == 200:
                logging.info("Drawing tool: All walls deleted from map %s", map_id)
                return (
                    html.Span("All walls deleted - click Refresh to reload map", style={"color": "#28a745"}),
                    {"trigger": current_trigger + 1},
                )
            error_msg = getattr(response, "text", str(response))  # Error body or repr
            return html.Span(f"Failed: {error_msg[:50]}", style={"color": "#ff4444"}), no_update
        except Exception as del_error:  # noqa: BLE001 - preserve broad-except behavior
            logging.error("Drawing tool: Error deleting walls - %s", del_error)
            return html.Span(f"Error: {str(del_error)[:50]}", style={"color": "#ff4444"}), no_update

    def _delete_all_zones(self, site_id: str | None, map_id: str | None, current_trigger: int) -> tuple[Any, Any]:
        """Delete every zone on the current map (one DELETE per zone)."""
        from dash import html, no_update  # Local import keeps module import-light

        logging.info(  # Audit trigger
            "Drawing tool: Delete all zones button clicked - site_id=%s, map_id=%s", site_id, map_id
        )
        try:
            zones_response = self._state.mistapi_ref.api.v1.sites.zones.listSiteZones(  # Fetch zones
                self._state.api_session_ref, site_id
            )
            if not hasattr(zones_response, "status_code") or zones_response.status_code != 200:
                return html.Span("Failed to fetch zones list", style={"color": "#ff4444"}), no_update
            all_zones = zones_response.data if hasattr(zones_response, "data") else []  # All site zones
            map_zones = [z for z in all_zones if z.get("map_id") == map_id]  # Filter to current map
            if not map_zones:  # Nothing to delete
                return html.Span("No zones found on this map", style={"color": "#ffc107"}), no_update
            logging.warning("Drawing tool: Deleting %s zones from map %s", len(map_zones), map_id)  # Audit
            deleted_count, failed_count = self._delete_zones_one_by_one(site_id, map_zones)  # Loop
            if failed_count == 0:
                return (
                    html.Span(
                        f"Deleted {deleted_count} zones - click Refresh to reload map",
                        style={"color": "#28a745"},
                    ),
                    {"trigger": current_trigger + 1},
                )
            return (
                html.Span(
                    f"Deleted {deleted_count}, failed {failed_count} zones",
                    style={"color": "#ffc107"},
                ),
                {"trigger": current_trigger + 1},
            )
        except Exception as del_error:  # noqa: BLE001 - preserve broad-except behavior
            logging.exception("Drawing tool: Error deleting zones - %s", del_error)
            return html.Span(f"Error: {str(del_error)[:50]}", style={"color": "#ff4444"}), no_update

    def _delete_zones_one_by_one(self, site_id: str | None, map_zones: list[dict[str, Any]]) -> tuple[int, int]:
        """Delete each zone individually; return (deleted, failed) counts."""
        deleted_count = 0  # Successful deletes
        failed_count = 0  # Failed deletes (logged but tolerated)
        for zone in map_zones:  # One DELETE per zone (Mist has no bulk endpoint)
            zone_id = zone.get("id")  # UUID of zone to delete
            zone_name = zone.get("name", "Unknown")  # Display name for logs
            try:
                del_response = self._state.mistapi_ref.api.v1.sites.zones.deleteSiteZone(  # Mist API write
                    self._state.api_session_ref, site_id, zone_id
                )
                if hasattr(del_response, "status_code") and del_response.status_code in [200, 204]:
                    deleted_count += 1
                    logging.info("Drawing tool: Deleted zone '%s'", zone_name)  # Audit success
                else:
                    failed_count += 1
                    logging.error("Drawing tool: Failed to delete zone '%s'", zone_name)
            except Exception as zone_err:  # noqa: BLE001 - preserve broad-except behavior
                failed_count += 1
                logging.error("Drawing tool: Error deleting zone '%s': %s", zone_name, zone_err)
        return deleted_count, failed_count

    # ------------------------------------------------------------------
    # Callback wiring
    # ------------------------------------------------------------------

    def register(self, app: Dash) -> None:  # WHY: hooks this wave's app.callback(...) blocks into Dash
        """Attach the drawing-tools callback in this cluster to ``app``."""
        from dash import Input, Output, State  # WHY: local import keeps module import-light

        app.callback(  # WHY: handle_drawing_tools - save/delete shapes/paths/walls/zones
            [
                Output("drawing-tool-status", "children"),  # WHY: status text/widget output
                Output("cache-bust-store", "data", allow_duplicate=True),  # WHY: bumps to refresh dropdown
            ],
            [
                Input("save-shape-btn", "n_clicks"),  # WHY: save last drawn shape
                Input("clear-drawings-btn", "n_clicks"),  # WHY: local clear hint
                Input("delete-paths-btn", "n_clicks"),  # WHY: wipe sitesurvey_path
                Input("delete-wayfinding-btn", "n_clicks"),  # WHY: wipe wayfinding_path
                Input("delete-walls-btn", "n_clicks"),  # WHY: wipe wall_path
                Input("delete-zones-btn", "n_clicks"),  # WHY: delete every zone on this map
            ],
            [
                State("drawing-mode-dropdown", "value"),  # WHY: active drawing mode
                State("zone-name-input", "value"),  # WHY: zone name when saving as zone
                State("map-display", "figure"),  # WHY: current figure for shape extraction
                State("map-config-store", "data"),  # WHY: site_id/map_id/ppm source
                State("cache-bust-store", "data"),  # WHY: cache-bust counter
            ],
            prevent_initial_call=True,  # WHY: avoid initial render thrash
        )(self.handle_drawing_tools)
