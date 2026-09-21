"""Browser tests for the brand theme and its rendered contrast (issue #3136).

Why a browser test:
    A static read of a stylesheet cannot prove what a page paints. The accent
    reaches the page through three layers that can each win: the theme file, the
    shared `portal.css`, and an inline `<style>` block that `base.html` writes
    after both.

    That layering produced the defect this file guards. The theme set the open
    accordion heading to a readable ink, and `portal.css` overrode it with the
    raw brand color at 3.02:1, because its selector carries higher specificity
    and it loads later. Only a rendered measurement sees that.

Method:
    Each test reads the computed color of a real element and applies the WCAG
    2.1 relative luminance formula to the pair.
"""

from __future__ import annotations

import logging
import socket
import threading
from collections.abc import Iterator
from typing import Any

import pytest

logger = logging.getLogger(__name__)

pytest.importorskip("playwright", reason="playwright is absent, so no browser test can run")

READY_TIMEOUT_MS = 15000  # One page load must not block the suite.
SETTLE_MS = 800  # A theme swap replaces a stylesheet, so the page needs one paint.
TEXT_FLOOR = 4.5  # The WCAG 2.1 floor for normal text.
GRAPHIC_FLOOR = 3.0  # The WCAG 2.1 floor for a control boundary or a graphic.
BRAND_COLOR = "rgb(226, 0, 116)"  # #E20074 as the browser reports it.
SHIPPED_THEMES = ("magenta", "dark", "light", "high-contrast")

# One helper, injected into the page, returns the contrast ratio of two colors.
RATIO_JS = """
(pair) => {
    const lum = (c) => {
        const [r, g, b] = c.match(/\\d+/g).slice(0, 3).map(Number).map(v => {
            const s = v / 255;
            return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    };
    const [hi, lo] = [lum(pair[0]), lum(pair[1])].sort((a, b) => b - a);
    return Math.round(((hi + 0.05) / (lo + 0.05)) * 100) / 100;
}
"""


def free_port() -> int:
    """Return a port that no other process holds right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))  # Port zero asks the operating system for a free port.
        return int(probe.getsockname()[1])


@pytest.fixture(scope="module")
def theme_portal(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Serve the portal, so the browser reads the real stylesheets."""
    from werkzeug.serving import make_server

    from web_portal.app import WebPortalApp
    from web_portal.menu_registry import build_static_menu_actions

    data_dir = tmp_path_factory.mktemp("theme_data")
    app = WebPortalApp.create_app(apisession=None, menu_actions=build_static_menu_actions(), org_id="test-org")
    app.config["TESTING"] = True
    app.config["DATA_DIR"] = str(data_dir)

    port = free_port()  # Never take a fixed port, because a developer may hold it.
    server = make_server("127.0.0.1", port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    logger.info("Starting the theme portal on port %d", port)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=10)
        WebPortalApp.shutdown_app(app)


@pytest.fixture
def portal_page(page: Any, theme_portal: str) -> Any:
    """Open the operations page with no saved theme preference."""
    page.goto(f"{theme_portal}/operations", wait_until="networkidle", timeout=READY_TIMEOUT_MS)
    page.evaluate("() => localStorage.removeItem('misthelper-theme')")
    page.reload(wait_until="networkidle", timeout=READY_TIMEOUT_MS)
    page.wait_for_selector(".op-item", state="attached", timeout=READY_TIMEOUT_MS)
    return page


def ratio(page: Any, foreground: str, background: str) -> float:
    """Return the contrast ratio the browser computes for one color pair."""
    return page.evaluate(RATIO_JS, [foreground, background])


def open_first_category(page: Any) -> None:
    """Open the first category, which reveals the open heading style."""
    page.locator("h2 button").first.click()
    page.wait_for_timeout(400)


def use_theme(page: Any, name: str) -> None:
    """Switch the page to one theme and wait for the new stylesheet to paint."""
    page.evaluate("name => applyTheme(name)", name)
    page.wait_for_timeout(SETTLE_MS)


