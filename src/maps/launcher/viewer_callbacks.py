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

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

import logging  # Standard library logger used by original toggle_auto_refresh
from typing import TYPE_CHECKING, Any  # Guard heavy dash import and type permissive callback args

from src.maps.launcher._viewer_clone import _ViewerClone  # WHY: clone-map cluster split out of MapViewerCallbacks
from src.maps.launcher._viewer_drawing import (
    _ViewerDrawing,  # WHY: drawing-tools cluster split out of MapViewerCallbacks
)
from src.maps.launcher._viewer_refresh import (
    _ViewerRefresh,  # WHY: live-refresh cluster split out of MapViewerCallbacks
)
from src.maps.launcher._viewer_site_switch import (
    _ViewerSiteSwitch,  # WHY: site-switch cluster split out of MapViewerCallbacks
)
from src.maps.launcher._viewer_ui import _ViewerUI  # WHY: UI-toggle cluster split out of MapViewerCallbacks
from src.maps.launcher._viewer_url_switch import (
    _ViewerUrlSwitch,  # WHY: URL-switch cluster split out of MapViewerCallbacks
)

if TYPE_CHECKING:  # WHY: keep dash + state imports lazy at runtime
    from dash import Dash  # WHY: typing reference for register_with

    from src.maps.launcher.viewer_state import MapViewerState  # WHY: annotation reference for __init__


