"""Map clone cluster (extracted from MapsManager).

Split out of ``src/maps/maps_manager.py`` so the ~288 LOC map-clone
flow lives in its own module. The extracted methods stay as methods
of a small wrapper class :class:`_MapsClone`; ``__getattr__``
delegates lookups that miss on the wrapper to the wrapped MapsManager,
so ``self.apisession`` and other shared state work without rewrites.

MapsManager keeps a slim ``clone_map`` delegating method because the
menu-dispatch table in ``_build_menu_dispatch`` references
``self.clone_map`` and existing tests stub it on the MapsManager class.
"""

from __future__ import annotations

import logging
from typing import Any

import mistapi  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class _MapsClone:
    """Wrapper class holding the extracted clone methods."""

    def __init__(self, maps_manager: Any) -> None:
        self._mm = maps_manager

    def __getattr__(self, name: str) -> Any:
        mm = self.__dict__.get("_mm")
        if mm is None:  # pragma: no cover - only during broken init
            raise AttributeError(name)
        return getattr(mm, name)

    def _fetch_source_map_with_display(self, site_id: str, source_map_id: str) -> dict | None:
        """Fetch source map from API and display its key attributes; return None on failure."""
        logging.debug("Calling getSiteMap API - site_id: %s, map_id: %s", site_id, source_map_id)
        print("\nFetching source map details...")
        response = mistapi.api.v1.sites.maps.getSiteMap(self.apisession, site_id=site_id, map_id=source_map_id)
        if response.status_code != 200:
            logging.error("Failed to fetch source map - HTTP %s", response.status_code)
            print(f"\n! Failed to fetch source map: HTTP {response.status_code}")
            return None
        source_map = response.data
        print(f"\n{'-' * 80}")
        print(f"Source Map: {source_map.get('name', 'Unnamed')}")
        print(f"Type: {source_map.get('type', 'N/A')}")
        print(f"Dimensions: {source_map.get('width', 'N/A')}x{source_map.get('height', 'N/A')}")
        print(f"PPM: {source_map.get('ppm', 'N/A')}")
        print(f"Has Image: {'Yes' if 'url' in source_map else 'No'}")
        print(f"Has Walls: {'Yes' if 'wall_path' in source_map else 'No'}")
        print(f"Has Wayfinding: {'Yes' if 'wayfinding_path' in source_map else 'No'}")
        print(f"{'-' * 80}")
        return source_map

    def _prompt_clone_name(self, source_map: dict) -> str | None:
        """Prompt for a clone name using the source map name as default; return None on EOF."""
        default_name = f"{source_map.get('name', 'Map')} (Copy)"
        try:
            new_name = InputUtils.safe_input(
                f"\nEnter name for cloned map [{default_name}]: ", context="_prompt_clone_name"
            ).strip()
        except EOFError:
            logging.info("EOF detected during clone name prompt")
            return None
        return new_name or default_name

    def _build_clone_payload(self, source_map: dict, new_name: str) -> dict:
        """Build a clone payload dict by copying all cloneable fields from the source map."""
        payload: dict[str, Any] = {"name": new_name, "type": source_map.get("type", "image")}
        cloneable_fields = [
            "width",
            "height",
            "height_m",
            "ppm",
            "orientation",
            "latlng",
            "latlng_br",
            "origin_x",
            "origin_y",
            "wayfinding",
            "wayfinding_path",
            "wall_path",
            "sitesurvey_path",
            "occupancy_limit",
            "locked",
            "view",
        ]
        for field in cloneable_fields:
            if field in source_map:
                payload[field] = source_map[field]
        return payload

    def _fetch_source_zone_count(self, site_id: str, source_map_id: str) -> int:
        """Count zones belonging to the source map; return 0 if fetch fails."""
        try:
            zones_check = mistapi.api.v1.sites.zones.listSiteZones(self.apisession, site_id=site_id)
            if zones_check.status_code == 200:
                return len([z for z in zones_check.data if z.get("map_id") == source_map_id])
        except Exception as zone_error:
            logging.debug("Could not fetch zone count for clone plan: %s", zone_error)
        return 0

    def _confirm_clone(self, source_map: dict, new_name: str, source_zones_count: int, clone_payload: dict) -> bool:
        """Display the clone plan and prompt user to confirm; return True to proceed."""
        print(f"\n{'-' * 80}")
        print("Clone Plan:")
        print(f"  New name: {new_name}")
        print("  Will copy: dimensions, orientation, location data, wayfinding, walls")
        print(f"  Image: {'Yes - will download and re-upload' if 'url' in source_map else 'No image to copy'}")
        zone_msg = (
            f"  Zones: {source_zones_count} zone(s) will be cloned"
            if source_zones_count > 0
            else "  Zones: None found on source map"
        )
        print(zone_msg)
        print(f"{'-' * 80}")
        confirm = (
            InputUtils.safe_input("\nProceed with full clone? (yes/no): ", context="_confirm_clone").strip().lower()
        )
        if confirm not in ["yes", "y"]:
            print("\n! Clone cancelled")
            return False
        return True

    def _download_clone_image(self, source_map: dict) -> str | None:
        """Download the source map image to a temp file; return the temp path or None."""
        import tempfile

        if "url" not in source_map:
            return None
        image_temp_path = None
        try:
            print("\nDownloading map image...")
            image_url = source_map["url"]
            file_ext = self._determine_image_extension(image_url)
            temp_fd, image_temp_path = tempfile.mkstemp(suffix=file_ext)
            os.close(temp_fd)
            response = requests.get(image_url, timeout=60)
            if response.status_code == 200:
                with open(image_temp_path, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded image ({len(response.content) / 1024:.1f} KB)")
                return image_temp_path
            print(f"! Warning: Failed to download image (HTTP {response.status_code})")
        except Exception as download_error:
            logging.error("Error downloading map image: %s", download_error)
            print(f"! Warning: Could not download image: {download_error}")
        if image_temp_path and os.path.exists(image_temp_path):
            os.remove(image_temp_path)
        return None

    def _create_cloned_map_entry(self, site_id: str, clone_payload: dict, image_temp_path: str | None) -> str | None:
        """Call createSiteMap API and return the new map ID; cleans up temp on failure."""
        print("\nCreating cloned map...")
        clone_response = mistapi.api.v1.sites.maps.createSiteMap(self.apisession, site_id=site_id, body=clone_payload)
        if clone_response.status_code not in [200, 201]:
            print(f"\n! Failed to clone map: HTTP {clone_response.status_code}")
            logging.error("Map clone failed: %s - %s", clone_response.status_code, clone_response.data)
            if image_temp_path and os.path.exists(image_temp_path):
                os.remove(image_temp_path)
            return None
        cloned_map = clone_response.data
        cloned_map_id = cloned_map.get("id")
        if not cloned_map_id:
            print("\n! Error: Cloned map has no ID")
            logging.error("Cloned map missing ID in response")
            return None
        print(f"\n{'-' * 80}")
        print("Map structure cloned successfully!")
        print(f"Cloned Map ID: {cloned_map_id}")
        print(f"Name: {cloned_map.get('name')}")
        print(f"{'-' * 80}")
        return cloned_map_id

    def _upload_clone_image(self, site_id: str, cloned_map_id: str, image_temp_path: str) -> None:
        """Upload image from temp path to cloned map and clean up the temp file."""
        try:
            print("\nUploading image to cloned map...")
            upload_response = mistapi.api.v1.sites.maps.addSiteMapImageFile(  # type: ignore[union-attr]
                self.apisession, site_id=site_id, map_id=str(cloned_map_id), file=image_temp_path
            )
            if upload_response.status_code in [200, 201]:
                print("Image uploaded successfully!")
                logging.info("Image uploaded to cloned map %s", cloned_map_id)
            else:
                print(f"! Warning: Failed to upload image: HTTP {upload_response.status_code}")
                logging.error("Image upload to cloned map failed: %s", upload_response.status_code)
        except Exception as upload_error:
            logging.error("Error uploading image to cloned map: %s", upload_error)
            print(f"! Warning: Could not upload image to cloned map: {upload_error}")
        finally:
            if os.path.exists(image_temp_path):
                os.remove(image_temp_path)

    def _clone_single_zone(self, site_id: str, cloned_map_id: str, zone: dict) -> bool:
        """Clone a single zone to the new map; return True on success."""
        try:
            zone_payload: dict[str, Any] = {
                "name": zone.get("name", "Unnamed Zone"),
                "map_id": cloned_map_id,
                "vertices": zone.get("vertices", []),
            }
            if "type" in zone:
                zone_payload["type"] = zone["type"]
            if "z" in zone:
                zone_payload["z"] = zone["z"]
            zone_response = mistapi.api.v1.sites.zones.createSiteZone(
                self.apisession, site_id=site_id, body=zone_payload
            )
            if zone_response.status_code in [200, 201]:
                logging.debug("Cloned zone '%s' to new map", zone.get("name"))
                return True
            logging.warning("Failed to clone zone '%s': HTTP %s", zone.get("name"), zone_response.status_code)
        except Exception as zone_error:
            logging.error("Error cloning zone '%s': %s", zone.get("name"), zone_error)
        return False

    def _clone_zones(self, site_id: str, source_map_id: str, cloned_map_id: str) -> tuple[int, int]:
        """Clone all zones from source map to cloned map; return (cloned, failed)."""
        print("\nCloning zones...")
        try:
            zones_response = mistapi.api.v1.sites.zones.listSiteZones(self.apisession, site_id=site_id)
            if zones_response.status_code != 200:
                print("! Warning: Could not fetch zones for cloning")
                return 0, 0
            source_zones = [z for z in zones_response.data if z.get("map_id") == source_map_id]
            if not source_zones:
                print("No zones found on source map to clone")
                return 0, 0
            results = [self._clone_single_zone(site_id, cloned_map_id, zone) for zone in source_zones]
            cloned = sum(results)
            failed = len(results) - cloned
            print(f"Zones cloned: {cloned} (failed: {failed})")
            return cloned, failed
        except Exception as zones_error:
            logging.exception("Error during zone cloning: %s", zones_error)
            print(f"! Warning: Zone cloning failed: {zones_error}")
            return 0, 0

    def _print_clone_summary(self, summary: MapCloneSummary, zone_result: ZoneCloneResult) -> None:
        """Print the final clone completion summary."""
        source_map = summary.source_map  # Unpack original-map record from the bundle.
        new_name = summary.new_name  # Unpack the user-chosen clone name from the bundle.
        cloned_map_id = summary.cloned_map_id  # Unpack the new map's UUID from the bundle.
        clone_payload = summary.clone_payload  # Unpack the body posted to Mist from the bundle.
        had_image = summary.had_image  # Unpack the image-uploaded flag from the bundle.
        zones_cloned = zone_result.cloned  # Unpack successful-zone count for the summary line.
        zones_failed = zone_result.failed  # Unpack failed-zone count for the summary line.
        print(f"\n{'-' * 80}")
        print("CLONE COMPLETE")
        print(f"{'-' * 80}")
        print(f"Original Map: {source_map.get('name')}")
        print(f"Cloned Map: {new_name}")
        print(f"Cloned Map ID: {cloned_map_id}")
        print("\nCloned elements:")
        print(f"  -> Dimensions: {clone_payload.get('width', 'N/A')}x{clone_payload.get('height', 'N/A')}")
        print(f"  -> PPM: {clone_payload.get('ppm', 'N/A')}")
        print(f"  -> Walls: {'Yes' if 'wall_path' in clone_payload else 'No'}")
        print(f"  -> Wayfinding: {'Yes' if 'wayfinding_path' in clone_payload else 'No'}")
        print(f"  -> Image: {'Yes' if had_image else 'No'}")
        zone_text = f"{zones_cloned} cloned" + (f" ({zones_failed} failed)" if zones_failed > 0 else "")
        print(f"  -> Zones: {zone_text}")
        print(f"{'-' * 80}")

    def clone_map(self):
        """Clone/duplicate an existing map at the current site including image, walls, paths, and zones."""
        logging.info("clone_map operation initiated")
        print("\n" + "-" * 80)
        print("CLONE/DUPLICATE MAP")
        print("-" * 80)
        print("! This will clone ALL map data: image, walls, paths, zones, wayfinding, etc.")
        site_id, site_name = self.get_current_site()
        if not site_id:
            logging.warning("clone_map aborted: No site selected")
            return
        logging.debug("clone_map - Site: %s (ID: %s)", site_name, site_id)
        try:
            print("\nSelect the map to clone:")
            source_map_id = self._select_map_from_site(site_id, site_name)
            if not source_map_id:
                logging.info("clone_map aborted: No source map selected")
                return
            source_map = self._fetch_source_map_with_display(site_id, source_map_id)
            if source_map is None:
                return
            new_name = self._prompt_clone_name(source_map)
            if not new_name:
                return
            clone_payload = self._build_clone_payload(source_map, new_name)
            source_zones_count = self._fetch_source_zone_count(site_id, source_map_id)
            if not self._confirm_clone(source_map, new_name, source_zones_count, clone_payload):
                return
            image_temp_path = self._download_clone_image(source_map)
            cloned_map_id = self._create_cloned_map_entry(site_id, clone_payload, image_temp_path)
            if not cloned_map_id:
                return
            if image_temp_path:
                self._upload_clone_image(site_id, cloned_map_id, image_temp_path)
            zones_cloned, zones_failed = self._clone_zones(site_id, source_map_id, cloned_map_id)
            self._print_clone_summary(
                MapCloneSummary(
                    source_map=source_map,
                    new_name=new_name,
                    cloned_map_id=cloned_map_id,
                    clone_payload=clone_payload,
                    had_image=bool(image_temp_path),
                ),
                ZoneCloneResult(cloned=zones_cloned, failed=zones_failed),
            )
            logging.info(
                "Successfully cloned map %s to %s at site %s (zones: %s)",
                source_map_id,
                cloned_map_id,
                site_id,
                zones_cloned,
            )
        except EOFError:
            logging.info("EOF detected during map clone")
        except Exception as e:
            logging.exception("Error cloning map: %s", e)
            print(f"\n! Error cloning map: {e}")


def clone_map(maps_manager: Any):
    """Entry point mirroring MapsManager.clone_map.

    Kept as a module-level factory so callers can invoke the clone
    flow without instantiating :class:`_MapsClone` directly.
    """
    return _MapsClone(maps_manager).clone_map()
