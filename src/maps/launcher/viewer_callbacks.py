"""Dash callback handlers extracted from ``_launch_plotly_viewer``.

Each method on :class:`MapViewerCallbacks` corresponds to one Dash
callback that was previously nested as a closure inside
:py:meth:`src.maps.maps_manager.MapsManager._launch_plotly_viewer`.
The :meth:`MapViewerCallbacks.register_with` method wires every
callback to its ``@app.callback`` decorator with byte-identical
``Input`` / ``Output`` / ``State`` signatures, ``prevent_initial_call``
flags, and user-facing strings.

Wave A scope: five trivial UI toggles (``apply_layer_toggles``,
``display_click_data``, ``toggle_origin_mode``,
``toggle_zone_name_input``, ``toggle_auto_refresh``).

Waves B + C scope: eight more callbacks bringing zone management,
delete/clone panels, origin-set-on-click, drawn-shape label updates,
and the utilities button row. Each method stays at CC <= 10 either
naturally or by delegating to private ``_handle_*`` helpers.

To add a callback in a later wave:

1. Implement the method on this class (keep CC <= 10; extract
   ``_handle_*`` helpers when complexity demands it).
2. Add any new closure dependencies as fields on
   :class:`src.maps.launcher.viewer_state.MapViewerState`.
3. Add a corresponding ``app.callback(...)(self.<method>)`` block to
   :meth:`register_with`, mirroring the original decorator arguments
   exactly (Inputs, Outputs, States, ``prevent_initial_call``,
   ``allow_duplicate``).
"""

from __future__ import annotations

import logging  # Standard library logger used by original toggle_auto_refresh
import time  # Used to seed refresh timestamps in toggle_auto_refresh
from datetime import datetime  # Used by wave-D refresh callbacks for human-readable audit timestamps
from typing import TYPE_CHECKING, Any  # Guard heavy dash import and type permissive callback args

if TYPE_CHECKING:  # pragma: no cover - typing-only imports
    from dash import Dash  # noqa: F401 - typing reference for register_with

    from src.maps.launcher.viewer_state import MapViewerState  # noqa: F401


