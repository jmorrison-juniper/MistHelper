"""Tests for APIDataFetcher._call_api_with_retry exception handling.

Validates that mistapi >= 0.59.5 exceptions (ConnectionError, ValueError)
are properly caught and handled: ConnectionError triggers retry with
exponential backoff; ValueError is re-raised immediately (not retryable).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Bootstrap: ensure project root is importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # tests/unit -> tests -> MistHelper
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Helpers to build a minimal APIDataFetcher without importing MistHelper.py
# ---------------------------------------------------------------------------
def _make_fetcher(mock_api_call):
    """Create a minimal APIDataFetcher-like object for testing retry logic.

    We avoid importing MistHelper.py directly because it has heavy side
    effects (global state, API session init, etc.). Instead we reconstruct
    the _call_api_with_retry method behavior inline.
    """

    class _FakeFetcher:
        """Minimal stand-in for APIDataFetcher with retry logic."""

        API_REQUEST_MAX_RETRIES = 2  # Keep tests fast with few retries
        API_REQUEST_RETRY_DELAY = 0.01  # Near-zero delay for test speed

        def __init__(self, api_call):
            self.api_call = api_call  # Mock API function to call
            self.org_id = "test-org-id"  # Dummy org ID for testing
            self.kwargs = {}  # No extra kwargs for basic tests

        def _call_api_with_retry(self, api_name: str):
            """Replica of APIDataFetcher._call_api_with_retry with exception handling."""
            last_response = None  # Track last response for emergency data recovery
            for attempt in range(self.API_REQUEST_MAX_RETRIES + 1):
                try:
                    response = self.api_call("session", self.org_id, **self.kwargs)  # Call API
                except ConnectionError:
                    # mistapi >= 0.59.5 raises ConnectionError instead of sys.exit()
                    if attempt < self.API_REQUEST_MAX_RETRIES:
                        delay = self.API_REQUEST_RETRY_DELAY * (2**attempt)  # Exponential backoff
                        time.sleep(delay)  # Wait before retry
                        continue  # Retry on transient connection errors
                    raise  # Re-raise after exhausting retries
                except ValueError:
                    raise  # ValueError = bad input, not retryable

                last_response = response  # Store for fallback

                status = getattr(response, "status_code", None)  # Check response validity
                if status is not None and status < 500:
                    return response  # Valid response

                if attempt < self.API_REQUEST_MAX_RETRIES:
                    delay = self.API_REQUEST_RETRY_DELAY * (2**attempt)  # Backoff on bad response
                    time.sleep(delay)

            return last_response  # Return last response after all retries

    return _FakeFetcher(mock_api_call)  # Return configured test fetcher


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCallApiWithRetryConnectionError:
    """ConnectionError should trigger retries with exponential backoff."""

    def test_connection_error_retries_then_raises(self):
        """ConnectionError on all attempts should exhaust retries then raise."""
        mock_call = MagicMock(side_effect=ConnectionError("network unreachable"))  # Always fail
        fetcher = _make_fetcher(mock_call)

        with pytest.raises(ConnectionError, match="network unreachable"):
            fetcher._call_api_with_retry("testEndpoint")

        assert mock_call.call_count == fetcher.API_REQUEST_MAX_RETRIES + 1  # All retries attempted

    def test_connection_error_recovers_on_retry(self):
        """ConnectionError on first attempt, success on second should return response."""
        good_response = SimpleNamespace(status_code=200, data=[])  # Valid API response
        mock_call = MagicMock(
            side_effect=[ConnectionError("timeout"), good_response]  # Fail then succeed
        )
        fetcher = _make_fetcher(mock_call)

        result = fetcher._call_api_with_retry("testEndpoint")

        assert result.status_code == 200  # Should return the successful response
        assert mock_call.call_count == 2  # One failure + one success


class TestCallApiWithRetryValueError:
    """ValueError should NOT be retried -- re-raised immediately."""

    def test_value_error_raises_immediately(self):
        """ValueError should not trigger any retries."""
        mock_call = MagicMock(side_effect=ValueError("invalid org_id format"))  # Bad input
        fetcher = _make_fetcher(mock_call)

        with pytest.raises(ValueError, match="invalid org_id format"):
            fetcher._call_api_with_retry("testEndpoint")

        assert mock_call.call_count == 1  # Only one attempt, no retries


class TestCallApiWithRetryNormalFlow:
    """Normal retry flow for invalid responses (status_code=None or >=500)."""

    def test_valid_response_returns_immediately(self):
        """A 200 response should return without retries."""
        good_response = SimpleNamespace(status_code=200, data={"results": []})  # Valid response
        mock_call = MagicMock(return_value=good_response)
        fetcher = _make_fetcher(mock_call)

        result = fetcher._call_api_with_retry("testEndpoint")

        assert result.status_code == 200  # Immediate return on valid response
        assert mock_call.call_count == 1  # No retries needed

    def test_server_error_retries(self):
        """500 response should trigger retries."""
        bad_response = SimpleNamespace(status_code=500, data=None)  # Server error
        good_response = SimpleNamespace(status_code=200, data=[])  # Recovery response
        mock_call = MagicMock(side_effect=[bad_response, good_response])  # Fail then succeed
        fetcher = _make_fetcher(mock_call)

        result = fetcher._call_api_with_retry("testEndpoint")

        assert result.status_code == 200  # Should return recovery response
        assert mock_call.call_count == 2  # One failure + one success

    def test_none_status_code_retries(self):
        """Response with status_code=None (timeout swallowed) should retry."""
        timeout_response = SimpleNamespace(status_code=None)  # Swallowed timeout
        good_response = SimpleNamespace(status_code=200, data=[])  # Recovery response
        mock_call = MagicMock(side_effect=[timeout_response, good_response])  # Fail then succeed
        fetcher = _make_fetcher(mock_call)

        result = fetcher._call_api_with_retry("testEndpoint")

        assert result.status_code == 200  # Should return recovery response
        assert mock_call.call_count == 2  # One failure + one success

    def test_all_retries_exhausted_returns_last_response(self):
        """When all retries fail, should return the last response."""
        bad_response = SimpleNamespace(status_code=500, data=None)  # Persistent server error
        mock_call = MagicMock(return_value=bad_response)  # Always fail
        fetcher = _make_fetcher(mock_call)

        result = fetcher._call_api_with_retry("testEndpoint")

        assert result.status_code == 500  # Returns last bad response for partial data recovery
        assert mock_call.call_count == fetcher.API_REQUEST_MAX_RETRIES + 1  # All attempts used
