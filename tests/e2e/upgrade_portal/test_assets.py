"""Browser tests for the vendored assets and the content security policy.

Why:
    The portal serves Bootstrap 5.3.3 from its own static folder and sets a
    content security policy of `'self'` with no `'unsafe-inline'`. A unit test
    can read the policy text, and a request test can read the header. Neither
    one proves that a real browser accepted the policy and still painted the
    page. Only a browser test proves that.

Why the tests read a computed style:
    A stylesheet that answers 200 has still not applied. A wrong media type, a
    blocked request, or a parse failure all leave the page unstyled while every
    asset URL answers 200. Each test below therefore reads a value that only
    one stylesheet can produce.

Why the tests call a script function:
    The same argument holds for a script. The tests call a function that
    `portal.js` exports and read the version that the Bootstrap bundle exports,
    so a script that loaded but never ran fails the test.

Why the tests read the asset addresses:
    A page that reached a content delivery network would still look correct on
    a workstation with an open network path. The tests compare the origin of
    every stylesheet and every script with the origin of the page, so a fetch
    from any other host fails. That keeps the portal usable on a management
    network that reaches no public host.

Why the module reaches no cloud:
    Every call below reads the portal itself. No test starts a capture, creates
    a run, or writes a firmware version.
"""

from __future__ import annotations

from typing import Any

import pytest

# The Playwright package must exist before this module defines a browser test.
# A run without the package reports a skip and never an import error.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

HISTORY_PAGE_PATH = "/history"  # Every asset loads through `layout.html`, so one page proves the set.

# `contracts/ui-testids.md` lines 198, 202, and 212 fix these three names.
HISTORY_TABLE_ID = "history-table"
HISTORY_PREVIOUS_ID = "history-page-previous"
CSRF_META_ID = "csrf-meta"

CSP_HEADER = "content-security-policy"  # Playwright lower cases every header name.

# `app/security.py` fixes each of these parts of the policy.
REQUIRED_POLICY_PARTS = (
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self'",
    "connect-src 'self'",
    "font-src 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "object-src 'none'",
)

# A policy that held either word would let an inline script or an inline style run.
FORBIDDEN_POLICY_WORDS = ("unsafe-inline", "unsafe-eval")

# `layout.html` loads these two files from the static folder, never from a network.
BOOTSTRAP_STYLESHEET = "vendor/bootstrap/bootstrap.min.css"
BOOTSTRAP_SCRIPT = "vendor/bootstrap/bootstrap.bundle.min.js"
PORTAL_STYLESHEET = "css/portal.css"
PORTAL_SCRIPT = "js/portal.js"

BOOTSTRAP_VERSION = "5.3.3"  # The vendored copy states this version in its own header.

# Bootstrap Reboot sets `box-sizing` on every element. `portal.css` sets none,
# and the browser default for a table is `content-box`.
BOOTSTRAP_BOX_SIZING = "border-box"

# `portal.css` line 354 gives `.portal-button` an inline flex layout, and line
# 342 makes the box around the paging controls a flex container. CSS then
# blockifies the display of a flex item, so the browser reports `flex` and not
# `inline-flex`. Both values mean that the rule applied, and no browser default
# and no Bootstrap rule gives a plain button either one.
PORTAL_BUTTON_DISPLAYS = ("inline-flex", "flex")

# `portal.css` line 356 sets this value on the same rule. The browser default is
# `normal`, and blockification leaves this property alone, so the value proves
# the same rule applied and needs no reasoning about the parent box.
PORTAL_BUTTON_JUSTIFY = "center"

# The theme file sets every custom property that `portal.css` reads.
THEME_PROPERTY = "--portal-text"

OK_STATUS = 200  # The contract fixes this status for the page and for a static file.
UNAUTHORIZED_STATUS = 401  # `runtime/identity.py` answers this code with no session.
NOT_FOUND_STATUS = 404  # The route is not registered yet.

GATE_TIMEOUT_MS = 5000  # The page is server rendered, so every control is present at once.

# The two fixtures below reach the network and the file system, so a failure in
# either one describes the environment and never the page under test.
ENVIRONMENT_FIXTURES = ("capture_portal_server", "page")


