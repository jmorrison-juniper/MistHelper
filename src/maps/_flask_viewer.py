"""Flask-based interactive map viewer (extracted from MapsManager).

Split out of ``src/maps/maps_manager.py`` so the enormous embedded HTML
template + Flask route wiring lives in a dedicated file. The launcher
takes explicit callables for the map-payload/response builders so the
module stays independent of MapsManager and easy to test.

SECURITY: :func:`_resolve_flask_bind_address` binds 0.0.0.0 only when
the container heuristics fire. Direct execution stays on localhost.
"""

from __future__ import annotations  # WHY: enable postponed annotations for slotted dataclasses referencing Callable.

import logging  # WHY: structured server-side logs for the Flask viewer route handlers.
from collections.abc import Callable  # WHY: modern Callable import location per ruff UP035.
from dataclasses import dataclass  # WHY: frozen slotted bundles collapse wide signatures below the 5-param limit.
from typing import Any  # WHY: precise typing for injected callables + site/map dict payloads.

import mistapi  # type: ignore[import-untyped]  # WHY: Mist SDK is the source of truth for site maps + image URLs.

from src.maps._browser_opener import (
    DelayedBrowserOpener,
)  # WHY: one stoppable opener replaces the daemon thread that no caller joined.
from src.maps._container_detection import is_running_in_container  # WHY: gate 0.0.0.0 bind to container envs only.

logger = logging.getLogger(__name__)  # WHY: module-scoped logger keeps route-handler emissions grouped in logs.

_DEFAULT_FLASK_PORT = 8050  # WHY: fixed default port matches the pre-refactor behaviour for existing operators.
_LOCALHOST_BIND = "127.0.0.1"  # WHY: bind loopback outside containers so Windows Firewall does not flag the process.
_CONTAINER_BIND = "0.0.0.0"  # nosec B104 - container must bind all interfaces to reach host browser.
_HTTP_OK = 200  # WHY: named status keeps route handlers readable without magic numbers.
_HTTP_NOT_FOUND = 404  # WHY: named status makes 404 branches self-documenting for reviewers.
_HTTP_SERVER_ERROR = 500  # WHY: named status keeps 500 fallbacks obvious in the diff.
_IMAGE_REQUEST_TIMEOUT_S = 30  # WHY: bounded HTTP GET prevents the map-image proxy from hanging Flask worker threads.
_BROWSER_OPEN_DELAY_S = 1.5  # WHY: small delay lets Flask finish binding before the browser hits localhost.
_DEFAULT_IMAGE_MIMETYPE = "image/png"  # WHY: matches Mist floorplan default so downstream <img> tags render correctly.
_UNNAMED = "Unnamed"  # WHY: shared placeholder label when a site/map lacks a name in the API response.
_ERR_MAP_NOT_FOUND = "Map not found"  # WHY: reused string keeps 404 payloads consistent across endpoints.
_ERR_NO_IMAGE_URL = "No image URL"  # WHY: reused string surfaces Mist map records missing an image URL field.
_ERR_MAP_DATA_FAILED = "Failed to fetch map data. Check server logs for details."  # WHY: friendly generic 500 body.
_ERR_MAPS_LIST_FAILED = "Failed to fetch maps. Check server logs for details."  # WHY: friendly 500 for site maps list.
_ERR_MAP_IMAGE_FAILED = (
    "Failed to fetch map image. Check server logs for details."  # WHY: friendly 500 for image proxy.
)
_TOKEN_ATTR = "_api_token"  # nosec B105 - The value is the mistapi attribute name, not a token value.
_AUTHORIZATION_HEADER = "Authorization"  # WHY: exposes header key so proxies + tests do not repeat the literal.
_CONTENT_TYPE_HEADER = "Content-Type"  # WHY: response-header key reused between fetch + proxy paths.
_ROUTE_INDEX = "/"  # WHY: canonical index route so dispatch table matches the mounted Flask endpoints.
_ROUTE_SITE_MAPS = "/api/site/<site_id>/maps"  # WHY: keep the maps-list URL definition close to the handler.
_ROUTE_MAP_IMAGE = "/api/map-image/<site_id>/<map_id>"  # WHY: image proxy path used by the front-end <img> tag.
_ROUTE_MAP_DATA = "/api/map/<site_id>/<map_id>"  # WHY: JSON payload path fetched by Plotly renderMap() calls.


@dataclass(frozen=True, slots=True)
class MapDataRequest:  # WHY: bundles the six inputs the map-data endpoint needs under one param.
    """Frozen bundle carrying every input needed to serve the /api/map endpoint."""

    api_session: Any  # WHY: mistapi session ferried in from the CLI/entry point (untyped SDK object).
    all_sites: list[dict]  # WHY: pre-fetched site list to enrich the response with site names.
    site_id: str  # WHY: identifies which Mist site owns the requested map.
    map_id: str  # WHY: identifies which map record inside the site to render.
    collect_payload_fn: Callable  # WHY: MapsManager-provided callable that gathers entities on the map.
    build_response_fn: Callable  # WHY: MapsManager-provided callable that shapes the JSON envelope.


@dataclass(frozen=True, slots=True)
class ViewerPageContext:  # WHY: keeps the root-page renderer at a single-parameter signature.
    """Frozen bundle for the root page render -- keeps ``_render_viewer_page`` at 5 params."""

    json_module: Any  # WHY: injected ``json`` module so the renderer can be tested with a stub encoder.
    render_template_string: Callable  # WHY: Flask's Jinja renderer -- injected so tests can substitute a stub.
    initial_site_id: str  # WHY: preselected site for the dropdown on first paint.
    initial_map_id: str  # WHY: preselected map for the dropdown on first paint.
    all_sites: list[dict]  # WHY: full site list rendered into the sidebar dropdown.
    all_maps: list[dict]  # WHY: initial site's map list rendered into the sidebar dropdown.


@dataclass(frozen=True, slots=True)
class FlaskViewerContext:  # WHY: single-param bundle for launch_flask_viewer's public entry point.
    """Frozen bundle carrying every input required by :func:`launch_flask_viewer`."""

    api_session: Any  # WHY: mistapi session shared with every route handler for authenticated calls.
    initial_site_id: str  # WHY: initial dropdown selection on the root page.
    initial_map_id: str  # WHY: initial dropdown selection on the root page.
    all_sites: list[dict]  # WHY: full site list injected into the initial HTML page.
    all_maps: list[dict]  # WHY: initial site's map list injected into the initial HTML page.
    collect_payload_fn: Callable  # WHY: MapsManager-bound method that assembles /api/map JSON payloads.
    build_response_fn: Callable  # WHY: MapsManager-bound method that finalises /api/map JSON responses.


