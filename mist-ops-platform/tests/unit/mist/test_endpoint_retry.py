"""Tests for HTTP 429 retry and backoff in MistEndpointService (Issue #1886).

Before this fix, no module under mist-ops-platform/src read a 429
response or retried the call. A throttled organization then handed a
stale read or a lost write straight back to the caller. These tests
prove a 429 triggers a retry and that the retry limit is respected.
"""

from __future__ import annotations

import json  # WHY: build a JSONDecodeError that the SDK can raise.
import logging  # WHY: capture the empty-body warning.
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest  # WHY: assert that SDK exceptions reach the caller.
import requests  # WHY: use the same exception classes as the HTTP stack.

from src.shared.mist.endpoints import (
    HTTP_TOO_MANY_REQUESTS,
    MAX_429_RETRIES,
    MistEndpointService,
)
from src.shared.mist.types import MistEndpoint, MistEntityRegistry

# WHY: one shared endpoint record, only the mocked function matters here.
_ENDPOINT = MistEndpoint(
    entity_type="org_site_list",
    api_module="orgs.sites",
    read_method="listOrgSites",
    write_method=None,
    id_params=("org_id",),
)

EXPECTED_CALLS_AFTER_ONE_RETRY = 2  # WHY: one retry means the first attempt plus one more.
EXPECTED_CALLS_AFTER_TWO_RETRIES = 3  # WHY: two retries plus the first attempt.
EXPECTED_CALLS_AT_RETRY_LIMIT = MAX_429_RETRIES + 1  # WHY: the first attempt plus every retry.
RETRY_AFTER_SECONDS = "5"  # WHY: the header value the mock response returns.
RETRY_AFTER_AS_FLOAT = 5.0  # WHY: the numeric value _backoff_delay must produce from it.
HTTP_OK = 200  # WHY: name the success status so a reader does not read a bare number.
HTTP_NOT_FOUND = 404  # WHY: name the client error status for failure-mode coverage.
HTTP_SERVER_ERROR = 500  # WHY: name the server error status for failure-mode coverage.


def _make_response(
    status_code: int,
    data: dict | str | None = None,
    headers: dict | None = None,
) -> SimpleNamespace:
    """Create a mock SDK response object with an optional headers mapping."""
    body = {} if data is None else data  # WHY: keep an empty string as a failure marker.
    return SimpleNamespace(status_code=status_code, data=body, headers=headers)


def _run_read(service: MistEndpointService, mock_func: MagicMock) -> SimpleNamespace:
    """Call read_entity with the registry, resolver, and time.sleep patched out."""
    with (
        patch.object(service, "_resolve_func", return_value=mock_func),
        patch.object(MistEntityRegistry, "get", return_value=_ENDPOINT),
        patch("src.shared.mist.endpoints.time.sleep"),
    ):
        return service.read_entity("org_site_list", {"org_id": "test-org"})


class TestRetryOn429:
    """Verify a 429 reply triggers a retry instead of an immediate failure."""

    def test_a_429_then_success_retries_once(self) -> None:
        service = MistEndpointService(MagicMock())  # WHY: no rate limiter needed for this test.
        # WHY: one throttle, then a normal response.
        responses = [
            _make_response(HTTP_TOO_MANY_REQUESTS),
            _make_response(200, data={"id": "a"}),
        ]
        mock_func = MagicMock(side_effect=responses)

        result = _run_read(service, mock_func)  # WHY: the call under test.

        # WHY: the first call plus one retry.
        assert mock_func.call_count == EXPECTED_CALLS_AFTER_ONE_RETRY
        assert result.status_code == HTTP_OK  # WHY: the retry must return the eventual success.

    def test_two_429s_then_success_retries_twice(self) -> None:
        service = MistEndpointService(MagicMock())  # WHY: no rate limiter needed for this test.
        # WHY: two throttles in a row, then a normal response.
        responses = [
            _make_response(HTTP_TOO_MANY_REQUESTS),
            _make_response(HTTP_TOO_MANY_REQUESTS),
            _make_response(200, data={"id": "a"}),
        ]
        mock_func = MagicMock(side_effect=responses)

        result = _run_read(service, mock_func)  # WHY: the call under test.

        assert mock_func.call_count == EXPECTED_CALLS_AFTER_TWO_RETRIES
        assert result.status_code == HTTP_OK  # WHY: the retries must return the eventual success.

    def test_non_429_5xx_returns_without_retry(self) -> None:
        service = MistEndpointService(MagicMock())  # WHY: no rate limiter needed for this test.
        response = _make_response(HTTP_SERVER_ERROR)  # WHY: simulate one 500 response.
        mock_func = MagicMock(return_value=response)  # WHY: simulate one server error response.

        result = _run_read(service, mock_func)  # WHY: the call under test.

        assert mock_func.call_count == 1  # WHY: only 429 is safe to retry automatically.
        assert result.status_code == HTTP_SERVER_ERROR  # WHY: report the 500 to the caller.

    def test_non_429_4xx_returns_without_retry(self) -> None:
        service = MistEndpointService(MagicMock())  # WHY: no rate limiter needed for this test.
        status_code = HTTP_NOT_FOUND  # Prove the HTTP 4xx status family with a status-named value.
        response = _make_response(status_code)  # WHY: simulate one 404 response.
        mock_func = MagicMock(return_value=response)  # WHY: simulate one client error response.

        result = _run_read(service, mock_func)  # WHY: the call under test.

        assert mock_func.call_count == 1  # WHY: only 429 is safe to retry automatically.
        assert result.status_code == HTTP_NOT_FOUND  # WHY: report the 404 to the caller.

    def test_connection_timeout_reaches_the_caller(self) -> None:
        service = MistEndpointService(MagicMock())  # WHY: no rate limiter needed for this test.
        mock_func = MagicMock(side_effect=requests.exceptions.Timeout("read timed out"))

        with pytest.raises(requests.exceptions.Timeout, match="read timed out"):
            _run_read(service, mock_func)  # WHY: the timeout must not become an empty success.

    def test_connection_error_reaches_the_caller(self) -> None:
        service = MistEndpointService(MagicMock())  # WHY: no rate limiter needed for this test.
        mock_func = MagicMock(side_effect=requests.exceptions.ConnectionError("dns failure"))

        with pytest.raises(requests.exceptions.ConnectionError, match="dns failure"):
            _run_read(service, mock_func)  # WHY: do not hide the connection failure.

    def test_malformed_json_error_reaches_the_caller(self) -> None:
        service = MistEndpointService(MagicMock())  # WHY: no rate limiter needed for this test.
        mock_func = MagicMock(side_effect=json.JSONDecodeError("bad json", "", 0))

        with pytest.raises(json.JSONDecodeError):
            _run_read(service, mock_func)  # WHY: malformed JSON from the SDK must stay visible.

    def test_empty_body_warning_reaches_the_operator(self, caplog) -> None:
        service = MistEndpointService(MagicMock())  # WHY: no rate limiter needed for this test.
        mock_func = MagicMock(return_value=_make_response(HTTP_OK, data=""))

        with caplog.at_level(logging.WARNING):
            result = _run_read(service, mock_func)  # WHY: test the empty-body path.

        assert result.data == {}  # WHY: the caller receives a safe empty data object.
        assert "Mist response body is empty" in caplog.text  # WHY: report the empty body.


