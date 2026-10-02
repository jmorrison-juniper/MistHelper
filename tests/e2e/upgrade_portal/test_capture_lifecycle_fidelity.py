"""Read native capture fields and private partial adoption through the shipped browser surfaces."""

from __future__ import annotations

import logging
from collections.abc import Iterator, Mapping
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
import redis
import requests
from werkzeug.serving import make_server

from src.export.data_exporter import DataExporter
from src.upgrade_portal.capture import store
from src.upgrade_portal.runtime import identity
from tests.support.upgrade_portal_e2e import RunOwnerHeaderCheck, allocate_resources
from tests.support.upgrade_portal_e2e.capture_fidelity import NativeCaptureFixture, PrivateCaptureScenario
from tests.support.upgrade_portal_e2e.model_version_picker import ModelVersionPicker

if TYPE_CHECKING:
    from playwright.sync_api import Browser, Page

sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")
logger = logging.getLogger(__name__)


class PrivateBrowserRun:
    """Own the loopback server, browser context, response owner, and cleanup."""

    def __init__(self, scenario: PrivateCaptureScenario, browser: Browser, root: Path) -> None:
        """Retain passive inputs before the fixture registers guaranteed cleanup."""
        self.scenario = scenario
        self.browser = browser
        self.root = root
        self.cleanup = ExitStack()
        self.ready = False
        self.requests: list[str] = []
        self.errors: list[str] = []

    def start(self) -> None:
        """Start one private server and register cleanup after each acquired resource."""
        self.resources = allocate_resources(self.root)
        self.cleanup.callback(self.resources.release_port)
        self.resources.release_port()
        self.server = make_server("127.0.0.1", self.resources.port, self.scenario.app, threaded=True)
        self.cleanup.callback(self.server.server_close)
        self.thread = Thread(target=self.server.serve_forever, name=self.resources.test_run_id, daemon=True)
        self.url = f"http://127.0.0.1:{self.resources.port}"
        self.owner_check = RunOwnerHeaderCheck(self.scenario.overrides.test_run_id)
        logger.info("Start one private loopback browser server")
        self.thread.start()
        self.cleanup.callback(self.thread.join, timeout=5)
        self.cleanup.callback(self.server.shutdown)
        logger.debug("Started private browser servers=1 port=%d", self.resources.port)
        self.context = self.browser.new_context(base_url=self.url)
        self.cleanup.callback(self.context.close)
        self.install_cookies()
        self.page = self.context.new_page()
        self.cleanup.callback(self.page.close)
        self.page.on("request", lambda request: self.requests.append(request.url))
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))

    def install_cookies(self) -> None:
        """Install only the two cookies of the owned fake Flask session."""
        client = self.scenario.session.client
        for name in ("session", identity.BROWSER_ID_COOKIE):
            cookie = client.get_cookie(name)
            assert cookie is not None, f"The private client has no {name!r} cookie."
            self.context.add_cookies([{"name": name, "value": cookie.value, "url": self.url}])
        assert {cookie["name"] for cookie in self.context.cookies()} == {"session", identity.BROWSER_ID_COOKIE}

    def require_ready(self) -> None:
        """Require a real response from this private server before a browser assertion."""
        response = self.page.goto("/healthz", wait_until="domcontentloaded")
        assert response is not None and response.status == 200
        self.owner_check.require(response.headers)
        assert self.thread.is_alive()
        self.ready = True
        logger.debug("Checked private server health responses=1 owned response headers=1")

    def close(self) -> None:
        """Stop every owned browser and server resource before checking evidence."""
        logger.info("Stop the private browser and loopback server")
        self.cleanup.close()
        if not self.ready:
            logger.warning(
                "Caution: the private server never proved readiness. The test cannot prove browser behavior."
            )
            return
        assert not self.thread.is_alive(), "The private loopback server did not stop."
        assert self.errors == [], f"The shipped browser script failed: {self.errors!r}"
        assert len(self.requests) > 0
        assert all(address.startswith(self.url + "/") for address in self.requests), self.requests
        assert self.scenario.reads.actions == []
        logger.debug(
            "Checked owned browser requests=%d outside requests=0 script errors=0 callbacks=0", len(self.requests)
        )
        print(
            f"Checked owned browser requests={len(self.requests)} outside requests=0 "
            "script errors=0 upgrade/start/cancel callbacks=0."
        )


