"""Client tests for the guest portal SMS provider test operation."""

from __future__ import annotations  # WHY: keep annotations consistent with source modules.

from dataclasses import dataclass  # WHY: fake mistapi responses need a tiny typed object.
from typing import Any  # WHY: fake SDK call signatures accept the session object.

from src.mist.intelligence.troubleshooting.sms_provider_test.client import SmsProviderTestClient
from src.mist.intelligence.troubleshooting.sms_provider_test.model import (
    SMSGLOBAL_PROVIDER,
    TELSTRA_PROVIDER,
    TWILIO_PROVIDER,
)


@dataclass(slots=True)
class FakeResponse:
    """Minimal mistapi response used by client tests."""

    status_code: int | None  # WHY: client reads this attribute from mistapi responses.
    data: object  # WHY: client converts this attribute into response text.


def test_client_dispatches_to_each_provider_call() -> None:
    """Client dispatch must call the SDK function that matches the provider."""
    calls: list[tuple[str, dict[str, str]]] = []  # WHY: record each provider call and body.

    def make_call(name: str) -> Any:
        """Return one fake SDK call that records its provider name."""

        def call(_session: object, body: dict[str, str]) -> FakeResponse:
            calls.append((name, body))  # WHY: capture the dispatch result for assertions.
            return FakeResponse(200, {"ok": True})  # WHY: successful response keeps focus on dispatch.

        return call  # WHY: caller installs this fake in the call map.

    client = SmsProviderTestClient(  # WHY: inject fake SDK functions and avoid network access.
        object(),
        {
            "twilio": make_call("twilio"),
            "smsglobal": make_call("smsglobal"),
            "telstra": make_call("telstra"),
        },
    )
    client.test_provider(TWILIO_PROVIDER, {"to": "+1"})  # WHY: exercise Twilio dispatch.
    client.test_provider(SMSGLOBAL_PROVIDER, {"to": "+2"})  # WHY: exercise SMSGlobal dispatch.
    client.test_provider(TELSTRA_PROVIDER, {"to": "+3"})  # WHY: exercise Telstra dispatch.
    assert [name for name, _body in calls] == ["twilio", "smsglobal", "telstra"]  # WHY: order proves dispatch.


def test_client_normalizes_http_4xx_response() -> None:
    """Client must keep status and response text for HTTP 4xx responses."""

    def failed_call(_session: object, _body: dict[str, str]) -> FakeResponse:
        return FakeResponse(403, {"detail": "Permission Denied"})  # WHY: simulate Mist refusing the request.

    client = SmsProviderTestClient(object(), {"twilio": failed_call})  # WHY: one fake call is enough here.
    result = client.test_provider(TWILIO_PROVIDER, {"to": "+1"})  # WHY: run the fake failed call.
    assert result.status_code == 403  # WHY: operator must see the HTTP status.
    assert not result.accepted  # WHY: non-2xx responses are failure verdicts.
    assert "Permission Denied" in result.response_text  # WHY: operator must see the response body.


def test_client_normalizes_http_5xx_response() -> None:
    """Client must keep status and response text for HTTP 5xx responses."""

    def failed_call(_session: object, _body: dict[str, str]) -> FakeResponse:
        return FakeResponse(503, {"detail": "Service Unavailable"})  # WHY: simulate a Mist service failure.

    client = SmsProviderTestClient(object(), {"twilio": failed_call})  # WHY: one fake call is enough here.
    result = client.test_provider(TWILIO_PROVIDER, {"to": "+1"})  # WHY: run the fake failed call.
    assert result.status_code == 503  # WHY: operator must see the HTTP status.
    assert not result.accepted  # WHY: non-2xx responses are failure verdicts.
    assert "Service Unavailable" in result.response_text  # WHY: operator must see the response body.
