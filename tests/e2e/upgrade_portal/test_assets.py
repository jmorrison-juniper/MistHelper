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

# `app/security.py` fixes each of these parts of the policy. The image rule
# names the `data:` scheme, because the vendored Bootstrap stylesheet draws
# every control graphic as an inline SVG image.
REQUIRED_POLICY_PARTS = (
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    "img-src 'self' data:",
    "connect-src 'self'",
    "font-src 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "object-src 'none'",
)

# A policy that held either word would let an inline script or an inline style run.
FORBIDDEN_POLICY_WORDS = ("unsafe-inline", "unsafe-eval")

# The browser fires `securitypolicyviolation` on the document for each resource
# that the policy blocks, and it fires the event for a stylesheet resource as
# well as for an element. The listener below therefore catches a blocked `data:`
# image that Bootstrap draws through a `url()` rule, which no header test finds.
#
# Playwright injects an init script before any script of the page runs and
# outside the policy, so `script-src 'self'` neither blocks this listener nor
# hides a violation from it.
BLOCKED_RESOURCE_STORE = "portalBlockedResources"
BLOCKED_RESOURCE_LISTENER = f"""
    window.{BLOCKED_RESOURCE_STORE} = [];
    document.addEventListener('securitypolicyviolation', (event) => {{
        window.{BLOCKED_RESOURCE_STORE}.push(
            event.violatedDirective + ' blocked ' + String(event.blockedURI).slice(0, 60)
        );
    }});
"""

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

# Both shipped themes, so a rule that wins under one theme cannot hide under the
# other. The brand theme paints a dark page and is the default.
THEME_NAMES = ("magenta", "default")

# `contracts/ui-testids.md` lines 209 and 210 fix these two names. The history
# tab is the active tab of the history page and the site tab is not, so one page
# reads the resting header link and the active header link together.
NAV_SITES_ID = "nav-sites"
NAV_HISTORY_ID = "nav-history"

# Each pair names one element of the header beside the custom property that must
# paint it. `portal.css` section 5 styles a link with `.portal-shell a`, which
# names one class and one element name. A rule that names one bare class loses
# that comparison, so each rule below once painted the page link color and
# ignored its own token. Only a computed color finds that.
HEADER_INK_CASES = (
    (".portal-brand", "--portal-header-text"),
    (f'[data-testid="{NAV_SITES_ID}"]', "--portal-header-link"),
    (f'[data-testid="{NAV_HISTORY_ID}"]', "--portal-header-link-active"),
)

# A link that carries a button class. This selector names the class on purpose,
# because the class itself is the subject of the test.
LINK_BUTTON_SELECTOR = "a.portal-button-primary"
LINK_BUTTON_INK = "--portal-on-accent"
NO_UNDERLINE = "none"  # A button carries no underline, whichever element draws it.

# The probe sets `style.color` through the CSSOM. The policy blocks the `style`
# attribute of the markup, which is a different thing, so this assignment stands.
# The probe turns a token such as `#ffffff` into the `rgb(255, 255, 255)` form
# that a computed color always reads, so the two values compare directly.
PAINTED_AND_EXPECTED = """
    (node, token) => {
        const raw = getComputedStyle(document.documentElement).getPropertyValue(token).trim();
        const probe = document.createElement('span');
        probe.style.color = raw;
        document.body.appendChild(probe);
        const expected = getComputedStyle(probe).color;
        probe.remove();
        return { painted: getComputedStyle(node).color, expected: expected, raw: raw };
    }
"""

# The token that names the two scrollbar colors, thumb first and track second.
SCROLLBAR_TOKEN = "--portal-scrollbar"

# The value the browser computes when no rule names the colors. The browser then
# picks its own pair, which is light on every theme.
SCROLLBAR_AUTO = "auto"

# `portal.css` names the pair on the root element, because the browser reads the
# root element to paint the scrollbar of the window. The shell is the `body`
# element, which is a child of the root, so a rule on the shell arrives too late.
SCROLLBAR_ROOT_SELECTOR = "html"