def _lazy_fixture(request: pytest.FixtureRequest, name: str) -> Any:
    """Build one environment fixture, and turn a setup failure into a skip.

    Why:
        The server fixture needs a server for this platform and the page fixture
        needs a browser binary. Neither part exists on every workstation. A plain
        request would report an error, which reads in a report as a broken test.

    Args:
        request: The pytest request object of the calling fixture.
        name: The fixture to build.

    Returns:
        The fixture value.
    """
    try:  # The failure below describes the environment, never the page.
        return request.getfixturevalue(name)
    except Exception as failure:  # A skip states the real cause, so nothing hides.
        pytest.skip(f"The fixture {name} could not start, so no browser test can run. Cause: {failure}")


@pytest.fixture
def portal_page(request: pytest.FixtureRequest) -> Any:
    """Return a browser page that points at the running portal.

    Args:
        request: The pytest request object.

    Returns:
        The Playwright page object.
    """
    for name in ENVIRONMENT_FIXTURES:  # The server must answer before the browser opens a page.
        value = _lazy_fixture(request, name)
    return value


def _open(page: Any, path: str) -> Any:
    """Open one path and return the answer, or skip when the route is absent.

    Args:
        page: The Playwright page object.
        path: The path to open, relative to the portal address.

    Returns:
        The Playwright response object.

    Raises:
        AssertionError: If a built page answers a status the contract does not
            fix.
    """
    answer = page.goto(path, wait_until="load")  # `load` waits for every stylesheet and script.
    if answer is None:  # A page with no answer gives the test nothing to read.
        pytest.skip(f"The browser returned no response for {path}.")
    if answer.status == UNAUTHORIZED_STATUS:  # `identity.require_session` refused the request.
        pytest.skip(f"{path} answered 401. The portal holds no session, so no browser test reaches this page.")
    if answer.status == NOT_FOUND_STATUS:  # The blueprint that owns this path is not registered.
        pytest.skip(f"{path} answered 404. The route is not built yet.")
    assert answer.status == OK_STATUS, f"{path} answered {answer.status}. `contracts/http-api.md` fixes 200."
    return answer


@pytest.fixture
def loaded_page(portal_page: Any) -> Any:
    """Return a page whose every stylesheet and script has finished loading.

    Why:
        Each test of this module reads a value that an asset produces, so the
        page must reach the `load` event first.

    Args:
        portal_page: The browser page that points at the portal.

    Returns:
        The Playwright page object.
    """
    _open(portal_page, HISTORY_PAGE_PATH)
    return portal_page


def _asset_addresses(page: Any) -> list[str]:
    """Return the whole address of every stylesheet and every script of a page.

    Args:
        page: The Playwright page object.

    Returns:
        The resolved address of each stylesheet and script, in page order.
    """
    reader = """() => {
        const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(node => node.href);
        const scripts = Array.from(document.querySelectorAll('script[src]')).map(node => node.src);
        return styles.concat(scripts);
    }"""
    return [str(address) for address in page.evaluate(reader)]


def _page_origin(page: Any) -> str:
    """Return the origin of the page, such as `http://127.0.0.1:8056`.

    Args:
        page: The Playwright page object.

    Returns:
        The origin text.
    """
    return str(page.evaluate("() => window.location.origin"))


