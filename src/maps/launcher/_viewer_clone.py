"""Clone-map cluster extracted from ``viewer_callbacks.py``.

Owns the single Wave-E1 public callback ``execute_clone_operation`` plus
its private helpers (input validation, source-map fetch, image
download/upload, per-zone clone, success rendering).  Follows the same
wrapper-class + ``__getattr__`` template used by
:mod:`src.capture._packet_capture_org` so the parent
:class:`~src.maps.launcher.viewer_callbacks.MapViewerCallbacks` stays a
thin coordinator that hands each Dash callback off to the appropriate
cluster.
"""

from __future__ import annotations  # WHY: postponed evaluation consistent with parent module

import logging  # WHY: audit trail for clone-operation diagnostics
import os  # WHY: module-level temp-file handling avoids repeated local imports
import tempfile  # WHY: module-level temp-file creation used by image download helper
from typing import TYPE_CHECKING, Any  # WHY: opaque manager + type-permissive Dash callback args

import requests  # WHY: module-level HTTP client used by image download helper

if TYPE_CHECKING:  # WHY: keep dash imports lazy at runtime
    from dash import Dash  # WHY: annotation reference for register(app)

_ERROR_COLOR = "#ff4444"  # WHY: shared red for user-visible failure spans
_SUCCESS_COLOR = "#00ff88"  # WHY: shared green for user-visible success span
_OK_STATUSES = frozenset({200, 201})  # WHY: HTTP codes accepted by Mist write endpoints
_IMAGE_EXTS = frozenset({"png", "jpg", "jpeg", "gif", "svg"})  # WHY: whitelist of image file extensions
_DEFAULT_IMAGE_EXT = ".png"  # WHY: fallback suffix when URL lacks a recognizable extension
_HTTP_TIMEOUT_SECS = 60  # WHY: preserve original 60s image-download timeout
_CLONE_PROPS: tuple[str, ...] = (  # WHY: table-driven property copy replaces four branches
    "width",  # WHY: image width in pixels
    "height",  # WHY: image height in pixels
    "height_m",  # WHY: real-world height in meters
    "ppm",  # WHY: pixels-per-meter scale factor
    "orientation",  # WHY: map rotation
    "latlng",  # WHY: top-left geo anchor
    "latlng_br",  # WHY: bottom-right geo anchor
    "origin_x",  # WHY: origin x offset for coordinate system
    "origin_y",  # WHY: origin y offset for coordinate system
    "wayfinding",  # WHY: wayfinding data blob
    "wayfinding_path",  # WHY: wayfinding path definitions
    "wall_path",  # WHY: wall path definitions
    "sitesurvey_path",  # WHY: site-survey path definitions
    "occupancy_limit",  # WHY: occupancy cap for the map
    "locked",  # WHY: locked-editing flag
    "view",  # WHY: default view settings
)


def _error_span(message: str) -> Any:  # WHY: single factory for red error spans keeps callers short
    """Build the standard red error ``html.Span`` used across the cluster."""
    from dash import html  # WHY: local import keeps module import-light

    return html.Span(message, style={"color": _ERROR_COLOR})  # WHY: shared color constant


def _error_response(message: str) -> tuple[Any, Any]:  # WHY: (span, no_update) return pattern used by many branches
    """Build the two-tuple returned by Dash callbacks on user-visible failure."""
    from dash import no_update  # WHY: local import keeps module import-light

    return (_error_span(message), no_update)  # WHY: pair the span with a no-op cache-bust update


def _safe_unlink(path: str | None) -> None:  # WHY: dedup temp-file cleanup across three call sites
    """Remove ``path`` if it exists; silently ignore missing files."""
    if path and os.path.exists(path):  # WHY: guard against None and stale paths
        os.remove(path)  # WHY: drop temp file to avoid disk-space leakage


def _infer_image_extension(image_url: str) -> str:  # WHY: extension inference is a distinct concern
    """Return a dot-prefixed extension inferred from ``image_url``."""
    if "." not in image_url:  # WHY: no separator means no extension to infer
        return _DEFAULT_IMAGE_EXT  # WHY: fall back to the module default
    url_ext = image_url.rsplit(".", 1)[-1].split("?")[0].lower()  # WHY: strip query, normalize case
    if url_ext in _IMAGE_EXTS:  # WHY: only accept known image extensions
        return f".{url_ext}"  # WHY: reattach the dot prefix
    return _DEFAULT_IMAGE_EXT  # WHY: unknown extension -> module default


