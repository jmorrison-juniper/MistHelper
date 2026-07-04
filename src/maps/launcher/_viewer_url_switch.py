"""URL-map-switch cluster extracted from ``viewer_callbacks.py``.

Owns the single Wave-E3 public callback ``handle_url_map_switch`` plus its
private helpers (URL preflight, target-map fetch, device/zone/client
overlays, coverage heatmap rendering).  Follows the same wrapper-class +
``__getattr__`` template used by the other Wave-1..5 clusters so the
parent :class:`~src.maps.launcher.viewer_callbacks.MapViewerCallbacks`
stays a thin coordinator that hands each Dash callback off to the
appropriate cluster.
"""

from __future__ import annotations  # WHY: postponed evaluation consistent with parent module

import logging  # WHY: audit trail for URL-switch diagnostics
from dataclasses import dataclass  # WHY: frozen value objects collapse parameter counts
from typing import TYPE_CHECKING, Any  # WHY: opaque manager + type-permissive Dash callback args

if TYPE_CHECKING:  # WHY: keep dash imports lazy at runtime
    from dash import Dash  # WHY: annotation reference for register(app)


# ----------------------------------------------------------------------
# Module-level constants (magic numbers + repeated literals extracted)
# ----------------------------------------------------------------------

_DEFAULT_MAP_WIDTH = 1000  # WHY: fallback width matches original getattr default
_DEFAULT_MAP_HEIGHT = 1000  # WHY: fallback height matches original getattr default
_DEFAULT_PPM = 10  # WHY: pixels-per-meter default when API omits the field
_DEFAULT_MAP_NAME = "Unnamed"  # WHY: matches original name-missing label
_DEVICES_PAGE_LIMIT = 1000  # WHY: paginate ceiling used by original listSiteDevicesStats call
_CLIENTS_PAGE_LIMIT = 1000  # WHY: paginate ceiling used by original wireless-client call
_HTTP_OK = 200  # WHY: named constant is clearer than magic 200 in every guard
_CROSSHAIR_SIZE_PX = 40  # WHY: half-length of orientation crosshair in pixels (original literal)
_DOT_DISTANCE_PX = 50  # WHY: radius from device center to orientation dot (original literal)
_ORIENTATION_ANGLE_OFFSET = 90  # WHY: convert Mist orientation (0=north) into math radians frame
_LABEL_Y_OFFSET = 15  # WHY: label placed 15 px below device marker (original literal)
_CLIENT_LABEL_Y_OFFSET = 10  # WHY: client label sits closer to the marker than device labels
_MAC_SUFFIX_LEN = 8  # WHY: last-8 chars of MAC used when hostname is empty (mirror original)
_ERROR_MSG_TRUNCATE = 200  # WHY: coverage-exception logs truncated to 200 chars in original
_MAX_RSSI_FALLBACK_IDX = 4  # WHY: original fallback index when result_def lacks column names
_COVERAGE_QUERY_PARAMS: dict[str, str] = {  # WHY: identical query parameters to the original call
    "resolution": "fine",  # WHY: request per-cell fine-grained coverage
    "duration": "1d",  # WHY: aggregate over the last day (matches original)
    "type": "client",  # WHY: client-perceived coverage rather than raw AP power
    "from_apollo": "true",  # WHY: fetch from Apollo backend (matches original)
}
_HEATMAP_COLORSCALE: list[list[Any]] = [  # WHY: 5-stop RSSI colorscale mirrored byte-for-byte
    [0.0, "rgb(0, 0, 255)"],  # WHY: weakest signal = blue
    [0.33, "rgb(0, 255, 0)"],  # WHY: moderate signal = green
    [0.50, "rgb(255, 255, 0)"],  # WHY: fair signal = yellow
    [0.67, "rgb(255, 165, 0)"],  # WHY: strong signal = orange
    [1.0, "rgb(255, 0, 0)"],  # WHY: strongest signal = red
]
_CLIENT_MARKER: dict[str, Any] = {  # WHY: extract client marker style so trace helper stays ≤25 lines
    "symbol": "circle",  # WHY: original client symbol
    "size": 12,  # WHY: original client size
    "color": "#00ff00",  # WHY: original green fill
    "line": {"color": "white", "width": 2},  # WHY: original white outline
    "opacity": 0.9,  # WHY: original alpha
}
_ORIGIN_MARKER: dict[str, Any] = {  # WHY: extract origin marker style so trace helper stays ≤25 lines
    "symbol": "x",  # WHY: original origin symbol
    "size": 20,  # WHY: original origin size
    "color": "yellow",  # WHY: original yellow fill
    "line": {"width": 3, "color": "black"},  # WHY: original black outline
}
_LAYOUT_XAXIS_BASE: dict[str, Any] = {  # WHY: extract xaxis config so layout helper stays ≤25 lines
    "showgrid": False,  # WHY: hide grid
    "zeroline": False,  # WHY: hide zeroline
    "scaleanchor": "y",  # WHY: lock aspect ratio
    "scaleratio": 1,  # WHY: 1:1 x:y
    "constrain": "domain",  # WHY: honour domain
}
_LAYOUT_YAXIS_BASE: dict[str, Any] = {  # WHY: extract yaxis config so layout helper stays ≤25 lines
    "showgrid": False,  # WHY: hide grid
    "zeroline": False,  # WHY: hide zeroline
    "constrain": "domain",  # WHY: honour domain
}
_LAYOUT_LEGEND: dict[str, Any] = {"bgcolor": "rgba(0,0,0,0.7)", "font": {"color": "white"}}  # WHY: translucent legend
_LAYOUT_MARGIN: dict[str, int] = {"l": 50, "r": 50, "t": 50, "b": 50}  # WHY: original margins
_HEATMAP_COLORBAR: dict[str, Any] = {  # WHY: extract colorbar dict so heatmap helper stays ≤25 lines
    "title": {"text": "RSSI (dBm)", "side": "right", "font": {"size": 12, "color": "white"}},  # WHY: label
    "thickness": 20,  # WHY: original thickness
    "len": 0.5,  # WHY: original relative length
    "y": 0.95,  # WHY: original y anchor
    "yanchor": "top",  # WHY: anchor at top
    "tickfont": {"size": 10, "color": "white"},  # WHY: original tick font
}
_DEVICE_TYPE_CONFIG: dict[str, dict[str, Any]] = {  # WHY: symbol/color config per device type
    "ap": {  # WHY: Access Point rendering config
        "symbol": "triangle-up",  # WHY: original AP symbol
        "name": "Access Points",  # WHY: legend label
        "size": 20,  # WHY: original marker size
        "colors": {"connected": "#00ff00", "disconnected": "#ff0000", "upgrading": "#ff8800"},  # WHY: status palette
    },
    "switch": {  # WHY: Switch rendering config
        "symbol": "square",  # WHY: original Switch symbol
        "name": "Switches",  # WHY: legend label
        "size": 18,  # WHY: original marker size
        "colors": {"connected": "#00ccff", "disconnected": "#ff0000", "upgrading": "#ff8800"},  # WHY: status palette
    },
    "gateway": {  # WHY: Gateway rendering config
        "symbol": "diamond",  # WHY: original Gateway symbol
        "name": "Gateways",  # WHY: legend label
        "size": 20,  # WHY: original marker size
        "colors": {"connected": "#ff00ff", "disconnected": "#ff0000", "upgrading": "#ff8800"},  # WHY: status palette
    },
}


