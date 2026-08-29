"""Browser proof that the capture page fills the capture identifier (issue #2093).

Why:
    `tests/unit/upgrade_portal/test_capture_identifier_field.py` reads the text
    of the script and the text of the page. Text cannot prove that a selector
    finds an element. Only a browser can prove that, because only a browser
    builds the tree that the selector searches.

    These tests run the real `portal.js` against the real `capture/capture.html`
    inside a real browser. The first test drives the poll paint. The second test
    clicks the start button and answers the request with a stand-in.

    Both tests fail against the code of issue #2093. The old paint searched the
    progress region for a field that sits outside the region, found nothing,
    and left the field empty.

No server and no network:
    The page comes from `flask.render_template`, and the browser reads it
    through `set_content`. No test here opens a port, and no test here reaches
    a cloud. A stand-in replaces `window.fetch` before the page script runs, so
    no request leaves the browser.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

# The Playwright package must exist before this module defines a browser test.
# A run without the package reports a skip and never an import error.
pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

from playwright.sync_api import Error as PlaywrightError  # WHY: The skip above runs first.

from src.upgrade_portal.app import factory  # WHY: The skip above runs first.

# WHY: This file sits at tests/e2e/upgrade_portal, so the root is three levels up.
REPO_ROOT = Path(__file__).resolve().parents[3]

# WHY: The real script that the real page loads. The browser reads this text.
SCRIPT_PATH = REPO_ROOT / "src" / "upgrade_portal" / "app" / "assets" / "static" / "js" / "portal.js"

# WHY: contracts/ui-testids.md fixes each name below. A locator reads no other attribute.
IDENTIFIER_TESTID = "capture-identifier"
PROGRESS_TESTID = "capture-progress"
START_TESTID = "capture-start-button"
REFRESH_TESTID = "capture-refresh-button"
SIZE_TESTID = "capture-size-bytes"

# WHY: The capture of the issue report, and the site that held it.
CAPTURE_ID = "cap-c44534904756404c817d7d8bdb939313-01"
SITE_ID = "cf36153a-97bb-4974-8f8f-e9cc25d64d83"

# WHY: The stored size that the issue report showed beside the empty field.
STORED_SIZE = 17770

# WHY: The six section keys of GET /api/captures/<id>/status. A paint that misses
# one section must not stop the paint of the identifier.
SECTION_KEYS = ("devices", "clients_wired", "clients_wireless", "clients_guest", "extras", "alarms")

# WHY: One stand-in for `window.fetch`. It answers the start call and the status
# call from a table, so no request leaves the browser. The script reads `ok`,
# `status`, and `text`, so the stand-in answers with those three names. The
# longest matching address wins, because `/api/captures/<id>` is the head of
# `/api/captures/<id>/status` and the two must never trade answers.
FETCH_STAND_IN = """
(answers) => {
    window.__portalRequests = [];
    var fragments = Object.keys(answers).sort(function (left, right) {
        return right.length - left.length;
    });
    window.fetch = function (url) {
        var address = String(url);
        window.__portalRequests.push(address);
        var body = null;
        fragments.forEach(function (fragment) {
            if (body === null && address.indexOf(fragment) !== -1) {
                body = answers[fragment];
            }
        });
        return Promise.resolve({
            ok: body !== null,
            status: body !== null ? 200 : 404,
            text: function () {
                return Promise.resolve(JSON.stringify(body === null ? {} : body));
            }
        });
    };
}
"""

# WHY: The start call writes this attribute onto the region, and the poll reads
# it back. A test that drives the poll alone must write it the same way.
ADOPT_CAPTURE = f"""
(captureId) => {{
    document.querySelector('[data-testid="{PROGRESS_TESTID}"]').setAttribute("data-capture-id", captureId);
}}
"""

# WHY: The field holds no word until a paint fills it. A wait on that text is
# steadier than a wait on a promise that the test cannot reach.
IDENTIFIER_FILLED = f"() => document.querySelector('[data-testid=\"{IDENTIFIER_TESTID}\"]').textContent.trim() !== ''"

# WHY: A stand-in answers at once, so five seconds is generous for every wait.
WAIT_MILLISECONDS = 5000


def status_body(state: str, percent: int) -> dict[str, Any]:
    """Build one status body of GET /api/captures/<capture_id>/status.

    Args:
        state: The capture state, such as `running` or `verified`.
        percent: The progress value from 0 to 100.

    Returns:
        The body, with every key that the paint reads.
    """
    return {  # The keys that `paintCaptureStatus` reads, in the order of the contract.
        "capture_id": CAPTURE_ID,  # The value that the field under test must show.
        "state": state,  # The word in the progress heading.
        "percent": percent,  # The bar width and the ARIA value.
        "sections": {key: "complete" for key in SECTION_KEYS},  # Every section, so no paint step returns early.
        "counts": {"devices_total": 8},  # One count, because the paint reads the map and never a fixed key.
        "partial_reasons": [],  # A whole capture, so the warning stays hidden.
        "verified": state == "verified",  # The badge word, and the trigger of the stored size read.
        "message": "The capture is complete.",  # The sentence under the bar.
    }


def render_capture_page(capture_identifier: str, status: dict[str, Any] | None = None) -> str:
    """Return the real capture page, rendered with Jinja.

    Why:
        A copy of the markup would pass after the real page lost the field. The
        render reads the same template that the portal serves, so a later edit
        of that template reaches these tests.

    Args:
        capture_identifier: The identifier the server renders into the page. An
            empty text stands for a page that no capture has reached yet.
        status: The status map the route supplies. `None` stands for a page that
            no capture has reached yet.

    Returns:
        The whole page as HTML.
    """
    import flask  # WHY: A local import keeps the module import cheap when the browser is absent.

    app = factory.create_app()  # The real application, with the real template folder.
    with app.test_request_context("/captures/new"):  # WHY: `url_for` needs a request context.
        return flask.render_template(  # The real template, with the variables a route supplies.
            "capture/capture.html",
            site_id=SITE_ID,  # The start button posts this site.
            site_name="The site of the test",  # The heading text.
            capture_id=capture_identifier,  # WHY: The page derives the field under test from this name.
            status=status or {},  # WHY: The page derives the state, the bar, and the counts from this map.
            stored_size_bytes=0,  # The size field starts at zero, as the issue report showed.
            tier=2,  # contracts/http-api.md fixes tier 2 as the default.
            role="pre",  # A pre-check capture, as the run page starts.
            run_id="",  # No run owns this capture, so the page shows the single-capture path.
            poll_interval_seconds=30,  # Decision D3 fixes the 30-second poll.
        )


@pytest.fixture(autouse=True)
def portal_test_id_attribute() -> None:
    """Take the place of the fixture of the same name in the conftest file.

    Why:
        The conftest fixture asks the Playwright plugin for its own driver, so
        that `get_by_test_id` reads `data-testid`. This module never calls
        `get_by_test_id`. Every locator below writes the attribute out in full,
        so the module needs no driver from the plugin and starts its own.

        A fixture in a module takes the place of a fixture of the same name in
        a conftest file. This one does nothing, which keeps the plugin out of
        the way of the browser that the next fixture starts.
    """


@pytest.fixture(scope="module")
def browser(playwright: Any) -> Iterator[Any]:
    """Start one browser for this module, and stop it at the end.

    Why:
        A browser start costs a second or more. One browser serves every test
        of this module, and each test opens its own page.

        The driver arrives from the Playwright plugin rather than from a private
        ``sync_playwright()`` call. Another test in the same session starts an
        asyncio loop, and the sync API refuses to start a second driver inside
        that loop. A private driver therefore passed when this module ran alone
        and raised at setup in a full run, which turned the browser gate red.

    Args:
        playwright: The driver that the Playwright plugin owns for the session.

    Yields:
        The browser.
    """
    try:
        started = playwright.chromium.launch()  # WHY: One engine is enough to prove a selector.
    except PlaywrightError as error:  # WHY: A workstation with no browser binary reports a skip.
        pytest.skip(f"No browser binary is installed. {error}")
    try:
        yield started  # The tests run here.
    finally:
        started.close()  # WHY: A leaked browser would hold a process after the run.


def open_capture_page(
    browser: Any,
    capture_identifier: str,
    answers: dict[str, Any],
    status: dict[str, Any] | None = None,
) -> Any:
    """Open one capture page with the real script and a stand-in for the network.

    Why:
        Every test needs the same four steps. One helper keeps the steps in one
        place, so the tests can never drift apart.

    Args:
        browser: The browser of the module fixture.
        capture_identifier: The identifier the server renders into the page.
        answers: The body to answer for each address fragment.
        status: The status map the route supplies at load.

    Returns:
        The page, with the script loaded and armed.
    """
    page = browser.new_page()  # WHY: A fresh page carries no state from another test.
    page.set_content(render_capture_page(capture_identifier, status))  # WHY: The real page, with no server.
    page.evaluate(FETCH_STAND_IN, answers)  # WHY: The stand-in must stand before the script arms a control.
    page.add_script_tag(content=SCRIPT_PATH.read_text(encoding="utf-8"))  # WHY: The real script, after the tree.
    return page


def test_the_poll_fills_the_identifier(browser: Any) -> None:
    """A poll of a running capture writes the identifier into the field.

    Why:
        The start call writes the identifier onto the region, and every poll
        after it paints the page. The old paint searched that region for the
        field, and the field sits outside the region, so the field stayed
        empty for the whole life of the capture.

        This test clicks the manual refresh control of FR-040. That control and
        the 30-second timer both reach `refreshCaptureStatus`, so one click
        proves the path that the timer takes.

    Args:
        browser: The browser of the module fixture.
    """
    answers = {f"/api/captures/{CAPTURE_ID}/status": status_body("running", 40)}  # The poll answer.
    page = open_capture_page(browser, "", answers)  # A page that no capture has reached yet.
    try:
        assert page.locator(f'[data-testid="{IDENTIFIER_TESTID}"]').inner_text().strip() == ""  # Empty at load.
        page.evaluate(ADOPT_CAPTURE, CAPTURE_ID)  # WHY: The start call already wrote this attribute.
        page.locator(f'[data-testid="{REFRESH_TESTID}"]').click()  # The real listener of the real control.
        page.wait_for_function(IDENTIFIER_FILLED, timeout=WAIT_MILLISECONDS)  # WHY: The paint waits for a promise.
        assert page.locator(f'[data-testid="{IDENTIFIER_TESTID}"]').inner_text().strip() == CAPTURE_ID
    finally:
        page.close()  # WHY: A leaked page would hold memory for the rest of the module.


def test_the_start_call_fills_the_identifier(browser: Any) -> None:
    """A click on the start button writes the identifier as soon as the call answers.

    Why:
        FR-032 asks the page to name the capture at once, so the operator can
        record that name before the capture ends. This test drives the real
        listener that `initCapturePage` attached, and never a paint helper.

    Args:
        browser: The browser of the module fixture.
    """
    answers = {  # One body for each address that the start path calls.
        f"/api/captures/{CAPTURE_ID}/status": status_body("running", 20),  # The first poll after the start.
        f"/api/sites/{SITE_ID}/captures": {"capture_id": CAPTURE_ID, "state": "running"},  # The 202 answer.
        f"/api/captures/{CAPTURE_ID}": {"stored_size_bytes": STORED_SIZE},  # The stored size read.
    }
    page = open_capture_page(browser, "", answers)  # A page that no capture has reached yet.
    try:
        page.locator(f'[data-testid="{START_TESTID}"]').click()  # The real listener of the real button.
        page.wait_for_function(  # WHY: The paint waits for a promise, so the test waits for the text.
            IDENTIFIER_FILLED,
            timeout=WAIT_MILLISECONDS,
        )
        assert page.locator(f'[data-testid="{IDENTIFIER_TESTID}"]').inner_text().strip() == CAPTURE_ID
    finally:
        page.close()  # WHY: A leaked page would hold memory for the rest of the module.


def test_the_stored_size_still_fills(browser: Any) -> None:
    """The stored size keeps its own paint.

    Why:
        The stored size never failed, because it already read the document. The
        repair must not move that read or change its address. This test also
        proves that the stand-in for the network really drives the whole chain,
        so a pass of the two tests above carries meaning.

    Args:
        browser: The browser of the module fixture.
    """
    answers = {  # The two addresses that the verified path calls, in the order of the match.
        f"/api/captures/{CAPTURE_ID}/status": status_body("verified", 100),  # The poll answer.
        f"/api/captures/{CAPTURE_ID}": {"stored_size_bytes": STORED_SIZE},  # The stored size read.
    }
    page = open_capture_page(
        browser, CAPTURE_ID, answers, status_body("verified", 100)
    )  # A verified page has stored tables.
    try:
        page.locator(f'[data-testid="{REFRESH_TESTID}"]').click()  # The real listener of the real control.
        page.wait_for_function(  # WHY: The refresh reads the status, and the verified state reads the size.
            f"() => document.querySelector('[data-testid=\"{SIZE_TESTID}\"]').textContent.trim()"
            f' === "{STORED_SIZE}"',
            timeout=WAIT_MILLISECONDS,
        )
        assert page.locator(f'[data-testid="{IDENTIFIER_TESTID}"]').inner_text().strip() == CAPTURE_ID
    finally:
        page.close()  # WHY: A leaked page would hold memory for the rest of the module.
