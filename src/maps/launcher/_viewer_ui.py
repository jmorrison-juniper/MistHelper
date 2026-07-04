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
from collections.abc import Callable  # WHY: opaque manager + type-permissive Dash callback args
from dataclasses import dataclass  # WHY: frozen value objects collapse parameter counts
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # WHY: keep dash imports lazy at runtime
    from dash import Dash  # WHY: annotation reference for register(app)


# ----------------------------------------------------------------------
# Module-level constants (magic numbers + repeated literals extracted)
# ----------------------------------------------------------------------

_ORIGIN_ACTIVE_BG = "#667eea"  # WHY: purple fill signals armed origin-set mode
_ORIGIN_ACTIVE_BORDER = "2px solid #00bfff"  # WHY: cyan border reinforces armed state
_ORIGIN_IDLE_BG = "#3d3d3d"  # WHY: neutral gray signals inactive origin-set mode
_ORIGIN_IDLE_BORDER = "1px solid #667eea"  # WHY: thin purple border at rest

_ZONE_INPUT_VISIBLE = {"display": "block", "marginBottom": "10px"}  # WHY: reveal zone-name field
_ZONE_INPUT_HIDDEN = {"display": "none"}  # WHY: hide zone-name field outside zone mode

_INITIAL_COUNTDOWN_TEXT = "Clients: 30s | RF: 5:00"  # WHY: label shown when refresh armed
_DISABLED_COUNTDOWN_TEXT = "Auto-refresh: Off"  # WHY: label shown when refresh disarmed

_DELETE_PANEL_BASE = {  # WHY: shared destructive-red border/background
    "padding": "12px 20px",
    "backgroundColor": "#330000",
    "borderBottom": "2px solid #ff4444",
}
_CLONE_PANEL_BASE = {  # WHY: shared success-green border/background
    "padding": "12px 20px",
    "backgroundColor": "#1a1a1a",
    "borderBottom": "1px solid #00ff88",
}

_CROSSHAIR_HALF_SIZE = 40  # WHY: half-length of origin crosshair arms in pixels
_METERS_TO_FEET = 3.28084  # WHY: SI to imperial conversion factor for ruler labels
_SUCCESS_STATUSES = (200, 204)  # WHY: HTTP status codes Mist returns for successful delete

_ZONE_PROMPT_STYLE = {"fontSize": "11px", "color": "#888", "fontStyle": "italic"}  # WHY: default zone-info prompt
_ZONE_META_STYLE = {"fontSize": "11px", "color": "#888", "margin": "4px 0"}  # WHY: gray meta text for origin panel
_ZONE_HINT_STYLE = {"fontSize": "10px", "color": "#888"}  # WHY: secondary hint text style
_ORIGIN_PROMPT_STYLE = {"fontSize": "11px", "color": "#ff8800", "margin": "4px 0"}  # WHY: orange prompt to click
_ORIGIN_OK_STYLE = {"fontSize": "11px", "color": "#00ff00", "margin": "4px 0"}  # WHY: green confirmation style
_ORIGIN_HINT_STYLE = {"fontSize": "10px", "color": "#888", "margin": "4px 0"}  # WHY: gray "exit mode" hint

# WHY: static dispatch table for handle_utilities keeps its CC low
_UTILITY_RESPONSES: dict[str, tuple[str, str, str]] = {
    "auto-zone-btn": (  # WHY: AI auto-zone request => purple/info
        "Robot Auto-Zone: AI-powered zone detection - analyzes walls and creates location zones automatically",
        "#667eea",
        "info",
    ),
    "change-image-btn": (  # WHY: change-image request => orange/warning
        "! Change Image: Use Mist API updateSiteMapImage - feature requires file upload",
        "#ff8800",
        "info",
    ),
    "remove-image-btn": (  # WHY: destructive remove-image request => red/warning-level log
        "! Remove Image: Use Mist API deleteSiteMapImage - DESTRUCTIVE operation",
        "#ff4444",
        "warning",
    ),
    "rename-btn": (  # WHY: rename request => orange/warning color
        "! Rename: Use Mist API updateSiteMap with new name - requires text input",
        "#ff8800",
        "info",
    ),
}


# ----------------------------------------------------------------------
# Frozen value objects (collapse multi-arg passthroughs)
# ----------------------------------------------------------------------


@dataclass(frozen=True)  # WHY: immutable bundle for auto-refresh outputs
class _RefreshPayload:  # WHY: frozen value object for toggle_auto_refresh return tuple
    """Bundle of the five Dash outputs emitted by toggle_auto_refresh."""

    disabled: bool  # WHY: applied to all three dcc.Interval components uniformly
    refresh_data: dict[str, float]  # WHY: refresh-times-store payload
    countdown_text: str  # WHY: countdown-display label


@dataclass(frozen=True)  # WHY: immutable delete-map input bundle
class _DeleteMapConfig:  # WHY: frozen value object for the delete-map workflow inputs
    """Resolved site_id/map_id/map_name for the delete-map workflow."""

    site_id: str | None  # WHY: destination site UUID for the Mist API call
    map_id: str | None  # WHY: target map UUID for the Mist API call
    map_name: str  # WHY: display label used in status messages and logs


@dataclass(frozen=True)  # WHY: immutable origin coordinate pair
class _OriginPoint:  # WHY: frozen value object for origin crosshair coordinates
    """Origin coordinates in pixel space for crosshair updates."""

    x: float  # WHY: origin X in figure pixel coordinates
    y: float  # WHY: origin Y in figure pixel coordinates


# ----------------------------------------------------------------------
# Free-function helpers (extracted to keep methods small)
# ----------------------------------------------------------------------


