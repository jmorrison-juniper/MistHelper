"""Measure shipped browser controls without alternate routes or script substitutes."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from tests.support.wip_target_controls.portal import LocalPortalServer

if TYPE_CHECKING:
    from playwright.sync_api import CDPSession, Page

logger = logging.getLogger(__name__)
SCRIPT_PATH = Path(__file__).resolve().parents[3] / "web_portal" / "static" / "js" / "operations.js"


class TargetAcceptance:
    """Reject missing target and caution metadata with counted direct decisions."""

    @staticmethod
    def require_switch(parameters: list[dict[str, Any]]) -> None:
        """Require exactly the two actual prompt answers in their existing order."""
        logger.info("Checking 1 menu 63 row and %d target descriptors", len(parameters))
        expected = (("site_id", "site"), ("device_id", "device"))
        actual = tuple((parameter["name"], parameter["param_type"]) for parameter in parameters)
        valid = actual == expected and all(parameter["required"] is True for parameter in parameters)
        switch = parameters[1] if len(parameters) == 2 else {}
        valid = valid and switch.get("device_filter") == "switch" and switch.get("depends_on") == "site_id"
        assert valid, f"Checked 1 row and {len(parameters)} descriptors. Menu 63 needs the required site and switch."
        logger.debug("Checked 1 row and 2 required descriptors in site-then-switch order")

    @staticmethod
    def require_caution(row: dict[str, Any]) -> None:
        """Reject a WIP row whose category-derived warning metadata is absent."""
        logger.info("Checking 1 displayed WIP row for caution metadata")
        assert row.get("work_in_progress") is True, "Checked 1 WIP row. Its required caution metadata is missing."
        logger.debug("Checked 1 WIP row and 1 caution property")


class BrowserJourney:
    """Use real controls, real requests, and real handler completion."""

    def __init__(self, page: Page, server: LocalPortalServer) -> None:
        """Keep this browser tied to the owned shipped portal."""
        self.page = page
        self.server = server

    def open(self) -> None:
        """Prove the loaded controller is the exact shipped file."""
        logger.info("Opening the shipped issue 3158 Operations page")
        with self.page.expect_response(lambda response: response.url.endswith("/static/js/operations.js")) as loaded:
            response = self.page.goto(self.server.url + "/operations", wait_until="networkidle", timeout=15000)
        assert response is not None, "The shipped page returned no response."
        self.server.owner.require(response.headers)
        script = loaded.value.body()
        assert script == SCRIPT_PATH.read_bytes(), "The browser did not execute the exact shipped operations.js."
        self.page.locator('.op-item[data-menu="63"]').wait_for(state="attached")
        logger.debug("Loaded 1 shipped controller with SHA256 %s", hashlib.sha256(script).hexdigest())

    def select(self, number: str) -> None:
        """Expand the actual category and select its actual row."""
        row = self.page.locator(f'.op-item[data-menu="{number}"]')
        if not row.is_visible():
            self.page.locator(".accordion-item", has=row).locator("button.accordion-button").click()
        row.click()
        self.page.locator("#parameterLoading").wait_for(state="hidden")

    def run(self) -> dict[str, Any]:
        """Start through the real browser button and wait for actual completion."""
        logger.info("Activating 1 actual browser Run control")
        with self.page.expect_response(lambda response: response.url.endswith("/api/operations/run")) as started:
            self.page.get_by_test_id("run-btn").click()
        response = started.value
        self.server.owner.require(response.headers)
        assert response.status == 202, response.json()
        result = self.server.portal.wait(response.json()["run_id"])
        logger.debug("The actual browser Run returned status %s", result["status"])
        return result

    def input_requests(self) -> list[dict[str, Any]]:
        """Return only actual browser Run bodies from the server request ledger."""
        return [
            call["body"]
            for call in self.server.portal.ledger.calls
            if call["method"] == "POST" and call["path"] == "/api/operations/run"
        ]


class BrowserCallbacks:
    """Count executed selector callbacks through Chromium's native profiler."""

    def __init__(self, page: Page) -> None:
        """Start coverage before the shipped script loads."""
        self.session: CDPSession = page.context.new_cdp_session(page)
        self.session.send("Debugger.enable")
        self.session.send("Profiler.enable")
        self.session.send("Profiler.startPreciseCoverage", {"callCount": True, "detailed": True})

    def counts(self) -> dict[str, int]:
        """Read actual selector continuations without replacing fetch or promises."""
        counts = {"site": 0, "device": 0}
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        starts = {"site": source.index("function fetchSites("), "device": source.index("function fetchDevices(")}
        ends = {
            "site": source.index("function populateSiteOptions("),
            "device": source.index("function populateDeviceOptions("),
        }
        for script in self.session.send("Profiler.takePreciseCoverage")["result"]:
            if not script["url"].endswith("/static/js/operations.js"):
                continue
            actual = self.session.send("Debugger.getScriptSource", {"scriptId": script["scriptId"]})["scriptSource"]
            assert actual == source, "The profiled selector code differs from the shipped controller."
            for function in script["functions"]:
                span = function["ranges"][0]
                text = source[span["startOffset"] : span["endOffset"]]
                for family in counts:
                    if starts[family] < span["startOffset"] < ends[family] and text.startswith("function("):
                        counts[family] += span["count"]
        logger.info("Checked %d site callbacks and %d device callbacks", counts["site"], counts["device"])
        return counts

    def close(self) -> None:
        """Release the owned profiler independently from optional artifacts."""
        self.session.send("Profiler.stopPreciseCoverage")
        self.session.send("Profiler.disable")
        self.session.send("Debugger.disable")
        self.session.detach()
