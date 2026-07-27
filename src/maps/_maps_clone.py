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

from __future__ import annotations  # Enable PEP 604 style unions on 3.10+ runtimes.

import logging  # Module-level structured logger for the clone workflow.
import os  # Filesystem helpers for temp-file cleanup after image transfer.
import tempfile  # Cross-platform temporary file creation for downloaded map images.
from dataclasses import dataclass  # Frozen bundle helpers to satisfy the 5-item rule.
from typing import Any  # Loose typing for Mist API JSON payloads.

import mistapi  # type: ignore[import-untyped]  # Mist REST client used for all map/zone calls.
import requests  # HTTP client used to download the source map image binary.

from src.dataclasses.map_clone_deps import MapCloneSummary, ZoneCloneResult  # Bundle records for summary printing.
from src.utils.input_utils import InputUtils  # EOF-safe interactive prompt helper.

logger = logging.getLogger(__name__)  # Module logger keyed to this file for filtering.

# Table of source-map fields that are safe to copy verbatim into the clone POST body.
_CLONEABLE_MAP_FIELDS: tuple[str, ...] = (
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
)

# HTTP status codes that the Mist API treats as a successful write for map/zone creates.
_OK_CREATE_STATUS: tuple[int, ...] = (200, 201)

# Affirmative responses accepted when confirming a clone at the interactive prompt.
_YES_ANSWERS: frozenset[str] = frozenset({"yes", "y"})


@dataclass(frozen=True, slots=True)
class _ClonePrep:
    """Bundle of inputs computed before the write phase kicks off."""

    source_map: dict[str, Any]  # Full source map record fetched from the API.
    new_name: str  # User-approved name for the clone target.
    clone_payload: dict[str, Any]  # Body ready to POST to createSiteMap.
    zones_count: int  # Number of zones present on the source map.


@dataclass(frozen=True, slots=True)
class _CloneWriteResult:
    """Bundle of outputs produced by the write phase of the clone workflow."""

    cloned_map_id: str  # New map UUID assigned by the Mist API.
    had_image: bool  # True when an image was uploaded to the clone.
    zones_cloned: int  # Count of zones the API accepted on the clone.
    zones_failed: int  # Count of zones that failed to clone.


