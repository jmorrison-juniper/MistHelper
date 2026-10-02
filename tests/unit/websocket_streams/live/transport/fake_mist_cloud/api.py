"""Fake Mist API session for issue #3671 transport and runner tests."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import uuid  # Default trigger answers need stable-shaped identifiers.
from collections.abc import Callable  # Tests can set a hook or answer factory.
from dataclasses import dataclass  # Response and call records stay small.
from typing import Any  # Overrides can return different data shapes.

import requests  # The fake session exposes a real requests.Session object.

from tests.unit.websocket_streams.live.transport.fake_mist_cloud.server import (
    FakeMistCloud,
)  # Default shell URLs come from the fake cloud.


@dataclass(frozen=True, slots=True)
class FakeApiCall:
    """One fake Mist API call."""

    method: str  # HTTP method name.
    uri: str  # API URI path.
    body: object | None  # Request body.


@dataclass(slots=True)
class FakeApiResponse:
    """A small APIResponse-compatible object."""

    status_code: int  # HTTP status code.
    data: object  # Parsed response data. The SDK keeps the raw text when the body is not JSON.
    url: str = ""  # SDK APIResponse exposes this attribute.
    raw_data: str = ""  # SDK APIResponse exposes this attribute.
    next: str | None = None  # SDK APIResponse exposes this attribute.
    headers: dict[str, str] | None = None  # SDK APIResponse exposes this attribute.
    proxy_error: bool = False  # SDK APIResponse exposes this attribute.


@dataclass(frozen=True, slots=True)
class FakeApiOverride:
    """One path override for the fake API session."""

    pattern: str  # A substring matched against the request URI.
    status_code: int  # The response status.
    data: object  # The response data. A string models a body that is not JSON.
    exception: Exception | None = None  # Optional exception to raise instead.


class FakeApiSession:
    """A Mist SDK-compatible API session for offline tests."""

    def __init__(self, cloud: FakeMistCloud | None = None, cloud_uri: str = "api.mist.com") -> None:
        """Build one fake API session."""
        self.cloud = cloud  # The fake cloud supplies loopback shell and screen addresses.
        self._cloud_uri = cloud_uri  # The transport endpoint reads this private SDK field.
        self._apitoken = ["fake-token"]  # The transport endpoint reads this private SDK field.
        self._apitoken_index = 0  # The transport endpoint reads this private SDK field.
        self._session = requests.Session()  # Cookies, verify, and cert match the SDK shape.
        self.calls: list[FakeApiCall] = []  # Tests assert trigger request order and body.
        self.overrides: list[FakeApiOverride] = []  # Tests can force errors or custom data.
        self.before_post_return: Callable[[str, object | None], None] | None = None  # Early publish hook.

    def add_override(
        self,
        pattern: str,
        status_code: int = 200,
        data: object | None = None,
        exception: Exception | None = None,
    ) -> None:
        """Add one response override.

        Args:
            pattern: A substring of the request URI.
            status_code: The response status.
            data: The response data, or None for an empty object. An empty string models an empty body.
            exception: An exception to raise instead of the answer.
        """
        answer = {} if data is None else data  # Keep an empty string, because it models an empty body.
        self.overrides.append(FakeApiOverride(pattern, status_code, answer, exception))  # New overrides append.

    def mist_post(self, uri: str, body: object | None = None) -> FakeApiResponse:
        """Record a POST and return a fake response."""
        self.calls.append(FakeApiCall("POST", uri, body))  # Keep exact call data.
        override = self._override(uri)  # Tests can replace the default answer.
        if override is not None and override.exception is not None:  # Exceptions model SDK failures.
            raise override.exception  # Raise the configured exception.
        if self.before_post_return is not None:  # Command tests publish early output here.
            self.before_post_return(uri, body)  # Run the hook before the answer returns.
        if override is not None:  # A matching override wins over defaults.
            return FakeApiResponse(override.status_code, override.data, url=uri)  # Return override data.
        return FakeApiResponse(200, self._default_post_data(uri), url=uri)  # Return the default trigger data.

    def mist_get(self, uri: str) -> FakeApiResponse:
        """Record a GET and return a fake response."""
        self.calls.append(FakeApiCall("GET", uri, None))  # Keep exact call data.
        override = self._override(uri)  # Tests can replace the default answer.
        if override is not None and override.exception is not None:  # Exceptions model SDK failures.
            raise override.exception  # Raise the configured exception.
        if override is not None:  # A matching override wins over defaults.
            return FakeApiResponse(override.status_code, override.data, url=uri)  # Return override data.
        return FakeApiResponse(200, {}, url=uri)  # Default GET is empty success.

    def mist_delete(self, uri: str) -> FakeApiResponse:
        """Record a DELETE and return a fake response."""
        self.calls.append(FakeApiCall("DELETE", uri, None))  # Keep exact call data.
        override = self._override(uri)  # Tests can replace the default answer.
        if override is not None and override.exception is not None:  # Exceptions model SDK failures.
            raise override.exception  # Raise the configured exception.
        if override is not None:  # A matching override wins over defaults.
            return FakeApiResponse(override.status_code, override.data, url=uri)  # Return override data.
        return FakeApiResponse(200, {}, url=uri)  # Default DELETE is empty success.

    def _override(self, uri: str) -> FakeApiOverride | None:
        """Return the first matching override."""
        for override in self.overrides:  # Overrides are checked in insertion order.
            if override.pattern in uri:  # A substring match keeps tests simple.
                return override  # Return the configured override.
        return None  # No override matched.

    def _default_post_data(self, uri: str) -> dict[str, Any]:
        """Return default data for a POST URI."""
        if uri.endswith("/shell"):  # Shell triggers return a WebSocket URL.
            return {"url": self._cloud_url("/shell/default")}  # The fake shell path is stable.
        if uri.endswith("/run_top") or uri.endswith("/monitor_traffic"):  # Screen commands return a URL.
            return {"url": self._cloud_url("/screen/default")}  # The fake screen path is stable.
        if uri.endswith("/pcaps/capture"):  # Capture triggers return an identifier.
            return {"id": str(uuid.uuid4())}  # The capture filter matches this id.
        return {"session": str(uuid.uuid4())}  # Command triggers return a session identifier.

    def _cloud_url(self, path: str) -> str:
        """Return a fake cloud URL for one path."""
        if self.cloud is None:  # Some tests use the API session without a server.
            return f"ws://127.0.0.1:1{path}"  # Port 1 is never contacted in those tests.
        return f"{self.cloud.base_ws_url}{path}"  # The fake server owns this address.
