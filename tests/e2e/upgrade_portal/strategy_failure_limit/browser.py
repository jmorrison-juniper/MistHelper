"""Own a loopback browser server and measure the shipped failure-field behavior."""

from __future__ import annotations

import json
import os
import re
import socket
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import pytest
from werkzeug.serving import make_server

from src.upgrade_portal.runtime import identity
from tests.e2e.upgrade_portal.strategy_failure_limit.portal import FailureLimitPortal, FailureLimitScope
from tests.support.upgrade_portal_e2e import RunOwnerHeaderCheck

if TYPE_CHECKING:
    from playwright.sync_api import Browser, Page

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

FIELD_STATE_SCRIPT = """node => {
    const group = node.parentElement;
    const strategy = node.form.querySelector('[name="strategy"]:checked');
    const rectangle = node.getBoundingClientRect();
    return {
        strategy: strategy.value, value: node.value, visible: node.getClientRects().length === 1,
        hidden: group.hidden, disabled: node.disabled, required: node.required, willValidate: node.willValidate,
        valid: node.checkValidity(), formValid: node.form.checkValidity(),
        valueMissing: node.validity.valueMissing, rangeUnderflow: node.validity.rangeUnderflow,
        rangeOverflow: node.validity.rangeOverflow,
        posted: new FormData(node.form).getAll(node.name), formData: Array.from(new FormData(node.form).entries()),
        id: node.id, name: node.name, testId: node.dataset.testid, type: node.type, min: node.min, max: node.max,
        rule: group.getAttribute('data-org-requires-strategy'),
        rectangle: rectangle.toJSON(), groupRectangle: group.getBoundingClientRect().toJSON(),
        viewport: {width: innerWidth, height: innerHeight},
        theme: document.documentElement.getAttribute('data-bs-theme'),
        startTop: node.form.querySelector('[name="start_time"]').getBoundingClientRect().top
    };
}"""


class FailureLimitServer:
    """Serve only this test's process-owned application on an allocated loopback port."""

    def __init__(self, portal: FailureLimitPortal, directory: Path) -> None:
        """Allocate a server without starting a helper process or production service."""
        self.server = make_server("127.0.0.1", 0, portal.app, threaded=True)
        self.address = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        self.owner_path = directory / "server-owner.json"

    def start(self, run_id: str) -> None:
        """Start the owned server and record the real process and thread identifiers."""
        self.thread.start()
        assert self.thread.is_alive() is True
        record = {"run_id": run_id, "pid": os.getpid(), "thread": self.thread.ident, "address": self.address}
        self.owner_path.write_text(json.dumps(record), encoding="utf-8")
        print("Started 1 owned loopback server: " + json.dumps(record))

    def close(self) -> None:
        """Stop this server and prove that its thread and listener no longer exist."""
        if self.thread.ident is not None:
            self.server.shutdown()
            self.thread.join(timeout=5)
        self.server.server_close()
        self.owner_path.unlink(missing_ok=True)
        assert self.thread.is_alive() is False
        assert self.server.socket.fileno() == -1
        try:
            with socket.create_connection(("127.0.0.1", self.server.server_port), timeout=0.5):
                raise AssertionError("The owned browser server still has a listener.")
        except ConnectionRefusedError:
            print(f"Checked 1 stopped browser listener on port {self.server.server_port}.")


class FailureLimitBrowser:
    """Drive an actual Chromium page without shared conftest globals."""

    def __init__(self, browser: Browser, portal: FailureLimitPortal, directory: Path, settings: dict[str, Any]) -> None:
        """Create an owned context, page, server, and artifact directory."""
        self.portal = portal
        self.context = browser.new_context(**settings["context"])
        self.page = self.context.new_page()
        self.server = FailureLimitServer(portal, directory)
        self.artifacts = directory / settings["theme"]

    def open(self, strategy: str | None, percentage: int | None = None) -> None:
        """Load a signed current page, including a genuine saved strategy when requested."""
        self.portal.seed(strategy, percentage)
        for name in ("session", identity.BROWSER_ID_COOKIE):
            cookie = self.portal.client.get_cookie(name)
            assert cookie is not None, f"The fixture has no {name} cookie."
            self.context.add_cookies([{"name": name, "value": cookie.value, "url": self.server.address}])
        response = self.page.goto(self.server.address + "/healthz")
        assert response is not None and response.status == 200
        assert RunOwnerHeaderCheck(self.portal.run_id).require(response.headers) == self.portal.run_id
        self.page.goto(self.server.address + "/upgrade/org/options?theme=" + self.artifacts.name)
        sync_api.expect(self.page.get_by_test_id("org-upgrade-options")).to_be_visible()

    def state(self) -> dict[str, Any]:
        """Measure the actual DOM, native validation, geometry, and FormData."""
        field = self.page.get_by_test_id("org-upgrade-max-failures")
        assert field.count() == 1
        measured = field.evaluate(FIELD_STATE_SCRIPT)
        assert isinstance(measured, dict)
        self.artifacts.mkdir(exist_ok=True)
        name = f"{measured['strategy']}-{uuid4().hex}"
        (self.artifacts / f"{name}.json").write_text(json.dumps(measured, indent=2), encoding="utf-8")
        self.page.screenshot(path=str(self.artifacts / f"{name}.png"), full_page=True)
        print(
            f"Checked 1 browser failure field for {measured['strategy']}: "
            f"visible={measured['visible']}, disabled={measured['disabled']}, posted={measured['posted']}."
        )
        return measured

    def review(self) -> dict[str, Any]:
        """Record one actual save JSON and stop on the typed confirmation page."""
        with self.page.expect_response("**/api/org-upgrades/options") as received:
            self.page.get_by_test_id("org-upgrade-review").click()
        response = received.value
        assert response.status == 200
        assert RunOwnerHeaderCheck(self.portal.run_id).require(response.headers) == self.portal.run_id
        payload = response.request.post_data_json
        assert isinstance(payload, dict)
        assert response.request.headers["x-csrftoken"] != ""
        self.page.wait_for_url(re.compile(r".*/upgrade/org/confirm$"))
        sync_api.expect(self.page.get_by_test_id("org-upgrade-start")).to_be_disabled()
        sync_api.expect(self.page.get_by_test_id("org-upgrade-confirmation")).to_have_value("")
        return payload

    def close(self, collection_module: str) -> None:
        """Stop owned resources, retain measured counts, and remove the registered operator."""
        try:
            self.context.tracing.stop(path=str(self.artifacts.parent / "trace.zip"))
            self.context.close()
        finally:
            try:
                self.server.close()
                measured = self.portal.require_idle()
                measured["collection_module"] = collection_module
                path = self.artifacts.parent / "callback-counts.json"
                path.write_text(json.dumps(measured), encoding="utf-8")
            finally:
                owner = self.portal.app.config.get("FAILURE_LIMIT_OWNER")
                if owner is not None:
                    identity.SESSION_REGISTRY.drop(owner.key)


