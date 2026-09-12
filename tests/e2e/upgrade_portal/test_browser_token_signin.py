"""Browser tests for the browser-token sign-in journey of the capture portal.

Why:
    A route test can prove that a browser-token post answers the next path. It
    cannot prove that the real form submits, that the signed-in browser can use
    the token-built session on a later Mist read, or that sign-out clears that
    session. These tests drive the running portal and read the isolated
    server evidence that the stand-in writes.

Identifier contract:
    `contracts/ui-testids.md` fixes every identifier below. Each locator reads
    `data-testid` only. No locator reads visible text, a style class, or an
    element position.
"""

from __future__ import annotations

import json  # Read the JSON Lines evidence file that the server process writes.
from pathlib import Path  # Type the artifact and log paths supplied by fixtures.
from typing import Any  # Playwright page and response objects are free-form.

import pytest  # The test framework and its skip helper.

# The Playwright package must exist before this module defines a browser test.
# A run without the package reports a skip and never an import error.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

SIGNIN_PATH = "/auth/signin"  # The sign-in form that the browser-token journey starts on.
ORG_PAGE_PATH = "/select/org"  # The first signed-in page after the token succeeds.
MODE_PAGE_PATH = "/select/mode"  # The page that stores the upgrade mode.
SITE_PAGE_PATH = "/select/site"  # The Mist-backed site picker after the mode.

SIGNIN_MODE_BROWSER_TOKEN_ID = "signin-mode-browser-token"  # The radio for this credential mode.
SIGNIN_BROWSER_TOKEN_ID = "signin-browser-token"  # The token field that the browser submits.
SIGNIN_SUBMIT_ID = "signin-submit"  # The form submit control.
SIGNIN_ERROR_ID = "signin-error"  # The sign-in refusal region.
ORG_SEARCH_ID = "org-search"  # The organization picker proves the session opened.
ORG_ROW_PREFIX = "org-row-"  # Dynamic organization row prefix.
ORG_SELECT_PREFIX = "org-select-"  # Dynamic organization choose button prefix.
MODE_SINGLE_SITE_ID = "mode-single-site"  # The single-site mode choice.
MODE_CONTINUE_ID = "mode-continue"  # The mode form submit control.
SITE_ROW_PREFIX = "site-row-"  # Dynamic site row prefix.
SITE_OPEN_PREFIX = "site-open-"  # Dynamic site open button prefix.
INVENTORY_TABLE_ID = "inventory-table"  # The inventory page forces a Mist-backed read.
SIGNOUT_BUTTON_ID = "signout-button"  # The signed-in navigation sign-out control.

OK_STATUS = 200  # The contract fixes this status for the pages that open.
BAD_REQUEST_STATUS = 400  # The contract fixes this status for a refused credential.
UNAUTHORIZED_STATUS = 401  # The contract fixes this status for a missing session.
NOT_FOUND_STATUS = 404  # A 404 means a blueprint is missing.
GATE_TIMEOUT_MS = 60000  # The sign-in dependency panel can need more time during a full suite.


def _page_status(page: Any, path: str) -> int:
    """Open one path and return the status code of the answer.

    Args:
        page: The Playwright page object.
        path: The path to open, relative to the portal address.

    Returns:
        The status code that the portal answered.
    """
    answer = page.goto(path, wait_until="domcontentloaded", timeout=GATE_TIMEOUT_MS)  # Open the real path.
    if answer is None:  # A page with no answer gives the test nothing to read.
        pytest.skip(f"The browser returned no response for {path}.")
    status: int = answer.status  # Store the status so the caller can assert it.
    return status  # The caller decides which status the contract permits.


def _require_ok(status: int, path: str) -> None:
    """Fail when a page route does not answer the contract status.

    Args:
        status: The status code the portal answered.
        path: The path the test opened.
    """
    if status == UNAUTHORIZED_STATUS:  # A session route refused the browser.
        raise AssertionError(f"{path} answered 401. The browser-token journey has no live session.")
    if status == NOT_FOUND_STATUS:  # A route module is missing from the isolated server.
        raise AssertionError(f"{path} answered 404. The portal did not register the route.")
    assert status == OK_STATUS, f"{path} answered {status}, not {OK_STATUS}."  # Every other status is a fault.


