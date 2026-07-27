"""Map fetch / coverage / payload cluster (extracted from MapsManager).

Split out of ``src/maps/maps_manager.py`` so the ~338 LOC layer-fetch
flow lives in its own module. The extracted methods stay as methods of
a small wrapper class :class:`_MapsCoverage`; ``__getattr__`` delegates
lookups that miss on the wrapper to the wrapped MapsManager, so calls
to ``self._resolve_site_name``, ``self._extract_walls``, and
``self._extract_wayfinding`` (which still live on MapsManager) resolve
without rewrites.

MapsManager instantiates :class:`_MapsCoverage` directly from its own
delegating wrappers because ``launch_viewer_standalone`` passes
``self._collect_map_payload`` and ``self._build_map_data_response`` as
bound-method callables to ``launch_flask_viewer``.
"""

from __future__ import annotations  # WHY: enable postponed annotations for slim class refs.

import logging  # WHY: emit warnings on API failures without raising.
from collections.abc import Callable  # WHY: modern typing home for Callable per UP035.
from dataclasses import dataclass, fields  # WHY: model the layer bundle immutably.
from typing import Any  # WHY: type API-session opaque object.

import mistapi  # WHY: Mist SDK for site/device/map fetch.

logger = logging.getLogger(__name__)  # WHY: module-scoped logger separates the log surface.

# Fetch-side tuning knobs kept as named constants so intent is obvious.
_DEVICE_LIMIT = 1000  # WHY: cap Mist site-devices response so we never page.
_DEFAULT_RSSI = -80  # WHY: sentinel RSSI when the coverage grid omits max/avg_rssi.
_COVERAGE_INDEX_FALLBACK: tuple[int, int, int] = (0, 1, 4)  # WHY: legacy Mist row layout when result_def lookup fails.
_COVERAGE_PARAMS_BASE: dict[str, str] = {  # WHY: static query params shared by every coverage layer request.
    "resolution": "fine",  # WHY: request the highest-resolution coverage tiles.
    "duration": "1d",  # WHY: aggregate over the last day for a stable heat map.
    "from_apollo": "true",  # WHY: switch Mist backend to the Apollo coverage engine.
}
_DEFAULT_MAP_DIMENSION = 1000  # WHY: fallback map width/height when Mist omits the field.
_DEFAULT_PPM = 1.0  # WHY: neutral pixels-per-meter when Mist omits ppm.

# Sentinel returned by :func:`_safe_call` when an API call fails or produces empty data.
_EMPTY_RESPONSE: Any = None  # WHY: named sentinel improves grep-ability over bare `None` compares.


def _safe_call(label: str, api_call: Callable[[], Any]) -> Any:  # WHY: shared safe API-call wrapper.
    """Invoke ``api_call`` and return the response or ``None`` on failure/empty."""
    try:  # WHY: Mist SDK raises broadly (HTTP, JSON, connection). We log and continue.
        response = api_call()  # WHY: run the caller-provided Mist API call.
    except Exception as exc:  # WHY: never crash a map-render because one layer failed.
        logging.warning("Error fetching %s: %s", label, exc)  # WHY: preserve prior log format for grep.
        return _EMPTY_RESPONSE  # WHY: signal failure to the caller with a shared sentinel.
    if response.status_code != 200 or not response.data:  # WHY: guard against error status or empty payload.
        return _EMPTY_RESPONSE  # WHY: treat empty/non-OK like a soft failure.
    return response  # WHY: hand back the intact response object for projection.


def _select_on_map(
    items: list[dict[str, Any]], map_id: str, projector: Callable[[dict[str, Any]], dict[str, Any]]
) -> list[dict[str, Any]]:  # WHY: shared map filter.
    """Project ``items`` filtered to those bound to ``map_id`` with a non-None ``x``."""
    return [projector(item) for item in items if _is_on_map(item, map_id)]  # WHY: keep listcomp CC bounded.


def _select_with_x(
    items: list[dict[str, Any]], projector: Callable[[dict[str, Any]], dict[str, Any]]
) -> list[dict[str, Any]]:  # WHY: no-map filter variant.
    """Project ``items`` that have a non-None ``x`` regardless of map binding."""
    return [
        projector(item) for item in items if item.get("x") is not None
    ]  # WHY: for endpoints already scoped by map_id.