class CapturePageChecks:
    """Check real rendered fields without an API payload or a tracing-dependent decision."""

    @staticmethod
    def open(run: PrivateBrowserRun, capture_id: str) -> Page:
        """Open the shipped stored-capture page and check response ownership."""
        response = run.page.goto(f"/captures/{capture_id}", wait_until="networkidle")
        assert response is not None and response.status == 200
        run.owner_check.require(response.headers)
        sync_api.expect(run.page.get_by_test_id("capture-verified-badge")).to_have_text("Verified")
        return run.page

    @staticmethod
    def counts(page: Page, expected: Mapping[str, int]) -> None:
        """Require exactly nine visible count cells and every native value."""
        sync_api.expect(page.locator("[data-capture-count]")).to_have_count(9)
        assert len(expected) == 9
        for key, value in expected.items():
            cell = page.locator(f'[data-capture-count="{key}"]')
            sync_api.expect(cell).to_be_visible()
            sync_api.expect(cell).to_have_text(str(value))
        logger.debug("Checked rendered native count fields=9")

    @staticmethod
    def devices(page: Page, version: str) -> None:
        """Read each actual Version and Status cell with exact native MAC membership."""
        table = page.get_by_test_id("capture-device-table")
        sync_api.expect(table.locator("tbody tr")).to_have_count(3)
        for number in range(1, 4):
            row = page.get_by_test_id(f"capture-device-row-00000000000{number}")
            sync_api.expect(row).to_be_visible()
            cells = row.get_by_role("cell")
            sync_api.expect(cells).to_have_count(10)
            sync_api.expect(cells.nth(4)).to_have_text(version)
            sync_api.expect(cells.nth(5)).to_have_text("connected")
        logger.debug("Checked rendered device rows=3 Version/Status cells=6")

    @staticmethod
    def parents(page: Page, guest: bool = False) -> None:
        """Require actual serving names rather than guessed seed labels."""
        for number, kind in enumerate(("ap", "gateway", "switch"), start=1):
            row = page.get_by_test_id(f"capture-client-row-aabbcc00000{number}")
            sync_api.expect(row).to_be_visible()
            sync_api.expect(row.get_by_role("cell").nth(3)).to_have_text(f"E2E {kind} {number}")
        if guest:
            row = page.get_by_test_id("capture-client-row-aabbcc000099")
            sync_api.expect(row.get_by_role("cell").nth(2)).to_have_text("E2E ap 1")
        logger.debug("Checked rendered matched parent cells=%d", 4 if guest else 3)

    @staticmethod
    def history(run: PrivateBrowserRun, capture_id: str, expected_content: str) -> None:
        """Read content completeness from the actual stored-history surface."""
        response = run.page.goto("/history", wait_until="networkidle")
        assert response is not None and response.status == 200
        run.owner_check.require(response.headers)
        row = run.page.get_by_test_id(f"history-row-{capture_id}")
        sync_api.expect(row).to_be_visible()
        sync_api.expect(row.locator(".portal-badge")).to_have_text(expected_content)
        logger.debug("Checked rendered stored-history content fields=1 value=%s", expected_content)


