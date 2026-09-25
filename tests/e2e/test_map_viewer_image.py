"""Browser tests for the floor plan image of the Maps page (issue #3236).

Why:
    The image route called ``getOrgMapImage``, which the Mist SDK does not hold.
    Every map therefore drew the device markers on an empty field. An operator
    could not see the rooms and the walls behind the access points.

    These tests choose a site and a map the way an operator does. A simulated
    cloud serves a real PNG file, so the browser decodes the image and Plotly
    draws it.

How Plotly shows the image:
    Plotly loads a layout image with ``new Image()`` and draws it to a canvas.
    It then puts a ``data:image/png`` URL on the SVG ``image`` node. If the load
    fails, Plotly removes the node and shows no sign. The tests therefore read
    the ``href`` of the node, not the portal path.
"""

from __future__ import annotations

import logging
import socket
import struct
import threading
import zlib
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

logger = logging.getLogger(__name__)  # Keep the test log records on the module logger.

pytest.importorskip("playwright", reason="playwright is absent, so no browser test can run")

READY_TIMEOUT_MS = 15000  # One page load must not block the suite.
SETTLE_MS = 800  # Give a late image load time to draw, so a wrong draw shows before the check.
HOLD_TIMEOUT_S = 10.0  # The longest wait for a held server answer.

SITE_ID = "11111111-2222-3333-4444-555555555555"  # The one simulated site.
SITE_NAME = "Denver Branch"  # The site name in the picker.
IMAGE_MAP_ID = "aaaaaaaa-bbbb-cccc-dddd-000000000001"  # A floor plan with an image.
GOOGLE_MAP_ID = "aaaaaaaa-bbbb-cccc-dddd-000000000002"  # A Google map, which has no image.
IMAGE_URL = "https://api.mist.com/api/v1/forward/download?jwt=simulated-signed-value"  # The live link shape.
FLOOR_WIDTH = 600  # The floor plan width in pixels.
FLOOR_HEIGHT = 400  # The floor plan height in pixels.

NOTE_SELECTOR = "[data-testid=map-image-note]"  # The note that explains a missing image.
NO_IMAGE_NOTE = "This floor plan has no image. The map shows the device positions only."  # The Google map note.
IMAGE_FAILED_NOTE = (  # The note for a failed download.
    "The portal could not load the floor plan image. The map shows the device positions only."
)

MAP_RECORDS = [
    {
        "id": IMAGE_MAP_ID,
        "name": "Floor 1",
        "type": "image",
        "url": IMAGE_URL,
        "width": FLOOR_WIDTH,
        "height": FLOOR_HEIGHT,
    },
    {"id": GOOGLE_MAP_ID, "name": "Campus", "type": "google", "width": 200, "height": 150},
]  # One map of each shape.

DEVICES = [
    {"id": "d1", "name": "AP-LOBBY", "type": "ap", "x": 120, "y": 90, "mac": "aa01", "map_id": IMAGE_MAP_ID},
    {"id": "d2", "name": "AP-EAST", "type": "ap", "x": 450, "y": 260, "mac": "aa02", "map_id": IMAGE_MAP_ID},
    {"id": "d3", "name": "SW-IDF-1", "type": "switch", "x": 300, "y": 200, "mac": "aa03", "map_id": IMAGE_MAP_ID},
    {"id": "d4", "name": "AP-YARD", "type": "ap", "x": 50, "y": 40, "mac": "aa04", "map_id": GOOGLE_MAP_ID},
]  # Three devices on the floor plan and one on the Google map.

IMAGE_HREFS_JS = """
() => Array.from(document.querySelectorAll('#plotArea .imagelayer image')).map(
    node => node.getAttributeNS('http://www.w3.org/1999/xlink', 'href') || node.getAttribute('href') || '')
"""  # Read the href of each drawn layout image.
IMAGE_DRAWN_JS = f"() => ({IMAGE_HREFS_JS.strip()})().some(href => href.startsWith('data:image/png'))"  # Wait gate.
MARKER_COUNT_JS = "() => document.querySelectorAll('#plotArea .scatterlayer .point').length"  # Drawn markers.
PLOT_TITLE_JS = "() => (document.querySelector('#plotArea .gtitle') || {}).textContent || ''"  # The plot title.


