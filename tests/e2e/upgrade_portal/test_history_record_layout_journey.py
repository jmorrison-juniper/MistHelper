"""Measure the native history records with private process-owned audit input.

The required browser checks use installed Playwright, not importorskip.
The private server keeps controlled audit input outside the shared browser trail.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import create_autospec
from urllib.parse import urlencode, urlsplit

import pytest
from flask import Response
from playwright._impl._api_structures import SetCookieParam
from playwright.sync_api import Browser, Locator, Page, Route, expect

from src.upgrade_portal.runtime import lock
from src.upgrade_portal.runtime.server import build_server_command
from tests.support.upgrade_portal_e2e import (
    E2EResources,
    RunOwnerHeaderCheck,
    allocate_resources,
    build_child_environment,
)
from tests.support.upgrade_portal_e2e.records.audit import TrailHoldCheck

logger = logging.getLogger(__name__)


class RecordServer:
    """Run the canonical native fixture in one private server process."""

    class Settings:
        """Keep the child gate and exact native import separate from production."""

        ROOT = Path(__file__).resolve().parents[3]
        CHILD = "HISTORY_RECORD_LAYOUT_CHILD"
        NATIVE = "tests.e2e.upgrade_portal.conftest"
        TARGET = "tests.e2e.upgrade_portal.test_history_record_layout_journey:app"
        SITE = "22222222-2222-2222-2222-222222222222"

    @classmethod
    def environment(cls, resources: E2EResources) -> dict[str, str]:
        """Use the shipped scrub and native child metadata without a shared process."""
        logger.info("Prepare one private native history environment")
        environment = build_child_environment(os.environ)
        environment.update(
            {
                cls.Settings.CHILD: "1",
                "UPGRADE_PORTAL_E2E_SESSION": "1",
                "UPGRADE_PORTAL_E2E_RUN_ID": resources.test_run_id,
                "CAPTURE_PORT": str(resources.port),
                "CAPTURE_SECRET_KEY": "upgrade-portal-e2e-cookie-signing-key",
                "UPGRADE_PORTAL_E2E_ARTIFACT_DIRECTORY": str(resources.artifact_directory),
                "UPGRADE_PORTAL_E2E_LOG_PATH": str(resources.log_path),
                "UPGRADE_PORTAL_E2E_OWNER_PATH": str(resources.process_owner_path),
                "GUNICORN_CMD_ARGS": f"--control-socket {resources.log_path}.ctl",
            }
        )
        logger.debug("Prepared one scrubbed native history environment")
        return environment

    @classmethod
    @contextmanager
    def running(cls, resources: E2EResources) -> Iterator[None]:
        """Start and stop only the exact process that this fixture creates."""
        command = build_server_command(cls.Settings.TARGET, resources.port)
        environment = cls.environment(resources)
        resources.release_port()
        logger.info("Start one private native history process")
        with resources.log_path.open("wb") as output:
            process = subprocess.Popen(command, cwd=cls.Settings.ROOT, env=environment, stdout=output, stderr=output)
        resources.process_owner_path.write_text(str(process.pid), encoding="ascii")
        try:
            cls.ready(resources, process)
            yield
        finally:
            logger.info("Stop the exact private native history process")
            process.terminate()
            process.wait(timeout=5)
            resources.process_owner_path.unlink()
            with socket.socket() as probe:
                assert probe.connect_ex(("127.0.0.1", resources.port)) != 0
            assert not Path(f"{resources.log_path}.ctl").exists()
            TrailHoldCheck(resources.artifact_directory / lock.AUDIT_FILE_NAME).evaluate().require_no_leak()
            RecordMeasurements.Guard.Safety.retain(resources)
            RecordMeasurements.Guard.Safety.require(resources.artifact_directory)
            logger.debug("Stopped one process with closed port and absent owner and control records")

    @staticmethod
    def ready(resources: E2EResources, process: subprocess.Popen[bytes]) -> None:
        """Bound startup with the existing ten-second budget and check the response owner."""
        from urllib.error import URLError
        from urllib.request import urlopen

        logger.info("Read the private native history health response")
        for _attempt in range(20):
            assert process.poll() is None, "The private native history process stopped during startup."
            try:
                with urlopen(f"http://127.0.0.1:{resources.port}/healthz", timeout=0.5) as response:
                    assert response.status == 200
                    headers = {name.lower(): value for name, value in response.headers.items()}
                    RunOwnerHeaderCheck(resources.test_run_id).require(headers)
                logger.debug("Verified one native history response owner")
                return
            except (URLError, TimeoutError):
                time.sleep(0.5)
        raise AssertionError("Checked 20 startup attempts. The private native history server did not answer.")

    @classmethod
    def application(cls) -> object:
        """Load one canonical native application and seed only its private release trail."""
        RecordMeasurements.Guard.Safety.install()
        native = import_module(cls.Settings.NATIVE)
        built = native.app
        assert native.TEST_RUN_ID == os.environ["UPGRADE_PORTAL_E2E_RUN_ID"]
        logger.info("Prepare one private native release record")
        record = {
            "org_id": native.STAND_IN_ORG_ID,
            "site_id": native.STAND_IN_SITE_ID,
            "action": "release",
            "actor_email": native.STAND_IN_EMAIL,
            "previous_actor_email": native.SECOND_EMAIL,
            "occurred_at": "2026-09-03T10:00:00Z",
        }
        trail = lock.audit_trail_path()
        assert trail.parent == Path(os.environ["UPGRADE_PORTAL_E2E_ARTIFACT_DIRECTORY"]).resolve()
        trail.write_text(json.dumps(record) + "\n", encoding="utf-8")
        built.after_request(RecordMeasurements.Guard.Safety.record)
        logger.debug("Prepared one release record without a held lock or shared audit write")
        return built


class RecordMeasurements:
    """Read painted boxes and text ranges from every actual record cell."""

    SCRIPT = """
    () => {
      const box = node => {
        const value = node.getBoundingClientRect();
        return {x: value.x, y: value.y, width: value.width, height: value.height,
                right: value.right, bottom: value.bottom};
      };
      const cell = node => {
        const style = getComputedStyle(node);
        const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
        const texts = [];
        while (walker.nextNode()) {
          const text = walker.currentNode;
          if (!text.textContent.trim() || text.parentElement.closest('.visually-hidden, [hidden]')) continue;
          const range = document.createRange();
          range.selectNodeContents(text);
          const parent = text.parentElement;
          const parentStyle = getComputedStyle(parent);
          const clip = parent.closest('.history-record-value, .history-record-badge');
          const clipStyle = clip ? getComputedStyle(clip) : null;
          const rectangles = [...range.getClientRects()].filter(value => value.width > 0);
          texts.push({value: text.textContent.trim(), title: parent.title || node.title,
                      lines: new Set(rectangles.map(value => Math.round(value.y))).size,
                      textWidth: range.getBoundingClientRect().width, box: box(parent),
                      client: parent.clientWidth, scroll: parent.scrollWidth,
                      whiteSpace: parentStyle.whiteSpace, overflow: parentStyle.overflowX,
                      ellipsis: parentStyle.textOverflow, fontSize: parentStyle.fontSize,
                      clip: clip ? {
                        width: clip.clientWidth - parseFloat(clipStyle.paddingLeft) -
                               parseFloat(clipStyle.paddingRight),
                        ellipsis: clipStyle.textOverflow, overflow: clipStyle.overflowX
                      } : null});
        }
        return {box: box(node), client: node.clientWidth, scroll: node.scrollWidth,
                textNeed: texts.reduce((width, text) => width + text.textWidth, 0) + parseFloat(style.paddingLeft) +
                          parseFloat(style.paddingRight),
                color: style.backgroundColor, texts,
                links: [...node.querySelectorAll('a')].map(link => ({
                  href: link.getAttribute('href'), box: box(link), text: link.textContent.trim()
                }))};
      };
      return {
        width: innerWidth, pageWidth: document.documentElement.scrollWidth,
        tables: ['run', 'operation', 'audit', 'capture'].map(kind => {
          const table = document.querySelector(
            `[data-testid="${kind === 'capture' ? 'history-table' : 'history-' + kind + '-table'}"]`);
          if (!table) throw new Error('A required native history table is absent.');
          const container = table.parentElement;
          const boundary = box(container);
          const headers = [...table.querySelectorAll('thead th')].map(cell);
          return {kind, box: box(table), container: boundary,
                  client: container.clientWidth, scroll: container.scrollWidth,
                  headers, visibleColumns: headers.map((header, index) => ({
                    index, visible: header.box.x >= boundary.x &&
                                    header.box.right <= Math.min(boundary.right, innerWidth)
                  })),
                  rows: [...table.querySelectorAll('tbody tr[data-testid]')].map(row => ({
                    id: row.dataset.testid, box: box(row),
                    cells: [...row.querySelectorAll(':scope > th, :scope > td')].map(cell)
                  }))};
        })
      };
    }
    """

    @staticmethod
    def read(page: Page, name: str) -> dict[str, Any]:
        """Retain measurements before a guard decision, including a failing decision."""
        logger.info("Measure one native history page")
        page.mouse.move(0, 0)
        report = page.evaluate(RecordMeasurements.SCRIPT)
        assert isinstance(report, dict)
        directory = os.environ.get("HISTORY_RECORD_LAYOUT_EVIDENCE")
        if directory:
            target = Path(directory)
            assert target.is_absolute() and target.is_dir()
            (target / f"{name}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            if os.environ.get("HISTORY_RECORD_LAYOUT_SCREENSHOTS") == "1":
                page.screenshot(path=str(target / f"{name}.png"), full_page=True)
        logger.debug("Measured one page with %s tables", len(report["tables"]))
        return report

    class Guard:
        """Require measured input before accepting any layout claim."""

        class Safety:
            """Measure real production callbacks inside the private child only."""

            TAPS: dict[str, Any] = {}

            @classmethod
            def install(cls) -> None:
                """Refuse live HTTP, store, and firmware callbacks before native construction."""
                from requests import Session

                logger.info("Install seven private live-callback guards")
                targets = [
                    ("mist_http", Session, "request"),
                    ("document_connect", import_module("src.upgrade_portal.capture.store"), "connect_database"),
                    ("lock_connect", lock, "connect_lock_store"),
                    ("site_devices", import_module("mistapi.api.v1.sites.devices"), "upgradeSiteDevices"),
                    ("site_device", import_module("mistapi.api.v1.sites.devices"), "upgradeDevice"),
                    ("org_devices", import_module("mistapi.api.v1.orgs.devices"), "upgradeOrgDevices"),
                    ("org_ssrs", import_module("mistapi.api.v1.orgs.ssr"), "upgradeOrgSsrs"),
                ]
                for name, module, attribute in targets:
                    callback = getattr(module, attribute)
                    tap = create_autospec(callback, side_effect=AssertionError("The layout attempted a live callback."))
                    cls.TAPS[name] = tap
                    setattr(module, attribute, tap)
                logger.debug("Installed seven native callback guards with exact callable signatures")

            @classmethod
            def record(cls, response: Response) -> Response:
                """Persist safe counts after every actual native response."""
                target = Path(os.environ["UPGRADE_PORTAL_E2E_ARTIFACT_DIRECTORY"]) / "layout-callbacks.json"
                counts = {name: tap.call_count for name, tap in cls.TAPS.items()}
                logger.info("Write seven private native callback counts")
                target.write_text(json.dumps({"checked_callbacks": len(counts), "counts": counts}), encoding="utf-8")
                logger.debug("Wrote seven private callback counts")
                return response

            @staticmethod
            def require(directory: Path) -> None:
                """Fail missing evidence or any attempted production callback."""
                target = directory / "layout-callbacks.json"
                try:
                    report = json.loads(target.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    logger.exception("Checked 0 live callback records. The required input cannot be read.")
                    raise
                print(f"Checked {len(report['counts'])} live callbacks.")
                expected = set(
                    "mist_http document_connect lock_connect site_devices site_device org_devices org_ssrs".split()
                )
                assert report["checked_callbacks"] == 7
                assert set(report["counts"]) == expected and set(report["counts"].values()) == {0}
                print("HTTP, store, and firmware callback counts remain zero.")

            @staticmethod
            def retain(resources: E2EResources) -> None:
                """Retain only this stopped process's controlled local evidence when requested."""
                directory = os.environ.get("HISTORY_RECORD_LAYOUT_EVIDENCE")
                if directory:
                    target = Path(directory) / f"runtime-{resources.test_run_id}"
                    logger.info("Retain one stopped private native runtime")
                    shutil.copytree(resources.artifact_directory, target)
                    logger.debug("Retained one private runtime without a live process or owner record")

        @classmethod
        def require(cls, report: dict[str, Any]) -> None:
            """Check every populated record table and report the actual denominator."""
            logger.info("Check the measured native history records")
            assert report["pageWidth"] <= report["width"] + 1, "The history page scrolls horizontally."
            records = report["tables"][:3]
            assert [len(table["headers"]) for table in records] == [11, 8, 5]
            rows = [row for table in records for row in table["rows"]]
            cells = [cell for row in rows for cell in row["cells"]]
            print(f"Checked 1 native page, {len(rows)} record rows, and {len(cells)} record cells.")
            assert all(table["rows"] for table in records), "The guard must measure all three populated tables."
            for table in records:
                assert table["container"]["x"] >= 0 and table["container"]["right"] <= report["width"]
                assert all(header["textNeed"] <= header["client"] + 1 for header in table["headers"])
                for row in table["rows"]:
                    cls.row(row, table["headers"])
            logger.debug("Checked %s record rows and %s record cells", len(rows), len(cells))

        @classmethod
        def row(cls, row: dict[str, Any], headers: list[dict[str, Any]]) -> None:
            """Require compact rows, aligned cells, and matching surfaces."""
            assert row["box"]["height"] <= 48, f'{row["id"]}: height {row["box"]["height"]} exceeds 48 pixels.'
            assert len(row["cells"]) == len(headers)
            color = row["cells"][0]["color"]
            for cell, header in zip(row["cells"], headers, strict=True):
                assert cell["color"] == color, "The row header has another surface."
                assert abs(cell["box"]["x"] - header["box"]["x"]) <= 1, "A header and its cell do not align."
                assert abs(cell["box"]["width"] - header["box"]["width"]) <= 1
                for text in cell["texts"]:
                    cls.value(text)

        @staticmethod
        def value(text: dict[str, Any]) -> None:
            """Require one text line and the complete title of each clipped value."""
            assert text["lines"] == 1, "A record value occupies several lines."
            clip = text["clip"]
            if clip is None:
                return
            assert clip["ellipsis"] == "ellipsis" and clip["overflow"] == "hidden", "A value has no ellipsis."
            title, value = text["title"], text["value"]
            assert title, "A clipped value has no complete title."
            if " ".join(title.split()) != value:
                assert value.endswith(" UTC"), "A value title differs from the complete text."
                moment = datetime.fromisoformat(title.replace("Z", "+00:00")).astimezone(UTC)
                assert moment.strftime("%Y-%m-%d %H:%M UTC") == value, "A stored moment title changed."

    @staticmethod
    def open(page: Page, resources: E2EResources, parameters: dict[str, str | int]) -> None:
        """Read the real route with exact owner and limit checks."""
        logger.info("Open one controlled native history scope")
        response = page.goto("/history?" + urlencode(parameters), wait_until="load")
        assert response is not None and response.status == 200
        RunOwnerHeaderCheck(resources.test_run_id).require(response.headers)
        expect(page.get_by_test_id("history-run-row-e2e-failed-run-0001")).to_have_count(1)
        page.wait_for_function(
            """async () => (await (await fetch(location.href)).text()).includes(
               'data-testid="history-operation-row-org-run-e2e-mixed-0001"')""",
            timeout=10_000,
        )
        response = page.reload(wait_until="load")
        assert response is not None and response.status == 200
        expect(page.get_by_test_id("history-audit-row-1")).to_have_count(1)
        expect(page.get_by_test_id("history-run-table").locator("thead th").nth(1)).to_have_attribute(
            "aria-sort", "none"
        )
        asset = page.request.get("/static/css/history_records.css")
        assert asset.status == 200 and asset.headers["content-type"].startswith("text/css")
        logger.debug("Opened one native history page with runs, operations, and private audit input")

    @staticmethod
    def origin(route: Route, origin: str) -> None:
        """Refuse an outside origin or a write before any browser transport."""
        request = route.request
        assert urlsplit(request.url).netloc == urlsplit(origin).netloc, "The browser requested another origin."
        assert request.method == "GET", "The layout journey attempted a write."
        route.continue_()


