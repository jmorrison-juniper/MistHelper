"""Dash/Plotly viewer launcher extracted from ``_plotly_viewer.py``.

The original ``_PlotlyViewer._launch_plotly_viewer`` method held ~1300
lines of Dash layout literals, figure setup, and server boot. This
module splits that body into a :class:`_ViewerLauncher` class whose
sole responsibility is orchestrating the viewer session, plus a set of
small builder helpers (each under 25 lines) that construct discrete
pieces of the Dash ``html.Div`` layout tree.

The launcher receives the wrapped :class:`_PlotlyViewer` instance and
forwards attribute lookups back through it so figure-population helpers
(``_add_walls``, ``_add_clients_to_figure``, ``_categorize_devices``,
and so on) still reach the shared implementation without duplication.
"""

from __future__ import annotations  # WHY: Defer annotation resolution -- allows PEP 604 unions on 3.10.

import logging  # WHY: Emit lifecycle traces to the project logger.
import os  # WHY: Read DASH_PORT env + inspect container state for host binding.
from dataclasses import dataclass  # WHY: Frozen bundle keeps _make_viewer_state under STRUCT-PARAMS.
from typing import TYPE_CHECKING, Any  # WHY: TYPE_CHECKING avoids a runtime import cycle with _plotly_viewer.

from src.dataclasses.map_scaling_deps import MapDimensions  # WHY: Typed bundle for map size + ppm passed into heatmap.
from src.dataclasses.map_viewer_deps import (  # WHY: Grouped input dataclasses defined by the wrapper.
    HeatmapRenderCtx,  # WHY: Groups fig/renderer/coverage for optional heatmap.
    MapViewerData,  # WHY: Map payload bundle (map_data/devices/zones/clients).
    MapViewerOptional,  # WHY: Optional overlays bundle (coverage, all_maps, all_sites).
    MapViewerScope,  # WHY: Session identity bundle (site_id, site_name, map_id).
)
from src.maps.launcher import MapViewerCallbacks, MapViewerState  # WHY: Callback + shared-state pair wired into Dash.
from src.maps.plotly_heatmap_renderer import PlotlyCoverageHeatmapRenderer  # WHY: RF heatmap renderer instance.
from src.maps.plotly_map_callback_manager import PlotlyMapCallbackManager  # WHY: Layer/click callback delegate.
from src.maps.plotly_map_figure_builder import PlotlyMapFigureBuilder  # WHY: Walls/wayfinding/zones figure builder.
from src.maps.plotly_map_serializer import (  # WHY: Store payload serializer + params bundle.
    MapConfigParams,
    PlotlyMapDataSerializer,
)
from src.maps.plotly_map_templates import DashTemplateManager  # WHY: HTML/CSS template provider for the Dash shell.

try:  # WHY: mistapi is required for real deletes but tests may stub it.
    import mistapi  # type: ignore[import-untyped]  # WHY: Runtime reference for delete callbacks.
except ImportError:  # pragma: no cover - viewer is unreachable without mistapi anyway
    mistapi = None  # type: ignore[assignment]

if TYPE_CHECKING:  # WHY: Import only for static checkers to avoid circular runtime dependency.
    from src.maps._plotly_viewer import _PlotlyViewer  # WHY: Wrapper class we delegate helper methods through.

logger = logging.getLogger(__name__)  # WHY: Module-scoped logger for launcher traces.


@dataclass(frozen=True, slots=True)
class _ViewerStateInputs:  # WHY: Bundles _make_viewer_state args to keep it under STRUCT-PARAMS.
    """Inputs `_make_viewer_state` needs beyond scope/data (normalized lists + helpers + ppm)."""

    all_maps: list[dict[str, Any]]  # WHY: Normalized non-None list of other maps in the site.
    all_sites: list[dict[str, Any]]  # WHY: Normalized non-None list of other sites in the org.
    helpers: dict[str, Any]  # WHY: Renderer/serializer/template/callback bundle.
    ppm: float  # WHY: Validated pixels-per-meter for label fallbacks.


@dataclass(frozen=True, slots=True)
class _ViewerRuntime:  # WHY: Bundles Dash runtime handles so _pack_viewer_context stays under STRUCT-PARAMS.
    """Runtime instances (Dash app, plotly figure, callback state) for the packed context."""

    app: Any  # WHY: Configured Dash application instance.
    fig: Any  # WHY: Plotly figure being populated with traces.
    viewer_state: MapViewerState  # WHY: Shared MapViewerState wired into callbacks.


@dataclass(frozen=True, slots=True)
class _ViewerContextInputs:  # WHY: Bundles session inputs so _pack_viewer_context stays under STRUCT-PARAMS.
    """Session inputs (scope, data, optional overlays) fed into the context dict."""

    scope: MapViewerScope  # WHY: Site/map identity for the current session.
    data: MapViewerData  # WHY: Map payload (map_data + devices + zones + clients).
    optional: MapViewerOptional  # WHY: Optional overlay lists (coverage/all_maps/all_sites).


# JS payload driving the map-switch clientside callback (unchanged from
# the original inline literal -- moved here so the launcher method
# stays under the STRUCT-LENGTH ceiling).
_JS_MAP_SWITCH_CALLBACK = """
            function(selected_map_id, config) {
                var current_map_id = config ? config.map_id : null;
                if (!selected_map_id || selected_map_id === current_map_id) {
                    return window.dash_clientside.no_update;
                }

                // Check if URL already has this map_id - if so, don't redirect (prevents loop)
                var urlParams = new URLSearchParams(window.location.search);
                var url_map_id = urlParams.get('map_id');
                if (url_map_id === selected_map_id) {
                    console.log('Map switch: URL already has map_id=' + selected_map_id + ', skipping redirect');
                    return window.dash_clientside.no_update;
                }

                // Redirect to URL with map_id parameter (preserve site_id if present)
                var site_id = urlParams.get('site_id') || (config ? config.site_id : null);
                var new_url = '/?map_id=' + selected_map_id;
                if (site_id) {
                    new_url += '&site_id=' + site_id;
                }
                console.log('Map switch: redirecting to map_id=' + selected_map_id);
                window.location.href = new_url;
                return '';
            }
            """  # WHY: Verbatim redirect handler wired via app.clientside_callback.


# JS payload driving the cache-bust reload callback -- reloads the
# page after clone/delete so freshly-created maps show up.
_JS_CACHE_BUST_CALLBACK = """
            function(cache_bust_data) {
                if (!cache_bust_data || !cache_bust_data.trigger) {
                    return window.dash_clientside.no_update;
                }
                // Check if this trigger was already processed (stored in sessionStorage)
                var lastTrigger = parseInt(sessionStorage.getItem('lastCacheBustTrigger') || '0');
                var currentTrigger = cache_bust_data.trigger;

                // Only reload if trigger is NEW (greater than last processed)
                if (currentTrigger > lastTrigger) {
                    console.log('Cache bust: Reloading page to refresh map data '
                        + '(trigger=' + currentTrigger + ', last=' + lastTrigger + ')');
                    // Store this trigger as processed before reloading
                    sessionStorage.setItem('lastCacheBustTrigger', currentTrigger.toString());
                    // Small delay to allow status message to display briefly
                    setTimeout(function() {
                        window.location.reload();
                    }, 1500);
                }
                return window.dash_clientside.no_update;
            }
            """  # WHY: Verbatim reload handler wired via app.clientside_callback.


# Device type render config (marker sizes + status color palette per
# device kind). Kept module-scoped so the launcher method body stays
# short and the dictionary literal is not counted against it.
_DEVICE_TYPE_CONFIG: dict[str, dict[str, Any]] = {  # WHY: Symbol/size/status-color per device kind.
    "ap": {  # WHY: Access-point marker config.
        "symbol": "triangle-up",  # WHY: Distinctive triangle for APs.
        "name": "Access Points",  # WHY: Legend label.
        "size": 20,  # WHY: Slightly larger for high visibility.
        "colors": {  # WHY: Status-based marker color palette.
            "connected": "#00ff00",  # WHY: Bright green = healthy.
            "disconnected": "#ff0000",  # WHY: Red = offline.
            "upgrading": "#ff8800",  # WHY: Amber = firmware update in progress.
        },
    },
    "switch": {  # WHY: Switch marker config.
        "symbol": "square",  # WHY: Square differentiates from APs.
        "name": "Switches",  # WHY: Legend label.
        "size": 18,  # WHY: Slightly smaller than APs.
        "colors": {  # WHY: Status-based marker color palette.
            "connected": "#00ccff",  # WHY: Cyan = healthy switch.
            "disconnected": "#ff0000",  # WHY: Red = offline.
            "upgrading": "#ff8800",  # WHY: Amber = firmware update.
        },
    },
    "gateway": {  # WHY: Gateway marker config.
        "symbol": "diamond",  # WHY: Diamond distinguishes gateways.
        "name": "Gateways",  # WHY: Legend label.
        "size": 20,  # WHY: Same size as APs for prominence.
        "colors": {  # WHY: Status-based marker color palette.
            "connected": "#ff00ff",  # WHY: Magenta = healthy gateway.
            "disconnected": "#ff0000",  # WHY: Red = offline.
            "upgrading": "#ff8800",  # WHY: Amber = firmware update.
        },
    },
}