def _is_on_map(item: dict[str, Any], map_id: str) -> bool:  # WHY: shared predicate for on-map records.
    """Return True when ``item`` is placed on ``map_id`` and has a non-None ``x``."""
    return item.get("map_id") == map_id and item.get("x") is not None  # WHY: shared filter for layer records.


def _project_device(device: dict[str, Any]) -> dict[str, Any]:  # WHY: shape one Mist device record for the viewer.
    """Project a Mist device-stats record down to the viewer's display fields."""
    return {  # WHY: viewer only needs a subset of the Mist device schema.
        "x": device.get("x"),  # WHY: pixel-space x coordinate.
        "y": device.get("y"),  # WHY: pixel-space y coordinate.
        "name": device.get("name", device.get("mac", "Unknown")),  # WHY: fall back to MAC when name missing.
        "type": device.get("type", "ap"),  # WHY: default to AP because most map devices are APs.
        "status": device.get("status", "unknown"),  # WHY: keep a status placeholder for the legend.
        "mac": device.get("mac", ""),  # WHY: MAC is used for click-through detail lookups.
        "orientation": device.get("orientation", 0),  # WHY: rotate the AP icon on the map.
    }


def _project_zone(zone: dict[str, Any]) -> dict[str, Any]:  # WHY: shape one zone record for the viewer.
    """Project a zone record to the viewer's name/vertices shape."""
    return {"name": zone.get("name", "Zone"), "vertices": zone.get("vertices", [])}  # WHY: viewer needs a stable shape.


def _project_wifi_client(client: dict[str, Any]) -> dict[str, Any]:  # WHY: shape one connected WiFi client.
    """Project a wireless-client stats record down to the viewer's display fields."""
    return {  # WHY: the viewer draws WiFi clients as small dots with a tooltip.
        "x": client.get("x"),  # WHY: pixel-space x coordinate.
        "y": client.get("y"),  # WHY: pixel-space y coordinate.
        "mac": client.get("mac", "Unknown"),  # WHY: MAC is the primary identifier for a client.
        "ssid": client.get("ssid", "-"),  # WHY: dash preserves table alignment when SSID missing.
        "name": client.get("hostname", "") or client.get("name", ""),  # WHY: prefer DHCP hostname over Mist name.
    }


def _project_unconnected_client(client: dict[str, Any]) -> dict[str, Any]:  # WHY: shape one unconnected client.
    """Project an unconnected-client record to the viewer's display fields."""
    return {  # WHY: unconnected clients only carry MAC + manufacturer.
        "x": client.get("x"),  # WHY: pixel-space x coordinate.
        "y": client.get("y"),  # WHY: pixel-space y coordinate.
        "mac": client.get("mac", "Unknown"),  # WHY: identifier when hostname is unavailable.
        "manufacture": client.get("manufacture", "-"),  # WHY: dash preserves table alignment.
    }


def _project_ble_device(device: dict[str, Any]) -> dict[str, Any]:  # WHY: shape one BLE-asset record.
    """Project a BLE-discovered asset record to the viewer's display fields."""
    return {
        "x": device.get("x"),
        "y": device.get("y"),
        "mac": device.get("mac", "Unknown"),
    }  # WHY: BLE only needs xy+mac.


def _project_asset(asset: dict[str, Any]) -> dict[str, Any]:  # WHY: shape one named-asset record.
    """Project a named-asset record to the viewer's display fields."""
    return {  # WHY: assets show name + MAC label in the viewer.
        "x": asset.get("x"),  # WHY: pixel-space x coordinate.
        "y": asset.get("y"),  # WHY: pixel-space y coordinate.
        "name": asset.get("name", "Asset"),  # WHY: generic label preserves rendering.
        "mac": asset.get("mac", "-"),  # WHY: dash preserves table alignment.
    }


def _project_sdk_client(client: dict[str, Any]) -> dict[str, Any]:  # WHY: shape one SDK/Marvis client.
    """Project an SDK/Marvis indoor-location record to the viewer's display fields."""
    return {  # WHY: SDK clients carry a UUID rather than a MAC.
        "x": client.get("x"),  # WHY: pixel-space x coordinate.
        "y": client.get("y"),  # WHY: pixel-space y coordinate.
        "name": client.get("name", ""),  # WHY: SDK app-supplied label.
        "uuid": client.get("uuid", "-"),  # WHY: dash preserves table alignment when UUID missing.
    }


