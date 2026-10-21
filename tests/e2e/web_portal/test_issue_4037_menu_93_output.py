"""Exercise Menu 93 output through the no-browser Flask client."""

from __future__ import annotations  # Keep test annotations from adding runtime import requirements.

import logging  # Emit the synthetic warning through the operation log capture.
import re  # Read the CSRF token from the rendered operations page.
from dataclasses import replace  # Preserve the registered menu metadata while mocking its handler.
from pathlib import Path  # Type the isolated output directory used by this test.
from typing import Any  # Type the shared Flask client fixture.

import pytest  # Use the typed monkeypatch fixture.

from src.foundation.models.operation_outcome import OperationOutcome  # Exercise the explicit handler result path.
from web_portal.services.event_bus import PortalEventBus  # Exercise the real completion event path.
from web_portal.services.operation import OperationExecutor  # Execute the mocked operation through production logic.


def _empty_result_handler() -> OperationOutcome:
    """Return an explicit empty result with log wording outside the legacy markers."""
    logging.getLogger("test.issue_3168").info(
        "The handler found no current alarms for this report."
    )  # WHY: avoid marker prose.
    return OperationOutcome("no_output", "The report found no current alarms.")  # WHY: provide the stable result value.


def _build_outcome_executor(client: Any, monkeypatch: pytest.MonkeyPatch) -> tuple[OperationExecutor, PortalEventBus]:
    """Build the portal executor with one handler that returns an explicit result."""
    from web_portal.menu_registry import build_static_menu_actions  # Reuse the registered safe menu metadata.

    menu_actions = build_static_menu_actions()  # Keep the production menu setup.
    menu_actions["93"] = replace(menu_actions["93"], handler=_empty_result_handler)  # Mock only the API handler.
    event_bus = PortalEventBus()  # Keep completion events on the production path.
    executor = OperationExecutor(menu_actions, None, None, event_bus)  # Use the real portal executor.
    monkeypatch.setitem(
        client.application.config, "OPERATION_EXECUTOR", executor
    )  # Route Flask requests to the executor.
    monkeypatch.setitem(client.application.config, "EVENT_BUS", event_bus)  # Share events with the same bus.
    return executor, event_bus  # Return both resources for test assertions and cleanup.


def _read_csrf_token(client: Any) -> str:
    """Read the CSRF token from the real operations page."""
    page = client.get("/operations")  # Render the real page before the protected request.
    token_match = re.search(
        r'<meta name="csrf-token" content="([^"]+)">', page.get_data(as_text=True)
    )  # WHY: read the token from the real page markup.
    if token_match is None:  # Stop if the page does not provide its request token.
        raise AssertionError("The operations page did not return a CSRF token.")  # Identify the setup failure.
    return token_match.group(1)  # Use the token returned by the page.


def _start_test_operation(client: Any, csrf_token: str) -> str:
    """Start menu 93 through the protected Flask route."""
    response = client.post(
        "/api/operations/run",
        json={"menu_number": "93", "parameters": {}},
        headers={"X-CSRFToken": csrf_token},
    )  # Start the operation through the production route.
    assert response.status_code == 202  # Require the portal to accept the mocked run.
    response_data = response.get_json()  # Read the JSON response from the production route.
    if not isinstance(response_data, dict):  # Reject a response with the wrong shape.
        raise AssertionError("The run route did not return a JSON object.")  # Name the blocked test setup.
    run_id = response_data.get("run_id")  # Read the identifier from the route response.
    if not isinstance(run_id, str):  # Reject a missing or invalid run identifier.
        raise AssertionError("The run route did not return a string run identifier.")  # Name the blocked test setup.
    return run_id  # Return the run identity created by Flask.