class _ViewerLauncher:  # WHY: Class boundary that owns the extracted launch workflow.
    """Orchestrate Dash/Plotly viewer startup for a single map session.

    Instances are single-use: :meth:`run` bootstraps the Dash app,
    builds the figure, assembles the layout, and blocks on the Dash
    server until the operator terminates the viewer.
    """

    def __init__(self, viewer: _PlotlyViewer) -> None:  # WHY: Accept the wrapper so helper methods stay reachable.
        """Store the wrapped viewer so helper methods and MapsManager attrs stay reachable."""
        self._viewer = viewer  # WHY: All figure-population helpers live on the wrapper.

    def run(  # WHY: Public entry point -- called from _PlotlyViewer._launch_plotly_viewer.
        self,
        scope: MapViewerScope,
        data: MapViewerData,
        optional: MapViewerOptional,
    ) -> None:
        """Boot the Dash viewer for the given scope/data/optional bundles."""
        self._log_startup(scope, data, optional)  # WHY: Structured info log before heavy work begins.
        dash_modules = self._viewer._try_import_dash_modules(data.map_data, data.devices)  # WHY: Lazy import.
        if dash_modules is None:  # WHY: Helper already invoked the static-fallback path.
            return  # WHY: Nothing else to do -- static path handled the render.
        self._viewer._print_viewer_intro_banner()  # WHY: User-facing banner on stderr.
        ctx = self._build_viewer_context(scope, data, optional, dash_modules)  # WHY: Consolidated per-session state.
        self._populate_figure(ctx)  # WHY: Walls/wayfinding/zones/paths/clients/devices/beacons/heatmap.
        self._apply_figure_layout(ctx)  # WHY: Update axes, legend, dark theme, meta.
        self._assign_dash_layout(ctx)  # WHY: Build the html.Div tree and assign to app.layout.
        self._register_clientside_callbacks(ctx)  # WHY: Wire the 2 JS-only redirect/reload callbacks.
        ctx["viewer_callbacks"].register_with(ctx["app"])  # WHY: Wave A/B/C server-side callbacks (13 total).
        self._serve_dash_app(ctx["app"])  # WHY: Blocking Dash server run.

    def _log_startup(  # WHY: Split logging call out of run() to keep run under 25 lines.
        self,
        scope: MapViewerScope,
        data: MapViewerData,
        optional: MapViewerOptional,
    ) -> None:
        """Emit structured info log describing what the viewer was invoked with."""
        coverage_count = self._viewer._resolve_coverage_count(optional.coverage_data)  # WHY: Count or 'None' label.
        logging.info(  # WHY: Wide info line -- includes site/map/counts for support diagnostics.
            "_launch_plotly_viewer called - site: %s (%s), map_id: %s, "
            "devices: %s, zones: %s, clients: %s, coverage: %s, "
            "available_maps: %s, available_sites: %s",
            scope.site_name,  # WHY: Human-readable site.
            scope.site_id,  # WHY: UUID for support.
            scope.map_id,  # WHY: Map UUID for support.
            len(data.devices),  # WHY: Device count.
            len(data.zones),  # WHY: Zone count.
            len(data.clients),  # WHY: Client count.
            coverage_count,  # WHY: Coverage sample count or 'None'.
            len(optional.all_maps or []),  # WHY: Other-map count.
            len(optional.all_sites or []),  # WHY: Other-site count.
        )

    def _build_viewer_context(  # WHY: Aggregate stage helpers so run() stays compact.
        self,
        scope: MapViewerScope,
        data: MapViewerData,
        optional: MapViewerOptional,
        dash_modules: tuple[Any, ...],
    ) -> dict[str, Any]:
        """Return a dict bundling Dash modules, figure, viewer state, and helpers."""
        all_maps, all_sites = self._viewer._normalize_optional_lists(  # WHY: Ensure iterable defaults.
            optional.all_maps,
            optional.all_sites,
        )
        helpers = self._build_dash_helpers()  # WHY: Renderer/serializer/template-mgr trio.
        app = self._create_dash_app(dash_modules[1], helpers["template_mgr"])  # WHY: dash_modules[1] == Dash class.
        fig, ppm = self._prepare_figure(data)  # WHY: Fresh plotly Figure + ppm validated against clients.
        state_inputs = _ViewerStateInputs(  # WHY: Bundle args to keep _make_viewer_state under STRUCT-PARAMS.
            all_maps=all_maps,
            all_sites=all_sites,
            helpers=helpers,
            ppm=ppm,
        )
        viewer_state = self._make_viewer_state(scope, data, state_inputs)  # WHY: Shared state for callbacks.
        runtime = _ViewerRuntime(app=app, fig=fig, viewer_state=viewer_state)  # WHY: Bundle Dash runtime handles.
        ctx_inputs = _ViewerContextInputs(scope=scope, data=data, optional=optional)  # WHY: Bundle session inputs.
        return self._pack_viewer_context(ctx_inputs, dash_modules, state_inputs, runtime)  # WHY: Assemble flat dict.

    def _pack_viewer_context(  # WHY: Split from _build_viewer_context so it stays under STRUCT-LENGTH.
        self,
        ctx_inputs: _ViewerContextInputs,
        dash_modules: tuple[Any, ...],
        state_inputs: _ViewerStateInputs,
        runtime: _ViewerRuntime,
    ) -> dict[str, Any]:
        """Return the flat context dict handed to every stage helper."""
        context = _pack_session_ctx(ctx_inputs, state_inputs)  # WHY: Scope/data/optional + normalized lists.
        context.update(_pack_dash_modules_ctx(dash_modules))  # WHY: Dash classes + layout constructors.
        context.update(_pack_runtime_ctx(runtime, state_inputs))  # WHY: App/figure/ppm/helpers/state runtime bundle.
        context["_launcher"] = self  # WHY: Layout helpers dispatch back to viewer wrapper methods.
        return context  # WHY: One flat dict avoids passing 10 args between stages.

    def _build_dash_helpers(self) -> dict[str, Any]:  # WHY: Consolidate helper instantiation.
        """Return the renderer/serializer/template trio used by the launcher."""
        return {  # WHY: Flat dict returned so context builder stays under limits.
            "callback_manager": PlotlyMapCallbackManager(),  # WHY: Delegate for layer/click dispatch.
            "template_mgr": DashTemplateManager(org_id=self._viewer.org_id),  # WHY: HTML/CSS template provider.
            "figure_builder": PlotlyMapFigureBuilder(logger=logging.getLogger(__name__)),  # WHY: Walls/paths builder.
            "heatmap_renderer": PlotlyCoverageHeatmapRenderer(logger=logging.getLogger(__name__)),  # WHY: Heatmap.
            "serializer": PlotlyMapDataSerializer(),  # WHY: Store/dropdown option serializer.
        }

    def _create_dash_app(self, Dash: Any, template_mgr: DashTemplateManager) -> Any:  # WHY: Configure Dash instance.
        """Instantiate the Dash app with dark-theme template and metadata."""
        logging.debug("Creating Dash application instance")  # WHY: Trace lifecycle for support.
        app_meta = template_mgr.get_app_meta()  # WHY: Pulls title / callback exception flag.
        app = Dash(  # WHY: Standard Dash constructor call.
            __name__,  # WHY: Anchor Dash asset paths to this module.
            update_title=app_meta["update_title"],  # WHY: Suppress default "Updating..." flash.
            title=app_meta["title"],  # WHY: Browser tab title.
            suppress_callback_exceptions=app_meta["suppress_callback_exceptions"],  # WHY: Needed for duplicate outputs.
        )
        app.index_string = template_mgr.get_html_template()  # WHY: Inject custom HTML shell + CSS.
        return app  # WHY: Return configured Dash app for the caller.

    def _prepare_figure(self, data: MapViewerData) -> tuple[Any, float]:  # WHY: Build fresh figure + validated ppm.
        """Return a fresh Plotly figure and the validated pixels-per-meter value."""
        import plotly.graph_objects as go  # type: ignore[import-untyped]  # WHY: Local import -- plotly is optional.

        logging.debug("Building Plotly figure")  # WHY: Trace lifecycle for support.
        fig = go.Figure()  # WHY: Fresh figure -- all traces are added below.
        map_width = data.map_data.get("width", 1000)  # WHY: Default width if missing.
        map_height = data.map_data.get("height", 1000)  # WHY: Default height if missing.
        ppm = data.map_data.get("ppm", 10)  # WHY: Default 10 px/m when unset.
        logging.debug(  # WHY: Trace canvas dimensions for support.
            "Map canvas dimensions: %sx%s, PPM from map: %s",
            map_width,
            map_height,
            ppm,
        )
        ppm = self._viewer._validate_ppm(data.clients, ppm)  # WHY: Returns corrected PPM on >10% mismatch.
        return fig, ppm  # WHY: Caller stores both in the context bundle.

    def _make_viewer_state(  # WHY: Build the MapViewerState with all wave A/B/C fields.
        self,
        scope: MapViewerScope,
        data: MapViewerData,
        inputs: _ViewerStateInputs,
    ) -> MapViewerState:
        """Return the shared MapViewerState instance consumed by callback handlers."""
        helpers, all_sites, all_maps = inputs.helpers, inputs.all_sites, inputs.all_maps  # WHY: Local shortcuts.
        return MapViewerState(  # WHY: Container carries every ref needed by 13 registered callbacks.
            callback_manager=helpers["callback_manager"],  # WHY: Wave A delegate.
            zones=data.zones,  # WHY: Wave B/C zone toggle + zone-action callbacks.
            map_id=scope.map_id,  # WHY: Wave B/C fallback for delete/utilities.
            site_id=scope.site_id,  # WHY: Wave C site_id for delete/zone API calls.
            api_session_ref=self._viewer.apisession,  # WHY: Wave C live mistapi session.
            ppm=inputs.ppm,  # WHY: Wave C label update fallback ppm.
            mistapi_ref=mistapi,  # WHY: Wave C module reference for deleteSiteMap/Zone.
            maps_manager_ref=self._viewer._mm,  # WHY: Wave C _backup_map_geometry callback needs real manager.
            serializer=helpers["serializer"],  # WHY: Wave E2 dropdown/store builder.
            all_sites=all_sites,  # WHY: Wave E2 URL/site-switch site list.
            all_maps=all_maps,  # WHY: Wave E2 URL/site-switch map list.
            available_sites=all_sites,  # WHY: Wave E2 parity duplicate.
            figure_builder=helpers["figure_builder"],  # WHY: Wave E2 shared builder.
            heatmap_renderer=helpers["heatmap_renderer"],  # WHY: Wave E2 heatmap renderer.
        )

    def _populate_figure(self, ctx: dict[str, Any]) -> None:  # WHY: Attach every trace/annotation to the figure.
        """Attach background, walls, wayfinding, zones, paths, clients, devices, beacons, heatmap, origin."""
        import plotly.graph_objects as go  # type: ignore[import-untyped]  # WHY: Local import for optional dep.

        fig, data = ctx["fig"], ctx["data"]  # WHY: Frequently used locals.
        map_width, map_height = data.map_data.get("width", 1000), data.map_data.get("height", 1000)  # WHY: Canvas dims.
        self._viewer._add_background_image_to_figure(fig, data.map_data, map_width, map_height)  # WHY: Floorplan bg.
        ctx["helpers"]["figure_builder"].add_walls(fig, data.map_data)  # WHY: Wall segments.
        ctx["helpers"]["figure_builder"].add_wayfinding(fig, data.map_data)  # WHY: Wayfinding paths.
        ctx["helpers"]["figure_builder"].add_zones(fig, data.zones)  # WHY: Zone polygons.
        self._viewer._add_site_survey_paths(fig, data.map_data)  # WHY: Site survey validation paths.
        self._viewer._add_clients_to_figure(fig, data.clients, ctx["scope"].map_id)  # WHY: Client dots.
        self._add_devices_and_beacons(ctx)  # WHY: Devices + vbeacons + BLE grouped into helper.
        self._maybe_add_heatmap(ctx, map_width, map_height)  # WHY: Optional RF coverage overlay.
        self._viewer._add_origin_marker_trace(fig, data.map_data, go)  # WHY: Origin cross marker.

    def _add_devices_and_beacons(self, ctx: dict[str, Any]) -> None:  # WHY: Split from _populate_figure.
        """Render per-type device markers plus vbeacon and BLE beacon overlays."""
        fig, data = ctx["fig"], ctx["data"]  # WHY: Frequently used locals.
        device_types = self._viewer._categorize_devices_by_type(data.devices)  # WHY: {'ap': [...], 'switch': [...]}.
        for device_type, type_cfg in _DEVICE_TYPE_CONFIG.items():  # WHY: One iteration per kind.
            self._viewer._render_device_type_on_figure(fig, device_types[device_type], type_cfg, device_type)
        self._viewer._add_vbeacons_to_figure(fig, data.map_data)  # WHY: Virtual beacons + coverage rings.
        self._viewer._add_ble_beacons_to_figure(fig, data.map_data)  # WHY: 3rd-party BLE beacons.

    def _maybe_add_heatmap(self, ctx: dict[str, Any], map_width: int, map_height: int) -> None:
        """Delegate the optional RF-heatmap trace to the viewer wrapper."""
        self._viewer._maybe_add_heatmap_trace(  # WHY: Optional RF coverage overlay.
            HeatmapRenderCtx(
                fig=ctx["fig"],
                heatmap_renderer=ctx["helpers"]["heatmap_renderer"],
                coverage_data=ctx["optional"].coverage_data,
            ),
            MapDimensions(width_px=map_width, height_px=map_height, ppm=ctx["ppm"]),
        )

    def _apply_figure_layout(self, ctx: dict[str, Any]) -> None:  # WHY: Push axis/legend/theme config onto figure.
        """Apply dark-theme layout, axis config, meta hints, and origin crosshair."""
        fig, data = ctx["fig"], ctx["data"]  # WHY: Frequently used locals.
        map_width = data.map_data.get("width", 1000)  # WHY: Right-margin computation.
        map_height = data.map_data.get("height", 1000)  # WHY: Y-axis inverted range.
        fig.update_layout(**_figure_layout_kwargs(data, ctx["ppm"], map_width, map_height))  # WHY: Extracted dict.
        self._viewer._add_origin_crosshair(fig, data.map_data)  # WHY: Post-layout so it sits on top.

    def _assign_dash_layout(self, ctx: dict[str, Any]) -> None:  # WHY: Build+assign app.layout in one place.
        """Build the complete html.Div layout tree and assign it to ``app.layout``."""
        map_dropdown_options, site_dropdown_options = self._viewer._build_selector_options(  # WHY: Compute options.
            ctx["all_maps"],
            ctx["all_sites"],
        )
        html_mod, dcc_mod = ctx["html"], ctx["dcc"]  # WHY: Local aliases keep call sites short.
        ctx["app"].layout = html_mod.Div(  # WHY: Top-level layout is a Div containing all sections.
            [
                _build_header_row(html_mod, dcc_mod, ctx["scope"], site_dropdown_options, map_dropdown_options),
                _build_clone_panel(html_mod, dcc_mod, ctx["data"].map_data),
                _build_delete_panel(html_mod, ctx["data"].map_data),
                _build_main_container(html_mod, dcc_mod, ctx),
                *_build_state_stores(dcc_mod, ctx),
                *_build_refresh_intervals(dcc_mod),
                dcc_mod.Location(id="url-location", refresh=True),  # WHY: URL sync for map/site switching.
                html_mod.Div(id="map-switch-trigger", style={"display": "none"}),  # WHY: Hidden JS trigger div.
            ],
            style={"height": "100vh", "display": "flex", "flexDirection": "column"},  # WHY: Full viewport shell.
        )

    def _register_clientside_callbacks(self, ctx: dict[str, Any]) -> None:  # WHY: Wire the 2 JS-only callbacks.
        """Register the map-switch redirect and cache-bust reload JS callbacks."""
        Input, Output, State = ctx["Input"], ctx["Output"], ctx["State"]  # WHY: Local aliases.
        ctx["app"].clientside_callback(  # WHY: Map dropdown -> URL redirect.
            _JS_MAP_SWITCH_CALLBACK,
            Output("map-switch-trigger", "children"),
            [Input("map-selector-dropdown", "value")],
            [State("map-config-store", "data")],
            prevent_initial_call=True,
        )
        ctx["app"].clientside_callback(  # WHY: Cache-bust store -> full page reload.
            _JS_CACHE_BUST_CALLBACK,
            Output("map-switch-trigger", "children", allow_duplicate=True),
            [Input("cache-bust-store", "data")],
            prevent_initial_call=True,
        )

    def _serve_dash_app(self, app: Any) -> None:  # WHY: Blocking Dash server + browser open.
        """Resolve binding, print banner, schedule browser open, and run Dash server."""
        dash_host, dash_port = self._viewer._resolve_dash_binding(os)  # WHY: Container-aware host/port.
        self._viewer._print_dash_startup_banner(dash_host, dash_port)  # WHY: User-facing banner.
        self._viewer._schedule_browser_open(dash_port)  # WHY: Background browser open (no-op in containers).
        self._viewer._run_dash_server(app, dash_host, dash_port)  # WHY: Blocking run + KeyboardInterrupt handler.


