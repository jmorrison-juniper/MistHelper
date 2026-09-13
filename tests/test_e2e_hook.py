"""Tests for the end-to-end client comparison performance hook.

Why:
    Issue 2482 needs proof that the hook stays off by default, emits one event
    when enabled, preserves the result, preserves exceptions, and records no
    private identifiers.
"""

from __future__ import annotations  # Keep annotations lazy for the project Python targets.

import json  # Parse the JSON Lines event that the recorder sink emits.
from typing import Any  # Type the small fixture maps without adding a model.

import pytest  # Use pytest for monkeypatch and exception checks.

from src.upgrade_portal.compare import clients  # Import the real comparison path.
from src.utils.performance import Recorder, RecorderSettings  # Build isolated recorders for each test.

PRIVATE_MAC = "aa:bb:cc:dd:ee:ff"  # A private client address that must not enter the event.
PRIVATE_IP = "10.20.30.40"  # A private client IP that must not enter the event.
PRIVATE_ORG = "11111111-1111-1111-1111-111111111111"  # A private organization identifier.
PRIVATE_SITE = "22222222-2222-2222-2222-222222222222"  # A private site identifier.


def _client(mac: str = PRIVATE_MAC, device: str = "001122334455") -> dict[str, str]:
    """Return one client row for the offline comparison fixture."""
    return {  # Build the minimum row that the comparison reads.
        clients.MAC_KEY: mac,  # Use a real address shape to test privacy.
        clients.DEVICE_MAC_KEY: device,  # Keep the serving device stable.
        clients.DEVICE_NAME_KEY: "switch-one",  # Give the output a readable device name.
        clients.HOSTNAME_KEY: "client-one",  # Give the output a readable client name.
        "ip": PRIVATE_IP,  # Include an IP that the hook must not record.
    }  # Return the row to the capture fixture.


def _capture() -> dict[str, Any]:
    """Return one offline capture with private identifiers in the payload."""
    return {  # Build a capture shape that the real comparison reads.
        "org_id": PRIVATE_ORG,  # Include an organization identifier in source data.
        "site_id": PRIVATE_SITE,  # Include a site identifier in source data.
        clients.CLIENTS_KEY: {  # Store client sections in the production shape.
            clients.KIND_WIRED: [_client()],  # Add one wired client to compare.
            clients.KIND_WIRELESS: [],  # Keep the other sections empty.
            clients.KIND_GUEST: [],  # Keep the other sections empty.
        },
    }  # Return the capture to the test.


def _set_recorder(monkeypatch: pytest.MonkeyPatch, level: str) -> Recorder:
    """Install one recorder on the comparison module for one test."""
    recorder = Recorder(RecorderSettings(level=level))  # Build an isolated recorder.
    monkeypatch.setattr(clients, "_PERFORMANCE_RECORDER", recorder)  # Replace the module recorder.
    return recorder  # Let the test inspect emitted events.


def test_hook_emits_nothing_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """The default off level must emit no event."""
    recorder = _set_recorder(monkeypatch, "off")  # Force the disabled level.
    result = clients.compare_clients(_capture(), _capture())  # Run the real path.
    assert result.deltas[0].outcome == clients.OUTCOME_PRESENT  # Prove the function still ran.
    assert recorder.sink.drain() == []  # Confirm the disabled hook emits nothing.


def test_hook_emits_one_event_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """The base level must emit exactly one operation event."""
    recorder = _set_recorder(monkeypatch, "base")  # Force the enabled level.
    result = clients.compare_clients(_capture(), _capture())  # Run the real path.
    records = recorder.sink.drain()  # Drain the sink after the timed work.
    assert result.deltas[0].outcome == clients.OUTCOME_PRESENT  # Confirm the result shape.
    assert len(records) == 1  # One operation call must emit one event.
    event = json.loads(records[0])  # Parse the one event for field checks.
    assert event["event_type"] == "operation"  # Confirm the selected event family.
    assert event["source"]["symbol"] == "compare_clients"  # Confirm the source symbol.


def test_hook_does_not_alter_the_function_result(monkeypatch: pytest.MonkeyPatch) -> None:
    """The enabled hook must return the same comparison result."""
    _set_recorder(monkeypatch, "off")  # Use the off path as the reference.
    disabled = clients.compare_clients(_capture(), _capture())  # Collect the reference result.
    _set_recorder(monkeypatch, "base")  # Use the enabled path as the candidate.
    enabled = clients.compare_clients(_capture(), _capture())  # Collect the candidate result.
    assert enabled == disabled  # Dataclass equality proves no behavior change.


def test_hook_does_not_swallow_exceptions(monkeypatch: pytest.MonkeyPatch) -> None:
    """The hook must let the original exception propagate."""
    recorder = _set_recorder(monkeypatch, "base")  # Enable the hook for the error path.

    def broken_client_map(*_args: object) -> dict[str, Any]:
        """Return an impossible map to force the comparison fault."""
        return {"bad": None}  # Force both rows to appear absent for one address.

    monkeypatch.setattr(clients, "_client_map", broken_client_map)  # Inject the fault into the real loop.
    with pytest.raises(ValueError, match="holds no pre-check row"):  # The original error must propagate.
        clients.compare_clients(_capture(), _capture())  # Run the hooked path.
    records = recorder.sink.drain()  # Drain after the exception escapes.
    assert len(records) == 1  # The error path still emits one event.
    assert json.loads(records[0])["status"] == "error"  # The event marks the failed outcome.


def test_hook_records_no_private_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """The event must not contain a MAC, an IP address, an org, or a site."""
    recorder = _set_recorder(monkeypatch, "base")  # Enable the hook for inspection.
    clients.compare_clients(_capture(), _capture())  # Run the path with private source data.
    payload = recorder.sink.drain()[0]  # Read the one event line.
    assert PRIVATE_MAC not in payload  # The client address must not appear.
    assert PRIVATE_MAC.replace(":", "") not in payload  # The normalized address must not appear.
    assert PRIVATE_IP not in payload  # The client IP address must not appear.
    assert PRIVATE_ORG not in payload  # The organization identifier must not appear.
    assert PRIVATE_SITE not in payload  # The site identifier must not appear.
