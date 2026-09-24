"""The browser proof that a refused form post opens the error page.

Why:
    Issue #3275. Every form post carries a security token. When the token check
    failed, the portal answered the JSON envelope, and the browser showed the raw
    text ``{"error":{"code":"csrf_missing",...}}``. The operator lost the form
    and found no way back. The contract test in
    ``tests/contract/upgrade_portal/test_csrf_error_page.py`` reads the markup.
    Only a browser sends the real ``Referer`` header, and only a browser follows
    the link back.

The two journeys:
    1. The session ends while the form is open, as after a portal restart. The
       link back then opens the sign-in form.
    2. The session stays valid, but the token is stale, as after a second
       sign-in in another tab. The link back opens the form, and the form then
       works.

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

FORM_PATH = "/select/mode"  # A plain form post that `portal.js` never intercepts.
CSRF_STATUS = 400  # The contract binds this status to a missing token.
CSRF_MISSING_CODE = "csrf_missing"  # The code that a support request quotes.
PAGE_TITLE = "The portal refused the form"  # The heading of the refusal page.
RECOVERY_SENTENCE = "Open the form again, then send it again."  # The sentence that names the recovery.
STALE_TOKEN = "stale-token-value-for-issue-3275"  # A token that no session issued.
GATE_TIMEOUT_MS = 60000  # A cold store can need more time during a full suite.

SIGN_IN_URL = re.compile(r"/auth/signin")  # A browser page with no session opens the sign-in form (#3214).
SITE_LIST_URL = re.compile(r"/select/site")  # The single-site mode continues to the site list.


def _open_mode_form(page: Any) -> None:
    """Open the mode form, and require the control that sends it.

    Args:
        page: A signed-in page of the stand-in portal.
    """
    answer = page.goto(FORM_PATH, wait_until="domcontentloaded", timeout=GATE_TIMEOUT_MS)  # The real form page.
    assert answer is not None and answer.ok, f"{FORM_PATH} did not open."  # A missing form ends the journey.
    sync_api.expect(page.get_by_test_id("mode-continue")).to_be_visible()  # The form is ready for a choice.


def _is_form_post(response: Any) -> bool:
    """Report whether one response answers the post of the mode form.

    Args:
        response: One response that the page received.

    Returns:
        True for the post itself, and False for a later redirect or an asset.
    """
    return bool(response.request.method == "POST" and response.url.endswith(FORM_PATH))  # The post only.


def _send_single_site(page: Any) -> Any:
    """Choose the single-site mode, send the form, and return the answer of the post.

    Args:
        page: A page that shows the mode form.

    Returns:
        The response of the form post.
    """
    page.get_by_test_id("mode-single-site").check()  # The operator chooses one site.
    with page.expect_response(_is_form_post, timeout=GATE_TIMEOUT_MS) as answer:  # Catch the post itself.
        page.get_by_test_id("mode-continue").click()  # A plain press sends the form.
    return answer.value  # The answer of the post itself.


def _read_refusal_page(page: Any, response: Any) -> None:
    """Require the refusal page with its code, its sentence, and both links.

    Args:
        page: The page that shows the answer of the post.
        response: The response of the refused post.
    """
    assert response.status == CSRF_STATUS, f"The post answered {response.status}."  # The contract status.
    sync_api.expect(page.get_by_test_id("error-title")).to_have_text(PAGE_TITLE)  # A page, not raw JSON.
    sync_api.expect(page.get_by_test_id("error-code")).to_have_text(CSRF_MISSING_CODE)  # The stable code.
    message = page.get_by_test_id("error-message")  # The sentence with the signal word.
    sync_api.expect(message).to_contain_text(RECOVERY_SENTENCE)  # The sentence names the recovery.
    sync_api.expect(page.get_by_test_id("error-back-link")).to_have_attribute("href", FORM_PATH)  # The form page.
    sync_api.expect(page.get_by_test_id("error-site-list-link")).to_be_visible()  # The second way out stays.
    spoken = message.aria_snapshot()  # The signal word and the sentence, as a screen reader reads them.
    assert "Warning:" in spoken and RECOVERY_SENTENCE in spoken, f"The alert reads {spoken!r}."
    assert STALE_TOKEN not in page.content(), "The page shows the refused token."  # The page hides the token.


def test_a_form_post_after_the_session_ends_opens_the_error_page(page: Any, tmp_path: Path) -> None:
    """Prove that an ended session gives a page with a link back to the sign-in form.

    Args:
        page: A signed-in page of the stand-in portal.
        tmp_path: The pytest folder of this test.
    """
    _open_mode_form(page)  # The operator opens the form while the session is live.
    page.context.clear_cookies()  # The portal restart ends the session, and the browser keeps the old form.
    response = _send_single_site(page)  # The operator sends the old form.
    _read_refusal_page(page, response)  # The page names the fault and both ways out.
    assert page.get_by_test_id("signout-button").count() == 0, "The header offers a sign-out with no session."
    page.screenshot(path=str(tmp_path / "refused-after-session-end.png"), full_page=True)  # The refusal page.
    page.get_by_test_id("error-back-link").click()  # The operator opens the form again.
    page.wait_for_url(SIGN_IN_URL, timeout=GATE_TIMEOUT_MS)  # No session, so the portal asks for a sign-in.
    page.screenshot(path=str(tmp_path / "back-link-opens-sign-in.png"), full_page=True)  # The next page.
    assert page.get_by_test_id("error-page").count() == 0, "The link back opened the error page again."


def test_a_stale_token_in_a_live_session_recovers_through_the_link_back(page: Any, tmp_path: Path) -> None:
    """Prove that the link back opens a fresh form, and that the fresh form works.

    Args:
        page: A signed-in page of the stand-in portal.
        tmp_path: The pytest folder of this test.
    """
    _open_mode_form(page)  # The operator opens the form.
    token_field = page.get_by_test_id("mode-picker").locator("input[name=csrf_token]")  # The token of this form.
    token_field.evaluate("(field, value) => { field.value = value; }", STALE_TOKEN)  # A second sign-in made it stale.
    response = _send_single_site(page)  # The operator sends the form with the stale token.
    _read_refusal_page(page, response)  # The page names the fault and both ways out.
    sync_api.expect(page.get_by_test_id("signout-button")).to_be_visible()  # The live session can still sign out.
    page.screenshot(path=str(tmp_path / "refused-stale-token.png"), full_page=True)  # The refusal page.
    page.get_by_test_id("error-back-link").click()  # The operator opens the form again.
    page.wait_for_url(re.compile(re.escape(FORM_PATH)), timeout=GATE_TIMEOUT_MS)  # The session is still live.
    sync_api.expect(page.get_by_test_id("mode-picker")).to_be_visible()  # The fresh form carries a fresh token.
    page.get_by_test_id("mode-single-site").check()  # The operator chooses one site again.
    page.get_by_test_id("mode-continue").click()  # The operator sends the fresh form.
    page.wait_for_url(SITE_LIST_URL, timeout=GATE_TIMEOUT_MS)  # The portal accepted the fresh form.
    page.screenshot(path=str(tmp_path / "fresh-form-accepted.png"), full_page=True)  # The next page.
    assert page.get_by_test_id("error-page").count() == 0, "The fresh form reached the error page."
