"""Exercise the actual sign-in script and direct presentation-guard failures.

The Node probe records control states and request counts, never credentials.
The guards are the same guards that read the real Chromium page.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tests.e2e.upgrade_portal.issue_3295_signin_support import SigninGuards
from tests.support.upgrade_portal_e2e.owner import RunOwnerHeaderCheck


class PresentationSamples:
    """Provide finite measurements for direct guard decisions."""

    @staticmethod
    def rectangle(left: int, top: int, width: int, height: int) -> dict[str, int]:
        """Construct one explicit measured rectangle for negative controls."""
        return {"left": left, "top": top, "right": left + width, "bottom": top + height}

    @staticmethod
    def geometry() -> dict[str, Any]:
        """Provide one valid record, including every required count."""
        return {
            "label": PresentationSamples.rectangle(20, 60, 100, 20),
            "field": PresentationSamples.rectangle(20, 88, 300, 38),
            "note": PresentationSamples.rectangle(20, 134, 300, 40),
            "group": PresentationSamples.rectangle(20, 60, 300, 114),
            "buttons": [PresentationSamples.rectangle(20, 10, 200, 40)],
            "labels": 1,
            "notes": 1,
            "groups": 1,
            "pageWidth": 360,
            "pageScroll": 360,
            "formWidth": 300,
            "formScroll": 300,
            "groupWidth": 300,
            "groupScroll": 300,
        }

    @staticmethod
    def mode(active: bool) -> dict[str, bool]:
        """Provide one complete active or inactive control measurement."""
        return {
            "fieldVisible": active,
            "noteVisible": active,
            "disabled": not active,
            "tokenInForm": active,
            "focused": False,
        }


class NodeSigninProbe:
    """Run the shipped script against an explicit, offline DOM stand-in."""

    script = r"""
const fs = require("node:fs");
const vm = require("node:vm");
const settings = JSON.parse(fs.readFileSync(0, "utf8"));
const source = fs.readFileSync(process.argv[1], "utf8");
class Control {
    constructor(value, required = false) {
        this.value = value;
        this.attributes = new Set(required ? ["required"] : []);
        this.listeners = {};
        this.disabled = true;
        this.hidden = true;
        this.textContent = "";
    }
    hasAttribute(name) { return this.attributes.has(name); }
    setAttribute(name) { this.attributes.add(name); }
    removeAttribute(name) { this.attributes.delete(name); }
    addEventListener(name, listener) {
        this.listeners[name] = this.listeners[name] || [];
        this.listeners[name].push(listener);
    }
}
const email = new Control("fake.operator@example.invalid", settings.emailRequired !== false);
const password = new Control("fake-password-for-node-only", settings.passwordRequired !== false);
const token = new Control(settings.empty ? " \t " : "fake-token-for-node-only");
const group = new Control("");
const error = new Control("");
const host = new Control("api.eu.mist.com");
const modes = ["provider_login", "browser_token", "environment_token"].map(value => new Control(value));
const form = new Control("");
let selected = modes[0];
const controls = {
    "signin-browser-token": settings.missingInput ? null : token,
    "signin-email": settings.missingEmail ? null : email,
    "signin-password": settings.missingPassword ? null : password,
    "signin-error": error
};
function query(selector) {
    if (selector === 'input[name="mode"]:checked') { return selected; }
    if (selector === 'select[name="host"]') { return host; }
    if (selector === 'meta[name="csrf-token"]') {
        return {getAttribute: () => "fake-csrf-for-node-only"};
    }
    const match = selector.match(/data-testid="([^"]+)"/);
    return match ? controls[match[1]] : null;
}
form.querySelector = query;
form.querySelectorAll = () => modes;
token.closest = selector => selector === "form" ? (settings.missingForm ? null : form)
    : (settings.missingGroup ? null : group);
