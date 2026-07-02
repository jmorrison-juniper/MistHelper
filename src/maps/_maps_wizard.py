"""Intelligent map-replacement wizard (extracted from MapsManager).

Split out of ``src/maps/maps_manager.py`` so the ~600 LOC wizard flow
lives in its own module. The extracted methods stay as methods of a
small wrapper class :class:`_MapsWizard`; ``__getattr__`` delegates any
attribute the wizard does not define directly (``apisession``,
``_backup_map_geometry``, ``_select_map_from_site``, ``get_current_site``)
to the wrapped MapsManager, so the extraction diff stays tiny.

Callers use :func:`run_wizard`; MapsManager keeps a slim delegating
method so its menu-dispatch table still resolves ``self.intelligent_map_replacement_wizard``.
"""

from __future__ import annotations

import logging
from typing import Any

import mistapi  # type: ignore[import-untyped]

from src.dataclasses.map_scaling_deps import (
    MapDimensions,
    MapScalingFactors,
    OriginalMapMetrics,
    ScaleChoiceContext,
)
from src.dataclasses.map_wizard_deps import (
    MapWizardApplyContext,
    MapWizardApplyTarget,
    MapWizardPreviewContext,
    MapWizardSummaryContext,
)
from src.utils.input_utils import InputUtils

logger = logging.getLogger(__name__)


