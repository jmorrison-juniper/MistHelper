"""The browser proof that a wrong address opens the error page, not raw JSON.

Why:
    Issue #3274. A browser that opened an unknown address of the portal showed
    the raw text ``{"error":{"code":"not_found",...}}``. The page held no portal
    layout and no link back to the site list. The contract test in
    ``tests/contract/upgrade_portal/test_unknown_url_page.py`` reads the markup.
    Only a browser sends the real navigation headers and follows the link.

The three journeys:
    1. A signed-in operator opens a wrong address. The link opens the site list.
    2. A browser with no session opens a wrong address. The header shows no
       sign-out control, and the link asks for a sign-in.
    3. A signed-in operator opens a bookmark of a path that accepts a form post
       only. The page names the refused method, and the session stays live.

Identifier contract:
    Every locator reads a ``data-testid`` attribute, as rule 4 of
    ``contracts/ui-testids.md`` states.
"""

from __future__ import annotations

import re  # Match the page that each link opens.
from pathlib import Path  # Type the pytest folder that receives each screenshot.
from typing import Any  # Playwright page and response objects are free-form.

import pytest  # The test framework.

# The Playwright package must exist before this module defines a browser test.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

UNKNOWN_PATH = "/unknown-upgrade-portal-route"  # The address of the issue. No route serves it.
POST_ONLY_PATH = "/auth/signout"  # A real path that accepts a form post only.
NOT_FOUND_STATUS = 404  # No route serves the address.
NOT_ALLOWED_STATUS = 405  # The path refuses the method of a page view.
GATE_TIMEOUT_MS = 60000  # A cold store can need more time during a full suite.

NO_PAGE_TITLE = "The portal found no such page"  # The heading of the page for a wrong address.
NO_PAGE_SENTENCE = "The portal holds no page at this address."  # The first sentence of the page.
NOT_FOUND_CODE = "not_found"  # The code that a support request quotes.
NOT_ALLOWED_CODE = "method_not_allowed"  # The code of a refused method.
SITE_LIST_PATH = "/select/site"  # The recovery link of `error.html`.

# The site picker sends a session with no organization to the organization
# picker first, so the link can end on either picker.
PICKER_URL = re.compile(r"/select/(site|org)")
SIGN_IN_URL = re.compile(r"/auth/signin")  # A browser page with no session opens the sign-in form (#3214).


def _open(page: Any, path: str, status: int) -> Any:
    """Open one address, and require the status of the answer.

    Args:
        page: A page of the stand-in portal.
        path: The address to open.
        status: The status that the answer must carry.

    Returns:
        The response of the page view.
    """
    answer = page.goto(path, wait_until="domcontentloaded", timeout=GATE_TIMEOUT_MS)  # A real page view.
    assert answer is not None and answer.status == status, f"{path} did not answer {status}."  # The status first.
    return answer  # The caller reads the headers.


def _read_no_page(page: Any) -> None:
    """Require the page for a wrong address, with its code, its sentence, and its link.

    Args:
        page: The page that shows the answer.
    """
    sync_api.expect(page.get_by_test_id("error-title")).to_have_text(NO_PAGE_TITLE)  # A page, not raw JSON.
    sync_api.expect(page.get_by_test_id("error-code")).to_have_text(NOT_FOUND_CODE)  # The stable code.
    sync_api.expect(page.get_by_test_id("error-status-code")).to_have_text(str(NOT_FOUND_STATUS))  # The status.
    message = page.get_by_test_id("error-message")  # The sentence with the signal word.
    spoken = message.aria_snapshot()  # The signal word and the sentence, as a screen reader reads them.
    assert "Warning:" in spoken and NO_PAGE_SENTENCE in spoken, f"The alert reads {spoken!r}."
    link = page.get_by_test_id("error-site-list-link")  # The way back that the issue asks for.
    sync_api.expect(link).to_have_attribute("href", SITE_LIST_PATH)  # The link names the site list.
    assert UNKNOWN_PATH not in page.content(), "The page repeats the address that the browser sent."


def test_a_wrong_address_opens_the_error_page_and_the_site_list(page: Any, tmp_path: Path) -> None:
    """Prove that a signed-in operator reads the page and returns to the site list.

    Args:
        page: A signed-in page of the stand-in portal.
        tmp_path: The pytest folder of this test.
    """
    _open(page, UNKNOWN_PATH, NOT_FOUND_STATUS)  # The operator opens a wrong address.
    _read_no_page(page)  # The page names the fault and the way back.
    sync_api.expect(page.get_by_test_id("signout-button")).to_be_visible()  # The live session can sign out.
    page.screenshot(path=str(tmp_path / "wrong-address.png"), full_page=True)  # The page for a wrong address.
    page.get_by_test_id("error-site-list-link").click()  # A plain press, the way an operator leaves the page.
    page.wait_for_url(PICKER_URL, timeout=GATE_TIMEOUT_MS)  # The picker opens.
    page.screenshot(path=str(tmp_path / "after-site-list-link.png"), full_page=True)  # The next page.
    assert page.get_by_test_id("error-page").count() == 0, "The link opened the error page again."


def test_a_wrong_address_with_no_session_hides_the_session_controls(page: Any, tmp_path: Path) -> None:
    """Prove that a browser with no session reads the page and then the sign-in form.

    Args:
        page: A signed-in page of the stand-in portal.
        tmp_path: The pytest folder of this test.
    """
    page.context.clear_cookies()  # A portal restart ends the session, as an old bookmark then finds.
    _open(page, UNKNOWN_PATH, NOT_FOUND_STATUS)  # The browser opens a wrong address.
    _read_no_page(page)  # The page names the fault and the way back.
    assert page.get_by_test_id("signout-button").count() == 0, "The header offers a sign-out with no session."
    page.screenshot(path=str(tmp_path / "wrong-address-no-session.png"), full_page=True)  # The page.
    page.get_by_test_id("error-site-list-link").click()  # The operator follows the way back.
    page.wait_for_url(SIGN_IN_URL, timeout=GATE_TIMEOUT_MS)  # No session, so the portal asks for a sign-in.
    page.screenshot(path=str(tmp_path / "site-list-link-asks-for-sign-in.png"), full_page=True)  # The form.
    assert page.get_by_test_id("error-page").count() == 0, "The link opened the error page again."


def test_a_bookmark_of_a_post_only_path_opens_the_error_page(page: Any, tmp_path: Path) -> None:
    """Prove that a page view of a post-only path reads the page and keeps the session.

    Args:
        page: A signed-in page of the stand-in portal.
        tmp_path: The pytest folder of this test.
    """
    answer = _open(page, POST_ONLY_PATH, NOT_ALLOWED_STATUS)  # A bookmark of the sign-out path.
    allowed = {name.strip().upper() for name in answer.headers.get("allow", "").split(",")}  # The header.
    assert "POST" in allowed, f"The Allow header names {sorted(allowed)}."  # HTTP requires the accepted methods.
    sync_api.expect(page.get_by_test_id("error-code")).to_have_text(NOT_ALLOWED_CODE)  # A page, not raw JSON.
    sync_api.expect(page.get_by_test_id("error-status-code")).to_have_text(str(NOT_ALLOWED_STATUS))  # The status.
    sync_api.expect(page.get_by_test_id("signout-button")).to_be_visible()  # A page view signs nobody out.
    page.screenshot(path=str(tmp_path / "post-only-bookmark.png"), full_page=True)  # The page for a refused method.
    sync_api.expect(page.get_by_test_id("error-site-list-link")).to_be_visible()  # The way back stays.
    assert page.get_by_test_id("error-back-link").count() == 0, "A page view has no form to open again."
