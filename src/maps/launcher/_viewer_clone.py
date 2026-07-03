"""Clone-map cluster extracted from ``viewer_callbacks.py``.

Owns the single Wave-E1 public callback ``execute_clone_operation`` plus
its 11 private helpers (input validation, source-map fetch, image
download/upload, per-zone clone, success rendering).  Follows the same
wrapper-class + ``__getattr__`` template used by
:mod:`src.capture._packet_capture_org` so the parent
:class:`~src.maps.launcher.viewer_callbacks.MapViewerCallbacks` stays a
thin coordinator that hands each Dash callback off to the appropriate
cluster.
"""

from __future__ import annotations  # WHY: postponed evaluation consistent with parent module

import logging  # WHY: audit trail for clone-operation diagnostics
from typing import TYPE_CHECKING, Any  # WHY: opaque manager + type-permissive Dash callback args

if TYPE_CHECKING:  # WHY: keep dash imports lazy at runtime
    from dash import Dash  # WHY: annotation reference for register(app)


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

    # ------------------------------------------------------------------
    # Extracted callback body + helpers (wave E1 clone-map cluster)
    # ------------------------------------------------------------------

    def execute_clone_operation(
        self,
        n_clicks: int,
        new_name: str | None,
        config: dict[str, Any] | None,
        cache_bust_data: dict[str, Any] | None,
    ) -> tuple[Any, Any]:
        """Clone the current map with all properties, image, and zones."""
        from dash import html, no_update  # Local import keeps module import-light

        current_trigger = cache_bust_data.get("trigger", 0) if cache_bust_data else 0  # Cache-bust counter

        validation = self._validate_clone_inputs(n_clicks, new_name, config)  # Reject early on bad input
        if len(validation) != 3:  # Validation returned an error tuple of length 2
            return validation
        new_name_clean, site_id_local, source_map_id = validation  # Unpack validated values

        logging.info(  # Audit start of clone op
            "Clone operation started - source: %s, new name: %s", source_map_id, new_name_clean
        )
        try:
            self._backup_before_clone(site_id_local, source_map_id, config or {})  # Safety net
            source_map = self._fetch_source_map(site_id_local, source_map_id)  # Step 1: fetch source
            if source_map is None:  # Source fetch failed
                return (
                    html.Span("! Failed to fetch source map", style={"color": "#ff4444"}),  # User-visible error
                    no_update,
                )
            return self._perform_clone(site_id_local, source_map_id, new_name_clean, source_map, current_trigger)
        except Exception as clone_error:  # noqa: BLE001 - preserve original broad-except behavior
            logging.exception("Clone operation failed: %s", clone_error)  # Capture stack trace
            return (
                html.Span(
                    "! Clone operation failed. Check server logs for details.",
                    style={"color": "#ff4444"},
                ),
                no_update,
            )

    @staticmethod
    def _validate_clone_inputs(
        n_clicks: int,
        new_name: str | None,
        config: dict[str, Any] | None,
    ) -> tuple[Any, Any] | tuple[str, str, str]:
        """Return error tuple on bad input, or (clean_name, site_id, map_id) on success."""
        from dash import html, no_update  # Local import keeps module import-light

        if not n_clicks:  # Button never clicked => silent no-op
            return ("", no_update)
        if not new_name or not new_name.strip():  # Required: non-empty cloned-map name
            return (
                html.Span("! Please enter a name for the cloned map", style={"color": "#ff4444"}),
                no_update,
            )
        new_name_clean = new_name.strip()  # Strip whitespace from user input
        site_id_local = config.get("site_id") if config else None  # Pull site_id from config store
        source_map_id = config.get("map_id") if config else None  # Pull source map_id from config store
        if not site_id_local or not source_map_id:  # Both required for the API calls
            return (
                html.Span("! Missing site or map configuration", style={"color": "#ff4444"}),
                no_update,
            )
        return (new_name_clean, site_id_local, source_map_id)  # All inputs validated

    def _backup_before_clone(self, site_id: str, source_map_id: str, config: dict[str, Any]) -> None:
        """Create a pre-clone geometry backup of the source map (best-effort)."""
        source_map_name = config.get("map_name", "Unknown")  # Display name for the backup file
        logging.info("Creating backup of source map '%s' before cloning", source_map_name)  # Audit trail
        backup_path = self._state.maps_manager_ref._backup_map_geometry(  # Call MapsManager helper
            api_session=self._state.api_session_ref,
            site_id=site_id,
            map_id=source_map_id,
            map_name=source_map_name,
            backup_reason="pre_clone",
        )
        if backup_path:  # Backup succeeded
            logging.info("Pre-clone backup saved: %s", backup_path)  # Path for operator recovery

    def _fetch_source_map(self, site_id: str, source_map_id: str) -> dict[str, Any] | None:
        """Fetch the source map record from Mist; return None on failure."""
        logging.info("Fetching source map %s for clone", source_map_id)  # Audit start
        source_response = self._state.mistapi_ref.api.v1.sites.maps.getSiteMap(  # Mist API read
            self._state.api_session_ref, site_id=site_id, map_id=source_map_id
        )
        logging.debug("Source map fetch status_code=%s", getattr(source_response, "status_code", "?"))
        if source_response.status_code != 200:  # Non-200 means we cannot proceed
            logging.error("Clone failed: Could not fetch source map - HTTP %s", source_response.status_code)
            return None
        data: dict[str, Any] = source_response.data  # Parsed JSON payload of the source map
        return data

    def _perform_clone(
        self,
        site_id: str,
        source_map_id: str,
        new_name: str,
        source_map: dict[str, Any],
        current_trigger: int,
    ) -> tuple[Any, Any]:
        """Run steps 2-6 of the clone workflow (payload, image, create, upload, zones)."""
        from dash import html, no_update  # Local import keeps module import-light

        clone_payload = self._build_clone_payload(source_map, new_name)  # Step 2: build payload
        image_temp_path = self._download_source_image(source_map)  # Step 3: download image (best-effort)
        cloned_map_id = self._create_cloned_map(site_id, clone_payload, image_temp_path)  # Step 4: create
        if cloned_map_id is None:  # Map creation failed
            return (
                html.Span("! Failed to create cloned map", style={"color": "#ff4444"}),
                no_update,
            )
        image_uploaded = self._upload_clone_image(site_id, cloned_map_id, image_temp_path)  # Step 5: upload
        zones_cloned = self._clone_zones_for_map(site_id, source_map_id, cloned_map_id)  # Step 6: zones
        return self._render_clone_success(new_name, cloned_map_id, image_uploaded, zones_cloned, current_trigger)

    @staticmethod
    def _build_clone_payload(source_map: dict[str, Any], new_name: str) -> dict[str, Any]:
        """Assemble the full clone payload preserving dimensional + location + path props."""
        clone_payload: dict[str, Any] = {"name": new_name, "type": source_map.get("type", "image")}  # Base payload
        # Property groups copied byte-identically from the source map (order preserved from original)
        for prop in ["width", "height", "height_m", "ppm", "orientation"]:  # Dimensional properties
            if prop in source_map:
                clone_payload[prop] = source_map[prop]
        for prop in ["latlng", "latlng_br", "origin_x", "origin_y"]:  # Geo / origin properties
            if prop in source_map:
                clone_payload[prop] = source_map[prop]
        for prop in ["wayfinding", "wayfinding_path", "wall_path", "sitesurvey_path"]:  # Path properties
            if prop in source_map:
                clone_payload[prop] = source_map[prop]
        for prop in ["occupancy_limit", "locked", "view"]:  # Misc settings
            if prop in source_map:
                clone_payload[prop] = source_map[prop]
        logging.debug("Clone payload prepared with %d properties", len(clone_payload))  # Diagnostic
        return clone_payload  # Caller passes to createSiteMap

    @staticmethod
    def _download_source_image(source_map: dict[str, Any]) -> str | None:
        """Download the source map image to a temp file; return path or None on any failure."""
        if "url" not in source_map:  # No image to download
            return None
        import os  # Local import keeps module import-light
        import tempfile  # Local import keeps module import-light

        import requests  # Local import: external HTTP dep only needed at call time

        image_temp_path: str | None = None  # Final temp file path (set below)
        try:
            image_url = source_map["url"]  # URL of the source map image
            file_ext = ".png"  # Default extension if URL lacks one
            if "." in image_url:  # Try to infer the real extension
                url_ext = image_url.rsplit(".", 1)[-1].split("?")[0]
                if url_ext.lower() in ["png", "jpg", "jpeg", "gif", "svg"]:
                    file_ext = f".{url_ext.lower()}"
            temp_fd, image_temp_path = tempfile.mkstemp(suffix=file_ext)  # Create temp file
            os.close(temp_fd)  # Close fd; we'll reopen via path
            logging.info("Downloading source map image from %s", image_url)  # Audit start
            response = requests.get(image_url, timeout=60)  # 60s timeout matches original
            if response.status_code == 200:  # Success: write bytes to temp file
                with open(image_temp_path, "wb") as fh:
                    fh.write(response.content)
                logging.info("Downloaded source map image (%.1f KB)", len(response.content) / 1024)
                return image_temp_path
            logging.warning("Failed to download image: HTTP %s", response.status_code)  # Non-200
            if image_temp_path and os.path.exists(image_temp_path):
                os.remove(image_temp_path)
            return None
        except Exception as img_err:  # noqa: BLE001 - preserve broad-except behavior
            logging.error("Error downloading image: %s", img_err)  # Audit failure
            if image_temp_path and os.path.exists(image_temp_path):
                os.remove(image_temp_path)
            return None

    def _create_cloned_map(
        self, site_id: str, clone_payload: dict[str, Any], image_temp_path: str | None
    ) -> str | None:
        """Call createSiteMap; clean up temp image on failure; return new map_id or None."""
        import os  # Local import keeps module import-light

        logging.info("Creating cloned map '%s' at site %s", clone_payload.get("name"), site_id)  # Audit
        clone_response = self._state.mistapi_ref.api.v1.sites.maps.createSiteMap(  # Mist API write
            self._state.api_session_ref, site_id=site_id, body=clone_payload
        )
        logging.debug("createSiteMap status_code=%s", getattr(clone_response, "status_code", "?"))
        if clone_response.status_code not in [200, 201]:  # Created or OK accepted
            logging.error("Clone failed: Could not create map - HTTP %s", clone_response.status_code)
            if image_temp_path and os.path.exists(image_temp_path):  # Cleanup orphaned temp file
                os.remove(image_temp_path)
            return None
        cloned_map = clone_response.data  # Parsed payload of the new map
        cloned_map_id: str | None = cloned_map.get("id")  # New map's UUID
        logging.info("Cloned map created: %s", cloned_map_id)  # Audit success
        return cloned_map_id

    def _upload_clone_image(self, site_id: str, cloned_map_id: str, image_temp_path: str | None) -> bool:
        """Upload the temp image to the cloned map; always remove temp file on exit."""
        if not image_temp_path:  # No image was downloaded
            return False
        import os  # Local import keeps module import-light

        if not os.path.exists(image_temp_path):  # Defensive: temp file missing
            return False
        image_uploaded = False  # Track outcome for status message
        try:
            logging.info("Uploading image to cloned map %s", cloned_map_id)  # Audit start
            upload_response = self._state.mistapi_ref.api.v1.sites.maps.addSiteMapImageFile(
                self._state.api_session_ref,
                site_id=site_id,
                map_id=cloned_map_id,
                file=image_temp_path,
            )
            logging.debug("addSiteMapImageFile status_code=%s", getattr(upload_response, "status_code", "?"))
            if upload_response.status_code in [200, 201]:  # Success codes
                image_uploaded = True
                logging.info("Image uploaded to cloned map %s", cloned_map_id)  # Audit success
            else:
                logging.warning("Image upload failed: HTTP %s", upload_response.status_code)
        except Exception as upload_err:  # noqa: BLE001 - preserve broad-except behavior
            logging.error("Error uploading image: %s", upload_err)  # Audit failure
        finally:
            if os.path.exists(image_temp_path):  # Always clean up temp file
                os.remove(image_temp_path)
        return image_uploaded

    def _clone_zones_for_map(self, site_id: str, source_map_id: str, cloned_map_id: str) -> int:
        """Replicate each zone associated with source_map_id under cloned_map_id; return count cloned."""
        zones_cloned = 0  # Successful zone-create count
        try:
            logging.info("Listing zones at site %s to clone for map %s", site_id, source_map_id)  # Audit
            zones_response = self._state.mistapi_ref.api.v1.sites.zones.listSiteZones(
                self._state.api_session_ref, site_id=site_id
            )
            if zones_response.status_code != 200:  # Cannot list zones => skip cloning silently
                logging.warning("Zone listing failed: HTTP %s", zones_response.status_code)
                return 0
            source_zones = [z for z in zones_response.data if z.get("map_id") == source_map_id]  # Filter
            logging.debug("Found %d source zones to clone", len(source_zones))  # Diagnostic
            for zone in source_zones:  # Replicate each one
                if self._clone_single_zone(site_id, cloned_map_id, zone):
                    zones_cloned += 1
        except Exception as zone_err:  # noqa: BLE001 - preserve original broad-except behavior
            logging.error("Zone cloning error: %s", zone_err)  # Audit failure
        return zones_cloned

    def _clone_single_zone(self, site_id: str, cloned_map_id: str, zone: dict[str, Any]) -> bool:
        """Create one zone under cloned_map_id; return True on success."""
        try:
            zone_payload: dict[str, Any] = {  # Replicate the zone's identifying fields
                "name": zone.get("name", "Unnamed Zone"),
                "map_id": cloned_map_id,
                "vertices": zone.get("vertices", []),
            }
            if "type" in zone:  # Preserve optional fields when present
                zone_payload["type"] = zone["type"]
            if "z" in zone:
                zone_payload["z"] = zone["z"]
            zone_response = self._state.mistapi_ref.api.v1.sites.zones.createSiteZone(
                self._state.api_session_ref, site_id=site_id, body=zone_payload
            )
            return zone_response.status_code in [200, 201]  # Created or OK
        except Exception:  # noqa: BLE001 - preserve original broad-except behavior
            return False

    @staticmethod
    def _render_clone_success(
        new_name: str,
        cloned_map_id: str,
        image_uploaded: bool,
        zones_cloned: int,
        current_trigger: int,
    ) -> tuple[Any, Any]:
        """Build the success Span and incremented cache-bust dict for the clone callback."""
        from dash import html  # Local import keeps module import-light

        result_parts = [f"Map '{new_name}' created successfully!"]  # Always include base message
        if image_uploaded:  # Append optional facets
            result_parts.append("Image: uploaded")
        if zones_cloned > 0:
            result_parts.append(f"Zones: {zones_cloned} cloned")
        logging.info(  # Audit final summary
            "Clone complete: %s (ID: %s), image=%s, zones=%s",
            new_name,
            cloned_map_id,
            image_uploaded,
            zones_cloned,
        )
        new_cache_bust = {"trigger": current_trigger + 1}  # Bump trigger to refresh dropdown
        return (
            html.Span(" | ".join(result_parts), style={"color": "#00ff88", "fontWeight": "bold"}),
            new_cache_bust,
        )

    # ------------------------------------------------------------------
    # Callback wiring
    # ------------------------------------------------------------------

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
