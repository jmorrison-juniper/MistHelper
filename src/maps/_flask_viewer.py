"""Flask-based interactive map viewer (extracted from MapsManager).

Split out of ``src/maps/maps_manager.py`` so the enormous embedded HTML
template + Flask route wiring lives in a dedicated file. The launcher
takes explicit callables for the map-payload/response builders so the
module stays independent of MapsManager and easy to test.

SECURITY: :func:`_resolve_flask_bind_address` binds 0.0.0.0 only when
the container heuristics fire; direct execution stays on localhost.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

import mistapi  # type: ignore[import-untyped]

from src.maps._container_detection import is_running_in_container

logger = logging.getLogger(__name__)


def _handle_map_data_request(
    api_session,
    all_sites: list[dict],
    site_id: str,
    map_id: str,
    collect_payload_fn: Callable,
    build_response_fn: Callable,
):
    """Top-level orchestrator for the Flask /api/map endpoint. Returns a Flask Response."""
    from flask import jsonify

    logging.info("[Flask API] Fetching map data for site %s, map %s", site_id, map_id)
    try:
        map_data, layers = collect_payload_fn(api_session, all_sites, site_id, map_id)
        if map_data is None:
            return jsonify({"error": "Map not found"}), 404
        payload = build_response_fn(site_id, map_id, map_data, layers)
        return jsonify(payload)
    except Exception as e:
        logging.exception("Error fetching map data: %s", e)
        return jsonify({"error": "Failed to fetch map data. Check server logs for details."}), 500


def _render_viewer_page(
    html_template: str,
    json_module,
    render_template_string,
    initial_site_id: str,
    initial_map_id: str,
    all_sites: list[dict],
    all_maps: list[dict],
):
    """Render the Flask root page; injects sorted-sites + maps JSON into the HTML template."""
    sites_sorted = sorted(all_sites, key=lambda x: x.get("name", "").lower())
    sites_json = json_module.dumps([{"id": s.get("id"), "name": s.get("name", "Unnamed")} for s in sites_sorted])
    maps_json = json_module.dumps([{"id": m.get("id"), "name": m.get("name", "Unnamed")} for m in all_maps])
    return render_template_string(
        html_template,
        initial_site_id=initial_site_id,
        initial_map_id=initial_map_id,
        all_sites_json=sites_json,
        all_maps_json=maps_json,
    )


def _handle_site_maps_request(api_session, jsonify, site_id: str):
    """Flask /api/site/<id>/maps handler -- returns the site's maps list as JSON."""
    logging.info("[Flask API] Fetching maps for site %s", site_id)
    try:
        response = mistapi.api.v1.sites.maps.listSiteMaps(api_session, site_id=site_id)
        if response.status_code != 200 or not response.data:
            return jsonify({"maps": []})
        maps = [{"id": m.get("id"), "name": m.get("name", "Unnamed")} for m in response.data]
        return jsonify({"maps": maps})
    except Exception as e:
        logging.exception("Error fetching maps: %s", e)
        return (
            jsonify({"error": "Failed to fetch maps. Check server logs for details.", "maps": []}),
            500,
        )


def _fetch_map_image_bytes(api_session, site_id: str, map_id: str):
    """Look up the map record, fetch its image bytes with auth. Returns (response, error_tuple)."""
    import requests as req_lib

    map_response = mistapi.api.v1.sites.maps.getSiteMap(api_session, site_id=site_id, map_id=map_id)
    if map_response.status_code != 200:
        return None, ("Map not found", 404)
    image_url = map_response.data.get("url", "")
    if not image_url:
        return None, ("No image URL", 404)
    token = getattr(api_session, "_api_token", "")
    headers = {"Authorization": f"Token {token}"} if token else {}
    image_response = req_lib.get(image_url, headers=headers, timeout=30)
    return image_response, None


def _handle_map_image_request(api_session, site_id: str, map_id: str):
    """Flask /api/map-image/<site>/<map> handler -- proxies the authenticated image fetch."""
    from flask import Response

    logging.info("[Flask API] Fetching map image for site %s, map %s", site_id, map_id)
    try:
        image_response, error = _fetch_map_image_bytes(api_session, site_id, map_id)
        if error is not None:
            return error
        if image_response.status_code != 200:
            logging.warning("Failed to fetch image: %s", image_response.status_code)
            return f"Image fetch failed: {image_response.status_code}", 404
        content_type = image_response.headers.get("Content-Type", "image/png")
        return Response(image_response.content, mimetype=content_type)
    except Exception as e:
        logging.exception("Error fetching map image: %s", e)
        return "Failed to fetch map image. Check server logs for details.", 500