@dataclass(frozen=True)
class MapLayers:  # WHY: immutable bundle for the viewer's layer records.
    """Immutable bundle of every layer the viewer needs to render one map."""

    site_name: str  # WHY: header text in the viewer.
    walls: list[Any]  # WHY: wall segments extracted from wayfinding data.
    wayfinding: list[Any]  # WHY: graph edges for wayfinding overlays.
    devices: list[dict[str, Any]]  # WHY: on-map APs/switches/gateways.
    zones: list[dict[str, Any]]  # WHY: named polygon zones.
    wifi_clients: list[dict[str, Any]]  # WHY: connected wireless clients.
    unconnected: list[dict[str, Any]]  # WHY: unconnected wireless clients.
    ble_devices: list[dict[str, Any]]  # WHY: BLE-discovered assets.
    assets: list[dict[str, Any]]  # WHY: named RFID/BLE assets.
    sdk_clients: list[dict[str, Any]]  # WHY: SDK/Marvis indoor-location clients.
    wifi_cov: list[Any]  # WHY: WiFi coverage grid.
    ble_cov: list[Any]  # WHY: BLE (asset) coverage grid.
    app_cov: list[Any]  # WHY: SDK-app coverage grid.


class _MapsCoverage:
    """Wrapper class holding the extracted fetch/coverage/payload methods."""

    def __init__(self, maps_manager: Any) -> None:
        """Store the parent MapsManager so ``__getattr__`` can forward misses."""
        self._mm = maps_manager  # WHY: retained collaborator for _resolve_site_name / _extract_* helpers.

    def __getattr__(self, name: str) -> Any:
        """Forward attribute lookups that miss on this wrapper to the wrapped MapsManager."""
        mm = self.__dict__.get("_mm")  # WHY: avoid recursion during broken __init__ paths.
        if mm is None:  # pragma: no cover - only during broken init
            raise AttributeError(name)  # WHY: preserve normal AttributeError semantics.
        return getattr(mm, name)  # WHY: standard dunder-delegation pattern.

    def _fetch_map_devices(self, api_session: Any, site_id: str, map_id: str) -> list[dict[str, Any]]:
        """Fetch site devices and return only those located on this map."""
        response = _safe_call(  # WHY: uniform failure handling across every fetch method.
            "devices",  # WHY: log label distinguishes which layer failed.
            lambda: mistapi.api.v1.sites.stats.listSiteDevicesStats(  # WHY: Mist SDK entry-point for device stats.
                api_session,
                site_id=site_id,
                type="all",
                limit=_DEVICE_LIMIT,  # WHY: request every device type up to cap.
            ),
        )
        if response is None:  # WHY: propagate empty result when the API call failed.
            return []  # WHY: viewer treats an empty layer as "no data".
        return _select_on_map(response.data, map_id, _project_device)  # WHY: project + filter records to this map.

    def _fetch_map_zones(self, api_session: Any, site_id: str, map_id: str) -> list[dict[str, Any]]:
        """Fetch zones for this site and filter to those bound to the requested map."""
        response = _safe_call(  # WHY: shared safe-call wrapper.
            "zones",  # WHY: label surfaces which layer failed in logs.
            lambda: mistapi.api.v1.sites.zones.listSiteZones(api_session, site_id=site_id),  # WHY: Mist zones endpoint.
        )
        if response is None:  # WHY: propagate empty result when the API call failed.
            return []  # WHY: viewer treats an empty layer as "no data".
        return [_project_zone(z) for z in response.data if z.get("map_id") == map_id]  # WHY: zones lack an ``x``.

    def _fetch_map_wifi_clients(self, api_session: Any, site_id: str, map_id: str) -> list[dict[str, Any]]:
        """Fetch connected WiFi clients on this map."""
        response = _safe_call(  # WHY: shared safe-call wrapper.
            "wifi clients",  # WHY: label surfaces which layer failed in logs.
            lambda: mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(  # WHY: Mist wireless-clients endpoint.
                api_session, site_id=site_id
            ),
        )
        if response is None:  # WHY: propagate empty result when the API call failed.
            return []  # WHY: viewer treats an empty layer as "no data".
        return _select_on_map(response.data, map_id, _project_wifi_client)  # WHY: project + filter records to this map.

    def _fetch_map_unconnected_clients(self, api_session: Any, site_id: str, map_id: str) -> list[dict[str, Any]]:
        """Fetch unconnected WiFi client stats for this map."""
        response = _safe_call(  # WHY: shared safe-call wrapper.
            "unconnected clients",  # WHY: label surfaces which layer failed in logs.
            lambda: mistapi.api.v1.sites.stats.listSiteUnconnectedClientStats(  # WHY: Mist unconnected endpoint.
                api_session, site_id=site_id, map_id=map_id  # WHY: endpoint already filters by map_id server-side.
            ),
        )
        if response is None:  # WHY: propagate empty result when the API call failed.
            return []  # WHY: viewer treats an empty layer as "no data".
        return _select_with_x(response.data, _project_unconnected_client)  # WHY: no client-side map filter needed.

    def _fetch_map_ble_devices(self, api_session: Any, site_id: str, map_id: str) -> list[dict[str, Any]]:
        """Fetch BLE-discovered assets bound to this map."""
        response = _safe_call(  # WHY: shared safe-call wrapper.
            "BLE devices",  # WHY: label surfaces which layer failed in logs.
            lambda: mistapi.api.v1.sites.stats.listSiteDiscoveredAssets(  # WHY: Mist BLE-assets endpoint.
                api_session, site_id=site_id
            ),
        )
        if response is None:  # WHY: propagate empty result when the API call failed.
            return []  # WHY: viewer treats an empty layer as "no data".
        return _select_on_map(response.data, map_id, _project_ble_device)  # WHY: project + filter records to this map.

    def _fetch_map_assets(self, api_session: Any, site_id: str, map_id: str) -> list[dict[str, Any]]:
        """Fetch named assets bound to this map."""
        response = _safe_call(  # WHY: shared safe-call wrapper.
            "assets",  # WHY: label surfaces which layer failed in logs.
            lambda: mistapi.api.v1.sites.stats.listSiteAssetsStats(  # WHY: Mist assets endpoint.
                api_session, site_id=site_id
            ),
        )
        if response is None:  # WHY: propagate empty result when the API call failed.
            return []  # WHY: viewer treats an empty layer as "no data".
        return _select_on_map(response.data, map_id, _project_asset)  # WHY: project + filter records to this map.

    def _fetch_map_sdk_clients(self, api_session: Any, site_id: str, map_id: str) -> list[dict[str, Any]]:
        """Fetch SDK/Marvis indoor-location clients for this map."""
        response = _safe_call(  # WHY: shared safe-call wrapper.
            "SDK clients",  # WHY: label surfaces which layer failed in logs.
            lambda: mistapi.api.v1.sites.stats.getSiteSdkStatsByMap(  # WHY: Mist SDK-by-map endpoint.
                api_session, site_id=site_id, map_id=map_id  # WHY: endpoint already scoped by map_id server-side.
            ),
        )
        if response is None:  # WHY: propagate empty result when the API call failed.
            return []  # WHY: viewer treats an empty layer as "no data".
        return _select_with_x(response.data, _project_sdk_client)  # WHY: server-side map filter is already applied.

    @staticmethod
    def _resolve_coverage_indices(result_def: list[str]) -> tuple[int, int, int]:
        """Return (x_idx, y_idx, rssi_idx) into a coverage row, with a -1 RSSI sentinel."""
        try:  # WHY: result_def may omit expected columns. Fall back on legacy layout.
            x_idx = result_def.index("x")  # WHY: locate the x column.
            y_idx = result_def.index("y")  # WHY: locate the y column.
            rssi_idx = _pick_rssi_index(result_def)  # WHY: max_rssi preferred over avg_rssi, -1 when absent.
            return x_idx, y_idx, rssi_idx  # WHY: hand indices to the row-to-point projector.
        except ValueError:  # WHY: index() raises ValueError when a column is missing.
            return _COVERAGE_INDEX_FALLBACK  # WHY: use documented legacy positions.

    @staticmethod
    def _coverage_row_to_point(
        item: list[Any], indices: tuple[int, int, int], ppm_value: float
    ) -> dict[str, Any] | None:
        """Convert a coverage result row to a {x, y, rssi} point in pixel space."""
        x_idx, y_idx, rssi_idx = indices  # WHY: unpack once for readability below.
        if len(item) <= max(x_idx, y_idx, rssi_idx):  # WHY: guard against short rows Mist sometimes returns.
            return None  # WHY: signal caller to drop this row.
        values = _extract_row_values(item, x_idx, y_idx, rssi_idx)  # WHY: pull x/y/rssi honoring sentinel index.
        if values is None:  # WHY: any missing value invalidates the point.
            return None  # WHY: signal caller to drop this row.
        x_m, y_m, rssi = values  # WHY: unpack projected values for the pixel-space math.
        return {"x": x_m * ppm_value, "y": y_m * ppm_value, "rssi": rssi}  # WHY: convert meters to pixels.

    def _fetch_coverage_layer(
        self,
        api_session: Any,
        site_id: str,
        map_id: str,
        coverage_type: str,
        ppm_value: float,
    ) -> list[dict[str, Any]] | None:
        """Fetch one coverage layer (client/asset/sdkclient) and convert meters to pixels."""
        params = _coverage_query_params(map_id, coverage_type)  # WHY: extracted so this function stays short.
        coverage_url = _coverage_url(site_id)  # WHY: extracted so this function stays short.
        logging.info("[Flask API] Fetching %s coverage for map %s", coverage_type, map_id)  # WHY: audit trail.
        try:  # WHY: `api_session.mist_get` may raise on network errors.
            response = api_session.mist_get(coverage_url, query=params)  # WHY: fetch coverage payload from Mist.
        except Exception as exc:  # WHY: swallow errors so one bad layer does not kill the viewer.
            logging.warning("Error fetching %s coverage: %s", coverage_type, exc)  # WHY: preserve log format.
            return None  # WHY: signal missing layer to the caller.
        if response.status_code != 200:  # WHY: coverage responses may be 400 while other layers succeed.
            return None  # WHY: skip this layer without failing the whole render.
        return self._coverage_response_to_grid(response.data, ppm_value, coverage_type)  # WHY: parse to grid points.

    def _coverage_response_to_grid(
        self, coverage_data: Any, ppm_value: float, coverage_type: str
    ) -> list[dict[str, Any]] | None:
        """Parse a coverage API payload into a list of grid points, or None on error."""
        if _is_coverage_error_payload(coverage_data, coverage_type):  # WHY: API sometimes returns {"exception": ...}.
            return None  # WHY: skip layer when the coverage API reported an error.
        results = coverage_data.get("results", [])  # WHY: raw coverage rows.
        result_def = coverage_data.get("result_def", [])  # WHY: schema for interpreting each row.
        if not (results and result_def):  # WHY: viewer needs both rows and schema.
            return None  # WHY: skip layer when payload is empty.
        indices = self._resolve_coverage_indices(result_def)  # WHY: resolve column layout with fallback.
        grid_points = _rows_to_grid_points(results, indices, ppm_value)  # WHY: extracted for length + clarity.
        logging.info(  # WHY: report how many points made it through the projection.
            "[Flask API] %s coverage: %s grid points (ppm=%s)",
            coverage_type,
            len(grid_points),
            ppm_value,
        )
        return grid_points  # WHY: return the projected grid to the caller.

    def _fetch_all_coverage(
        self, api_session: Any, site_id: str, map_id: str, ppm: float
    ) -> tuple[list[Any], list[Any], list[Any]]:
        """Fetch WiFi + BLE + App coverage layers (each one is None-safe)."""
        if not ppm:  # WHY: no ppm means no meter-to-pixel conversion is possible.
            return [], [], []  # WHY: return empty layers rather than fail the whole map.
        wifi = (
            self._fetch_coverage_layer(api_session, site_id, map_id, "client", ppm) or []
        )  # WHY: WiFi client heat map.
        ble = self._fetch_coverage_layer(api_session, site_id, map_id, "asset", ppm) or []  # WHY: BLE asset heat map.
        app = self._fetch_coverage_layer(api_session, site_id, map_id, "sdkclient", ppm) or []  # WHY: SDK app heat map.
        return wifi, ble, app  # WHY: caller unpacks into the MapLayers bundle.

    @staticmethod
    def _count_devices_by_type(devices: list[dict[str, Any]]) -> tuple[int, int, int]:
        """Return (ap_count, switch_count, gateway_count) by walking the device list once."""
        counts = {"ap": 0, "switch": 0, "gateway": 0}  # WHY: single pass keeps CC low.
        for device in devices:  # WHY: iterate once across the device list.
            counts[_bucket_for_device(device)] += 1  # WHY: increment the resolved bucket.
        return counts["ap"], counts["switch"], counts["gateway"]  # WHY: preserve legacy return order.

    def _collect_map_payload(
        self, api_session: Any, all_sites: list[dict[str, Any]], site_id: str, map_id: str
    ) -> tuple[dict[str, Any] | None, MapLayers | tuple[()]]:
        """Gather every layer needed to render this map.

        Returns ``(map_data, layers)`` or ``(None, ())`` on missing map.
        """
        map_data = _fetch_map_metadata(api_session, site_id, map_id)  # WHY: bail if the base map is missing.
        if map_data is None:  # WHY: no map -> nothing to render.
            return None, ()  # WHY: preserve legacy sentinel for callers.
        layers = self._assemble_layers(api_session, all_sites, site_id, map_id, map_data)  # WHY: keep function short.
        return map_data, layers  # WHY: caller passes both to the response builder.

    def _assemble_layers(
        self, api_session: Any, all_sites: list[dict[str, Any]], site_id: str, map_id: str, map_data: dict[str, Any]
    ) -> MapLayers:
        """Fan out to every layer fetch and return an immutable :class:`MapLayers`."""
        ppm = map_data.get("ppm", _DEFAULT_PPM)  # WHY: meters-per-pixel for coverage projection.
        wifi_cov, ble_cov, app_cov = self._fetch_all_coverage(api_session, site_id, map_id, ppm)  # WHY: heat maps.
        records = self._fetch_layer_records(api_session, site_id, map_id)  # WHY: shrinks the parent function.
        return MapLayers(  # WHY: bundle every layer into a single immutable value.
            site_name=self._resolve_site_name(all_sites, site_id),  # WHY: header text for the viewer.
            walls=self._extract_walls(map_data),  # WHY: wall polylines live inside map_data.
            wayfinding=self._extract_wayfinding(map_data),  # WHY: navigation graph lives inside map_data.
            wifi_cov=wifi_cov,  # WHY: WiFi coverage grid.
            ble_cov=ble_cov,  # WHY: BLE coverage grid.
            app_cov=app_cov,  # WHY: SDK app coverage grid.
            **records,  # WHY: merge per-map record layers fetched above.
        )

    def _fetch_layer_records(self, api_session: Any, site_id: str, map_id: str) -> dict[str, list[dict[str, Any]]]:
        """Fetch every per-map record layer and return kwargs for :class:`MapLayers`."""
        return {  # WHY: dict layout mirrors MapLayers fields for **kwargs merge.
            "devices": self._fetch_map_devices(api_session, site_id, map_id),  # WHY: on-map devices.
            "zones": self._fetch_map_zones(api_session, site_id, map_id),  # WHY: named zones.
            "wifi_clients": self._fetch_map_wifi_clients(api_session, site_id, map_id),  # WHY: connected WiFi clients.
            "unconnected": self._fetch_map_unconnected_clients(api_session, site_id, map_id),  # WHY: unconnected WiFi.
            "ble_devices": self._fetch_map_ble_devices(api_session, site_id, map_id),  # WHY: BLE assets.
            "assets": self._fetch_map_assets(api_session, site_id, map_id),  # WHY: named assets.
            "sdk_clients": self._fetch_map_sdk_clients(api_session, site_id, map_id),  # WHY: SDK/Marvis clients.
        }

    def _build_map_data_response(
        self, site_id: str, map_id: str, map_data: dict[str, Any], layers: MapLayers | tuple[Any, ...]
    ) -> dict[str, Any]:
        """Assemble the final JSON dict returned by the /api/map endpoint."""
        bundle = _coerce_layers(layers)  # WHY: legacy callers may still pass a raw tuple.
        base = _base_map_section(site_id, map_id, bundle.site_name, map_data)  # WHY: header/dimensions/image sub-dict.
        counts = self._count_devices_by_type(bundle.devices)  # WHY: split by device type for the sidebar.
        return {  # WHY: single dict merges base metadata + every layer's records + counts.
            **base,  # WHY: header/dimensions/image URL live in the base section.
            **_devices_section(bundle, counts),  # WHY: devices + per-type counts.
            **_wireless_section(bundle),  # WHY: WiFi + unconnected + BLE + asset + SDK client records.
            **_topology_section(bundle),  # WHY: zones + walls + wayfinding overlays.
            **_coverage_section(bundle),  # WHY: coverage heat maps.
        }