def free_port() -> int:
    """Return a port that no other process holds right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:  # A short-lived socket finds the port.
        probe.bind(("127.0.0.1", 0))  # Port zero asks the operating system for a free port.
        return int(probe.getsockname()[1])  # Release the port for the test server.


def png_chunk(kind: bytes, body: bytes) -> bytes:
    """Frame one PNG chunk with its length and its checksum."""
    checksum = zlib.crc32(kind + body) & 0xFFFFFFFF  # PNG checks the type and the body together.
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", checksum)  # Length, type, body, CRC.


def build_floor_plan_png(width: int, height: int) -> bytes:
    """Build a real PNG file that shows a grid of rooms, like a simple floor plan."""
    wall, room = b"\x33\x33\x33", b"\xf2\xf2\xe6"  # Dark walls on a light floor.
    room_pixels = bytearray(room * width)  # One row that crosses the rooms.
    for column in list(range(0, width, 50)) + [width - 1]:  # A wall every 50 pixels and at the right edge.
        room_pixels[column * 3 : column * 3 + 3] = wall  # Paint one wall pixel in the row.
    wall_row, room_row = b"\x00" + wall * width, b"\x00" + bytes(room_pixels)  # Filter type 0 starts each row.
    rows = (wall_row if row % 50 == 0 or row == height - 1 else room_row for row in range(height))  # The grid.
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8-bit RGB, no interlace.
    body = zlib.compress(b"".join(rows))  # PNG stores the rows as one zlib stream.
    parts = [png_chunk(b"IHDR", header), png_chunk(b"IDAT", body), png_chunk(b"IEND", b"")]  # The 3 chunks.
    return b"\x89PNG\r\n\x1a\n" + b"".join(parts)  # The signature comes first.


class SimulatedDownload:
    """Stand in for one streamed ``requests`` answer from the storage host."""

    def __init__(self, status_code: int, content: bytes) -> None:
        """Store the status and the body."""
        self.status_code = status_code  # The status that the storage host answers.
        self.headers = {"Content-Type": "binary/octet-stream"}  # The storage host sends a generic type.
        self._content = content if status_code == 200 else b"<Error>AccessDenied</Error>"  # An XML error body.

    def iter_content(self, chunk_size: int = 1) -> Iterator[bytes]:
        """Yield the body in pieces, like a streamed answer."""
        for start in range(0, len(self._content), chunk_size):  # Walk the body one piece at a time.
            yield self._content[start : start + chunk_size]  # Give the route one piece.

    def close(self) -> None:
        """Release nothing, because no socket exists."""
        logger.debug("The simulated download closed")  # The route closes each streamed answer.


@dataclass
class SimulatedCloud:
    """Answer the SDK reads and the image download of the Maps page."""

    png: bytes  # The floor plan image that the storage host holds.
    download_status: int = 200  # 403 simulates an expired link.
    downloads: int = 0  # The number of image downloads that the route started.
    hold_stage: str = ""  # "data" holds the map read, and "image" holds the download.
    started: threading.Event = field(default_factory=threading.Event)  # The held answer began.
    release: threading.Event = field(default_factory=threading.Event)  # The test lets the held answer go.
    finished: threading.Event = field(default_factory=threading.Event)  # The held answer left the fake.

    def reset(self) -> None:
        """Return to a fast cloud with a valid link."""
        self.download_status, self.downloads, self.hold_stage = 200, 0, ""  # No failure and no hold.
        for event in (self.started, self.release, self.finished):  # Each test starts with clear events.
            event.clear()  # A set event from the last test would skip a wait.

    def hold_if(self, stage: str) -> None:
        """Hold the answer of one stage until the test releases it."""
        if self.hold_stage != stage:  # Only the chosen stage waits.
            return
        self.started.set()  # Tell the test that the slow answer began.
        self.release.wait(HOLD_TIMEOUT_S)  # Wait for the test, with a limit so no thread hangs.
        self.finished.set()  # Tell the test that the slow answer is about to leave.

    def list_org_sites(self, *_args: Any, **_kwargs: Any) -> SimpleNamespace:
        """Answer the site list like ``listOrgSites``."""
        return SimpleNamespace(status_code=200, data=[{"id": SITE_ID, "name": SITE_NAME}])  # One site.

    def list_site_maps(self, *_args: Any, **_kwargs: Any) -> SimpleNamespace:
        """Answer the map list like ``listSiteMaps``."""
        return SimpleNamespace(status_code=200, data=[dict(record) for record in MAP_RECORDS])  # Both maps.

    def get_site_map(self, _session: Any, _site_id: str, map_id: str) -> SimpleNamespace:
        """Answer one map read like ``getSiteMap``, and hold it when the test asks."""
        record = next((item for item in MAP_RECORDS if item["id"] == map_id), None)  # Find the map.
        if map_id == IMAGE_MAP_ID:  # Only the image map can be slow.
            self.hold_if("data")  # A slow read lets the operator choose another map first.
        return SimpleNamespace(status_code=200 if record else 404, data=dict(record or {}))  # The SDK shape.

    def list_site_devices(self, *_args: Any, **_kwargs: Any) -> SimpleNamespace:
        """Answer the device list like ``listSiteDevices``."""
        return SimpleNamespace(status_code=200, data=[dict(device) for device in DEVICES])  # Every device.

    def download(self, _url: str, **_options: Any) -> SimulatedDownload:
        """Answer the image download, and hold it when the test asks."""
        self.downloads += 1  # Count each download that reaches the storage host.
        self.hold_if("image")  # A slow download lets the operator choose another map first.
        return SimulatedDownload(self.download_status, self.png)  # The image, or an expired link.


@pytest.fixture(scope="module")
def simulated_cloud() -> SimulatedCloud:
    """Build one simulated cloud for the module."""
    return SimulatedCloud(png=build_floor_plan_png(FLOOR_WIDTH, FLOOR_HEIGHT))  # A real, decodable PNG file.


@pytest.fixture(scope="module")
def maps_portal(simulated_cloud: SimulatedCloud) -> Iterator[str]:
    """Serve the web portal with the simulated cloud in place of the Mist API."""
    import mistapi
    import requests
    from werkzeug.serving import make_server

    from web_portal.app import WebPortalApp
    from web_portal.menu_registry import build_static_menu_actions

    real_get = requests.get  # Keep the real call for any other URL.

    def routed_get(url: str, **options: Any) -> Any:
        """Send the floor plan link to the simulated storage host only."""
        if url == IMAGE_URL:  # The map record link.
            return simulated_cloud.download(url, **options)  # Answer from the simulated storage host.
        return real_get(url, **options)  # Leave every other caller unchanged.

    with pytest.MonkeyPatch.context() as patcher:  # Undo every patch when the module ends.
        patcher.setattr(mistapi.api.v1.orgs.sites, "listOrgSites", simulated_cloud.list_org_sites)  # Sites.
        patcher.setattr(mistapi.api.v1.sites.maps, "listSiteMaps", simulated_cloud.list_site_maps)  # Map list.
        patcher.setattr(mistapi.api.v1.sites.maps, "getSiteMap", simulated_cloud.get_site_map)  # One map.
        patcher.setattr(mistapi.api.v1.sites.devices, "listSiteDevices", simulated_cloud.list_site_devices)
        patcher.setattr(requests, "get", routed_get)  # The route downloads the image with requests.get.
        app = WebPortalApp.create_app(apisession=None, menu_actions=build_static_menu_actions(), org_id="test-org")
        app.config["TESTING"] = True  # Report route errors instead of hiding them.
        app.config["APISESSION"] = SimpleNamespace()  # The map routes only test that a session exists.
        server = make_server("127.0.0.1", free_port(), app, threaded=True)  # Never take a fixed port.
        thread = threading.Thread(target=server.serve_forever, daemon=True)  # Serve beside the browser.
        logger.info("Starting the maps portal on port %d", server.server_port)  # Name the port for triage.
        thread.start()  # Accept requests from the browser.
        try:
            yield f"http://127.0.0.1:{server.server_port}"  # The tests open pages under this address.
        finally:
            simulated_cloud.release.set()  # Free any held server thread before the shutdown.
            server.shutdown()  # Stop the request loop.
            thread.join(timeout=10)  # Wait for the loop to end.
            WebPortalApp.shutdown_app(app)  # Stop the background threads of the portal.


@pytest.fixture
def cloud(simulated_cloud: SimulatedCloud) -> Iterator[SimulatedCloud]:
    """Give each test a fast cloud, and free a held answer after the test."""
    simulated_cloud.reset()  # No failure and no hold from the last test.
    yield simulated_cloud  # The test changes the cloud as it needs.
    simulated_cloud.release.set()  # Never leave a server thread waiting after a test.


@pytest.fixture(scope="module")
def shot_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Return the folder for the screenshots of this module."""
    return tmp_path_factory.mktemp("map_shots")  # A reviewer reads each picture after the run.


