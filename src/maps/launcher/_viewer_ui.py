"""UI toggles cluster extracted from ``viewer_callbacks.py``.

Owns the 12 user-facing UI callbacks (click details, mode toggles,
panel show/hide, utilities row, drawn-shape labels, origin-on-click,
map deletion, zone edit/remove) along with their private ``_handle_*``
and ``_render_*`` helpers.  Follows the same wrapper-class +
``__getattr__`` template used by :mod:`src.capture._packet_capture_org`
so the parent
:class:`~src.maps.launcher.viewer_callbacks.MapViewerCallbacks` stays a
thin coordinator that hands each Dash callback off to the appropriate
cluster.
"""

from __future__ import annotations  # WHY: postponed evaluation consistent with parent module

import logging  # WHY: audit trail for destructive UI actions (delete map/zone)
import time  # WHY: countdown baseline for auto-refresh toggle
from typing import TYPE_CHECKING, Any  # WHY: opaque manager + type-permissive Dash callback args

if TYPE_CHECKING:  # WHY: keep dash imports lazy at runtime
    from dash import Dash  # WHY: annotation reference for register(app)


class _ViewerUI:  # WHY: wrapper class hosting the UI-toggle callback cluster
    """Cluster class holding the extracted UI-toggle callback bodies."""

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
    # Extracted callback methods (waves A + B + C of the UI cluster)
    # ------------------------------------------------------------------

    def display_click_data(self, click_data: Any) -> Any:  # WHY: Dash callback body for clickData->details panel
        """Render a Dash details panel describing the most recently clicked trace point."""
        # Defer import of dash.html until the callback actually fires,
        # mirroring the original closure which captured `html` from the
        # enclosing _launch_plotly_viewer scope.
        from dash import html  # Local import keeps module import-light

        # Build the click-details panel via the callback manager helper
        # which produces dash.html components (P/H3/Div).
        return self._state.callback_manager.build_click_details(
            click_data=click_data,  # Plotly clickData dict (point + curve info)
            html=html,  # Pass dash.html so the helper can build widgets
        )

    def toggle_origin_mode(  # WHY: parity-based toggle for origin-set mode
        self, n_clicks: int, current_style: dict[str, Any]
    ) -> dict[str, Any]:
        """Toggle origin setting mode on/off with visual feedback."""
        if n_clicks % 2 == 1:  # Odd click count means mode is ACTIVE
            current_style["backgroundColor"] = "#667eea"  # Purple fill highlights armed state
            current_style["border"] = "2px solid #00bfff"  # Cyan border reinforces armed state
            return current_style  # Return mutated style dict to Dash
        # Even clicks (including initial 0) mean the mode is INACTIVE
        current_style["backgroundColor"] = "#3d3d3d"  # Neutral dark gray = inactive button
        current_style["border"] = "1px solid #667eea"  # Thin purple border at rest
        return current_style  # Return mutated style dict to Dash

    def toggle_zone_name_input(self, mode: str | None) -> dict[str, str]:  # WHY: input row is zone-mode-only
        """Show zone name input only when zone mode is selected."""
        if mode == "zone":  # Only zone drawing mode needs the zone-name field
            return {"display": "block", "marginBottom": "10px"}  # Reveal the input row
        return {"display": "none"}  # Hide the input for wall/path/measure modes

    def toggle_auto_refresh(  # WHY: drives 3 dcc.Interval flags + countdown label
        self, toggle_value: list[str] | None
    ) -> tuple[bool, bool, bool, dict[str, float], str]:
        """Enable or disable auto-refresh intervals based on checkbox."""
        is_enabled = "enabled" in (toggle_value or [])  # Checklist contains "enabled" when checked
        current_time = time.time()  # Snapshot epoch seconds for countdown baseline

        if is_enabled:  # User just turned auto-refresh ON
            logging.info("Live data refresh: Auto-refresh ENABLED by user")  # Preserve audit log
            # Seed both refresh timestamps to "now" so countdown starts at the full interval
            refresh_data = {
                "client_last_refresh": current_time,  # Wireless client refresh anchor
                "coverage_last_refresh": current_time,  # RF coverage refresh anchor
            }
            countdown_text = "Clients: 30s | RF: 5:00"  # Initial countdown label shown to user
        else:  # User turned auto-refresh OFF
            logging.info("Live data refresh: Auto-refresh DISABLED by user")  # Preserve audit log
            refresh_data = {
                "client_last_refresh": 0,  # Zero sentinel = client refresh stopped
                "coverage_last_refresh": 0,  # Zero sentinel = coverage refresh stopped
            }
            countdown_text = "Auto-refresh: Off"  # Display string communicating disabled state

        # Dash dcc.Interval components are paused via disabled=True, so we
        # invert the user-facing boolean: "enabled" => disabled=False.
        return (
            not is_enabled,  # client-refresh-interval.disabled
            not is_enabled,  # coverage-refresh-interval.disabled
            not is_enabled,  # countdown-tick-interval.disabled
            refresh_data,  # refresh-times-store.data
            countdown_text,  # countdown-display.children
        )

    def toggle_individual_zones(  # WHY: flips visibility on "Zone:"-prefixed traces per checklist
        self, selected_zone_ids: list[str] | None, current_fig: dict[str, Any]
    ) -> dict[str, Any]:
        """Show/hide individual zones based on checklist."""
        if not self._state.zones:  # No zones available => nothing to toggle
            return current_fig  # Return figure unchanged

        # Build a set for O(1) membership tests across many traces
        selected_set = set(selected_zone_ids) if selected_zone_ids else set()  # Empty when user cleared all

        # Walk every trace, flipping visibility only on "Zone:"-named traces
        for trace in current_fig["data"]:  # Plotly traces array
            trace_name = trace.get("name", "")  # Some traces lack a name key
            if trace_name.startswith("Zone:"):  # Only mutate zone overlay traces
                zone_name = trace_name.replace("Zone: ", "")  # Strip the "Zone: " prefix
                for i, zone in enumerate(self._state.zones):  # Find the matching zone record
                    if zone.get("name") == zone_name:  # Name match anchors the ID lookup
                        zone_id = zone.get("id", f"zone_{i}")  # Fallback ID matches original closure
                        trace["visible"] = zone_id in selected_set  # True/False drives visibility
                        break  # Stop scanning zones once matched

        return current_fig  # Return mutated figure dict to Dash

    def toggle_delete_panel(  # WHY: dispatches on the button id captured in callback_context
        self,
        _delete_clicks: int,
        _cancel_clicks: int,
        _confirm_clicks: int,
        current_style: dict[str, Any],
        config: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], Any]:
        """Show or hide the delete confirmation panel and update map name."""
        import dash  # Local import: dash.callback_context only exists at request time
        from dash import no_update  # Sentinel used to skip output updates

        ctx = dash.callback_context  # Dash provides trigger info via callback_context
        if not ctx.triggered:  # WHY: no trigger => leave outputs untouched via no_update
            return current_style, no_update

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]  # Component id that fired

        current_map_name = config.get("map_name", "Unknown") if config else "Unknown"  # Display name from config store

        if button_id == "delete-btn":  # User clicked the red "Delete map" button
            logging.warning(  # Audit log captures who/what is being deleted
                "Delete panel opened for map '%s' (ID: %s)",
                current_map_name,
                config.get("map_id") if config else "unknown",
            )
            return (
                {  # Show the panel (display: block) with destructive-red styling
                    "display": "block",
                    "padding": "12px 20px",
                    "backgroundColor": "#330000",
                    "borderBottom": "2px solid #ff4444",
                },
                f"Map: {current_map_name}",  # Update the panel header with the map name
            )
        if button_id in ["cancel-delete-btn", "confirm-delete-btn"]:  # Hide panel on cancel or confirm
            return (
                {  # Hide the panel (display: none) preserving the rest of the styling
                    "display": "none",
                    "padding": "12px 20px",
                    "backgroundColor": "#330000",
                    "borderBottom": "2px solid #ff4444",
                },
                no_update,  # Don't overwrite the map name display while hiding
            )

        return current_style, no_update  # Fallback: keep style, skip name update

    def toggle_clone_panel(  # WHY: dispatches on the button id captured in callback_context
        self,
        _clone_clicks: int,
        _cancel_clicks: int,
        _execute_clicks: int,
        current_style: dict[str, Any],
    ) -> dict[str, Any]:
        """Show or hide the clone input panel."""
        import dash  # Local import: dash.callback_context only exists at request time

        ctx = dash.callback_context  # Dash provides trigger info via callback_context
        if not ctx.triggered:  # WHY: no trigger => leave the style dict unchanged
            return current_style

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]  # Component id that fired

        if button_id == "clone-btn":  # User clicked the green "Clone map" button
            logging.info("Clone panel opened for map %s", self._state.map_id)  # Audit trail
            return {  # Show the panel (display: block) with success-green styling
                "display": "block",
                "padding": "12px 20px",
                "backgroundColor": "#1a1a1a",
                "borderBottom": "1px solid #00ff88",
            }
        if button_id in ["cancel-clone-btn", "execute-clone-btn"]:  # Hide panel on cancel or execute
            return {  # Hide the panel (display: none) preserving the rest of the styling
                "display": "none",
                "padding": "12px 20px",
                "backgroundColor": "#1a1a1a",
                "borderBottom": "1px solid #00ff88",
            }

        return current_style  # Fallback: keep style

    def handle_utilities(
        self,
        _auto_zone_clicks: int,
        _change_clicks: int,
        _remove_clicks: int,
        _rename_clicks: int,
    ) -> Any:
        """Handle utilities button clicks."""
        import dash  # Local import: dash.callback_context only exists at request time
        from dash import html  # html.Span for status output

        ctx = dash.callback_context  # Dash provides trigger info via callback_context
        if not ctx.triggered:  # No trigger => render empty status
            return ""

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]  # Component id that fired
        map_id = self._state.map_id  # Closure-equivalent: original logged map_id

        if button_id == "auto-zone-btn":  # AI auto-zone detection request
            msg = (
                "Robot Auto-Zone: AI-powered zone detection"
                " - analyzes walls and creates location zones automatically"
            )
            logging.info("Utilities: Auto-Zone requested for map %s", map_id)  # Audit trail
            return html.Span(msg, style={"color": "#667eea", "fontWeight": "bold"})  # Purple = info
        if button_id == "change-image-btn":  # Replace map image request
            msg = "! Change Image: Use Mist API updateSiteMapImage - feature requires file upload"
            logging.info("Utilities: Change Image requested for map %s", map_id)  # Audit trail
            return html.Span(msg, style={"color": "#ff8800"})  # Orange = warning
        if button_id == "remove-image-btn":  # Destructive: remove map image
            msg = "! Remove Image: Use Mist API deleteSiteMapImage - DESTRUCTIVE operation"
            logging.warning("Utilities: Remove Image requested for map %s", map_id)  # Warning-level audit
            return html.Span(msg, style={"color": "#ff4444"})  # Red = destructive
        if button_id == "rename-btn":  # Rename map request
            msg = "! Rename: Use Mist API updateSiteMap with new name - requires text input"
            logging.info("Utilities: Rename requested for map %s", map_id)  # Audit trail
            return html.Span(msg, style={"color": "#ff8800"})  # Orange = warning

        return ""  # Fallback: empty status

    def update_shape_labels(self, relayoutData: dict[str, Any] | None, current_fig: dict[str, Any]) -> dict[str, Any]:
        """Add multi-unit measurement labels to drawn shapes."""
        if not relayoutData:  # No relayout event => nothing to annotate
            return current_fig  # Return unchanged figure

        # PPM may be user-updated via the calibration tool; fall back to state default
        current_ppm = current_fig.get("layout", {}).get("meta", {}).get("ppm", self._state.ppm)

        shapes = current_fig.get("layout", {}).get("shapes", [])  # User-drawn shapes list
        if shapes and len(shapes) > 0:  # Process only when at least one shape exists
            for _, shape in enumerate(shapes):  # Index unused but preserved from original
                if shape.get("type") == "line":  # Annotate only line (ruler) shapes
                    x0, y0 = shape.get("x0", 0), shape.get("y0", 0)  # Line start coordinates
                    x1, y1 = shape.get("x1", 0), shape.get("y1", 0)  # Line end coordinates
                    length_px = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5  # Euclidean length in pixels

                    length_m = length_px / current_ppm if current_ppm > 0 else 0  # Convert px -> meters
                    length_ft = length_m * 3.28084  # Convert meters -> feet

                    annotation = dict(  # Multi-unit annotation widget shown next to the line
                        x=(x0 + x1) / 2,  # Center X position
                        y=(y0 + y1) / 2,  # Center Y position
                        text=f"<b>{length_px:.1f} px</b><br>{length_ft:.2f} ft<br>{length_m:.2f} m",
                        showarrow=False,
                        font=dict(size=12, color="cyan", family="Arial Black"),
                        bgcolor="rgba(0,0,0,0.7)",
                        bordercolor="cyan",
                        borderwidth=2,
                        borderpad=4,
                    )

                    if "annotations" not in current_fig["layout"]:  # Ensure annotations array exists
                        current_fig["layout"]["annotations"] = []  # Initialize when missing
                    current_fig["layout"]["annotations"].append(annotation)  # Append the new label

        return current_fig  # Return mutated figure dict to Dash

    def set_origin_from_click(
        self,
        clickData: dict[str, Any] | None,
        mode_clicks: int | None,
        current_fig: dict[str, Any],
    ) -> tuple[Any, dict[str, Any]]:
        """Set origin point when map is clicked in origin-setting mode."""
        from dash import html  # html.P for status output

        if not mode_clicks or mode_clicks % 2 == 0:  # Mode is inactive (even clicks)
            current_origin_x = current_fig.get("layout", {}).get("meta", {}).get("origin_x", 0)  # Existing X
            current_origin_y = current_fig.get("layout", {}).get("meta", {}).get("origin_y", 0)  # Existing Y
            return [
                html.P(  # Show the current origin coordinates in gray
                    f"Current: ({current_origin_x}, {current_origin_y})",
                    style={"fontSize": "11px", "color": "#888", "margin": "4px 0"},
                )
            ], current_fig

        if not clickData:  # Mode is active but user hasn't clicked yet
            return [
                html.P("Click map to set origin", style={"fontSize": "11px", "color": "#ff8800", "margin": "4px 0"})
            ], current_fig

        point = clickData["points"][0]  # First clicked point carries the coordinates
        new_origin_x = point["x"]  # Click X position
        new_origin_y = point["y"]  # Click Y position

        if "meta" not in current_fig["layout"]:  # Ensure meta dict exists for persistence
            current_fig["layout"]["meta"] = {}  # Initialize when missing
        current_fig["layout"]["meta"]["origin_x"] = new_origin_x  # Persist X for later callbacks
        current_fig["layout"]["meta"]["origin_y"] = new_origin_y  # Persist Y for later callbacks

        self._update_origin_traces(current_fig, new_origin_x, new_origin_y)  # Refresh crosshair traces

        status = [  # Confirmation widgets shown to the user
            html.P(
                f"[OK] Origin set: ({new_origin_x:.1f}, {new_origin_y:.1f})",
                style={"fontSize": "11px", "color": "#00ff00", "margin": "4px 0"},
            ),
            html.P("Click button again to exit mode", style={"fontSize": "10px", "color": "#888", "margin": "4px 0"}),
        ]

        logging.info("Map origin updated to (%.1f, %.1f)", new_origin_x, new_origin_y)  # Preserve audit log
        return status, current_fig

    @staticmethod
    def _update_origin_traces(current_fig: dict[str, Any], new_origin_x: float, new_origin_y: float) -> None:
        """Update the Origin / Origin Point / vertical crosshair traces in place."""
        crosshair_size = 40  # Half-length of crosshair arms in pixels
        for trace in current_fig["data"]:  # Walk every trace looking for origin markers
            if trace.get("name") == "Origin":  # Horizontal crosshair line
                trace["x"] = [new_origin_x - crosshair_size, new_origin_x + crosshair_size]
                trace["y"] = [new_origin_y, new_origin_y]
                trace["hovertext"] = f"Origin: ({new_origin_x:.1f}, {new_origin_y:.1f})"
            elif trace.get("name") == "Origin Point":  # Center dot marker
                trace["x"] = [new_origin_x]
                trace["y"] = [new_origin_y]
                trace["hovertext"] = f"Origin: ({new_origin_x:.1f}, {new_origin_y:.1f})"
            elif "hovertext" in trace and "Origin:" in str(trace.get("hovertext", "")):  # Vertical line lacks name
                if trace.get("mode") == "lines" and not trace.get("showlegend"):  # Distinguish vertical crosshair
                    trace["x"] = [new_origin_x, new_origin_x]
                    trace["y"] = [new_origin_y - crosshair_size, new_origin_y + crosshair_size]
                    trace["hovertext"] = f"Origin: ({new_origin_x:.1f}, {new_origin_y:.1f})"

    def execute_delete_map(
        self,
        confirm_clicks: int,
        cache_bust_data: dict[str, Any] | None,
        config: dict[str, Any] | None,
    ) -> tuple[Any, Any]:
        """Actually delete the map via Mist API - creates backup first."""
        from dash import html, no_update  # Local import keeps module import-light

        current_trigger = cache_bust_data.get("trigger", 0) if cache_bust_data else 0  # Cache bust counter

        if not confirm_clicks:  # User hasn't actually confirmed the delete
            return "", no_update

        config_site_id = config.get("site_id") if config else self._state.site_id  # Prefer config store value
        config_map_id = config.get("map_id") if config else self._state.map_id  # Prefer config store value
        config_map_name = config.get("map_name", "Unknown") if config else "Unknown"  # Display name

        try:
            self._backup_before_delete(config_site_id, config_map_id, config_map_name)  # Safety net side-effect only
            logging.warning(  # Destructive-operation audit log
                "DESTRUCTIVE: Deleting map '%s' (ID: %s) from site %s", config_map_name, config_map_id, config_site_id
            )
            delete_response = self._state.mistapi_ref.api.v1.sites.maps.deleteSiteMap(  # Mist API mutation
                self._state.api_session_ref, site_id=config_site_id, map_id=config_map_id
            )
            return self._render_delete_result(delete_response, config_map_name, config_map_id, current_trigger)
        except Exception as delete_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.exception("Error deleting map: %s", delete_error)  # Capture stack trace
            return html.Span(f"Error: {str(delete_error)[:50]}", style={"color": "#ff4444"}), no_update

    def _backup_before_delete(self, site_id: str | None, map_id: str | None, map_name: str) -> Any:
        """Run pre-delete backup and log the outcome; return backup path or None."""
        logging.info("Creating safety backup before deleting map '%s'", map_name)  # Audit trail
        backup_path = self._state.maps_manager_ref._backup_map_geometry(  # Call MapsManager helper
            api_session=self._state.api_session_ref,
            site_id=site_id,
            map_id=map_id,
            map_name=map_name,
            backup_reason="pre_delete",
        )
        if backup_path:  # Backup succeeded
            logging.info("Pre-delete backup saved: %s", backup_path)  # Path for operator recovery
        else:
            logging.warning("Pre-delete backup failed - proceeding with deletion anyway")  # Non-fatal warning
        return backup_path  # Return for caller (currently informational only)

    @staticmethod
    def _render_delete_result(
        delete_response: Any,
        map_name: str,
        map_id: str | None,
        current_trigger: int,
    ) -> tuple[Any, Any]:
        """Render the Dash output based on the Mist API delete response."""
        from dash import html, no_update  # Local import keeps module import-light

        if delete_response.status_code in [200, 204]:  # Success status codes from Mist API
            logging.info("Map '%s' (ID: %s) deleted successfully", map_name, map_id)  # Audit success
            new_cache_bust = {"trigger": current_trigger + 1}  # Increment to invalidate caches
            return (
                html.Span(
                    f"Map '{map_name}' deleted! Close this browser tab.",
                    style={"color": "#00ff88", "fontWeight": "bold"},
                ),
                new_cache_bust,
            )
        logging.error("Map deletion failed: HTTP %s", delete_response.status_code)  # Audit failure
        return (
            html.Span(f"Delete failed: HTTP {delete_response.status_code}", style={"color": "#ff4444"}),
            no_update,
        )

    def handle_zone_actions(
        self,
        _edit_clicks: int,
        _remove_clicks: int,
        clickData: dict[str, Any] | None,
        selected_zone_data: dict[str, Any] | None,
    ) -> tuple[Any, dict[str, Any]]:
        """Handle zone edit/remove and display selected zone info."""
        import dash  # Local import: dash.callback_context only exists at request time
        from dash import html  # html widgets for status output

        ctx = dash.callback_context  # Dash provides trigger info via callback_context
        if not ctx.triggered:  # No trigger => render default prompt
            return html.P(
                "Click a zone for details", style={"fontSize": "11px", "color": "#888", "fontStyle": "italic"}
            ), selected_zone_data or {"zone_id": None, "zone_name": None}

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]  # Component id that fired
        current_zone = selected_zone_data or {"zone_id": None, "zone_name": None}  # Defensive default

        if trigger_id == "edit-zone-btn":  # User clicked the Edit button
            return self._handle_zone_edit(current_zone)
        if trigger_id == "remove-zone-btn":  # User clicked the Remove button
            return self._handle_zone_remove(current_zone)
        if trigger_id == "map-display" and clickData:  # User clicked a zone on the map
            return self._handle_zone_click(clickData, current_zone)

        return (  # Fallback: render default prompt with current selection preserved
            html.P("Click a zone for details", style={"fontSize": "11px", "color": "#888", "fontStyle": "italic"}),
            current_zone,
        )

    def _handle_zone_edit(self, current_zone: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        """Render the edit-zone response panel."""
        from dash import html  # html widgets for status output

        if current_zone.get("zone_id"):  # A zone is already selected
            logging.info(
                "Zone management: Edit zone %s requested for map %s", current_zone.get("zone_name"), self._state.map_id
            )
            return (
                html.Div(
                    [
                        html.P(
                            f"Pencil Edit Zone: {current_zone.get('zone_name', 'Unknown')}",
                            style={"fontSize": "11px", "color": "#667eea", "fontWeight": "bold"},
                        ),
                        html.P(
                            "Use Mist Dashboard to modify zone shape",
                            style={"fontSize": "10px", "color": "#888"},
                        ),
                    ]
                ),
                current_zone,
            )
        return self._render_zone_not_selected(current_zone)  # Prompt the user to select one first

    def _handle_zone_remove(self, current_zone: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        """Delete the selected zone via Mist API and render the result."""
        from dash import html  # html widgets for status output

        if not current_zone.get("zone_id"):  # No zone selected
            return self._render_zone_not_selected(current_zone)  # Prompt user to select one

        zone_id = current_zone.get("zone_id")  # Zone UUID for the API delete
        zone_name = current_zone.get("zone_name", "Unknown")  # Display name for logs
        logging.warning(
            "Zone management: Deleting zone %s (ID: %s) from site %s", zone_name, zone_id, self._state.site_id
        )

        try:
            delete_response = self._state.mistapi_ref.api.v1.sites.zones.deleteSiteZone(  # Mist API mutation
                self._state.api_session_ref, site_id=self._state.site_id, zone_id=zone_id
            )
            return self._render_zone_delete_result(delete_response, zone_name, current_zone)
        except Exception as del_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.exception("Error deleting zone: %s", del_error)  # Capture stack trace
            return (
                html.Div(
                    [
                        html.P(
                            f"X Error: {str(del_error)[:40]}",
                            style={"fontSize": "11px", "color": "#ff4444", "fontWeight": "bold"},
                        )
                    ]
                ),
                current_zone,
            )

    @staticmethod
    def _render_zone_delete_result(
        delete_response: Any, zone_name: str, current_zone: dict[str, Any]
    ) -> tuple[Any, dict[str, Any]]:
        """Render the Dash output based on the Mist API zone delete response."""
        from dash import html  # html widgets for status output

        if delete_response.status_code in [200, 204]:  # Success status codes from Mist API
            logging.info("Zone %s deleted successfully", zone_name)  # Audit success
            return html.Div(
                [
                    html.P(
                        f"[OK] Zone deleted: {zone_name}",
                        style={"fontSize": "11px", "color": "#00ff88", "fontWeight": "bold"},
                    ),
                    html.P("Refresh the page to update view", style={"fontSize": "10px", "color": "#888"}),
                ]
            ), {
                "zone_id": None,
                "zone_name": None,
            }  # Clear selection after delete
        logging.error("Zone deletion failed: HTTP %s", delete_response.status_code)  # Audit failure
        return (
            html.Div(
                [
                    html.P(
                        f"X Delete failed: HTTP {delete_response.status_code}",
                        style={"fontSize": "11px", "color": "#ff4444", "fontWeight": "bold"},
                    ),
                    html.P(
                        "Check permissions and try again",
                        style={"fontSize": "10px", "color": "#888"},
                    ),
                ]
            ),
            current_zone,  # Keep selection on failure so user can retry
        )

    @staticmethod
    def _render_zone_not_selected(current_zone: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        """Render the 'select a zone first' prompt."""
        from dash import html  # html widgets for status output

        return (
            html.Div(
                [
                    html.P(
                        "! Select a zone first",
                        style={"fontSize": "11px", "color": "#ffaa00", "fontWeight": "bold"},
                    ),
                    html.P(
                        "Click on a zone in the map to select it",
                        style={"fontSize": "10px", "color": "#888"},
                    ),
                ]
            ),
            current_zone,
        )

    def _handle_zone_click(self, clickData: dict[str, Any], current_zone: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        """Render the response when the user clicks a zone on the map."""
        from dash import html  # html widgets for status output

        point = clickData["points"][0]  # First clicked point carries the hovertext
        hover_text = point.get("hovertext", "")  # Hovertext encodes the zone name

        if "Zone:" not in hover_text:  # Clicked something other than a zone overlay
            return (
                html.P("Click a zone for details", style={"fontSize": "11px", "color": "#888", "fontStyle": "italic"}),
                current_zone,
            )

        zone_name = hover_text.split("Zone: ")[1] if "Zone: " in hover_text else "Unknown"  # Extract name
        zone_id = None  # Default when no matching zone record
        for zone in self._state.zones:  # Look up the UUID by name match
            if zone.get("name") == zone_name:
                zone_id = zone.get("id")
                break  # Stop scanning zones once matched

        return html.Div(
            [
                html.P(
                    f">> Selected: {zone_name}",
                    style={
                        "fontSize": "12px",
                        "color": "#00ff00",
                        "fontWeight": "bold",
                        "marginBottom": "5px",
                    },
                ),
                html.P(
                    f"ID: {zone_id[:8] if zone_id else 'Unknown'}...",
                    style={"fontSize": "10px", "color": "#888"},
                ),
            ]
        ), {"zone_id": zone_id, "zone_name": zone_name}

    # ------------------------------------------------------------------
    # Wiring: bind every UI callback in this cluster to ``app.callback``
    # ------------------------------------------------------------------

    def register(self, app: Dash) -> None:  # WHY: hooks this wave's app.callback(...) blocks into Dash
        """Attach the UI-toggle callbacks in this cluster to ``app``."""
        from dash import Input, Output, State  # WHY: local import keeps module import-light

        app.callback(  # WHY: display_click_data - Plotly clickData -> details panel children
            Output("click-data", "children"),
            Input("map-display", "clickData"),
        )(self.display_click_data)

        app.callback(  # WHY: toggle_origin_mode - parity-based origin-mode toggle
            Output("origin-mode-button", "style"),
            Input("origin-mode-button", "n_clicks"),
            State("origin-mode-button", "style"),
            prevent_initial_call=True,
        )(self.toggle_origin_mode)

        app.callback(  # WHY: toggle_zone_name_input - show zone-name field only in zone mode
            Output("zone-name-container", "style"),
            Input("drawing-mode-dropdown", "value"),
            prevent_initial_call=True,
        )(self.toggle_zone_name_input)

        app.callback(  # WHY: toggle_auto_refresh - drives 3 dcc.Interval flags + countdown label
            [
                Output("client-refresh-interval", "disabled"),
                Output("coverage-refresh-interval", "disabled"),
                Output("countdown-tick-interval", "disabled"),
                Output("refresh-times-store", "data"),
                Output("countdown-display", "children"),
            ],
            [Input("auto-refresh-toggle", "value")],
            prevent_initial_call=True,
        )(self.toggle_auto_refresh)

        app.callback(  # WHY: toggle_individual_zones - flips visibility on Zone: traces
            Output("map-display", "figure", allow_duplicate=True),
            Input("zone-toggle", "value"),
            State("map-display", "figure"),
            prevent_initial_call=True,
        )(self.toggle_individual_zones)

        app.callback(  # WHY: toggle_delete_panel - dispatches on callback_context trigger id
            [Output("delete-panel", "style"), Output("delete-map-name-display", "children")],
            [
                Input("delete-btn", "n_clicks"),
                Input("cancel-delete-btn", "n_clicks"),
                Input("confirm-delete-btn", "n_clicks"),
            ],
            [State("delete-panel", "style"), State("map-config-store", "data")],
            prevent_initial_call=True,
        )(self.toggle_delete_panel)

        app.callback(  # WHY: toggle_clone_panel - dispatches on callback_context trigger id
            Output("clone-panel", "style"),
            [
                Input("clone-btn", "n_clicks"),
                Input("cancel-clone-btn", "n_clicks"),
                Input("execute-clone-btn", "n_clicks"),
            ],
            [State("clone-panel", "style")],
            prevent_initial_call=True,
        )(self.toggle_clone_panel)

        app.callback(  # WHY: handle_utilities - routes 4 utilities buttons to status widgets
            Output("utilities-status", "children"),
            [
                Input("auto-zone-btn", "n_clicks"),
                Input("change-image-btn", "n_clicks"),
                Input("remove-image-btn", "n_clicks"),
                Input("rename-btn", "n_clicks"),
            ],
            prevent_initial_call=True,
        )(self.handle_utilities)

        app.callback(  # WHY: update_shape_labels - multi-unit annotation on drawn lines
            Output("map-display", "figure", allow_duplicate=True),
            Input("map-display", "relayoutData"),
            State("map-display", "figure"),
            prevent_initial_call=True,
        )(self.update_shape_labels)

        app.callback(  # WHY: set_origin_from_click - map click sets origin in origin mode
            [Output("origin-status", "children"), Output("map-display", "figure", allow_duplicate=True)],
            Input("map-display", "clickData"),
            [State("origin-mode-button", "n_clicks"), State("map-display", "figure")],
            prevent_initial_call=True,
        )(self.set_origin_from_click)

        app.callback(  # WHY: execute_delete_map - backup + Mist API deleteSiteMap
            [Output("delete-status", "children"), Output("cache-bust-store", "data", allow_duplicate=True)],
            Input("confirm-delete-btn", "n_clicks"),
            [State("cache-bust-store", "data"), State("map-config-store", "data")],
            prevent_initial_call=True,
        )(self.execute_delete_map)

        app.callback(  # WHY: handle_zone_actions - edit/remove/click zone selection
            [Output("selected-zone-info", "children"), Output("selected-zone-store", "data")],
            [
                Input("edit-zone-btn", "n_clicks"),
                Input("remove-zone-btn", "n_clicks"),
                Input("map-display", "clickData"),
            ],
            [State("selected-zone-store", "data")],
            prevent_initial_call=True,
        )(self.handle_zone_actions)