def _pick_rssi_index(result_def: list[str]) -> int:
    """Return the RSSI column index, preferring max over avg, or -1 when neither exists."""
    if "max_rssi" in result_def:  # WHY: Mist prefers max_rssi when available.
        return result_def.index("max_rssi")  # WHY: exact column position.
    if "avg_rssi" in result_def:  # WHY: fall back to avg_rssi when max is missing.
        return result_def.index("avg_rssi")  # WHY: exact column position.
    return -1  # WHY: sentinel signals "no rssi column".


def _extract_row_values(item: list[Any], x_idx: int, y_idx: int, rssi_idx: int) -> tuple[Any, Any, Any] | None:
    """Return (x, y, rssi) from a row, or None when any value is missing."""
    x_m = item[x_idx]  # WHY: raw x in meters.
    y_m = item[y_idx]  # WHY: raw y in meters.
    rssi = item[rssi_idx] if rssi_idx >= 0 else _DEFAULT_RSSI  # WHY: honor sentinel index for RSSI.
    if x_m is None or y_m is None or rssi is None:  # WHY: any missing value invalidates the point.
        return None  # WHY: caller drops the row.
    return x_m, y_m, rssi  # WHY: hand values back for pixel conversion.


def _coverage_url(site_id: str) -> str:
    """Return the coverage endpoint URL for the given site."""
    return f"/api/v1/sites/{site_id}/location/coverage"  # WHY: single source for the URL template.