# ----------------------------------------------------------------------
# Frozen value objects (collapse >5-parameter function signatures)
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class _MapLayers:  # WHY: bundle background+overlay entities for figure builder
    """Value object holding the fetched entities used to build the URL-switch figure."""

    map_data: dict[str, Any]  # WHY: map metadata (width, height, ppm, origin, name)
    devices: list[dict[str, Any]]  # WHY: devices filtered to this map
    zones: list[dict[str, Any]]  # WHY: zones filtered to this map
    clients: list[dict[str, Any]]  # WHY: wireless clients with coordinates on this map


@dataclass(frozen=True)
class _FigureBuildContext:  # WHY: bundle build inputs so figure builder stays ≤5 params
    """Value object carrying the identifiers + layers required to compose the figure."""

    url_map_id: str  # WHY: map id used for heatmap fetch and log correlation
    site_id_local: str  # WHY: site id used for heatmap fetch
    layers: _MapLayers  # WHY: pre-fetched entity bundle
    config: dict[str, Any]  # WHY: shared config (site_id override, etc.)


@dataclass(frozen=True)
class _DeviceRenderArrays:  # WHY: bundle parallel arrays used by device rendering helpers
    """Value object grouping per-device parallel arrays for marker/label/crosshair rendering."""

    x_coords: list[float]  # WHY: pixel x positions
    y_coords: list[float]  # WHY: pixel y positions
    names: list[str]  # WHY: display names (fallback to MAC)
    colors: list[str]  # WHY: per-device status color
    hover_texts: list[str]  # WHY: per-device hover HTML
    type_devices: list[dict[str, Any]]  # WHY: raw device dicts (for orientation lookup)


@dataclass(frozen=True)
class _CrosshairSpec:  # WHY: bundle per-device crosshair parameters
    """Value object describing the crosshair placement for one device."""

    x: float  # WHY: pixel x
    y: float  # WHY: pixel y
    device_color: str  # WHY: crosshair stroke color (matches marker)
    legend_name: str  # WHY: legend group name (type-specific)


@dataclass(frozen=True)
class _OrientationSpec:  # WHY: bundle per-device orientation-dot parameters
    """Value object describing the orientation dot for one device."""

    x: float  # WHY: pixel x of device center
    y: float  # WHY: pixel y of device center
    orientation: float  # WHY: Mist orientation angle (0 = north)
    device_color: str  # WHY: dot fill color (matches marker)
    legend_name: str  # WHY: legend group name (type-specific)


@dataclass(frozen=True)
class _HeatmapSpec:  # WHY: bundle heatmap axis/z/range so append helper stays ≤5 params
    """Value object describing the sparse heatmap grid to append to a figure."""

    unique_x: list[float]  # WHY: distinct x bin coordinates
    unique_y: list[float]  # WHY: distinct y bin coordinates
    z_matrix: list[list[float | None]]  # WHY: dense z matrix aligned with x/y bins
    min_rssi: float  # WHY: colorscale lower bound
    max_rssi_val: float  # WHY: colorscale upper bound


# ----------------------------------------------------------------------
# Module-level pure helpers
# ----------------------------------------------------------------------


def _grid_is_valid_row(item: Any, max_idx: int) -> bool:  # WHY: predicate for grid row shape
    """Return True iff ``item`` is an indexable row with enough columns."""
    return isinstance(item, (list, tuple)) and len(item) > max_idx  # WHY: guard bad rows


def _grid_row_values(item: list[Any], indices: tuple[int, int, int]) -> tuple[Any, Any, Any]:  # WHY: unpack row
    """Return (x, y, max_rssi) from ``item`` using column indices."""
    x_idx, y_idx, max_rssi_idx = indices  # WHY: unpack tuple
    return item[x_idx], item[y_idx], item[max_rssi_idx]  # WHY: single tuple return


def _process_grid_row(
    item: Any,  # WHY: raw grid row
    indices: tuple[int, int, int],  # WHY: column indices
    max_idx: int,  # WHY: minimum row length required
    ppm_local: float,  # WHY: pixels-per-meter conversion factor
) -> tuple[tuple[float, float], float] | None:
    """Return ``((px_x, px_y), max_rssi)`` for a valid row or ``None`` when malformed."""
    if not _grid_is_valid_row(item, max_idx):  # WHY: skip rows with wrong shape
        return None  # WHY: caller drops this row
    x_m, y_m, max_rssi = _grid_row_values(item, indices)  # WHY: extract cols
    if x_m is None or y_m is None or max_rssi is None:  # WHY: drop incomplete rows
        return None  # WHY: caller drops this row
    return (x_m * ppm_local, y_m * ppm_local), max_rssi  # WHY: meters -> pixels


def _build_client_hover(client: dict[str, Any], x: float, y: float) -> str:  # WHY: identical hover HTML
    """Render the hover HTML block for one wireless client (mirrors original format)."""
    return (  # WHY: multi-line string keeps original layout
        "<b>Client</b><br>"  # WHY: header block
        f"MAC: {client.get('mac', 'N/A')}<br>"  # WHY: MAC address line
        f"Hostname: {client.get('hostname', 'N/A')}<br>"  # WHY: hostname line
        f"SSID: {client.get('ssid', 'N/A')}<br>"  # WHY: SSID line
        f"AP: {client.get('ap_name', 'N/A')}<br>"  # WHY: connected AP line
        f"Band: {client.get('band', 'N/A')}<br>"  # WHY: radio band line
        f"Signal: {client.get('rssi', 'N/A')} dBm<br>"  # WHY: RSSI line
        f"Position: ({x}, {y})"  # WHY: coordinate footer
    )


def _build_device_hover(device: dict[str, Any], device_status: str) -> str:  # WHY: identical hover HTML
    """Render the hover HTML block for one device (mirrors original format)."""
    return (  # WHY: multi-line string keeps original layout
        f"<b>{device.get('name', 'Unnamed')}</b><br>"  # WHY: bold name header
        f"Type: {device.get('type', 'N/A')}<br>"  # WHY: device type line
        f"Model: {device.get('model', 'N/A')}<br>"  # WHY: model line
        f"MAC: {device.get('mac', 'N/A')}<br>"  # WHY: MAC address line
        f"Status: <b>{device_status.upper()}</b>"  # WHY: bold status footer
    )


