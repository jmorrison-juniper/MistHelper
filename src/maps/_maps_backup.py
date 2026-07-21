"""Map geometry backup helpers extracted from MapsManager.

Split out of ``src/maps/maps_manager.py`` so the geometry-backup flow
lives in its own module. Callers construct a :class:`BackupRequest`
and hand it to :func:`backup_map_geometry`; the module also fixes the
missing ``os`` import the original class-based version silently relied
on. MapsManager keeps a thin ``_backup_map_geometry`` delegating method
because ``src/maps/launcher/viewer_callbacks.py`` invokes it through
``maps_manager_ref._backup_map_geometry(...)`` and tests stub it on
the MapsManager class.
"""

from __future__ import annotations  # WHY: postponed annotation evaluation

import json  # WHY: JSON serialization of the backup document
import logging  # WHY: audit trail for backup operations
import os  # WHY: filesystem path handling for backup files
from collections.abc import Callable  # WHY: modern typing home for callable protocol
from dataclasses import dataclass  # WHY: frozen slots BackupRequest declaration
from datetime import datetime  # WHY: timestamp formatting for filenames + metadata
from typing import Any  # WHY: opaque API session / dict payload typing

import mistapi  # WHY: Mist API client for site/map endpoints
import requests  # WHY: HTTP client for map image downloads

logger = logging.getLogger(__name__)  # WHY: module-scoped logger

_DATA_SUBDIR = "data"  # WHY: sibling folder that holds every backup artefact
_ALLOWED_IMG_EXTS = ("png", "jpg", "jpeg", "gif", "svg", "webp")  # WHY: whitelist of image extensions
_DEFAULT_EXT = ".png"  # WHY: fallback extension when URL lacks a recognizable one
_SAFE_CHARS: tuple[str, ...] = (" ", "-", "_")  # WHY: filename-safe non-alphanumeric characters
_MAX_NAME_LEN = 50  # WHY: cap on sanitized map name segment length
_TIMESTAMP_FMT = "%Y%m%d_%H%M%S"  # WHY: uniform timestamp format across filenames
_IMG_TIMEOUT_SECS = 60  # WHY: bounded image download HTTP timeout
_HTTP_OK = 200  # WHY: only accept 200 responses from Mist / image hosts

_MAP_PROP_KEYS: tuple[str, ...] = (  # WHY: table-driven snapshot of map-level properties
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
)

_DEVICE_PLACEMENT_FIELDS: tuple[str, ...] = (  # WHY: fields retained for each device placement
    "id",
    "name",
    "mac",
    "type",
    "model",
    "map_id",
    "x",
    "y",
    "orientation",
    "height",
)


@dataclass(frozen=True, slots=True)  # WHY: aggregate 5 params into a single value object
class BackupRequest:  # WHY: parameter-object collapses call surface
    """Parameters describing a single geometry-backup request."""

    api_session: Any  # WHY: opaque authenticated Mist session handle
    site_id: str  # WHY: Mist site scope for the backup
    map_id: str  # WHY: identifies the map being backed up
    map_name: str  # WHY: friendly name embedded in filenames + metadata
    backup_reason: str = "manual"  # WHY: audit tag such as pre_clone / pre_delete


def _safe_name(map_name: str) -> str:  # WHY: sanitize an arbitrary name for the filesystem
    """Return a filesystem-safe, length-capped variant of ``map_name``."""
    cleaned = "".join(  # WHY: replace anything not in the whitelist with underscore
        c if c.isalnum() or c in _SAFE_CHARS else "_" for c in map_name
    )
    return cleaned.strip().replace(" ", "_")[:_MAX_NAME_LEN]  # WHY: trim + underscore-join


def _timestamp() -> str:  # WHY: single source for backup timestamp formatting
    """Return the current time formatted for use inside filenames."""
    return datetime.now().strftime(_TIMESTAMP_FMT)  # WHY: uniform timestamp representation


def _data_dir() -> str:  # WHY: ensure and return the backup output directory
    """Ensure the data directory exists and return its absolute path."""
    path = os.path.join(os.getcwd(), _DATA_SUBDIR)  # WHY: sibling data/ folder under CWD
    os.makedirs(path, exist_ok=True)  # WHY: idempotent directory creation
    return path  # WHY: caller writes artefacts under this directory


def _image_ext(url: str) -> str:  # WHY: derive image extension without exceptions
    """Return a supported image extension parsed from ``url``, else the default."""
    if "." not in url:  # WHY: no dot means no inferrable extension
        return _DEFAULT_EXT
    ext = url.rsplit(".", 1)[-1].split("?")[0].lower()  # WHY: strip query-string, normalize case
    return f".{ext}" if ext in _ALLOWED_IMG_EXTS else _DEFAULT_EXT  # WHY: guard against unknown ext


