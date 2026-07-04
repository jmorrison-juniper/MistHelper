"""Intelligent map-replacement wizard (extracted from MapsManager)."""

from __future__ import annotations  # WHY: enable PEP 604 union types on 3.10+ codebase.

import logging  # WHY: emit info/debug/warning traces from wizard flow.
import os  # WHY: validate replacement image file path on disk.
from dataclasses import dataclass  # WHY: pack helper args into 5-Item Rule bundles.
from typing import Any  # WHY: MapsManager and mist API records are loosely-typed dicts.

import mistapi  # WHY: Mist REST client for all wizard API calls.

from src.dataclasses.map_scaling_deps import (  # WHY: shared scaling arg bundles.
    MapDimensions,  # WHY: pixel size + PPM triple.
    MapScalingFactors,  # WHY: mode + x/y factor bundle.
    OriginalMapMetrics,  # WHY: original map dims + PPM + width_m for scaling math.
    ScaleChoiceContext,  # WHY: input bundle for scaling menu dispatcher.
)
from src.dataclasses.map_wizard_deps import (  # WHY: shared wizard step bundles.
    MapWizardApplyContext,  # WHY: mutable apply-step state (assets + errors).
    MapWizardApplyTarget,  # WHY: apply-step target identifiers + image path.
    MapWizardPreviewContext,  # WHY: preview-step render inputs.
    MapWizardSummaryContext,  # WHY: summary-step render inputs.
)
from src.utils.input_utils import InputUtils  # WHY: consistent CTRL-C/EOF-safe prompt helper.

logger = logging.getLogger(__name__)  # WHY: module-scoped logger for structured tracing.

# WHY: named constants replace magic numbers so intent is self-documenting.
VALID_IMAGE_EXTENSIONS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".gif")  # WHY: allowed floor-plan formats.
ASPECT_MISMATCH_TOLERANCE: float = 0.01  # WHY: >=1% width/height ratio delta triggers distortion warning.
PREVIEW_DEVICE_SAMPLE: int = 5  # WHY: preview cap on devices printed before ellipsis.
PREVIEW_ZONE_SAMPLE: int = 3  # WHY: preview cap on zones printed before ellipsis.
HTTP_OK: int = 200  # WHY: successful Mist API GET/PUT status code.
HTTP_CREATED: int = 201  # WHY: alternate success code for image upload endpoint.
BACKUP_REASON: str = "pre_replacement"  # WHY: audit tag stored with the pre-change map backup.
BANNER_WIDTH: int = 80  # WHY: uniform horizontal-rule width for console step headers.
SCALE_CHOICE_PRESERVE_PHYSICAL: str = "2"  # WHY: menu option to preserve real-world positions.
SCALE_CHOICE_MANUAL_PPM: str = "3"  # WHY: menu option to enter PPM manually.
SCALE_CHOICE_NONE: str = "4"  # WHY: menu option to skip coordinate scaling entirely.
DEFAULT_SCALE_FACTOR: float = 1.0  # WHY: identity scale used when dimensions match or none/preserve modes chosen.
DEFAULT_PPM_FALLBACK: float = 1.0  # WHY: safe non-zero PPM when original data is missing.


# WHY: internal frozen bundle so the apply-step image upload helper stays under 5 params.
@dataclass(frozen=True, slots=True)
class _ImageUploadTarget:  # WHY: 5-Item Rule bundle for the image upload helper signature.
    """Site/map/file identifiers required to upload a floor-plan image."""

    site_id: str  # WHY: Mist site UUID owning the target map.
    map_id: str  # WHY: Mist map UUID receiving the replacement image.
    file_path: str  # WHY: absolute path to the new floor-plan file on disk.


# WHY: internal frozen bundle so per-asset scaling helpers keep tidy signatures.
@dataclass(frozen=True, slots=True)
class _AssetScaleParams:  # WHY: 5-Item Rule bundle so asset scalers keep ≤5 args.
    """Site + factors + errors accumulator for a single asset-type scaler."""

    site_id: str  # WHY: Mist site UUID owning the assets being repositioned.
    scale_x: float  # WHY: x-axis multiplier applied to every asset's stored x coordinate.
    scale_y: float  # WHY: y-axis multiplier applied to every asset's stored y coordinate.
    errors: list[Any]  # WHY: out-list where scalers append failure descriptions for the summary step.


# WHY: internal bundle for the run-time state shared across wizard stages.
@dataclass(frozen=True, slots=True)
class _WizardStageInputs:  # WHY: 5-Item Rule bundle shared across wizard stages.
    """Frozen inputs passed between _wizard_run stages to keep signatures small."""

    site_id: str  # WHY: Mist site UUID chosen at wizard entry.
    map_id: str  # WHY: Mist map UUID selected in step 1.
    current_map: dict[str, Any]  # WHY: pre-change map record used across preview/apply/summary.
    map_name: str  # WHY: human-readable name reused in every step's heading.
    assets: dict[str, Any]  # WHY: bundled devices/zones/beacons/vbeacons for the entire wizard.


# WHY: internal bundle for the commit-and-summarize tail so it stays under 5 params.
@dataclass(frozen=True, slots=True)
class _CommitBundle:  # WHY: 5-Item Rule bundle for the apply-tail helper signature.
    """File + backup + errors triple passed to the commit-and-summarize tail."""

    file_path: str  # WHY: absolute path of the new image being applied.
    backup_file: str  # WHY: pre-change backup path for the summary output.
    errors: list[Any]  # WHY: out-list of failure strings accumulated by _wizard_apply.


