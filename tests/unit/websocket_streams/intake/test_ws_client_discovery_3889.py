"""Test safe wired-client choices for issue #3889."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from types import SimpleNamespace  # Build SDK responses without network access.
from typing import Any  # Type monkeypatch callbacks without SDK internals.

import mistapi  # Patch only the wired-client GET call.
import pytest  # Check bounded request failures.
from flask import Flask  # Exercise the route through a local test client.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Assert explicit discovery failures.
from src.mist.realtime.websocket_streams.intake.pickers.service import StreamPickerService  # Test picker behavior.
from src.mist.realtime.websocket_streams.web.blueprint.registry import WebSocketBlueprint  # Test route wiring.
from src.mist.realtime.websocket_streams.web.blueprint.requests.services import ServiceRequest  # Inject fake services.

SITE_ID = "11111111-2222-3333-4444-555555555555"  # Use a stable site identifier.
OTHER_SITE_ID = "22222222-3333-4444-5555-666666666666"  # Prove site isolation.
DEVICE_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"  # Use a stable switch identifier.
DEVICE_MAC = "aabbcc000002"  # Match the selected switch.
CLIENT_MAC = "aabbccddeeff"  # Match one client.
ORG_ID = "99999999-8888-7777-6666-555555555555"  # Use a stable organization identifier.
CLIENT_RECORDS = [
    {"site_id": SITE_ID, "mac": CLIENT_MAC, "hostname": "Client One", "device_mac": [DEVICE_MAC]},
    {"site_id": OTHER_SITE_ID, "mac": "001122334455", "hostname": "Other Site", "device_mac": [DEVICE_MAC]},
    {"site_id": SITE_ID, "mac": "001122334466", "hostname": "Other Switch", "device_mac": ["aabbcc000099"]},
    {"site_id": SITE_ID, "mac": "AA:BB:CC:DD:EE:FF", "hostname": "Duplicate", "device_mac": [DEVICE_MAC]},
    {
        "site_id": SITE_ID,
        "mac": "001122334477",
        "hostname": "Port Client",
        "device_mac_port": [{"device_mac": DEVICE_MAC}],
    },
]  # Include valid and unrelated client records.


def install_switches(monkeypatch: Any) -> None:
    """Install one fake switch in the scoped device picker."""

    def list_devices(_session: object, site_id: str, **_kwargs: object) -> SimpleNamespace:
        """Return one selected switch with an explicit MAC."""
        return SimpleNamespace(
            status_code=200,
            data=(
                [
                    {
                        "id": DEVICE_ID,
                        "name": "Switch One",
                        "type": "switch",
                        "model": "EX4100",
                        "mac": DEVICE_MAC,
                    }
                ]
                if site_id == SITE_ID
                else []
            ),
        )  # The fake response carries only the selected site's switch.

    monkeypatch.setattr(mistapi.api.v1.sites.devices, "listSiteDevices", list_devices)  # Avoid Mist Cloud.


def install_gateway(monkeypatch: Any) -> None:
    """Install one SRX gateway without a proven WAN association."""

    def list_devices(_session: object, **_kwargs: object) -> SimpleNamespace:
        """Return a gateway but no client association."""
        return SimpleNamespace(
            status_code=200,
            data=[{"id": DEVICE_ID, "name": "Gateway One", "type": "gateway", "model": "SRX320", "mac": DEVICE_MAC}],
        )  # The WAN search cannot scope results to this gateway.

    monkeypatch.setattr(mistapi.api.v1.sites.devices, "listSiteDevices", list_devices)  # Avoid Mist Cloud.


def install_search(monkeypatch: Any, answer: SimpleNamespace, calls: list[tuple[str, str, int]]) -> None:
    """Install one fake SDK client search."""

    def search_clients(
        _session: object, site_id: str, device_mac: str | None = None, limit: int | None = None
    ) -> SimpleNamespace:
        """Return the prepared answer and record its query scope."""
        calls.append((site_id, str(device_mac), int(limit or 0)))  # Record only safe query metadata.
        return answer  # Keep every test independent from Mist Cloud.

    monkeypatch.setattr(
        mistapi.api.v1.sites.wired_clients, "searchSiteWiredClients", search_clients
    )  # Replace the SDK GET.


def build_test_client(monkeypatch: Any, service: StreamPickerService) -> Any:
    """Build a Flask client with an injected WebSocket service."""
    clients = SimpleNamespace(clients=service.clients)  # Keep client suggestions in their own route service.
    services = SimpleNamespace(pickers=SimpleNamespace(clients=clients))  # Match the route's app service shape.
    monkeypatch.setattr(ServiceRequest, "current", staticmethod(lambda: services))  # Inject local services.
    app = Flask(__name__)  # Create an isolated route host.
    app.register_blueprint(WebSocketBlueprint.create())  # Register the WebSocket routes.
    return app.test_client()  # Keep requests inside Flask.


def fail_search(*_args: object, **_kwargs: object) -> SimpleNamespace:
    """Raise a safe transport error without using Mist Cloud."""
    raise TimeoutError("simulated request timeout")  # Exercise the explicit service-error path.


def test_client_choices_require_selected_site_and_device(monkeypatch: Any) -> None:
    """Only wired rows tied to the selected site and switch become choices."""
    install_switches(monkeypatch)  # Populate the server-side target cache.
    calls: list[tuple[str, str, int]] = []  # Record the bounded GET arguments.
    answer = SimpleNamespace(status_code=200, data={"results": CLIENT_RECORDS, "next": None})  # Complete page.
    install_search(monkeypatch, answer, calls)  # Install a scoped fake SDK response.
    service = StreamPickerService(object(), ORG_ID)  # Build the picker with a fake session.
    device_rows = service.devices(SITE_ID)["rows"]  # Keep internal device MAC data out of the public picker.
    payload = service.clients(SITE_ID, DEVICE_ID)  # Resolve choices through the selected device.

    assert "_device_mac" not in device_rows[0]  # Do not expose the server-side association key.
    assert payload["rows"] == [
        {"id": CLIENT_MAC, "label": "Client One", "family": "ex", "detail": CLIENT_MAC},
        {"id": "001122334477", "label": "Port Client", "family": "ex", "detail": "001122334477"},
    ]  # Keep verified associations and one row per MAC.
    assert calls == [(SITE_ID, DEVICE_MAC, 100)]  # Query one selected device with bounded results.


def test_client_choices_reject_unknown_device_before_lookup(monkeypatch: Any) -> None:
    """A device from another site cannot drive the client query."""
    install_switches(monkeypatch)  # Cache the switch only under SITE_ID.
    queried: list[str] = []  # Record any accidental client search.

    def search_clients(_session: object, site_id: str, **_kwargs: object) -> SimpleNamespace:
        """Record a query that must not occur."""
        queried.append(site_id)  # A wrong-site selection must stop before Mist.
        return SimpleNamespace(status_code=200, data={"results": [], "next": None})  # Return an empty answer.

    monkeypatch.setattr(
        mistapi.api.v1.sites.wired_clients, "searchSiteWiredClients", search_clients
    )  # Replace the SDK GET.
    service = StreamPickerService(object(), ORG_ID)  # Build the picker with a fake session.

    with pytest.raises(StreamRequestError, match="not available at this site") as raised:
        # Reject a device absent from that site.
        service.clients(OTHER_SITE_ID, DEVICE_ID)  # Try to cross the site boundary.

    assert getattr(raised.value, "code", None) == "picker_unavailable"  # Report a capability reason.
    assert queried == []  # Do not query clients for an unverified device.


@pytest.mark.parametrize(
    ("status_code", "expected_code"),
    [(403, "picker_request_failed"), (503, "picker_service_failed")],
)
def test_client_lookup_errors_are_not_empty_results(monkeypatch: Any, status_code: int, expected_code: str) -> None:
    """Mist errors return explicit request or service failures."""
    install_switches(monkeypatch)  # Cache a valid selected switch.
    monkeypatch.setattr(
        mistapi.api.v1.sites.wired_clients,
        "searchSiteWiredClients",
        lambda *_args, **_kwargs: SimpleNamespace(status_code=status_code, data={}),
    )  # Return an upstream error without a network request.
    service = StreamPickerService(object(), ORG_ID)  # Build the picker with a fake session.

    with pytest.raises(StreamRequestError) as raised:  # Do not report an upstream failure as an empty list.
        service.clients(SITE_ID, DEVICE_ID)  # Read the scoped choices.

    assert getattr(raised.value, "code", None) == expected_code  # Preserve the failure class.
    assert getattr(raised.value, "extra", {}).get("upstream_status") == status_code  # Keep safe status evidence.


def test_client_lookup_with_more_pages_is_unavailable(monkeypatch: Any) -> None:
    """The picker refuses partial results when Mist returns a next page."""
    install_switches(monkeypatch)  # Cache a valid selected switch.
    monkeypatch.setattr(
        mistapi.api.v1.sites.wired_clients,
        "searchSiteWiredClients",
        lambda *_args, **_kwargs: SimpleNamespace(
            status_code=200,
            data={"results": [{"site_id": SITE_ID, "mac": CLIENT_MAC, "device_mac": [DEVICE_MAC]}], "next": "/next"},
        ),
    )  # Simulate an incomplete paginated answer.
    service = StreamPickerService(object(), ORG_ID)  # Build the picker with a fake session.

    with pytest.raises(StreamRequestError) as raised:  # Partial lists must not look complete.
        service.clients(SITE_ID, DEVICE_ID)  # Read the scoped choices.

    assert getattr(raised.value, "code", None) == "picker_incomplete"  # Explain that the result is incomplete.


def test_client_lookup_network_failure_is_explicit(monkeypatch: Any) -> None:
    """A transport failure does not become an empty client list."""
    install_switches(monkeypatch)  # Cache a valid selected switch.
    monkeypatch.setattr(
        mistapi.api.v1.sites.wired_clients,
        "searchSiteWiredClients",
        fail_search,
    )  # Simulate a network timeout without a live request.
    service = StreamPickerService(object(), ORG_ID)  # Build the picker with a fake session.

    with pytest.raises(StreamRequestError, match="could not read client suggestions") as raised:
        service.clients(SITE_ID, DEVICE_ID)  # Run the read-only picker path.

    assert getattr(raised.value, "code", None) == "picker_service_failed"  # Show an explicit error state.


def test_empty_client_lookup_has_a_plain_reason(monkeypatch: Any) -> None:
    """A successful empty search remains distinct from a request error."""
    install_switches(monkeypatch)  # Cache a valid selected switch.
    answer = SimpleNamespace(status_code=200, data={"results": [], "next": None})  # Return an empty page.
    install_search(monkeypatch, answer, [])  # Replace the SDK GET.
    payload = StreamPickerService(object(), ORG_ID).clients(SITE_ID, DEVICE_ID)  # Read without Mist Cloud.

    assert payload["rows"] == []  # Keep the empty state distinct.
    assert payload["reason"] == "No wired clients are listed for this switch."  # Give manual-entry guidance.


def test_malformed_client_response_is_unavailable(monkeypatch: Any) -> None:
    """An unknown response shape does not appear as an empty result."""
    install_switches(monkeypatch)  # Cache a valid selected switch.
    answer = SimpleNamespace(status_code=200, data={"items": []})  # Omit the documented results key.
    install_search(monkeypatch, answer, [])  # Replace the SDK GET.
    service = StreamPickerService(object(), ORG_ID)  # Build the picker with a fake session.

    with pytest.raises(StreamRequestError, match="unsupported client response") as raised:
        service.clients(SITE_ID, DEVICE_ID)  # Refuse the unknown response contract.

    assert getattr(raised.value, "code", None) == "picker_unavailable"  # Keep manual entry enabled.


def test_gateway_lookup_stays_unavailable(monkeypatch: Any) -> None:
    """WAN client records do not prove selected-gateway association."""
    install_gateway(monkeypatch)  # Cache a gateway without association evidence.
    service = StreamPickerService(object(), ORG_ID)  # Build the picker with a fake session.

    with pytest.raises(StreamRequestError, match="Gateway association") as raised:
        # Never use site-wide WAN rows.
        service.clients(SITE_ID, DEVICE_ID)  # Keep gateway suggestions disabled.

    assert getattr(raised.value, "code", None) == "picker_unavailable"  # Return manual-entry guidance.


def test_gateway_route_returns_manual_guidance(monkeypatch: Any) -> None:
    """The route reports unavailable gateway discovery as an explicit error."""
    install_gateway(monkeypatch)  # Cache a gateway without association evidence.
    service = StreamPickerService(object(), ORG_ID)  # Build the route's picker.
    client = build_test_client(monkeypatch, service)  # Inject the picker into Flask.
    response = client.get(f"/api/websockets/sites/{SITE_ID}/devices/{DEVICE_ID}/clients")  # Request gateway choices.
    payload = response.get_json()  # Read the bounded JSON error.

    assert response.status_code == 503  # The route distinguishes unavailable discovery.
    assert payload["code"] == "picker_unavailable"  # Keep the capability reason stable.
    assert "manually" in payload["error"]  # Direct the operator to manual input.


def test_client_route_validates_scope_and_returns_choices(monkeypatch: Any) -> None:
    """The route exposes the scoped read through the existing JSON boundary."""
    install_switches(monkeypatch)  # Cache the selected switch for the service.
    answer = SimpleNamespace(status_code=200, data={"results": CLIENT_RECORDS[:1], "next": None})  # One choice.
    install_search(monkeypatch, answer, [])  # Replace the SDK GET without recording unused metadata.
    service = StreamPickerService(object(), ORG_ID)  # Build the route's authenticated picker seam.
    client = build_test_client(monkeypatch, service)  # Inject it into an isolated Flask route.
    response = client.get(f"/api/websockets/sites/{SITE_ID}/devices/{DEVICE_ID}/clients")  # Read suggestions.

    assert response.status_code == 200  # The lookup succeeded.
    assert response.get_json()["rows"][0]["id"] == CLIENT_MAC  # The response contains the scoped choice.