def _coverage_query_params(map_id: str, coverage_type: str) -> dict[str, str]:
    """Return the coverage query params for the given map + coverage type."""
    return {**_COVERAGE_PARAMS_BASE, "map_id": map_id, "type": coverage_type}  # WHY: keeps base params immutable.


def _is_coverage_error_payload(coverage_data: Any, coverage_type: str) -> bool:
    """Return True when the coverage payload signals an API-side exception."""
    if isinstance(coverage_data, dict) and "exception" in coverage_data:  # WHY: Mist error envelope.
        logging.warning("[Flask API] %s coverage API error", coverage_type)  # WHY: preserve prior log format.
        return True  # WHY: caller returns None so this layer is dropped.
    return False  # WHY: normal payload - proceed with parsing.


def _rows_to_grid_points(results: list[Any], indices: tuple[int, int, int], ppm_value: float) -> list[dict[str, Any]]:
    """Project each coverage row and drop rows that failed the projection."""
    projected = (
        _MapsCoverage._coverage_row_to_point(row, indices, ppm_value) for row in results
    )  # WHY: lazy generator.
    return [point for point in projected if point is not None]  # WHY: drop invalid rows in one pass.


def _bucket_for_device(device: dict[str, Any]) -> str:
    """Return the counting bucket for a device (ap|switch|gateway), defaulting to ap."""
    device_type = device.get("type")  # WHY: look up once for both branches.
    if device_type in ("switch", "gateway"):  # WHY: only these two are recognized non-AP buckets.
        return str(device_type)  # WHY: return the exact bucket name (cast Any -> str for strict typing).
    return "ap"  # WHY: unset or unknown types are treated as APs.