def _pack_session_ctx(
    ctx_inputs: _ViewerContextInputs,
    state_inputs: _ViewerStateInputs,
) -> dict[str, Any]:  # WHY: Session inputs slice of the context dict.
    """Return the session-input portion of the flat context dict."""
    return {  # WHY: Scope/data/optional + normalized lists consumed by stages.
        "scope": ctx_inputs.scope,  # WHY: Session identity bundle.
        "data": ctx_inputs.data,  # WHY: Map payload bundle.
        "optional": ctx_inputs.optional,  # WHY: Overlay lists container.
        "all_maps": state_inputs.all_maps,  # WHY: Normalized alternate map list.
        "all_sites": state_inputs.all_sites,  # WHY: Normalized alternate site list.
    }


def _pack_dash_modules_ctx(dash_modules: tuple[Any, ...]) -> dict[str, Any]:  # WHY: Dash slice of the context dict.
    """Return the Dash-modules portion of the flat context dict."""
    _dash, Dash, Input, Output, State, dcc, html, _no_update = dash_modules  # WHY: Unpack lazy imports.
    return {  # WHY: Dash classes + layout constructors consumed by callbacks.
        "Dash": Dash,  # WHY: Dash app class.
        "Input": Input,  # WHY: Dash callback Input reference.
        "Output": Output,  # WHY: Dash callback Output reference.
        "State": State,  # WHY: Dash callback State reference.
        "dcc": dcc,  # WHY: dash-core-components module.
        "html": html,  # WHY: dash-html-components module.
    }


def _pack_runtime_ctx(
    runtime: _ViewerRuntime,
    state_inputs: _ViewerStateInputs,
) -> dict[str, Any]:  # WHY: Runtime slice of the context dict.
    """Return the runtime portion of the flat context dict."""
    return {  # WHY: App/figure/ppm/helpers/state consumed by stages.
        "app": runtime.app,  # WHY: Configured Dash app instance.
        "fig": runtime.fig,  # WHY: Plotly figure being populated.
        "ppm": state_inputs.ppm,  # WHY: Validated pixels-per-meter.
        "helpers": state_inputs.helpers,  # WHY: Renderer/serializer/template bundle.
        "viewer_state": runtime.viewer_state,  # WHY: Shared state for callbacks.
        "viewer_callbacks": MapViewerCallbacks(state=runtime.viewer_state),  # WHY: Callback handler collection.
    }


def _xaxis_dark_config(map_width: int) -> dict[str, Any]:  # WHY: Extracted axis dict keeps launcher shorter.
    """Return the dark-theme x-axis dict for ``fig.update_layout``."""
    return dict(  # WHY: Plotly axis options dict.
        range=[-50, map_width + 50],  # WHY: Add margins to show full map extent.
        visible=True,
        title="X (pixels)",  # WHY: Standard axis title.
        gridcolor="#444",
        zerolinecolor="#666",
        color="#b0b0b0",  # WHY: Dark-theme axis colors.
        constrain="domain",  # WHY: Keep zoom within canvas.
    )


def _figure_layout_title(data: MapViewerData) -> dict[str, Any]:  # WHY: Title dict extracted to shrink layout kwargs.
    """Return the dark-theme title dict for ``fig.update_layout``."""
    return {  # WHY: Plotly title options.
        "text": f"Map: {data.map_data.get('name', 'Unnamed')}",  # WHY: Prefix + map name.
        "font": {"size": 20, "color": "#e0e0e0"},  # WHY: Dark-theme title font.
    }


