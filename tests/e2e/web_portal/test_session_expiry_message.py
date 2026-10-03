"""Browser tests for the message an expired session shows (issue #3087).

Why:
    An operator whose session expired clicked Run and read this.

    ```text
    Failed to start operation: Failed to execute 'json' on 'Response':
    Unexpected token '<', "<!doctype "... is not valid JSON
    ```

    The real cause was a stale CSRF token. The message named neither the cause
    nor an action.

    The server half of the repair answers an API caller with JSON. The client
    half matters too, because a proxy page and a server error page also arrive
    as HTML. These tests drive `readJsonAnswer` inside a real browser, so they
    prove the shipped function, not a copy of it.
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
HTML_ERROR_BODY = "<!doctype html>\\n<html lang=en>\\n<title>400 Bad Request</title>\\n"


def free_port() -> int:
    """Return a port that no other process holds right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))  # Port zero asks the operating system for a free port.
        return int(probe.getsockname()[1])


@pytest.fixture(scope="module")
def expiry_portal(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Serve the portal, so the browser can load the shipped scripts."""
    from werkzeug.serving import make_server

    from web_portal.app import WebPortalApp
    from web_portal.menu_registry import build_static_menu_actions

    data_dir = tmp_path_factory.mktemp("expiry_data")
    app = WebPortalApp.create_app(apisession=None, menu_actions=build_static_menu_actions(), org_id="test-org")
    app.config["TESTING"] = True
    app.config["DATA_DIR"] = str(data_dir)

    port = free_port()  # Never take a fixed port, because a developer may hold it.
    server = make_server("127.0.0.1", port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    logger.info("Starting the expiry portal on port %d", port)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=10)
        WebPortalApp.shutdown_app(app)


@pytest.fixture
def portal_page(page: Any, expiry_portal: str) -> Any:
    """Open the operations page, which loads portal.js and its helpers."""
    page.goto(f"{expiry_portal}/operations", wait_until="networkidle", timeout=READY_TIMEOUT_MS)
    page.wait_for_function("() => typeof readJsonAnswer === 'function'", timeout=READY_TIMEOUT_MS)
    return page


def read_answer(page: Any, status: int, body: str, content_type: str) -> dict:
    """Send one synthetic answer through the shipped reader and return the object."""
    return page.evaluate(
        """async ([status, body, contentType]) => {
            const response = new Response(body, {
                status: status,
                headers: { 'Content-Type': contentType }
            });
            return await readJsonAnswer(response);
        }""",
        [status, body, content_type],
    )


class TestTheReaderAlwaysYieldsAReason:
    """The reported message must never reach an operator again."""

    def test_html_error_page_yields_a_session_reason(self, portal_page: Any) -> None:
        """The exact reported body must produce a sentence, not a parser message."""
        answer = read_answer(portal_page, 400, HTML_ERROR_BODY, "text/html; charset=utf-8")
        assert "expired" in answer["error"].lower()
        assert "Reload the page" in answer["error"]
        assert "not valid JSON" not in answer["error"]
        assert "Unexpected token" not in answer["error"]

    def test_json_refusal_keeps_the_server_reason(self, portal_page: Any) -> None:
        """When the server names a reason, the reader must not replace it."""
        body = (
            '{"error": "Your session expired. Reload the page, then start the operation again.",'
            ' "code": "csrf_expired"}'
        )
        answer = read_answer(portal_page, 400, body, "application/json")
        assert answer["code"] == "csrf_expired"
        assert answer["error"].startswith("Your session expired.")

    def test_successful_answer_passes_through_unchanged(self, portal_page: Any) -> None:
        """A normal answer must arrive exactly as the server sent it."""
        answer = read_answer(portal_page, 200, '{"run_id": "abc-123", "sites": [1, 2]}', "application/json")
        assert answer == {"run_id": "abc-123", "sites": [1, 2]}
        assert "error" not in answer

    def test_empty_body_yields_a_reason(self, portal_page: Any) -> None:
        """A dropped connection sends no body, and the reader must still answer."""
        answer = read_answer(portal_page, 502, "", "text/html")
        assert "restarting" in answer["error"]

    def test_server_error_page_names_the_log(self, portal_page: Any) -> None:
        """A 500 page must send the reader to the log that holds the cause."""
        answer = read_answer(portal_page, 500, "<html><body>Internal Server Error</body></html>", "text/html")
        assert "script.log" in answer["error"]

    def test_json_body_without_an_error_field_gains_one(self, portal_page: Any) -> None:
        """A refusal that carries JSON but names no reason must still read as a failure."""
        answer = read_answer(portal_page, 403, '{"detail": "forbidden"}', "application/json")
        assert answer["error"]  # The caller checks this field before it shows a result.
        assert answer["detail"] == "forbidden"  # The original payload must survive.


class TestEveryCallerUsesTheReader:
    """A missed call site would reproduce the defect on that one control."""

    def test_no_script_calls_response_json_directly(self, portal_page: Any, expiry_portal: str) -> None:
        """Every portal script must read an answer through the shared reader."""
        names = ["portal.js", "operations.js", "operation_results.js", "data_preview.js"]
        offenders = []
        for name in names:
            body = portal_page.request.get(f"{expiry_portal}/static/js/{name}").text()
            code = "\n".join(line for line in body.splitlines() if not line.strip().startswith("//"))
            if ".json()" in code:  # A direct read is the defect this issue repaired.
                offenders.append(name)
        assert offenders == []