def _build_refresh_payload(
    is_enabled: bool, current_time: float
) -> _RefreshPayload:  # WHY: helper for toggle_auto_refresh
    """Return the immutable _RefreshPayload for the given toggle state."""
    if is_enabled:  # WHY: user just armed auto-refresh
        logging.info("Live data refresh: Auto-refresh ENABLED by user")  # WHY: preserve audit log
        data = {  # WHY: seed both refresh timestamps to "now" so countdowns start full
            "client_last_refresh": current_time,
            "coverage_last_refresh": current_time,
        }
        return _RefreshPayload(
            disabled=False, refresh_data=data, countdown_text=_INITIAL_COUNTDOWN_TEXT
        )  # WHY: armed payload
    logging.info("Live data refresh: Auto-refresh DISABLED by user")  # WHY: preserve audit log
    stopped: dict[str, float] = {  # WHY: float dict matches _RefreshPayload's invariant type
        "client_last_refresh": 0.0,
        "coverage_last_refresh": 0.0,
    }
    return _RefreshPayload(
        disabled=True, refresh_data=stopped, countdown_text=_DISABLED_COUNTDOWN_TEXT
    )  # WHY: disarmed payload


def _resolve_zone_id(zones: list[dict[str, Any]], zone_name: str) -> tuple[str, int] | None:  # WHY: name->id resolver
    """Return (zone_id, index) whose name matches zone_name, or None."""
    for idx, zone in enumerate(zones):  # WHY: linear scan is bounded (~zones per map)
        if zone.get("name") == zone_name:  # WHY: name match anchors the ID lookup
            return zone.get("id", f"zone_{idx}"), idx  # WHY: fallback ID mirrors original closure
    return None  # WHY: unknown name => leave visibility untouched


def _apply_zone_visibility(
    fig: dict[str, Any], zones: list[dict[str, Any]], selected: set[str]
) -> None:  # WHY: mutate Zone traces
    """Mutate fig traces so Zone: overlays reflect the selected set."""
    for trace in fig["data"]:  # WHY: Plotly figures store traces under "data"
        trace_name = trace.get("name", "")  # WHY: not every trace carries a name
        if not trace_name.startswith("Zone:"):  # WHY: guard limits mutation to zone overlays
            continue  # WHY: non-zone trace => skip visibility change
        zone_name = trace_name.replace("Zone: ", "")  # WHY: strip prefix to match zone record
        resolved = _resolve_zone_id(zones, zone_name)  # WHY: delegate name->id lookup
        if resolved is None:  # WHY: unknown zone => skip visibility change
            continue  # WHY: leave trace untouched when name is unresolved
        zone_id, _ = resolved  # WHY: only need the id, index unused here
        trace["visible"] = zone_id in selected  # WHY: True/False drives Plotly visibility


def _delete_panel_style(button_id: str) -> tuple[dict[str, Any] | None, bool]:  # WHY: dispatcher for delete-panel style
    """Return (style dict, whether name should update) for a delete-panel trigger."""
    if button_id == "delete-btn":  # WHY: user opened the delete panel
        return ({"display": "block", **_DELETE_PANEL_BASE}, True)  # WHY: show + refresh name
    if button_id in {"cancel-delete-btn", "confirm-delete-btn"}:  # WHY: hide on close/confirm
        return ({"display": "none", **_DELETE_PANEL_BASE}, False)  # WHY: hide, keep name display
    return (None, False)  # WHY: unknown trigger => sentinel for caller


def _clone_panel_style(button_id: str) -> dict[str, Any] | None:  # WHY: dispatcher for clone-panel style
    """Return the clone-panel style dict for a trigger id, or None."""
    if button_id == "clone-btn":  # WHY: user opened the clone panel
        return {"display": "block", **_CLONE_PANEL_BASE}  # WHY: show panel
    if button_id in {"cancel-clone-btn", "execute-clone-btn"}:  # WHY: hide on close/execute
        return {"display": "none", **_CLONE_PANEL_BASE}  # WHY: hide panel
    return None  # WHY: unknown trigger => sentinel for caller


def _measurement_annotation(shape: dict[str, Any], ppm: float) -> dict[str, Any]:
    """Return the multi-unit annotation dict for a ruler line shape."""
    x0, y0 = shape.get("x0", 0), shape.get("y0", 0)  # WHY: start of ruler line
    x1, y1 = shape.get("x1", 0), shape.get("y1", 0)  # WHY: end of ruler line
    length_px = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5  # WHY: pixel-space Euclidean length
    length_m = length_px / ppm if ppm > 0 else 0  # WHY: guard against zero PPM
    length_ft = length_m * _METERS_TO_FEET  # WHY: derived imperial length
    return {  # WHY: Plotly annotation dict shown next to the drawn line
        "x": (x0 + x1) / 2,
        "y": (y0 + y1) / 2,
        "text": f"<b>{length_px:.1f} px</b><br>{length_ft:.2f} ft<br>{length_m:.2f} m",
        "showarrow": False,
        "font": {"size": 12, "color": "cyan", "family": "Arial Black"},
        "bgcolor": "rgba(0,0,0,0.7)",
        "bordercolor": "cyan",
        "borderwidth": 2,
        "borderpad": 4,
    }


def _origin_layout_meta(fig: dict[str, Any]) -> dict[str, Any]:
    """Return the layout.meta dict for a figure, creating it when absent."""
    layout = fig.setdefault("layout", {})  # WHY: guarantee layout container exists
    meta: dict[str, Any] = layout.setdefault("meta", {})  # WHY: annotate cast to dict[str, Any]
    return meta  # WHY: return typed dict so mypy strict is satisfied


def _persist_origin(fig: dict[str, Any], origin: _OriginPoint) -> None:
    """Persist origin coordinates into the figure's layout meta bag."""
    meta = _origin_layout_meta(fig)  # WHY: reuse the setdefault helper
    meta["origin_x"] = origin.x  # WHY: later callbacks read this back
    meta["origin_y"] = origin.y  # WHY: paired with origin_x for full point


def _update_horizontal_origin(trace: dict[str, Any], origin: _OriginPoint) -> None:
    """Refit the horizontal crosshair trace to the new origin."""
    trace["x"] = [origin.x - _CROSSHAIR_HALF_SIZE, origin.x + _CROSSHAIR_HALF_SIZE]  # WHY: span across X
    trace["y"] = [origin.y, origin.y]  # WHY: horizontal line stays at origin Y
    trace["hovertext"] = f"Origin: ({origin.x:.1f}, {origin.y:.1f})"  # WHY: keep hover accurate