def _figure_layout_newshape() -> dict[str, Any]:  # WHY: Newshape dict extracted to shrink layout kwargs.
    """Return the newshape dict configuring cyan drawing outlines."""
    return dict(  # WHY: Plotly newshape options.
        line=dict(color="cyan", width=3),  # WHY: Cyan outline for new drawings.
        fillcolor="rgba(0,255,255,0.2)",  # WHY: Semi-transparent cyan fill.
        opacity=0.8,  # WHY: Slight transparency so map remains visible.
    )


def _figure_layout_meta(data: MapViewerData, ppm: float) -> dict[str, Any]:  # WHY: Meta dict extracted for readability.
    """Return the meta dict carrying PPM + origin used by clientside callbacks."""
    return {  # WHY: Callbacks read PPM + origin from figure meta.
        "ppm": ppm,  # WHY: Pixels-per-meter for measurement callbacks.
        "origin_x": data.map_data.get("origin_x", 0),  # WHY: Map origin X coordinate.
        "origin_y": data.map_data.get("origin_y", 0),  # WHY: Map origin Y coordinate.
    }


def _figure_layout_kwargs(  # WHY: Kwargs bundle extracted from _apply_figure_layout to shrink it.
    data: MapViewerData,
    ppm: float,
    map_width: int,
    map_height: int,
) -> dict[str, Any]:
    """Return the kwargs dict passed to ``fig.update_layout`` for the dark theme."""
    return dict(  # WHY: Layout options dict consumed via **kwargs.
        title=_figure_layout_title(data),  # WHY: Extracted title dict.
        xaxis=_xaxis_dark_config(map_width),  # WHY: Extracted axis dict.
        yaxis=_yaxis_dark_config(map_height),  # WHY: Extracted axis dict.
        autosize=True,  # WHY: Fill container width.
        hovermode="closest",  # WHY: Tooltip on nearest point.
        showlegend=True,  # WHY: Interaction defaults.
        uirevision="constant",  # WHY: Preserve view across callbacks.
        legend=_legend_dark_config(),  # WHY: Extracted legend dict.
        plot_bgcolor="#1a1a1a",  # WHY: Dark plot surface.
        paper_bgcolor="#1a1a1a",  # WHY: Dark paper surface.
        margin=dict(l=50, r=50, t=80, b=50),  # WHY: Even padding around plot.
        dragmode="zoom",  # WHY: Default to pan/zoom. Drawing tools toggle this.
        newshape=_figure_layout_newshape(),  # WHY: Extracted drawing outline defaults.
        meta=_figure_layout_meta(data, ppm),  # WHY: Extracted meta dict.
    )


def _yaxis_dark_config(map_height: int) -> dict[str, Any]:  # WHY: Extracted axis dict keeps launcher shorter.
    """Return the dark-theme y-axis dict (inverted since Mist origin is top-left)."""
    return dict(  # WHY: Plotly axis options dict.
        range=[map_height + 50, -50],  # WHY: Inverted range with margins -- Mist uses top-left origin.
        visible=True,
        title="Y (pixels)",  # WHY: Standard axis title.
        scaleanchor="x",
        scaleratio=1,  # WHY: Preserve aspect ratio with X.
        gridcolor="#444",
        zerolinecolor="#666",
        color="#b0b0b0",  # WHY: Dark-theme axis colors.
        constrain="domain",  # WHY: Keep zoom within canvas.
    )


def _legend_dark_config() -> dict[str, Any]:  # WHY: Extracted legend dict keeps launcher shorter.
    """Return the dark-theme legend dict for ``fig.update_layout``."""
    return dict(  # WHY: Plotly legend options dict.
        x=0.02,
        y=0.98,  # WHY: Top-left anchor.
        bgcolor="rgba(45,45,45,0.9)",  # WHY: Semi-transparent dark background.
        bordercolor="#667eea",
        borderwidth=2,  # WHY: Purple border matches header.
        font=dict(color="#e0e0e0", size=12),  # WHY: Light text on dark bg.
    )


def _build_header_row(
    html_mod: Any,
    dcc_mod: Any,
    scope: MapViewerScope,
    site_options: list[dict[str, Any]],
    map_options: list[dict[str, Any]],
) -> Any:
    """Return the header ``html.Div`` -- site+map dropdowns plus utility buttons."""
    return html_mod.Div(  # WHY: Whole header is a single row Div with two inline children.
        [
            _build_site_dropdown(html_mod, dcc_mod, scope.site_id, site_options),  # WHY: Left side.
            _build_map_dropdown(html_mod, dcc_mod, scope.map_id, map_options),  # WHY: Left side, next to site.
            _build_utility_buttons_row(html_mod, dcc_mod),  # WHY: Right-floated button strip.
        ],
        style={
            "padding": "15px 20px",
            "borderBottom": "2px solid #667eea",  # WHY: Purple divider under header.
            "backgroundColor": "#2a2a2a",
        },
    )


def _build_site_dropdown(html_mod: Any, dcc_mod: Any, site_id: str, options: list[dict[str, Any]]) -> Any:
    """Return the site-selector dropdown wrapped in its label Div."""
    return html_mod.Div(  # WHY: Inline-block wrapper for label + dropdown.
        [
            html_mod.Span("Site: ", style={"fontSize": "14px", "color": "#888", "marginRight": "5px"}),  # WHY: Label.
            dcc_mod.Dropdown(  # WHY: Site switcher control.
                id="site-selector-dropdown",  # WHY: Callback binding ID.
                options=options,  # WHY: Populated list of {label, value} entries.
                value=site_id,  # WHY: Pre-select current site.
                clearable=False,
                searchable=True,  # WHY: Force a value. Allow keyboard filter.
                style={"width": "250px", "display": "inline-block", "verticalAlign": "middle"},  # WHY: Row layout.
                className="dark-dropdown",  # WHY: Custom CSS for dark theme.
            ),
        ],
        style={"display": "inline-block", "marginRight": "20px", "verticalAlign": "middle"},  # WHY: Row layout.
    )


def _build_map_dropdown(html_mod: Any, dcc_mod: Any, map_id: str, options: list[dict[str, Any]]) -> Any:
    """Return the map-selector dropdown wrapped in its label Div."""
    return html_mod.Div(  # WHY: Inline-block wrapper for label + dropdown.
        [
            html_mod.Span("Map: ", style={"fontSize": "14px", "color": "#888", "marginRight": "5px"}),  # WHY: Label.
            dcc_mod.Dropdown(  # WHY: Map switcher control.
                id="map-selector-dropdown",  # WHY: Callback binding ID.
                options=options,  # WHY: Populated list of {label, value} entries.
                value=map_id,  # WHY: Pre-select current map.
                clearable=False,
                searchable=False,  # WHY: Force a value. Small list so no search needed.
                style={"width": "200px", "display": "inline-block", "verticalAlign": "middle"},  # WHY: Row layout.
                className="dark-dropdown",  # WHY: Custom CSS for dark theme.
            ),
        ],
        style={"display": "inline-block", "marginRight": "30px", "verticalAlign": "middle"},  # WHY: Row layout.
    )


def _build_utility_buttons_row(html_mod: Any, dcc_mod: Any) -> Any:  # WHY: Right-floated action button strip.
    """Return the right-floated Div containing auto-refresh controls and utility buttons."""
    return html_mod.Div(  # WHY: Right-floated container.
        [
            _build_auto_refresh_group(html_mod, dcc_mod),  # WHY: Toggle + refresh button + countdown.
            _utility_button(html_mod, "[AUTO] Auto-Zone", "auto-zone-btn", _AUTOZONE_STYLE),  # WHY: Auto-zone.
            _utility_button(html_mod, "[PIN] Add vBeacon", "add-vbeacon-btn", _VBEACON_STYLE),  # WHY: vBeacon.
            _utility_button(html_mod, "[ANT] Add Beacon", "add-beacon-btn", _BLE_BEACON_STYLE),  # WHY: BLE beacon.
            _utility_button(html_mod, "[IMG] Change Image", "change-image-btn", _NEUTRAL_STYLE),  # WHY: Image swap.
            _utility_button(html_mod, "[DEL] Remove Image", "remove-image-btn", _NEUTRAL_STYLE),  # WHY: Image drop.
            _utility_button(html_mod, "[EDIT] Rename", "rename-btn", _NEUTRAL_STYLE),  # WHY: Rename map.
            _utility_button(html_mod, "[X] Delete", "delete-btn", _DELETE_STYLE),  # WHY: Destructive delete.
            _utility_button(html_mod, "[+] Clone", "clone-btn", _CLONE_STYLE),  # WHY: Clone map.
            html_mod.Div(
                id="utilities-status",  # WHY: Ephemeral status text next to buttons.
                style={"display": "inline-block", "marginLeft": "20px", "color": "#a0a0ff", "fontSize": "13px"},
            ),
        ],
        style={"display": "inline-block", "float": "right"},  # WHY: Push to the right of the header row.
    )


def _build_auto_refresh_group(html_mod: Any, dcc_mod: Any) -> Any:  # WHY: Toggle + button + countdown label.
    """Return the auto-refresh toggle + manual refresh button + countdown Div."""
    return html_mod.Div(  # WHY: Grouped inline-block container with border.
        [
            dcc_mod.Checklist(  # WHY: Single-option checklist acts as a toggle.
                id="auto-refresh-toggle",
                options=[{"label": " Auto-Refresh", "value": "enabled"}],  # WHY: Human label.
                value=["enabled"],  # WHY: Default ON.
                labelStyle={"display": "inline-block", "fontSize": "12px", "color": "#e0e0e0"},  # WHY: Inline label.
                style={"display": "inline-block", "marginRight": "10px"},  # WHY: Inline row.
            ),
            html_mod.Button("Refresh", id="manual-refresh-btn", n_clicks=0, style=_REFRESH_BUTTON_STYLE),  # WHY: Bump.
            html_mod.Span(
                id="countdown-display",
                children="Clients: 30s | RF: 5m",  # WHY: Live countdown text.
                style={"fontSize": "11px", "color": "#667eea", "marginRight": "15px", "verticalAlign": "middle"},
            ),
        ],
        style=_AUTO_REFRESH_GROUP_STYLE,  # WHY: Border + padding define the group visually.
    )


