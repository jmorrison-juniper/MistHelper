"""Browser proofs for accessible names on the Operations page."""

from __future__ import annotations

import logging
import socket
import threading
from collections.abc import Iterator
from typing import Any

import pytest

logger = logging.getLogger(__name__)

pytest.importorskip("playwright", reason="playwright is absent, so no browser test can run")

READY_TIMEOUT_MS = 15000
STATIC_CONTROLS = (
    ("#opSearch", "Search operations"),
    ("#resultsFileSelect", "Select a result file"),
    ("#resultsSearch", "Filter result rows"),
    ("#dataPreviewSearch", "Search preview rows"),
)
DYNAMIC_MENUS = (("257", False), ("263", True), ("267", True))


def free_port() -> int:
    """Return an available loopback port for the test server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


@pytest.fixture(scope="module")
def portal_url(flask_app: Any) -> Iterator[str]:
    """Serve the Flask application for browser accessibility checks."""
    from werkzeug.serving import make_server

    port = free_port()
    server = make_server("127.0.0.1", port, flask_app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    logger.info("Starting the accessibility test server on port %d", port)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        logger.info("Stopping the accessibility test server on port %d", port)
        server.shutdown()
        thread.join(timeout=10)


@pytest.fixture
def operations_page(page: Any, portal_url: str) -> Any:
    """Return the rendered Operations page after its operation list loads."""
    page.goto(f"{portal_url}/operations", wait_until="networkidle", timeout=READY_TIMEOUT_MS)
    page.wait_for_selector(".op-item", state="attached", timeout=READY_TIMEOUT_MS)
    return page


def test_static_controls_have_programmatic_names(operations_page: Any) -> None:
    """Each existing static control must use a label or an ARIA label."""
    present_count = 0
    for selector, expected_name in STATIC_CONTROLS:
        control = operations_page.locator(selector)
        assert control.count() == 1, f"{selector} is absent, so the accessibility proof measures nothing."
        present_count += 1
        name_source = control.evaluate(
            "element => ({"
            "labelCount: element.labels ? element.labels.length : 0,"
            "ariaLabel: element.getAttribute('aria-label') || ''"
            "})"
        )
        assert (
            name_source["labelCount"] > 0 or name_source["ariaLabel"] == expected_name
        ), f"{selector} has no label or expected aria-label. A placeholder does not satisfy this proof."
    print(f"The static accessibility proof examined {present_count} Operations controls.")
    assert present_count == len(STATIC_CONTROLS)


@pytest.mark.xfail(
    strict=True,
    reason="Issue #4041: generated controls need labels in the owned web_portal/static/js/operations.js file.",
)
@pytest.mark.parametrize(("menu_number", "choose_endpoint"), DYNAMIC_MENUS)
def test_generated_controls_have_programmatic_names(
    operations_page: Any,
    menu_number: str,
    choose_endpoint: bool,
) -> None:
    """Representative generated controls must use their visible labels as names."""
    operation = operations_page.locator(f'.op-item[data-menu="{menu_number}"]')
    assert operation.count() == 1, f"Menu {menu_number} is absent, so the accessibility proof measures nothing."
    operation.evaluate("element => element.click()")
    operations_page.wait_for_selector("#parameterFields select, #parameterFields input", state="attached")
    if choose_endpoint:
        chooser = operations_page.locator("#param-endpoint_operation")
        chooser.select_option(index=1)
    controls = operations_page.locator("#parameterFields select, #parameterFields input")
    examined_count = controls.count()
    print(f"The dynamic accessibility proof examined {examined_count} controls for menu {menu_number}.")
    assert examined_count > 0, f"Menu {menu_number} rendered no controls, so the proof measures nothing."
    for index in range(examined_count):
        name_source = controls.nth(index).evaluate(
            "element => ({"
            "id: element.id,"
            "labelCount: element.labels ? element.labels.length : 0,"
            "ariaLabel: element.getAttribute('aria-label') || ''"
            "})"
        )
        assert (
            name_source["labelCount"] > 0 or name_source["ariaLabel"]
        ), f"{name_source['id']} has no associated label or aria-label."