def test_menu_93_database_warning_keeps_inventory_in_completed_result(
    client: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:  # Exercise the completed result through the no-browser web route.
    """Keep the inventory file in the Flask status response after an unrelated database warning."""
    from web_portal.menu_registry import build_static_menu_actions  # Reuse the production-safe menu registry.

    monkeypatch.setenv("DATA_DIR", str(tmp_path))  # Keep operation output inside this test's temporary directory.
    warning = (  # The issue reports the beginning, but the full warning was not captured.
        "No database host answers the connection probe; retry after the data rows become available."
    )

    def write_inventory() -> None:
        """Write one valid result and emit the unrelated warning."""
        (tmp_path / "SiteInventory.csv").write_text(
            "device\nAP-1\n",
            encoding="utf-8",
        )  # Create a valid inventory export before warning classification runs.
        logging.getLogger("src.operations.exporting.export.data_exporter").warning(
            warning
        )  # Preserve the separate database warning in the run log.

    menu_actions = build_static_menu_actions()  # Use the portal's real registered operation metadata.
    menu_actions["93"] = replace(menu_actions["93"], handler=write_inventory)  # Mock the handler, not Mist API access.
    event_bus = PortalEventBus()  # Keep the test on the production completion event path.
    executor = OperationExecutor(menu_actions, None, None, event_bus)  # Run the mocked menu through production logic.
    monkeypatch.setitem(client.application.config, "OPERATION_EXECUTOR", executor)  # Route requests to this executor.
    monkeypatch.setitem(client.application.config, "EVENT_BUS", event_bus)  # Share the executor completion events.

    try:  # Keep executor cleanup active for every assertion path.
        page = client.get("/operations")  # Read the portal token needed by the protected run route.
        token_match = re.search(r'<meta name="csrf-token" content="([^"]+)">', page.get_data(as_text=True))
        if token_match is None:  # A missing page token must stop the protected request.
            raise AssertionError("The operations page did not return a CSRF token.")  # Name the blocked test setup.
        csrf_token = token_match.group(1)  # Keep the exact token returned by the real page.
        start = client.post(
            "/api/operations/run",
            json={"menu_number": "93", "parameters": {}},
            headers={"X-CSRFToken": csrf_token},
        )  # Start the registered operation through the Flask route.
        assert start.status_code == 202  # Require the portal to accept the mocked run.
        run_id = start.get_json()["run_id"]  # Read the identifier returned by the real route.
        executor._runs[run_id]["_future"].result(timeout=10)  # Wait for the bounded background operation to finish.

        completed = client.get(f"/api/operations/status/{run_id}")  # Read the completed result through Flask.
        result = completed.get_json()  # Decode the same status payload that the portal client receives.
        assert completed.status_code == 200  # Require a valid completed-run response.
        assert result["status"] == "completed"  # Prove the warning did not change the successful terminal state.
        assert result["output_files"] == ["SiteInventory.csv"]  # Keep the inventory visible in the result.
        assert (tmp_path / "SiteInventory.csv").is_file()  # Confirm the listed output exists in the test data root.
    finally:  # Release the worker and event bus after the route assertions.
        executor.shutdown(10)  # Drain the operation worker and remove its process-wide capture hooks.
        event_bus.stop()  # Clear event subscribers and release the test bus.


def test_explicit_empty_result_controls_flask_run_status(
    client: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:  # Exercise the returned outcome through the no-browser web route.
    """A typed empty result must control the status response despite unrelated log wording."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))  # Keep scanner state inside the test directory.
    executor, event_bus = _build_outcome_executor(client, monkeypatch)  # Use the real portal route and executor.
    try:  # Keep executor cleanup active for every assertion path.
        csrf_token = _read_csrf_token(client)  # Read the form token required by the protected route.
        run_id = _start_test_operation(client, csrf_token)  # Start the safe mocked handler.
        executor._runs[run_id]["_future"].result(timeout=10)  # Wait for terminal classification to finish.
        response = client.get(f"/api/operations/status/{run_id}")  # Read the result through the real status route.
        result = response.get_json()  # Decode the status payload used by the browser.
        assert response.status_code == 200  # Require a valid status response.
        assert result["status"] == "completed"  # Require the handler outcome to control the terminal state.
        assert result["completion_message"] == (  # Keep the exact explicit reason visible to the operator.
            "Operation completed with no output file: The report found no current alarms."
        )
        assert result["output_files"] == []  # Confirm the no-output response has no discovered file.
    finally:  # Release the executor and event bus after the route assertions.
        executor.shutdown(10)  # Drain the operation worker and remove its process-wide capture hooks.
        event_bus.stop()  # Clear event subscribers and release the test bus.