def _utility_button(html_mod: Any, label: str, btn_id: str, style: dict[str, Any]) -> Any:  # WHY: Uniform buttons.
    """Return a header utility button with pre-built style dict."""
    return html_mod.Button(label, id=btn_id, n_clicks=0, style=style)  # WHY: Single-shot factory.


# Precomputed button styles for the header utility strip -- kept as
# module-level constants so the builder functions above stay well under
# the STRUCT-LENGTH ceiling and the styles can be reused verbatim.
_AUTO_REFRESH_GROUP_STYLE = {  # WHY: Bordered pill around auto-refresh controls.
    "display": "inline-block",
    "marginRight": "20px",
    "padding": "5px 10px",
    "backgroundColor": "#1a1a1a",
    "borderRadius": "4px",
    "border": "1px solid #444",
}
_REFRESH_BUTTON_STYLE = {  # WHY: Manual refresh button style.
    "marginRight": "15px",
    "padding": "6px 12px",
    "backgroundColor": "#3d3d3d",
    "color": "#00ff00",
    "border": "1px solid #00ff00",
    "borderRadius": "4px",
    "cursor": "pointer",
    "fontSize": "12px",
    "verticalAlign": "middle",
}
_AUTOZONE_STYLE = {  # WHY: Solid purple call-to-action button.
    "marginRight": "10px",
    "padding": "8px 15px",
    "backgroundColor": "#667eea",
    "color": "white",
    "border": "none",
    "borderRadius": "4px",
    "cursor": "pointer",
    "fontWeight": "bold",
}
_VBEACON_STYLE = {  # WHY: Outlined green vBeacon button.
    "marginRight": "10px",
    "padding": "8px 15px",
    "backgroundColor": "#3d3d3d",
    "color": "#00ff00",
    "border": "1px solid #00ff00",
    "borderRadius": "4px",
    "cursor": "pointer",
}
_BLE_BEACON_STYLE = {  # WHY: Outlined blue BLE beacon button.
    "marginRight": "10px",
    "padding": "8px 15px",
    "backgroundColor": "#3d3d3d",
    "color": "#00bfff",
    "border": "1px solid #00bfff",
    "borderRadius": "4px",
    "cursor": "pointer",
}
_NEUTRAL_STYLE = {  # WHY: Neutral neutral-purple outlined button.
    "marginRight": "10px",
    "padding": "8px 15px",
    "backgroundColor": "#3d3d3d",
    "color": "#e0e0e0",
    "border": "1px solid #667eea",
    "borderRadius": "4px",
    "cursor": "pointer",
}
_DELETE_STYLE = {  # WHY: Destructive delete button (red outline).
    "marginRight": "10px",
    "padding": "8px 15px",
    "backgroundColor": "#3d3d3d",
    "color": "#ff4444",
    "border": "1px solid #ff4444",
    "borderRadius": "4px",
    "cursor": "pointer",
}
_CLONE_STYLE = {  # WHY: Clone button (green outline, bold).
    "padding": "8px 15px",
    "backgroundColor": "#3d3d3d",
    "color": "#00ff88",
    "border": "1px solid #00ff88",
    "borderRadius": "4px",
    "cursor": "pointer",
    "fontWeight": "bold",
}


def _build_clone_panel(html_mod: Any, dcc_mod: Any, map_data: dict[str, Any]) -> Any:  # WHY: Hidden clone panel.
    """Return the hidden clone-name input panel (revealed by [+] Clone button)."""
    default_name = f"{map_data.get('name', 'Map')} (Copy)"  # WHY: Prefill with '<name> (Copy)'.
    return html_mod.Div(  # WHY: Whole panel wrapped in a display:none div.
        id="clone-panel",
        children=[
            html_mod.Div(
                _build_clone_panel_contents(html_mod, dcc_mod, default_name),
                style={"display": "flex", "alignItems": "center", "justifyContent": "center"},
            )
        ],
        style={
            "display": "none",
            "padding": "12px 20px",  # WHY: Hidden by default. Padded when shown.
            "backgroundColor": "#1a1a1a",
            "borderBottom": "1px solid #00ff88",
        },
    )


def _build_clone_panel_contents(html_mod: Any, dcc_mod: Any, default_name: str) -> list[Any]:  # WHY: Inner children.
    """Return the label/input/buttons inside the clone panel."""
    return [
        html_mod.Span(
            "[+] Clone Map: ",  # WHY: Panel label.
            style={"color": "#00ff88", "fontWeight": "bold", "marginRight": "10px"},
        ),
        dcc_mod.Input(
            id="clone-name-input",
            type="text",  # WHY: New map name input.
            placeholder=default_name,
            value=default_name,
            style=_CLONE_INPUT_STYLE,
        ),
        html_mod.Button("Execute Clone", id="execute-clone-btn", n_clicks=0, style=_CLONE_EXECUTE_STYLE),  # WHY: Go.
        html_mod.Button("Cancel", id="cancel-clone-btn", n_clicks=0, style=_CLONE_CANCEL_STYLE),  # WHY: Bail.
        html_mod.Span(
            id="clone-status",  # WHY: Status text updated by callback.
            style={"marginLeft": "15px", "color": "#e0e0e0", "fontSize": "13px"},
        ),
    ]


_CLONE_INPUT_STYLE = {  # WHY: Clone name input styling.
    "width": "300px",
    "padding": "8px 12px",
    "backgroundColor": "#2a2a2a",
    "color": "#e0e0e0",
    "border": "1px solid #00ff88",
    "borderRadius": "4px",
    "marginRight": "10px",
}
_CLONE_EXECUTE_STYLE = {  # WHY: Green solid execute button.
    "padding": "8px 15px",
    "backgroundColor": "#00ff88",
    "color": "#1a1a1a",
    "border": "none",
    "borderRadius": "4px",
    "cursor": "pointer",
    "fontWeight": "bold",
    "marginRight": "10px",
}
_CLONE_CANCEL_STYLE = {  # WHY: Red-outlined cancel button.
    "padding": "8px 15px",
    "backgroundColor": "#3d3d3d",
    "color": "#ff4444",
    "border": "1px solid #ff4444",
    "borderRadius": "4px",
    "cursor": "pointer",
}


def _build_delete_panel(html_mod: Any, map_data: dict[str, Any]) -> Any:  # WHY: Hidden delete confirmation panel.
    """Return the hidden delete-confirmation panel (revealed by [X] Delete)."""
    return html_mod.Div(  # WHY: Whole panel wrapped in a display:none div.
        id="delete-panel",
        children=[
            html_mod.Div(
                _build_delete_panel_contents(html_mod, map_data),
                style={"display": "flex", "alignItems": "center", "justifyContent": "center"},
            )
        ],
        style={
            "display": "none",
            "padding": "12px 20px",  # WHY: Hidden until delete button toggles it.
            "backgroundColor": "#330000",
            "borderBottom": "2px solid #ff4444",
        },
    )


def _build_delete_panel_contents(html_mod: Any, map_data: dict[str, Any]) -> list[Any]:  # WHY: Delete panel children.
    """Return the warning/label/buttons inside the delete panel."""
    return [
        html_mod.Span(
            "X DESTRUCTIVE: Delete this floorplan? ",  # WHY: Bold warning message.
            style={"color": "#ff4444", "fontWeight": "bold", "marginRight": "10px"},
        ),
        html_mod.Span(
            id="delete-map-name-display",  # WHY: Confirms which map will be deleted.
            children=f"Map: {map_data.get('name', 'Unknown')}",
            style={"color": "#ffaa00", "marginRight": "20px"},
        ),
        html_mod.Button(
            "YES - DELETE MAP", id="confirm-delete-btn", n_clicks=0, style=_DELETE_CONFIRM_STYLE  # WHY: Confirmation.
        ),
        html_mod.Button("Cancel", id="cancel-delete-btn", n_clicks=0, style=_DELETE_CANCEL_STYLE),  # WHY: Bail out.
        html_mod.Span(
            id="delete-status",  # WHY: Status text updated by callback.
            style={"marginLeft": "15px", "color": "#e0e0e0", "fontSize": "13px"},
        ),
    ]


_DELETE_CONFIRM_STYLE = {  # WHY: Bold red confirmation button.
    "padding": "8px 15px",
    "backgroundColor": "#ff4444",
    "color": "white",
    "border": "none",
    "borderRadius": "4px",
    "cursor": "pointer",
    "fontWeight": "bold",
    "marginRight": "10px",
}
_DELETE_CANCEL_STYLE = {  # WHY: Green-outlined cancel button.
    "padding": "8px 15px",
    "backgroundColor": "#3d3d3d",
    "color": "#00ff88",
    "border": "1px solid #00ff88",
    "borderRadius": "4px",
    "cursor": "pointer",
}


def _build_main_container(html_mod: Any, dcc_mod: Any, ctx: dict[str, Any]) -> Any:  # WHY: Map + sidebar row.
    """Return the main content Div: map graph on the left, sidebar on the right."""
    return html_mod.Div(  # WHY: Two-column flex row (CSS class 'main-container').
        [
            _build_map_graph_area(html_mod, dcc_mod, ctx["fig"], ctx["data"].map_data),  # WHY: Left column.
            _build_sidebar_column(html_mod, dcc_mod, ctx),  # WHY: Right column.
        ],
        className="main-container",  # WHY: Layout handled via external CSS class.
    )


def _build_map_graph_area(html_mod: Any, dcc_mod: Any, fig: Any, map_data: dict[str, Any]) -> Any:
    """Return the left-column Div containing the interactive Plotly map graph."""
    return html_mod.Div(  # WHY: Wrapper Div (class map-container) controls flex sizing.
        [
            dcc_mod.Graph(  # WHY: Plotly graph component.
                id="map-display",
                figure=fig,  # WHY: Bind figure created earlier.
                config=_graph_config(map_data),  # WHY: Extracted config dict.
                style={"height": "100%", "width": "100%"},  # WHY: Fill the container.
            ),
        ],
        className="map-container",  # WHY: External CSS controls flex sizing.
    )