def _summarise_named_records(records: list[dict]) -> list[dict]:  # WHY: dropdown payload shared across handlers.
    """Return only ``id``/``name`` pairs from each record. Used for both site + map dropdowns."""
    return [{"id": r.get("id"), "name": r.get("name", _UNNAMED)} for r in records]  # WHY: minimal dropdown payload.


def _handle_map_data_request(request: MapDataRequest):  # WHY: single orchestrator for the /api/map endpoint.
    """Top-level orchestrator for the Flask /api/map endpoint. Returns a Flask Response."""
    from flask import jsonify  # WHY: local import keeps this module importable without Flask installed globally.

    logging.info("[Flask API] Fetching map data for site %s, map %s", request.site_id, request.map_id)  # WHY: trace.
    try:
        map_data, layers = request.collect_payload_fn(  # WHY: delegate entity gathering to MapsManager helper.
            request.api_session, request.all_sites, request.site_id, request.map_id
        )
        if map_data is None:  # WHY: no map row means the ID does not exist in this site.
            return jsonify({"error": _ERR_MAP_NOT_FOUND}), _HTTP_NOT_FOUND  # WHY: 404 when Mist has no such map.
        payload = request.build_response_fn(request.site_id, request.map_id, map_data, layers)  # WHY: shape reply.
        return jsonify(payload)  # WHY: Flask serialises the JSON envelope with the payload dict.
    except Exception as e:  # WHY: broad catch surfaces to the operator without leaking internals to the browser.
        logging.exception("Error fetching map data: %s", e)  # WHY: full stack captured server-side for debugging.
        return jsonify({"error": _ERR_MAP_DATA_FAILED}), _HTTP_SERVER_ERROR  # WHY: generic 500 keeps details hidden.


def _render_viewer_page(html_template: str, ctx: ViewerPageContext):  # WHY: pure Jinja render of the root page.
    """Render the Flask root page. Injects sorted-sites + maps JSON into the HTML template."""
    sites_sorted = sorted(ctx.all_sites, key=lambda x: x.get("name", "").lower())  # WHY: alphabetise dropdown.
    sites_json = ctx.json_module.dumps(_summarise_named_records(sites_sorted))  # WHY: encode dropdown payload.
    maps_json = ctx.json_module.dumps(_summarise_named_records(ctx.all_maps))  # WHY: encode map dropdown payload.
    return ctx.render_template_string(  # WHY: Jinja injects state so the JS boots with the right selection.
        html_template,
        initial_site_id=ctx.initial_site_id,
        initial_map_id=ctx.initial_map_id,
        all_sites_json=sites_json,
        all_maps_json=maps_json,
    )


def _handle_site_maps_request(api_session, jsonify, site_id: str):  # WHY: /api/site/<id>/maps route handler.
    """Flask /api/site/<id>/maps handler -- returns the site's maps list as JSON."""
    logging.info("[Flask API] Fetching maps for site %s", site_id)  # WHY: trace which site is being fetched.
    try:
        response = mistapi.api.v1.sites.maps.listSiteMaps(api_session, site_id=site_id)  # WHY: Mist SDK call.
        if response.status_code != _HTTP_OK or not response.data:  # WHY: non-200 or empty body -> treat as no maps.
            return jsonify({"maps": []})  # WHY: empty list keeps the front-end dropdown happy on absent data.
        return jsonify({"maps": _summarise_named_records(response.data)})  # WHY: strip to id/name for the UI.
    except Exception as e:  # WHY: broad catch converts SDK/network errors into a well-formed 500 for the browser.
        logging.exception("Error fetching maps: %s", e)  # WHY: capture full stack for post-mortem log review.
        return jsonify({"error": _ERR_MAPS_LIST_FAILED, "maps": []}), _HTTP_SERVER_ERROR  # WHY: safe 500 payload.


def _fetch_map_image_bytes(api_session, site_id: str, map_id: str):  # WHY: authenticated map-image proxy helper.
    """Look up the map record, fetch its image bytes with auth. Returns (response, error_tuple)."""
    import requests as req_lib  # WHY: lazy import keeps optional dependency out of module import cost.

    map_response = mistapi.api.v1.sites.maps.getSiteMap(api_session, site_id=site_id, map_id=map_id)  # WHY: SDK call.
    if map_response.status_code != _HTTP_OK:  # WHY: Mist rejected the map lookup entirely -- bail with 404.
        return None, (_ERR_MAP_NOT_FOUND, _HTTP_NOT_FOUND)  # WHY: bubble a clean 404 up to the Flask handler.
    image_url = map_response.data.get("url", "")  # WHY: Mist returns absolute signed URL when available.
    if not image_url:  # WHY: some map records omit the signed URL -- treat as no floorplan available.
        return None, (_ERR_NO_IMAGE_URL, _HTTP_NOT_FOUND)  # WHY: 404 when the map record lacks a floorplan image.
    token = getattr(api_session, _TOKEN_ATTR, "")  # WHY: mistapi stashes the bearer here (private attribute).
    headers = {_AUTHORIZATION_HEADER: f"Token {token}"} if token else {}  # WHY: forward auth only when we have one.
    image_response = req_lib.get(image_url, headers=headers, timeout=_IMAGE_REQUEST_TIMEOUT_S)  # WHY: bounded GET.
    return image_response, None  # WHY: caller inspects status_code + content on success path.


def _handle_map_image_request(api_session, site_id: str, map_id: str):
    """Flask /api/map-image/<site>/<map> handler -- proxies the authenticated image fetch."""
    from flask import Response  # WHY: local import so tests can stub Flask without importing it at module load.

    logging.info("[Flask API] Fetching map image for site %s, map %s", site_id, map_id)  # WHY: trace entry.
    try:
        image_response, error = _fetch_map_image_bytes(api_session, site_id, map_id)  # WHY: delegate the fetch.
        if error is not None:
            return error  # WHY: guard clause -- helper already produced a Flask-compatible (body, status) tuple.
        if image_response.status_code != _HTTP_OK:
            logging.warning("Failed to fetch image: %s", image_response.status_code)  # WHY: warn on upstream failure.
            return f"Image fetch failed: {image_response.status_code}", _HTTP_NOT_FOUND  # WHY: keep body brief.
        content_type = image_response.headers.get(_CONTENT_TYPE_HEADER, _DEFAULT_IMAGE_MIMETYPE)  # WHY: passthrough.
        return Response(image_response.content, mimetype=content_type)  # WHY: stream bytes through as-is.
    except Exception as e:  # WHY: broad catch so a network hiccup never leaks a stack trace into the browser.
        logging.exception("Error fetching map image: %s", e)  # WHY: full stack captured server-side.
        return _ERR_MAP_IMAGE_FAILED, _HTTP_SERVER_ERROR  # WHY: generic 500 keeps upstream details hidden.