def _update_origin_point(trace: dict[str, Any], origin: _OriginPoint) -> None:
    """Refit the origin dot marker to the new origin."""
    trace["x"] = [origin.x]  # WHY: single-point marker at origin X
    trace["y"] = [origin.y]  # WHY: single-point marker at origin Y
    trace["hovertext"] = f"Origin: ({origin.x:.1f}, {origin.y:.1f})"  # WHY: keep hover accurate


def _update_vertical_origin(trace: dict[str, Any], origin: _OriginPoint) -> None:
    """Refit the vertical crosshair trace to the new origin."""
    trace["x"] = [origin.x, origin.x]  # WHY: vertical line stays at origin X
    trace["y"] = [origin.y - _CROSSHAIR_HALF_SIZE, origin.y + _CROSSHAIR_HALF_SIZE]  # WHY: span across Y
    trace["hovertext"] = f"Origin: ({origin.x:.1f}, {origin.y:.1f})"  # WHY: keep hover accurate


def _is_vertical_origin_trace(trace: dict[str, Any]) -> bool:
    """Return True when trace is the unnamed vertical origin crosshair."""
    hover = str(trace.get("hovertext", ""))  # WHY: normalize to string before search
    if "Origin:" not in hover:  # WHY: cheap rejection for non-origin traces
        return False
    if trace.get("mode") != "lines":  # WHY: vertical crosshair is a line trace
        return False
    return not trace.get("showlegend")  # WHY: crosshair hides from the legend


