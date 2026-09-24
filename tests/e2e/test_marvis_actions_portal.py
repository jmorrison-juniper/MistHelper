"""Browser tests for the operations page controls of menu 270, Marvis Actions (issue #3299).

Why:
    FR-031 and FR-032 state two rules. An operator can start menu 270 from the
    operations page. The page sends one answer for each of the six CLI prompts,
    in prompt order. The guardrail test
    ``tests/guardrails/test_marvis_actions_portal_exposure.py`` pins the Python
    registry. These tests prove the part that the registry test cannot see: the
    browser draws the six controls, selects the report mode first, and sends
    the answers in the order that the CLI reads them.

    Warning: a control that the page draws out of order moves every later
    answer by one prompt. A mode 3 run could then read the comment as the
    typed confirmation. These tests therefore read the request body that the
    browser sends.

Scope:
    The tests serve the Flask application in this process with the static menu
    registry, so they need no Mist API token and no live organization. The
    browser answers each run request itself, so no operation starts and no
    Mist record changes.

Fixture note:
    The tests use the ``page`` fixture of ``pytest-playwright``. The module
    ``test_operations_panel_workflow.py`` states the reason.
"""

from __future__ import annotations

import json
import logging
import socket
import threading
from collections.abc import Iterator
from typing import Any

import pytest

from src.marvis.actions.model import CATEGORY_NAMES, RESOLUTION_CODES, TOPIC_NAMES

logger = logging.getLogger(__name__)  # A module logger keeps the record source readable.

pytest.importorskip("playwright", reason="playwright is absent, so no browser test can run")

READY_TIMEOUT_MS = 15000  # One page load must not block the suite.
MARVIS_MENU = "270"  # The menu number that issue #3299 added.
GROUP_TITLE = "Marvis Actions"  # The accordion group that holds menu 270.
GROUP_BUTTON = "#operationAccordion .accordion-button"  # The header button of each accordion group.
RUN_BUTTON = '[data-testid="run-btn"]'  # The Run button of the operations panel.
RUN_ROUTE_GLOB = "**/api/operations/run"  # The run request that the browser sends.
PLACEHOLDER_OPTIONS = 1  # Each choice list starts with one "-- Select --" option.
MODE_COUNT = 3  # The CLI offers three modes: two reports and one resolve.
CONTROL_NAMES = (  # The six controls, in the order of the six CLI prompts.
    "marvis_mode",
    "marvis_category",
    "marvis_subcategory",
    "marvis_resolution_code",
    "marvis_comment",
    "marvis_confirmation",
)
STOPPED_RUN = {"error": "The browser test stopped the run before the server."}  # The canned run answer.


