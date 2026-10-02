"""Controlled native SDK transport with passive observations for issue #3699."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock
from urllib.parse import urlencode

from mistapi.__api_response import APIResponse
from requests import Response
from requests.exceptions import ConnectionError, Timeout

from tests.unit.export.test_endpoint_family_exporter import _trend_response
from tests.unit.export.trend_object_export.documents import TrendDocument


@dataclass(frozen=True)
class WireScenario:
    """Describe one real local HTTP response without a success default."""

    status: int
    body: object
    headers: dict[str, str] = field(default_factory=dict)
    wire: bytes | None = None


@dataclass(frozen=True)
class NativeBoundaries:
    """Expose only observations and owned input state, not I/O methods."""

    document: TrendDocument
    transport: NativeTrendTransport
    writer: MagicMock
    network: MagicMock
    router: MagicMock


class NativeResponseFactory:
    """Build complete HTTP responses for the actual SDK decoder."""

    HOST = "https://api.issue3699.test"

    @staticmethod
    def make(uri: str, scenario: WireScenario) -> Response:
        """Retain prepared headers, status, JSON, and optional malformed wire bytes."""
        response = _trend_response(NativeResponseFactory.HOST + uri, scenario.body, scenario.headers)
        response.status_code = scenario.status
        if scenario.wire is not None:
            response._content = scenario.wire
        return response

    @staticmethod
    def failure(uri: str, name: str) -> Response | APIResponse | None:
        """Construct native later-page failure conditions without decoding substitutions."""
        if name == "none_status":
            return APIResponse(None, NativeResponseFactory.HOST + uri)
        if name == "missing_response":
            return None
        if name in ("403", "503"):
            scenario = WireScenario(
                int(name), {"error": "source-body-marker-3699", "apitoken": "credential-marker-3699"}
            )
        else:
            wire = b'{"source-body-marker-3699":' if name == "malformed_json" else b""
            scenario = WireScenario(200, None, wire=wire)
        return NativeResponseFactory.make(uri, scenario)


class NativeTrendTransport:
    """Own the local transport boundary while real SDK operations construct requests."""

    def __init__(self, document: TrendDocument) -> None:
        """Prepare only the exact site lookup and selected trend response."""
        site_uri = "/api/v1/orgs/org-3335/sites?limit=1000"
        self.responses: dict[str, Response | APIResponse | Exception | None] = {
            site_uri: NativeResponseFactory.make(
                site_uri, WireScenario(200, [{"id": "site-3335", "name": "Local Site"}])
            ),
            document.target.uri: NativeResponseFactory.make(document.target.uri, WireScenario(200, document.payload)),
        }
        self.calls: list[tuple[str, dict[str, str] | None]] = []
        self.decoded: list[APIResponse] = []

    def request(self, uri: str, query: dict[str, str] | None = None) -> APIResponse | None:
        """Decode real wire responses and reject every unexpected request."""
        self.calls.append((uri, query))
        key = uri + ("?" + urlencode(query) if query else "")
        response = self.responses[key]
        if isinstance(response, Exception):
            raise response
        if response is None:
            return None
        native = (
            response if isinstance(response, APIResponse) else APIResponse(response, NativeResponseFactory.HOST + key)
        )
        self.decoded.append(native)
        return native

    def paginated(
        self, document: TrendDocument, shape: str, first: list[dict[str, Any]], second: list[dict[str, Any]]
    ) -> str:
        """Supply actual header or results links for real SDK traversal."""
        next_uri = document.target.uri + "?page=2"
        body = first if shape == "list" else {"results": first, "next": next_uri}
        headers = {"X-Page-Total": "2", "X-Page-Limit": "1", "X-Page-Page": "1"} if shape == "list" else {}
        self.responses[document.target.uri] = NativeResponseFactory.make(
            document.target.uri, WireScenario(200, body, headers)
        )
        self.responses[next_uri] = NativeResponseFactory.make(
            next_uri, WireScenario(200, second if shape == "list" else {"results": second})
        )
        return next_uri

    @staticmethod
    def expected_calls(document: TrendDocument, next_uri: str | None = None) -> list[tuple[str, Any]]:
        """State the exact native calls without deriving them from observed calls."""
        expected: list[tuple[str, Any]] = [
            ("/api/v1/orgs/org-3335/sites", {"limit": "1000"}),
            (document.target.uri, {}),
        ]
        return expected + ([(next_uri, None)] if next_uri is not None else [])


COMMON_FAILURES = (
    (
        "http_4xx",
        WireScenario(403, {"error": "source-body-marker-3699", "apitoken": "credential-marker-3699"}),
    ),
    (
        "http_5xx",
        WireScenario(503, {"error": "source-body-marker-3699", "apitoken": "credential-marker-3699"}),
    ),
    (
        "malformed_json",
        WireScenario(200, None, wire=b'{"source-body-marker-3699":"credential-marker-3699",'),
    ),
    ("empty_body", WireScenario(200, None, wire=b"")),
    ("timeout", Timeout("source-body-marker-3699 credential-marker-3699")),
    ("connection_error", ConnectionError("source-body-marker-3699 credential-marker-3699")),
    ("none_status", APIResponse(None, NativeResponseFactory.HOST + "/api/v1/unavailable")),
)