def _http_get_bytes(url: str) -> tuple[bytes | None, int]:  # WHY: isolate HTTP call from callers
    """GET ``url`` and return ``(content-or-None, status_code)``."""
    try:  # WHY: network I/O may raise; caller wants graceful fallback
        response = requests.get(url, timeout=_IMG_TIMEOUT_SECS)  # WHY: bounded network wait
    except Exception as err:  # WHY: any failure downgrades to warn + skip
        logger.warning("Image backup failed: %s", err)  # WHY: surface reason to operator
        return None, 0  # WHY: sentinel indicating no HTTP round-trip happened
    ok = response.status_code == _HTTP_OK  # WHY: only 200 payload counts as usable content
    return (response.content if ok else None), response.status_code  # WHY: hand back both


def _write_image(filename: str, content: bytes) -> None:  # WHY: persist downloaded image
    """Write ``content`` under the data directory as ``filename`` and log size."""
    path = os.path.join(_data_dir(), filename)  # WHY: absolute destination path
    with open(path, "wb") as img_file:  # WHY: binary write mode preserves bytes
        img_file.write(content)
    logger.info("Map image backed up: %s (%.1f KB)", filename, len(content) / 1024)  # WHY: audit


def _download_image(
    map_data: dict[str, Any], map_name: str, reason: str
) -> tuple[str | None, tuple[str, str] | None]:  # WHY: orchestrate image download
    """Download the map image; return ``(filename, (safe_name, timestamp))`` or ``(None, None)``."""
    url = map_data.get("url")  # WHY: image URL is optional in the map record
    if not url:  # WHY: no URL means nothing to download
        return None, None
    safe_name = _safe_name(map_name)  # WHY: reused for the JSON filename downstream
    stamp = _timestamp()  # WHY: reused for the JSON filename downstream
    filename = f"map_backup_{safe_name}_{reason}_{stamp}{_image_ext(url)}"  # WHY: filesystem-safe name
    content, status = _http_get_bytes(url)  # WHY: single HTTP round-trip
    if content is None:  # WHY: download failed or non-200
        if status:  # WHY: only log HTTP status when a request actually completed
            logger.warning("Could not download map image: HTTP %s", status)
        return None, None
    _write_image(filename, content)  # WHY: side-effect write to disk
    return filename, (safe_name, stamp)  # WHY: caller reuses these for JSON pairing


def _call_api(  # WHY: encapsulate try/except around a Mist listSite* call
    api_call: Callable[..., Any], api_session: Any, site_id: str, label: str
) -> Any | None:
    """Invoke ``api_call`` and return the response or ``None`` on exception."""
    try:  # WHY: fetch is best-effort; caller degrades gracefully
        return api_call(api_session, site_id=site_id)  # WHY: shared site-scoped signature
    except Exception as err:  # WHY: swallow to keep the backup usable
        logger.debug("%s backup skipped: %s", label, err)  # WHY: diagnostic trace only
        return None


def _response_items(response: Any, label: str) -> list[Any] | None:  # WHY: normalize API response body
    """Return ``response.data`` as a list, ``None`` when response is unusable."""
    if response is None:  # WHY: exception path already logged
        return None
    if response.status_code != _HTTP_OK:  # WHY: guard non-OK response
        logger.warning("Could not fetch %s for backup: HTTP %s", label, response.status_code)
        return None
    return response.data if isinstance(response.data, list) else []  # WHY: defensive list check


def _fetch_items(  # WHY: generic fetch + filter for zones / beacons / vbeacons
    request: BackupRequest, api_call: Callable[..., Any], label: str
) -> list[Any]:
    """Fetch items via ``api_call`` and return those tied to ``request.map_id``."""
    response = _call_api(api_call, request.api_session, request.site_id, label)  # WHY: safe invocation
    items = _response_items(response, label)  # WHY: unified None/status handling
    if items is None:  # WHY: response failed or non-OK
        return []
    hits = [item for item in items if item.get("map_id") == request.map_id]  # WHY: filter to this map
    logger.debug("Backup includes %s %s for map %s", len(hits), label, request.map_id)  # WHY: audit
    return hits


