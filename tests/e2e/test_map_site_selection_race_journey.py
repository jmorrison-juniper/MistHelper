"""Hold real Chromium map-list responses and inspect the current site's controls."""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from flask import Response, jsonify, request
from playwright.sync_api import CDPSession, Page
from werkzeug.serving import make_server

from tests.unit.web_portal.test_map_site_selection_race import (
    TEMPLATE_PATH,
    MapListObservation,
    MapScriptRunner,
    MapSiteFacts,
    MapSiteScenario,
)
from web_portal.app import WebPortalApp
from web_portal.menu_registry import build_static_menu_actions

logger = logging.getLogger(__name__)
WAIT_SECONDS = 15
FRAME_CHECKPOINT = """() => new Promise((resolve, reject) => {
    const deadline = setTimeout(() => reject(new Error('The browser frame checkpoint exceeded 15 seconds.')), 15000);
    requestAnimationFrame(() => requestAnimationFrame(() => { clearTimeout(deadline); resolve(); }));
})"""


@dataclass
class HeldMapList:
    """Keep one actual HTTP response pending until its test completes it."""

    site: str
    method: str
    path: str
    release: threading.Event = field(default_factory=threading.Event)
    reply: dict[str, object] = field(default_factory=dict)

    def answer(self, reply: dict[str, object]) -> None:
        """Supply the response before the waiting server thread resumes."""
        logger.info("The test server will release 1 held map-list response for site %s", self.site)
        body_release = self.reply.get("body_release")
        self.reply = reply
        self.release.set()
        if isinstance(body_release, threading.Event):
            body_release.set()
        logger.debug("The test server released 1 held response with status %s", reply["status"])


class MapListServer:
    """Serve synthetic records at the actual Maps HTTP boundary."""

    def __init__(self) -> None:
        """Create a private request ledger and condition for one test."""
        self.calls: list[HeldMapList] = []
        self.condition = threading.Condition()

    @staticmethod
    def sites() -> Response:
        """Offer two known sites without a Mist session or API call."""
        return jsonify(
            {"sites": [{"id": MapSiteFacts.SITE_A, "name": "Site A"}, {"id": MapSiteFacts.SITE_B, "name": "Site B"}]}
        )

    def receive(self, site_id: str) -> Response:
        """Hold each real request and return its independently chosen response."""
        call = HeldMapList(site_id, request.method, request.path)
        with self.condition:
            self.calls.append(call)
            self.condition.notify_all()
        logger.info("The test server holds actual map-list GET request %d for site %s", len(self.calls), site_id)
        if not call.release.wait(WAIT_SECONDS):
            raise TimeoutError("The test did not release its held map-list response within 15 seconds.")
        body_release = call.reply.get("body_release")
        if call.reply.get("disconnect") or isinstance(body_release, threading.Event):

            def broken_body() -> Iterator[bytes]:
                """Hold a real JSON body or disconnect it after the headers arrive."""
                yield b'{"maps":'
                if isinstance(body_release, threading.Event) and not body_release.wait(WAIT_SECONDS):
                    raise TimeoutError("The test did not release its held JSON body within 15 seconds.")
                if call.reply.get("disconnect"):
                    raise ConnectionResetError("The test disconnected its local map-list response.")
                yield str(call.reply["body"])[len('{"maps":') :].encode("utf-8")

            return Response(broken_body(), content_type="application/json")
        body = call.reply["body"]
        if not isinstance(body, (str, bytes)):
            raise TypeError("The controlled HTTP body must contain text or bytes.")
        return Response(body, status=int(call.reply["status"]), content_type="application/json")

    def wait_for(self, count: int) -> HeldMapList:
        """Require the exact next request before the journey changes selection."""
        with self.condition:
            arrived = self.condition.wait_for(lambda: len(self.calls) >= count, timeout=WAIT_SECONDS)
            assert arrived, f"Actual map-list request {count} did not reach the isolated server."
            assert len(self.calls) == count, "A site selection produced an extra map-list request."
            return self.calls[count - 1]

    def ledger(self) -> list[dict[str, str]]:
        """Return actual request paths and methods in server arrival order."""
        return [{"site": call.site, "method": call.method, "path": call.path} for call in self.calls]


