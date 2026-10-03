"""Browser tests for the responsive operations portal (issue #3132).

Why:
    The portal carried one media query for the whole page, so it read as a
    desktop page on every device. On a 390 pixel phone the list and the run
    panel stacked, and selecting an operation put the Run button 609 pixels
    below the fold. The page gave no sign that the selection had worked.

    A measurement, not an impression, drives each test below. Each one states
    the number it holds.

Scope:
    These tests read rendered geometry. A rule that only changes a colour is
    not tested here, because the theme files own colour.
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
SETTLE_MS = 900  # The panel scroll and the parameter fetch each need one round trip.
MIN_TOUCH_PX = 44  # The widely used minimum for a touch target.

PHONE = {"width": 390, "height": 844}
TABLET_PORTRAIT = {"width": 768, "height": 1024}
DESKTOP = {"width": 1440, "height": 900}


def free_port() -> int:
    """Return a port that no other process holds right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))  # Port zero asks the operating system for a free port.
        return int(probe.getsockname()[1])


@pytest.fixture(scope="module")
def responsive_portal(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Serve the portal, so a browser can read the real stylesheets."""
    from werkzeug.serving import make_server

    from web_portal.app import WebPortalApp
    from web_portal.menu_registry import build_static_menu_actions

    data_dir = tmp_path_factory.mktemp("responsive_data")
    app = WebPortalApp.create_app(apisession=None, menu_actions=build_static_menu_actions(), org_id="test-org")
    app.config["TESTING"] = True
    app.config["DATA_DIR"] = str(data_dir)

    port = free_port()  # Never take a fixed port, because a developer may hold it.
    server = make_server("127.0.0.1", port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    logger.info("Starting the responsive portal on port %d", port)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=10)
        WebPortalApp.shutdown_app(app)


def open_operations(page: Any, base_url: str, viewport: dict) -> Any:
    """Load the operations page at one viewport size."""
    page.set_viewport_size(viewport)
    page.goto(f"{base_url}/operations", wait_until="networkidle", timeout=READY_TIMEOUT_MS)
    page.wait_for_selector(".op-item", state="attached", timeout=READY_TIMEOUT_MS)
    return page


def select_first_operation(page: Any) -> None:
    """Open the first category and select its first operation."""
    page.locator("h2 button").first.click()
    page.wait_for_timeout(400)
    page.locator(".op-item").first.click()
    page.wait_for_timeout(SETTLE_MS)


def rect(page: Any, selector: str) -> dict | None:
    """Return the rendered box of one element, or None when it is absent."""
    return page.evaluate(
        """sel => {
            const el = document.querySelector(sel);
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return {
                x: Math.round(r.x), y: Math.round(r.y),
                width: Math.round(r.width), height: Math.round(r.height),
                visible: el.offsetParent !== null || getComputedStyle(el).position === 'fixed'
            };
        }""",
        selector,
    )


def horizontal_overflow(page: Any) -> int:
    """Return the number of pixels the document exceeds the viewport width."""
    return page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")


class TestNoViewportOverflows:
    """A page that scrolls sideways hides content the operator needs."""

    @pytest.mark.parametrize(
        "viewport",
        [
            {"width": 360, "height": 740},
            PHONE,
            TABLET_PORTRAIT,
            {"width": 1024, "height": 768},
            DESKTOP,
            {"width": 1920, "height": 1080},
        ],
        ids=["phone-small", "phone", "tablet-portrait", "tablet-landscape", "laptop", "desktop"],
    )
    def test_page_never_scrolls_sideways(self, page: Any, responsive_portal: str, viewport: dict) -> None:
        """Every supported width must render without horizontal overflow."""
        open_operations(page, responsive_portal, viewport)
        assert horizontal_overflow(page) == 0


class TestThePhoneShowsTheRunControl:
    """The reported defect put the primary action below the fold."""

    def test_run_button_is_visible_after_a_selection(self, page: Any, responsive_portal: str) -> None:
        """A selection must bring the Run button into view without a manual scroll."""
        open_operations(page, responsive_portal, PHONE)
        select_first_operation(page)
        box = rect(page, '[data-testid="run-btn"]')
        assert box["y"] >= 0
        assert box["y"] + box["height"] <= PHONE["height"], "The Run button must sit inside the viewport"

    def test_selected_panel_clears_the_sticky_navbar(self, page: Any, responsive_portal: str) -> None:
        """A scrolled panel must not hide beneath the sticky header."""
        open_operations(page, responsive_portal, PHONE)
        select_first_operation(page)
        navbar = rect(page, ".portal-navbar")
        panel = rect(page, "#selectedOp")
        assert panel["y"] >= navbar["y"] + navbar["height"]

    def test_back_control_appears_on_a_stacked_layout(self, page: Any, responsive_portal: str) -> None:
        """The operator needs a way back to the list when the panes stack."""
        open_operations(page, responsive_portal, PHONE)
        select_first_operation(page)
        assert rect(page, '[data-testid="back-to-list"]')["visible"] is True

    def test_back_control_returns_the_view_to_the_search_box(self, page: Any, responsive_portal: str) -> None:
        """The control must move the view, and it must not reload the page."""
        open_operations(page, responsive_portal, PHONE)
        select_first_operation(page)
        page.locator('[data-testid="back-to-list"]').click()
        page.wait_for_timeout(SETTLE_MS)
        search = rect(page, "#opSearch")
        assert 0 <= search["y"] <= PHONE["height"], "The search box must return into view"

    def test_the_helper_reports_a_stacked_layout(self, page: Any, responsive_portal: str) -> None:
        """The scroll decision must read the layout, not guess from a width."""
        open_operations(page, responsive_portal, PHONE)
        assert page.evaluate("() => panesAreStacked()") is True

    def test_the_selection_brings_the_whole_panel_into_view(self, page: Any, responsive_portal: str) -> None:
        """The sticky bar pins the button, and the scroll fits the whole panel.

        Measured on a 390 by 844 phone. With the scroll the panel occupies 565
        to 779 and fits. Without it the panel runs from 636 to 850 and its last
        6 pixels fall past the fold, so the operator cannot see the panel end.
        """
        open_operations(page, responsive_portal, PHONE)
        select_first_operation(page)
        panel = rect(page, "#selectedOp")
        assert panel["y"] >= 0
        assert panel["y"] + panel["height"] <= PHONE["height"], "The whole panel must fit after a selection"


class TestTouchTargets:
    """A finger needs a larger target than a mouse pointer does."""

    @pytest.mark.parametrize(
        "selector",
        ['[data-testid="run-btn"]', '[data-testid="back-to-list"]', ".op-item", ".accordion-button"],
    )
    def test_control_meets_the_touch_minimum_on_a_phone(self, page: Any, responsive_portal: str, selector: str) -> None:
        """Each control an operator presses must be at least 44 pixels tall."""
        open_operations(page, responsive_portal, PHONE)
        select_first_operation(page)
        assert rect(page, selector)["height"] >= MIN_TOUCH_PX


class TestTheDesktopLayoutIsUnchanged:
    """A mobile repair must not cost the desktop reader anything."""

    def test_panes_stay_side_by_side(self, page: Any, responsive_portal: str) -> None:
        """The two-pane layout is the reason the desktop page reads well."""
        open_operations(page, responsive_portal, DESKTOP)
        select_first_operation(page)
        assert page.evaluate("() => panesAreStacked()") is False

    def test_mobile_only_controls_stay_hidden(self, page: Any, responsive_portal: str) -> None:
        """A desktop reader must never meet a control that belongs to a phone."""
        open_operations(page, responsive_portal, DESKTOP)
        select_first_operation(page)
        assert rect(page, '[data-testid="back-to-list"]')["visible"] is False
        assert rect(page, '[data-testid="table-scroll-hint"]')["visible"] is False

    def test_the_action_bar_is_not_sticky(self, page: Any, responsive_portal: str) -> None:
        """A sticky bar wastes height on a screen that already shows the button."""
        open_operations(page, responsive_portal, DESKTOP)
        select_first_operation(page)
        assert page.evaluate("() => getComputedStyle(document.querySelector('.op-action-bar')).position") == "static"

    def test_the_page_intro_and_brand_remain(self, page: Any, responsive_portal: str) -> None:
        """The phone hides two labels for space. The desktop must keep both."""
        open_operations(page, responsive_portal, DESKTOP)
        assert rect(page, ".portal-page-intro")["visible"] is True
        assert rect(page, ".brand-text")["visible"] is True


class TestThePhoneReclaimsHeight:
    """A phone screen is short, so a repeated label costs real space."""

    def test_the_duplicate_brand_label_is_hidden(self, page: Any, responsive_portal: str) -> None:
        """The logo already carries the name, so the text beside it repeats it."""
        open_operations(page, responsive_portal, PHONE)
        assert rect(page, ".brand-text")["visible"] is False

    def test_the_category_list_is_bounded(self, page: Any, responsive_portal: str) -> None:
        """An unbounded list of 18 categories buries the run panel."""
        open_operations(page, responsive_portal, PHONE)
        page.locator("h2 button").first.click()
        page.wait_for_timeout(400)
        height = rect(page, "#operationAccordion")["height"]
        assert height <= PHONE["height"] * 0.60, "The list must not fill the screen"
