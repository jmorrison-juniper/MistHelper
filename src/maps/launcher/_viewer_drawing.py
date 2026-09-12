"""Drawing-tools cluster extracted from ``viewer_callbacks.py``.

Owns the single Wave-E1 public callback ``handle_drawing_tools`` plus
its private helpers (dispatcher + save/delete branches for shapes,
zones, wayfinding, walls, validation paths).  Follows the same
wrapper-class + ``__getattr__`` template used by
:mod:`src.capture._packet_capture_org` so the parent
:class:`~src.maps.launcher.viewer_callbacks.MapViewerCallbacks` stays a
thin coordinator that hands each Dash callback off to the appropriate
cluster.
"""

from __future__ import annotations  # WHY: postponed evaluation consistent with parent module

import logging  # WHY: audit trail for drawing-tool diagnostics
import uuid  # WHY: unique ids for new validation paths
from dataclasses import dataclass  # WHY: group related parameters into frozen configs
from typing import TYPE_CHECKING, Any  # WHY: opaque manager + type-permissive Dash callback args

if TYPE_CHECKING:  # WHY: keep dash imports lazy at runtime
    from collections.abc import Callable  # WHY: type hint for dispatch table values

    from dash import Dash  # WHY: annotation reference for register(app)


@dataclass(frozen=True, slots=True)
class _DrawingConfig:  # WHY: bundle Mist context passed to every save/delete branch
    """Bundle site/map/PPM/cache-bust trigger for drawing operations."""

    site_id: str | None  # WHY: Mist site scope for API writes
    map_id: str | None  # WHY: Mist map scope for API writes
    ppm: float  # WHY: pixels-per-meter conversion factor
    current_trigger: int  # WHY: cache-bust counter to force map reload


@dataclass(frozen=True, slots=True)
class _ShapeSaveRequest:  # WHY: bundle save-shape inputs consumed by dispatcher
    """Bundle mode + zone name + figure for save-shape dispatch."""

    drawing_mode: str | None  # WHY: which save branch to invoke
    zone_name: str | None  # WHY: required for zone saves
    current_fig: dict[str, Any]  # WHY: Plotly figure containing drawn shapes


@dataclass(frozen=True, slots=True)
class _SaveResultSpec:  # WHY: bundle rendering metadata for save-shape responses
    """Bundle rendering metadata for a save-shape API response."""

    success_msg: str  # WHY: user-facing success text
    failure_prefix: str  # WHY: prefix for failure Span
    audit_success: str  # WHY: log message on success
    audit_failure: str  # WHY: log message on failure
    success_codes: tuple[int, ...]  # WHY: HTTP codes considered a successful save


@dataclass(frozen=True, slots=True)
class _MapResetSpec:  # WHY: bundle payload + audit strings for map-reset delete ops
    """Bundle payload + audit strings for a map-reset delete op."""

    payload: dict[str, Any]  # WHY: updateSiteMap body to zero the collection
    click_label: str  # WHY: pre-call audit label ("Delete paths"/"Delete wayfinding")
    success_msg: str  # WHY: user-facing success text
    success_log: str  # WHY: post-success log format string
    failure_prefix: str  # WHY: prefix for failure Span
    error_context: str  # WHY: exception-branch log context word