class MapSiteCoverage:
    """Observe executed completion callbacks and retain exact V8 coverage."""

    def __init__(self, page: Page, output: Path) -> None:
        """Start precise coverage before the Maps script loads."""
        self.session: CDPSession = page.context.new_cdp_session(page)
        self.output = output
        self.samples: list[dict[str, object]] = []
        self.sources: dict[str, str] = {}
        self.session.send("Debugger.enable")
        self.session.send("Profiler.enable")
        self.session.send("Profiler.startPreciseCoverage", {"callCount": True, "detailed": True})

    def collect(self) -> list[dict[str, object]]:
        """Read the actual page script and its execution ranges."""
        result = self.session.send("Profiler.takePreciseCoverage")
        scripts = []
        for entry in result["result"]:
            if not entry["url"].endswith("/maps"):
                continue
            script_id = entry["scriptId"]
            if script_id not in self.sources:
                self.sources[script_id] = self.session.send("Debugger.getScriptSource", {"scriptId": script_id})[
                    "scriptSource"
                ]
            if "function onSiteChange()" in self.sources[script_id]:
                assert (
                    self.sources[script_id] == MapScriptRunner.read()
                ), "The measured script differs from the template."
                scripts.append(entry)
        self.samples.extend(scripts)
        return scripts

    def require_completion(self) -> None:
        """Prove a list-result or failure continuation ran after response delivery."""
        continuations = 0
        for entry in self.collect():
            source = self.sources[entry["scriptId"]]
            start, end = source.index("function onSiteChange()"), source.index("function onMapChange()")
            for function in entry["functions"]:
                location = function["ranges"][0]
                text = source[location["startOffset"] : location["endOffset"]]
                if start < location["startOffset"] < end and text.startswith(("function(data)", "function(error)")):
                    continuations += location["count"]
        assert continuations >= 1, "No actual map-list result or failure continuation executed."
        logger.info("The coverage guard checked %d executed map-list completion callbacks", continuations)

    def close(self) -> None:
        """Save measured execution data and release the browser instrumentation."""
        self.collect()
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.output.write_text(
            json.dumps(
                {
                    "template_sha256": hashlib.sha256(TEMPLATE_PATH.read_bytes()).hexdigest(),
                    "scripts": self.sources,
                    "samples": self.samples,
                }
            ),
            encoding="utf-8",
        )
        self.session.send("Profiler.stopPreciseCoverage")
        self.session.detach()


