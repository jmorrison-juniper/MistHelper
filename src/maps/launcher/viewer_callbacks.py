"""Dash callback handlers extracted from ``_launch_plotly_viewer``.

Each method on :class:`MapViewerCallbacks` corresponds to one Dash
callback that was previously nested as a closure inside
:py:meth:`src.maps.maps_manager.MapsManager._launch_plotly_viewer`.
The :meth:`MapViewerCallbacks.register_with` method wires every
callback to its ``@app.callback`` decorator with byte-identical
``Input`` / ``Output`` / ``State`` signatures, ``prevent_initial_call``
flags, and user-facing strings.

Wave A scope: five trivial UI toggles, each with cyclomatic complexity
<= 3:

* ``toggle_layers`` -- delegates to ``PlotlyMapCallbackManager``.
* ``display_click_data`` -- delegates to ``PlotlyMapCallbackManager``.
* ``toggle_origin_mode`` -- mutates a style dict based on click parity.
* ``toggle_zone_name_input`` -- shows/hides an input row by mode.
* ``toggle_auto_refresh`` -- enables/disables five Interval components.

To add a callback in a later wave:

1. Implement the method on this class (keep CC <= 10).
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
from typing import TYPE_CHECKING, Any  # Guard heavy dash import and type permissive callback args

if TYPE_CHECKING:  # pragma: no cover - typing-only imports
    from dash import Dash  # noqa: F401 - typing reference for register_with

    from src.maps.launcher.viewer_state import MapViewerState  # noqa: F401


class MapViewerCallbacks:
    """Callback handlers for the Plotly/Dash map viewer (wave A scope)."""

    def __init__(self, state: MapViewerState) -> None:
        # Store the shared state container so each callback method can
        # access closure-equivalent values (e.g. callback_manager) via
        # self._state without needing per-callback parameters.
        self._state = state  # MapViewerState instance carrying viewer context

    # ------------------------------------------------------------------
    # Callback bodies (preserve original behavior byte-for-byte)
    # ------------------------------------------------------------------

    def toggle_layers(  # noqa: PLR0913 - signature mirrors original Dash callback
        self,
        infra_layers: Any,
        beacon_layers: Any,
        client_layers: Any,
        device_layers: Any,
        filter_layers: Any,
        current_fig: Any,
    ) -> Any:
        # Delegate visibility toggling to PlotlyMapCallbackManager which
        # owns the layer-name -> trace mapping logic (extracted earlier).
        return self._state.callback_manager.apply_layer_toggles(
            current_fig=current_fig,  # Plotly figure dict from State input
            infra_layers=infra_layers,  # Walls/wayfinding toggle values
            beacon_layers=beacon_layers,  # Beacon overlay toggle values
            client_layers=client_layers,  # Connected-client toggle values
            device_layers=device_layers,  # AP/switch/gateway toggle values
            filter_layers=filter_layers,  # Status filter toggle values
        )

    def display_click_data(self, click_data: Any) -> Any:
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
    # Wiring: bind every method above to its @app.callback
    # ------------------------------------------------------------------

    def register_with(self, app: Dash) -> None:
        """Attach all wave-A callbacks to the provided Dash ``app``."""
        # Import dash decorator helpers lazily so this module stays
        # importable when dash is missing (matches the fallback behavior
        # in MapsManager._launch_plotly_viewer).
        from dash import Input, Output, State  # Local import keeps module import-light

        logging.info(  # Trace registration start so operators can confirm wiring
            "MapViewerCallbacks: registering %d wave-A callbacks", 5
        )

        # --- toggle_layers --------------------------------------------
        app.callback(  # Wire layer visibility toggles to the figure output
            Output("map-display", "figure"),  # Output: replaces the figure
            [
                Input("layer-toggle", "value"),  # Walls/wayfinding checklist
                Input("beacon-toggle", "value"),  # Beacon overlay checklist
                Input("client-toggle", "value"),  # Connected-clients checklist
                Input("device-toggle", "value"),  # AP/switch/gateway checklist
                Input("filter-toggle", "value"),  # Status-filter checklist
            ],
            State("map-display", "figure"),  # Current figure passed in for mutation
        )(
            self.toggle_layers
        )  # Bind the decorator to the bound method

        # --- display_click_data ---------------------------------------
        app.callback(  # Wire map clicks to the details panel output
            Output("click-data", "children"),  # Output: details-panel children
            Input("map-display", "clickData"),  # Input: Plotly clickData dict
        )(
            self.display_click_data
        )  # Bind the decorator to the bound method

        # --- toggle_origin_mode ---------------------------------------
        app.callback(  # Wire origin-mode button to its own style output
            Output("origin-mode-button", "style"),  # Output: button style dict
            Input("origin-mode-button", "n_clicks"),  # Input: button click counter
            State("origin-mode-button", "style"),  # State: current style dict
            prevent_initial_call=True,  # Don't toggle on page load (n_clicks=None)
        )(
            self.toggle_origin_mode
        )  # Bind the decorator to the bound method

        # --- toggle_zone_name_input -----------------------------------
        app.callback(  # Wire drawing-mode dropdown to zone-name container
            Output("zone-name-container", "style"),  # Output: container style dict
            Input("drawing-mode-dropdown", "value"),  # Input: selected mode value
            prevent_initial_call=True,  # Don't re-render on page load
        )(
            self.toggle_zone_name_input
        )  # Bind the decorator to the bound method

        # --- toggle_auto_refresh --------------------------------------
        app.callback(  # Wire auto-refresh checkbox to five outputs
            [
                Output("client-refresh-interval", "disabled"),  # Client interval gate
                Output("coverage-refresh-interval", "disabled"),  # Coverage interval gate
                Output("countdown-tick-interval", "disabled"),  # Countdown tick gate
                Output("refresh-times-store", "data"),  # Refresh timestamp store
                Output("countdown-display", "children"),  # Countdown label widget
            ],
            [Input("auto-refresh-toggle", "value")],  # Input: checklist value list
            prevent_initial_call=True,  # Don't reset timers on page load
        )(
            self.toggle_auto_refresh
        )  # Bind the decorator to the bound method

        logging.debug("MapViewerCallbacks: wave-A callbacks registered (5)")  # Trace successful wiring for debug audits