def _resolve_flask_bind_address() -> tuple[str, int]:
    """Return ``(host, port)`` for the Flask server, binding all interfaces in a container."""
    if is_running_in_container():
        logging.debug("Container detected: binding Flask to 0.0.0.0")  # WHY: confirm the host override in logs.
        return _CONTAINER_BIND, _DEFAULT_FLASK_PORT  # WHY: bind all interfaces so host browser can reach the port.
    return _LOCALHOST_BIND, _DEFAULT_FLASK_PORT  # WHY: default to loopback for standalone desktop usage.


_BANNER_SEPARATOR = "-" * 80  # WHY: reused decorator line keeps banner formatting consistent.
_BANNER_LINES = (  # WHY: table-driven banner replaces sequential print calls, easier to extend and test.
    "! Features:",
    "!   - Site and map switching via dropdowns",
    "!   - Device, zone, and client visualization",
    "!   - Pan and zoom controls",
    "!   - Refresh button for live data",
    "! Press Ctrl+C to stop server",
)


def _print_flask_viewer_banner(host: str, port: int) -> None:
    """Emit the pre-launch ASCII banner that lists URL + key features."""
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.info("\n%s", _BANNER_SEPARATOR)  # WHY: leading blank line separates banner from prior console output.
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.info("LAUNCHING FLASK MAP VIEWER")  # WHY: identifies the launched mode to the operator.
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.info("%s", _BANNER_SEPARATOR)  # WHY: divider between title and body of the banner.
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.info("! Server URL: http://%s:%s", host, port)  # WHY: URL comes first so operators can click through.
    for line in _BANNER_LINES:
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("%s", line)  # WHY: table-driven emission keeps additions trivial.
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.info("%s", _BANNER_SEPARATOR)  # WHY: trailing divider signals end of banner block.


def _maybe_open_browser(port: int) -> DelayedBrowserOpener | None:
    """Start a delayed browser open, unless the viewer runs in a container.

    Returns the opener so the caller can stop the thread. Returns ``None`` in a
    container, because the host opens the browser there.
    """
    if is_running_in_container():
        # WHY: containers expose ports externally. Caller handles browser launch on the host side.
        logger.debug("The viewer runs in a container, so it schedules no browser open")
        return None  # WHY: The caller has no thread to stop on this path.
    url = f"http://{_LOCALHOST_BIND}:{port}"  # WHY: hardcode loopback -- container path exits early.
    logger.info("The viewer schedules a browser open to %s", url)  # WHY: Records the request before the start.
    opener = DelayedBrowserOpener(url, delay_s=_BROWSER_OPEN_DELAY_S)  # WHY: The delay lets Flask bind the port.
    opener.start()  # WHY: The wait runs off the main thread, so the Flask server can start.
    return opener  # WHY: The caller stops this opener after the server returns.


def _run_flask_server(flask_app, host: str, port: int) -> None:
    """Run the Flask server until interrupted. Mirror the original KeyboardInterrupt path."""
    try:
        logging.info("Starting Flask server on http://%s:%s", host, port)  # WHY: audit trail before blocking call.
        flask_app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False)  # WHY: prod-safe args.
    except KeyboardInterrupt:
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\n\nFlask map viewer stopped by user")  # WHY: friendly console signal on Ctrl+C.
        logging.info("Flask map viewer stopped by user (Ctrl+C)")  # WHY: matching log entry for grep-based audits.
    except Exception as e:  # WHY: broad catch prevents a Flask crash from tearing down the CLI silently.
        logging.exception("Error running Flask server: %s", e)  # WHY: full stack for post-mortem log review.
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.warning("\n! Error running map viewer: %s", e)  # WHY: surface failure to operator on stdout as well.