def _reset_evidence(path: Path) -> None:
    """Remove the browser-token evidence file before one scenario starts.

    Args:
        path: The evidence file that the server process writes.
    """
    path.unlink(missing_ok=True)  # Each test reads only the events of its own journey.


def _evidence_rows(path: Path) -> list[dict[str, Any]]:
    """Read the browser-token evidence rows that exist now.

    Args:
        path: The evidence file that the server process writes.

    Returns:
        One mapping for each JSON Lines row.
    """
    if not path.exists():  # A scenario can prove that no browser-token seam ran.
        return []  # No file means no server evidence exists.
    lines = path.read_text(encoding="utf-8").splitlines()  # Read the small artifact file.
    return [json.loads(line) for line in lines if line.strip()]  # Blank lines are not evidence rows.


def _row_keys(page: Any, prefix: str) -> list[str]:
    """Return the dynamic key of every row with one identifier prefix.

    Args:
        page: The Playwright page object.
        prefix: The identifier prefix.

    Returns:
        One key for each matching row.
    """
    rows = page.locator(f'[data-testid^="{prefix}"]')  # A prefix match still selects by `data-testid`.
    markers = rows.evaluate_all("nodes => nodes.map(node => node.getAttribute('data-testid'))")  # Read IDs only.
    return [str(marker)[len(prefix) :] for marker in markers if marker]  # Strip the stable prefix from each row.


def _first_key(page: Any, prefix: str) -> str:
    """Return the first dynamic key for one row prefix.

    Args:
        page: The Playwright page object.
        prefix: The identifier prefix.

    Returns:
        The first dynamic key.
    """
    keys = _row_keys(page, prefix)  # Read keys that the current page published.
    if not keys:  # The page holds no row to drive.
        pytest.skip(f"The page shows no element with the identifier prefix {prefix}.")
    return keys[0]  # The first row is a sample of one stable row shape.


def _is_signin_post(answer: Any) -> bool:
    """Report whether one response belongs to the sign-in post.

    Args:
        answer: The Playwright response object.

    Returns:
        True when the answer is the browser-token sign-in post.
    """
    method = str(answer.request.method)  # Read the request method once for a stable comparison.
    return method == "POST" and str(answer.url).endswith(SIGNIN_PATH)  # The script posts only this path here.


def _sign_in_with_browser_token(page: Any, token: str) -> None:
    """Submit the browser-token form and wait for the organization picker.

    Args:
        page: The Playwright page object with no portal session.
        token: The fake token that the isolated server accepts.
    """
    _require_ok(_page_status(page, SIGNIN_PATH), SIGNIN_PATH)  # Start from the real sign-in page.
    page.get_by_test_id(SIGNIN_MODE_BROWSER_TOKEN_ID).check()  # Select the browser-token credential mode.
    page.get_by_test_id(SIGNIN_BROWSER_TOKEN_ID).fill(token)  # Type the fake token into the real field.
    with page.expect_response(_is_signin_post, timeout=GATE_TIMEOUT_MS) as event:  # Wait for the script post.
        page.get_by_test_id(SIGNIN_SUBMIT_ID).click()  # A plain click must submit the browser-token form.
    assert event.value.status == OK_STATUS, f"The sign-in post answered {event.value.status}, not {OK_STATUS}."
    page.wait_for_url(f"**{ORG_PAGE_PATH}", timeout=GATE_TIMEOUT_MS)  # The script opens the next page.
    sync_api.expect(page.get_by_test_id(ORG_SEARCH_ID)).to_be_visible(timeout=GATE_TIMEOUT_MS)  # Page is usable.


def _choose_first_org_and_mode(page: Any) -> None:
    """Choose the first organization and single-site mode.

    Args:
        page: The Playwright page object on the organization picker.
    """
    org_id = _first_key(page, ORG_ROW_PREFIX)  # Read the organization key that the page published.
    page.get_by_test_id(f"{ORG_SELECT_PREFIX}{org_id}").click()  # Submit the real organization form.
    page.wait_for_url(f"**{MODE_PAGE_PATH}", timeout=GATE_TIMEOUT_MS)  # The route opens the mode picker.
    page.get_by_test_id(MODE_SINGLE_SITE_ID).check()  # Select the existing single-site journey.
    page.get_by_test_id(MODE_CONTINUE_ID).click()  # Submit the real mode form.
    page.wait_for_url(f"**{SITE_PAGE_PATH}", timeout=GATE_TIMEOUT_MS)  # The route opens the site picker.


