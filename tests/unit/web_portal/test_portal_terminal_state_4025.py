"""Portal terminal-state tests for the issue #4025 HTTP 404 answer.

Issue #4025 reports that menus 260 and 261 "never reach a terminal state".
Measurement showed the run does reach a terminal state, but the wrong one: the
exporter logs ``! No <operation> data found`` for an upstream HTTP 404, and the
portal classifier reads that text as an honest empty result and reports
``Complete``. The operator then believes the organization holds no applications.

These tests bridge the two halves. They drive the real
``SimpleEndpointExporter._run`` against a stubbed non-raising 404 response, take
the exact log lines it produces, and feed them to the real portal classifier.
A 404 must classify as a handled error, so the run ends failed and terminal. A
genuine empty success must still classify as an empty result, so a real empty
organization keeps its honest wording.

The terminal state depends on the portal text classifier. Issue #3168 tracks the
replacement of that classifier with a typed outcome, and this coupling must be
revisited then.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.foundation.support.utils.menu_entry import MenuEntry
from src.operations.exporting.export.simple_endpoint_exporter import (
    SimpleEndpointExporter,
    _SimpleEndpointOp,
)
from web_portal.services.operation import OperationExecutor

# Menu 260 runs this operation. Issue #4025 names it as the HTTP 404 case.
ORG_APPLICATION_LIST = _SimpleEndpointOp("getOrgApplicationList", "mistapi.api.v1.orgs.wxtags")
MENU_UNDER_TEST = "260"  # The portal menu row that issue #4025 names.
ORG_APPLICATIONS_URL = "/api/v1/orgs/org-one/wxtags/apps"  # The published SDK route the cloud rejects.


class _EventBus:
    """Collect published events without starting a browser or an SSE stream."""

    def __init__(self) -> None:
        """Start with an empty event list."""
        self.events: list[tuple[str, dict]] = []  # Hold the event type and payload for later reads.

    def publish(self, event_type: str, data: dict) -> None:
        """Record one event the executor would stream to the browser."""
        self.events.append((event_type, data))  # Keep the exact event for an assertion.


class _StubResponse:
    """Stand in for a mistapi APIResponse that does not raise on an error status."""

    def __init__(self, status_code: int | None, data: Any, url: str) -> None:
        """Record the fields the exporter and the SDK pagination helper read."""
        self.status_code = status_code  # The HTTP status the exporter must inspect.
        self.data = data  # The parsed body, which holds an error payload for a 4xx answer.
        self.url = url  # The request URL, so an error line can name the failed path.
        self.next: str | None = None  # No further page exists for this answer.
        self.raw_data = ""  # The SDK keeps the unparsed body, which these tests do not read.
        self.headers: dict[str, str] = {}  # The SDK records response headers.
        self.proxy_error = False  # A proxy failure is a separate SDK condition.


def _capture_exporter_lines(response: Any, caplog: pytest.LogCaptureFixture) -> list[str]:
    """Run the real exporter against one stubbed response and return its log lines."""
    module = MagicMock()  # The exporter reads apisession and DataExporter from this resolver.
    module.apisession = MagicMock()  # The SDK call receives this session object.
    callable_obj = MagicMock(return_value=response)  # The SDK function returns the stubbed response.
    with (
        patch("src.operations.exporting.export.simple_endpoint_exporter.SourceDependencyResolver", module),
        patch.object(SimpleEndpointExporter, "_resolve", return_value=callable_obj),
        caplog.at_level(logging.INFO),
    ):
        SimpleEndpointExporter._run(ORG_APPLICATION_LIST, "org-one", "org-one")  # Drive the production path.
    return [record.getMessage() for record in caplog.records]  # Return the exact operator-facing lines.


def _build_executor() -> OperationExecutor:
    """Build a portal executor that knows only the menu issue #4025 names."""
    menu_actions = {  # The executor needs a handler and a title for each run record.
        MENU_UNDER_TEST: MenuEntry(
            menu_id=MENU_UNDER_TEST,  # Keep the menu number available to the executor.
            handler=lambda: None,  # These tests call the classifier helpers directly.
            title="List organization applications",  # Run records require a readable title.
            category="interactive_safe",  # The classifier helpers do not read this field.
            destructive=False,  # This operation only reads data.
            supports_fast=False,  # Fast-mode metadata is irrelevant here.
        )
    }
    return OperationExecutor(menu_actions, None, None, _EventBus())  # A fake bus keeps the test offline.


def _run_record_from(executor: OperationExecutor, lines: list[str]) -> dict:
    """Build a portal run record that holds the supplied log lines."""
    run = executor._build_run_record(MENU_UNDER_TEST)  # Use the production run record shape.
    for line in lines:  # Replay every line the exporter produced, in order.
        run["log_messages"].append({"message": line, "level": "info"})  # Match the portal log entry shape.
    return run  # Return the record for a classifier read.


def test_a_404_run_classifies_as_a_handled_error(caplog: pytest.LogCaptureFixture) -> None:
    """An upstream HTTP 404 must end the portal run as a handled error."""
    response = _StubResponse(404, {"detail": "Not Found"}, ORG_APPLICATIONS_URL)
    lines = _capture_exporter_lines(response, caplog)
    executor = _build_executor()
    assert executor._handled_error_reason(_run_record_from(executor, lines)) is not None


def test_a_404_run_does_not_classify_as_an_empty_result(caplog: pytest.LogCaptureFixture) -> None:
    """An upstream HTTP 404 must not read as an honest empty organization."""
    response = _StubResponse(404, {"detail": "Not Found"}, ORG_APPLICATIONS_URL)
    lines = _capture_exporter_lines(response, caplog)
    executor = _build_executor()
    assert executor._no_output_reason(_run_record_from(executor, lines)) is None


def test_a_404_reason_names_the_status_code(caplog: pytest.LogCaptureFixture) -> None:
    """The portal failure reason must carry the HTTP status for the operator."""
    response = _StubResponse(404, {"detail": "Not Found"}, ORG_APPLICATIONS_URL)
    lines = _capture_exporter_lines(response, caplog)
    executor = _build_executor()
    assert "404" in str(executor._handled_error_reason(_run_record_from(executor, lines)))


def test_a_500_run_classifies_as_a_handled_error(caplog: pytest.LogCaptureFixture) -> None:
    """An upstream server failure must also end the run as a handled error."""
    response = _StubResponse(500, {"detail": "Internal Server Error"}, ORG_APPLICATIONS_URL)
    lines = _capture_exporter_lines(response, caplog)
    executor = _build_executor()
    assert executor._handled_error_reason(_run_record_from(executor, lines)) is not None


def test_an_empty_success_still_classifies_as_an_empty_result(caplog: pytest.LogCaptureFixture) -> None:
    """A genuine empty organization must keep the honest empty-result answer."""
    response = _StubResponse(200, {"results": []}, ORG_APPLICATIONS_URL)
    lines = _capture_exporter_lines(response, caplog)
    executor = _build_executor()
    assert executor._no_output_reason(_run_record_from(executor, lines)) is not None


def test_an_empty_success_does_not_classify_as_a_handled_error(caplog: pytest.LogCaptureFixture) -> None:
    """A genuine empty organization must not be reported as a failure."""
    response = _StubResponse(200, {"results": []}, ORG_APPLICATIONS_URL)
    lines = _capture_exporter_lines(response, caplog)
    executor = _build_executor()
    assert executor._handled_error_reason(_run_record_from(executor, lines)) is None