def _fetch_devices(request: BackupRequest) -> Any | None:  # WHY: wrap listSiteDevices exception path
    """Fetch site-device response object; returns ``None`` on error."""
    try:  # WHY: network I/O may raise; caller wants graceful fallback
        return mistapi.api.v1.sites.devices.listSiteDevices(  # WHY: Mist API listing
            request.api_session, site_id=request.site_id, type="all"
        )
    except Exception as err:  # WHY: any failure downgrades to warn + skip
        logger.warning("Device placement backup failed: %s", err)  # WHY: surface reason
        return None


def _placement_row(device: dict[str, Any]) -> dict[str, Any]:  # WHY: shape a single placement
    """Return the placement snapshot for one device."""
    return {key: device.get(key) for key in _DEVICE_PLACEMENT_FIELDS}  # WHY: table-driven fields


def _is_mapped_placement(device: dict[str, Any], map_id: str) -> bool:  # WHY: placement filter predicate
    """Return True when ``device`` belongs to ``map_id`` and has coordinates."""
    return device.get("map_id") == map_id and ("x" in device or "y" in device)


def _fetch_device_placements(request: BackupRequest) -> list[dict[str, Any]]:  # WHY: build placement list
    """Return device placement snapshots for ``request.map_id``."""
    response = _fetch_devices(request)  # WHY: encapsulated try/except
    devices = _response_items(response, "devices")  # WHY: unified None/status handling
    if devices is None:  # WHY: response failed or non-OK
        return []
    hits = [_placement_row(d) for d in devices if _is_mapped_placement(d, request.map_id)]
    logger.debug("Backup includes %s device placements for map %s", len(hits), request.map_id)
    return hits


def _write_backup(  # WHY: persist final backup document to disk
    backup: dict[str, Any], map_name: str, reason: str, name_ts: tuple[str, str] | None
) -> tuple[str, str]:
    """Write ``backup`` as JSON; return ``(absolute_path, filename)``."""
    safe_name, stamp = name_ts if name_ts else (_safe_name(map_name), _timestamp())  # WHY: reuse image stamp
    filename = f"map_backup_{safe_name}_{reason}_{stamp}.json"  # WHY: matches image filename layout
    path = os.path.join(_data_dir(), filename)  # WHY: absolute destination path
    with open(path, "w", encoding="utf-8") as backup_file:  # WHY: text-mode UTF-8 write
        json.dump(backup, backup_file, indent=2, ensure_ascii=False)  # WHY: pretty JSON for humans
    return path, filename


def _count_nodes(backup: dict[str, Any], path_key: str) -> int | None:  # WHY: geometry-path node count
    """Return the node count for ``path_key`` or ``None`` if zero/missing."""
    geometry = backup.get("geometry") or {}  # WHY: geometry section may be absent
    nodes = geometry.get(path_key, {}).get("nodes", [])  # WHY: default empty list for missing keys
    return len(nodes) or None  # WHY: 0 collapses to None so summary hides empty entries


def _count_list(backup: dict[str, Any], key: str) -> int | None:  # WHY: top-level list count
    """Return the length of ``backup[key]`` or ``None`` if the list is empty."""
    return len(backup.get(key, [])) or None  # WHY: 0 collapses to None for summary formatting


_SUMMARY_ROWS: tuple[tuple[str, Callable[[dict[str, Any]], int | None]], ...] = (  # WHY: table-driven rows
    ("Walls", lambda b: _count_nodes(b, "wall_path")),
    ("Wayfinding", lambda b: _count_nodes(b, "wayfinding_path")),
    ("Zones", lambda b: _count_list(b, "zones")),
    ("Devices", lambda b: _count_list(b, "device_placements")),
    ("Beacons", lambda b: _count_list(b, "beacons")),
    ("VBeacons", lambda b: _count_list(b, "vbeacons")),
)


def _summary_rows(backup: dict[str, Any], image_filename: str | None) -> list[tuple[str, Any]]:
    """Return the (label, value) pairs feeding the summary string."""
    rows: list[tuple[str, Any]] = [("Image", "Yes" if image_filename else None)]  # WHY: image row first
    rows.extend((label, fn(backup)) for label, fn in _SUMMARY_ROWS)  # WHY: table-driven remaining rows
    return rows


def _format_summary_rows(rows: list[tuple[str, Any]]) -> str:  # WHY: render rows into summary text
    """Join populated (label, value) rows into a comma-separated summary."""
    populated = [f"{label}: {value}" for label, value in rows if value]  # WHY: drop falsy entries
    return ", ".join(populated) or "Empty map"  # WHY: fallback for empty maps


def _build_summary(backup: dict[str, Any], image_filename: str | None) -> str:  # WHY: assemble summary line
    """Return a comma-separated summary of populated backup sections."""
    return _format_summary_rows(_summary_rows(backup, image_filename))  # WHY: rows + render pipeline