def _create_temp_image_path(image_url: str) -> str:  # WHY: encapsulate temp-file creation ritual
    """Create an empty temp file with an extension inferred from ``image_url``."""
    file_ext = _infer_image_extension(image_url)  # WHY: pick correct suffix
    temp_fd, image_temp_path = tempfile.mkstemp(suffix=file_ext)  # WHY: allocate a unique temp path
    os.close(temp_fd)  # WHY: close fd; caller will reopen the path for writing
    return image_temp_path  # WHY: hand back only the path to the caller


def _download_bytes(image_url: str) -> bytes | None:  # WHY: HTTP call isolated for testability
    """Fetch ``image_url`` and return response bytes or ``None`` on non-200."""
    logging.info("Downloading source map image from %s", image_url)  # WHY: audit trail
    response = requests.get(image_url, timeout=_HTTP_TIMEOUT_SECS)  # WHY: shared timeout constant
    if response.status_code != 200:  # WHY: only 200 counts as a successful image fetch
        logging.warning("Failed to download image: HTTP %s", response.status_code)  # WHY: diagnostic
        return None  # WHY: signal failure without raising
    return response.content  # WHY: return raw bytes for the caller to persist


class _ViewerClone:  # WHY: wrapper class hosting the clone-map callback cluster
    """Cluster class holding the extracted execute_clone_operation body + helpers."""

    def __init__(self, manager: Any) -> None:  # WHY: bind parent so __getattr__ can proxy shared state
        """Store the parent MapViewerCallbacks for delegate lookups."""
        self._mm = manager  # WHY: enable __getattr__ delegation back to the parent class

    def __getattr__(self, name: str) -> Any:  # WHY: transparent proxy for shared state access
        """Delegate unknown attributes to the wrapped parent manager."""
        mm = self.__dict__.get("_mm")  # WHY: guard against half-initialized instances
        if mm is None:  # WHY: only trips during broken init; avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly
        return getattr(mm, name)  # WHY: forward all other attributes to parent

    def execute_clone_operation(
        self,
        n_clicks: int,  # WHY: Dash callback trigger count
        new_name: str | None,  # WHY: user-entered name for the cloned map
        config: dict[str, Any] | None,  # WHY: current map-config store payload
        cache_bust_data: dict[str, Any] | None,  # WHY: current cache-bust store payload
    ) -> tuple[Any, Any]:
        """Clone the current map with all properties, image, and zones."""
        current_trigger = cache_bust_data.get("trigger", 0) if cache_bust_data else 0  # WHY: cache-bust counter
        validation = self._validate_clone_inputs(n_clicks, new_name, config)  # WHY: reject early on bad input
        if len(validation) != 3:  # WHY: validation error tuple has length 2
            return validation  # WHY: forward error tuple unchanged
        new_name_clean, site_id_local, source_map_id = validation  # WHY: unpack validated inputs
        logging.info(  # WHY: audit start of clone op
            "Clone operation started - source: %s, new name: %s", source_map_id, new_name_clean
        )
        return self._run_clone_pipeline(  # WHY: single delegating call keeps this body short
            site_id_local, source_map_id, new_name_clean, config or {}, current_trigger
        )

    def _run_clone_pipeline(  # WHY: exception-guarded orchestration extracted from public callback
        self,
        site_id: str,  # WHY: target Mist site
        source_map_id: str,  # WHY: source map to clone from
        new_name: str,  # WHY: validated cloned-map name
        config: dict[str, Any],  # WHY: config store for backup metadata
        current_trigger: int,  # WHY: current cache-bust counter
    ) -> tuple[Any, Any]:
        """Run the clone workflow under a broad-except guard; return callback tuple."""
        try:
            self._backup_before_clone(site_id, source_map_id, config)  # WHY: safety net
            source_map = self._fetch_source_map(site_id, source_map_id)  # WHY: step 1 fetch
            if source_map is None:  # WHY: source fetch failed
                return _error_response("! Failed to fetch source map")  # WHY: user-visible failure
            return self._perform_clone(site_id, source_map_id, new_name, source_map, current_trigger)
        except Exception as clone_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.exception("Clone operation failed: %s", clone_error)  # WHY: capture stack trace
            return _error_response("! Clone operation failed. Check server logs for details.")

    @staticmethod
    def _clean_map_name(new_name: str | None) -> str | None:  # WHY: name normalization is a distinct concern
        """Return stripped ``new_name`` or ``None`` when empty/whitespace-only."""
        stripped = (new_name or "").strip()  # WHY: coerce None to empty then strip
        return stripped or None  # WHY: empty string maps to None sentinel

    @staticmethod
    def _extract_map_ids(config: dict[str, Any] | None) -> tuple[Any, Any]:  # WHY: pull IDs in one hop
        """Return ``(site_id, map_id)`` from ``config`` (either may be ``None``)."""
        if not config:  # WHY: absent store payload -> nothing to extract
            return (None, None)  # WHY: caller treats None as validation failure
        return (config.get("site_id"), config.get("map_id"))  # WHY: verbatim lookup

    @staticmethod
    def _validate_clone_inputs(
        n_clicks: int,  # WHY: Dash callback trigger count
        new_name: str | None,  # WHY: user-entered clone name candidate
        config: dict[str, Any] | None,  # WHY: current map-config store payload
    ) -> tuple[Any, Any] | tuple[str, str, str]:
        """Return error tuple on bad input, or (clean_name, site_id, map_id) on success."""
        from dash import no_update  # WHY: local import keeps module import-light

        if not n_clicks:  # WHY: button never clicked => silent no-op
            return ("", no_update)  # WHY: empty status leaves UI unchanged
        new_name_clean = _ViewerClone._clean_map_name(new_name)  # WHY: normalize name up front
        if new_name_clean is None:  # WHY: single guard replaces prior compound condition
            return _error_response("! Please enter a name for the cloned map")  # WHY: user-visible failure
        site_id_local, source_map_id = _ViewerClone._extract_map_ids(config)  # WHY: single guard for both IDs
        if not site_id_local or not source_map_id:  # WHY: both required for the API calls
            return _error_response("! Missing site or map configuration")  # WHY: user-visible failure
        return (new_name_clean, site_id_local, source_map_id)  # WHY: all inputs validated

    def _backup_before_clone(self, site_id: str, source_map_id: str, config: dict[str, Any]) -> None:
        """Create a pre-clone geometry backup of the source map (best-effort)."""
        source_map_name = config.get("map_name", "Unknown")  # WHY: display name for the backup file
        logging.info("Creating backup of source map '%s' before cloning", source_map_name)  # WHY: audit trail
        backup_path = self._state.maps_manager_ref._backup_map_geometry(  # WHY: call MapsManager helper
            api_session=self._state.api_session_ref,  # WHY: authenticated Mist session
            site_id=site_id,  # WHY: scope the backup to this site
            map_id=source_map_id,  # WHY: backup only the source map
            map_name=source_map_name,  # WHY: friendly name embedded in backup file
            backup_reason="pre_clone",  # WHY: tag reason for audit
        )
        if backup_path:  # WHY: backup succeeded
            logging.info("Pre-clone backup saved: %s", backup_path)  # WHY: path for operator recovery

    def _fetch_source_map(self, site_id: str, source_map_id: str) -> dict[str, Any] | None:
        """Fetch the source map record from Mist; return None on failure."""
        logging.info("Fetching source map %s for clone", source_map_id)  # WHY: audit start
        source_response = self._state.mistapi_ref.api.v1.sites.maps.getSiteMap(  # WHY: Mist API read
            self._state.api_session_ref, site_id=site_id, map_id=source_map_id
        )
        logging.debug(
            "Source map fetch status_code=%s", getattr(source_response, "status_code", "?")
        )  # WHY: diagnostic
        if source_response.status_code != 200:  # WHY: non-200 means we cannot proceed
            logging.error(
                "Clone failed: Could not fetch source map - HTTP %s", source_response.status_code
            )  # WHY: audit
            return None  # WHY: signal failure without raising
        data: dict[str, Any] = source_response.data  # WHY: parsed JSON payload of the source map
        return data  # WHY: hand the record back to the caller

    def _perform_clone(
        self,
        site_id: str,  # WHY: target Mist site
        source_map_id: str,  # WHY: source map to clone from
        new_name: str,  # WHY: validated cloned-map name
        source_map: dict[str, Any],  # WHY: already-fetched source map record
        current_trigger: int,  # WHY: current cache-bust counter
    ) -> tuple[Any, Any]:
        """Run steps 2-6 of the clone workflow (payload, image, create, upload, zones)."""
        clone_payload = self._build_clone_payload(source_map, new_name)  # WHY: step 2 build payload
        image_temp_path = self._download_source_image(source_map)  # WHY: step 3 image (best-effort)
        cloned_map_id = self._create_cloned_map(site_id, clone_payload, image_temp_path)  # WHY: step 4 create
        if cloned_map_id is None:  # WHY: map creation failed
            return _error_response("! Failed to create cloned map")  # WHY: user-visible failure
        image_uploaded = self._upload_clone_image(site_id, cloned_map_id, image_temp_path)  # WHY: step 5 upload
        zones_cloned = self._clone_zones_for_map(site_id, source_map_id, cloned_map_id)  # WHY: step 6 zones
        return self._render_clone_success(new_name, cloned_map_id, image_uploaded, zones_cloned, current_trigger)

    @staticmethod
    def _build_clone_payload(source_map: dict[str, Any], new_name: str) -> dict[str, Any]:
        """Assemble the full clone payload preserving dimensional + location + path props."""
        clone_payload: dict[str, Any] = {  # WHY: base payload copied byte-identically from source
            "name": new_name,  # WHY: caller-supplied name overrides the source name
            "type": source_map.get("type", "image"),  # WHY: default to image type
        }
        for prop in _CLONE_PROPS:  # WHY: table-driven copy replaces four separate branches
            if prop in source_map:  # WHY: only copy properties actually present on source
                clone_payload[prop] = source_map[prop]  # WHY: preserve original value verbatim
        logging.debug("Clone payload prepared with %d properties", len(clone_payload))  # WHY: diagnostic
        return clone_payload  # WHY: caller passes to createSiteMap

    @staticmethod
    def _download_source_image(source_map: dict[str, Any]) -> str | None:
        """Download the source map image to a temp file; return path or None on any failure."""
        if "url" not in source_map:  # WHY: no image to download
            return None  # WHY: signal absence to callers
        image_url = source_map["url"]  # WHY: URL of the source map image
        image_temp_path: str | None = None  # WHY: track path for cleanup on failure
        try:
            image_temp_path = _create_temp_image_path(image_url)  # WHY: allocate temp file up front
            image_bytes = _download_bytes(image_url)  # WHY: fetch remote bytes via HTTP
            if image_bytes is None:  # WHY: non-200 or missing content
                _safe_unlink(image_temp_path)  # WHY: drop the empty temp file
                return None  # WHY: signal failure
            with open(image_temp_path, "wb") as fh:  # WHY: persist bytes to temp file
                fh.write(image_bytes)  # WHY: write fetched payload
            logging.info("Downloaded source map image (%.1f KB)", len(image_bytes) / 1024)  # WHY: audit success
            return image_temp_path  # WHY: hand path to caller for later upload
        except Exception as img_err:  # noqa: BLE001 - preserve broad-except behavior
            logging.error("Error downloading image: %s", img_err)  # WHY: audit failure
            _safe_unlink(image_temp_path)  # WHY: clean up temp file on error
            return None  # WHY: signal failure without raising

    def _create_cloned_map(
        self,
        site_id: str,  # WHY: target Mist site
        clone_payload: dict[str, Any],  # WHY: payload prepared by _build_clone_payload
        image_temp_path: str | None,  # WHY: temp file cleaned up on failure
    ) -> str | None:
        """Call createSiteMap; clean up temp image on failure; return new map_id or None."""
        logging.info("Creating cloned map '%s' at site %s", clone_payload.get("name"), site_id)  # WHY: audit
        clone_response = self._state.mistapi_ref.api.v1.sites.maps.createSiteMap(  # WHY: Mist API write
            self._state.api_session_ref, site_id=site_id, body=clone_payload
        )
        logging.debug("createSiteMap status_code=%s", getattr(clone_response, "status_code", "?"))  # WHY: diagnostic
        if clone_response.status_code not in _OK_STATUSES:  # WHY: accept 200 or 201
            logging.error("Clone failed: Could not create map - HTTP %s", clone_response.status_code)  # WHY: audit
            _safe_unlink(image_temp_path)  # WHY: cleanup orphaned temp file
            return None  # WHY: signal failure
        cloned_map = clone_response.data  # WHY: parsed payload of the new map
        cloned_map_id: str | None = cloned_map.get("id")  # WHY: new map's UUID
        logging.info("Cloned map created: %s", cloned_map_id)  # WHY: audit success
        return cloned_map_id  # WHY: hand ID to caller

    def _upload_clone_image(self, site_id: str, cloned_map_id: str, image_temp_path: str | None) -> bool:
        """Upload the temp image to the cloned map; always remove temp file on exit."""
        if not image_temp_path or not os.path.exists(image_temp_path):  # WHY: nothing to upload
            return False  # WHY: signal skipped upload
        try:
            return self._do_image_upload(site_id, cloned_map_id, image_temp_path)  # WHY: guarded upload
        finally:
            _safe_unlink(image_temp_path)  # WHY: always clean up temp file

    def _do_image_upload(self, site_id: str, cloned_map_id: str, image_temp_path: str) -> bool:
        """Invoke Mist ``addSiteMapImageFile`` and log outcome; return True on success."""
        try:
            logging.info("Uploading image to cloned map %s", cloned_map_id)  # WHY: audit start
            upload_response = self._state.mistapi_ref.api.v1.sites.maps.addSiteMapImageFile(  # WHY: Mist write
                self._state.api_session_ref,  # WHY: authenticated session
                site_id=site_id,  # WHY: scope to this site
                map_id=cloned_map_id,  # WHY: target the new map
                file=image_temp_path,  # WHY: upload the downloaded temp file
            )
            logging.debug(
                "addSiteMapImageFile status_code=%s", getattr(upload_response, "status_code", "?")
            )  # WHY: diag
            if upload_response.status_code in _OK_STATUSES:  # WHY: accept 200 or 201
                logging.info("Image uploaded to cloned map %s", cloned_map_id)  # WHY: audit success
                return True  # WHY: success path
            logging.warning("Image upload failed: HTTP %s", upload_response.status_code)  # WHY: audit non-200
            return False  # WHY: signal failure without raising
        except Exception as upload_err:  # noqa: BLE001 - preserve broad-except behavior
            logging.error("Error uploading image: %s", upload_err)  # WHY: audit failure
            return False  # WHY: never raise past callback boundary

    def _clone_zones_for_map(self, site_id: str, source_map_id: str, cloned_map_id: str) -> int:
        """Replicate each zone associated with source_map_id under cloned_map_id; return count cloned."""
        try:
            source_zones = self._fetch_source_zones(site_id, source_map_id)  # WHY: filtered zone list
        except Exception as zone_err:  # noqa: BLE001 - preserve original broad-except behavior
            logging.error("Zone cloning error: %s", zone_err)  # WHY: audit failure
            return 0  # WHY: skip cloning silently
        return sum(  # WHY: count of zones successfully created
            1 for zone in source_zones if self._clone_single_zone(site_id, cloned_map_id, zone)
        )

    def _fetch_source_zones(self, site_id: str, source_map_id: str) -> list[dict[str, Any]]:
        """List zones at ``site_id`` and return only those attached to ``source_map_id``."""
        logging.info("Listing zones at site %s to clone for map %s", site_id, source_map_id)  # WHY: audit
        zones_response = self._state.mistapi_ref.api.v1.sites.zones.listSiteZones(  # WHY: Mist API read
            self._state.api_session_ref, site_id=site_id
        )
        if zones_response.status_code != 200:  # WHY: cannot list zones => skip cloning silently
            logging.warning("Zone listing failed: HTTP %s", zones_response.status_code)  # WHY: audit
            return []  # WHY: empty list produces zero clones
        source_zones = [z for z in zones_response.data if z.get("map_id") == source_map_id]  # WHY: filter
        logging.debug("Found %d source zones to clone", len(source_zones))  # WHY: diagnostic
        return source_zones  # WHY: hand filtered list to caller

    def _clone_single_zone(self, site_id: str, cloned_map_id: str, zone: dict[str, Any]) -> bool:
        """Create one zone under cloned_map_id; return True on success."""
        try:
            zone_payload = self._build_zone_payload(cloned_map_id, zone)  # WHY: shape the create payload
            zone_response = self._state.mistapi_ref.api.v1.sites.zones.createSiteZone(  # WHY: Mist write
                self._state.api_session_ref, site_id=site_id, body=zone_payload
            )
            return zone_response.status_code in _OK_STATUSES  # WHY: accept 200 or 201
        except Exception:  # noqa: BLE001 - preserve original broad-except behavior
            return False  # WHY: never raise past caller boundary

    @staticmethod
    def _build_zone_payload(cloned_map_id: str, zone: dict[str, Any]) -> dict[str, Any]:
        """Shape the create-zone payload preserving optional ``type`` and ``z`` fields."""
        zone_payload: dict[str, Any] = {  # WHY: replicate the zone's identifying fields
            "name": zone.get("name", "Unnamed Zone"),  # WHY: default name when missing
            "map_id": cloned_map_id,  # WHY: attach to the newly created map
            "vertices": zone.get("vertices", []),  # WHY: preserve polygon vertices
        }
        for optional in ("type", "z"):  # WHY: preserve optional fields when present
            if optional in zone:  # WHY: only copy present keys
                zone_payload[optional] = zone[optional]  # WHY: verbatim copy
        return zone_payload  # WHY: caller passes to createSiteZone

    @staticmethod
    def _render_clone_success(
        new_name: str,  # WHY: user-facing cloned map name
        cloned_map_id: str,  # WHY: UUID of the newly created map
        image_uploaded: bool,  # WHY: whether image upload succeeded
        zones_cloned: int,  # WHY: count of successfully cloned zones
        current_trigger: int,  # WHY: current cache-bust counter to bump
    ) -> tuple[Any, Any]:
        """Build the success Span and incremented cache-bust dict for the clone callback."""
        from dash import html  # WHY: local import keeps module import-light

        result_parts = [f"Map '{new_name}' created successfully!"]  # WHY: always include base message
        if image_uploaded:  # WHY: append optional image facet
            result_parts.append("Image: uploaded")  # WHY: user-visible summary line
        if zones_cloned > 0:  # WHY: append optional zone facet
            result_parts.append(f"Zones: {zones_cloned} cloned")  # WHY: user-visible summary line
        logging.info(  # WHY: audit final summary
            "Clone complete: %s (ID: %s), image=%s, zones=%s",
            new_name,
            cloned_map_id,
            image_uploaded,
            zones_cloned,
        )
        new_cache_bust = {"trigger": current_trigger + 1}  # WHY: bump trigger to refresh dropdown
        span = html.Span(" | ".join(result_parts), style={"color": _SUCCESS_COLOR, "fontWeight": "bold"})  # WHY: green
        return (span, new_cache_bust)  # WHY: Dash callback expects (children, store-data)

    def register(self, app: Dash) -> None:  # WHY: hooks this wave's app.callback(...) blocks into Dash
        """Attach the clone-map callback in this cluster to ``app``."""
        from dash import Input, Output, State  # WHY: local import keeps module import-light

        app.callback(  # WHY: execute_clone_operation - full map+image+zones clone
            [
                Output("clone-status", "children"),  # WHY: status text/widget output
                Output("cache-bust-store", "data", allow_duplicate=True),  # WHY: bumps to refresh dropdown
            ],
            [Input("execute-clone-btn", "n_clicks")],  # WHY: triggered by the Execute Clone button
            [
                State("clone-name-input", "value"),  # WHY: new cloned-map name
                State("map-config-store", "data"),  # WHY: site_id/map_id source
                State("cache-bust-store", "data"),  # WHY: cache-bust counter
            ],
            prevent_initial_call=True,  # WHY: avoid initial render thrash
        )(self.execute_clone_operation)