def computed(page: Any, selector: str, prop: str) -> str:
    """Return one computed style value for the first matching element."""
    return page.evaluate(
        "args => { const e = document.querySelector(args[0]); return e ? getComputedStyle(e)[args[1]] : null; }",
        [selector, prop],
    )


class TestTheFirstVisitLandsOnTheBrandTheme:
    """An operator with no saved preference must meet the brand theme."""

    def test_the_theme_stylesheet_is_the_brand_theme(self, portal_page: Any) -> None:
        """The page must request the brand stylesheet on a fresh browser."""
        href = portal_page.evaluate("() => document.getElementById('theme-css').href")
        assert href.endswith("/magenta.css")

    def test_the_page_paints_the_brand_surface(self, portal_page: Any) -> None:
        """The brand theme is dark, so the page must be near black."""
        assert computed(portal_page, "body", "backgroundColor") == "rgb(13, 13, 13)"

    def test_the_rendered_accent_is_the_brand_color(self, portal_page: Any) -> None:
        """base.html injects the accent last, so this proves the two settings agree."""
        accent = portal_page.evaluate(
            "() => getComputedStyle(document.documentElement).getPropertyValue('--portal-accent').trim()"
        )
        assert accent.upper() == "#E20074"

    def test_the_primary_button_carries_the_brand_fill(self, portal_page: Any) -> None:
        """A blue Run button on a magenta page is the mismatch this guards."""
        open_first_category(portal_page)
        portal_page.locator(".op-item").first.click()
        portal_page.wait_for_timeout(SETTLE_MS)
        assert computed(portal_page, '[data-testid="run-btn"]', "backgroundColor") == BRAND_COLOR

    def test_the_header_carries_the_brand_fill(self, portal_page: Any) -> None:
        """The header is the first brand signal on every page."""
        image = computed(portal_page, ".portal-navbar", "backgroundImage")
        assert "linear-gradient" in image
        assert "163, 0, 90" in image  # The dark end of the brand fill.


class TestTheAccentNeverPaintsUnreadableText:
    """An accent is a fill. Text through the same token needs its own ink."""

    @pytest.mark.parametrize("theme", SHIPPED_THEMES)
    def test_open_category_heading_meets_the_text_floor(self, portal_page: Any, theme: str) -> None:
        """Measured before the repair: 3.02 magenta, 2.58 dark, 4.27 light, 2.60 high contrast."""
        use_theme(portal_page, theme)
        open_first_category(portal_page)
        ink = computed(portal_page, ".accordion-button:not(.collapsed)", "color")
        surface = computed(portal_page, ".accordion-button:not(.collapsed)", "backgroundColor")
        measured = ratio(portal_page, ink, surface)
        assert measured >= TEXT_FLOOR, f"{theme} paints the open heading at {measured}:1"

    @pytest.mark.parametrize("theme", SHIPPED_THEMES)
    def test_the_heading_ink_is_never_the_raw_brand_color(self, portal_page: Any, theme: str) -> None:
        """#E20074 gives 3.02:1 on a card, so no theme may paint text with it."""
        use_theme(portal_page, theme)
        open_first_category(portal_page)
        assert computed(portal_page, ".accordion-button:not(.collapsed)", "color") != BRAND_COLOR