const requests = [];
const context = {
    document: {readyState: "loading", addEventListener() {}, querySelector: query},
    window: {location: {assign() {}}}, FormData: class FormData {},
    fetch: (url, options) => {
        const body = JSON.parse(options.body);
        requests.push({
            url, keys: Object.keys(body).sort(), mode: body.mode, host: body.host,
            cleared: token.value === "", json: options.headers["Content-Type"],
            csrf: Boolean(options.headers["X-CSRFToken"]), credentials: options.credentials
        });
        return Promise.resolve({
            ok: false, status: settings.status || 400,
            text: () => Promise.resolve(JSON.stringify({error: {
                code: "bad_credentials",
                message: "The portal could not sign you in. Check the token, then try again."
            }}))
        });
    }
};
vm.createContext(context);
vm.runInContext(source, context);
context.window.upgradePortal.initBrowserTokenSignIn();
const states = [];
function record() {
    states.push({
        selected: selected.value, hidden: group.hidden, disabled: token.disabled,
        emailRequired: email.hasAttribute("required"), passwordRequired: password.hasAttribute("required"),
        tokenPreserved: token.value === (settings.empty ? " \t " : "fake-token-for-node-only"),
        providerPreserved: email.value === "fake.operator@example.invalid"
            && password.value === "fake-password-for-node-only",
        hostPreserved: host.value === "api.eu.mist.com"
    });
}
record();
for (const value of ["browser_token", "provider_login", "environment_token", "browser_token"]) {
    selected = modes.find(mode => mode.value === value);
    for (const listener of selected.listeners.change || []) { listener(); }
    record();
}
for (let cycle = 0; cycle < 10; cycle++) {
    for (const index of [0, 1]) {
        selected = modes[index];
        for (const listener of selected.listeners.change || []) { listener(); }
    }
}
const beforeSubmit = requests.length;
let prevented = false;
for (const listener of form.listeners.submit || []) {
    listener({preventDefault() { prevented = true; }});
}
setImmediate(() => {
    process.stdout.write(JSON.stringify({
        states, beforeSubmit, requests, prevented, tokenCleared: token.value === "",
        submitListeners: (form.listeners.submit || []).length,
        modeListeners: modes.map(mode => (mode.listeners.change || []).length),
        message: error.textContent, errorVisible: !error.hidden
    }));
});
"""

    @staticmethod
    def run(settings: dict[str, Any]) -> dict[str, Any]:
        """Require Node and report its actual controller result."""
        node = shutil.which("node")
        if node is None:
            pytest.fail("Node is missing. The actual sign-in controller cannot be verified.")
        root = Path(__file__).resolve().parents[3]
        source = root / "src/upgrade_portal/app/assets/static/js/portal.js"
        logging.getLogger(__name__).info("Running the offline sign-in controller probe.")
        result = subprocess.run(
            [node, "-e", NodeSigninProbe.script, str(source)],
            input=json.dumps(settings),
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=True,
            timeout=15,
        )
        measured = json.loads(result.stdout)
        logging.getLogger(__name__).debug("Measured %s mode states.", len(measured["states"]))
        return measured

    @staticmethod
    def assert_modes(result: dict[str, Any], password_required: bool) -> None:
        """Require preserved values and each original validation baseline."""
        states = result["states"]
        assert [state["selected"] for state in states] == [
            "provider_login",
            "browser_token",
            "provider_login",
            "environment_token",
            "browser_token",
        ]
        for state in states:
            active = state["selected"] == "browser_token"
            assert state["hidden"] is not active and state["disabled"] is not active
            assert state["emailRequired"] is not active
            assert state["passwordRequired"] is (password_required and not active)
            assert state["tokenPreserved"] is True and state["providerPreserved"] is True
            assert state["hostPreserved"] is True


class TestSigninPresentationNegativeControls:
    """Prove that exact geometry, mode, style, and ownership guards can fail."""

    @pytest.mark.parametrize(
        ("target", "key", "value", "reason"),
        [
            ("label", "left", 22, "left edge"),
            ("label", "bottom", 89, "overlaps the field"),
            ("field", "top", 97, "gap exceeds"),
            ("group", "top", 49, "overlaps a mode button"),
            ("note", "right", 322, "outside the token group"),
            ("note", "bottom", 176, "below the token group"),
            ("label", "left", float("nan"), "not finite"),
            ("field", "right", 20, "no area"),
        ],
    )
    def test_bad_geometry_is_rejected(self, target: str, key: str, value: float, reason: str) -> None:
        """Reject a precise bad coordinate through the actual browser guard."""
        measured = PresentationSamples.geometry()
        measured[target][key] = value
        with pytest.raises(AssertionError, match=reason):
            SigninGuards.geometry(measured)

    @pytest.mark.parametrize(
        ("key", "value", "reason"),
        [
            ("labels", 0, "exactly 1"),
            ("notes", 0, "exactly 1"),
            ("groups", 0, "exactly 1"),
            ("buttons", [], "measurements are missing"),
            ("field", None, "measurement is missing"),
            ("groupScroll", 301, "group has horizontal overflow"),
            ("formScroll", 301, "form has horizontal overflow"),
            ("pageWidth", 319, "exceeds the viewport"),
        ],
    )
    def test_missing_or_overflowing_geometry_is_rejected(self, key: str, value: Any, reason: str) -> None:
        """Fail when required input is unreadable, empty, or outside its width."""
        measured = PresentationSamples.geometry()
        measured[key] = value
        with pytest.raises(AssertionError, match=reason):
            SigninGuards.geometry(measured)

    @pytest.mark.parametrize("key", ["fieldVisible", "noteVisible", "disabled", "tokenInForm", "focused"])
    def test_bad_inactive_mode_is_rejected(self, key: str) -> None:
        """Reject each inactive-state defect without a browser dependency."""
        measured = PresentationSamples.mode(False)
        measured[key] = not measured[key]
        with pytest.raises(AssertionError, match="visibility|eligibility|successful|focus"):
            SigninGuards.mode(measured, False)

    @pytest.mark.parametrize(("key", "value"), [("weight", "400"), ("content", '"Warning:"'), ("whitespace", "normal")])
    def test_bad_warning_style_is_rejected(self, key: str, value: str) -> None:
        """Reject normal weight, lost spacing, and a wrapping prefix."""
        measured = {"weight": "700", "content": '"Warning: "', "whitespace": "nowrap"}
        measured[key] = value
        with pytest.raises(AssertionError, match="Warning prefix"):
            SigninGuards.prefix(measured)

    @pytest.mark.parametrize("headers", [{}, {"X-MistHelper-E2E-Run-ID": "foreign-issue3295-run"}])
    def test_missing_or_foreign_process_owner_is_rejected(self, headers: dict[str, str]) -> None:
        """Keep the shared ownership guard active without importing conftest."""
        with pytest.raises(AssertionError, match="owner|run|Run|header|Header"):
            RunOwnerHeaderCheck("issue3295-owned-run").require(headers)


class TestActualSigninController:
    """Exercise the actual shipped initializer, not a copied mode algorithm."""

    @pytest.mark.parametrize("password_required", [True, False])
    def test_modes_preserve_values_and_required_baselines(self, password_required: bool) -> None:
        """Restore each original requirement and submit exactly once."""
        result = NodeSigninProbe.run({"passwordRequired": password_required})
        NodeSigninProbe.assert_modes(result, password_required)
        assert result["beforeSubmit"] == 0 and result["submitListeners"] == 1
        assert result["modeListeners"] == [1, 1, 1] and result["prevented"] is True
        assert len(result["requests"]) == 1 and result["tokenCleared"] is True
        request = result["requests"][0]
        assert request == {
            "url": "/auth/signin",
            "keys": ["host", "mode", "token"],
            "mode": "browser_token",
            "host": "api.eu.mist.com",
            "cleared": True,
            "json": "application/json",
            "csrf": True,
            "credentials": "same-origin",
        }

    @pytest.mark.parametrize("missing", ["missingInput", "missingForm", "missingGroup"])
    def test_missing_signin_structure_starts_no_listener(self, missing: str) -> None:
        """An absent complete sign-in group must not affect another page."""
        result = NodeSigninProbe.run({missing: True})
        assert result["requests"] == [] and result["submitListeners"] == 0
        assert result["modeListeners"] == [0, 0, 0]
        assert result["states"][0]["emailRequired"] is True
        assert result["states"][0]["passwordRequired"] is True

    @pytest.mark.parametrize("missing", ["missingEmail", "missingPassword"])
    def test_trimmed_provider_fields_keep_the_token_controller_usable(self, missing: str) -> None:
        """Keep the existing harmless guard for an omitted provider field."""
        result = NodeSigninProbe.run({missing: True})
        assert len(result["requests"]) == 1 and result["submitListeners"] == 1
        assert result["tokenCleared"] is True and result["errorVisible"] is True
        assert result["message"] == "The portal could not sign you in. Check the token, then try again."

    def test_empty_token_sends_zero_requests(self) -> None:
        """The actual client cure must stop whitespace-only token submission."""
        result = NodeSigninProbe.run({"empty": True})
        assert result["requests"] == [] and result["prevented"] is True
        assert result["message"] == "Type a Mist API token before you sign in."
        assert result["beforeSubmit"] == 0 and result["errorVisible"] is True

    @pytest.mark.parametrize("status", [400, 503])
    def test_http_refusal_keeps_the_token_cleared(self, status: int) -> None:
        """Client and service failures must keep the existing safe message."""
        result = NodeSigninProbe.run({"status": status})
        assert len(result["requests"]) == 1 and result["tokenCleared"] is True
        assert result["message"] == "The portal could not sign you in. Check the token, then try again."
        assert result["errorVisible"] is True


class TestSigninCollectionBoundary:
    """Prove missing-package behavior through a fresh full-tree pytest process."""

    script = """
