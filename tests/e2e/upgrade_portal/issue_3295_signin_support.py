"""Measure issue #3295 with the shipped form and the process-owned browser portal.

The presentation contract lives in
``specs/3295-signin-credential-layout/contracts/presentation.md``.
No helper imports a conftest module or records a credential value.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from tests.support.upgrade_portal_e2e.owner import RunOwnerHeaderCheck

if TYPE_CHECKING:
    from playwright.sync_api import Locator, Page, Response


@dataclass(frozen=True)
class SigninBrowserContext:
    """Keep a page and its safe evidence under the same process owner."""

    page: Page
    token: str
    evidence: Path
    server_log: Path
    artifacts: Path


class SigninMeasurements:
    """Read actual rectangles, control eligibility, and Chromium listeners."""

    @staticmethod
    def geometry(page: Page) -> dict[str, Any]:
        """Read existing token elements before checking the new group."""
        return page.get_by_test_id("signin-browser-token").evaluate("""input => {
                const box = node => node ? node.getBoundingClientRect().toJSON() : null;
                const group = input.closest('[data-testid="signin-browser-token-group"]');
                const buttons = Array.from(input.form.querySelectorAll('input[name="mode"]'));
                const note = document.getElementById(input.getAttribute("aria-describedby"));
                return {
                    label: box(input.labels[0]), field: box(input), note: box(note),
                    group: box(group), buttons: buttons.map(node => box(node.nextElementSibling)),
                    labels: input.labels.length, notes: note ? 1 : 0,
                    groups: input.form.querySelectorAll('[data-testid="signin-browser-token-group"]').length,
                    pageWidth: document.documentElement.clientWidth,
                    pageScroll: document.documentElement.scrollWidth,
                    formWidth: input.form.clientWidth, formScroll: input.form.scrollWidth,
                    overflow: Array.from(document.querySelectorAll("body *")).filter(node =>
                        node.getBoundingClientRect().right > document.documentElement.clientWidth
                    ).map(node => ({tag: node.tagName, id: node.id,
                        testid: node.getAttribute("data-testid"), right: node.getBoundingClientRect().right,
                        dependency: Boolean(node.closest("#dependency-panel"))})),
                    groupWidth: group ? group.clientWidth : 0,
                    groupScroll: group ? group.scrollWidth : 0
                };
            }""")

    @staticmethod
    def mode(page: Page) -> dict[str, Any]:
        """Read visibility and successful controls without reading their values."""
        return page.get_by_test_id("signin-browser-token").evaluate("""input => {
                const visible = node => Boolean(node && node.getClientRects().length
                    && getComputedStyle(node).visibility !== "hidden");
                const note = document.getElementById(input.getAttribute("aria-describedby"));
                return {
                    selected: input.form.querySelector('input[name="mode"]:checked').value,
                    fieldVisible: visible(input), noteVisible: visible(note),
                    disabled: input.disabled, focused: document.activeElement === input,
                    tokenInForm: new FormData(input.form).has("token"),
                    emailRequired: input.form.elements.email.required,
                    passwordRequired: input.form.elements.password.required
                };
            }""")

    @staticmethod
    def prefix(alert: Locator) -> dict[str, str]:
        """Measure the generated prefix, not the surrounding message weight."""
        return alert.evaluate("""node => {
                const prefix = getComputedStyle(node, "::before");
                const message = getComputedStyle(node);
                return {content: prefix.content, weight: prefix.fontWeight,
                    foreground: message.color, background: message.backgroundColor,
                    whitespace: prefix.whiteSpace};
            }""")

    @staticmethod
    def listeners(page: Page) -> dict[str, int]:
        """Count actual listeners through Chromium without replacing registration."""
        session = page.context.new_cdp_session(page)
        counts: dict[str, int] = {}
        try:
            for selector in (
                "form",
                '[data-testid="signin-mode-provider"]',
                '[data-testid="signin-mode-browser-token"]',
            ):
                reference = session.send(
                    "Runtime.evaluate", {"expression": f"document.querySelector({json.dumps(selector)})"}
                )
                object_id = reference["result"]["objectId"]
                listeners = session.send("DOMDebugger.getEventListeners", {"objectId": object_id})["listeners"]
                counts[selector] = len(listeners)
        finally:
            session.detach()
        return counts

    @staticmethod
    def focus(page: Page) -> str:
        """Return a safe control identifier for keyboard evidence."""
        return page.evaluate("""() => {
                const node = document.activeElement;
                return node.getAttribute("data-testid") || node.id || node.tagName.toLowerCase();
            }""")


class SigninGuards:
    """Fail on missing measurements and on exact presentation defects."""

    @staticmethod
    def alignment(measurement: dict[str, Any]) -> None:
        """Require the complete label directly above the field."""
        label, field = measurement["label"], measurement["field"]
        assert measurement["labels"] == 1, "Checked token labels: expected exactly 1."
        assert isinstance(label, dict) and isinstance(field, dict), "The label or field measurement is missing."
        coordinates = [rectangle[key] for rectangle in (label, field) for key in ("left", "top", "right", "bottom")]
        assert all(math.isfinite(value) for value in coordinates), "The label or field measurement is not finite."
        assert all(
            rectangle["right"] > rectangle["left"] and rectangle["bottom"] > rectangle["top"]
            for rectangle in (label, field)
        ), "The label or field rectangle has no area."
        assert (
            abs(label["left"] - field["left"]) <= 1
        ), "The label left edge differs from the field by more than 1 pixel."
        gap = field["top"] - label["bottom"]
        assert gap >= 0, "The label overlaps the field."
        assert gap <= 16, "The label-to-field gap exceeds 16 pixels."

    @staticmethod
    def containment(measurement: dict[str, Any]) -> None:
        """Require the semantic group below every mode button."""
        group, buttons = measurement["group"], measurement["buttons"]
        assert measurement["groups"] == 1 and isinstance(group, dict), "Checked token groups: expected exactly 1."
        assert len(buttons) >= 1, "The mode button measurements are missing."
        assert measurement["notes"] == 1, "Checked token notes: expected exactly 1."
        assert group["top"] >= max(button["bottom"] for button in buttons), "The token group overlaps a mode button."
        for name in ("label", "field", "note"):
            rectangle = measurement[name]
            assert isinstance(rectangle, dict), f"The {name} measurement is missing."
            assert rectangle["left"] >= group["left"] - 1, f"The {name} starts outside the token group."
            assert rectangle["right"] <= group["right"] + 1, f"The {name} ends outside the token group."
            assert rectangle["top"] >= group["top"] - 1, f"The {name} is above the token group."
            assert rectangle["bottom"] <= group["bottom"] + 1, f"The {name} is below the token group."
        assert measurement["groupScroll"] <= measurement["groupWidth"], "The token group has horizontal overflow."

    @staticmethod
    def geometry(measurement: dict[str, Any]) -> None:
        """State the measured counts before applying each geometry guard."""
        print(
            f"Issue 3295 geometry checked {measurement['labels']} label, 1 field, "
            f"{measurement['notes']} note, {measurement['groups']} group, "
            f"and {len(measurement['buttons'])} mode buttons."
        )
        SigninGuards.alignment(measurement)
        SigninGuards.containment(measurement)
        assert measurement["formScroll"] <= measurement["formWidth"], "The sign-in form has horizontal overflow."
        assert measurement["group"]["right"] <= measurement["pageWidth"], "The token group exceeds the viewport."
        assert measurement["group"]["left"] >= 0, "The token group starts outside the viewport."

    @staticmethod
    def mode(measurement: dict[str, Any], active: bool) -> None:
        """Require the inactive mode to hide, disable, and exclude the token."""
        print("Issue 3295 mode checked 1 token field and 1 explanatory note.")
        assert measurement["fieldVisible"] is active, "The token field visibility differs from its mode."
        assert measurement["noteVisible"] is active, "The token note visibility differs from its mode."
        assert measurement["disabled"] is not active, "The token field eligibility differs from its mode."
        assert measurement["tokenInForm"] is active, "The inactive token enters successful form controls."
        if not active:
            assert measurement["focused"] is False, "The inactive token has keyboard focus."

    @staticmethod
    def prefix(measurement: dict[str, str]) -> None:
        """Require the unchanged signal word and the common bold weight."""
        print("Issue 3295 Warning style checked 1 generated prefix.")
        assert measurement["content"] == '"Warning: "', "The Warning prefix or its space changed."
        assert measurement["weight"] == "700", "The Warning prefix does not have weight 700."
        assert measurement["whitespace"] == "nowrap", "The Warning prefix can wrap."


class SigninJourney:
    """Drive only the existing owned sign-in and error routes."""

    @staticmethod
    def open(context: SigninBrowserContext, theme: str = "magenta") -> None:
        """Require the actual sign-in response and its process owner."""
        logging.getLogger(__name__).info("Opening the owned sign-in page.")
        response = context.page.goto(f"/auth/signin?theme={theme}", wait_until="networkidle", timeout=60000)
        assert response is not None and response.status == 200, "The sign-in route did not answer 200."
        owner = context.evidence.parent.name
        assert RunOwnerHeaderCheck(owner).require(response.headers) == owner
        assert context.page.get_by_test_id("signin-mode-provider").is_checked() is True
        logging.getLogger(__name__).debug("Opened 1 sign-in page for the expected owner.")

    @staticmethod
    def save(context: SigninBrowserContext, name: str, measurement: object) -> None:
        """Retain only measurements and screenshots with cleared token fields."""
        logging.getLogger(__name__).info("Saving the safe sign-in evidence for %s.", name)
        token = context.page.get_by_test_id("signin-browser-token")
        if token.count():
            assert token.input_value() == ""
        else:
            assert context.page.get_by_test_id("error-page").count() == 1, "The safe screenshot page is missing."
        context.artifacts.mkdir(parents=True, exist_ok=True)
        (context.artifacts / f"{name}.json").write_text(json.dumps(measurement, indent=2), encoding="utf-8")
        context.page.screenshot(path=str(context.artifacts / f"{name}.png"), full_page=True)
        logging.getLogger(__name__).debug("Saved 1 measurement and 1 safe screenshot.")

    @staticmethod
    def events(context: SigninBrowserContext) -> list[dict[str, Any]]:
        """Read the existing process-owned evidence without deleting another test's rows."""
        if not context.evidence.exists():
            return []
        rows = [json.loads(line) for line in context.evidence.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert all(row["run_id"] == context.evidence.parent.name for row in rows), "The evidence has another owner."
        return rows

    @staticmethod
    def private(context: SigninBrowserContext, submitted: str, response: Response) -> None:
        """Require readable logs and zero returned or persistent token surfaces."""
        assert context.server_log.is_file() is True, "The owned server log is missing."
        storage = context.page.evaluate("() => [JSON.stringify(localStorage), JSON.stringify(sessionStorage)]")
        surfaces = [
            context.page.content(),
            response.text(),
            json.dumps(response.headers),
            json.dumps(context.page.context.cookies()),
            context.server_log.read_text(encoding="utf-8"),
            *storage,
        ]
        if context.evidence.exists():
            surfaces.append(context.evidence.read_text(encoding="utf-8"))
        assert all(
            submitted not in surface for surface in surfaces
        ), "A token reached a returned or persistent surface."
        assert submitted not in json.dumps(response.request.headers), "A token reached a request header."
        assert submitted not in response.request.url, "A token reached a request URL."
        answer = context.page.request.get("/select/org", headers={"Accept": "application/json"})
        assert answer.status == 401 and answer.json()["error"]["code"] == "not_authenticated"
        assert submitted not in answer.text(), "A refused token reached session metadata."
        assert RunOwnerHeaderCheck(context.evidence.parent.name).require(answer.headers) == context.evidence.parent.name

    @staticmethod
    def keyboard(context: SigninBrowserContext) -> list[dict[str, str]]:
        """Verify exact native radio traversal after Tab reaches the provider."""
        evidence: list[dict[str, str]] = []
        assert SigninMeasurements.focus(context.page) == "signin-mode-provider", "Tab did not reach the provider mode."
        sequence = [
            ("ArrowRight", "signin-mode-browser-token"),
            ("Tab", "signin-browser-token"),
            ("Tab", "signin-submit"),
            ("Shift+Tab", "signin-browser-token"),
            ("Shift+Tab", "signin-mode-browser-token"),
            ("ArrowLeft", "signin-mode-provider"),
            ("Tab", "signin-submit"),
            ("Shift+Tab", "signin-mode-provider"),
            ("ArrowRight", "signin-mode-browser-token"),
            ("Tab", "signin-browser-token"),
        ]
        for key, expected in sequence:
            context.page.keyboard.press(key)
            focused = SigninMeasurements.focus(context.page)
            evidence.append({"key": key, "focus": focused})
            assert focused == expected, f"After {key}, focus is {focused}, not {expected}."
        return evidence


class SigninTheme:
    """Distinguish native upgrade themes from genuine main-asset compatibility."""

    native = ("magenta", "default")
    main = ("light", "dark", "magenta", "high-contrast")

    @staticmethod
    def apply(context: SigninBrowserContext, name: str, catalog: str) -> dict[str, Any]:
        """Load original stylesheet bytes through one same-origin browser route."""
        root = Path(__file__).resolve().parents[3]
        if catalog == "native":
            path = root / "src/upgrade_portal/app/assets/static/css/themes" / f"{name}.css"
            url = f"/static/css/themes/{name}.css?issue3295=measure"
        else:
            assert catalog == "main" and name in SigninTheme.main, "The compatibility asset is not allowlisted."
            path = root / "web_portal/static/css/themes" / f"{name}.css"
            url = f"/__issue3295__/themes/main/{name}.css?issue3295=measure"
            content = path.read_bytes()
            context.page.route(f"**{url}", lambda route: route.fulfill(body=content, content_type="text/css"))
        evidence = SigninTheme.loaded(context, path, url)
        evidence["catalog"], evidence["theme"] = catalog, name
        evidence["asset"] = str(path.relative_to(root))
        return evidence

    @staticmethod
    def loaded(context: SigninBrowserContext, path: Path, url: str) -> dict[str, Any]:
        """Verify actual asset bytes and an active sheet without a fallback."""
        name = path.stem
        with context.page.expect_response(lambda response: response.url.endswith(url), timeout=60000) as event:
            context.page.evaluate(
                """([url, scheme]) => {
                    document.documentElement.setAttribute("data-bs-theme", scheme);
                    document.getElementById("theme-css").href = url;
                }""",
                [url, "light" if name in ("light", "default") else "dark"],
            )
        response = event.value
        assert response.status == 200, "The actual theme asset did not answer 200."
        digest = hashlib.sha256(response.body()).hexdigest()
        assert digest == hashlib.sha256(path.read_bytes()).hexdigest(), "The loaded theme differs from the original."
        context.page.wait_for_function(
            """url => Array.from(document.styleSheets).some(sheet => sheet.href && sheet.href.endsWith(url))""", arg=url
        )
        applied = context.page.evaluate(
            "() => getComputedStyle(document.documentElement).getPropertyValue('--portal-bg').trim()"
        )
        declaration = re.search(r"--portal-bg:\s*([^;]+);", path.read_text(encoding="utf-8"))
        assert declaration is not None, "The theme background declaration is missing."
        assert applied == declaration.group(1).strip(), "The theme background uses a fallback or another asset."
        return {"sha256": digest, "background": applied, "status": response.status}

    @staticmethod
    def variants() -> list[tuple[str, str]]:
        """Name every native and compatibility cell without inventing aliases."""
        return [*(("native", name) for name in SigninTheme.native), *(("main", name) for name in SigninTheme.main)]
