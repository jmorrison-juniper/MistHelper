"""Site/scale/dropdown cluster extracted from ``viewer_callbacks.py``.

Owns the Wave-E2 public callbacks ``set_scale``, ``refresh_map_dropdown``,
``handle_site_from_url``, ``sync_dropdown_with_url`` and
``handle_site_switch_from_dropdown`` plus their private helpers
(scale calibration, site payload construction, background image
injection, device trace rendering).  Follows the same wrapper-class +
``__getattr__`` template used by :mod:`src.capture._packet_capture_org`
so the parent
:class:`~src.maps.launcher.viewer_callbacks.MapViewerCallbacks` stays a
thin coordinator that hands each Dash callback off to the appropriate
cluster.
"""

from __future__ import annotations  # WHY: postponed evaluation consistent with parent module

import logging  # WHY: audit trail for site-switch diagnostics
from typing import TYPE_CHECKING, Any  # WHY: opaque manager + type-permissive Dash callback args

if TYPE_CHECKING:  # WHY: keep dash imports lazy at runtime
    from dash import Dash  # WHY: annotation reference for register(app)


# ----------------------------------------------------------------------
# Module-level constants (magic numbers + repeated literals extracted)
# ----------------------------------------------------------------------

_HTTP_OK = 200  # WHY: named constant clearer than magic 200 in every guard
_DEFAULT_MAP_NAME = "Unnamed"  # WHY: matches original name-missing label
_DEFAULT_MAP_WIDTH = 1000  # WHY: fallback width matches original getattr default
_DEFAULT_MAP_HEIGHT = 1000  # WHY: fallback height matches original getattr default
_DEFAULT_PPM = 1.0  # WHY: pixels-per-meter default preserved from original
_DEVICES_PAGE_LIMIT = 1000  # WHY: paginate ceiling used by original listSiteDevicesStats call
_METERS_TO_FEET = 3.28084  # WHY: unit conversion factor preserved from original
_MARKER_SIZE = 12  # WHY: original marker size for simple device traces
_MARKER_OUTLINE_WIDTH = 1  # WHY: original marker outline width
_TEXT_FONT_SIZE = 10  # WHY: original text font size for device labels
_TITLE_FONT_SIZE = 16  # WHY: original figure-title font size
_TITLE_X_CENTER = 0.5  # WHY: original centered title placement
_MARGIN_TOP_PX = 40  # WHY: original top-margin so title has clearance
_BG_COLOR = "#1e1e1e"  # WHY: original dark background theme
_FG_COLOR = "#e0e0e0"  # WHY: original light foreground colour
_LINE_COLOR = "white"  # WHY: original marker outline colour
_STATUS_CONNECTED_COLOR = "#00ff00"  # WHY: original bright green for connected devices
_STATUS_DISCONNECTED_COLOR = "#ff0000"  # WHY: original bright red for disconnected devices
_STATUS_OTHER_COLOR = "#ffaa00"  # WHY: original amber for unknown/upgrading status