def _resolve_device_status(device: dict[str, Any]) -> str:  # WHY: single-branch status resolver
    """Classify a device into ``connected|disconnected|upgrading`` for color/hover lookup."""
    if device.get("upgrade_status") or device.get("fwupdate", {}).get("progress") is not None:  # WHY: upgrade signal
        return "upgrading"  # WHY: prioritise upgrade state
    if device.get("status", "disconnected") == "connected":  # WHY: online state
        return "connected"  # WHY: connected label
    return "disconnected"  # WHY: default disconnected


def _client_label(client: dict[str, Any]) -> str:  # WHY: label choice mirrors original ternary
    """Return the annotation label for a client (hostname if set, else last-N of MAC)."""
    hostname: str = client.get("hostname", "") or ""  # WHY: prefer hostname when populated
    client_mac: str = client.get("mac", "unknown") or "unknown"  # WHY: MAC fallback for label
    return hostname if hostname else client_mac[-_MAC_SUFFIX_LEN:]  # WHY: same rule as original


def _build_type_marker(type_cfg: dict[str, Any], colors: list[str]) -> dict[str, Any]:  # WHY: shared builder
    """Return the per-type marker dict used by device scatter traces."""
    return {  # WHY: single source of truth for marker styling
        "symbol": type_cfg["symbol"],  # WHY: type-specific glyph
        "size": type_cfg["size"],  # WHY: type-specific size
        "color": colors,  # WHY: per-device status color
        "line": {"color": "white", "width": 2},  # WHY: preserve original outline
        "opacity": 0.9,  # WHY: match original alpha
    }