def free_port() -> int:
    """Return a port that no other process holds right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:  # Open one short-lived probe socket.
        probe.bind(("127.0.0.1", 0))  # Port zero asks the operating system for a free port.
        return int(probe.getsockname()[1])  # Return the port that the operating system chose.


@pytest.fixture(scope="module")
def portal_url(flask_app: Any) -> Iterator[str]:
    """Serve the portal in this process and return its base address.

    Why:
        A browser needs a real HTTP endpoint. Werkzeug serves one in a thread
        and runs on Windows, which Gunicorn cannot do because it imports
        ``fcntl``.
    """
    from werkzeug.serving import make_server  # Import late, so a missing browser skips before this import.

    port = free_port()  # Never take a fixed port, because a developer may hold it.
    server = make_server("127.0.0.1", port, flask_app, threaded=True)  # Bind the test server to loopback only.
    thread = threading.Thread(target=server.serve_forever, daemon=True)  # Serve in the background.
    logger.info("Starting the Marvis Actions portal test server on port %d", port)  # Log before the start.
    thread.start()  # Start to serve requests.
    logger.debug("The Marvis Actions portal test server runs on port %d", port)  # Log after the start.
    try:
        yield f"http://127.0.0.1:{port}"  # Hand the base address to each test.
    finally:
        logger.info("Stopping the Marvis Actions portal test server on port %d", port)  # Log before the stop.
        server.shutdown()  # Release the port, so a later test can bind its own.
        thread.join(timeout=10)  # Wait a bounded time for the thread to end.
        logger.debug("Stopped the Marvis Actions portal test server")  # Log after the stop.


@pytest.fixture
def marvis_page(page: Any, portal_url: str) -> Any:
    """Return the operations page with menu 270 selected and its six controls drawn.

    The accordion starts collapsed. An operator expands the group before a
    selection, and this fixture performs the same steps in the same order.
    """
    logger.info("Opening the operations page to select menu %s", MARVIS_MENU)  # Log before the page load.
    page.goto(f"{portal_url}/operations", wait_until="networkidle", timeout=READY_TIMEOUT_MS)  # Load the page.
    page.locator(GROUP_BUTTON, has_text=GROUP_TITLE).click()  # Expand the group, like an operator does.
    row = page.locator(f".op-item[data-menu='{MARVIS_MENU}']")  # Find the menu 270 row.
    row.wait_for(state="visible", timeout=READY_TIMEOUT_MS)  # Wait for the accordion animation to end.
    row.click()  # Select the operation, which fetches its parameters.
    last_control = f"#param-{CONTROL_NAMES[-1]}"  # The page draws this control last.
    page.wait_for_selector(last_control, state="attached", timeout=READY_TIMEOUT_MS)  # Wait for all six.
    logger.debug("Menu %s shows its controls", MARVIS_MENU)  # Log after the controls appear.
    return page  # Hand the prepared page to the test.


def control_value(page: Any, name: str) -> str:
    """Return the current value of one control, which is the answer that the browser sends."""
    return str(page.locator(f"#param-{name}").input_value())  # Read the value of the select or the text box.


def option_count(page: Any, name: str) -> int:
    """Return the count of options in one choice list, without the placeholder."""
    total = page.locator(f"#param-{name} option").count()  # Count every option of the list.
    return int(total) - PLACEHOLDER_OPTIONS  # Drop the "-- Select --" option, which no prompt reads.


def send_run(page: Any) -> dict[str, Any]:
    """Click Run, answer the request in the browser, and return the body that the browser sent.

    Why:
        A canned answer keeps the run away from the server, so no operation
        starts. The test reads the body, which is the contract with the CLI.
    """

    def answer_in_browser(route: Any) -> None:
        """Fulfill one run request with the canned answer.

        Args:
            route: The intercepted route.
        """
        route.fulfill(status=200, content_type="application/json", body=json.dumps(STOPPED_RUN))  # No run.

    logger.info("Sending one run request that the browser answers itself")  # Log before the click.
    page.route(RUN_ROUTE_GLOB, answer_in_browser)  # Stop the run request inside the browser.
    with page.expect_request(RUN_ROUTE_GLOB, timeout=READY_TIMEOUT_MS) as request_info:  # Catch the request.
        page.locator(RUN_BUTTON).click()  # Start the run, like an operator does.
    body = dict(request_info.value.post_data_json)  # Read the JSON body that the browser sent.
    logger.debug("The browser sent the run body %s", body)  # Log the body. It holds no secret.
    return body  # Hand the body to the test.


class TestMenu270Controls:
    """Prove that the operations page asks the questions of menu 270 in the order of the CLI."""

    def test_the_group_lists_menu_270(self, marvis_page: Any) -> None:
        """FR-031. The Marvis Actions group lists one operation, and the panel names menu 270."""
        header = marvis_page.locator(GROUP_BUTTON, has_text=GROUP_TITLE)  # Find the group header.
        group_count = header.locator(".op-count").inner_text()  # Read the count that the header shows.
        title = marvis_page.locator("#selectedOpTitle").inner_text()  # Read the title of the panel.
        print(f"The {GROUP_TITLE} group lists {group_count} operation, and the panel title is '{title}'.")
        assert group_count == "1", "The Marvis Actions group must hold menu 270 only."
        assert MARVIS_MENU in title, "The panel must name the selected menu number."

    def test_the_panel_draws_six_controls_in_prompt_order(self, marvis_page: Any) -> None:
        """FR-032. The browser sends one answer for each control, in the order of the controls."""
        script = "groups => groups.map(group => group.id)"  # Read the id of each drawn control group.
        drawn = marvis_page.eval_on_selector_all("#parameterFields > div", script)  # Read the drawn order.
        print(f"The panel drew {len(drawn)} controls for menu {MARVIS_MENU}: {drawn}")
        assert drawn == [f"param-group-{name}" for name in CONTROL_NAMES]

    def test_the_report_mode_is_selected_first(self, marvis_page: Any) -> None:
        """A blank CLI answer selects mode 1, every category, and every subcategory. The page must agree."""
        values = {name: control_value(marvis_page, name) for name in CONTROL_NAMES}  # Read each answer.
        assert values == {
            "marvis_mode": "1",
            "marvis_category": "all",
            "marvis_subcategory": "all",
            "marvis_resolution_code": RESOLUTION_CODES[0].key,
            "marvis_comment": "",
            "marvis_confirmation": "",
        }
        assert marvis_page.locator(RUN_BUTTON).is_enabled(), "A report run needs no comment and no confirmation."

    def test_the_lists_offer_every_mode_topic_and_code(self, marvis_page: Any) -> None:
        """Each list offers "all" first, then one option for each category, topic, or code."""
        counts = {name: option_count(marvis_page, name) for name in CONTROL_NAMES[:4]}  # Count the choices.
        print(f"The menu {MARVIS_MENU} lists offer these option counts: {counts}")
        assert counts == {
            "marvis_mode": MODE_COUNT,
            "marvis_category": len(CATEGORY_NAMES) + 1,
            "marvis_subcategory": len(TOPIC_NAMES) + 1,
            "marvis_resolution_code": len(RESOLUTION_CODES),
        }

    def test_the_resolve_mode_states_that_it_changes_mist(self, marvis_page: Any) -> None:
        """Mode 3 writes a status to Mist, so its label must tell the operator before the run."""
        label = marvis_page.locator("#param-marvis_mode option[value='3']").inner_text()  # Read the mode 3 label.
        assert "changes Mist" in label

    def test_a_report_run_sends_the_answers_in_prompt_order(self, marvis_page: Any) -> None:
        """Mode 2 with one topic sends the pair key, because two categories share a subcategory key."""
        marvis_page.select_option("#param-marvis_mode", "2")  # Choose the open actions report.
        marvis_page.select_option("#param-marvis_category", "switch")  # Choose the Wired category.
        marvis_page.select_option("#param-marvis_subcategory", "switch/sw_offline")  # Choose one topic.
        body = send_run(marvis_page)  # Click Run and read the body that the browser sent.
        assert str(body["menu_number"]) == MARVIS_MENU
        assert body["parameters"]["input_answers"] == [
            "2",
            "switch",
            "switch/sw_offline",
            RESOLUTION_CODES[0].key,
            "",
            "",
        ]

    def test_a_resolve_run_sends_the_code_the_comment_and_the_confirmation(self, marvis_page: Any) -> None:
        """Mode 3 reads all six answers. The comment must reach prompt 5 and the confirmation prompt 6."""
        marvis_page.select_option("#param-marvis_mode", "3")  # Choose the resolve mode.
        marvis_page.select_option("#param-marvis_resolution_code", "nonsuggested")  # Choose the "other" code.
        marvis_page.fill("#param-marvis_comment", "Bounced the switch port")  # Type the required comment.
        marvis_page.fill("#param-marvis_confirmation", "RESOLVE 2")  # Type the confirmation text.
        body = send_run(marvis_page)  # Click Run and read the body that the browser sent.
        assert body["parameters"]["input_answers"] == [
            "3",
            "all",
            "all",
            "nonsuggested",
            "Bounced the switch port",
            "RESOLVE 2",
        ]
