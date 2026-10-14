"""Exercise Menu 93 output through the no-browser Flask client."""

from __future__ import annotations  # Keep test annotations from adding runtime import requirements.

import logging  # Emit the synthetic warning through the operation log capture.
import re  # Read the CSRF token from the rendered operations page.
from dataclasses import replace  # Preserve the registered menu metadata while mocking its handler.
from pathlib import Path  # Type the isolated output directory used by this test.
from typing import Any  # Type the shared Flask client fixture.

import pytest  # Use the typed monkeypatch fixture.

from web_portal.services.event_bus import PortalEventBus  # Exercise the real completion event path.
from web_portal.services.operation import OperationExecutor  # Execute the mocked operation through production logic.


def test_menu_93_database_warning_keeps_inventory_in_completed_result(
    client: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:  # Exercise the completed result through the no-browser web route.
    """Keep the inventory file in the Flask status response after an unrelated database warning."""
    from web_portal.menu_registry import build_static_menu_actions  # Reuse the production-safe menu registry.

    monkeypatch.setenv("DATA_DIR", str(tmp_path))  # Keep operation output inside this test's temporary directory.
    warning = "No database host answers the connection probe."  # Reproduce the standalone warning from issue #4037.

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
