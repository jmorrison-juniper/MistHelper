"""Shared assertions for observable HTTP failure modes."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13 test runs.

from types import SimpleNamespace  # Build status result objects without network access.

import pytest  # Assert the transport exception path without hand-written try blocks.
import requests  # Build response doubles that match the mistapi SDK input.
from mistapi.__api_response import APIResponse  # Verify the real SDK empty-result behavior.

OK_STATUS_CODE = 200  # Use the SDK success status that still hides body parse failures.
MALFORMED_BODY = b"{bad json"  # Give the SDK invalid JSON that it catches internally.
RESPONSE_URL = "https://api.mist.example/self"  # Use a synthetic URL to avoid live requests.


def assert_transport_exception_observation(exception_name: str) -> None:
    """Assert that a transport failure reaches the caller as an exception."""
    exception_types = {  # Map detector marker names to real Requests exception classes.
        "Timeout": requests.exceptions.Timeout,  # Model a request timeout from the transport.
        "ConnectionError": requests.exceptions.ConnectionError,  # Model a failed connection.
    }
    selected_exception = exception_types[exception_name]  # Select the exact failure requested.

    def raise_transport_failure() -> None:
        """Raise the selected transport exception for this contract test."""
        raise selected_exception("synthetic transport failure")  # Prove the exception path.

    with pytest.raises(selected_exception):  # Assert the caller can observe this exception.
        raise_transport_failure()  # Execute the synthetic transport failure.


def assert_mistapi_empty_result_observation(body_marker: str | bytes) -> None:
    """Assert that mistapi maps body parse failures to an empty result."""
    body = MALFORMED_BODY if body_marker == "JSONDecodeError" else body_marker  # Select body data.
    response = requests.Response()  # Build a real Requests response for the SDK parser.
    response.status_code = OK_STATUS_CODE  # Keep the HTTP status successful for this asymmetry.
    response.url = RESPONSE_URL  # Give the SDK a URL for diagnostic fields.
    response._content = body if isinstance(body, bytes) else str(body).encode()  # Set raw body bytes.
    api_response = APIResponse(response, RESPONSE_URL)  # Let mistapi parse the response.
    assert api_response.status_code == OK_STATUS_CODE  # The caller still sees HTTP 200.
    assert api_response.data == {}  # The caller sees the SDK default empty result.


def assert_http_status_observation(status_code: int) -> None:
    """Assert that a caller can inspect an HTTP failure status."""
    result = SimpleNamespace(status_code=status_code, data={"detail": "failure"})  # Fake API result.
    assert result.status_code == status_code  # The status code must stay observable.
    assert result.data == {"detail": "failure"}  # The body must stay separate from status.