class _MapsWizard:
    """Wrapper class holding the extracted wizard methods.

    Attribute lookups that miss on this class delegate to the wrapped
    MapsManager via :meth:`__getattr__`. That covers ``apisession`` and
    the small set of MapsManager helpers the wizard calls through
    ``self.`` without touching the extracted method bodies.
    """

    def __init__(self, maps_manager: Any) -> None:
        self._mm = maps_manager

    def __getattr__(self, name: str) -> Any:
        mm = self.__dict__.get("_mm")
        if mm is None:  # pragma: no cover - only during broken init
            raise AttributeError(name)
        return getattr(mm, name)

    def _wizard_fetch_devices(self, site_id: str, map_id: str) -> list:
        """Fetch all devices placed on the given map."""
        try:
            resp = mistapi.api.v1.sites.devices.listSiteDevices(self.apisession, site_id=site_id, type="all")
            if resp.status_code == 200:
                all_devices = resp.data if isinstance(resp.data, list) else []
                return [d for d in all_devices if d.get("map_id") == map_id]
        except Exception as err:
            logging.debug("Could not fetch devices for wizard: %s", err)
        return []

    def _wizard_fetch_zones(self, site_id: str, map_id: str) -> list:
        """Fetch all zones placed on the given map."""
        try:
            resp = mistapi.api.v1.sites.zones.listSiteZones(self.apisession, site_id=site_id)
            if resp.status_code == 200:
                return [z for z in resp.data if z.get("map_id") == map_id]
        except Exception as err:
            logging.debug("Could not fetch zones for wizard: %s", err)
        return []

    def _wizard_fetch_beacons(self, site_id: str, map_id: str) -> tuple[list, list]:
        """Fetch BLE beacons and virtual beacons on the given map. Returns (beacons, vbeacons)."""
        beacons: list = []
        vbeacons: list = []
        try:
            b_resp = mistapi.api.v1.sites.beacons.listSiteBeacons(self.apisession, site_id=site_id)
            if b_resp.status_code == 200:
                beacons = [b for b in b_resp.data if b.get("map_id") == map_id]
            v_resp = mistapi.api.v1.sites.vbeacons.listSiteVBeacons(self.apisession, site_id=site_id)
            if v_resp.status_code == 200:
                vbeacons = [v for v in v_resp.data if v.get("map_id") == map_id]
        except Exception as err:
            logging.debug("Could not fetch beacons for wizard: %s", err)
        return beacons, vbeacons

    def _wizard_fetch_assets(self, site_id: str, map_id: str) -> dict:
        """Fetch all map assets: devices, zones, beacons, vbeacons.

        Returns dict with keys devices, zones, beacons, vbeacons (all lists).
        """
        beacons, vbeacons = self._wizard_fetch_beacons(site_id, map_id)
        return {
            "devices": self._wizard_fetch_devices(site_id, map_id),
            "zones": self._wizard_fetch_zones(site_id, map_id),
            "beacons": beacons,
            "vbeacons": vbeacons,
        }

    def _wizard_get_new_image(self) -> tuple[str, int, int] | None:
        """Prompt for the replacement image file path and return (path, width, height).

        Returns None if input is cancelled or invalid.
        """
        import os

        from PIL import Image

        print(f"\n{'-' * 80}")
        print("STEP 2: Select New Floor Plan Image")
        print("-" * 80)
        print("\nEnter the path to the new floor plan image:")
        print("Supported formats: PNG, JPG, JPEG, GIF")

        try:
            file_path = InputUtils.safe_input("File path: ", context="_wizard_get_new_image").strip()
        except EOFError:
            logging.info("EOF detected during file path input")
            return None

        file_path = file_path.strip('"').strip("'")

        if not file_path:
            print("\n! No file path provided")
            return None

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            print(f"\n! File not found or not a file: {file_path}")
            return None

        valid_extensions = [".png", ".jpg", ".jpeg", ".gif"]
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in valid_extensions:
            print(f"\n! Invalid file type: {file_ext}. Supported: {', '.join(valid_extensions)}")
            return None

        try:
            with Image.open(file_path) as img:
                new_width_px, new_height_px = img.size
                print(f"\nNew image dimensions: {new_width_px} x {new_height_px} pixels")
        except Exception as img_err:
            print(f"\n! Failed to read image dimensions: {img_err}")
            return None

        return file_path, new_width_px, new_height_px

    def _wizard_determine_scaling(
        self,
        original: OriginalMapMetrics,
        new_dimensions: tuple[int, int],
    ) -> tuple[str, float, float, float] | None:
        """Prompt user for scaling mode and return (scaling_mode, scale_x, scale_y, new_ppm).

        Returns None if the user cancels.
        """
        new_width_px, new_height_px = new_dimensions  # Unpack new image pixel size for clarity.
        print(f"\n{'-' * 80}")
        print("STEP 3: Configure Scaling")
        print("-" * 80)

        same_dimensions = new_width_px == original.width_px and new_height_px == original.height_px
        if same_dimensions:
            print("\nImage dimensions match exactly - no coordinate translation needed.")
            return "none", 1.0, 1.0, original.ppm

        width_ratio = new_width_px / original.width_px if original.width_px > 0 else 1.0
        height_ratio = new_height_px / original.height_px if original.height_px > 0 else 1.0

        print(f"\n  Original: {original.width_px} x {original.height_px} px")
        print(f"  New:      {new_width_px} x {new_height_px} px")
        w_sign = "+" if width_ratio > 1 else ""
        h_sign = "+" if height_ratio > 1 else ""
        print(f"  Width ratio:  {width_ratio:.4f}x ({w_sign}{((width_ratio - 1) * 100):.1f}%)")
        print(f"  Height ratio: {height_ratio:.4f}x ({h_sign}{((height_ratio - 1) * 100):.1f}%)")

        aspect_diff = abs(width_ratio - height_ratio)
        if aspect_diff >= 0.01:
            print(f"\n  WARNING: Aspect ratio differs by {aspect_diff:.2%} - placements may appear distorted.")

        print("\nScaling options:")
        print("  1. Proportional - Scale all coordinates by image ratio (recommended)")
        print("  2. Preserve Physical - Keep real-world positions, update PPM only")
        print("  3. Manual PPM - Enter new pixels-per-meter value manually")
        print("  4. No Scaling - Replace image only, keep all coordinates unchanged")

        try:
            scale_choice = (
                InputUtils.safe_input("\nSelect scaling mode [1]: ", context="_wizard_determine_scaling").strip() or "1"
            )
        except EOFError:
            logging.info("EOF detected during scale mode selection")
            return None

        return self._apply_scale_choice(
            scale_choice,
            ScaleChoiceContext(
                width_ratio=width_ratio,
                height_ratio=height_ratio,
                original_ppm=original.ppm,
                original_width_m=original.width_m,
                new_width_px=new_width_px,
            ),
        )

    def _apply_scale_choice(
        self,
        scale_choice: str,
        ctx: ScaleChoiceContext,
    ) -> tuple[str, float, float, float]:
        """Map a scaling menu choice to (scaling_mode, scale_x, scale_y, new_ppm)."""
        if scale_choice == "2":
            if ctx.original_width_m and ctx.original_width_m > 0:
                new_ppm = ctx.new_width_px / ctx.original_width_m
            else:
                new_ppm = ctx.new_width_px / (ctx.new_width_px / ctx.original_ppm) if ctx.original_ppm else 1.0
            print(f"\nPreserving physical positions. New PPM: {new_ppm:.2f}")
            return "preserve_physical", 1.0, 1.0, new_ppm

        if scale_choice == "3":
            try:
                new_ppm_input = InputUtils.safe_input(
                    f"Enter new PPM (current: {ctx.original_ppm:.2f}): ", context="_apply_scale_choice"
                ).strip()
                new_ppm = float(new_ppm_input) if new_ppm_input else ctx.original_ppm
            except (ValueError, EOFError):
                print("Invalid PPM value, using original")
                new_ppm = ctx.original_ppm
            print(f"\nUsing manual PPM: {new_ppm:.2f}, scaling: x={ctx.width_ratio:.4f}, y={ctx.height_ratio:.4f}")
            return "manual_ppm", ctx.width_ratio, ctx.height_ratio, new_ppm

        if scale_choice == "4":
            print("\nNo coordinate scaling - image replacement only")
            return "none", 1.0, 1.0, ctx.original_ppm

        # Default: proportional (choice "1" or anything else)
        print(f"\nUsing proportional scaling: x={ctx.width_ratio:.4f}, y={ctx.height_ratio:.4f}")
        return "proportional", ctx.width_ratio, ctx.height_ratio, ctx.original_ppm

    def _wizard_scale_path_nodes(self, nodes: list, scale_x: float, scale_y: float) -> list:
        """Return a copy of path nodes with x/y coordinates scaled."""
        scaled = []
        for node in nodes:
            scaled_node = dict(node)
            if isinstance(scaled_node.get("x"), (int, float)):
                scaled_node["x"] = scaled_node["x"] * scale_x
            if isinstance(scaled_node.get("y"), (int, float)):
                scaled_node["y"] = scaled_node["y"] * scale_y
            scaled.append(scaled_node)
        return scaled

    def _wizard_scale_geometry(self, current_map: dict, factors: MapScalingFactors, dims: MapDimensions) -> dict:
        """Build the map-update body: dimensions, PPM, and scaled wall/wayfinding paths."""
        scale_x = factors.x_factor  # Unpack x-axis scale factor for readability.
        scale_y = factors.y_factor  # Unpack y-axis scale factor for readability.
        new_width_px = dims.width_px  # Unpack new pixel width for the update body.
        new_height_px = dims.height_px  # Unpack new pixel height for the update body.
        new_ppm = dims.ppm  # Unpack new PPM so width_m/height_m can be recomputed.
        map_update: dict = {"width": new_width_px, "height": new_height_px, "ppm": new_ppm}
        if new_ppm and new_ppm > 0:
            map_update["width_m"] = new_width_px / new_ppm
            map_update["height_m"] = new_height_px / new_ppm

        if scale_x == 1.0 and scale_y == 1.0:
            return map_update

        for path_key in ("wall_path", "wayfinding_path"):
            nodes = current_map.get(path_key, {}).get("nodes")
            if not nodes:
                continue
            scaled_nodes = self._wizard_scale_path_nodes(nodes, scale_x, scale_y)
            map_update[path_key] = {"nodes": scaled_nodes}
            logging.debug("Scaled %d %s nodes", len(scaled_nodes), path_key)

        return map_update

    def _wizard_scale_devices(self, site_id: str, devices: list, scale_x: float, scale_y: float, errors: list) -> None:
        """Scale device x/y positions and update each device via the API."""
        print(f"  Updating {len(devices)} device positions...")
        updated, failed = 0, 0
        for device in devices:
            try:
                resp = mistapi.api.v1.sites.devices.updateSiteDevice(
                    self.apisession,
                    site_id=site_id,
                    device_id=device.get("id"),
                    body={"x": device.get("x", 0) * scale_x, "y": device.get("y", 0) * scale_y},
                )
                if resp.status_code == 200:
                    updated += 1
                else:
                    failed += 1
                    logging.warning("Device update failed for %s: HTTP %d", device.get("id"), resp.status_code)
            except Exception as err:
                failed += 1
                logging.error("Device update error for %s: %s", device.get("id"), err)
        print(f"    Devices updated: {updated}, failed: {failed}")
        if failed:
            errors.append(f"{failed} device updates failed")

    def _wizard_scale_zones(self, site_id: str, zones: list, scale_x: float, scale_y: float, errors: list) -> None:
        """Scale zone vertex coordinates and update each zone via the API."""
        print(f"  Updating {len(zones)} zone positions...")
        updated, failed = 0, 0
        for zone in zones:
            try:
                vertices = zone.get("vertices", [])
                if not vertices:
                    updated += 1
                    continue
                scaled_vertices = [{"x": v.get("x", 0) * scale_x, "y": v.get("y", 0) * scale_y} for v in vertices]
                resp = mistapi.api.v1.sites.zones.updateSiteZone(
                    self.apisession, site_id=site_id, zone_id=zone.get("id"), body={"vertices": scaled_vertices}
                )
                if resp.status_code == 200:
                    updated += 1
                else:
                    failed += 1
                    logging.warning("Zone update failed for %s: HTTP %d", zone.get("id"), resp.status_code)
            except Exception as err:
                failed += 1
                logging.error("Zone update error for %s: %s", zone.get("id"), err)
        print(f"    Zones updated: {updated}, failed: {failed}")
        if failed:
            errors.append(f"{failed} zone updates failed")

    def _wizard_scale_beacons(self, site_id: str, beacons: list, scale_x: float, scale_y: float, errors: list) -> None:
        """Scale beacon positions and update each beacon via the API."""
        print(f"  Updating {len(beacons)} beacon positions...")
        updated, failed = 0, 0
        for beacon in beacons:
            try:
                resp = mistapi.api.v1.sites.beacons.updateSiteBeacon(
                    self.apisession,
                    site_id=site_id,
                    beacon_id=beacon.get("id"),
                    body={"x": beacon.get("x", 0) * scale_x, "y": beacon.get("y", 0) * scale_y},
                )
                if resp.status_code == 200:
                    updated += 1
                else:
                    failed += 1
            except Exception as err:
                failed += 1
                logging.error("Beacon update error: %s", err)
        print(f"    Beacons updated: {updated}, failed: {failed}")
        if failed:
            errors.append(f"{failed} beacon updates failed")

    def _wizard_scale_vbeacons(
        self, site_id: str, vbeacons: list, scale_x: float, scale_y: float, errors: list
    ) -> None:
        """Scale virtual beacon positions and update each vbeacon via the API."""
        print(f"  Updating {len(vbeacons)} virtual beacon positions...")
        updated, failed = 0, 0
        for vbeacon in vbeacons:
            try:
                resp = mistapi.api.v1.sites.vbeacons.updateSiteVBeacon(
                    self.apisession,
                    site_id=site_id,
                    vbeacon_id=vbeacon.get("id"),
                    body={"x": vbeacon.get("x", 0) * scale_x, "y": vbeacon.get("y", 0) * scale_y},
                )
                if resp.status_code == 200:
                    updated += 1
                else:
                    failed += 1
            except Exception as err:
                failed += 1
                logging.error("Virtual beacon update error: %s", err)
        print(f"    Virtual beacons updated: {updated}, failed: {failed}")
        if failed:
            errors.append(f"{failed} virtual beacon updates failed")

    def _wizard_run(self, site_id: str, site_name: str) -> None:
        """Execute the core wizard steps after site selection."""
        map_id = self._wizard_select_and_display_map(site_id, site_name)
        if not map_id:
            return

        current_map_response = mistapi.api.v1.sites.maps.getSiteMap(self.apisession, site_id=site_id, map_id=map_id)
        if current_map_response.status_code != 200:
            print(f"\n! Failed to fetch map details: HTTP {current_map_response.status_code}")
            return

        current_map = current_map_response.data
        map_name = current_map.get("name", "Unnamed")
        assets = self._wizard_fetch_assets(site_id, map_id)
        self._wizard_print_map_summary(current_map, map_name, assets)

        image_result = self._wizard_get_new_image()
        if not image_result:
            return
        file_path, new_width_px, new_height_px = image_result

        scaling_result = self._wizard_determine_scaling(
            OriginalMapMetrics(
                width_px=current_map.get("width", 0),
                height_px=current_map.get("height", 0),
                ppm=current_map.get("ppm", 1.0),
                width_m=current_map.get("width_m", 0),
            ),
            (new_width_px, new_height_px),
        )
        if scaling_result is None:
            return
        scaling_mode, scale_x, scale_y, new_ppm = scaling_result
        # Issue #433 Phase C T3: pre-build the two shared bundles so all three
        # wizard helpers (preview/apply/summary) get matching scaling state.
        new_dims = MapDimensions(width_px=new_width_px, height_px=new_height_px, ppm=new_ppm)
        new_factors = MapScalingFactors(mode=scaling_mode, x_factor=scale_x, y_factor=scale_y)

        backup_file = self._wizard_create_backup(site_id, map_id, map_name)
        if backup_file is None:
            return

        self._wizard_preview(
            MapWizardPreviewContext(current_map=current_map, map_name=map_name, assets=assets),
            new_dims,
            new_factors,
        )
        if not self._wizard_confirm():
            return

        errors: list = []
        self._wizard_apply(
            MapWizardApplyTarget(site_id=site_id, map_id=map_id, file_path=file_path),
            MapWizardApplyContext(current_map=current_map, assets=assets, errors=errors),
            new_dims,
            new_factors,
        )
        self._wizard_print_summary(
            MapWizardSummaryContext(map_name=map_name, backup_file=backup_file, errors=errors),
            new_dims,
            new_factors,
        )
        logging.info("wizard completed for %s: mode=%s errors=%d", map_id, scaling_mode, len(errors))

    def intelligent_map_replacement_wizard(self):
        """Intelligent Map Replacement Wizard.

        Replaces a floor plan image while intelligently preserving and translating:
        - Device placements (APs, switches, gateways) with coordinate scaling
        - Zones with vertex coordinate translation
        - Walls and wayfinding paths
        - Beacons and virtual beacons

        Supports different scale/dimension scenarios:
        1. Same dimensions - direct replacement
        2. Different dimensions, same scale - coordinate translation
        3. Different dimensions, different scale - intelligent scaling with preview
        """
        logging.info("intelligent_map_replacement_wizard initiated")
        print("\n" + "=" * 80)
        print("INTELLIGENT MAP REPLACEMENT WIZARD")
        print("=" * 80)

        site_id, site_name = self.get_current_site()
        if not site_id:
            logging.warning("Map replacement wizard aborted: No site selected")
            return

        try:
            self._wizard_run(site_id, site_name)
        except EOFError:
            logging.info("EOF detected in map replacement wizard")
        except ImportError as import_err:
            print(f"\n! Missing required dependency: {import_err}")
            print("Install with: pip install Pillow")
            logging.error("Map replacement wizard import error: %s", import_err)
        except Exception as err:
            logging.exception("Error in map replacement wizard: %s", err)
            print(f"\n! Error: {err}")

    def _wizard_select_and_display_map(self, site_id: str, site_name: str) -> str | None:
        """Select map and display current map info header. Returns map_id or None."""
        print("\nThis wizard helps you replace a floor plan image while preserving")
        print("device placements, zones, walls, and other map data.")
        print("=" * 80)
        print("\n" + "-" * 80)
        print("STEP 1: Select Map to Replace")
        print("-" * 80)
        map_id = self._select_map_from_site(site_id, site_name)
        if not map_id:
            logging.info("Map replacement wizard aborted: No map selected")
        return map_id

    def _wizard_print_map_summary(self, current_map: dict, map_name: str, assets: dict) -> None:
        """Print current map properties and asset counts to the console."""
        print(f"\n{'-' * 80}")
        print(f"Current Map: {map_name}")
        print(f"{'-' * 80}")
        print(f"  Dimensions: {current_map.get('width', 'N/A')} x {current_map.get('height', 'N/A')} px")
        print(f"  PPM: {current_map.get('ppm', 'N/A')}")
        print(f"  Has Image: {'Yes' if 'url' in current_map else 'No'}")
        wall_nodes = len(current_map.get("wall_path", {}).get("nodes", []))
        wayfinding_nodes = len(current_map.get("wayfinding_path", {}).get("nodes", []))
        print("\nAssets on this map:")
        print(f"  Devices: {len(assets['devices'])}")
        print(f"  Zones: {len(assets['zones'])}")
        print(f"  BLE Beacons: {len(assets['beacons'])}")
        print(f"  Virtual Beacons: {len(assets['vbeacons'])}")
        print(f"  Wall Nodes: {wall_nodes}")
        print(f"  Wayfinding Nodes: {wayfinding_nodes}")

    def _wizard_create_backup(self, site_id: str, map_id: str, map_name: str) -> str | None:
        """Create a backup of current map geometry. Returns backup_file path or None on cancel."""
        print(f"\n{'-' * 80}")
        print("STEP 4: Creating Backup")
        print("-" * 80)
        backup_file = self._backup_map_geometry(
            api_session=self.apisession,
            site_id=site_id,
            map_id=map_id,
            map_name=map_name,
            backup_reason="pre_replacement",
        )
        if backup_file:
            print(f"Backup saved: {backup_file}")
            return backup_file

        print("! Warning: Backup may not have completed fully")
        try:
            proceed = (
                InputUtils.safe_input("Continue anyway? (yes/no): ", context="_wizard_create_backup").strip().lower()
            )
        except EOFError:
            return None
        if proceed not in ("yes", "y"):
            print("\n! Operation cancelled")
            return None
        return ""

    def _wizard_preview(
        self,
        context: MapWizardPreviewContext,
        dims: MapDimensions,
        factors: MapScalingFactors,
    ) -> None:
        """Print step-5 preview of what will change."""
        current_map = context.current_map  # Unpack current map record for original-dim lookup.
        map_name = context.map_name  # Unpack human-readable map name for the heading.
        assets = context.assets  # Unpack asset bundle for the coord-translation sample.
        new_width_px = dims.width_px  # Unpack new pixel width for the preview line.
        new_height_px = dims.height_px  # Unpack new pixel height for the preview line.
        new_ppm = dims.ppm  # Unpack new PPM for the preview line.
        scaling_mode = factors.mode  # Unpack scaling mode for the preview line.
        scale_x = factors.x_factor  # Unpack x-axis factor for the translation sample.
        scale_y = factors.y_factor  # Unpack y-axis factor for the translation sample.
        print(f"\n{'-' * 80}")
        print("STEP 5: Preview Changes")
        print("-" * 80)
        print(f"\nMap: {map_name}")
        orig_w, orig_h = current_map.get("width", 0), current_map.get("height", 0)
        orig_ppm = current_map.get("ppm", 0)
        print(f"  Dimensions: {orig_w}x{orig_h} -> {new_width_px}x{new_height_px} px")
        print(f"  PPM: {orig_ppm:.2f} -> {new_ppm:.2f}  Mode: {scaling_mode}")

        if scaling_mode == "none" or (scale_x == 1.0 and scale_y == 1.0):
            print("\n  No coordinate changes required")
            return

        print(f"\nCoordinate Translation (scale_x={scale_x:.4f}, scale_y={scale_y:.4f}):")
        for device in assets["devices"][:5]:
            old_x, old_y = device.get("x", 0), device.get("y", 0)
            name = device.get("name", device.get("mac", "Unknown"))
            print(f"    {name}: ({old_x:.1f}, {old_y:.1f}) -> ({old_x * scale_x:.1f}, {old_y * scale_y:.1f})")
        if len(assets["devices"]) > 5:
            print(f"    ... and {len(assets['devices']) - 5} more devices")
        for zone in assets["zones"][:3]:
            print(f"    Zone {zone.get('name', 'Unnamed')}: {len(zone.get('vertices', []))} vertices will be scaled")
        if len(assets["zones"]) > 3:
            print(f"    ... and {len(assets['zones']) - 3} more zones")

    def _wizard_confirm(self) -> bool:
        """Prompt for REPLACE confirmation. Returns True if confirmed."""
        print(f"\n{'-' * 80}")
        print("STEP 6: Confirm and Apply")
        print("-" * 80)
        print("\n! WARNING: This will modify the map and update all device/zone positions.")
        try:
            confirm = InputUtils.safe_input("\nType 'REPLACE' to proceed: ", context="_wizard_confirm").strip()
        except EOFError:
            logging.info("EOF detected during confirmation")
            return False
        if confirm != "REPLACE":
            print("\n! Operation cancelled")
            return False
        return True

    def _wizard_apply(
        self,
        target: MapWizardApplyTarget,
        context: MapWizardApplyContext,
        dims: MapDimensions,
        factors: MapScalingFactors,
    ) -> None:
        """Apply all wizard changes: map update, image upload, and coordinate scaling."""
        site_id = target.site_id  # Unpack site UUID for the API calls below.
        map_id = target.map_id  # Unpack map UUID for the API calls below.
        file_path = target.file_path  # Unpack path to the new image file being uploaded.
        current_map = context.current_map  # Unpack pre-change map record for path scaling.
        assets = context.assets  # Unpack asset bundle so each subtype helper can scale in place.
        errors = context.errors  # Unpack the out-list helpers append failure descriptions to.
        scale_x = factors.x_factor  # Unpack x-axis factor so the geometry helper builds the body.
        scale_y = factors.y_factor  # Unpack y-axis factor so the geometry helper builds the body.
        scaling_mode = factors.mode  # Unpack scaling mode to gate the asset-scaling block.
        print("\nApplying changes...")
        print("  Updating map properties...")
        map_update = self._wizard_scale_geometry(current_map, factors, dims)
        try:
            resp = mistapi.api.v1.sites.maps.updateSiteMap(
                self.apisession, site_id=site_id, map_id=map_id, body=map_update
            )
            if resp.status_code == 200:
                print("    Map properties updated successfully")
            else:
                errors.append(f"Map update failed: HTTP {resp.status_code}")
                print(f"    ! Failed to update map: HTTP {resp.status_code}")
        except Exception as map_err:
            errors.append(f"Map update error: {map_err}")
            print(f"    ! Error updating map: {map_err}")

        print("  Uploading new image...")
        try:
            upload_resp = mistapi.api.v1.sites.maps.addSiteMapImageFile(
                self.apisession, site_id=site_id, map_id=map_id, file=file_path
            )
            if upload_resp.status_code in (200, 201):
                print("    Image uploaded successfully")
            else:
                errors.append(f"Image upload failed: HTTP {upload_resp.status_code}")
                print(f"    ! Failed to upload image: HTTP {upload_resp.status_code}")
        except Exception as img_err:
            errors.append(f"Image upload error: {img_err}")
            print(f"    ! Error uploading image: {img_err}")

        if scaling_mode == "proportional" and (scale_x != 1.0 or scale_y != 1.0):
            self._wizard_scale_devices(site_id, assets["devices"], scale_x, scale_y, errors)
            self._wizard_scale_zones(site_id, assets["zones"], scale_x, scale_y, errors)
            self._wizard_scale_beacons(site_id, assets["beacons"], scale_x, scale_y, errors)
            self._wizard_scale_vbeacons(site_id, assets["vbeacons"], scale_x, scale_y, errors)

    def _wizard_print_summary(
        self,
        context: MapWizardSummaryContext,
        dims: MapDimensions,
        factors: MapScalingFactors,
    ) -> None:
        """Print the completion summary."""
        map_name = context.map_name  # Unpack human-readable map name for the heading.
        backup_file = context.backup_file  # Unpack pre-change backup path for the failure footer.
        errors = context.errors  # Unpack accumulated apply errors for the optional warning block.
        new_width_px = dims.width_px  # Unpack new pixel width for the summary line.
        new_height_px = dims.height_px  # Unpack new pixel height for the summary line.
        new_ppm = dims.ppm  # Unpack new PPM for the summary line.
        scaling_mode = factors.mode  # Unpack scaling mode for the summary line.
        print(f"\n{'=' * 80}")
        print("MAP REPLACEMENT COMPLETE")
        print("=" * 80)
        print(f"\nMap: {map_name}  New: {new_width_px}x{new_height_px} px  PPM: {new_ppm:.2f}  Mode: {scaling_mode}")
        if errors:
            print(f"\n! Completed with {len(errors)} warning(s):")
            for err in errors:
                print(f"  - {err}")
            print(f"\nBackup file: {backup_file}")
        else:
            print("\nAll changes applied successfully!")
            print(f"Backup file: {backup_file}")


def run_wizard(maps_manager: Any):
    """Entry point: launch the intelligent map replacement wizard.

    Thin factory so MapsManager and tests can invoke the wizard without
    instantiating :class:`_MapsWizard` directly.
    """
    return _MapsWizard(maps_manager).intelligent_map_replacement_wizard()