class _ViewerUrlSwitch:  # WHY: wrapper class hosting the URL-switch callback cluster
    """Cluster class holding the extracted handle_url_map_switch body + helpers."""

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
    # Extracted callback body + helpers (wave E3 URL-switch cluster)
    # ------------------------------------------------------------------

    def handle_url_map_switch(
        self,
        url_search: str | None,  # WHY: URL query string carrying map_id
        config: dict[str, Any] | None,  # WHY: current map-config store contents
        _current_fig: dict[str, Any],  # WHY: prev figure (unused; kept for callback signature)
        available_maps: list[dict[str, Any]] | None,  # WHY: cached map allow-list
        _dropdown_value: str | None,  # WHY: current dropdown (unused; kept for signature)
    ) -> tuple[Any, Any]:
        """Handle map switching when URL contains map_id parameter."""
        from dash import no_update  # WHY: sentinel used to skip output updates

        prep = self._prepare_url_map_switch(url_search, config, available_maps)  # WHY: run guard chain
        if prep is None:  # WHY: any guard failed -> no update
            return no_update, no_update  # WHY: propagate skip to Dash
        url_map_id, site_id_local, normalized_config = prep  # WHY: unpack validated triple
        try:
            return self._perform_url_map_switch(url_map_id, site_id_local, normalized_config)  # WHY: heavy path
        except Exception as e:  # WHY: catch-all parity with original handler
            logging.exception("URL map switch: Error loading map - %s", e)  # WHY: preserve original log
            return no_update, no_update  # WHY: skip update on any exception

    def _prepare_url_map_switch(
        self,
        url_search: str | None,  # WHY: raw URL query string
        config: dict[str, Any] | None,  # WHY: nullable config store
        available_maps: list[dict[str, Any]] | None,  # WHY: nullable map allow-list
    ) -> tuple[str, str, dict[str, Any]] | None:
        """Run all URL-switch preflight guards; return ``(url_map_id, site_id, config)`` or ``None``."""
        url_map_id = self._extract_url_map_id(url_search)  # WHY: parse map_id from URL
        if url_map_id is None:  # WHY: missing param -> abort
            return None  # WHY: guard failure signals no-update
        normalized_config = config or {}  # WHY: default to empty dict for safe .get()
        validated = self._validate_switch_targets(
            url_map_id, normalized_config, available_maps or []
        )  # WHY: allow-list
        if validated is None:  # WHY: config-match, missing site_id, or unknown map -> abort
            return None  # WHY: propagate guard failure
        site_id_local = validated  # WHY: rename for clarity
        logging.info("URL map switch: Loading map %s (current: %s)", url_map_id, normalized_config.get("map_id"))
        return url_map_id, site_id_local, normalized_config  # WHY: pass validated triple to caller

    def _extract_url_map_id(self, url_search: str | None) -> str | None:  # WHY: extracted for CC reduction
        """Return the ``map_id`` from ``url_search`` (or ``None`` when absent)."""
        if not url_search:  # WHY: nothing to parse
            return None  # WHY: signal miss
        url_map_id = self._site._extract_url_param(url_search, "map_id")  # WHY: reuse site-cluster helper
        return url_map_id or None  # WHY: coerce empty string to None

    def _validate_switch_targets(
        self,
        url_map_id: str,  # WHY: candidate map id from URL
        normalized_config: dict[str, Any],  # WHY: current config store
        available_maps: list[dict[str, Any]],  # WHY: fallback allow-list
    ) -> str | None:
        """Return the resolved ``site_id`` if the switch is legal, else ``None``."""
        if url_map_id == normalized_config.get("map_id"):  # WHY: already on this map -> abort
            logging.debug("URL map switch: URL map_id %s matches config, no switch needed", url_map_id)
            return None  # WHY: skip redundant switch
        site_id_local: str | None = normalized_config.get("site_id")  # WHY: site_id required for API calls
        if not site_id_local:  # WHY: guard missing site context
            logging.warning("URL map switch: site_id not available in config")
            return None  # WHY: skip when unresolvable
        if not self._validate_url_map_id(url_map_id, site_id_local, available_maps):  # WHY: allow-list check
            return None  # WHY: reject unknown map
        return site_id_local  # WHY: propagate validated id

    def _validate_url_map_id(
        self,
        url_map_id: str,  # WHY: candidate map id from URL
        site_id_local: str,  # WHY: resolved site id
        available_maps: list[dict[str, Any]],  # WHY: fallback list from store
    ) -> bool:
        """Validate ``url_map_id`` against a fresh API fetch (falls back to store)."""
        valid_map_ids = self._fetch_valid_map_ids(site_id_local, available_maps)  # WHY: fresh ID list
        if url_map_id not in valid_map_ids:  # WHY: reject unknown map
            logging.warning("URL map switch: Invalid map_id %s", url_map_id)
            return False  # WHY: fail closed
        return True  # WHY: allow switch to proceed

    def _fetch_valid_map_ids(
        self,
        site_id_local: str,  # WHY: site id for API call
        available_maps: list[dict[str, Any]],  # WHY: fallback store contents
    ) -> list[str | None]:
        """Fetch a fresh map ID list, falling back to the supplied store on errors."""
        fresh_ids = self._try_fetch_fresh_map_ids(site_id_local)  # WHY: attempt fresh fetch
        if fresh_ids is not None:  # WHY: fetch succeeded
            return fresh_ids  # WHY: return authoritative list
        return [m.get("id") for m in available_maps]  # WHY: store fallback on any failure

    def _try_fetch_fresh_map_ids(self, site_id_local: str) -> list[str | None] | None:  # WHY: isolate try/except
        """Attempt a fresh listSiteMaps call; return ``None`` on any failure to signal fallback."""
        try:
            fresh_response = self._state.mistapi_ref.api.v1.sites.maps.listSiteMaps(  # WHY: call fresh listing
                self._state.api_session_ref, site_id=site_id_local
            )
        except Exception as fetch_err:  # WHY: mirror original except-block log
            logging.warning("URL map switch: Error fetching fresh maps: %s", fetch_err)
            return None  # WHY: signal caller to use fallback store
        if fresh_response.status_code != _HTTP_OK:  # WHY: HTTP gate mirrors original
            logging.warning("URL map switch: Could not fetch fresh maps, using store")
            return None  # WHY: signal fallback path
        fresh_maps = fresh_response.data if fresh_response.data else []  # WHY: guard None data
        return [m.get("id") for m in fresh_maps]  # WHY: extract id column

    def _perform_url_map_switch(
        self,
        url_map_id: str,  # WHY: validated target map id
        site_id_local: str,  # WHY: validated site id
        config: dict[str, Any],  # WHY: current config store
    ) -> tuple[Any, Any]:
        """Fetch new map + entities and build a fresh figure + updated config."""
        from dash import no_update  # WHY: sentinel used to skip output updates

        new_map_data = self._fetch_target_map(url_map_id, site_id_local)  # WHY: fetch map details
        if new_map_data is None:  # WHY: API failure -> skip update
            return no_update, no_update  # WHY: propagate skip
        layers = _MapLayers(  # WHY: bundle entity layers into one value object
            map_data=new_map_data,
            devices=self._fetch_devices_for_map(url_map_id, site_id_local),  # WHY: device list
            zones=self._fetch_zones_for_map(url_map_id, site_id_local),  # WHY: zone list
            clients=self._fetch_clients_for_map(url_map_id, site_id_local),  # WHY: client list
        )
        ctx = _FigureBuildContext(  # WHY: bundle identifiers + layers for figure builder
            url_map_id=url_map_id, site_id_local=site_id_local, layers=layers, config=config
        )
        new_fig = self._build_url_switch_figure(ctx)  # WHY: compose figure from layers
        new_config = self._merge_url_switch_config(config, url_map_id, new_map_data)  # WHY: updated config
        logging.info("URL map switch: Successfully switched to map '%s'", new_map_data.get("name", _DEFAULT_MAP_NAME))
        return new_fig, new_config  # WHY: return figure + updated config store

    def _fetch_target_map(self, url_map_id: str, site_id_local: str) -> dict[str, Any] | None:
        """Fetch the target map's full data (returns None on HTTP failure)."""
        map_response = self._state.mistapi_ref.api.v1.sites.maps.getSiteMap(  # WHY: single-map fetch
            self._state.api_session_ref, site_id_local, url_map_id
        )
        if map_response.status_code != _HTTP_OK:  # WHY: mirror original HTTP gate
            logging.error("URL map switch: Failed to fetch map - HTTP %s", map_response.status_code)
            return None  # WHY: signal caller to skip
        new_map_data: dict[str, Any] = map_response.data  # WHY: explicit annotation coerces Any for strict typing
        logging.info(  # WHY: mirror original info log with map metadata
            "URL map switch: Loaded map '%s' (%sx%s, ppm=%s)",
            new_map_data.get("name", _DEFAULT_MAP_NAME),
            new_map_data.get("width", _DEFAULT_MAP_WIDTH),
            new_map_data.get("height", _DEFAULT_MAP_HEIGHT),
            new_map_data.get("ppm") or _DEFAULT_PPM,
        )
        return new_map_data  # WHY: return parsed map metadata

    def _fetch_devices_for_map(self, url_map_id: str, site_id_local: str) -> list[dict[str, Any]]:
        """Fetch site devices and filter to ``url_map_id``."""
        devices_response = self._state.mistapi_ref.api.v1.sites.stats.listSiteDevicesStats(  # WHY: paged devices call
            self._state.api_session_ref, site_id=site_id_local, limit=_DEVICES_PAGE_LIMIT
        )
        if devices_response.status_code != _HTTP_OK:  # WHY: mirror original HTTP gate
            return []  # WHY: no devices on failure
        all_devices = self._state.mistapi_ref.get_all(  # WHY: pagination helper exhausts result set
            response=devices_response, mist_session=self._state.api_session_ref
        )
        return [d for d in all_devices if d.get("map_id") == url_map_id]  # WHY: filter to map

    def _fetch_zones_for_map(self, url_map_id: str, site_id_local: str) -> list[dict[str, Any]]:
        """Fetch site zones and filter to ``url_map_id``."""
        zones_response = self._state.mistapi_ref.api.v1.sites.zones.listSiteZones(  # WHY: paged zones call
            self._state.api_session_ref, site_id=site_id_local
        )
        if zones_response.status_code != _HTTP_OK:  # WHY: mirror original HTTP gate
            return []  # WHY: no zones on failure
        all_zones = self._state.mistapi_ref.get_all(  # WHY: pagination helper exhausts result set
            response=zones_response, mist_session=self._state.api_session_ref
        )
        return [z for z in all_zones if z.get("map_id") == url_map_id]  # WHY: filter to map

    def _fetch_clients_for_map(self, url_map_id: str, site_id_local: str) -> list[dict[str, Any]]:
        """Fetch wireless clients filtered to ``url_map_id`` (with coordinates)."""
        clients_response = self._state.mistapi_ref.api.v1.sites.stats.listSiteWirelessClientsStats(  # WHY: clients call
            self._state.api_session_ref, site_id=site_id_local, limit=_CLIENTS_PAGE_LIMIT
        )
        if clients_response.status_code != _HTTP_OK:  # WHY: mirror original HTTP gate
            return []  # WHY: no clients on failure
        all_clients = self._state.mistapi_ref.get_all(  # WHY: exhaust pagination
            response=clients_response, mist_session=self._state.api_session_ref
        )
        return [  # WHY: filter: same map + has x coordinate (matches original)
            c for c in all_clients if c.get("map_id") == url_map_id and c.get("x") is not None
        ]

    def _build_url_switch_figure(self, ctx: _FigureBuildContext) -> Any:  # WHY: dataclass collapses params
        """Compose a Plotly figure for a URL-driven map switch (background + layers + theme)."""
        import plotly.graph_objects as go  # WHY: local import - heavy module

        layers = ctx.layers  # WHY: shorthand alias
        map_data = layers.map_data  # WHY: shorthand alias
        map_width = map_data.get("width", _DEFAULT_MAP_WIDTH)  # WHY: derive width with default
        map_height = map_data.get("height", _DEFAULT_MAP_HEIGHT)  # WHY: derive height with default
        ppm_local = map_data.get("ppm") or _DEFAULT_PPM  # WHY: mirror original ppm default
        new_fig = go.Figure()  # WHY: start empty figure
        self._site._add_background_image(  # WHY: reuse extracted site-cluster helper
            new_fig, map_data, map_width, map_height, anchor_top=False
        )
        self._state.figure_builder.add_walls(new_fig, map_data)  # WHY: walls layer (reuse collaborator)
        self._state.figure_builder.add_wayfinding(new_fig, map_data)  # WHY: wayfinding layer
        self._state.figure_builder.add_zones(new_fig, layers.zones)  # WHY: zones layer
        self._add_url_switch_devices(new_fig, layers.devices)  # WHY: device markers + labels + crosshairs
        self._add_url_switch_clients(new_fig, layers.clients)  # WHY: client markers + labels
        self._add_url_switch_origin(new_fig, map_data)  # WHY: origin marker
        self._add_url_switch_heatmap(new_fig, ctx.url_map_id, ctx.site_id_local, ppm_local, ctx.config)  # WHY: RF
        self._apply_url_switch_layout(new_fig, map_data.get("name", _DEFAULT_MAP_NAME), map_width, map_height)
        return new_fig  # WHY: fully-composed figure

    def _add_url_switch_devices(self, fig: Any, devices: list[dict[str, Any]]) -> None:
        """Group devices by type and add full marker/label/crosshair traces (mirrors original)."""
        device_types = self._group_devices_by_type(devices)  # WHY: {type: [devices...]}
        for device_type, type_cfg in _DEVICE_TYPE_CONFIG.items():  # WHY: iterate same config as original
            type_devices = device_types.get(device_type, [])  # WHY: filter to this type
            if not type_devices:  # WHY: skip empty types
                continue
            self._render_url_switch_device_type(fig, type_devices, type_cfg)  # WHY: per-type render

    @staticmethod
    def _group_devices_by_type(devices: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Group devices into ap/switch/gateway buckets (requires x and y coords)."""
        buckets: dict[str, list[dict[str, Any]]] = {"ap": [], "switch": [], "gateway": []}  # WHY: known buckets
        for device in devices:  # WHY: single pass
            device_type = device.get("type", "ap")  # WHY: default to ap when type missing
            if device.get("x") is None or device.get("y") is None:  # WHY: skip un-placed devices
                continue
            if device_type in buckets:  # WHY: only known types
                buckets[device_type].append(device)  # WHY: append to matching bucket
        return buckets  # WHY: return grouped dict

    def _render_url_switch_device_type(
        self,
        fig: Any,  # WHY: target Plotly figure
        type_devices: list[dict[str, Any]],  # WHY: devices of one type
        type_cfg: dict[str, Any],  # WHY: type styling config
    ) -> None:
        """Render the marker trace + labels + crosshairs for one device type."""
        arrays = self._build_device_arrays(type_devices, type_cfg)  # WHY: compute parallel arrays once
        self._add_url_switch_marker_trace(fig, arrays, type_cfg)  # WHY: marker layer
        self._add_url_switch_device_labels(fig, arrays, type_cfg)  # WHY: annotation layer
        self._add_url_switch_orientation_crosshairs(fig, arrays, type_cfg)  # WHY: orientation crosshairs

    @staticmethod
    def _build_device_arrays(
        type_devices: list[dict[str, Any]],  # WHY: devices for one type
        type_cfg: dict[str, Any],  # WHY: styling config with color palette
    ) -> _DeviceRenderArrays:
        """Compute parallel x/y/name/color/hover arrays for one device type."""
        x_coords = [d["x"] for d in type_devices]  # WHY: pixel x list
        y_coords = [d["y"] for d in type_devices]  # WHY: pixel y list
        names = [d.get("name", d.get("mac", "Unknown")) for d in type_devices]  # WHY: display label list
        colors: list[str] = []  # WHY: per-device color
        hovers: list[str] = []  # WHY: per-device hover HTML
        for device in type_devices:  # WHY: single pass to fill color+hover
            device_status = _resolve_device_status(device)  # WHY: classify state
            colors.append(type_cfg["colors"][device_status])  # WHY: color from type config
            hovers.append(_build_device_hover(device, device_status))  # WHY: hover text
        return _DeviceRenderArrays(  # WHY: bundle everything into a value object
            x_coords=x_coords,
            y_coords=y_coords,
            names=names,
            colors=colors,
            hover_texts=hovers,
            type_devices=type_devices,
        )

    @staticmethod
    def _add_url_switch_marker_trace(
        fig: Any,  # WHY: target Plotly figure
        arrays: _DeviceRenderArrays,  # WHY: parallel arrays for this device type
        type_cfg: dict[str, Any],  # WHY: styling config
    ) -> None:
        """Add the per-type marker trace (preserves original styling)."""
        import plotly.graph_objects as go  # WHY: local import - heavy module

        marker = _build_type_marker(type_cfg, arrays.colors)  # WHY: shared marker builder
        fig.add_trace(  # WHY: append scatter marker trace
            go.Scatter(
                x=arrays.x_coords,  # WHY: pixel x positions
                y=arrays.y_coords,  # WHY: pixel y positions
                mode="markers",  # WHY: markers-only trace
                name=type_cfg["name"],  # WHY: legend label
                marker=marker,  # WHY: shared marker dict
                hovertext=arrays.hover_texts,  # WHY: per-device hover payload
                hoverinfo="text",  # WHY: hover uses only hovertext
                visible=True,  # WHY: shown by default
                showlegend=True,  # WHY: appears in legend
            )
        )

    @staticmethod
    def _add_url_switch_device_labels(
        fig: Any,  # WHY: target Plotly figure
        arrays: _DeviceRenderArrays,  # WHY: parallel arrays for annotations
        type_cfg: dict[str, Any],  # WHY: styling config
    ) -> None:
        """Add per-device name annotations under each marker."""
        for x, y, name, device_color in zip(  # WHY: parallel iteration over all 4 arrays
            arrays.x_coords, arrays.y_coords, arrays.names, arrays.colors, strict=True
        ):
            fig.add_annotation(  # WHY: label placed below marker
                x=x,
                y=y - _LABEL_Y_OFFSET,  # WHY: offset below marker
                text=f"<b>{name}</b>",  # WHY: bold display name
                showarrow=False,  # WHY: no arrow needed
                font=dict(size=11, color="white", family="Arial Black"),  # WHY: original font
                bgcolor="rgba(0,0,0,0.85)",  # WHY: original bg
                bordercolor=device_color,  # WHY: border matches device color
                borderwidth=2,  # WHY: original border width
                borderpad=3,  # WHY: original padding
                xanchor="center",  # WHY: center on x
                yanchor="bottom",  # WHY: anchor at bottom
                name=f"{type_cfg['name']} Label",  # WHY: annotation grouping
            )

    def _add_url_switch_orientation_crosshairs(
        self,
        fig: Any,  # WHY: target Plotly figure
        arrays: _DeviceRenderArrays,  # WHY: parallel arrays for orientation
        type_cfg: dict[str, Any],  # WHY: styling config
    ) -> None:
        """Add horizontal+vertical lines + directional dot per device (mirrors original)."""
        import math  # WHY: local import - lightweight

        import plotly.graph_objects as go  # WHY: local import - heavy module

        legend_name = f"{type_cfg['name']} Orientation"  # WHY: shared legend group name
        for x, y, device, device_color in zip(  # WHY: parallel iteration over all 4 arrays
            arrays.x_coords, arrays.y_coords, arrays.type_devices, arrays.colors, strict=True
        ):
            crosshair = _CrosshairSpec(x=x, y=y, device_color=device_color, legend_name=legend_name)  # WHY: bundle
            self._add_crosshair_lines(fig, crosshair, go)  # WHY: add horiz+vert lines
            orient = _OrientationSpec(  # WHY: bundle orientation dot inputs
                x=x,
                y=y,
                orientation=device.get("orientation", 0),
                device_color=device_color,
                legend_name=legend_name,
            )
            self._add_orientation_dot(fig, orient, math, go)  # WHY: add directional dot

    @staticmethod
    def _add_crosshair_lines(fig: Any, spec: _CrosshairSpec, go: Any) -> None:  # WHY: dataclass collapses params
        """Add the horizontal + vertical crosshair lines for one device."""
        line_style = dict(color=spec.device_color, width=3)  # WHY: shared stroke config
        fig.add_trace(  # WHY: horizontal line trace
            go.Scatter(
                x=[spec.x - _CROSSHAIR_SIZE_PX, spec.x + _CROSSHAIR_SIZE_PX],  # WHY: horizontal endpoints
                y=[spec.y, spec.y],  # WHY: constant y
                mode="lines",  # WHY: line-only trace
                line=line_style,  # WHY: reuse stroke config
                name=spec.legend_name,  # WHY: legend grouping
                showlegend=False,  # WHY: hidden from legend
                hoverinfo="skip",  # WHY: no hover
            )
        )
        fig.add_trace(  # WHY: vertical line trace
            go.Scatter(
                x=[spec.x, spec.x],  # WHY: constant x
                y=[spec.y - _CROSSHAIR_SIZE_PX, spec.y + _CROSSHAIR_SIZE_PX],  # WHY: vertical endpoints
                mode="lines",  # WHY: line-only trace
                line=line_style,  # WHY: reuse stroke config
                name=spec.legend_name,  # WHY: legend grouping
                showlegend=False,  # WHY: hidden from legend
                hoverinfo="skip",  # WHY: no hover
            )
        )

    @staticmethod
    def _add_orientation_dot(fig: Any, orient: _OrientationSpec, math: Any, go: Any) -> None:  # WHY: dataclass
        """Add the directional dot showing each device's orientation angle."""
        math_angle = _ORIENTATION_ANGLE_OFFSET - orient.orientation  # WHY: mirror original angle conversion
        rad = math.radians(math_angle)  # WHY: convert to radians for trig
        dot_x = orient.x + _DOT_DISTANCE_PX * math.cos(rad)  # WHY: displace along x
        dot_y = orient.y - _DOT_DISTANCE_PX * math.sin(rad)  # WHY: displace along y (negated y-axis)
        fig.add_trace(  # WHY: dot trace at computed position
            go.Scatter(
                x=[dot_x],  # WHY: single-point x
                y=[dot_y],  # WHY: single-point y
                mode="markers",  # WHY: marker-only
                marker=dict(  # WHY: original dot styling
                    size=12,
                    color=orient.device_color,
                    symbol="circle",
                    line=dict(color="black", width=2),
                ),
                name=orient.legend_name,  # WHY: legend grouping
                showlegend=False,  # WHY: hidden from legend
                hoverinfo="skip",  # WHY: no hover
            )
        )

    def _add_url_switch_clients(self, fig: Any, clients: list[dict[str, Any]]) -> None:
        """Add client markers + per-client annotation labels (mirrors original)."""
        client_x, client_y, client_hover, client_names = self._collect_client_arrays(clients)  # WHY: parallel arrays
        if not client_x:  # WHY: nothing to add
            return
        self._add_url_switch_client_trace(fig, client_x, client_y, client_hover)  # WHY: marker trace
        self._add_url_switch_client_labels(fig, client_x, client_y, client_names)  # WHY: annotation loop

    @staticmethod
    def _add_url_switch_client_trace(  # WHY: extracted trace call to keep parent ≤25 lines
        fig: Any,
        client_x: list[float],
        client_y: list[float],
        client_hover: list[str],
    ) -> None:
        """Add the client marker scatter trace."""
        import plotly.graph_objects as go  # WHY: local import - heavy module

        fig.add_trace(  # WHY: append client scatter
            go.Scatter(
                x=client_x,  # WHY: pixel x
                y=client_y,  # WHY: pixel y
                mode="markers",  # WHY: markers-only
                name="Clients",  # WHY: legend label
                marker=_CLIENT_MARKER,  # WHY: shared client marker style
                hovertext=client_hover,  # WHY: per-client hover
                hoverinfo="text",  # WHY: hover uses only hovertext
                visible=True,  # WHY: shown by default
                showlegend=True,  # WHY: appears in legend
            )
        )

    @staticmethod
    def _add_url_switch_client_labels(  # WHY: extracted annotation loop to keep parent ≤25 lines
        fig: Any,
        client_x: list[float],
        client_y: list[float],
        client_names: list[str],
    ) -> None:
        """Add annotation labels beneath each client marker."""
        for x, y, name in zip(client_x, client_y, client_names, strict=True):  # WHY: parallel iteration
            fig.add_annotation(  # WHY: label placed below marker
                x=x,
                y=y - _CLIENT_LABEL_Y_OFFSET,  # WHY: closer to marker than device labels
                text=f"<b>{name}</b>",  # WHY: bold display label
                showarrow=False,  # WHY: no arrow
                font=dict(size=9, color="white", family="Arial"),  # WHY: original font
                bgcolor="rgba(0,128,0,0.9)",  # WHY: green translucent bg
                bordercolor="white",  # WHY: white border
                borderwidth=1,  # WHY: thin border
                borderpad=2,  # WHY: original padding
                xanchor="center",  # WHY: center on x
                yanchor="bottom",  # WHY: anchor at bottom
                name="Clients Label",  # WHY: annotation grouping
            )

    @staticmethod
    def _collect_client_arrays(
        clients: list[dict[str, Any]],  # WHY: raw client list
    ) -> tuple[list[float], list[float], list[str], list[str]]:
        """Walk clients once, returning parallel arrays of x/y/hover/name."""
        client_x: list[float] = []  # WHY: pixel x
        client_y: list[float] = []  # WHY: pixel y
        client_hover: list[str] = []  # WHY: hover HTML
        client_names: list[str] = []  # WHY: display label
        for client in clients:  # WHY: single pass
            x = client.get("x")  # WHY: pixel x lookup
            y = client.get("y")  # WHY: pixel y lookup
            if x is None or y is None:  # WHY: skip un-placed clients
                continue
            client_x.append(x)  # WHY: accumulate x
            client_y.append(y)  # WHY: accumulate y
            client_names.append(_client_label(client))  # WHY: accumulate label
            client_hover.append(_build_client_hover(client, x, y))  # WHY: accumulate hover HTML
        return client_x, client_y, client_hover, client_names  # WHY: return parallel arrays

    @staticmethod
    def _add_url_switch_origin(fig: Any, map_data: dict[str, Any]) -> None:
        """Add the map-origin marker (hidden by default)."""
        import plotly.graph_objects as go  # WHY: local import - heavy module

        origin = map_data.get("origin", {}) or {}  # WHY: safe default when key missing
        fig.add_trace(  # WHY: hidden origin marker trace
            go.Scatter(
                x=[origin.get("x", 0)],  # WHY: single-point x (default 0 when unset)
                y=[origin.get("y", 0)],  # WHY: single-point y (default 0 when unset)
                mode="markers+text",  # WHY: marker + label
                name="Map Origin",  # WHY: legend label
                marker=_ORIGIN_MARKER,  # WHY: shared origin marker style
                text=["Origin"],  # WHY: static label
                textposition="top center",  # WHY: label above marker
                textfont=dict(color="yellow", size=10),  # WHY: original font
                visible=False,  # WHY: hidden by default (toggle in legend)
                showlegend=True,  # WHY: still shown in legend to toggle
            )
        )

    def _add_url_switch_heatmap(
        self,
        fig: Any,  # WHY: target Plotly figure
        url_map_id: str,  # WHY: map id for coverage endpoint
        site_id_local: str,  # WHY: site id fallback
        ppm_local: float,  # WHY: pixels-per-meter for heatmap scaling
        config: dict[str, Any],  # WHY: config store may override site_id
    ) -> None:
        """Fetch RF coverage and add a heatmap trace; silently logs on failure."""
        site_id_for_coverage = config.get("site_id") or site_id_local  # WHY: mirror original site_id source
        if not site_id_for_coverage:  # WHY: mirror original guard
            logging.warning("URL map switch: Cannot fetch RF coverage - site_id is None")
            return
        try:
            coverage_data = self._fetch_url_switch_coverage(url_map_id, site_id_for_coverage)  # WHY: coverage fetch
            if coverage_data is None:  # WHY: already logged inside helper
                return
            self._render_url_switch_heatmap(fig, coverage_data, ppm_local, url_map_id)  # WHY: render layer
        except Exception as rf_error:  # WHY: mirror original catch-all
            logging.warning("URL map switch: Could not load RF coverage - %s", rf_error, exc_info=True)

    def _fetch_url_switch_coverage(self, url_map_id: str, site_id_for_coverage: str) -> dict[str, Any] | None:
        """Hit the RF coverage endpoint; return parsed data or None on failure/error envelope."""
        coverage_url = f"/api/v1/sites/{site_id_for_coverage}/location/coverage"  # WHY: mirror original path
        coverage_params = dict(_COVERAGE_QUERY_PARAMS, map_id=url_map_id)  # WHY: add map_id to shared params
        logging.info("URL map switch: Fetching RF coverage for map %s", url_map_id)
        coverage_response = self._state.api_session_ref.mist_get(coverage_url, query=coverage_params)  # WHY: HTTP call
        if coverage_response.status_code != _HTTP_OK:  # WHY: mirror original HTTP gate
            logging.warning("URL map switch: RF coverage API returned HTTP %s", coverage_response.status_code)
            return None
        coverage_data: dict[str, Any] = coverage_response.data  # WHY: explicit annotation coerces Any for strict typing
        if isinstance(coverage_data, dict) and "exception" in coverage_data:  # WHY: error envelope check
            logging.warning(
                "URL map switch: RF Coverage backend error - %s",
                str(coverage_data.get("exception", ""))[:_ERROR_MSG_TRUNCATE],
            )
            return None
        return coverage_data  # WHY: return parsed payload

    def _render_url_switch_heatmap(
        self,
        fig: Any,  # WHY: target Plotly figure
        coverage_data: dict[str, Any],  # WHY: parsed coverage payload
        ppm_local: float,  # WHY: pixels-per-meter for grid scaling
        url_map_id: str,  # WHY: for log correlation
    ) -> None:
        """Build + add the heatmap trace from coverage payload (or log gracefully)."""
        results = coverage_data.get("results", [])  # WHY: list of grid rows
        result_def = coverage_data.get("result_def", [])  # WHY: column-name schema
        logging.info("URL map switch: RF coverage API returned %d grid points", len(results))
        if not results or not result_def:  # WHY: mirror original empty-payload log
            logging.info("URL map switch: No RF coverage data available for this map (empty results)")
            return
        indices = self._resolve_url_switch_indices(result_def)  # WHY: (x, y, max_rssi) indices
        grid_data = self._build_url_switch_grid(results, indices, ppm_local)  # WHY: filtered grid
        if not grid_data:  # WHY: mirror original empty-grid log
            logging.warning("URL map switch: RF coverage - no valid grid data after processing %d points", len(results))
            return
        self._add_url_switch_heatmap_trace(fig, grid_data, url_map_id)  # WHY: append heatmap

    @staticmethod
    def _resolve_url_switch_indices(result_def: list[str]) -> tuple[int, int, int]:
        """Find (x, y, max_rssi) column indices in ``result_def`` (falls back to 0,1,4)."""
        try:
            return result_def.index("x"), result_def.index("y"), result_def.index("max_rssi")  # WHY: named lookup
        except ValueError as idx_error:  # WHY: mirror original log + fallback
            logging.warning("URL map switch: Coverage data missing expected fields in result_def: %s", idx_error)
            return 0, 1, _MAX_RSSI_FALLBACK_IDX  # WHY: original positional fallback

    @staticmethod
    def _build_url_switch_grid(
        results: list[list[Any]],  # WHY: raw grid rows
        indices: tuple[int, int, int],  # WHY: column indices
        ppm_local: float,  # WHY: pixels-per-meter conversion factor
    ) -> dict[tuple[float, float], float]:
        """Convert raw row-list results into a ``{(px_x, px_y): max_rssi}`` dict."""
        max_idx = max(indices)  # WHY: guard row shape once
        processed = (_process_grid_row(item, indices, max_idx, ppm_local) for item in results)  # WHY: lazy pipe
        return {coords: rssi for entry in processed if entry is not None for coords, rssi in [entry]}  # WHY: dict comp

    @staticmethod
    def _add_url_switch_heatmap_trace(
        fig: Any,  # WHY: target Plotly figure
        grid_data: dict[tuple[float, float], float],  # WHY: sparse coverage grid
        url_map_id: str,  # WHY: log correlation id
    ) -> None:
        """Build z-matrix from sparse grid_data and add the Heatmap trace."""
        all_rssi = list(grid_data.values())  # WHY: flatten values for min/max
        unique_x = sorted({x for x, _y in grid_data})  # WHY: distinct x bins
        unique_y = sorted({y for _x, y in grid_data})  # WHY: distinct y bins
        spec = _HeatmapSpec(  # WHY: bundle inputs to keep append helper ≤5 params
            unique_x=unique_x,
            unique_y=unique_y,
            z_matrix=[[grid_data.get((x_val, y_val)) for x_val in unique_x] for y_val in unique_y],
            min_rssi=min(all_rssi),
            max_rssi_val=max(all_rssi),
        )
        _ViewerUrlSwitch._append_heatmap(fig, spec)  # WHY: append trace
        logging.info(
            "URL map switch: Added RF coverage heatmap with %d cells, RSSI range %s to %s dBm (map %s)",
            len(grid_data),
            spec.min_rssi,
            spec.max_rssi_val,
            url_map_id,
        )

    @staticmethod
    def _append_heatmap(fig: Any, spec: _HeatmapSpec) -> None:  # WHY: dataclass collapses params
        """Append the Plotly Heatmap trace to ``fig`` using the sparse grid summary."""
        import plotly.graph_objects as go  # WHY: local import - heavy module

        fig.add_trace(  # WHY: append heatmap trace
            go.Heatmap(
                x=spec.unique_x,  # WHY: x bin coordinates
                y=spec.unique_y,  # WHY: y bin coordinates
                z=spec.z_matrix,  # WHY: dense z-matrix
                colorscale=_HEATMAP_COLORSCALE,  # WHY: shared 5-stop palette
                zmin=spec.min_rssi,  # WHY: colorscale lower bound
                zmax=spec.max_rssi_val,  # WHY: colorscale upper bound
                opacity=0.5,  # WHY: original alpha
                name="RF Coverage",  # WHY: legend label
                visible=False,  # WHY: hidden by default (toggle in legend)
                showscale=True,  # WHY: colorbar shown when visible
                colorbar=_HEATMAP_COLORBAR,  # WHY: extracted colorbar config
                connectgaps=True,  # WHY: fill gaps between cells
                zsmooth="best",  # WHY: smooth rendering
            )
        )

    @staticmethod
    def _apply_url_switch_layout(
        fig: Any,  # WHY: target Plotly figure
        new_map_name: str,  # WHY: title text
        new_map_width: int,  # WHY: xaxis range
        new_map_height: int,  # WHY: yaxis range (inverted)
    ) -> None:
        """Apply the URL-switch figure layout (preserves original styling)."""
        xaxis = {**_LAYOUT_XAXIS_BASE, "range": [0, new_map_width]}  # WHY: pixel bounds on shared base
        yaxis = {**_LAYOUT_YAXIS_BASE, "range": [new_map_height, 0]}  # WHY: inverted y on shared base
        fig.update_layout(  # WHY: single layout update mirrors original
            title=dict(text=f"Map: {new_map_name}", font=dict(color="white")),  # WHY: title text
            xaxis=xaxis,  # WHY: extracted x config
            yaxis=yaxis,  # WHY: extracted y config
            plot_bgcolor="#1a1a1a",  # WHY: original bg
            paper_bgcolor="#1a1a1a",  # WHY: original bg
            font=dict(color="#e0e0e0"),  # WHY: light font on dark bg
            showlegend=True,  # WHY: legend visible
            legend=_LAYOUT_LEGEND,  # WHY: shared legend config
            margin=_LAYOUT_MARGIN,  # WHY: shared margins
        )

    @staticmethod
    def _merge_url_switch_config(
        config: dict[str, Any],  # WHY: current config store
        url_map_id: str,  # WHY: new map id
        new_map_data: dict[str, Any],  # WHY: new map metadata source
    ) -> dict[str, Any]:
        """Update ``config`` with the newly-switched map info (preserves site_id)."""
        new_config = config.copy()  # WHY: don't mutate caller's dict
        new_config["map_id"] = url_map_id  # WHY: set new map id
        new_config["map_name"] = new_map_data.get("name", _DEFAULT_MAP_NAME)  # WHY: display name
        new_config["ppm"] = new_map_data.get("ppm") or _DEFAULT_PPM  # WHY: coverage scaling
        new_config["map_width"] = new_map_data.get("width", _DEFAULT_MAP_WIDTH)  # WHY: pixel width
        new_config["map_height"] = new_map_data.get("height", _DEFAULT_MAP_HEIGHT)  # WHY: pixel height
        return new_config  # WHY: return the updated store payload

    # ------------------------------------------------------------------
    # Callback wiring
    # ------------------------------------------------------------------

    def register(self, app: Dash) -> None:  # WHY: hooks this wave's app.callback(...) blocks into Dash
        """Attach the URL-switch callback in this cluster to ``app``."""
        from dash import Input, Output, State  # WHY: local import keeps module import-light

        app.callback(  # WHY: handle_url_map_switch - map switch triggered by URL change
            [
                Output("map-display", "figure", allow_duplicate=True),  # WHY: replaces the figure
                Output("map-config-store", "data", allow_duplicate=True),  # WHY: updates current-map config
            ],
            [Input("url-location", "search")],  # WHY: URL change trigger
            [
                State("map-config-store", "data"),  # WHY: current config
                State("map-display", "figure"),  # WHY: current figure
                State("available-maps-store", "data"),  # WHY: map allow-list
                State("map-selector-dropdown", "value"),  # WHY: current selection
            ],
            prevent_initial_call="initial_duplicate",  # WHY: allow initial run on duplicate output
        )(self.handle_url_map_switch)