class _MapsClone:
    """Wrapper class holding the extracted clone methods."""

    def __init__(self, maps_manager: Any) -> None:
        self._mm = maps_manager  # Retain wrapped MapsManager for attribute delegation.

    def __getattr__(self, name: str) -> Any:
        mm = self.__dict__.get("_mm")  # Access instance dict directly to avoid recursion.
        if mm is None:  # pragma: no cover - only during broken init
            raise AttributeError(name)  # Preserve normal AttributeError semantics for consumers.
        return getattr(mm, name)  # Delegate all missing lookups to the wrapped manager.

    def _fetch_source_map_with_display(self, site_id: str, source_map_id: str) -> dict | None:
        """Fetch source map from API and display its key attributes. Return None on failure."""
        logging.debug(
            "Calling getSiteMap API - site_id: %s, map_id: %s", site_id, source_map_id
        )  # Trace API call args.
        print("\nFetching source map details...")  # User-visible progress marker.
        response = mistapi.api.v1.sites.maps.getSiteMap(self.apisession, site_id=site_id, map_id=source_map_id)
        if response.status_code != 200:  # Any non-200 means the map could not be read.
            logging.error("Failed to fetch source map - HTTP %s", response.status_code)  # Log the failure code.
            print(f"\n! Failed to fetch source map: HTTP {response.status_code}")  # Surface to CLI user.
            return None  # Caller aborts when source map is unavailable.
        source_map = response.data  # Extract the JSON body from the mistapi response envelope.
        self._print_source_map_details(source_map)  # Delegate pretty-printing to keep this fn small.
        return source_map  # Hand the record back to the pipeline.

    @staticmethod
    def _print_source_map_details(source_map: dict) -> None:
        """Print a formatted block describing the source map's key attributes."""
        print(f"\n{'-' * 80}")  # Divider above the details block.
        print(f"Source Map: {source_map.get('name', 'Unnamed')}")  # Human-readable identifier.
        print(f"Type: {source_map.get('type', 'N/A')}")  # image / geojson / and so on
        print(f"Dimensions: {source_map.get('width', 'N/A')}x{source_map.get('height', 'N/A')}")  # WxH in pixels.
        print(f"PPM: {source_map.get('ppm', 'N/A')}")  # Pixels-per-meter scale.
        print(f"Has Image: {'Yes' if 'url' in source_map else 'No'}")  # Image asset presence flag.
        print(f"Has Walls: {'Yes' if 'wall_path' in source_map else 'No'}")  # Wall overlay flag.
        print(f"Has Wayfinding: {'Yes' if 'wayfinding_path' in source_map else 'No'}")  # Wayfinding flag.
        print(f"{'-' * 80}")  # Divider below the details block.

    def _prompt_clone_name(self, source_map: dict) -> str | None:
        """Prompt for a clone name using the source map name as default. Return None on EOF."""
        default_name = (
            f"{source_map.get('name', 'Map')} (Copy)"  # Compose a safe default so blank input still names it.
        )
        try:
            new_name = InputUtils.safe_input(
                f"\nEnter name for cloned map [{default_name}]: ", context="_prompt_clone_name"
            ).strip()  # Interactive prompt with EOF handling.
        except EOFError:
            logging.info("EOF detected during clone name prompt")  # Non-fatal: user closed stdin.
            return None  # Signal the caller to abort the clone gracefully.
        return new_name or default_name  # Fall back to the default when the user hits Enter.

    def _build_clone_payload(self, source_map: dict, new_name: str) -> dict:
        """Build a clone payload dict by copying all cloneable fields from the source map."""
        payload: dict[str, Any] = {"name": new_name, "type": source_map.get("type", "image")}  # Required attrs first.
        for field in _CLONEABLE_MAP_FIELDS:  # Iterate the module-level whitelist for stable ordering.
            if field in source_map:  # Skip missing fields so we do not overwrite server defaults with None.
                payload[field] = source_map[field]  # Copy the raw value. API tolerates whatever type came in.
        return payload  # Fully assembled body for createSiteMap.

    def _fetch_source_zone_count(self, site_id: str, source_map_id: str) -> int:
        """Count zones belonging to the source map. Return 0 if fetch fails."""
        try:
            zones_check = mistapi.api.v1.sites.zones.listSiteZones(self.apisession, site_id=site_id)  # Fetch all zones.
            if zones_check.status_code == 200:  # Only trust the count on a clean response.
                return len([z for z in zones_check.data if z.get("map_id") == source_map_id])  # Filter by map.
        except Exception as zone_error:  # Any failure is non-fatal for the clone-plan preview.
            logging.debug("Could not fetch zone count for clone plan: %s", zone_error)  # Debug-only breadcrumb.
        return 0  # Default to zero so the plan text still reads sensibly.

    def _confirm_clone(self, source_map: dict, new_name: str, source_zones_count: int, clone_payload: dict) -> bool:
        """Display the clone plan and prompt user to confirm. Return True to proceed."""
        print(f"\n{'-' * 80}")  # Divider above the plan block.
        print("Clone Plan:")  # Section title for the pre-flight summary.
        print(f"  New name: {new_name}")  # Show the resolved clone name.
        print("  Will copy: dimensions, orientation, location data, wayfinding, walls")  # Static capability list.
        print(f"  Image: {'Yes - will download and re-upload' if 'url' in source_map else 'No image to copy'}")
        zone_msg = (
            f"  Zones: {source_zones_count} zone(s) will be cloned"
            if source_zones_count > 0
            else "  Zones: None found on source map"
        )  # Choose singular vs plural-style message based on count.
        print(zone_msg)  # Print the zone plan line.
        print(f"{'-' * 80}")  # Divider below the plan block.
        confirm = (
            InputUtils.safe_input("\nProceed with full clone? (yes/no): ", context="_confirm_clone").strip().lower()
        )  # Normalize the answer for comparison against the module-level whitelist.
        if confirm not in _YES_ANSWERS:  # Anything other than a canonical yes cancels the clone.
            print("\n! Clone cancelled")  # Surface the cancellation to the user.
            return False  # Caller must abort the pipeline.
        return True  # Green-light the write phase.

    def _download_clone_image(self, source_map: dict) -> str | None:
        """Download the source map image to a temp file. Return the temp path or None."""
        if "url" not in source_map:  # No image URL means nothing to download.
            return None  # Signal the caller to skip the image upload phase.
        image_temp_path: str | None = None  # Track the temp path so we can clean up on failure.
        try:
            image_temp_path = self._download_image_to_tempfile(source_map["url"])  # Delegate HTTP + write.
            if image_temp_path is not None:  # Only report success when the file actually landed on disk.
                return image_temp_path  # Path is now owned by the caller until upload/cleanup.
        except Exception as download_error:  # Network/O errors are non-fatal. Clone can proceed without image.
            logging.error("Error downloading map image: %s", download_error)  # Full stack trace to the log.
            print(f"! Warning: Could not download image: {download_error}")  # User-facing warning.
        self._cleanup_temp_file(image_temp_path)  # Idempotent cleanup handles both partial-download failure modes.
        return None  # Signal image-less clone path.

    def _download_image_to_tempfile(self, image_url: str) -> str | None:
        """Perform the HTTP GET and write the body to a fresh temp file. Return path or None."""
        print("\nDownloading map image...")  # Progress marker for the user.
        file_ext = self._determine_image_extension(image_url)  # Reuse MapsManager's URL->ext heuristic.
        temp_fd, image_temp_path = tempfile.mkstemp(suffix=file_ext)  # Get an exclusive temp file with correct suffix.
        os.close(temp_fd)  # Close the OS handle so we can reopen with a normal write.
        response = requests.get(image_url, timeout=60)  # Blocking GET with a generous timeout for large PNGs.
        if response.status_code != 200:  # Only 200 counts as a valid image body.
            print(f"! Warning: Failed to download image (HTTP {response.status_code})")  # Surface HTTP failure.
            self._cleanup_temp_file(image_temp_path)  # Remove the empty temp file we just created.
            return None  # Report failure to the caller so it can log a warning.
        with open(image_temp_path, "wb") as f:  # Overwrite the temp file with the image bytes.
            f.write(response.content)  # Persist the payload in one shot. Images fit comfortably in memory.
        print(f"Downloaded image ({len(response.content) / 1024:.1f} KB)")  # Report size for user feedback.
        return image_temp_path  # Hand the path to the caller for upload.

    @staticmethod
    def _cleanup_temp_file(path: str | None) -> None:
        """Remove ``path`` if it exists. Tolerate missing paths and OS errors quietly."""
        if not path:  # Guard: nothing to clean up.
            return
        if os.path.exists(path):  # Only unlink real files to avoid noisy exceptions.
            os.remove(path)  # Best-effort cleanup. Errors here are not actionable.

    def _create_cloned_map_entry(self, site_id: str, clone_payload: dict, image_temp_path: str | None) -> str | None:
        """Call createSiteMap API and return the new map ID. Cleans up temp on failure."""
        print("\nCreating cloned map...")  # Progress marker.
        clone_response = mistapi.api.v1.sites.maps.createSiteMap(self.apisession, site_id=site_id, body=clone_payload)
        if clone_response.status_code not in _OK_CREATE_STATUS:  # Non-success codes abort the flow.
            print(f"\n! Failed to clone map: HTTP {clone_response.status_code}")  # Surface HTTP failure.
            logging.error("Map clone failed: %s - %s", clone_response.status_code, clone_response.data)  # Log body.
            self._cleanup_temp_file(image_temp_path)  # No cloned map, so drop the buffered image.
            return None  # Signal upstream to bail out.
        cloned_map = clone_response.data  # Extract the created record.
        cloned_map_id = cloned_map.get("id")  # Grab the new UUID for downstream calls.
        if not cloned_map_id:  # Defensive: API should always return an id on 200/201.
            print("\n! Error: Cloned map has no ID")  # Surface the malformed response.
            logging.error("Cloned map missing ID in response")  # Record the anomaly for debugging.
            return None  # Cannot continue without a target id.
        self._print_created_map_details(cloned_map_id, cloned_map.get("name"))  # Pretty-print the success block.
        return cloned_map_id  # Ready to attach image + zones.

    @staticmethod
    def _print_created_map_details(cloned_map_id: str, name: Any) -> None:
        """Print the success block after the clone map row is inserted."""
        print(f"\n{'-' * 80}")  # Divider.
        print("Map structure cloned successfully!")  # Headline.
        print(f"Cloned Map ID: {cloned_map_id}")  # Echo the new UUID.
        print(f"Name: {name}")  # Echo the resolved name.
        print(f"{'-' * 80}")  # Divider.

    def _upload_clone_image(self, site_id: str, cloned_map_id: str, image_temp_path: str) -> None:
        """Upload image from temp path to cloned map and clean up the temp file."""
        try:
            print("\nUploading image to cloned map...")  # Progress marker.
            upload_response = mistapi.api.v1.sites.maps.addSiteMapImageFile(  # type: ignore[union-attr]
                self.apisession, site_id=site_id, map_id=str(cloned_map_id), file=image_temp_path
            )  # Multipart upload of the previously downloaded image bytes.
            if upload_response.status_code in _OK_CREATE_STATUS:  # 200/201 == accepted.
                print("Image uploaded successfully!")  # User-facing success message.
                logging.info("Image uploaded to cloned map %s", cloned_map_id)  # Structured success log.
            else:
                print(f"! Warning: Failed to upload image: HTTP {upload_response.status_code}")  # Non-fatal warning.
                logging.error("Image upload to cloned map failed: %s", upload_response.status_code)  # Log HTTP.
        except Exception as upload_error:  # Any exception is non-fatal for the outer clone.
            logging.error("Error uploading image to cloned map: %s", upload_error)  # Full failure trace.
            print(f"! Warning: Could not upload image to cloned map: {upload_error}")  # User-facing warning.
        finally:
            self._cleanup_temp_file(image_temp_path)  # Always release the temp file regardless of outcome.

    def _clone_single_zone(self, site_id: str, cloned_map_id: str, zone: dict) -> bool:
        """Clone a single zone to the new map. Return True on success."""
        try:
            zone_payload: dict[str, Any] = {
                "name": zone.get("name", "Unnamed Zone"),
                "map_id": cloned_map_id,
                "vertices": zone.get("vertices", []),
            }  # Base payload shared by all zone types.
            if "type" in zone:  # Optional field: only copy when set on the source.
                zone_payload["type"] = zone["type"]  # Preserve zone class (indoor/outdoor/etc).
            if "z" in zone:  # Optional field: only copy when set on the source.
                zone_payload["z"] = zone["z"]  # Preserve elevation.
            zone_response = mistapi.api.v1.sites.zones.createSiteZone(
                self.apisession, site_id=site_id, body=zone_payload
            )  # Fire the create-zone API for the clone target.
            if zone_response.status_code in _OK_CREATE_STATUS:  # Accept 200 and 201 as success.
                logging.debug("Cloned zone '%s' to new map", zone.get("name"))  # Trace success for audit trails.
                return True  # Caller increments the success counter.
            logging.warning(
                "Failed to clone zone '%s': HTTP %s", zone.get("name"), zone_response.status_code
            )  # Zone-scoped warning: outer flow keeps going.
        except Exception as zone_error:  # Per-zone errors must not derail the whole clone.
            logging.error("Error cloning zone '%s': %s", zone.get("name"), zone_error)  # Record the failure.
        return False  # Default path: caller increments the failure counter.

    def _fetch_source_zones(self, site_id: str, source_map_id: str) -> list[dict] | None:
        """Return zones bound to the source map, or None when the fetch fails."""
        zones_response = mistapi.api.v1.sites.zones.listSiteZones(self.apisession, site_id=site_id)  # List all zones.
        if zones_response.status_code != 200:  # Non-200 means we cannot proceed with zone cloning.
            print("! Warning: Could not fetch zones for cloning")  # Surface the warning.
            return None  # Sentinel differentiates fetch-failure from empty-list.
        return [z for z in zones_response.data if z.get("map_id") == source_map_id]  # Filter by owning map.

    def _clone_zones(self, site_id: str, source_map_id: str, cloned_map_id: str) -> tuple[int, int]:
        """Clone all zones from source map to cloned map. Return (cloned, failed)."""
        print("\nCloning zones...")  # Progress marker.
        try:
            source_zones = self._fetch_source_zones(site_id, source_map_id)  # Delegate list+filter.
            if source_zones is None:  # Fetch failed - warning already printed.
                return 0, 0  # No work done, no failures to report.
            if not source_zones:  # Empty list: nothing to clone.
                print("No zones found on source map to clone")  # Confirm to the user.
                return 0, 0  # Zero counts propagate up unchanged.
            results = [self._clone_single_zone(site_id, cloned_map_id, zone) for zone in source_zones]  # Fan out.
            cloned = sum(results)  # True->1, False->0.
            failed = len(results) - cloned  # Failures = total minus successes.
            print(f"Zones cloned: {cloned} (failed: {failed})")  # Summary line.
            return cloned, failed  # Hand the tallies to the caller.
        except Exception as zones_error:  # Blanket safety net. Keeps outer clone flow intact.
            logging.exception("Error during zone cloning: %s", zones_error)  # Full trace to the log.
            print(f"! Warning: Zone cloning failed: {zones_error}")  # User-facing warning.
            return 0, 0  # Fall back to zero counts.

    def _print_clone_summary(self, summary: MapCloneSummary, zone_result: ZoneCloneResult) -> None:
        """Print the final clone completion summary."""
        source_map = summary.source_map  # Original-map record from the bundle.
        new_name = summary.new_name  # User-chosen clone name.
        cloned_map_id = summary.cloned_map_id  # Newly assigned map UUID.
        clone_payload = summary.clone_payload  # Body posted to Mist.
        had_image = summary.had_image  # Image-uploaded flag.
        zones_cloned = zone_result.cloned  # Successful zone count for the summary.
        zones_failed = zone_result.failed  # Failed zone count for the summary.
        print(f"\n{'-' * 80}")  # Top divider.
        print("CLONE COMPLETE")  # Section title.
        print(f"{'-' * 80}")  # Header divider.
        print(f"Original Map: {source_map.get('name')}")  # Original name.
        print(f"Cloned Map: {new_name}")  # New name.
        print(f"Cloned Map ID: {cloned_map_id}")  # New UUID.
        print("\nCloned elements:")  # Subsection header.
        print(f"  -> Dimensions: {clone_payload.get('width', 'N/A')}x{clone_payload.get('height', 'N/A')}")  # Size.
        print(f"  -> PPM: {clone_payload.get('ppm', 'N/A')}")  # Scale.
        print(f"  -> Walls: {'Yes' if 'wall_path' in clone_payload else 'No'}")  # Wall status.
        print(f"  -> Wayfinding: {'Yes' if 'wayfinding_path' in clone_payload else 'No'}")  # Wayfinding status.
        print(f"  -> Image: {'Yes' if had_image else 'No'}")  # Image upload status.
        zone_text = f"{zones_cloned} cloned" + (f" ({zones_failed} failed)" if zones_failed > 0 else "")
        print(f"  -> Zones: {zone_text}")  # Zones line.
        print(f"{'-' * 80}")  # Bottom divider.

    @staticmethod
    def _print_clone_header() -> None:
        """Print the CLI banner that introduces the clone workflow."""
        print("\n" + "-" * 80)  # Top divider.
        print("CLONE/DUPLICATE MAP")  # Banner title.
        print("-" * 80)  # Bottom divider.
        print("! This will clone ALL map data: image, walls, paths, zones, wayfinding, etc.")  # Confirmation banner.

    def _prepare_clone(self, site_id: str, source_map_id: str) -> _ClonePrep | None:
        """Fetch source, prompt for name, build payload, count zones, and confirm."""
        source_map = self._fetch_source_map_with_display(site_id, source_map_id)  # Load + display source map.
        if source_map is None:  # Fetch failed - warning already printed.
            return None  # Signal caller to bail.
        new_name = self._prompt_clone_name(source_map)  # Interactive name prompt.
        if not new_name:  # EOF or empty resolved name aborts.
            return None
        clone_payload = self._build_clone_payload(source_map, new_name)  # Assemble POST body.
        zones_count = self._fetch_source_zone_count(site_id, source_map_id)  # Pre-count for plan display.
        if not self._confirm_clone(source_map, new_name, zones_count, clone_payload):  # Interactive confirm.
            return None  # User declined.
        return _ClonePrep(
            source_map=source_map,
            new_name=new_name,
            clone_payload=clone_payload,
            zones_count=zones_count,
        )  # Bundle the prep outputs for the write phase.

    def _execute_clone(self, site_id: str, source_map_id: str, prep: _ClonePrep) -> _CloneWriteResult | None:
        """Perform the writes: image download, create map, upload image, clone zones."""
        image_temp_path = self._download_clone_image(prep.source_map)  # Download image (or None).
        cloned_map_id = self._create_cloned_map_entry(site_id, prep.clone_payload, image_temp_path)  # Create map.
        if not cloned_map_id:  # createSiteMap failed - already logged + cleaned up.
            return None
        if image_temp_path:  # Only upload when we actually have a file on disk.
            self._upload_clone_image(site_id, cloned_map_id, image_temp_path)  # Upload + cleanup temp.
        zones_cloned, zones_failed = self._clone_zones(site_id, source_map_id, cloned_map_id)  # Copy zones.
        return _CloneWriteResult(
            cloned_map_id=cloned_map_id,
            had_image=bool(image_temp_path),
            zones_cloned=zones_cloned,
            zones_failed=zones_failed,
        )  # Bundle write outputs for the summary phase.

    def _finalize_clone(self, site_id: str, source_map_id: str, prep: _ClonePrep, result: _CloneWriteResult) -> None:
        """Emit the summary block and audit log after the write phase succeeds."""
        summary = MapCloneSummary(
            source_map=prep.source_map,
            new_name=prep.new_name,
            cloned_map_id=result.cloned_map_id,
            clone_payload=prep.clone_payload,
            had_image=result.had_image,
        )  # Pack summary inputs into the frozen bundle expected by _print_clone_summary.
        zones = ZoneCloneResult(cloned=result.zones_cloned, failed=result.zones_failed)  # Zone tallies bundle.
        self._print_clone_summary(summary, zones)  # Emit the final summary block.
        logging.info(
            "Successfully cloned map %s to %s at site %s (zones: %s)",
            source_map_id,
            result.cloned_map_id,
            site_id,
            result.zones_cloned,
        )  # Structured audit log entry.

    def _run_clone_pipeline(self, site_id: str, site_name: str) -> None:
        """Sequence the interactive clone workflow after the site is resolved."""
        print("\nSelect the map to clone:")  # Prompt lead-in.
        source_map_id = self._select_map_from_site(site_id, site_name)  # Interactive map picker.
        if not source_map_id:  # No map chosen - abort quietly.
            logging.info("clone_map aborted: No source map selected")  # Info-level breadcrumb.
            return
        prep = self._prepare_clone(site_id, source_map_id)  # Prep stage returns None on any abort path.
        if prep is None:  # Any abort message has already been surfaced by _prepare_clone.
            return
        result = self._execute_clone(site_id, source_map_id, prep)  # Write stage returns None on create failure.
        if result is None:  # Nothing to summarize when the write failed.
            return
        self._finalize_clone(site_id, source_map_id, prep, result)  # Summary + audit log delegated to helper.

    def clone_map(self):
        """Clone/duplicate an existing map at the current site including image, walls, paths, and zones."""
        logging.info("clone_map operation initiated")  # Audit-log entry point.
        self._print_clone_header()  # CLI banner.
        site_id, site_name = self.get_current_site()  # Resolve currently-selected site.
        if not site_id:  # No site selected -> nothing to clone.
            logging.warning("clone_map aborted: No site selected")  # Warn since caller expected a site.
            return
        logging.debug("clone_map - Site: %s (ID: %s)", site_name, site_id)  # Trace site context.
        try:
            self._run_clone_pipeline(site_id, site_name)  # All interactive + API work lives in the pipeline.
        except EOFError:
            logging.info("EOF detected during map clone")  # User closed stdin mid-flow.
        except Exception as e:  # Blanket safety net keeps CLI menu usable after clone errors.
            logging.exception("Error cloning map: %s", e)  # Full trace.
            print(f"\n! Error cloning map: {e}")  # User-facing error.


def clone_map(maps_manager: Any):
    """Entry point mirroring MapsManager.clone_map.

    Kept as a module-level factory so callers can invoke the clone
    flow without instantiating :class:`_MapsClone` directly.
    """
    return _MapsClone(maps_manager).clone_map()  # Instantiate wrapper and run the flow.
