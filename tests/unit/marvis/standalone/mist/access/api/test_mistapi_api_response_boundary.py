"""Test the mistapi APIResponse body parsing boundary."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13 tests.

import requests  # Build real response objects for the SDK parser.
from mistapi.__api_response import APIResponse  # Drive the installed SDK response boundary.

OK_STATUS_CODE = 200  # Name the successful status that masks parse failures.
RESPONSE_URL = "https://api.mist.example/self"  # Use a synthetic URL to avoid a live request.


def assert_mistapi_empty_result_observation() -> None:
    """Assert that mistapi maps bad and empty bodies to empty data."""
    for body in (b"{bad json", b""):  # Exercise malformed JSON and an empty body at the SDK boundary.
        response = requests.Response()  # Build the concrete response type that mistapi accepts.
        response.status_code = OK_STATUS_CODE  # Preserve the successful HTTP status from issue #2934.
        response.url = RESPONSE_URL  # Give the SDK a URL for diagnostic fields.
        response._content = body  # Set the raw body bytes that the SDK parses internally.
        api_response = APIResponse(response, RESPONSE_URL)  # Drive the real installed SDK parser.
        assert api_response.status_code == OK_STATUS_CODE  # The caller still observes HTTP 200.
        assert api_response.data == {}  # The caller observes the SDK default empty result.


def test_mistapi_api_response_returns_empty_data_for_unparseable_body() -> None:
    """Malformed and empty bodies must document the mistapi empty-result asymmetry."""
    assert_mistapi_empty_result_observation()  # Call the SDK boundary assertion exactly once.
