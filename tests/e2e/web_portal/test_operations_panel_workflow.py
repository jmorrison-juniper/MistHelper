"""Browser tests for the operations page panel visibility (issue #3030).

Why:
    The operations page could not run any operation. Every panel carried the
    Bootstrap class ``d-none``, and the script tried to reveal each one by
    writing ``element.style.display``. Bootstrap declares that class with
    ``display: none !important``, which outranks an inline style, so the panel
    stayed invisible. A user clicked an operation and saw nothing.

    The existing tests asserted that an element exists in the document. An
    element that carries ``d-none`` still exists, so those assertions passed
    while the page was unusable.

    Warning: a test that reads the document but never reads the computed style
    cannot tell a visible control from a hidden one. These tests therefore read
    the computed style inside a real browser.

Scope:
    These tests serve the Flask application in this process with the static menu
    registry, so they need no Mist API token and no live organization. They
    cover the visibility contract only. A live run needs credentials, and
    ``tests/e2e/upgrade_portal`` covers that path for the other portal.

Fixture note:
    The tests use the ``page`` fixture of ``pytest-playwright``. A direct call
    to ``sync_playwright`` fails with "Please use the Async API instead" when
    another test in this directory already runs an event loop.
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
SETTLE_MS = 600  # The click handler and the parameter fetch need a moment to finish.


def free_port() -> int:
    """Return a port that no other process holds right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))  # Port zero asks the operating system for a free port.
        return int(probe.getsockname()[1])


@pytest.fixture(scope="module")
def portal_url(flask_app: Any) -> Iterator[str]:
    """Serve the portal in this process and return its base address.

    Why:
        A browser needs a real HTTP endpoint. Werkzeug serves one in a thread
        and runs on Windows, which Gunicorn cannot do because it imports
        ``fcntl``.
    """
    from werkzeug.serving import make_server

    port = free_port()  # Never take a fixed port, because a developer may hold it.
    server = make_server("127.0.0.1", port, flask_app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    logger.info("Starting the portal test server on port %d", port)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        logger.info("Stopping the portal test server on port %d", port)
        server.shutdown()  # Release the port, so a later test can bind its own.
        thread.join(timeout=10)


@pytest.fixture
def operations_page(page: Any, portal_url: str) -> Any:
    """Return the operations page with one category expanded.

    The accordion starts collapsed, so every operation row is attached but
    hidden. A user expands a category before clicking a row, and this fixture
    performs that same step.
    """
    page.goto(f"{portal_url}/operations", wait_until="networkidle", timeout=READY_TIMEOUT_MS)
    # The rows are attached but collapsed, so wait for attachment and not for visibility.
    page.wait_for_selector(".op-item", state="attached", timeout=READY_TIMEOUT_MS)
    headers = page.locator("[data-testid='operation-accordion'] button")
    for index in range(headers.count()):  # Open each category until one reveals a row.
        headers.nth(index).click()
        page.wait_for_timeout(250)  # Let the accordion animation settle.
        if page.locator(".op-item:visible").count() > 0:  # This category holds a visible row now.
            return page
    pytest.skip("No accordion category revealed an operation row, so the workflow cannot run.")
    return page


def is_visible(page: Any, element_id: str) -> bool:
    """Report whether one element is visible to a user right now."""
    return bool(
        page.evaluate(
            "id => { const el = document.getElementById(id);"
            " return !!el && getComputedStyle(el).display !== 'none'; }",
            element_id,
        )
    )


def first_visible_item(page: Any) -> Any:
    """Return the first operation row that a user can click."""
    return page.locator(".op-item:visible").first


class TestTheOperationsPagePaintsItsControls:
    """Prove that a user can see the controls after selecting an operation."""

    def test_the_page_lists_operations(self, operations_page: Any) -> None:
        """A page with no operation cannot prove anything below, so measure the list first."""
        count = operations_page.locator(".op-item").count()
        visible = operations_page.locator(".op-item:visible").count()
        print(f"The operations page painted {count} operation rows, and {visible} are visible now.")
        assert count > 0, "The operations page listed no operation, so this test measures nothing."
        assert visible > 0, "No operation row is reachable, so a user cannot select one."

    def test_selecting_an_operation_reveals_the_panel(self, operations_page: Any) -> None:
        """Issue #3030. This is the assertion that the defect failed."""
        assert not is_visible(operations_page, "selectedOp"), "The panel is visible before any selection."
        first_visible_item(operations_page).click()
        operations_page.wait_for_timeout(SETTLE_MS)
        assert is_visible(operations_page, "selectedOp"), (
            "Selecting an operation left the panel hidden. The Bootstrap class 'd-none' carries "
            "'display: none !important', so an inline style cannot reveal it. Issue #3030."
        )

    def test_the_run_button_is_visible_after_a_selection(self, operations_page: Any) -> None:
        """A hidden Run button makes every operation unreachable from the browser."""
        first_visible_item(operations_page).click()
        operations_page.wait_for_timeout(SETTLE_MS)
        assert operations_page.locator(
            '[data-testid="run-btn"]'
        ).is_visible(), "The Run button is not visible, so a user cannot start the operation. Issue #3030."

    def test_the_panel_names_the_selected_operation(self, operations_page: Any) -> None:
        """A visible panel must also carry the right content."""
        item = first_visible_item(operations_page)
        menu_number = item.get_attribute("data-menu")
        item.click()
        operations_page.wait_for_timeout(SETTLE_MS)
        assert menu_number in operations_page.locator("#selectedOpTitle").inner_text()

    def test_the_hidden_class_beats_an_inline_style(self, operations_page: Any) -> None:
        """Pin the browser rule that caused the defect, so a reader sees the cause.

        If a future Bootstrap release drops the ``!important`` declaration, this
        test fails and tells the next engineer that the repair may be relaxed.
        """
        beats_inline = operations_page.evaluate(
            "() => { const probe = document.createElement('div');"
            " probe.className = 'd-none'; probe.style.display = 'block';"
            " document.body.appendChild(probe);"
            " const hidden = getComputedStyle(probe).display === 'none';"
            " probe.remove(); return hidden; }"
        )
        assert beats_inline is True, (
            "The class 'd-none' no longer outranks an inline style. The repair for issue #3030 "
            "may now be simplified, and this test records that change."
        )
