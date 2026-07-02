"""Map geometry backup cluster (extracted from MapsManager).

Split out of ``src/maps/maps_manager.py`` so the ~223 LOC backup flow
lives in its own module. The extracted methods stay as methods of a
small wrapper class :class:`_MapsBackup`; ``__getattr__`` delegates
lookups that miss on the wrapper to the wrapped MapsManager, so
``self.apisession`` and other shared state work without rewrites.

MapsManager keeps a slim ``_backup_map_geometry`` delegating method
because ``src/maps/launcher/viewer_callbacks.py`` invokes it through
``maps_manager_ref._backup_map_geometry(...)`` and tests stub it on
the MapsManager class.
"""

from __future__ import annotations

import logging
from typing import Any

import mistapi  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class _MapsBackup:
    """Wrapper class holding the extracted backup methods."""

    def __init__(self, maps_manager: Any) -> None:
        self._mm = maps_manager

    def __getattr__(self, name: str) -> Any:
        mm = self.__dict__.get("_mm")
        if mm is None:  # pragma: no cover - only during broken init
            raise AttributeError(name)
        return getattr(mm, name)

    def _backup_download_image(self, map_data, map_name, backup_reason):
        """Download map image for backup. Returns (filename, content) or (None, None)."""
        from datetime import datetime

        import requests

        image_url = map_data.get("url")
        if not image_url:
            return None, None

        try:
            file_ext = ".png"
            if "." in image_url:
                url_ext = image_url.rsplit(".", 1)[-1].split("?")[0].lower()
                if url_ext in ["png", "jpg", "jpeg", "gif", "svg", "webp"]:
                    file_ext = f".{url_ext}"

            safe_map_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in map_name)
            safe_map_name = safe_map_name.strip().replace(" ", "_")[:50]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"map_backup_{safe_map_name}_{backup_reason}_{timestamp}{file_ext}"

            data_dir = os.path.join(os.getcwd(), "data")
            os.makedirs(data_dir, exist_ok=True)

            response = requests.get(image_url, timeout=60)
            if response.status_code == 200:
                image_path = os.path.join(data_dir, image_filename)
                with open(image_path, "wb") as img_file:
                    img_file.write(response.content)
                image_size_kb = len(response.content) / 1024
                logging.info("Map image backed up: %s (%.1f KB)", image_filename, image_size_kb)
                return image_filename, (safe_map_name, timestamp)
            logging.warning("Could not download map image: HTTP %s", response.status_code)
        except Exception as img_err:
            logging.warning("Image backup failed: %s", img_err)
        return None, None

    def _backup_fetch_items(self, api_session, site_id, map_id, api_call, item_name):
        """Fetch items from API and filter to map. Returns list of matching items."""
        try:
            response = api_call(api_session, site_id=site_id)
            if response.status_code == 200:
                all_items = response.data if isinstance(response.data, list) else []
                map_items = [item for item in all_items if item.get("map_id") == map_id]
                logging.debug("Backup includes %s %s for map %s", len(map_items), item_name, map_id)
                return map_items
            logging.warning("Could not fetch %s for backup: HTTP %s", item_name, response.status_code)
        except Exception as err:
            logging.debug("%s backup skipped: %s", item_name, err)
        return []

    def _backup_fetch_device_placements(self, api_session, site_id, map_id):
        """Fetch device placements on a specific map."""
        try:
            devices_response = mistapi.api.v1.sites.devices.listSiteDevices(api_session, site_id=site_id, type="all")
            if devices_response.status_code == 200:
                all_devices = devices_response.data if isinstance(devices_response.data, list) else []
                placements = []
                for device in all_devices:
                    if device.get("map_id") == map_id and ("x" in device or "y" in device):
                        placements.append(
                            {
                                "id": device.get("id"),
                                "name": device.get("name"),
                                "mac": device.get("mac"),
                                "type": device.get("type"),
                                "model": device.get("model"),
                                "map_id": device.get("map_id"),
                                "x": device.get("x"),
                                "y": device.get("y"),
                                "orientation": device.get("orientation"),
                                "height": device.get("height"),
                            }
                        )
                logging.debug("Backup includes %s device placements for map %s", len(placements), map_id)
                return placements
            logging.warning("Could not fetch devices for backup: HTTP %s", devices_response.status_code)
        except Exception as device_err:
            logging.warning("Device placement backup failed: %s", device_err)
        return []

    def _backup_write_file(self, geometry_backup, map_name, backup_reason, name_timestamp=None):
        """Write backup data to JSON file. Returns file path."""
        import json
        from datetime import datetime

        if name_timestamp:
            safe_map_name, timestamp = name_timestamp
        else:
            safe_map_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in map_name)
            safe_map_name = safe_map_name.strip().replace(" ", "_")[:50]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_filename = f"map_backup_{safe_map_name}_{backup_reason}_{timestamp}.json"
        data_dir = os.path.join(os.getcwd(), "data")
        os.makedirs(data_dir, exist_ok=True)
        backup_path = os.path.join(data_dir, backup_filename)

        with open(backup_path, "w", encoding="utf-8") as backup_file:
            json.dump(geometry_backup, backup_file, indent=2, ensure_ascii=False)
        return backup_path, backup_filename

    def _count_geometry_path_nodes(self, geometry_backup: dict, path_key: str) -> "int | None":
        """Count nodes in a geometry path. Returns count or None if empty."""
        geometry = geometry_backup.get("geometry") or {}
        nodes = geometry.get(path_key, {}).get("nodes", [])
        count = len(nodes)
        return count if count > 0 else None

    def _count_backup_list(self, geometry_backup: dict, key: str) -> "int | None":
        """Count items in a top-level backup list. Returns count or None if empty."""
        count = len(geometry_backup.get(key, []))
        return count if count > 0 else None

    def _backup_print_summary(self, backup_filename, image_filename, geometry_backup):
        """Print backup summary to console."""
        counts = [
            ("Image", "Yes" if image_filename else None),
            ("Walls", self._count_geometry_path_nodes(geometry_backup, "wall_path")),
            ("Wayfinding", self._count_geometry_path_nodes(geometry_backup, "wayfinding_path")),
            ("Zones", self._count_backup_list(geometry_backup, "zones")),
            ("Devices", self._count_backup_list(geometry_backup, "device_placements")),
            ("Beacons", self._count_backup_list(geometry_backup, "beacons")),
            ("VBeacons", self._count_backup_list(geometry_backup, "vbeacons")),
        ]
        summary = ", ".join(f"{k}: {v}" for k, v in counts if v) or "Empty map"
        logging.info("Map backup saved: %s (%s)", backup_filename, summary)
        print(f"\n   [*] Map backup saved: {backup_filename}")
        if image_filename:
            print(f"       Image: {image_filename}")
        print(f"       {summary}")

    def _backup_map_geometry(self, api_session, site_id, map_id, map_name, backup_reason="manual"):
        """Backup map geometry data (walls, zones, wayfinding paths) to JSON file.

        Called automatically before destructive operations (delete) and during cloning
        to preserve geometry data that would otherwise be lost.

        Returns:
            str: Path to backup file if successful, None if failed.
        """
        from datetime import datetime

        try:
            logging.info("Map geometry backup initiated - map: %s (%s), reason: %s", map_name, map_id, backup_reason)

            map_response = mistapi.api.v1.sites.maps.getSiteMap(api_session, site_id=site_id, map_id=map_id)
            if map_response.status_code != 200:
                logging.error("Map backup failed: Could not fetch map data - HTTP %s", map_response.status_code)
                return None

            map_data = map_response.data

            geometry_backup = {
                "backup_info": {
                    "timestamp": datetime.now().isoformat(),
                    "reason": backup_reason,
                    "map_id": map_id,
                    "map_name": map_name,
                    "site_id": site_id,
                },
                "map_properties": {
                    key: map_data.get(key)
                    for key in [
                        "name",
                        "type",
                        "width",
                        "height",
                        "width_m",
                        "height_m",
                        "ppm",
                        "orientation",
                        "origin_x",
                        "origin_y",
                        "latlng",
                        "latlng_tl",
                        "latlng_br",
                        "locked",
                        "view",
                        "occupancy_limit",
                        "flags",
                        "url",
                        "thumbnail_url",
                    ]
                },
                "geometry": {
                    "wall_path": map_data.get("wall_path"),
                    "wayfinding_path": map_data.get("wayfinding_path"),
                    "wayfinding": map_data.get("wayfinding"),
                    "sitesurvey_path": map_data.get("sitesurvey_path"),
                },
            }

            # Download image
            image_filename, name_timestamp = self._backup_download_image(map_data, map_name, backup_reason)
            if image_filename:
                geometry_backup["backup_info"]["image_file"] = image_filename

            # Fetch related entities
            geometry_backup["device_placements"] = self._backup_fetch_device_placements(api_session, site_id, map_id)
            geometry_backup["zones"] = self._backup_fetch_items(
                api_session, site_id, map_id, mistapi.api.v1.sites.zones.listSiteZones, "zones"
            )
            geometry_backup["beacons"] = self._backup_fetch_items(
                api_session, site_id, map_id, mistapi.api.v1.sites.beacons.listSiteBeacons, "beacons"
            )
            geometry_backup["vbeacons"] = self._backup_fetch_items(
                api_session, site_id, map_id, mistapi.api.v1.sites.vbeacons.listSiteVBeacons, "vbeacons"
            )

            # Write and summarize
            backup_path, backup_filename = self._backup_write_file(
                geometry_backup, map_name, backup_reason, name_timestamp
            )
            self._backup_print_summary(backup_filename, image_filename, geometry_backup)

            return backup_path

        except Exception as backup_error:
            logging.exception("Map geometry backup failed: %s", backup_error)
            print(f"\n   [!] Warning: Could not backup map geometry: {backup_error}")
            return None


def backup_map_geometry(
    maps_manager: Any,
    api_session,
    site_id,
    map_id,
    map_name,
    backup_reason: str = "manual",
):
    """Entry point mirroring MapsManager._backup_map_geometry.

    Kept as a module-level factory so callers can invoke the backup
    without instantiating :class:`_MapsBackup` directly.
    """
    return _MapsBackup(maps_manager)._backup_map_geometry(
        api_session, site_id, map_id, map_name, backup_reason
    )