class _ViewerSiteSwitch:  # WHY: wrapper class hosting the site-switch callback cluster
    """Cluster class holding the extracted site/scale/dropdown callbacks + helpers."""

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
    # set_scale + PPM helpers
    # ------------------------------------------------------------------

    def set_scale(  # WHY: Dash callback that calibrates PPM from a user-drawn line
        self,
        n_clicks: int | None,
        actual_length_m: float | None,
        current_fig: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """Calculate and update PPM based on drawn line and known length."""
        logging.info("set_scale: n_clicks=%s, actual_length_m=%s", n_clicks, actual_length_m)  # WHY: entry trace
        if not n_clicks or not actual_length_m or actual_length_m <= 0:  # WHY: guard invalid input
            return "[!] Please enter a valid length in meters", current_fig  # WHY: preserve user-visible error
        shapes = current_fig.get("layout", {}).get("shapes", [])  # WHY: read user-drawn shapes from figure
        last_line = self._find_last_line_shape(shapes)  # WHY: locate most recent line shape
        if not last_line:  # WHY: guard missing ruler line
            return "[!] Please draw a line first using the ruler tool", current_fig  # WHY: preserve original text
        new_ppm = self._compute_new_ppm(last_line, actual_length_m)  # WHY: length_px / known_meters = ppm
        self._store_new_ppm(current_fig, new_ppm)  # WHY: persist PPM in figure metadata
        self._reannotate_measurements(current_fig, shapes, new_ppm)  # WHY: refresh every measurement annotation
        status_msg = self._build_scale_status(new_ppm, actual_length_m, last_line)  # WHY: identical status text
        logging.info(  # WHY: mirror original log line for calibration audit
            "Map scale updated: PPM %s -> %.2f (user calibration: %sm)", self._state.ppm, new_ppm, actual_length_m
        )
        return status_msg, current_fig  # WHY: return status + updated figure

    def _build_scale_status(  # WHY: extract format so set_scale stays ≤25 lines
        self, new_ppm: float, actual_length_m: float, last_line: dict[str, Any]
    ) -> str:
        """Return the byte-identical scale-status string shown in the UI."""
        length_px = self._line_length_px(last_line)  # WHY: reuse for readability
        return (  # WHY: mirror original status string format byte-for-byte
            f"[OK] Scale set! New PPM: {new_ppm:.2f} " f"({actual_length_m:.2f}m = {length_px:.1f}px)"
        )

    @staticmethod
    def _find_last_line_shape(shapes: list[dict[str, Any]]) -> dict[str, Any] | None:  # WHY: newest-first search
        """Return the most recently drawn ``line`` shape (or None)."""
        for shape in reversed(shapes):  # WHY: walk shapes newest first
            if shape.get("type") == "line":  # WHY: match the ruler tool's line shape
                return shape  # WHY: return first match (newest)
        return None  # WHY: no line shape drawn yet

    @staticmethod
    def _line_length_px(line_shape: dict[str, Any]) -> float:  # WHY: pure Euclidean geometry helper
        """Return pixel length of a Plotly line shape via Euclidean distance."""
        x0, y0 = line_shape.get("x0", 0), line_shape.get("y0", 0)  # WHY: line start
        x1, y1 = line_shape.get("x1", 0), line_shape.get("y1", 0)  # WHY: line end
        return float(((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5)  # WHY: coerce Any to float for strict typing

    @classmethod
    def _compute_new_ppm(cls, line_shape: dict[str, Any], actual_length_m: float) -> float:  # WHY: PPM derivation
        """Derive pixels-per-meter from a drawn line + its measured length."""
        return cls._line_length_px(line_shape) / actual_length_m  # WHY: px / meters = ppm

    @staticmethod
    def _store_new_ppm(current_fig: dict[str, Any], new_ppm: float) -> None:  # WHY: mutate meta in place
        """Persist the new PPM into ``layout.meta.ppm`` (creating dict if needed)."""
        if "meta" not in current_fig["layout"]:  # WHY: create meta dict if missing
            current_fig["layout"]["meta"] = {}  # WHY: initialise empty meta bag
        current_fig["layout"]["meta"]["ppm"] = new_ppm  # WHY: store for subsequent annotations

    def _reannotate_measurements(  # WHY: refresh every ruler annotation
        self,
        current_fig: dict[str, Any],
        shapes: list[dict[str, Any]],
        new_ppm: float,
    ) -> None:
        """Refresh every ``... px`` measurement annotation with the new PPM."""
        if "annotations" not in current_fig["layout"]:  # WHY: nothing to update
            return  # WHY: early exit
        for ann_idx, annotation in enumerate(current_fig["layout"]["annotations"]):  # WHY: iterate annotations
            if "px" not in annotation.get("text", ""):  # WHY: skip non-measurement annotations
                continue  # WHY: only ruler annotations contain "px"
            self._update_annotation_text(current_fig, ann_idx, shapes, new_ppm)  # WHY: recalculate this one

    @staticmethod
    def _update_annotation_text(  # WHY: update one measurement annotation
        current_fig: dict[str, Any],
        ann_idx: int,
        shapes: list[dict[str, Any]],
        new_ppm: float,
    ) -> None:
        """Update one measurement annotation's text using the first line shape."""
        for shape in shapes:  # WHY: find the shape paired with this annotation
            if shape.get("type") != "line":  # WHY: skip non-line shapes
                continue  # WHY: only line shapes carry measurements
            sx0, sy0 = shape.get("x0", 0), shape.get("y0", 0)  # WHY: shape line start
            sx1, sy1 = shape.get("x1", 0), shape.get("y1", 0)  # WHY: shape line end
            shape_px = ((sx1 - sx0) ** 2 + (sy1 - sy0) ** 2) ** 0.5  # WHY: recompute length
            shape_m = shape_px / new_ppm  # WHY: convert to meters at new PPM
            shape_ft = shape_m * _METERS_TO_FEET  # WHY: preserve original feet conversion
            current_fig["layout"]["annotations"][ann_idx][  # WHY: mirror original text format exactly
                "text"
            ] = f"<b>{shape_px:.1f} px</b><br>{shape_ft:.2f} ft<br>{shape_m:.2f} m"
            break  # WHY: original code broke after first matching shape

    # ------------------------------------------------------------------
    # refresh_map_dropdown + helpers
    # ------------------------------------------------------------------

    def refresh_map_dropdown(  # WHY: Dash callback that repopulates the map selector
        self,
        _cache_bust_data: Any,
        _manual_clicks: int | None,
        _url_search: str | None,
        config: dict[str, Any] | None,
    ) -> tuple[Any, Any]:
        """Fetch fresh map list from API after clone/delete, manual refresh, or page load."""
        from dash import no_update  # WHY: sentinel used to skip output updates

        site_id_local = self._current_config_site_id(config)  # WHY: site_id is required for the API call
        if not site_id_local:  # WHY: guard - cannot refresh without site context
            logging.warning("Cannot refresh map dropdown: site_id not available")  # WHY: mirror original log
            return no_update, no_update  # WHY: skip updates when site_id missing
        return self._do_refresh_map_dropdown(site_id_local, no_update)  # WHY: extracted body keeps CC low

    def _do_refresh_map_dropdown(  # WHY: extracted body so refresh_map_dropdown stays ≤25 lines and CC ≤5
        self, site_id_local: str, no_update: Any
    ) -> tuple[Any, Any]:
        """Perform the actual fetch + payload build, guarded by outer site_id check."""
        trigger_id = self._resolve_refresh_trigger()  # WHY: identify what fired the callback
        logging.info("Refreshing map dropdown list (trigger: %s)", trigger_id)  # WHY: mirror original log
        try:
            maps_response = self._state.mistapi_ref.api.v1.sites.maps.listSiteMaps(  # WHY: fresh fetch
                self._state.api_session_ref, site_id=site_id_local
            )
            if maps_response.status_code != _HTTP_OK:  # WHY: API failed -> keep current options
                logging.warning("Failed to refresh map list: HTTP %s", maps_response.status_code)  # WHY: mirror log
                return no_update, no_update  # WHY: signal no change on API failure
            return self._build_refresh_payload(maps_response)  # WHY: build options + store from fresh data
        except Exception as refresh_error:  # WHY: catch-all parity with original
            logging.exception("Error refreshing map dropdown: %s", refresh_error)  # WHY: mirror original log
            return no_update, no_update  # WHY: signal no change on exception

    @staticmethod
    def _resolve_refresh_trigger() -> str:  # WHY: extract Dash context lookup so caller stays simple
        """Return the trigger id that fired the refresh callback (or ``initial_load``)."""
        import dash  # WHY: local import - dash.callback_context only exists at request time

        ctx = dash.callback_context  # WHY: per-request trigger context
        if not ctx.triggered:  # WHY: empty means we are in the initial page load
            return "initial_load"  # WHY: mirror original label
        prop_id: str = ctx.triggered[0]["prop_id"]  # WHY: annotate for strict-typed str return
        return prop_id.split(".")[0]  # WHY: strip prop suffix to get component id

    def _build_refresh_payload(  # WHY: separate serializer call keeps _do_refresh_map_dropdown small
        self, maps_response: Any
    ) -> tuple[Any, Any]:
        """Return (dropdown options, store data) for a successful map-list response."""
        fresh_maps = maps_response.data if maps_response.data else []  # WHY: default to empty list
        logging.info("Map dropdown refreshed: %d maps found", len(fresh_maps))  # WHY: mirror original log
        options = self._state.serializer.build_dropdown_options(  # WHY: options for the dropdown
            fresh_maps, default_name=_DEFAULT_MAP_NAME
        )
        store = self._state.serializer.build_named_items(  # WHY: full data for the shared store
            fresh_maps, default_name=_DEFAULT_MAP_NAME
        )
        return options, store  # WHY: 2-tuple matches original Output list

    # ------------------------------------------------------------------
    # handle_site_from_url + helpers
    # ------------------------------------------------------------------

    def handle_site_from_url(  # WHY: Dash callback that sets dropdown from URL param
        self,
        url_search: str | None,
        config: dict[str, Any] | None,
        available_sites: list[dict[str, Any]] | None,
    ) -> list[Any]:
        """Handle site selection when URL contains site_id parameter (for bookmarks/links)."""
        from dash import no_update  # WHY: sentinel used to skip output updates

        resolved = self._resolve_url_site_id(url_search, config, available_sites)  # WHY: guard chain extracted
        if resolved is None:  # WHY: no change needed (any of: no url, no param, same, invalid)
            return [no_update]  # WHY: return single-element list to match Output signature
        logging.info("URL site switch: Setting dropdown to site %s", resolved)  # WHY: mirror original log
        return [resolved]  # WHY: return the site_id wrapped in a list

    def _resolve_url_site_id(  # WHY: extracted guard chain so handle_site_from_url has CC ≤5
        self,
        url_search: str | None,
        config: dict[str, Any] | None,
        available_sites: list[dict[str, Any]] | None,
    ) -> str | None:
        """Return the site_id to set (or None to signal 'no update needed')."""
        url_site_id = self._extract_optional_url_param(url_search, "site_id")  # WHY: bail-safe param lookup
        if not url_site_id:  # WHY: no URL or param absent -> no change
            return None  # WHY: signal caller to no_update
        if url_site_id == self._current_config_site_id(config):  # WHY: already there -> no change
            return None  # WHY: signal caller to no_update
        if not self._is_known_site(url_site_id, available_sites):  # WHY: reject unknown site
            logging.warning("URL site switch: Invalid site_id %s", url_site_id)  # WHY: mirror original log
            return None  # WHY: signal caller to no_update
        return url_site_id  # WHY: valid URL param, caller should set dropdown

    # ------------------------------------------------------------------
    # sync_dropdown_with_url + helpers
    # ------------------------------------------------------------------

    def sync_dropdown_with_url(  # WHY: Dash callback that sets map dropdown from URL param
        self,
        url_search: str | None,
        available_maps: list[dict[str, Any]] | None,
        current_dropdown_value: str | None,
    ) -> Any:
        """Sync dropdown selection with URL parameter on page load."""
        from dash import no_update  # WHY: sentinel used to skip output updates

        resolved = self._resolve_url_map_id(url_search, available_maps, current_dropdown_value)  # WHY: extract
        if resolved is None:  # WHY: no change needed
            return no_update  # WHY: signal Dash to skip
        logging.debug("URL dropdown sync: Setting dropdown to %s", resolved)  # WHY: mirror original log
        return resolved  # WHY: return the map_id for the dropdown

    def _resolve_url_map_id(  # WHY: extracted guard chain so sync_dropdown_with_url has CC ≤5
        self,
        url_search: str | None,
        available_maps: list[dict[str, Any]] | None,
        current_dropdown_value: str | None,
    ) -> str | None:
        """Return the map_id to set (or None to signal 'no update needed')."""
        url_map_id = self._extract_optional_url_param(url_search, "map_id")  # WHY: bail-safe param lookup
        if not url_map_id:  # WHY: no URL or param absent -> no change
            return None  # WHY: signal caller to no_update
        if url_map_id == current_dropdown_value:  # WHY: already in sync -> no change
            return None  # WHY: signal caller to no_update
        if not self._is_known_map(url_map_id, available_maps):  # WHY: reject unknown map
            logging.warning("URL dropdown sync: Invalid map_id %s", url_map_id)  # WHY: mirror original log
            return None  # WHY: signal caller to no_update
        return url_map_id  # WHY: valid URL param, caller should set dropdown

    # ------------------------------------------------------------------
    # URL/config lookup shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_optional_url_param(url_search: str | None, name: str) -> str | None:  # WHY: bail-safe wrapper
        """Return ``name`` from ``url_search`` or ``None`` if url_search is empty."""
        if not url_search:  # WHY: guard empty or None URL
            return None  # WHY: nothing to parse
        return _ViewerSiteSwitch._extract_url_param(url_search, name)  # WHY: delegate to strict parser

    @staticmethod
    def _extract_url_param(url_search: str, name: str) -> str | None:  # WHY: also called from _viewer_url_switch
        """Parse a single query-string parameter from a ``?key=value&...`` string."""
        import urllib.parse  # WHY: stdlib URL parsing

        params = urllib.parse.parse_qs(url_search.lstrip("?"))  # WHY: strip leading ? then parse
        return params.get(name, [None])[0]  # WHY: return first value or None

    @staticmethod
    def _current_config_site_id(config: dict[str, Any] | None) -> Any:  # WHY: null-safe accessor
        """Return the current ``site_id`` from config, or None if config is missing."""
        return config.get("site_id") if config else None  # WHY: mirror original inline ternary

    @staticmethod
    def _is_known_site(  # WHY: allow-list check so guard chain stays flat
        site_id: str, available_sites: list[dict[str, Any]] | None
    ) -> bool:
        """Return True if ``site_id`` appears in the available-sites list."""
        valid_ids = [s.get("id") for s in available_sites] if available_sites else []  # WHY: allow-list
        return site_id in valid_ids  # WHY: membership test

    @staticmethod
    def _is_known_map(  # WHY: allow-list check so guard chain stays flat
        map_id: str, available_maps: list[dict[str, Any]] | None
    ) -> bool:
        """Return True if ``map_id`` appears in the available-maps list."""
        valid_ids = [m.get("id") for m in available_maps] if available_maps else []  # WHY: allow-list
        return map_id in valid_ids  # WHY: membership test

    # ------------------------------------------------------------------
    # handle_site_switch_from_dropdown + helpers
    # ------------------------------------------------------------------

    def handle_site_switch_from_dropdown(  # WHY: Dash callback that swaps active site + rebuilds figure
        self,
        selected_site_id: str | None,
        config: dict[str, Any] | None,
        available_sites: list[dict[str, Any]] | None,
        _current_fig: dict[str, Any],
    ) -> tuple[Any, Any, Any, Any, Any]:
        """Handle site switching from dropdown - rebuilds dropdown options, store, config, and figure."""
        from dash import no_update  # WHY: sentinel used to skip output updates

        noop = (no_update, no_update, no_update, no_update, no_update)  # WHY: 5-way skip preserved
        logging.info("[SITE-SWITCH] Callback triggered with site_id=%s", selected_site_id)  # WHY: entry trace
        if not self._preflight_site_switch(selected_site_id, config):  # WHY: guard chain moved into helper
            return noop  # WHY: preflight already logged the reason
        return self._dispatch_site_switch(selected_site_id, config, available_sites, noop)  # WHY: heavy lifting

    def _dispatch_site_switch(  # WHY: extracted try/except so callback CC stays ≤5
        self,
        selected_site_id: str | None,
        config: dict[str, Any] | None,
        available_sites: list[dict[str, Any]] | None,
        noop: tuple[Any, Any, Any, Any, Any],
    ) -> tuple[Any, Any, Any, Any, Any]:
        """Resolve site name, perform switch, and translate exceptions into noop."""
        resolved_id = selected_site_id or ""  # WHY: normalize once so downstream helpers avoid re-fallback
        site_name = self._resolve_site_name(resolved_id, available_sites or [])  # WHY: display name lookup
        logging.info("[SITE-SWITCH] Switching to site %s (%s)", site_name, resolved_id)  # WHY: mirror log
        try:
            return self._perform_site_switch(resolved_id, site_name, config)  # WHY: heavy lifting
        except Exception as site_switch_error:  # WHY: catch-all parity with original
            logging.exception("[SITE-SWITCH] Error: %s", site_switch_error)  # WHY: mirror original log
            return noop  # WHY: skip all outputs on failure

    def _preflight_site_switch(  # WHY: extracted guard chain so callback has CC ≤5
        self, selected_site_id: str | None, config: dict[str, Any] | None
    ) -> bool:
        """Return True if a site switch should proceed; log + return False otherwise."""
        if not selected_site_id:  # WHY: guard missing input
            logging.warning("[SITE-SWITCH] No selected_site_id provided")  # WHY: mirror original log
            return False  # WHY: caller should skip
        if selected_site_id == self._current_config_site_id(config):  # WHY: same -> no-op
            logging.debug(  # WHY: mirror original log
                "[SITE-SWITCH] Same site selected (%s), no update needed", selected_site_id
            )
            return False  # WHY: caller should skip
        return True  # WHY: switch is worth performing

    @staticmethod
    def _resolve_site_name(site_id: str, available_sites: list[dict[str, Any]]) -> str:  # WHY: display-name lookup
        """Look up display name for a site_id from the available-sites list."""
        return next(  # WHY: first match wins (matches original semantics)
            (s.get("name", "Unknown") for s in available_sites if s.get("id") == site_id), "Unknown"
        )

    def _perform_site_switch(  # WHY: fetch maps for new site + build dropdown/figure payload
        self,
        selected_site_id: str,
        site_name: str,
        config: dict[str, Any] | None,
    ) -> tuple[Any, Any, Any, Any, Any]:
        """Fetch maps for new site, build dropdown + figure for the first map."""
        from dash import no_update  # WHY: sentinel used to skip output updates

        new_maps = self._fetch_site_maps(selected_site_id)  # WHY: None on API failure, [] on no maps
        if new_maps is None:  # WHY: API call failed
            return no_update, no_update, no_update, no_update, no_update  # WHY: preserve original 5-tuple skip
        if not new_maps:  # WHY: site has no maps -> empty figure
            return self._build_empty_site_payload(selected_site_id, site_name, config)  # WHY: empty payload
        return self._build_first_map_payload(selected_site_id, site_name, new_maps, config)  # WHY: pick first map

    def _fetch_site_maps(self, site_id: str) -> list[dict[str, Any]] | None:  # WHY: HTTP guard + normalize empty
        """Fetch site map list; return ``None`` on API failure, ``[]`` on empty."""
        maps_response = self._state.mistapi_ref.api.v1.sites.maps.listSiteMaps(  # WHY: Mist API call
            self._state.api_session_ref, site_id=site_id
        )
        if maps_response.status_code != _HTTP_OK:  # WHY: mirror original HTTP gate
            logging.error(  # WHY: mirror original log
                "[SITE-SWITCH] Failed to fetch maps for site %s - HTTP %s", site_id, maps_response.status_code
            )
            return None  # WHY: caller distinguishes None (failure) from [] (no data)
        new_maps = maps_response.data if maps_response.data else []  # WHY: normalize empty
        logging.info("[SITE-SWITCH] Found %d maps for site", len(new_maps))  # WHY: mirror original log
        return new_maps  # WHY: return list of maps

    def _build_empty_site_payload(  # WHY: 5-tuple for "site with no maps"
        self,
        selected_site_id: str,
        site_name: str,
        config: dict[str, Any] | None,
    ) -> tuple[list[Any], None, list[Any], dict[str, Any], Any]:
        """Return the 5-tuple shown when a site has no maps."""
        import plotly.graph_objects as go  # WHY: local import - heavy module

        logging.warning("[SITE-SWITCH] No maps found for site %s", selected_site_id)  # WHY: mirror original log
        empty_fig = go.Figure()  # WHY: empty figure with site-level title
        empty_fig.update_layout(  # WHY: match original empty-figure styling byte-for-byte
            title=f"No maps found for site: {site_name}",
            paper_bgcolor=_BG_COLOR,
            plot_bgcolor=_BG_COLOR,
            font=dict(color=_FG_COLOR),
        )
        updated_config = self._merge_empty_site_config(config, selected_site_id, site_name)  # WHY: config copy
        return [], None, [], updated_config, empty_fig  # WHY: empty options, no selection, empty store

    @staticmethod
    def _merge_empty_site_config(  # WHY: extract config mutation to keep _build_empty_site_payload short
        config: dict[str, Any] | None, site_id: str, site_name: str
    ) -> dict[str, Any]:
        """Return a config copy for the empty-site case (map_id/map_name cleared)."""
        updated_config = config.copy() if config else {}  # WHY: preserve other config keys
        updated_config["site_id"] = site_id  # WHY: update site
        updated_config["site_name"] = site_name  # WHY: update site name
        updated_config["map_id"] = None  # WHY: no active map
        updated_config["map_name"] = None  # WHY: clear name too
        return updated_config  # WHY: return mutated copy

    def _build_first_map_payload(  # WHY: 5-tuple for "site with at least one map"
        self,
        selected_site_id: str,
        site_name: str,
        new_maps: list[dict[str, Any]],
        config: dict[str, Any] | None,
    ) -> tuple[Any, Any, Any, dict[str, Any], Any]:
        """Build dropdown options, store, updated config, and figure for the first map."""
        new_map_options = self._state.serializer.build_dropdown_options(  # WHY: dropdown options
            new_maps, default_name=_DEFAULT_MAP_NAME
        )
        new_maps_store = self._state.serializer.build_named_items(  # WHY: full store data
            new_maps, default_name=_DEFAULT_MAP_NAME
        )
        first_map = new_maps[0]  # WHY: pick first map (matches original)
        selected_map_id: str = first_map.get("id", "")  # WHY: coerce to str for strict typing downstream
        map_name = first_map.get("name", _DEFAULT_MAP_NAME)  # WHY: map display name
        updated_config = self._merge_site_switch_config(config, selected_site_id, site_name, first_map)  # WHY: cfg
        new_fig = self._build_site_switch_figure(  # WHY: fresh figure for the first map
            selected_site_id, selected_map_id, first_map, site_name, map_name
        )
        logging.info("[SITE-SWITCH] Successfully loaded map %s", map_name)  # WHY: mirror original log
        return new_map_options, selected_map_id, new_maps_store, updated_config, new_fig  # WHY: 5-tuple

    @staticmethod
    def _merge_site_switch_config(  # WHY: config mutation isolated for testability
        config: dict[str, Any] | None,
        site_id: str,
        site_name: str,
        first_map: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge site + first-map info into a copy of the existing config dict."""
        updated_config = config.copy() if config else {}  # WHY: preserve other keys
        updated_config["site_id"] = site_id  # WHY: new site
        updated_config["site_name"] = site_name  # WHY: new site name
        updated_config["map_id"] = first_map.get("id")  # WHY: first map UUID
        updated_config["map_name"] = first_map.get("name", _DEFAULT_MAP_NAME)  # WHY: first map name
        updated_config["ppm"] = first_map.get("ppm", _DEFAULT_PPM)  # WHY: PPM (default preserved)
        updated_config["map_width"] = first_map.get("width", _DEFAULT_MAP_WIDTH)  # WHY: canvas width
        updated_config["map_height"] = first_map.get("height", _DEFAULT_MAP_HEIGHT)  # WHY: canvas height
        return updated_config  # WHY: return mutated copy

    def _build_site_switch_figure(  # WHY: fresh figure for a first-map render
        self,
        selected_site_id: str,
        selected_map_id: str,
        map_data: dict[str, Any],
        site_name: str,
        map_name: str,
    ) -> Any:
        """Construct a fresh Plotly figure for the first map on a newly-selected site."""
        import plotly.graph_objects as go  # WHY: local import - heavy module

        new_fig = go.Figure()  # WHY: start with an empty figure
        map_width = map_data.get("width", _DEFAULT_MAP_WIDTH)  # WHY: canvas width
        map_height = map_data.get("height", _DEFAULT_MAP_HEIGHT)  # WHY: canvas height
        self._add_background_image(new_fig, map_data, map_width, map_height, anchor_top=False)  # WHY: background
        devices = self._fetch_site_switch_devices(selected_site_id, selected_map_id)  # WHY: APs/switches/gateways
        self._add_simple_device_traces(new_fig, devices)  # WHY: simple marker-per-device traces
        self._apply_site_switch_layout(new_fig, site_name, map_name, map_width, map_height)  # WHY: layout/theme
        return new_fig  # WHY: return finished figure

    @staticmethod
    def _add_background_image(  # WHY: Plotly background-image injection
        fig: Any,
        map_data: dict[str, Any],
        map_width: int,
        map_height: int,
        anchor_top: bool,
    ) -> None:
        """Add the map background image; ``anchor_top`` selects y=map_height vs y=0."""
        if "url" not in map_data:  # WHY: no image to add
            return  # WHY: nothing to do
        fig.add_layout_image(  # WHY: Plotly background-image API
            source=map_data["url"],
            xref="x",
            yref="y",
            x=0,
            y=map_height if anchor_top else 0,  # WHY: site-switch used map_height; URL-switch used 0
            sizex=map_width,
            sizey=map_height,
            sizing="stretch",
            opacity=1.0,
            layer="below",
        )

    def _fetch_site_switch_devices(  # WHY: fetch site devices and filter to a specific map
        self, site_id: str, map_id: str
    ) -> list[dict[str, Any]]:
        """Fetch site devices and filter to the given map (returns [] on failure)."""
        try:
            all_devices = self._call_site_devices_api(site_id)  # WHY: extracted HTTP call keeps CC low
            return [d for d in all_devices if d.get("map_id") == map_id]  # WHY: filter to this map
        except Exception:  # WHY: mirror original bare-except behavior
            return []  # WHY: swallow failures and return empty list

    def _call_site_devices_api(self, site_id: str) -> list[dict[str, Any]]:  # WHY: extracted API call
        """Call listSiteDevicesStats and return the device list (empty on non-200)."""
        devices_response = self._state.mistapi_ref.api.v1.sites.stats.listSiteDevicesStats(  # WHY: Mist API call
            self._state.api_session_ref, site_id=site_id, limit=_DEVICES_PAGE_LIMIT
        )
        if devices_response.status_code != _HTTP_OK:  # WHY: API failure -> no devices
            return []  # WHY: empty list on non-200
        return devices_response.data or []  # WHY: normalize None -> []

    def _add_simple_device_traces(  # WHY: iterate devices and add per-device markers
        self, fig: Any, devices: list[dict[str, Any]]
    ) -> None:
        """Add per-device markers to the figure using the original simple-style logic."""
        import plotly.graph_objects as go  # WHY: local import - heavy module

        for device in devices:  # WHY: one trace per device (preserve original behavior)
            color = self._simple_device_color(device.get("status", "unknown"))  # WHY: status-based color
            symbol = self._simple_device_symbol(device.get("type", "ap"))  # WHY: type-based symbol
            self._add_single_device_trace(fig, device, color, symbol, go)  # WHY: append one Scatter trace

    @staticmethod
    def _simple_device_color(status: str) -> str:  # WHY: status -> marker color
        """Map device status to marker color (mirrors original site-switch logic)."""
        if status == "connected":  # WHY: bright green for connected
            return _STATUS_CONNECTED_COLOR  # WHY: preserve original literal
        if status == "disconnected":  # WHY: bright red for disconnected
            return _STATUS_DISCONNECTED_COLOR  # WHY: preserve original literal
        return _STATUS_OTHER_COLOR  # WHY: amber for unknown/upgrading

    @staticmethod
    def _simple_device_symbol(device_type: str) -> str:  # WHY: device type -> marker symbol
        """Map device type to marker symbol (mirrors original site-switch logic)."""
        if device_type == "switch":  # WHY: switches rendered as squares
            return "square"  # WHY: original symbol
        if device_type == "gateway":  # WHY: gateways rendered as diamonds
            return "diamond"  # WHY: original symbol
        return "circle"  # WHY: default (used for APs in original site-switch)

    @staticmethod
    def _add_single_device_trace(  # WHY: append one Scatter trace for a device
        fig: Any,
        device: dict[str, Any],
        marker_color: str,
        marker_symbol: str,
        go: Any,
    ) -> None:
        """Add a single device's marker+label trace (mirrors original site-switch logic)."""
        fig.add_trace(  # WHY: delegate scatter construction to helper so this stays ≤25 lines
            _ViewerSiteSwitch._build_device_scatter(device, marker_color, marker_symbol, go)
        )

    @staticmethod
    def _build_device_scatter(  # WHY: build the go.Scatter object for one device
        device: dict[str, Any], marker_color: str, marker_symbol: str, go: Any
    ) -> Any:
        """Return the ``go.Scatter`` for a single device (marker + label + hover)."""
        name = device.get("name", "Unknown")  # WHY: display name
        dtype = device.get("type", "ap")  # WHY: device type
        status = device.get("status", "unknown")  # WHY: connectivity status
        line = {"color": _LINE_COLOR, "width": _MARKER_OUTLINE_WIDTH}  # WHY: marker outline dict
        marker = {"size": _MARKER_SIZE, "color": marker_color, "symbol": marker_symbol, "line": line}  # WHY: marker
        hover = f"<b>{name}</b><br>Type: {dtype}<br>Status: {status}<extra></extra>"  # WHY: hover format
        return go.Scatter(  # WHY: single Scatter trace per device
            x=[device.get("x", 0)],
            y=[device.get("y", 0)],
            mode="markers+text",
            marker=marker,
            text=[name],
            textposition="top center",
            textfont={"size": _TEXT_FONT_SIZE, "color": _FG_COLOR},
            name=name,
            showlegend=False,
            hovertemplate=hover,
        )

    @staticmethod
    def _apply_site_switch_layout(  # WHY: apply figure layout (title, axes, theme, drag mode)
        fig: Any,
        site_name: str,
        map_name: str,
        map_width: int,
        map_height: int,
    ) -> None:
        """Apply the site-switch figure layout (title, axes, theme, drag mode)."""
        fig.update_layout(  # WHY: preserve original layout dict byte-for-byte
            title=_ViewerSiteSwitch._build_layout_title(site_name, map_name),  # WHY: extracted title dict
            paper_bgcolor=_BG_COLOR,
            plot_bgcolor=_BG_COLOR,
            xaxis=_ViewerSiteSwitch._build_layout_xaxis(map_width),  # WHY: extracted xaxis dict
            yaxis=dict(range=[0, map_height], showgrid=False, zeroline=False, showticklabels=False),
            margin=dict(l=0, r=0, t=_MARGIN_TOP_PX, b=0),
            dragmode="pan",
        )

    @staticmethod
    def _build_layout_title(site_name: str, map_name: str) -> dict[str, Any]:  # WHY: shrink parent
        """Return the title dict for the site-switch layout."""
        return dict(  # WHY: mirror original title attributes byte-for-byte
            text=f"{site_name} - {map_name}",
            font=dict(color=_FG_COLOR, size=_TITLE_FONT_SIZE),
            x=_TITLE_X_CENTER,
        )

    @staticmethod
    def _build_layout_xaxis(map_width: int) -> dict[str, Any]:  # WHY: shrink parent + reuse-ready
        """Return the xaxis dict for the site-switch layout."""
        return dict(  # WHY: mirror original xaxis attributes byte-for-byte
            range=[0, map_width],
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            scaleanchor="y",
            scaleratio=1,
        )

    # ------------------------------------------------------------------
    # Callback wiring (split into per-callback binders to satisfy STRUCT-LENGTH)
    # ------------------------------------------------------------------

    def register(self, app: Dash) -> None:  # WHY: hooks this wave's app.callback(...) blocks into Dash
        """Attach the 5 site-switch callbacks in this cluster to ``app``."""
        from dash import Input, Output, State  # WHY: local import keeps module import-light

        self._bind_set_scale(app, Input, Output, State)  # WHY: bind set_scale callback
        self._bind_refresh_dropdown(app, Input, Output, State)  # WHY: bind refresh_map_dropdown callback
        self._bind_site_switch(app, Input, Output, State)  # WHY: bind handle_site_switch_from_dropdown callback
        self._bind_site_from_url(app, Input, Output, State)  # WHY: bind handle_site_from_url callback
        self._bind_dropdown_url_sync(app, Input, Output, State)  # WHY: bind sync_dropdown_with_url callback

    def _bind_set_scale(  # WHY: register set_scale callback with byte-identical args
        self, app: Dash, Input: Any, Output: Any, State: Any
    ) -> None:
        """Bind ``set_scale`` - calibrate PPM from drawn line."""
        app.callback(
            [Output("scale-status", "children"), Output("map-display", "figure", allow_duplicate=True)],
            Input("set-scale-button", "n_clicks"),  # WHY: triggered by Set Scale button
            [State("scale-length-input", "value"), State("map-display", "figure")],  # WHY: input + current fig
            prevent_initial_call=True,  # WHY: avoid initial render thrash
        )(self.set_scale)

    def _bind_refresh_dropdown(  # WHY: register refresh_map_dropdown callback with byte-identical args
        self, app: Dash, Input: Any, Output: Any, State: Any
    ) -> None:
        """Bind ``refresh_map_dropdown`` - repopulate map selector."""
        app.callback(
            [Output("map-selector-dropdown", "options"), Output("available-maps-store", "data")],
            [
                Input("cache-bust-store", "data"),  # WHY: cache-bust signal
                Input("manual-refresh-btn", "n_clicks"),  # WHY: manual refresh button
                Input("url-location", "search"),  # WHY: URL change trigger
            ],
            [State("map-config-store", "data")],  # WHY: site_id source
            prevent_initial_call=False,  # WHY: run on initial load to get fresh data
        )(self.refresh_map_dropdown)

    def _bind_site_switch(  # WHY: register handle_site_switch_from_dropdown callback with byte-identical args
        self, app: Dash, Input: Any, Output: Any, State: Any
    ) -> None:
        """Bind ``handle_site_switch_from_dropdown`` - swap active site."""
        app.callback(
            [
                Output("map-selector-dropdown", "options"),
                Output("map-selector-dropdown", "value", allow_duplicate=True),
                Output("available-maps-store", "data", allow_duplicate=True),
                Output("map-config-store", "data", allow_duplicate=True),
                Output("map-display", "figure", allow_duplicate=True),
            ],
            [Input("site-selector-dropdown", "value")],  # WHY: triggered by site selection
            [
                State("map-config-store", "data"),  # WHY: current config
                State("available-sites-store", "data"),  # WHY: sites store
                State("map-display", "figure"),  # WHY: current figure
            ],
            prevent_initial_call=True,  # WHY: avoid initial render thrash
        )(self.handle_site_switch_from_dropdown)

    def _bind_site_from_url(  # WHY: register handle_site_from_url callback with byte-identical args
        self, app: Dash, Input: Any, Output: Any, State: Any
    ) -> None:
        """Bind ``handle_site_from_url`` - sync dropdown to URL param."""
        app.callback(
            [Output("site-selector-dropdown", "value")],
            [Input("url-location", "search")],  # WHY: URL change trigger
            [State("map-config-store", "data"), State("available-sites-store", "data")],
            prevent_initial_call="initial_duplicate",  # WHY: allow initial run on duplicate output
        )(self.handle_site_from_url)

    def _bind_dropdown_url_sync(  # WHY: register sync_dropdown_with_url callback with byte-identical args
        self, app: Dash, Input: Any, Output: Any, State: Any
    ) -> None:
        """Bind ``sync_dropdown_with_url`` - map dropdown selection from URL."""
        app.callback(
            Output("map-selector-dropdown", "value"),
            [Input("url-location", "search")],  # WHY: URL change trigger
            [State("available-maps-store", "data"), State("map-selector-dropdown", "value")],
            prevent_initial_call=False,  # WHY: must run on initial load
        )(self.sync_dropdown_with_url)