class TestCaptureLifecycleFidelity:
    """Keep every new browser case isolated from the shared global server records."""

    class OutsideCalls:
        """Own the actual outside-I/O refusal boundaries of these browser tests."""

        @staticmethod
        def isolate(monkeypatch: pytest.MonkeyPatch) -> list[Mock]:
            """Fail instead of reaching an SDK transport, Redis, ArangoDB, or exporter."""
            targets = [
                (requests.sessions.Session, "request"),
                (redis.Redis, "execute_command"),
                (store, "connect_database"),
                (DataExporter, "write_with_format_selection"),
            ]
            forbidden = [
                Mock(side_effect=AssertionError("The browser harness reached outside transport or storage."))
                for _ in targets
            ]
            for (owner, name), callback in zip(targets, forbidden, strict=True):
                monkeypatch.setattr(owner, name, callback)
            return forbidden

    @pytest.fixture
    def private_browser(
        self, browser: Browser, request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
    ) -> Iterator[PrivateBrowserRun]:
        """Own a process-isolated scenario, outside-I/O guards, and automatic directory cleanup."""
        forbidden = self.OutsideCalls.isolate(monkeypatch)
        with ExitStack() as cleanup:
            directory = cleanup.enter_context(TemporaryDirectory(prefix="misthelper-3375-browser-"))
            scenario = PrivateCaptureScenario(NativeCaptureFixture.read(request.config), monkeypatch)
            cleanup.callback(scenario.session.close)
            scenario.app.config["WTF_CSRF_ENABLED"] = True
            run = PrivateBrowserRun(scenario, browser, Path(directory))
            cleanup.callback(run.close)
            run.start()
            run.require_ready()
            yield run
            assert [callback.call_count for callback in forbidden] == [0, 0, 0, 0]
        assert not Path(directory).exists()
        print("Checked owned browser resource directories=1 remaining=0 outside transport/store boundaries=4 calls=0.")

    @pytest.mark.parametrize(
        ("capture_id", "version", "content"),
        [
            ("e2e-capture-pre-0001", "0.14.29216", "complete"),
            ("e2e-capture-standalone-0001", "0.14.29216", "complete"),
            ("e2e-capture-post-0001", "0.15.1", "complete"),
            ("e2e-capture-stored-poll-0001", "0.14.29216", "complete"),
            ("e2e-capture-tier3-0001", "0.14.29216", "partial"),
        ],
    )
    def test_native_seed_fields_render_exactly(
        self, private_browser: PrivateBrowserRun, capture_id: str, version: str, content: str
    ) -> None:
        """Require native count, device, parent, and stored-content fields for each original seed."""
        page = CapturePageChecks.open(private_browser, capture_id)
        guest = capture_id == "e2e-capture-tier3-0001"
        expected = {
            "devices_total": 3,
            "devices_connected": 3,
            "devices_disconnected": 0,
            "gateways": 1,
            "switches": 1,
            "access_points": 1,
            "clients_wired": 0,
            "clients_wireless": 3,
            "clients_guest": 1 if guest else 0,
        }
        CapturePageChecks.counts(page, expected)
        assert page.locator("[data-capture-count]").count() == 9
        CapturePageChecks.devices(page, version)
        CapturePageChecks.parents(page, guest)
        CapturePageChecks.history(private_browser, capture_id, content)
        print(f"Checked fields: counts=9 Version/Status=6 parents={4 if guest else 3} content=1.")

    def test_private_verified_partial_is_adopted_by_the_actual_card(self, private_browser: PrivateBrowserRun) -> None:
        """Use current model controls and the actual saved plan before reading the real pre-check card."""
        run = private_browser
        identifiers = run.scenario.Identifiers
        response = run.page.goto("/upgrade/org/options", wait_until="networkidle")
        assert response is not None and response.status == 200
        run.owner_check.require(response.headers)
        ModelVersionPicker(run.page).select("0.15.1", 6)
        run.page.get_by_test_id("org-upgrade-review").click()
        run.page.wait_for_url("**/upgrade/org/confirm")
        partial = run.page.get_by_test_id(f"org-upgrade-precheck-row-{identifiers.SITE_ID}")
        pending = run.page.get_by_test_id(f"org-upgrade-precheck-row-{identifiers.PENDING_SITE_ID}")
        sync_api.expect(partial).to_have_attribute("data-ready", "true")
        sync_api.expect(partial.get_by_test_id(f"org-upgrade-precheck-capture-{identifiers.SITE_ID}")).to_have_text(
            identifiers.CAPTURE_ID
        )
        sync_api.expect(run.page.get_by_test_id(f"org-upgrade-precheck-tier-{identifiers.SITE_ID}")).to_have_text("3")
        sync_api.expect(pending).to_have_attribute("data-ready", "false")
        sync_api.expect(
            run.page.get_by_test_id(f"org-upgrade-precheck-state-{identifiers.PENDING_SITE_ID}")
        ).to_have_text("missing")
        sync_api.expect(run.page.get_by_test_id("org-upgrade-confirmation")).to_be_disabled()
        print("Checked real pre-check cards=1 model controls=6 site rows=2 partial adoptions=1 pending refusals=1.")

    def test_private_unmatched_parent_is_explicitly_unknown(self, private_browser: PrivateBrowserRun) -> None:
        """Render one genuinely unmatched client without changing any shared capture."""
        run = private_browser
        identifiers = run.scenario.Identifiers
        page = CapturePageChecks.open(run, identifiers.CAPTURE_ID)
        table = page.get_by_test_id("capture-client-wireless-table")
        sync_api.expect(table.locator("tbody tr")).to_have_count(4)
        CapturePageChecks.parents(page, guest=True)
        row = page.get_by_test_id(f"capture-client-row-{identifiers.UNMATCHED_CLIENT_MAC}")
        sync_api.expect(row).to_be_visible()
        sync_api.expect(row.get_by_role("cell").nth(3)).to_have_text("unknown")
        document = run.scenario.records.load_capture(identifiers.CAPTURE_ID).capture
        assert document is not None and document["capture_id"] == identifiers.CAPTURE_ID
        unmatched = document["clients"]["wireless"][-1]
        assert unmatched["device_mac"] == "001122334455" and "device_name" not in unmatched
        print("Checked private wireless rows=4 matched parent fields=3 unmatched parent fields=1 guessed labels=0.")
