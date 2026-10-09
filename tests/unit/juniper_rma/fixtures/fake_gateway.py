"""Test doubles for the Juniper integration. No double opens a network connection.

The fixtures use synthetic values that follow the documented shapes. No value
here comes from a customer, and no value here is a credential.
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import json  # WHY: fixtures are written as JSON bytes, the same form that the API sends.
from dataclasses import dataclass, field  # WHY: small typed records for the recorded calls.
from pathlib import Path  # WHY: the saved replies live beside this module.
from types import SimpleNamespace  # WHY: a session stand-in with the attributes the workflows read.
from typing import Any  # WHY: fixture payloads are loosely typed.

from src.operations.exporting.juniper_rma.api.asset_service import (
    JuniperAssetService,  # WHY: the real service, fed by a double.
)
from src.operations.exporting.juniper_rma.api.case_service import (
    JuniperCaseService,  # WHY: the real service, fed by a double.
)
from src.operations.exporting.juniper_rma.api.gateway import (
    JuniperTransportError,  # WHY: the error that the doubles can raise.
)
from src.operations.exporting.juniper_rma.api.messages import (  # WHY: the envelope builder and reader used by the real services.  # noqa: E501
    JuniperTransportReply,
    RequestMessageBuilder,
    ResponseStatusReader,
)
from src.operations.exporting.juniper_rma.settings import (
    JuniperSettings,  # WHY: the settings record that the tests build.
)

CASE_BASE_URL = "https://apigw.juniper.net/css-caseapi/1.0"  # WHY: the production Case base address.
ASSET_BASE_URL = "https://apigw.juniper.net/css-asset/1.0"  # WHY: the production Asset base address.
TOKEN_URL = "https://apigw.juniper.net/invoke/pub.apigateway.oauth2/getAccessToken"  # WHY: the token endpoint.
TEST_SECRET = "secret-test-value"  # WHY: a fake client secret, used to prove that it never reaches a log.
TEST_TOKEN = "token-test-value"  # WHY: a fake bearer token, used to prove that it never reaches a log.


def make_settings(**overrides: Any) -> JuniperSettings:
    """Return a settings record with synthetic values. Keyword arguments replace single fields."""
    values: dict[str, Any] = {  # WHY: every field has a synthetic value.
        "app_id": "app-test-value",
        "customer_source_id": "source-test-value",
        "client_id": "client-test-value",
        "client_secret": TEST_SECRET,
        "user_id": "user.test@example.com",
        "account_id": "0000000000",
        "contact_email": "contact.test@example.com",
        "token_url": TOKEN_URL,
        "case_base_url": CASE_BASE_URL,
        "asset_base_url": ASSET_BASE_URL,
        "allowed_hosts": ("apigw.juniper.net",),
        "requests_per_second": 2.0,
        "retry_attempts": 3,
        "ca_bundle": None,
        "retention_days": 180,
        "ticket_key_field": "case_number",
    }
    values.update(overrides)  # WHY: the caller changes only the fields it names.
    return JuniperSettings(**values)  # WHY: the validated record for the tests.


def json_bytes(payload: Any) -> bytes:
    """Return the payload as UTF-8 JSON bytes, the form that the API sends."""
    return json.dumps(payload).encode("utf-8")  # WHY: the gateway reads bytes and parses them.


FIXTURE_ROOT = Path(__file__).resolve().parent  # WHY: the saved replies sit beside this module.


def load_fixture(section: str, name: str) -> dict[str, Any]:  # WHY: one saved reply, parsed as JSON.
    """Return one saved reply from the fixtures folder, as the parsed body."""
    path = FIXTURE_ROOT / section / f"{name}.json"  # WHY: the file that holds the named reply.
    payload: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))  # WHY: the body, as the gateway returns it.
    return payload  # WHY: the body for the caller.


class FakeClock:
    """A clock that moves only when a test moves it."""

    def __init__(self, start: float = 0.0) -> None:
        """Start the clock at the given time."""
        self.now = start  # WHY: the current fake time in seconds.

    def __call__(self) -> float:
        """Return the current fake time."""
        return self.now  # WHY: the rate limiter and the token cache read this value.

    def advance(self, seconds: float) -> None:
        """Move the clock forward by the given seconds."""
        self.now += seconds  # WHY: a sleep moves the clock, as a real sleep would.


class FakeResponse:
    """A minimal stand-in for a requests response with a status, a body, and a close call."""

    def __init__(self, status_code: int, body: bytes = b"") -> None:
        """Store the status and the body bytes."""
        self.status_code = status_code  # WHY: the HTTP status the gateway checks.
        self.content = body  # WHY: the token reader reads the whole body.
        self._body = body  # WHY: the streaming reader reads the body in chunks.
        self.closed = False  # WHY: a test can confirm that the connection was released.

    def iter_content(self, chunk_size: int = 8192) -> Any:
        """Yield the body in chunks of the requested size."""
        for start in range(0, len(self._body), chunk_size):  # WHY: stream the bytes in order.
            yield self._body[start : start + chunk_size]  # WHY: one chunk at a time.

    def close(self) -> None:
        """Mark the response as closed."""
        self.closed = True  # WHY: the gateway must release every connection.


class FakeHttpSession:
    """Replays queued replies to POST calls and records every call. Exceptions in the queue are raised."""

    def __init__(self, replies: list[FakeResponse | BaseException]) -> None:
        """Store the queue of replies in the order that the calls will use them."""
        self._replies = list(replies)  # WHY: a copy, so the test list stays unchanged.
        self.calls: list[tuple[str, dict[str, Any]]] = []  # WHY: every URL and keyword set that was posted.

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        """Record the POST call and return the next queued reply."""
        return self._next(url, kwargs)  # WHY: POST and GET share one reply queue.

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        """Record the GET call and return the next queued reply."""
        return self._next(url, kwargs)  # WHY: the gateway retries GET through the same queue.

    def _next(self, url: str, kwargs: dict[str, Any]) -> FakeResponse:
        """Record the call and return the next queued reply."""
        self.calls.append((url, kwargs))  # WHY: the tests check headers, redirects, timeouts, and parameters.
        if not self._replies:  # WHY: a call without a queued reply is a test mistake.
            raise AssertionError("FakeHttpSession received a call with no queued reply")  # WHY: fail loudly.
        reply = self._replies.pop(0)  # WHY: the next reply in order.
        if isinstance(reply, BaseException):  # WHY: a queued exception simulates a transport failure.
            raise reply  # WHY: the gateway must handle it.
        return reply  # WHY: the reply for the caller.


@dataclass
class FakeCall:
    """One recorded call of the fake gateway. A POST records its envelope, and a GET records its query."""

    endpoint: str  # WHY: the operation name.
    base_url: str  # WHY: the base address that the service passed.
    path: str  # WHY: the operation path.
    body: dict[str, Any] = field(default_factory=dict)  # WHY: the envelope that the service built, for assertions.
    query: dict[str, str] = field(default_factory=dict)  # WHY: the query parameters of a GET, for assertions.


@dataclass
class FakeGateway:
    """Replays queued bodies by endpoint name, records each envelope, and can raise transport errors."""

    bodies: dict[str, list[dict[str, Any]]] = field(default_factory=dict)  # WHY: queued reply bodies by endpoint.
    failures: dict[str, list[JuniperTransportError]] = field(default_factory=dict)  # WHY: queued transport errors.
    statuses: dict[str, list[int]] = field(default_factory=dict)  # WHY: queued HTTP statuses, 200 when none is queued.
    calls: list[FakeCall] = field(default_factory=list)  # WHY: every call, in order.

    def post(
        self,
        endpoint: str,
        base_url: str,
        path: str,
        build_body: Any,
    ) -> JuniperTransportReply:
        """Build the envelope as the real gateway would, record it, and return the next queued body."""
        transaction = "0" * 32  # WHY: a fixed identifier keeps the assertions simple.
        body = build_body(transaction)  # WHY: the service's envelope builder runs exactly as in production.
        self.calls.append(FakeCall(endpoint=endpoint, base_url=base_url, path=path, body=body))  # WHY: record it.
        return self._next_reply(endpoint, transaction)  # WHY: the same queue serves POST and GET.

    def get(
        self,
        endpoint: str,
        base_url: str,
        path: str,
        query: dict[str, str],
    ) -> JuniperTransportReply:
        """Record the query and return the next queued body, as the real gateway does for a GET."""
        self.calls.append(FakeCall(endpoint=endpoint, base_url=base_url, path=path, query=dict(query)))  # WHY.
        return self._next_reply(endpoint, "")  # WHY: a GET has no transaction identifier.

    def _next_reply(self, endpoint: str, transaction: str) -> JuniperTransportReply:
        """Return the next queued failure, body, and status for one endpoint."""
        queued_failures = self.failures.get(endpoint, [])  # WHY: a queued failure replaces the reply.
        if queued_failures:  # WHY: the failure happens before a reply.
            raise queued_failures.pop(0)  # WHY: the service must handle a transport error.
        queued_bodies = self.bodies.get(endpoint, [])  # WHY: the replies for this endpoint.
        reply_body = queued_bodies.pop(0) if queued_bodies else {}  # WHY: an empty body when the queue is empty.
        queued_statuses = self.statuses.get(endpoint, [])  # WHY: a queued HTTP status replaces the default 200.
        http_status = queued_statuses.pop(0) if queued_statuses else 200  # WHY: 200 when no status is queued.
        return JuniperTransportReply(  # WHY: the same reply shape that the real gateway returns.
            endpoint=endpoint,
            http_status=http_status,
            body=reply_body,
            transaction_id=transaction,
            attempts=1,
        )

    def calls_for(self, endpoint: str) -> list[FakeCall]:
        """Return the recorded calls for one endpoint."""
        return [call for call in self.calls if call.endpoint == endpoint]  # WHY: assertions read one endpoint.


def build_session(gateway: Any, settings: JuniperSettings) -> SimpleNamespace:
    """Return a session stand-in that wires the real services to the given gateway."""
    builder = RequestMessageBuilder(settings)  # WHY: envelopes use the test settings.
    reader = ResponseStatusReader()  # WHY: replies are read by the real reader.
    return SimpleNamespace(  # WHY: the workflows read settings, case, and asset from the session.
        settings=settings,
        case=JuniperCaseService(gateway, builder, reader, settings.case_base_url),
        asset=JuniperAssetService(gateway, builder, reader, settings.asset_base_url),
    )