class MapSiteBrowser:
    """Select real controls and observe complete page state without replacing behavior."""

    def __init__(self, page: Page, server: MapListServer, output: Path) -> None:
        """Collect requests, errors, and coverage for one isolated journey."""
        self.page, self.server = page, server
        self.coverage = MapSiteCoverage(page, output / "coverage.json")
        self.events: dict[str, list[object]] = {"errors": [], "requests": [], "console": [], "observations": []}
        page.on("pageerror", lambda error: self.events["errors"].append(str(error)))
        page.on("request", lambda call: self.events["requests"].append({"method": call.method, "url": call.url}))
        page.on("console", lambda message: self.events["console"].append({"type": message.type, "text": message.text}))

    def open(self, portal: str) -> None:
        """Load the actual template and wait for its actual site request."""
        logger.info("The browser will open the Maps page at the isolated local server")
        self.page.route(
            "**/*",
            lambda route: (
                route.continue_()
                if route.request.url.startswith(f"{portal}/")
                else route.fulfill(status=502, body="The test blocked an unexpected remote request.")
            ),
        )
        self.page.goto(f"{portal}/maps", wait_until="networkidle", timeout=WAIT_SECONDS * 1000)
        self.page.locator(f"#siteSelect option[value='{MapSiteFacts.SITE_B}']").wait_for(
            state="attached", timeout=WAIT_SECONDS * 1000
        )
        self.page.evaluate("""() => {
            window.mapListMutations = [];
            window.mapListObserver = new MutationObserver(records => {
                window.mapListMutations.push(...records.map(record => ({
                    type: record.type, attribute: record.attributeName
                })));
            });
            for (const id of ['mapSelect', 'plotArea', 'mapImageNote', 'devicePanel']) {
                window.mapListObserver.observe(document.getElementById(id),
                    {attributes: true, childList: true, subtree: true, characterData: true});
            }
        }""")
        logger.debug("The browser opened the page with both synthetic sites available")

    def choose(self, site: str) -> HeldMapList | None:
        """Create a selection through the existing Site control."""
        count = len(self.server.calls)
        self.page.get_by_test_id("site-select").select_option(site, timeout=WAIT_SECONDS * 1000)
        return self.server.wait_for(count + 1) if site else None

    def complete(self, call: HeldMapList, reply: dict[str, object]) -> None:
        """Deliver a real response, then prove that its browser continuation ran."""
        self.coverage.collect()
        event_name = "requestfailed" if reply.get("disconnect") else "requestfinished"
        with self.page.expect_event(
            event_name, predicate=lambda completed: completed.url.endswith(call.path), timeout=WAIT_SECONDS * 1000
        ) as event:
            call.answer(reply)
        completed = event.value
        assert bool(completed.failure) == bool(reply.get("disconnect")), f"Unexpected completion: {completed.failure}."
        self.page.evaluate(FRAME_CHECKPOINT)
        self.coverage.require_completion()
        self.events["observations"].append(
            {
                "site": call.site,
                "status": reply["status"],
                "state": self.snapshot(),
                "mutations": self.page.evaluate("mapListMutations"),
            }
        )

    def snapshot(self) -> dict[str, object]:
        """Read every option and the visible map state from the actual DOM."""
        return self.page.evaluate("""() => {
            const maps = document.getElementById('mapSelect');
            const placeholder = document.getElementById('mapPlaceholder');
            const plot = document.getElementById('plotArea');
            return {
                controls: {
                    site: document.getElementById('siteSelect').value,
                    options: Array.from(maps.options, option => ({
                        value: option.value, label: option.textContent, width: option.dataset.width ?? null,
                        height: option.dataset.height ?? null, selected: option.selected
                    })),
                    map: maps.value, disabled: maps.disabled, message: placeholder?.textContent ?? '',
                    errorCount: Number(placeholder?.textContent === 'Failed to load floor plans.' &&
                        !placeholder.classList.contains('d-none'))
                },
                view: {
                    title: plot.querySelector('.gtitle')?.textContent ?? '',
                    devices: plot.data ?? [], images: plot.layout?.images ?? [],
                    x: plot.layout?.xaxis?.range ?? [], y: plot.layout?.yaxis?.range ?? [],
                    scale: plot.layout?.yaxis?.scaleanchor ?? '',
                    scrollZoom: plot._context?.scrollZoom ?? null, responsive: plot._context?.responsive ?? null,
                    note: document.getElementById('mapImageNote').textContent,
                    noteHidden: document.getElementById('mapImageNote').classList.contains('d-none'),
                    panelHidden: document.getElementById('devicePanel').classList.contains('d-none'),
                    deviceCount: document.getElementById('deviceCount').textContent
                }
            };
        }""")


class MapStaleJourney:
    """Prepare race states and release JSON bodies without canceling requests."""

    @staticmethod
    def start_body(journey: MapSiteBrowser, call: HeldMapList) -> None:
        """Let A's current response parser wait for a real incomplete HTTP body."""
        reply = {**MapSiteFacts.success(), "body_release": threading.Event()}
        with journey.page.expect_response(
            lambda response: response.url.endswith(call.path), timeout=WAIT_SECONDS * 1000
        ):
            call.answer(reply)
        journey.page.evaluate(FRAME_CHECKPOINT)

    @classmethod
    def prepare(cls, journey: MapSiteBrowser, scenario: MapSiteScenario, stream: bool = False) -> HeldMapList:
        """Execute controlled fixture actions through the real Site control."""
        for action in scenario.actions:
            if "select" in action:
                site = action["select"]
                assert isinstance(site, str)
                call = journey.choose(site)
                if stream and len(journey.server.calls) == 1 and isinstance(call, HeldMapList):
                    cls.start_body(journey, call)
            else:
                index, reply = action["finish"], action["reply"]
                assert isinstance(index, int) and isinstance(reply, dict)
                journey.complete(journey.server.calls[index], reply)
        return journey.server.calls[0]


@pytest.fixture
def map_lists() -> MapListServer:
    """Give every case a private server ledger and independent held responses."""
    return MapListServer()