def open_site(page: Any, portal: str) -> None:
    """Open the Maps page and choose the simulated site."""
    page.goto(f"{portal}/maps", wait_until="networkidle", timeout=READY_TIMEOUT_MS)  # Load the page.
    site_option = f"#siteSelect option[value='{SITE_ID}']"  # The site appears after the site list answers.
    page.wait_for_selector(site_option, state="attached", timeout=READY_TIMEOUT_MS)  # Wait for the list.
    page.select_option("#siteSelect", SITE_ID)  # Choose the site like an operator.
    map_option = f"#mapSelect option[value='{IMAGE_MAP_ID}']"  # The maps appear after the map list answers.
    page.wait_for_selector(map_option, state="attached", timeout=READY_TIMEOUT_MS)  # Wait for the maps.


def image_hrefs(page: Any) -> list[str]:
    """Return the href of each layout image that Plotly drew."""
    return list(page.evaluate(IMAGE_HREFS_JS))  # An empty list means that no image is on the plot.


def test_an_image_map_shows_the_floor_plan(page: Any, maps_portal: str, cloud: SimulatedCloud, shot_dir: Path) -> None:
    """US1: an operator sees the floor plan image behind the device markers."""
    open_site(page, maps_portal)  # Open the page and choose the site.
    page.select_option("#mapSelect", IMAGE_MAP_ID)  # Choose the floor plan.
    page.wait_for_function(IMAGE_DRAWN_JS, timeout=READY_TIMEOUT_MS)  # Plotly decoded and drew the image.
    page.screenshot(path=str(shot_dir / "01-image-map.png"), full_page=True)  # Keep the evidence.
    assert image_hrefs(page)[0].startswith("data:image/png")  # The real image is on the plot.
    assert page.evaluate(MARKER_COUNT_JS) == 3  # The three devices of the floor plan are on top.
    assert page.locator(NOTE_SELECTOR).is_hidden()  # No note, because nothing is missing.
    assert cloud.downloads == 1  # The browser cache serves the second read of the same image.


