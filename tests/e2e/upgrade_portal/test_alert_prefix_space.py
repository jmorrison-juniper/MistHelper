"""The browser proof that each alert reads a space after its signal word.

Why:
    Section 12 of ``portal.css`` prints a signal word before each alert, so the
    level reads without color. ``portal.js`` writes the alert sentence as plain
    text with no leading space. Issue #3277 records the sign-in alert that then
    read "Warning:The portal could not sign you in". The unit test in
    ``tests/unit/upgrade_portal/test_flash_prefix_space.py`` reads the rule
    text. Only a browser builds the generated text, so only a browser proves
    what the operator reads.

What each test reads:
    Each test reads the ARIA snapshot of one alert. The snapshot holds the
    generated signal word and the sentence, in the order that a screen reader
    reads them. Each test also saves a screenshot of the alert into the pytest
    folder of the test, so an engineer can compare the painted alert with the
    snapshot.

Identifier contract:
    Every locator reads a ``data-testid`` attribute, as rule 4 of
    ``contracts/ui-testids.md`` states.
"""

from __future__ import annotations

import re  # Find a signal word that touches the next word.
from pathlib import Path  # Type the pytest folder that receives each screenshot.
from typing import Any  # Playwright page and response objects are free-form.

import pytest  # The test framework and its parameter helper.

# The Playwright package must exist before this module defines a browser test.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

SIGNIN_PATH = "/auth/signin"  # The sign-in form of the journey in issue #3277.
ORG_PAGE_PATH = "/select/org"  # A signed-in page that holds the shared flash region.

SIGNIN_MODE_BROWSER_TOKEN_ID = "signin-mode-browser-token"  # The radio for the browser-token mode.
SIGNIN_BROWSER_TOKEN_ID = "signin-browser-token"  # The token field that the browser submits.
SIGNIN_SUBMIT_ID = "signin-submit"  # The form submit control.
SIGNIN_ERROR_ID = "signin-error"  # The sign-in refusal region.
FLASH_REGION_ID = "flash-message"  # The shared flash region of each signed-in page.

OK_STATUS = 200  # The contract fixes this status for each page that opens.
BAD_REQUEST_STATUS = 400  # The contract fixes this status for a refused credential.
GATE_TIMEOUT_MS = 60000  # The sign-in dependency panel can need more time during a full suite.

# The signal word of each alert level. ASD-STE100 fixes "Warning" and "Caution".
SIGNAL_WORDS = {"info": "Note:", "success": "Done:", "warning": "Caution:", "danger": "Warning:"}

# The sentence that each flash test writes through the public script function.
SAMPLE_SENTENCE = "The stand-in wrote this sentence."

# The script calls the public function that every page script uses for a message.
SHOW_FLASH_SCRIPT = "([sentence, level]) => window.upgradePortal.showFlash(sentence, level)"

# A signal word that touches the next word, such as "Warning:The".
TOUCHING_WORD_PATTERN = re.compile(r"(Note|Done|Caution|Warning):\S")


def _open(page: Any, path: str) -> None:
    """Open one portal page, and fail when the portal answers another status.

    Args:
        page: The Playwright page object.
        path: The path to open, relative to the portal address.
    """
    answer = page.goto(path, wait_until="domcontentloaded", timeout=GATE_TIMEOUT_MS)  # Open the real path.
    assert answer is not None and answer.status == OK_STATUS, f"{path} did not answer {OK_STATUS}"


def _is_signin_post(answer: Any) -> bool:
    """Report whether one response belongs to the sign-in post.

    Args:
        answer: The Playwright response object.

    Returns:
        True when the answer is the sign-in post.
    """
    method = str(answer.request.method)  # Read the request method once for a stable comparison.
    return method == "POST" and str(answer.url).endswith(SIGNIN_PATH)  # The script posts only this path here.


def test_a_refused_browser_token_reads_a_space_after_the_signal_word(
    signed_out_page: Any, browser_token_value: str, tmp_path: Path
) -> None:
    """Prove that the sign-in refusal reads "Warning: " and then the sentence.

    Why:
        This test walks the journey of issue #3277. The browser-token mode
        posts through the page script, and ``showSigninError`` writes the
        refusal as plain text with no leading space.

    Args:
        signed_out_page: A page with no preloaded portal session.
        browser_token_value: The fake token that the server stand-in accepts.
        tmp_path: The pytest folder of this test.
    """
    _open(signed_out_page, SIGNIN_PATH)  # Start from the real form.
    signed_out_page.get_by_test_id(SIGNIN_MODE_BROWSER_TOKEN_ID).check()  # Select the browser-token mode.
    signed_out_page.get_by_test_id(SIGNIN_BROWSER_TOKEN_ID).fill(f"{browser_token_value}-wrong")  # A refused value.
    with signed_out_page.expect_response(_is_signin_post, timeout=GATE_TIMEOUT_MS) as event:  # Wait for the post.
        signed_out_page.get_by_test_id(SIGNIN_SUBMIT_ID).click()  # A plain click sends the field value.
    assert event.value.status == BAD_REQUEST_STATUS, f"The refusal answered {event.value.status}."
    alert = signed_out_page.get_by_test_id(SIGNIN_ERROR_ID)  # The region that the script fills.
    sync_api.expect(alert).to_be_visible(timeout=GATE_TIMEOUT_MS)  # The refusal must show before the read.
    alert.screenshot(path=str(tmp_path / "signin-refusal.png"))  # The evidence that an engineer compares.
    spoken = alert.aria_snapshot()  # The signal word and the sentence, as a screen reader reads them.
    assert "Warning: " in spoken and not TOUCHING_WORD_PATTERN.search(spoken), f"The alert reads {spoken!r}."


@pytest.mark.parametrize("level", sorted(SIGNAL_WORDS))
def test_each_script_flash_reads_a_space_after_its_signal_word(page: Any, level: str, tmp_path: Path) -> None:
    """Prove that each flash level reads its signal word, one space, and the sentence.

    Why:
        ``showFlash`` writes each message that a page script reports, such as a
        lock takeover or a stop outcome. It writes the sentence as plain text
        with no leading space, so the space must come from the stylesheet.

    Args:
        page: A signed-in page of the stand-in portal.
        level: The alert level under test.
        tmp_path: The pytest folder of this test.
    """
    _open(page, ORG_PAGE_PATH)  # A signed-in page that holds the shared flash region.
    page.evaluate(SHOW_FLASH_SCRIPT, [SAMPLE_SENTENCE, level])  # Write the message the way a page script does.
    region = page.get_by_test_id(FLASH_REGION_ID)  # The region that holds the new message.
    sync_api.expect(region).to_contain_text(SAMPLE_SENTENCE)  # The message must show before the read.
    region.screenshot(path=str(tmp_path / f"flash-{level}.png"))  # The evidence that an engineer compares.
    expected = f"{SIGNAL_WORDS[level]} {SAMPLE_SENTENCE}"  # The signal word, one space, and the sentence.
    spoken = region.aria_snapshot()  # The text that a screen reader reads for the region.
    assert expected in spoken, f"The {level} flash reads {spoken!r}, not {expected!r}."