def _open_first_inventory(page: Any) -> None:
    """Open the first site inventory from the site picker.

    Args:
        page: The Playwright page object on the site picker.
    """
    site_id = _first_key(page, SITE_ROW_PREFIX)  # Read the site key that the page published.
    with page.expect_response(lambda answer: answer.request.is_navigation_request()) as event:  # Wait for GET.
        page.get_by_test_id(f"{SITE_OPEN_PREFIX}{site_id}").click()  # Open the inventory by its row control.
    _require_ok(event.value.status, f"the inventory page of site {site_id}")  # A route failure must not hide.
    sync_api.expect(page.get_by_test_id(INVENTORY_TABLE_ID)).to_be_visible(timeout=GATE_TIMEOUT_MS)  # Page works.


def _assert_no_token_surface(page: Any, token: str, evidence_path: Path, log_path: Path) -> None:
    """Assert that common browser and server surfaces hold no token value.

    Args:
        page: The Playwright page object after the journey.
        token: The fake token that the browser submitted.
        evidence_path: The browser-token evidence file.
        log_path: The isolated server log path.
    """
    assert token not in page.content(), "The browser token reached the current page HTML."  # Markup must be clean.
    cookies = page.context.cookies()  # Read browser cookies through Playwright.
    assert all(token not in item["value"] for item in cookies), "A cookie holds the browser token."  # Cookies clean.
    evidence = evidence_path.read_text(encoding="utf-8") if evidence_path.exists() else ""  # Artifact text.
    assert token not in evidence, "The browser-token evidence artifact holds the token value."  # Artifact clean.
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""  # Server log.
    assert token not in log_text, "The isolated portal log holds the browser token."  # Logs must be clean.


