"""Map viewer routes for the MistHelper web portal.

Provides site listing, map enumeration, map data for Plotly.js
rendering, and map image serving. Replaces the standalone Dash viewer.
"""

from flask import Blueprint, current_app, jsonify, render_template

maps_bp = Blueprint("maps", __name__)


@maps_bp.route("/maps")
def maps_page():
    """Render the map viewer page."""
    return render_template("map_viewer.html")


@maps_bp.route("/api/maps/sites")
def list_sites():
    """Return list of sites for the map viewer dropdown."""
    apisession = current_app.config.get("APISESSION")
    org_id = current_app.config.get("ORG_ID")
    if not apisession or not org_id:
        return jsonify({"sites": [], "error": "Not authenticated"})
    sites = _fetch_sites(apisession, org_id)
    return jsonify({"sites": sites})


@maps_bp.route("/api/maps/site/<site_id>/maps")
def list_site_maps(site_id):
    """Return list of maps for a specific site."""
    apisession = current_app.config.get("APISESSION")
    if not apisession:
        return jsonify({"maps": [], "error": "Not authenticated"})
    maps = _fetch_site_maps(apisession, site_id)
    return jsonify({"maps": maps})


@maps_bp.route("/api/maps/site/<site_id>/map/<map_id>/data")
def map_data(site_id, map_id):
    """Return map data with device positions for Plotly.js rendering."""
    apisession = current_app.config.get("APISESSION")
    if not apisession:
        return jsonify({"error": "Not authenticated"}), 401
    data = _fetch_map_data(apisession, site_id, map_id)
    if data is None:
        return jsonify({"error": "Map not found"}), 404
    return jsonify(data)


@maps_bp.route("/api/maps/image/<map_id>")
def map_image(map_id):
    """Serve a map background image."""
    apisession = current_app.config.get("APISESSION")
    if not apisession:
        return jsonify({"error": "Not authenticated"}), 401
    image_data = _fetch_map_image(apisession, map_id)
    if image_data is None:
        return jsonify({"error": "Image not found"}), 404
    from flask import Response

    return Response(
        image_data["content"],
        mimetype=image_data.get("content_type", "image/png"),
    )


def _fetch_sites(apisession, org_id: str) -> list:
    """Fetch site list from Mist API."""
    try:
        import mistapi

        response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
        sites = response.data if hasattr(response, "data") else []
        return [{"id": site.get("id", ""), "name": site.get("name", "")} for site in sites]
    except Exception:
        return []


def _fetch_site_maps(apisession, site_id: str) -> list:
    """Fetch map list for a specific site from Mist API."""
    try:
        import mistapi

        response = mistapi.api.v1.sites.maps.listSiteMaps(apisession, site_id)
        maps = response.data if hasattr(response, "data") else []
        return [
            {
                "id": m.get("id", ""),
                "name": m.get("name", ""),
                "width": m.get("width", 0),
                "height": m.get("height", 0),
                "has_image": bool(m.get("url")),
            }
            for m in maps
        ]
    except Exception:
        return []


def _fetch_map_data(apisession, site_id: str, map_id: str) -> dict:
    """Fetch map data with device positions for rendering."""
    try:
        import mistapi

        response = mistapi.api.v1.sites.maps.getSiteMap(apisession, site_id, map_id)
        map_info = response.data if hasattr(response, "data") else {}
        devices = _get_map_devices(apisession, site_id, map_id)
        return {
            "map_id": map_id,
            "name": map_info.get("name", ""),
            "image_url": f"/api/maps/image/{map_id}",
            "width": map_info.get("width", 0),
            "height": map_info.get("height", 0),
            "devices": devices,
        }
    except Exception:
        return None


def _get_map_devices(apisession, site_id: str, map_id: str) -> list:
    """Fetch devices positioned on a specific map."""
    try:
        import mistapi

        response = mistapi.api.v1.sites.devices.listSiteDevices(apisession, site_id, type="all")
        devices = response.data if hasattr(response, "data") else []
        return [
            {
                "id": d.get("id", ""),
                "name": d.get("name", ""),
                "type": d.get("type", "ap"),
                "x": d.get("x", 0),
                "y": d.get("y", 0),
                "mac": d.get("mac", ""),
            }
            for d in devices
            if d.get("map_id") == map_id
        ]
    except Exception:
        return []


def _fetch_map_image(apisession, map_id: str) -> dict:
    """Fetch map background image binary data."""
    try:
        import mistapi

        response = mistapi.api.v1.orgs.maps.getOrgMapImage(
            apisession,
            current_app.config.get("ORG_ID"),
            map_id,
        )
        if hasattr(response, "content"):
            return {
                "content": response.content,
                "content_type": "image/png",
            }
        return None
    except Exception:
        return None
