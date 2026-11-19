"""Tests for the ``searchOrgInventory`` export menu."""

from __future__ import annotations

import logging
import socket
from collections.abc import Iterator
from http import HTTPStatus
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import mistapi
import pytest
from mistapi.__api_response import APIResponse

from src.operations.exporting.export.org_inventory_search_exporter import OrgInventorySearchExporter

MODULE = "src.operations.exporting.export.org_inventory_search_exporter"


@pytest.fixture
def wired(monkeypatch: pytest.MonkeyPatch) -> Iterator[dict[str, Any]]:
    """Wire the exporter to isolated SDK, prompt, and writer doubles."""
    network = MagicMock(side_effect=AssertionError("Network access is forbidden"))  # Reject unintended requests.
    for attribute in ("connect", "connect_ex"):  # Guard direct connections before exercising the exporter.
        monkeypatch.setattr(socket.socket, attribute, network)  # Keep the test independent of local services.
    for attribute in ("getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr", "create_connection"):
        monkeypatch.setattr(socket, attribute, network)  # Block DNS and high-level connections.
    mistapi_mod = MagicMock(name="mistapi")  # Replace external requests without replacing response processing.
    mistapi_mod.get_all.side_effect = mistapi.get_all  # Exercise the installed SDK pagination contract.
    monkeypatch.setattr(f"{MODULE}.mistapi", mistapi_mod)  # Keep the SDK endpoint synthetic.
    processor = MagicMock(name="DataProcessingUtils")  # Isolate output transformations from persistence.
    processor.flatten_nested_fields.side_effect = lambda rows: rows  # Retain row values for argument checks.
    processor.escape_multiline.side_effect = lambda rows: rows  # Retain row values for argument checks.
    monkeypatch.setattr(f"{MODULE}.DataProcessingUtils", processor)  # Prevent unrelated data processing.
    helper = MagicMock(name="MistHelper")  # Supply source dependencies without application startup.
    helper.apisession = MagicMock(name="apisession")  # Avoid a real API session or credentials.
    helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1372"  # Use a synthetic organization.
    helper.InputUtils.safe_input.return_value = ""  # Default to no filters.
    helper.DataExporter.write_with_format_selection.return_value = True  # Model the writer boolean contract.
    monkeypatch.setitem(__import__("sys").modules, "MistHelper", helper)  # Retain the existing resolver seam.
    yield {"mistapi": mistapi_mod, "processor": processor, "helper": helper, "network": network}
    network.assert_not_called()  # Detect forbidden attempts even if the exporter catches their exceptions.


@pytest.fixture
def response(wired: dict[str, Any]) -> APIResponse:
    """Provide an SDK response without constructing an HTTP request."""
    result = APIResponse(None, "https://synthetic.invalid/inventory")  # Model a native transport response.
    result.status_code = 200  # Default to a successful initial request.
    result.data = {"results": []}  # Match the inventory search response envelope.
    wired["mistapi"].api.v1.orgs.inventory.searchOrgInventory.return_value = result  # Bind the synthetic response.
    return result  # Tests can vary status and data independently.


@pytest.mark.parametrize("status_code", [200, 206, 299, HTTPStatus.OK])
def test_inventory_calls_sdk_once_and_writes_rows(
    wired: dict[str, Any], response: APIResponse, caplog: pytest.LogCaptureFixture, status_code: int
) -> None:
    """The menu calls the endpoint once and uses the operationId for output."""
    target = wired["mistapi"].api.v1.orgs.inventory.searchOrgInventory  # Inspect the real entry-point call.
    rows = [{"id": "device-1", "mac": "00:11:22:33:44:55"}]  # Keep all inventory synthetic.
    response.status_code = status_code  # Cover both success boundaries and a partial-content status.
    response.data = {"results": rows}  # Exercise the installed SDK envelope handling.
    with caplog.at_level(logging.DEBUG):  # Capture both operator and persistence messages.
        result = OrgInventorySearchExporter.inventory()  # Preserve the public None return.
    assert result is None  # The menu contract does not expose a new status return.
    target.assert_called_once_with(wired["helper"].apisession, "org-1372")  # Preserve request arguments.
    wired["helper"].DataExporter.write_with_format_selection.assert_called_once_with(
        [{"id": "device-1", "mac": "00:11:22:33:44:55"}],
        "OrgInventorySearch_org-1372.csv",
        api_function_name="searchOrgInventory",
    )
    assert "persisted 1 rows" in caplog.text  # Successful writes retain their debug message.
    assert "1 organization inventory search record(s) exported" in caplog.text  # Preserve the success message.
    wired["network"].assert_not_called()  # The real SDK helper must not attempt a request.