def test_a_map_with_no_image_shows_the_note(page: Any, maps_portal: str, cloud: SimulatedCloud, shot_dir: Path) -> None:
    """US2: a Google map draws the markers and says that the map has no image."""
    open_site(page, maps_portal)  # Open the page and choose the site.
    google_option = page.locator(f"#mapSelect option[value='{GOOGLE_MAP_ID}']")  # The Google map entry.
    assert google_option.inner_text() == "Campus (no image)"  # The list marks the map before the choice.
    page.select_option("#mapSelect", GOOGLE_MAP_ID)  # Choose the Google map.
    page.locator(NOTE_SELECTOR).wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # The note explains the plot.
    page.screenshot(path=str(shot_dir / "02-no-image-map.png"), full_page=True)  # Keep the evidence.
    assert page.locator(NOTE_SELECTOR).inner_text() == NO_IMAGE_NOTE  # One clear sentence.
    assert page.evaluate(MARKER_COUNT_JS) == 1  # The one device of the Google map is drawn.
    assert image_hrefs(page) == []  # No image, because none exists.
    assert cloud.downloads == 0  # The portal asks for no image that does not exist.


def test_a_failed_download_shows_the_failure_note(
    page: Any, maps_portal: str, cloud: SimulatedCloud, shot_dir: Path
) -> None:
    """US3: an expired link draws the markers and says that the image failed."""
    cloud.download_status = 403  # The storage host refuses the link.
    open_site(page, maps_portal)  # Open the page and choose the site.
    page.select_option("#mapSelect", IMAGE_MAP_ID)  # Choose the floor plan.
    page.locator(NOTE_SELECTOR).wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # The note explains the plot.
    page.screenshot(path=str(shot_dir / "03-failed-download.png"), full_page=True)  # Keep the evidence.
    assert page.locator(NOTE_SELECTOR).inner_text() == IMAGE_FAILED_NOTE  # The operator learns of the failure.
    assert page.evaluate(MARKER_COUNT_JS) == 3  # The device positions stay usable.
    assert image_hrefs(page) == []  # No broken image is on the plot.
    assert cloud.downloads >= 1  # The portal tried the download.


@pytest.mark.parametrize("stage", ["data", "image"])
def test_a_late_answer_never_replaces_the_newer_map(
    page: Any, maps_portal: str, cloud: SimulatedCloud, shot_dir: Path, stage: str
) -> None:
    """A slow answer for the first map must not draw over the second map."""
    cloud.hold_stage = stage  # Hold the map read or the image download of the floor plan.
    open_site(page, maps_portal)  # Open the page and choose the site.
    page.select_option("#mapSelect", IMAGE_MAP_ID)  # Choose the floor plan first.
    assert cloud.started.wait(HOLD_TIMEOUT_S)  # The server now holds the slow answer.
    page.select_option("#mapSelect", GOOGLE_MAP_ID)  # Choose the Google map before the answer arrives.
    page.wait_for_function(f"() => ({PLOT_TITLE_JS})() === 'Campus'", timeout=READY_TIMEOUT_MS)  # Map 2 is drawn.
    cloud.release.set()  # Let the slow answer for the floor plan go.
    assert cloud.finished.wait(HOLD_TIMEOUT_S)  # The slow answer left the server.
    page.wait_for_timeout(SETTLE_MS)  # Give a wrong draw time to appear.
    page.screenshot(path=str(shot_dir / f"04-late-{stage}.png"), full_page=True)  # Keep the evidence.
    assert page.evaluate(PLOT_TITLE_JS) == "Campus"  # The newer choice stays on the plot.
    assert page.evaluate(MARKER_COUNT_JS) == 1  # The markers belong to the Google map.
    assert image_hrefs(page) == []  # The floor plan image did not land on the Google map.
    assert page.locator(NOTE_SELECTOR).inner_text() == NO_IMAGE_NOTE  # The note still matches the plot.