def _fetch_map_metadata(api_session: Any, site_id: str, map_id: str) -> dict[str, Any] | None:
    """Fetch the base map document (walls, wayfinding, ppm, url) or None on error."""
    map_response = mistapi.api.v1.sites.maps.getSiteMap(
        api_session, site_id=site_id, map_id=map_id
    )  # WHY: single call.
    if map_response.status_code != 200:  # WHY: viewer bails when the map itself cannot be loaded.
        return None  # WHY: signal missing map to the caller.
    data: dict[str, Any] | None = map_response.data  # WHY: annotate to satisfy strict mypy return type.
    return data  # WHY: hand the base map document back for layer assembly.


def _coerce_layers(layers: MapLayers | tuple[Any, ...]) -> MapLayers:
    """Return ``layers`` as a :class:`MapLayers` (accept legacy 13-tuple for back-compat)."""
    if isinstance(layers, MapLayers):  # WHY: modern callers pass the dataclass directly.
        return layers  # WHY: no coercion needed.
    field_names = tuple(field.name for field in fields(MapLayers))  # WHY: preserves declaration order.
    return MapLayers(**dict(zip(field_names, layers, strict=True)))  # WHY: strict zip catches length mismatch.


def _base_map_section(site_id: str, map_id: str, site_name: str, map_data: dict[str, Any]) -> dict[str, Any]:
    """Return the header/dimensions/image portion of the map-data response."""
    original_url = map_data.get("url", "")  # WHY: viewer only serves the proxy URL when a real URL exists.
    image_url = f"/api/map-image/{site_id}/{map_id}" if original_url else ""  # WHY: preserve legacy proxy shape.
    return {  # WHY: caller merges this section into the top-level response dict.
        "site_id": site_id,  # WHY: echo IDs back for client-side dropdown sync.
        "site_name": site_name,  # WHY: header text for the viewer.
        "map_id": map_id,  # WHY: echo IDs back for client-side dropdown sync.
        "map_name": map_data.get("name", "Unnamed"),  # WHY: default keeps the header non-empty.
        "width": map_data.get("width", _DEFAULT_MAP_DIMENSION),  # WHY: viewer needs canvas dimensions.
        "height": map_data.get("height", _DEFAULT_MAP_DIMENSION),  # WHY: viewer needs canvas dimensions.
        "image_url": image_url,  # WHY: proxied image or empty string.
        "ppm": map_data.get("ppm", _DEFAULT_PPM),  # WHY: pixel-per-meter for client-side conversions.
    }