def _print_summary(  # WHY: user-visible backup summary output
    backup_filename: str, image_filename: str | None, backup: dict[str, Any]
) -> None:
    """Log and print a human-readable summary of the backup contents."""
    summary = _build_summary(backup, image_filename)  # WHY: single source of formatted counts
    logger.info("Map backup saved: %s (%s)", backup_filename, summary)  # WHY: structured audit log
    # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
    logger.info("\n   [*] Map backup saved: %s", backup_filename)
    if image_filename:  # WHY: only show image line when there is one
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.info("       Image: %s", image_filename)
    # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
    logger.info("       %s", summary)


def _fetch_map(request: BackupRequest) -> dict[str, Any] | None:  # WHY: fetch base map data
    """Fetch the base map record; return dict payload or ``None`` on failure."""
    response = mistapi.api.v1.sites.maps.getSiteMap(  # WHY: Mist API read for map record
        request.api_session, site_id=request.site_id, map_id=request.map_id
    )
    if response.status_code != _HTTP_OK:  # WHY: non-200 means backup cannot proceed
        logger.error("Map backup failed: Could not fetch map data - HTTP %s", response.status_code)
        return None
    data: dict[str, Any] = response.data  # WHY: parsed JSON payload of the map
    return data


def _base_backup(request: BackupRequest, map_data: dict[str, Any]) -> dict[str, Any]:  # WHY: initial skeleton
    """Build the initial backup dict from request context and fetched map data."""
    return {  # WHY: three-section skeleton matches restore contract
        "backup_info": {
            "timestamp": datetime.now().isoformat(),
            "reason": request.backup_reason,
            "map_id": request.map_id,
            "map_name": request.map_name,
            "site_id": request.site_id,
        },
        "map_properties": {key: map_data.get(key) for key in _MAP_PROP_KEYS},
        "geometry": {
            "wall_path": map_data.get("wall_path"),
            "wayfinding_path": map_data.get("wayfinding_path"),
            "wayfinding": map_data.get("wayfinding"),
            "sitesurvey_path": map_data.get("sitesurvey_path"),
        },
    }


_RELATED_ITEM_FETCHERS: tuple[tuple[str, Callable[..., Any]], ...] = (  # WHY: table-driven related fetches
    ("zones", mistapi.api.v1.sites.zones.listSiteZones),
    ("beacons", mistapi.api.v1.sites.beacons.listSiteBeacons),
    ("vbeacons", mistapi.api.v1.sites.vbeacons.listSiteVBeacons),
)


def _populate_related(backup: dict[str, Any], request: BackupRequest) -> None:  # WHY: attach related lists
    """Populate device placements plus zones/beacons/vbeacons into ``backup``."""
    backup["device_placements"] = _fetch_device_placements(request)  # WHY: dedicated device-fetch path
    for key, api_call in _RELATED_ITEM_FETCHERS:  # WHY: table-driven expansion
        backup[key] = _fetch_items(request, api_call, key)


def _perform_backup(request: BackupRequest) -> str | None:  # WHY: end-to-end backup pipeline
    """Run the full backup pipeline; return the JSON backup path or ``None``."""
    logger.info(  # WHY: audit start of the pipeline
        "Map geometry backup initiated - map: %s (%s), reason: %s",
        request.map_name,
        request.map_id,
        request.backup_reason,
    )
    map_data = _fetch_map(request)  # WHY: fetch base map payload
    if map_data is None:  # WHY: unable to fetch base map -> abort
        return None
    backup = _base_backup(request, map_data)  # WHY: build initial skeleton
    image_filename, name_ts = _download_image(map_data, request.map_name, request.backup_reason)
    if image_filename:  # WHY: record image filename in backup metadata
        backup["backup_info"]["image_file"] = image_filename
    _populate_related(backup, request)  # WHY: attach device/zone/beacon lists
    path, filename = _write_backup(backup, request.map_name, request.backup_reason, name_ts)  # WHY: persist
    _print_summary(filename, image_filename, backup)  # WHY: user-visible summary
    return path


def backup_map_geometry(request: BackupRequest) -> str | None:  # WHY: public entry point
    """Backup map geometry data to a JSON file; return path on success or ``None``."""
    try:  # WHY: pipeline may raise; wrapper degrades to warning
        return _perform_backup(request)
    except Exception as err:  # WHY: any failure surfaces as warning, not crash
        logger.exception("Map geometry backup failed: %s", err)  # WHY: full traceback in log
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        logger.warning("\n   [!] Warning: Could not backup map geometry: %s", err)
        return None