import importlib.abc
import json
import sys
class MissingBrowser(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "playwright" or fullname.startswith("playwright."):
            raise ModuleNotFoundError("No module named 'playwright'")
sys.meta_path.insert(0, MissingBrowser())
import pytest
options = [sys.argv[1], "--collect-only", "-q", "-rs", "-p", "no:cacheprovider", "-p", "pytest_timeout"]
status = pytest.main(options)
identities = [name for name, module in sys.modules.items()
    if name.endswith("conftest") and "upgrade_portal" in str(getattr(module, "__file__", ""))]
print("Issue 3295 fixture package identity: " + json.dumps(sorted(identities)))
raise SystemExit(status)
"""

    @staticmethod
    def collect(tree: str, strict: str) -> subprocess.CompletedProcess[str]:
        """Isolate package absence from the real environment and fixture module."""
        root = Path(__file__).resolve().parents[3]
        environment = {**os.environ, "UPGRADE_PORTAL_E2E_STRICT": strict, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
        logging.getLogger(__name__).info("Collecting the missing-package browser tree %s.", tree)
        result = subprocess.run(
            [sys.executable, "-B", "-c", TestSigninCollectionBoundary.script, tree],
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )
        logging.getLogger(__name__).debug("The missing-package collection returned %s.", result.returncode)
        return result

    @pytest.mark.parametrize(
        ("tree", "strict", "expected"),
        [
            ("tests/e2e/upgrade_portal/", "0", 5),
            ("tests/e2e/upgrade_portal/", "1", 4),
            ("tests/e2e/", "0", 2),
            ("tests/e2e/", "1", 2),
        ],
    )
    def test_missing_browser_package_preserves_the_collection_policy(
        self, tree: str, strict: str, expected: int
    ) -> None:
        """Keep the new module safe and expose the unrelated full-tree import fault."""
        result = self.collect(tree, strict)
        assert result.returncode == expected, result.stdout + result.stderr
        report = result.stdout + result.stderr
        assert "NameError" not in report and "INTERNALERROR" not in report
        identities = json.loads(report.split("Issue 3295 fixture package identity: ", 1)[1].splitlines()[0])
        assert identities.count("tests.e2e.upgrade_portal.conftest") == 1
        assert all(name.startswith("tests.e2e.upgrade_portal.") for name in identities)
        if strict == "1":
            assert "not installed" in report and "forbids a skip" in report
        else:
            assert "skipped" in report and "test_issue_3295_signin_layout.py" in report
        if tree == "tests/e2e/":
            assert "ERROR collecting tests/e2e/test_map_title_contrast.py" in report
        print(f"Issue 3295 missing-package collection checked {tree}, strict={strict}, exit={result.returncode}.")