def _resolve_flask_bind_address() -> tuple[str, int]:
    """Return ``(host, port)`` for the Flask server, binding all interfaces in a container."""
    port = 8050
    if is_running_in_container():
        logging.debug("Container detected: binding Flask to 0.0.0.0")
        return "0.0.0.0", port  # nosec B104 - container must bind all interfaces
    return "127.0.0.1", port


def _print_flask_viewer_banner(host: str, port: int) -> None:
    """Print the pre-launch ASCII banner that lists URL + key features."""
    print("\n" + "-" * 80)
    print("LAUNCHING FLASK MAP VIEWER")
    print("-" * 80)
    print(f"! Server URL: http://{host}:{port}")
    print("! Features:")
    print("!   - Site and map switching via dropdowns")
    print("!   - Device, zone, and client visualization")
    print("!   - Pan and zoom controls")
    print("!   - Refresh button for live data")
    print("! Press Ctrl+C to stop server")
    print("-" * 80)


def _maybe_open_browser(port: int) -> None:
    """Spawn a daemon thread to open the browser after a short delay, unless in a container."""
    import threading
    import webbrowser

    if is_running_in_container():
        return  # Containerized -- caller will open the browser externally

    def open_browser() -> None:
        """Wait briefly then point the default browser at the local Flask server."""
        import time

        time.sleep(1.5)
        webbrowser.open(f"http://127.0.0.1:{port}")

    threading.Thread(target=open_browser, daemon=True).start()


def _run_flask_server(flask_app, host: str, port: int) -> None:
    """Run the Flask server until interrupted; mirror the original KeyboardInterrupt path."""
    try:
        logging.info("Starting Flask server on http://%s:%s", host, port)
        flask_app.run(host=host, port=port, debug=False, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\nFlask map viewer stopped by user")
        logging.info("Flask map viewer stopped by user (Ctrl+C)")
    except Exception as e:
        logging.exception("Error running Flask server: %s", e)
        print(f"\n! Error running map viewer: {e}")


def launch_flask_viewer(
    api_session,
    initial_site_id: str,
    initial_map_id: str,
    all_sites: list[dict],
    all_maps: list[dict],
    collect_payload_fn: Callable,
    build_response_fn: Callable,
):
    """Launch interactive Flask-based map viewer (simpler alternative to Dash).

    This viewer uses Flask for server-side rendering and Plotly.js for client-side
    map display. Site/map switching is handled via JavaScript fetch() calls to
    Flask API endpoints, which is more reliable than Dash callbacks.

    Args:
        api_session: Authenticated mistapi session used for API calls.
        initial_site_id: Site ID to load initially
        initial_map_id: Map ID to load initially
        all_sites: List of all sites in the organization
        all_maps: List of maps for the initial site
        collect_payload_fn: Callable that assembles the map payload dict.
        build_response_fn: Callable that builds the map-data HTTP response.
    """
    import json as json_module

    from flask import Flask, jsonify, render_template_string

    logging.info("_launch_flask_viewer: Starting Flask viewer for site %s, map %s", initial_site_id, initial_map_id)

    flask_app = Flask(__name__)
    flask_app.config["JSON_SORT_KEYS"] = False

    # HTML template with embedded Plotly.js
    HTML_TEMPLATE = """
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

    @flask_app.route("/")
    def index():
        """Serve the main viewer page."""
        return _render_viewer_page(
            HTML_TEMPLATE,
            json_module,
            render_template_string,
            initial_site_id,
            initial_map_id,
            all_sites,
            all_maps,
        )

    @flask_app.route("/api/site/<site_id>/maps")
    def get_site_maps(site_id):
        """API endpoint -- proxies to _handle_site_maps_request."""
        return _handle_site_maps_request(api_session, jsonify, site_id)

    @flask_app.route("/api/map-image/<site_id>/<map_id>")
    def get_map_image(site_id, map_id):
        """Proxy endpoint -- delegates to _handle_map_image_request."""
        return _handle_map_image_request(api_session, site_id, map_id)

    @flask_app.route("/api/map/<site_id>/<map_id>")
    def get_map_data(site_id, map_id):
        """Delegate to MapsManager._handle_map_data_request -- routes Flask request to the orchestrator."""
        return _handle_map_data_request(api_session, all_sites, site_id, map_id, collect_payload_fn, build_response_fn)

    flask_host, flask_port = _resolve_flask_bind_address()
    _print_flask_viewer_banner(flask_host, flask_port)
    _maybe_open_browser(flask_port)
    _run_flask_server(flask_app, flask_host, flask_port)