def _graph_config(map_data: dict[str, Any]) -> dict[str, Any]:  # WHY: Extracted config dict keeps builder small.
    """Return the ``dcc.Graph`` config dict enabling drawing tools + PNG export."""
    return {  # WHY: Plotly graph config -- drawing toolbar, editable shapes, PNG export.
        "displayModeBar": True,
        "displaylogo": False,  # WHY: Show toolbar without Plotly branding.
        "modeBarButtonsToAdd": [  # WHY: Drawing tools + eraser.
            "drawline",
            "drawopenpath",
            "drawclosedpath",
            "drawcircle",
            "drawrect",
            "eraseshape",
        ],
        "scrollZoom": True,
        "editable": True,  # WHY: Wheel-zoom + shape drag.
        "edits": {"shapePosition": True, "annotationPosition": True},  # WHY: Drag existing shapes.
        "toImageButtonOptions": {  # WHY: PNG export options.
            "format": "png",
            "filename": f"map_{map_data.get('name', 'export')}",  # WHY: Prefill with map name.
            "height": 1080,
            "width": 1920,
            "scale": 2,  # WHY: HiDPI export for reports.
        },
    }


def _build_sidebar_column(html_mod: Any, dcc_mod: Any, ctx: dict[str, Any]) -> Any:  # WHY: Right-column control panel.
    """Return the right-column sidebar Div containing all control widgets."""
    return html_mod.Div(  # WHY: Class 'sidebar' handles scrolling + width.
        [
            html_mod.H3("Layer Controls"),  # WHY: Section header.
            *_build_layer_toggle_sections(html_mod, dcc_mod),  # WHY: Multiple layer checklists.
            html_mod.Hr(),
            *_build_drawing_tools_section(html_mod, dcc_mod),  # WHY: Drawing + zone-input + save + clear + deletes.
            html_mod.Hr(),
            *_build_measurement_help_section(html_mod),  # WHY: Static help text for measurement.
            html_mod.Hr(),
            *_build_scale_setter_section(html_mod, dcc_mod),  # WHY: Set-scale input + button.
            html_mod.Hr(),
            *_build_origin_setter_section(html_mod, ctx["data"].map_data),  # WHY: Set-origin button + status.
            html_mod.Hr(),
            *_build_zones_section(html_mod, dcc_mod, ctx),  # WHY: Zone listing + edit/remove buttons.
            html_mod.Hr(),
            _build_map_info_section(html_mod, ctx),  # WHY: Static info readout.
            html_mod.Hr(),
            _build_click_data_section(html_mod),  # WHY: Placeholder for click-to-inspect callback output.
        ],
        className="sidebar",  # WHY: External CSS controls widths + scroll behavior.
    )


def _build_layer_toggle_sections(html_mod: Any, dcc_mod: Any) -> list[Any]:  # WHY: Grouped checklist heads.
    """Return the five layer-toggle checklists (infrastructure, beacons, clients, devices, filters)."""
    sections: list[Any] = []  # WHY: Accumulated header + checklist pairs.
    for section in _LAYER_TOGGLE_SECTIONS:  # WHY: Iterate the section spec table.
        sections.extend(_build_layer_toggle_section(html_mod, dcc_mod, section))
    return sections


def _build_layer_toggle_section(html_mod: Any, dcc_mod: Any, spec: dict[str, Any]) -> list[Any]:
    """Return the (subhead, Checklist) pair for a single layer-toggle section."""
    return [  # WHY: Two-element block appended by the caller.
        _sidebar_subhead(html_mod, spec["title"], margin_top=spec.get("margin_top", "0")),  # WHY: Section label.
        dcc_mod.Checklist(  # WHY: Layer toggle checklist widget.
            id=spec["id"],  # WHY: Callback binding ID.
            options=spec["options"],  # WHY: Layer option list.
            value=spec["value"],  # WHY: Default checked layers.
            labelStyle=_CHECK_LABEL_STYLE,  # WHY: Shared block-label style.
            style={"marginBottom": "10px"},  # WHY: Space between sections.
        ),
    ]


def _sidebar_subhead(html_mod: Any, text: str, margin_top: str = "0") -> Any:  # WHY: Small styled subheader.
    """Return a small purple ``html.H4`` used as a sidebar section header."""
    return html_mod.H4(  # WHY: Standard sidebar subhead style.
        text,
        style={"fontSize": "13px", "color": "#667eea", "marginTop": margin_top, "marginBottom": "5px"},
    )


_LAYER_TOGGLE_OPTIONS = [  # WHY: Options for infrastructure layer checklist.
    {"label": " [W] Walls", "value": "walls"},
    {"label": " [M] Wayfinding", "value": "wayfinding"},
    {"label": " [Z] Location Zones", "value": "zones"},
    {"label": " [P] Proximity Zones", "value": "proximity_zones"},
    {"label": " [V] Validation Paths", "value": "validation"},
    {"label": " [R] RF Diagnostics Heatmap", "value": "rf_heatmap"},
    {"label": " [O] Map Origin", "value": "origin"},
]
_BEACON_TOGGLE_OPTIONS = [  # WHY: Options for beacon/positioning checklist.
    {"label": " [vB] Virtual Beacons", "value": "vbeacons"},
    {"label": " [C] vBeacon Coverage", "value": "vbeacon_coverage"},
    {"label": " [3P] 3rd Party Beacons", "value": "ble_beacons"},
]
_CLIENT_TOGGLE_OPTIONS = [  # WHY: Options for client checklist.
    {"label": " [Wi] WiFi Clients", "value": "wifi_clients"},
    {"label": " [Wr] Wired Clients", "value": "wired_clients"},
    {"label": " [Ex] Excluded Clients", "value": "excluded_clients"},
    {"label": " [AP] Show Associated AP", "value": "show_client_ap"},
]
_DEVICE_TOGGLE_OPTIONS = [  # WHY: Options for device checklist.
    {"label": " [AP] Access Points", "value": "aps"},
    {"label": " [SW] Switches", "value": "switches"},
    {"label": " [GW] Gateways", "value": "gateways"},
    {"label": " [MS] Mesh Associations", "value": "mesh_links"},
]
_FILTER_TOGGLE_OPTIONS = [  # WHY: Options for filter checklist.
    {"label": " [HI] Hide Inactive Items", "value": "hide_inactive"},
]
_CHECK_LABEL_STYLE = {"display": "block", "margin": "8px 0", "fontSize": "13px"}  # WHY: Checklist label style.

_LAYER_TOGGLE_SECTIONS = [  # WHY: Table drives _build_layer_toggle_sections loop.
    {
        "title": "Infrastructure",
        "id": "layer-toggle",  # WHY: Walls/wayfinding/zones section.
        "options": _LAYER_TOGGLE_OPTIONS,
        "value": ["walls", "wayfinding", "zones", "validation"],  # WHY: Defaults visible.
        "margin_top": "10px",  # WHY: First section pushes down from Hr above.
    },
    {
        "title": "Beacons & Positioning",
        "id": "beacon-toggle",  # WHY: vBeacon/coverage/BLE section.
        "options": _BEACON_TOGGLE_OPTIONS,
        "value": ["vbeacons", "ble_beacons"],  # WHY: Defaults visible.
    },
    {
        "title": "Clients",
        "id": "client-toggle",  # WHY: Client section.
        "options": _CLIENT_TOGGLE_OPTIONS,
        "value": ["wifi_clients", "wired_clients", "show_client_ap"],  # WHY: Defaults visible.
    },
    {
        "title": "Devices",
        "id": "device-toggle",  # WHY: APs/switches/gateways/mesh section.
        "options": _DEVICE_TOGGLE_OPTIONS,
        "value": ["aps", "switches", "gateways"],  # WHY: Defaults visible.
    },
    {
        "title": "Filters",
        "id": "filter-toggle",  # WHY: Hide-inactive filter section.
        "options": _FILTER_TOGGLE_OPTIONS,
        "value": [],  # WHY: No filters checked by default.
    },
]


def _build_drawing_tools_section(html_mod: Any, dcc_mod: Any) -> list[Any]:  # WHY: Drawing header + sub-widgets.
    """Return the drawing-tools sidebar block: help, mode dropdown, zone input, action + delete buttons."""
    return [
        html_mod.H3("Drawing Tools"),  # WHY: Section title.
        _build_drawing_help_details(html_mod),  # WHY: Collapsible "How to use" block.
        _build_drawing_mode_dropdown(html_mod, dcc_mod),  # WHY: Path / Zone / Wall / Measure selector.
        _build_zone_name_input(html_mod, dcc_mod),  # WHY: Zone-name input revealed for Zone mode.
        _build_drawing_action_buttons(html_mod),  # WHY: Save-shape + clear-drawings.
        html_mod.Hr(style={"margin": "10px 0"}),
        html_mod.P(
            "Delete from Mist API:",  # WHY: Section label.
            style={"fontSize": "12px", "color": "#ff6666", "marginBottom": "8px"},
        ),
        _build_delete_from_mist_buttons(html_mod),  # WHY: 4 destructive delete buttons.
        html_mod.Div(
            id="drawing-tool-status",  # WHY: Live status for save/delete callbacks.
            style={"fontSize": "11px", "color": "#a0a0ff", "marginTop": "8px", "minHeight": "40px"},
        ),
    ]


def _build_drawing_help_details(html_mod: Any) -> Any:  # WHY: Collapsible instructions block.
    """Return the collapsible "How to use" details element for drawing tools."""
    return html_mod.Details(  # WHY: Native disclosure widget.
        [
            html_mod.Summary(
                "How to use",  # WHY: Clickable summary.
                style={"fontSize": "12px", "color": "#00bfff", "cursor": "pointer", "marginBottom": "8px"},
            ),
            html_mod.Div(
                _build_drawing_help_paragraphs(html_mod),
                style={
                    "backgroundColor": "#2a2a2a",
                    "padding": "8px",  # WHY: Boxed help block.
                    "borderRadius": "4px",
                    "marginBottom": "10px",
                },
            ),
        ],
        open=False,  # WHY: Collapsed by default.
    )