class _MapsWizard:  # WHY: wrapper class hosting extracted wizard flow methods.
    """Wrapper class holding the extracted wizard methods; delegates to MapsManager."""

    def __init__(self, maps_manager: Any) -> None:  # WHY: keep a reference to MapsManager for delegation.
        """Store the wrapped MapsManager for attribute delegation."""
        self._mm = maps_manager  # WHY: retain manager so __getattr__ can proxy calls.

    def __getattr__(self, name: str) -> Any:  # WHY: proxy unknown attrs to MapsManager.
        """Delegate missing attribute lookups to the wrapped MapsManager."""
        mm = self.__dict__.get("_mm")  # WHY: read via __dict__ to avoid infinite __getattr__ recursion.
        if mm is None:  # pragma: no cover - only during broken init
            raise AttributeError(name)  # WHY: surface the true missing-attr error to the caller.
        return getattr(mm, name)  # WHY: forward unresolved lookups to MapsManager transparently.

    def _wizard_fetch_devices(self, site_id: str, map_id: str) -> list[Any]:  # WHY: pull devices attached to this map.
        """Fetch all devices placed on the given map."""
        try:
            resp = mistapi.api.v1.sites.devices.listSiteDevices(  # WHY: pull every device in the site.
                self.apisession, site_id=site_id, type="all"
            )
        except Exception as err:  # WHY: log and swallow so wizard stays operable on API failures.
            logging.debug("Could not fetch devices for wizard: %s", err)  # WHY: keep flow going on errors.
            return []  # WHY: empty list keeps caller math (len()/iteration) safe.
        return self._filter_records_by_map(resp, map_id)  # WHY: reuse status/filter helper.

    def _filter_records_by_map(self, resp: Any, map_id: str) -> list[Any]:  # WHY: shared HTTP-OK + map-id filter.
        """Return records whose ``map_id`` field matches when the response is HTTP OK."""
        if resp.status_code != HTTP_OK:  # WHY: only trust records from a successful response.
            return []  # WHY: fail closed so partial data never leaks into scaling math.
        data = resp.data if isinstance(resp.data, list) else []  # WHY: guard against dict/None payloads.
        return [record for record in data if record.get("map_id") == map_id]  # WHY: restrict to this map only.

    def _wizard_fetch_zones(self, site_id: str, map_id: str) -> list[Any]:  # WHY: pull zones attached to this map.
        """Fetch all zones placed on the given map."""
        try:
            resp = mistapi.api.v1.sites.zones.listSiteZones(  # WHY: pull every zone in the site.
                self.apisession, site_id=site_id
            )
        except Exception as err:  # WHY: log and swallow so wizard stays operable on API failures.
            logging.debug("Could not fetch zones for wizard: %s", err)  # WHY: swallow so wizard can continue.
            return []  # WHY: empty list keeps downstream len()/loops safe.
        return self._filter_records_by_map(resp, map_id)  # WHY: reuse map-id filter.

    def _wizard_fetch_beacons(
        self, site_id: str, map_id: str
    ) -> tuple[list[Any], list[Any]]:  # WHY: pull physical + virtual beacons.
        """Fetch BLE beacons and virtual beacons on the given map."""
        try:
            beacons = self._fetch_beacons_of_kind(  # WHY: physical BLE beacons.
                mistapi.api.v1.sites.beacons.listSiteBeacons, site_id, map_id
            )
            vbeacons = self._fetch_beacons_of_kind(  # WHY: virtual beacons share the same shape.
                mistapi.api.v1.sites.vbeacons.listSiteVBeacons, site_id, map_id
            )
        except Exception as err:
            logging.debug("Could not fetch beacons for wizard: %s", err)  # WHY: keep flow going on errors.
            return [], []  # WHY: two empty lists match the documented tuple contract.
        return beacons, vbeacons  # WHY: pair matches downstream unpacking (beacons, vbeacons).

    def _fetch_beacons_of_kind(self, api_call: Any, site_id: str, map_id: str) -> list[Any]:
        """Fetch one beacon kind (real or virtual) filtered to the given map."""
        resp = api_call(self.apisession, site_id=site_id)  # WHY: single endpoint invocation.
        return self._filter_records_by_map(resp, map_id)  # WHY: reuse status/filter helper.

    def _wizard_fetch_assets(self, site_id: str, map_id: str) -> dict[str, Any]:
        """Fetch all map assets: devices, zones, beacons, vbeacons."""
        beacons, vbeacons = self._wizard_fetch_beacons(site_id, map_id)  # WHY: single beacons round-trip.
        return {  # WHY: dict keys match downstream unpacking sites.
            "devices": self._wizard_fetch_devices(site_id, map_id),  # WHY: APs/switches/gateways on map.
            "zones": self._wizard_fetch_zones(site_id, map_id),  # WHY: zone polygons on map.
            "beacons": beacons,  # WHY: physical BLE beacon list.
            "vbeacons": vbeacons,  # WHY: virtual beacon list.
        }

    def _wizard_get_new_image(self) -> tuple[str, int, int] | None:
        """Prompt for the replacement image file path and return (path, width, height)."""
        self._print_step_header(2, "Select New Floor Plan Image")  # WHY: consistent step banner.
        print("\nEnter the path to the new floor plan image:")  # WHY: user instruction.
        print("Supported formats: PNG, JPG, JPEG, GIF")  # WHY: remind user of allowed types.
        file_path = self._prompt_file_path()  # WHY: EOF-safe prompt returning cleaned path or None.
        if file_path is None:  # WHY: user cancelled or entered nothing.
            return None  # WHY: propagate cancellation up to _wizard_run.
        if not self._is_valid_image_file(file_path):  # WHY: reject bad path/type before opening it.
            return None  # WHY: helper already printed the user-facing error.
        dims = self._read_image_dimensions(file_path)  # WHY: obtain pixel W/H via Pillow.
        if dims is None:  # WHY: Pillow read failed for a corrupt/unsupported file.
            return None  # WHY: helper already printed the reason.
        return file_path, dims[0], dims[1]  # WHY: expand tuple for the historic return shape.

    def _prompt_file_path(self) -> str | None:
        """Prompt for a file path, strip quotes, and return None on cancel or empty input."""
        try:
            raw = InputUtils.safe_input(  # WHY: EOF/CTRL-C handled uniformly.
                "File path: ", context="_wizard_get_new_image"
            ).strip()
        except EOFError:
            logging.info("EOF detected during file path input")  # WHY: leave a trail for debug.
            return None  # WHY: signal cancel to caller.
        cleaned = raw.strip('"').strip("'")  # WHY: users often paste quoted paths from explorer.
        if not cleaned:  # WHY: empty input == cancel.
            print("\n! No file path provided")  # WHY: user-visible feedback.
            return None  # WHY: propagate cancel.
        return cleaned  # WHY: clean, non-empty path for downstream validation.

    def _is_valid_image_file(self, file_path: str) -> bool:
        """Return True when the path points to an existing file with a supported extension."""
        if not os.path.exists(file_path) or not os.path.isfile(file_path):  # WHY: both checks needed (dir vs file).
            print(f"\n! File not found or not a file: {file_path}")  # WHY: surface exact problem.
            return False  # WHY: caller aborts wizard.
        file_ext = os.path.splitext(file_path)[1].lower()  # WHY: normalise for case-insensitive compare.
        if file_ext not in VALID_IMAGE_EXTENSIONS:  # WHY: enforce Mist-supported formats.
            print(f"\n! Invalid file type: {file_ext}. Supported: {', '.join(VALID_IMAGE_EXTENSIONS)}")
            return False  # WHY: caller aborts wizard.
        return True  # WHY: path is safe to open with Pillow.

    def _read_image_dimensions(self, file_path: str) -> tuple[int, int] | None:
        """Open the image with Pillow and return (width_px, height_px) or None on failure."""
        from PIL import Image  # WHY: lazy import so wizard imports stay light for non-image callers.

        try:
            with Image.open(file_path) as img:  # WHY: context manager frees the file handle promptly.
                width_px, height_px = img.size  # WHY: Pillow returns (w, h) tuple in pixels.
                print(f"\nNew image dimensions: {width_px} x {height_px} pixels")  # WHY: user visibility.
                return width_px, height_px  # WHY: return tuple in expected order.
        except Exception as img_err:
            print(f"\n! Failed to read image dimensions: {img_err}")  # WHY: surface Pillow error text.
            return None  # WHY: caller aborts wizard.

    def _wizard_determine_scaling(  # WHY: entry point for scaling mode selection.
        self,
        original: OriginalMapMetrics,
        new_dimensions: tuple[int, int],
    ) -> tuple[str, float, float, float] | None:
        """Prompt user for scaling mode and return (scaling_mode, scale_x, scale_y, new_ppm)."""
        new_width_px, new_height_px = new_dimensions  # WHY: unpack for readability in comparisons.
        self._print_step_header(3, "Configure Scaling")  # WHY: consistent step banner.
        if new_width_px == original.width_px and new_height_px == original.height_px:  # WHY: no-op fast path.
            print("\nImage dimensions match exactly - no coordinate translation needed.")
            return "none", DEFAULT_SCALE_FACTOR, DEFAULT_SCALE_FACTOR, original.ppm  # WHY: identity result.
        width_ratio, height_ratio = self._compute_dimension_ratios(  # WHY: safe divide-by-zero handling.
            original, new_width_px, new_height_px
        )
        self._print_scaling_deltas(original, new_width_px, new_height_px, width_ratio, height_ratio)
        self._print_scaling_menu()  # WHY: show four scaling options to the user.
        scale_choice = self._prompt_scale_choice()  # WHY: EOF-safe menu prompt.
        if scale_choice is None:  # WHY: user cancelled with CTRL-D during menu.
            return None  # WHY: propagate cancel to _wizard_run.
        ctx = self._build_scale_choice_ctx(original, new_width_px, width_ratio, height_ratio)  # WHY: pack params.
        return self._apply_scale_choice(scale_choice, ctx)  # WHY: dispatch to mode-specific branch.

    def _build_scale_choice_ctx(  # WHY: build the ScaleChoiceContext bundle.
        self,
        original: OriginalMapMetrics,
        new_width_px: int,
        width_ratio: float,
        height_ratio: float,
    ) -> ScaleChoiceContext:
        """Assemble the scale-choice context so _wizard_determine_scaling stays short."""
        return ScaleChoiceContext(  # WHY: single construction site keeps caller compact.
            width_ratio=width_ratio,  # WHY: computed proportional x factor.
            height_ratio=height_ratio,  # WHY: computed proportional y factor.
            original_ppm=original.ppm,  # WHY: baseline for physical-preserve math.
            original_width_m=original.width_m,  # WHY: real-world width used in mode 2.
            new_width_px=new_width_px,  # WHY: new pixel width used in mode 2 PPM calc.
        )

    def _compute_dimension_ratios(
        self, original: OriginalMapMetrics, new_width_px: int, new_height_px: int
    ) -> tuple[float, float]:
        """Return (width_ratio, height_ratio) safely handling zero-width/height originals."""
        width_ratio = (  # WHY: fall back to identity when original width unavailable.
            new_width_px / original.width_px if original.width_px > 0 else DEFAULT_SCALE_FACTOR
        )
        height_ratio = (  # WHY: fall back to identity when original height unavailable.
            new_height_px / original.height_px if original.height_px > 0 else DEFAULT_SCALE_FACTOR
        )
        return width_ratio, height_ratio  # WHY: tuple keeps caller unpacking clean.

    def _print_scaling_deltas(
        self,
        original: OriginalMapMetrics,
        new_width_px: int,
        new_height_px: int,
        width_ratio: float,
        height_ratio: float,
    ) -> None:
        """Print original/new dimensions plus ratio deltas and aspect warning."""
        print(f"\n  Original: {original.width_px} x {original.height_px} px")  # WHY: baseline dimensions.
        print(f"  New:      {new_width_px} x {new_height_px} px")  # WHY: new dimensions for comparison.
        w_sign = "+" if width_ratio > 1 else ""  # WHY: explicit + sign for positive deltas.
        h_sign = "+" if height_ratio > 1 else ""  # WHY: explicit + sign for positive deltas.
        print(f"  Width ratio:  {width_ratio:.4f}x ({w_sign}{((width_ratio - 1) * 100):.1f}%)")
        print(f"  Height ratio: {height_ratio:.4f}x ({h_sign}{((height_ratio - 1) * 100):.1f}%)")
        aspect_diff = abs(width_ratio - height_ratio)  # WHY: measure distortion risk.
        if aspect_diff >= ASPECT_MISMATCH_TOLERANCE:  # WHY: threshold from named constant.
            print(f"\n  WARNING: Aspect ratio differs by {aspect_diff:.2%} - placements may appear distorted.")

    def _print_scaling_menu(self) -> None:
        """Print the four scaling mode options."""
        print("\nScaling options:")  # WHY: menu header.
        print("  1. Proportional - Scale all coordinates by image ratio (recommended)")
        print("  2. Preserve Physical - Keep real-world positions, update PPM only")
        print("  3. Manual PPM - Enter new pixels-per-meter value manually")
        print("  4. No Scaling - Replace image only, keep all coordinates unchanged")

    def _prompt_scale_choice(self) -> str | None:
        """Prompt for the scaling menu selection; return the trimmed string or None on EOF."""
        try:
            raw = InputUtils.safe_input(  # WHY: uniform EOF/CTRL-C handling.
                "\nSelect scaling mode [1]: ", context="_wizard_determine_scaling"
            ).strip()
        except EOFError:
            logging.info("EOF detected during scale mode selection")  # WHY: trace user cancel.
            return None  # WHY: signal cancel.
        return raw or "1"  # WHY: default to proportional when user hits enter.

    def _apply_scale_choice(
        self,
        scale_choice: str,
        ctx: ScaleChoiceContext,
    ) -> tuple[str, float, float, float]:
        """Map a scaling menu choice to (scaling_mode, scale_x, scale_y, new_ppm)."""
        if scale_choice == SCALE_CHOICE_PRESERVE_PHYSICAL:  # WHY: mode 2 handled by dedicated helper.
            return self._resolve_preserve_physical(ctx)  # WHY: PPM-only update, identity scale factors.
        if scale_choice == SCALE_CHOICE_MANUAL_PPM:  # WHY: mode 3 delegates to manual PPM prompt.
            return self._resolve_manual_ppm(ctx)  # WHY: keeps _apply_scale_choice CC low.
        if scale_choice == SCALE_CHOICE_NONE:  # WHY: mode 4 keeps all coordinates unchanged.
            print("\nNo coordinate scaling - image replacement only")
            return "none", DEFAULT_SCALE_FACTOR, DEFAULT_SCALE_FACTOR, ctx.original_ppm  # WHY: identity result.
        print(f"\nUsing proportional scaling: x={ctx.width_ratio:.4f}, y={ctx.height_ratio:.4f}")
        return "proportional", ctx.width_ratio, ctx.height_ratio, ctx.original_ppm  # WHY: default branch.

    def _resolve_preserve_physical(self, ctx: ScaleChoiceContext) -> tuple[str, float, float, float]:
        """Compute new PPM that keeps real-world positions across image replacement."""
        if ctx.original_width_m and ctx.original_width_m > 0:  # WHY: preferred anchor is stored width_m.
            new_ppm = ctx.new_width_px / ctx.original_width_m  # WHY: recompute pixels-per-meter.
        elif ctx.original_ppm:  # WHY: fall back to reconstructing width_m from original PPM.
            new_ppm = ctx.new_width_px / (ctx.new_width_px / ctx.original_ppm)  # WHY: preserves anchor implicitly.
        else:
            new_ppm = DEFAULT_PPM_FALLBACK  # WHY: safe non-zero PPM when no anchor data exists.
        print(f"\nPreserving physical positions. New PPM: {new_ppm:.2f}")  # WHY: user-visible result.
        return "preserve_physical", DEFAULT_SCALE_FACTOR, DEFAULT_SCALE_FACTOR, new_ppm  # WHY: identity xy.

    def _resolve_manual_ppm(self, ctx: ScaleChoiceContext) -> tuple[str, float, float, float]:
        """Prompt for a manual PPM value; fall back to original PPM on invalid/EOF input."""
        try:
            raw = InputUtils.safe_input(  # WHY: EOF-safe prompt.
                f"Enter new PPM (current: {ctx.original_ppm:.2f}): ", context="_apply_scale_choice"
            ).strip()
            new_ppm = float(raw) if raw else ctx.original_ppm  # WHY: empty input keeps existing PPM.
        except (ValueError, EOFError):
            print("Invalid PPM value, using original")  # WHY: user-visible fallback notice.
            new_ppm = ctx.original_ppm  # WHY: safe default preserves prior behaviour.
        print(f"\nUsing manual PPM: {new_ppm:.2f}, scaling: x={ctx.width_ratio:.4f}, y={ctx.height_ratio:.4f}")
        return "manual_ppm", ctx.width_ratio, ctx.height_ratio, new_ppm  # WHY: use pixel ratios for xy.

    def _wizard_scale_path_nodes(self, nodes: list[Any], scale_x: float, scale_y: float) -> list[Any]:
        """Return a copy of path nodes with x/y coordinates scaled."""
        scaled = []  # WHY: collect scaled node copies without mutating source.
        for node in nodes:
            scaled.append(self._scale_single_node(node, scale_x, scale_y))  # WHY: per-node clone+scale.
        return scaled  # WHY: caller replaces original list wholesale.

    def _scale_single_node(self, node: dict[str, Any], scale_x: float, scale_y: float) -> dict[str, Any]:
        """Return a shallow copy of ``node`` with numeric x/y multiplied by the scale factors."""
        scaled_node = dict(node)  # WHY: preserve non-x/y fields unchanged.
        if isinstance(scaled_node.get("x"), (int, float)):  # WHY: guard non-numeric x fields.
            scaled_node["x"] = scaled_node["x"] * scale_x  # WHY: apply x-axis scale factor.
        if isinstance(scaled_node.get("y"), (int, float)):  # WHY: guard non-numeric y fields.
            scaled_node["y"] = scaled_node["y"] * scale_y  # WHY: apply y-axis scale factor.
        return scaled_node  # WHY: return the mutated copy.

    def _wizard_scale_geometry(
        self, current_map: dict[str, Any], factors: MapScalingFactors, dims: MapDimensions
    ) -> dict[str, Any]:
        """Build the map-update body: dimensions, PPM, and scaled wall/wayfinding paths."""
        map_update = self._build_geometry_dimensions(dims)  # WHY: base body with width/height/ppm/*_m.
        if factors.x_factor == DEFAULT_SCALE_FACTOR and factors.y_factor == DEFAULT_SCALE_FACTOR:  # WHY: no scale.
            return map_update  # WHY: skip expensive path-node scaling.
        for path_key in ("wall_path", "wayfinding_path"):  # WHY: both path types share the same shape.
            self._maybe_scale_path(map_update, current_map, path_key, factors)  # WHY: mutate body in place.
        return map_update  # WHY: single return keeps signature clean.

    def _build_geometry_dimensions(self, dims: MapDimensions) -> dict[str, Any]:
        """Return the base map-update dict with width/height/ppm plus width_m/height_m when valid."""
        map_update: dict[str, Any] = {  # WHY: minimum keys always present.
            "width": dims.width_px,  # WHY: new pixel width sent to API.
            "height": dims.height_px,  # WHY: new pixel height sent to API.
            "ppm": dims.ppm,  # WHY: new pixels-per-meter sent to API.
        }
        if dims.ppm and dims.ppm > 0:  # WHY: divide-by-zero guard.
            map_update["width_m"] = dims.width_px / dims.ppm  # WHY: derived real-world width.
            map_update["height_m"] = dims.height_px / dims.ppm  # WHY: derived real-world height.
        return map_update  # WHY: caller may append path_key entries.

    def _maybe_scale_path(
        self,
        map_update: dict[str, Any],
        current_map: dict[str, Any],
        path_key: str,
        factors: MapScalingFactors,
    ) -> None:
        """Scale the named path's nodes into ``map_update`` when present."""
        nodes = current_map.get(path_key, {}).get("nodes")  # WHY: fetch nested list safely.
        if not nodes:  # WHY: skip absent/empty paths.
            return  # WHY: nothing to scale.
        scaled_nodes = self._wizard_scale_path_nodes(nodes, factors.x_factor, factors.y_factor)  # WHY: reuse scaler.
        map_update[path_key] = {"nodes": scaled_nodes}  # WHY: mirror Mist's nested shape.
        logging.debug("Scaled %d %s nodes", len(scaled_nodes), path_key)  # WHY: trace scaling counts.

    def _wizard_scale_devices(
        self, site_id: str, devices: list[Any], scale_x: float, scale_y: float, errors: list[Any]
    ) -> None:
        """Scale device x/y positions and update each device via the API."""
        params = _AssetScaleParams(site_id=site_id, scale_x=scale_x, scale_y=scale_y, errors=errors)  # WHY: bundle.
        self._apply_asset_scaling(  # WHY: shared loop across asset kinds.
            label="device", records=devices, updater=self._update_single_device, params=params
        )

    def _update_single_device(self, record: dict[str, Any], params: _AssetScaleParams) -> bool:
        """Update one device's x/y via the API; return True on success."""
        resp = mistapi.api.v1.sites.devices.updateSiteDevice(  # WHY: PATCH-style position update.
            self.apisession,
            site_id=params.site_id,
            device_id=record.get("id"),
            body={  # WHY: only x/y change; other device fields left untouched.
                "x": record.get("x", 0) * params.scale_x,
                "y": record.get("y", 0) * params.scale_y,
            },
        )
        if resp.status_code != HTTP_OK:  # WHY: non-OK counts as failure for the summary.
            logging.warning("Device update failed for %s: HTTP %d", record.get("id"), resp.status_code)
            return False  # WHY: increment failed counter in shared loop.
        return True  # WHY: increment updated counter in shared loop.

    def _wizard_scale_zones(
        self, site_id: str, zones: list[Any], scale_x: float, scale_y: float, errors: list[Any]
    ) -> None:
        """Scale zone vertex coordinates and update each zone via the API."""
        params = _AssetScaleParams(site_id=site_id, scale_x=scale_x, scale_y=scale_y, errors=errors)  # WHY: bundle.
        self._apply_asset_scaling(  # WHY: reuse the shared loop.
            label="zone", records=zones, updater=self._update_single_zone, params=params
        )

    def _update_single_zone(self, record: dict[str, Any], params: _AssetScaleParams) -> bool:
        """Update one zone's vertices via the API; return True on success."""
        vertices = record.get("vertices", [])  # WHY: zone shape is a vertex list.
        if not vertices:  # WHY: empty polygon has nothing to scale.
            return True  # WHY: count as success; nothing changed but nothing failed either.
        scaled_vertices = [  # WHY: element-wise multiply on x/y.
            {"x": v.get("x", 0) * params.scale_x, "y": v.get("y", 0) * params.scale_y} for v in vertices
        ]
        resp = mistapi.api.v1.sites.zones.updateSiteZone(  # WHY: replace vertices atomically.
            self.apisession, site_id=params.site_id, zone_id=record.get("id"), body={"vertices": scaled_vertices}
        )
        if resp.status_code != HTTP_OK:  # WHY: non-OK counts as failure for the summary.
            logging.warning("Zone update failed for %s: HTTP %d", record.get("id"), resp.status_code)
            return False  # WHY: increment failed counter.
        return True  # WHY: increment updated counter.

    def _wizard_scale_beacons(
        self, site_id: str, beacons: list[Any], scale_x: float, scale_y: float, errors: list[Any]
    ) -> None:
        """Scale beacon positions and update each beacon via the API."""
        params = _AssetScaleParams(site_id=site_id, scale_x=scale_x, scale_y=scale_y, errors=errors)  # WHY: bundle.
        self._apply_asset_scaling(  # WHY: reuse shared loop with beacon updater.
            label="beacon", records=beacons, updater=self._update_single_beacon, params=params
        )

    def _update_single_beacon(self, record: dict[str, Any], params: _AssetScaleParams) -> bool:
        """Update one physical beacon's x/y via the API; return True on success."""
        resp = mistapi.api.v1.sites.beacons.updateSiteBeacon(  # WHY: PATCH beacon position.
            self.apisession,
            site_id=params.site_id,
            beacon_id=record.get("id"),
            body={"x": record.get("x", 0) * params.scale_x, "y": record.get("y", 0) * params.scale_y},
        )
        return bool(resp.status_code == HTTP_OK)  # WHY: cast Any→bool for strict typing.

    def _wizard_scale_vbeacons(
        self, site_id: str, vbeacons: list[Any], scale_x: float, scale_y: float, errors: list[Any]
    ) -> None:
        """Scale virtual beacon positions and update each vbeacon via the API."""
        params = _AssetScaleParams(site_id=site_id, scale_x=scale_x, scale_y=scale_y, errors=errors)  # WHY: bundle.
        self._apply_asset_scaling(  # WHY: reuse shared loop with vbeacon updater.
            label="virtual beacon", records=vbeacons, updater=self._update_single_vbeacon, params=params
        )

    def _update_single_vbeacon(self, record: dict[str, Any], params: _AssetScaleParams) -> bool:
        """Update one virtual beacon's x/y via the API; return True on success."""
        resp = mistapi.api.v1.sites.vbeacons.updateSiteVBeacon(  # WHY: PATCH vbeacon position.
            self.apisession,
            site_id=params.site_id,
            vbeacon_id=record.get("id"),
            body={"x": record.get("x", 0) * params.scale_x, "y": record.get("y", 0) * params.scale_y},
        )
        return bool(resp.status_code == HTTP_OK)  # WHY: cast Any→bool for strict typing.

    def _apply_asset_scaling(self, label: str, records: list[Any], updater: Any, params: _AssetScaleParams) -> None:
        """Shared per-asset loop that dispatches to ``updater`` and totals success/failure."""
        print(f"  Updating {len(records)} {label} positions...")  # WHY: user-visible progress line.
        updated, failed = 0, 0  # WHY: aggregate counters shown after the loop.
        for record in records:
            try:
                ok = updater(record, params)  # WHY: dispatch to asset-kind-specific updater.
            except Exception as err:
                failed += 1  # WHY: any raised exception is a failure.
                logging.error("%s update error for %s: %s", label.capitalize(), record.get("id"), err)
                continue  # WHY: skip the ok-flag branch after handling exception.
            if ok:
                updated += 1  # WHY: success bumps updated counter.
            else:
                failed += 1  # WHY: non-OK bumps failed counter (updater already logged detail).
        print(f"    {label.capitalize()}s updated: {updated}, failed: {failed}")  # WHY: totals for user.
        if failed:
            params.errors.append(f"{failed} {label} updates failed")  # WHY: bubble up to summary step.

    def _wizard_run(self, site_id: str, site_name: str) -> None:
        """Execute the core wizard steps after site selection."""
        stage = self._prepare_wizard_stage(site_id, site_name)  # WHY: bundles map/asset context.
        if stage is None:  # WHY: user cancelled during map selection or fetch failed.
            return  # WHY: nothing else to do.
        image = self._wizard_get_new_image()  # WHY: step 2 picks the replacement image.
        if not image:  # WHY: user cancelled during image selection.
            return  # WHY: abort wizard.
        file_path, new_width_px, new_height_px = image  # WHY: expand tuple for readability.
        scaling = self._resolve_scaling_result(stage.current_map, new_width_px, new_height_px)  # WHY: step 3.
        if scaling is None:  # WHY: user cancelled during scaling menu.
            return  # WHY: abort wizard.
        new_dims, new_factors = scaling  # WHY: unpack the dims+factors bundle pair.
        backup_file = self._wizard_create_backup(site_id, stage.map_id, stage.map_name)  # WHY: step 4.
        if backup_file is None:  # WHY: user cancelled backup confirmation.
            return  # WHY: abort wizard.
        self._run_apply_stage(stage, file_path, new_dims, new_factors, backup_file)  # WHY: steps 5-7 finalize.

    def _prepare_wizard_stage(self, site_id: str, site_name: str) -> _WizardStageInputs | None:
        """Select the target map, fetch its record + assets, and return a stage bundle."""
        map_id = self._wizard_select_and_display_map(site_id, site_name)  # WHY: user picks the map.
        if not map_id:  # WHY: no selection means abort.
            return None  # WHY: signal cancel to caller.
        resp = mistapi.api.v1.sites.maps.getSiteMap(self.apisession, site_id=site_id, map_id=map_id)  # WHY: read map.
        if resp.status_code != HTTP_OK:  # WHY: cannot proceed without the map record.
            print(f"\n! Failed to fetch map details: HTTP {resp.status_code}")  # WHY: user-visible error.
            return None  # WHY: signal fetch failure.
        current_map = resp.data  # WHY: preserved for preview/apply/summary.
        map_name = current_map.get("name", "Unnamed")  # WHY: fallback for missing names.
        assets = self._wizard_fetch_assets(site_id, map_id)  # WHY: devices/zones/beacons/vbeacons in one call.
        self._wizard_print_map_summary(current_map, map_name, assets)  # WHY: user sees current state.
        return _WizardStageInputs(  # WHY: bundle keeps subsequent signatures tidy.
            site_id=site_id, map_id=map_id, current_map=current_map, map_name=map_name, assets=assets
        )

    def _resolve_scaling_result(
        self, current_map: dict[str, Any], new_width_px: int, new_height_px: int
    ) -> tuple[MapDimensions, MapScalingFactors] | None:
        """Run the scaling prompt and return (dims, factors) bundles or None on cancel."""
        result = self._wizard_determine_scaling(  # WHY: step 3 dialogue.
            OriginalMapMetrics(
                width_px=current_map.get("width", 0),  # WHY: baseline width for ratio math.
                height_px=current_map.get("height", 0),  # WHY: baseline height for ratio math.
                ppm=current_map.get("ppm", DEFAULT_PPM_FALLBACK),  # WHY: safe default when missing.
                width_m=current_map.get("width_m", 0),  # WHY: enables preserve-physical mode.
            ),
            (new_width_px, new_height_px),
        )
        if result is None:  # WHY: user cancelled the menu.
            return None  # WHY: propagate cancel.
        scaling_mode, scale_x, scale_y, new_ppm = result  # WHY: expand for dataclass construction.
        new_dims = MapDimensions(width_px=new_width_px, height_px=new_height_px, ppm=new_ppm)  # WHY: pack dims.
        new_factors = MapScalingFactors(mode=scaling_mode, x_factor=scale_x, y_factor=scale_y)  # WHY: pack factors.
        return new_dims, new_factors  # WHY: tuple keeps caller signature small.

    def _run_apply_stage(  # WHY: post-preview commit flow shared between wizard entry points.
        self,
        stage: _WizardStageInputs,
        file_path: str,
        new_dims: MapDimensions,
        new_factors: MapScalingFactors,
        backup_file: str,
    ) -> None:
        """Run preview -> confirm -> apply -> summary for the pre-prepared stage bundle."""
        self._wizard_preview(  # WHY: step 5 shows the diff to the user.
            MapWizardPreviewContext(current_map=stage.current_map, map_name=stage.map_name, assets=stage.assets),
            new_dims,
            new_factors,
        )
        if not self._wizard_confirm():  # WHY: step 6 gates step 7 with REPLACE confirmation.
            return  # WHY: user aborted right before commit.
        errors: list[Any] = []  # WHY: accumulator flowed through step 7 into the summary printer.
        bundle = _CommitBundle(file_path=file_path, backup_file=backup_file, errors=errors)  # WHY: pack tail args.
        self._commit_and_summarize(stage, bundle, new_dims, new_factors)  # WHY: split commit tail.

    def _commit_and_summarize(  # WHY: tail portion of the apply stage split out to satisfy STRUCT-LENGTH.
        self,
        stage: _WizardStageInputs,
        bundle: _CommitBundle,
        new_dims: MapDimensions,
        new_factors: MapScalingFactors,
    ) -> None:
        """Commit the change set and print the summary line."""
        self._wizard_apply(  # WHY: step 7 commits the change set.
            MapWizardApplyTarget(site_id=stage.site_id, map_id=stage.map_id, file_path=bundle.file_path),
            MapWizardApplyContext(current_map=stage.current_map, assets=stage.assets, errors=bundle.errors),
            new_dims,
            new_factors,
        )
        self._wizard_print_summary(  # WHY: step 8 tells the user what happened.
            MapWizardSummaryContext(map_name=stage.map_name, backup_file=bundle.backup_file, errors=bundle.errors),
            new_dims,
            new_factors,
        )
        logging.info(  # WHY: structured completion log for post-run debugging.
            "wizard completed for %s: mode=%s errors=%d", stage.map_id, new_factors.mode, len(bundle.errors)
        )

    def intelligent_map_replacement_wizard(self) -> None:
        """Intelligent Map Replacement Wizard entry point."""
        logging.info("intelligent_map_replacement_wizard initiated")  # WHY: trace wizard start.
        self._print_wizard_banner()  # WHY: uniform banner across every wizard invocation.
        site_id, site_name = self.get_current_site()  # WHY: MapsManager exposes the active site tuple.
        if not site_id:  # WHY: no site == nothing to do.
            logging.warning("Map replacement wizard aborted: No site selected")  # WHY: trace abort reason.
            return  # WHY: caller may still show the menu again.
        self._run_wizard_guarded(site_id, site_name)  # WHY: wrap _wizard_run in the shared error guard.

    def _print_wizard_banner(self) -> None:
        """Print the wizard title banner."""
        print("\n" + "=" * BANNER_WIDTH)  # WHY: uniform banner width matches other steps.
        print("INTELLIGENT MAP REPLACEMENT WIZARD")  # WHY: user-visible title.
        print("=" * BANNER_WIDTH)  # WHY: bottom rule of banner.

    def _run_wizard_guarded(self, site_id: str, site_name: str) -> None:
        """Invoke ``_wizard_run`` and translate common exceptions into user-friendly messages."""
        try:
            self._wizard_run(site_id, site_name)  # WHY: main flow.
        except EOFError:
            logging.info("EOF detected in map replacement wizard")  # WHY: expected cancel path.
        except ImportError as import_err:
            print(f"\n! Missing required dependency: {import_err}")  # WHY: Pillow may be missing.
            print("Install with: pip install Pillow")  # WHY: actionable remediation for the user.
            logging.error("Map replacement wizard import error: %s", import_err)  # WHY: structured trace.
        except Exception as err:
            logging.exception("Error in map replacement wizard: %s", err)  # WHY: full traceback for debug.
            print(f"\n! Error: {err}")  # WHY: brief user-facing summary.

    def _wizard_select_and_display_map(self, site_id: str, site_name: str) -> str | None:
        """Select map and display current map info header. Returns map_id or None."""
        print("\nThis wizard helps you replace a floor plan image while preserving")  # WHY: user intro.
        print("device placements, zones, walls, and other map data.")  # WHY: continue intro.
        print("=" * BANNER_WIDTH)  # WHY: separator between intro and step header.
        self._print_step_header(1, "Select Map to Replace")  # WHY: uniform step banner.
        map_id = self._select_map_from_site(site_id, site_name)  # WHY: MapsManager helper prompts the user.
        if not map_id:  # WHY: no map == abort.
            logging.info("Map replacement wizard aborted: No map selected")  # WHY: trace abort.
            return None  # WHY: explicit None keeps return type strict.
        return str(map_id)  # WHY: cast Any→str so signature stays str|None strictly.

    def _print_step_header(self, step_number: int, title: str) -> None:
        """Print a consistent step banner with rules above and below."""
        print(f"\n{'-' * BANNER_WIDTH}")  # WHY: top rule of the step banner.
        print(f"STEP {step_number}: {title}")  # WHY: step number + title.
        print("-" * BANNER_WIDTH)  # WHY: bottom rule.

    def _wizard_print_map_summary(self, current_map: dict[str, Any], map_name: str, assets: dict[str, Any]) -> None:
        """Print current map properties and asset counts to the console."""
        print(f"\n{'-' * BANNER_WIDTH}")  # WHY: top rule for the summary block.
        print(f"Current Map: {map_name}")  # WHY: map name heading.
        print(f"{'-' * BANNER_WIDTH}")  # WHY: bottom rule of the heading.
        print(f"  Dimensions: {current_map.get('width', 'N/A')} x {current_map.get('height', 'N/A')} px")
        print(f"  PPM: {current_map.get('ppm', 'N/A')}")  # WHY: current PPM for reference.
        print(f"  Has Image: {'Yes' if 'url' in current_map else 'No'}")  # WHY: indicates prior upload.
        wall_nodes = len(current_map.get("wall_path", {}).get("nodes", []))  # WHY: count for summary.
        wayfinding_nodes = len(current_map.get("wayfinding_path", {}).get("nodes", []))  # WHY: count.
        print("\nAssets on this map:")  # WHY: sub-heading.
        print(f"  Devices: {len(assets['devices'])}")  # WHY: user-visible asset count.
        print(f"  Zones: {len(assets['zones'])}")  # WHY: user-visible asset count.
        print(f"  BLE Beacons: {len(assets['beacons'])}")  # WHY: user-visible asset count.
        print(f"  Virtual Beacons: {len(assets['vbeacons'])}")  # WHY: user-visible asset count.
        print(f"  Wall Nodes: {wall_nodes}")  # WHY: how many wall-path points will scale.
        print(f"  Wayfinding Nodes: {wayfinding_nodes}")  # WHY: how many wayfinding points will scale.

    def _wizard_create_backup(self, site_id: str, map_id: str, map_name: str) -> str | None:
        """Create a backup of current map geometry. Returns backup_file path or None on cancel."""
        self._print_step_header(4, "Creating Backup")  # WHY: uniform step banner.
        backup_file = self._backup_map_geometry(  # WHY: MapsManager writes a JSON backup file.
            api_session=self.apisession,
            site_id=site_id,
            map_id=map_id,
            map_name=map_name,
            backup_reason=BACKUP_REASON,  # WHY: audit tag stored with the backup file.
        )
        if backup_file:  # WHY: happy path.
            print(f"Backup saved: {backup_file}")  # WHY: tell user where it landed.
            return str(backup_file)  # WHY: cast Any→str so signature stays str|None strictly.
        print("! Warning: Backup may not have completed fully")  # WHY: warn before asking to proceed.
        return self._prompt_continue_without_backup()  # WHY: handles yes/no + EOF in one place.

    def _prompt_continue_without_backup(self) -> str | None:
        """Ask the user to continue without a verified backup; return empty on yes else None."""
        try:
            proceed = (
                InputUtils.safe_input(  # WHY: EOF/CTRL-C safe prompt.
                    "Continue anyway? (yes/no): ", context="_wizard_create_backup"
                )
                .strip()
                .lower()
            )
        except EOFError:
            return None  # WHY: EOF == cancel.
        if proceed not in ("yes", "y"):  # WHY: default to no unless explicit yes.
            print("\n! Operation cancelled")  # WHY: user-visible feedback.
            return None  # WHY: signal cancel to caller.
        return ""  # WHY: empty string means "continue without backup path".

    def _wizard_preview(
        self,
        context: MapWizardPreviewContext,
        dims: MapDimensions,
        factors: MapScalingFactors,
    ) -> None:
        """Print step-5 preview of what will change."""
        self._print_step_header(5, "Preview Changes")  # WHY: uniform step banner.
        self._print_preview_header(context, dims, factors)  # WHY: map name + dims + PPM lines.
        if factors.mode == "none" or (  # WHY: identity scaling short-circuits translation preview.
            factors.x_factor == DEFAULT_SCALE_FACTOR and factors.y_factor == DEFAULT_SCALE_FACTOR
        ):
            print("\n  No coordinate changes required")  # WHY: user-visible clarity.
            return  # WHY: nothing else to preview.
        print(  # WHY: header for the translation sample block.
            f"\nCoordinate Translation (scale_x={factors.x_factor:.4f}, scale_y={factors.y_factor:.4f}):"
        )
        self._print_device_preview_sample(context.assets["devices"], factors)  # WHY: device sample block.
        self._print_zone_preview_sample(context.assets["zones"])  # WHY: zone sample block.

    def _print_preview_header(
        self,
        context: MapWizardPreviewContext,
        dims: MapDimensions,
        factors: MapScalingFactors,
    ) -> None:
        """Print map name + dimensions + PPM/mode delta lines for the preview step."""
        print(f"\nMap: {context.map_name}")  # WHY: identify the map being changed.
        orig_w = context.current_map.get("width", 0)  # WHY: baseline width.
        orig_h = context.current_map.get("height", 0)  # WHY: baseline height.
        orig_ppm = context.current_map.get("ppm", 0)  # WHY: baseline PPM.
        print(f"  Dimensions: {orig_w}x{orig_h} -> {dims.width_px}x{dims.height_px} px")  # WHY: diff line.
        print(f"  PPM: {orig_ppm:.2f} -> {dims.ppm:.2f}  Mode: {factors.mode}")  # WHY: PPM diff + mode.

    def _print_device_preview_sample(self, devices: list[Any], factors: MapScalingFactors) -> None:
        """Print up to ``PREVIEW_DEVICE_SAMPLE`` translated device positions with an ellipsis line."""
        for device in devices[:PREVIEW_DEVICE_SAMPLE]:  # WHY: cap volume so preview stays scannable.
            old_x, old_y = device.get("x", 0), device.get("y", 0)  # WHY: unpack for clarity.
            name = device.get("name", device.get("mac", "Unknown"))  # WHY: prefer name, fall back to MAC.
            print(  # WHY: show old vs new coords side-by-side.
                f"    {name}: ({old_x:.1f}, {old_y:.1f}) -> "
                f"({old_x * factors.x_factor:.1f}, {old_y * factors.y_factor:.1f})"
            )
        if len(devices) > PREVIEW_DEVICE_SAMPLE:  # WHY: hint that more exist beyond the sample cap.
            print(f"    ... and {len(devices) - PREVIEW_DEVICE_SAMPLE} more devices")

    def _print_zone_preview_sample(self, zones: list[Any]) -> None:
        """Print up to ``PREVIEW_ZONE_SAMPLE`` zone vertex counts with an ellipsis line."""
        for zone in zones[:PREVIEW_ZONE_SAMPLE]:  # WHY: cap volume for readable preview.
            print(  # WHY: describe how many vertices each zone will move.
                f"    Zone {zone.get('name', 'Unnamed')}: " f"{len(zone.get('vertices', []))} vertices will be scaled"
            )
        if len(zones) > PREVIEW_ZONE_SAMPLE:  # WHY: hint at the rest.
            print(f"    ... and {len(zones) - PREVIEW_ZONE_SAMPLE} more zones")

    def _wizard_confirm(self) -> bool:
        """Prompt for REPLACE confirmation. Returns True if confirmed."""
        self._print_step_header(6, "Confirm and Apply")  # WHY: uniform step banner.
        print("\n! WARNING: This will modify the map and update all device/zone positions.")
        try:
            confirm = InputUtils.safe_input(  # WHY: EOF-safe prompt.
                "\nType 'REPLACE' to proceed: ", context="_wizard_confirm"
            ).strip()
        except EOFError:
            logging.info("EOF detected during confirmation")  # WHY: trace cancel path.
            return False  # WHY: EOF == not confirmed.
        if confirm != "REPLACE":  # WHY: exact case-sensitive match required as safety gate.
            print("\n! Operation cancelled")  # WHY: user-visible feedback.
            return False  # WHY: caller aborts the apply step.
        return True  # WHY: proceed with the destructive step.

    def _wizard_apply(
        self,
        target: MapWizardApplyTarget,
        context: MapWizardApplyContext,
        dims: MapDimensions,
        factors: MapScalingFactors,
    ) -> None:
        """Apply all wizard changes: map update, image upload, and coordinate scaling."""
        print("\nApplying changes...")  # WHY: user sees a header before three sub-steps.
        self._apply_map_update(target, context, dims, factors)  # WHY: sub-step 7a: dimensions/PPM/paths.
        self._apply_image_upload(  # WHY: sub-step 7b: PUT the new image bytes.
            _ImageUploadTarget(site_id=target.site_id, map_id=target.map_id, file_path=target.file_path),
            context.errors,
        )
        self._apply_asset_updates(target.site_id, context, factors)  # WHY: sub-step 7c: reposition assets.

    def _apply_map_update(
        self,
        target: MapWizardApplyTarget,
        context: MapWizardApplyContext,
        dims: MapDimensions,
        factors: MapScalingFactors,
    ) -> None:
        """Send the map dimensions/PPM/path update to the API and record any failure."""
        print("  Updating map properties...")  # WHY: sub-step label.
        map_update = self._wizard_scale_geometry(context.current_map, factors, dims)  # WHY: build body.
        try:
            resp = mistapi.api.v1.sites.maps.updateSiteMap(  # WHY: PATCH map properties.
                self.apisession, site_id=target.site_id, map_id=target.map_id, body=map_update
            )
        except Exception as map_err:
            context.errors.append(f"Map update error: {map_err}")  # WHY: bubble up to summary.
            print(f"    ! Error updating map: {map_err}")  # WHY: user-visible failure.
            return  # WHY: cannot check response after exception.
        if resp.status_code == HTTP_OK:  # WHY: success path.
            print("    Map properties updated successfully")  # WHY: user visibility.
            return  # WHY: nothing else to report.
        context.errors.append(f"Map update failed: HTTP {resp.status_code}")  # WHY: capture non-OK.
        print(f"    ! Failed to update map: HTTP {resp.status_code}")  # WHY: user-visible failure.

    def _apply_image_upload(self, target: _ImageUploadTarget, errors: list[Any]) -> None:
        """Upload the new floor-plan image; record any failure in ``errors``."""
        print("  Uploading new image...")  # WHY: sub-step label.
        try:
            resp = mistapi.api.v1.sites.maps.addSiteMapImageFile(  # WHY: multipart image upload.
                self.apisession, site_id=target.site_id, map_id=target.map_id, file=target.file_path
            )
        except Exception as img_err:
            errors.append(f"Image upload error: {img_err}")  # WHY: bubble up to summary.
            print(f"    ! Error uploading image: {img_err}")  # WHY: user-visible failure.
            return  # WHY: cannot check response after exception.
        if resp.status_code in (HTTP_OK, HTTP_CREATED):  # WHY: API returns 200 or 201 on success.
            print("    Image uploaded successfully")  # WHY: user visibility.
            return  # WHY: nothing else to report.
        errors.append(f"Image upload failed: HTTP {resp.status_code}")  # WHY: capture non-2xx.
        print(f"    ! Failed to upload image: HTTP {resp.status_code}")  # WHY: user-visible failure.

    def _apply_asset_updates(self, site_id: str, context: MapWizardApplyContext, factors: MapScalingFactors) -> None:
        """Scale devices/zones/beacons/vbeacons when proportional mode is active with real factors."""
        if factors.mode != "proportional":  # WHY: only proportional mode touches asset coords.
            return  # WHY: skip asset scaling for other modes.
        if factors.x_factor == DEFAULT_SCALE_FACTOR and factors.y_factor == DEFAULT_SCALE_FACTOR:  # WHY: no-op.
            return  # WHY: identity scale would be a wasted round trip.
        assets = context.assets  # WHY: alias for terser calls below.
        errors = context.errors  # WHY: shared out-list threaded through scalers.
        self._wizard_scale_devices(site_id, assets["devices"], factors.x_factor, factors.y_factor, errors)
        self._wizard_scale_zones(site_id, assets["zones"], factors.x_factor, factors.y_factor, errors)
        self._wizard_scale_beacons(site_id, assets["beacons"], factors.x_factor, factors.y_factor, errors)
        self._wizard_scale_vbeacons(site_id, assets["vbeacons"], factors.x_factor, factors.y_factor, errors)

    def _wizard_print_summary(
        self,
        context: MapWizardSummaryContext,
        dims: MapDimensions,
        factors: MapScalingFactors,
    ) -> None:
        """Print the completion summary."""
        print(f"\n{'=' * BANNER_WIDTH}")  # WHY: top rule of the summary banner.
        print("MAP REPLACEMENT COMPLETE")  # WHY: title.
        print("=" * BANNER_WIDTH)  # WHY: bottom rule.
        print(  # WHY: one-line result summary.
            f"\nMap: {context.map_name}  New: {dims.width_px}x{dims.height_px} px  "
            f"PPM: {dims.ppm:.2f}  Mode: {factors.mode}"
        )
        if context.errors:  # WHY: warn about partial failures.
            self._print_summary_errors(context.errors, context.backup_file)  # WHY: dedicated block.
            return  # WHY: no success block after errors.
        print("\nAll changes applied successfully!")  # WHY: happy path.
        print(f"Backup file: {context.backup_file}")  # WHY: remind user of rollback file.

    def _print_summary_errors(self, errors: list[Any], backup_file: str) -> None:
        """Print the warning block plus per-error lines and the backup path."""
        print(f"\n! Completed with {len(errors)} warning(s):")  # WHY: header with count.
        for err in errors:
            print(f"  - {err}")  # WHY: itemise each recorded failure.
        print(f"\nBackup file: {backup_file}")  # WHY: remind user of rollback file for recovery.


def run_wizard(maps_manager: Any) -> None:
    """Entry point: launch the intelligent map replacement wizard."""
    return _MapsWizard(maps_manager).intelligent_map_replacement_wizard()  # WHY: thin factory + delegate.