class _ViewerDrawing:  # WHY: wrapper class hosting the drawing-tools callback cluster
    """Cluster class holding the extracted handle_drawing_tools body + helpers."""

    def __init__(self, manager: Any) -> None:  # WHY: bind parent so __getattr__ can proxy shared state
        """Store the parent MapViewerCallbacks for delegate lookups."""
        self._mm = manager  # WHY: enable __getattr__ delegation back to the parent class

    def __getattr__(self, name: str) -> Any:  # WHY: transparent proxy for shared state access
        """Delegate unknown attributes to the wrapped parent manager."""
        mm = self.__dict__.get("_mm")  # WHY: guard against half-initialized instances
        if mm is None:  # WHY: only trips during broken init. Avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly
        return getattr(mm, name)  # WHY: forward all other attributes to parent

    # ------------------------------------------------------------------
    # Extracted callback body + helpers (wave E1 drawing-tools cluster)
    # ------------------------------------------------------------------

    def handle_drawing_tools(self, *args: Any) -> tuple[Any, Any]:  # WHY: Wave-E1 public Dash callback entry
        """Handle drawing tool actions - save shapes to Mist or delete from Mist."""
        import dash  # WHY: dash.callback_context only exists at request time
        from dash import no_update  # WHY: keep import light at module load

        ctx = dash.callback_context  # WHY: Dash exposes trigger info via callback_context
        if not ctx.triggered:  # WHY: no trigger => no-op
            return "", no_update  # WHY: empty Span + no cache-bust change
        _s, _c, dp_clicks, _dw, dwl_clicks, _dz, mode, zone, fig, cfg, cache = args  # WHY: unpack 11 Dash args
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]  # WHY: component id that fired
        logging.info(  # WHY: audit which button fired and the click counts
            "Drawing tools callback triggered: button_id=%s, del_path_clicks=%s, del_wall_clicks=%s",
            button_id,
            dp_clicks,
            dwl_clicks,
        )
        drawing_cfg = self._resolve_drawing_config(cfg, cache)  # WHY: build config dataclass from raw stores
        request = _ShapeSaveRequest(drawing_mode=mode, zone_name=zone, current_fig=fig or {})  # WHY: save inputs
        return self._dispatch_drawing_button(button_id, request, drawing_cfg)  # WHY: route to per-button handler

    def _resolve_drawing_config(
        self, raw_config: dict[str, Any] | None, raw_cache_bust: dict[str, Any] | None
    ) -> _DrawingConfig:  # WHY: merge Dash state stores with parent-state fallbacks
        """Merge Dash state stores with fallbacks from the parent state singleton."""
        site_id, map_id, ppm = self._resolve_site_map_ppm(raw_config)  # WHY: extract site/map/ppm via helper
        current_trigger = (raw_cache_bust or {}).get("trigger", 0)  # WHY: cache-bust counter default 0
        return _DrawingConfig(  # WHY: build immutable config carrier
            site_id=site_id, map_id=map_id, ppm=ppm, current_trigger=current_trigger
        )

    def _resolve_site_map_ppm(
        self, raw_config: dict[str, Any] | None
    ) -> tuple[str | None, str | None, float]:  # WHY: split fallback chain to keep CC low
        """Return (site_id, map_id, ppm) resolved from Dash config with parent-state fallbacks."""
        cfg = raw_config or {}  # WHY: single normalization for downstream .get calls
        site_id = cfg.get("site_id") or self._state.site_id  # WHY: prefer config-store value
        map_id = cfg.get("map_id") or self._state.map_id  # WHY: prefer config-store value
        ppm = cfg.get("ppm", self._state.ppm) if raw_config else self._state.ppm  # WHY: PPM fallback
        return site_id, map_id, ppm  # WHY: hand three-tuple back to caller

    def _dispatch_drawing_button(
        self, button_id: str, request: _ShapeSaveRequest, cfg: _DrawingConfig
    ) -> tuple[Any, Any]:
        """Route a drawing-tool button click to its specific handler."""
        from dash import no_update  # WHY: default fall-through response for unknown buttons

        table = self._button_dispatch_table(request, cfg)  # WHY: build id->handler map for O(1) lookup
        handler = table.get(button_id)  # WHY: dict lookup keeps CC flat
        if handler is None:  # WHY: unknown button id => silent no-op
            return "", no_update  # WHY: preserve original blank fall-through
        return handler()  # WHY: invoke the resolved zero-arg lambda handler

    def _button_dispatch_table(
        self, request: _ShapeSaveRequest, cfg: _DrawingConfig
    ) -> dict[str, Callable[[], tuple[Any, Any]]]:
        """Return the button-id -> handler map used by the dispatcher."""
        return {  # WHY: each entry captures request/cfg via closure for zero-arg call site
            "clear-drawings-btn": self._local_clear_message,  # WHY: local-only clear (no Mist call)
            "save-shape-btn": lambda: self._handle_save_shape(request, cfg),  # WHY: persist last drawn shape
            "delete-paths-btn": lambda: self._delete_validation_paths(cfg),  # WHY: wipe sitesurvey_path
            "delete-wayfinding-btn": lambda: self._delete_wayfinding_paths(cfg),  # WHY: wipe wayfinding_path
            "delete-walls-btn": lambda: self._delete_walls(cfg),  # WHY: wipe wall_path
            "delete-zones-btn": lambda: self._delete_all_zones(cfg),  # WHY: delete every zone on this map
        }

    @staticmethod
    def _local_clear_message() -> tuple[Any, Any]:
        """Return the local-only clear hint (no Mist call)."""
        from dash import html, no_update  # WHY: Dash components only needed on this branch

        msg = "Use the eraser tool in the toolbar to clear drawings from the map"  # WHY: user guidance
        logging.info("Drawing tool: Clear local drawings requested")  # WHY: audit user action
        return html.Span(msg, style={"color": "#ffc107"}), no_update  # WHY: yellow hint + no cache bump

    def _handle_save_shape(self, request: _ShapeSaveRequest, cfg: _DrawingConfig) -> tuple[Any, Any]:
        """Persist the last drawn shape according to the active drawing mode."""
        from dash import html, no_update  # WHY: html.Span + no_update needed for empty/error branches

        shapes = request.current_fig.get("layout", {}).get("shapes", [])  # WHY: Plotly shapes list
        if not shapes:  # WHY: nothing drawn yet
            return (
                html.Span("No shapes drawn. Use toolbar to draw first.", style={"color": "#ff6666"}),
                no_update,
            )
        last_shape = shapes[-1]  # WHY: most-recently drawn shape
        try:
            return self._dispatch_save_by_mode(last_shape, request, cfg)  # WHY: pick per-mode handler
        except Exception as save_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.exception("Drawing tool: Error saving shape - %s", save_error)  # WHY: audit failure
            return html.Span(f"Error: {str(save_error)[:50]}", style={"color": "#ff4444"}), no_update

    def _dispatch_save_by_mode(
        self, last_shape: dict[str, Any], request: _ShapeSaveRequest, cfg: _DrawingConfig
    ) -> tuple[Any, Any]:
        """Route by drawing_mode to the correct save-shape branch."""
        from dash import html, no_update  # WHY: measurement branch needs Span + no_update

        mode = request.drawing_mode  # WHY: extract once for readability
        if mode == "zone":  # WHY: persist as a Mist zone
            return self._save_zone_shape(last_shape, request, cfg)
        if mode == "wall":  # WHY: append to wall_path
            return self._save_wall_shape(last_shape, cfg)
        if mode == "path":  # WHY: append to sitesurvey_path
            return self._save_validation_path_shape(last_shape, cfg)
        return (  # WHY: measurement mode is not persisted
            html.Span("Measurement mode - shapes not saved to Mist", style={"color": "#888"}),
            no_update,
        )

    def _save_zone_shape(
        self, last_shape: dict[str, Any], request: _ShapeSaveRequest, cfg: _DrawingConfig
    ) -> tuple[Any, Any]:  # WHY: persist a rectangle shape as a Mist zone
        """Persist a rectangle shape as a Mist zone."""
        from dash import html, no_update  # WHY: guard-clause responses use Span + no_update

        zone_name = request.zone_name  # WHY: extract once for readability
        if not zone_name:  # WHY: required field for zone creation
            return html.Span("Please enter a zone name first", style={"color": "#ff6666"}), no_update
        if last_shape.get("type", "unknown") != "rect":  # WHY: Mist zones must be rectangles via this UI
            return (
                html.Span("Zones require rectangle shapes. Use Draw Rectangle tool.", style={"color": "#ff6666"}),
                no_update,
            )
        return self._persist_zone_and_render(last_shape, zone_name, cfg)  # WHY: happy path via helper

    def _persist_zone_and_render(
        self, last_shape: dict[str, Any], zone_name: str, cfg: _DrawingConfig
    ) -> tuple[Any, Any]:  # WHY: split zone POST + rendering from guard clauses
        """Build the zone payload, POST to Mist, and render the response Span."""
        zone_data = self._build_zone_payload(last_shape, zone_name, cfg.map_id, cfg.ppm)  # WHY: shape -> API body
        logging.info("Drawing tool: Creating zone '%s' at site %s", zone_name, cfg.site_id)  # WHY: audit start
        response = self._state.mistapi_ref.api.v1.sites.zones.createSiteZone(  # WHY: Mist API write
            self._state.api_session_ref, cfg.site_id, zone_data
        )
        spec = _SaveResultSpec(  # WHY: rendering metadata for the response branch
            success_msg=f"Zone '{zone_name}' saved to Mist!",
            failure_prefix="Failed to save zone",
            audit_success=f"Drawing tool: Zone '{zone_name}' created successfully",
            audit_failure="Drawing tool: Failed to create zone",
            success_codes=(200, 201),
        )
        return self._render_save_result(response, spec, cfg.current_trigger)  # WHY: render Dash output

    @staticmethod
    def _build_zone_payload(
        last_shape: dict[str, Any], zone_name: str, map_id: str | None, ppm: float
    ) -> dict[str, Any]:
        """Convert a rect shape's pixel corners into a Mist zone payload in meters."""
        x0 = last_shape.get("x0", 0) / ppm  # WHY: top-left X in meters
        y0 = last_shape.get("y0", 0) / ppm  # WHY: top-left Y in meters
        x1 = last_shape.get("x1", 0) / ppm  # WHY: bottom-right X in meters
        y1 = last_shape.get("y1", 0) / ppm  # WHY: bottom-right Y in meters
        vertices = [  # WHY: Mist zones store 4 corner vertices
            {"x": x0, "y": y0},
            {"x": x1, "y": y0},
            {"x": x1, "y": y1},
            {"x": x0, "y": y1},
        ]
        return {"name": zone_name, "map_id": map_id, "vertices": vertices}  # WHY: complete Mist zone payload

    def _save_wall_shape(self, last_shape: dict[str, Any], cfg: _DrawingConfig) -> tuple[Any, Any]:
        """Append a wall segment (line) to the map's wall_path."""
        from dash import html, no_update  # WHY: guard-clause response uses Span + no_update

        if last_shape.get("type", "unknown") != "line":  # WHY: walls must be lines
            return (
                html.Span("Walls require line shapes. Use Draw Line tool.", style={"color": "#ff6666"}),
                no_update,
            )
        return self._persist_wall_and_render(last_shape, cfg)  # WHY: happy path via helper

    def _persist_wall_and_render(
        self, last_shape: dict[str, Any], cfg: _DrawingConfig
    ) -> tuple[Any, Any]:  # WHY: split wall PATCH + rendering from guard clause
        """Build wall update payload, PATCH to Mist, and render the response Span."""
        x0, y0, x1, y1 = self._extract_wall_endpoints(last_shape)  # WHY: pixel coords, not meters
        logging.info(  # WHY: audit segment coordinates
            "Drawing tool: Saving wall segment from (%.1f, %.1f) to (%.1f, %.1f) pixels", x0, y0, x1, y1
        )
        existing_wall_path = self._fetch_existing_wall_path(cfg)  # WHY: read-modify-write pattern
        update_data = self._build_wall_update(x0, y0, x1, y1, existing_wall_path)  # WHY: append + rebuild
        response = self._state.mistapi_ref.api.v1.sites.maps.updateSiteMap(  # WHY: Mist API write
            self._state.api_session_ref, cfg.site_id, cfg.map_id, update_data
        )
        spec = _SaveResultSpec(  # WHY: rendering metadata for the response branch
            success_msg="Wall segment saved to Mist!",
            failure_prefix="Failed to save wall",
            audit_success="Drawing tool: Wall segment added successfully",
            audit_failure="Drawing tool: Failed to save wall",
            success_codes=(200,),
        )
        return self._render_save_result(response, spec, cfg.current_trigger)  # WHY: render Dash output

    @staticmethod
    def _extract_wall_endpoints(last_shape: dict[str, Any]) -> tuple[float, float, float, float]:
        """Return (x0, y0, x1, y1) in pixels for the drawn wall line."""
        x0 = last_shape.get("x0", 0)  # WHY: pixel x of segment start
        y0 = last_shape.get("y0", 0)  # WHY: pixel y of segment start
        x1 = last_shape.get("x1", 0)  # WHY: pixel x of segment end
        y1 = last_shape.get("y1", 0)  # WHY: pixel y of segment end
        return x0, y0, x1, y1  # WHY: hand back for logging + payload build

    def _fetch_existing_wall_path(self, cfg: _DrawingConfig) -> dict[str, Any]:
        """Fetch the map's current wall_path so we can append to it."""
        map_response = self._state.mistapi_ref.api.v1.sites.maps.getSiteMap(  # WHY: read-before-write
            self._state.api_session_ref, cfg.site_id, cfg.map_id
        )
        existing_wall_path: dict[str, Any] = {}  # WHY: default empty wall_path container
        if hasattr(map_response, "data"):  # WHY: guard against error responses without data
            existing_wall_path = map_response.data.get("wall_path", {}) or {}  # WHY: normalize None to {}
        return existing_wall_path  # WHY: caller builds updated payload from this

    @staticmethod
    def _build_wall_update(
        x0: float, y0: float, x1: float, y1: float, existing_wall_path: dict[str, Any]
    ) -> dict[str, Any]:
        """Append a two-node wall segment to the existing wall_path structure."""
        existing_nodes = existing_wall_path.get("nodes", [])  # WHY: append to current node list
        node_count = len(existing_nodes)  # WHY: used to derive unique W<n> names
        new_nodes = [  # WHY: two-node wall segment with adjacency edge
            {
                "name": f"W{node_count}",
                "position": {"x": x0, "y": y0},
                "edges": {f"W{node_count + 1}": "wall"},
            },
            {"name": f"W{node_count + 1}", "position": {"x": x1, "y": y1}, "edges": {}},
        ]
        existing_nodes.extend(new_nodes)  # WHY: mutate list in place so returned dict shares state
        wall_path_data = {  # WHY: preserved coordinate default matches original behavior
            "coordinate": existing_wall_path.get("coordinate", "actual"),
            "nodes": existing_nodes,
        }
        return {"wall_path": wall_path_data}  # WHY: updateSiteMap payload envelope

    def _save_validation_path_shape(self, last_shape: dict[str, Any], cfg: _DrawingConfig) -> tuple[Any, Any]:
        """Append a validation path (line) to the map's sitesurvey_path list."""
        shape_type = last_shape.get("type", "unknown")  # WHY: guard-clauses branch on shape type
        early = self._validate_path_shape(shape_type)  # WHY: return early if type is unsupported
        if early is not None:  # WHY: guard-clause exit for path/other shapes
            return early
        x0, y0, x1, y1 = self._extract_path_endpoints_meters(last_shape, cfg.ppm)  # WHY: pixel -> meters
        logging.info("Drawing tool: Fetching existing sitesurvey_path before append")  # WHY: audit start
        existing_paths = self._fetch_existing_paths(cfg)  # WHY: read-modify-write pattern
        update_data = self._build_path_update(x0, y0, x1, y1, existing_paths)  # WHY: append + rebuild
        response = self._state.mistapi_ref.api.v1.sites.maps.updateSiteMap(  # WHY: Mist API write
            self._state.api_session_ref, cfg.site_id, cfg.map_id, update_data
        )
        spec = _SaveResultSpec(  # WHY: rendering metadata for the response branch
            success_msg="Validation path saved to Mist!",
            failure_prefix="Failed to save path",
            audit_success="Drawing tool: Validation path added successfully",
            audit_failure="Drawing tool: Failed to save path",
            success_codes=(200,),
        )
        return self._render_save_result(response, spec, cfg.current_trigger)  # WHY: render Dash output

    @staticmethod
    def _validate_path_shape(shape_type: str) -> tuple[Any, Any] | None:
        """Return an early Dash response for unsupported shape types, else None."""
        from dash import html, no_update  # WHY: guard-clause responses use Span + no_update

        if shape_type == "path":  # WHY: SVG paths not supported in this UI yet
            return (
                html.Span(
                    "Path saving requires SVG parsing. Use Mist Portal for complex paths.",
                    style={"color": "#ff8800"},
                ),
                no_update,
            )
        if shape_type != "line":  # WHY: anything else is unsupported
            return (
                html.Span("Paths require line shapes. Use Draw Line tool.", style={"color": "#ff6666"}),
                no_update,
            )
        return None  # WHY: signal caller to proceed with the save

    @staticmethod
    def _extract_path_endpoints_meters(last_shape: dict[str, Any], ppm: float) -> tuple[float, float, float, float]:
        """Return (x0, y0, x1, y1) in meters for the drawn validation-path line."""
        x0 = last_shape.get("x0", 0) / ppm  # WHY: pixel -> meter for segment start
        y0 = last_shape.get("y0", 0) / ppm  # WHY: pixel -> meter for segment start
        x1 = last_shape.get("x1", 0) / ppm  # WHY: pixel -> meter for segment end
        y1 = last_shape.get("y1", 0) / ppm  # WHY: pixel -> meter for segment end
        return x0, y0, x1, y1  # WHY: hand back for payload build

    def _fetch_existing_paths(self, cfg: _DrawingConfig) -> list[dict[str, Any]]:
        """Fetch the map's current sitesurvey_path list so we can append to it."""
        map_response = self._state.mistapi_ref.api.v1.sites.maps.getSiteMap(  # WHY: read-before-write
            self._state.api_session_ref, cfg.site_id, cfg.map_id
        )
        existing_paths: list[dict[str, Any]] = []  # WHY: default empty paths list
        if hasattr(map_response, "data"):  # WHY: guard against error responses without data
            existing_paths = map_response.data.get("sitesurvey_path", []) or []  # WHY: normalize None to []
        return existing_paths  # WHY: caller builds updated payload from this

    @staticmethod
    def _build_path_update(
        x0: float, y0: float, x1: float, y1: float, existing_paths: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Append a single two-node validation path to the existing list."""
        new_path = {  # WHY: single two-node validation path
            "id": str(uuid.uuid4()),
            "name": f"Path_{len(existing_paths) + 1}",
            "coordinate": "actual",
            "nodes": [
                {"name": "P0", "position": {"x": x0, "y": y0}, "edges": {"P1": "path"}},
                {"name": "P1", "position": {"x": x1, "y": y1}, "edges": {}},
            ],
        }
        existing_paths.append(new_path)  # WHY: mutate list in place so returned dict shares state
        return {"sitesurvey_path": existing_paths}  # WHY: updateSiteMap payload envelope

    @staticmethod
    def _render_save_result(response: Any, spec: _SaveResultSpec, current_trigger: int) -> tuple[Any, Any]:
        """Render the Dash output based on a save-shape Mist response."""
        from dash import html, no_update  # WHY: Span + no_update needed for both branches

        if hasattr(response, "status_code") and response.status_code in spec.success_codes:  # WHY: success path
            logging.info(spec.audit_success)  # WHY: audit success
            return (
                html.Span(spec.success_msg, style={"color": "#28a745", "fontWeight": "bold"}),
                {"trigger": current_trigger + 1},
            )
        error_msg = getattr(response, "text", str(response))  # WHY: error body or repr
        logging.error("%s - %s", spec.audit_failure, error_msg)  # WHY: audit failure
        return (
            html.Span(f"{spec.failure_prefix}: {error_msg[:50]}", style={"color": "#ff4444"}),
            no_update,
        )

    def _delete_validation_paths(self, cfg: _DrawingConfig) -> tuple[Any, Any]:
        """Clear all sitesurvey_path entries via updateSiteMap."""
        spec = _MapResetSpec(  # WHY: bundle audit strings + payload for the shared reset runner
            payload={"sitesurvey_path": []},
            click_label="Delete paths",
            success_msg="All validation paths deleted - click Refresh to reload map",
            success_log="Drawing tool: All validation paths deleted from map %s",
            failure_prefix="Delete paths failed",
            error_context="paths",
        )
        return self._run_map_reset(spec, cfg)  # WHY: shared updateSiteMap reset flow

    def _delete_wayfinding_paths(self, cfg: _DrawingConfig) -> tuple[Any, Any]:
        """Clear all wayfinding_path entries via updateSiteMap."""
        spec = _MapResetSpec(  # WHY: bundle audit strings + payload for the shared reset runner
            payload={"wayfinding_path": {"coordinate": "actual", "nodes": []}},
            click_label="Delete wayfinding",
            success_msg="All wayfinding paths deleted - click Refresh to reload map",
            success_log="Drawing tool: All wayfinding paths deleted from map %s",
            failure_prefix="Delete wayfinding failed",
            error_context="wayfinding",
        )
        return self._run_map_reset(spec, cfg)  # WHY: shared updateSiteMap reset flow

    def _run_map_reset(self, spec: _MapResetSpec, cfg: _DrawingConfig) -> tuple[Any, Any]:
        """Execute a shared updateSiteMap-based collection reset (paths/wayfinding)."""
        from dash import html, no_update  # WHY: exception branch uses Span + no_update

        logging.info(  # WHY: audit trigger
            "Drawing tool: %s button clicked - site_id=%s, map_id=%s", spec.click_label, cfg.site_id, cfg.map_id
        )
        try:
            logging.info("Drawing tool: Calling updateSiteMap with %s", spec.payload)  # WHY: audit body
            response = self._state.mistapi_ref.api.v1.sites.maps.updateSiteMap(  # WHY: Mist API write
                self._state.api_session_ref, cfg.site_id, cfg.map_id, spec.payload
            )
            logging.info(  # WHY: audit response
                "Drawing tool: updateSiteMap response status_code=%s", getattr(response, "status_code", "N/A")
            )
            return self._render_reset_result(response, spec, cfg)  # WHY: render Dash output from response
        except Exception as del_error:  # noqa: BLE001 - preserve broad-except behavior
            logging.exception("Drawing tool: Error deleting %s - %s", spec.error_context, del_error)
            return html.Span(f"Error: {str(del_error)[:50]}", style={"color": "#ff4444"}), no_update

    @staticmethod
    def _render_reset_result(response: Any, spec: _MapResetSpec, cfg: _DrawingConfig) -> tuple[Any, Any]:
        """Render the Dash output based on a map-reset updateSiteMap response."""
        from dash import html, no_update  # WHY: Span + no_update needed for both branches

        if hasattr(response, "status_code") and response.status_code == 200:  # WHY: success path
            logging.info(spec.success_log, cfg.map_id)  # WHY: audit success
            return (
                html.Span(spec.success_msg, style={"color": "#28a745"}),
                {"trigger": cfg.current_trigger + 1},
            )
        error_msg = getattr(response, "text", str(response))  # WHY: error body or repr
        logging.error("Drawing tool: %s - %s", spec.failure_prefix, error_msg)  # WHY: audit failure
        return html.Span(f"Failed: {error_msg[:50]}", style={"color": "#ff4444"}), no_update

    def _delete_walls(self, cfg: _DrawingConfig) -> tuple[Any, Any]:
        """Clear wall_path entries via updateSiteMap."""
        from dash import html, no_update  # WHY: all response branches use Span + no_update

        try:
            update_data: dict[str, Any] = {"wall_path": {"coordinate": "actual", "nodes": []}}  # WHY: reset wall_path
            response = self._state.mistapi_ref.api.v1.sites.maps.updateSiteMap(  # WHY: Mist API write
                self._state.api_session_ref, cfg.site_id, cfg.map_id, update_data
            )
            if hasattr(response, "status_code") and response.status_code == 200:  # WHY: success path
                logging.info("Drawing tool: All walls deleted from map %s", cfg.map_id)  # WHY: audit success
                return (
                    html.Span("All walls deleted - click Refresh to reload map", style={"color": "#28a745"}),
                    {"trigger": cfg.current_trigger + 1},
                )
            error_msg = getattr(response, "text", str(response))  # WHY: error body or repr
            return html.Span(f"Failed: {error_msg[:50]}", style={"color": "#ff4444"}), no_update
        except Exception as del_error:  # noqa: BLE001 - preserve broad-except behavior
            logging.error("Drawing tool: Error deleting walls - %s", del_error)  # WHY: preserve error-not-exception log
            return html.Span(f"Error: {str(del_error)[:50]}", style={"color": "#ff4444"}), no_update

    def _delete_all_zones(self, cfg: _DrawingConfig) -> tuple[Any, Any]:
        """Delete every zone on the current map (one DELETE per zone)."""
        from dash import html, no_update  # WHY: exception branch uses Span + no_update

        logging.info(  # WHY: audit trigger
            "Drawing tool: Delete all zones button clicked - site_id=%s, map_id=%s", cfg.site_id, cfg.map_id
        )
        try:
            map_zones = self._fetch_zones_for_map(cfg)  # WHY: list-and-filter to the current map
            if isinstance(map_zones, tuple):  # WHY: fetch signalled an early Dash response
                return map_zones
            logging.warning("Drawing tool: Deleting %s zones from map %s", len(map_zones), cfg.map_id)  # WHY: audit
            deleted_count, failed_count = self._delete_zones_one_by_one(cfg.site_id, map_zones)  # WHY: loop
            return self._render_delete_zones_result(deleted_count, failed_count, cfg.current_trigger)  # WHY: render
        except Exception as del_error:  # noqa: BLE001 - preserve broad-except behavior
            logging.exception("Drawing tool: Error deleting zones - %s", del_error)  # WHY: audit failure
            return html.Span(f"Error: {str(del_error)[:50]}", style={"color": "#ff4444"}), no_update

    def _fetch_zones_for_map(self, cfg: _DrawingConfig) -> list[dict[str, Any]] | tuple[Any, Any]:
        """Return the zones filtered to the current map, or an early Dash response."""
        from dash import html, no_update  # WHY: guard-clauses return Dash-shaped tuples

        zones_response = self._state.mistapi_ref.api.v1.sites.zones.listSiteZones(  # WHY: fetch zones
            self._state.api_session_ref, cfg.site_id
        )
        if not self._zones_response_ok(zones_response):  # WHY: fetch failed
            return html.Span("Failed to fetch zones list", style={"color": "#ff4444"}), no_update
        map_zones = self._filter_zones_by_map(zones_response, cfg.map_id)  # WHY: filter to current map
        if not map_zones:  # WHY: nothing to delete
            return html.Span("No zones found on this map", style={"color": "#ffc107"}), no_update
        return map_zones  # WHY: list of zone dicts for the caller loop

    @staticmethod
    def _zones_response_ok(response: Any) -> bool:  # WHY: keep guard-clause check flat
        """Return True when listSiteZones responded with HTTP 200."""
        return hasattr(response, "status_code") and response.status_code == 200  # WHY: 2-branch bool

    @staticmethod
    def _filter_zones_by_map(response: Any, map_id: str | None) -> list[dict[str, Any]]:
        """Return the subset of zones whose map_id matches the current map."""
        all_zones = response.data if hasattr(response, "data") else []  # WHY: all site zones
        return [z for z in all_zones if z.get("map_id") == map_id]  # WHY: filter to current map

    @staticmethod
    def _render_delete_zones_result(deleted_count: int, failed_count: int, current_trigger: int) -> tuple[Any, Any]:
        """Render the Dash output based on delete-all-zones counts."""
        from dash import html  # WHY: both branches emit Span components

        if failed_count == 0:  # WHY: all deletes succeeded
            return (
                html.Span(f"Deleted {deleted_count} zones - click Refresh to reload map", style={"color": "#28a745"}),
                {"trigger": current_trigger + 1},
            )
        return (  # WHY: mixed success/failure summary
            html.Span(f"Deleted {deleted_count}, failed {failed_count} zones", style={"color": "#ffc107"}),
            {"trigger": current_trigger + 1},
        )

    def _delete_zones_one_by_one(self, site_id: str | None, map_zones: list[dict[str, Any]]) -> tuple[int, int]:
        """Delete each zone individually. Return (deleted, failed) counts."""
        deleted_count = 0  # WHY: successful deletes
        failed_count = 0  # WHY: failed deletes (logged but tolerated)
        for zone in map_zones:  # WHY: one DELETE per zone (Mist has no bulk endpoint)
            zone_id = zone.get("id")  # WHY: UUID of zone to delete
            zone_name = zone.get("name", "Unknown")  # WHY: display name for logs
            try:
                del_response = self._state.mistapi_ref.api.v1.sites.zones.deleteSiteZone(  # WHY: Mist API write
                    self._state.api_session_ref, site_id, zone_id
                )
                if hasattr(del_response, "status_code") and del_response.status_code in [200, 204]:  # WHY: success
                    deleted_count += 1  # WHY: bump success counter
                    logging.info("Drawing tool: Deleted zone '%s'", zone_name)  # WHY: audit success
                else:
                    failed_count += 1  # WHY: bump failure counter
                    logging.error("Drawing tool: Failed to delete zone '%s'", zone_name)  # WHY: audit failure
            except Exception as zone_err:  # noqa: BLE001 - preserve broad-except behavior
                failed_count += 1  # WHY: bump failure counter on exception
                logging.error("Drawing tool: Error deleting zone '%s': %s", zone_name, zone_err)  # WHY: audit
        return deleted_count, failed_count  # WHY: hand counts back to caller for rendering

    # ------------------------------------------------------------------
    # Callback wiring
    # ------------------------------------------------------------------

    def register(self, app: Dash) -> None:  # WHY: hooks this wave's app.callback(...) blocks into Dash
        """Attach the drawing-tools callback in this cluster to ``app``."""
        outputs, inputs, states = self._build_dash_wiring()  # WHY: split wiring metadata build for brevity
        app.callback(outputs, inputs, states, prevent_initial_call=True)(self.handle_drawing_tools)

    @staticmethod
    def _build_dash_wiring() -> tuple[list[Any], list[Any], list[Any]]:
        """Return the (outputs, inputs, states) wiring for handle_drawing_tools."""
        from dash import Input, Output, State  # WHY: local import keeps module import-light

        outputs = [  # WHY: status Span + cache-bust store bump
            Output("drawing-tool-status", "children"),
            Output("cache-bust-store", "data", allow_duplicate=True),
        ]
        inputs = [  # WHY: every button that fires the callback
            Input("save-shape-btn", "n_clicks"),
            Input("clear-drawings-btn", "n_clicks"),
            Input("delete-paths-btn", "n_clicks"),
            Input("delete-wayfinding-btn", "n_clicks"),
            Input("delete-walls-btn", "n_clicks"),
            Input("delete-zones-btn", "n_clicks"),
        ]
        states = [  # WHY: read-only state stores merged into callback args
            State("drawing-mode-dropdown", "value"),
            State("zone-name-input", "value"),
            State("map-display", "figure"),
            State("map-config-store", "data"),
            State("cache-bust-store", "data"),
        ]
        return outputs, inputs, states  # WHY: caller passes tuple through to app.callback(...)
