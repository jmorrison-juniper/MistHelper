"""Prove safe first-failure evidence without changing read-only retry behavior."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest
import requests
from mistapi.__api_response import APIResponse

from src.api import api_data_fetcher as fetcher_module
from src.api.api_data_fetcher import APIDataFetcher
from src.config import runtime_settings

_PRIVATE_RESPONSE_TEXT = "private-retry-evidence-sentinel"


@dataclass(frozen=True)
class _RetryCase:
    """Describe an independent response sequence and its unchanged retry policy."""

    status_codes: tuple[int | None, ...]
    retry_limit: int
    delays: tuple[float, ...]


@dataclass(frozen=True)
class _RetryBoundaries:
    """Expose only the endpoint, delay, network, and output boundaries under test."""

    session: object
    endpoint: MagicMock
    sleep: MagicMock
    network: MagicMock
    writer: MagicMock


@pytest.fixture
def boundaries(monkeypatch: pytest.MonkeyPatch) -> _RetryBoundaries:
    """Block real requests and output writes without changing SDK logging."""
    boundaries = _RetryBoundaries(
        session=object(),
        endpoint=MagicMock(__name__="controlledReadOnlyEndpoint"),
        sleep=MagicMock(),
        network=MagicMock(side_effect=AssertionError("The retry test attempted a network request.")),
        writer=MagicMock(side_effect=AssertionError("The retry test attempted an output or store write.")),
    )
    resolver = SimpleNamespace(
        apisession=boundaries.session,
        DataExporter=SimpleNamespace(write_with_format_selection=boundaries.writer),
    )
    monkeypatch.setattr(fetcher_module, "SourceDependencyResolver", resolver)
    monkeypatch.setattr(fetcher_module, "time", SimpleNamespace(sleep=boundaries.sleep))
    monkeypatch.setattr(requests.Session, "request", boundaries.network)
    monkeypatch.setattr(runtime_settings, "API_REQUEST_MAX_RETRIES", 2)
    monkeypatch.setattr(runtime_settings, "API_REQUEST_RETRY_DELAY", 2)
    return boundaries


class TestFirstFailureEvidence:
    """Measure real fetcher diagnostics and exact side effects at the SDK boundary."""

    @staticmethod
    def _native_response(status: int | None) -> APIResponse:
        """Use the real SDK response with private content and mocked transport."""
        url = f"https://api.invalid/api/v1/orgs/controlled/readonly?token={_PRIVATE_RESPONSE_TEXT}"
        if status is None:
            return APIResponse(response=None, url=url)
        transport = MagicMock(spec=requests.Response)
        transport.status_code = status
        transport.url = url
        transport.headers = {"Authorization": _PRIVATE_RESPONSE_TEXT}
        transport.text = json.dumps({"error": _PRIVATE_RESPONSE_TEXT} if status >= 400 else [{"id": "returned-row"}])
        transport.json.return_value = json.loads(transport.text)
        return APIResponse(response=transport, url=url)

    @staticmethod
    def _expected_diagnostics(case: _RetryCase) -> list[tuple[int, str]]:
        """Specify every warning and the final error without reading product output."""
        expected: list[tuple[int, str]] = []
        for attempt, delay in enumerate(case.delays):
            status = case.status_codes[attempt] if case.status_codes[attempt] is not None else "unavailable"
            expected.append(
                (
                    logging.WARNING,
                    f"API call controlledReadOnlyEndpoint failed (attempt {attempt + 1}/{case.retry_limit + 1}, "
                    f"HTTP status: {status}) - retrying in {delay:.0f}s",
                )
            )
        if case.status_codes[-1] is None or case.status_codes[-1] >= 500:
            status = case.status_codes[-1] if case.status_codes[-1] is not None else "unavailable"
            expected.append(
                (
                    logging.ERROR,
                    f"API call controlledReadOnlyEndpoint failed after {case.retry_limit + 1} attempts "
                    f"(HTTP status: {status})",
                )
            )
        return expected

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(_RetryCase(status_codes=(503, 200), retry_limit=1, delays=(2,)), id="first-503-then-200"),
            pytest.param(
                _RetryCase(status_codes=(500, 502, 503, 200), retry_limit=3, delays=(2, 4, 8)),
                id="different-server-failures-then-200",
            ),
            pytest.param(
                _RetryCase(status_codes=(503, 502, 504), retry_limit=2, delays=(2, 4)), id="exhausted-server-failures"
            ),
            pytest.param(_RetryCase(status_codes=(None, 200), retry_limit=1, delays=(2,)), id="absent-status-then-200"),
            pytest.param(_RetryCase(status_codes=(200,), retry_limit=2, delays=()), id="immediate-200"),
            pytest.param(_RetryCase(status_codes=(400,), retry_limit=2, delays=()), id="http-400-no-retry"),
            pytest.param(_RetryCase(status_codes=(401,), retry_limit=2, delays=()), id="http-401-no-retry"),
            pytest.param(_RetryCase(status_codes=(403,), retry_limit=2, delays=()), id="http-403-no-retry"),
            pytest.param(_RetryCase(status_codes=(404,), retry_limit=2, delays=()), id="http-404-no-retry"),
            pytest.param(_RetryCase(status_codes=(429,), retry_limit=2, delays=()), id="http-429-no-retry"),
            pytest.param(_RetryCase(status_codes=(503,), retry_limit=0, delays=()), id="zero-retry-ceiling"),
            pytest.param(
                _RetryCase(status_codes=(None, None), retry_limit=1, delays=(2,)), id="exhausted-absent-statuses"
            ),
            pytest.param(
                _RetryCase(status_codes=(None, 502, 200), retry_limit=2, delays=(2, 4)),
                id="absent-and-server-statuses-then-200",
            ),
        ],
    )
    def test_retry_trace(
        self,
        case: _RetryCase,
        boundaries: _RetryBoundaries,
        caplog: pytest.LogCaptureFixture,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Retain each failed status and preserve response identity, calls, and delays."""
        responses = [self._native_response(status) for status in case.status_codes]
        boundaries.endpoint.side_effect = responses
        monkeypatch.setattr(runtime_settings, "API_REQUEST_MAX_RETRIES", case.retry_limit)
        fetcher = APIDataFetcher("Controlled read-only evidence", boundaries.endpoint, "unused.csv", page=100)
        fetcher.org_id = "org-1"
        with caplog.at_level(logging.DEBUG, logger=fetcher_module.logger.name):
            result = fetcher._call_api_with_retry("controlledReadOnlyEndpoint")
        records = [record for record in caplog.records if record.name == fetcher_module.logger.name]
        diagnostics = [(record.levelno, record.getMessage()) for record in records]
        expected = self._expected_diagnostics(case)
        assert result is responses[-1]
        assert boundaries.endpoint.call_args_list == [call(boundaries.session, "org-1", page=100)] * len(responses)
        assert boundaries.sleep.call_args_list == [call(delay) for delay in case.delays]
        assert boundaries.network.call_count == boundaries.writer.call_count == 0
        assert all(_PRIVATE_RESPONSE_TEXT not in message for _, message in diagnostics)
        assert len(diagnostics) == len(expected)
        assert diagnostics == expected

    @pytest.mark.parametrize(
        "status",
        [
            pytest.param(None, id="absent-status"),
            pytest.param(True, id="boolean-is-not-an-http-status"),
            pytest.param(503.0, id="float-is-not-an-http-status"),
            pytest.param(f"503 {_PRIVATE_RESPONSE_TEXT}", id="private-string-is-not-an-http-status"),
            pytest.param(MagicMock(name=_PRIVATE_RESPONSE_TEXT), id="arbitrary-object-is-not-an-http-status"),
        ],
    )
    def test_non_integer_status_is_not_rendered(
        self, status: object, boundaries: _RetryBoundaries, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Name absent status evidence without formatting arbitrary SDK values."""
        if isinstance(status, MagicMock):
            status.__str__.side_effect = AssertionError("The diagnostic formatted an arbitrary status object.")
        response = SimpleNamespace(status_code=status, raw_data=_PRIVATE_RESPONSE_TEXT)
        with caplog.at_level(logging.DEBUG, logger=fetcher_module.logger.name):
            APIDataFetcher._log_retry_attempt("controlledReadOnlyEndpoint", 0, 2, response)
        diagnostics = [
            (record.levelno, record.getMessage())
            for record in caplog.records
            if record.name == fetcher_module.logger.name
        ]
        assert diagnostics == [
            (
                logging.WARNING,
                "API call controlledReadOnlyEndpoint failed (attempt 1/3, HTTP status: unavailable) - retrying in 2s",
            )
        ]
        assert boundaries.sleep.call_args_list == [call(2)]
        assert boundaries.network.call_count == boundaries.writer.call_count == 0

    @pytest.mark.parametrize(
        "failure",
        [
            pytest.param(requests.Timeout("controlled timeout"), id="timeout"),
            pytest.param(requests.ConnectionError("controlled connection error"), id="connection-error"),
        ],
    )
    def test_transport_exception_still_propagates(
        self, failure: requests.RequestException, boundaries: _RetryBoundaries, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Keep raised transport failures outside the response retry algorithm."""
        boundaries.endpoint.side_effect = failure
        fetcher = APIDataFetcher("Controlled read-only evidence", boundaries.endpoint, "unused.csv")
        fetcher.org_id = "org-1"
        with pytest.raises(type(failure)) as caught:
            fetcher._call_api_with_retry("controlledReadOnlyEndpoint")
        assert caught.value is failure
        assert boundaries.endpoint.call_args_list == [call(boundaries.session, "org-1")]
        assert boundaries.sleep.call_args_list == []
        assert [record for record in caplog.records if record.name == fetcher_module.logger.name] == []
        assert boundaries.network.call_count == boundaries.writer.call_count == 0