def test_inventory_forwards_non_empty_filters(wired: dict[str, Any], response: APIResponse) -> None:
    """Non-empty prompts become the SDK query parameters, including integer limit."""
    values = iter(["switch", "", "", "edge", "", "", "", "", "", "connected", "", "25", "", ""])
    wired["helper"].InputUtils.safe_input.side_effect = lambda *args, **kwargs: next(values)  # Preserve prompt order.
    target = wired["mistapi"].api.v1.orgs.inventory.searchOrgInventory  # Inspect forwarded filters.

    OrgInventorySearchExporter.inventory()

    target.assert_called_once_with(
        wired["helper"].apisession,
        "org-1372",
        type="switch",
        name="edge",
        status="connected",
        limit=25,
    )
    wired["helper"].DataExporter.write_with_format_selection.assert_not_called()


def test_inventory_empty_org_aborts_before_prompt_or_call(wired: dict[str, Any]) -> None:
    """A cancelled organization selection does not call prompts or the SDK."""
    wired["helper"].ConfigUtils.get_cached_or_prompted_org_id.return_value = ""
    target = wired["mistapi"].api.v1.orgs.inventory.searchOrgInventory

    OrgInventorySearchExporter.inventory()

    assert target.call_args_list == []
    assert wired["helper"].InputUtils.safe_input.call_args_list == []


def test_inventory_api_error_is_logged(wired: dict[str, Any], caplog: pytest.LogCaptureFixture) -> None:
    """An SDK failure returns to the menu and records an error."""
    wired["mistapi"].api.v1.orgs.inventory.searchOrgInventory.side_effect = RuntimeError("boom")

    with caplog.at_level(logging.ERROR):
        OrgInventorySearchExporter.inventory()

    assert "Error fetching organization inventory search" in caplog.text


@pytest.mark.parametrize("status_code", [404, 503])
def test_inventory_http_status_error_is_logged(
    wired: dict[str, Any], caplog: pytest.LogCaptureFixture, status_code: int
) -> None:
    """An HTTP 404 or HTTP 503 SDK failure must return to the menu and log."""
    error = RuntimeError(f"HTTP {status_code}")  # Preserve the cloud status in the SDK error.
    wired["mistapi"].api.v1.orgs.inventory.searchOrgInventory.side_effect = error  # Reach the failure path.

    with caplog.at_level(logging.ERROR):  # Capture the product error signal.
        OrgInventorySearchExporter.inventory()  # Call the real exporter entry point from src.

    assert f"HTTP {status_code}" in caplog.text  # Prove the operator can see the status.
    assert "Error fetching organization inventory search" in caplog.text  # Prove the product logged the failure.
    wired["helper"].DataExporter.write_with_format_selection.assert_not_called()  # Failed calls must not write.


@pytest.mark.parametrize("status_code", [199, 300, 403, 404, 503, None, True, False, "200", 200.0, [], {}])
@pytest.mark.parametrize("payload", [{"results": [{"id": "synthetic-device"}]}, {"error": "synthetic failure"}])
def test_inventory_rejects_failed_or_malformed_initial_status(
    wired: dict[str, Any], response: APIResponse, caplog: pytest.LogCaptureFixture, status_code: Any, payload: Any
) -> None:
    """Reject failed, transport, and malformed statuses before pagination or output."""
    response.status_code = status_code  # Include the native None transport-failure status.
    response.data = payload  # Cover apparent rows and error envelopes that the SDK otherwise treats as empty.
    with caplog.at_level(logging.DEBUG):  # Detect false persistence and operator messages together.
        result = OrgInventorySearchExporter.inventory()  # Exercise the supported public failure behavior.
    assert result is None  # Request failures still return safely to the menu.
    assert "Error fetching organization inventory search" in caplog.text  # Require the established error signal.
    assert "searchOrgInventory request failed" in caplog.text  # Explain why the initial response was rejected.
    assert "No organization inventory search data found" not in caplog.text  # Failure is not a valid empty result.
    assert "exported to" not in caplog.text  # Failure is not a successful export.
    assert "persisted" not in caplog.text  # Failure is not successful persistence.
    wired["mistapi"].get_all.assert_not_called()  # Validate the initial status before SDK pagination.
    wired["processor"].flatten_nested_fields.assert_not_called()  # Do not transform invalid response rows.
    wired["helper"].DataExporter.write_with_format_selection.assert_not_called()  # Preserve existing output.
    wired["network"].assert_not_called()  # The failure path must remain fully offline.