def _build_drawing_help_paragraphs(html_mod: Any) -> list[Any]:  # WHY: The actual help lines.
    """Return the list of help ``html.P`` elements shown when the details block is expanded."""
    return [  # WHY: Numbered instructions + color-coded shape reminders.
        html_mod.P("1. Select a Drawing Mode below", style=_HELP_STYLE_NEUTRAL),
        html_mod.P("2. Use toolbar above map to draw shape", style=_HELP_STYLE_NEUTRAL),
        html_mod.P("3. Click 'Save Last Shape to Mist'", style=_HELP_STYLE_NEUTRAL),
        html_mod.P("Zones: Draw rectangle for coverage areas", style=_HELP_STYLE_BLUE),
        html_mod.P("Walls: Draw line for RF attenuation", style=_HELP_STYLE_ORANGE),
        html_mod.P(
            "Paths: Draw line for validation routes",  # WHY: Magenta = validation paths.
            style={"fontSize": "11px", "color": "#ff00ff", "margin": "4px 0 8px 10px"},
        ),
    ]


_HELP_STYLE_NEUTRAL = {"fontSize": "11px", "color": "#aaa", "margin": "4px 0 4px 10px"}  # WHY: Neutral gray help line.
_HELP_STYLE_BLUE = {"fontSize": "11px", "color": "#00bfff", "margin": "4px 0 4px 10px"}  # WHY: Zone hint.
_HELP_STYLE_ORANGE = {"fontSize": "11px", "color": "#ffa500", "margin": "4px 0 4px 10px"}  # WHY: Wall hint.


def _build_drawing_mode_dropdown(html_mod: Any, dcc_mod: Any) -> Any:  # WHY: Mode selector widget.
    """Return the drawing-mode dropdown Div (Path / Zone / Wall / Measure)."""
    return html_mod.Div(  # WHY: Wrap label + dropdown together.
        [
            html_mod.Label(
                "Drawing Mode:", style={"fontSize": "12px", "color": "#888", "marginBottom": "4px"}  # WHY: Field label.
            ),
            dcc_mod.Dropdown(  # WHY: Mode selector.
                id="drawing-mode-dropdown",
                options=[  # WHY: Four modes -- validation path, zone rect, wall, measure-only.
                    {"label": "Validation Path (magenta)", "value": "path"},
                    {"label": "Zone Rectangle (cyan)", "value": "zone"},
                    {"label": "Wall Segment (orange)", "value": "wall"},
                    {"label": "Measurement Only", "value": "measure"},
                ],
                value="measure",  # WHY: Default so drawing does not save anything unintentionally.
                clearable=False,
                style={"marginBottom": "10px", "color": "#e0e0e0"},
                className="dark-dropdown",
            ),
        ],
        style={"marginBottom": "10px"},
    )


def _build_zone_name_input(html_mod: Any, dcc_mod: Any) -> Any:  # WHY: Text input for zone label.
    """Return the hidden zone-name input Div (shown when Zone drawing mode is selected)."""
    return html_mod.Div(  # WHY: Container toggled visible by callback.
        [
            dcc_mod.Input(
                id="zone-name-input",
                type="text",  # WHY: Free-text zone label.
                placeholder="Zone name (required)",
                style=_ZONE_NAME_INPUT_STYLE,
            ),
        ],
        id="zone-name-container",
        style={"display": "none"},  # WHY: Hidden until Zone mode is chosen.
    )


_ZONE_NAME_INPUT_STYLE = {  # WHY: Reusable zone-name input styling.
    "width": "100%",
    "padding": "8px",
    "marginBottom": "8px",
    "backgroundColor": "#3d3d3d",
    "color": "#e0e0e0",
    "border": "1px solid #00bfff",
    "borderRadius": "4px",
}


def _build_drawing_action_buttons(html_mod: Any) -> Any:  # WHY: Save-shape + clear-drawings row.
    """Return the Div containing 'Save Last Shape' and 'Clear All Drawings' action buttons."""
    return html_mod.Div(  # WHY: Wrap two full-width action buttons.
        [
            html_mod.Button(
                "[SAVE] Save Last Shape to Mist", id="save-shape-btn", n_clicks=0, style=_SAVE_SHAPE_STYLE  # WHY: Save.
            ),
            html_mod.Button(
                "[CLR] Clear All Drawings",
                id="clear-drawings-btn",
                n_clicks=0,  # WHY: Reset.
                style=_CLEAR_DRAWINGS_STYLE,
            ),
        ]
    )


_SAVE_SHAPE_STYLE = {  # WHY: Green save button.
    "width": "100%",
    "marginBottom": "8px",
    "padding": "10px",
    "backgroundColor": "#28a745",
    "color": "white",
    "border": "none",
    "borderRadius": "4px",
    "cursor": "pointer",
    "fontSize": "13px",
    "fontWeight": "bold",
}
_CLEAR_DRAWINGS_STYLE = {  # WHY: Yellow-outlined clear button.
    "width": "100%",
    "marginBottom": "8px",
    "padding": "8px",
    "backgroundColor": "#3d3d3d",
    "color": "#ffc107",
    "border": "1px solid #ffc107",
    "borderRadius": "4px",
    "cursor": "pointer",
    "fontSize": "13px",
}


def _build_delete_from_mist_buttons(html_mod: Any) -> Any:  # WHY: 4 destructive delete buttons.
    """Return the Div containing the four 'delete X from Mist' buttons."""
    return html_mod.Div(  # WHY: Group 4 full-width delete buttons together.
        [_delete_from_mist_button(html_mod, spec) for spec in _DELETE_FROM_MIST_SPECS]
    )


def _delete_from_mist_button(html_mod: Any, spec: dict[str, str]) -> Any:  # WHY: One row of the delete panel.
    """Return a single delete-from-Mist button constructed from the spec dict."""
    return html_mod.Button(  # WHY: Full-width outlined destructive button.
        spec["label"],  # WHY: User-visible action text.
        id=spec["id"],  # WHY: Callback binding ID.
        n_clicks=0,  # WHY: Track click count.
        style=_delete_row_style(spec["color"]),  # WHY: Shared row styling.
    )


_DELETE_FROM_MIST_SPECS = [  # WHY: Table driving the 4 destructive Mist API delete buttons.
    {"label": "Delete Validation Paths", "id": "delete-paths-btn", "color": "#ff4444"},  # WHY: Wipe paths.
    {"label": "Delete Wayfinding Paths", "id": "delete-wayfinding-btn", "color": "#ff8844"},  # WHY: Wipe wayfinding.
    {"label": "Delete All Walls", "id": "delete-walls-btn", "color": "#ff4444"},  # WHY: Wipe walls.
    {"label": "Delete All Zones", "id": "delete-zones-btn", "color": "#ff66ff"},  # WHY: Wipe zones.
]


def _delete_row_style(color: str) -> dict[str, Any]:  # WHY: Consistent styling for 4 delete rows.
    """Return the shared delete-row style dict parameterized by the accent color."""
    return {  # WHY: Full-width outlined destructive button.
        "width": "100%",
        "marginBottom": "6px",
        "padding": "6px",
        "backgroundColor": "#3d3d3d",
        "color": color,
        "border": f"1px solid {color}",
        "borderRadius": "4px",
        "cursor": "pointer",
        "fontSize": "11px",
    }


def _build_measurement_help_section(html_mod: Any) -> list[Any]:  # WHY: Static measurement help text.
    """Return the measurement-tools sidebar help paragraphs."""
    return [
        html_mod.H3("Measurement Tools"),  # WHY: Section header.
        html_mod.P("Use the toolbar above the map:", style={"fontSize": "12px", "color": "#888"}),
        html_mod.P("- Draw Line - Measure distances", style=_MEASURE_HELP_STYLE),
        html_mod.P("- Draw Path - Create routes", style=_MEASURE_HELP_STYLE),
        html_mod.P("- Draw Circle - Mark areas", style=_MEASURE_HELP_STYLE),
        html_mod.P("- Erase - Remove drawings", style=_MEASURE_HELP_STYLE),
    ]


_MEASURE_HELP_STYLE = {"fontSize": "11px", "marginLeft": "10px", "color": "#999"}  # WHY: Measurement help style.


def _build_scale_setter_section(html_mod: Any, dcc_mod: Any) -> list[Any]:  # WHY: Set-scale controls.
    """Return the set-scale controls: instructions + length input + apply button + status Div."""
    return [
        html_mod.H3("Set Scale"),  # WHY: Section header.
        html_mod.P("1. Draw a line of known length", style={"fontSize": "11px", "color": "#888"}),
        html_mod.P("2. Enter actual length below", style={"fontSize": "11px", "color": "#888"}),
        html_mod.Div(  # WHY: Wrapper for input + button + status.
            [
                dcc_mod.Input(
                    id="scale-length-input",
                    type="number",  # WHY: Meters input.
                    placeholder="Length in meters",
                    style=_SCALE_INPUT_STYLE,
                ),
                html_mod.Button(
                    "Set Scale from Last Line", id="set-scale-button", style=_SCALE_APPLY_STYLE  # WHY: Apply button.
                ),
                html_mod.Div(
                    id="scale-status",  # WHY: Live status text.
                    style={"marginTop": "8px", "fontSize": "11px", "color": "#a0a0ff"},
                ),
            ]
        ),
    ]


_SCALE_INPUT_STYLE = {  # WHY: Scale-input styling.
    "width": "100%",
    "padding": "8px",
    "marginBottom": "8px",
    "backgroundColor": "#3d3d3d",
    "color": "#e0e0e0",
    "border": "1px solid #667eea",
    "borderRadius": "4px",
}
_SCALE_APPLY_STYLE = {  # WHY: Purple apply button.
    "width": "100%",
    "padding": "8px",
    "backgroundColor": "#667eea",
    "color": "white",
    "border": "none",
    "borderRadius": "4px",
    "cursor": "pointer",
    "fontWeight": "bold",
}