@pytest.fixture
def maps_race_portal(map_lists: MapListServer, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """Serve the production page on a private port without credentials or stores."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "portal-data"))
    monkeypatch.setenv("WEBHOOK_ENABLED", "false")
    app = WebPortalApp.create_app(None, build_static_menu_actions(), "synthetic-map-org")
    app.config["TESTING"] = True
    app.view_functions["maps.list_sites"] = map_lists.sites
    app.view_functions["maps.list_site_maps"] = map_lists.receive
    app.view_functions["maps.map_data"] = lambda site_id, map_id: jsonify(
        {
            "map_id": map_id,
            "name": "B-map",
            "width": 900,
            "height": 500,
            "devices": [{"name": "AP-B", "mac": "b001", "type": "ap", "x": 120, "y": 90}],
            "image_url": "",
        }
    )
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    logger.info("The test server will start on isolated loopback port %d", server.server_port)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        for call in map_lists.calls:
            if not call.release.is_set() or isinstance(call.reply.get("body_release"), threading.Event):
                call.answer(MapSiteFacts.success())
        server.shutdown()
        thread.join(timeout=WAIT_SECONDS)
        server.server_close()
        WebPortalApp.shutdown_app(app)
        logger.debug("The test server stopped")


@pytest.fixture
def journey(
    page: Page, maps_race_portal: str, map_lists: MapListServer, request: pytest.FixtureRequest
) -> Iterator[MapSiteBrowser]:
    """Retain browser evidence only under the caller's controlled output directory."""
    output = Path(request.config.getoption("output"))
    output = output if output.is_absolute() else request.config.rootpath / output
    directory = output / request.node.name.replace("/", "-")
    browser = MapSiteBrowser(page, map_lists, directory)
    browser.open(maps_race_portal)
    try:
        yield browser
    finally:
        browser.coverage.close()
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "journey.json").write_text(
            json.dumps({"requests": map_lists.ledger(), "events": browser.events}), encoding="utf-8"
        )
        page.evaluate("() => window.mapListObserver.disconnect()")
        remote = [call for call in browser.events["requests"] if not call["url"].startswith(f"{maps_race_portal}/")]
        assert remote == [], "The browser attempted an unexpected remote request."


