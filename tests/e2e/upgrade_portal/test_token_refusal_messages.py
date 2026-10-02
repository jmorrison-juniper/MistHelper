"""Prove token refusal messages through the existing isolated browser portal."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.support.upgrade_portal_e2e.owner import RunOwnerHeaderCheck

if TYPE_CHECKING:
    from playwright.sync_api import Page, Response

sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

TOKEN_MESSAGE = "The portal could not sign you in. Check the token, then try again."
EMPTY_MESSAGE = "The token field is empty. Type your token, then try again."
CLIENT_MESSAGE = "Type a Mist API token before you sign in."
TIMEOUT_MS = 60000


@dataclass(frozen=True)
class TokenBrowserContext:
    """Bind a clean browser page to its isolated evidence and artifacts."""

    page: Page
    token: str
    evidence: Path
    server_log: Path
    artifacts: Path


@pytest.fixture
def token_browser(
    signed_out_page: Page,
    browser_token_value: str,
    browser_token_evidence_path: Path,
    browser_token_server_log_path: Path,
    tmp_path: Path,
) -> TokenBrowserContext:
    """Use the existing server and a browser with no signed-in cookie."""
    return TokenBrowserContext(
        signed_out_page, browser_token_value, browser_token_evidence_path, browser_token_server_log_path, tmp_path
    )


class TokenRefusalBrowser:
    """Read actual responses and safe server evidence without interception."""

    @staticmethod
    def open_form(context: TokenBrowserContext) -> None:
        """Require the owned portal before a sign-in interaction."""
        page = context.page
        response = page.goto("/auth/signin", wait_until="domcontentloaded", timeout=TIMEOUT_MS)
        if response is None:
            raise AssertionError("The isolated portal returned no sign-in response.")
        assert response.status == 200
        # The fixture directory names its process owner without importing a second conftest instance.
        expected_run = context.evidence.parent.name
        assert RunOwnerHeaderCheck(expected_run).require(response.headers) == expected_run
        page.get_by_test_id("signin-mode-browser-token").check()

    @staticmethod
    def evidence_rows(path: Path) -> list[dict[str, object]]:
        """An absent file is valid only before any token boundary event."""
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    @staticmethod
    def assert_alert(context: TokenBrowserContext, message: str, name: str) -> None:
        """Check visual text and the generated signal word for screen readers."""
        alert = context.page.get_by_test_id("signin-error")
        sync_api.expect(alert).to_be_visible(timeout=TIMEOUT_MS)
        sync_api.expect(alert).to_have_text(message)
        assert alert.aria_snapshot() == f'- alert: "Warning: {message}"'
        sync_api.expect(context.page.get_by_test_id("signin-browser-token")).to_have_value("")
        alert.screenshot(path=str(context.artifacts / f"{name}.png"))

    @staticmethod
    def assert_private(context: TokenBrowserContext, submitted: str, response: Response | None = None) -> None:
        """Require readable logs and zero token exposure on browser surfaces."""
        assert context.server_log.is_file(), "The isolated portal server log is missing."
        surfaces = [
            context.page.content(),
            json.dumps(context.page.context.cookies()),
            context.server_log.read_text(encoding="utf-8"),
        ]
        if context.evidence.exists():
            surfaces.append(context.evidence.read_text(encoding="utf-8"))
        if response is not None:
            surfaces.extend((response.text(), json.dumps(response.headers)))
        for surface in surfaces:
            assert submitted not in surface, "A browser token reached a response, cookie, log, or evidence file."

    @staticmethod
    def assert_signed_out(context: TokenBrowserContext) -> None:
        """A refused browser must not acquire access to a session route."""
        response = context.page.request.get("/select/org", headers={"Accept": "application/json"})
        assert response.status == 401
        assert response.json()["error"]["code"] == "not_authenticated"
        expected_run = context.evidence.parent.name
        assert RunOwnerHeaderCheck(expected_run).require(response.headers) == expected_run


class TestTokenRefusalBrowserMessages:
    """Preserve client validation and prove both changed server messages."""

    def test_rejected_token_renders_json_refusal(self, token_browser: TokenBrowserContext) -> None:
        """A normal browser click displays the token-specific cloud refusal."""
        page = token_browser.page
        before = TokenRefusalBrowser.evidence_rows(token_browser.evidence)
        submitted = f"{token_browser.token}-wrong"
        TokenRefusalBrowser.open_form(token_browser)
        page.get_by_test_id("signin-browser-token").fill(submitted)
        with page.expect_response(
            lambda response: response.request.method == "POST" and response.url.endswith("/auth/signin"),
            timeout=TIMEOUT_MS,
        ) as event:
            page.get_by_test_id("signin-submit").click()
        response = event.value
        assert response.status == 400
        assert response.json() == {"error": {"code": "bad_credentials", "message": TOKEN_MESSAGE}}
        TokenRefusalBrowser.assert_alert(token_browser, TOKEN_MESSAGE, "rejected-token")
        rows = TokenRefusalBrowser.evidence_rows(token_browser.evidence)[len(before) :]
        assert [row["event"] for row in rows] == ["browser_token_session"]
        assert rows[0]["accepted"] is False
        assert rows[0]["run_id"] == token_browser.evidence.parent.name
        TokenRefusalBrowser.assert_private(token_browser, submitted, response)
        TokenRefusalBrowser.assert_signed_out(token_browser)

    def test_empty_token_keeps_client_cure(self, token_browser: TokenBrowserContext) -> None:
        """The existing client cure prevents a needless server request."""
        page = token_browser.page
        before = TokenRefusalBrowser.evidence_rows(token_browser.evidence)
        posts: list[str] = []
        TokenRefusalBrowser.open_form(token_browser)
        page.on(
            "request",
            lambda request: (
                posts.append(request.method)
                if request.method == "POST" and request.url.endswith("/auth/signin")
                else None
            ),
        )
        page.get_by_test_id("signin-submit").click()
        TokenRefusalBrowser.assert_alert(token_browser, CLIENT_MESSAGE, "empty-token-client")
        assert posts == []
        assert TokenRefusalBrowser.evidence_rows(token_browser.evidence) == before
        TokenRefusalBrowser.assert_private(token_browser, token_browser.token)
        TokenRefusalBrowser.assert_signed_out(token_browser)

    def test_empty_token_native_submit_renders_server_refusal(self, token_browser: TokenBrowserContext) -> None:
        """Native submission keeps CSRF and server validation active."""
        page = token_browser.page
        before = TokenRefusalBrowser.evidence_rows(token_browser.evidence)
        TokenRefusalBrowser.open_form(token_browser)
        # Native submission bypasses only the browser checks and the script's local empty-field cure.
        with page.expect_navigation(wait_until="domcontentloaded", timeout=TIMEOUT_MS) as navigation:
            page.get_by_test_id("signin-submit").evaluate(
                "(button) => HTMLFormElement.prototype.submit.call(button.form)"
            )
        response = navigation.value
        if response is None:
            raise AssertionError("The native form submission returned no response.")
        assert response.status == 400
        assert response.headers["content-type"].startswith("text/html")
        TokenRefusalBrowser.assert_alert(token_browser, EMPTY_MESSAGE, "empty-token-server")
        assert TokenRefusalBrowser.evidence_rows(token_browser.evidence) == before
        TokenRefusalBrowser.assert_private(token_browser, token_browser.token, response)
        TokenRefusalBrowser.assert_signed_out(token_browser)