def _build_origin_setter_section(html_mod: Any, map_data: dict[str, Any]) -> list[Any]:  # WHY: Set-origin controls.
    """Return the set-origin controls: instructions + enable button + current-origin readout."""
    return [
        html_mod.H3("Set Origin"),  # WHY: Section header.
        html_mod.P("Click map to set coordinate origin", style={"fontSize": "11px", "color": "#888"}),
        html_mod.Div(  # WHY: Wrapper for button + status.
            [
                html_mod.Button(
                    "Enable Origin Setting Mode",
                    id="origin-mode-button",
                    n_clicks=0,  # WHY: Toggle.
                    style=_ORIGIN_BUTTON_STYLE,
                ),
                html_mod.Div(
                    id="origin-status",
                    children=[
                        html_mod.P(  # WHY: Show current origin coordinates.
                            f"Current: ({map_data.get('origin_x', 0)}, {map_data.get('origin_y', 0)})",
                            style={"fontSize": "11px", "color": "#888", "margin": "4px 0"},
                        )
                    ],
                ),
            ]
        ),
    ]


_ORIGIN_BUTTON_STYLE = {  # WHY: Full-width outlined toggle button.
    "width": "100%",
    "padding": "8px",
    "marginBottom": "8px",
    "backgroundColor": "#3d3d3d",
    "color": "white",
    "border": "1px solid #667eea",
    "borderRadius": "4px",
    "cursor": "pointer",
    "fontWeight": "bold",
}


def _build_zones_section(html_mod: Any, dcc_mod: Any, ctx: dict[str, Any]) -> list[Any]:  # WHY: Location zones panel.
    """Return the location-zones sidebar block: toggle widget + selected-zone info + edit/remove buttons."""
    zones = ctx["data"].zones  # WHY: Local for readability.
    viewer = ctx["_launcher"]._viewer  # WHY: Reach wrapper method _build_zone_toggle_widget.
    widget = viewer._build_zone_toggle_widget(zones, dcc_mod, html_mod)  # WHY: Real zone toggle checkbox list.
    return [
        html_mod.H3("Location Zones"),  # WHY: Section header.
        html_mod.Div(  # WHY: Wrapper containing zone toggle widget + info panel + buttons.
            [
                widget,  # WHY: Toggle widget produced by the wrapper (may be None if zones empty).
                html_mod.Div(
                    id="selected-zone-info",  # WHY: Callback writes zone details here.
                    children=[
                        html_mod.P(
                            "Click a zone for details",
                            style={"fontSize": "11px", "color": "#888", "fontStyle": "italic"},
                        )
                    ],
                    style={"padding": "10px", "backgroundColor": "#3d3d3d", "borderRadius": "4px", "marginTop": "10px"},
                ),
                _build_zone_edit_buttons(html_mod) if zones else None,  # WHY: Edit/Remove buttons only w/ zones.
            ]
        ),
    ]


def _build_zone_edit_buttons(html_mod: Any) -> Any:  # WHY: Edit + Remove zone buttons (only if zones exist).
    """Return the Edit/Remove zone buttons Div shown when at least one zone exists."""
    return html_mod.Div(  # WHY: Two-column edit + remove row.
        [
            html_mod.Button(
                "[EDIT] Edit Zone", id="edit-zone-btn", n_clicks=0, style=_ZONE_EDIT_STYLE  # WHY: Edit selected zone.
            ),
            html_mod.Button(
                "[DEL] Remove Zone",
                id="remove-zone-btn",
                n_clicks=0,  # WHY: Delete selected zone.
                style=_ZONE_REMOVE_STYLE,
            ),
        ],
        style={"marginTop": "10px", "display": "flex"},
    )


_ZONE_EDIT_STYLE = {  # WHY: Purple 48%-width edit button.
    "width": "48%",
    "marginRight": "4%",
    "padding": "6px",
    "backgroundColor": "#667eea",
    "color": "white",
    "border": "none",
    "borderRadius": "4px",
    "cursor": "pointer",
    "fontSize": "12px",
}
_ZONE_REMOVE_STYLE = {  # WHY: Red 48%-width delete button.
    "width": "48%",
    "padding": "6px",
    "backgroundColor": "#ff4444",
    "color": "white",
    "border": "none",
    "borderRadius": "4px",
    "cursor": "pointer",
    "fontSize": "12px",
}


def _build_map_info_section(html_mod: Any, ctx: dict[str, Any]) -> Any:  # WHY: Static info readout Div.
    """Return the map-info sidebar block: dimensions, ppm, orientation, and per-entity counts."""
    data = ctx["data"]  # WHY: Local shortcut for readability.
    map_data = data.map_data
    map_width = map_data.get("width", 1000)
    map_height = map_data.get("height", 1000)
    return html_mod.Div(  # WHY: Contains H3 header + counts paragraphs.
        id="map-info",
        children=[
            html_mod.H3("Map Info"),  # WHY: Section header lives inside for a11y.
            *_map_info_paragraphs(html_mod, map_data, map_width, map_height, data),
        ],
    )


def _map_info_paragraphs(  # WHY: Build all 9 info paragraphs.
    html_mod: Any,
    map_data: dict[str, Any],
    map_width: int,
    map_height: int,
    data: MapViewerData,
) -> list[Any]:
    """Return the list of ``html.P`` info rows shown in the Map Info panel."""
    return [
        _info_row(html_mod, "Dimensions: ", f"{map_width} x {map_height} px"),  # WHY: Canvas size.
        _info_row(html_mod, "PPM: ", f"{map_data.get('ppm', 'N/A')}"),  # WHY: Pixels per meter.
        _info_row(html_mod, "Orientation: ", f"{map_data.get('orientation', 0)} deg"),  # WHY: Map orientation.
        _info_row(html_mod, "Devices: ", f"{len(data.devices)}"),  # WHY: Device count.
        _info_row(html_mod, "Clients: ", f"{len(data.clients)}"),  # WHY: Client count.
        _info_row(html_mod, "Zones: ", f"{len(data.zones)}"),  # WHY: Zone count.
        _info_row(html_mod, "vBeacons: ", f"{len(map_data.get('vbeacons', []))}"),  # WHY: Virtual beacon count.
        _info_row(html_mod, "BLE Beacons: ", f"{len(map_data.get('beacons', []))}"),  # WHY: BLE beacon count.
        _info_row(html_mod, "Validation Paths: ", f"{len(map_data.get('sitesurvey_path', []))}"),  # WHY: Paths.
    ]


def _info_row(html_mod: Any, label: str, value: str) -> Any:  # WHY: Uniform label-value paragraph.
    """Return an info-row ``html.P`` with badge label + value text."""
    return html_mod.P([html_mod.Span(label, className="info-badge"), value])  # WHY: Badge class handles styling.


def _build_click_data_section(html_mod: Any) -> Any:  # WHY: Placeholder Div for click callback output.
    """Return the click-data placeholder Div (populated by the display_click_data callback)."""
    return html_mod.Div(  # WHY: Sidebar Div toggled by click callback.
        id="click-data",
        children=[
            html_mod.H3("Device Info"),  # WHY: Header before device details.
            html_mod.P(
                "Click a device for details", style={"color": "#888", "fontStyle": "italic"}  # WHY: Empty-state hint.
            ),
        ],
    )


def _build_state_stores(dcc_mod: Any, ctx: dict[str, Any]) -> list[Any]:  # WHY: 6 dcc.Store components.
    """Return the 6 hidden ``dcc.Store`` components used for map/site/zone state."""
    serializer = ctx["helpers"]["serializer"]  # WHY: Local shortcut.
    return [  # WHY: Ordered list preserves render order for Dash reconciliation.
        _map_config_store(dcc_mod, ctx),
        dcc_mod.Store(
            id="available-maps-store",  # WHY: Sibling maps list for dropdown.
            data=serializer.build_named_items(ctx["all_maps"], default_name="Unnamed"),
        ),
        dcc_mod.Store(
            id="available-sites-store",  # WHY: Sibling sites list for dropdown.
            data=serializer.build_named_items(ctx["all_sites"], default_name="Unnamed Site"),
        ),
        dcc_mod.Store(id="selected-zone-store", data=serializer.build_selected_zone_store()),  # WHY: Zone selection.
        dcc_mod.Store(id="refresh-times-store", data=serializer.build_refresh_times_store()),  # WHY: Last-refresh ts.
        dcc_mod.Store(id="cache-bust-store", data=serializer.build_cache_bust_store()),  # WHY: Clone/delete reload.
    ]


def _map_config_store(dcc_mod: Any, ctx: dict[str, Any]) -> Any:  # WHY: Split largest store out of _build_state_stores.
    """Return the ``map-config-store`` Store carrying the current map identity payload."""
    serializer = ctx["helpers"]["serializer"]  # WHY: Local shortcut.
    data, scope = ctx["data"], ctx["scope"]  # WHY: Local shortcuts.
    params = MapConfigParams(  # WHY: Frozen bundle keeps builder signature 1-arg.
        site_id=scope.site_id,
        site_name=scope.site_name,
        map_id=scope.map_id,
        map_name=data.map_data.get("name", "Unknown"),
        ppm=ctx["ppm"],
        map_width=data.map_data.get("width", 1000),
        map_height=data.map_data.get("height", 1000),
    )
    return dcc_mod.Store(  # WHY: Store holds the map-identity dict for JS callbacks.
        id="map-config-store",
        data=serializer.build_map_config(params),  # WHY: Current-map identity payload.
    )


def _build_refresh_intervals(dcc_mod: Any) -> list[Any]:  # WHY: 3 dcc.Interval components for periodic refresh.
    """Return the three periodic ``dcc.Interval`` components (clients, coverage, countdown)."""
    return [
        dcc_mod.Interval(
            id="client-refresh-interval",  # WHY: Wireless client positions refresh cadence.
            interval=30 * 1000,
            n_intervals=0,
            disabled=False,
        ),  # WHY: 30s poll.
        dcc_mod.Interval(
            id="coverage-refresh-interval",  # WHY: RF coverage refresh cadence.
            interval=5 * 60 * 1000,
            n_intervals=0,
            disabled=False,
        ),  # WHY: 5m poll.
        dcc_mod.Interval(
            id="countdown-tick-interval",  # WHY: Drives the header countdown display.
            interval=1000,
            n_intervals=0,
            disabled=False,
        ),  # WHY: 1s tick.
    ]