class TestMapSiteSelectionRaceJourney:
    """Old responses must not alter current options or error notifications."""

    def test_latest_b_keeps_only_b_maps_after_a_completes(self, journey: MapSiteBrowser) -> None:
        """Hold A, complete B, then release A and require the exact B-only controls."""
        first = journey.choose(MapSiteFacts.SITE_A)
        second = journey.choose(MapSiteFacts.SITE_B)
        assert isinstance(first, HeldMapList) and isinstance(second, HeldMapList)
        journey.complete(second, MapSiteFacts.success("b"))
        before = journey.snapshot()
        MapListObservation.check(
            before["controls"],
            MapSiteFacts.expected(MapSiteFacts.SITE_B, ("b",)),
            journey.server.ledger(),
            (MapSiteFacts.SITE_A, MapSiteFacts.SITE_B),
        )
        journey.page.evaluate("() => { window.mapListMutations = []; }")
        journey.complete(first, MapSiteFacts.success("a-old"))
        after = journey.snapshot()
        MapListObservation.check(
            after["controls"],
            MapSiteFacts.expected(MapSiteFacts.SITE_B, ("b",)),
            journey.server.ledger(),
            (MapSiteFacts.SITE_A, MapSiteFacts.SITE_B),
        )
        assert after == before
        assert journey.page.evaluate("mapListMutations") == []
        assert journey.events["errors"] == []
        assert [call["method"] for call in journey.server.ledger()] == ["GET", "GET"]

    @pytest.mark.parametrize("latest", ("pending", "success", "failure", "blank", "a-success", "a-failure"))
    @pytest.mark.parametrize(
        "stale",
        ("success", "reported-error", "http-503", "invalid-json", "connection", "body-success", "body-connection"),
    )
    def test_site_choice_occurrences_ignore_stale_results(
        self, journey: MapSiteBrowser, latest: str, stale: str
    ) -> None:
        """Measure stale results while the latest choice is pending, complete, blank, or repeated."""
        scenario = MapSiteScenario.state(latest)
        first = MapStaleJourney.prepare(journey, scenario, stream=stale.startswith("body-"))
        before = journey.snapshot()
        MapListObservation.check(before["controls"], scenario.expected, journey.server.ledger(), scenario.sites)
        journey.page.evaluate("() => { window.mapListMutations = []; }")
        reply = (
            MapSiteFacts.success("a-old")
            if stale in ("success", "body-success")
            else MapSiteFacts.failures()["connection" if stale == "body-connection" else stale]
        )
        journey.complete(first, reply)
        MapListObservation.check(
            journey.snapshot()["controls"], scenario.expected, journey.server.ledger(), scenario.sites
        )
        assert journey.snapshot() == before
        assert journey.page.evaluate("mapListMutations") == []
        assert journey.events["errors"] == []

    @pytest.mark.parametrize("failure", tuple(MapSiteFacts.failures()))
    def test_current_failure_is_visible_and_keeps_controls_disabled(
        self, journey: MapSiteBrowser, failure: str
    ) -> None:
        """Real transport, status, parsing, and map-list failures must remain visible."""
        current = journey.choose(MapSiteFacts.SITE_B)
        assert isinstance(current, HeldMapList)
        journey.complete(current, MapSiteFacts.failures()[failure])
        expected = MapSiteFacts.expected(MapSiteFacts.SITE_B, disabled=True, message=MapSiteFacts.ERROR)
        MapListObservation.check(
            journey.snapshot()["controls"], expected, journey.server.ledger(), (MapSiteFacts.SITE_B,)
        )
        assert journey.page.locator("#mapPlaceholder").is_visible()
        assert journey.events["errors"] == []

    def test_a_valid_empty_list_keeps_the_enabled_blank_option(self, journey: MapSiteBrowser) -> None:
        """An empty successful site must not receive a failure notification."""
        current = journey.choose(MapSiteFacts.SITE_B)
        assert isinstance(current, HeldMapList)
        journey.complete(current, MapSiteFacts.success())
        MapListObservation.check(
            journey.snapshot()["controls"],
            MapSiteFacts.expected(MapSiteFacts.SITE_B),
            journey.server.ledger(),
            (MapSiteFacts.SITE_B,),
        )
        assert journey.page.get_by_test_id("map-select").is_enabled()
        assert journey.events["errors"] == []

    def test_selected_b_map_and_blank_map_keep_existing_behavior(self, journey: MapSiteBrowser) -> None:
        """A stale list must preserve the selected map, then blank selection clears it."""
        first, second = journey.choose(MapSiteFacts.SITE_A), journey.choose(MapSiteFacts.SITE_B)
        assert isinstance(first, HeldMapList) and isinstance(second, HeldMapList)
        journey.complete(second, MapSiteFacts.success("b"))
        journey.page.get_by_test_id("map-select").select_option(
            str(MapSiteFacts.FLOORS["b"]["id"]), timeout=WAIT_SECONDS * 1000
        )
        journey.page.locator("#plotArea .gtitle").wait_for(state="visible", timeout=WAIT_SECONDS * 1000)
        journey.page.evaluate(FRAME_CHECKPOINT)
        before = journey.snapshot()
        journey.page.evaluate("() => { window.mapListMutations = []; }")
        journey.complete(first, MapSiteFacts.success("a-old"))
        assert journey.snapshot() == before
        assert before["view"]["title"] == "B-map"
        assert journey.page.evaluate("mapListMutations") == []
        requests_before_blank = len(journey.events["requests"])
        journey.page.get_by_test_id("map-select").select_option("", timeout=WAIT_SECONDS * 1000)
        assert len(journey.events["requests"]) == requests_before_blank
        assert journey.snapshot()["view"]["title"] == ""
        assert journey.page.get_by_test_id("map-image-note").is_hidden()
        assert journey.page.get_by_test_id("device-panel").is_hidden()
        assert journey.events["errors"] == []