# The box that a wide table scrolls inside. `scrollbar-color` inherits, so the one
# rule on the root element must reach this box as well. `review/history.html` line
# 108 puts this box on the history page.
TABLE_SCROLL_SELECTOR = ".portal-table-scroll"

# The same idea as the probe above, for a pair of colors instead of one. The probe
# turns a token such as `#8a8a8a #1f1f1f` into the `rgb(138, 138, 138) rgb(31, 31,
# 31)` form that a computed value always reads, so the two values compare
# directly. `scrollbar-color` inherits, so a probe that could not take the
# assignment would read the value of the page. The caller therefore refuses the
# `auto` value, which is what such a probe would read while no rule paints.
SCROLLBAR_PAINTED_AND_EXPECTED = """
    (node, token) => {
        const raw = getComputedStyle(document.documentElement).getPropertyValue(token).trim();
        const probe = document.createElement('span');
        probe.style.scrollbarColor = raw;
        document.body.appendChild(probe);
        const expected = getComputedStyle(probe).scrollbarColor;
        probe.remove();
        return { painted: getComputedStyle(node).scrollbarColor, expected: expected, raw: raw };
    }
"""

OK_STATUS = 200  # The contract fixes this status for the page and for a static file.
UNAUTHORIZED_STATUS = 401  # `runtime/identity.py` answers this code with no session.
NOT_FOUND_STATUS = 404  # The route is not registered yet.

GATE_TIMEOUT_MS = 5000  # The page is server rendered, so every control is present at once.

# The server fixture states its own fault and its own skip, so this module must
# not translate either one. The browser fixture is different: a workstation
# without a browser binary describes the workstation and never the page.
SERVER_FIXTURE = "capture_portal_server"
BROWSER_FIXTURE = "page"


def _browser_page(request: pytest.FixtureRequest) -> Any:
    """Build the browser page, and report a missing browser binary as a skip.

    Why:
        Playwright needs a browser binary that no source tree carries. A plain
        request would report an error, which reads in a report as a broken test.
        A missing binary is the one environment fault this module still hides,
        because it stops every browser test for a reason outside the portal.

    Args:
        request: The pytest request object of the calling fixture.

    Returns:
        The Playwright page object.
    """
    try:  # A missing browser binary describes the workstation, never the page.
        return request.getfixturevalue(BROWSER_FIXTURE)
    except Exception as failure:  # A skip states the real cause, so nothing hides.
        pytest.skip(f"Playwright could not open a browser, so no browser test can run. Cause: {failure}")


@pytest.fixture
def portal_page(request: pytest.FixtureRequest) -> Any:
    """Return a browser page that points at the running portal.

    Why:
        The server must answer before the browser opens a page. The server
        fixture reports its own fault and its own skip, so this fixture asks
        for it plainly and lets either answer through.

    Args:
        request: The pytest request object.

    Returns:
        The Playwright page object.
    """
    request.getfixturevalue(SERVER_FIXTURE)  # A fault here is a fault of the portal, so it must not become a skip.
    return _browser_page(request)