class TestRetryLimitIsRespected:
    """Verify the retry loop stops at MAX_429_RETRIES instead of looping forever."""

    def test_constant_429_stops_at_the_retry_limit(self) -> None:
        service = MistEndpointService(MagicMock())  # WHY: no rate limiter needed for this test.
        # WHY: every attempt is throttled, so the limit must be what stops the loop.
        mock_func = MagicMock(return_value=_make_response(HTTP_TOO_MANY_REQUESTS))

        result = _run_read(service, mock_func)  # WHY: the call under test.

        # WHY: this is the proof a broken loop would fail: a hard stop at the limit.
        assert mock_func.call_count == EXPECTED_CALLS_AT_RETRY_LIMIT
        # WHY: the last 429 reaches the caller.
        assert result.status_code == HTTP_TOO_MANY_REQUESTS

    def test_the_retry_is_logged_as_a_warning(self, caplog) -> None:
        import logging

        service = MistEndpointService(MagicMock())  # WHY: no rate limiter needed for this test.
        responses = [
            _make_response(HTTP_TOO_MANY_REQUESTS),
            _make_response(200, data={"id": "a"}),
        ]
        mock_func = MagicMock(side_effect=responses)

        with caplog.at_level(logging.WARNING):
            _run_read(service, mock_func)  # WHY: the call under test.

        assert "429" in caplog.text  # WHY: an operator must see why the call was retried.


class TestBackoffHonorsRetryAfter:
    """Verify a Retry-After header controls the wait, not just exponential backoff."""

    def test_retry_after_header_is_used_as_the_sleep_duration(self) -> None:
        service = MistEndpointService(MagicMock())  # WHY: no rate limiter needed for this test.
        # WHY: the API told the caller exactly how long to wait.
        responses = [
            _make_response(HTTP_TOO_MANY_REQUESTS, headers={"Retry-After": RETRY_AFTER_SECONDS}),
            _make_response(200, data={"id": "a"}),
        ]
        mock_func = MagicMock(side_effect=responses)

        with (
            patch.object(service, "_resolve_func", return_value=mock_func),
            patch.object(MistEntityRegistry, "get", return_value=_ENDPOINT),
            patch("src.shared.mist.endpoints.time.sleep") as mock_sleep,
        ):
            service.read_entity("org_site_list", {"org_id": "test-org"})  # WHY: call under test.

        # WHY: the header value must win over the default exponential backoff.
        mock_sleep.assert_called_once_with(RETRY_AFTER_AS_FLOAT)

    def test_a_missing_header_falls_back_to_exponential_backoff(self) -> None:
        service = MistEndpointService(MagicMock())  # WHY: no rate limiter needed for this test.
        # WHY: no Retry-After header this time, so backoff must fall back.
        responses = [
            _make_response(HTTP_TOO_MANY_REQUESTS, headers={}),
            _make_response(200, data={"id": "a"}),
        ]
        mock_func = MagicMock(side_effect=responses)

        with (
            patch.object(service, "_resolve_func", return_value=mock_func),
            patch.object(MistEntityRegistry, "get", return_value=_ENDPOINT),
            patch("src.shared.mist.endpoints.time.sleep") as mock_sleep,
        ):
            service.read_entity("org_site_list", {"org_id": "test-org"})  # WHY: call under test.

        # WHY: attempt 0 backs off BASE_BACKOFF_SECONDS, a small positive number.
        assert mock_sleep.call_args[0][0] > 0