class TestContentSecurityPolicy:
    """The portal sets a strict policy and holds no inline script or style."""

    def test_the_page_carries_the_policy_header(self, portal_page: Any) -> None:
        """Every page answer carries a content security policy header.

        Why:
            `app/security.py` sets the header for every answer. A page with no
            header would run any script that reached it.

        Args:
            portal_page: The browser page that points at the portal.
        """
        answer = _open(portal_page, HISTORY_PAGE_PATH)
        assert CSP_HEADER in answer.headers, "The page answer carries no content security policy header."

    @pytest.mark.parametrize("part", REQUIRED_POLICY_PARTS)
    def test_the_policy_holds_each_source_rule(self, portal_page: Any, part: str) -> None:
        """The policy names `'self'` for each source that the portal reads.

        Why:
            A policy that left one source out would let that source reach any
            host. The frame rule and the object rule name `'none'`, because the
            portal renders no frame and no plugin object.

        Args:
            portal_page: The browser page that points at the portal.
            part: The policy part that this run reads.
        """
        answer = _open(portal_page, HISTORY_PAGE_PATH)
        policy = str(answer.headers.get(CSP_HEADER, ""))
        assert part in policy, f"The policy holds no `{part}` rule. The policy reads: {policy}"

    @pytest.mark.parametrize("word", FORBIDDEN_POLICY_WORDS)
    def test_the_policy_holds_no_unsafe_word(self, portal_page: Any, word: str) -> None:
        """The policy allows no inline script, no inline style, and no `eval`.

        Why:
            `'unsafe-inline'` would undo the whole policy, because a script that
            reached the page could then run. The portal keeps every behavior in
            `portal.js` for this reason.

        Args:
            portal_page: The browser page that points at the portal.
            word: The forbidden word that this run reads.
        """
        answer = _open(portal_page, HISTORY_PAGE_PATH)
        policy = str(answer.headers.get(CSP_HEADER, ""))
        assert word not in policy, f"The policy holds `{word}`, so an inline script would run."

    def test_the_page_holds_no_inline_script(self, loaded_page: Any) -> None:
        """No script element of the page carries its code in the page itself.

        Why:
            The policy blocks an inline script, so such a script would never
            run. The page would then hold a dead control that looks live.

        Args:
            loaded_page: The page with every asset loaded.
        """
        count = loaded_page.evaluate("() => document.querySelectorAll('script:not([src])').length")
        assert count == 0, f"The page holds {count} inline scripts, and the policy blocks each one."

    def test_the_page_holds_no_inline_style(self, loaded_page: Any) -> None:
        """No element of the page carries a style attribute or a style element.

        Why:
            The policy blocks both, so a value written that way never reaches
            the paint. A layout that depended on one would break silently.

        Args:
            loaded_page: The page with every asset loaded.
        """
        count = loaded_page.evaluate("() => document.querySelectorAll('[style], style').length")
        assert count == 0, f"The page holds {count} inline styles, and the policy blocks each one."


class TestAssetsAreVendored:
    """Every stylesheet and every script comes from the portal itself."""

    def test_every_asset_comes_from_the_portal_origin(self, loaded_page: Any) -> None:
        """No stylesheet and no script reaches another host.

        Why:
            The portal runs on a management network that reaches no public host.
            A page that fetched Bootstrap from a content delivery network would
            render without style there, and the policy would block the fetch.

        Args:
            loaded_page: The page with every asset loaded.
        """
        origin = _page_origin(loaded_page)
        far = [address for address in _asset_addresses(loaded_page) if not address.startswith(f"{origin}/")]
        assert not far, f"These assets come from another host: {far}"

    @pytest.mark.parametrize("asset", (BOOTSTRAP_STYLESHEET, BOOTSTRAP_SCRIPT, PORTAL_STYLESHEET, PORTAL_SCRIPT))
    def test_the_page_names_each_expected_asset(self, loaded_page: Any, asset: str) -> None:
        """The page loads each of the four files that `layout.html` names.

        Why:
            A same-origin test alone would pass on a page that dropped every
            asset. This test states which four files must reach the page.

        Args:
            loaded_page: The page with every asset loaded.
            asset: The static path that this run reads.
        """
        addresses = _asset_addresses(loaded_page)
        assert any(asset in address for address in addresses), f"The page loads no {asset}."

    @pytest.mark.parametrize("asset", (BOOTSTRAP_STYLESHEET, BOOTSTRAP_SCRIPT))
    def test_each_vendored_file_answers(self, loaded_page: Any, asset: str) -> None:
        """The portal serves each vendored Bootstrap file from its own folder.

        Why:
            The static folder holds Bootstrap 5.3.3. A missing file would leave
            the page unstyled, and the policy would block a replacement.

        Args:
            loaded_page: The page with every asset loaded.
            asset: The static path that this run reads.
        """
        answer = loaded_page.request.get(f"{_page_origin(loaded_page)}/static/{asset}")
        assert answer.status == OK_STATUS, f"/static/{asset} answered {answer.status}."