def _devices_section(bundle: MapLayers, counts: tuple[int, int, int]) -> dict[str, Any]:
    """Return the devices sub-dict (records + per-type counts) for the response."""
    ap_count, switch_count, gateway_count = counts  # WHY: unpack once for readability.
    return {  # WHY: caller merges this section into the top-level response dict.
        "devices": bundle.devices,  # WHY: full device list for the map layer.
        "device_count": len(bundle.devices),  # WHY: sidebar shows total count.
        "ap_count": ap_count,  # WHY: sidebar breakdown by type.
        "switch_count": switch_count,  # WHY: sidebar breakdown by type.
        "gateway_count": gateway_count,  # WHY: sidebar breakdown by type.
    }


def _wireless_section(bundle: MapLayers) -> dict[str, Any]:
    """Return the wireless/asset sub-dict for the response."""
    return {  # WHY: caller merges this section into the top-level response dict.
        "wifi_clients": bundle.wifi_clients,  # WHY: connected WiFi clients.
        "wifi_client_count": len(bundle.wifi_clients),  # WHY: sidebar count.
        "unconnected_clients": bundle.unconnected,  # WHY: unconnected WiFi clients.
        "unconnected_client_count": len(bundle.unconnected),  # WHY: sidebar count.
        "ble_devices": bundle.ble_devices,  # WHY: BLE assets on the map.
        "ble_device_count": len(bundle.ble_devices),  # WHY: sidebar count.
        "assets": bundle.assets,  # WHY: named assets on the map.
        "asset_count": len(bundle.assets),  # WHY: sidebar count.
        "sdk_clients": bundle.sdk_clients,  # WHY: SDK/Marvis clients on the map.
        "sdk_client_count": len(bundle.sdk_clients),  # WHY: sidebar count.
    }


def _topology_section(bundle: MapLayers) -> dict[str, Any]:
    """Return the topology (zones/walls/wayfinding) sub-dict for the response."""
    return {  # WHY: caller merges this section into the top-level response dict.
        "zones": bundle.zones,  # WHY: named polygon zones.
        "zone_count": len(bundle.zones),  # WHY: sidebar count.
        "walls": bundle.walls,  # WHY: wall segments for the map background.
        "wall_count": len(bundle.walls),  # WHY: sidebar count.
        "wayfinding": bundle.wayfinding,  # WHY: wayfinding graph edges.
        "wayfinding_count": len(bundle.wayfinding),  # WHY: sidebar count.
    }


def _coverage_section(bundle: MapLayers) -> dict[str, Any]:
    """Return the coverage-heat-map sub-dict for the response."""
    return {  # WHY: caller merges this section into the top-level response dict.
        "wifi_coverage": bundle.wifi_cov,  # WHY: WiFi coverage heat map.
        "ble_coverage": bundle.ble_cov,  # WHY: BLE coverage heat map.
        "app_coverage": bundle.app_cov,  # WHY: SDK-app coverage heat map.
    }