class RecordProof:
    """Verify controls and real stylesheet faults on private native pages."""

    @staticmethod
    def identities(page: Page, scope: str) -> None:
        """Require the current native scope, exact counts, and digest-only audit value."""
        controls = page.locator("[data-run-bulk-controls]")
        assert controls.get_attribute("data-organization-id") == "11111111-1111-1111-1111-111111111111"
        expected = "site:" + RecordServer.Settings.SITE if scope == "site" else "all-sites"
        assert controls.get_attribute("data-history-scope") == expected
        count = 2 if scope == "site" else 8
        expect(page.get_by_test_id("history-run-table").locator("tbody tr[data-testid]")).to_have_count(count)
        expect(page.get_by_test_id("history-operation-table").locator("tbody tr[data-testid]")).to_have_count(5)
        audit = page.get_by_test_id("history-audit-row-1")
        digest = audit.locator(":scope > td").nth(2)
        expect(digest).to_have_text("ef9f811c166805f7")
        expect(digest).to_have_attribute("title", "ef9f811c166805f7")
        assert "e2e.operator@example.invalid" not in page.get_by_test_id("history-audit-table").inner_html()
        logger.debug("Verified one selected native scope and one complete audit digest")

    @staticmethod
    def columns(page: Page) -> None:
        """Scroll each column into view and measure the actual visible intersection."""
        logger.info("Reach all 24 record columns inside their table containers")
        for kind in ("run", "operation", "audit"):
            table = page.get_by_test_id(f"history-{kind}-table")
            for header in table.locator("thead th").all():
                header.scroll_into_view_if_needed()
                visible = header.evaluate("""node => {
                      const cell = node.getBoundingClientRect();
                      const container = node.closest('.portal-table-scroll').getBoundingClientRect();
                      return cell.left >= container.left &&
                             cell.right <= Math.min(container.right, innerWidth);
                    }""")
                assert visible, "A record column remains outside the visible container."
            table.evaluate("node => { node.parentElement.scrollLeft = 0; }")
        logger.debug("Verified all 24 column intersections without a full-width fit claim")

    @staticmethod
    def hover(page: Page) -> None:
        """Compare every real row cell during hover in the active native theme."""
        logger.info("Measure three hovered native record rows")
        for kind in ("run", "operation", "audit"):
            row = page.get_by_test_id(f"history-{kind}-table").locator("tbody tr[data-testid]").first
            row.locator(":scope > th").hover()
            colors = row.locator(":scope > th, :scope > td").evaluate_all(
                "cells => cells.map(cell => getComputedStyle(cell).backgroundColor)"
            )
            assert len(set(colors)) == 1, "The hovered row header has another surface."
        page.mouse.move(0, 0)
        logger.debug("Verified three hovered native record surfaces")

    @staticmethod
    def mutate(route: Route, kind: str) -> None:
        """Change only one private response from the actual component asset."""
        response = route.fetch()
        assert response.status == 200 and response.headers["content-type"].startswith("text/css")
        source = response.text()
        selector = ".history-records-audit thead th:nth-child"
        changes = {
            "wrap": (("white-space: nowrap", "white-space: normal; word-break: break-word"),),
            "surface": (("var(--portal-surface)", "transparent"),),
            "ellipsis": (("text-overflow: ellipsis", "text-overflow: clip"),),
            "audit-digest": (
                (f"{selector}(4) {{ width: 18%; }}", f"{selector}(4) {{ width: 2%; }}"),
                (f"{selector}(5) {{ width: 18%; }}", f"{selector}(5) {{ width: 34%; }}"),
            ),
        }
        for before, after in changes[kind]:
            assert before in source, "The style mutation found no real input."
            source = source.replace(before, after)
        if kind == "audit-digest":
            source += (
                "\n.history-records-audit .history-record-value { " "white-space: normal; word-break: break-word; }\n"
            )
        route.fulfill(response=response, body=source)

    class Links:
        """Keep painted visibility separate from native navigation completion."""

        @classmethod
        def open(cls, page: Page, resources: E2EResources, action: tuple[str, str]) -> None:
            """Require a full title and an actual visible link before activation."""
            marker, mode = action
            link = page.get_by_test_id(marker)
            if marker.startswith("history-run-row"):
                link = link.locator("th a")
            assert link.get_attribute("title") == link.text_content()
            target = link.get_attribute("href")
            assert target is not None
            link.scroll_into_view_if_needed()
            assert link.evaluate("""node => {
                  const box = node.getBoundingClientRect();
                  const container = node.closest('.portal-table-scroll').getBoundingClientRect();
                  return box.left >= container.left && box.right <= Math.min(container.right, innerWidth);
                }""")
            cls.activate(page, resources, link, (target, mode))

        @staticmethod
        def activate(page: Page, resources: E2EResources, link: Locator, action: tuple[str, str]) -> None:
            """Wait for the real response and navigation without changing timeout settings."""
            target, mode = action
            logger.info("Activate one native history row link with %s", mode)
            with page.expect_response(lambda response: urlsplit(response.url).path == urlsplit(target).path) as result:
                if mode == "keyboard":
                    link.focus()
                    expect(link).to_be_focused()
                    link.press("Enter")
                else:
                    link.tap()
            assert result.value.status == 200
            RunOwnerHeaderCheck(resources.test_run_id).require(result.value.headers)
            expect(page).to_have_url(f"http://127.0.0.1:{resources.port}{target}")
            logger.debug("Activated one real native row link with status 200")