class MapViewerCallbacks:
    """Callback handlers for the Plotly/Dash map viewer (waves A + B + C)."""

    def __init__(self, state: MapViewerState) -> None:
        """Store the shared MapViewerState for use by every callback method."""
        # Store the shared state container so each callback method can
        # access closure-equivalent values (e.g. callback_manager) via
        # self._state without needing per-callback parameters.
        self._state = state  # MapViewerState instance carrying viewer context

    # ------------------------------------------------------------------
    # Wave A callback bodies
    # ------------------------------------------------------------------

    def display_click_data(self, click_data: Any) -> Any:
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

    def toggle_origin_mode(self, n_clicks: int, current_style: dict[str, Any]) -> dict[str, Any]:
        """Toggle origin setting mode on/off with visual feedback."""
        if n_clicks % 2 == 1:  # Odd click count means mode is ACTIVE
            current_style["backgroundColor"] = "#667eea"  # Purple fill highlights armed state
            current_style["border"] = "2px solid #00bfff"  # Cyan border reinforces armed state
            return current_style  # Return mutated style dict to Dash
        # Even clicks (including initial 0) mean the mode is INACTIVE
        current_style["backgroundColor"] = "#3d3d3d"  # Neutral dark gray = inactive button
        current_style["border"] = "1px solid #667eea"  # Thin purple border at rest
        return current_style  # Return mutated style dict to Dash

    def toggle_zone_name_input(self, mode: str | None) -> dict[str, str]:
        """Show zone name input only when zone mode is selected."""
        if mode == "zone":  # Only zone drawing mode needs the zone-name field
            return {"display": "block", "marginBottom": "10px"}  # Reveal the input row
        return {"display": "none"}  # Hide the input for wall/path/measure modes

    def toggle_auto_refresh(self, toggle_value: list[str] | None) -> tuple[bool, bool, bool, dict[str, float], str]:
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

    # ------------------------------------------------------------------
    # Wave B callback bodies
    # ------------------------------------------------------------------

    def toggle_individual_zones(
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

    def toggle_delete_panel(
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
        if not ctx.triggered:  # No trigger => keep current style and skip name update
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

    def toggle_clone_panel(
        self,
        _clone_clicks: int,
        _cancel_clicks: int,
        _execute_clicks: int,
        current_style: dict[str, Any],
    ) -> dict[str, Any]:
        """Show or hide the clone input panel."""
        import dash  # Local import: dash.callback_context only exists at request time

        ctx = dash.callback_context  # Dash provides trigger info via callback_context
        if not ctx.triggered:  # No trigger => return existing style unchanged
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

    # ------------------------------------------------------------------
    # Wave C callback bodies (API-touching but bounded)
    # ------------------------------------------------------------------

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
            backup_path = self._backup_before_delete(config_site_id, config_map_id, config_map_name)  # Safety net
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
    # Wave D callback bodies (live-refresh: countdown + clients + coverage)
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
        min_rssi, max_rssi = MapViewerCallbacks._compute_rssi_bounds(grid_data)  # Color scale bounds
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
    # Wave E1: execute_clone_operation + handle_drawing_tools
    # ------------------------------------------------------------------

    def execute_clone_operation(
        self,
        n_clicks: int,
        new_name: str | None,
        config: dict[str, Any] | None,
        cache_bust_data: dict[str, Any] | None,
    ) -> tuple[Any, Any]:
        """Clone the current map with all properties, image, and zones."""
        from dash import html, no_update  # Local import keeps module import-light

        current_trigger = cache_bust_data.get("trigger", 0) if cache_bust_data else 0  # Cache-bust counter

        validation = self._validate_clone_inputs(n_clicks, new_name, config)  # Reject early on bad input
        if len(validation) != 3:  # Validation returned an error tuple of length 2
            return validation
        new_name_clean, site_id_local, source_map_id = validation  # Unpack validated values

        logging.info(  # Audit start of clone op
            "Clone operation started - source: %s, new name: %s", source_map_id, new_name_clean
        )
        try:
            self._backup_before_clone(site_id_local, source_map_id, config or {})  # Safety net
            source_map = self._fetch_source_map(site_id_local, source_map_id)  # Step 1: fetch source
            if source_map is None:  # Source fetch failed
                return (
                    html.Span("! Failed to fetch source map", style={"color": "#ff4444"}),  # User-visible error
                    no_update,
                )
            return self._perform_clone(site_id_local, source_map_id, new_name_clean, source_map, current_trigger)
        except Exception as clone_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.exception("Clone operation failed: %s", clone_error)  # Capture stack trace
            return (
                html.Span(
                    "! Clone operation failed. Check server logs for details.",
                    style={"color": "#ff4444"},
                ),
                no_update,
            )

    @staticmethod
    def _validate_clone_inputs(
        n_clicks: int,
        new_name: str | None,
        config: dict[str, Any] | None,
    ) -> tuple[Any, Any] | tuple[str, str, str]:
        """Return error tuple on bad input, or (clean_name, site_id, map_id) on success."""
        from dash import html, no_update  # Local import keeps module import-light

        if not n_clicks:  # Button never clicked => silent no-op
            return ("", no_update)
        if not new_name or not new_name.strip():  # Required: non-empty cloned-map name
            return (
                html.Span("! Please enter a name for the cloned map", style={"color": "#ff4444"}),
                no_update,
            )
        new_name_clean = new_name.strip()  # Strip whitespace from user input
        site_id_local = config.get("site_id") if config else None  # Pull site_id from config store
        source_map_id = config.get("map_id") if config else None  # Pull source map_id from config store
        if not site_id_local or not source_map_id:  # Both required for the API calls
            return (
                html.Span("! Missing site or map configuration", style={"color": "#ff4444"}),
                no_update,
            )
        return (new_name_clean, site_id_local, source_map_id)  # All inputs validated

    def _backup_before_clone(self, site_id: str, source_map_id: str, config: dict[str, Any]) -> None:
        """Create a pre-clone geometry backup of the source map (best-effort)."""
        source_map_name = config.get("map_name", "Unknown")  # Display name for the backup file
        logging.info("Creating backup of source map '%s' before cloning", source_map_name)  # Audit trail
        backup_path = self._state.maps_manager_ref._backup_map_geometry(  # Call MapsManager helper
            api_session=self._state.api_session_ref,
            site_id=site_id,
            map_id=source_map_id,
            map_name=source_map_name,
            backup_reason="pre_clone",
        )
        if backup_path:  # Backup succeeded
            logging.info("Pre-clone backup saved: %s", backup_path)  # Path for operator recovery

    def _fetch_source_map(self, site_id: str, source_map_id: str) -> dict[str, Any] | None:
        """Fetch the source map record from Mist; return None on failure."""
        logging.info("Fetching source map %s for clone", source_map_id)  # Audit start
        source_response = self._state.mistapi_ref.api.v1.sites.maps.getSiteMap(  # Mist API read
            self._state.api_session_ref, site_id=site_id, map_id=source_map_id
        )
        logging.debug("Source map fetch status_code=%s", getattr(source_response, "status_code", "?"))
        if source_response.status_code != 200:  # Non-200 means we cannot proceed
            logging.error("Clone failed: Could not fetch source map - HTTP %s", source_response.status_code)
            return None
        data: dict[str, Any] = source_response.data  # Parsed JSON payload of the source map
        return data

    def _perform_clone(
        self,
        site_id: str,
        source_map_id: str,
        new_name: str,
        source_map: dict[str, Any],
        current_trigger: int,
    ) -> tuple[Any, Any]:
        """Run steps 2-6 of the clone workflow (payload, image, create, upload, zones)."""
        from dash import html, no_update  # Local import keeps module import-light

        clone_payload = self._build_clone_payload(source_map, new_name)  # Step 2: build payload
        image_temp_path = self._download_source_image(source_map)  # Step 3: download image (best-effort)
        cloned_map_id = self._create_cloned_map(site_id, clone_payload, image_temp_path)  # Step 4: create
        if cloned_map_id is None:  # Map creation failed
            return (
                html.Span("! Failed to create cloned map", style={"color": "#ff4444"}),
                no_update,
            )
        image_uploaded = self._upload_clone_image(site_id, cloned_map_id, image_temp_path)  # Step 5: upload
        zones_cloned = self._clone_zones_for_map(site_id, source_map_id, cloned_map_id)  # Step 6: zones
        return self._render_clone_success(new_name, cloned_map_id, image_uploaded, zones_cloned, current_trigger)

    @staticmethod
    def _build_clone_payload(source_map: dict[str, Any], new_name: str) -> dict[str, Any]:
        """Assemble the full clone payload preserving dimensional + location + path props."""
        clone_payload: dict[str, Any] = {"name": new_name, "type": source_map.get("type", "image")}  # Base payload
        # Property groups copied byte-identically from the source map (order preserved from original)
        for prop in ["width", "height", "height_m", "ppm", "orientation"]:  # Dimensional properties
            if prop in source_map:
                clone_payload[prop] = source_map[prop]
        for prop in ["latlng", "latlng_br", "origin_x", "origin_y"]:  # Geo / origin properties
            if prop in source_map:
                clone_payload[prop] = source_map[prop]
        for prop in ["wayfinding", "wayfinding_path", "wall_path", "sitesurvey_path"]:  # Path properties
            if prop in source_map:
                clone_payload[prop] = source_map[prop]
        for prop in ["occupancy_limit", "locked", "view"]:  # Misc settings
            if prop in source_map:
                clone_payload[prop] = source_map[prop]
        logging.debug("Clone payload prepared with %d properties", len(clone_payload))  # Diagnostic
        return clone_payload  # Caller passes to createSiteMap

    @staticmethod
    def _download_source_image(source_map: dict[str, Any]) -> str | None:
        """Download the source map image to a temp file; return path or None on any failure."""
        if "url" not in source_map:  # No image to download
            return None
        import os  # Local import keeps module import-light
        import tempfile  # Local import keeps module import-light

        import requests  # Local import: external HTTP dep only needed at call time

        image_temp_path: str | None = None  # Final temp file path (set below)
        try:
            image_url = source_map["url"]  # URL of the source map image
            file_ext = ".png"  # Default extension if URL lacks one
            if "." in image_url:  # Try to infer the real extension
                url_ext = image_url.rsplit(".", 1)[-1].split("?")[0]
                if url_ext.lower() in ["png", "jpg", "jpeg", "gif", "svg"]:
                    file_ext = f".{url_ext.lower()}"
            temp_fd, image_temp_path = tempfile.mkstemp(suffix=file_ext)  # Create temp file
            os.close(temp_fd)  # Close fd; we'll reopen via path
            logging.info("Downloading source map image from %s", image_url)  # Audit start
            response = requests.get(image_url, timeout=60)  # 60s timeout matches original
            if response.status_code == 200:  # Success: write bytes to temp file
                with open(image_temp_path, "wb") as fh:
                    fh.write(response.content)
                logging.info("Downloaded source map image (%.1f KB)", len(response.content) / 1024)
                return image_temp_path
            logging.warning("Failed to download image: HTTP %s", response.status_code)  # Non-200
            if image_temp_path and os.path.exists(image_temp_path):
                os.remove(image_temp_path)
            return None
        except Exception as img_err:  # noqa: BLE001 - preserve broad-except behavior
            logging.error("Error downloading image: %s", img_err)  # Audit failure
            if image_temp_path and os.path.exists(image_temp_path):
                os.remove(image_temp_path)
            return None

    def _create_cloned_map(
        self, site_id: str, clone_payload: dict[str, Any], image_temp_path: str | None
    ) -> str | None:
        """Call createSiteMap; clean up temp image on failure; return new map_id or None."""
        import os  # Local import keeps module import-light

        logging.info("Creating cloned map '%s' at site %s", clone_payload.get("name"), site_id)  # Audit
        clone_response = self._state.mistapi_ref.api.v1.sites.maps.createSiteMap(  # Mist API write
            self._state.api_session_ref, site_id=site_id, body=clone_payload
        )
        logging.debug("createSiteMap status_code=%s", getattr(clone_response, "status_code", "?"))
        if clone_response.status_code not in [200, 201]:  # Created or OK accepted
            logging.error("Clone failed: Could not create map - HTTP %s", clone_response.status_code)
            if image_temp_path and os.path.exists(image_temp_path):  # Cleanup orphaned temp file
                os.remove(image_temp_path)
            return None
        cloned_map = clone_response.data  # Parsed payload of the new map
        cloned_map_id: str | None = cloned_map.get("id")  # New map's UUID
        logging.info("Cloned map created: %s", cloned_map_id)  # Audit success
        return cloned_map_id

    def _upload_clone_image(self, site_id: str, cloned_map_id: str, image_temp_path: str | None) -> bool:
        """Upload the temp image to the cloned map; always remove temp file on exit."""
        if not image_temp_path:  # No image was downloaded
            return False
        import os  # Local import keeps module import-light

        if not os.path.exists(image_temp_path):  # Defensive: temp file missing
            return False
        image_uploaded = False  # Track outcome for status message
        try:
            logging.info("Uploading image to cloned map %s", cloned_map_id)  # Audit start
            upload_response = self._state.mistapi_ref.api.v1.sites.maps.addSiteMapImageFile(
                self._state.api_session_ref,
                site_id=site_id,
                map_id=cloned_map_id,
                file=image_temp_path,
            )
            logging.debug("addSiteMapImageFile status_code=%s", getattr(upload_response, "status_code", "?"))
            if upload_response.status_code in [200, 201]:  # Success codes
                image_uploaded = True
                logging.info("Image uploaded to cloned map %s", cloned_map_id)  # Audit success
            else:
                logging.warning("Image upload failed: HTTP %s", upload_response.status_code)
        except Exception as upload_err:  # noqa: BLE001 - preserve broad-except behavior
            logging.error("Error uploading image: %s", upload_err)  # Audit failure
        finally:
            if os.path.exists(image_temp_path):  # Always clean up temp file
                os.remove(image_temp_path)
        return image_uploaded

    def _clone_zones_for_map(self, site_id: str, source_map_id: str, cloned_map_id: str) -> int:
        """Replicate each zone associated with source_map_id under cloned_map_id; return count cloned."""
        zones_cloned = 0  # Successful zone-create count
        try:
            logging.info("Listing zones at site %s to clone for map %s", site_id, source_map_id)  # Audit
            zones_response = self._state.mistapi_ref.api.v1.sites.zones.listSiteZones(
                self._state.api_session_ref, site_id=site_id
            )
            if zones_response.status_code != 200:  # Cannot list zones => skip cloning silently
                logging.warning("Zone listing failed: HTTP %s", zones_response.status_code)
                return 0
            source_zones = [z for z in zones_response.data if z.get("map_id") == source_map_id]  # Filter
            logging.debug("Found %d source zones to clone", len(source_zones))  # Diagnostic
            for zone in source_zones:  # Replicate each one
                if self._clone_single_zone(site_id, cloned_map_id, zone):
                    zones_cloned += 1
        except Exception as zone_err:  # noqa: BLE001 - preserve original broad-except behavior
            logging.error("Zone cloning error: %s", zone_err)  # Audit failure
        return zones_cloned

    def _clone_single_zone(self, site_id: str, cloned_map_id: str, zone: dict[str, Any]) -> bool:
        """Create one zone under cloned_map_id; return True on success."""
        try:
            zone_payload: dict[str, Any] = {  # Replicate the zone's identifying fields
                "name": zone.get("name", "Unnamed Zone"),
                "map_id": cloned_map_id,
                "vertices": zone.get("vertices", []),
            }
            if "type" in zone:  # Preserve optional fields when present
                zone_payload["type"] = zone["type"]
            if "z" in zone:
                zone_payload["z"] = zone["z"]
            zone_response = self._state.mistapi_ref.api.v1.sites.zones.createSiteZone(
                self._state.api_session_ref, site_id=site_id, body=zone_payload
            )
            return zone_response.status_code in [200, 201]  # Created or OK
        except Exception:  # noqa: BLE001 - preserve original broad-except behavior
            return False

    @staticmethod
    def _render_clone_success(
        new_name: str,
        cloned_map_id: str,
        image_uploaded: bool,
        zones_cloned: int,
        current_trigger: int,
    ) -> tuple[Any, Any]:
        """Build the success Span and incremented cache-bust dict for the clone callback."""
        from dash import html  # Local import keeps module import-light

        result_parts = [f"Map '{new_name}' created successfully!"]  # Always include base message
        if image_uploaded:  # Append optional facets
            result_parts.append("Image: uploaded")
        if zones_cloned > 0:
            result_parts.append(f"Zones: {zones_cloned} cloned")
        logging.info(  # Audit final summary
            "Clone complete: %s (ID: %s), image=%s, zones=%s",
            new_name,
            cloned_map_id,
            image_uploaded,
            zones_cloned,
        )
        new_cache_bust = {"trigger": current_trigger + 1}  # Bump trigger to refresh dropdown
        return (
            html.Span(" | ".join(result_parts), style={"color": "#00ff88", "fontWeight": "bold"}),
            new_cache_bust,
        )

    # ------------------------------------------------------------------
    # handle_drawing_tools + per-button helpers
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
    # Wave E2: set_scale
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
        return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5  # Euclidean distance in pixels

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

    # ------------------------------------------------------------------
    # Wave E2: refresh_map_dropdown
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Wave E2: handle_site_from_url
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Wave E2: sync_dropdown_with_url
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Wave E2: handle_site_switch_from_dropdown
    # ------------------------------------------------------------------

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
    ) -> tuple[list, None, list, dict[str, Any], Any]:
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
    ) -> tuple[Any, str, Any, dict[str, Any], Any]:
        """Build dropdown options, store, updated config, and figure for the first map."""
        new_map_options = self._state.serializer.build_dropdown_options(new_maps, default_name="Unnamed")  # Options
        new_maps_store = self._state.serializer.build_named_items(new_maps, default_name="Unnamed")  # Store data
        first_map = new_maps[0]  # Pick first map (matches original)
        selected_map_id = first_map.get("id")  # Map UUID
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
    # Wave E2: handle_url_map_switch
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
        url_map_id = self._extract_url_param(url_search, "map_id")  # Pull map_id from URL
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
        new_map_data = map_response.data  # Parsed map dict
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
        self._add_background_image(new_fig, map_data, map_width, map_height, anchor_top=False)  # Background
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
        coverage_data = coverage_response.data
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
    # Wiring: bind every method above to its @app.callback
    # ------------------------------------------------------------------

    def register_with(self, app: Dash) -> None:
        """Attach all wave-A + wave-B + wave-C + wave-D + wave-E1 + wave-E2 callbacks to ``app``."""
        # Import dash decorator helpers lazily so this module stays
        # importable when dash is missing (matches the fallback behavior
        # in MapsManager._launch_plotly_viewer).
        from dash import Input, Output, State  # Local import keeps module import-light

        logging.info(  # Trace registration start so operators can confirm wiring
            "MapViewerCallbacks: registering %d callbacks (waves A+B+C+D+E1+E2)", 24
        )

        # --- Wave A ---------------------------------------------------
        app.callback(  # PlotlyMapCallbackManager.apply_layer_toggles (registered directly, no adapter)
            Output("map-display", "figure"),  # Output: replaces the figure
            [
                Input("layer-toggle", "value"),  # Walls/wayfinding checklist
                Input("beacon-toggle", "value"),  # Beacon overlay checklist
                Input("client-toggle", "value"),  # Connected-clients checklist
                Input("device-toggle", "value"),  # AP/switch/gateway checklist
                Input("filter-toggle", "value"),  # Status-filter checklist
            ],
            State("map-display", "figure"),  # Current figure passed in last for mutation
        )(self._state.callback_manager.apply_layer_toggles)

        app.callback(  # display_click_data
            Output("click-data", "children"),  # Output: details-panel children
            Input("map-display", "clickData"),  # Input: Plotly clickData dict
        )(self.display_click_data)

        app.callback(  # toggle_origin_mode
            Output("origin-mode-button", "style"),  # Output: button style dict
            Input("origin-mode-button", "n_clicks"),  # Input: button click counter
            State("origin-mode-button", "style"),  # State: current style dict
            prevent_initial_call=True,  # Don't toggle on page load (n_clicks=None)
        )(self.toggle_origin_mode)

        app.callback(  # toggle_zone_name_input
            Output("zone-name-container", "style"),  # Output: container style dict
            Input("drawing-mode-dropdown", "value"),  # Input: selected mode value
            prevent_initial_call=True,  # Don't re-render on page load
        )(self.toggle_zone_name_input)

        app.callback(  # toggle_auto_refresh
            [
                Output("client-refresh-interval", "disabled"),  # Client interval gate
                Output("coverage-refresh-interval", "disabled"),  # Coverage interval gate
                Output("countdown-tick-interval", "disabled"),  # Countdown tick gate
                Output("refresh-times-store", "data"),  # Refresh timestamp store
                Output("countdown-display", "children"),  # Countdown label widget
            ],
            [Input("auto-refresh-toggle", "value")],  # Input: checklist value list
            prevent_initial_call=True,  # Don't reset timers on page load
        )(self.toggle_auto_refresh)

        # --- Wave B ---------------------------------------------------
        app.callback(  # toggle_individual_zones
            Output("map-display", "figure", allow_duplicate=True),  # Mutates figure (duplicate output)
            Input("zone-toggle", "value"),  # Per-zone checklist
            State("map-display", "figure"),  # Current figure for in-place mutation
            prevent_initial_call=True,  # Avoid initial render thrash
        )(self.toggle_individual_zones)

        app.callback(  # toggle_delete_panel
            [Output("delete-panel", "style"), Output("delete-map-name-display", "children")],
            [
                Input("delete-btn", "n_clicks"),  # Open panel
                Input("cancel-delete-btn", "n_clicks"),  # Hide panel (cancel)
                Input("confirm-delete-btn", "n_clicks"),  # Hide panel (after confirm)
            ],
            [State("delete-panel", "style"), State("map-config-store", "data")],  # Style + config store
            prevent_initial_call=True,  # Avoid initial render thrash
        )(self.toggle_delete_panel)

        app.callback(  # toggle_clone_panel
            Output("clone-panel", "style"),  # Style dict for the clone panel
            [
                Input("clone-btn", "n_clicks"),  # Open panel
                Input("cancel-clone-btn", "n_clicks"),  # Hide panel (cancel)
                Input("execute-clone-btn", "n_clicks"),  # Hide panel (after execute)
            ],
            [State("clone-panel", "style")],  # Current style dict
            prevent_initial_call=True,  # Avoid initial render thrash
        )(self.toggle_clone_panel)

        app.callback(  # handle_utilities
            Output("utilities-status", "children"),  # Status text/widget output
            [
                Input("auto-zone-btn", "n_clicks"),  # AI auto-zone button
                Input("change-image-btn", "n_clicks"),  # Change image button
                Input("remove-image-btn", "n_clicks"),  # Remove image button
                Input("rename-btn", "n_clicks"),  # Rename button
            ],
            prevent_initial_call=True,  # Avoid initial render thrash
        )(self.handle_utilities)

        # --- Wave C ---------------------------------------------------
        app.callback(  # update_shape_labels
            Output("map-display", "figure", allow_duplicate=True),  # Mutates figure (duplicate output)
            Input("map-display", "relayoutData"),  # Triggered by user drawing/moving shapes
            State("map-display", "figure"),  # Current figure for in-place mutation
            prevent_initial_call=True,  # Avoid initial render thrash
        )(self.update_shape_labels)

        app.callback(  # set_origin_from_click
            [Output("origin-status", "children"), Output("map-display", "figure", allow_duplicate=True)],
            Input("map-display", "clickData"),  # Triggered by map clicks
            [State("origin-mode-button", "n_clicks"), State("map-display", "figure")],  # Mode + figure
            prevent_initial_call=True,  # Avoid initial render thrash
        )(self.set_origin_from_click)

        app.callback(  # execute_delete_map
            [Output("delete-status", "children"), Output("cache-bust-store", "data", allow_duplicate=True)],
            Input("confirm-delete-btn", "n_clicks"),  # Triggered by final confirm
            [State("cache-bust-store", "data"), State("map-config-store", "data")],  # Cache + config
            prevent_initial_call=True,  # Avoid initial render thrash
        )(self.execute_delete_map)

        app.callback(  # handle_zone_actions
            [Output("selected-zone-info", "children"), Output("selected-zone-store", "data")],
            [
                Input("edit-zone-btn", "n_clicks"),  # Edit button
                Input("remove-zone-btn", "n_clicks"),  # Remove button
                Input("map-display", "clickData"),  # Zone click on the map
            ],
            [State("selected-zone-store", "data")],  # Current selection state
            prevent_initial_call=True,  # Avoid initial render thrash
        )(self.handle_zone_actions)

        # --- Wave D ---------------------------------------------------
        app.callback(  # update_countdown_display
            Output("countdown-display", "children", allow_duplicate=True),  # Updates countdown label
            [Input("countdown-tick-interval", "n_intervals")],  # Fires every second
            [State("refresh-times-store", "data"), State("auto-refresh-toggle", "value")],  # Anchors + toggle
            prevent_initial_call=True,  # Avoid initial render thrash
        )(self.update_countdown_display)

        app.callback(  # update_clients_traces
            [
                Output("map-display", "figure", allow_duplicate=True),  # Mutated figure (duplicate output)
                Output("refresh-times-store", "data", allow_duplicate=True),  # Updated refresh anchor
            ],
            [
                Input("client-refresh-interval", "n_intervals"),  # 30s timer trigger
                Input("manual-refresh-btn", "n_clicks"),  # Manual refresh button
            ],
            [
                State("map-config-store", "data"),  # site_id/map_id source
                State("map-display", "figure"),  # Current figure for in-place mutation
                State("client-toggle", "value"),  # Reserved (kept for parity with original)
                State("refresh-times-store", "data"),  # Existing refresh anchors
            ],
            prevent_initial_call=True,  # Avoid initial render thrash
        )(self.update_clients_traces)

        app.callback(  # update_coverage_heatmap
            [
                Output("map-display", "figure", allow_duplicate=True),  # Mutated figure (duplicate output)
                Output("refresh-times-store", "data", allow_duplicate=True),  # Updated refresh anchor
            ],
            [Input("coverage-refresh-interval", "n_intervals")],  # 5-minute timer trigger
            [
                State("map-config-store", "data"),  # site_id/map_id/ppm source
                State("map-display", "figure"),  # Current figure for in-place mutation
                State("layer-toggle", "value"),  # Drives heatmap visibility flag
                State("refresh-times-store", "data"),  # Existing refresh anchors
            ],
            prevent_initial_call=True,  # Avoid initial render thrash
        )(self.update_coverage_heatmap)

        # --- Wave E1 --------------------------------------------------
        app.callback(  # handle_drawing_tools
            [
                Output("drawing-tool-status", "children"),  # Status text/widget output
                Output("cache-bust-store", "data", allow_duplicate=True),  # Bumps to refresh dropdown
            ],
            [
                Input("save-shape-btn", "n_clicks"),  # Save last drawn shape
                Input("clear-drawings-btn", "n_clicks"),  # Local clear hint
                Input("delete-paths-btn", "n_clicks"),  # Wipe sitesurvey_path
                Input("delete-wayfinding-btn", "n_clicks"),  # Wipe wayfinding_path
                Input("delete-walls-btn", "n_clicks"),  # Wipe wall_path
                Input("delete-zones-btn", "n_clicks"),  # Delete every zone on this map
            ],
            [
                State("drawing-mode-dropdown", "value"),  # Active drawing mode
                State("zone-name-input", "value"),  # Zone name when saving as zone
                State("map-display", "figure"),  # Current figure for shape extraction
                State("map-config-store", "data"),  # site_id/map_id/ppm source
                State("cache-bust-store", "data"),  # Cache-bust counter
            ],
            prevent_initial_call=True,  # Avoid initial render thrash
        )(self.handle_drawing_tools)

        app.callback(  # execute_clone_operation
            [
                Output("clone-status", "children"),  # Status text/widget output
                Output("cache-bust-store", "data", allow_duplicate=True),  # Bumps to refresh dropdown
            ],
            [Input("execute-clone-btn", "n_clicks")],  # Triggered by the Execute Clone button
            [
                State("clone-name-input", "value"),  # New cloned-map name
                State("map-config-store", "data"),  # site_id/map_id source
                State("cache-bust-store", "data"),  # Cache-bust counter
            ],
            prevent_initial_call=True,  # Avoid initial render thrash
        )(self.execute_clone_operation)

        # --- Wave E2 --------------------------------------------------
        app.callback(  # set_scale
            [Output("scale-status", "children"), Output("map-display", "figure", allow_duplicate=True)],
            Input("set-scale-button", "n_clicks"),  # Triggered by Set Scale button
            [State("scale-length-input", "value"), State("map-display", "figure")],  # Input + current figure
            prevent_initial_call=True,  # Avoid initial render thrash
        )(self.set_scale)

        app.callback(  # refresh_map_dropdown
            [Output("map-selector-dropdown", "options"), Output("available-maps-store", "data")],
            [
                Input("cache-bust-store", "data"),  # Cache-bust signal
                Input("manual-refresh-btn", "n_clicks"),  # Manual refresh button
                Input("url-location", "search"),  # URL change trigger
            ],
            [State("map-config-store", "data")],  # site_id source
            prevent_initial_call=False,  # Run on initial load to get fresh data
        )(self.refresh_map_dropdown)

        app.callback(  # handle_site_switch_from_dropdown
            [
                Output("map-selector-dropdown", "options"),
                Output("map-selector-dropdown", "value", allow_duplicate=True),
                Output("available-maps-store", "data", allow_duplicate=True),
                Output("map-config-store", "data", allow_duplicate=True),
                Output("map-display", "figure", allow_duplicate=True),
            ],
            [Input("site-selector-dropdown", "value")],  # Triggered by site selection
            [
                State("map-config-store", "data"),  # Current config
                State("available-sites-store", "data"),  # Sites store
                State("map-display", "figure"),  # Current figure
            ],
            prevent_initial_call=True,  # Avoid initial render thrash
        )(self.handle_site_switch_from_dropdown)

        app.callback(  # handle_site_from_url
            [Output("site-selector-dropdown", "value")],
            [Input("url-location", "search")],  # URL change trigger
            [State("map-config-store", "data"), State("available-sites-store", "data")],
            prevent_initial_call="initial_duplicate",  # Allow initial run on duplicate output
        )(self.handle_site_from_url)

        app.callback(  # sync_dropdown_with_url
            Output("map-selector-dropdown", "value"),
            [Input("url-location", "search")],  # URL change trigger
            [State("available-maps-store", "data"), State("map-selector-dropdown", "value")],
            prevent_initial_call=False,  # Must run on initial load
        )(self.sync_dropdown_with_url)

        app.callback(  # handle_url_map_switch
            [
                Output("map-display", "figure", allow_duplicate=True),
                Output("map-config-store", "data", allow_duplicate=True),
            ],
            [Input("url-location", "search")],  # URL change trigger
            [
                State("map-config-store", "data"),  # Current config
                State("map-display", "figure"),  # Current figure
                State("available-maps-store", "data"),  # Map allow-list
                State("map-selector-dropdown", "value"),  # Current selection
            ],
            prevent_initial_call="initial_duplicate",  # Allow initial run on duplicate output
        )(self.handle_url_map_switch)

        logging.debug(  # Trace registration end
            "MapViewerCallbacks: callbacks registered "
            "(5 wave-A + 4 wave-B + 4 wave-C + 3 wave-D + 2 wave-E1 + 6 wave-E2)"
        )
