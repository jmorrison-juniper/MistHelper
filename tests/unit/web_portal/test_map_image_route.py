"""Route tests for the floor plan image of the Maps page (issue #3236).

The image route called ``mistapi.api.v1.orgs.maps.getOrgMapImage``, which the
installed SDK does not hold. The route raised ``AttributeError`` and answered
404, so the Maps page never showed a floor plan.

The Mist API has no GET operation for a map image. The map record carries the
image location in its read-only field ``url``. A live probe on 2026-09-25 shows
that the field points to ``https://api.mist.com`` with one ``jwt`` query
parameter, and that a download with no credential answers 200 after one
redirect to the storage host.

These tests use a bare Flask app, a fake SDK, and a fake download, so they need
no network and no Mist credential.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

import mistapi
import pytest
import requests
from flask import Flask

from web_portal.routes import maps as maps_module
from web_portal.routes.maps import maps_bp

logger = logging.getLogger(__name__)  # Keep the test log records on the module logger.

SITE_ID = "11111111-2222-3333-4444-555555555555"  # A site identifier in the Mist UUID form.
IMAGE_MAP_ID = "aaaaaaaa-bbbb-cccc-dddd-000000000001"  # A floor plan with an image.
GOOGLE_MAP_ID = "aaaaaaaa-bbbb-cccc-dddd-000000000002"  # A Google map, which has no image.
PLAIN_HTTP_MAP_ID = "aaaaaaaa-bbbb-cccc-dddd-000000000003"  # An image map with a plain http link.
UNKNOWN_MAP_ID = "aaaaaaaa-bbbb-cccc-dddd-000000000004"  # A map that the site does not hold.
JWT_VALUE = "signed-value-that-must-not-reach-a-log"  # The secret part of the download link.
IMAGE_URL = f"https://api.mist.com/api/v1/forward/download?jwt={JWT_VALUE}"  # The live link shape.

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64  # The PNG signature and a short body.
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 64  # The JPEG signature and a short body.
GIF87_BYTES = b"GIF87a" + b"\x00" * 64  # The first GIF signature.
GIF89_BYTES = b"GIF89a" + b"\x00" * 64  # The second GIF signature.
WEBP_BYTES = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 64  # The WebP container signature.
HTML_BYTES = b"<!doctype html><script>alert(1)</script>"  # A page that must never reach the portal origin.
SVG_BYTES = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'  # An image that holds script.

IMAGE_PATH = f"/api/maps/site/{SITE_ID}/map/{IMAGE_MAP_ID}/image"  # The new portal image path.
NO_IMAGE_MESSAGE = "This floor plan has no image."  # The body of the no-image answer.
DOWNLOAD_FAILED_MESSAGE = "The portal could not download the floor plan image."  # The body of a 502 answer.
MAP_NOT_FOUND_MESSAGE = "Map not found"  # The body of a failed map read.
CACHE_CONTROL = "private, max-age=300"  # The browser keeps the image for 5 minutes.

MAP_RECORDS = [
    {"id": IMAGE_MAP_ID, "name": "Floor 1", "type": "image", "url": IMAGE_URL, "width": 1539, "height": 1007},
    {"id": GOOGLE_MAP_ID, "name": "Campus", "type": "google", "width": 0, "height": 0},
    {"id": PLAIN_HTTP_MAP_ID, "name": "Old floor", "type": "image", "url": "http://example.test/a.png"},
]  # The three map shapes that the route must tell apart.


class FakeDownload:
    """Stand in for one streamed ``requests`` answer."""

    def __init__(self, status_code: int = 200, chunks: tuple[bytes, ...] = (PNG_BYTES,), header: str = "") -> None:
        """Store the status, the body chunks, and the upstream content type."""
        self.status_code = status_code  # The status that the storage host answers.
        self.headers = {"Content-Type": header or "image/png"}  # The upstream header, which the route must not trust.
        self._chunks = list(chunks)  # The body in the order that the stream yields it.
        self.closed = False  # The route must close a streamed answer.

    def iter_content(self, chunk_size: int = 1) -> Any:
        """Yield the body chunks, like a streamed answer."""
        yield from self._chunks  # The route reads the chunks until the size limit.

    def close(self) -> None:
        """Record that the route released the connection."""
        self.closed = True  # A streamed answer holds a connection until it closes.


@dataclass
class DownloadRecorder:
    """Record each download that the route starts, and answer with one reply."""

    reply: Any = field(default_factory=FakeDownload)  # A FakeDownload, or an exception to raise.
    calls: list[tuple[str, dict[str, Any]]] = field(default_factory=list)  # The URL and the options of each call.

    def get(self, url: str, **options: Any) -> Any:
        """Stand in for ``requests.get``."""
        self.calls.append((url, options))  # Keep the options, because the test checks the limits.
        if isinstance(self.reply, BaseException):  # A network failure raises instead of answering.
            raise self.reply
        return self.reply


@dataclass
class FakeMapsApi:
    """Stand in for the map reads of the Mist SDK."""

    records: list[dict[str, Any]]  # The maps of the one test site.
    reads: int = 0  # The number of single map reads, which a refusal must keep at zero.
    failure: BaseException | None = None  # An exception for a map read that fails.

    def get_site_map(self, _session: Any, _site_id: str, map_id: str) -> SimpleNamespace:
        """Answer one map read like ``getSiteMap``."""
        self.reads += 1  # Count the read before a failure, like the real call.
        if self.failure is not None:  # A network or SDK failure raises.
            raise self.failure
        record = next((item for item in self.records if item["id"] == map_id), None)  # Find the map.
        return SimpleNamespace(status_code=200 if record else 404, data=record or {})  # The SDK answer shape.

    def list_site_maps(self, _session: Any, _site_id: str) -> SimpleNamespace:
        """Answer one map list like ``listSiteMaps``."""
        return SimpleNamespace(status_code=200, data=list(self.records))  # Every map of the site.


@pytest.fixture
def maps_api(monkeypatch: pytest.MonkeyPatch) -> FakeMapsApi:
    """Replace the SDK map reads and the device list with fakes."""
    fake = FakeMapsApi(records=[dict(record) for record in MAP_RECORDS])  # Copy, so a test can change a record.
    monkeypatch.setattr(mistapi.api.v1.sites.maps, "getSiteMap", fake.get_site_map)  # The single map read.
    monkeypatch.setattr(mistapi.api.v1.sites.maps, "listSiteMaps", fake.list_site_maps)  # The map list.
    no_devices = SimpleNamespace(status_code=200, data=[])  # The data answer also reads the devices.
    monkeypatch.setattr(mistapi.api.v1.sites.devices, "listSiteDevices", lambda *_a, **_k: no_devices)
    return fake


@pytest.fixture
def downloads(monkeypatch: pytest.MonkeyPatch) -> DownloadRecorder:
    """Replace the image download with a recorder."""
    recorder = DownloadRecorder()  # The default reply is a PNG image.
    monkeypatch.setattr(requests, "get", recorder.get)  # The route downloads with requests.get.
    return recorder


@pytest.fixture
def client(maps_api: FakeMapsApi, downloads: DownloadRecorder) -> Any:
    """Serve the maps blueprint from a bare Flask app with a fake session."""
    app = Flask(__name__)  # A bare app avoids the portal factory and its threads.
    app.config["APISESSION"] = SimpleNamespace()  # The routes only test that a session exists.
    app.config["ORG_ID"] = "test-org"  # The site list reads the organization.
    app.register_blueprint(maps_bp)  # Register the routes under test only.
    return app.test_client()


class TestTheMapDataNamesTheImage:
    """The data answer names the portal image path only for a real image."""

    def test_an_image_map_names_the_site_image_path(self, client: Any) -> None:
        """FR-001: an image map names the new site-scoped portal path."""
        answer = client.get(f"/api/maps/site/{SITE_ID}/map/{IMAGE_MAP_ID}/data")  # Read the map data.
        assert answer.status_code == 200  # The data read works.
        assert answer.get_json()["image_url"] == IMAGE_PATH  # The page asks this path for the image.

    @pytest.mark.parametrize("map_id", [GOOGLE_MAP_ID, PLAIN_HTTP_MAP_ID, UNKNOWN_MAP_ID])
    def test_a_map_with_no_usable_image_names_no_path(self, client: Any, map_id: str) -> None:
        """FR-001: a map with no https image names an empty path."""
        answer = client.get(f"/api/maps/site/{SITE_ID}/map/{map_id}/data")  # Read the map data.
        assert answer.get_json()["image_url"] == ""  # The page must not ask for an image that does not exist.

    def test_the_map_list_marks_only_the_https_image_map(self, client: Any) -> None:
        """FR-006: the list uses the same image rule as the data answer."""
        answer = client.get(f"/api/maps/site/{SITE_ID}/maps")  # Read the map list.
        marks = {item["id"]: item["has_image"] for item in answer.get_json()["maps"]}  # One mark for each map.
        assert marks == {IMAGE_MAP_ID: True, GOOGLE_MAP_ID: False, PLAIN_HTTP_MAP_ID: False}  # One rule for both.


class TestTheImagePathServesTheImage:
    """The image path downloads the bytes and serves them from the portal origin."""

    def test_the_path_serves_the_png_bytes(self, client: Any, downloads: DownloadRecorder) -> None:
        """FR-002 and FR-005: the answer holds the bytes and the cache rule."""
        answer = client.get(IMAGE_PATH)  # Ask for the floor plan image.
        assert answer.status_code == 200  # The download worked.
        assert answer.mimetype == "image/png"  # The type comes from the signature.
        assert answer.data == PNG_BYTES  # The portal serves the bytes unchanged.
        assert answer.headers["Cache-Control"] == CACHE_CONTROL  # One map view downloads the image one time.
        assert downloads.reply.closed is True  # The route released the streamed connection.

    def test_the_download_sends_no_credential(self, client: Any, downloads: DownloadRecorder) -> None:
        """FR-003: the jwt link needs no token, so the route sends none."""
        client.get(IMAGE_PATH)  # Ask for the floor plan image.
        assert len(downloads.calls) == 1  # One image request makes one download.
        url, options = downloads.calls[0]  # The only download of this request.
        assert url == IMAGE_URL  # The route downloads the link of the map record.
        assert "Authorization" not in (options.get("headers") or {})  # The token never leaves for the image host.
        assert "auth" not in options  # No other credential form leaves either.

    def test_the_download_has_time_limits_and_streams(self, client: Any, downloads: DownloadRecorder) -> None:
        """FR-003: a slow host cannot hold a portal thread without a limit."""
        client.get(IMAGE_PATH)  # Ask for the floor plan image.
        assert len(downloads.calls) == 1  # One image request makes one download.
        options = downloads.calls[0][1]  # The options of the only download.
        assert options["timeout"] == (5, 30)  # 5 seconds to connect and 30 seconds to read.
        assert options["stream"] is True  # The route reads the body in chunks to apply the size limit.
        assert options.get("allow_redirects", True) is True  # The jwt link redirects to the storage host.

    @pytest.mark.parametrize(
        ("content", "expected"),
        [
            (PNG_BYTES, "image/png"),
            (JPEG_BYTES, "image/jpeg"),
            (GIF87_BYTES, "image/gif"),
            (GIF89_BYTES, "image/gif"),
            (WEBP_BYTES, "image/webp"),
        ],
        ids=["png", "jpeg", "gif87a", "gif89a", "webp"],
    )
    def test_the_first_bytes_decide_the_type(
        self, client: Any, downloads: DownloadRecorder, content: bytes, expected: str
    ) -> None:
        """FR-004: a generic upstream header does not stop a real image."""
        downloads.reply = FakeDownload(chunks=(content,), header="binary/octet-stream")  # A generic storage header.
        answer = client.get(IMAGE_PATH)  # Ask for the floor plan image.
        assert answer.status_code == 200  # The signature proves the image.
        assert answer.mimetype == expected  # The portal names the real type.


class TestTheImagePathRefusesABadDownload:
    """A failed download answers 502 and never serves the bytes."""

    @pytest.mark.parametrize("content", [HTML_BYTES, SVG_BYTES, b""], ids=["html", "svg", "empty"])
    def test_bytes_that_are_not_a_raster_image_are_refused(
        self, client: Any, downloads: DownloadRecorder, content: bytes
    ) -> None:
        """FR-004: HTML or SVG bytes from the portal origin could run script."""
        downloads.reply = FakeDownload(chunks=(content,), header="image/png")  # A false upstream header.
        answer = client.get(IMAGE_PATH)  # Ask for the floor plan image.
        assert answer.status_code == 502  # The portal refuses the bytes.
        assert answer.get_json() == {"error": DOWNLOAD_FAILED_MESSAGE}  # The page reads one clear sentence.
        assert downloads.reply.closed is True  # The route released the connection on a refusal too.

    def test_an_image_over_the_size_limit_is_refused(
        self, client: Any, downloads: DownloadRecorder, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """FR-003: a huge answer cannot fill the portal memory."""
        monkeypatch.setattr(maps_module.MapImageDownloader, "MAX_BYTES", 100)  # A small limit keeps the test fast.
        downloads.reply = FakeDownload(chunks=(PNG_BYTES, b"\x00" * 64))  # 136 bytes, over the limit.
        answer = client.get(IMAGE_PATH)  # Ask for the floor plan image.
        assert answer.status_code == 502  # The portal stops the read at the limit.
        assert downloads.reply.closed is True  # The route released the connection.

    @pytest.mark.parametrize("status", [301, 403, 404, 500])
    def test_an_upstream_failure_status_is_refused(self, client: Any, downloads: DownloadRecorder, status: int) -> None:
        """US3: an expired link answers 403, and the page must learn of it."""
        downloads.reply = FakeDownload(status_code=status)  # The storage host refuses the link.
        answer = client.get(IMAGE_PATH)  # Ask for the floor plan image.
        assert answer.status_code == 502  # The portal reports a failed download.

    @pytest.mark.parametrize(
        "failure", [requests.ConnectionError("down"), requests.Timeout("slow")], ids=["connection", "timeout"]
    )
    def test_a_network_failure_is_refused(
        self, client: Any, downloads: DownloadRecorder, failure: BaseException
    ) -> None:
        """US3: a network failure answers 502 instead of a server error."""
        downloads.reply = failure  # The download raises.
        answer = client.get(IMAGE_PATH)  # Ask for the floor plan image.
        assert answer.status_code == 502  # The portal reports a failed download.
        assert answer.get_json() == {"error": DOWNLOAD_FAILED_MESSAGE}  # The page reads one clear sentence.


class TestTheImagePathRefusesAMapWithNoImage:
    """A map with no image, or a map that the read cannot find, answers 404."""

    @pytest.mark.parametrize("map_id", [GOOGLE_MAP_ID, PLAIN_HTTP_MAP_ID])
    def test_a_map_with_no_https_image_answers_404(self, client: Any, downloads: DownloadRecorder, map_id: str) -> None:
        """US2: the route downloads nothing for a map with no usable image."""
        answer = client.get(f"/api/maps/site/{SITE_ID}/map/{map_id}/image")  # Ask for an image that is absent.
        assert answer.status_code == 404  # No image exists.
        assert answer.get_json() == {"error": NO_IMAGE_MESSAGE}  # The body names the cause.
        assert downloads.calls == []  # The route starts no download.

    def test_a_map_that_the_read_cannot_find_answers_404(self, client: Any, downloads: DownloadRecorder) -> None:
        """A map read that answers 404 gives the same map-not-found answer."""
        answer = client.get(f"/api/maps/site/{SITE_ID}/map/{UNKNOWN_MAP_ID}/image")  # An unknown map.
        assert answer.status_code == 404  # The map does not exist.
        assert answer.get_json() == {"error": MAP_NOT_FOUND_MESSAGE}  # The body names the cause.
        assert downloads.calls == []  # The route starts no download.

    def test_a_map_read_that_raises_answers_404(
        self, client: Any, maps_api: FakeMapsApi, downloads: DownloadRecorder
    ) -> None:
        """A failed SDK call gives the map-not-found answer, not a server error."""
        maps_api.failure = RuntimeError("the cloud is down")  # The SDK call raises.
        answer = client.get(IMAGE_PATH)  # Ask for the floor plan image.
        assert answer.status_code == 404  # The route catches the failure.
        assert answer.get_json() == {"error": MAP_NOT_FOUND_MESSAGE}  # The body names the cause.

    @pytest.mark.parametrize(
        "path",
        [
            f"/api/maps/site/not-a-uuid/map/{IMAGE_MAP_ID}/image",
            f"/api/maps/site/{SITE_ID}/map/not-a-uuid/image",
            f"/api/maps/site/{SITE_ID.upper()}x/map/{IMAGE_MAP_ID}/image",
        ],
        ids=["bad-site", "bad-map", "site-with-suffix"],
    )
    def test_an_identifier_that_is_not_a_uuid_makes_no_call(
        self, client: Any, maps_api: FakeMapsApi, path: str
    ) -> None:
        """FR-008: a strange identifier never reaches the SDK path."""
        answer = client.get(path)  # Ask with a bad identifier.
        assert answer.status_code == 404  # The route refuses the identifier.
        assert answer.get_json() == {"error": MAP_NOT_FOUND_MESSAGE}  # The same answer as an unknown map.
        assert maps_api.reads == 0  # The route made no API call.

    def test_the_path_needs_a_session(self, client: Any) -> None:
        """The image path answers 401 with no API session, like the data path."""
        client.application.config["APISESSION"] = None  # The portal holds no session.
        answer = client.get(IMAGE_PATH)  # Ask for the floor plan image.
        assert answer.status_code == 401  # The route refuses before any read.


class TestTheOldPathIsGone:
    """The old path never worked, so no compatibility path stays."""

    def test_the_old_image_rule_is_not_registered(self, client: Any) -> None:
        """D3: the blueprint registers only the site-scoped image path."""
        rules = {rule.rule for rule in client.application.url_map.iter_rules()}  # Every registered path.
        assert "/api/maps/image/<map_id>" not in rules  # The broken path is gone.
        assert "/api/maps/site/<site_id>/map/<map_id>/image" in rules  # The new path exists.


class TestTheLogsHoldNoSecret:
    """The logs name the site and the map, never the download link."""

    @pytest.mark.parametrize(
        "reply",
        [
            FakeDownload(),
            FakeDownload(status_code=403),
            requests.ConnectionError(f"Max retries exceeded with url: {IMAGE_URL}"),
        ],
        ids=["image", "refused", "connection-text-quotes-the-link"],
    )
    def test_no_log_record_names_the_jwt(
        self, client: Any, downloads: DownloadRecorder, caplog: pytest.LogCaptureFixture, reply: Any
    ) -> None:
        """The jwt value opens the image for anyone, so no log may hold it."""
        downloads.reply = reply  # A success, a refusal, or a network failure whose text quotes the link.
        with caplog.at_level(logging.DEBUG):  # Capture every level, because a debug line can leak too.
            client.get(IMAGE_PATH)  # Ask for the floor plan image.
        assert caplog.records  # The route logs its actions, so the check reads real lines.
        assert JWT_VALUE not in caplog.text  # No line holds the secret.

    def test_a_urllib3_debug_line_hides_the_jwt(self, caplog: pytest.LogCaptureFixture) -> None:
        """urllib3 logs each request path at DEBUG level, so the module hides the jwt value."""
        pool_logger = logging.getLogger("urllib3.connectionpool")  # The logger that writes each request path.
        path = IMAGE_URL.removeprefix("https://api.mist.com")  # The path and the query, like urllib3 logs them.
        with caplog.at_level(logging.DEBUG, logger="urllib3.connectionpool"):  # Capture the debug line.
            pool_logger.debug(
                '%s://%s:%s "%s %s %s" %s %s', "https", "api.mist.com", 443, "GET", path, "HTTP/1.1", 302, 0
            )
        assert "jwt=***REDACTED***" in caplog.text  # The line keeps its shape for triage.
        assert JWT_VALUE not in caplog.text  # The value never reaches a handler.

    def test_a_urllib3_debug_line_hides_the_storage_signature(self, caplog: pytest.LogCaptureFixture) -> None:
        """The Mist link redirects to a signed storage link, and urllib3 logs that path too."""
        pool_logger = logging.getLogger("urllib3.connectionpool")  # The logger that writes each request path.
        secrets = {  # Each value grants access to the file until the link expires.
            "X-Amz-Credential": "TESTKEYID%2F20260925%2Fus-east-1%2Fs3%2Faws4_request",
            "X-Amz-Security-Token": "TESTSESSIONTOKENVALUE",
            "x-amz-signature": "0123456789abcdef0123456789abcdef",
        }
        query = "&".join(f"{name}={value}" for name, value in secrets.items())  # Mix the case, like a proxy can.
        path = f"/floor-plan.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&{query}&X-Amz-Expires=300"  # The storage path.
        with caplog.at_level(logging.DEBUG, logger="urllib3.connectionpool"):  # Capture the debug line.
            pool_logger.debug(
                '%s://%s:%s "%s %s %s" %s %s', "https", "storage.example", 443, "GET", path, "HTTP/1.1", 200, 0
            )
        assert caplog.text.count("***REDACTED***") == len(secrets)  # Each secret value is hidden.
        assert "X-Amz-Expires=300" in caplog.text  # A value that grants nothing stays readable for triage.
        for value in secrets.values():  # No secret value reaches a handler.
            assert value not in caplog.text, "a storage link secret reached the log"