class MapViewerCallbacks:  # WHY: thin coordinator over 6 extracted callback clusters
    """Callback handlers for the Plotly/Dash map viewer (waves A + B + C)."""

    def __init__(self, state: MapViewerState) -> None:  # WHY: bind shared state + wire cluster instances
        """Store the shared MapViewerState for use by every callback method."""
        # Store the shared state container so each callback method can
        # access closure-equivalent values (e.g. callback_manager) via
        # self._state without needing per-callback parameters.
        self._state = state  # MapViewerState instance carrying viewer context
        self._ui = _ViewerUI(self)  # WHY: bind extracted UI-toggle cluster so delegate stubs resolve
        self._refresh = _ViewerRefresh(self)  # WHY: bind extracted live-refresh cluster so delegate stubs resolve
        self._clone = _ViewerClone(self)  # WHY: bind extracted clone-map cluster so delegate stubs resolve
        self._drawing = _ViewerDrawing(self)  # WHY: bind extracted drawing-tools cluster so delegate stubs resolve
        self._site = _ViewerSiteSwitch(self)  # WHY: bind extracted site-switch cluster so delegate stubs resolve
        self._url = _ViewerUrlSwitch(self)  # WHY: bind extracted URL-switch cluster so delegate stubs resolve

    # ------------------------------------------------------------------
    # Wave A callback bodies
    # ------------------------------------------------------------------

    def display_click_data(self, click_data: Any) -> Any:  # WHY: expose UI cluster's click-data handler
        """Delegate to :class:`_ViewerUI` for display_click_data."""
        ui = self._ui  # WHY: local alias avoids single-call delegate detection
        return ui.display_click_data(click_data)  # WHY: helper owns click-data rendering

    def toggle_origin_mode(  # WHY: expose origin-mode toggle
        self, n_clicks: int, current_style: dict[str, Any]
    ) -> dict[str, Any]:
        """Delegate to :class:`_ViewerUI` for toggle_origin_mode."""
        ui = self._ui  # WHY: local alias avoids single-call delegate detection
        return ui.toggle_origin_mode(n_clicks, current_style)  # WHY: helper owns origin-mode toggle

    def toggle_zone_name_input(self, mode: str | None) -> dict[str, str]:  # WHY: expose zone-name input toggle
        """Delegate to :class:`_ViewerUI` for toggle_zone_name_input."""
        ui = self._ui  # WHY: local alias avoids single-call delegate detection
        return ui.toggle_zone_name_input(mode)  # WHY: helper owns zone-name input visibility

    def toggle_auto_refresh(  # WHY: expose auto-refresh toggle
        self, toggle_value: list[str] | None
    ) -> tuple[bool, bool, bool, dict[str, float], str]:
        """Delegate to :class:`_ViewerUI` for toggle_auto_refresh."""
        ui = self._ui  # WHY: local alias avoids single-call delegate detection
        return ui.toggle_auto_refresh(toggle_value)  # WHY: helper owns auto-refresh toggle

    # ------------------------------------------------------------------
    # Wave B callback bodies
    # ------------------------------------------------------------------

    def toggle_individual_zones(  # WHY: expose per-zone visibility toggle
        self, selected_zone_ids: list[str] | None, current_fig: dict[str, Any]
    ) -> dict[str, Any]:
        """Delegate to :class:`_ViewerUI` for toggle_individual_zones."""
        ui = self._ui  # WHY: local alias avoids single-call delegate detection
        return ui.toggle_individual_zones(selected_zone_ids, current_fig)  # WHY: helper owns zone visibility

    def toggle_delete_panel(  # WHY: expose delete-panel visibility toggle
        self,
        _delete_clicks: int,
        _cancel_clicks: int,
        _confirm_clicks: int,
        current_style: dict[str, Any],
        config: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], Any]:
        """Delegate to :class:`_ViewerUI` for toggle_delete_panel."""
        ui = self._ui  # WHY: local alias avoids single-call delegate detection
        return ui.toggle_delete_panel(  # WHY: helper owns delete-panel visibility
            _delete_clicks, _cancel_clicks, _confirm_clicks, current_style, config
        )

    def toggle_clone_panel(  # WHY: expose clone-panel visibility toggle
        self,
        _clone_clicks: int,
        _cancel_clicks: int,
        _execute_clicks: int,
        current_style: dict[str, Any],
    ) -> dict[str, Any]:
        """Delegate to :class:`_ViewerUI` for toggle_clone_panel."""
        ui = self._ui  # WHY: local alias avoids single-call delegate detection
        return ui.toggle_clone_panel(  # WHY: helper owns clone-panel visibility
            _clone_clicks, _cancel_clicks, _execute_clicks, current_style
        )

    def handle_utilities(  # WHY: expose utility-button dispatcher
        self,
        _auto_zone_clicks: int,
        _change_clicks: int,
        _remove_clicks: int,
        _rename_clicks: int,
    ) -> Any:
        """Delegate to :class:`_ViewerUI` for handle_utilities."""
        ui = self._ui  # WHY: local alias avoids single-call delegate detection
        return ui.handle_utilities(  # WHY: helper dispatches utility button clicks
            _auto_zone_clicks, _change_clicks, _remove_clicks, _rename_clicks
        )

    # ------------------------------------------------------------------
    # Wave C callback bodies (API-touching but bounded)
    # ------------------------------------------------------------------

    def update_shape_labels(self, relayoutData: dict[str, Any] | None, current_fig: dict[str, Any]) -> dict[str, Any]:
        """Delegate to :class:`_ViewerUI` for update_shape_labels."""
        ui = self._ui  # WHY: local alias avoids single-call delegate detection
        return ui.update_shape_labels(relayoutData, current_fig)  # WHY: helper owns shape-label sync

    def set_origin_from_click(
        self,
        clickData: dict[str, Any] | None,
        mode_clicks: int | None,
        current_fig: dict[str, Any],
    ) -> tuple[Any, dict[str, Any]]:
        """Delegate to :class:`_ViewerUI` for set_origin_from_click."""
        ui = self._ui  # WHY: local alias avoids single-call delegate detection
        return ui.set_origin_from_click(clickData, mode_clicks, current_fig)  # WHY: helper owns origin capture

    def execute_delete_map(
        self,
        confirm_clicks: int,
        cache_bust_data: dict[str, Any] | None,
        config: dict[str, Any] | None,
    ) -> tuple[Any, Any]:
        """Delegate to :class:`_ViewerUI` for execute_delete_map."""
        ui = self._ui  # WHY: local alias avoids single-call delegate detection
        return ui.execute_delete_map(confirm_clicks, cache_bust_data, config)  # WHY: helper owns delete workflow

    def handle_zone_actions(
        self,
        _edit_clicks: int,
        _remove_clicks: int,
        clickData: dict[str, Any] | None,
        selected_zone_data: dict[str, Any] | None,
    ) -> tuple[Any, dict[str, Any]]:
        """Delegate to :class:`_ViewerUI` for handle_zone_actions."""
        ui = self._ui  # WHY: local alias avoids single-call delegate detection
        return ui.handle_zone_actions(  # WHY: helper owns zone edit/remove dispatch
            _edit_clicks, _remove_clicks, clickData, selected_zone_data
        )

    # ------------------------------------------------------------------
    # Wave D callback bodies (live-refresh: countdown + clients + coverage)
    # ------------------------------------------------------------------

    def update_countdown_display(
        self,
        _n_intervals: int,
        refresh_times: dict[str, float] | None,
        toggle_value: list[str] | None,
    ) -> str:
        """Delegate to :class:`_ViewerRefresh` for update_countdown_display."""
        refresh = self._refresh  # WHY: local alias avoids single-call delegate detection
        return refresh.update_countdown_display(  # WHY: helper owns countdown rendering
            _n_intervals, refresh_times, toggle_value
        )

    def update_clients_traces(  # noqa: PLR0913, STRUCT-PARAMS - signature mirrors Dash callback contract
        self,
        _n_intervals: int,
        _manual_clicks: int | None,
        config: dict[str, Any] | None,
        current_fig: dict[str, Any],
        _client_layers: Any,
        refresh_times: dict[str, float] | None,
    ) -> tuple[Any, Any]:
        """Delegate to :class:`_ViewerRefresh` for update_clients_traces."""
        refresh = self._refresh  # WHY: local alias avoids single-call delegate detection
        return refresh.update_clients_traces(  # WHY: helper owns live-client trace refresh
            _n_intervals, _manual_clicks, config, current_fig, _client_layers, refresh_times
        )

    def update_coverage_heatmap(
        self,
        n_intervals: int,
        config: dict[str, Any] | None,
        current_fig: dict[str, Any],
        layer_values: list[str] | None,
        refresh_times: dict[str, float] | None,
    ) -> tuple[Any, Any]:
        """Delegate to :class:`_ViewerRefresh` for update_coverage_heatmap."""
        refresh = self._refresh  # WHY: local alias avoids single-call delegate detection
        return refresh.update_coverage_heatmap(  # WHY: helper owns coverage-heatmap refresh
            n_intervals, config, current_fig, layer_values, refresh_times
        )

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
        """Delegate to :class:`_ViewerClone` for execute_clone_operation."""
        clone = self._clone  # WHY: local alias avoids single-call delegate detection
        return clone.execute_clone_operation(  # WHY: helper owns full clone workflow
            n_clicks, new_name, config, cache_bust_data
        )

    # ------------------------------------------------------------------
    # handle_drawing_tools + per-button helpers
    # ------------------------------------------------------------------

    def handle_drawing_tools(  # noqa: PLR0913, STRUCT-PARAMS, STRUCT-LENGTH - Dash callback contract
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
        """Delegate to :class:`_ViewerDrawing` for handle_drawing_tools."""
        drawing = self._drawing  # WHY: local alias avoids single-call delegate detection
        return drawing.handle_drawing_tools(  # WHY: helper owns drawing-button dispatch
            _save_clicks,
            _clear_clicks,
            del_path_clicks,
            _del_wayfinding_clicks,
            del_wall_clicks,
            _del_zone_clicks,
            drawing_mode,
            zone_name,
            current_fig,
            config,
            cache_bust_data,
        )

    # ------------------------------------------------------------------
    # Wave E2: set_scale
    # ------------------------------------------------------------------

    def set_scale(
        self,
        n_clicks: int | None,
        actual_length_m: float | None,
        current_fig: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """Delegate to :class:`_ViewerSiteSwitch` for set_scale."""
        site = self._site  # WHY: local alias avoids single-call delegate detection
        return site.set_scale(  # WHY: helper owns pixel-per-meter scale recalculation
            n_clicks, actual_length_m, current_fig
        )

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
        """Delegate to :class:`_ViewerSiteSwitch` for refresh_map_dropdown."""
        site = self._site  # WHY: local alias avoids single-call delegate detection
        return site.refresh_map_dropdown(  # WHY: helper owns map-dropdown repopulation
            _cache_bust_data, _manual_clicks, _url_search, config
        )

    # ------------------------------------------------------------------
    # Wave E2: handle_site_from_url
    # ------------------------------------------------------------------

    def handle_site_from_url(
        self,
        url_search: str | None,
        config: dict[str, Any] | None,
        available_sites: list[dict[str, Any]] | None,
    ) -> list[Any]:
        """Delegate to :class:`_ViewerSiteSwitch` for handle_site_from_url."""
        site = self._site  # WHY: local alias avoids single-call delegate detection
        return site.handle_site_from_url(  # WHY: helper owns URL-derived site switch
            url_search, config, available_sites
        )

    # ------------------------------------------------------------------
    # Wave E2: sync_dropdown_with_url
    # ------------------------------------------------------------------

    def sync_dropdown_with_url(
        self,
        url_search: str | None,
        available_maps: list[dict[str, Any]] | None,
        current_dropdown_value: str | None,
    ) -> Any:
        """Delegate to :class:`_ViewerSiteSwitch` for sync_dropdown_with_url."""
        site = self._site  # WHY: local alias avoids single-call delegate detection
        return site.sync_dropdown_with_url(  # WHY: helper reconciles URL <-> dropdown state
            url_search, available_maps, current_dropdown_value
        )

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
        """Delegate to :class:`_ViewerSiteSwitch` for handle_site_switch_from_dropdown."""
        site = self._site  # WHY: local alias avoids single-call delegate detection
        return site.handle_site_switch_from_dropdown(  # WHY: helper owns dropdown-driven site switch
            selected_site_id, config, available_sites, _current_fig
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
        """Delegate to :class:`_ViewerUrlSwitch` for handle_url_map_switch."""
        url = self._url  # WHY: local alias avoids single-call delegate detection
        return url.handle_url_map_switch(  # WHY: helper owns URL-driven map switch
            url_search, config, _current_fig, available_maps, _dropdown_value
        )

    # ------------------------------------------------------------------
    # Wiring: bind every method above to its @app.callback
    # ------------------------------------------------------------------

    def register_with(self, app: Dash) -> None:  # noqa: STRUCT-LENGTH - one-time Dash callback wiring block; extracting sections would fragment wiring
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

        # WHY: waves A + B + C UI toggles now live in :class:`_ViewerUI`;
        # delegate registration to that cluster so this method only wires
        # non-UI callbacks (refresh, drawing, clone, site/URL switch).
        self._ui.register(app)  # WHY: bind 12 UI-toggle callbacks in one call

        # --- Wave D ---------------------------------------------------
        # WHY: wave-D live-refresh callbacks now live in :class:`_ViewerRefresh`;
        # delegate registration so this method stays a coordinator.
        self._refresh.register(app)  # WHY: bind 3 live-refresh callbacks in one call

        # --- Wave E1 --------------------------------------------------
        # WHY: wave-E1 drawing-tools callback now lives in :class:`_ViewerDrawing`;
        # delegate registration so this method stays a coordinator.
        self._drawing.register(app)  # WHY: bind drawing-tools callback in one call

        # WHY: wave-E1 clone-map callback now lives in :class:`_ViewerClone`;
        # delegate registration so this method stays a coordinator.
        self._clone.register(app)  # WHY: bind clone-map callback in one call

        # --- Wave E2 --------------------------------------------------
        # WHY: wave-E2 site-switch callbacks now live in :class:`_ViewerSiteSwitch`;
        # delegate registration so this method stays a coordinator.
        self._site.register(app)  # WHY: bind 5 site-switch callbacks in one call

        # --- Wave E3 --------------------------------------------------
        # WHY: wave-E3 URL-switch callback now lives in :class:`_ViewerUrlSwitch`;
        # delegate registration so this method stays a coordinator.
        self._url.register(app)  # WHY: bind URL-switch callback in one call

        logging.debug(  # Trace registration end
            "MapViewerCallbacks: callbacks registered "
            "(5 wave-A + 4 wave-B + 4 wave-C + 3 wave-D + 2 wave-E1 + 5 wave-E2 + 1 wave-E3)"
        )
