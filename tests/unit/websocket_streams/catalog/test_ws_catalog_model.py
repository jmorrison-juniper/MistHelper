"""Tests for the WebSocket catalog model records."""

from src.mist.realtime.websocket_streams.catalog.model import (
    ChannelDefinition,
    FieldKind,
    FieldSpec,
    Safety,
    UtilityDefinition,
)  # Import catalog records under test.


def test_channel_definition_hides_path_and_builds_repeated_paths() -> None:
    """A channel payload excludes the path and path building repeats one target."""
    field = FieldSpec("site_id", "Site", FieldKind.UUID, required=True, picker="sites")  # Build the target field.
    channel = ChannelDefinition(
        "site.devices", "site", "Device events", "Device events.", "/sites/{site_id}/devices", (field,), "site_id"
    )  # Build one channel.
    payload = channel.to_payload()  # Convert the channel for the page.
    paths = channel.build_paths(
        {"site_id": ("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")}
    )  # Build paths for two sites.
    assert "path_template" not in payload  # The page must not receive a path.
    assert paths == (
        "/sites/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/devices",
        "/sites/bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb/devices",
    )  # Each site gives one path.


def test_utility_definition_payload_marks_lock() -> None:
    """A utility payload carries the lock state and field payloads."""
    field = FieldSpec("host", "Host", FieldKind.HOST, required=True)  # Build the host field.
    target = FieldSpec(
        "device_id", "Device", FieldKind.UUID, required=True, picker="devices"
    )  # Build the device target.
    utility = UtilityDefinition(
        "ex.ping", "ex", "ping", "Ping", "Ping a host.", (field,), Safety.READ, "lines", (target,)
    )  # Build one utility.
    payload = utility.to_payload(locked=True)  # Convert the utility for the page.
    assert payload["locked"] is True  # The payload must carry the lock state.
    assert payload["fields"][0]["name"] == "host"  # The field payload must name the SDK parameter.
