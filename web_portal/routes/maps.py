"""Map viewer routes for the MistHelper web portal.

Provides site listing, map enumeration, map data for Plotly.js
rendering, and map image serving. Replaces the standalone Dash viewer.

The Mist API has no GET operation for a map image. A map record holds the
image location in its read-only field ``url``. The link carries a ``jwt``
query parameter, so the download needs no API token. The portal downloads the
image and serves it from its own origin, because the page policy allows an
image from the portal origin only. See issue #3236.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

import requests
from flask import Blueprint, Response, current_app, jsonify, render_template, url_for

logger = logging.getLogger(__name__)  # Use a module logger so map failures name this route module.

maps_bp = Blueprint("maps", __name__)  # The map page and the map JSON routes share one blueprint.

UUID_PATTERN = re.compile(r"[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}")  # The Mist identifier form.
MAP_NOT_FOUND_MESSAGE = "Map not found"  # The answer for a map that the read cannot find.
IMAGE_CACHE_CONTROL = "private, max-age=300"  # The browser keeps one floor plan for 5 minutes.


class DownloadLinkLogFilter(logging.Filter):
    """Hide the secret values of a download link in a urllib3 debug line.

    urllib3 logs each request path at DEBUG level. The floor plan link holds a
    ``jwt`` value. The Mist link then redirects to a signed storage link that
    holds an AWS credential, a session token, and a signature. Each value grants
    access to the file, so a DEBUG run would write them to the log without this
    filter.
    """

    SECRET_VALUE = re.compile(
        r"((?:jwt|X-Amz-Credential|X-Amz-Security-Token|X-Amz-Signature)=)[^&\s\"']+", re.IGNORECASE
    )  # The value ends at the next parameter, a space, or a quote.
    SECRET_MARKERS = ("jwt=", "x-amz-")  # A fast test that skips the lines that hold no link secret.

    def filter(self, record: logging.LogRecord) -> bool:
        """Replace each secret link value in the record, and keep the record."""
        try:
            message = record.getMessage()  # Render the final text one time.
        except (TypeError, ValueError):  # A malformed record holds no text to clean, and it must not break a request.
            return True
        lowered = message.lower()  # The storage parameter names can arrive in any case.
        if any(marker in lowered for marker in self.SECRET_MARKERS):  # Most urllib3 lines hold no link secret.
            record.msg = self.SECRET_VALUE.sub(r"\1***REDACTED***", message)  # Keep the key, and hide the value.
            record.args = ()  # The message is already rendered.
        return True  # Never drop a record. Only clean it.


logging.getLogger("urllib3.connectionpool").addFilter(DownloadLinkLogFilter())  # urllib3 logs the request path.


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
        return jsonify({"error": MAP_NOT_FOUND_MESSAGE}), 404
    return jsonify(data)


@maps_bp.route("/api/maps/site/<site_id>/map/<map_id>/image")
def map_image(site_id, map_id):
    """Serve the floor plan image of one map from the portal origin."""
    apisession = current_app.config.get("APISESSION")  # The map read needs the Mist session.
    if not apisession:  # A portal with no session cannot read the map record.
        return jsonify({"error": "Not authenticated"}), 401
    if not (UUID_PATTERN.fullmatch(site_id) and UUID_PATTERN.fullmatch(map_id)):  # Refuse a strange path value.
        return jsonify({"error": MAP_NOT_FOUND_MESSAGE}), 404  # The same answer as an unknown map.
    logger.info("Serving the floor plan image of site %s map %s", site_id, map_id)  # Both values are UUIDs now.
    result = MapImageSource.fetch(apisession, site_id, map_id)  # Read the map, then download its image.
    logger.debug("The floor plan image of map %s answered %d", map_id, result.status)  # Log the outcome.
    if result.status != 200:  # A missing map, a map with no image, or a failed download.
        return jsonify({"error": result.error}), result.status
    answer = Response(result.content, mimetype=result.mimetype)  # Serve the bytes with the proven type.
    answer.headers["Cache-Control"] = IMAGE_CACHE_CONTROL  # A second view within 5 minutes reads the browser cache.
    return answer


def _fetch_sites(apisession, org_id: str) -> list:
    """Fetch site list from Mist API."""
    try:
        import mistapi

        response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id)
        sites = response.data if hasattr(response, "data") else []
        return [{"id": site.get("id", ""), "name": site.get("name", "")} for site in sites]
    except Exception as error:  # Keep the map selector usable when the Mist API request fails.
        logger.exception(
            "Map site list failed for org %s with %s: %s", org_id, type(error).__name__, error
        )  # Log the exception class and text for issue triage.
        return []


def _fetch_site_maps(apisession, site_id: str) -> list:
    """Fetch map list for a specific site from Mist API."""
    try:
        import mistapi  # Import on first use, like the other map helpers of this module.

        logger.info("Fetching the map list of site %s", site_id)  # Log before the API call.
        response = mistapi.api.v1.sites.maps.listSiteMaps(apisession, site_id)  # Every map of the site.
        maps = response.data if hasattr(response, "data") else []  # The SDK answer carries the list in data.
        logger.debug("Received %d maps for site %s", len(maps), site_id)  # Log the count after the call.
        return [
            {
                "id": m.get("id", ""),  # The page sends this identifier back for the map data.
                "name": m.get("name", ""),  # The picker shows this name.
                "width": m.get("width", 0),  # The plot width in map pixels.
                "height": m.get("height", 0),  # The plot height in map pixels.
                "has_image": bool(MapImageSource.image_url_of(m)),  # The same image rule as the data answer.
            }
            for m in maps
        ]
    except Exception as error:  # Keep the map selector usable when one site map request fails.
        logger.exception(
            "Site map list failed for site %s with %s: %s", site_id, type(error).__name__, error
        )  # Log the exception class and text for issue triage.
        return []


def _fetch_map_data(apisession, site_id: str, map_id: str) -> dict | None:
    """Fetch map data with device positions for rendering."""
    try:
        import mistapi  # Import on first use, like the other map helpers of this module.

        logger.info("Fetching map %s of site %s", map_id, site_id)  # Log before the API call.
        response = mistapi.api.v1.sites.maps.getSiteMap(apisession, site_id, map_id)  # One map record.
        map_info = response.data if hasattr(response, "data") else {}  # The SDK answer carries the record.
        devices = _get_map_devices(apisession, site_id, map_id)  # The devices placed on this map.
        image_url = ""  # A map with no https image names no path, so the page asks for no image.
        if MapImageSource.image_url_of(map_info):  # Only an image map with an https link has a floor plan.
            image_url = url_for("maps.map_image", site_id=site_id, map_id=map_id)  # The portal image path.
        logger.debug("Map %s holds %d devices and image %s", map_id, len(devices), bool(image_url))  # Result.
        return {
            "map_id": map_id,  # The page checks that the answer belongs to its choice.
            "name": map_info.get("name", ""),  # The plot title.
            "image_url": image_url,  # The portal path, never the signed link.
            "width": map_info.get("width", 0),  # The plot width in map pixels.
            "height": map_info.get("height", 0),  # The plot height in map pixels.
            "devices": devices,  # The markers of the plot.
        }
    except Exception as error:  # Let the caller return 404 instead of raising a remote API failure.
        logger.exception(
            "Map data fetch failed for site %s map %s with %s: %s", site_id, map_id, type(error).__name__, error
        )  # Log the exception class and text for issue triage.
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
    except Exception as error:  # Keep map rendering usable when one device list request fails.
        logger.exception(
            "Map device list failed for site %s map %s with %s: %s", site_id, map_id, type(error).__name__, error
        )  # Log the exception class and text for issue triage.
        return []


@dataclass(frozen=True)
class MapImageResult:
    """Hold the outcome of one floor plan image request."""

    status: int  # The HTTP status of the portal answer.
    error: str = ""  # The one sentence that the page reads when the portal refuses.
    content: bytes = b""  # The image bytes when the download works.
    mimetype: str = ""  # The image type that the first bytes prove.


class MapImageSource:
    """Read a map record and decide the answer of the floor plan image path."""

    NO_IMAGE_MESSAGE = "This floor plan has no image."  # The answer for a map with no https image.
    DOWNLOAD_FAILED_MESSAGE = "The portal could not download the floor plan image."  # The answer for a 502.

    @staticmethod
    def image_url_of(record: dict[str, Any]) -> str:
        """Return the https image URL of a map record, or an empty string.

        Only an image map holds a floor plan file. A Google map, or a map with a
        plain http link, gives an empty string, so the page asks for no image.
        """
        if record.get("type", "image") != "image":  # A Google map has no floor plan file.
            return ""
        url = record.get("url") or ""  # The read-only field that the Mist cloud writes.
        return url if isinstance(url, str) and url.startswith("https://") else ""  # Refuse plain http.

    @staticmethod
    def read_record(apisession: Any, site_id: str, map_id: str) -> dict[str, Any] | None:
        """Read one map record, or return None when the read fails or finds no map."""
        import mistapi  # Import on first use, like the other map helpers of this module.

        logger.info("Reading map %s of site %s for its image", map_id, site_id)  # Log before the API call.
        try:
            response = mistapi.api.v1.sites.maps.getSiteMap(apisession, site_id, map_id)  # One map record.
        except Exception as error:  # Answer a clean 404 when the Mist API request fails.
            logger.exception("The map read failed for map %s with %s", map_id, type(error).__name__)
            return None
        record = getattr(response, "data", None)  # The SDK answer carries the record in data.
        found = getattr(response, "status_code", 0) == 200 and isinstance(record, dict) and bool(record)
        logger.debug("The map read for map %s found a record: %s", map_id, found)  # Log the result.
        return record if found else None  # An empty or failed read counts as no map.

    @classmethod
    def fetch(cls, apisession: Any, site_id: str, map_id: str) -> MapImageResult:
        """Read the map, download its image, and decide the answer of the path."""
        record = cls.read_record(apisession, site_id, map_id)  # The record names the image link.
        if record is None:  # The read failed or found no map.
            return MapImageResult(status=404, error=MAP_NOT_FOUND_MESSAGE)
        url = cls.image_url_of(record)  # Only an https image link can serve a floor plan.
        if not url:  # A Google map or a plain http link.
            return MapImageResult(status=404, error=cls.NO_IMAGE_MESSAGE)
        content = MapImageDownloader.download(url) or b""  # Empty bytes mean a failed download.
        mimetype = MapImageDownloader.image_type_of(content)  # Prove the type from the first bytes.
        if not mimetype:  # A failure, an HTML page, an SVG file, or empty bytes.
            logger.warning("The floor plan of map %s is not a usable raster image", map_id)  # Name the map only.
            return MapImageResult(status=502, error=cls.DOWNLOAD_FAILED_MESSAGE)
        return MapImageResult(status=200, content=content, mimetype=mimetype)  # A proven raster image.


class MapImageDownloader:
    """Download a floor plan image and prove that the bytes are a raster image.

    Warning: never log the download link or a network exception text. The link
    holds a ``jwt`` value, and that value opens the image for anyone who holds it.
    """

    MAX_BYTES = 25 * 1024 * 1024  # A larger file is not a floor plan, and it would fill the portal memory.
    CHUNK_BYTES = 64 * 1024  # Read the stream in 64 KiB pieces, so the size limit applies early.
    TIMEOUT = (5, 30)  # 5 seconds to connect and 30 seconds to read, so a slow host cannot hold a thread.
    SIGNATURES = (
        (b"\x89PNG\r\n\x1a\n", "image/png"),
        (b"\xff\xd8\xff", "image/jpeg"),
        (b"GIF87a", "image/gif"),
        (b"GIF89a", "image/gif"),
    )  # The first bytes of each raster type that a browser draws safely.

    @classmethod
    def download(cls, url: str) -> bytes | None:
        """Download the image bytes, or return None when the download fails.

        The link carries its own ``jwt``, so the call sends no API token. The
        call follows the redirect to the storage host.
        """
        logger.info("Downloading one floor plan image")  # Log before the network call, without the link.
        answer = None  # No answer exists until the connection opens.
        try:
            answer = requests.get(url, timeout=cls.TIMEOUT, stream=True)  # Send no header and no credential.
            return cls.read_body(answer)  # Apply the status rule and the size limit.
        except requests.RequestException as error:  # A refused connection, a timeout, or a broken stream.
            # Log the class only. The exception text of requests quotes the URL with its jwt value.
            logger.error("The floor plan download failed with %s", type(error).__name__)
            return None
        finally:
            if answer is not None:  # A connection opened, so release it.
                answer.close()  # A streamed answer holds a connection until it closes.

    @classmethod
    def read_body(cls, answer: Any) -> bytes | None:
        """Read a streamed answer up to the size limit, or return None."""
        if answer.status_code != 200:  # An expired link answers 403, and a long redirect chain ends as 3xx.
            logger.warning("The floor plan download answered %d", answer.status_code)  # The status only.
            return None
        content = bytearray()  # Collect the pieces in one growing buffer.
        for chunk in answer.iter_content(cls.CHUNK_BYTES):  # Read the body one piece at a time.
            content.extend(chunk)  # Add the piece to the buffer.
            if len(content) > cls.MAX_BYTES:  # Stop before a huge file fills the memory.
                logger.warning("The floor plan image is larger than %d bytes", cls.MAX_BYTES)  # Name the limit.
                return None
        logger.debug("Downloaded %d floor plan bytes", len(content))  # Log the size after the read.
        return bytes(content)  # Give the caller an immutable copy.

    @classmethod
    def image_type_of(cls, content: bytes) -> str:
        """Return the image type that the first bytes prove, or an empty string.

        The storage host sends a generic content type, so the portal reads the
        signature instead. SVG and HTML can hold script, so the portal never
        serves them from its own origin.
        """
        for signature, mimetype in cls.SIGNATURES:  # Check each raster signature in turn.
            if content.startswith(signature):  # The file header names the real type.
                return mimetype
        if content[:4] == b"RIFF" and content[8:12] == b"WEBP":  # WebP wraps its data in a RIFF container.
            return "image/webp"
        return ""  # Refuse every other type.