class FailureLimitChecks:
    """Require exact state, payload, geometry, and adjacent control preservation."""

    @staticmethod
    def state(measured: dict[str, Any], strategy: str, percentage: int) -> None:
        """Require all operator and native-validation states for one applicable decision."""
        applies = strategy != "big_bang"
        assert measured["strategy"] == strategy
        assert (measured["visible"], measured["hidden"], measured["disabled"]) == (applies, not applies, not applies)
        assert (measured["required"], measured["willValidate"], measured["formValid"]) == (True, applies, True)
        assert measured["value"] == str(percentage)
        assert measured["posted"] == ([str(percentage)] if applies else [])
        assert (measured["id"], measured["name"], measured["testId"]) == (
            "max-failure-percentage",
            "max_failure_percentage",
            "org-upgrade-max-failures",
        )
        assert (measured["type"], measured["min"], measured["max"]) == ("number", "0", "100")
        assert measured["rule"] == "canary rrm serial"

    @staticmethod
    def targets(page: Page) -> list[dict[str, str]]:
        """Verify six model-specific lists and select a supported target in each real control."""
        controls = page.locator("[data-org-version-for]")
        assert controls.count() == 6
        targets = []
        for index in range(controls.count()):
            control = controls.nth(index)
            model = control.evaluate("node => node.closest('tr').children[3].textContent.trim()")
            versions = list(FailureLimitScope.facts["versions"][model])
            offered = control.locator("option").evaluate_all("nodes => nodes.map(node => node.value)")
            assert sorted(offered) == sorted(["", *versions]), f"The {model} list has another version or a duplicate."
            control.select_option(versions[-1])
            mac = control.get_attribute("data-org-version-for")
            assert isinstance(mac, str)
            targets.append({"mac": mac, "version_target": control.input_value()})
        return targets

    @staticmethod
    def payload(measured: dict[str, Any], body: dict[str, Any], targets: list[dict[str, str]]) -> None:
        """Compare the complete native form and actual save JSON, without its variable CSRF value."""
        strategy = measured["strategy"]
        expected: dict[str, Any] = {**FailureLimitScope.facts["form"], "strategy": strategy}
        if strategy != "big_bang":
            expected["max_failure_percentage"] = measured["value"]
        if strategy == "canary":
            expected.update(canary_phases="1,10,50,100", max_failures="")
        if strategy == "rrm":
            expected.update({name: "" for name in FailureLimitScope.facts["radio_fields"]})
        native: dict[str, Any] = {"selected_types": []}
        for name, value in measured["formData"]:
            if name == "selected_types":
                native[name].append(value)
            elif name != "csrf_token":
                native[name] = value
        assert native == expected
        assert body == {**expected, "targets": targets}

    @staticmethod
    def geometry(measured: dict[str, Any]) -> None:
        """Require an unclipped field or an empty hidden group rectangle."""
        rectangle = measured["rectangle"]
        if measured["visible"]:
            assert rectangle["width"] >= 240
            assert 0 <= rectangle["left"] < rectangle["right"] <= measured["viewport"]["width"]
            assert measured["groupRectangle"]["height"] > rectangle["height"] > 0
        else:
            assert (rectangle["width"], rectangle["height"]) == (0, 0)
            assert measured["groupRectangle"]["height"] == 0

    @staticmethod
    def adjacent(page: Page, strategy: str) -> None:
        """Keep the phase, model-specific, reboot, and Junos controls unchanged."""
        phases = page.get_by_test_id("org-upgrade-canary-phases")
        assert (phases.is_visible(), phases.is_disabled()) == (strategy == "canary", strategy != "canary")
        for test_id in ("org-reboot-yes", "org-junos-yes"):
            sync_api.expect(page.get_by_test_id(test_id)).to_be_checked()
            sync_api.expect(page.get_by_test_id(test_id)).to_be_enabled()
        sync_api.expect(page.get_by_test_id("org-upgrade-review")).to_be_enabled()
        assert page.locator("[data-org-version-for]:disabled").count() == 0