class TestTheBrandSurfacesMeetTheirFloors:
    """The brand theme states a ratio for each pair. These read the real page."""

    def test_page_text_is_readable(self, portal_page: Any) -> None:
        """White on near black carries the whole page, so it must be clear."""
        measured = ratio(
            portal_page,
            computed(portal_page, "body", "color"),
            computed(portal_page, "body", "backgroundColor"),
        )
        assert measured >= TEXT_FLOOR

    def test_muted_text_is_readable(self, portal_page: Any) -> None:
        """A muted line still carries meaning, so it holds the same floor."""
        measured = ratio(
            portal_page,
            computed(portal_page, ".text-muted", "color"),
            computed(portal_page, "body", "backgroundColor"),
        )
        assert measured >= TEXT_FLOOR

    def test_the_primary_button_label_is_readable(self, portal_page: Any) -> None:
        """White on the brand fill is the pair the theme documents at 4.68:1."""
        open_first_category(portal_page)
        portal_page.locator(".op-item").first.click()
        portal_page.wait_for_timeout(SETTLE_MS)
        measured = ratio(
            portal_page,
            computed(portal_page, '[data-testid="run-btn"]', "color"),
            computed(portal_page, '[data-testid="run-btn"]', "backgroundColor"),
        )
        assert measured >= TEXT_FLOOR

    def test_the_chosen_operation_row_is_readable(self, portal_page: Any) -> None:
        """The chosen row takes the brand fill, so its label must stay legible."""
        open_first_category(portal_page)
        portal_page.locator(".op-item").first.click()
        portal_page.wait_for_timeout(SETTLE_MS)
        measured = ratio(
            portal_page,
            computed(portal_page, ".op-item.active", "color"),
            computed(portal_page, ".op-item.active", "backgroundColor"),
        )
        assert measured >= TEXT_FLOOR

    def test_the_header_link_is_readable(self, portal_page: Any) -> None:
        """A navigation link sits on the brand fill, not on the page surface."""
        measured = ratio(
            portal_page,
            computed(portal_page, ".portal-navbar .nav-link", "color"),
            "rgb(196, 0, 106)",  # The light end of the fill, which is the harder pair.
        )
        assert measured >= TEXT_FLOOR

    def test_the_field_boundary_is_visible(self, portal_page: Any) -> None:
        """A field an operator cannot find is a field that reads as absent."""
        measured = ratio(
            portal_page,
            computed(portal_page, "#opSearch", "borderTopColor"),
            computed(portal_page, "#opSearch", "backgroundColor"),
        )
        assert measured >= GRAPHIC_FLOOR


class TestEveryThemeStillWorks:
    """A new default must not break a theme an operator already chose."""

    @pytest.mark.parametrize("theme", SHIPPED_THEMES)
    def test_theme_loads_and_paints(self, portal_page: Any, theme: str) -> None:
        """Each theme must swap its stylesheet and paint its own surface."""
        use_theme(portal_page, theme)
        href = portal_page.evaluate("() => document.getElementById('theme-css').href")
        assert href.endswith(f"/{theme}.css")
        assert computed(portal_page, "body", "backgroundColor") != ""

    @pytest.mark.parametrize("theme", SHIPPED_THEMES)
    def test_body_text_is_readable_in_every_theme(self, portal_page: Any, theme: str) -> None:
        """A theme that fails this test is unusable, whatever its colors."""
        use_theme(portal_page, theme)
        measured = ratio(
            portal_page,
            computed(portal_page, "body", "color"),
            computed(portal_page, "body", "backgroundColor"),
        )
        assert measured >= TEXT_FLOOR

    def test_only_the_light_theme_asks_bootstrap_for_light_controls(self, portal_page: Any) -> None:
        """Bootstrap draws its own controls, so the flag must match the surface."""
        for theme in SHIPPED_THEMES:
            use_theme(portal_page, theme)
            flag = portal_page.evaluate("() => document.documentElement.getAttribute('data-bs-theme')")
            assert flag == ("light" if theme == "light" else "dark"), f"{theme} set {flag}"

    def test_the_choice_survives_a_reload(self, portal_page: Any, theme_portal: str) -> None:
        """An operator who picks a theme must keep it on the next page."""
        use_theme(portal_page, "dark")
        portal_page.goto(f"{theme_portal}/operations", wait_until="networkidle", timeout=READY_TIMEOUT_MS)
        portal_page.wait_for_timeout(SETTLE_MS)
        href = portal_page.evaluate("() => document.getElementById('theme-css').href")
        assert href.endswith("/dark.css")