def _open(page: Any, path: str) -> Any:
    """Open one path and return the answer.

    Why:
        Every status below 200 used to report a skip. A whole run then read no
        asset and still reported success, which is the state this suite exists
        to catch. The fixture now starts its own portal, so a 401 means the
        sign-in seam is broken and a 404 means a blueprint is missing. Both are
        faults of the portal.

    Args:
        page: The Playwright page object.
        path: The path to open, relative to the portal address.

    Returns:
        The Playwright response object.

    Raises:
        AssertionError: If the browser returned no answer, or if the page
            answered a status the contract does not fix.
    """
    answer = page.goto(path, wait_until="load")  # `load` waits for every stylesheet and script.
    assert answer is not None, f"The browser returned no response for {path}, so no asset could be read."
    if answer.status == UNAUTHORIZED_STATUS:  # `identity.require_session` refused the request.
        message = f"{path} answered 401. The portal this run started holds no sign-in seam."
        raise AssertionError(message)
    if answer.status == NOT_FOUND_STATUS:  # The blueprint that owns this path is not registered.
        raise AssertionError(f"{path} answered 404. The blueprint that owns this path is not registered.")
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

    def test_the_browser_blocked_no_resource_of_the_page(self, portal_page: Any) -> None:
        """The browser loaded every resource of the page and blocked none.

        Why:
            Every other test of this class reads the policy text. A correct text
            still proves nothing about the paint, because a policy that omits
            one scheme blocks a resource while the header itself reads well.

            That is not a guess. The image rule once read `img-src 'self'`, and
            the vendored Bootstrap stylesheet draws the caret of a selection
            list, the dot of a radio control, the tick of a checkbox, and the
            knob of a switch as an inline SVG image. The browser blocked all 23
            of them, so every one of those controls painted as an empty box. The
            header test passed for the whole time that defect stood.

            This test reads the browser instead of the header. The listener
            below records the event that the browser fires for each blocked
            resource, so a policy that blocks anything at all fails here.

        Args:
            portal_page: The browser page that points at the portal.
        """
        portal_page.add_init_script(BLOCKED_RESOURCE_LISTENER)  # Runs before any stylesheet of the page loads.
        _open(portal_page, HISTORY_PAGE_PATH)
        blocked = portal_page.evaluate(f"() => window.{BLOCKED_RESOURCE_STORE} || []")
        assert not blocked, f"The policy blocked these resources of the page: {blocked}"


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


class TestThemeColorsReachThePaint:
    """Each theme token reaches the element it names, not the stylesheet alone.

    Why:
        A token that a rule sets is not a color that the browser paints. Section
        5 of `portal.css` styles a link with `.portal-shell a`, which names one
        class and one element name. A rule that names one bare class, such as
        `.portal-brand` or `.portal-button-primary`, loses that comparison. The
        brand text, every navigation link, and every link styled as a button
        therefore took the page link color and ignored their own tokens, which
        put pale pink text on the brand fill and left a button underlined.

        Every other test of this suite passed while the header looked wrong,
        because no test in this repository read a painted color. These tests read
        one, under both shipped themes.
    """

    @staticmethod
    def _ink(page: Any, selector: str, token: str) -> dict[str, str]:
        """Return the painted color of one element beside the color of one token.

        Args:
            page: The browser page, already opened on the history page.
            selector: The element to read.
            token: The custom property that must paint that element.

        Returns:
            The painted color, the color the token names, and the raw token text.
        """
        element = page.locator(selector).first
        sync_api.expect(element).to_be_visible(timeout=GATE_TIMEOUT_MS)
        answer: dict[str, str] = element.evaluate(PAINTED_AND_EXPECTED, token)
        assert answer["raw"], f"No theme sets {token}, so this comparison would pass on two empty values."
        return answer

    @pytest.mark.parametrize("theme", THEME_NAMES)
    @pytest.mark.parametrize(("selector", "token"), HEADER_INK_CASES)
    def test_a_header_link_paints_its_own_token(self, portal_page: Any, theme: str, selector: str, token: str) -> None:
        """Each link of the header paints the header token, never the page link.

        Why:
            The header may carry a brand fill, and the page link color is tuned
            for the page surface. A header link that falls back to the page link
            color loses contrast against that fill, and no stylesheet test finds
            it, because the rule and the token are both present and correct.

        Args:
            portal_page: The browser page that points at the portal.
            theme: One shipped theme name.
            selector: The header element to read.
            token: The custom property that must paint it.
        """
        _open(portal_page, f"{HISTORY_PAGE_PATH}?theme={theme}")
        answer = self._ink(portal_page, selector, token)
        assert answer["painted"] == answer["expected"], (
            f"Under the {theme} theme {selector} paints {answer['painted']}, "
            f"and {token} names {answer['expected']}. A more specific rule won."
        )

    @pytest.mark.parametrize("theme", THEME_NAMES)
    def test_a_link_styled_as_a_button_paints_the_button_ink(self, portal_page: Any, theme: str) -> None:
        """A link that carries a button class paints the button text color.

        Why:
            The portal draws some buttons as a link, because the control moves
            the operator to another page. Such a link took the page link color on
            top of the button fill, which put pale pink text on a magenta pill.

        Args:
            portal_page: The browser page that points at the portal.
            theme: One shipped theme name.
        """
        _open(portal_page, f"{HISTORY_PAGE_PATH}?theme={theme}")
        answer = self._ink(portal_page, LINK_BUTTON_SELECTOR, LINK_BUTTON_INK)
        assert answer["painted"] == answer["expected"], (
            f"Under the {theme} theme the link button paints {answer['painted']}, "
            f"and {LINK_BUTTON_INK} names {answer['expected']}. A more specific rule won."
        )

    @pytest.mark.parametrize("theme", THEME_NAMES)
    def test_a_link_styled_as_a_button_carries_no_underline(self, portal_page: Any, theme: str) -> None:
        """A link that carries a button class draws no underline.

        Why:
            A button carries no underline, and the browser underlines a link by
            default. The rule that removes it names one bare class and lost to
            the section 5 rule, so the pill kept the underline of a link.

        Args:
            portal_page: The browser page that points at the portal.
            theme: One shipped theme name.
        """
        _open(portal_page, f"{HISTORY_PAGE_PATH}?theme={theme}")
        element = portal_page.locator(LINK_BUTTON_SELECTOR).first
        sync_api.expect(element).to_be_visible(timeout=GATE_TIMEOUT_MS)
        found = element.evaluate("node => getComputedStyle(node).textDecorationLine")
        assert found == NO_UNDERLINE, f"Under the {theme} theme the link button reads text-decoration {found}."