def test_inventory_rejects_missing_initial_status(wired: dict[str, Any], caplog: pytest.LogCaptureFixture) -> None:
    """A response without a status cannot become a normal empty result."""
    response = SimpleNamespace(data={"results": []}, next=None)  # Model a malformed response without status.
    wired["mistapi"].api.v1.orgs.inventory.searchOrgInventory.return_value = response  # Inject the malformed shape.
    with caplog.at_level(logging.DEBUG):  # Detect all misleading status messages.
        result = OrgInventorySearchExporter.inventory()  # Exercise validation through the menu entry point.
    assert result is None  # Retain the public return contract.
    assert "Error fetching organization inventory search" in caplog.text  # Require a visible request failure.
    assert "No organization inventory search data found" not in caplog.text  # Missing status is not empty success.
    assert "exported to" not in caplog.text  # Missing status is not an export.
    wired["mistapi"].get_all.assert_not_called()  # Reject malformed input before pagination.
    wired["helper"].DataExporter.write_with_format_selection.assert_not_called()  # Do not persist malformed input.


@pytest.mark.parametrize("rows", [[], {"results": []}])
def test_inventory_valid_empty_result(
    wired: dict[str, Any], response: APIResponse, caplog: pytest.LogCaptureFixture, rows: Any
) -> None:
    """Successful empty responses retain the normal message without writing."""
    response.data = rows  # Cover both list and results-envelope SDK shapes.
    with caplog.at_level(logging.DEBUG):  # Capture the operator empty-result message.
        result = OrgInventorySearchExporter.inventory()  # Run the real SDK pagination helper offline.
    assert result is None  # Preserve the menu contract.
    assert "No organization inventory search data found" in caplog.text  # A valid empty result is not a failure.
    assert "Error fetching" not in caplog.text  # Successful empty results must not report a request error.
    assert "exported to" not in caplog.text  # No rows means no completed export.
    wired["mistapi"].get_all.assert_called_once()  # Prove the valid response reached SDK processing.
    wired["helper"].DataExporter.write_with_format_selection.assert_not_called()  # Preserve empty-result behavior.


def test_inventory_writer_false_reports_failure(
    wired: dict[str, Any], response: APIResponse, caplog: pytest.LogCaptureFixture
) -> None:
    """A false writer result cannot produce persistence or export-success messages."""
    response.data = {"results": [{"id": "synthetic-device"}]}  # Supply a valid matching row.
    wired["helper"].DataExporter.write_with_format_selection.return_value = False  # Model a reported write failure.
    with caplog.at_level(logging.DEBUG):  # Detect both misleading messages in the original implementation.
        result = OrgInventorySearchExporter.inventory()  # Preserve the public return on failure.
    assert result is None  # The menu does not acquire a new return type.
    assert "searchOrgInventory export failed" in caplog.text  # Make the output failure visible.
    assert "OrgInventorySearch_org-1372.csv" in caplog.text  # Identify the intended output for the operator.
    assert "exported to" not in caplog.text  # A failed writer must not claim export success.
    assert "persisted" not in caplog.text  # A failed writer must not claim persistence.
    assert "No organization inventory search data found" not in caplog.text  # Rows existed but output failed.
    wired["helper"].DataExporter.write_with_format_selection.assert_called_once()  # Do not retry failed output.


@pytest.mark.parametrize("stage", ["writer", "transform"])
def test_inventory_processing_error_retains_public_behavior(
    wired: dict[str, Any], response: APIResponse, caplog: pytest.LogCaptureFixture, stage: str
) -> None:
    """Raised processing failures retain the existing logged None-return behavior."""
    response.data = [{"id": "synthetic-device"}]  # Cover the valid SDK list shape.
    target = wired["helper"].DataExporter.write_with_format_selection  # Default to the writer failure path.
    if stage == "transform":  # Exercise transform errors separately from writer errors.
        target = wired["processor"].flatten_nested_fields  # Retain existing transform exception handling.
    target.side_effect = RuntimeError(f"{stage} failure")  # Use a synthetic exception without private context.
    with caplog.at_level(logging.DEBUG):  # Check the supported error and success message behavior.
        result = OrgInventorySearchExporter.inventory()  # Return to the menu after an existing exception.
    assert result is None  # Preserve the public return contract.
    assert f"{stage} failure" in caplog.text  # Preserve the reported exception cause.
    assert "Error fetching organization inventory search" in caplog.text  # Preserve the existing failure message.
    assert "exported to" not in caplog.text  # Exceptions do not produce export success.
    assert "persisted" not in caplog.text  # Exceptions do not produce persistence success.