class TestHistoryRecordLayoutJourney:
    """Exercise every required width, scope, and theme without shared record mutations."""

    @pytest.fixture(scope="module")
    def record_server(
        self, request: pytest.FixtureRequest
    ) -> Iterator[tuple[E2EResources, dict[str, list[SetCookieParam]]]]:
        """Reuse the already-loaded native fixture identity without another conftest import."""
        path = RecordServer.Settings.ROOT / "tests/e2e/upgrade_portal/conftest.py"
        native = [
            plugin
            for plugin in request.config.pluginmanager.get_plugins()
            if isinstance(plugin, ModuleType) and getattr(plugin, "__file__", "") == str(path)
        ]
        assert len(native) == 1, "The journey must use one current native fixture module."
        cookies: dict[str, list[SetCookieParam]] = {
            "operator": native[0].operator_session_cookies(native[0].STAND_IN_EMAIL, native[0].STAND_IN_BROWSER_ID),
            "controls": native[0].controls_operator_cookies(),
        }
        root = Path("/tmp") if sys.platform == "darwin" else Path(tempfile.gettempdir())
        # A short owned path lets the native Gunicorn control socket bind on macOS.
        with tempfile.TemporaryDirectory(prefix="misthelper-3491-", dir=root) as folder:
            resources = allocate_resources(Path(folder).resolve())
            origin = f"http://127.0.0.1:{resources.port}"
            for values in cookies.values():
                for cookie in values:
                    cookie["url"] = origin
            with RecordServer.running(resources):
                yield resources, cookies

    @pytest.fixture
    def record_page(
        self, record_server: tuple[E2EResources, dict[str, list[SetCookieParam]]], browser: Browser
    ) -> Iterator[Page]:
        """Keep every browser context and request inside the exact owned origin."""
        resources, cookies = record_server
        origin = f"http://127.0.0.1:{resources.port}"
        context = browser.new_context(base_url=origin, has_touch=True)
        context.add_cookies(cookies["operator"])
        context.route("**/*", lambda route: RecordMeasurements.origin(route, origin))
        errors: list[str] = []
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(error.message))
        try:
            yield page
        finally:
            context.close()
            assert not errors, f"Checked one native script context. Browser errors: {errors}"

    @pytest.mark.parametrize(
        "view",
        [
            pytest.param((width, scope, theme), id=f"{scope}-{theme}-{width}")
            for theme in ("magenta", "default")
            for scope in ("organization", "site")
            for width in (1024, 1280, 1440)
        ],
    )
    def test_native_record_rows(
        self,
        record_page: Page,
        record_server: tuple[E2EResources, dict[str, list[SetCookieParam]]],
        view: tuple[int, str, str],
    ) -> None:
        """Measure every record column on the shipped route before the guard decision."""
        width, scope, theme = view
        resources, _cookies = record_server
        record_page.set_viewport_size({"width": width, "height": 900})
        parameters: dict[str, str | int] = {"limit": 200, "theme": theme}
        if scope == "site":
            parameters["site_id"] = RecordServer.Settings.SITE
        RecordMeasurements.open(record_page, resources, parameters)
        report = RecordMeasurements.read(record_page, f"{scope}-{theme}-{width}")
        assert [len(table["rows"]) for table in report["tables"][:3]] == [2 if scope == "site" else 8, 5, 1]
        RecordMeasurements.Guard.require(report)
        RecordProof.identities(record_page, scope)
        RecordProof.columns(record_page)
        RecordProof.hover(record_page)

    @pytest.mark.parametrize("kind", ("wrap", "surface", "ellipsis", "audit-digest"))
    def test_guard_rejects_actual_style_faults(
        self, record_page: Page, record_server: tuple[E2EResources, dict[str, list[SetCookieParam]]], kind: str
    ) -> None:
        """A bounded actual asset mutation must fail the same browser decision."""
        record_page.route("**/css/history_records.css", lambda route: RecordProof.mutate(route, kind))
        resources, _cookies = record_server
        RecordMeasurements.open(record_page, resources, {"limit": 200, "theme": "magenta"})
        report = RecordMeasurements.read(record_page, f"fault-{kind}")
        if kind == "audit-digest":
            digest = report["tables"][2]["rows"][0]["cells"][3]["texts"][0]
            assert digest["lines"] > 1 and digest["value"] == "ef9f811c166805f7"
            with pytest.raises(AssertionError, match="several lines"):
                RecordMeasurements.Guard.value(digest)
        with pytest.raises(AssertionError):
            RecordMeasurements.Guard.require(report)
        logger.debug("Rejected one actual native component fault")

    @pytest.mark.parametrize(
        "action",
        [
            ("history-run-row-e2e-stopped-run-0001", "keyboard"),
            ("history-run-row-e2e-stopped-run-0001", "touch"),
            ("history-operation-open-org-run-e2e-retry-0001", "keyboard"),
            ("history-operation-open-org-run-e2e-retry-0001", "touch"),
        ],
    )
    def test_row_links_retain_keyboard_and_touch_actions(
        self,
        record_page: Page,
        record_server: tuple[E2EResources, dict[str, list[SetCookieParam]]],
        action: tuple[str, str],
    ) -> None:
        """A clipped run or owned operation identifier retains its real link action."""
        resources, cookies = record_server
        if action[0].startswith("history-operation"):
            record_page.context.clear_cookies()
            record_page.context.add_cookies(cookies["controls"])
        RecordMeasurements.open(record_page, resources, {"limit": 200, "theme": "default"})
        RecordProof.Links.open(record_page, resources, action)
        expected = (
            "/upgrade/org/jobs/org-run-e2e-retry-0001"
            if action[0].startswith("history-operation")
            else ("/runs/e2e-stopped-run-0001")
        )
        assert urlsplit(record_page.url).path == expected


class TestRecordCallbackEvidence:
    """Reject failed or unreadable native callback evidence without a shared fixture."""

    @pytest.mark.parametrize("kind", ("nonzero", "missing", "invalid"))
    def test_callback_guard_rejects_failed_or_unreadable_evidence(self, tmp_path: Path, kind: str) -> None:
        """The exact native callback decision must reject each negative input."""
        target = tmp_path / "layout-callbacks.json"
        expected: type[Exception]
        if kind == "nonzero":
            names = "mist_http document_connect lock_connect site_devices site_device org_devices org_ssrs".split()
            counts = {name: int(name == "mist_http") for name in names}
            target.write_text(json.dumps({"checked_callbacks": 7, "counts": counts}), encoding="utf-8")
            expected = AssertionError
        elif kind == "invalid":
            target.write_text("{invalid", encoding="utf-8")
            expected = json.JSONDecodeError
        else:
            expected = FileNotFoundError
        with pytest.raises(expected):
            RecordMeasurements.Guard.Safety.require(tmp_path)


if os.environ.get(RecordServer.Settings.CHILD) == "1":
    app = RecordServer.application()