_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MistHelper Map Viewer</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background-color: #1a1a1a;
            color: #e0e0e0;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        .header {
            padding: 15px 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        .header h1 {
            font-size: 20px;
            font-weight: 600;
            margin-right: 30px;
        }
        .dropdown-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .dropdown-group label {
            font-size: 14px;
            color: rgba(255,255,255,0.8);
        }
        select {
            padding: 8px 12px;
            font-size: 14px;
            border: none;
            border-radius: 4px;
            background-color: rgba(255,255,255,0.9);
            color: #333;
            min-width: 200px;
            cursor: pointer;
        }
        select:focus { outline: 2px solid #667eea; }
        .status {
            margin-left: auto;
            font-size: 13px;
            color: rgba(255,255,255,0.7);
        }
        .loading {
            color: #ffd700;
            font-weight: bold;
        }
        .main-content {
            flex: 1;
            display: flex;
            overflow: hidden;
        }
        #map-container {
            flex: 1;
            padding: 10px;
        }
        #map-display {
            width: 100%;
            height: 100%;
            background-color: #2d2d2d;
            border-radius: 8px;
        }
        .sidebar {
            width: 280px;
            background-color: #2d2d2d;
            padding: 20px;
            overflow-y: auto;
            border-left: 1px solid #444;
        }
        .sidebar h3 {
            color: #a0a0ff;
            font-size: 14px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #444;
        }
        .info-item {
            margin: 8px 0;
            font-size: 13px;
            color: #b0b0b0;
        }
        .info-item strong { color: #e0e0e0; }
        .layer-toggle {
            margin: 6px 0;
        }
        .layer-toggle label {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
            font-size: 13px;
            padding: 4px 0;
        }
        .layer-toggle input[type="checkbox"] {
            width: 16px;
            height: 16px;
        }
        .refresh-btn {
            margin-top: 15px;
            width: 100%;
            padding: 10px;
            background-color: #667eea;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 13px;
            font-weight: bold;
        }
        .refresh-btn:hover { background-color: #5a6fd6; }
        .refresh-btn:disabled { background-color: #555; cursor: not-allowed; }
    </style>
</head>
<body>
    <div class="header">
        <h1>MistHelper Map Viewer</h1>
        <div class="dropdown-group">
            <label for="site-select">Site:</label>
            <select id="site-select"></select>
        </div>
        <div class="dropdown-group">
            <label for="map-select">Map:</label>
            <select id="map-select"></select>
        </div>
        <div class="status" id="status-display">Ready</div>
    </div>

    <div class="main-content">
        <div id="map-container">
            <div id="map-display"></div>
        </div>
        <div class="sidebar">
            <h3>Map Information</h3>
            <div id="map-info">
                <div class="info-item"><strong>Site:</strong> <span id="info-site">-</span></div>
                <div class="info-item"><strong>Map:</strong> <span id="info-map">-</span></div>
                <div class="info-item"><strong>Dimensions:</strong> <span id="info-dims">-</span></div>
                <div class="info-item"><strong>Access Points:</strong> <span id="info-aps">-</span></div>
                <div class="info-item"><strong>Switches:</strong> <span id="info-switches">-</span></div>
                <div class="info-item"><strong>Gateways:</strong> <span id="info-gateways">-</span></div>
                <div class="info-item"><strong>Zones:</strong> <span id="info-zones">-</span></div>
                <div class="info-item"><strong>WiFi Clients:</strong> <span id="info-wifi-clients">-</span></div>
                <div class="info-item"><strong>Unconnected:</strong> <span id="info-unconnected">-</span></div>
                <div class="info-item"><strong>App Clients:</strong> <span id="info-sdk">-</span></div>
                <div class="info-item"><strong>BLE Devices:</strong> <span id="info-ble">-</span></div>
                <div class="info-item"><strong>Assets:</strong> <span id="info-assets">-</span></div>
            </div>

            <h3 style="margin-top: 20px;">Layer Controls</h3>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-aps" checked> Access Points</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-switches" checked> Switches</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-gateways" checked> Gateways</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-zones" checked> Zones</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-wifi-clients" checked> WiFi Clients (Connected)</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-unconnected-clients" checked>
                    WiFi Clients (Unconnected)</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-ble-devices" checked> Bluetooth Devices</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-assets" checked> Assets</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-sdk-clients" checked> App Clients (Marvis)</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-walls" checked> Walls</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-wayfinding" checked> Wayfinding Paths</label>
            </div>

            <h3 style="margin-top: 20px;">Coverage Heatmaps</h3>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-wifi-coverage"> WiFi RF Coverage</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-ble-coverage"> BLE Coverage</label>
            </div>
            <div class="layer-toggle">
                <label><input type="checkbox" id="toggle-app-coverage"> App Coverage</label>
            </div>

            <h3 style="margin-top: 20px;">Legend</h3>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 0; height: 0;
                    border-left: 8px solid transparent;
                    border-right: 8px solid transparent;
                    border-bottom: 14px solid #00cc00;
                    margin-right: 8px;"></span>
                Device (Connected)
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 0; height: 0;
                    border-left: 8px solid transparent;
                    border-right: 8px solid transparent;
                    border-bottom: 14px solid #ff8c00;
                    margin-right: 8px;"></span>
                Device (Transitional)
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 0; height: 0;
                    border-left: 8px solid transparent;
                    border-right: 8px solid transparent;
                    border-bottom: 14px solid #ff4444;
                    margin-right: 8px;"></span>
                Device (Offline)
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 12px; height: 12px;
                    background-color: #9966ff; border-radius: 50%;
                    margin-right: 8px;"></span>
                WiFi Client (Connected)
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 12px; height: 12px;
                    background-color: #888888; border-radius: 50%;
                    margin-right: 8px;"></span>
                WiFi Client (Unconnected)
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 12px; height: 12px;
                    background-color: #66ccff; border-radius: 50%;
                    margin-right: 8px;"></span>
                App Client (Marvis)
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 12px; height: 12px;
                    background-color: #003366; border-radius: 50%;
                    margin-right: 8px;"></span>
                Bluetooth Device
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 12px; height: 12px;
                    background-color: #00cc00; border-radius: 50%;
                    margin-right: 8px;"></span>
                Asset
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 16px; height: 3px;
                    background-color: #ff0000;
                    margin-right: 8px;"></span>
                Wall
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 16px; height: 3px;
                    background-color: #00bfff; border-style: dashed;
                    margin-right: 8px;"></span>
                Wayfinding
            </div>
            <div class="legend-item" style="margin: 6px 0; font-size: 12px;">
                <span style="display: inline-block; width: 16px; height: 12px;
                    background-color: rgba(255,165,0,0.5);
                    border: 2px dashed orange;
                    margin-right: 8px;"></span>
                Zone
            </div>

            <button class="refresh-btn" id="refresh-btn" onclick="refreshCurrentMap()">
                Refresh Data
            </button>
        </div>
    </div>

    <script>
        // State
        let currentSiteId = '{{ initial_site_id }}';
        let currentMapId = '{{ initial_map_id }}';
        let allSites = {{ all_sites_json | safe }};
        let currentMaps = {{ all_maps_json | safe }};
        let currentFigure = null;
        let currentMapData = null;  // Store current map data for re-rendering

        // Layer visibility state
        let layerVisibility = {
            aps: true,
            switches: true,
            gateways: true,
            zones: true,
            wifiClients: true,
            unconnectedClients: true,
            bleDevices: true,
            assets: true,
            sdkClients: true,
            walls: true,
            wayfinding: true,
            wifiCoverage: false,
            bleCoverage: false,
            appCoverage: false
        };

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            populateSiteDropdown();
            populateMapDropdown();
            loadMapData(currentSiteId, currentMapId);

            // Event listeners
            document.getElementById('site-select').addEventListener('change', handleSiteChange);
            document.getElementById('map-select').addEventListener('change', handleMapChange);

            // Layer toggle listeners
            document.getElementById('toggle-aps').addEventListener('change', function() {
                layerVisibility.aps = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-switches').addEventListener('change', function() {
                layerVisibility.switches = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-gateways').addEventListener('change', function() {
                layerVisibility.gateways = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-zones').addEventListener('change', function() {
                layerVisibility.zones = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-wifi-clients').addEventListener('change', function() {
                layerVisibility.wifiClients = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-unconnected-clients').addEventListener('change', function() {
                layerVisibility.unconnectedClients = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-ble-devices').addEventListener('change', function() {
                layerVisibility.bleDevices = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-assets').addEventListener('change', function() {
                layerVisibility.assets = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-sdk-clients').addEventListener('change', function() {
                layerVisibility.sdkClients = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-walls').addEventListener('change', function() {
                layerVisibility.walls = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-wayfinding').addEventListener('change', function() {
                layerVisibility.wayfinding = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-wifi-coverage').addEventListener('change', function() {
                layerVisibility.wifiCoverage = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-ble-coverage').addEventListener('change', function() {
                layerVisibility.bleCoverage = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
            document.getElementById('toggle-app-coverage').addEventListener('change', function() {
                layerVisibility.appCoverage = this.checked;
                if (currentMapData) renderMap(currentMapData);
            });
        });

        function setStatus(message, isLoading = false) {
            const statusEl = document.getElementById('status-display');
            statusEl.textContent = message;
            statusEl.className = isLoading ? 'status loading' : 'status';
        }

        function populateSiteDropdown() {
            const select = document.getElementById('site-select');
            select.innerHTML = '';
            allSites.forEach(site => {
                const option = document.createElement('option');
                option.value = site.id;
                option.textContent = site.name;
                if (site.id === currentSiteId) option.selected = true;
                select.appendChild(option);
            });
        }

        function populateMapDropdown() {
            const select = document.getElementById('map-select');
            select.innerHTML = '';
            currentMaps.forEach(map => {
                const option = document.createElement('option');
                option.value = map.id;
                option.textContent = map.name;
                if (map.id === currentMapId) option.selected = true;
                select.appendChild(option);
            });
        }

        async function handleSiteChange(event) {
            const newSiteId = event.target.value;
            if (newSiteId === currentSiteId) return;

            setStatus('Loading site...', true);
            console.log('[Site Change] Switching to site:', newSiteId);

            try {
                // Fetch maps for new site
                const response = await fetch('/api/site/' + newSiteId + '/maps');
                if (!response.ok) throw new Error('Failed to fetch maps');

                const data = await response.json();
                currentSiteId = newSiteId;
                currentMaps = data.maps;

                // Update map dropdown
                populateMapDropdown();

                // Load first map if available
                if (currentMaps.length > 0) {
                    currentMapId = currentMaps[0].id;
                    document.getElementById('map-select').value = currentMapId;
                    await loadMapData(currentSiteId, currentMapId);
                } else {
                    currentMapId = null;
                    showEmptyMap('No maps found for this site');
                }

                setStatus('Ready');
            } catch (error) {
                console.error('Error switching site:', error);
                setStatus('Error: ' + error.message);
            }
        }

        async function handleMapChange(event) {
            const newMapId = event.target.value;
            if (newMapId === currentMapId) return;

            currentMapId = newMapId;
            await loadMapData(currentSiteId, currentMapId);
        }

        async function loadMapData(siteId, mapId) {
            if (!siteId || !mapId) {
                showEmptyMap('No map selected');
                return;
            }

            setStatus('Loading map...', true);
            console.log('[Load Map] Fetching data for site:', siteId, 'map:', mapId);

            try {
                const response = await fetch('/api/map/' + siteId + '/' + mapId);
                if (!response.ok) throw new Error('Failed to fetch map data');

                const data = await response.json();
                console.log('[Load Map] Received data:', data);

                // Update info panel
                updateInfoPanel(data);

                // Render Plotly figure
                renderMap(data);

                setStatus('Ready');
            } catch (error) {
                console.error('Error loading map:', error);
                setStatus('Error: ' + error.message);
                showEmptyMap('Error loading map');
            }
        }

        function updateInfoPanel(data) {
            document.getElementById('info-site').textContent = data.site_name || '-';
            document.getElementById('info-map').textContent = data.map_name || '-';
            document.getElementById('info-dims').textContent = data.width + ' x ' + data.height + ' px';
            document.getElementById('info-aps').textContent = data.ap_count || 0;
            document.getElementById('info-switches').textContent = data.switch_count || 0;
            document.getElementById('info-gateways').textContent = data.gateway_count || 0;
            document.getElementById('info-zones').textContent = data.zone_count || 0;
            document.getElementById('info-wifi-clients').textContent = data.wifi_client_count || 0;
            document.getElementById('info-unconnected').textContent = data.unconnected_client_count || 0;
            document.getElementById('info-sdk').textContent = data.sdk_client_count || 0;
            document.getElementById('info-ble').textContent = data.ble_device_count || 0;
            document.getElementById('info-assets').textContent = data.asset_count || 0;
        }

        function renderMap(data) {
            // Store data for re-rendering when toggling layers
            currentMapData = data;

            const traces = [];

            // Add walls traces (render first so they're behind other elements)
            // Walls are line segments: each has x1,y1 -> x2,y2
            if (layerVisibility.walls && data.walls && data.walls.length > 0) {
                console.log('Rendering ' + data.walls.length + ' wall segments');
                let wallX = [];
                let wallY = [];
                for (let i = 0; i < data.walls.length; i++) {
                    const segment = data.walls[i];
                    // Add line segment with null separator
                    wallX.push(segment.x1, segment.x2, null);
                    wallY.push(segment.y1, segment.y2, null);
                }
                if (wallX.length > 0) {
                    traces.push({
                        x: wallX,
                        y: wallY,
                        mode: 'lines',
                        type: 'scatter',
                        name: 'Walls',
                        line: { color: '#ff8c00', width: 6 },
                        hoverinfo: 'name'
                    });
                }
            }

            // Add wayfinding paths - line segments with x1,y1 -> x2,y2
            if (layerVisibility.wayfinding && data.wayfinding && data.wayfinding.length > 0) {
                console.log('Rendering ' + data.wayfinding.length + ' wayfinding segments');
                let pathX = [];
                let pathY = [];
                for (let i = 0; i < data.wayfinding.length; i++) {
                    const segment = data.wayfinding[i];
                    // Add line segment with null separator
                    pathX.push(segment.x1, segment.x2, null);
                    pathY.push(segment.y1, segment.y2, null);
                }
                if (pathX.length > 0) {
                    traces.push({
                        x: pathX,
                        y: pathY,
                        mode: 'lines',
                        type: 'scatter',
                        name: 'Wayfinding',
                        line: { color: '#0066ff', width: 5, dash: 'dash' },
                        hoverinfo: 'name'
                    });
                }
            }

            // Add zones (with labels) - dynamic rainbow colors based on zone count
            if (layerVisibility.zones && data.zones && data.zones.length > 0) {
                // Generate unique colors by evenly subdividing the rainbow (HSL hue 0-360)
                function hslToRgba(h, s, l, a) {
                    const c = (1 - Math.abs(2 * l - 1)) * s;
                    const x = c * (1 - Math.abs((h / 60) % 2 - 1));
                    const m = l - c / 2;
                    let r, g, b;
                    if (h < 60) { r = c; g = x; b = 0; }
                    else if (h < 120) { r = x; g = c; b = 0; }
                    else if (h < 180) { r = 0; g = c; b = x; }
                    else if (h < 240) { r = 0; g = x; b = c; }
                    else if (h < 300) { r = x; g = 0; b = c; }
                    else { r = c; g = 0; b = x; }
                    return `rgba(${Math.round((r + m) * 255)},` +
                        `${Math.round((g + m) * 255)},` +
                        `${Math.round((b + m) * 255)},${a})`;
                }

                const zoneCount = data.zones.length;
                // Golden angle (137.508 degrees) ensures maximum color separation between adjacent zones
                const goldenAngle = 137.508;

                data.zones.forEach((zone, idx) => {
                    if (zone.vertices && zone.vertices.length >= 3) {
                        const zoneX = zone.vertices.map(v => v.x);
                        const zoneY = zone.vertices.map(v => v.y);
                        zoneX.push(zoneX[0]);  // Close polygon
                        zoneY.push(zoneY[0]);

                        // Use golden angle for maximum color separation between sequential zones
                        const hue = (idx * goldenAngle) % 360;
                        const fillColor = hslToRgba(hue, 0.7, 0.6, 0.25);
                        const lineColor = hslToRgba(hue, 0.9, 0.4, 1.0);

                        // Add solid border first (underneath) for overlap visibility
                        traces.push({
                            x: zoneX,
                            y: zoneY,
                            mode: 'lines',
                            type: 'scatter',
                            name: '',
                            showlegend: false,
                            line: { color: lineColor, width: 5 },
                            hoverinfo: 'skip'
                        });

                        // Add filled zone with thinner dashed border on top
                        traces.push({
                            x: zoneX,
                            y: zoneY,
                            mode: 'lines',
                            type: 'scatter',
                            name: zone.name || 'Zone ' + (idx + 1),
                            fill: 'toself',
                            fillcolor: fillColor,
                            line: { color: 'rgba(255,255,255,0.8)', width: 2, dash: 'dot' },
                            hovertemplate: '<b>' + (zone.name || 'Zone') + '</b><extra></extra>'
                        });

                        // Add zone label at centroid
                        const centroidX = zoneX.slice(0, -1).reduce((a, b) => a + b, 0) / (zoneX.length - 1);
                        const centroidY = zoneY.slice(0, -1).reduce((a, b) => a + b, 0) / (zoneY.length - 1);

                        traces.push({
                            x: [centroidX],
                            y: [centroidY],
                            mode: 'markers+text',
                            type: 'scatter',
                            text: [zone.name || 'Zone'],
                            textfont: { size: 16, color: '#1a1a1a', family: 'Arial Black' },
                            textposition: 'middle center',
                            marker: { size: 40, color: 'rgba(255,255,255,0.85)', symbol: 'square' },
                            showlegend: false,
                            hoverinfo: 'skip'
                        });
                    }
                });
            }

            // Helper function for device status-based coloring
            function getDeviceColor(status, connectedColor) {
                const transitionalStatuses = ['restart', 'upgrading', 'reboot_required', 'provisioning'];
                const offlineStatuses = ['disconnected', 'offline'];
                const statusLower = (status || '').toLowerCase();
                if (transitionalStatuses.includes(statusLower)) return '#ff8c00';  // Orange
                if (offlineStatuses.includes(statusLower)) return '#ff4444';  // Red
                return connectedColor;
            }

            // Add Access Points trace (green triangles)
            if (layerVisibility.aps && data.devices && data.devices.length > 0) {
                const aps = data.devices.filter(d => d.type === 'ap' || !d.type);
                if (aps.length > 0) {
                    const apTrace = {
                        x: aps.map(d => d.x),
                        y: aps.map(d => d.y),
                        mode: 'markers+text',
                        type: 'scatter',
                        name: 'Access Points',
                        text: aps.map(d => d.name),
                        textposition: 'top center',
                        textfont: { size: 14, color: '#1a1a1a', family: 'Arial Bold' },
                        marker: {
                            size: 22,
                            color: aps.map(d => getDeviceColor(d.status, '#00cc00')),
                            symbol: 'triangle-up',
                            angle: aps.map(d => d.orientation || 0),
                            line: { color: '#000000', width: 2 }
                        },
                        hovertemplate: '<b>%{text}</b><br>Type: AP<br>'
                            + 'Status: %{customdata[0]}<br>MAC: %{customdata[1]}<br>'
                            + 'Orientation: %{customdata[2]}deg<extra></extra>',
                        customdata: aps.map(d => [d.status, d.mac, d.orientation || 0])
                    };
                    traces.push(apTrace);
                }
            }

            // Add Switches trace (cyan squares)
            if (layerVisibility.switches && data.devices && data.devices.length > 0) {
                const switches = data.devices.filter(d => d.type === 'switch');
                if (switches.length > 0) {
                    const switchTrace = {
                        x: switches.map(d => d.x),
                        y: switches.map(d => d.y),
                        mode: 'markers+text',
                        type: 'scatter',
                        name: 'Switches',
                        text: switches.map(d => d.name),
                        textposition: 'top center',
                        textfont: { size: 14, color: '#1a1a1a', family: 'Arial Bold' },
                        marker: {
                            size: 22,
                            color: switches.map(d => getDeviceColor(d.status, '#00ccff')),
                            symbol: 'square',
                            line: { color: '#000000', width: 2 }
                        },
                        hovertemplate: '<b>%{text}</b><br>Type: Switch<br>'
                            + 'Status: %{customdata[0]}<br>MAC: %{customdata[1]}'
                            + '<extra></extra>',
                        customdata: switches.map(d => [d.status, d.mac])
                    };
                    traces.push(switchTrace);
                }
            }

            // Add Gateways trace (purple diamonds)
            if (layerVisibility.gateways && data.devices && data.devices.length > 0) {
                const gateways = data.devices.filter(d => d.type === 'gateway');
                if (gateways.length > 0) {
                    const gatewayTrace = {
                        x: gateways.map(d => d.x),
                        y: gateways.map(d => d.y),
                        mode: 'markers+text',
                        type: 'scatter',
                        name: 'Gateways',
                        text: gateways.map(d => d.name),
                        textposition: 'top center',
                        textfont: { size: 14, color: '#1a1a1a', family: 'Arial Bold' },
                        marker: {
                            size: 22,
                            color: gateways.map(d => getDeviceColor(d.status, '#cc66ff')),
                            symbol: 'diamond',
                            line: { color: '#000000', width: 2 }
                        },
                        hovertemplate: '<b>%{text}</b><br>Type: Gateway<br>'
                            + 'Status: %{customdata[0]}<br>MAC: %{customdata[1]}'
                            + '<extra></extra>',
                        customdata: gateways.map(d => [d.status, d.mac])
                    };
                    traces.push(gatewayTrace);
                }
            }

            // Add WiFi clients trace (connected - purple)
            if (layerVisibility.wifiClients && data.wifi_clients && data.wifi_clients.length > 0) {
                const wifiClientTrace = {
                    x: data.wifi_clients.map(c => c.x),
                    y: data.wifi_clients.map(c => c.y),
                    mode: 'markers+text',
                    type: 'scatter',
                    name: 'WiFi Clients',
                    text: data.wifi_clients.map(c => c.name || ''),
                    textposition: 'top center',
                    textfont: { size: 11, color: '#1a1a1a', family: 'Arial' },
                    marker: {
                        size: 14,
                        color: '#9966ff',
                        symbol: 'circle',
                        line: { color: '#4400aa', width: 1 }
                    },
                    hovertemplate: '<b>WiFi Client</b><br>'
                        + 'Name: %{customdata[0]}<br>MAC: %{customdata[1]}<br>'
                        + 'SSID: %{customdata[2]}<extra></extra>',
                    customdata: data.wifi_clients.map(c => [c.name || '-', c.mac || 'Unknown', c.ssid || '-'])
                };
                traces.push(wifiClientTrace);
            }

            // Add unconnected WiFi clients trace (grey)
            if (layerVisibility.unconnectedClients && data.unconnected_clients && data.unconnected_clients.length > 0) {
                const unconnectedTrace = {
                    x: data.unconnected_clients.map(c => c.x),
                    y: data.unconnected_clients.map(c => c.y),
                    mode: 'markers',
                    type: 'scatter',
                    name: 'Unconnected Clients',
                    marker: {
                        size: 8,
                        color: '#888888',
                        symbol: 'circle',
                        line: { color: '#444444', width: 1 }
                    },
                    hovertemplate: '<b>Unconnected Client</b><br>'
                        + 'MAC: %{customdata[0]}<br>'
                        + 'Manufacturer: %{customdata[1]}<extra></extra>',
                    customdata: data.unconnected_clients.map(c => [c.mac || 'Unknown', c.manufacture || '-'])
                };
                traces.push(unconnectedTrace);
            }

            // Add BLE/Bluetooth devices trace (dark blue)
            if (layerVisibility.bleDevices && data.ble_devices && data.ble_devices.length > 0) {
                const bleTrace = {
                    x: data.ble_devices.map(d => d.x),
                    y: data.ble_devices.map(d => d.y),
                    mode: 'markers',
                    type: 'scatter',
                    name: 'Bluetooth Devices',
                    marker: {
                        size: 10,
                        color: '#003366',
                        symbol: 'circle',
                        line: { color: '#001a33', width: 1 }
                    },
                    hovertemplate: '<b>BLE Device</b><br>MAC: %{customdata[0]}<extra></extra>',
                    customdata: data.ble_devices.map(d => [d.mac || 'Unknown'])
                };
                traces.push(bleTrace);
            }

            // Add assets trace (green) with name labels
            if (layerVisibility.assets && data.assets && data.assets.length > 0) {
                const assetTrace = {
                    x: data.assets.map(a => a.x),
                    y: data.assets.map(a => a.y),
                    mode: 'markers+text',
                    type: 'scatter',
                    name: 'Assets',
                    text: data.assets.map(a => a.name || ''),
                    textposition: 'top center',
                    textfont: { size: 12, color: '#1a1a1a', family: 'Arial Bold' },
                    marker: {
                        size: 12,
                        color: '#00cc00',
                        symbol: 'diamond',
                        line: { color: '#006600', width: 1 }
                    },
                    hovertemplate: '<b>Asset</b><br>Name: %{customdata[0]}<br>MAC: %{customdata[1]}<extra></extra>',
                    customdata: data.assets.map(a => [a.name || 'Unknown', a.mac || '-'])
                };
                traces.push(assetTrace);
            }

            // Add SDK/Marvis clients trace (light blue)
            if (layerVisibility.sdkClients && data.sdk_clients && data.sdk_clients.length > 0) {
                const sdkClientTrace = {
                    x: data.sdk_clients.map(c => c.x),
                    y: data.sdk_clients.map(c => c.y),
                    mode: 'markers+text',
                    type: 'scatter',
                    name: 'App Clients',
                    text: data.sdk_clients.map(c => c.name || ''),
                    textposition: 'top center',
                    textfont: { size: 11, color: '#1a1a1a', family: 'Arial' },
                    marker: {
                        size: 14,
                        color: '#66ccff',
                        symbol: 'circle',
                        line: { color: '#0077cc', width: 1 }
                    },
                    hovertemplate: '<b>App Client</b><br>'
                        + 'Name: %{customdata[0]}<br>'
                        + 'UUID: %{customdata[1]}<extra></extra>',
                    customdata: data.sdk_clients.map(c => [c.name || '-', c.uuid || '-'])
                };
                traces.push(sdkClientTrace);
            }

            // Coverage heatmap traces (rendered below device markers for visibility)
            // Helper function to create coverage heatmap trace
            function createCoverageHeatmap(coverageData, layerName, colorscale) {
                if (!coverageData || coverageData.length === 0) return null;

                // Group coverage data into a grid for heatmap visualization
                const x_values = coverageData.map(p => p.x);
                const y_values = coverageData.map(p => p.y);
                const rssi_values = coverageData.map(p => p.rssi);

                // Create scatter plot with color-coded markers for coverage visualization
                // Using scatter instead of heatmap for better performance with sparse data
                return {
                    x: x_values,
                    y: y_values,
                    mode: 'markers',
                    type: 'scatter',
                    name: layerName,
                    marker: {
                        size: 8,
                        color: rssi_values,
                        colorscale: colorscale,
                        cmin: -90,
                        cmax: -30,
                        opacity: 0.6,
                        showscale: false
                    },
                    hovertemplate: '<b>' + layerName + '</b><br>'
                        + 'RSSI: %{marker.color:.0f} dBm<br>'
                        + 'X: %{x:.1f}<br>Y: %{y:.1f}<extra></extra>',
                    visible: true
                };
            }

            // WiFi coverage heatmap
            if (layerVisibility.wifiCoverage && data.wifi_coverage && data.wifi_coverage.length > 0) {
                const wifiHeatmap = createCoverageHeatmap(
                    data.wifi_coverage,
                    'WiFi Coverage',
                    [[0, '#0000ff'], [0.25, '#00ffff'], [0.5, '#00ff00'], [0.75, '#ffff00'], [1, '#ff0000']]
                );
                if (wifiHeatmap) {
                    traces.unshift(wifiHeatmap);  // Add at beginning so it renders below other elements
                }
            }

            // BLE coverage heatmap
            if (layerVisibility.bleCoverage && data.ble_coverage && data.ble_coverage.length > 0) {
                const bleHeatmap = createCoverageHeatmap(
                    data.ble_coverage,
                    'BLE Coverage',
                    [[0, '#4b0082'], [0.25, '#8a2be2'], [0.5, '#ba55d3'], [0.75, '#da70d6'], [1, '#ff69b4']]
                );
                if (bleHeatmap) {
                    traces.unshift(bleHeatmap);
                }
            }

            // App coverage heatmap
            if (layerVisibility.appCoverage && data.app_coverage && data.app_coverage.length > 0) {
                const appHeatmap = createCoverageHeatmap(
                    data.app_coverage,
                    'App Coverage',
                    [[0, '#006400'], [0.25, '#228b22'], [0.5, '#32cd32'], [0.75, '#7cfc00'], [1, '#adff2f']]
                );
                if (appHeatmap) {
                    traces.unshift(appHeatmap);
                }
            }

            const layout = {
                title: {
                    text: data.map_name || 'Map',
                    font: { color: '#e0e0e0', size: 16 }
                },
                images: data.image_url ? [{
                    source: data.image_url,
                    xref: 'x',
                    yref: 'y',
                    x: 0,
                    y: 0,
                    sizex: data.width,
                    sizey: data.height,
                    sizing: 'stretch',
                    layer: 'below'
                }] : [],
                xaxis: {
                    range: [-20, data.width + 20],
                    showgrid: false,
                    zeroline: false,
                    color: '#888'
                },
                yaxis: {
                    range: [data.height + 20, -20],  // Inverted for top-left origin
                    showgrid: false,
                    zeroline: false,
                    scaleanchor: 'x',
                    scaleratio: 1,
                    color: '#888'
                },
                paper_bgcolor: '#1e1e1e',
                plot_bgcolor: '#2d2d2d',
                showlegend: true,
                legend: {
                    x: 0.02,
                    y: 0.98,
                    bgcolor: 'rgba(45,45,45,0.9)',
                    bordercolor: '#667eea',
                    font: { color: '#e0e0e0' }
                },
                margin: { l: 50, r: 20, t: 50, b: 30 },
                dragmode: 'pan'
            };

            const config = {
                displayModeBar: true,
                displaylogo: false,
                scrollZoom: true,
                modeBarButtonsToAdd: ['drawline', 'eraseshape'],
                toImageButtonOptions: { format: 'png', filename: 'map_export' }
            };

            Plotly.react('map-display', traces, layout, config);
            currentFigure = { traces, layout };
        }

        function showEmptyMap(message) {
            const layout = {
                title: { text: message, font: { color: '#888', size: 16 } },
                paper_bgcolor: '#1e1e1e',
                plot_bgcolor: '#2d2d2d',
                xaxis: { visible: false },
                yaxis: { visible: false }
            };
            Plotly.react('map-display', [], layout, {});
        }

        async function refreshCurrentMap() {
            const btn = document.getElementById('refresh-btn');
            btn.disabled = true;
            btn.textContent = 'Refreshing...';

            await loadMapData(currentSiteId, currentMapId);

            btn.disabled = false;
            btn.textContent = 'Refresh Data';
        }
    </script>
</body>
</html>
"""


def _mount_index_route(flask_app, ctx: FlaskViewerContext, json_module: Any, render_template_string) -> None:
    """Attach the index (/) route -- factory actively packs a ViewerPageContext each request."""

    @flask_app.route(_ROUTE_INDEX)
    def index():
        """Serve the main viewer page."""
        page_ctx = ViewerPageContext(  # WHY: actively pack render inputs so ARCH-DELEGATE passthrough is avoided.
            json_module=json_module,
            render_template_string=render_template_string,
            initial_site_id=ctx.initial_site_id,
            initial_map_id=ctx.initial_map_id,
            all_sites=ctx.all_sites,
            all_maps=ctx.all_maps,
        )
        return _render_viewer_page(_HTML_TEMPLATE, page_ctx)  # WHY: delegate to pure renderer with bundled context.


def _mount_site_maps_route(flask_app, api_session: mistapi.APISession, jsonify) -> None:
    """Attach the /api/sites/<site_id>/maps route bound to the current API session."""

    @flask_app.route(_ROUTE_SITE_MAPS)
    def get_site_maps(site_id):
        """API endpoint -- proxies to :func:`_handle_site_maps_request`."""
        return _handle_site_maps_request(api_session, jsonify, site_id)  # WHY: hand SDK session + Flask helper down.


def _mount_map_image_route(flask_app, api_session: mistapi.APISession) -> None:
    """Attach the /api/sites/<site_id>/maps/<map_id>/image proxy route."""

    @flask_app.route(_ROUTE_MAP_IMAGE)
    def get_map_image(site_id, map_id):
        """Proxy endpoint -- delegates to :func:`_handle_map_image_request`."""
        return _handle_map_image_request(api_session, site_id, map_id)  # WHY: authenticated image byte forwarder.


def _mount_map_data_route(flask_app, ctx: FlaskViewerContext) -> None:
    """Attach the /api/sites/<site_id>/maps/<map_id>/data route with packed request bundles."""
    api_session = ctx.api_session  # WHY: local avoids capturing the whole ctx object in the closure.

    @flask_app.route(_ROUTE_MAP_DATA)
    def get_map_data(site_id, map_id):
        """Route Flask request into the map-data orchestrator with a packed request dataclass."""
        request = MapDataRequest(  # WHY: closure actively packs the frozen dataclass -- not a pure passthrough.
            api_session=api_session,
            all_sites=ctx.all_sites,
            site_id=site_id,
            map_id=map_id,
            collect_payload_fn=ctx.collect_payload_fn,
            build_response_fn=ctx.build_response_fn,
        )
        return _handle_map_data_request(request)  # WHY: delegate to orchestrator with bundled inputs.


def _register_flask_routes(
    flask_app, ctx: FlaskViewerContext, json_module: Any, render_template_string, jsonify
) -> None:
    """Mount every /api and index route by dispatching to focused single-route helpers."""
    _mount_index_route(flask_app, ctx, json_module, render_template_string)  # WHY: mount / for the viewer HTML page.
    _mount_site_maps_route(flask_app, ctx.api_session, jsonify)  # WHY: mount the site-scoped map listing endpoint.
    _mount_map_image_route(flask_app, ctx.api_session)  # WHY: mount the authenticated image byte proxy route.
    _mount_map_data_route(flask_app, ctx)  # WHY: mount the map payload/data endpoint with active packing.


def _build_flask_app(ctx: FlaskViewerContext):
    """Construct and wire the Flask app. Returns the ready-to-run instance."""
    import json as json_module  # WHY: local import keeps JSON module out of import graph unless viewer runs.

    from flask import Flask, jsonify, render_template_string  # WHY: local so import cost is deferred to launch time.

    flask_app = Flask(__name__)  # WHY: Flask needs the module __name__ to locate static/template folders.
    flask_app.json.sort_keys = False  # WHY: preserve key order so the browser matches server payload.
    _register_flask_routes(flask_app, ctx, json_module, render_template_string, jsonify)  # WHY: mount all endpoints.
    return flask_app  # WHY: caller runs the returned app after banner + browser-open steps.


def launch_flask_viewer(ctx: FlaskViewerContext):
    """Launch interactive Flask-based map viewer (simpler alternative to Dash).

    This viewer uses Flask for server-side rendering and Plotly.js for client-side
    map display. Site/map switching is handled via JavaScript fetch() calls to
    Flask API endpoints, which is more reliable than Dash callbacks.

    Args:
        ctx: Frozen :class:`FlaskViewerContext` bundle carrying the session,
            initial selection, site/map lists, and payload/response callables.
    """
    logging.info(  # WHY: audit trail before Flask app construction begins.
        "_launch_flask_viewer: Starting Flask viewer for site %s, map %s",
        ctx.initial_site_id,
        ctx.initial_map_id,
    )
    flask_app = _build_flask_app(ctx)  # WHY: helper handles imports + Flask config + route registration.
    flask_host, flask_port = _resolve_flask_bind_address()  # WHY: pick loopback versus all-interfaces based on env.
    _print_flask_viewer_banner(flask_host, flask_port)  # WHY: operator-facing status before the blocking run call.
    browser_opener = _maybe_open_browser(flask_port)  # WHY: fires only on desktop -- container path returns None.
    try:
        _run_flask_server(flask_app, flask_host, flask_port)  # WHY: blocking call -- returns on Ctrl+C or fatal error.
    finally:
        if browser_opener is not None:  # WHY: a container run scheduled no opener, so it has no thread to join.
            browser_opener.stop()  # WHY: the join runs on every exit path, so no thread outlives the server.