class TestMapSiteChoiceCompatibility:
    """Current recovery, safe labels, and clearing must preserve ordinary controls."""

    @pytest.mark.parametrize("body", ("bad json", b""), ids=("malformed_json", "empty_body"))
    def test_malformed_json_and_empty_body_errors_are_visible(self, journey: MapSiteBrowser, body: str | bytes) -> None:
        """Explicit body failures must show one error rather than an empty success."""
        current = journey.choose(MapSiteFacts.SITE_B)
        assert isinstance(current, HeldMapList)
        journey.complete(current, {"status": 200, "body": body})
        MapListObservation.check(
            journey.snapshot()["controls"],
            MapSiteFacts.expected(MapSiteFacts.SITE_B, disabled=True, message=MapSiteFacts.ERROR),
            journey.server.ledger(),
            (MapSiteFacts.SITE_B,),
        )
        assert journey.page.locator("#mapPlaceholder").is_visible()
        assert journey.events["errors"] == []

    def test_a_new_choice_clears_the_current_error(self, journey: MapSiteBrowser) -> None:
        """Clear the prior error immediately, then accept only the new site's list."""
        failed = journey.choose(MapSiteFacts.SITE_B)
        assert isinstance(failed, HeldMapList)
        journey.complete(failed, MapSiteFacts.failures()["reported-error"])
        current = journey.choose(MapSiteFacts.SITE_A)
        assert isinstance(current, HeldMapList)
        assert journey.snapshot()["controls"] == MapSiteFacts.expected(MapSiteFacts.SITE_A, disabled=True)
        journey.complete(current, MapSiteFacts.success("a-new"))
        MapListObservation.check(
            journey.snapshot()["controls"],
            MapSiteFacts.expected(MapSiteFacts.SITE_A, ("a-new",)),
            journey.server.ledger(),
            (MapSiteFacts.SITE_B, MapSiteFacts.SITE_A),
        )
        assert journey.events["errors"] == []

    def test_map_labels_remain_safe_text_in_original_order(self, journey: MapSiteBrowser) -> None:
        """Map-list validation must preserve labels without executing supplied markup."""
        label = '<img src=x onerror="window.mapSiteNameExecuted=true">'
        floor = {**MapSiteFacts.FLOORS["b"], "name": label, "width": 0, "height": 0}
        current = journey.choose(MapSiteFacts.SITE_B)
        assert isinstance(current, HeldMapList)
        journey.complete(current, {"status": 200, "body": json.dumps({"maps": [floor, MapSiteFacts.FLOORS["a-new"]]})})
        options = journey.snapshot()["controls"]["options"]
        assert [option["label"] for option in options] == ["-- Select a map --", label + " (no image)", "A-new"]
        assert options[1]["width"] == "0" and options[1]["height"] == "0"
        assert journey.page.locator("#mapSelect img").count() == 0
        assert journey.page.evaluate("() => Object.hasOwn(window, 'mapSiteNameExecuted')") is False
        assert journey.page.get_by_test_id("map-select").input_value() == ""
        assert journey.events["errors"] == []

    def test_blank_site_clears_a_displayed_map_before_stale_completion(self, journey: MapSiteBrowser) -> None:
        """Clearing a displayed map must also invalidate earlier map-list work."""
        first, current = journey.choose(MapSiteFacts.SITE_A), journey.choose(MapSiteFacts.SITE_B)
        assert isinstance(first, HeldMapList) and isinstance(current, HeldMapList)
        journey.complete(current, MapSiteFacts.success("b"))
        journey.page.get_by_test_id("map-select").select_option(
            str(MapSiteFacts.FLOORS["b"]["id"]), timeout=WAIT_SECONDS * 1000
        )
        journey.page.locator("#plotArea .gtitle").wait_for(state="visible", timeout=WAIT_SECONDS * 1000)
        journey.page.evaluate(FRAME_CHECKPOINT)
        assert journey.page.get_by_test_id("device-panel").is_visible()
        request_count = len(journey.events["requests"])
        assert journey.choose("") is None
        before = journey.snapshot()
        assert before["controls"] == MapSiteFacts.expected("", disabled=True)
        assert before["view"]["title"] == ""
        assert journey.page.get_by_test_id("map-image-note").is_hidden()
        assert journey.page.get_by_test_id("device-panel").is_hidden()
        assert len(journey.events["requests"]) == request_count
        journey.page.evaluate("() => { window.mapListMutations = []; }")
        journey.complete(first, MapSiteFacts.success("a-old"))
        assert journey.snapshot() == before
        assert journey.page.evaluate("mapListMutations") == []
        assert journey.events["errors"] == []

    @pytest.mark.parametrize("stale", ("success", "connection"))
    def test_a_blank_a_keeps_the_second_occurrence(self, journey: MapSiteBrowser, stale: str) -> None:
        """A blank selection must not let the first request for A become current again."""
        first = journey.choose(MapSiteFacts.SITE_A)
        assert journey.choose("") is None
        current = journey.choose(MapSiteFacts.SITE_A)
        assert isinstance(first, HeldMapList) and isinstance(current, HeldMapList)
        journey.complete(current, MapSiteFacts.success("a-new"))
        before = journey.snapshot()
        journey.page.evaluate("() => { window.mapListMutations = []; }")
        journey.complete(first, MapSiteFacts.success("a-old") if stale == "success" else MapSiteFacts.failures()[stale])
        MapListObservation.check(
            journey.snapshot()["controls"],
            MapSiteFacts.expected(MapSiteFacts.SITE_A, ("a-new",)),
            journey.server.ledger(),
            (MapSiteFacts.SITE_A, MapSiteFacts.SITE_A),
        )
        assert journey.snapshot() == before
        assert journey.page.evaluate("mapListMutations") == []
        assert journey.events["errors"] == []