class TestTheScrollbarTakesTheThemeColors:
    """The scrollbar of the window and of a table box paints the theme pair.

    Why:
        The browser paints its own scrollbar, and it picks a light pair unless a
        rule names the colors. The dark theme therefore shipped with a light gray
        scrollbar down the right edge of a near black page, and a second one
        under every wide table. The `color-scheme` value that `data-bs-theme`
        brings does not reach the scrollbar in every browser, so `portal.css`
        names the colors and this test reads what the browser painted.

        The rule sits on the root element, and `scrollbar-color` inherits, so one
        rule covers the window and every box that scrolls inside the page. A rule
        moved to `.portal-shell` would still paint the table box, because the
        shell is the parent of that box, and would leave the window scrollbar
        light. The two elements are therefore read apart.
    """

    @staticmethod
    def _pair(page: Any, selector: str) -> dict[str, str]:
        """Return the painted scrollbar pair beside the pair that the token names.

        Args:
            page: The browser page, already opened on the history page.
            selector: The element to read.

        Returns:
            The painted pair, the pair the token names, and the raw token text.
        """
        answer: dict[str, str] = page.locator(selector).first.evaluate(SCROLLBAR_PAINTED_AND_EXPECTED, SCROLLBAR_TOKEN)
        assert answer["raw"], f"No theme sets {SCROLLBAR_TOKEN}, so this comparison would read two empty values."
        assert (
            answer["expected"] != SCROLLBAR_AUTO
        ), f"{SCROLLBAR_TOKEN} reads {answer['raw']}, which the browser did not accept as a scrollbar pair."
        return answer

    @pytest.mark.parametrize("theme", THEME_NAMES)
    @pytest.mark.parametrize("selector", (SCROLLBAR_ROOT_SELECTOR, TABLE_SCROLL_SELECTOR))
    def test_a_scrolling_box_paints_the_scrollbar_token(self, portal_page: Any, theme: str, selector: str) -> None:
        """The window and the table box both paint the scrollbar pair of the theme.

        Why:
            A theme that sets the token while no rule reads it paints nothing,
            and a rule that reads the token from the wrong element paints only
            the inner box. Both faults leave a light scrollbar on a dark page,
            and neither one shows in a stylesheet test.

        Args:
            portal_page: The browser page that points at the portal.
            theme: One shipped theme name.
            selector: The element whose scrollbar must carry the theme pair.
        """
        _open(portal_page, f"{HISTORY_PAGE_PATH}?theme={theme}")
        answer = self._pair(portal_page, selector)
        assert answer["painted"] == answer["expected"], (
            f"Under the {theme} theme {selector} paints scrollbar-color {answer['painted']}, "
            f"and {SCROLLBAR_TOKEN} names {answer['expected']}."
        )