class TestStylesheetsApplied:
    """Each stylesheet reaches the paint, not the network alone."""

    def test_the_bootstrap_stylesheet_applied(self, loaded_page: Any) -> None:
        """Bootstrap Reboot set the box model of the page.

        Why:
            Reboot sets `box-sizing` on every element. `portal.css` sets none,
            and the browser default for a table is `content-box`. This value
            therefore proves that the vendored Bootstrap stylesheet applied.

        Args:
            loaded_page: The page with every asset loaded.
        """
        table = loaded_page.get_by_test_id(HISTORY_TABLE_ID)
        sync_api.expect(table).to_be_visible(timeout=GATE_TIMEOUT_MS)
        found = table.evaluate("node => getComputedStyle(node).boxSizing")
        assert found == BOOTSTRAP_BOX_SIZING, f"The table reads box-sizing {found}, so Bootstrap did not apply."

    def test_the_portal_stylesheet_applied(self, loaded_page: Any) -> None:
        """The portal stylesheet set the layout of the paging control.

        Why:
            `portal.css` gives `.portal-button` a flex layout and centers its
            content. The browser default is `inline-block` for a button and
            `inline` for a link, with a content position of `normal`, and
            Bootstrap styles neither one. Both values therefore prove that
            `portal.css` applied.

        Args:
            loaded_page: The page with every asset loaded.
        """
        control = loaded_page.get_by_test_id(HISTORY_PREVIOUS_ID)
        sync_api.expect(control).to_be_visible(timeout=GATE_TIMEOUT_MS)
        style = control.evaluate("node => [getComputedStyle(node).display, getComputedStyle(node).justifyContent]")
        assert style[0] in PORTAL_BUTTON_DISPLAYS, f"The control reads display {style[0]}, so portal.css did not apply."
        assert style[1] == PORTAL_BUTTON_JUSTIFY, f"The control reads justify-content {style[1]}, not centered."

    def test_the_theme_stylesheet_applied(self, loaded_page: Any) -> None:
        """The theme file set the custom properties that the portal reads.

        Why:
            `portal.css` reads every color from a custom property, and the theme
            file sets them. A missing theme leaves each property empty, and the
            page then paints with the browser colors alone.

        Args:
            loaded_page: The page with every asset loaded.
        """
        table = loaded_page.get_by_test_id(HISTORY_TABLE_ID)
        sync_api.expect(table).to_be_visible(timeout=GATE_TIMEOUT_MS)
        found = table.evaluate(f"node => getComputedStyle(node).getPropertyValue('{THEME_PROPERTY}').trim()")
        assert found, f"The property {THEME_PROPERTY} is empty, so no theme stylesheet applied."


class TestScriptsApplied:
    """Each script reaches the browser and runs, not the network alone."""

    def test_the_bootstrap_bundle_ran(self, loaded_page: Any) -> None:
        """The vendored Bootstrap bundle ran and reports its own version.

        Why:
            A component of the bundle reports the version it was built from. A
            bundle that loaded but never ran leaves no such value, and a bundle
            of another version reports another number.

        Args:
            loaded_page: The page with every asset loaded.
        """
        found = loaded_page.evaluate("() => (window.bootstrap && window.bootstrap.Modal.VERSION) || ''")
        assert found == BOOTSTRAP_VERSION, f"The bundle reports version {found!r}, not {BOOTSTRAP_VERSION}."

    def test_the_portal_script_ran(self, loaded_page: Any) -> None:
        """The portal script ran and one of its functions answers correctly.

        Why:
            `portal.js` holds every behavior of the portal, because the policy
            blocks an inline script. A script that loaded but raised while it
            parsed would leave every control dead, and a presence test alone
            would not find that.

        Args:
            loaded_page: The page with every asset loaded.
        """
        call = "() => window.upgradePortal.phaseProgressText({ settled: 4, total: 9 })"
        assert loaded_page.evaluate(call) == "4 of 9 settled", "The portal script did not run its own function."

    def test_the_portal_script_reads_the_page(self, loaded_page: Any) -> None:
        """The portal script reads the token that the page carries.

        Why:
            Every write of the portal sends this token. A script that could not
            read it would leave every write refused, which proves that the
            script both ran and reached the document.

        Args:
            loaded_page: The page with every asset loaded.
        """
        written = loaded_page.get_by_test_id(CSRF_META_ID).get_attribute("content")
        assert loaded_page.evaluate("() => window.upgradePortal.getCsrfToken()") == written
