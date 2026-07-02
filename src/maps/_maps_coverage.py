"""Map fetch / coverage / payload cluster (extracted from MapsManager).

Split out of ``src/maps/maps_manager.py`` so the ~338 LOC layer-fetch
flow lives in its own module. The extracted methods stay as methods of
a small wrapper class :class:`_MapsCoverage`; ``__getattr__`` delegates
lookups that miss on the wrapper to the wrapped MapsManager, so calls
to ``self._resolve_site_name``, ``self._extract_walls``, and
``self._extract_wayfinding`` (which still live on MapsManager) resolve
without rewrites.

MapsManager keeps slim delegating wrappers for ``_collect_map_payload``
and ``_build_map_data_response`` because ``launch_viewer_standalone``
passes them as bound-method callables to ``launch_flask_viewer``.
"""

from __future__ import annotations

import logging
from typing import Any

import mistapi  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class _MapsCoverage:
    """Wrapper class holding the extracted fetch/coverage/payload methods."""

    def __init__(self, maps_manager: Any) -> None:
        self._mm = maps_manager

    def __getattr__(self, name: str) -> Any:
        mm = self.__dict__.get("_mm")
        if mm is None:  # pragma: no cover - only during broken init
            raise AttributeError(name)
        return getattr(mm, name)

    @staticmethod
    def _map_device_record(device: dict) -> dict:
        """Project a Mist device-stats record down to the viewer's display fields."""
        return {
            "x": device.get("x"),
            "y": device.get("y"),
            "name": device.get("name", device.get("mac", "Unknown")),
            "type": device.get("type", "ap"),
            "status": device.get("status", "unknown"),
            "mac": device.get("mac", ""),
            "orientation": device.get("orientation", 0),
        }

    def _fetch_map_devices(self, api_session, site_id: str, map_id: str) -> list[dict]:
        """Fetch site devices and return only those located on this map."""
        try:
            response = mistapi.api.v1.sites.stats.listSiteDevicesStats(
                api_session, site_id=site_id, type="all", limit=1000
            )
            if response.status_code != 200 or not response.data:
                return []
            return [
                self._map_device_record(d)
                for d in response.data
                if d.get("map_id") == map_id and d.get("x") is not None
            ]
        except Exception as e:
            logging.warning("Error fetching devices: %s", e)
            return []

    def _fetch_map_zones(self, api_session, site_id: str, map_id: str) -> list[dict]:
        """Fetch zones for this site and filter to those bound to the requested map."""
        try:
            response = mistapi.api.v1.sites.zones.listSiteZones(api_session, site_id=site_id)
            if response.status_code != 200 or not response.data:
                return []
            return [
                {"name": z.get("name", "Zone"), "vertices": z.get("vertices", [])}
                for z in response.data
                if z.get("map_id") == map_id
            ]
        except Exception as e:
            logging.warning("Error fetching zones: %s", e)
            return []

    @staticmethod
    def _map_wifi_client_record(client: dict) -> dict:
        """Project a wireless-client stats record down to the viewer's display fields."""
        return {
            "x": client.get("x"),
            "y": client.get("y"),
            "mac": client.get("mac", "Unknown"),
            "ssid": client.get("ssid", "-"),
            "name": client.get("hostname", "") or client.get("name", ""),
        }

    def _fetch_map_wifi_clients(self, api_session, site_id: str, map_id: str) -> list[dict]:
        """Fetch connected WiFi clients on this map."""
        try:
            response = mistapi.api.v1.sites.stats.listSiteWirelessClientsStats(api_session, site_id=site_id)
            if response.status_code != 200 or not response.data:
                return []
            return [
                self._map_wifi_client_record(c)
                for c in response.data
                if c.get("map_id") == map_id and c.get("x") is not None
            ]
        except Exception as e:
            logging.warning("Error fetching WiFi clients: %s: %s", type(e).__name__, str(e))
            return []

    def _fetch_map_unconnected_clients(self, api_session, site_id: str, map_id: str) -> list[dict]:
        """Fetch unconnected WiFi client stats for this map."""
        try:
            response = mistapi.api.v1.sites.stats.listSiteUnconnectedClientStats(
                api_session, site_id=site_id, map_id=map_id
            )
            if response.status_code != 200 or not response.data:
                return []
            return [
                {
                    "x": c.get("x"),
                    "y": c.get("y"),
                    "mac": c.get("mac", "Unknown"),
                    "manufacture": c.get("manufacture", "-"),
                }
                for c in response.data
                if c.get("x") is not None
            ]
        except Exception as e:
            logging.warning("Error fetching unconnected clients: %s: %s", type(e).__name__, str(e))
            return []

    def _fetch_map_ble_devices(self, api_session, site_id: str, map_id: str) -> list[dict]:
        """Fetch BLE-discovered assets bound to this map."""
        try:
            response = mistapi.api.v1.sites.stats.listSiteDiscoveredAssets(api_session, site_id=site_id)
            if response.status_code != 200 or not response.data:
                return []
            return [
                {"x": d.get("x"), "y": d.get("y"), "mac": d.get("mac", "Unknown")}
                for d in response.data
                if d.get("map_id") == map_id and d.get("x") is not None
            ]
        except Exception as e:
            logging.warning("Error fetching BLE devices: %s", e)
            return []

    def _fetch_map_assets(self, api_session, site_id: str, map_id: str) -> list[dict]:
        """Fetch named assets bound to this map."""
        try:
            response = mistapi.api.v1.sites.stats.listSiteAssetsStats(api_session, site_id=site_id)
            if response.status_code != 200 or not response.data:
                return []
            return [
                {
                    "x": a.get("x"),
                    "y": a.get("y"),
                    "name": a.get("name", "Asset"),
                    "mac": a.get("mac", "-"),
                }
                for a in response.data
                if a.get("map_id") == map_id and a.get("x") is not None
            ]
        except Exception as e:
            logging.warning("Error fetching assets: %s: %s", type(e).__name__, str(e))
            return []

    def _fetch_map_sdk_clients(self, api_session, site_id: str, map_id: str) -> list[dict]:
        """Fetch SDK/Marvis indoor-location clients for this map."""
        try:
            response = mistapi.api.v1.sites.stats.getSiteSdkStatsByMap(api_session, site_id=site_id, map_id=map_id)
            if response.status_code != 200 or not response.data:
                return []
            return [
                {
                    "x": c.get("x"),
                    "y": c.get("y"),
                    "name": c.get("name", ""),
                    "uuid": c.get("uuid", "-"),
                }
                for c in response.data
                if c.get("x") is not None
            ]
        except Exception as e:
            logging.warning("Error fetching SDK clients: %s", e)
            return []

    @staticmethod
    def _resolve_coverage_indices(result_def: list[str]) -> tuple[int, int, int]:
        """Return (x_idx, y_idx, rssi_idx) into a coverage row, with a -1 RSSI sentinel."""
        try:
            x_idx = result_def.index("x")
            y_idx = result_def.index("y")
            if "max_rssi" in result_def:
                rssi_idx = result_def.index("max_rssi")
            elif "avg_rssi" in result_def:
                rssi_idx = result_def.index("avg_rssi")
            else:
                rssi_idx = -1
            return x_idx, y_idx, rssi_idx
        except ValueError:
            return 0, 1, 4

    @staticmethod
    def _coverage_row_to_point(item: list, indices: tuple[int, int, int], ppm_value: float) -> dict | None:
        """Convert a coverage result row to a {x, y, rssi} point in pixel space."""
        x_idx, y_idx, rssi_idx = indices
        if len(item) <= max(x_idx, y_idx, rssi_idx):
            return None
        x_m = item[x_idx]
        y_m = item[y_idx]
        rssi = item[rssi_idx] if rssi_idx >= 0 else -80
        if x_m is None or y_m is None or rssi is None:
            return None
        return {"x": x_m * ppm_value, "y": y_m * ppm_value, "rssi": rssi}

    def _fetch_coverage_layer(
        self,
        api_session,
        site_id: str,
        map_id: str,
        coverage_type: str,
        ppm_value: float,
    ) -> list[dict] | None:
        """Fetch one coverage layer (client/asset/sdkclient) and convert meters to pixels."""
        try:
            coverage_url = f"/api/v1/sites/{site_id}/location/coverage"
            params = {
                "resolution": "fine",
                "duration": "1d",
                "map_id": map_id,
                "type": coverage_type,
                "from_apollo": "true",
            }
            logging.info("[Flask API] Fetching %s coverage for map %s", coverage_type, map_id)
            response = api_session.mist_get(coverage_url, query=params)
            if response.status_code != 200:
                return None
            return self._coverage_response_to_grid(response.data, ppm_value, coverage_type)
        except Exception as e:
            logging.warning("Error fetching %s coverage: %s", coverage_type, e)
            return None

    def _coverage_response_to_grid(self, coverage_data, ppm_value: float, coverage_type: str) -> list[dict] | None:
        """Parse a coverage API payload into a list of grid points, or None on error."""
        if isinstance(coverage_data, dict) and "exception" in coverage_data:
            logging.warning("[Flask API] %s coverage API error", coverage_type)
            return None
        results = coverage_data.get("results", [])
        result_def = coverage_data.get("result_def", [])
        if not (results and result_def):
            return None
        indices = self._resolve_coverage_indices(result_def)
        grid_points = [
            point
            for point in (self._coverage_row_to_point(r, indices, ppm_value) for r in results)
            if point is not None
        ]
        logging.info(
            "[Flask API] %s coverage: %s grid points (ppm=%s)",
            coverage_type,
            len(grid_points),
            ppm_value,
        )
        return grid_points

    def _fetch_all_coverage(self, api_session, site_id: str, map_id: str, ppm: float) -> tuple[list, list, list]:
        """Fetch WiFi + BLE + App coverage layers (each one is None-safe)."""
        if not ppm:
            return [], [], []
        wifi = self._fetch_coverage_layer(api_session, site_id, map_id, "client", ppm) or []
        ble = self._fetch_coverage_layer(api_session, site_id, map_id, "asset", ppm) or []
        app = self._fetch_coverage_layer(api_session, site_id, map_id, "sdkclient", ppm) or []
        return wifi, ble, app

    @staticmethod
    def _count_devices_by_type(devices: list[dict]) -> tuple[int, int, int]:
        """Return (ap_count, switch_count, gateway_count) by walking the device list once."""
        ap_count = sum(1 for d in devices if d.get("type") == "ap" or not d.get("type"))
        switch_count = sum(1 for d in devices if d.get("type") == "switch")
        gateway_count = sum(1 for d in devices if d.get("type") == "gateway")
        return ap_count, switch_count, gateway_count

    def _collect_map_payload(
        self, api_session, all_sites: list[dict], site_id: str, map_id: str
    ) -> tuple[dict | None, tuple]:
        """Gather every layer needed to render this map.

        Returns ``(map_data, layers_tuple)`` or ``(None, ())`` on missing map.
        """
        site_name = self._resolve_site_name(all_sites, site_id)
        map_response = mistapi.api.v1.sites.maps.getSiteMap(api_session, site_id=site_id, map_id=map_id)
        if map_response.status_code != 200:
            return None, ()
        map_data = map_response.data
        ppm = map_data.get("ppm", 1.0)
        walls = self._extract_walls(map_data)
        wayfinding = self._extract_wayfinding(map_data)
        devices = self._fetch_map_devices(api_session, site_id, map_id)
        zones = self._fetch_map_zones(api_session, site_id, map_id)
        wifi_clients = self._fetch_map_wifi_clients(api_session, site_id, map_id)
        unconnected = self._fetch_map_unconnected_clients(api_session, site_id, map_id)
        ble_devices = self._fetch_map_ble_devices(api_session, site_id, map_id)
        assets = self._fetch_map_assets(api_session, site_id, map_id)
        sdk_clients = self._fetch_map_sdk_clients(api_session, site_id, map_id)
        wifi_cov, ble_cov, app_cov = self._fetch_all_coverage(api_session, site_id, map_id, ppm)
        layers = (
            site_name,
            walls,
            wayfinding,
            devices,
            zones,
            wifi_clients,
            unconnected,
            ble_devices,
            assets,
            sdk_clients,
            wifi_cov,
            ble_cov,
            app_cov,
        )
        return map_data, layers

    def _build_map_data_response(self, site_id: str, map_id: str, map_data: dict, layers: tuple) -> dict:
        """Assemble the final JSON dict returned by the /api/map endpoint."""
        (
            site_name,
            walls,
            wayfinding,
            devices,
            zones,
            wifi_clients,
            unconnected,
            ble_devices,
            assets,
            sdk_clients,
            wifi_cov,
            ble_cov,
            app_cov,
        ) = layers
        ap_count, switch_count, gateway_count = self._count_devices_by_type(devices)
        original_url = map_data.get("url", "")
        image_url = f"/api/map-image/{site_id}/{map_id}" if original_url else ""
        return {
            "site_id": site_id,
            "site_name": site_name,
            "map_id": map_id,
            "map_name": map_data.get("name", "Unnamed"),
            "width": map_data.get("width", 1000),
            "height": map_data.get("height", 1000),
            "image_url": image_url,
            "ppm": map_data.get("ppm", 1.0),
            "devices": devices,
            "device_count": len(devices),
            "ap_count": ap_count,
            "switch_count": switch_count,
            "gateway_count": gateway_count,
            "zones": zones,
            "zone_count": len(zones),
            "wifi_clients": wifi_clients,
            "wifi_client_count": len(wifi_clients),
            "unconnected_clients": unconnected,
            "unconnected_client_count": len(unconnected),
            "ble_devices": ble_devices,
            "ble_device_count": len(ble_devices),
            "assets": assets,
            "asset_count": len(assets),
            "sdk_clients": sdk_clients,
            "sdk_client_count": len(sdk_clients),
            "walls": walls,
            "wall_count": len(walls),
            "wayfinding": wayfinding,
            "wayfinding_count": len(wayfinding),
            "wifi_coverage": wifi_cov,
            "ble_coverage": ble_cov,
            "app_coverage": app_cov,
        }


def collect_map_payload(maps_manager: Any, api_session, all_sites: list, site_id: str, map_id: str):
    """Entry point mirroring MapsManager._collect_map_payload."""
    return _MapsCoverage(maps_manager)._collect_map_payload(api_session, all_sites, site_id, map_id)


def build_map_data_response(maps_manager: Any, site_id: str, map_id: str, map_data: dict, layers: tuple) -> dict:
    """Entry point mirroring MapsManager._build_map_data_response."""
    return _MapsCoverage(maps_manager)._build_map_data_response(site_id, map_id, map_data, layers)