def _extract_zone_selection(clickData: dict[str, Any], zones: list[dict[str, Any]]) -> tuple[str, str | None]:
    """Return (zone_name, zone_id) for a click on a Zone: trace, or ("", None)."""
    point = clickData["points"][0]  # WHY: first clicked point carries hover metadata
    hover_text = point.get("hovertext", "")  # WHY: hovertext encodes the zone name
    if "Zone:" not in hover_text:  # WHY: caller filters non-zone clicks upstream
        return "", None
    zone_name = hover_text.split("Zone: ")[1] if "Zone: " in hover_text else "Unknown"  # WHY: parse name
    resolved = _resolve_zone_id(zones, zone_name)  # WHY: shared name->id resolver
    zone_id = resolved[0] if resolved else None  # WHY: unwrap optional tuple
    return zone_name, zone_id


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
        from dash import html  # WHY: local import keeps module import-light

        return self._state.callback_manager.build_click_details(  # WHY: helper produces dash.html widgets
            click_data=click_data,  # WHY: Plotly clickData dict (point + curve info)
            html=html,  # WHY: pass dash.html so the helper can build widgets
        )

    def toggle_origin_mode(  # WHY: parity-based toggle for origin-set mode
        self, n_clicks: int, current_style: dict[str, Any]
    ) -> dict[str, Any]:
        """Toggle origin setting mode on/off with visual feedback."""
        if n_clicks % 2 == 1:  # WHY: odd click count means mode is ACTIVE
            current_style["backgroundColor"] = _ORIGIN_ACTIVE_BG  # WHY: purple fill highlights armed state
            current_style["border"] = _ORIGIN_ACTIVE_BORDER  # WHY: cyan border reinforces armed state
            return current_style  # WHY: return mutated style dict to Dash
        current_style["backgroundColor"] = _ORIGIN_IDLE_BG  # WHY: neutral dark gray = inactive button
        current_style["border"] = _ORIGIN_IDLE_BORDER  # WHY: thin purple border at rest
        return current_style  # WHY: return mutated style dict to Dash

    def toggle_zone_name_input(self, mode: str | None) -> dict[str, str]:  # WHY: input row is zone-mode-only
        """Show zone name input only when zone mode is selected."""
        if mode == "zone":  # WHY: only zone drawing mode needs the zone-name field
            return _ZONE_INPUT_VISIBLE  # WHY: reveal the input row
        return _ZONE_INPUT_HIDDEN  # WHY: hide the input for wall/path/measure modes

    def toggle_auto_refresh(  # WHY: drives 3 dcc.Interval flags + countdown label
        self, toggle_value: list[str] | None
    ) -> tuple[bool, bool, bool, dict[str, float], str]:
        """Enable or disable auto-refresh intervals based on checkbox."""
        is_enabled = "enabled" in (toggle_value or [])  # WHY: checklist contains "enabled" when checked
        payload = _build_refresh_payload(is_enabled, time.time())  # WHY: delegate to keep method short
        return (  # WHY: Dash outputs are (interval x3, store, countdown label)
            payload.disabled,
            payload.disabled,
            payload.disabled,
            payload.refresh_data,
            payload.countdown_text,
        )

    def toggle_individual_zones(  # WHY: flips visibility on "Zone:"-prefixed traces per checklist
        self, selected_zone_ids: list[str] | None, current_fig: dict[str, Any]
    ) -> dict[str, Any]:
        """Show/hide individual zones based on checklist."""
        if not self._state.zones:  # WHY: no zones available => nothing to toggle
            return current_fig  # WHY: return figure unchanged
        selected_set = set(selected_zone_ids) if selected_zone_ids else set()  # WHY: O(1) membership tests
        _apply_zone_visibility(current_fig, self._state.zones, selected_set)  # WHY: mutate in place
        return current_fig  # WHY: return mutated figure dict to Dash

    def toggle_delete_panel(  # WHY: dispatches on the button id captured in callback_context
        self,
        _delete_clicks: int,
        _cancel_clicks: int,
        _confirm_clicks: int,
        current_style: dict[str, Any],
        config: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], Any]:
        """Show or hide the delete confirmation panel and update map name."""
        import dash  # WHY: local import: dash.callback_context only exists at request time
        from dash import no_update  # WHY: sentinel used to skip output updates

        ctx = dash.callback_context  # WHY: Dash provides trigger info via callback_context
        if not ctx.triggered:  # WHY: no trigger => leave outputs untouched via no_update
            return current_style, no_update
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]  # WHY: component id that fired
        style, refresh_name = _delete_panel_style(button_id)  # WHY: delegate branch selection
        if style is None:  # WHY: unknown trigger => keep current style
            return current_style, no_update
        return self._delete_panel_outputs(style, refresh_name, config, no_update)  # WHY: assemble outputs

    def _delete_panel_outputs(  # WHY: extracted to shrink toggle_delete_panel and log opens
        self,
        style: dict[str, Any],
        refresh_name: bool,
        config: dict[str, Any] | None,
        no_update: Any,
    ) -> tuple[dict[str, Any], Any]:
        """Return the (style, name-display) tuple, logging on panel open."""
        if not refresh_name:  # WHY: cancel/confirm paths hide without touching the label
            return style, no_update
        current_map_name = config.get("map_name", "Unknown") if config else "Unknown"  # WHY: display name
        logging.warning(  # WHY: audit log captures who/what is being deleted
            "Delete panel opened for map '%s' (ID: %s)",
            current_map_name,
            config.get("map_id") if config else "unknown",
        )
        return style, f"Map: {current_map_name}"  # WHY: refresh the panel header

    def toggle_clone_panel(  # WHY: dispatches on the button id captured in callback_context
        self,
        _clone_clicks: int,
        _cancel_clicks: int,
        _execute_clicks: int,
        current_style: dict[str, Any],
    ) -> dict[str, Any]:
        """Show or hide the clone input panel."""
        import dash  # WHY: local import: dash.callback_context only exists at request time

        ctx = dash.callback_context  # WHY: Dash provides trigger info via callback_context
        if not ctx.triggered:  # WHY: no trigger => leave the style dict unchanged
            return current_style
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]  # WHY: component id that fired
        style = _clone_panel_style(button_id)  # WHY: delegate branch selection
        if style is None:  # WHY: unknown trigger => keep current style
            return current_style
        if button_id == "clone-btn":  # WHY: only log when the user is opening the panel
            logging.info("Clone panel opened for map %s", self._state.map_id)  # WHY: audit trail
        return style  # WHY: return the resolved style dict

    def handle_utilities(
        self,
        _auto_zone_clicks: int,
        _change_clicks: int,
        _remove_clicks: int,
        _rename_clicks: int,
    ) -> Any:
        """Handle utilities button clicks."""
        import dash  # WHY: local import: dash.callback_context only exists at request time
        from dash import html  # WHY: html.Span for status output

        ctx = dash.callback_context  # WHY: Dash provides trigger info via callback_context
        if not ctx.triggered:  # WHY: no trigger => render empty status
            return ""
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]  # WHY: component id that fired
        response = _UTILITY_RESPONSES.get(button_id)  # WHY: static dispatch keeps CC low
        if response is None:  # WHY: unknown trigger => empty status
            return ""
        return self._render_utility_response(button_id, response, html)  # WHY: extract to shrink function

    def _render_utility_response(  # WHY: extracted to keep handle_utilities small
        self,
        button_id: str,
        response: tuple[str, str, str],
        html: Any,
    ) -> Any:
        """Log the utility request and render the corresponding html.Span."""
        msg, color, log_level = response  # WHY: unpack the dispatch tuple
        map_id = self._state.map_id  # WHY: closure-equivalent audit key
        log_fn = logging.warning if log_level == "warning" else logging.info  # WHY: severity per action
        log_fn("Utilities: %s requested for map %s", button_id, map_id)  # WHY: audit trail per click
        style = {"color": color}  # WHY: base color from the dispatch table
        if button_id == "auto-zone-btn":  # WHY: only the info request emphasises bold text
            style["fontWeight"] = "bold"
        return html.Span(msg, style=style)  # WHY: render the status widget

    def update_shape_labels(self, relayoutData: dict[str, Any] | None, current_fig: dict[str, Any]) -> dict[str, Any]:
        """Add multi-unit measurement labels to drawn shapes."""
        if not relayoutData:  # WHY: no relayout event => nothing to annotate
            return current_fig  # WHY: return unchanged figure
        line_shapes = self._collect_line_shapes(current_fig)  # WHY: extract to shrink CC
        if not line_shapes:  # WHY: nothing to annotate
            return current_fig  # WHY: return unchanged figure
        return self._append_measurement_labels(current_fig, line_shapes)  # WHY: delegate mutation

    def _collect_line_shapes(self, current_fig: dict[str, Any]) -> list[dict[str, Any]]:  # WHY: extract for CC
        """Return the list of user-drawn line shapes from the figure layout."""
        shapes = current_fig.get("layout", {}).get("shapes", [])  # WHY: user-drawn shapes list
        return [s for s in shapes if s.get("type") == "line"]  # WHY: filter narrows loop scope

    def _append_measurement_labels(  # WHY: extract mutation loop to shrink update_shape_labels
        self, current_fig: dict[str, Any], line_shapes: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Append multi-unit annotation dicts for every line shape into the figure."""
        current_ppm = current_fig.get("layout", {}).get("meta", {}).get("ppm", self._state.ppm)  # WHY: latest PPM
        annotations = current_fig.setdefault("layout", {}).setdefault("annotations", [])  # WHY: ensure list exists
        for shape in line_shapes:  # WHY: bounded by user-drawn ruler count
            annotations.append(_measurement_annotation(shape, current_ppm))  # WHY: append the new label
        return current_fig  # WHY: return mutated figure dict to Dash

    def set_origin_from_click(
        self,
        clickData: dict[str, Any] | None,
        mode_clicks: int | None,
        current_fig: dict[str, Any],
    ) -> tuple[Any, dict[str, Any]]:
        """Set origin point when map is clicked in origin-setting mode."""
        from dash import html  # WHY: html.P for status output

        if not mode_clicks or mode_clicks % 2 == 0:  # WHY: mode is inactive (even clicks)
            return self._render_origin_current(current_fig, html), current_fig
        if not clickData:  # WHY: mode active but user hasn't clicked yet
            prompt = html.P("Click map to set origin", style=_ORIGIN_PROMPT_STYLE)  # WHY: prompt widget
            return [prompt], current_fig
        return self._apply_origin_click(clickData, current_fig, html)  # WHY: extract to keep function short

    @staticmethod
    def _render_origin_current(current_fig: dict[str, Any], html: Any) -> list[Any]:
        """Render the "current origin" gray label shown when mode is inactive."""
        meta = current_fig.get("layout", {}).get("meta", {})  # WHY: read persisted origin
        origin_x = meta.get("origin_x", 0)  # WHY: default when origin never set
        origin_y = meta.get("origin_y", 0)  # WHY: default when origin never set
        return [html.P(f"Current: ({origin_x}, {origin_y})", style=_ZONE_META_STYLE)]  # WHY: gray label widget

    def _apply_origin_click(
        self, clickData: dict[str, Any], current_fig: dict[str, Any], html: Any
    ) -> tuple[list[Any], dict[str, Any]]:
        """Persist the clicked point as the origin and refresh crosshair traces."""
        point = clickData["points"][0]  # WHY: first clicked point carries the coordinates
        origin = _OriginPoint(x=point["x"], y=point["y"])  # WHY: bundle for downstream helpers
        _persist_origin(current_fig, origin)  # WHY: write into layout.meta
        self._update_origin_traces(current_fig, origin.x, origin.y)  # WHY: refresh crosshair traces
        logging.info("Map origin updated to (%.1f, %.1f)", origin.x, origin.y)  # WHY: preserve audit log
        status = [  # WHY: confirmation widgets shown to the user
            html.P(f"[OK] Origin set: ({origin.x:.1f}, {origin.y:.1f})", style=_ORIGIN_OK_STYLE),
            html.P("Click button again to exit mode", style=_ORIGIN_HINT_STYLE),
        ]
        return status, current_fig

    @staticmethod
    def _update_origin_traces(current_fig: dict[str, Any], new_origin_x: float, new_origin_y: float) -> None:
        """Update the Origin / Origin Point / vertical crosshair traces in place."""
        origin = _OriginPoint(x=new_origin_x, y=new_origin_y)  # WHY: bundle for per-trace helpers
        for trace in current_fig["data"]:  # WHY: walk every trace looking for origin markers
            updater = _select_origin_updater(trace)  # WHY: classify the trace once
            if updater is not None:  # WHY: only mutate matched origin traces
                updater(trace, origin)

    def execute_delete_map(
        self,
        confirm_clicks: int,
        cache_bust_data: dict[str, Any] | None,
        config: dict[str, Any] | None,
    ) -> tuple[Any, Any]:
        """Actually delete the map via Mist API - creates backup first."""
        from dash import html, no_update  # WHY: local import keeps module import-light

        if not confirm_clicks:  # WHY: user hasn't actually confirmed the delete
            return "", no_update
        current_trigger = cache_bust_data.get("trigger", 0) if cache_bust_data else 0  # WHY: cache-bust counter
        resolved = self._resolve_delete_config(config)  # WHY: pack site/map/name into a value object
        try:
            return self._invoke_map_delete(resolved, current_trigger)  # WHY: happy path returns tuple
        except Exception as delete_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.exception("Error deleting map: %s", delete_error)  # WHY: capture stack trace
            return html.Span(f"Error: {str(delete_error)[:50]}", style={"color": "#ff4444"}), no_update

    def _resolve_delete_config(self, config: dict[str, Any] | None) -> _DeleteMapConfig:
        """Build a _DeleteMapConfig from the Dash store or fall back to state."""
        site_id = config.get("site_id") if config else self._state.site_id  # WHY: prefer store value
        map_id = config.get("map_id") if config else self._state.map_id  # WHY: prefer store value
        map_name = config.get("map_name", "Unknown") if config else "Unknown"  # WHY: display fallback
        return _DeleteMapConfig(site_id=site_id, map_id=map_id, map_name=map_name)

    def _invoke_map_delete(self, resolved: _DeleteMapConfig, current_trigger: int) -> tuple[Any, Any]:
        """Backup, call Mist deleteSiteMap, and render the response."""
        self._backup_before_delete(resolved.site_id, resolved.map_id, resolved.map_name)  # WHY: safety net
        logging.warning(  # WHY: destructive-operation audit log
            "DESTRUCTIVE: Deleting map '%s' (ID: %s) from site %s",
            resolved.map_name,
            resolved.map_id,
            resolved.site_id,
        )
        delete_response = self._state.mistapi_ref.api.v1.sites.maps.deleteSiteMap(  # WHY: Mist API mutation
            self._state.api_session_ref, site_id=resolved.site_id, map_id=resolved.map_id
        )
        return self._render_delete_result(delete_response, resolved.map_name, resolved.map_id, current_trigger)

    def _backup_before_delete(self, site_id: str | None, map_id: str | None, map_name: str) -> Any:
        """Run pre-delete backup and log the outcome; return backup path or None."""
        logging.info("Creating safety backup before deleting map '%s'", map_name)  # WHY: audit trail
        backup_path = self._state.maps_manager_ref._backup_map_geometry(  # WHY: MapsManager helper
            api_session=self._state.api_session_ref,
            site_id=site_id,
            map_id=map_id,
            map_name=map_name,
            backup_reason="pre_delete",
        )
        if backup_path:  # WHY: backup succeeded
            logging.info("Pre-delete backup saved: %s", backup_path)  # WHY: path for operator recovery
        else:
            logging.warning("Pre-delete backup failed - proceeding with deletion anyway")  # WHY: non-fatal
        return backup_path  # WHY: return for caller (currently informational only)

    @staticmethod
    def _render_delete_result(
        delete_response: Any,
        map_name: str,
        map_id: str | None,
        current_trigger: int,
    ) -> tuple[Any, Any]:
        """Render the Dash output based on the Mist API delete response."""
        from dash import html, no_update  # WHY: local import keeps module import-light

        if delete_response.status_code in _SUCCESS_STATUSES:  # WHY: HTTP success codes
            logging.info("Map '%s' (ID: %s) deleted successfully", map_name, map_id)  # WHY: audit success
            new_cache_bust = {"trigger": current_trigger + 1}  # WHY: increment invalidates caches
            msg = f"Map '{map_name}' deleted! Close this browser tab."  # WHY: user prompt
            style = {"color": "#00ff88", "fontWeight": "bold"}  # WHY: green success color
            return html.Span(msg, style=style), new_cache_bust
        logging.error("Map deletion failed: HTTP %s", delete_response.status_code)  # WHY: audit failure
        err = html.Span(f"Delete failed: HTTP {delete_response.status_code}", style={"color": "#ff4444"})
        return err, no_update

    def handle_zone_actions(
        self,
        _edit_clicks: int,
        _remove_clicks: int,
        clickData: dict[str, Any] | None,
        selected_zone_data: dict[str, Any] | None,
    ) -> tuple[Any, dict[str, Any]]:
        """Handle zone edit/remove and display selected zone info."""
        import dash  # WHY: local import: dash.callback_context only exists at request time
        from dash import html  # WHY: html widgets for status output

        current_zone = selected_zone_data or {"zone_id": None, "zone_name": None}  # WHY: defensive default
        ctx = dash.callback_context  # WHY: Dash provides trigger info via callback_context
        if not ctx.triggered:  # WHY: no trigger => render default prompt
            return html.P("Click a zone for details", style=_ZONE_PROMPT_STYLE), current_zone
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]  # WHY: component id that fired
        return self._dispatch_zone_action(trigger_id, clickData, current_zone, html)  # WHY: static dispatch

    def _dispatch_zone_action(  # WHY: extracted to keep handle_zone_actions small and CC low
        self,
        trigger_id: str,
        clickData: dict[str, Any] | None,
        current_zone: dict[str, Any],
        html: Any,
    ) -> tuple[Any, dict[str, Any]]:
        """Dispatch a zone-action trigger to the appropriate handler."""
        if trigger_id == "edit-zone-btn":  # WHY: user clicked Edit
            return self._handle_zone_edit(current_zone)
        if trigger_id == "remove-zone-btn":  # WHY: user clicked Remove
            return self._handle_zone_remove(current_zone)
        if trigger_id == "map-display" and clickData:  # WHY: user clicked a zone on the map
            return self._handle_zone_click(clickData, current_zone)
        return html.P("Click a zone for details", style=_ZONE_PROMPT_STYLE), current_zone  # WHY: fallback

    def _handle_zone_edit(self, current_zone: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        """Render the edit-zone response panel."""
        from dash import html  # WHY: html widgets for status output

        if not current_zone.get("zone_id"):  # WHY: no zone selected
            return self._render_zone_not_selected(current_zone)  # WHY: prompt user to select one
        logging.info(  # WHY: audit trail per edit request
            "Zone management: Edit zone %s requested for map %s",
            current_zone.get("zone_name"),
            self._state.map_id,
        )
        title_style = {"fontSize": "11px", "color": "#667eea", "fontWeight": "bold"}  # WHY: bold purple
        title = html.P(f"Pencil Edit Zone: {current_zone.get('zone_name', 'Unknown')}", style=title_style)
        hint = html.P("Use Mist Dashboard to modify zone shape", style=_ZONE_HINT_STYLE)  # WHY: pointer
        return html.Div([title, hint]), current_zone  # WHY: keep current selection

    def _handle_zone_remove(self, current_zone: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        """Delete the selected zone via Mist API and render the result."""
        from dash import html  # WHY: html widgets for status output

        if not current_zone.get("zone_id"):  # WHY: no zone selected
            return self._render_zone_not_selected(current_zone)  # WHY: prompt user to select one
        zone_id = current_zone.get("zone_id")  # WHY: zone UUID for the API delete
        zone_name = current_zone.get("zone_name", "Unknown")  # WHY: display name for logs
        logging.warning(  # WHY: destructive-action audit log
            "Zone management: Deleting zone %s (ID: %s) from site %s",
            zone_name,
            zone_id,
            self._state.site_id,
        )
        try:
            delete_response = self._state.mistapi_ref.api.v1.sites.zones.deleteSiteZone(  # WHY: Mist API
                self._state.api_session_ref, site_id=self._state.site_id, zone_id=zone_id
            )
            return self._render_zone_delete_result(delete_response, zone_name, current_zone)
        except Exception as del_error:  # noqa: BLE001 - preserve original broad-except behavior
            return self._render_zone_delete_exception(del_error, current_zone, html)  # WHY: extract error path

    @staticmethod
    def _render_zone_delete_exception(  # WHY: extracted so _handle_zone_remove stays small
        del_error: Exception, current_zone: dict[str, Any], html: Any
    ) -> tuple[Any, dict[str, Any]]:
        """Render the error panel and log the stack trace for a zone-delete failure."""
        logging.exception("Error deleting zone: %s", del_error)  # WHY: capture stack trace
        err_style = {"fontSize": "11px", "color": "#ff4444", "fontWeight": "bold"}  # WHY: red bold
        err = html.P(f"X Error: {str(del_error)[:40]}", style=err_style)  # WHY: truncated message
        return html.Div([err]), current_zone  # WHY: keep selection so user can retry

    @staticmethod
    def _render_zone_delete_result(
        delete_response: Any, zone_name: str, current_zone: dict[str, Any]
    ) -> tuple[Any, dict[str, Any]]:
        """Render the Dash output based on the Mist API zone delete response."""
        from dash import html  # WHY: html widgets for status output

        if delete_response.status_code in _SUCCESS_STATUSES:  # WHY: HTTP success codes
            logging.info("Zone %s deleted successfully", zone_name)  # WHY: audit success
            ok_style = {"fontSize": "11px", "color": "#00ff88", "fontWeight": "bold"}  # WHY: green bold
            ok = html.P(f"[OK] Zone deleted: {zone_name}", style=ok_style)  # WHY: success message
            hint = html.P("Refresh the page to update view", style=_ZONE_HINT_STYLE)  # WHY: guidance
            return html.Div([ok, hint]), {"zone_id": None, "zone_name": None}  # WHY: clear selection
        logging.error("Zone deletion failed: HTTP %s", delete_response.status_code)  # WHY: audit failure
        err_style = {"fontSize": "11px", "color": "#ff4444", "fontWeight": "bold"}  # WHY: red bold
        err = html.P(f"X Delete failed: HTTP {delete_response.status_code}", style=err_style)
        hint = html.P("Check permissions and try again", style=_ZONE_HINT_STYLE)  # WHY: guidance
        return html.Div([err, hint]), current_zone  # WHY: keep selection on failure

    @staticmethod
    def _render_zone_not_selected(current_zone: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        """Render the 'select a zone first' prompt."""
        from dash import html  # WHY: html widgets for status output

        warn_style = {"fontSize": "11px", "color": "#ffaa00", "fontWeight": "bold"}  # WHY: amber warning
        warn = html.P("! Select a zone first", style=warn_style)  # WHY: primary line
        hint = html.P("Click on a zone in the map to select it", style=_ZONE_HINT_STYLE)  # WHY: guidance
        return html.Div([warn, hint]), current_zone  # WHY: keep selection unchanged

    def _handle_zone_click(self, clickData: dict[str, Any], current_zone: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
        """Render the response when the user clicks a zone on the map."""
        from dash import html  # WHY: html widgets for status output

        zone_name, zone_id = _extract_zone_selection(clickData, self._state.zones)  # WHY: parse hover
        if not zone_name:  # WHY: clicked something other than a zone overlay
            return html.P("Click a zone for details", style=_ZONE_PROMPT_STYLE), current_zone
        return self._render_zone_click_status(zone_name, zone_id, html)  # WHY: extract widget assembly

    @staticmethod
    def _render_zone_click_status(zone_name: str, zone_id: str | None, html: Any) -> tuple[Any, dict[str, Any]]:
        """Render the Dash widget confirming a zone was selected."""
        title_style = {  # WHY: green bold title text
            "fontSize": "12px",
            "color": "#00ff00",
            "fontWeight": "bold",
            "marginBottom": "5px",
        }
        title = html.P(f">> Selected: {zone_name}", style=title_style)  # WHY: primary confirmation line
        id_text = f"ID: {zone_id[:8] if zone_id else 'Unknown'}..."  # WHY: truncated ID for display
        subline = html.P(id_text, style=_ZONE_HINT_STYLE)  # WHY: gray hint style
        return html.Div([title, subline]), {"zone_id": zone_id, "zone_name": zone_name}

    # ------------------------------------------------------------------
    # Wiring: bind every UI callback in this cluster to ``app.callback``
    # ------------------------------------------------------------------

    def register(self, app: Dash) -> None:  # WHY: hooks this wave's app.callback(...) blocks into Dash
        """Attach the UI-toggle callbacks in this cluster to ``app``."""
        from dash import Input, Output, State  # WHY: local import keeps module import-light

        self._register_wave_a(app, Input, Output, State)  # WHY: split by wave keeps register() small
        self._register_wave_b(app, Input, Output, State)  # WHY: wave B toggles/panels/utilities
        self._register_wave_c(app, Input, Output, State)  # WHY: wave C shape/origin/delete/zone

    def _register_wave_a(self, app: Dash, Input: Any, Output: Any, State: Any) -> None:
        """Register wave-A callbacks (click details / origin mode / zone-name / auto-refresh)."""
        self._bind_click_data(app, Input, Output)  # WHY: display_click_data binding
        self._bind_origin_mode(app, Input, Output, State)  # WHY: toggle_origin_mode binding
        self._bind_zone_name_input(app, Input, Output)  # WHY: toggle_zone_name_input binding
        self._bind_auto_refresh(app, Input, Output)  # WHY: toggle_auto_refresh binding

    def _bind_click_data(self, app: Dash, Input: Any, Output: Any) -> None:  # WHY: extract to shrink wave-A
        """Bind the display_click_data callback."""
        app.callback(  # WHY: Plotly clickData -> details panel children
            Output("click-data", "children"),
            Input("map-display", "clickData"),
        )(self.display_click_data)

    def _bind_origin_mode(
        self, app: Dash, Input: Any, Output: Any, State: Any
    ) -> None:  # WHY: extract to shrink wave-A
        """Bind the toggle_origin_mode callback."""
        app.callback(  # WHY: parity-based origin-mode toggle
            Output("origin-mode-button", "style"),
            Input("origin-mode-button", "n_clicks"),
            State("origin-mode-button", "style"),
            prevent_initial_call=True,
        )(self.toggle_origin_mode)

    def _bind_zone_name_input(self, app: Dash, Input: Any, Output: Any) -> None:  # WHY: extract to shrink wave-A
        """Bind the toggle_zone_name_input callback."""
        app.callback(  # WHY: show zone-name field only in zone mode
            Output("zone-name-container", "style"),
            Input("drawing-mode-dropdown", "value"),
            prevent_initial_call=True,
        )(self.toggle_zone_name_input)

    def _bind_auto_refresh(self, app: Dash, Input: Any, Output: Any) -> None:  # WHY: extract to shrink wave-A
        """Bind the toggle_auto_refresh callback."""
        app.callback(  # WHY: drives 3 dcc.Interval flags + countdown label
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

    def _register_wave_b(self, app: Dash, Input: Any, Output: Any, State: Any) -> None:
        """Register wave-B callbacks (zone toggle / delete panel / clone panel / utilities)."""
        self._bind_zone_toggle(app, Input, Output, State)  # WHY: toggle_individual_zones binding
        self._bind_delete_panel(app, Input, Output, State)  # WHY: toggle_delete_panel binding
        self._bind_clone_panel(app, Input, Output, State)  # WHY: toggle_clone_panel binding
        self._bind_utilities(app, Input, Output)  # WHY: handle_utilities binding

    def _bind_zone_toggle(
        self, app: Dash, Input: Any, Output: Any, State: Any
    ) -> None:  # WHY: extract to shrink wave-B
        """Bind the toggle_individual_zones callback."""
        app.callback(  # WHY: flips visibility on Zone: traces
            Output("map-display", "figure", allow_duplicate=True),
            Input("zone-toggle", "value"),
            State("map-display", "figure"),
            prevent_initial_call=True,
        )(self.toggle_individual_zones)

    def _bind_delete_panel(
        self, app: Dash, Input: Any, Output: Any, State: Any
    ) -> None:  # WHY: extract to shrink wave-B
        """Bind the toggle_delete_panel callback."""
        app.callback(  # WHY: dispatches on callback_context trigger id
            [Output("delete-panel", "style"), Output("delete-map-name-display", "children")],
            [
                Input("delete-btn", "n_clicks"),
                Input("cancel-delete-btn", "n_clicks"),
                Input("confirm-delete-btn", "n_clicks"),
            ],
            [State("delete-panel", "style"), State("map-config-store", "data")],
            prevent_initial_call=True,
        )(self.toggle_delete_panel)

    def _bind_clone_panel(
        self, app: Dash, Input: Any, Output: Any, State: Any
    ) -> None:  # WHY: extract to shrink wave-B
        """Bind the toggle_clone_panel callback."""
        app.callback(  # WHY: dispatches on callback_context trigger id
            Output("clone-panel", "style"),
            [
                Input("clone-btn", "n_clicks"),
                Input("cancel-clone-btn", "n_clicks"),
                Input("execute-clone-btn", "n_clicks"),
            ],
            [State("clone-panel", "style")],
            prevent_initial_call=True,
        )(self.toggle_clone_panel)

    def _bind_utilities(self, app: Dash, Input: Any, Output: Any) -> None:  # WHY: extract to shrink wave-B
        """Bind the handle_utilities callback."""
        app.callback(  # WHY: routes 4 utilities buttons to status widgets
            Output("utilities-status", "children"),
            [
                Input("auto-zone-btn", "n_clicks"),
                Input("change-image-btn", "n_clicks"),
                Input("remove-image-btn", "n_clicks"),
                Input("rename-btn", "n_clicks"),
            ],
            prevent_initial_call=True,
        )(self.handle_utilities)

    def _register_wave_c(self, app: Dash, Input: Any, Output: Any, State: Any) -> None:
        """Register wave-C callbacks (shape labels / origin click / delete map / zone actions)."""
        self._bind_shape_labels(app, Input, Output, State)  # WHY: update_shape_labels binding
        self._bind_origin_click(app, Input, Output, State)  # WHY: set_origin_from_click binding
        self._bind_execute_delete(app, Input, Output, State)  # WHY: execute_delete_map binding
        self._bind_zone_actions(app, Input, Output, State)  # WHY: handle_zone_actions binding

    def _bind_shape_labels(
        self, app: Dash, Input: Any, Output: Any, State: Any
    ) -> None:  # WHY: extract to shrink wave-C
        """Bind the update_shape_labels callback."""
        app.callback(  # WHY: multi-unit annotation on drawn lines
            Output("map-display", "figure", allow_duplicate=True),
            Input("map-display", "relayoutData"),
            State("map-display", "figure"),
            prevent_initial_call=True,
        )(self.update_shape_labels)

    def _bind_origin_click(
        self, app: Dash, Input: Any, Output: Any, State: Any
    ) -> None:  # WHY: extract to shrink wave-C
        """Bind the set_origin_from_click callback."""
        app.callback(  # WHY: map click sets origin in origin mode
            [Output("origin-status", "children"), Output("map-display", "figure", allow_duplicate=True)],
            Input("map-display", "clickData"),
            [State("origin-mode-button", "n_clicks"), State("map-display", "figure")],
            prevent_initial_call=True,
        )(self.set_origin_from_click)

    def _bind_execute_delete(
        self, app: Dash, Input: Any, Output: Any, State: Any
    ) -> None:  # WHY: extract to shrink wave-C
        """Bind the execute_delete_map callback."""
        app.callback(  # WHY: backup + Mist API deleteSiteMap
            [Output("delete-status", "children"), Output("cache-bust-store", "data", allow_duplicate=True)],
            Input("confirm-delete-btn", "n_clicks"),
            [State("cache-bust-store", "data"), State("map-config-store", "data")],
            prevent_initial_call=True,
        )(self.execute_delete_map)

    def _bind_zone_actions(
        self, app: Dash, Input: Any, Output: Any, State: Any
    ) -> None:  # WHY: extract to shrink wave-C
        """Bind the handle_zone_actions callback."""
        app.callback(  # WHY: edit/remove/click zone selection
            [Output("selected-zone-info", "children"), Output("selected-zone-store", "data")],
            [
                Input("edit-zone-btn", "n_clicks"),
                Input("remove-zone-btn", "n_clicks"),
                Input("map-display", "clickData"),
            ],
            [State("selected-zone-store", "data")],
            prevent_initial_call=True,
        )(self.handle_zone_actions)


def _select_origin_updater(  # WHY: pure classifier flattens nested branching in _update_origin_traces
    trace: dict[str, Any],
) -> Callable[[dict[str, Any], _OriginPoint], None] | None:
    """Return the per-trace updater callable for an origin trace, or None."""
    name = trace.get("name")  # WHY: named origin traces get direct dispatch
    if name == "Origin":  # WHY: horizontal crosshair trace
        return _update_horizontal_origin
    if name == "Origin Point":  # WHY: center dot marker
        return _update_origin_point
    if _is_vertical_origin_trace(trace):  # WHY: unnamed vertical crosshair identified by hovertext
        return _update_vertical_origin
    return None  # WHY: unrelated trace => leave untouched
