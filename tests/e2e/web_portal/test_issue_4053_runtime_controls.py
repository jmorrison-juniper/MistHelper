"""Browser regression tests for menu 91 and menu 195 runtime controls."""

from __future__ import annotations

import json
import logging
import socket
import threading
from collections.abc import Iterator
from typing import Any

import pytest

pytest.importorskip("playwright", reason="playwright is absent, so no browser test can run")

logger = logging.getLogger(__name__)
READY_TIMEOUT_MS = 15000


@pytest.fixture(scope="module")
def issue_4053_portal_url(flask_app: Any) -> Iterator[str]:
    """Serve the portal application for one browser test module."""
    from werkzeug.serving import make_server

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = int(probe.getsockname()[1])
    server = make_server("127.0.0.1", port, flask_app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    logger.info("Starting the issue #4053 test server on port %d", port)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        logger.info("Stopping the issue #4053 test server on port %d", port)
        server.shutdown()
        thread.join(timeout=10)


def test_runtime_controls_have_stable_ids_and_context_answers(page: Any, issue_4053_portal_url: str) -> None:
    """The browser collects menu answers by prompt context rather than position."""
    page.set_viewport_size({"width": 1024, "height": 768})
    page.goto(f"{issue_4053_portal_url}/operations", wait_until="networkidle", timeout=READY_TIMEOUT_MS)
    page.route("**/api/operations/parameters/*", _provide_issue_4053_parameters)
    page.route(
        "**/api/operations/run",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"error": "The test intercepted this operation."}),
        ),
    )

    for menu_number, parameters in _menu_parameters().items():
        operation = page.locator(f'.op-item[data-menu="{menu_number}"]')
        assert operation.count() == 1, f"Menu {menu_number} is absent from the operations list."
        operation.evaluate("element => element.click()")
        for parameter in parameters:
            control = page.locator(f'[data-testid="param-{parameter["name"]}"]')
            control.wait_for(state="attached", timeout=READY_TIMEOUT_MS)
            assert control.count() == 1, f"Menu {menu_number} lacks a stable control for {parameter["name"]}."
        if menu_number == "91":
            page.locator('[data-testid="param-manufacturer"]').fill("Arista")
        else:
            page.locator('[data-testid="param-primary_csv"]').select_option("file:primary.csv")
        answers = page.evaluate("collectInputContextAnswers()")
        if menu_number == "91":
            assert answers == {"manufacturer_report_selection": "Arista"}
        else:
            assert answers["address_audit_post_table"] == "q"
            assert answers["address_audit_writeback_gate"] == "n"
        with page.expect_request("**/api/operations/run") as request_info:
            page.locator("#runBtn").click()
        payload = json.loads(request_info.value.post_data or "{}")
        assert "input_answers" not in payload.get("parameters", {})
        assert payload["parameters"]["input_context_answers"] == answers


def _menu_parameters() -> dict[str, list[dict[str, Any]]]:
    """Return the menu controls used by the browser contract."""
    return {
        "91": [
            {
                "name": "manufacturer",
                "label": "Manufacturer",
                "param_type": "text",
                "required": False,
                "default": "",
                "answer_context": "manufacturer_report_selection",
            }
        ],
        "195": [
            {
                "name": "primary_csv",
                "label": "Primary CSV",
                "param_type": "choice",
                "required": True,
                "options": [{"value": "file:primary.csv", "label": "primary.csv"}],
                "answer_context": "address_audit_csv_pick",
            },
            {
                "name": "authority_csv",
                "label": "Authority CSV",
                "param_type": "choice",
                "required": False,
                "options": [{"value": "", "label": "Skip"}],
                "answer_context": "address_audit_business_csv_pick",
            },
            {
                "name": "business_name",
                "label": "Business name",
                "param_type": "text",
                "required": False,
                "default": "",
                "answer_context": "address_audit_business_name",
            },
            {
                "name": "post_table_action",
                "label": "After the audit",
                "param_type": "choice",
                "required": True,
                "default": "q",
                "options": [
                    {"value": "1", "label": "Save report"},
                    {"value": "q", "label": "Quit"},
                ],
                "answer_context": "address_audit_post_table",
            },
            {
                "name": "write_back",
                "label": "Write corrections to Mist",
                "param_type": "choice",
                "required": True,
                "default": "n",
                "options": [
                    {"value": "n", "label": "No"},
                    {"value": "y", "label": "Yes"},
                ],
                "answer_context": "address_audit_writeback_gate",
            },
        ],
    }


def _provide_issue_4053_parameters(route: Any) -> None:
    """Return mocked parameter data without contacting Mist."""
    menu_number = route.request.url.rsplit("/", maxsplit=1)[-1]
    route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps(
            {
                "menu_number": menu_number,
                "description": f"Operation {menu_number}",
                "category": "interactive_safe",
                "parameters": _menu_parameters()[menu_number],
            }
        ),
    )