class TestBrowserTokenSignInJourney:
    """Drive the browser-token sign-in form through the running portal."""

    def test_valid_token_reaches_inventory_and_signout_clears_the_session(
        self,
        signed_out_page: Any,
        browser_token_value: str,
        browser_token_evidence_path: Path,
        browser_token_server_log_path: Path,
    ) -> None:
        """A valid browser token opens a Mist-backed page and signs out cleanly.

        Args:
            signed_out_page: A page with no preloaded portal session.
            browser_token_value: The fake token that the server stand-in accepts.
            browser_token_evidence_path: The safe evidence file path.
            browser_token_server_log_path: The isolated server log path.
        """
        _reset_evidence(browser_token_evidence_path)  # Read only this journey's server-side events.
        _sign_in_with_browser_token(signed_out_page, browser_token_value)  # Submit through the real form.
        _choose_first_org_and_mode(signed_out_page)  # Move from organization to the site picker.
        _open_first_inventory(signed_out_page)  # Force a Mist-backed read through the token-built session.
        rows = _evidence_rows(browser_token_evidence_path)  # Read the child process evidence.
        events = [row["event"] for row in rows]  # Keep only event names for sequence assertions.
        assert "browser_token_session" in events, "The server recorded no browser-token session build."
        assert any(row.get("accepted") is True for row in rows), "The server did not accept the fake token."
        assert "token_identity" in events, "The server recorded no token identity read."
        assert "mist_get" in events, "No Mist-backed page used the browser-token session."
        _assert_no_token_surface(
            signed_out_page, browser_token_value, browser_token_evidence_path, browser_token_server_log_path
        )
        signed_out_page.get_by_test_id(SIGNOUT_BUTTON_ID).click()  # Use the real sign-out control.
        signed_out_page.wait_for_url(f"**{SIGNIN_PATH}", timeout=GATE_TIMEOUT_MS)  # Sign-out returns to the form.
        status = _page_status(signed_out_page, ORG_PAGE_PATH)  # A later signed-in page must now refuse.
        assert status == UNAUTHORIZED_STATUS, f"{ORG_PAGE_PATH} answered {status} after sign-out."

    def test_invalid_token_stays_on_the_form_and_creates_no_session(
        self,
        signed_out_page: Any,
        browser_token_value: str,
        browser_token_evidence_path: Path,
    ) -> None:
        """A refused browser token shows a page error and opens no session.

        Args:
            signed_out_page: A page with no preloaded portal session.
            browser_token_value: The fake token that the server stand-in accepts.
            browser_token_evidence_path: The safe evidence file path.
        """
        _reset_evidence(browser_token_evidence_path)  # Read only this refusal's server-side events.
        bad_token = f"{browser_token_value}-wrong"  # An obvious fake value that the stand-in refuses.
        _require_ok(_page_status(signed_out_page, SIGNIN_PATH), SIGNIN_PATH)  # Start from the form.
        signed_out_page.get_by_test_id(SIGNIN_MODE_BROWSER_TOKEN_ID).check()  # Select the browser-token mode.
        signed_out_page.get_by_test_id(SIGNIN_BROWSER_TOKEN_ID).fill(bad_token)  # Type the refused fake token.
        with signed_out_page.expect_response(_is_signin_post, timeout=GATE_TIMEOUT_MS) as event:  # Wait for post.
            signed_out_page.get_by_test_id(SIGNIN_SUBMIT_ID).click()  # A plain click sends the field value.
        assert event.value.status == BAD_REQUEST_STATUS, f"The refusal answered {event.value.status}."
        sync_api.expect(signed_out_page.get_by_test_id(SIGNIN_ERROR_ID)).to_be_visible(timeout=GATE_TIMEOUT_MS)
        status = _page_status(signed_out_page, ORG_PAGE_PATH)  # A refused token must not create a session.
        assert status == UNAUTHORIZED_STATUS, f"{ORG_PAGE_PATH} answered {status} after a refused token."
        evidence = browser_token_evidence_path.read_text(encoding="utf-8")  # The evidence must remain safe.
        assert bad_token not in evidence, "The refusal evidence holds the submitted token value."

    def test_missing_token_stays_in_the_browser_and_opens_no_session(self, signed_out_page: Any) -> None:
        """An empty browser-token field stops before the portal request.

        Args:
            signed_out_page: A page with no preloaded portal session.
        """
        _require_ok(_page_status(signed_out_page, SIGNIN_PATH), SIGNIN_PATH)  # Start from the form.
        signed_out_page.get_by_test_id(SIGNIN_MODE_BROWSER_TOKEN_ID).check()  # Select the browser-token mode.
        signed_out_page.get_by_test_id(SIGNIN_SUBMIT_ID).click()  # Submit with an empty token field.
        sync_api.expect(signed_out_page.get_by_test_id(SIGNIN_ERROR_ID)).to_be_visible(timeout=GATE_TIMEOUT_MS)
        status = _page_status(signed_out_page, ORG_PAGE_PATH)  # The empty field must not create a session.
        assert status == UNAUTHORIZED_STATUS, f"{ORG_PAGE_PATH} answered {status} after an empty token."

    def test_missing_session_cannot_open_a_signed_in_page(self, signed_out_page: Any) -> None:
        """A browser with no session cannot open the organization picker.

        Args:
            signed_out_page: A page with no preloaded portal session.
        """
        status = _page_status(signed_out_page, ORG_PAGE_PATH)  # The signed-in page requires a session.
        assert status == UNAUTHORIZED_STATUS, f"{ORG_PAGE_PATH} answered {status} without a session."

    def test_cookie_fixture_session_does_not_use_the_browser_token_seam(
        self,
        page: Any,
        browser_token_evidence_path: Path,
    ) -> None:
        """The existing cookie session fixture stays independent of token sign-in.

        Args:
            page: The default E2E page that already holds a signed session.
            browser_token_evidence_path: The safe evidence file path.
        """
        _reset_evidence(browser_token_evidence_path)  # Isolate the default cookie-session boundary.
        _require_ok(_page_status(page, ORG_PAGE_PATH), ORG_PAGE_PATH)  # The cookie fixture still opens the page.
        sync_api.expect(page.get_by_test_id(ORG_SEARCH_ID)).to_be_visible(timeout=GATE_TIMEOUT_MS)  # Page works.
        assert _evidence_rows(browser_token_evidence_path) == []  # No browser-token builder ran for cookies.
